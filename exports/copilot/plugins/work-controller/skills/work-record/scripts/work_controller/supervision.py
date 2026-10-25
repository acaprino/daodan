"""Bounded observations and non-authoritative supervision recommendations."""

from __future__ import annotations

import time
from typing import Any

ACTIONS = {
    "CONTINUE",
    "STEER_WORKER",
    "STOP_WORKER",
    "RETRY_WORKER",
    "START_VERIFIER",
    "FINISH",
    "ESCALATE",
}


def observe(engine: Any, attempt_id: str, *, event_limit: int = 8) -> dict[str, Any]:
    """Build a small observation without artifact bodies or a whole-run transcript."""
    attempt = engine.store.attempt(attempt_id)
    job = engine.store.job(attempt["run_id"], attempt["job_id"])
    jobs = engine.store.jobs(attempt["run_id"])
    run = engine.store.run(attempt["run_id"])
    definition = engine.definition(attempt["run_id"])
    dependent_verification = False
    for candidate_id, dependencies in definition.dependencies.items():
        if attempt["job_id"] not in dependencies:
            continue
        candidate = engine.store.job(attempt["run_id"], candidate_id)
        if candidate["payload"]["type"] == "command" and candidate["status"] != "succeeded":
            dependent_verification = True
    events = [
        {"kind": event["kind"], "created_at": event["created_at"]}
        for event in engine.store.attempt_events(attempt_id, limit=event_limit)
    ]
    return {
        "run_id": attempt["run_id"],
        "run_status": run["status"],
        "run_outcome": run["outcome"],
        "global_attempts_used": sum(item["attempts"] for item in jobs),
        "global_max_attempts": definition.data["budget"]["max_attempts"],
        "attempt_id": attempt_id,
        "job_id": attempt["job_id"],
        "attempt_status": attempt["status"],
        "job_status": job["status"],
        "attempts_used": job["attempts"],
        "max_attempts": job["payload"]["max_attempts"],
        "expired": attempt["status"] in ("reserved", "running", "completing") and time.time() >= attempt["expires_at"],
        "expected_outputs": [
            {"name": item["name"], "type": item["type"]}
            for item in job["payload"]["produces"]
        ],
        "error": attempt["error"][:1000] if attempt["error"] else None,
        "verification_pending": dependent_verification,
        "all_jobs_succeeded": all(item["status"] == "succeeded" for item in jobs),
        "events": events,
    }


def recommend(observation: dict[str, Any]) -> str:
    """Apply a deterministic policy. The result is advice, never a state transition."""
    status = observation["attempt_status"]
    if status == "unknown" or observation["job_status"] == "blocked":
        return "ESCALATE"
    run_status = observation.get("run_status", "in_progress")
    if run_status != "in_progress":
        if status == "delivered" and run_status == "complete":
            return "FINISH"
        return "ESCALATE"
    if status in ("failed", "revoked"):
        global_exhausted = observation.get("global_attempts_used", 0) >= observation.get(
            "global_max_attempts", 100
        )
        if observation["attempts_used"] < observation["max_attempts"] and not global_exhausted:
            return "RETRY_WORKER"
        return "ESCALATE"
    if observation["expired"]:
        return "STOP_WORKER"
    if status in ("reserved", "running", "completing"):
        return "CONTINUE"
    if status == "delivered":
        if observation["verification_pending"]:
            return "START_VERIFIER"
        if observation["all_jobs_succeeded"]:
            return "FINISH"
        return "CONTINUE"
    return "ESCALATE"


def supervise(engine: Any, attempt_id: str) -> dict[str, Any]:
    observation = observe(engine, attempt_id)
    action = recommend(observation)
    if action not in ACTIONS:
        raise RuntimeError("supervision policy returned an unknown action")
    return {"action": action, "authoritative": False, "observation": observation}
