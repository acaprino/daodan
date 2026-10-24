"""Evaluate every registered review lens individually and as a selected team."""
from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True

from dataset import extract_catalog
from run_eval import (
    BASE, REPO, JULIA_REVISION, JULIA_WEIGHT_SHA256, digest, encoded, initialize, load_julia, model_cache, read_json, utc_now, write_json,
    write_text,
)

SOURCE = BASE / "all-reviewers"
RUN = BASE / "runs/20261020T-all-reviewers"
VARIANTS = ("catalog_noul", "grounded_noul", "grounded_choice")
FROZEN_INPUTS = ("suite.json", "catalog.json", "inventory.json")
RUNTIME_SOURCES = ("all_reviewers_eval.py", "run_eval.py", "dataset.py")


def verify_frozen_inputs() -> None:
    """Bind scorer labels and execution code as well as model-visible requests."""
    plan = read_json(RUN / "plan.json")
    if set(plan.get("frozen_inputs", {})) != set(FROZEN_INPUTS):
        raise ValueError("Run plan lacks frozen scorer input bindings")
    for name in FROZEN_INPUTS:
        if digest((RUN / name).read_bytes()) != plan["frozen_inputs"][name]:
            raise ValueError(f"Frozen input changed: {name}")
    if set(plan.get("runtime_sources", {})) != set(RUNTIME_SOURCES):
        raise ValueError("Run plan lacks execution source bindings")
    for name in RUNTIME_SOURCES:
        if digest((BASE / name).read_bytes()) != plan["runtime_sources"][name]:
            raise ValueError(f"Execution source changed: {name}; start a new run")
    for name, expected in plan["source_hashes"].items():
        if Path(name).name != name or digest((SOURCE / name).read_bytes()) != expected:
            raise ValueError(f"Prepared source changed: {name}")


def decode_answers(request: dict, raw: dict) -> tuple[dict, list[str]]:
    """Validate and derive decisions using the requested binary semantics."""
    if not isinstance(raw, dict) or not isinstance(raw.get("answers"), dict):
        raise ValueError("Model output lacks an answer mapping")
    answers = raw["answers"]
    if set(answers) != set(request["questions"]):
        raise ValueError("Model returned a different question set")
    probabilities, selected = {}, []
    for qid, question_spec in request["questions"].items():
        answer = answers[qid]
        kind = question_spec["type"]
        if not isinstance(answer, dict) or answer.get("type") != kind or kind not in {"noul", "choice"}:
            raise ValueError("Answer type differs from requested type")
        p = answer.get("probabilities")
        if not isinstance(p, dict) or set(p) != {"false", "true"} or any(
            type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in p.values()
        ):
            raise ValueError("Invalid binary probabilities")
        if not math.isclose(sum(p.values()), 1.0, rel_tol=0, abs_tol=1e-6):
            raise ValueError("Unnormalized probabilities")
        probabilities[qid] = p["true"]
        if kind == "choice":
            if list(question_spec["criteria"]) != ["false", "true"]:
                raise ValueError("Choice criteria must keep false before true")
            winner = "true" if p["true"] > p["false"] else "false"
            if answer.get("choice") != winner:
                raise ValueError("Categorical answer disagrees with binary argmax")
            active = winner == "true"
        else:
            if "noul" in answer and (
                type(answer["noul"]) not in (int, float)
                or not math.isfinite(answer["noul"])
                or not math.isclose(answer["noul"], p["true"], rel_tol=0, abs_tol=1e-9)
            ):
                raise ValueError("Noul answer disagrees with true probability")
            active = p["true"] >= 0.5
        if active:
            selected.append(qid)
    return probabilities, selected


def model_sessions(metadata: dict) -> set[str]:
    """Reject mixed checkpoint identities when a run resumes."""
    model = metadata.get("models", {}).get("julia/all-reviewers", {})
    sessions = model.get("load_sessions", [])
    ids = set()
    checkpoint_files = None
    for session in sessions:
        if (
            session.get("revision") != JULIA_REVISION
            or session.get("weight_sha256") != JULIA_WEIGHT_SHA256
            or session.get("strict_encoding") is not True
            or session.get("marker_only_head") is not False
            or session.get("max_length") != 8192
            or not session.get("checkpoint_files")
            or not isinstance(session.get("session_id"), str)
            or not session["session_id"]
            or session["session_id"] in ids
        ):
            raise ValueError("Invalid or mismatched model session")
        if checkpoint_files is not None and checkpoint_files != session["checkpoint_files"]:
            raise ValueError("Cached checkpoint files changed between model sessions")
        checkpoint_files = session["checkpoint_files"]
        ids.add(session["session_id"])
    return ids


def validate_record(request: dict, record: dict, sessions: set[str]) -> None:
    if record.get("id") != request["id"] or record.get("request_sha256") != request["sha256"]:
        raise ValueError("Result/request mismatch")
    if record.get("model_session_id") not in sessions:
        raise ValueError("Result has no matching pinned model session")
    if record.get("status") not in {"ok", "error"} or type(record.get("inference_performed")) is not bool:
        raise ValueError("Invalid result completion status")
    if record["status"] == "ok":
        if not record["inference_performed"]:
            raise ValueError("Successful result lacks completed inference")
        probabilities, selected = decode_answers(request, record.get("raw_output"))
        if record.get("probabilities") != probabilities or record.get("selected") != selected:
            raise ValueError("Saved decisions disagree with complete raw output")
    elif record.get("probabilities") is not None or record.get("selected"):
        raise ValueError("Failed result contains scored decisions")


def question(role: dict, catalog: dict, variant: str) -> dict:
    if variant == "catalog_noul":
        return {
            "type": "noul",
            "instructions": "Does the supplied task and evidence satisfy the reviewer's TRIGGER WHEN?",
            "criteria": {
                "false": catalog["do_not_trigger_when"] or "",
                "true": catalog["trigger_when"] or "",
            },
        }
    return {
        "type": "noul" if variant == "grounded_noul" else "choice",
        "instructions": role["question"],
        "criteria": {"false": role["criteria"]["false"], "true": role["criteria"]["true"]},
    }


def validate_suite(roles: list[dict], teams: list[dict], catalog: dict) -> None:
    ids = {role["role_id"] for role in roles}
    if len(ids) != len(roles) or len(ids) != 22:
        raise ValueError("The audited inventory requires exactly 22 unique lenses")
    source_ids = {row["id"] for row in catalog["roles"]}
    if ids - source_ids:
        raise ValueError(f"Unregistered lenses: {sorted(ids - source_ids)}")
    audited = set(catalog["reviewer_ids"]) | {
        "project-knowledge:guide-reviewer", "project-knowledge:instructions-auditor",
        "project-knowledge:documentation-engineer", "project-knowledge:doc-humanizer",
    }
    if ids != audited:
        raise ValueError(f"Suite differs from audited reviewer inventory: {sorted(ids ^ audited)}")
    case_ids = set()
    for role in roles:
        path = REPO / role["source_path"]
        if digest(path.read_bytes()) != role["source_sha256"]:
            raise ValueError(f"Source changed: {path}")
        if not isinstance(role["question"], str) or not role["question"].strip():
            raise ValueError(f"Missing self-contained question: {role['role_id']}")
        if set(role["criteria"]) != {"false", "true"} or not all(role["criteria"].values()):
            raise ValueError(f"Missing complementary criteria: {role['role_id']}")
        cases = role["cases"]
        if len(cases) != 6 or sum(case["expected"] is True for case in cases) != 3:
            raise ValueError(f"Need three positive and three negative cases: {role['role_id']}")
        for case in cases:
            if type(case["expected"]) is not bool:
                raise ValueError("Individual expectations must be Boolean")
            if case["id"] in case_ids:
                raise ValueError("Duplicate case ID")
            case_ids.add(case["id"])
            validate_state(case["state"], ids)
    covered = set()
    for team in teams:
        if team["id"] in case_ids:
            raise ValueError("Duplicate team ID")
        case_ids.add(team["id"])
        validate_state(team["state"], ids)
        required = set(team["required_roles"])
        optional = set(team["allowed_roles"])
        if not required or required & optional or (required | optional) - ids:
            raise ValueError(f"Invalid required/allowed team: {team['id']}")
        covered.update(required)
    if covered != ids:
        raise ValueError(f"Every lens must be required in at least one team problem: {sorted(ids - covered)}")


def validate_state(state: dict, ids: set[str]) -> None:
    if set(state) != {"task", "artifacts"} or not isinstance(state["task"], str) or not state["task"]:
        raise ValueError("Model state must contain only task and artifacts")
    if not state["artifacts"]:
        raise ValueError("A control needs concrete evidence")
    for artifact in state["artifacts"]:
        if set(artifact) != {"path", "content"} or not all(isinstance(v, str) for v in artifact.values()):
            raise ValueError("Artifacts contain only path and content")
    if any(role in encoded(state) for role in ids):
        raise ValueError("Model state contains a reviewer ID")


def make_requests(roles: list[dict], teams: list[dict], catalog: dict) -> list[dict]:
    original = {row["id"]: row for row in catalog["roles"]}
    output = []
    for role in roles:
        for case in role["cases"]:
            for variant in VARIANTS:
                output.append({
                    "id": f"individual-{case['id']}-{variant}",
                    "kind": "individual", "case_id": case["id"], "variant": variant,
                    "state": case["state"],
                    "questions": {role["role_id"]: question(role, original[role["role_id"]], variant)},
                })
    for team in teams:
        for variant in VARIANTS[1:]:
            output.append({
                "id": f"team-{team['id']}-{variant}",
                "kind": "team", "case_id": team["id"], "variant": variant,
                "state": team["state"],
                "questions": {role["role_id"]: question(role, original[role["role_id"]], variant) for role in roles},
            })
    for request in output:
        request["sha256"] = digest(encoded(request))
    return output


def prepare() -> None:
    if any((RUN / "results").glob("*.json")):
        raise ValueError("Cannot change preparation after inference starts")
    catalog = extract_catalog(REPO)
    roles = [
        role for path in sorted(SOURCE.glob("group-*.json"))
        for role in read_json(path)["roles"]
    ]
    roles.sort(key=lambda role: role["role_id"])
    teams = read_json(SOURCE / "teams.json")["cases"]
    validate_suite(roles, teams, catalog)
    requests = make_requests(roles, teams, catalog)
    write_json(RUN / "suite.json", {"roles": roles, "teams": teams}, freeze=True)
    write_json(RUN / "catalog.json", catalog, freeze=True)
    write_json(RUN / "inventory.json", read_json(SOURCE / "inventory.json"), freeze=True)
    for request in requests:
        write_json(RUN / "requests" / f"{request['id']}.json", request, freeze=True)
    if not (RUN / "plan.json").exists():
        write_json(RUN / "plan.json", {
            "prepared_at": utc_now(), "threshold": 0.5,
            "tested_lenses": [role["role_id"] for role in roles],
            "individual_cases": sum(len(role["cases"]) for role in roles),
            "team_cases": len(teams), "requests": len(requests),
            "requested_binary_decisions": sum(len(request["questions"]) for request in requests),
            "variants": {
                "catalog_noul": "Exact extracted trigger text; incompatible inputs remain failures, not negative predictions.",
                "grounded_noul": "Independently authored applicability question with complementary short descriptions.",
                "grounded_choice": "Same question/descriptions; categorical false/true choice independently for each lens.",
            },
            "team_rule": "Ask every lens independently; select all with true probability >=0.5 (choice uses argmax with false first). No single-winner team constraint.",
            "ground_truth": (
                "Individual relevance has explicit positive and negative controls. Team required_roles are mandatory, "
                "allowed_roles are acceptable additions, and the complement is forbidden within the stated task scope. "
                "Allowed roles never count as false positives. No complete-team decision is scored from partial outputs."
            ),
            "limitations": (
                "Synthetic task-plus-evidence selection controls authored before predictions. Not actual reviewer execution, "
                "production coverage, measured token savings, or proof of equivalence to exact kernel triggers. "
                "Compact criteria and fixtures share role-source knowledge; independent review checks labels before inference."
            ),
            "source_hashes": {path.name: digest(path.read_bytes()) for path in sorted(SOURCE.glob("*.json"))},
            "script_sha256": digest(Path(__file__).read_bytes()),
            "frozen_inputs": {name: digest((RUN / name).read_bytes()) for name in FROZEN_INPUTS},
            "runtime_sources": {name: digest((BASE / name).read_bytes()) for name in RUNTIME_SOURCES},
        }, freeze=True)
    verify_frozen_inputs()
    print(f"Prepared {len(roles)} lenses, {len(requests)} requests")


def capacity() -> None:
    """Check tokenizer limits without loading weights or inspecting predictions."""
    model_cache()
    checkpoint = BASE / ".cache/huggingface/hub/models--SupersonicLabs--Julia-1/snapshots" / JULIA_REVISION
    sys.path.insert(0, str(checkpoint))
    from transformers import AutoTokenizer
    from julia.data import sequence

    tokenizer = AutoTokenizer.from_pretrained(checkpoint / "tokenizer", local_files_only=True)
    catalog = extract_catalog(REPO)
    roles = [role for path in sorted(SOURCE.glob("group-*.json")) for role in read_json(path)["roles"]]
    teams = read_json(SOURCE / "teams.json")["cases"]
    validate_suite(roles, teams, catalog)
    failures, valid, max_tokens = [], 0, 0
    for request in make_requests(roles, teams, catalog):
        for qid, q in request["questions"].items():
            try:
                result = sequence(tokenizer, {
                    "state": request["state"], "question": q["instructions"],
                    "type": q["type"], "options": list(q["criteria"].values()),
                }, max_length=8192, head_length=512, strict=True)
                # sequence checks lengths; empty descriptions are checked separately.
                if not all(q["criteria"].values()):
                    raise ValueError("Empty criterion")
                valid += 1
                max_tokens = max(max_tokens, len(result["ids"]))
            except ValueError as error:
                failures.append({"request": request["id"], "role": qid, "variant": request["variant"], "error": str(error)})
    write_json(SOURCE / "capacity.json", {
        "recorded_at": utc_now(), "valid_questions": valid, "max_tokens": max_tokens,
        "failures": failures, "weights_loaded": False,
        "source_hashes": {p.name: digest(p.read_bytes()) for p in SOURCE.glob("*.json") if p.name != "capacity.json"},
    })
    unexpected = [row for row in failures if row["variant"] != "catalog_noul"]
    print(f"Tokenizer-only validation: {valid} valid; {len(failures)} exact-catalog failures; {len(unexpected)} grounded failures; max {max_tokens} tokens.")
    if unexpected:
        raise ValueError(f"Grounded criteria or states need lossless preparation: {unexpected}")


def verify_request(request: dict) -> None:
    body = {key: value for key, value in request.items() if key != "sha256"}
    if request["sha256"] != digest(encoded(body)):
        raise ValueError(f"Request changed: {request['id']}")


def execute(resume: bool) -> None:
    verify_frozen_inputs()
    suite = read_json(RUN / "suite.json")
    expected = {r["id"]: r for r in make_requests(suite["roles"], suite["teams"], read_json(RUN / "catalog.json"))}
    paths = sorted((RUN / "requests").glob("*.json"))
    if len(paths) != len(expected):
        raise ValueError("Missing or unexpected request files")
    metadata = initialize(RUN)
    sessions = model_sessions(metadata)
    pending = []
    for path in paths:
        request = read_json(path)
        verify_request(request)
        if path.name != f"{request['id']}.json" or request != expected.get(request["id"]):
            raise ValueError("Request differs from frozen suite")
        target = RUN / "results" / path.name
        if target.exists():
            if not resume:
                raise ValueError("Use --resume to preserve completed output")
            validate_record(request, read_json(target), sessions)
        else:
            pending.append(request)
    if not pending:
        return
    args = argparse.Namespace(
        batch_size=1, threads=4, allow_download=False,
        variant="all-reviewers", require_complete_catalog=True,
    )
    metadata["gates"] = [
        {"gate": "runtime", "status": "Reuse of the previously authorized local environment; no new environment created."},
        {"gate": "Julia weights", "status": "Previously authorized cached, pinned weights; offline loading only."},
        {"gate": "paid LLM baseline", "status": "Not part of this follow-up; no new calls."},
    ]
    metadata["anomalies"] = [
        "This follow-up uses fresh synthetic task-plus-artifact controls, not the original hunk corpus.",
        "Exact catalog questions preserve missing or oversized options as unavailable inputs.",
        "Grounded criteria are declared adaptations from source charters, not verbatim frontmatter.",
        "No actual reviewer-agent execution, production reliability or token savings are measured.",
    ]
    metadata["provenance"]["all_reviewers_eval_sha256"] = digest(Path(__file__).read_bytes())
    write_json(RUN / "metadata.json", metadata)
    engine = load_julia(RUN, args)
    sessions = model_sessions(read_json(RUN / "metadata.json"))
    started = time.perf_counter()
    for index, request in enumerate(pending, 1):
        record = {
            "id": request["id"], "request_sha256": request["sha256"],
            "status": "error", "raw_output": None, "probabilities": None,
            "inference_performed": False, "model_session_id": engine.benchmark_session_id,
        }
        call_start = time.perf_counter()
        errors, encodings = {}, {}
        for qid, q in request["questions"].items():
            row = {
                "state": request["state"], "question": q["instructions"],
                "type": q["type"], "options": list(q["criteria"].values()),
            }
            try:
                encodings[qid] = engine.encoding_info([row])[0]
            except Exception as error:
                errors[qid] = f"{type(error).__name__}: {error}"
        record["encoding"] = encodings
        record["encoding_errors"] = errors
        if not errors:
            payload = {"state": request["state"], "questions": request["questions"]}
            write_json(RUN / "wire" / f"{request['id']}.json", payload, freeze=True)
            try:
                raw = engine.predict(**payload)
                record["raw_output"] = raw
                record["inference_performed"] = True
                probabilities, selected = decode_answers(request, raw)
                record.update(status="ok", probabilities=probabilities, selected=selected)
            except Exception as error:
                record["error"] = f"{type(error).__name__}: {error}"
        record["wall_seconds"] = time.perf_counter() - call_start
        validate_record(request, record, sessions)
        write_json(RUN / "results" / f"{request['id']}.json", record, freeze=True)
        if index % 12 == 0 or index == len(pending):
            print(f"Completed {index}/{len(pending)} requests; elapsed {time.perf_counter()-started:.1f}s", flush=True)


def score_individual(cases: list[dict], predictions: dict[str, bool]) -> dict:
    available = [case for case in cases if case["id"] in predictions]
    return {
        "available": len(available), "expected_cases": len(cases),
        "tp": sum(case["expected"] and predictions[case["id"]] for case in available),
        "fn": sum(case["expected"] and not predictions[case["id"]] for case in available),
        "fp": sum(not case["expected"] and predictions[case["id"]] for case in available),
        "tn": sum(not case["expected"] and not predictions[case["id"]] for case in available),
    }


def score_team(case: dict, selected: list[str], all_roles: set[str]) -> dict:
    chosen, required, allowed = set(selected), set(case["required_roles"]), set(case["allowed_roles"])
    if chosen - all_roles:
        raise ValueError("Unknown selected role")
    return {
        "selected": sorted(chosen), "required": sorted(required), "allowed": sorted(allowed),
        "missing": sorted(required - chosen), "false_positives": sorted(chosen - required - allowed),
        "required_hits": len(chosen & required), "required_support": len(required),
        "acceptable_team": required <= chosen <= required | allowed,
        "exact_required_team": chosen == required,
    }


def report() -> None:
    verify_frozen_inputs()
    suite = read_json(RUN / "suite.json")
    roles, teams = suite["roles"], suite["teams"]
    requests = make_requests(roles, teams, read_json(RUN / "catalog.json"))
    sessions = model_sessions(read_json(RUN / "metadata.json"))
    records = {}
    for request in requests:
        path = RUN / "results" / f"{request['id']}.json"
        if not path.exists():
            raise ValueError(f"Execution incomplete: {path.name}")
        record = read_json(path)
        validate_record(request, record, sessions)
        records[request["id"]] = record
    individual, team_results = {}, {}
    ids = {role["role_id"] for role in roles}
    for variant in VARIANTS:
        individual[variant] = {}
        for role in roles:
            predictions = {}
            for case in role["cases"]:
                record = records[f"individual-{case['id']}-{variant}"]
                if record["status"] == "ok":
                    predictions[case["id"]] = role["role_id"] in record["selected"]
            individual[variant][role["role_id"]] = score_individual(role["cases"], predictions)
    for variant in VARIANTS[1:]:
        team_results[variant] = {}
        for team in teams:
            record = records[f"team-{team['id']}-{variant}"]
            team_results[variant][team["id"]] = (
                score_team(team, record["selected"], ids) if record["status"] == "ok"
                else {"status": "unavailable"}
            )
    scores = {
        "individual": individual, "teams": team_results,
        "attempted_requests": len(records),
        "successful_requests": sum(r["status"] == "ok" for r in records.values()),
        "actual_classification_decisions": sum(len(r["probabilities"] or {}) for r in records.values()),
    }
    summary = {}
    for variant in VARIANTS:
        rows = list(individual[variant].values())
        totals = {key: sum(row[key] for row in rows) for key in ("available", "tp", "fn", "fp", "tn")}
        totals["fully_correct_roles"] = [
            rid for rid, row in individual[variant].items()
            if row["available"] == 6 and row["tp"] == 3 and row["tn"] == 3
        ]
        summary[variant] = {"individual": totals}
        if variant in team_results:
            available_teams = [row for row in team_results[variant].values() if "status" not in row]
            summary[variant]["teams"] = {
                "available": len(available_teams),
                "acceptable": sum(row["acceptable_team"] for row in available_teams),
                "exact_required": sum(row["exact_required_team"] for row in available_teams),
                "required_hits": sum(row["required_hits"] for row in available_teams),
                "required_support": sum(row["required_support"] for row in available_teams),
                "false_positives": sum(len(row["false_positives"]) for row in available_teams),
                "selected": sum(len(row["selected"]) for row in available_teams),
            }
    scores["summary"] = summary
    scores["grounded_execution_complete"] = all(
        record["status"] == "ok" and record["inference_performed"]
        for request in requests if request["variant"] != "catalog_noul"
        for record in [records[request["id"]]]
    )
    write_json(RUN / "scores.json", scores)
    lines = [
        "# All-reviewer selection evaluation",
        "",
        f"Tested {len(roles)} registered lenses: 21 independent reviewers/auditors and the document-structure audit hybrid. "
        f"The suite contains {sum(len(r['cases']) for r in roles)} individual controls and {len(teams)} complete problems.",
        "",
        "This measures Julia's selection decisions. The reviewer agents themselves were not run against defects. "
        "All inputs include the task and concrete source/document evidence. This is a new synthetic selection suite, "
        "not directly comparable with the earlier code-hunk pilot. Questions and labels were fixed before inference; "
        "no threshold tuning or paid LLM baseline was performed.",
        "",
        f"Execution coverage: {scores['successful_requests']}/{len(records)} requests returned complete outputs; "
        f"{scores['actual_classification_decisions']} binary decisions were classified. "
        f"All grounded controls completed actual inference: {scores['grounded_execution_complete']}. "
        "Catalog input rejections are not negative predictions.",
        "",
        "| Variant | Individual correct | Required positive roles found | Negative controls incorrectly activated | Roles with all six controls correct |",
        "| --- | --- | --- | --- | --- |",
    ]
    for variant, value in summary.items():
        row = value["individual"]
        lines.append(
            f"| {variant} | {row['tp']+row['tn']}/{row['available']} | {row['tp']}/{row['tp']+row['fn']} | "
            f"{row['fp']}/{row['fp']+row['tn']} | {len(row['fully_correct_roles'])}/{len(roles)} |"
        )
    lines.extend([
        "",
        "## Individual reviewers",
        "",
        "Every lens has three positive and three negative controls. Cells show true positives / positive support, "
        "then false positives / negative support. Missing or incompatible outputs remain unavailable.",
        "",
        "| Reviewer | Exact catalog | Grounded noul | Grounded binary choice |",
        "| --- | --- | --- | --- |",
    ])
    for role in roles:
        cells = []
        for variant in VARIANTS:
            value = individual[variant][role["role_id"]]
            cells.append(
                f"{value['tp']}/{value['tp'] + value['fn']} TP; {value['fp']}/{value['fp'] + value['tn']} FP"
                f" ({value['available']}/6 available)"
            )
        lines.append("| " + " | ".join([role["role_id"], *cells]) + " |")
    lines.extend([
        "",
        "The exact catalog preserves extracted frontmatter strings. Missing negative criteria and oversized options "
        "are recorded as input incompatibilities. Grounded variants are explicitly authored adaptations to the role "
        "bodies. The binary choice variant uses the same descriptions, independently for every reviewer; "
        "it does not force a team to contain one person.",
        "",
        "## Selected teams",
        "",
        "Each problem specifies mandatory and acceptable optional reviewers. Every other lens is forbidden within "
        "the stated scope. An acceptable team includes every mandatory lens and no forbidden lens. "
        "Exact-required equality additionally excludes optional additions; it is reported separately. "
        "A missing or partial decision cannot form a scored team.",
        "",
        "| Variant | Acceptable teams | Exact required teams | Mandatory reviewers found | Out-of-scope selections | Total selected |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for variant in VARIANTS[1:]:
        row = summary[variant]["teams"]
        lines.append(
            f"| {variant} | {row['acceptable']}/{row['available']} | {row['exact_required']}/{row['available']} | "
            f"{row['required_hits']}/{row['required_support']} | {row['false_positives']} | {row['selected']} |"
        )
    lines.extend([
        "",
        "| Problem | Variant | Required found | Missing | Out-of-scope selections | Team acceptable |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for team in teams:
        for variant in VARIANTS[1:]:
            value = team_results[variant][team["id"]]
            if "status" in value:
                lines.append(f"| {team['id']} | {variant} | unavailable | unavailable | unavailable | unavailable |")
                continue
            lines.append(
                f"| {team['id']} | {variant} | {value['required_hits']}/{value['required_support']} | "
                f"{', '.join(value['missing']) or 'none'} | {', '.join(value['false_positives']) or 'none'} | "
                f"{value['acceptable_team']} |"
            )
    lines.extend([
        "",
        "## Evidence and limits",
        "",
        "[Frozen suite](runs/20261020T-all-reviewers/suite.json) contains each expected answer, source locator "
        "and rationale. [Inventory](runs/20261020T-all-reviewers/inventory.json) classifies all registered roles. "
        "[Scoring JSON](runs/20261020T-all-reviewers/scores.json) retains every selected team and individual confusion counts. "
        "The run also preserves exact requests, actual submitted payloads, raw outputs, encoding diagnostics and model identity.",
        "",
        "These few controls per role expose failures and coverage gaps; they cannot certify production reliability. "
        "Team labels are explicit scope judgments, not exhaustive universal truths about reviewer usefulness. "
        "A role may be relevant to multiple artifacts; optional eligibility prevents treating every reasonable extra "
        "reviewer as a proven error. Actual review effectiveness, runtime savings and net token economics remain unmeasured.",
        "",
        "Rebuild without inference:",
        "",
        "```powershell",
        "python -B evals/senior-review/choicer-eval/all_reviewers_eval.py report",
        "```",
        "",
    ])
    write_text(BASE / "ALL_REVIEWERS_RESULTS.md", "\n".join(lines))
    print(f"Wrote ALL_REVIEWERS_RESULTS.md: {scores['successful_requests']}/{len(records)} requests successful")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "capacity", "run", "report"])
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.action == "run":
        execute(args.resume)
    else:
        {"prepare": prepare, "capacity": capacity, "report": report}[args.action]()
