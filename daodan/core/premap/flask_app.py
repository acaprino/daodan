"""Source: the routes of a Flask application, from Flask's own loader and its own `url_map`, run in Daodan's container.

NOT YET RUN. This source was written without a container to try it in (no Modal credentials on the machine that wrote it):
nothing below is measured, `benchmarks/flask-routes/README.md` lists what was read in Flask's source and what the probe has to
measure, and the source is not in `premap.SOURCES` nor in `premap.FRAMEWORK_SOURCES` until it has been.

`commands` describes, for each folder with a Python manifest (`pyproject.toml` or `requirements.txt`, the files the restore of
`preparation.RESTORES` starts from) that declares `flask` among the pre-map's own `packages` (`context.stated`), Daodan's script
(`flask_routes.py`) run by the Python of the environment the runner restored for that folder (`container_runner.TOOLS["flask"]`,
`restores: "python"`), under `timeout`, with no network. The script loads the application with Flask's own `ScriptInfo.load_app`,
which is project code, so it runs only there, and prints each rule of `app.url_map` with its methods and its view function.

`read` binds each function to the snapshot's record of it, by file and qualified name (`sem_declarations`, the record the
snapshot's Python reader makes, where a nested function is `outer.inner` and Python's `__qualname__` has `outer.<locals>.inner`):
a row of the shape `route` at the function's `file:line`, with the rule as Flask writes it and one row per method (none for a rule
that names none). A handler with no such record is a row on its file with the gap and the cause, never a guess by name: a lambda,
a `functools.partial`, a callable object, a wrapper made without `functools.wraps`, a function in a file the snapshot does not
hold (a package of the environment), or a name the snapshot has twice. A class-based view (`view_class`) is a row on its class's
file with the gap: which method of the class answers which HTTP method is the class's `dispatch_request`, not read here. A
project that does not load (no `wsgi.py` or `app.py`, a module that raises, a package missing) is a gap with the words the
script wrote first; without a container engine the source states a gap, and nothing of the project runs on the machine of Daodan.
The rows are entries, not offered routes.

Evaluated and not used: `flask routes` (a text table without function, file or JSON).
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

import preparation

NAME, VERSION, RANK = "flask", "daodan/premap/v1", "scanner"
SCRIPT = "flask_routes.py"  # beside this module; `container_runner.TOOLS["flask"]` unpacks it at `T/SCRIPT`
RUN_TOTAL = 900  # seconds the script may take in all the folders together: a run lasts 1800, the restore of the packages in it
# not measured: `container_runner.TOOLS["flask"]` takes the 3 GB of the Node tools; the figure of an application that loads many modules is not known
MEMORY_GB = 3


def run_seconds(folders: int) -> int:
    """The time the script has in each of `folders` folders: they share `RUN_TOTAL`, so a project that takes its time does not
    take the rows of the others."""
    # shortcut: a project of more than 90 folders asks for more than RUN_TOTAL, 10 seconds each at the least; when one is met, raise it
    return max(10, RUN_TOTAL // folders)


def _folders(context) -> list[str]:
    """The folders whose manifest declares `flask`, among the pre-map's packages (the ecosystem and the name are the readers' own,
    `requirements` and the module graph; no import is searched). A package declared in another file than the restore's marks
    (`requirements/base.txt`) is not a folder: the restore does not run there."""
    # shortcut: only a `pyproject.toml` or a `requirements.txt` names a folder; a project that declares Flask elsewhere has no row and no gap
    return sorted({PurePosixPath(p["declared_in"].partition("#")[0]).parent.as_posix()
                   for p in context.stated.get("packages", ())
                   if p.get("ecosystem") == "pypi" and p.get("name") == "flask"
                   and PurePosixPath(p["declared_in"].partition("#")[0]).name in preparation.PYTHON})


def commands(context):
    folders = _folders(context)
    if not folders:
        return None
    seconds = str(run_seconds(len(folders)))
    return [{"tool": NAME, "argv": ["timeout", "--kill-after=10", seconds, f"{preparation.VENVS}/{folder}/bin/python", "-I",
                                    f"{preparation.T}/{SCRIPT}"],
             "cwd": folder, "env": {}, "network": "none"} for folder in folders]


def _stopped(result: dict, seconds: str) -> str:
    """Why the script did not give its answer: the limit that ended it, or what it wrote first (both ends of it)."""
    from premap import react_router
    if result["returncode"] == 124:  # `timeout` ended the command
        return f"{SCRIPT} did not end in {seconds} seconds"
    if result["returncode"] == 137:  # `timeout` had to kill it, or the memory of the run did: the signal does not say which
        return f"{SCRIPT} was killed (exit 137): it did not end in {seconds} seconds, or it ran out of memory ({MEMORY_GB} GB)"
    return f"{SCRIPT} exited with {result['returncode']}: {react_router._excerpt(result)}"


def _printed(result: dict) -> list[dict]:
    """The routes of the last line of the script's standard output (a module of the project may print before it). Raises
    ValueError for a line that is not the known layout: `called` and a list of rules with `rule`, `methods` and a `handler`."""
    lines = [line for line in result["stdout"].splitlines() if line.strip()]
    try:
        printed = json.loads(lines[-1])
    except (IndexError, ValueError):
        raise ValueError("the last line is no JSON") from None
    routes = printed.get("routes") if isinstance(printed, dict) else None
    if not (isinstance(printed, dict) and printed.get("called") is True and isinstance(routes, list)):
        raise ValueError("no `called` and list of `routes`")
    for route in routes:
        handler = route.get("handler") if isinstance(route, dict) else 0
        if (not isinstance(route, dict) or not isinstance(route.get("rule"), str) or not isinstance(route.get("methods"), list)
                or not (handler is None or isinstance(handler, dict) and handler.get("kind") in ("function", "class"))):
            raise ValueError("a route with no rule, methods or handler of the known layout")
    return routes


def _records(db, file: str, qualname: str) -> list[tuple[str, int]]:
    """`(qualified name, line)` of each record of `file` whose qualified name is `qualname`."""
    from snapshot_store import _unpack
    wanted = qualname.replace(".<locals>", "")  # Python's `__qualname__` writes a nested function so; the snapshot's reader does not
    return [(_unpack(payload).get("qualified_name") or name, line) for name, line, payload in db.execute(
        "SELECT name,l0,payload FROM sem_declarations WHERE file=? AND kind IN ('function','method')", (file,))
        if (_unpack(payload).get("qualified_name") or name) == wanted]


def read(context, commands, results):
    import flows
    import semantic_store
    from premap import react_router
    gaps, rows = [], []
    with semantic_store.semantic_reader(context.store) as db:
        for command, result in zip(commands, results):
            folder = command["cwd"]
            if result["returncode"] != 0:
                gaps.append({"kind": "model_failed", "path": folder, "detail": _stopped(result, command["argv"][2])})
                continue
            try:
                routes = _printed(result)
            except ValueError as error:
                gaps.append({"kind": "model_failed", "path": folder,
                             "detail": f"{SCRIPT} printed no JSON of the known layout ({error}): {react_router._excerpt(result)}"})
                continue
            if not routes:
                gaps.append({"kind": "model_partial", "path": folder, "detail": "the application has no rule in its url_map"})
                continue
            for route in routes:
                methods = route["methods"] or [None]  # a rule that names none: one row with no method
                handler = route["handler"]
                base = {"reader": NAME, "shape": "route", "kind": "rotta", "path": route["rule"],
                        **({"host": route["host"]} if route.get("host") else {})}
                file = None
                if handler and handler.get("file"):
                    file = posixpath.normpath(posixpath.join(folder, handler["file"]))
                if file is None or file.startswith("..") or file not in context.inventory.headers:
                    cause = ("no function: Flask's view for this endpoint is missing" if handler is None else
                             f"{handler['qualname']} has no source file of the project the snapshot holds ({file or 'none'})")
                    site = file if file and not file.startswith("..") and file in context.inventory.headers else folder
                    gaps.append({"kind": "outside_snapshot", "path": site, "detail": f"{route['rule']}: {cause}"})
                    continue
                module = {**base, "site": file, "symbol": f"{file}::{flows.MODULE}"}
                if handler["kind"] == "class":
                    for method in methods:
                        rows.append({**module, **({"method": method} if method else {}),
                                     "gap": f"{handler['qualname']} is a class-based view: which of its methods answers {method or 'a request'} is not read"})
                    continue
                found = _records(db, file, handler["qualname"])
                if len(found) != 1:
                    cause = (f"the snapshot has no function {handler['qualname']} in {file} (a lambda, a partial, or a wrapper made "
                             "without functools.wraps)") if not found else f"the snapshot has {len(found)} records for {handler['qualname']} in {file}"
                    for method in methods:
                        rows.append({**module, **({"method": method} if method else {}), "gap": f"{route['rule']}: {cause}"})
                    continue
                [(qualified, line)] = found
                for method in methods:
                    rows.append({**base, **({"method": method} if method else {}), "site": f"{file}:{line}",
                                 "symbol": f"{file}::{qualified}", "handler_source": NAME, "handler": qualified})
    return {"facts": {"framework_entries": rows} if rows else {}, "gaps": gaps}


def from_record(report):
    """The rows this source persisted in a pre-map and its gaps there; a pre-map made without the source, or where it was not
    needed, has none."""
    source = f"{NAME}@{VERSION}"
    return ([row for row in report.get("framework_entries", ()) if source in row["sources"]],
            [gap for gap in report["gaps"] if gap.get("source") == source])
