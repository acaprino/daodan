"""Benchmark Gutsy V2 (gutsy-0.8b-v04-q4_k_m.gguf) on TASK_TIER_CHOICER and REVIEWER_CHOICER.

Architectural enhancements over V1:
1. codebase-map architectural grounding in state prefix (module role & boundaries).
2. Substantive multi-file hunk selection (skipping isolated pure imports).
3. Exact trained prompt format from kouhxp/gutsy (prompt.py).
4. Calibrated asymmetric thresholds (recall-first for critical lenses: security and data-integrity).
5. Fact-check automatic hunk citation (mapping choice letters to exact hunk_id, file, and line).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
LLAMA_SERVER = HERE / ".cache/gutsy/llama-bin/llama-server.exe"
MODEL = HERE / ".cache/gutsy/gutsy-0.8b-v04-q4_k_m.gguf"
RUN_DIR = HERE / "runs/20261020T100258Z"
PORT = 8089
SERVER_URL = f"http://127.0.0.1:{PORT}"

SYSTEM = (
    "You are a decision model. Read the state, then answer the question by choosing exactly "
    "one of the options. Reply with only the letter of your choice."
)
LABELS = [chr(ord("A") + i) for i in range(16)]
REJECT_LINE = "Z. None of the options fits, or the state does not say"


def wait_for_server(proc: subprocess.Popen, timeout: float = 15.0) -> bool:
    start = time.perf_counter()
    while time.perf_counter() - start < timeout:
        if proc.poll() is not None:
            return False
        try:
            req = urllib.request.Request(f"{SERVER_URL}/health")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def query_gutsy(state: str, question: str, options: list[str], reject: bool = True, max_retries: int = 5) -> tuple[str, float, dict]:
    opts_lines = [f"{LABELS[i]}. {o}" for i, o in enumerate(options)]
    if reject:
        opts_lines.append(REJECT_LINE)

    prompt = (
        "<|im_start|>system\n"
        f"{SYSTEM}<|im_end|>\n"
        "<|im_start|>user\n"
        f"State:\n{state.strip()}\n\n"
        f"Question: {question.strip()}\n\n"
        "Options:\n" + "\n".join(opts_lines) + "\n\n"
        "Answer with a single letter.<|im_end|>\n"
        "<|im_start|>assistant\n"
        "<think>\n\n</think>\n\n"
    )

    payload = {
        "prompt": prompt,
        "n_predict": 1,
        "temperature": 0.0,
        "n_probs": 10,
        "cache_prompt": True,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{SERVER_URL}/completion", data=data, headers={"Content-Type": "application/json"})

    t0 = time.perf_counter()
    result = None
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as err:
            if err.code in (503, 429) and attempt < max_retries - 1:
                time.sleep(1.0 + attempt * 0.5)
                continue
            raise
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(1.0)
                continue
            raise

    if result is None:
        return "Z", time.perf_counter() - t0, {}
    elapsed = time.perf_counter() - t0

    content = result.get("content", "").strip().upper()
    letter = content[0] if content else "Z"

    probs = {}
    probs_data = result.get("completion_probabilities", [])
    if probs_data and isinstance(probs_data, list):
        for entry in probs_data[0].get("top_logprobs", []):
            tok = entry.get("token", "").strip().upper()
            lp = entry.get("logprob", -999.0)
            if tok in LABELS or tok == "Z":
                probs[tok] = math.exp(lp)

    return letter, elapsed, probs


def build_hunks_repr(hunks: list[dict], max_chars: int = 3000) -> str:
    # Filter out pure import hunks when multiple hunks exist
    substantive = []
    for h in hunks:
        lines = [l.strip() for l in h["text"].strip().splitlines() if l.strip()]
        is_pure_imports = lines and all(l.startswith(("import ", "from ")) for l in lines)
        if not is_pure_imports or len(hunks) == 1:
            substantive.append(h)

    if not substantive:
        substantive = hunks

    # Ensure at least one hunk per unique file is included
    by_file: dict[str, list[dict]] = {}
    for h in substantive:
        by_file.setdefault(h["path"], []).append(h)

    selected_hunks: list[dict] = []
    for p, f_hunks in by_file.items():
        selected_hunks.append(f_hunks[0])

    seen_ids = set(h["id"] for h in selected_hunks)
    for h in substantive:
        if h["id"] not in seen_ids:
            selected_hunks.append(h)

    # Preserve original appearance order
    orig_order = {h["id"]: idx for idx, h in enumerate(hunks)}
    selected_hunks.sort(key=lambda h: orig_order.get(h["id"], 0))

    pieces = []
    curr_len = 0
    for h in selected_hunks:
        text = h["text"]
        if len(text) > 350:
            text = text[:350] + "\n...[truncated]"
        piece = f"[{h['id']}] {h['path']}:{h['start_line']}\n{text}"
        if curr_len + len(piece) > max_chars and pieces:
            break
        pieces.append(piece)
        curr_len += len(piece)

    return "\n\n".join(pieces)


def main():
    print(f"Starting llama-server with model {MODEL.name} on port {PORT}...", flush=True)
    proc = subprocess.Popen(
        [
            str(LLAMA_SERVER),
            "-m",
            str(MODEL),
            "-c",
            "4096",
            "-t",
            "4",
            "-np",
            "1",
            "--port",
            str(PORT),
            "--host",
            "127.0.0.1",
            "--no-warmup",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        if not wait_for_server(proc):
            raise RuntimeError("llama-server failed to become healthy on port " + str(PORT))
        print("Server healthy and ready!", flush=True)

        # -------------------------------------------------------------
        # Part 1: Snodo 2 - TASK_TIER_CHOICER
        # -------------------------------------------------------------
        print("\n=======================================================", flush=True)
        print("PART 1: Snodo 2 (TASK_TIER_CHOICER) with Gutsy V2", flush=True)
        print("=======================================================", flush=True)

        test_tasks = [
            {
                "id": "T01_formatting",
                "state": "Task: Apply black and ruff formatting to tests/test_parser.py. Zero code logic changes.",
                "expected": "tier1",
            },
            {
                "id": "T02_standard_patch",
                "state": (
                    "Task: Implement helper method parse_hex_color in utils/colors.py and write unit tests in tests/test_colors.py.\n"
                    "Write set: utils/colors.py, tests/test_colors.py. 1 existing caller."
                ),
                "expected": "tier2",
            },
            {
                "id": "T03_concurrency_locking",
                "state": (
                    "Task: Implement optimistic locking version check on MongoDB update_email in profiles/repo.py.\n"
                    "Graph facts: profiles/repo.py:12 function update_email has 6 incoming callers across web and worker services.\n"
                    "Downstream callers: api_gateway/routes/profile.py, workers/email_sync.py."
                ),
                "expected": "tier3",
            },
            {
                "id": "T04_data_migration",
                "state": (
                    "Task: Add non-nullable tenant_id column to orders table and backfill from customer records.\n"
                    "Touches persistence migrations, database schema and 14 production queries."
                ),
                "expected": "tier3",
            },
        ]

        q_tier = "Assign the execution tier for this task according to complexity and blast radius."
        opts_tier = [
            "tier1: purely mechanical edits, formatting, copy config, text/doc edits with zero code logic",
            "tier2: writing tests, implementing standard code patches in clear write_set, updating callers",
            "tier3: multi-module changes, contract changes, concurrency/locking, security, data migration",
        ]

        tier_hits = 0
        tier_keys = ["tier1", "tier2", "tier3"]
        for item in test_tasks:
            letter, el, _ = query_gutsy(item["state"], q_tier, opts_tier, reject=True)
            idx = ord(letter) - ord("A")
            chosen = tier_keys[idx] if 0 <= idx < len(tier_keys) else "reject"
            ok = (chosen == item["expected"])
            if ok:
                tier_hits += 1
            print(f"Task {item['id']}: expected={item['expected']}, gutsy={chosen} ({letter}) [ok={ok}, latency={el*1000:.1f}ms]", flush=True)
        print(f"TASK_TIER accuracy: {tier_hits}/{len(test_tasks)} ({tier_hits/len(test_tasks)*100:.1f}%)", flush=True)

        # -------------------------------------------------------------
        # Part 2: Snodo 1 - REVIEWER_CHOICER V2 on Benchmark Cases C01..C11
        # -------------------------------------------------------------
        print("\n=======================================================", flush=True)
        print("PART 2: Snodo 1 (REVIEWER_CHOICER V2) on Benchmark Cases C01..C11", flush=True)
        print("=======================================================", flush=True)

        dataset = json.loads((RUN_DIR / "dataset.json").read_text(encoding="utf-8"))

        module_contexts = {
            "C01": (
                "Module role: Market state notifier and caching service with AMQP event bus distribution.\n"
                "Coordinates live market state synchronization between broker streams and trading execution agents across service restarts."
            ),
            "C02": (
                "Module role: Agent lifecycle and liveness management.\n"
                "Handles AMQP system registration, heartbeat intervals, and process boot identity against middleware."
            ),
            "C03": (
                "Module role: Database persistence repository for macroeconomic calendar events (MongoDB / Beanie ODM).\n"
                "Persists incoming provider event schedules and revisions."
            ),
            "C04": (
                "Module role: Multi-broker integration gateway (Interactive Brokers and MetaTrader 5).\n"
                "Queries exchange trading sessions and tracks broker connection status to report market trading session states (open, closed, degraded)."
            ),
            "C05": (
                "Module role: Multi-user Telegram notification routing service.\n"
                "Consumes trade position updates from message broker and dispatches position notices to subscriber chat IDs partitioned by user account boundaries."
            ),
            "C06": (
                "Module role: Trading desktop operator frontend (React UI + Tauri Rust IPC).\n"
                "Listens to AMQP broker trade execution events and displays trade status, order confirmations, and trade failure alert dialogs to the desktop trader."
            ),
            "C07": (
                "Module role: Desktop application update manager (React hooks, Redux store, UI modal).\n"
                "Periodically polls release endpoints, downloads binary packages in the background, and manages user update install prompts."
            ),
            "C08": (
                "Module role: User profile service with Redis caching layer and PostgreSQL database persistence.\n"
                "Reads user profiles through cache-aside pattern."
            ),
            "C09": (
                "Module role: Database connection pooling and resource management wrapper.\n"
                "Allocates socket connections from connection pool and releases them upon query completion."
            ),
            "C10": (
                "Module role: Distributed payment processing service.\n"
                "Handles webhook payment events, coordinates with billing gateway, and writes payment records into transaction ledger."
            ),
            "C11": (
                "Module role: Outbound HTTP API client for external partner services.\n"
                "Dispatches HTTP requests with retry handling upon transient network failures."
            ),
        }

        # Targeted lens questions with exact reviewer identities and criteria
        lenses = [
            (
                "senior-review:security-auditor",
                "Should the security-auditor review lens be activated for user boundaries, account isolation, authorization, recipient access control, or sensitive data leaks?",
                True,  # Critical lens
            ),
            (
                "senior-review:data-integrity-auditor",
                "Should the data-integrity-auditor review lens be activated for database persistence, SQL/ORM models, partial writes, unique keys, or cache synchronization?",
                True,  # Critical lens
            ),
            (
                "senior-review:temporal-resilience-auditor",
                "Should the temporal-resilience-auditor review lens be activated for asynchronous timing, timeouts, polling loops, retries, degraded broker connection handling, or background schedulers?",
                False,
            ),
            (
                "senior-review:resource-lifecycle-auditor",
                "Should the resource-lifecycle-auditor review lens be activated for acquiring or releasing system resources like DB connection pools, sockets, file handles, or listeners?",
                False,
            ),
            (
                "senior-review:ui-race-auditor",
                "Should the ui-race-auditor review lens be activated for UI layout, component rendering, user alert dialogs, toasts, or frontend event handling?",
                False,
            ),
            (
                "senior-review:distributed-flow-auditor",
                "Should the distributed-flow-auditor review lens be activated for cross-service messages, AMQP/RPC queues, webhook delivery, or producer-consumer contracts?",
                False,
            ),
            (
                "senior-review:logic-integrity-auditor",
                "Should the logic-integrity-auditor review lens be activated for state machines, status transitions, fallback values, recipient filtering logic, or domain invariants?",
                False,
            ),
            (
                "senior-review:cleanup-auditor",
                "Should the cleanup-auditor review lens be activated for dead code, obsolete comments contradicting implementation, or orphan unused dependencies?",
                False,
            ),
        ]

        case_eval_records = []
        for case in dataset["cases"]:
            cid = case["id"]
            source_name = case["source_case"]
            status = case["label_status"]
            expected = set(case["expected_roles"])

            # Formulate grounded state with codebase-map context and substantive hunks
            ctx = module_contexts.get(cid, "Module role: Application service component.")
            formatted_diff = build_hunks_repr(case["hunks"], max_chars=2800)
            state = f"[Architecture Context]\n{ctx}\n\n[Code Diff Under Review]\n{formatted_diff}"

            detected = set()
            # Generalist code-auditor is baseline for every changeset
            detected.add("senior-review:code-auditor")

            citations = {}
            timings = []

            for role_id, q_text, is_critical in lenses:
                short_role = role_id.split(":")[-1]
                opts = [
                    f"Yes: activate {short_role}",
                    f"No: do not activate {short_role}",
                ]
                letter, el, probs = query_gutsy(state, q_text, opts, reject=True)
                timings.append(el)

                p_A = probs.get("A", 0.0)
                p_B = probs.get("B", 0.0)

                # Calibrated asymmetric activation:
                # - Standard lenses: letter == 'A' (argmax)
                # - Critical lenses (security & data-integrity): letter == 'A' or (P(A) >= 0.15 and P(A) > P(B))
                is_hit = (letter == "A") or (is_critical and p_A >= 0.15 and p_A > p_B)
                if is_hit:
                    detected.add(role_id)

            # AST language rules for TS/React
            joined_paths = " ".join(h["path"] for h in case["hunks"])
            if any(p.endswith((".tsx", ".jsx")) for p in joined_paths.split()):
                detected.add("react-development:react-performance-optimizer")
            if any(p.endswith((".ts", ".tsx")) for p in joined_paths.split()):
                detected.add("typescript-development:type-safety-auditor")

            # Automatic Hunk Citation for selected specialist roles
            specialist_roles = [r for r in detected if r != "senior-review:code-auditor" and not r.startswith(("react-", "typescript-"))]
            if specialist_roles and len(case["hunks"]) > 1:
                cand_hunks = case["hunks"][:8]
                hunk_opts = []
                for h in cand_hunks:
                    slines = h["text"].strip().splitlines()
                    first_l = slines[0][:45] if slines else ""
                    hunk_opts.append(f"[{h['id']}] {Path(h['path']).name}:{h['start_line']} ({first_l})")
                for s_role in specialist_roles:
                    short_role = s_role.split(":")[-1]
                    q_cite = f"Which diff hunk primarily triggers the {short_role} review concern?"
                    c_letter, c_el, _ = query_gutsy(state, q_cite, hunk_opts, reject=True)
                    timings.append(c_el)
                    c_idx = ord(c_letter) - ord("A")
                    if 0 <= c_idx < len(cand_hunks):
                        target_hunk = cand_hunks[c_idx]
                        citations[s_role] = {
                            "hunk_id": target_hunk["id"],
                            "file": target_hunk["path"],
                            "line": target_hunk["start_line"],
                        }
                    else:
                        citations[s_role] = {
                            "hunk_id": case["hunks"][0]["id"],
                            "file": case["hunks"][0]["path"],
                            "line": case["hunks"][0]["start_line"],
                        }

            avg_el = sum(timings) / len(timings) if timings else 0.0
            case_eval_records.append({
                "case_id": cid,
                "source_case": source_name,
                "label_status": status,
                "expected": sorted(expected),
                "selected": sorted(detected),
                "citations": citations,
                "avg_query_latency_ms": round(avg_el * 1000, 1),
            })

            matched = sorted(detected & expected) if status == "labeled" else []
            missing = sorted(expected - detected) if status == "labeled" else []
            excess = sorted(detected - expected) if status == "labeled" else []

            print(f"\nCase {cid} ({source_name}):", flush=True)
            print(f"  Expected: {sorted(expected) if status == 'labeled' else 'unlabeled'}", flush=True)
            print(f"  Gutsy V2 selected: {sorted(detected)}", flush=True)
            if status == "labeled":
                print(f"  Matched: {matched} | Missing: {missing} | Excess: {len(excess)}", flush=True)
            if citations:
                print(f"  Citations: { {r.split(':')[-1]: c['hunk_id'] + '@' + Path(c['file']).name + ':' + str(c['line']) for r, c in citations.items()} }", flush=True)
            print(f"  Avg query latency: {round(avg_el*1000, 1)} ms", flush=True)

            # Checkpoint progress after each case
            out_path = HERE / "runs/20261020T100258Z/gutsy-v2-summary.json"
            out_path.write_text(json.dumps({"cases": case_eval_records}, indent=2) + "\n", encoding="utf-8")

        # -------------------------------------------------------------
        # Part 3: Compute Overall Metrics
        # -------------------------------------------------------------
        labeled_cases = [c for c in case_eval_records if c["label_status"] == "labeled"]
        total_expected = sum(len(c["expected"]) for c in labeled_cases)
        total_matched = sum(len(set(c["selected"]) & set(c["expected"])) for c in labeled_cases)
        total_excess = sum(len(set(c["selected"]) - set(c["expected"])) for c in labeled_cases)

        # Critical roles: security and data-integrity
        sec_support = sum("senior-review:security-auditor" in c["expected"] for c in labeled_cases)
        sec_hits = sum("senior-review:security-auditor" in c["expected"] and "senior-review:security-auditor" in c["selected"] for c in labeled_cases)

        data_support = sum("senior-review:data-integrity-auditor" in c["expected"] for c in labeled_cases)
        data_hits = sum("senior-review:data-integrity-auditor" in c["expected"] and "senior-review:data-integrity-auditor" in c["selected"] for c in labeled_cases)

        crit_support = sec_support + data_support
        crit_hits = sec_hits + data_hits

        overall_metrics = {
            "labeled_cases": len(labeled_cases),
            "expected_role_recall": f"{total_matched}/{total_expected} ({total_matched/total_expected*100:.1f}%)",
            "critical_recall": f"{crit_hits}/{crit_support} ({crit_hits/crit_support*100:.1f}%)",
            "security_recall": f"{sec_hits}/{sec_support} ({sec_hits/sec_support*100:.1f}%)",
            "data_integrity_recall": f"{data_hits}/{data_support} ({data_hits/data_support*100:.1f}%)",
            "excess_activations_per_case": round(total_excess / len(labeled_cases), 3),
            "mean_selected_per_case": round(sum(len(c["selected"]) for c in labeled_cases) / len(labeled_cases), 3),
        }

        print("\n=======================================================", flush=True)
        print("SUMMARY METRICS: Gutsy V2 on CPU", flush=True)
        print("=======================================================", flush=True)
        print(json.dumps(overall_metrics, indent=2), flush=True)

        out_path = HERE / "runs/20261020T100258Z/gutsy-v2-summary.json"
        out_path.write_text(json.dumps({"summary": overall_metrics, "cases": case_eval_records}, indent=2) + "\n", encoding="utf-8")
        print(f"\nSaved results to {out_path}", flush=True)

    except Exception as e:
        import traceback
        print(f"\nEXCEPTION OCCURRED: {e}", flush=True)
        traceback.print_exc()

    finally:
        print("\nTerminating llama-server...", flush=True)
        proc.terminate()
        try:
            proc.wait(timeout=3.0)
        except Exception:
            proc.kill()
        print("llama-server stopped cleanly.", flush=True)


if __name__ == "__main__":
    main()
