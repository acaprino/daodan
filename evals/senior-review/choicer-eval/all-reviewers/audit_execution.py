"""Independently verify frozen reviewer-selection requests, outputs and scores.

This auditor imports only the standard library. It does not import the runner,
its decoder, its scoring helpers or any model package. Run only after inference
and score generation are complete. --self-test does not read run artifacts.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[2]
SOURCE = BASE / "all-reviewers"
DEFAULT_RUN = BASE / "runs/20261020T-all-reviewers"
VARIANTS = ("catalog_noul", "grounded_noul", "grounded_choice")
REVISION = "a85b127321d580d65176c89ced8273f305745d85"
WEIGHT_SHA256 = "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"
CRITICAL_ROLES = (
    "senior-review:security-auditor",
    "senior-review:premise-auditor",
    "senior-review:data-integrity-auditor",
)


class AuditError(ValueError):
    """A frozen-input, execution-evidence or arithmetic mismatch."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def encode(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def object_hash(value: object) -> str:
    return hashlib.sha256(encode(value).encode("utf-8")).hexdigest()


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        require(key not in value, f"Duplicate JSON key: {key}")
        value[key] = item
    return value


def invalid_number(value: str) -> None:
    raise AuditError(f"Non-finite JSON number: {value}")


def read(path: Path) -> dict:
    require(path.is_file(), f"Missing artifact: {path}")
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=unique_object,
        parse_constant=invalid_number,
    )


def confined(path: Path) -> Path:
    path = path.resolve()
    require(path.is_relative_to(BASE), f"Path escapes benchmark root: {path}")
    return path


def check_state(state: dict, role_ids: set[str], locator: str) -> None:
    require(set(state) == {"task", "artifacts"}, f"{locator}: state contains scorer fields")
    require(isinstance(state["task"], str) and bool(state["task"]), f"{locator}: empty task")
    require(isinstance(state["artifacts"], list) and bool(state["artifacts"]), f"{locator}: no evidence")
    for artifact in state["artifacts"]:
        require(set(artifact) == {"path", "content"}, f"{locator}: extra artifact fields")
        require(all(isinstance(value, str) for value in artifact.values()), f"{locator}: invalid artifact")
    text = encode(state)
    require(not any(name in text for name in role_ids), f"{locator}: reviewer ID leaked into state")
    require(not any(name.split(":")[1] in text for name in role_ids), f"{locator}: reviewer label leaked into state")


def question_spec(role: dict, catalog_role: dict, variant: str) -> dict:
    if variant == "catalog_noul":
        return {
            "type": "noul",
            "instructions": "Does the supplied task and evidence satisfy the reviewer's TRIGGER WHEN?",
            "criteria": {
                "false": catalog_role["do_not_trigger_when"] or "",
                "true": catalog_role["trigger_when"] or "",
            },
        }
    return {
        "type": "choice" if variant == "grounded_choice" else "noul",
        "instructions": role["question"],
        "criteria": {"false": role["criteria"]["false"], "true": role["criteria"]["true"]},
    }


def reconstruct_requests(suite: dict, catalog: dict) -> dict[str, dict]:
    output = {}
    catalog_by_id = {row["id"]: row for row in catalog["roles"]}
    for role in suite["roles"]:
        for case in role["cases"]:
            for variant in VARIANTS:
                request = {
                    "id": f"individual-{case['id']}-{variant}",
                    "kind": "individual",
                    "case_id": case["id"],
                    "variant": variant,
                    "state": case["state"],
                    "questions": {
                        role["role_id"]: question_spec(role, catalog_by_id[role["role_id"]], variant)
                    },
                }
                request["sha256"] = object_hash(request)
                output[request["id"]] = request
    for case in suite["teams"]:
        for variant in VARIANTS[1:]:
            request = {
                "id": f"team-{case['id']}-{variant}",
                "kind": "team",
                "case_id": case["id"],
                "variant": variant,
                "state": case["state"],
                "questions": {
                    role["role_id"]: question_spec(role, catalog_by_id[role["role_id"]], variant)
                    for role in suite["roles"]
                },
            }
            request["sha256"] = object_hash(request)
            output[request["id"]] = request
    return output


def decode_independently(request: dict, raw: dict) -> tuple[dict, list[str]]:
    require(isinstance(raw, dict) and isinstance(raw.get("answers"), dict), "Missing complete raw answer mapping")
    answers = raw["answers"]
    require(set(answers) == set(request["questions"]), "Raw output question set differs from request")
    positive_probabilities, selected = {}, []
    for role_id, spec in request["questions"].items():
        answer = answers[role_id]
        require(isinstance(answer, dict), f"{role_id}: answer is not an object")
        require(answer.get("type") == spec["type"] and spec["type"] in {"noul", "choice"}, f"{role_id}: type mismatch")
        require(list(spec["criteria"]) == ["false", "true"], f"{role_id}: option order changed")
        values = answer.get("probabilities")
        require(isinstance(values, dict) and set(values) == {"false", "true"}, f"{role_id}: binary outcomes missing")
        require(
            all(type(p) in (int, float) and math.isfinite(p) and 0 <= p <= 1 for p in values.values()),
            f"{role_id}: invalid probability",
        )
        require(math.isclose(values["false"] + values["true"], 1, rel_tol=0, abs_tol=1e-6), f"{role_id}: not normalized")
        positive_probabilities[role_id] = values["true"]
        if spec["type"] == "choice":
            chosen = "false"
            if values["true"] > values["false"]:
                chosen = "true"
            require(answer.get("choice") == chosen, f"{role_id}: saved categorical choice disagrees with argmax")
            active = chosen == "true"
        else:
            if "noul" in answer:
                require(
                    type(answer["noul"]) in (int, float)
                    and math.isfinite(answer["noul"])
                    and math.isclose(answer["noul"], values["true"], rel_tol=0, abs_tol=1e-9),
                    f"{role_id}: noul scalar differs from true probability",
                )
            active = values["true"] >= 0.5
        if active:
            selected.append(role_id)
    return positive_probabilities, selected


def independent_scores(suite: dict, records: dict, decoded: dict) -> dict:
    individual, teams, summaries = {}, {}, {}
    for variant in VARIANTS:
        individual[variant] = {}
        for role in suite["roles"]:
            row = {"available": 0, "expected_cases": 6, "tp": 0, "fn": 0, "fp": 0, "tn": 0}
            for case in role["cases"]:
                key = f"individual-{case['id']}-{variant}"
                if key not in decoded:
                    continue
                prediction = role["role_id"] in decoded[key][1]
                row["available"] += 1
                outcome = ("tp" if prediction else "fn") if case["expected"] else ("fp" if prediction else "tn")
                row[outcome] += 1
            individual[variant][role["role_id"]] = row
        rows = individual[variant]
        totals = {key: sum(row[key] for row in rows.values()) for key in ("available", "tp", "fn", "fp", "tn")}
        totals["fully_correct_roles"] = [
            role_id for role_id, row in rows.items()
            if row["available"] == 6 and row["tp"] == 3 and row["tn"] == 3
        ]
        summaries[variant] = {"individual": totals}
    for variant in VARIANTS[1:]:
        teams[variant] = {}
        for case in suite["teams"]:
            key = f"team-{case['id']}-{variant}"
            if key not in decoded:
                teams[variant][case["id"]] = {"status": "unavailable"}
                continue
            selected = set(decoded[key][1])
            mandatory, optional = set(case["required_roles"]), set(case["allowed_roles"])
            missing = mandatory.difference(selected)
            extra = selected.difference(mandatory.union(optional))
            teams[variant][case["id"]] = {
                "selected": sorted(selected), "required": sorted(mandatory), "allowed": sorted(optional),
                "missing": sorted(missing), "false_positives": sorted(extra),
                "required_hits": len(mandatory.intersection(selected)), "required_support": len(mandatory),
                "acceptable_team": not missing and not extra, "exact_required_team": selected == mandatory,
            }
        rows = [row for row in teams[variant].values() if "status" not in row]
        summaries[variant]["teams"] = {
            "available": len(rows),
            "acceptable": sum(row["acceptable_team"] for row in rows),
            "exact_required": sum(row["exact_required_team"] for row in rows),
            "required_hits": sum(row["required_hits"] for row in rows),
            "required_support": sum(row["required_support"] for row in rows),
            "false_positives": sum(len(row["false_positives"]) for row in rows),
            "selected": sum(len(row["selected"]) for row in rows),
        }
    return {
        "individual": individual, "teams": teams,
        "attempted_requests": len(records),
        "successful_requests": len(decoded),
        "actual_classification_decisions": sum(len(probabilities) for probabilities, _ in decoded.values()),
        "summary": summaries,
        "grounded_execution_complete": all(
            key in decoded and record["inference_performed"]
            for key, record in records.items() if not key.endswith("-catalog_noul")
        ),
    }


def detailed_role_metrics(suite: dict, scores: dict) -> dict:
    critical, team_role_metrics = {}, {}
    for variant in VARIANTS:
        rows = {role_id: scores["individual"][variant][role_id] for role_id in CRITICAL_ROLES}
        totals = {
            key: sum(row[key] for row in rows.values())
            for key in ("available", "expected_cases", "tp", "fn", "fp", "tn")
        }
        totals.update(expected_positive_controls=9, expected_negative_controls=9)
        critical[variant] = {"roles": rows, "totals": totals}
    for variant in VARIANTS[1:]:
        team_role_metrics[variant] = {}
        available = [row for row in scores["teams"][variant].values() if "status" not in row]
        for role in suite["roles"]:
            role_id = role["role_id"]
            metrics = {
                "required_hits": 0, "required_support": 0,
                "forbidden_fp": 0, "forbidden_opportunities": 0,
                "optional_selected": 0, "optional_opportunities": 0,
                "available_team_problems": len(available),
            }
            for row in available:
                chosen = role_id in row["selected"]
                if role_id in row["required"]:
                    metrics["required_support"] += 1
                    metrics["required_hits"] += int(chosen)
                elif role_id in row["allowed"]:
                    metrics["optional_opportunities"] += 1
                    metrics["optional_selected"] += int(chosen)
                else:
                    metrics["forbidden_opportunities"] += 1
                    metrics["forbidden_fp"] += int(chosen)
            team_role_metrics[variant][role_id] = metrics
    return {
        "critical_individual_controls": critical,
        "team_role_metrics": team_role_metrics,
    }


def calibration_metrics(suite: dict, records: dict, decoded: dict) -> dict:
    """Describe probability quality without selecting or changing a threshold."""
    output = {}
    for variant in VARIANTS:
        observations = []
        for role in suite["roles"]:
            for case in role["cases"]:
                key = f"individual-{case['id']}-{variant}"
                if key not in decoded:
                    continue
                probability = decoded[key][0][role["role_id"]]
                predicted = role["role_id"] in decoded[key][1]
                raw_probabilities = records[key]["raw_output"]["answers"][role["role_id"]]["probabilities"]
                observations.append({
                    "probability": probability,
                    "expected": int(case["expected"]),
                    "incorrect": predicted != case["expected"],
                    "winning_probability": max(raw_probabilities.values()),
                })
        bins = []
        for index in range(10):
            members = [
                row for row in observations
                if min(int(row["probability"] * 10), 9) == index
            ]
            count = len(members)
            mean = sum(row["probability"] for row in members) / count if count else None
            frequency = sum(row["expected"] for row in members) / count if count else None
            bins.append({
                "lower_bound": index / 10, "upper_bound": (index + 1) / 10,
                "upper_bound_inclusive": index == 9, "count": count,
                "mean_true_probability": mean, "observed_positive_fraction": frequency,
                "absolute_gap": abs(mean - frequency) if count else None,
            })
        available = len(observations)
        output[variant] = {
            "available_individual_controls": available,
            "expected_individual_controls": 132,
            "brier_score": (
                sum((row["probability"] - row["expected"]) ** 2 for row in observations) / available
                if available else None
            ),
            "ece_10_equal_width_bins": (
                sum(row["count"] * (row["absolute_gap"] or 0) for row in bins) / available
                if available else None
            ),
            "incorrect_decisions": sum(row["incorrect"] for row in observations),
            "winning_probability_at_least_0_9_decisions": sum(
                row["winning_probability"] >= 0.9 for row in observations
            ),
            "incorrect_with_winning_probability_at_least_0_9": sum(
                row["incorrect"] and row["winning_probability"] >= 0.9
                for row in observations
            ),
            "bins": bins,
            "interpretation": "Descriptive only. ECE compares true probability with the observed positive fraction. No decision threshold or fallback policy is tuned.",
        }
    return output


def audit(run: Path) -> dict:
    plan, suite, catalog = read(run / "plan.json"), read(run / "suite.json"), read(run / "catalog.json")
    hashes = {"frozen_inputs": {}, "source_inputs": {}, "runtime_sources": {}, "role_sources": {}, "requests": {}, "wire": {}, "results": {}}
    require(plan.get("threshold") == 0.5, "Threshold differs from preregistered 0.5")
    require(set(plan.get("frozen_inputs", {})) == {"suite.json", "catalog.json", "inventory.json"}, "Incomplete frozen scorer input bindings")
    require(set(plan.get("runtime_sources", {})) == {"all_reviewers_eval.py", "run_eval.py", "dataset.py"}, "Incomplete execution source bindings")
    for field, root, output in (
        ("frozen_inputs", run, "frozen_inputs"),
        ("source_hashes", SOURCE, "source_inputs"),
        ("runtime_sources", BASE, "runtime_sources"),
    ):
        for name, expected in plan[field].items():
            require(Path(name).name == name, f"Nonlocal frozen path: {name}")
            actual = file_hash(root / name)
            require(actual == expected, f"{field}: changed bytes in {name}")
            hashes[output][name] = actual
    roles, team_cases = suite["roles"], suite["teams"]
    role_ids = {role["role_id"] for role in roles}
    require(len(roles) == len(role_ids) == 22, "Expected 22 unique roles")
    require(plan["tested_lenses"] == [role["role_id"] for role in roles], "Planned lens inventory mismatch")
    require(len(team_cases) == 12, "Expected 12 complete team problems")
    require(role_ids <= {role["id"] for role in catalog["roles"]}, "Unregistered role in suite")
    audited_ids = set(catalog["reviewer_ids"]) | {
        "project-knowledge:guide-reviewer", "project-knowledge:instructions-auditor",
        "project-knowledge:documentation-engineer", "project-knowledge:doc-humanizer",
    }
    require(role_ids == audited_ids, "Frozen catalog reviewer inventory differs from suite")
    case_ids, covered = set(), set()
    for role in roles:
        source_path = (REPO / role["source_path"]).resolve()
        require(source_path.is_relative_to(REPO / "plugins"), "Role source outside plugin kernels")
        source_hash = file_hash(source_path)
        require(source_hash == role["source_sha256"], f"Role charter changed: {role['role_id']}")
        hashes["role_sources"][role["source_path"]] = source_hash
        require(len(role["cases"]) == 6, f"{role['role_id']}: not six cases")
        labels = [case["expected"] for case in role["cases"]]
        require(all(type(label) is bool for label in labels) and sum(labels) == 3, f"{role['role_id']}: invalid 3/3 labels")
        for case in role["cases"]:
            require(case["id"] not in case_ids, f"Repeated case ID: {case['id']}")
            case_ids.add(case["id"])
            check_state(case["state"], role_ids, case["id"])
    for team in team_cases:
        require(team["id"] not in case_ids, f"Repeated team ID: {team['id']}")
        case_ids.add(team["id"])
        check_state(team["state"], role_ids, team["id"])
        mandatory, optional = set(team["required_roles"]), set(team["allowed_roles"])
        require(bool(mandatory) and not mandatory & optional and mandatory | optional <= role_ids, f"{team['id']}: invalid team labels")
        covered.update(mandatory)
    require(covered == role_ids, "Some roles never required in a complete problem")
    requests = reconstruct_requests(suite, catalog)
    require(len(requests) == plan["requests"] == 420, "Request count mismatch")
    require(sum(len(req["questions"]) for req in requests.values()) == plan["requested_binary_decisions"] == 924, "Decision count mismatch")
    require(plan["individual_cases"] == 132 and plan["team_cases"] == 12, "Frozen plan case count mismatch")
    expected_names = {f"{key}.json" for key in requests}
    require({path.name for path in (run / "requests").glob("*.json")} == expected_names, "Missing or unexpected request files")
    require({path.name for path in (run / "results").glob("*.json")} == expected_names, "Missing or unexpected result files")
    metadata = read(run / "metadata.json")
    sessions = metadata.get("models", {}).get("julia/all-reviewers", {}).get("load_sessions", [])
    session_ids, checkpoint_files = set(), None
    require(bool(sessions), "No pinned model load session")
    for session in sessions:
        require(session.get("revision") == REVISION and session.get("weight_sha256") == WEIGHT_SHA256, "Wrong model identity")
        require(session.get("strict_encoding") is True and session.get("marker_only_head") is False, "Lossy encoding settings")
        require(session.get("max_length") == 8192 and bool(session.get("checkpoint_files")), "Missing checkpoint or length evidence")
        session_id = session.get("session_id")
        require(isinstance(session_id, str) and bool(session_id) and session_id not in session_ids, "Invalid model session ID")
        session_ids.add(session_id)
        if checkpoint_files is not None:
            require(session["checkpoint_files"] == checkpoint_files, "Checkpoint file hashes changed across sessions")
        checkpoint_files = session["checkpoint_files"]
    records, decoded, rejected = {}, {}, []
    expected_wire_files = set()
    for key, expected in requests.items():
        request_path, result_path = run / "requests" / f"{key}.json", run / "results" / f"{key}.json"
        request, record = read(request_path), read(result_path)
        require(request == expected, f"{key}: request differs from frozen case/question")
        require(request["sha256"] == object_hash({k: v for k, v in request.items() if k != "sha256"}), f"{key}: request digest mismatch")
        hashes["requests"][key] = {"file_sha256": file_hash(request_path), "body_sha256": request["sha256"]}
        hashes["results"][key] = file_hash(result_path)
        require(record.get("id") == key and record.get("request_sha256") == request["sha256"], f"{key}: result not bound to request")
        require(record.get("model_session_id") in session_ids, f"{key}: unknown model session")
        require(record.get("status") in {"ok", "error"} and type(record.get("inference_performed")) is bool, f"{key}: invalid completion state")
        errors, encodings = record.get("encoding_errors"), record.get("encoding")
        require(isinstance(errors, dict) and isinstance(encodings, dict), f"{key}: missing encoding diagnostics")
        require(not set(errors) & set(encodings) and set(errors) | set(encodings) == set(request["questions"]), f"{key}: omitted encoding attempt")
        if not errors:
            wire_path = run / "wire" / f"{key}.json"
            require(read(wire_path) == {"state": request["state"], "questions": request["questions"]}, f"{key}: submitted payload differs")
            hashes["wire"][key] = file_hash(wire_path)
            expected_wire_files.add(wire_path.name)
        else:
            require(record["inference_performed"] is False and record.get("raw_output") is None, f"{key}: preflight failure has inference output")
        if record["status"] == "ok":
            require(not errors and record["inference_performed"], f"{key}: successful result lacks actual complete inference")
            probabilities, chosen = decode_independently(request, record.get("raw_output"))
            require(record.get("probabilities") == probabilities and record.get("selected") == chosen, f"{key}: saved mapping differs from raw output")
            decoded[key] = (probabilities, chosen)
        else:
            require(record.get("probabilities") is None and not record.get("selected"), f"{key}: failed result contains scored decisions")
            require(bool(errors) or bool(record.get("error")), f"{key}: failure lacks a reason")
            rejected.append({"request_id": key, "encoding_errors": errors, "error": record.get("error")})
        if request["variant"] != "catalog_noul":
            require(key in decoded, f"{key}: grounded inference omitted, failed or incomplete")
        if request["kind"] == "team":
            require(set(request["questions"]) == role_ids, f"{key}: team not asked all 22 roles")
            require(len(decoded[key][0]) == 22, f"{key}: partial team output")
        records[key] = record
    require({path.name for path in (run / "wire").glob("*.json")} == expected_wire_files, "Missing or unexpected submitted payload")
    scores = independent_scores(suite, records, decoded)
    published_scores = read(run / "scores.json")
    require(published_scores == scores, "Independent arithmetic differs from published scores.json")
    grounded_keys = [key for key in requests if not key.endswith("-catalog_noul")]
    require(len(grounded_keys) == 288 and all(key in decoded for key in grounded_keys), "Grounded execution coverage incomplete")
    return {
        "status": "pass",
        "scope": "Independent execution and arithmetic audit; no reviewer defect detection was run.",
        "checks": {
            "all_22_roles_six_balanced_controls": True, "all_12_teams_full_22_role_outputs_per_variant": True,
            "requests_reconstructed_from_frozen_suite": True, "state_contains_only_task_and_evidence": True,
            "scorer_labels_excluded_from_state": True, "wire_payloads_match_frozen_requests": True,
            "raw_false_true_mappings_match_saved_decisions": True, "independent_scores_match_published": True,
            "no_grounded_attempt_omissions": True, "all_grounded_requests_completed_actual_inference": True,
            "frozen_input_and_runtime_source_hashes_match": True, "role_charter_hashes_match": True,
        },
        "counts": {
            "roles": 22, "individual_controls": 132, "team_problems": 12,
            "request_files": len(requests), "grounded_requests": len(grounded_keys),
            "grounded_decisions": sum(len(decoded[key][0]) for key in grounded_keys),
            "successful_requests": len(decoded), "unavailable_requests": len(rejected),
        },
        "model_sessions": sorted(session_ids), "pinned_revision": REVISION, "pinned_weight_sha256": WEIGHT_SHA256,
        "hashes": hashes, "plan_sha256": file_hash(run / "plan.json"),
        "metadata_sha256": file_hash(run / "metadata.json"), "published_scores_sha256": file_hash(run / "scores.json"),
        "independent_scores": scores, "unavailable_requests": rejected,
        **detailed_role_metrics(suite, scores),
        "individual_calibration": calibration_metrics(suite, records, decoded),
        "limits": [
            "Structural checks cannot prove the absence of every subtle semantic hint in human-authored examples.",
            "Model execution evidence is the preserved payloads, raw outputs, encoding diagnostics and pinned-session metadata; this audit does not rerun the model.",
            "Weights are identified by recorded pinned hashes; this audit does not rehash the cached checkpoint.",
        ],
    }


def self_test() -> None:
    def sample(kind: str, probabilities: dict, choice: str | None = None) -> tuple[dict, dict]:
        request = {"questions": {"lens": {"type": kind, "criteria": {"false": "No", "true": "Yes"}}}}
        answer = {"type": kind, "probabilities": probabilities}
        if choice is not None:
            answer["choice"] = choice
        return request, {"answers": {"lens": answer}}

    require(decode_independently(*sample("noul", {"false": 0.5, "true": 0.5}))[1] == ["lens"], "Noul tie behavior")
    require(decode_independently(*sample("choice", {"false": 0.5, "true": 0.5}, "false"))[1] == [], "Choice tie behavior")
    require(decode_independently(*sample("choice", {"false": 0.2, "true": 0.8}, "true"))[1] == ["lens"], "Choice true mapping")
    invalid = [
        sample("choice", {"false": 0.2, "true": 0.8}, "false"),
        sample("noul", {"false": 0.5, "true": True}),
        sample("noul", {"false": 0.5, "true": float("nan")}),
        sample("noul", {"false": 0.2, "true": 0.2}),
        ({"questions": {"lens": {"type": "noul"}}}, {"answers": {}}),
    ]
    for request, raw in invalid:
        try:
            decode_independently(request, raw)
        except AuditError:
            pass
        else:
            raise AuditError("Decoder accepted invalid or partial output")
    print("Independent decoder self-checks passed; no run artifacts or predictions read.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    run = confined(args.run)
    output = confined(args.output or run / "independent-execution-audit.json")
    require(output.parent == run, "Audit report must be written directly inside its run directory")
    require(output.name not in {"suite.json", "catalog.json", "inventory.json", "plan.json", "scores.json", "metadata.json"}, "Audit cannot overwrite run inputs or scores")
    require(not any(part in {"requests", "results", "wire"} for part in output.relative_to(BASE).parts), "Audit cannot overwrite execution evidence")
    try:
        result = audit(run)
    except (AuditError, OSError, ValueError, KeyError, TypeError) as error:
        result = {"status": "fail", "error": f"{type(error).__name__}: {error}"}
    result.update({
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "auditor_path": Path(__file__).relative_to(REPO).as_posix(),
        "auditor_sha256": file_hash(Path(__file__)),
        "run": run.relative_to(BASE).as_posix(),
        "independence": "Standard library only; no runner, decoder, scoring helper or model imports.",
        "writes": [output.relative_to(BASE).as_posix()],
    })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encode(result), encoding="utf-8")
    print(f"Independent audit {result['status']}: {output}")
    if result["status"] == "fail":
        print(result["error"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
