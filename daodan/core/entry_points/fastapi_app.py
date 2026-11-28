"""Source: the routes of a FastAPI application, from FastAPI's own loader and its own route objects, run in Daodan's container.

Measured on Modal (FastAPI 0.165.0 with Starlette 1.10.0 and fastapi-cli 0.0.34, the runner's image, the network blocked; the same fixture
on 0.115.14 and 0.137.1): what the script prints, how the snapshot names and places the functions it binds, and what each failure writes are
in `benchmarks/fastapi-routes/README.md`; the answers the tests read are `tests/fixtures/premap/fastapi/`. The source is one of
`entry_points.FRAMEWORK_SOURCES`: its rows are entries of the links. It is written and tested and not wired (the patches are `benchmarks/fastapi-routes/wiring/`):
on two real applications the pinned Noir gives the same routes with the same functions and the framework's objects add none (`benchmarks/fastapi-routes/README.md`,
«Applicazioni vere»).

`commands` describes, for each folder with a Python manifest (`pyproject.toml` or `requirements.txt`, the files the restore of
`preparation.RESTORES` starts from) that declares `fastapi` among the pre-map's own `packages` (`context.stated`), Daodan's script
(`fastapi_routes.py`, which loads `python_script.py`) run, under `timeout` and with no network, in that folder by the Python of the environment
the runner restored for it: the nearest folder above it that the restore makes an environment for (`preparation.python_environment`, the code
the dynamic step of the Python tests and the Flask source use too) and, for Poetry, the one Poetry says. The script loads the application
the way `fastapi dev` and `fastapi run` find it (`fastapi-cli`: `[tool.fastapi] entrypoint`, else `main.py`, `app.py`, `api.py` and the
`app/` ones, and the object `app`, `api` or the first FastAPI one) and prints each route of it with its methods and its endpoint. The loader is
`fastapi-cli`'s, which comes with `fastapi[standard]`: a project that declares plain `fastapi` has no loader, and its folder is a gap that says
the module is missing. The application is project code, so it runs only there.

`read` gives each function as a name at a position, the form the links' binder ties to a function of the snapshot (`binder.bind`, spec 8.13
point 2: the source opens no store): a row of the shape `route` with the path as FastAPI writes it (`/files/{file_path:path}`, with the prefix of
the routers and mounts above it), one row per method (none for a class-based endpoint), `handler` the function's name and `site` the file and the line
of its `def`, which the script takes from the interpreter's own parse of the source. The function is the one FastAPI runs: after `functools.wraps`
the decorated function, without it the wrapper. The binder says the gap for a name it does not find once at that line (a lambda: the snapshot calls
it `(lambda)`). An endpoint with no file of the interpreter (a `functools.partial`, an object with `__call__`) or in a file the snapshot does not hold
is a gap that names it, and no row. An endpoint whose file is in the packages of the restored environment is not the project's: the four routes FastAPI
registers for itself (`openapi_url`, `docs_url`, `redoc_url` and `swagger_ui_oauth2_redirect_url`: the script says `docs`, from the owning application's
own attributes) are silent; one of a distribution that PEP 610's `direct_url.json` says was installed from a local directory is a gap (an installed copy of
the project, not the snapshot's file) with the directory; the others are counted in one `model_partial` gap of the folder with the routes and their modules.
A class-based endpoint (`HTTPEndpoint`) is a row on its class's file with the gap: which method of the class answers which HTTP method is not read here.
A websocket is a row of the shape `websocket` with neither method nor schema: it is an entry, and offers no route to the links.
Each row has the `schema` of its path (`_schema`), so the routes are offered to the links as Noir's, Next.js's and Flask's are; a route with an argument
that may hold a `/` (`path`), or whose convertor does not say it holds one segment (a convertor of the project's), has none (None), which the links tell
as a gap of the declared routes.

What the script cannot give is a gap and no wrong row: a loader that took the first FastAPI object of a module with another one in it, or with a `app`
that is something else (a wrapper), says the folder's application is not known (`competing`); a project that does not load (no default file, no
object, a module that raises, a package missing, `fastapi-cli` missing) is a gap with the words the script wrote first; without a container engine the
source states a gap, and nothing of the project runs on the machine of Daodan. A mount whose application has no routes (`StaticFiles`) and a route of a
type Starlette does not have (FastAPI 0.137.0's and 0.137.1's `_IncludedRouter`) are named in one `model_partial` gap of the folder; a `root_path` is one
too. Not read, and not told: the routes `app.frontend` registers (not in `app.routes`; a private list of the application, inferred), `app.not_found`'s (a function of the project;
never run), and any a lifespan or a startup handler adds, which loading does not run.

Evaluated and not used: `app.openapi()` (path, method and `operationId`, no function, and it fails where a model has no JSON schema while the routes
are there); `fastapi routes` does not exist; the private `_iter_routes_with_context` and `router.routes` (the release notes of 0.137.0 call it an
implementation detail). The routes are `fastapi.routing.iter_route_contexts` (0.137.2, named in its release notes) or, before it, `app.routes`.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

import preparation

NAME, VERSION, RANK = "fastapi", "daodan/premap/v1", "scanner"
SCRIPT = "fastapi_routes.py"  # beside this module, with `python_script.py` which it loads; `container_runner.TOOLS["fastapi"]` unpacks both at `T/`
RUN_TOTAL = 900  # seconds the script may take in all the folders together: a run lasts 1800, the restore of the packages in it
# `container_runner.TOOLS["fastapi"]` takes the 3 GB of the Node tools. Measured: the script's peak is 64-75 MB on the fixture and 122 MB for 4000
# routes (`benchmarks/fastapi-routes/README.md`); the peak of the project's own modules, and of the restore, on a large application is not measured
MEMORY_GB = 3
LISTED = 8  # how many routes of the environment's one gap, and of the one that are not read, name


def run_seconds(folders: int) -> int:
    """The time the script has in each of `folders` folders: they share `RUN_TOTAL`, so a project that takes its time does not
    take the rows of the others."""
    # shortcut: a project of more than 90 folders asks for more than RUN_TOTAL, 10 seconds each at the least; when one is met, raise it
    return max(10, RUN_TOTAL // folders)


def _python_folders(context) -> list[str]:
    """The folders whose manifest declares `fastapi`, among the pre-map's packages (the ecosystem and the name are the readers' own,
    `requirements` and the module graph; no import is searched). A package declared in another file than the restore's marks
    (`requirements/base.txt`) is not a folder: the restore does not run there."""
    # shortcut: only a `pyproject.toml` or a `requirements.txt` names a folder; a project that declares FastAPI elsewhere has no row and no gap
    return sorted({PurePosixPath(p["declared_in"].partition("#")[0]).parent.as_posix()
                   for p in context.stated.get("packages", ())
                   if p.get("ecosystem") == "pypi" and p.get("name") == "fastapi"
                   and PurePosixPath(p["declared_in"].partition("#")[0]).name in preparation.PYTHON})


def commands(context):
    from container import WORKDIR
    folders = _python_folders(context)
    if not folders:
        return None
    # the lockfiles are the checkout's: the snapshot keeps none, and a folder's manager is the one its lockfile names
    held = preparation.python_environments(context.inventory.files, lambda rel: (context.root / rel).is_file())
    seconds = str(run_seconds(len(folders)))
    found = []
    for folder in folders:
        env = preparation.python_environment(held, folder) or folder
        python = preparation.python_interpreter(env, held.get(env, "pip"), WORKDIR)
        found.append({"tool": NAME, "argv": ["sh", "-c", f'exec timeout --kill-after=10 "$1" {python} -I "$2"', "fastapi", seconds,
                                             f"{preparation.T}/{SCRIPT}"],
                      "cwd": folder, "env": {}, "network": "none", "venv": env})
    return found


def _stopped(result: dict, command: dict) -> str:
    """Why the script did not give its answer: the limit that ended it, or what it wrote first; and the environment it ran in, for
    the Python is the nearest folder's above, not always the folder's own."""
    from entry_points import frameworks
    where = f" (the Python of the environment restored for {command['venv']!r})" if command.get("venv") is not None else ""
    return frameworks.stopped(result, SCRIPT, command["argv"][4], MEMORY_GB) + where


def _text(value) -> bool:
    return value is None or isinstance(value, str)


def _flag(value) -> bool:
    return isinstance(value, bool)


def _names(value) -> bool:
    return isinstance(value, list) and all(isinstance(name, str) for name in value)


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


def _route(route) -> bool:
    if not (isinstance(route, dict) and route.get("kind") in ("http", "websocket") and isinstance(route.get("path"), str)
            and _names(route.get("methods")) and _flag(route.get("docs"))):
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
    what is not the known layout."""
    try:
        document = json.loads(result["stdout"])
    except ValueError:
        raise ValueError("the output is no JSON") from None
    competing = document.get("competing") if isinstance(document, dict) else None
    if not (isinstance(document, dict) and document.get("called") is True and isinstance(document.get("application"), str)
            and isinstance(document.get("found"), str) and isinstance(document.get("root_path"), str)
            and isinstance(competing, dict) and _names(competing.get("others")) and _names(competing.get("shadowed"))
            and isinstance(document.get("routes"), list) and isinstance(document.get("unread"), list)):
        raise ValueError("no `called`, `application`, `found`, `root_path`, `competing` and lists of `routes` and `unread`")
    if not all(isinstance(item, dict) and _text(item.get("path")) and isinstance(item.get("type"), str) for item in document["unread"]):
        raise ValueError("a route that is not read, of an unknown layout")
    if not all(_route(route) for route in document["routes"]):
        raise ValueError("a route of an unknown layout")
    return document


def _schema(route: dict) -> str | None:
    """The path of a route as `REST` reads it (`flows.path_schema`: `/api/users/{}` for `/api/users/{user_id}`, as for Noir's and
    Next.js's rows), made from Starlette's own compiled path and convertors (`parts` and `arguments` of the script, never the text of
    `path`): each argument whose convertor class says it holds one segment is a hole. None where the script gave no parts, or an argument may
    hold a `/` (`path`), or its convertor does not say (one of the project's: Starlette has no `part_isolating`): the route stands for several
    path schemas, a gap of the declared routes and never a join."""
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


def _list(items: list[tuple]) -> str:
    return ", ".join(f"{path} ({what})" for path, what in items[:LISTED]) + (f" and {len(items) - LISTED} more" if len(items) > LISTED else "")


def _rules(context, folder: str, document: dict, kinds: dict) -> tuple[list[dict], list[dict]]:
    """The rows and the gaps of one folder's routes."""
    import flows
    rows, gaps, shared = [], [], []
    for route in document["routes"]:
        handler, path = route["handler"], route["path"]
        file = posixpath.normpath(posixpath.join(folder, handler["file"])) if handler and handler.get("file") else None
        outside = file is None or file.startswith("..") or file not in context.inventory.headers
        if outside and handler and handler["environment"]:
            installed = handler.get("distribution")
            if route["docs"]:
                continue  # one of the four routes FastAPI registers for itself
            if installed:
                gaps.append({"kind": "outside_snapshot", "path": folder, "detail": (
                    f"{path}: {handler.get('qualname')} is an installed copy of the project, not the snapshot's file: "
                    f"{installed['name']} was installed from {installed['url']} ({file})")})
            else:
                shared.append((path, (handler.get("module") or "?").split(".")[0]))
            continue
        if outside:
            cause = ("no function: the route has no endpoint" if handler is None else
                     f"{handler.get('qualname') or handler['type']} has no source file of the project the snapshot holds "
                     f"({file or 'none'})")
            gaps.append({"kind": "outside_snapshot", "path": folder, "detail": f"{path}: {cause}"})
            continue
        http = route["kind"] == "http"
        base = {"reader": NAME, "shape": "route" if http else "websocket", "kind": kinds[route["kind"]], "path": path,
                **({"schema": _schema(route)} if http else {})}
        module = {**base, "site": file, "symbol": f"{file}::{flows.MODULE}"}
        for method in route["methods"] or [None]:  # a route that declares none: one row with no method
            one = {**module, **({"method": method} if method else {})}
            if handler["kind"] == "class":
                rows.append({**one, "gap": f"{handler.get('qualname')} is a class-based endpoint: which of its methods answers "
                                           f"{method or 'a request'} is not read"})
            else:  # a name at a position: the links' binder ties it to the one function of that name that holds the line
                line = handler.get("line")
                rows.append({**one, "site": f"{file}:{line}" if line else file, "handler": handler["qualname"].rsplit(".", 1)[-1]})
    if shared:
        many = len(shared) != 1
        gaps.append({"kind": "model_partial", "path": folder, "detail": (
            f"{len(shared)} route{'s' if many else ''} of the application {'are views' if many else 'is a view'} of packages of the restored "
            f"environment, not of the project: {_list(shared)}")})
    unread = [(item["path"] or "?", item["type"]) for item in document["unread"]]
    if unread:
        many = len(unread) != 1
        gaps.append({"kind": "model_partial", "path": folder, "detail": (
            f"{len(unread)} route{'s' if many else ''} of the application {'are' if many else 'is'} of a kind the script does not read (a mount "
            f"whose application has no routes, a route of a class Starlette does not have): {_list(unread)}")})
    if document["root_path"]:
        gaps.append({"kind": "model_partial", "path": folder, "detail": (
            f"the application has root_path {document['root_path']!r}: a proxy serves it under that prefix, which its routes lack")})
    if not document["routes"] and not unread:
        gaps.append({"kind": "model_partial", "path": folder, "detail": "the application has no route"})
    elif not rows and not gaps:
        gaps.append({"kind": "model_partial", "path": folder, "detail": "the application has no route of the project: it holds only FastAPI's "
                                                                          "own documentation routes"})
    return rows, gaps


def _competing(document: dict) -> str | None:
    """Why the application the loader took may not be the one the project serves, when the loader took the first FastAPI object of its module
    (no `entrypoint`, and none called `app` or `api`): the module holds other FastAPI objects, or `app` or `api` is something else, which is
    a wrapper around the one it took, whose mount prefixes the routes of the application lack."""
    competing, application = document["competing"], document["application"]
    said = []
    if competing["others"]:
        said.append(f"the loader of fastapi-cli took `{application}`, the first FastAPI object it found, and the module holds another "
                    f"({', '.join(competing['others'])}): which one the project serves is not known")
    if competing["shadowed"]:
        said.append(f"`{competing['shadowed'][0]}` of the module is not a FastAPI application but something else (a wrapper around `{application}`?): "
                    "its routes lack the prefix a wrapper mounts it at")
    return "; ".join(said) + ", so no route is read" if said else None


def read(context, commands, results):
    import entries
    from entry_points import frameworks
    kinds = {"http": entries.QUERIES[NAME]["route"]["kind"], "websocket": entries.QUERIES[NAME]["websocket"]["kind"]}
    gaps, rows = [], []
    for command, result in zip(commands, results):
        folder = command["cwd"]
        if result["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": folder, "detail": _stopped(result, command)})
            continue
        try:
            document = _printed(result)
        except ValueError as error:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"{SCRIPT} printed no JSON of the known layout ({error}): {frameworks.excerpt(result)}"})
            continue
        why = _competing(document)
        if why:
            gaps.append({"kind": "model_partial", "path": folder, "detail": why})
            continue
        found, notes = _rules(context, folder, document, kinds)
        rows += found
        gaps += notes
    return {"facts": {"framework_entries": rows} if rows else {}, "gaps": gaps}


def from_record(report):
    """The rows this source persisted in the record of the entry points and its gaps there; a record made without the source, or where it was not
    needed, has none."""
    source = f"{NAME}@{VERSION}"
    return ([row for row in report.get("framework_entries", ()) if source in row["sources"]],
            [gap for gap in report["gaps"] if gap.get("source") == source])
