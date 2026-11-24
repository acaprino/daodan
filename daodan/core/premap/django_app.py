"""Source: the routes a Django project declares, from Django's own loaded URLconf, run in Daodan's container.

Measured on Modal (Django 6.1.3, 5.2.19 and 4.2.30, the runner's image, the network blocked): what the script prints, how the snapshot names
and places the functions it binds, and what each failure writes are in `benchmarks/django-routes/README.md`; the answers the tests read are
`tests/fixtures/premap/django/`. The source is one of `premap.FRAMEWORK_SOURCES`: its rows are entries of the links.

`commands` describes, for each `manage.py` of the snapshot that sits at or below a folder with a Python manifest (`pyproject.toml` or
`requirements.txt`, the files the restore of `preparation.RESTORES` starts from) declaring `django` among the pre-map's own `packages`
(`context.stated`), Daodan's script (`django_routes.py`) run, under `timeout` and with no network, in the folder of that `manage.py` by the
Python of the environment the runner restored for it: the nearest folder above it that the restore makes an environment for
(`preparation.python_environment`, the code the dynamic step of the Python tests uses too) and, for Poetry, the one Poetry says
(`poetry env info -e`). The script runs the project's own `manage.py` with Django's documented `shell -c`, so the settings module is the one
`manage.py` sets, and prints each route of `get_resolver()` with its views; it is project code, so it runs only there.

`read` gives each function as a name at a position, the form the links' binder ties to a function of the snapshot (`binder.bind`, spec 8.13
point 2: the source opens no store): a row of the shape `route` with the route as Django writes it (`/shop/products/<int:pk>/`), `handler` the
function's name and `site` the file and the line of its `def`. Django declares no method per route: a class-based view has one row per HTTP method
its class answers (`http_method_names`, as Django's own `dispatch` reads it) on the function that answers it, and a viewset of Django REST
framework one per entry of its `actions`; a function view has one row with no method (`require_http_methods` keeps its list in a closure),
which the links tell as a declared route that has no method. A method answered by a function of a package of the environment (`ListView.get`,
`ModelViewSet.create`) is a row on the project's class (its file and line) with the gap that says so. A view whose file is in the packages of
the restored environment is not the project's: a view of a distribution that PEP 610's `direct_url.json` says was installed from a local
directory is a gap (an installed copy of the project, not the snapshot's file) with the directory; the others (the admin site, an extension's
routes, `TemplateView.as_view()` written as it is) are counted in one `model_partial` gap of the folder, by distribution: Django registers no
route of its own, so nothing is silent. A view with no file (an object with `__call__`) or in a file the snapshot does not hold is a gap that
names it. An include whose URLconf does not load (`unread`) is a gap and the other routes stay; a route under `i18n_patterns` is listed with the
prefix of the language the project loads in and one gap says that the other languages' routes are not. A project that does not load (a
settings module that raises or needs an environment variable, a missing package, a URLconf that queries a database) is a gap with the words
the script wrote first; without a container engine the source states a gap, and nothing of the project runs on the machine of Daodan.
Each row has the `schema` of its path (`_schema`) when every level of the route is a `path()` and every argument is one of Django's own
converters that spans one segment; a `re_path`, a `path` converter, a converter of the project and a route under `i18n_patterns` have none
(None), which the links tell as a gap of the declared routes.

Evaluated and not used: no command lists the URLs of a project (`show_urls` is django-extensions', third-party); see the script for the rest.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

import preparation

NAME, VERSION, RANK = "django", "daodan/premap/v2", "scanner"
SCRIPT = "django_routes.py"  # beside this module; `container_runner.TOOLS["django"]` unpacks it at `T/SCRIPT`
RUN_TOTAL = 900  # seconds the script may take in all the folders together: a run lasts 1800, the restore of the packages in it
MEMORY_GB = 3  # measured: the script's peak is 59-68 MB on the fixtures (`benchmarks/django-routes/README.md`); an application that is large is not
LISTED = 3  # how many routes of each distribution the environment's one gap names


def run_seconds(folders: int) -> int:
    """The time the script has in each of `folders` folders: they share `RUN_TOTAL`, so a project that takes its time does not take the
    rows of the others."""
    # shortcut: a project of more than 90 folders asks for more than RUN_TOTAL, 10 seconds each at the least; when one is met, raise it
    return max(10, RUN_TOTAL // folders)


def _manage_folders(context) -> list[str]:
    """The folders of the `manage.py` files that sit at or below a folder whose manifest declares `django`, among the pre-map's packages
    (the ecosystem and the name are the readers' own, `requirements` and the module graph; no import is searched). A package declared in
    another file than the restore's marks (`requirements/base.txt`) is not a folder: the restore does not run there."""
    from build_units import normalize_pypi_name  # the module graph keeps a `pyproject.toml` name as written (`Django>=5`), `requirements` normalizes
    from premap import frameworks
    # shortcut: only a `pyproject.toml` or a `requirements.txt` names a folder, and only a `manage.py` (what `django-admin startproject` makes, and
    # the one file whose settings module is Django's own documented entry) starts a load; a project that declares Django without one (a library
    # of apps, a project started from `wsgi.py` alone) has no row and no gap
    declared = sorted({PurePosixPath(p["declared_in"].partition("#")[0]).parent.as_posix()
                       for p in context.stated.get("packages", ())
                       if p.get("ecosystem") == "pypi" and normalize_pypi_name(p.get("name")) == "django"
                       and PurePosixPath(p["declared_in"].partition("#")[0]).name in preparation.PYTHON})
    held = frameworks.nearest_first(declared)
    return sorted({PurePosixPath(rel).parent.as_posix() for rel in context.inventory.files
                   if PurePosixPath(rel).name == "manage.py" and frameworks.folder_of(held, rel) is not None})


def commands(context):
    from container import WORKDIR
    folders = _manage_folders(context)
    if not folders:
        return None
    # the lockfiles are the checkout's: the snapshot keeps none, and a folder's manager is the one its lockfile names
    held = preparation.python_environments(context.inventory.files, lambda rel: (context.root / rel).is_file())
    seconds = str(run_seconds(len(folders)))
    found = []
    for folder in folders:
        env = preparation.python_environment(held, folder) or folder
        python = preparation.python_interpreter(env, held.get(env, "pip"), WORKDIR)
        found.append({"tool": NAME, "argv": ["sh", "-c", f'exec timeout --kill-after=10 "$1" {python} -I "$2"', NAME, seconds,
                                             f"{preparation.T}/{SCRIPT}"],
                      "cwd": folder, "env": {}, "network": "none", "venv": env})
    return found


def _stopped(result: dict, command: dict) -> str:
    """Why the script did not give its answer: the limit that ended it, or what it wrote first; and the environment it ran in, for the Python
    is the nearest folder's above, not always the folder's own."""
    from premap import frameworks
    where = f" (the Python of the environment restored for {command['venv']!r})" if command.get("venv") is not None else ""
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
            and (handler.get("line") is None or isinstance(handler["line"], int) and not _flag(handler["line"]))
            and isinstance(handler.get("owners"), list) and all(isinstance(owner, str) for owner in handler["owners"])):
        return False
    installed = handler.get("distribution")
    return ((installed is None or isinstance(installed, dict) and isinstance(installed.get("name"), str) and isinstance(installed.get("url"), str))
            and (handler.get("file") is None or isinstance(handler.get("qualname"), str)))  # a file is a function or a class, which has a name


def _route(route) -> bool:
    if not (isinstance(route, dict) and isinstance(route.get("path"), str) and _handler(route.get("view"))
            and (route.get("view") is None or route["view"]["kind"] == "class")):
        return False
    parts, arguments, answers = route.get("parts"), route.get("arguments"), route.get("handlers")
    return ((parts is None or isinstance(parts, list) and all(isinstance(part, list) and len(part) == 2 and _flag(part[0])
                                                                and isinstance(part[1], str) for part in parts))
            and isinstance(arguments, dict) and all(isinstance(name, str) and (isolating is None or _flag(isolating))
                                                    for name, isolating in arguments.items())
            and isinstance(answers, list) and bool(answers)
            and all(isinstance(answer, dict) and _text(answer.get("method")) and _handler(answer.get("handler")) for answer in answers))


def _printed(result: dict) -> dict:
    """The document the script printed: the whole standard output, checked as `read` uses it (every value it reads has the type it needs, so
    a malformed answer is a gap of its folder and never an exception in the middle of the others). Raises ValueError for what is not the known
    layout: `called`, a list of `routes`, the `unread` includes and the `locale`."""
    try:
        document = json.loads(result["stdout"])
    except ValueError:
        raise ValueError("the output is no JSON") from None
    unread, locale = (document.get("unread"), document.get("locale")) if isinstance(document, dict) else (None, None)
    if not (isinstance(document, dict) and document.get("called") is True and isinstance(document.get("routes"), list) and "locale" in document
            and isinstance(unread, list) and all(isinstance(item, dict) and isinstance(item.get("route"), str) and isinstance(item.get("error"), str)
                                                 for item in unread)
            and (locale is None or isinstance(locale, dict) and _text(locale.get("active")) and isinstance(locale.get("others"), int))):
        raise ValueError("no `called`, list of `routes`, list of `unread` and `locale`")
    if not all(_route(route) for route in document["routes"]):
        raise ValueError("a route of an unknown layout")
    return document


def _schema(route: dict) -> str | None:
    """The path of a route as `REST` reads it (`flows.path_schema`: `/shop/products/{}/` for `/shop/products/<int:pk>/`, as for Noir's and
    Next.js's rows), made from Django's own parts of the route (`parts` and `arguments` of the script, never the text of `path`): each
    argument whose converter the script says spans one segment is a hole. None where Django gave no parts (a `re_path`, `i18n_patterns`,
    a pattern class of the project), or an argument may hold a `/` (`PathConverter`) or its converter is the project's own: the route stands
    for several path schemas, a gap of the declared routes and never a join. The text of a route that holds `{...}` or starts a segment
    with `:` is read by `path_schema` as a parameter."""
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


def _in_snapshot(context, folder: str, described: dict | None) -> str | None:
    """The file of a function or class, from the root of the project, when the snapshot holds it."""
    if not described or not described.get("file"):
        return None
    file = posixpath.normpath(posixpath.join(folder, described["file"]))
    return file if not file.startswith("..") and file in context.inventory.headers else None


def _owner(described: dict) -> str:
    return ", ".join(described["owners"]) or (described.get("module") or "?").split(".")[0]


def _routes(context, folder: str, document: dict, kind: str) -> tuple[list[dict], list[dict]]:
    """The rows and the gaps of one folder's routes."""
    import flows
    rows, gaps, shared = [], [], {}
    if not document["routes"] and not document["unread"]:
        return rows, [{"kind": "model_partial", "path": folder, "detail": "the URLconf has no route"}]
    for route in document["routes"]:
        base = {"reader": NAME, "shape": "route", "kind": kind, "path": route["path"], "schema": _schema(route)}
        view = route["view"]
        view_file = _in_snapshot(context, folder, view)
        for answer in route["handlers"]:
            method, handler = answer["method"], answer["handler"]
            file = _in_snapshot(context, folder, handler)
            named = {"method": method} if method else {}
            if handler is None or handler["environment"]:  # the class answers with a function of the framework, or with none
                if view_file:  # the project's class is the route's: a row on it, and the gap that nothing of the project answers
                    cause = (f"{view['qualname']} is a class-based view with no HTTP method of its own" if handler is None else
                             f"{view['qualname']} is a class-based view and {method or 'a request'} is answered by {handler['qualname']} of "
                             f"{_owner(handler)}, not by a function of the project")
                    rows.append({**base, **named, "site": f"{view_file}:{view['line']}" if view.get("line") else view_file,
                                 "symbol": f"{view_file}::{flows.MODULE}", "gap": cause})
                elif handler and handler["distribution"]:
                    gaps.append({"kind": "outside_snapshot", "path": folder, "detail": (
                        f"{route['path']}: {handler.get('qualname')} is an installed copy of the project, not the snapshot's file: "
                        f"{handler['distribution']['name']} was installed from {handler['distribution']['url']} ({handler['file']})")})
                elif handler:
                    shared.setdefault(_owner(handler), {})[route["path"]] = None
                else:
                    gaps.append({"kind": "outside_snapshot", "path": folder, "detail": f"{route['path']}: no function answers it"})
                continue
            if file is None:
                cause = f"{handler.get('qualname') or handler['type']} has no source file of the project the snapshot holds ({handler.get('file') or 'none'})"
                gaps.append({"kind": "outside_snapshot", "path": folder, "detail": f"{route['path']}: {cause}"})
                continue
            module = {**base, **named, "site": file, "symbol": f"{file}::{flows.MODULE}"}
            if handler["kind"] == "class":  # a view the script could not take apart into methods
                rows.append({**module, "gap": f"{handler['qualname']} is a class-based view: which of its methods answers {method or 'a request'} is not read"})
            else:  # a name at a position: the links' binder ties it to the one function of that name that holds the line
                line = handler.get("line")
                rows.append({**module, "site": f"{file}:{line}" if line else file, "handler": handler["qualname"].rsplit(".", 1)[-1]})
    if shared:
        count = sum(len(paths) for paths in shared.values())
        named = "; ".join(f"{owner} ({len(paths)}: {', '.join(list(paths)[:LISTED])}{f' and {len(paths) - LISTED} more' if len(paths) > LISTED else ''})"
                          for owner, paths in sorted(shared.items()))
        gaps.append({"kind": "model_partial", "path": folder, "detail": (
            f"{count} route{'s' if count != 1 else ''} of the URLconf {'are views' if count != 1 else 'is a view'} of packages of the restored "
            f"environment, not of the project: {named}")})
    for item in document["unread"]:
        gaps.append({"kind": "model_partial", "path": folder, "detail": f"the URLconf included at {item['route']} did not load, its routes are not read: {item['error']}"})
    if document["locale"]:
        gaps.append({"kind": "model_partial", "path": folder, "detail": (
            f"the routes under i18n_patterns are listed with the prefix of the language `{document['locale']['active']}` the project loaded in, "
            f"without a path schema: the {document['locale']['others']} other languages of LANGUAGES have routes of their own that are not listed")})
    if not rows and not gaps:
        gaps.append({"kind": "model_partial", "path": folder, "detail": "the URLconf has no route of the project"})
    return rows, gaps


def read(context, commands, results):
    import entries
    from premap import frameworks
    kind = entries.QUERIES[NAME]["route"]["kind"]
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
        found, notes = _routes(context, folder, document, kind)
        rows += found
        gaps += notes
    return {"facts": {"framework_entries": rows} if rows else {}, "gaps": gaps}


def from_record(report):
    """The rows this source persisted in a pre-map and its gaps there; a pre-map made without the source, or where it was not needed, has
    none."""
    source = f"{NAME}@{VERSION}"
    return ([row for row in report.get("framework_entries", ()) if source in row["sources"]],
            [gap for gap in report["gaps"] if gap.get("source") == source])
