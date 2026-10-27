"""Controlled transcripts. Upstream fast-jev owns fitting, questions and rebuilding."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
UPSTREAM_COMMIT = "e3f262a7f4d42bd8dd32ced30d26176f7cb545b0"


def _bridge(payload: dict) -> dict:
    node = os.environ.get("NODE_BINARY") or shutil.which("node")
    if not node:
        raise RuntimeError("Node is required to exercise the actual fast-jev library")
    result = subprocess.run(
        [node, str(HERE / "compaction_bridge.mjs")],
        input=json.dumps(payload, ensure_ascii=False, allow_nan=False),
        capture_output=True, text=True, encoding="utf-8", timeout=45,
    )
    if result.returncode:
        raise RuntimeError("fast-jev bridge failed; set FAST_JEV_MODULE to the pinned dist/index.js: " + result.stderr[-1800:])
    return json.loads(result.stdout)


def _message(role: str, text: str = "", calls: list | None = None, results: list | None = None) -> dict:
    out = {"role": role, "text": text, "toolUses": calls or []}
    if results is not None:
        out["toolResults"] = results
    return out


def _pair(tool: str, inputs: dict, text: str, use_id: str = "candidate", error: bool = False) -> list[dict]:
    return [
        _message("assistant", calls=[{"tool_use_id": use_id, "tool": tool, "input": inputs}]),
        _message("user", results=[{"tool_use_id": use_id, "text": text, "isError": error}]),
    ]


def _tail(text: str) -> str:
    return "heartbeat\n" * ((600 - len(text)) // 10) + " " * ((600 - len(text)) % 10) + text


def transcript_specs() -> list[dict]:
    """Public inputs and separate private oracle. All candidate outputs are complete."""
    log_goal = "Explain error E72 using recorded diagnostic evidence. The diagnostic log is no longer available. If evidence does not establish a cause, say UNKNOWN."
    recovery_content = _tail("timeout=17; snapshot=H")
    recovery_hash = hashlib.sha256(recovery_content.encode()).hexdigest()
    rows = [
        ("C01", log_goal, "Read", {"file_path": "diagnostic.log"}, _tail("E72=LEASE_EXPIRED"), False,
         {"required_tokens": ["LEASE_EXPIRED"], "critical": True, "allowed_actions": ["keep"]}),
        ("C02", log_goal, "Read", {"file_path": "diagnostic.log"}, _tail(""), False,
         {"required_tokens": [], "critical": False, "dispensable": True, "expected_fact": "UNKNOWN"}),
        ("C03", "Report timeout from the latest config snapshot. Both reads address the same immutable snapshot H.", "Read", {"file_path": "snapshot/H/config.json"}, _tail("timeout=17; snapshot=H"), False,
         {"required_tokens": ["timeout=17"], "critical": False, "dispensable": True}),
        ("C04", "Verify candidate B. Evidence about a different candidate cannot attest candidate B.", "RunTests", {"sha": "A"}, _tail("sha=A PASS"), False,
         {"required_tokens": ["sha=B FAIL E_AUTH_19"], "critical": False, "dispensable": True}),
        ("C05", "Report the exact recorded failure location for candidate B. Tests cannot be run again and no other diagnostic copy exists.", "RunTests", {"sha": "B"}, _tail("sha=B tests/auth.py:42 E_AUTH_19"), True,
         {"required_tokens": ["sha=B", "tests/auth.py:42", "E_AUTH_19"], "critical": True, "allowed_actions": ["keep"]}),
        ("C06", "Report the exact recorded failure location for candidate B. Tests cannot be run again and no other diagnostic copy exists.", "RunTests", {"sha": "B"}, ("sha=B tests/auth.py:42 E_AUTH_19\n" + "heartbeat\n" * 70)[:600], True,
         {"required_tokens": ["sha=B", "tests/auth.py:42", "E_AUTH_19"], "critical": True, "allowed_actions": ["keep", "drop_result"]}),
        ("C07", "Report timeout from immutable snapshot H. A read-only fixture can recover the exact snapshot by path and SHA256; one additional read is permitted.", "Read", {"file_path": "snapshot/H/config.json"}, recovery_content, False,
         {"required_tokens": ["timeout=17"], "critical": False, "recoverable": True,
          "recovery": {"path": "snapshot/H/config.json", "sha256": recovery_hash, "content": recovery_content}}),
        ("C08", "Return the recorded receipt for the message already sent. Never send it again; the unique receipt cannot be reconstructed from another source.", "SendMessage", {"recipient": "fixture-recipient", "body": "fixture-notification"}, _tail("message_id=M-2049"), False,
         {"required_tokens": ["M-2049"], "critical": True, "allowed_actions": ["keep"], "protect_result": True}),
    ]
    specs = []
    for case_id, goal, tool, inputs, output, is_error, oracle in rows:
        messages = [_message("user", goal), *_pair(tool, inputs, output, error=is_error)]
        messages.extend(_message("assistant", "No new facts. The original objective remains active.") for _ in range(6))
        if case_id == "C03":
            messages.extend(_pair(tool, inputs, output, use_id="recent-copy"))
        elif case_id == "C04":
            messages.extend(_pair("RunTests", {"sha": "B"}, "sha=B FAIL E_AUTH_19", use_id="recent-candidate", error=True))
        elif case_id == "C07":
            messages.append(_message("user", f"Recovery locator: snapshot/H/config.json; SHA256={recovery_hash}. Read-only recovery remains available."))
        specs.append({"id": case_id, "goal": goal, "messages": messages,
                      "split": "development" if case_id in {"C03", "C07"} else "verification",
                      "oracle": oracle})
    return specs


def build_cases() -> list[dict]:
    cases = []
    for spec in transcript_specs():
        options = {"goal": spec["goal"], "preserveRecentMessages": 6,
                   "keepThreshold": 0.5, "truncateHeadChars": 300,
                   "maxStateTokens": 3000, "maxRequestTokens": 4096}
        for arm in ("A", "B"):
            prepared = _bridge({"action": "prepare", "messages": spec["messages"], "options": options, "arm": arm})
            cases.append({"id": f"{spec['id']}-{arm}", "domain": "compaction", "split": spec["split"],
                          "state": prepared["state"], "questions": prepared["questions"],
                          "oracle": {**spec["oracle"], "arm": arm, "messages": spec["messages"],
                                     "options": options, "upstream_commit": UPSTREAM_COMMIT,
                                     "state_stage": prepared["state_stage"],
                                     "estimated_upstream_tokens": prepared["estimated_upstream_tokens"]}})
    return cases


def _validate_response(case: dict, response: dict) -> None:
    for key in case["questions"]:
        value = response.get("answers", {}).get(key, {}).get("noul")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"Invalid bounded noul answer: {key}")


def _render(messages: list[dict], exclude_use_id: str | None = None) -> str:
    return "\n".join(m["text"] + "\n" + "\n".join(r["text"] for r in m.get("toolResults", [])
                                                  if r["tool_use_id"] != exclude_use_id)
                     for m in messages)


def decision_bearing(messages: list[dict], required_tokens: list[str]) -> bool:
    """True when at least one required fact lives only in the candidate result.

    A fact repeated in a pinned message (C03's recent copy, C04's recent candidate)
    survives every decision, so its preservation is structural and says nothing
    about the classifier. Only decision-bearing cases count as evidence either way.
    """
    outside = _render(messages, exclude_use_id="candidate")
    return any(token not in outside for token in required_tokens)


def score_case(case: dict, response: dict) -> dict:
    _validate_response(case, response)
    oracle = case["oracle"]
    applied = _bridge({"action": "apply", "messages": oracle["messages"], "options": oracle["options"],
                       "response": response, "protect_result": oracle.get("protect_result", False)})
    raw = applied["raw"]
    text = _render(raw["messages"])
    missing = [token for token in oracle.get("required_tokens", []) if token not in text]
    recovered = False
    recovery_reads = 0
    if missing and oracle.get("recoverable"):
        recovery = oracle["recovery"]
        actual = hashlib.sha256(recovery["content"].encode()).hexdigest()
        if actual == recovery["sha256"] and recovery["path"] in text and actual in text:
            recovered = all(token in recovery["content"] for token in missing)
            recovery_reads = int(recovered)
    action = next(d["action"] for d in raw["decisions"] if d["id"] == "t1")
    critical = [f"lost:{token}" for token in missing if oracle.get("critical")]
    if oracle.get("allowed_actions") and action not in oracle["allowed_actions"]:
        critical.append(f"unexpected_action:{action}")
    if not all(applied["invariants"].values()):
        critical.append("transcript_invariant")
    protected_missing = None
    if applied["protected"] is not None:
        protected_text = _render(applied["protected"]["messages"])
        protected_missing = [token for token in oracle.get("required_tokens", []) if token not in protected_text]
    before = raw["stats"]["charsBefore"]
    after = raw["stats"]["charsAfter"]
    before_bytes = len(json.dumps(oracle["messages"], ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    after_bytes = len(json.dumps(raw["messages"], ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    return {"action": action, "critical_failures": critical, "missing_facts_raw": missing,
            "evidence_decision_bearing": decision_bearing(oracle["messages"], oracle.get("required_tokens", [])),
            "evidence_preserved_raw": not missing, "evidence_preserved_after_recovery": not missing or recovered,
            "protected_missing_facts": protected_missing, "guardrail_applied": bool(oracle.get("protect_result")),
            "recovery_reads": recovery_reads, "superfluous_keep": bool(oracle.get("dispensable") and action == "keep"),
            "chars_before": before, "chars_after": after, "reduction_chars": before - after,
            "serialized_bytes_before": before_bytes, "serialized_bytes_after": after_bytes,
            "reduction_bytes": before_bytes - after_bytes,
            "token_savings": None, "token_savings_status": "not measured: target tokenizer not supplied",
            "invariants": applied["invariants"], "upstream_stats": raw["stats"],
            "compacted_messages": raw["messages"], "protected_compacted_messages": applied["protected"]["messages"] if applied["protected"] else None}


def deterministic_checks() -> dict:
    return _bridge({"action": "contracts"})
