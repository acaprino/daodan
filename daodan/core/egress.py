"""Which hosts a container run may reach: canonical, approved by the user, blocked, or still to ask.

Without asking, a run reaches only the canonical hosts (`container.REGISTRIES`, from `package-managers.json`) and
the hosts the user approved for the project. A host in neither list asks; a host the user blocked for the project is
refused with no question. A project is named by the caller, one string for one project (`project_of`). The four
answers: "always" and "block" (this project, kept), "once" and "no" (this analysis: the `session`).

The project's lists (`load`) are in its project file, the `.daodan` the app keeps beside a checkout of its own
(`repository.project_path`), never in the analysed project: one row a host with its answer, its author and its instant
(`project_file.answers`), written by the app's answer alone (`reply`). Only the rows of the person who runs Daodan
(`person`) apply; those of a file received from someone wait until that person confirms them in the app
(`project_file.adopt`), and MCP and the command line apply none of them. A folder that is no checkout of the app has no
project file: no lists, and "always" and "block" are refused for it.

The requests still to answer and the answers that last for an analysis are shared between processes, which differ:
the child that is refused, the app that answers, the analysis that reads the answer. They are two files in the
per-user shared folder (`embedding_worker.shared_cache_dir`; `PENDING_FILE`, `SESSION_FILE`), written whole with a
temporary file and `os.replace`, under an OS lock
(`locked`); a missing or corrupt file is an empty one. `begin` empties a project's requests when its analysis starts and
`end` its answers when it ends (`analysis`), so "once" lasts for the analysis the answer is used by. `PENDING` is this
process's copy of the requests; the answers are read from their file each time, so one that an analysis ended
elsewhere has forgotten is never kept here.

Where a person can answer (`answerable`: the analyses the app starts), a run asks as a PC's firewall does: its proxy holds
each connection to a host that asks (`container.PROXY_SCRIPT`, `ASKED`), the request is pending at once, and the
connection waits for the answer, with no time limit (`container.Asked`); a run that has not started waits for its
tool's hosts the same way (`preflight`). Elsewhere (MCP, the command line) nobody answers: the proxy refuses at once and
the request stays (`approval_required`).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import contextvars
import getpass
import ipaddress
import json
import os
import socket
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from embedding_worker import shared_cache_dir  # noqa: E402
from run_store import _try_lock  # noqa: E402  the OS byte-range lock the store takes for its registry

PENDING_FILE, SESSION_FILE, LOCK = "egress-pending.json", "egress-session.json", "egress.lock"
LOCK_SECONDS = 5  # past it the file is read and written without the lock: a stuck holder must not stop an analysis
PENDING: dict[str, dict] = {}  # project -> its requests still to answer, by (host, port): the analysis's register
WHERE: dict[str, dict] = {}  # project -> {host: [files that declare it]}, from `declare`
MARK = "@@daodan-refused "  # the line `container.PROXY_SCRIPT` prints for each refusal
ASKED = "@@daodan-asked "  # ... for a connection it holds until the answer (`answerable`)
GONE = "@@daodan-gone "  # ... for a held connection whose client gave up before the answer
ANSWERS = "DAODAN_ANSWERS"  # "app" in the processes the app starts, where a person answers (`answerable`)
POLL = 0.5  # how often a run that waits for an answer reads the answers again, in seconds
LOOKUPS = 16  # the names one analysis looks up at most, counted in its row of `SESSION_FILE` ("looked")
LOOKUP_SECONDS = 5  # how long the names of one run's refusals are looked up, all together
REPLIES = ("always", "once", "no", "block")
EMPTY = {"always": [], "block": []}  # the lists of a project with none (`load`): "always" and "block" are kept
ASKER = contextvars.ContextVar("egress_asker", default="")  # the tool whose runs ask now (`asking`); "" none named
PROJECT = contextvars.ContextVar("egress_project", default="")  # the analysed project's name (`within`); "" none


def project_of(manifest: Path) -> str:
    """The name of a snapshot's project: its store's root, whatever folder below it the snapshot targets. The analysis,
    its stages and the app name one project by it."""
    from snapshot_store import open_snapshot
    with open_snapshot(Path(manifest)) as store:
        return str(Path(store["root"]).resolve())


def name(folder: Path | str) -> str:
    """The project whose runs ask now: the analysis's (`within`), else the `folder` a run copies."""
    return PROJECT.get() or str(Path(folder).resolve())


@contextlib.contextmanager
def within(project: str):
    """Within it the runs over any folder of the project ask, and are answered, under its name (`project_of`)."""
    token = PROJECT.set(project)
    try:
        yield
    finally:
        PROJECT.reset(token)


@contextlib.contextmanager
def analysis(project: str):
    """One analysis of the project, all its steps: the requests of the one before are gone when it starts (`begin`),
    its "once" and "no" answers when it ends, however it ends (`end`); its runs ask under the project's name."""
    begin(project)
    try:
        with within(project):
            yield
    finally:
        end(project)


@contextlib.contextmanager
def asking(tool: str):
    """Within it the requests a run makes are the `tool`'s: the app asks about them together, one group a tool."""
    token = ASKER.set(tool)
    try:
        yield
    finally:
        ASKER.reset(token)


def new_session() -> dict:
    """The answers that last for one analysis: hosts allowed ("once") and hosts refused ("no")."""
    return {"allow": [], "deny": []}


@contextlib.contextmanager
def locked():
    """The shared files for this process alone (the OS releases the lock if its holder dies)."""
    folder = shared_cache_dir()
    descriptor = None
    try:
        folder.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(folder / LOCK, os.O_CREAT | os.O_RDWR, 0o600)
        deadline = time.monotonic() + LOCK_SECONDS
        while not _try_lock(descriptor) and time.monotonic() < deadline:
            time.sleep(0.02)
    except OSError:
        pass
    try:
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)  # closing the descriptor releases its lock


def _read(name: str) -> dict:
    try:
        held = json.loads((shared_cache_dir() / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return held if isinstance(held, dict) else {}


def _replace(path: Path, value: dict) -> None:
    """`path` holds `value`, written whole: a temporary file of its own beside it, then `os.replace`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, partial = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(value, sort_keys=True, indent=1))
        os.replace(partial, path)
    except BaseException:
        Path(partial).unlink(missing_ok=True)
        raise


def _write(name: str, value: dict) -> None:
    try:
        _replace(shared_cache_dir() / name, value)
    except OSError:
        pass  # the requests' copy in this process still holds them


def _hosts(value) -> list[str]:
    return sorted({h for h in value if isinstance(h, str)}) if isinstance(value, list) else []


def _row(shared: dict, project: str) -> dict:
    row = shared.get(project)
    return row if isinstance(row, dict) else {}


def _looked(project: str) -> int:
    """How many names the project's analysis has looked up (`resolve`), from its row of the shared file."""
    looked = _row(_read(SESSION_FILE), project).get("looked")
    return looked if isinstance(looked, int) and looked >= 0 else 0


def _held(project: str) -> dict | None:
    """The answers of the project's analysis in the shared file, if it has any (a row of lookups alone has none)."""
    row = _row(_read(SESSION_FILE), project)
    if not {"allow", "deny"} & set(row):
        return None
    return {"allow": _hosts(row.get("allow")), "deny": _hosts(row.get("deny"))}


def session(project: str) -> dict:
    """The answers of the project's analysis, as the shared file holds them now: none when it has no entry for the
    project (an analysis that ended, in any process, forgot them). A new value each time: `respond` changes them."""
    return _held(project) or new_session()


def respond(host: str, project: str, reply: str) -> None:
    """The user's `reply` about `host`, kept: "always" and "block" in the project file (`keep`), "once" and "no" in
    the analysis's answers, shared; the request is no longer pending. Called by whoever answers, in any process."""
    with locked():
        _, answers = answer(EMPTY, session(project), host, project, reply)
        if reply in ("always", "block"):
            keep(project, host, reply)
        shared = _read(SESSION_FILE)
        shared[project] = {**_row(shared, project), **answers}
        _write(SESSION_FILE, shared)
        rows = _read(PENDING_FILE)
        rows[project] = [row for row in rows.get(project, []) if row.get("host") != host.lower()]
        _write(PENDING_FILE, rows)
    PENDING.get(project, {}).pop(next((k for k in PENDING.get(project, {}) if k[0] == host.lower()), None), None)


def begin(project: str) -> None:
    """An analysis starts: the requests of the one before are gone, the run will ask again for what it still needs."""
    with locked():
        rows = _read(PENDING_FILE)
        rows.pop(project, None)
        _write(PENDING_FILE, rows)
    PENDING.pop(project, None)


def end(project: str) -> None:
    """An analysis ends: what the user said "once" or "no" to for it is forgotten."""
    with locked():
        shared = _read(SESSION_FILE)
        shared.pop(project, None)
        _write(SESSION_FILE, shared)


def person() -> str:
    """Who runs Daodan, the author of what the app writes in a project file (`getpass.getuser`); "" when the system
    names nobody, whose lists are then none."""
    try:
        return getpass.getuser()
    except (OSError, KeyError):
        return ""


def project_file_of(project: str | None) -> Path | None:
    """The project file of the project, where its lists are: the `.daodan` of the app's checkout (`repository`), which
    may not exist yet; None for any other folder."""
    import repository
    if not project or Path(project).name != repository.CHECKOUT:
        return None
    return repository.project_path(project)


def load(project: str | None) -> dict:
    """The project's lists, `{"always": [<host>], "block": [<host>]}`: the rows of its project file that are `person`'s
    (`project_file.answers`). A project with no file, or one that cannot be read, has none: a run asks again."""
    import project_file
    path = project_file_of(project)
    if path is None or not path.exists():
        return {key: [] for key in EMPTY}
    try:
        with contextlib.closing(project_file.open_project(path)) as db:
            own, _ = project_file.answers(db, person())
    except (sqlite3.Error, ValueError, OSError):  # `ProjectError` is a ValueError
        return {key: [] for key in EMPTY}
    return {key: [row["host"] for row in own if row["answer"] == key] for key in EMPTY}


def keep(project: str, host: str, reply: str) -> None:
    """`person`'s `reply` ("always" or "block") about `host`, in the project file (`project_file.keep_answer`): a file
    with the schema alone where there is none yet, which the first analysis fills (`project_file.create`)."""
    import project_file
    path = project_file_of(project)
    if path is None:
        raise ValueError(f"{project} is no checkout of the app, so it has no project file to keep the answer in: "
                         "answer for this analysis")
    if not path.exists():
        with contextlib.suppress(project_file.ProjectError):  # another writer made it meanwhile
            project_file.create(path)
    with contextlib.closing(project_file.open_project(path, write=True)) as db:
        project_file.keep_answer(db, host, reply, person())


def decide(host: str, project: str, state: dict, session: dict | None = None) -> str:
    """"deny" for a host the project blocked or one refused in this analysis, "allow" for a canonical, an approved or
    a once-allowed host, "ask" for any other. `state` is the project's lists (`load(project)`)."""
    from container import REGISTRIES  # here, not above: `container` will use this module to filter its proxy's hosts
    host, session = host.lower(), session or new_session()
    bare = host.removeprefix("http://")  # an apt archive is approved as its host is
    if bare in state["block"] or bare in session["deny"]:
        return "deny"
    if host in REGISTRIES or bare in state["always"] or bare in session["allow"]:
        return "allow"
    return "ask"


def answer(state: dict, session: dict, host: str, project: str, reply: str) -> tuple[dict, dict]:
    """The project's lists and the analysis's answers after the user's `reply` about `host`, as new values; the
    arguments are not changed. A host is in one list at most: the latest answer stands."""
    if reply not in REPLIES:
        raise ValueError(f"reply must be one of {REPLIES}: {reply!r}")
    host = host.lower()
    always, block, allow, deny = (list(state["always"]), list(state["block"]), list(session["allow"]),
                                  list(session["deny"]))
    if reply in ("always", "once"):  # the latest answer of the analysis stands
        deny = [name for name in deny if name != host]
    if reply == "always":
        always, block = sorted({*always, host}), [name for name in block if name != host]
    elif reply == "once":
        allow = sorted({*allow, host})
    elif reply == "no":
        allow, deny = [name for name in allow if name != host], sorted({*deny, host})
    else:  # blocked: out of every list that would open it
        block, always = sorted({*block, host}), [name for name in always if name != host]
        allow = [name for name in allow if name != host]
    return {"always": always, "block": block}, {"allow": allow, "deny": deny}


def answerable() -> bool:
    """Whether a person answers this process's requests: the app's analyses (`ANSWERS`, set by the app for the processes
    it starts). There a held connection waits for the answer; MCP and the command line have nobody, and refuse at once."""
    return os.environ.get(ANSWERS) == "app"


def wait(project: str, hosts, stop=None) -> None:
    """Until the user has answered for each of `hosts` (none decides "ask" any more), read again every `POLL` seconds,
    with no time limit: the app's analysis stops there for the person. `stop`, an Event, ends the wait sooner."""
    stop = stop or threading.Event()
    while any(decide(host, project, load(project), session(project)) == "ask" for host in hosts):
        if stop.wait(POLL):
            return


def refused(log: str, mark: str = MARK) -> list[dict]:
    """The `{host, port}` of each refusal in a proxy's log, in order and once each; with `mark`, of each line it marks
    (`ASKED`, `GONE`)."""
    found = []
    for line in log.splitlines():
        if not line.startswith(mark):
            continue
        try:
            row = json.loads(line[len(mark):])
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


def _name(host: str) -> str | None:
    """The name `resolve` looks up for a host, None for a literal address."""
    host = host.strip("[]")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return host
    return None


def resolve(requests: list[dict], lookups: int = LOOKUPS, seconds: float = LOOKUP_SECONDS) -> list[dict]:
    """Each request with the `address` of its host and whether it is the user's `network`, here on the host and not in
    the proxy: a literal address is read as it is, any other name is looked up once, up to `lookups` names and for
    `seconds` in all (the rest, a name that does not resolve and one that is no valid name have no address)."""
    hosts = [request["host"].strip("[]") for request in requests]
    found = {host: None if _name(host) else host for host in hosts}
    names = [host for host in found if found[host] is None][:max(lookups, 0)]
    if names:
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=len(names))
        asked = {pool.submit(socket.getaddrinfo, name, None, type=socket.SOCK_STREAM): name for name in names}
        done, _ = concurrent.futures.wait(asked, timeout=seconds)
        pool.shutdown(wait=False, cancel_futures=True)  # a lookup past the time is left to end on its own
        for future in done:
            try:
                found[asked[future]] = future.result()[0][4][0]
            except (OSError, ValueError, IndexError):  # ValueError: an empty label or one past 63 characters
                pass
    return [{**request, "address": found[host], "network": found[host] is not None and private(found[host])}
            for request, host in zip(requests, hosts)]


def requests(refused: list[dict], project: str, state: dict, session: dict, where: dict | None = None,
             lookups: int = LOOKUPS, known: dict | None = None) -> tuple[list[dict], list[dict]]:
    """What the refusals of a run (`refused`) are: the requests to answer, each `{host, port, address, network,
    declared_in}` (`resolve`, but for a request `known`, by `(host, port)`, already has them; `where`,
    `preparation.declared`'s, gives the files that declare a host), and the `host_denied` gaps, for a host the user
    blocked or refused in this analysis and for an allowed host the proxy refused at a port it does not open (at 443,
    an allowed host the run did not list is neither)."""
    where, known = where or {}, known or {}
    decided = [(row, decide(row["host"], project, state, session)) for row in refused]
    fresh = {(row["host"], row["port"]): row for row in resolve(
        [row for row, decision in decided if decision == "ask" and (row["host"], row["port"]) not in known], lookups)}
    asked = [{**row, "address": (fresh.get(key) or known[key]).get("address"),
              "network": bool((fresh.get(key) or known[key]).get("network")), "declared_in": where.get(row["host"], [])}
             for row, decision in decided if decision == "ask" for key in [(row["host"], row["port"])]]
    why = {"deny": "the user blocked it or said no to it",
           "allow": "the proxy opens an allowed host at port 443 only (an apt archive at 80, for its files)"}
    return asked, [{"kind": "host_denied", "host": row["host"], "port": row["port"],
                    "declared_in": where.get(row["host"], []),
                    "detail": f"{row['host']}:{row['port']} was refused: {why[decision]}"}
                   for row, decision in decided if decision == "deny" or decision == "allow" and row["port"] != "443"]


def collect(project: str, refused: list[dict], where: dict | None = None,
            waits: bool = False) -> tuple[list[dict], list[dict]]:
    """The refusals of a run (`container.run_in_container`): the requests join the project's pending ones, in this
    process and in the shared file, and come back with the `host_denied` gaps, `(asked, gaps)`. A request already
    pending is not looked up again, and one analysis looks up `LOOKUPS` names in all (`_looked`). `waits`: the
    connections of a running step wait for the answer (`container.Asked`), and its new requests say so (`held`)."""
    known = {(row["host"], row["port"]): row for row in pending(project)}
    state, answers, budget = load(project), session(project), max(LOOKUPS - _looked(project), 0)
    asks, gaps = requests(refused, project, state, answers, WHERE.get(project) if where is None else where, budget,
                          known)
    asks = [{**row, "tool": (known.get((row["host"], row["port"])) or {}).get("tool", ASKER.get()),
             **({"held": True} if waits else {})} for row in asks]
    looked =min(len({_name(row["host"]) for row in asks if (row["host"], row["port"]) not in known} - {None}),
                 budget)
    held = PENDING.setdefault(project, {})
    for row in asks:
        held.setdefault((row["host"], row["port"]), row)
    if asks:
        with locked():
            rows = _read(PENDING_FILE)
            there = rows.get(project) if isinstance(rows.get(project), list) else []
            have = {(row.get("host"), row.get("port")) for row in there if isinstance(row, dict)}
            rows[project] = [*there, *(row for row in asks if (row["host"], row["port"]) not in have)]
            _write(PENDING_FILE, rows)
            if looked:
                shared = _read(SESSION_FILE)
                shared[project] = {**_row(shared, project), "looked": _looked(project) + looked}
                _write(SESSION_FILE, shared)
    return asks, gaps


def declare(project: str, where: dict) -> None:
    """The files that declare each host of the project's run (`preparation.declared`'s `where`), which the requests
    of its runs name; this process's, set by the step that reads them."""
    WHERE[project] = dict(where)


def preflight(project: str, hosts: tuple[str, ...]) -> tuple[list[dict], list[dict]]:
    """The hosts a run is about to open that the user has not decided, before it starts: `(asked, gaps)`, the requests
    (now pending) and the `approval_required` gap of the step that does not start. A host that is allowed, or that the
    user refused, does not stop it: the proxy refuses the latter and says `host_denied` if the run reaches it. Where a
    person answers (`answerable`), the run waits for the answers instead (`wait`) and starts after them: nothing stops it."""
    state, answers = load(project), session(project)
    ask = [{"host": host.removeprefix("http://"), "port": "80" if host.startswith("http://") else "443"}
           for host in dict.fromkeys(name.lower() for name in hosts) if decide(host, project, state, answers) == "ask"]
    asked, _ = collect(project, ask, waits=answerable())
    if asked and answerable():
        wait(project, [row["host"] for row in asked])
        return [], []
    return asked, approval_gap(asked, "before")


def approval_gap(asked: list[dict], how: str = "failed") -> list[dict]:
    """The `approval_required` gap of a step with requests unanswered, none when it asked for nothing: `how` is
    "failed" (it failed asking), "before" (it did not start for them) or "ran" (it ran, and its result stands, without
    hosts its build declares)."""
    if not asked:
        return []
    said = ", ".join(f"{row['host']}:{row['port']}" + (f" (declared in {', '.join(row['declared_in'])})"
                                                        if row["declared_in"] else "") for row in asked)
    what = {"failed": "the step failed and asked for", "before": "the step did not start: it needs",
            "ran": "the step ran without"}[how]
    return [{"kind": "approval_required", "hosts": [row["host"] for row in asked],
             "detail": f"{what} hosts the user has not approved: {said}; answer in the app, then analyze again"}]


def pending(project: str) -> list[dict]:
    """The requests of the project's analysis that wait for an answer, whichever process was refused."""
    shared = _read(PENDING_FILE).get(project)
    if isinstance(shared, list):  # the file is the truth: a request answered in another process is gone from it
        return [row for row in shared if isinstance(row, dict) and "host" in row and "port" in row]
    return list(PENDING.get(project, {}).values())


def groups(projects: list[str]) -> list[dict]:
    """The requests waiting for an answer of `projects` (the names of one analysis), one group a tool that asked, in
    the order asked: `[{"tool", "project", "requests": [{"host", "port", "address", "network", "declared_in"}]}]`;
    `tool` is "" for runs no tool named (`asking`)."""
    found = {}
    for project in dict.fromkeys(projects):
        for row in pending(project):
            tool = row.get("tool") if isinstance(row.get("tool"), str) else ""
            found.setdefault((project, tool), {"tool": tool, "project": project, "requests": []})["requests"].append(
                {"host": row["host"], "port": row["port"], "address": row.get("address"),
                 "network": bool(row.get("network")), "declared_in": list(row.get("declared_in") or ())})
    return list(found.values())


def reply(project: str, hosts: list[str], said: str) -> None:
    """The user's answer `said` (one of `REPLIES`) to the requests of `project` for `hosts`, a group of them: the
    app's action, the only one that answers (MCP and the command line only read `groups`). A host that does not wait
    for an answer is refused, so that a page answers what was asked and nothing else."""
    if said not in REPLIES:
        raise ValueError(f"the answer must be one of {', '.join(REPLIES)}")
    if not isinstance(hosts, list) or not hosts or not all(isinstance(host, str) for host in hosts):
        raise ValueError("hosts must be a nonempty list of the hosts asked")
    waiting = {row["host"] for row in pending(project)}
    if unknown := sorted({host.lower() for host in hosts} - waiting):
        raise ValueError(f"no request waits for an answer for {', '.join(unknown)}")
    for host in dict.fromkeys(host.lower() for host in hosts):
        respond(host, project, said)


def main(argv: list[str] | None = None) -> int:
    """`daodan egress PROJECT...`: the requests waiting for an answer, by tool, as JSON. It never answers one: only the
    app does, where the user sees them."""
    parser = argparse.ArgumentParser(description="The hosts an analysis waits for the user to approve in the app.")
    parser.add_argument("projects", nargs="+", type=Path, help="the analysed project's folder")
    args = parser.parse_args(argv)
    print(json.dumps(groups([str(path.resolve()) for path in args.projects]), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
