"""Close the native report stages and stamp the report's end time."""
import json
import sys
from datetime import datetime
from pathlib import Path

out = Path(sys.argv[1])
state_path = out / ".team-review" / "state.json"
state = json.loads(state_path.read_text(encoding="utf-8"))
state["status"] = "complete"
state["current_phase"] = 5
state["phases"].update(
    {
        "phase_2_review": "complete",
        "phase_3_consolidation": "complete",
        "phase_4b_verification": "complete",
        "phase_4c_critic": "skipped: not in tier",
        "phase_4_report": "complete",
    }
)
state["files_created"] = [
    ".team-review/00-scope.md",
    ".team-review/01-context.md",
    ".team-review/02-selection.md",
    ".team-review/98-verification.md",
    ".team-review/99-consolidated.md",
    "jobs/job-01.md",
    "jobs/job-02.md",
    "jobs/job-03.md",
    "verification/F1-lens0.md",
    "verification/F1-lens1.md",
    "review-branch-943bdc44c-simplified.md",
]
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

consolidated = out / ".team-review" / "99-consolidated.md"
text = consolidated.read_text(encoding="utf-8")
if "## After verification" not in text:
    text += (
        "\n## After verification\n\n"
        "F1: verified, High, evidence class `reproduced` (base 109.8, candidate 97.6, "
        "in the return value and the ledger line). AL-1, AL-2, AL-3: `unverified (tier)`. Filtered: 0.\n"
    )
    consolidated.write_text(text, encoding="utf-8")

report = out / "review-branch-943bdc44c-simplified.md"
body = report.read_text(encoding="utf-8")
report.write_text(body.replace("@@END@@", datetime.now().strftime("%H:%M:%S")), encoding="utf-8")
print("closed")
