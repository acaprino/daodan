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
MARK = "@@daodan-refused "  # the line `container.PROXY_SCRIPT` prints for each refusal
LOOKUPS = 16  # the hosts one analysis resolves at most
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
