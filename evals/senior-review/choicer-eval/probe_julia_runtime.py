"""Compare input type and encoder paths, then evaluate fresh diagnostic controls."""
from __future__ import annotations

import argparse
import copy
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from run_eval import BASE, digest, encoded, load_julia, read_json, utc_now, write_json

RUN = BASE / "runs/20261020T-diagnostic"
OUT = RUN / "phase2"


def prepare() -> None:
    rows = []
    for state_id in ("python_raw", "react_raw", "python_plain", "react_plain"):
        source = read_json(RUN / "requests" / f"{state_id}.json")
        for qid in ("original_react", "property_react_descriptive", "property_data_descriptive"):
            question = source["questions"][qid]
            for kind in ("noul", "choice"):
                for order in ("forward", "reversed"):
                    options = [question["criteria"]["false"], question["criteria"]["true"]]
                    if order == "reversed":
                        options.reverse()
                    rows.append({
                        "id": f"{state_id}/{qid}/{kind}/{order}",
                        "state": source["state"], "question": question["instructions"],
                        "options": options, "type": kind,
                        "semantic_true_index": 1 if order == "forward" else 0,
                    })
    write_json(OUT / "type-requests.json", rows, freeze=True)
    plan = {
        "prepared_at": utc_now(),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "scope": "Development diagnostics only; no new pilot accuracy or calibrated probabilities claimed.",
        "type_order": (
            "Raw low-level rows intentionally permute semantic descriptions. "
            "For reversed noul, index zero represents the positive description; "
            "these are serialization/position diagnostics, not standard typed-API true probabilities."
        ),
        "runtime_parity": "Compare identical rows with optimized versus original encoder.forward; no new weights.",
        "fresh_controls": "Independently authored eight small examples frozen before inference.",
    }
    if not (OUT / "plan.json").exists():
        write_json(OUT / "plan.json", plan, freeze=True)
    controls = read_json(RUN / "fresh-controls.json")
    requests = []
    for control in controls["cases"]:
        requests.append({
            "id": control["id"], "state": control["state"],
            "questions": {
                "family": {
                    "type": "choice",
                    "instructions": "Which kind of code is shown?",
                    "criteria": {
                        "react": "React user interface component",
                        "persistence": "Database and cache access",
                        "computation": "Ordinary computation without a user interface or data storage",
                    },
                },
                "react": {
                    "type": "noul",
                    "instructions": "Does the code use React components or React hooks?",
                    "criteria": {
                        "false": "The code does not use React components or React hooks.",
                        "true": "The code uses React components or React hooks.",
                    },
                },
                "persistence": {
                    "type": "noul",
                    "instructions": "Does the code read or write a database or cache?",
                    "criteria": {
                        "false": "The code does not read or write a database or cache.",
                        "true": "The code reads or writes a database or cache.",
                    },
                },
            },
        })
    write_json(OUT / "fresh-requests.json", requests, freeze=True)


def softmax(values: list[float]) -> list[float]:
    maximum = max(values)
    exp = [math.exp(value - maximum) for value in values]
    return [value / sum(exp) for value in exp]


def execute() -> None:
    if (OUT / "type-results.json").exists():
        raise ValueError("Refusing to overwrite completed diagnostics")
    rows = read_json(OUT / "type-requests.json")
    write_json(OUT / "execution.json", {
        "started_at": utc_now(),
        "executed_script_sha256": digest(Path(__file__).read_bytes()),
        "type_request_sha256": digest((OUT / "type-requests.json").read_bytes()),
        "fresh_request_sha256": digest((OUT / "fresh-requests.json").read_bytes()),
        "fresh_control_sha256": digest((RUN / "fresh-controls.json").read_bytes()),
    }, freeze=True)
    args = argparse.Namespace(
        batch_size=1, threads=4, allow_download=False,
        variant="type-parity", require_complete_catalog=True,
    )
    engine = load_julia(OUT, args)
    logits = engine.logits(rows)
    write_json(OUT / "type-results.json", [
        {
            "id": row["id"], "request_sha256": digest(encoded(row)),
            "logits": values,
            "positive_description_probability": softmax(values)[row["semantic_true_index"]],
        }
        for row, values in zip(rows, logits)
    ], freeze=True)
    print("Completed type/order controls", flush=True)
    encoder = engine.model.encoder
    specialized = encoder.forward
    if not hasattr(encoder, "_julia_original_forward"):
        raise ValueError("Expected upstream original forward is unavailable")
    parity_rows = rows[:8]
    encoder.forward = encoder._julia_original_forward
    try:
        original_logits = engine.logits(parity_rows)
    finally:
        encoder.forward = specialized
    write_json(OUT / "encoder-parity.json", [
        {
            "id": row["id"], "optimized_logits": optimized,
            "original_logits": original,
            "max_absolute_delta": max(abs(a - b) for a, b in zip(optimized, original)),
            "same_argmax": max(range(len(optimized)), key=optimized.__getitem__) == max(range(len(original)), key=original.__getitem__),
        }
        for row, optimized, original in zip(parity_rows, logits[:8], original_logits)
    ], freeze=True)
    print("Completed encoder parity", flush=True)
    for request in read_json(OUT / "fresh-requests.json"):
        raw = engine.predict(state=request["state"], questions=request["questions"])
        write_json(OUT / "fresh-results" / f"{request['id']}.json", {
            "id": request["id"], "request_sha256": digest(encoded(request)),
            "raw_output": raw,
        }, freeze=True)
        print(f"Completed fresh control {request['id']}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run"])
    args = parser.parse_args()
    {"prepare": prepare, "run": execute}[args.action]()
