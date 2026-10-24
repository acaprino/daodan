"""Benchmark gutsy-0.8b-v04 on TASK_TIER_CHOICER and REVIEWER_CHOICER via llama-server on CPU."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LLAMA_SERVER = HERE / ".cache/gutsy/llama-bin/llama-server.exe"
MODEL = HERE / ".cache/gutsy/gutsy-0.8b-v04-q4_k_m.gguf"
RUN_DIR = HERE / "runs/20261020T100258Z"
PORT = 8089
SERVER_URL = f"http://127.0.0.1:{PORT}"


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


def query_gutsy(state: str, question: str, options: list[tuple[str, str]]) -> tuple[str, float, dict]:
    opts_lines = []
    letters = [chr(ord("A") + i) for i in range(len(options))]
    for letter, (key, desc) in zip(letters, options):
        opts_lines.append(f"{letter}. {desc}")

    prompt = (
        "<|im_start|>system\n"
        "You are a helpful assistant.<|im_end|>\n"
        "<|im_start|>user\n"
        f"State:\n{state}\n\n"
        f"Question: {question}\n\n"
        "Options:\n" + "\n".join(opts_lines) + "\n\n"
        "Answer with a single letter.<|im_end|>\n"
        "<|im_start|>assistant\n"
        "<think>\n\n</think>\n\n"
    )

    payload = {
        "prompt": prompt,
        "n_predict": 1,
        "temperature": 0.0,
        "cache_prompt": True,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{SERVER_URL}/completion", data=data, headers={"Content-Type": "application/json"})

    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30.0) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    elapsed = time.perf_counter() - t0

    content = result.get("content", "").strip().upper()
    letter = content[0] if content else "Z"
    return letter, elapsed, result


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
        print("PART 1: Snodo 2 (TASK_TIER_CHOICER) on sample micro-tasks", flush=True)
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
            ("tier1", "tier1: purely mechanical edits, formatting, copy config, text/doc edits with zero code logic"),
            ("tier2", "tier2: writing tests, implementing standard code patches in clear write_set, updating callers"),
            ("tier3", "tier3: multi-module changes, contract changes, concurrency/locking, security, data migration"),
            ("reject", "None of the options fits, or the state does not say"),
        ]

        tier_hits = 0
        for item in test_tasks:
            letter, el, _ = query_gutsy(item["state"], q_tier, opts_tier)
            idx = ord(letter) - ord("A")
            chosen = opts_tier[idx][0] if 0 <= idx < len(opts_tier) else "invalid"
            ok = (chosen == item["expected"])
            if ok:
                tier_hits += 1
            print(f"Task {item['id']}: expected={item['expected']}, gutsy={chosen} ({letter}) [ok={ok}, latency={el*1000:.1f}ms]", flush=True)
        print(f"TASK_TIER accuracy: {tier_hits}/{len(test_tasks)} ({tier_hits/len(test_tasks)*100:.1f}%)", flush=True)

        # -------------------------------------------------------------
        # Part 2: Snodo 1 - REVIEWER_CHOICER on C01..C11
        # -------------------------------------------------------------
        print("\n=======================================================", flush=True)
        print("PART 2: Snodo 1 (REVIEWER_CHOICER) on Benchmark Cases C01..C11", flush=True)
        print("=======================================================", flush=True)

        dataset = json.loads((RUN_DIR / "dataset.json").read_text(encoding="utf-8"))
        catalog = json.loads((RUN_DIR / "catalog.json").read_text(encoding="utf-8"))

        risk_families = [
            ("security", "Does this code change touch authentication, authorization, access control, secrets, or user data boundaries?", "senior-review:security-auditor"),
            ("data_integrity", "Does this code change touch database persistence, SQL, ORM models, transaction boundaries, or cache-database synchronization?", "senior-review:data-integrity-auditor"),
            ("temporal", "Does this code change touch asynchronous timing, timeouts, polling loops, retries, exponential backoff, intervals, or background schedulers?", "senior-review:temporal-resilience-auditor"),
            ("resource", "Does this code change acquire or release system resources like locks, sockets, connections, files, worker pools, or event listeners?", "senior-review:resource-lifecycle-auditor"),
            ("ui", "Does this code change touch UI layout, component rendering, scroll position, focus, DOM measurements, or frontend event races?", "senior-review:ui-race-auditor"),
            ("distributed", "Does this code change span cross-service messages, AMQP/RPC, webhooks, or producer-consumer contracts?", "senior-review:distributed-flow-auditor"),
            ("logic_integrity", "Does this code change touch state machines, order/status transitions, idempotency, or domain invariants?", "senior-review:logic-integrity-auditor"),
            ("chicken_egg", "Does this code change touch startup ordering, bootstrap, configuration loading, or migration dependencies?", "senior-review:chicken-egg-detector"),
        ]

        case_eval_records = []
        for case in dataset["cases"]:
            cid = case["id"]
            source_name = case["source_case"]
            status = case["label_status"]
            expected = set(case["expected_roles"])

            # Use all hunks (joined up to 2500 chars to avoid prompt bloat)
            full_diff = "\n\n".join(f"[{h['id']}] {h['path']}:{h['start_line']}\n{h['text']}" for h in case["hunks"][:4])
            if len(full_diff) > 2500:
                full_diff = full_diff[:2500] + "\n...[diff truncated]"
            state = f"Case {cid}: {source_name}\nCode diff under review:\n{full_diff}"

            detected = set()
            # Generalist code-auditor is always present on changesets
            detected.add("senior-review:code-auditor")

            timings = []
            for rname, rq, role_id in risk_families:
                opts = [
                    ("yes", f"Yes: {rq}"),
                    ("no", "No: this code change does not involve this risk"),
                    ("reject", "Unclear or none of the options fits"),
                ]
                letter, el, _ = query_gutsy(state, rq, opts)
                timings.append(el)
                if letter == "A":
                    detected.add(role_id)

            # Check language/AST rules for TS/React
            joined_paths = " ".join(h["path"] for h in case["hunks"])
            if any(p.endswith((".tsx", ".jsx")) for p in joined_paths.split()):
                detected.add("react-development:react-performance-optimizer")
            if any(p.endswith((".ts", ".tsx")) for p in joined_paths.split()):
                detected.add("typescript-development:type-safety-auditor")

            avg_el = sum(timings) / len(timings)
            case_eval_records.append({
                "case_id": cid,
                "source_case": source_name,
                "label_status": status,
                "expected": sorted(expected),
                "selected": sorted(detected),
                "avg_query_latency_ms": round(avg_el * 1000, 1),
            })

            matched = sorted(detected & expected) if status == "labeled" else []
            missing = sorted(expected - detected) if status == "labeled" else []
            excess = sorted(detected - expected) if status == "labeled" else []

            print(f"\nCase {cid} ({source_name}):", flush=True)
            print(f"  Expected: {sorted(expected) if status == 'labeled' else 'unlabeled'}", flush=True)
            print(f"  Gutsy selected: {sorted(detected)}", flush=True)
            if status == "labeled":
                print(f"  Matched: {matched} | Missing: {missing} | Excess: {len(excess)}", flush=True)
            print(f"  Avg latency: {round(avg_el*1000, 1)} ms/question", flush=True)

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
            "security_recall": f"{sec_hits}/{sec_support}",
            "data_integrity_recall": f"{data_hits}/{data_support}",
            "excess_activations_per_case": round(total_excess / len(labeled_cases), 3),
            "mean_selected_per_case": round(sum(len(c["selected"]) for c in labeled_cases) / len(labeled_cases), 3),
        }

        print("\n=======================================================", flush=True)
        print("SUMMARY METRICS: gutsy-0.8b-v04 on CPU", flush=True)
        print("=======================================================", flush=True)
        print(json.dumps(overall_metrics, indent=2), flush=True)

        out_path = HERE / "runs/20261020T100258Z/gutsy-eval-summary.json"
        out_path.write_text(json.dumps({"summary": overall_metrics, "cases": case_eval_records}, indent=2) + "\n", encoding="utf-8")
        print(f"\nSaved results to {out_path}", flush=True)

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
