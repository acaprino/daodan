"""Write BINDINGS.json, DISPATCH.json and state.json for this review."""
import json
import sys

out = sys.argv[1]
ctx = json.load(open(out + "/CONTEXT.json", encoding="utf-8"))
selection = [
    "senior-review:local-correctness-auditor",
    "senior-review:logic-integrity-auditor",
    "senior-review:artifact-lifecycle-auditor",
]
json.dump(
    {
        "candidate": ctx["candidate"],
        "selection": selection,
        "knowledge_selection": "",
        "output_dir": "jobs",
        "input_mode": "independent",
    },
    open(out + "/BINDINGS.json", "w", encoding="utf-8"),
    indent=2,
)
json.dump(
    {"roles": selection, "critic": False},
    open(out + "/DISPATCH.json", "w", encoding="utf-8"),
    indent=2,
)
json.dump(
    {
        "target": "6dd2c2bbf..943bdc44c",
        "status": "in_progress",
        "flags": {
            "reviewers": "auto",
            "all": False,
            "deep": False,
            "no_context": False,
            "fast": False,
            "rigorous": False,
        },
        "current_phase": 2,
        "phases": {
            "phase_0_resolution": "complete",
            "phase_0b_policy": "complete",
            "phase_1_context": "complete",
            "phase_1_selection": "complete",
            "phase_2_review": "in_progress",
            "phase_3_consolidation": "pending",
            "phase_4b_verification": "pending",
            "phase_4c_critic": "not-in-tier",
            "phase_4_report": "pending",
        },
        "files_created": [],
        "xray": {
            "run_id": "daodan-lite-20261107-2",
            "run_dir": None,
            "target": ".",
            "depth": "lite",
        },
    },
    open(out + "/.team-review/state.json", "w", encoding="utf-8"),
    indent=2,
)
print("written")
