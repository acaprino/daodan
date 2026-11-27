"""Which hosts a container run may reach: canonical, approved by the user, blocked, or still to ask.

Without asking, a run reaches only the canonical hosts (`container.REGISTRIES`, from `package-managers.json`) and
the hosts the user approved. A host in neither list asks; a host the user blocked is refused with no question.
The user's answers live in `egress.json` in the per-user shared folder (`embedding_worker.shared_cache_dir`), never in
the project: `{"whitelist": {<project>: [<host>]}, "blacklist": [<host>]}`. A project is named by the caller, one
string for one project. The four answers: "always" (this project), "once" (this analysis: the `session`), "no"
(this analysis) and "block" (every project, always). The module is pure but for `load` and `save`.
"""
from __future__ import annotations

import ipaddress
import json
import os
import socket
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from embedding_worker import shared_cache_dir  # noqa: E402

FILE = "egress.json"
PENDING: dict[str, dict] = {}  # project -> its requests still to answer, by (host, port): the analysis's register
SESSIONS: dict[str, dict] = {}  # project -> the answers that last for its analysis
MARK = "@@daodan-refused "  # the line `container.PROXY_SCRIPT` prints for each refusal
LOOKUPS = 16  # the hosts one analysis resolves at most
REPLIES = ("always", "once", "no", "block")


def new_session() -> dict:
    """The answers that last for one analysis: hosts allowed ("once") and hosts refused ("no")."""
    return {"allow": [], "deny": []}


def session(project: str) -> dict:
    """The answers of the project's analysis, made on first use."""
    return SESSIONS.setdefault(project, new_session())


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
    bare = host.removeprefix("http://")  # an apt archive is approved as its host is
    if bare in state["blacklist"] or bare in session["deny"]:
        return "deny"
    if host in REGISTRIES or bare in state["whitelist"].get(project, ()) or bare in session["allow"]:
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


def refused(log: str) -> list[dict]:
    """The `{host, port}` of each refusal in a proxy's log, in order and once each."""
    found = []
    for line in log.splitlines():
        if not line.startswith(MARK):
            continue
        try:
            row = json.loads(line[len(MARK):])
            host, port = row["host"], row["port"]
        except (ValueError, KeyError, TypeError):
            continue
        if isinstance(host, str) and isinstance(port, str) and host:
            entry = {"host": host.lower(), "port": port}
            if entry not in found:
                found.append(entry)
    return found


def private(address: str) -> bool:
    """Whether an address is private, loopback or link-local: the user's own network, which a host must not reach
    unasked. An IPv4 address inside an IPv6 one counts as the IPv4 one."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    ip = getattr(ip, "ipv4_mapped", None) or ip
    return ip.is_private or ip.is_loopback or ip.is_link_local


def resolve(requests: list[dict], lookups: int = LOOKUPS) -> list[dict]:
    """Each request with the `address` of its host and whether it is the user's `network`, here on the host and not in
    the proxy: a literal address is read as it is, any other name is looked up once, up to `lookups` names (the rest,
    and a name that does not resolve, have no address)."""
    found, looked = {}, 0
    out = []
    for request in requests:
        host = request["host"].strip("[]")
        if host not in found:
            try:
                ipaddress.ip_address(host)
                found[host] = host
            except ValueError:
                found[host] = None
                if looked < lookups:
                    looked += 1
                    try:
                        found[host] = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)[0][4][0]
                    except OSError:
                        pass
        out.append({**request, "address": found[host], "network": found[host] is not None and private(found[host])})
    return out


def requests(refused: list[dict], project: str, state: dict, session: dict, where: dict | None = None,
             lookups: int = LOOKUPS) -> tuple[list[dict], list[dict]]:
    """What the refusals of a run (`refused`) are: the requests to answer, each `{host, port, address, network,
    declared_in}` (`resolve`; `where`, `preparation.declared`'s, gives the files that declare a host), and the
    `host_denied` gaps, for a host the user blocked or refused in this analysis. A refused host that `decide` allows
    (a canonical one asked on another port) is neither."""
    where = where or {}
    decided = [(row, decide(row["host"], project, state, session)) for row in refused]
    asked = resolve([row for row, decision in decided if decision == "ask"], lookups)
    return ([{**row, "declared_in": where.get(row["host"], [])} for row in asked],
            [{"kind": "host_denied", "host": row["host"], "port": row["port"],
              "declared_in": where.get(row["host"], []),
              "detail": f"{row['host']}:{row['port']} was refused: the user blocked it or said no to it"}
             for row, decision in decided if decision == "deny"])


def collect(project: str, refused: list[dict], where: dict | None = None) -> tuple[list[dict], list[dict]]:
    """The refusals of a run (`container.run_in_container`): the requests join the project's `PENDING`, and come back
    with the `host_denied` gaps, `(asked, gaps)`."""
    asks, gaps = requests(refused, project, load(), session(project), where)
    held = PENDING.setdefault(project, {})
    for row in asks:
        held.setdefault((row["host"], row["port"]), row)
    return asks, gaps


def approval_gap(asked: list[dict]) -> list[dict]:
    """The `approval_required` gap of a step that failed with requests unanswered: none when it asked for nothing."""
    if not asked:
        return []
    said = ", ".join(f"{row['host']}:{row['port']}" + (f" (declared in {', '.join(row['declared_in'])})"
                                                        if row["declared_in"] else "") for row in asked)
    return [{"kind": "approval_required", "hosts": [row["host"] for row in asked],
             "detail": f"the step failed and asked for hosts the user has not approved: {said}; answer in the app, "
                       "then analyze again"}]


def pending(project: str) -> list[dict]:
    """The requests of the project's analysis that wait for an answer."""
    return list(PENDING.get(project, {}).values())
