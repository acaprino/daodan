"""Session hook: tell the main model whether this project records its decisions.

Reads the host's SessionStart payload on stdin, detects the project state with
adr_tool.py and prints additional context for an active or undecided project.
Writes nothing. Any error, a declined project or another event prints nothing.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
HERE = str(Path(__file__).resolve().parent)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

BUDGET_SECONDS = 6
FOREIGN_SHOWN = 5

ACTIVE = (
    "This project keeps decision records in {adr_dir}/. When a product or feature brainstorming settles a "
    "decision, whatever brainstorming or design method is running, record it as a Proposed record through "
    "project-delivery:adr-method (run adr_tool.py init-index first when {adr_dir}/README.md has no adr-index "
    "block), show the record to the user, and promote it to Accepted only when the user approves its exact text."
)
FOREIGN = (
    " The decision records in the foreign record directories listed below belong to another tool: read them "
    "as constraints on the decisions being settled, cite them, and never write them; new records go only to "
    "{adr_dir}/, and adr_tool.py state lists every foreign directory."
)
PROJECT = " Pass the project root below as --project to every adr_tool.py command."
UNDECIDED = (
    "This project has not chosen whether to keep decision records. At the first decision settled in a product "
    "or feature brainstorming, whatever brainstorming or design method is running, ask the user once whether "
    "to use decision records as this project's method; yes is the default. Never ask at session start or "
    "before a decision is settled. On yes, load project-delivery:adr-method, run adr_tool.py init-index and record "
    "that decision as the first Proposed record. On no, run adr_tool.py decline and tell the user that "
    "/daodan:record-decision turns decision records back on."
)


def context(payload: dict) -> str | None:
    if payload.get("hook_event_name") != "SessionStart" or not isinstance(payload.get("cwd"), str):
        return None
    import adr_tool

    state = adr_tool.project_state(payload["cwd"], deadline=time.monotonic() + BUDGET_SECONDS)
    foreign = state["foreign"]
    if state["state"] == "active":
        text = ACTIVE.format(adr_dir=state["adr_dir"]) + (FOREIGN.format(adr_dir=state["adr_dir"]) if foreign else "")
    elif state["state"] == "undecided":
        text = UNDECIDED
    else:
        return None
    # Instructions first, then the data lines: paths found on disk never sit inside an instruction.
    data = [f"Project root (data): {json.dumps(state['project'])}"]
    if foreign:
        hidden = len(foreign) - FOREIGN_SHOWN
        data.append(f"Foreign record directories (data): {json.dumps(foreign[:FOREIGN_SHOWN])}"
                    + (f" and {hidden} more" if hidden > 0 else ""))
    return text + PROJECT + "\n\n" + "\n".join(data)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read(1_048_577))
        text = context(payload) if isinstance(payload, dict) else None
        if text:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}},
                             ensure_ascii=True))
    except Exception:  # A session must start whatever this hook meets.
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
