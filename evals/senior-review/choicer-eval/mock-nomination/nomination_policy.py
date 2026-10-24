"""Pure nomination policy: validated mock answers -> nominated reviewers.

Standard library only, no I/O. Missing, malformed, Z or failed answers are
ABSTAIN, never negative votes, and never repaired by falling back to the
first hunk (or any invented evidence binding).

Mandatory lenses come from the senior-review dispatch table
(plugins/senior-review/skills/review-method/references/code-review.md:73-74:
code-auditor "Always", security-auditor "Always"). This module names them as a
frozen profile constant; it does not read plugin files at runtime.

``decode_answers`` below replicates all_reviewers_eval.py:43-81 faithfully.
The original is importable in a full choicer checkout, but it imports the
dataset/run_eval harness at module load; the replica keeps this asset usable
standalone and is pinned against the original semantics by the tests.
``score_team_probs`` replicates run_gutsy_benchmark.py:129-167 for the same
reason: importing that module executes ``from probe_gutsy import ...`` which
requires numpy/torch and fails in a stdlib-only environment (verified:
ModuleNotFoundError: numpy), so it cannot be imported without side effects.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

FROZEN_THRESHOLD = 0.5
MANDATORY_LENSES = frozenset(
    {"senior-review:code-auditor", "senior-review:security-auditor"}
)


@dataclass(frozen=True)
class FrozenProfile:
    default_threshold: float = FROZEN_THRESHOLD
    per_role_thresholds: dict = field(default_factory=dict)
    mandatory_lenses: frozenset = MANDATORY_LENSES
    min_margin: float = 0.0  # required p_true - p_false margin
    require_evidence_binding: bool = True
    z_is_abstain: bool = True

    def threshold_for(self, role: str) -> float:
        return float(self.per_role_thresholds.get(role, self.default_threshold))

    @classmethod
    def threshold_only_replay(cls) -> "FrozenProfile":
        """Profile that replays the recorded threshold scoring exactly.

        The saved Suite2/Suite3 numbers in gutsy-comparison.json were produced
        by a pure >= threshold rule with no mandatory-lens override and no
        evidence gate. This profile exists only to reproduce those recorded
        numbers without new inference; it is not the nomination policy.
        """
        return cls(mandatory_lenses=frozenset(), require_evidence_binding=False)


# --------------------------------------------------------------------------
# Contract gate: faithful replica of all_reviewers_eval.decode_answers:43-81
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# Per-question validation (tolerant: one bad answer abstains, others stand)
# --------------------------------------------------------------------------
def validate_answer(question_spec: dict, answer) -> dict:
    """Return {'status': 'ok', 'p_true': float} or {'status': 'ABSTAIN', ...}."""
    if answer is None:
        return {"status": "ABSTAIN", "reason": "missing_answer"}
    if not isinstance(answer, dict):
        return {"status": "ABSTAIN", "reason": "answer_not_a_mapping"}
    if answer.get("choice") == "Z" or answer.get("abstain") is True:
        return {"status": "ABSTAIN", "reason": "z_abstention"}
    kind = question_spec.get("type") if isinstance(question_spec, dict) else None
    if answer.get("type") != kind or kind not in {"noul", "choice"}:
        return {"status": "ABSTAIN", "reason": "type_mismatch"}
    p = answer.get("probabilities")
    if not isinstance(p, dict) or set(p) != {"false", "true"} or any(
        type(v) not in (int, float) or isinstance(v, bool)
        or not math.isfinite(v) or not 0 <= v <= 1 for v in p.values()
    ):
        return {"status": "ABSTAIN", "reason": "malformed_probabilities"}
    if not math.isclose(sum(p.values()), 1.0, rel_tol=0, abs_tol=1e-6):
        return {"status": "ABSTAIN", "reason": "unnormalized_probabilities"}
    if kind == "noul" and "noul" in answer:
        noul = answer["noul"]
        if type(noul) not in (int, float) or isinstance(noul, bool) or not math.isfinite(noul) \
                or not math.isclose(noul, p["true"], rel_tol=0, abs_tol=1e-9):
            return {"status": "ABSTAIN", "reason": "noul_mismatch"}
    return {"status": "ok", "p_true": float(p["true"])}


# --------------------------------------------------------------------------
# Replica of run_gutsy_benchmark.score_team_probs:129-167 (see module docstring)
# --------------------------------------------------------------------------
def score_team_probs(teams: list[dict], raw_probs: dict[str, dict[str, float]]) -> dict:
    by_thresh = {}
    for th in (0.45, 0.50, 0.55, 0.60, 0.65):
        req_found = req_total = out_of_scope = total_sel = acceptable = 0
        per_team = []
        for t in teams:
            tid = t["id"]
            req = set(t["required_roles"])
            allow = set(t["allowed_roles"])
            probs = raw_probs[tid]
            sel = {rid for rid, p in probs.items() if p >= th}
            req_hit = len(sel & req)
            req_found += req_hit
            req_total += len(req)
            forb = sel - (req | allow)
            out_of_scope += len(forb)
            total_sel += len(sel)
            is_acc = (req_hit == len(req)) and (len(forb) == 0)
            if is_acc:
                acceptable += 1
            per_team.append(
                {
                    "id": tid,
                    "required_found": f"{req_hit}/{len(req)}",
                    "missing": sorted(req - sel),
                    "out_of_scope": sorted(forb),
                    "selected": sorted(sel),
                    "acceptable": is_acc,
                }
            )
        by_thresh[f"{th:.2f}"] = {
            "acceptable_teams": f"{acceptable}/{len(teams)}",
            "mandatory_found": f"{req_found}/{req_total} ({req_found/req_total*100:.1f}%)",
            "out_of_scope_selections": out_of_scope,
            "mean_out_of_scope_per_team": round(out_of_scope / len(teams), 2),
            "total_selected": total_sel,
            "per_team": per_team,
        }
    return by_thresh


# --------------------------------------------------------------------------
# Policy
# --------------------------------------------------------------------------
def nominate(case_id: str, questions: dict, raw: dict | None,
             profile: FrozenProfile | None = None,
             evidence_bindings: dict | None = None,
             failure: str | None = None) -> dict:
    """Apply the frozen profile to one case/team of validated answers.

    ``evidence_bindings`` maps qid -> non-empty list of evidence/hunk ids
    explicitly bound by the caller. When the profile requires a binding and
    none is supplied for a role, that role ABSTAINs; no binding is invented.
    """
    profile = profile or FrozenProfile()
    nominated: list[str] = []
    applied, discarded, abstained = [], [], []

    if failure is not None or raw is None:
        # Whole-tool failure: every question abstains. Mandatory lenses are
        # still nominated by policy (they cannot be removed by a failure),
        # and the audit records that their nomination rests on the mandate,
        # not on a model vote.
        for qid in sorted(questions):
            entry = {"qid": qid, "status": "ABSTAIN",
                     "reason": failure or "tool_failure"}
            if qid in profile.mandatory_lenses:
                nominated.append(qid)
                entry["mandatory_retained"] = True
            abstained.append(entry)
        return _result(case_id, profile, nominated, applied, discarded, abstained)

    answers = raw.get("answers") if isinstance(raw, dict) else None
    if not isinstance(answers, dict):
        return nominate(case_id, questions, None, profile, evidence_bindings,
                        failure="missing_answer_mapping")

    for qid in sorted(questions):
        mandatory = qid in profile.mandatory_lenses
        verdict = validate_answer(questions[qid], answers.get(qid))
        if verdict["status"] != "ok":
            entry = {"qid": qid, "status": "ABSTAIN", "reason": verdict["reason"]}
            if mandatory:
                nominated.append(qid)
                entry["mandatory_retained"] = True
            abstained.append(entry)
            continue
        p = verdict["p_true"]
        threshold = profile.threshold_for(qid)
        margin = p - (1.0 - p)
        if mandatory:
            nominated.append(qid)
            applied.append({"qid": qid, "p_true": p, "threshold": threshold,
                            "reason": "mandatory_lens"})
            continue
        if p < threshold:
            discarded.append({"qid": qid, "status": "discarded", "p_true": p,
                              "threshold": threshold, "reason": "below_threshold"})
            continue
        if margin < profile.min_margin:
            discarded.append({"qid": qid, "status": "discarded", "p_true": p,
                              "threshold": threshold, "reason": "below_min_margin"})
            continue
        if profile.require_evidence_binding:
            binding = (evidence_bindings or {}).get(qid)
            if not binding:
                abstained.append({"qid": qid, "status": "ABSTAIN", "p_true": p,
                                  "reason": "evidence_binding_missing"})
                continue
        nominated.append(qid)
        applied.append({"qid": qid, "p_true": p, "threshold": threshold,
                        "reason": "threshold_met"})
    return _result(case_id, profile, nominated, applied, discarded, abstained)


def _result(case_id, profile, nominated, applied, discarded, abstained) -> dict:
    return {
        "case_id": case_id,
        "nominated": sorted(nominated),
        "audit": {
            "profile": {
                "default_threshold": profile.default_threshold,
                "per_role_thresholds": dict(profile.per_role_thresholds),
                "mandatory_lenses": sorted(profile.mandatory_lenses),
                "min_margin": profile.min_margin,
                "require_evidence_binding": profile.require_evidence_binding,
            },
            "applied": applied,
            "discarded": discarded,
            "abstained": abstained,
        },
    }
