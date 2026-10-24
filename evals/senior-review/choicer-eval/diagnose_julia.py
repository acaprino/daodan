"""Frozen local controls for separating Julia runtime and question-design faults."""
from __future__ import annotations

import argparse
import copy
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True

from run_eval import (
    BASE, digest, encoded, load_julia, read_json, utc_now, write_json,
)

RUN = BASE / "runs/20261020T-diagnostic"
SOURCE = BASE / "runs/20261020T100258Z-adapted"


def prepare() -> list[dict]:
    """Fix controls and expected signals before executing any new prediction."""
    original = read_json(SOURCE / "requests/julia/noul/C08-H1.json")
    dataset = read_json(SOURCE / "dataset.json")
    code = next(c for c in dataset["cases"] if c["id"] == "C08")["hunks"][0]["text"]
    react = "react-development:react-performance-optimizer"
    data = "senior-review:data-integrity-auditor"
    states = {
        "python_numbered": original["state"],
        "python_raw": code,
        "react_raw": (
            "import { useState } from 'react';\n"
            "export function Counter() {\n"
            "  const [count, setCount] = useState(0);\n"
            "  return <button onClick={() => setCount(count + 1)}>{count}</button>;\n"
            "}\n"
        ),
        "react_plain": "This file defines a React Counter component using useState and a button click handler.",
        "python_plain": (
            "This Python file defines asynchronous functions get_profile, update_email and delete_profile. "
            "get_profile reads a profile from Redis or MongoDB and writes it to Redis with a 300-second expiry. "
            "update_email and delete_profile write to MongoDB. The file contains no React components or browser UI."
        ),
    }
    questions = {
        "original_react": copy.deepcopy(original["questions"][react]),
        "original_data": copy.deepcopy(original["questions"][data]),
        "complement_react": {
            "type": "noul",
            "instructions": original["questions"][react]["instructions"],
            "criteria": {
                "true": original["questions"][react]["criteria"]["true"],
                "false": "The code does not use React components, hooks, rendering or state subscriptions.",
            },
        },
        "property_react_literal": {
            "type": "noul", "instructions": "Does the code use React components or React hooks?",
        },
        "property_react_descriptive": {
            "type": "noul",
            "instructions": "Does the code use React components or React hooks?",
            "criteria": {
                "false": "The code does not use React components or React hooks.",
                "true": "The code uses React components or React hooks.",
            },
        },
        "property_data_descriptive": {
            "type": "noul",
            "instructions": "Does the code read or write a database or cache?",
            "criteria": {
                "false": "The code does not read or write a database or cache.",
                "true": "The code reads or writes a database or cache.",
            },
        },
        "property_stack_choice": {
            "type": "choice",
            "instructions": "Which kind of code is shown?",
            "criteria": {
                "backend": "Python database and cache access",
                "frontend": "React user interface component",
            },
        },
        "property_stack_reversed": {
            "type": "choice",
            "instructions": "Which kind of code is shown?",
            "criteria": {
                "frontend": "React user interface component",
                "backend": "Python database and cache access",
            },
        },
    }
    requests = [{
        "id": "official_billing",
        "state": "I was charged twice for the same order.",
        "questions": {"team": {
            "type": "choice",
            "instructions": "Which team should handle this request?",
            "criteria": {
                "billing": "Billing and payment disputes",
                "shipping": "Shipping and delivery",
                "access": "Account access and login",
            },
        }},
    }]
    expected = {"official_billing": {"team": "billing"}}
    for state_id, state in states.items():
        requests.append({"id": state_id, "state": state, "questions": copy.deepcopy(questions)})
        is_react = state_id.startswith("react")
        expected[state_id] = {
            "original_react": is_react,
            "original_data": not is_react,
            "complement_react": is_react,
            "property_react_literal": is_react,
            "property_react_descriptive": is_react,
            "property_data_descriptive": not is_react,
            "property_stack_choice": "frontend" if is_react else "backend",
            "property_stack_reversed": "frontend" if is_react else "backend",
        }
    write_json(RUN / "plan.json", {
        "prepared_at": utc_now(), "purpose": __doc__,
        "threshold": 0.5,
        "hypotheses": [
            "Noncomplementary role criteria force an inapplicable choice.",
            "Abstract routing instructions fail while concrete observable-property questions discriminate.",
            "Runtime or serialization fault also breaks official elementary controls.",
        ],
        "interpretation": (
            "Diagnostic examples are development controls, not an independent benchmark. "
            "Natural-language summaries are manually authored experimental representations, not measured free routing inputs. "
            "Expected answers remain separate from model submissions."
        ),
        "expected": expected,
        "source_request_sha256": original["request_sha256"],
        "script_sha256": digest(Path(__file__).read_bytes()),
    }, freeze=True)
    for request in requests:
        request["sha256"] = digest(encoded(request))
        write_json(RUN / "requests" / f"{request['id']}.json", request, freeze=True)
    return requests


def execute() -> None:
    requests = [read_json(path) for path in sorted((RUN / "requests").glob("*.json"))]
    if not requests:
        raise ValueError("Prepare and freeze controls first")
    args = argparse.Namespace(
        batch_size=1, threads=4, allow_download=False,
        variant="diagnostic", require_complete_catalog=True,
    )
    engine = load_julia(RUN, args)
    for request in requests:
        target = RUN / "results" / f"{request['id']}.json"
        if target.exists():
            raise ValueError(f"Diagnostic output already exists: {target}")
        payload = {key: request[key] for key in ("state", "questions")}
        write_json(RUN / "wire" / f"{request['id']}.json", payload, freeze=True)
        started = time.perf_counter()
        raw = engine.predict(**payload)
        write_json(target, {
            "id": request["id"], "request_sha256": request["sha256"],
            "wall_seconds": time.perf_counter() - started,
            "model_session_id": engine.benchmark_session_id,
            "raw_output": raw,
        }, freeze=True)
        print(f"Completed {request['id']}", flush=True)


def summarize() -> None:
    expected = read_json(RUN / "plan.json")["expected"]
    rows = []
    for path in sorted((RUN / "results").glob("*.json")):
        result = read_json(path)
        request = read_json(RUN / "requests" / path.name)
        assert result["request_sha256"] == request["sha256"]
        for qid, answer in result["raw_output"]["answers"].items():
            actual = answer["noul"] >= 0.5 if answer["type"] == "noul" else answer["choice"]
            rows.append({
                "input": result["id"], "question": qid,
                "expected": expected[result["id"]][qid], "actual": actual,
                "p_true": answer.get("noul"), "correct": actual == expected[result["id"]][qid],
                "probabilities": answer["probabilities"],
            })
    write_json(RUN / "diagnostic-summary.json", {"rows": rows})
    for row in rows:
        print(f"{row['input']:18} {row['question']:29} expected={str(row['expected']):8} actual={str(row['actual']):8} p_true={row['p_true']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run", "summarize"])
    action = parser.parse_args().action
    {"prepare": prepare, "run": execute, "summarize": summarize}[action]()
