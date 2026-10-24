"""Test gutsy-0.8b-v04 on TASK_TIER_CHOICER and REVIEWER_CHOICER using native llama.cpp CLI."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LLAMA_CLI = HERE / ".cache/gutsy/llama-bin/llama-cli.exe"
MODEL = HERE / ".cache/gutsy/gutsy-0.8b-v04-q4_k_m.gguf"
RUN_DIR = HERE / "runs/20261020T100258Z"

if not LLAMA_CLI.exists() or not MODEL.exists():
    raise SystemExit(f"Missing {LLAMA_CLI} or {MODEL}")


def run_gutsy_single_turn(state: str, question: str, options: list[tuple[str, str]], threads: int = 4) -> tuple[str, float]:
    """Format prompt according to gutsy ChatML contract and query llama-cli."""
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

    cmd = [
        str(LLAMA_CLI),
        "-m",
        str(MODEL),
        "-p",
        prompt,
        "-n",
        "1",
        "--temp",
        "0",
        "-t",
        str(threads),
        "-c",
        "4096",
        "--no-warmup",
        "--simple-io",
    ]

    t0 = time.perf_counter()
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    elapsed = time.perf_counter() - t0

    # The single letter prediction appears on its own line after [Start thinking] or <think>
    lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    letter = None
    for line in lines:
        if line in letters:
            letter = line
            break
        # Sometimes it outputs "C." or "C"
        if len(line) == 2 and line[0] in letters and line[1] in ".):":
            letter = line[0]
            break
    if not letter:
        match = re.search(r"\b([A-Z])\b", res.stdout[res.stdout.rfind("<think>"):])
        if match and match.group(1) in letters:
            letter = match.group(1)
    if not letter:
        raise ValueError(f"Could not parse single-letter prediction from llama-cli output:\n{res.stdout[-500:]}")
    return letter, elapsed


def test_task_tier_choicer():
    print("=== Testing gutsy on Snodo 2: TASK_TIER_CHOICER ===")
    state = (
        "Task objective: Implement optimistic locking version check on MongoDB update_email in profiles/repo.py.\n"
        "Graph facts: profiles/repo.py:12 function update_email has 6 incoming callers across web and worker services.\n"
        "Downstream callers: api_gateway/routes/profile.py, workers/email_sync.py."
    )
    question = "Assign the execution tier for this code micro-task according to task complexity."
    options = [
        ("tier1", "tier1: mechanical edits, formatting, copy config, text/doc edits with zero code logic"),
        ("tier2", "tier2: writing tests, implementing standard code patches in clear write_set, updating callers"),
        ("tier3", "tier3: multi-module changes, contract changes, concurrency/locking, security, data migration"),
        ("reject", "None of the options fits, or the state does not say"),
    ]

    letter, elapsed = run_gutsy_single_turn(state, question, options)
    idx = ord(letter) - ord("A")
    chosen_key, chosen_desc = options[idx]
    print(f"Prediction: {letter} -> {chosen_key} ({chosen_desc}) [elapsed: {elapsed:.2f}s]")


def test_reviewer_routing_cases(limit_cases: int = 4):
    print(f"\n=== Testing gutsy on Snodo 1: REVIEWER_CHOICER (first {limit_cases} cases) ===")
    dataset = json.loads((RUN_DIR / "dataset.json").read_text(encoding="utf-8"))

    risk_families = [
        ("security", "Does this code change touch authentication, authorization, access control, secrets, or user data boundaries?", "senior-review:security-auditor"),
        ("data_integrity", "Does this code change touch database persistence, SQL, ORM models, transaction boundaries, or cache-database synchronization?", "senior-review:data-integrity-auditor"),
        ("temporal", "Does this code change touch asynchronous timing, timeouts, polling loops, retries, exponential backoff, intervals, or background schedulers?", "senior-review:temporal-resilience-auditor"),
        ("resource", "Does this code change acquire or release system resources like locks, sockets, connections, files, worker pools, or event listeners?", "senior-review:resource-lifecycle-auditor"),
        ("ui", "Does this code change touch UI layout, component rendering, scroll position, focus, DOM measurements, or frontend event races?", "senior-review:ui-race-auditor"),
        ("distributed", "Does this code change span cross-service messages, AMQP/RPC, webhooks, or producer-consumer contracts?", "senior-review:distributed-flow-auditor"),
    ]

    selected_cases = [c for c in dataset["cases"] if c["id"] in ("C01", "C03", "C05", "C08")][:limit_cases]
    for case in selected_cases:
        cid = case["id"]
        source_name = case["source_case"]
        status = case["label_status"]
        expected = case["expected_roles"]

        first_hunk = case["hunks"][0]
        hunk_code = first_hunk["text"]
        path = first_hunk["path"]
        state = f"File: {path}\nCode diff hunk:\n{hunk_code[:800]}"

        active_roles = []
        timings = []
        for risk_name, risk_question, role_id in risk_families:
            options = [
                ("yes", f"Yes: {risk_question}"),
                ("no", "No: this code change does not involve this risk"),
            ]
            letter, elapsed = run_gutsy_single_turn(state, risk_question, options)
            timings.append(elapsed)
            if letter == "A":
                active_roles.append(role_id)

        print(f"\nCase {cid} ({source_name}):")
        print(f"  Expected: {expected if status == 'labeled' else 'unlabeled'}")
        print(f"  Gutsy detected: {active_roles}")
        print(f"  Avg inference latency: {sum(timings)/len(timings):.2f}s per question")


if __name__ == "__main__":
    test_task_tier_choicer()
    test_reviewer_routing_cases(limit_cases=4)
