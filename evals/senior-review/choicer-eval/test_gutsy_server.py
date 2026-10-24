"""Run gutsy-0.8b-v04 on CPU via llama-server for fast, low-memory routing decisions."""

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
PORT = 8765
URL = f"http://127.0.0.1:{PORT}/completion"


def wait_for_server(timeout: float = 20.0) -> bool:
    start = time.perf_counter()
    while time.perf_counter() - start < timeout:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{PORT}/health")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def query_gutsy(state: str, question: str, options: list[tuple[str, str]]) -> tuple[str, float]:
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
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})

    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60.0) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    elapsed = time.perf_counter() - t0

    content = result.get("content", "").strip().upper()
    letter = content[0] if content else "Z"
    return letter, elapsed


def main():
    print(f"Starting llama-server with model {MODEL.name} on port {PORT}...")
    server_proc = subprocess.Popen(
        [
            str(LLAMA_SERVER),
            "-m",
            str(MODEL),
            "-c",
            "4096",
            "-t",
            "4",
            "--port",
            str(PORT),
            "--host",
            "127.0.0.1",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        if not wait_for_server():
            raise RuntimeError("llama-server did not become healthy in time")
        print("Server ready! Running Snodo 2 (TASK_TIER_CHOICER)...")

        # 1. Test TASK_TIER_CHOICER
        state_tier = (
            "Task objective: Implement optimistic locking version check on MongoDB update_email in profiles/repo.py.\n"
            "Graph facts: profiles/repo.py:12 function update_email has 6 incoming callers across web and worker services.\n"
            "Downstream callers: api_gateway/routes/profile.py, workers/email_sync.py."
        )
        q_tier = "Assign the execution tier for this code micro-task according to task complexity."
        opts_tier = [
            ("tier1", "tier1: mechanical edits, formatting, copy config, text/doc edits with zero code logic"),
            ("tier2", "tier2: writing tests, implementing standard code patches in clear write_set, updating callers"),
            ("tier3", "tier3: multi-module changes, contract changes, concurrency/locking, security, data migration"),
            ("reject", "None of the options fits, or the state does not say"),
        ]
        letter, el = query_gutsy(state_tier, q_tier, opts_tier)
        idx = ord(letter) - ord("A") if ord("A") <= ord(letter) < ord("A") + len(opts_tier) else -1
        print(f"Task tier choice: {letter} -> {opts_tier[idx] if idx >= 0 else 'Unknown'} in {el:.2f}s")

        # 2. Test REVIEWER_CHOICER on all 11 cases!
        print("\nRunning Snodo 1 (REVIEWER_CHOICER) across all 11 cases...")
        dataset = json.loads((RUN_DIR / "dataset.json").read_text(encoding="utf-8"))
        risk_families = [
            ("security", "Does this code change touch authentication, authorization, access control, secrets, or user data boundaries?", "senior-review:security-auditor"),
            ("data_integrity", "Does this code change touch database persistence, SQL, ORM models, transaction boundaries, or cache-database synchronization?", "senior-review:data-integrity-auditor"),
            ("temporal", "Does this code change touch asynchronous timing, timeouts, polling loops, retries, exponential backoff, intervals, or background schedulers?", "senior-review:temporal-resilience-auditor"),
            ("resource", "Does this code change acquire or release system resources like locks, sockets, connections, files, worker pools, or event listeners?", "senior-review:resource-lifecycle-auditor"),
            ("ui", "Does this code change touch UI layout, component rendering, scroll position, focus, DOM measurements, or frontend event races?", "senior-review:ui-race-auditor"),
            ("distributed", "Does this code change span cross-service messages, AMQP/RPC, webhooks, or producer-consumer contracts?", "senior-review:distributed-flow-auditor"),
        ]

        all_results = []
        for case in dataset["cases"]:
            cid = case["id"]
            source_name = case["source_case"]
            status = case["label_status"]
            expected = case["expected_roles"]

            # Use all hunks (joined or first hunk)
            full_diff = "\n".join(f"[{h['id']}] {h['path']}:{h['start_line']}\n{h['text']}" for h in case["hunks"][:4])
            if len(full_diff) > 2500:
                full_diff = full_diff[:2500] + "\n...[truncated]"
            state = f"Case {cid}: {source_name}\nCode diff hunks:\n{full_diff}"

            detected = []
            timings = []
            for risk_name, risk_q, role_id in risk_families:
                opts = [
                    ("yes", f"Yes: {risk_q}"),
                    ("no", "No: this code change does not involve this risk"),
                ]
                ans_letter, ans_el = query_gutsy(state, risk_q, opts)
                timings.append(ans_el)
                if ans_letter == "A":
                    detected.append(role_id)

            res_entry = {
                "case_id": cid,
                "source_case": source_name,
                "label_status": status,
                "expected": expected,
                "detected": detected,
                "avg_latency_s": round(sum(timings) / len(timings), 3),
            }
            all_results.append(res_entry)
            print(f"Case {cid} ({source_name}):")
            print(f"  Expected: {expected if status == 'labeled' else 'unlabeled'}")
            print(f"  Gutsy detected: {detected}")
            print(f"  Latency: {res_entry['avg_latency_s']}s/query")

        # Save summary
        out_file = HERE / "runs/20261020T100258Z/gutsy-routing-results.json"
        out_file.write_text(json.dumps(all_results, indent=2) + "\n", encoding="utf-8")
        print(f"\nSaved all results to {out_file}")

    finally:
        print("Shutting down llama-server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5.0)
        except Exception:
            server_proc.kill()
        print("Server stopped cleanly.")


if __name__ == "__main__":
    main()
