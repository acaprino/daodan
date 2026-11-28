"""Daodan's script, run in the container by the project's own Python (`premap/fastapi_app.py`): it loads the FastAPI application the way
the `fastapi` command does and prints its routes.

    python -I fastapi_routes.py        (cwd: the folder of the project)

The application is found by `fastapi-cli`, not by this script: the three functions its `fastapi dev` and `fastapi run` call, in the
order its own code gives (`fastapi_cli.cli._run`: a path or `--app` argument, then `[tool.fastapi] entrypoint` of the `pyproject.toml`
in the current folder, then auto-discovery). Daodan gives no argument, so: `FastAPIConfig.resolve()` reads the entrypoint; with one,
`get_import_data_from_import_string` splits it (and imports nothing); without one, `get_import_data()` tries `main.py`, `app.py`, `api.py`,
`app/main.py`, `app/app.py`, `app/api.py` (what `fastapi dev --help` lists), imports the module and takes the FastAPI object named `app` or
`api`, or else the first one `dir()` gives. The object is then loaded as `uvicorn` loads `module:attr` (`uvicorn.importer.import_from_string`),
which is what `fastapi run` hands the server. The functions are `fastapi_cli`'s own and public by name, and not documented as an API; what
is documented is the behaviour (https://fastapi.tiangolo.com/fastapi-cli/: `entrypoint`, the default file and object). `fastapi-cli`
comes with `fastapi[standard]`: without it the import fails and the folder's gap says so.

The routes are what FastAPI 0.137.2 and later give for it: `fastapi.routing.iter_route_contexts(app.routes)`, which flattens the routers
`include_router` keeps (since 0.137.0 `app.routes` holds `_IncludedRouter` objects, and the release notes say `router.routes` is an
implementation detail); a `RouteContext` has `path`, `path_format`, `name`, `methods`, `endpoint` and `original_route`, and forwards any
other attribute (`param_convertors`, `routes`, `app`) to the route it stands for. An earlier FastAPI has no such function: its `app.routes`
is flat, the same attributes are on the routes themselves, and the one loop reads both. A mount is entered by `routes` and its prefix is
`starlette.routing.compile_path(mount.path)`; a FastAPI sub-app's documentation routes are told by that sub-app's own `docs_url`.
Anything that is no `Route`, `WebSocketRoute`, `Mount` or `Host` of Starlette (a `_IncludedRouter` of FastAPI 0.137.0 and 0.137.1, a frontend
route) and a mount whose application has no routes (`StaticFiles`, an ASGI function) is `unread`, named by its type.

Per route: the path as FastAPI writes it, the methods it declares (Starlette's `Route` adds `HEAD` beside `GET`: dropped there; FastAPI's
`APIRoute` adds none), whether it is one of the four routes FastAPI registers for itself (`openapi_url`, `docs_url`, `redoc_url` and
`swagger_ui_oauth2_redirect_url`, compared with the owning application's attributes), the parts of its path and, for each parameter, the
exact convertor class says whether it holds one segment (`str`, `int`, `float`, `uuid` of Starlette: true; `path`: false; any other:
null, which is that the convertor does not say: Starlette has no `part_isolating`), and the handler: the function after `inspect.unwrap`
(`python_script.function_of`), or the class of a class-based endpoint.

Evaluated and not used: `app.openapi()` (path, method and `operationId`, never a function, and it fails for a model it cannot make a schema
of while the routes are there: `benchmarks/fastapi-routes/README.md`); `fastapi.routing.APIRoute.unique_id` (the operation's name); the
private `_iter_routes_with_context`; `app.routes` (a list that holds private objects since 0.137.0).

The answer is one JSON document, the only thing on the standard output (`python_script.run`); a failure writes `Type: message` to the
standard error and exits with 3.
"""
import importlib.util
import os
import sys

PREFERRED = ("app", "api")  # the names the CLI looks for first (`fastapi dev --help`)
DOCUMENTATION = ("openapi_url", "docs_url", "redoc_url", "swagger_ui_oauth2_redirect_url")  # FastAPI's own, as its constructor names them


def shared():
    """`python_script.py`, which is beside this file: loaded by its path, because the isolated interpreter has no folder of ours on `sys.path`."""
    spec = importlib.util.spec_from_file_location("daodan_python_script", os.path.join(os.path.dirname(os.path.abspath(__file__)), "python_script.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tokens(path_format, names):
    """The path as `[dynamic, text]` pairs. Starlette's `compile_path` writes each parameter as `{name}` in `path_format` (and
    `url_path_for` replaces exactly that), so the parameters are the `{name}` of the names the framework gave. Hand-written, because no
    function of Starlette gives the parts: `compile_path` returns the regex, the format and the convertors; `replace_params` (what
    `url_path_for` calls) needs a value for each parameter and runs the convertor's `to_string` on it, which for a convertor of the project's
    is project code run with an invented value."""
    marks = {"{" + name + "}": name for name in names}
    out, text, at = [], "", 0
    while at < len(path_format):
        mark = next((m for m in marks if path_format.startswith(m, at)), None)
        if mark is None:
            text += path_format[at]
            at += 1
            continue
        if text:
            out.append([False, text])
            text = ""
        out.append([True, marks[mark]])
        at += len(mark)
    return out + ([[False, text]] if text else [])


def isolating(convertor):
    """Whether Starlette's convertor holds one path segment: true for its own `str`, `int`, `float` and `uuid` (exact classes: the
    ones `starlette.convertors` ships), false for `path`, null for any other, which says nothing (a subclass may change the regex)."""
    from starlette import convertors
    if type(convertor) in (convertors.StringConvertor, convertors.IntegerConvertor, convertors.FloatConvertor, convertors.UUIDConvertor):
        return True
    return False if type(convertor) is convertors.PathConvertor else None


def written(path_format, param_convertors):
    """`(parts, arguments)` of a path Starlette compiled."""
    return tokens(path_format, param_convertors), {name: isolating(found) for name, found in param_convertors.items()}


def merged(first, second):
    """The arguments of a prefix and of the path under it: a name in both counts as one segment only if both say so."""
    return {name: (first[name] if name not in second else second[name] if name not in first else
                   True if first[name] is True and second[name] is True else None)
            for name in {*first, *second}}


def view(lib, endpoint, cwd):
    """The handler of a route: the function after `functools.wraps`, or the class of a class-based endpoint, None for no endpoint."""
    import inspect
    if endpoint is None:
        return None
    if inspect.isclass(endpoint):
        return lib.describe(endpoint, "class", cwd)
    return lib.describe(lib.function_of(endpoint), "function", cwd)


def declared(route, api, item):
    """The methods a route declares: Starlette's `Route` adds `HEAD` beside `GET` and FastAPI's `APIRoute` does not."""
    methods = set(item.methods or ())
    if not isinstance(route, api) and "GET" in methods:
        methods.discard("HEAD")
    return sorted(methods)


def walk(lib, routes, owner, prefix, cwd, out, unread):
    """Add the routes under `routes` (a list of routes or a list of what `iter_route_contexts` yields) to `out`, with `prefix` =
    `(path, parts, arguments)` of the mounts above; `owner` is the application they belong to, whose own documentation routes they may be."""
    from fastapi import routing as fastapi_routing
    from fastapi.routing import APIRoute
    from starlette import routing
    flatten = getattr(fastapi_routing, "iter_route_contexts", None)  # FastAPI 0.137.2 and later; before it `app.routes` is flat
    own = {getattr(owner, name, None) for name in DOCUMENTATION} - {None}
    for item in (flatten(routes) if flatten else routes):
        route = getattr(item, "original_route", item)  # a `RouteContext` has the route it stands for; a route is itself
        path = getattr(item, "path", None)
        if isinstance(route, routing.Mount):
            inner = item.routes
            if not inner and not hasattr(item.app, "routes"):
                unread.append({"path": path, "type": f"{type(item.app).__module__}.{type(item.app).__qualname__}"})
                continue
            before, convertors = routing.compile_path(path)[1:]
            parts, arguments = written(before, convertors)
            walk(lib, inner, item.app, (prefix[0] + path, prefix[1] + parts, merged(prefix[2], arguments)), cwd, out, unread)
        elif isinstance(route, routing.Host):  # the host is not in the row: nothing in the links reads one
            walk(lib, item.routes, item.app, prefix, cwd, out, unread)
        elif isinstance(route, (routing.Route, routing.WebSocketRoute)):
            http = isinstance(route, routing.Route)
            parts, arguments = written(item.path_format, item.param_convertors)
            out.append({"kind": "http" if http else "websocket", "path": prefix[0] + path,
                        "methods": declared(route, APIRoute, item) if http else [], "docs": path in own and not isinstance(route, APIRoute),
                        "parts": prefix[1] + parts, "arguments": merged(prefix[2], arguments),
                        "handler": view(lib, getattr(item, "endpoint", None), cwd)})
        else:
            unread.append({"path": path, "type": f"{type(route).__module__}.{type(route).__qualname__}"})


def load():
    """`(import data, application)` as the CLI loads them: see the module's docstring."""
    from fastapi_cli.config import FastAPIConfig
    from fastapi_cli.discover import get_import_data, get_import_data_from_import_string
    from uvicorn.importer import import_from_string
    config = FastAPIConfig.resolve()
    data = get_import_data_from_import_string(config.entrypoint, config.from_pyproject) if config.entrypoint else get_import_data()
    return data, import_from_string(data.import_string)


def competing(data):
    """What else the module holds that the loader may have taken for the application, when it took the first FastAPI object it found:
    `others`, the other FastAPI objects, and `shadowed`, a preferred name that holds something else (a wrapper around the application,
    served under the name a server looks for). Nothing where the entrypoint, or the preferred name, said which."""
    from fastapi import FastAPI
    names = {"others": [], "shadowed": []}
    if getattr(data, "app_name_config_source", "auto-discovery") != "auto-discovery" or data.app_name in PREFERRED:
        return names
    namespace = vars(sys.modules[data.module_data.module_import_str])
    names["others"] = sorted(name for name, value in namespace.items() if isinstance(value, FastAPI) and name != data.app_name)
    names["shadowed"] = [name for name in PREFERRED if name in namespace and not isinstance(namespace[name], FastAPI)]
    return names


def build(cwd):
    lib = shared()
    data, app = load()
    if not hasattr(app, "routes"):
        raise TypeError(f"{data.import_string} is a {type(app).__module__}.{type(app).__qualname__}, which has no routes")
    out, unread = [], []
    walk(lib, app.routes, app, ("", [], {}), cwd, out, unread)
    return {"called": True, "application": data.import_string, "found": data.module_config_source,
            "root_path": str(getattr(app, "root_path", "") or ""), "competing": competing(data), "routes": out, "unread": unread}


if __name__ == "__main__":
    shared().run(build)
