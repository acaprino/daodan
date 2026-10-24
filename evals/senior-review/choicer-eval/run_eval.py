# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "torch==2.14.0",
#   "transformers==5.0.0",
#   "safetensors>=0.5",
#   "numpy>=1.26",
# ]
# ///
"""Prepare, execute and rescore the offline reviewer-routing pilot.

Preparation/scoring work with ordinary Python and do not import the model runtime.
Creating a uv environment, downloading weights and paid calls are separate gates.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import string
import time
import urllib.request

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]
JULIA_REPO = "SupersonicLabs/Julia-1"
JULIA_REVISION = "a85b127321d580d65176c89ced8273f305745d85"
JULIA_WEIGHT_SHA256 = "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"
THRESHOLD = 0.5


def digest(value: bytes | str) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def confined(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = BASE / candidate
    candidate = candidate.resolve()
    if not candidate.is_relative_to(BASE):
        raise ValueError(f"Output escapes benchmark directory: {candidate}")
    return candidate


def write_text(path: str | Path, content: str, *, freeze: bool = False) -> None:
    target = confined(path)
    if target.exists():
        if target.read_text(encoding="utf-8") == content:
            return
        if freeze:
            raise ValueError(f"Frozen evidence differs: {target}. Start a new run.")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def write_json(path: str | Path, value: object, *, freeze: bool = False) -> None:
    write_text(path, encoded(value), freeze=freeze)


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def hardware() -> dict:
    info = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": platform.processor() or None,
        "logical_cpus": os.cpu_count(),
        "python": platform.python_version(),
        "ram_bytes": None,
        "gpu": "unused; CPU protocol",
    }
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                info["cpu_model"] = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    return info


def initialize(run: Path) -> dict:
    run = confined(run)
    path = run / "metadata.json"
    if path.exists():
        return read_json(path)
    metadata = {
        "schema": "choicer-eval/v1",
        "generated_at": utc_now(),
        "run_path": run.relative_to(REPO).as_posix(),
        "hardware": hardware(),
        "threshold": THRESHOLD,
        "threshold_protocol": "Fixed at 0.5 before inference; curve is descriptive, never tuned.",
        "models": {},
        "gates": [
            {"gate": "uv environment", "status": "not authorized / not created"},
            {"gate": "Julia weights", "status": "not authorized / not downloaded"},
            {"gate": "paid LLM baseline", "status": "not authorized / not called"},
        ],
        "anomalies": [
            "The verbatim REVIEWER_CHOICER returns selections, not probabilities. LLM ECE is unavailable.",
            "The full-review LLM baseline cannot become a single-choice control without changing its prompt; it is reused for comparison with both local variants.",
            "No case supplies symbol cards. Graph evidence is unavailable, not inferred.",
            "tier_router.py named in the design is absent from this checkout; this evaluates the specified prompt, not a proved installed routing implementation.",
            "Missing DO NOT TRIGGER WHEN is encoded as an empty false criterion and reported, never paraphrased or invented.",
            "Julia advertises a separate 48-token option limit. Exact criteria that exceed it are recorded as failures, not truncated.",
        ],
        "provenance": {"entry_sha256": digest(Path(__file__).read_bytes())},
    }
    write_json(path, metadata)
    return metadata


def required_inputs(run: Path) -> tuple[dict, dict, dict]:
    return tuple(read_json(run / name) for name in ("dataset.json", "catalog.json", "prompts.json"))


def reviewer_roles(catalog: dict) -> list[dict]:
    roles = [role for role in catalog["roles"] if role["is_reviewer"]]
    if len({r["id"] for r in roles}) != len(roles):
        raise ValueError("Duplicate reviewer IDs")
    if any(not r["trigger_when"] for r in roles):
        raise ValueError("A reviewer lacks TRIGGER WHEN; cannot invent a positive criterion")
    return roles


def hunk_state(hunk: dict) -> str:
    lines = hunk["text"].splitlines()
    numbered = "\n".join(
        f"{hunk['path']}:{hunk['start_line'] + offset} {line}"
        for offset, line in enumerate(lines)
    )
    state = f"[{hunk['id']}]\n{numbered}"
    if hunk.get("symbol_cards"):
        state += "\nSYMBOL CARDS:\n" + encoded(hunk["symbol_cards"])
    return state


def check_leakage(request: dict, case: dict) -> None:
    text = encoded(request).lower()
    for forbidden in ("expected dimension", "ground truth", "scoring notes", case["source_case"].lower()):
        if forbidden in text:
            raise ValueError(f"Model input contains prohibited case metadata: {forbidden}")


def build_requests(dataset: dict, catalog: dict, prompts: dict, impl: str, variant: str) -> list[dict]:
    roles = reviewer_roles(catalog)
    requests = []
    if impl == "llm" and variant != "noul":
        raise ValueError("Verbatim full REVIEWER_CHOICER is a multilabel baseline; llm/choice would change the protocol")
    for case in dataset["cases"]:
        if not case["hunks"]:
            continue
        if impl == "llm":
            template = prompts["REVIEWER_CHOICER"]["text"]
            rendered_catalog = "\n\n".join(
                f"{r['id']}\nTRIGGER WHEN: {r['trigger_when']}\n"
                f"DO NOT TRIGGER WHEN: {r['do_not_trigger_when'] or ''}"
                for r in roles
            )
            prompt = string.Template(template).substitute(
                mode="full", intent_and_docs="Not supplied.",
                # The 2026-10-20 spec rewrite renamed $graph_facts to
                # $code_graph_facts. Supply both names so the live closed-spec
                # template and frozen historical templates both render unchanged.
                graph_facts=encoded([card for h in case["hunks"] for card in h.get("symbol_cards", [])]),
                code_graph_facts=encoded([card for h in case["hunks"] for card in h.get("symbol_cards", [])]),
                tool_results="No deterministic checks were supplied.",
                reviewers_catalog=rendered_catalog,
                diff_content="\n\n".join(hunk_state(h) for h in case["hunks"]),
            )
            request = {
                "impl": impl, "variant": variant, "case_id": case["id"],
                "hunk_id": None, "prompt": prompt,
                "template_sha256": digest(template),
            }
            check_leakage(request, case)
            requests.append(request)
            continue
        for hunk in case["hunks"]:
            if variant == "noul":
                questions = {
                    r["id"]: {
                        "type": "noul",
                        "instructions": "Does this hunk satisfy the reviewer's TRIGGER WHEN?",
                        "criteria": {"true": r["trigger_when"], "false": r["do_not_trigger_when"] or ""},
                    } for r in roles
                }
            else:
                questions = {
                    "reviewer": {
                        "type": "choice",
                        "instructions": "Which reviewer's TRIGGER WHEN is best satisfied by this hunk?",
                        "criteria": {
                            r["id"]: r.get(
                                "choice_description",
                                f"TRIGGER WHEN: {r['trigger_when']}\nDO NOT TRIGGER WHEN: {r['do_not_trigger_when'] or ''}",
                            )
                            for r in roles
                        },
                    },
                }
            request = {
                "impl": impl, "variant": variant, "case_id": case["id"],
                "hunk_id": hunk["id"], "state": hunk_state(hunk), "questions": questions,
            }
            check_leakage(request, case)
            requests.append(request)
    return requests


def request_name(request: dict) -> str:
    return f"{request['case_id']}-{request['hunk_id'] or 'batch'}"


def prepare(run: Path, impl: str, variant: str) -> tuple[list[dict], dict, dict]:
    dataset, catalog, prompts = required_inputs(run)
    requests = build_requests(dataset, catalog, prompts, impl, variant)
    for request in requests:
        request["request_sha256"] = digest(encoded(request))
        write_json(run / "requests" / impl / variant / f"{request_name(request)}.json", request, freeze=True)
    return requests, dataset, catalog


def verified_results(run: Path, dataset: dict, catalog: dict, prompts: dict) -> list[dict]:
    """Reject results whose frozen input no longer matches this run's evidence."""
    records = [read_json(path) for path in sorted((run / "results").rglob("*.json"))]
    expected = {}
    for impl, variant in {(record["impl"], record["variant"]) for record in records}:
        for request in build_requests(dataset, catalog, prompts, impl, variant):
            expected[impl, variant, request_name(request)] = digest(encoded(request))
    for record in records:
        name = request_name(record)
        key = record["impl"], record["variant"], name
        request = read_json(run / "requests" / key[0] / key[1] / f"{name}.json")
        saved_digest = request.pop("request_sha256")
        if (
            key not in expected or digest(encoded(request)) != saved_digest
            or saved_digest != expected[key] or record.get("request_sha256") != saved_digest
        ):
            raise ValueError(f"Result/input/catalog binding failed: {key}")
        raw = record.get("raw_output")
        if isinstance(raw, dict) and "request_sha256" in raw and raw["request_sha256"] != saved_digest:
            raise ValueError(f"Capture/input binding failed: {key}")
    return records


def validate_llm(
    raw: dict, case: dict, catalog: dict, warnings: list[str] | None = None,
) -> list[str]:
    """Validate each citation, then return activation IDs as a set in source order."""
    if not isinstance(raw, dict) or raw.get("mode") != "full" or not isinstance(raw.get("selected"), list):
        raise ValueError("Invalid full-review response schema")
    warnings = warnings if warnings is not None else []
    known = {role["id"] for role in reviewer_roles(catalog)}
    hunks = {h["id"]: h for h in case["hunks"]}
    selected = []
    for entry in raw["selected"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("role"), str) or entry["role"] not in known:
            raise ValueError("Unknown reviewer")
        if entry.get("tier") not in ("tier2", "tier3") or entry.get("effort") not in ("medium", "high"):
            raise ValueError("Invalid reviewer tier or effort")
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip() or len(reason.split()) > 15:
            raise ValueError("Missing reason or reason exceeds 15 words")
        citation = entry.get("trigger_line")
        locator = re.fullmatch(r"\[(H\d+)\]\s+(.+)", citation) if isinstance(citation, str) else None
        if not locator or locator[1] not in hunks:
            raise ValueError("Missing or unrecognized hunk citation")
        hunk = hunks[locator[1]]
        # Side is an explicit token in the frozen prompt, never part of the path.
        # Anchor the exact supplied path, including spaces, rather than stripping
        # arbitrary prefixes or accepting a suffix that happens to name a file.
        coordinate = re.fullmatch(
            rf"(?:(base|candidate)\s+)?{re.escape(hunk['path'])}:(\d+)\s+(.+)",
            locator[2],
        )
        if not coordinate:
            raise ValueError("Citation is outside the supplied hunk")
        side, line_number, snippet = coordinate.groups()
        supplied_side = hunk.get("side")
        if supplied_side is not None:
            if supplied_side not in ("base", "candidate") or side != supplied_side:
                raise ValueError("Citation side does not match the supplied evidence side")
        elif side is not None:
            warnings.append(
                f"{locator[1]}: citation side '{side}' is not independently verified; "
                "the supplied evidence omitted a side binding."
            )
        else:
            warnings.append(
                f"{locator[1]}: citation omits the prompt's base/candidate token; "
                "the supplied evidence also omitted a side binding."
            )
        offset = int(line_number) - hunk["start_line"]
        lines = hunk["text"].splitlines()
        if not 0 <= offset < len(lines):
            raise ValueError("Citation is outside the supplied hunk")
        if not snippet.strip() or snippet.strip() not in lines[offset]:
            raise ValueError("Citation snippet is absent at the cited line")
        if entry["role"] in selected:
            warnings.append(
                f"{entry['role']}: repeated selection with a separately validated citation; "
                "counted once in the activation set."
            )
        else:
            selected.append(entry["role"])
    return selected


def base_record(request: dict) -> dict:
    return {
        key: request[key] for key in ("impl", "variant", "case_id", "hunk_id", "request_sha256")
    } | {
        "status": "blocked", "selected": [], "probabilities": None,
        "wall_seconds": None, "cpu_seconds": None, "phase": "unknown", "usage": None,
        "raw_output": None, "validation_warnings": [],
    }


def imported_llm(run: Path, args: argparse.Namespace, requests: list[dict], dataset: dict, catalog: dict) -> None:
    source = Path(args.responses).resolve()
    for request in requests:
        path = source / f"{request_name(request)}.json"
        if not path.is_file():
            continue
        capture = read_json(path)
        if capture.get("request_sha256") != request["request_sha256"]:
            raise ValueError(f"Response belongs to another input: {path.name}")
        record = base_record(request)
        record["raw_output"] = capture
        try:
            raw = capture["response"]
            if isinstance(raw, str):
                raw = json.loads(raw)
            case = next(c for c in dataset["cases"] if c["id"] == request["case_id"])
            record["selected"] = validate_llm(raw, case, catalog, record["validation_warnings"])
            record.update(
                status="ok", phase=capture.get("phase", "unknown"),
                wall_seconds=capture.get("wall_seconds"), cpu_seconds=capture.get("cpu_seconds"),
                usage=capture.get("usage"), model=capture.get("model"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            record.update(status="error", error=str(exc))
        write_json(run / "results" / "llm" / args.variant / path.name, record, freeze=True)


def call_llm(run: Path, args: argparse.Namespace, requests: list[dict], dataset: dict, catalog: dict) -> None:
    if not args.allow_paid_llm:
        raise ValueError("Paid LLM gate not granted. Prepare requests first; obtain explicit model/call/token approval.")
    if not args.model:
        raise ValueError("--model must be the authorized model identity")
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY unavailable. Use host-native calls and --responses with saved exact inputs.")
    for index, request in enumerate(requests):
        output = run / "results" / "llm" / args.variant / f"{request_name(request)}.json"
        if output.exists():
            raise ValueError(f"Refusing another paid call over saved output: {output}")
        body = {
            "model": args.model, "input": request["prompt"],
            "text": {"format": {"type": "json_object"}},
            "store": False,
        }
        write_json(run / "wire" / "llm" / output.name, body, freeze=True)
        record = base_record(request)
        started, cpu_started = time.perf_counter(), time.process_time()
        try:
            req = urllib.request.Request(
                "https://api.openai.com/v1/responses", encoded(body).encode("utf-8"),
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=180) as response:
                result = json.load(response)
            record["raw_output"] = result
            content = "".join(
                part.get("text", "") for item in result.get("output", [])
                for part in item.get("content", []) if part.get("type") == "output_text"
            )
            case = next(c for c in dataset["cases"] if c["id"] == request["case_id"])
            if result.get("status") != "completed":
                raise ValueError(f"Provider did not complete: {result.get('status')}")
            record.update(
                status="ok", selected=validate_llm(json.loads(content), case, catalog, record["validation_warnings"]),
                model=result.get("model"), usage=result.get("usage"),
            )
        except Exception as exc:
            record.update(status="error", error=f"{type(exc).__name__}: {exc}")
        record.update(
            wall_seconds=time.perf_counter() - started,
            cpu_seconds=time.process_time() - cpu_started,
            phase="cold" if index == 0 else "warm",
        )
        write_json(output, record, freeze=True)


def model_cache() -> Path:
    cache = confined(BASE / ".cache")
    for variable, child in {
        "HF_HOME": "huggingface", "HF_HUB_CACHE": "huggingface/hub",
        "TORCH_HOME": "torch", "XDG_CACHE_HOME": "xdg", "TMP": "tmp",
        "TEMP": "tmp", "TMPDIR": "tmp", "HF_MODULES_CACHE": "huggingface/modules",
    }.items():
        target = confined(cache / child)
        target.mkdir(parents=True, exist_ok=True)
        os.environ[variable] = str(target)
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    return cache


def file_digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def load_julia(run: Path, args: argparse.Namespace) -> object:
    cache = model_cache()
    if args.batch_size < 1:
        raise ValueError("--batch-size must be positive")
    if args.threads < 1:
        raise ValueError("--threads must be positive")
    load_started_at = utc_now()
    started, cpu_started = time.perf_counter(), time.process_time()
    from huggingface_hub import snapshot_download
    checkpoint = Path(snapshot_download(
        JULIA_REPO, revision=JULIA_REVISION, cache_dir=str(cache / "huggingface" / "hub"),
        allow_patterns=["*.json", "*.safetensors", "julia/**/*.py", "julia/*.py", "tokenizer/*", "*.txt"],
        local_files_only=not args.allow_download,
    ))
    weights = list(checkpoint.glob("*.safetensors"))
    if len(weights) != 1 or file_digest(weights[0]) != JULIA_WEIGHT_SHA256:
        raise ValueError("Julia weight SHA-256 differs from the pinned verified model")
    sys.path.insert(0, str(checkpoint))
    import torch
    from julia import load_model
    os.environ["JULIA_CPU_THREADS"] = str(args.threads)
    torch.set_num_threads(args.threads)
    engine = load_model(
        str(checkpoint), device="cpu", backend="torch", strict_encoding=True,
        max_length=8192, head_length=512, batch_size=args.batch_size,
        marker_only_head=False, compile_model=False,
    )
    metadata = initialize(run)
    model_key = f"julia/{args.variant}"
    previous = metadata["models"].get(model_key)
    session_id = f"{args.variant}-{load_started_at}"
    session = {
        "session_id": session_id, "load_started_at": load_started_at,
        "repo": JULIA_REPO, "revision": JULIA_REVISION,
        "weight_sha256": JULIA_WEIGHT_SHA256, "weight_bytes": weights[0].stat().st_size,
        "precision": "FP32", "device": "cpu", "threads": torch.get_num_threads(),
        "batch_size": engine.batch_size,
        "require_complete_catalog": args.require_complete_catalog,
        "strict_encoding": True, "marker_only_head": False, "max_length": 8192,
        "load_wall_seconds": time.perf_counter() - started,
        "load_cpu_seconds": time.process_time() - cpu_started,
        "versions": {name: importlib.metadata.version(name) for name in (
            "torch", "transformers", "safetensors", "numpy", "huggingface-hub",
        )},
        "checkpoint_files": {
            path.relative_to(checkpoint).as_posix(): file_digest(path)
            for path in checkpoint.rglob("*") if path.is_file()
        },
    }
    # Keep the initial load evidence intact, including records made before load
    # sessions were introduced. Later sessions append their resource settings.
    if previous is None:
        metadata["models"][model_key] = dict(session)
        metadata["models"][model_key]["load_sessions"] = [session]
    else:
        if "load_sessions" not in previous:
            prior_session = dict(previous)
            prior_session.setdefault("session_id", f"{args.variant}-initial")
            prior_session.setdefault("batch_size", 16)
            prior_session["batch_size_provenance"] = "Original fixed runner configuration"
            previous["load_sessions"] = [prior_session]
        previous["load_sessions"].append(session)
    engine.benchmark_session_id = session_id
    write_json(run / "metadata.json", metadata)
    return engine


def local_probabilities(raw: dict, request: dict, roles: list[str]) -> tuple[dict, list[str]]:
    answers = raw["answers"]
    if request["variant"] == "noul":
        probabilities = {role: float(answers[role]["probabilities"]["true"]) for role in roles}
        selected = [role for role in roles if probabilities[role] >= THRESHOLD]
    else:
        probabilities = {role: float(answers["reviewer"]["probabilities"][role]) for role in roles}
        selected = [max(roles, key=lambda role: probabilities[role])]
        if not math.isclose(sum(probabilities.values()), 1.0, abs_tol=1e-5):
            raise ValueError("Choice probability distribution does not sum to one")
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities.values()):
        raise ValueError("Invalid probability")
    return probabilities, selected


def pending_local_requests(run: Path, args: argparse.Namespace, requests: list[dict]) -> list[dict]:
    """Validate frozen request bindings before resuming any local inference."""
    result_dir = run / "results" / args.impl / args.variant
    expected_names = {f"{request_name(request)}.json" for request in requests}
    unexpected = {path.name for path in result_dir.glob("*.json")} - expected_names
    if unexpected:
        raise ValueError(f"Saved results have no matching request: {sorted(unexpected)}")
    pending = []
    for request in requests:
        content = {key: value for key, value in request.items() if key != "request_sha256"}
        if digest(encoded(content)) != request.get("request_sha256"):
            raise ValueError(f"Request hash is invalid: {request_name(request)}")
        output = result_dir / f"{request_name(request)}.json"
        if not output.exists():
            pending.append(request)
            continue
        if not args.resume:
            raise ValueError(f"Saved output already exists: {output}. Use --resume after verifying the run.")
        saved = read_json(output)
        for key in ("impl", "variant", "case_id", "hunk_id", "request_sha256"):
            if saved.get(key) != request[key]:
                raise ValueError(f"Saved output/request mismatch for {output.name}: {key}")
        if saved.get("status") not in ("ok", "error"):
            raise ValueError(f"Saved output is not a completed attempt: {output.name}")
    return pending


def run_local(run: Path, args: argparse.Namespace, requests: list[dict], catalog: dict) -> None:
    if args.impl == "laya":
        raise ValueError("Secondary laya experiment not provisioned. No unverified adapter or automatic fallback.")
    requests = pending_local_requests(run, args, requests)
    if not requests:
        return
    engine = load_julia(run, args)
    roles = [r["id"] for r in reviewer_roles(catalog)]
    inference_started = False
    for request in requests:
        output = run / "results" / args.impl / args.variant / f"{request_name(request)}.json"
        if output.exists():
            raise ValueError(f"Saved output already exists: {output}")
        record = base_record(request)
        record["runtime_config"] = {"batch_size": engine.batch_size, "threads": args.threads}
        record["model_session_id"] = engine.benchmark_session_id
        record["catalog_validation"] = (
            "complete_catalog_required" if args.require_complete_catalog else "partial_diagnostics_allowed"
        )
        record["inference_attempted"] = False
        record["inference_performed"] = False
        record["submitted_question_ids"] = []
        record["phase"] = "preflight"
        started, cpu_started = time.perf_counter(), time.process_time()
        try:
            valid, errors, encoding = {}, {}, {}
            for question_id, question in request["questions"].items():
                criteria = question["criteria"]
                options = (
                    [criteria["false"], criteria["true"]]
                    if question["type"] == "noul" else list(criteria.values())
                )
                row = {
                    "state": request["state"], "question": question["instructions"],
                    "type": question["type"], "options": options,
                }
                try:
                    details = engine.encoding_info([row])[0]
                    if details.get("stateTruncated") or details.get("optionsTruncated"):
                        raise ValueError("Encoding would truncate the exact input")
                    encoding[question_id] = details
                    valid[question_id] = question
                except Exception as exc:
                    errors[question_id] = f"{type(exc).__name__}: {exc}"
            record["encoding"] = encoding
            record["question_errors"] = errors
            if errors and args.require_complete_catalog:
                raw = {"answers": {}}
                record["rejection_reason"] = "Complete catalog required; at least one requested question is unsupported."
            elif valid:
                effective_input = {
                    "source_request_sha256": request["request_sha256"],
                    "state": request["state"], "questions": valid,
                }
                write_json(
                    run / "wire" / args.impl / args.variant / f"{request_name(request)}.json",
                    effective_input, freeze=True,
                )
                record["submitted_question_ids"] = list(valid)
                record["phase"] = "warm" if inference_started else "cold"
                inference_started = True
                record["inference_attempted"] = True
                raw = engine.predict(state=request["state"], questions=valid)
                record["inference_performed"] = True
            else:
                raw = {"answers": {}}
            record["raw_output"] = raw
            if errors:
                # Retain successful answers for inspection, but never score an
                # incomplete role catalog as if absent predictions were false.
                record.update(status="error", error="One or more exact questions are unsupported; see question_errors")
            else:
                probabilities, selected = local_probabilities(raw, request, roles)
                record.update(status="ok", probabilities=probabilities, selected=selected)
        except Exception as exc:
            record.update(status="error", error=f"{type(exc).__name__}: {exc}")
        record.update(
            wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu_started,
            usage={"input_tokens": None, "output_tokens": 0},
        )
        write_json(output, record, freeze=True)


def command_run(args: argparse.Namespace, run: Path) -> None:
    requests, dataset, catalog = prepare(run, args.impl, args.variant)
    if args.prepare_only:
        empty_criteria = [
            {"case_id": r["case_id"], "hunk_id": r["hunk_id"], "question_id": key}
            for r in requests for key, q in r.get("questions", {}).items()
            if any(not value for value in q["criteria"].values())
        ]
        summary = {
            "status": "prepared; no model calls", "impl": args.impl, "variant": args.variant,
            "calls": len(requests), "cases": len({r["case_id"] for r in requests}),
            "questions": sum(len(r.get("questions", {})) for r in requests),
            "input_characters": sum(len(r.get("prompt", encoded(r))) for r in requests),
            "provider_input_tokens": None,
            "planning_estimate_tokens_chars_div_4": math.ceil(sum(len(r.get("prompt", encoded(r))) for r in requests) / 4),
            "estimate_warning": "Planning heuristic only, not tokenizer counts or provider usage.",
            "empty_criteria_questions": empty_criteria,
            "empty_criteria_question_count": len(empty_criteria),
            "empty_criteria_effect": (
                "Julia requires nonempty rendered option descriptions. These exact questions are inadmissible; no replacement criteria are inferred."
                if empty_criteria else None
            ),
        }
        write_json(run / "plans" / f"{args.impl}-{args.variant}.json", summary)
        print(encoded({key: value for key, value in summary.items() if key != "empty_criteria_questions"}))
        return
    if args.impl == "llm":
        if args.responses:
            imported_llm(run, args, requests, dataset, catalog)
        else:
            call_llm(run, args, requests, dataset, catalog)
    else:
        run_local(run, args, requests, catalog)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("extract-catalog", "materialize-cases", "run", "score", "report"):
        child = sub.add_parser(command)
        child.add_argument("--run-dir", required=True, help="Directory inside this benchmark, preferably runs/<UTC timestamp>")
        if command == "materialize-cases":
            child.add_argument("--jupiter-root", default=r"D:\Projects\jupiter")
        if command == "run":
            child.add_argument("--impl", choices=("llm", "julia", "laya"), required=True)
            child.add_argument("--variant", choices=("noul", "choice"), required=True)
            child.add_argument("--prepare-only", action="store_true")
            child.add_argument("--allow-download", action="store_true", help="Only after explicit weights download approval")
            child.add_argument("--allow-paid-llm", action="store_true", help="Only after explicit model/calls/token approval")
            child.add_argument("--model")
            child.add_argument("--responses", help="Import hash-bound provider/host response captures; makes no calls")
            child.add_argument("--threads", type=int, default=4)
            child.add_argument("--batch-size", type=int, default=16)
            child.add_argument("--resume", action="store_true", help="Validate and preserve completed local results, then run missing requests")
            child.add_argument("--require-complete-catalog", action="store_true", help="Reject the whole requested batch before inference if any exact question is unsupported")
    args = parser.parse_args()
    run = confined(args.run_dir)
    if not run.is_relative_to(BASE / "runs") or run == BASE / "runs":
        parser.error("--run-dir must be a child of choicer-eval/runs/")
    initialize(run)
    try:
        if args.command == "extract-catalog":
            from dataset import extract_catalog, extract_prompts
            write_json(run / "catalog.json", extract_catalog(REPO), freeze=True)
            write_json(run / "prompts.json", extract_prompts(REPO), freeze=True)
        elif args.command == "materialize-cases":
            from dataset import materialize_cases
            write_json(run / "dataset.json", materialize_cases(REPO, Path(args.jupiter_root)), freeze=True)
        elif args.command == "run":
            command_run(args, run)
        else:
            from metrics import score, render_report
            dataset, catalog, prompts = required_inputs(run)
            results = verified_results(run, dataset, catalog, prompts)
            scored = score(dataset, catalog, results, threshold=THRESHOLD)
            write_json(run / "scores.json", scored)
            if args.command == "report":
                metadata = initialize(run)
                report = render_report(dataset, catalog, scored, metadata)
                write_text(run / "RESULTS.md", report)
        return 0
    except (ValueError, KeyError, OSError, ImportError) as exc:
        print(f"{args.command}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
