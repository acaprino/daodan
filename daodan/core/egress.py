"""Which hosts a container run may reach: canonical, approved by the user, blocked, or still to ask.

Without asking, a run reaches only the canonical hosts (`container.REGISTRIES`, from `package-managers.json`) and
the hosts the user approved. A host in neither list asks; a host the user blocked is refused with no question.
The user's answers live in `egress.json` in the per-user shared folder (`embedding_worker.shared_cache_dir`), never in
the project: `{"whitelist": {<project>: [<host>]}, "blacklist": [<host>]}`. A project is named by the caller, one
string for one project. The four answers: "always" (this project), "once" (this analysis: the `session`), "no"
(this analysis) and "block" (every project, always). The module is pure but for `load` and `save`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from embedding_worker import shared_cache_dir  # noqa: E402

FILE = "egress.json"
REPLIES = ("always", "once", "no", "block")


def new_session() -> dict:
    """The answers that last for one analysis: hosts allowed ("once") and hosts refused ("no")."""
    return {"allow": [], "deny": []}


def load() -> dict:
    """The saved answers; an absent or unreadable file is an empty state, and only well-formed entries are kept."""
    try:
        held = json.loads((shared_cache_dir() / FILE).read_text(encoding="utf-8"))
        whitelist, blacklist = held["whitelist"], held["blacklist"]
        if not isinstance(whitelist, dict) or not isinstance(blacklist, list):
            raise TypeError
    except (OSError, ValueError, KeyError, TypeError):
        return {"whitelist": {}, "blacklist": []}
    return {"whitelist": {project: sorted({h for h in hosts if isinstance(h, str)})
                          for project, hosts in whitelist.items() if isinstance(hosts, list)},
            "blacklist": sorted({h for h in blacklist if isinstance(h, str)})}


def save(state: dict) -> None:
    path = shared_cache_dir() / FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".partial")
    partial.write_text(json.dumps(state, sort_keys=True, indent=1), encoding="utf-8")
    os.replace(partial, path)


def decide(host: str, project: str, state: dict, session: dict | None = None) -> str:
    """"deny" for a blocked host or one refused in this analysis, "allow" for a canonical, an approved or a once-allowed
    host, "ask" for any other."""
    from container import REGISTRIES  # here, not above: `container` will use this module to filter its proxy's hosts
    host, session = host.lower(), session or new_session()
    if host in state["blacklist"] or host in session["deny"]:
        return "deny"
    if host in REGISTRIES or host in state["whitelist"].get(project, ()) or host in session["allow"]:
        return "allow"
    return "ask"


def answer(state: dict, session: dict, host: str, project: str, reply: str) -> tuple[dict, dict]:
    """The state and session after the user's `reply` about `host`, as new values; the arguments are not changed."""
    if reply not in REPLIES:
        raise ValueError(f"reply must be one of {REPLIES}: {reply!r}")
    host = host.lower()
    whitelist = {name: list(hosts) for name, hosts in state["whitelist"].items()}
    blacklist, allow, deny = list(state["blacklist"]), list(session["allow"]), list(session["deny"])
    if reply in ("always", "once"):  # the latest answer of the analysis stands
        deny = [name for name in deny if name != host]
    if reply == "always":
        whitelist[project] = sorted({*whitelist.get(project, ()), host})
    elif reply == "once":
        allow = sorted({*allow, host})
    elif reply == "no":
        allow, deny = [name for name in allow if name != host], sorted({*deny, host})
    else:
        blacklist = sorted({*blacklist, host})
    return {"whitelist": whitelist, "blacklist": blacklist}, {"allow": allow, "deny": deny}
