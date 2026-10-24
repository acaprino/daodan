"""Read-only loaders for the frozen gold data used by the mock nomination eval.

Development asset only. No loader writes. Gold labels are returned to the
scorer/test layer; ``public_state`` / ``build_questions`` deliberately build
model-visible inputs that contain no gold label fields, so a label cannot be
passed to ``decide(state, questions)`` through the helpers in this module.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHOICER = HERE.parent
RUN_C = CHOICER / "runs" / "20261020T100258Z"
TEAMS_PATH = CHOICER / "all-reviewers" / "teams.json"
SUITE_PATH = CHOICER / "runs" / "20261020T-all-reviewers" / "suite.json"

EXPECTED = {
    "gold_c_cases": 11,
    "gold_c_labeled": 10,
    "gold_c_activations": 23,
    "teams": 12,
    "team_required": 39,
    "team_roles": 22,
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_dataset() -> dict:
    return _read_json(RUN_C / "dataset.json")


def load_catalog() -> dict:
    return _read_json(RUN_C / "catalog.json")


def load_comparison() -> dict:
    return _read_json(RUN_C / "gutsy-comparison.json")


def load_teams() -> list[dict]:
    """Teams from all-reviewers/teams.json, falling back to the frozen suite."""
    if TEAMS_PATH.exists():
        data = _read_json(TEAMS_PATH)
        return list(data["cases"])
    return list(load_suite()["teams"])


def team_source() -> dict:
    """Which team source ``load_teams`` actually uses, for run provenance.

    ``load_teams`` picks ``teams.json`` when it exists and the frozen
    ``suite.json`` otherwise, using the same existence check, so this record
    names the source a run's teams came from rather than an assumed one.
    """
    if TEAMS_PATH.exists():
        return {"source": "teams.json", "path": str(TEAMS_PATH),
                "fallback_used": False}
    return {"source": "suite.json", "path": str(SUITE_PATH),
            "fallback_used": True}


def load_suite() -> dict:
    return _read_json(SUITE_PATH)


def reviewer_ids_c() -> list[str]:
    catalog = load_catalog()
    return [r["id"] for r in catalog["roles"] if r.get("is_reviewer", True)]


def team_role_ids() -> list[str]:
    return [r["role_id"] for r in load_suite()["roles"]]


def guard_counts() -> dict:
    """Return verified counts and raise if a frozen guard no longer holds."""
    dataset = load_dataset()
    cases = dataset["cases"]
    counts = {
        "gold_c_cases": len(cases),
        "gold_c_labeled": sum(c.get("label_status") == "labeled" for c in cases),
        "gold_c_activations": sum(
            len(c.get("expected_roles", []))
            for c in cases
            if c.get("label_status") == "labeled"
        ),
        "teams": len(load_teams()),
        "team_required": sum(len(t["required_roles"]) for t in load_teams()),
        "team_roles": len(team_role_ids()),
    }
    if counts != EXPECTED:
        raise ValueError(f"Frozen gold counts changed: {counts} != {EXPECTED}")
    return counts


def saved_probs() -> dict:
    """Saved Gutsy probabilities and recorded scores (no new inference)."""
    comp = load_comparison()
    return {
        "suite2_raw_probs": comp.get("suite2_raw_probs", {}),
        "suite3_raw_probs": comp.get("suite3_raw_probs", {}),
        "suite3_c01_c11": comp.get("suite3_c01_c11", {}),
        "suite2_grounded_noul": comp.get("suite2_grounded_noul", {}),
    }


def public_state_c(case: dict) -> dict:
    """Model-visible state for a Gold C case: hunk text only, no labels."""
    parts = []
    for hunk in case.get("hunks", []):
        parts.append(
            {"path": hunk.get("path"), "id": hunk.get("id"),
             "text": hunk.get("text", "")}
        )
    return {"case_id": case["id"], "hunks": parts}


def public_state_team(team: dict) -> dict:
    """Model-visible state for a team case: task/artifacts only, no labels."""
    state = team.get("state", {})
    return {
        "case_id": team["id"],
        "task": state.get("task", ""),
        "artifacts": [
            {"path": a.get("path"), "content": a.get("content", "")}
            for a in state.get("artifacts", [])
        ],
    }


def build_questions(role_ids: list[str]) -> dict:
    """Noul questions in the shape decode_answers expects. No gold in here."""
    return {
        rid: {
            "type": "noul",
            "instructions": f"Does this case require reviewer {rid}?",
            "criteria": {"false": "Not required", "true": "Required"},
        }
        for rid in role_ids
    }
