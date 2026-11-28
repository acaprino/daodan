"""Source: the routes of a Flask application, from Flask's own loader and its own `url_map`, run in Daodan's container.

Measured on Modal (Flask 3.1.3 and Werkzeug 3.1.9, the runner's image, the network blocked): what the script prints, how the snapshot
names and places the functions it binds, and what each failure writes are in `benchmarks/flask-routes/README.md`; the answers the
tests read are `tests/fixtures/premap/flask/`. The source is not wired (`benchmarks/flask-routes/README.md`, «Applicazioni vere»: on real
applications Noir gives the same routes and functions): it is not in `entry_points.SOURCES` and `FRAMEWORK_SOURCES`, and `entry-queries.json`
has no table for it, so `read` needs `entries.QUERIES["flask"]` (the tests and the benchmark put it there); wired, its rows are entries
of the links.

`commands` describes, for each folder with a Python manifest (`pyproject.toml` or `requirements.txt`, the files the restore of
`preparation.RESTORES` starts from) that declares `flask` among the pre-map's own `packages` (`context.stated`), Daodan's script
(`flask_routes.py`) run, under `timeout` and with no network, in that folder by the Python of the environment the runner restored for
it: the nearest folder above it that the restore makes an environment for (`preparation.python_environment`, the code the dynamic
step of the Python tests uses too: a uv workspace member runs in the root's, a folder inside a marked folder in that one's, a
folder with its own lockfile in its own, from the files of the project's perimeter, `preparation.perimeter_files`, which are the
ones the restore reads: a git-ignored lockfile is none of them) and, for Poetry, the one Poetry says (`poetry env info -e`). The script loads the
application with Flask's own `ScriptInfo.load_app`, which is project code, so it runs only there, and prints each rule of
`app.url_map` with its methods and its view function.

`read` gives each function as a name at a position, the form the links' binder ties to a function of the snapshot
(`binder.bind`, spec 8.13 point 2: the source opens no store): a row of the shape `route` with the rule as Flask writes it, one row
per method (none for a rule that declares none), `handler` the function's name and `site` the file and the line of its `def`, which the
script takes from the interpreter's own parse of the source (a decorated function's `co_firstlineno` is its first decorator). The
function is the one Flask runs: after `functools.wraps` the decorated function, without it the wrapper. The binder says the gap for a
name it does not find once at that line (a lambda: the snapshot calls it `(lambda)`). A view with no file of the interpreter (a
`functools.partial`, an object with `__call__`) or in a file the snapshot does not hold is a gap that names it, and no row. A view whose
file is in the packages of the restored environment is not the project's: Flask's own static rules (the script says `static`: the
application's, by `app.has_static_folder` and the endpoint Flask gives it; a blueprint's, by `app.blueprints` and its own
`send_static_file` being the view) are silent; a view of a distribution that PEP 610's `direct_url.json` says was
installed from a local directory is a gap (an installed copy of the project, not the snapshot's file) with the directory; the others
are counted in one `model_partial` gap of the folder with the rules and their modules (an extension's routes, a decorator that does
not use `functools.wraps`). A rule that is `build_only` or only redirects is no row and no gap. A class-based view (`view_class`)
is a row on its class's file with the gap: which method of the class answers which HTTP method is the class's `dispatch_request`,
not read here. A `DispatcherMiddleware` (`dispatch`, found by its class) that mounts the loaded application at a prefix, or holds
another application and not it, makes the folder a gap and no row, for the rules lack the prefix the dispatcher serves them under; one
whose main application is the loaded one keeps its rows and the gap names the Flask applications it mounts, with their rules as
served, not as rows. Any other wrapping of the application is not seen. A project that does not load (no `wsgi.py` or `app.py`, a
module that raises, a package missing), or whose script could not write its answer (exit 4), is a gap with the words the script
wrote first; without a container engine the source states a gap, and nothing of the project runs on the machine of Daodan. What a
folder's `read` takes from the answer is checked first, and whatever still fails while it is read (`ValueError`, `KeyError`,
`TypeError`, `RecursionError`) is that folder's gap, never an exception that loses the other folders' rows.
Each row has the `schema` of its path (`_schema`), so the routes are offered to the links as Noir's and Next.js's are; a rule with
an argument that may hold a `/` has none (None), which the links tell as a gap of the declared routes.

Evaluated and not used: `flask routes` (a text table without function, file or JSON).
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

import preparation

NAME, VERSION, RANK = "flask", "daodan/premap/v3", "scanner"
SCRIPT = "flask_routes.py"  # beside this module; `container_runner.TOOLS["flask"]` unpacks it at `T/SCRIPT`
RUN_TOTAL = 900  # seconds the script may take in all the folders together: a run lasts 1800, the restore of the packages in it
# `container_runner.TOOLS["flask"]` takes the 3 GB of the Node tools. Measured: the script's peak is 48-53 MB on the fixture and 75 MB for
# 3000 rules (`benchmarks/flask-routes/README.md`); the peak of the project's own modules, and of the restore, on a large application is
# not measured
MEMORY_GB = 3
LISTED = 8  # how many rules of the environment's one gap names


def run_seconds(folders: int) -> int:
    """The time the script has in each of `folders` folders: they share `RUN_TOTAL`, so a project that takes its time does not
    take the rows of the others."""
    # shortcut: a project of more than 90 folders asks for more than RUN_TOTAL, 10 seconds each at the least; when one is met, raise it
    return max(10, RUN_TOTAL // folders)


def _python_folders(context) -> list[str]:
    """The folders whose manifest declares `flask`, among the pre-map's packages (the ecosystem and the name are the readers' own,
    `requirements` and the module graph; no import is searched). A package declared in another file than the restore's marks
    (`requirements/base.txt`) is not a folder: the restore does not run there."""
    # shortcut: only a `pyproject.toml` or a `requirements.txt` names a folder, and only `flask` itself: a project that declares a package built
    # on Flask (Dash, Flask-RESTX) and not Flask, or Flask elsewhere, has no row and no gap. A lockfile lists the resolved packages, but the
    # pre-map reads no Python lock for them (`premap/uv.py` exports one in pylock.toml and keeps its local packages; Poetry's is not read):
    # when one states them, a folder whose lock holds `flask` is a Flask folder
    return sorted({PurePosixPath(p["declared_in"].partition("#")[0]).parent.as_posix()
                   for p in context.stated.get("packages", ())
                   if p.get("ecosystem") == "pypi" and p.get("name") == "flask"
                   and PurePosixPath(p["declared_in"].partition("#")[0]).name in preparation.PYTHON})


def commands(context):
    from container import WORKDIR
    folders = _python_folders(context)
    if not folders:
        return None
    # a folder's manager is the one its lockfile names, and the restore reads the files of the project's perimeter (the snapshot keeps no lockfile)
    held = preparation.python_environments(preparation.perimeter_files(context.root))
    seconds = str(run_seconds(len(folders)))
    found = []
    for folder in folders:
        env = preparation.python_environment(held, folder)  # a folder that declares flask has a manifest, so a marked folder at or above it
        python = preparation.python_interpreter(env, held[env], WORKDIR)
        found.append({"tool": NAME, "argv": ["sh", "-c", f'exec timeout --kill-after=10 "$1" {python} -I "$2"', "flask", seconds,
                                             f"{preparation.T}/{SCRIPT}"],
                      "cwd": folder, "env": {}, "network": "none", "venv": env})
    return found


def _stopped(result: dict, command: dict) -> str:
    """Why the script did not give its answer: the limit that ended it, or what it wrote first; and the environment it ran in, for
    the Python is the nearest folder's above, not always the folder's own."""
    from entry_points import frameworks
    where = f" (the Python of the environment restored for {command['venv']!r})" if command.get("venv") is not None else ""
    if result["returncode"] == 4:  # the script's own: it could not write the answer to the descriptor it saved
        return f"{SCRIPT} could not write its answer (exit 4): {frameworks.excerpt(result)}{where}"
    return frameworks.stopped(result, SCRIPT, command["argv"][4], MEMORY_GB) + where


def _text(value) -> bool:
    return value is None or isinstance(value, str)


def _flag(value) -> bool:
    return isinstance(value, bool)


def _handler(handler) -> bool:
    if handler is None:
        return True
    if not (isinstance(handler, dict) and handler.get("kind") in ("function", "class") and isinstance(handler.get("type"), str)
            and _text(handler.get("module")) and _text(handler.get("qualname")) and _text(handler.get("file")) and _flag(handler.get("environment"))
            and (handler.get("line") is None or isinstance(handler["line"], int) and not _flag(handler["line"]))):
        return False
    installed = handler.get("distribution")
    return ((installed is None or isinstance(installed, dict) and isinstance(installed.get("name"), str) and isinstance(installed.get("url"), str))
            and (handler.get("file") is None or isinstance(handler.get("qualname"), str)))  # a file is a function or a class, which has a name


def _dispatch(dispatch) -> bool:
    if dispatch is None:
        return True
    mounts = dispatch.get("mounts") if isinstance(dispatch, dict) else None
    return (isinstance(dispatch, dict) and dispatch.get("loaded") in ("main", "mounted", "other")
            and isinstance(dispatch.get("prefixes"), list) and all(isinstance(prefix, str) for prefix in dispatch["prefixes"])
            and isinstance(mounts, list) and all(
                isinstance(mount, dict) and isinstance(mount.get("prefix"), str) and isinstance(mount.get("count"), int)
                and not _flag(mount["count"]) and isinstance(mount.get("rules"), list) and all(isinstance(rule, str) for rule in mount["rules"])
                for mount in mounts))


def _route(route) -> bool:
    if not (isinstance(route, dict) and isinstance(route.get("rule"), str) and isinstance(route.get("methods"), list) and "handler" in route
            and all(isinstance(method, str) for method in route["methods"])
            and all(_flag(route.get(key)) for key in ("build_only", "redirect_to", "static"))):
        return False
    parts, arguments = route.get("parts"), route.get("arguments")
    return ((parts is None or isinstance(parts, list) and all(isinstance(part, list) and len(part) == 2 and _flag(part[0])
                                                                and isinstance(part[1], str) for part in parts))
            and (arguments is None or isinstance(arguments, dict) and all(isinstance(name, str) and (isolating is None or _flag(isolating))
                                                                           for name, isolating in arguments.items()))
            and _handler(route.get("handler")))


def _printed(result: dict) -> dict:
    """The document the script printed: the whole standard output, checked as `read` uses it (every value it reads has the type it
    needs, so a malformed answer is a gap of its folder and never an exception in the middle of the others). Raises ValueError for
    what is not the known layout: `called`, `dispatch` and a list of rules."""
    try:
        document = json.loads(result["stdout"])
    except ValueError:
        raise ValueError("the output is no JSON") from None
    if not (isinstance(document, dict) and document.get("called") is True and "dispatch" in document and _dispatch(document["dispatch"])
            and isinstance(document.get("routes"), list)):
        raise ValueError("no `called`, `dispatch` and list of `routes`")
    if not all(_route(route) for route in document["routes"]):
        raise ValueError("a rule of an unknown layout")
    return document


def _schema(route: dict) -> str | None:
    """The path of a rule as `REST` reads it (`flows.path_schema`: `/admin/users/{}` for `/admin/users/<int:user_id>`, as for Noir's
    and Next.js's rows), made from werkzeug's own parts of the rule (`parts` and `arguments` of the script, never the text of
    `rule`): each argument whose converter says `part_isolating` is a hole. None where werkzeug gave no parts, or an argument may hold
    a `/` (`PathConverter`, or a converter with a `/` in its regex), or its converter does not say: the rule stands for several path
    schemas, a gap of the declared routes and never a join. The text of a rule that holds `{...}` or starts a segment with `:` is read
    by `path_schema` as a parameter."""
    import flows
    parts, arguments = route.get("parts"), route.get("arguments")
    if not parts or arguments is None:
        return None
    path = ""
    for dynamic, text in parts:
        if not dynamic:
            path += text
        elif arguments.get(text) is True:
            path += "{" + text + "}"
        else:
            return None
    return flows.path_schema(path)


def _rules(context, folder: str, routes: list[dict], kind: str) -> tuple[list[dict], list[dict]]:
    """The rows and the gaps of one folder's rules."""
    import flows
    rows, gaps, shared = [], [], []
    if not routes:
        return rows, [{"kind": "model_partial", "path": folder, "detail": "the application has no rule in its url_map"}]
    for route in routes:
        if route["build_only"] or route["redirect_to"]:
            continue  # werkzeug never matches the one, and the other answers with a redirect: no function of the project serves them
        handler = route["handler"]
        file = posixpath.normpath(posixpath.join(folder, handler["file"])) if handler and handler.get("file") else None
        outside = file is None or file.startswith("..") or file not in context.inventory.headers
        if outside and handler and handler["environment"]:
            installed = handler.get("distribution")
            if route["static"]:
                continue  # the rule Flask registers for its own `static_folder`
            if installed:
                gaps.append({"kind": "outside_snapshot", "path": folder, "detail": (
                    f"{route['rule']}: {handler.get('qualname')} is an installed copy of the project, not the snapshot's file: "
                    f"{installed['name']} was installed from {installed['url']} ({file})")})
            else:
                shared.append((route["rule"], (handler.get("module") or "?").split(".")[0]))
            continue
        if outside:
            cause = ("no function: Flask's view for this endpoint is missing" if handler is None else
                     f"{handler.get('qualname') or handler['type']} has no source file of the project the snapshot holds "
                     f"({file or 'none'})")
            gaps.append({"kind": "outside_snapshot", "path": folder, "detail": f"{route['rule']}: {cause}"})
            continue
        base = {"reader": NAME, "shape": "route", "kind": kind, "path": route["rule"], "schema": _schema(route)}
        module = {**base, "site": file, "symbol": f"{file}::{flows.MODULE}"}
        for method in route["methods"] or [None]:  # a rule that declares none: one row with no method
            one = {**module, **({"method": method} if method else {})}
            if handler["kind"] == "class":
                rows.append({**one, "gap": f"{handler.get('qualname')} is a class-based view: which of its methods answers "
                                           f"{method or 'a request'} is not read"})
            else:  # a name at a position: the links' binder ties it to the one function of that name that holds the line
                line = handler.get("line")
                rows.append({**one, "site": f"{file}:{line}" if line else file, "handler": handler["qualname"].rsplit(".", 1)[-1]})
    if shared:
        many = len(shared) != 1
        listed = ", ".join(f"{rule} ({module})" for rule, module in shared[:LISTED]) + (f" and {len(shared) - LISTED} more" if len(shared) > LISTED else "")
        gaps.append({"kind": "model_partial", "path": folder, "detail": (
            f"{len(shared)} rule{'s' if many else ''} of the application {'are views' if many else 'is a view'} of packages of the restored "
            f"environment, not of the project: {listed}")})
    if not rows and not gaps:
        gaps.append({"kind": "model_partial", "path": folder, "detail": "the application has no rule of the project: its url_map holds "
                                                                          "only Flask's own static rule, or rules that are not served"})
    return rows, gaps


def _served(dispatch: dict) -> str:
    """The other Flask applications a dispatcher serves, with the first of their rules as it serves them (`prefix + rule`)."""
    return "; ".join(f"{mount['prefix'] or '(the root)'}: {', '.join(mount['rules'])}"
                     + (f" and {mount['count'] - len(mount['rules'])} more" if mount["count"] > len(mount["rules"]) else "") for mount in dispatch["mounts"])


def _dispatched(dispatch: dict) -> str:
    """Why a folder with a `DispatcherMiddleware` around its application has no rows, or what rows it has are not all of it."""
    if dispatch["loaded"] == "main":
        return f"the DispatcherMiddleware of the application mounts other Flask applications, whose rules are not rows: {_served(dispatch)}"
    cause = (f"the loaded application is mounted by a DispatcherMiddleware at {', '.join(dispatch['prefixes'])}: its rules lack the prefix"
             if dispatch["loaded"] == "mounted" else
             "a DispatcherMiddleware of the application's module does not hold the loaded application: the paths it is served at are not known")
    return f"{cause}, so none is read" + (f"; the Flask applications it serves, not rows: {_served(dispatch)}" if dispatch["mounts"] else "")


def read(context, commands, results):
    import entries
    from entry_points import frameworks
    kind = entries.QUERIES[NAME]["route"]["kind"]
    gaps, rows = [], []
    for command, result in zip(commands, results):
        folder = command["cwd"]
        if result["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": folder, "detail": _stopped(result, command)})
            continue
        try:  # one folder's answer: whatever it does to the code that reads it is that folder's gap
            document = _printed(result)
            dispatch = document["dispatch"]
            found, notes = ([], []) if dispatch and dispatch["loaded"] != "main" else _rules(context, folder, document["routes"], kind)
        except ValueError as error:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"{SCRIPT} printed no JSON of the known layout ({error}): {frameworks.excerpt(result)}"})
            continue
        except (KeyError, TypeError, RecursionError) as error:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"{SCRIPT} printed an answer that could not be read ({type(error).__name__}: {error}): {frameworks.excerpt(result)}"})
            continue
        if dispatch:
            notes.append({"kind": "model_partial", "path": folder, "detail": _dispatched(dispatch)})
        rows += found
        gaps += notes
    return {"facts": {"framework_entries": rows} if rows else {}, "gaps": gaps}


def from_record(report):
    """The rows this source persisted in the record of the entry points and its gaps there; a record made without the source, or where it was not
    needed, has none."""
    source = f"{NAME}@{VERSION}"
    return ([row for row in report.get("framework_entries", ()) if source in row["sources"]],
            [gap for gap in report["gaps"] if gap.get("source") == source])
