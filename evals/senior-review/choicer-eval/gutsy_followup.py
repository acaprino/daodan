"""Frozen, CPU-only input ablation and question comparison. No production writes.

prepare freezes source-derived cases, prompts and labels before inference.
prepare-slot freezes a slot-restore run over a complete reference run's exact inputs.
run checkpoints every raw request/response, refuses truncation and samples RAM.
In slot-restore mode it encodes each state prefix once, saves the server slot and
restores it before every question, verifying the reuse on each call.
report scores partial positive labels and explicit negative judgments separately.
compare pairs every slot-restore answer with the full re-encoding reference.
"""
from __future__ import annotations

import argparse
import ast
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request

import run_gutsy_v2_eval as legacy

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE / "runs/20261020T100258Z/dataset.json"
REV = "936ba644e2cee4680be1d2c29c7aadfbfb86e1bf"
PREFIX = "senior-review:"
NEW_QUESTIONS = {
    "security-auditor": "Does this code control access to accounts or private data, validate untrusted input, or handle credentials or sensitive output? Review the trust boundary even if no exploit is shown. Pure internal computation without a trust boundary is not sufficient.",
    "data-integrity-auditor": "Does this code read, write, invalidate or reconcile persisted records or cached copies of external state? Include local caches whose contents must agree with a source of truth. A temporary dictionary used only for computation is not sufficient.",
    "temporal-resilience-auditor": "Does this code govern retries, timers, polling, recovery after failure, or whether background errors remain visible over time? Review failure and recovery behavior even if the normal path works. Merely using async syntax or converting a timestamp is not sufficient.",
    "resource-lifecycle-auditor": "Does this code acquire, retain or release a lock, file, connection, subscription, worker or bounded resource slot? Consider success, failure and cancellation paths. Ordinary value allocation or an async call alone is not sufficient.",
    "ui-race-auditor": "Does this code coordinate UI events or asynchronous results with rendered state, visibility, focus, scroll or layout? Consider whether a user action or notification can race the UI state. Static styling or text alone is not sufficient.",
    "distributed-flow-auditor": "Does this code publish, receive, acknowledge or route messages across a service or process boundary, or define the contract between their producer and consumer? Pure local computation or an internal function call is not sufficient.",
    "logic-integrity-auditor": "Does this code enforce a domain rule, allowed state transition, ordering requirement, idempotency condition or ownership rule across operations? Consider correctness of fallback values and terminal states. Generic formatting or numerical conversion alone is not sufficient.",
    "cleanup-auditor": "Does the supplied evidence show unused or obsolete code, dependencies or assets, or documentation that disagrees with implementation? The mere presence of comments, documentation, or a changed file does not establish this concern.",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def legacy_constants():
    tree = ast.parse((HERE / "run_gutsy_v2_eval.py").read_text(encoding="utf-8"))
    values = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"module_contexts", "lenses"}:
                    values[target.id] = ast.literal_eval(node.value)
    return values


def window_hunks(hunks: list[dict], budget: int = 2800) -> list[dict]:
    """Losslessly partition each file, preserving exact text and original offsets.

    Character budget bounds source text, not tokens. The server tokenizer checks
    the complete prompt separately. Oversized lines split at character offsets.
    """
    by_file = {}
    for hunk in hunks:
        by_file.setdefault(hunk["path"], []).append(hunk)
    windows = []
    for path, group in by_file.items():
        pieces, used = [], 0
        for hunk in group:
            offset = 0
            while offset < len(hunk["text"]):
                space = budget - used
                if not space:
                    windows.append({"path": path, "pieces": pieces})
                    pieces, used, space = [], 0, budget
                remaining = hunk["text"][offset:]
                take = min(space, len(remaining))
                if take < len(remaining):
                    newline = remaining.rfind("\n", 0, take)
                    if newline >= 0:
                        take = newline + 1
                text = remaining[:take]
                pieces.append({"hunk_id": hunk["id"], "path": path,
                               "offset": offset, "text": text,
                               "line": hunk["start_line"] + hunk["text"][:offset].count("\n")})
                used += take
                offset += take
        if pieces:
            windows.append({"path": path, "pieces": pieces})
    for index, window in enumerate(windows, 1):
        window["id"] = f"W{index:03}"
    return windows


def window_state(cid: str, window: dict, context: str = "") -> str:
    pieces = "\n\n".join(
        f"[{p['hunk_id']}] {p['path']}:{p['line']} (character offset {p['offset']})\n{p['text']}"
        for p in window["pieces"]
    )
    header = f"[Architecture Context]\n{context}\n\n" if context else ""
    return f"Case {cid}\n{header}[Code Under Review]\n{pieces}"


def prepare(out: Path, prefix_mode: str = "slot-restore"):
    if prefix_mode not in ("full", "slot-restore"):
        raise ValueError(f"Unknown prefix mode: {prefix_mode}")
    out.mkdir(parents=True, exist_ok=False)
    values = legacy_constants()
    dataset = load(ORIGINAL)
    old = [c for c in dataset["cases"] if c["id"] in {"C01", "C07"}]
    roles = [r for r, _, _ in values["lenses"]]
    prompts = {
        "v2": {r: {"question": q, "options": [f"Yes: activate {r.split(':')[-1]}",
                                                     f"No: do not activate {r.split(':')[-1]}"]}
               for r, q, _ in values["lenses"]},
        "candidate": {PREFIX + r: {"question": q, "options": ["Yes", "No"]}
                      for r, q in NEW_QUESTIONS.items()},
    }
    # Whole functions, taken from distinct files at a pinned pre-existing revision.
    # Explicit negative labels concern only the shown snippet, not its whole project.
    descriptors = [
        ("E01", "development", "jupiter-common/jupiter_common/utils/scope_utils.py", 318, 373,
         ["security-auditor", "logic-integrity-auditor"], ["data-integrity-auditor", "resource-lifecycle-auditor", "ui-race-auditor"],
         "Filters account visibility using JWT scopes and ownership keys; local sets are not persistence."),
        ("E02", "development", "jupiter-common/jupiter_common/utils/async_cache.py", 91, 130,
         ["data-integrity-auditor"], ["security-auditor", "ui-race-auditor", "resource-lifecycle-auditor"],
         "Gets and sets cache entries and TTL; no credentials, UI or resource acquisition is shown."),
        ("E03", "development", "jupiter-common/jupiter_common/utils/ack_round_trip.py", 38, 119,
         ["temporal-resilience-auditor", "distributed-flow-auditor", "logic-integrity-auditor"], ["data-integrity-auditor", "ui-race-auditor"],
         "Publish/ACK correlation, bounded attempts, timeouts and final cleanup; no persistence or UI."),
        ("E04", "development", "jupiter-common/jupiter_common/utils/datetime_utils.py", 89, 111,
         [], ["temporal-resilience-auditor", "resource-lifecycle-auditor", "data-integrity-auditor", "distributed-flow-auditor", "security-auditor", "ui-race-auditor"],
         "Pure datetime conversion is not a scheduler, retry, resource, transport or trust boundary."),
        ("E05", "verification", "jupiter-common/jupiter_common/utils/circuit_breaker.py", 394, 423,
         ["temporal-resilience-auditor", "logic-integrity-auditor", "resource-lifecycle-auditor"], ["data-integrity-auditor", "ui-race-auditor"],
         "Circuit state admission and release of bounded in-flight probe slots govern recovery and lifecycle."),
        ("E06", "verification", "jupiter-common/jupiter_common/utils/id_utils.py", 71, 104,
         [], ["security-auditor", "temporal-resilience-auditor", "data-integrity-auditor", "resource-lifecycle-auditor", "ui-race-auditor", "distributed-flow-auditor"],
         "Deterministic display/agent identifiers use SHA-256; no security token or transport is implemented here."),
        ("E07", "verification", "jupiter-core/jupiter_core/utils/instrumented_lock.py", 149, 217,
         ["resource-lifecycle-auditor"], ["data-integrity-auditor", "security-auditor", "ui-race-auditor", "distributed-flow-auditor"],
         "Lock acquisition/release and async context-manager exit; metrics are local counters."),
        ("E08", "verification", "jupiter-core/jupiter_core/utils/log_safety.py", 87, 121,
         ["security-auditor"], ["data-integrity-auditor", "resource-lifecycle-auditor", "ui-race-auditor", "distributed-flow-auditor"],
         "Masks credentials and sensitive values in output; connection strings are text, not acquired sockets."),
    ]
    real = []
    for cid, split, path, start, end, positive, negative, rationale in descriptors:
        raw = subprocess.check_output(["git", "-C", "D:/Projects/jupiter", "show", f"{REV}:{path}"])
        text = "".join(raw.decode("utf-8").splitlines(keepends=True)[start - 1:end])
        real.append({"id": cid, "split": split, "expected_roles": [PREFIX + r for r in positive],
                     "negative_roles": [PREFIX + r for r in negative], "label_status": "labeled",
                     "label_rationale": rationale, "label_kind": "coordinator applicability judgment, not known bug",
                     "provenance": {"repo": "D:/Projects/jupiter", "revision": REV,
                                    "path": path, "blob_sha256": digest(raw)},
                     "hunks": [{"id": "H1", "path": path, "start_line": start,
                                "end_line": end, "text": text, "sha256": digest(text.encode())}]})
    cases = old + real
    jobs = []
    for case in cases:
        cid = case["id"]
        if cid.startswith("C"):
            # Freeze handwritten V2 context to isolate input packing, NOT map grounding.
            context = values["module_contexts"][cid]
            truncated = legacy.build_hunks_repr(case["hunks"], max_chars=2800)
            states = [("truncated", {"id": "W000", "pieces": []},
                       f"[Architecture Context]\n{context}\n\n[Code Diff Under Review]\n{truncated}")]
            states += [("windowed", w, window_state(cid, w, context)) for w in window_hunks(case["hunks"])]
            variants = ["v2"]
        else:
            # Identical, lossless input for both prompt variants; no handwritten context.
            states = [("windowed", w, window_state(cid, w)) for w in window_hunks(case["hunks"])]
            variants = ["v2", "candidate"]
        for mode, window, state in states:
            for variant in variants:
                for role in roles:
                    jobs.append({"case_id": cid, "mode": mode, "window": window,
                                 "variant": variant, "role": role, "state": state,
                                 **prompts[variant][role]})
    # Ensure untouched verification predictions follow all development work.
    jobs.sort(key=lambda j: (j["case_id"] >= "E05", j["case_id"], j["mode"], j["window"]["id"], j["variant"], j["role"]))
    for index, job in enumerate(jobs, 1):
        job["id"] = f"Q{index:04}"
    save(out / "cases.json", cases)
    save(out / "jobs.json", jobs)
    save(out / "prompts.json", prompts)
    plan = {
        "status": "frozen", "roles": roles, "jobs": len(jobs), "source_revision": REV,
        "prefix_mode": prefix_mode,
        "prefix_mode_basis": ("Slot restore was adopted after runs/20261021-gutsy-followup-slot/COMPARISON.md: "
                              "495/496 identical letters against full re-encoding, the only flip a near tie. "
                              "Compare results only within one prefix mode."),
        "memory_limit_bytes": 1_000_000_000, "server_context_tokens": 1536,
        "selection": "exact generated A only; Z and invalid outputs never become No",
        "scope": "C01/C07 input ablation plus 8 real-source applicability cases, no production changes",
        "historical_context": "manually authored V2 fixture, not extracted map cards; potential contamination",
        "questions": "one frozen candidate; no tuning after verification outcomes",
        "splits": "distinct source files; one project; same coordinator labels and prompts; not independently blinded",
        "inference_inputs": "opaque case ID, source path/range/text, fixed questions; no expected labels or titles",
        "predeclared_success": "Report recall, explicit-negative activations, coverage, latency, memory and regressions; no target accuracy promised",
        "hashes": {name: digest((out / name).read_bytes()) for name in ("cases.json", "jobs.json", "prompts.json")},
        "runner_sha256": digest(Path(__file__).read_bytes()),
        "legacy_sha256": digest((HERE / "run_gutsy_v2_eval.py").read_bytes()),
    }
    save(out / "plan.json", plan)
    print(json.dumps({"run": str(out), "jobs": len(jobs), "windows": {c["id"]: len(window_hunks(c["hunks"])) for c in cases}}, indent=2))


def state_prefix(job: dict) -> str:
    """State part of the trained prompt; it ends immediately before "Question:"."""
    return (f"<|im_start|>system\n{legacy.SYSTEM}<|im_end|>\n"
            f"<|im_start|>user\nState:\n{job['state'].strip()}\n\n")


def question_suffix(job: dict) -> str:
    return (f"Question: {job['question'].strip()}\n\nOptions:\n"
            + "\n".join(f"{chr(65 + i)}. {text}" for i, text in enumerate(job["options"]))
            + f"\n{legacy.REJECT_LINE}\n\nAnswer with a single letter.<|im_end|>\n"
            "<|im_start|>assistant\n<think>\n\n</think>\n\n")


def build_prompt(job: dict) -> str:
    return state_prefix(job) + question_suffix(job)


def exact_probabilities(result: dict, token_ids: dict) -> dict:
    """Never conflate bare A, space-A or lowercase a; missing top-k is unknown."""
    entries = result.get("completion_probabilities", [])
    if not entries:
        return {label: None for label in token_ids}
    row = entries[0]
    scores = {entry["id"]: entry["logprob"] for entry in row.get("top_logprobs", [])}
    if "id" in row and "logprob" in row:
        scores[row["id"]] = row["logprob"]
    return {label: math.exp(scores[tid]) if tid in scores else None for label, tid in token_ids.items()}


class MemoryMonitor:
    """Windows sampled combined working set and per-process lifetime peaks.

    Samples are compact tuples so the monitor does not grow the footprint it
    measures: time, then rss, peak rss and private bytes of server and runner.
    """
    FIELDS = ("rss", "peak_rss", "private")

    def __init__(self, proc, limit):
        self.proc, self.limit = proc, limit
        self.stop = threading.Event()
        self.exceeded = False
        self.samples = []
        self.error = None

    def sample(self):
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        handles = [kernel.OpenProcess(0x0400 | 0x0010, False, pid) for pid in (self.proc.pid, os.getpid())]
        try:
            if not all(handles):
                raise OSError("Cannot monitor owned process memory")
            while not self.stop.is_set():
                values = []
                for handle in handles:
                    counters = Counters()
                    counters.cb = ctypes.sizeof(counters)
                    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                        raise OSError("GetProcessMemoryInfo failed")
                    values.extend((counters.WorkingSetSize, counters.PeakWorkingSetSize, counters.PrivateUsage))
                self.samples.append((time.time(), *values))
                if values[0] + values[3] >= self.limit:
                    self.exceeded = True
                    self.proc.terminate()
                    return
                self.stop.wait(0.1)
        except Exception as exc:
            self.error = str(exc)
            self.proc.terminate()
        finally:
            for handle in handles:
                if handle:
                    kernel.CloseHandle(handle)

    def export(self) -> list[dict]:
        return [{"time": s[0], "server": dict(zip(self.FIELDS, s[1:4])),
                 "runner": dict(zip(self.FIELDS, s[4:7]))} for s in self.samples]


def request(base: str, endpoint: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base + endpoint, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read())


def tokenize(base: str, text: str) -> list[int]:
    return request(base, "/tokenize", {"content": text, "add_special": True})["tokens"]


SLOT_ROOT = HERE / ".cache/gutsy/slots"
SLOT_FILE = "prefix-state.bin"
NEAR_TIE_MARGIN = 0.05
COMPARISON_RULE = {
    "near_tie_margin": NEAR_TIE_MARGIN,
    "near_tie_basis": ("Reference |P(A) - P(B)|, fixed before this run from the 16-question smoke test, whose "
                       "largest probability difference was 0.029. Those questions are part of this comparison."),
    "adopt_if": [
        "all planned calls valid in both runs",
        "identical frozen prompts",
        "same model, binary and server profile except the slot directory",
        "prefix reuse verified on every call: cache_n equals the prefix tokens and cache_n plus prompt_n equals the prompt tokens",
        "every letter flip has a reference margin below near_tie_margin",
        "memory bound respected",
    ],
    "otherwise": "keep full re-encoding as the reference mechanism",
    "reported_not_tuned": "Case-level selection and aggregate score changes are reported; they do not alter this rule.",
}


def server_args(plan: dict, port: int, slot_dir: Path | None = None) -> list[str]:
    """CPU profile of the reference run; slot restore adds only the state directory."""
    args = [str(legacy.LLAMA_SERVER), "-m", str(legacy.MODEL), "-ngl", "0", "-c", str(plan["server_context_tokens"]),
            "-t", "4", "-np", "1", "--batch-size", "32", "--ubatch-size", "32", "--cache-ram", "0",
            "--ctx-checkpoints", "1"]
    if slot_dir is not None:
        args += ["--slot-save-path", str(slot_dir)]
    return args + ["--host", "127.0.0.1", "--port", str(port), "--no-warmup"]


def runtime_signature(args: list[str]) -> list[str]:
    """Server arguments without the per-run port and slot directory."""
    kept, skip = [], False
    for arg in args:
        if skip:
            skip = False
        elif arg in ("--port", "--slot-save-path"):
            skip = True
        else:
            kept.append(arg)
    return kept


def encode_state(base: str, prefix: str, n_prefix: int) -> dict:
    """Encode one state prefix from an empty slot and save it; the state file is reused per prefix."""
    erased = request(base, "/slots/0?action=erase", {})
    t0 = time.perf_counter()
    encoded = request(base, "/completion", {"prompt": prefix, "n_predict": 0, "temperature": 0, "seed": 42,
                                            "cache_prompt": True, "id_slot": 0})
    encode_seconds = time.perf_counter() - t0
    timings = encoded.get("timings", {})
    if encoded.get("truncated") or timings.get("cache_n") != 0 or timings.get("prompt_n") != n_prefix:
        raise RuntimeError(f"Prefix was not encoded whole from an empty slot: {timings}")
    t1 = time.perf_counter()
    saved = request(base, "/slots/0?action=save", {"filename": SLOT_FILE})
    if saved.get("n_saved") != n_prefix:
        raise RuntimeError(f"Saved {saved.get('n_saved')} of {n_prefix} prefix tokens")
    return {"prefix_sha256": digest(prefix.encode()), "prefix_tokens": n_prefix, "erase": erased,
            "encode": {"seconds": encode_seconds, "timings": timings, "content": encoded.get("content")},
            "save": {"seconds": time.perf_counter() - t1, "response": saved}}


def prepare_slot(out: Path, reference: Path):
    """Freeze a slot-restore run over the reference run's exact cases, jobs and prompts."""
    ref_plan = load(reference / "plan.json")
    ref_execution = load(reference / "execution.json")
    if ref_execution.get("status") != "complete" or ref_plan.get("prefix_mode", "full") != "full":
        raise ValueError("The reference must be a complete full re-encoding run")
    for name, expected in ref_plan["hashes"].items():
        if digest((reference / name).read_bytes()) != expected:
            raise ValueError(f"Reference artifact changed: {name}")
    legacy_sha = digest((HERE / "run_gutsy_v2_eval.py").read_bytes())
    if ref_plan.get("legacy_sha256") != legacy_sha:
        raise ValueError("Legacy questions changed since the reference was frozen")
    out.mkdir(parents=True, exist_ok=False)
    for name in ref_plan["hashes"]:
        (out / name).write_bytes((reference / name).read_bytes())
    plan = {key: value for key, value in ref_plan.items() if key not in {"status", "runner_sha256", "predeclared_success"}}
    plan.update({
        "status": "frozen",
        "prefix_mode": "slot-restore",
        "prefix_protocol": ("For each state: erase slot 0, encode the state prefix once with n_predict 0, save the slot. "
                            "Before every question: restore the slot, then send the complete prompt with cache_prompt. "
                            "The prefix ends immediately before 'Question:'."),
        "reference_run": reference.relative_to(HERE).as_posix(),
        "reference_plan_sha256": digest((reference / "plan.json").read_bytes()),
        "reference_runner_sha256": ref_plan["runner_sha256"],
        "comparison_rule": COMPARISON_RULE,
        "predeclared_success": "Compare every question with the reference and apply comparison_rule without tuning it on these outcomes.",
        "runner_sha256": digest(Path(__file__).read_bytes()),
        "legacy_sha256": legacy_sha,
    })
    save(out / "plan.json", plan)
    print(json.dumps({"run": str(out), "jobs": ref_plan["jobs"], "reference": plan["reference_run"]}, indent=2))


def run(out: Path):
    plan = load(out / "plan.json")
    if plan.get("status") != "frozen":
        raise ValueError("Plan is not frozen")
    for name, expected in plan["hashes"].items():
        if digest((out / name).read_bytes()) != expected:
            raise ValueError(f"Frozen artifact changed: {name}")
    if digest(Path(__file__).read_bytes()) != plan["runner_sha256"]:
        raise ValueError("Runner changed since plan freeze")
    if (out / "execution.json").exists():
        raise ValueError("Execution already attempted; preserve it and prepare a new run")
    mode = plan.get("prefix_mode", "full")
    if mode not in ("full", "slot-restore"):
        raise ValueError(f"Unknown prefix mode: {mode}")
    jobs = load(out / "jobs.json")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    slot_dir = SLOT_ROOT / out.name if mode == "slot-restore" else None
    if slot_dir is not None:
        slot_dir.mkdir(parents=True, exist_ok=False)
        (out / "states").mkdir()
    args = server_args(plan, port, slot_dir)
    execution = {"status": "running", "prefix_mode": mode, "args": args, "completed_calls": 0, "states_encoded": 0,
                 "model_sha256": file_digest(legacy.MODEL), "binary_sha256": file_digest(legacy.LLAMA_SERVER)}
    (out / "wire").mkdir()
    save(out / "execution.json", execution)
    with (out / "server.log").open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
        monitor = MemoryMonitor(proc, plan["memory_limit_bytes"])
        thread = threading.Thread(target=monitor.sample, daemon=True)
        thread.start()
        started = time.perf_counter()
        try:
            deadline = time.monotonic() + 60
            while True:
                if proc.poll() is not None:
                    raise RuntimeError("Owned server stopped during startup")
                try:
                    request(base, "/health")
                    break
                except (urllib.error.URLError, TimeoutError):
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Server health deadline exceeded")
                    time.sleep(0.25)
            execution["startup_seconds"] = time.perf_counter() - started
            execution["props"] = request(base, "/props")
            tokens = {label: request(base, "/tokenize", {"content": label, "add_special": False})["tokens"] for label in ("A", "B", "Z")}
            if any(len(ids) != 1 for ids in tokens.values()):
                raise ValueError("Option letters are not single tokens")
            token_ids = {label: ids[0] for label, ids in tokens.items()}
            execution["option_token_ids"] = token_ids
            # Preflight before any inference: sizes and, for slot restore, token-level prefixes.
            prompt_tokens, prefix_tokens, prefix_ids = {}, {}, {}
            for job in jobs:
                ids = tokenize(base, build_prompt(job))
                if len(ids) + 8 > plan["server_context_tokens"]:
                    raise ValueError(f"Oversized prompt {job['id']}: {len(ids)} tokens; nothing truncated")
                prompt_tokens[job["id"]] = len(ids)
                if mode == "slot-restore":
                    key = digest(state_prefix(job).encode())
                    if key not in prefix_ids:
                        prefix_ids[key] = tokenize(base, state_prefix(job))
                    head = prefix_ids[key]
                    if len(ids) <= len(head) or ids[:len(head)] != head:
                        raise ValueError(f"State prefix is not a token prefix of {job['id']}; no inference started")
                    prefix_tokens[key] = len(head)
            prefix_ids.clear()
            execution["preflight"] = {"prompts": len(prompt_tokens), "max_prompt_tokens": max(prompt_tokens.values()),
                                      "distinct_prefixes": len(prefix_tokens)}
            save(out / "execution.json", execution)
            current, state_id = None, None
            for job in jobs:
                if (out / "STOP").exists():
                    raise InterruptedError("Coordinator stop requested")
                if monitor.exceeded or monitor.error or proc.poll() is not None:
                    raise RuntimeError("Server or memory monitor failed")
                prompt = build_prompt(job)
                count = prompt_tokens[job["id"]]
                payload = {"prompt": prompt, "n_predict": 1, "temperature": 0, "seed": 42,
                           "n_probs": 100, "cache_prompt": True}
                record = {"id": job["id"], "case_id": job["case_id"], "role": job["role"],
                          "mode": job["mode"], "variant": job["variant"], "window_id": job["window"]["id"],
                          "prompt_sha256": digest(prompt.encode()), "prompt_tokens": count,
                          "prefix_mode": mode, "request": payload, "status": "sent"}
                if mode == "slot-restore":
                    prefix = state_prefix(job)
                    key = digest(prefix.encode())
                    if key != current:
                        execution["states_encoded"] += 1
                        state_id = f"S{execution['states_encoded']:03}"
                        state = encode_state(base, prefix, prefix_tokens[key])
                        state.update(state_id=state_id, first_job=job["id"], case_id=job["case_id"],
                                     mode=job["mode"], window_id=job["window"]["id"])
                        save(out / "states" / f"{state_id}.json", state)
                        current = key
                    payload["id_slot"] = 0
                    record.update(prefix_sha256=key, prefix_tokens=prefix_tokens[key], state_id=state_id)
                dest = out / "wire" / (job["id"] + ".json")
                save(dest, record)
                t0 = time.perf_counter()
                try:
                    if mode == "slot-restore":
                        restored = request(base, "/slots/0?action=restore", {"filename": SLOT_FILE})
                        record["restore"] = {"seconds": time.perf_counter() - t0, "response": restored}
                        if restored.get("n_restored") != record["prefix_tokens"]:
                            raise RuntimeError(f"Restored {restored.get('n_restored')} of {record['prefix_tokens']} prefix tokens")
                        t0 = time.perf_counter()
                    result = request(base, "/completion", payload)
                    if result.get("truncated"):
                        raise ValueError("Server reported truncation")
                    letter = result.get("content", "").strip()
                    record.update(response=result, seconds=time.perf_counter() - t0,
                                  letter=letter, probabilities=exact_probabilities(result, token_ids),
                                  status="ok" if letter in token_ids else "invalid")
                    if mode == "slot-restore":
                        timings = result.get("timings", {})
                        record["prefix_reuse_verified"] = (
                            timings.get("cache_n") == record["prefix_tokens"]
                            and timings.get("cache_n", 0) + timings.get("prompt_n", 0) == count)
                    if record["status"] != "ok":
                        record["interpretation"] = "invalid output, not negative"
                except Exception as exc:
                    record.update(status="error", error=str(exc), seconds=time.perf_counter() - t0)
                    save(dest, record)
                    raise
                save(dest, record)
                execution["completed_calls"] += 1
                save(out / "execution.json", execution)
                if execution["completed_calls"] % 32 == 0:
                    print(f"Completed {execution['completed_calls']}/{len(jobs)}; {job['case_id']} {job['mode']} {job['variant']}", flush=True)
            execution["status"] = "complete"
        except Exception as exc:
            execution.update(status="failed", error=repr(exc))
            raise
        finally:
            execution["wall_seconds"] = time.perf_counter() - started
            monitor.stop.set()
            thread.join(timeout=5)
            proc.terminate() if proc.poll() is None else None
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            save(out / "memory.json", {"samples": monitor.export(), "exceeded": monitor.exceeded, "error": monitor.error})
            execution["server_exit_code"] = proc.returncode
            if slot_dir is not None:
                state_file = slot_dir / SLOT_FILE
                execution["slot_state_bytes"] = state_file.stat().st_size if state_file.exists() else None
                state_file.unlink(missing_ok=True)
                try:
                    slot_dir.rmdir()
                    execution["slot_cleanup"] = "removed"
                except OSError as exc:
                    execution["slot_cleanup"] = f"left in place: {exc}"
            save(out / "execution.json", execution)
    report(out)


def file_digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def report(out: Path):
    plan, cases, jobs = load(out / "plan.json"), load(out / "cases.json"), load(out / "jobs.json")
    mode = plan.get("prefix_mode", "full")
    results = {p.stem: load(p) for p in sorted((out / "wire").glob("Q*.json"))}
    rows = []
    for case in cases:
        modes = sorted({(j["mode"], j["variant"]) for j in jobs if j["case_id"] == case["id"]})
        for input_mode, variant in modes:
            relevant = [j for j in jobs if j["case_id"] == case["id"] and (j["mode"], j["variant"]) == (input_mode, variant)]
            observed = [results[j["id"]] for j in relevant if j["id"] in results]
            complete = len(observed) == len(relevant) and all(r["status"] == "ok" for r in observed)
            selected = {r["role"] for r in observed if r.get("letter") == "A" and r["status"] == "ok"}
            fixed = {PREFIX + "code-auditor"}
            if any(h["path"].endswith((".ts", ".tsx")) for h in case["hunks"]):
                fixed.add("typescript-development:type-safety-auditor")
            if any(h["path"].endswith((".tsx", ".jsx")) for h in case["hunks"]):
                fixed.add("react-development:react-performance-optimizer")
            expected, negative = set(case["expected_roles"]), set(case.get("negative_roles", []))
            total = selected | fixed
            rows.append({"case_id": case["id"], "split": case.get("split", "historical"),
                         "mode": input_mode, "variant": variant, "complete": complete,
                         "calls": len(observed), "planned_calls": len(relevant),
                         "selected_model": sorted(selected), "selected_fixed": sorted(fixed),
                         "selected": sorted(total), "matched": sorted(total & expected),
                         "missing": sorted(expected - total) if complete else None,
                         "expected": sorted(expected), "negative": sorted(negative),
                         "negative_activations": sorted(total & negative),
                         "excess_partial_label_proxy": len(total - expected),
                         "abstentions": sum(r.get("letter") == "Z" for r in observed),
                         "seconds": sum(r.get("seconds", 0) for r in observed),
                         "activation_evidence": [{"role": r["role"], "window_id": r["window_id"], "response": r["id"]}
                                                 for r in observed if r.get("letter") == "A"],
                         "evidence_note": "Activation windows are locators, not validated defect citations."})
    samples = load(out / "memory.json")["samples"]
    summary = {"rows": rows, "prefix_mode": mode, "planned_calls": len(jobs), "observed_calls": len(results),
               "sampled_peak_combined_rss": max((s["server"]["rss"] + s["runner"]["rss"] for s in samples), default=None),
               "server_peak_rss": max((s["server"]["peak_rss"] for s in samples), default=None)}
    save(out / "scores.json", summary)
    lines = ["# Gutsy input and question follow-up", "", f"Prefix mode: {mode}.", "", "## Observed results", "",
             "| Case | Split | Input | Questions | Recall hits/support | Explicit negatives activated/support | Calls | Seconds | Complete |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| {r['case_id']} | {r['split']} | {r['mode']} | {r['variant']} | {len(r['matched'])}/{len(r['expected'])} | {len(r['negative_activations'])}/{len(r['negative'])} | {r['calls']} | {r['seconds']:.1f} | {r['complete']} |")
    lines += ["", "## Boundaries", "", "- Historical input packing changes only; handwritten V2 context is fixed, not authenticated map evidence.",
              "- All full-window source characters are retained. Windows may split functions and lose cross-window context.",
              "- New cases are real pinned source snippets, not independently verified production defects. Applicability labels are partial and authored by the coordinator.",
              "- Development and verification use distinct files in one project; neither establishes cross-project generalization.",
              "- Candidate wording and Yes/No options are one joint prompt treatment, frozen before outcomes. No claim isolates individual wording changes.",
              "- Model selections and inherited filename-based baseline selections are recorded separately. No added static cleanup rule.",
              "- A is activation, B is negative, Z is abstention; missing or invalid output is incomplete coverage.",
              "- Raw vocabulary probabilities are uncalibrated diagnostics. No top-k omission is interpreted as zero.",
              "- Union can improve recall by activating more reviewers. Excess against partial labels is not a measured false-positive rate.",
              "- No semantic citation validation, map integration, full-catalog, premise-positive or live downstream reviewer test was performed.",
              f"- Sampled combined runner/server peak RSS: {summary['sampled_peak_combined_rss']} bytes. OS caches and host are excluded; sampling is not a hard OS memory cap.",
              "- Exact prompts, raw responses, token counts, server timing/cache diagnostics, source hashes and memory samples are retained."]
    if mode == "slot-restore":
        lines.append("- Seconds count question calls only; prefix encoding, slot saves and restores are timed in COMPARISON.md.")
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2))


def compare_job(full: dict, slot: dict, near_tie: float) -> dict:
    """One question answered by full re-encoding and by slot restore."""
    deltas = {}
    for label in ("A", "B", "Z"):
        x, y = full["probabilities"].get(label), slot["probabilities"].get(label)
        deltas[label] = None if x is None or y is None else y - x
    known = [abs(value) for value in deltas.values() if value is not None]
    p_a, p_b = full["probabilities"].get("A"), full["probabilities"].get("B")
    margin = None if p_a is None or p_b is None else abs(p_a - p_b)
    return {"id": full["id"], "case_id": full["case_id"], "mode": full["mode"], "variant": full["variant"],
            "role": full["role"], "window_id": full["window_id"],
            "same_prompt": full["prompt_sha256"] == slot["prompt_sha256"],
            "full_letter": full["letter"], "slot_letter": slot["letter"],
            "flip": full["letter"] != slot["letter"],
            "full_probabilities": full["probabilities"], "slot_probabilities": slot["probabilities"],
            "deltas": deltas, "max_abs_delta": max(known) if known else None,
            "unknown_probability": len(known) < len(deltas),
            "reference_margin": margin, "near_tie": margin is not None and margin < near_tie,
            "prefix_reuse_verified": slot.get("prefix_reuse_verified") is True}


def memory_peaks(run_dir: Path) -> dict:
    memory = load(run_dir / "memory.json")
    samples = memory["samples"]
    return {"sampled_peak_combined_rss": max((s["server"]["rss"] + s["runner"]["rss"] for s in samples), default=None),
            "server_peak_rss": max((s["server"]["peak_rss"] for s in samples), default=None),
            "exceeded": memory["exceeded"], "error": memory["error"]}


def score_totals(rows: list[dict]) -> dict:
    totals = {}
    for row in rows:
        name = row["case_id"] if row["split"] == "historical" else row["split"]
        total = totals.setdefault(f"{name}, {row['mode']}, {row['variant']}",
                                  {"expected_found": 0, "expected": 0, "negatives_activated": 0, "negatives": 0})
        total["expected_found"] += len(row["matched"])
        total["expected"] += len(row["expected"])
        total["negatives_activated"] += len(row["negative_activations"])
        total["negatives"] += len(row["negative"])
    return totals


def compare(out: Path, reference: Path):
    """Pair every slot-restore answer with the full re-encoding reference and apply the frozen rule."""
    plan, ref_plan = load(out / "plan.json"), load(reference / "plan.json")
    if plan.get("prefix_mode") != "slot-restore" or ref_plan.get("prefix_mode", "full") != "full":
        raise ValueError("Compare a slot-restore run with its full re-encoding reference")
    if plan["hashes"] != ref_plan["hashes"] or plan.get("reference_run") != reference.relative_to(HERE).as_posix():
        raise ValueError("The runs do not share the frozen reference jobs")
    rule = plan["comparison_rule"]
    execution, ref_execution = load(out / "execution.json"), load(reference / "execution.json")
    jobs = load(out / "jobs.json")
    slot = {p.stem: load(p) for p in sorted((out / "wire").glob("Q*.json"))}
    full = {p.stem: load(p) for p in sorted((reference / "wire").glob("Q*.json"))}
    states = [load(p) for p in sorted((out / "states").glob("S*.json"))]
    valid = (len(slot) == len(full) == len(jobs)
             and all(r.get("status") == "ok" for r in (*slot.values(), *full.values())))
    rows = [compare_job(full[j["id"]], slot[j["id"]], rule["near_tie_margin"]) for j in jobs
            if full.get(j["id"], {}).get("status") == "ok" and slot.get(j["id"], {}).get("status") == "ok"]
    flips = sorted((r for r in rows if r["flip"]),
                   key=lambda r: 1.0 if r["reference_margin"] is None else r["reference_margin"])
    deltas = sorted(r["max_abs_delta"] for r in rows if r["max_abs_delta"] is not None)
    scores, ref_scores = load(out / "scores.json"), load(reference / "scores.json")
    ref_rows = {(r["case_id"], r["mode"], r["variant"]): r for r in ref_scores["rows"]}
    case_changes = []
    for row in scores["rows"]:
        before = ref_rows[(row["case_id"], row["mode"], row["variant"])]
        if row["selected_model"] != before["selected_model"]:
            case_changes.append({"case_id": row["case_id"], "mode": row["mode"], "variant": row["variant"],
                                 "added": sorted(set(row["selected_model"]) - set(before["selected_model"])),
                                 "removed": sorted(set(before["selected_model"]) - set(row["selected_model"])),
                                 "expected_found": [len(before["matched"]), len(row["matched"])],
                                 "expected": len(row["expected"]),
                                 "negatives_activated": [len(before["negative_activations"]), len(row["negative_activations"])],
                                 "negatives": len(row["negative"])})
    slot_memory, ref_memory = memory_peaks(out), memory_peaks(reference)
    question = sum(r.get("seconds", 0) for r in slot.values())
    restore = sum(r.get("restore", {}).get("seconds", 0) for r in slot.values())
    encode = sum(s["encode"]["seconds"] for s in states)
    saving = sum(s["save"]["seconds"] for s in states)
    ref_question = sum(r.get("seconds", 0) for r in full.values())
    slot_model = question + restore + encode + saving
    groups = {}
    for r in full.values():
        groups.setdefault(f"{r['case_id']} {r['mode']}", {"full": 0.0, "slot": 0.0})["full"] += r.get("seconds", 0)
    for r in slot.values():
        groups.setdefault(f"{r['case_id']} {r['mode']}", {"full": 0.0, "slot": 0.0})["slot"] += (
            r.get("seconds", 0) + r.get("restore", {}).get("seconds", 0))
    for s in states:
        groups.setdefault(f"{s['case_id']} {s['mode']}", {"full": 0.0, "slot": 0.0})["slot"] += (
            s["encode"]["seconds"] + s["save"]["seconds"])
    ref_wall, slot_wall = ref_execution.get("wall_seconds"), execution.get("wall_seconds")
    timing = {"reference_wall_seconds": ref_wall, "slot_wall_seconds": slot_wall,
              "wall_speedup": ref_wall / slot_wall if ref_wall and slot_wall else None,
              "reference_model_seconds": ref_question, "slot_model_seconds": slot_model,
              "model_time_speedup": ref_question / slot_model if slot_model else None,
              "slot_question_seconds": question, "slot_restore_seconds": restore,
              "slot_prefix_encode_seconds": encode, "slot_save_seconds": saving, "states_encoded": len(states),
              "mean_reference_question_seconds": ref_question / len(full) if full else None,
              "mean_slot_question_seconds": question / len(slot) if slot else None,
              "mean_slot_restore_seconds": restore / len(slot) if slot else None,
              "by_case_and_input": groups}
    repeat = None
    smoke_path = HERE / "runs/20261020-gutsy-slot-smoke/smoke.json"
    if smoke_path.exists():
        same = []
        for record in load(smoke_path)["records"]:
            s, f = slot.get(record["id"]), full.get(record["id"])
            if s and f and s.get("status") == "ok":
                delta = max(abs((s["probabilities"][k] or 0) - (f["probabilities"][k] or 0)) for k in "ABZ")
                same.append(s["letter"] == record["letter"] and delta == record["max_abs_prob_delta"])
        repeat = {"source": smoke_path.relative_to(HERE).as_posix(), "questions": len(same), "identical": sum(same),
                  "method": "letter and exact largest probability difference against the same reference"}
    checks = {
        "valid": valid,
        "prompts": len(rows) == len(jobs) and all(r["same_prompt"] for r in rows),
        "runtime": (execution.get("model_sha256") == ref_execution.get("model_sha256")
                    and execution.get("binary_sha256") == ref_execution.get("binary_sha256")
                    and runtime_signature(execution["args"]) == runtime_signature(ref_execution["args"])),
        "reuse": len(rows) == len(jobs) and all(r["prefix_reuse_verified"] for r in rows),
        "near_ties": all(r["near_tie"] for r in flips),
        "memory": (not slot_memory["exceeded"] and slot_memory["error"] is None
                   and slot_memory["sampled_peak_combined_rss"] is not None
                   and slot_memory["sampled_peak_combined_rss"] < plan["memory_limit_bytes"]),
    }
    adopted = all(checks.values())
    verdict = ("adopt slot restore as the prefix mechanism for later iterations" if adopted
               else "keep full re-encoding as the reference mechanism")
    near_tie_count = sum(r["near_tie"] for r in rows)
    p95 = deltas[min(len(deltas) - 1, math.ceil(0.95 * len(deltas)) - 1)] if deltas else None
    comparison = {"reference_run": plan["reference_run"], "slot_run": out.relative_to(HERE).as_posix(),
                  "rule": rule, "checks": checks, "adopted": adopted, "verdict": verdict,
                  "questions": len(rows), "identical_letters": len(rows) - len(flips),
                  "identical_probabilities": sum(r["full_probabilities"] == r["slot_probabilities"] for r in rows),
                  "flips": flips, "reference_near_ties": near_tie_count,
                  "max_abs_delta": deltas[-1] if deltas else None,
                  "median_abs_delta": statistics.median(deltas) if deltas else None, "p95_abs_delta": p95,
                  "unknown_probability_questions": sum(r["unknown_probability"] for r in rows),
                  "case_changes": case_changes,
                  "totals": {"full": score_totals(ref_scores["rows"]), "slot": score_totals(scores["rows"])},
                  "timing": timing, "memory": {"full": ref_memory, "slot": slot_memory},
                  "repeatability": repeat, "rows": rows}
    save(out / "comparison.json", comparison)
    labels = {"valid": "All planned calls valid in both runs", "prompts": "Identical frozen prompts",
              "runtime": "Same model, binary and server profile except the slot directory",
              "reuse": "Prefix reuse verified on every call",
              "near_ties": f"Every letter flip is a near tie (reference margin below {rule['near_tie_margin']})",
              "memory": "Memory bound respected"}

    def ratio(n, d):
        return f"{n}/{d} ({100 * n / d:.1f}%)" if d else f"{n}/0"

    def fmt(value, digits=1):
        return "n/a" if value is None else f"{value:.{digits}f}"

    lines = ["# Slot restore versus full re-encoding", "",
             f"Reference: `{plan['reference_run']}` (full re-encoding). Candidate: `{comparison['slot_run']}` (slot restore).",
             "", f"**Verdict: {verdict}.** The rule was frozen in `plan.json` before inference.", "",
             "## Checks", "", "| Check | Result |", "| --- | --- |"]
    lines += [f"| {labels[k]} | {'pass' if v else 'fail'} |" for k, v in checks.items()]
    lines += ["", "## Answers", "",
              f"- Identical letters: {ratio(comparison['identical_letters'], len(rows))}.",
              f"- Identical A/B/Z probabilities: {ratio(comparison['identical_probabilities'], len(rows))}.",
              f"- Largest absolute probability difference: {fmt(comparison['max_abs_delta'], 4)}; "
              f"median {fmt(comparison['median_abs_delta'], 4)}; 95th percentile {fmt(p95, 4)}.",
              f"- Reference answers inside the near-tie margin: {near_tie_count} of {len(rows)}.",
              f"- Questions with a probability outside the returned top 100: {comparison['unknown_probability_questions']}."]
    if flips:
        lines += ["", "| Question | Case | Input | Questions | Window | Role | Full | Slot | Reference P(A), P(B) | Reference margin |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in flips:
            pa, pb = r["full_probabilities"]["A"], r["full_probabilities"]["B"]
            lines.append(f"| {r['id']} | {r['case_id']} | {r['mode']} | {r['variant']} | {r['window_id']} | "
                         f"{r['role'].split(':')[-1]} | {r['full_letter']} | {r['slot_letter']} | "
                         f"{fmt(pa, 3)}, {fmt(pb, 3)} | {fmt(r['reference_margin'], 3)} |")
    lines += ["", "## Case-level selections", ""]
    if case_changes:
        lines += ["| Case | Input | Questions | Added | Removed | Expected found (full, slot) | Negatives activated (full, slot) |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        for c in case_changes:
            lines.append(f"| {c['case_id']} | {c['mode']} | {c['variant']} | "
                         f"{', '.join(x.split(':')[-1] for x in c['added']) or 'none'} | "
                         f"{', '.join(x.split(':')[-1] for x in c['removed']) or 'none'} | "
                         f"{c['expected_found'][0]}/{c['expected']}, {c['expected_found'][1]}/{c['expected']} | "
                         f"{c['negatives_activated'][0]}/{c['negatives']}, {c['negatives_activated'][1]}/{c['negatives']} |")
    else:
        lines.append(f"All {len(scores['rows'])} case, input and question rows select the same perspectives.")
    lines += ["", "| Rows | Expected found, full | Expected found, slot | Negatives activated, full | Negatives activated, slot |",
              "| --- | --- | --- | --- | --- |"]
    for name, a in comparison["totals"]["full"].items():
        b = comparison["totals"]["slot"][name]
        lines.append(f"| {name} | {a['expected_found']}/{a['expected']} | {b['expected_found']}/{b['expected']} | "
                     f"{a['negatives_activated']}/{a['negatives']} | {b['negatives_activated']}/{b['negatives']} |")
    lines += ["", "## Runtime", "", "| Measure | Full re-encoding | Slot restore |", "| --- | --- | --- |",
              f"| Wall time, seconds | {fmt(ref_wall)} | {fmt(slot_wall)} |",
              f"| Model time, seconds | {fmt(ref_question)} | {fmt(slot_model)} |",
              f"| Mean question call, seconds | {fmt(timing['mean_reference_question_seconds'], 2)} | {fmt(timing['mean_slot_question_seconds'], 2)} |",
              f"| Prefix encodings | none | {len(states)}, {fmt(encode)} s |",
              f"| Slot saves and restores, seconds | none | {fmt(saving + restore)} |",
              "", f"Speedup: {fmt(timing['wall_speedup'], 2)}x wall time, {fmt(timing['model_time_speedup'], 2)}x model time.",
              "", "| Case and input | Full, seconds | Slot, seconds | Speedup |", "| --- | --- | --- | --- |"]
    for name, g in groups.items():
        lines.append(f"| {name} | {fmt(g['full'])} | {fmt(g['slot'])} | {fmt(g['full'] / g['slot'] if g['slot'] else None, 2)}x |")
    lines += ["", "## Memory", "", "| Measure | Full re-encoding | Slot restore |", "| --- | --- | --- |",
              f"| Sampled peak, server and runner, bytes | {ref_memory['sampled_peak_combined_rss']} | {slot_memory['sampled_peak_combined_rss']} |",
              f"| Server lifetime peak working set, bytes | {ref_memory['server_peak_rss']} | {slot_memory['server_peak_rss']} |"]
    if repeat:
        lines += ["", f"Cross-process repeatability: {repeat['identical']} of {repeat['questions']} slot answers from the "
                      f"earlier smoke test were reproduced exactly ({repeat['method']})."]
    lines += ["", "## Boundaries", "",
              "- Full re-encoding is the frozen reference, not ground truth. Both paths process the same tokens; slot restore "
              "encodes the state prefix as its own prompt, so prompt batches end at different positions and floating-point "
              "results differ slightly. A decision whose two options are nearly tied can flip under either path.",
              "- If slot restore is adopted, results are compared only within one prefix mode. This run is the slot-mode "
              "baseline for the same 496 questions.",
              "- The near-tie margin was fixed from the 16-question smoke test, whose questions are part of this comparison.",
              "- One machine, binary, model, thread count and server profile. Raw probabilities are uncalibrated."]
    (out / "COMPARISON.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: comparison[k] for k in ("verdict", "checks", "questions", "identical_letters",
                                                  "identical_probabilities", "max_abs_delta")}
                     | {"flips": len(flips), "case_changes": len(case_changes), "timing": {k: v for k, v in timing.items() if k != "by_case_and_input"}}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "prepare-slot", "run", "report", "compare"))
    parser.add_argument("--out", required=True, help="Run directory relative to this benchmark")
    parser.add_argument("--reference", help="Complete full re-encoding run, for prepare-slot and compare")
    parser.add_argument("--prefix-mode", choices=("slot-restore", "full"), default="slot-restore",
                        help="For prepare: slot restore (adopted default) or full re-encoding for a new reference")
    args = parser.parse_args()

    def inside(path: str) -> Path:
        target = (HERE / path).resolve()
        if not target.is_relative_to(HERE / "runs"):
            parser.error("Run directories must be inside this benchmark's runs directory")
        return target

    target = inside(args.out)
    if args.action in ("prepare-slot", "compare"):
        if not args.reference:
            parser.error(f"{args.action} requires --reference")
        {"prepare-slot": prepare_slot, "compare": compare}[args.action](target, inside(args.reference))
    elif args.action == "prepare":
        prepare(target, args.prefix_mode)
    else:
        {"run": run, "report": report}[args.action](target)
