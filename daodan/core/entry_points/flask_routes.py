"""Daodan's script, run in the container by the project's own Python (`premap/flask_app.py`): it loads the Flask application with
Flask's own loader and prints its routes.

    python -I flask_routes.py        (cwd: the folder of the project)

The application is found by Flask, not by this script: `ScriptInfo.load_app()` (documented, `flask.cli`) reads `wsgi.py`, then `app.py`,
then, in the module, `app`, `application`, the one Flask instance or the factory `create_app` / `make_app`; `FLASK_APP` (the
documented variable of `--app`) and the `.flaskenv` / `.env` files (`flask.cli.load_dotenv`, the loader of the `flask` command) are
honoured the way the command honours them. The routes are `app.url_map.iter_rules()` and, by endpoint, `app.view_functions`: the
rule as the framework writes it (`/users/<int:id>`), the methods it declares (`declared`), the flags `build_only` and `redirect_to`
(a rule werkzeug never matches, and one that redirects), whether it is a rule Flask registers for a static folder (the application's, or
a blueprint's), the parts
of its path and the `part_isolating` of the converter of each argument as werkzeug parsed them (`parameters`), and the handler: the
function after `inspect.unwrap` (what `functools.wraps` ties to the wrapper), a bound method as its function, or the class of a
class-based view (`view_class`). The file of the handler is the interpreter's (`inspect.getsourcefile`), relative to the folder the
script runs in, its line the line of its `def` (`definition_line`), whether the file is in the packages the interpreter installs and,
when it is, the distribution that holds it where PEP 610's `direct_url.json` says it was installed from a local directory.

Evaluated and not used: `flask routes` (an official command, but a text table of endpoint, methods and rule: no function, no file,
and no JSON; reading its columns would be a reader of a printed format); `flask.cli.find_best_app` (a step of `load_app`); for the
parts of a rule, werkzeug's public `Rule.arguments` (names only), `Rule.build` (needs a value for each argument and runs the
converters' `to_url`, project code for a custom one) and `Rule.get_converter` (makes a converter from names, does not say which one
an argument has): the structures `Rule._trace` and `Rule._converters` are what werkzeug's own parse of the rule left, and the text of
the rule is never read here (werkzeug 3.1.9, `benchmarks/flask-routes/README.md`).
Measured on Modal, in the runner's image with the network blocked: `benchmarks/flask-routes/README.md`.

The answer is one JSON document, `{"called": true, "dispatch": null, "routes": [...]}`, and the only thing on the standard output:
before the project's code runs, the script saves descriptor 1 (at a number from `SAVED` up) and points it at the standard error, so
whatever the project prints (or its child processes, or a replaced `sys.stdout`) goes there; the document is written to the saved
descriptor and the script leaves with `os._exit`, so a thread that does not end or an `atexit` function of the project cannot hold it or
write after it. A failure writes `Type: message` to the standard error and exits with 3 (Flask's own words for an application it cannot
find, or the project's own error while its module loads); a document that cannot be written (the pipe broke, or the project closed or
replaced the saved descriptor, which is checked) exits with 4, in the same way. `dispatch` says what a `DispatcherMiddleware` around the
loaded application changes of its paths (`dispatch`): the paths the rules are served at are `prefix + rule` where it is mounted.
"""
import ast
import functools
import importlib.metadata
import inspect
import json
import os
import sys
import sysconfig
import tokenize

# where the interpreter installs packages (`sysconfig`, documented): a view whose file is there is the framework's or a library's
PACKAGES = tuple({os.path.realpath(sysconfig.get_paths()[key]) for key in ("purelib", "platlib")})
SAVED = 100  # the lowest descriptor number the answer's copy of descriptor 1 may take
LISTED = 8  # how many rules of a mounted application the answer names


def parameters(rule):
    """`(parts, arguments)` of a werkzeug rule, from the structures werkzeug itself parses the rule into (`Rule._trace` and
    `Rule._converters`: no public attribute gives the converter of each argument, and `Rule.arguments` holds only the names), None
    for what this werkzeug does not have. `parts` is the path as `[dynamic, text]` pairs (`[false, "/"]`, `[true, "user_id"]`, from the
    `|` that ends the host part); `arguments` maps each argument to the `part_isolating` of its converter, the attribute werkzeug
    documents on `BaseConverter` and its matcher reads: False for an argument that may hold a `/`."""
    trace, converters = getattr(rule, "_trace", None), getattr(rule, "_converters", None)
    marker = next((i for i, (dynamic, text) in enumerate(trace or ()) if not dynamic and text == "|"), None)
    parts = None if marker is None else [[dynamic, text] for dynamic, text in trace[marker + 1:]]
    arguments = None if converters is None else {name: getattr(found, "part_isolating", None) for name, found in converters.items()}
    return parts, arguments


def declared(rule):
    """The methods a rule declares: its `methods` less the ones the framework adds. Werkzeug adds `HEAD` beside `GET` (`Rule.__init__`),
    Flask adds `OPTIONS` and says so on the rule (`provide_automatic_options`, set by `add_url_rule`); `methods=["OPTIONS"]` or
    `["HEAD"]` alone is declared and stays."""
    methods = set(rule.methods or ())
    if getattr(rule, "provide_automatic_options", False):
        methods.discard("OPTIONS")
    if "GET" in methods:
        methods.discard("HEAD")
    return sorted(methods)


@functools.lru_cache(maxsize=None)
def definitions(file):
    """`{first line: line of the def}` of each function in the module `file`, from the interpreter's own parse of the whole module: a
    function's `co_firstlineno` is the line of its first decorator, or its `def`'s. Parsing the module and not the function's own lines
    keeps a method, a nested function or one with a line at column 0 (a multi-line string) from failing to parse."""
    try:
        with tokenize.open(file) as source:
            tree = ast.parse(source.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return {}
    return {min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)]): node.lineno for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def definition_line(target, file):
    """The line of the `def` of a function in `file`; for what is not a `def` (a lambda) the line its code starts on; None where the
    object has no code."""
    first = getattr(getattr(target, "__code__", None), "co_firstlineno", None)
    return definitions(file).get(first, first)


@functools.lru_cache(maxsize=None)
def packages_distributions():
    return importlib.metadata.packages_distributions() if hasattr(importlib.metadata, "packages_distributions") else {}  # Python 3.10 and later


def installed_from(module):
    """`{name, url}` of the distribution of a top-level module when PEP 610's `direct_url.json` (`importlib.metadata`) says it was
    installed from a local directory: the project's own code, copied into the environment; None otherwise."""
    for name in packages_distributions().get((module or "").split(".")[0], ()):
        try:
            data = json.loads(importlib.metadata.distribution(name).read_text("direct_url.json") or "null")
        except (ValueError, importlib.metadata.PackageNotFoundError):
            continue
        if isinstance(data, dict) and str(data.get("url", "")).startswith("file://") and "dir_info" in data:
            return {"name": name, "url": data["url"]}
    return None


def handler(view, cwd):
    """`{kind, type, module, qualname, file, line, environment, distribution}` of what a view function stands for; `type` is the class
    of the object (a `functools.partial` and an object with `__call__` have no `qualname` and no `file`: it is what a gap can say they
    are), `file` is None where the interpreter gives none, `environment` whether it is in the packages the interpreter installs,
    `distribution` the local directory it was installed from."""
    if view is None:
        return None
    target = getattr(view, "view_class", None)
    kind = "class" if target is not None else "function"
    if target is None:
        try:
            target = inspect.unwrap(view)
        except ValueError:  # a cycle of `__wrapped__`
            target = view
        target = getattr(target, "__func__", target)  # a bound method is its function
    try:
        file = inspect.getsourcefile(target)
    except TypeError:  # a built-in or a callable object: no source file
        file = None
    real = os.path.realpath(file) if file else None
    environment = bool(real) and any(real.startswith(packages + os.sep) for packages in PACKAGES)
    module = getattr(target, "__module__", None)
    return {"kind": kind, "type": f"{type(target).__module__}.{type(target).__qualname__}",
            "module": module, "qualname": getattr(target, "__qualname__", None),
            "file": os.path.relpath(file, cwd).replace(os.sep, "/") if file else None,
            "line": definition_line(target, file) if file and kind == "function" else None,
            "environment": environment, "distribution": installed_from(module) if environment else None}


def flask_of(wsgi, flask):
    """The Flask application a WSGI callable is, or the one whose bound `wsgi_app` it is; None for any other callable."""
    owner = wsgi if isinstance(wsgi, flask.Flask) else getattr(wsgi, "__self__", None)
    return owner if isinstance(owner, flask.Flask) else None


def served(dispatcher, dispatcher_class, prefix="", seen=None):
    """`[(prefix, wsgi)]` of every WSGI application a `DispatcherMiddleware` serves: its main `app` at `prefix` and each of its `mounts` at
    the prefix it is mounted at, the dispatchers among them opened in turn. `DispatcherMiddleware.__call__` gives an application that is
    mounted at `/sub` the path after `/sub` (it moves the prefix to `SCRIPT_NAME`), so a rule `/hello` of it is served at `/sub/hello`."""
    seen = set() if seen is None else seen
    if id(dispatcher) in seen:
        return []
    seen.add(id(dispatcher))
    found = []
    for at, wsgi in [(prefix, dispatcher.app), *((prefix + mount, wsgi) for mount, wsgi in sorted(dispatcher.mounts.items()))]:
        found += served(wsgi, dispatcher_class, at, seen) if isinstance(wsgi, dispatcher_class) else [(at, wsgi)]
    return found


def dispatch(app, flask):
    """None, or what a `DispatcherMiddleware` (`werkzeug.middleware.dispatcher`, public and documented, with its `app` and its `mounts`)
    changes of the paths the loaded application is served at: `{loaded, prefixes, mounts}`. `loaded` is `main` when the loaded application
    is the main application of every dispatcher that holds it (its rules are served as they are), `mounted` when a dispatcher mounts it at
    a prefix (`prefixes`: its rules lack it), `other` when no dispatcher holds it; `mounts` the other Flask applications the dispatchers
    serve, each with its prefix and its rules as served (`prefix + rule`). None when nothing is to be said. A dispatcher is found by its
    class, on `app.wsgi_app` (Flask's documented way to wrap an application) and among the globals of the module that holds the loaded
    application (`Flask.import_name` names it, and the module that holds it as a global): never by the name it has. A wrapping that is not
    a `DispatcherMiddleware` is not seen."""
    try:
        from werkzeug.middleware.dispatcher import DispatcherMiddleware
    except ImportError:
        return None
    found = []

    def see(value):
        if isinstance(value, DispatcherMiddleware) and all(value is not other for other in found):
            found.append(value)
    see(getattr(app, "wsgi_app", None))
    named = sys.modules.get(app.import_name)
    for module in list(sys.modules.values()):
        namespace = getattr(module, "__dict__", None)
        if isinstance(namespace, dict) and (module is named or any(value is app for value in list(namespace.values()))):
            for value in list(namespace.values()):
                see(value)
    seen = set()
    entries = [entry for dispatcher in found for entry in served(dispatcher, DispatcherMiddleware, "", seen)]
    mine = [prefix for prefix, wsgi in entries if flask_of(wsgi, flask) is app]
    prefixes = sorted({prefix for prefix in mine if prefix})
    loaded = "mounted" if prefixes else "main" if mine else "other"
    mounts, taken = [], set()
    for prefix, wsgi in entries:
        other = flask_of(wsgi, flask)
        if other is not None and other is not app and (prefix, id(other)) not in taken:
            taken.add((prefix, id(other)))
            rules = [prefix + rule.rule for rule in other.url_map.iter_rules()]
            mounts.append({"prefix": prefix, "count": len(rules), "rules": rules[:LISTED]})
    return None if loaded != "mounted" and not mounts else {"loaded": loaded, "prefixes": prefixes, "mounts": mounts}


def static_rule(app, rule):
    """Whether the rule is one Flask registers for a static folder: the application's (the endpoint `static`, which `Flask.__init__` gives
    it while `has_static_folder`, and the Quickstart documents) or a blueprint's (`Blueprint.register` gives its `send_static_file` as the view
    while the blueprint's `has_static_folder`: `app.blueprints` lists them)."""
    if app.has_static_folder and rule.endpoint == "static":
        return True
    view = app.view_functions.get(rule.endpoint)
    return view is not None and any(blueprint.has_static_folder and view == blueprint.send_static_file for blueprint in app.blueprints.values())


def leave(code, text=None):
    """Write `text` to the standard error, as bytes (the project may have replaced `sys.stderr`), and leave at once."""
    if text:
        os.write(2, text.encode("utf-8", "replace"))
    os._exit(code)


def saved_descriptor():
    """A copy of descriptor 1, at a number from `SAVED` up and close-on-exec: the project's own files take the low numbers, so they do not
    reuse it by chance. A project that closes or replaces it on purpose is a gap (`main` checks it before it writes)."""
    import fcntl  # the container's Linux: not at the top, so that the module can be read where it is not
    try:
        return fcntl.fcntl(1, fcntl.F_DUPFD_CLOEXEC, SAVED)
    except OSError:  # the limit on open descriptors is below `SAVED`
        return os.dup(1)


def main():
    cwd = os.getcwd()
    answer = saved_descriptor()  # the descriptor the answer goes to: kept before the project's code can reach it
    kept = os.fstat(answer)
    os.dup2(2, 1)  # whatever the project prints, and its children, goes to the standard error
    try:
        import flask
        from flask.cli import ScriptInfo, load_dotenv
        load_dotenv()
        app = ScriptInfo(app_import_path=os.environ.get("FLASK_APP")).load_app()
        routes = [{"rule": rule.rule, "methods": declared(rule), "build_only": bool(rule.build_only),
                   "redirect_to": rule.redirect_to is not None, "static": static_rule(app, rule),
                   "parts": parts, "arguments": arguments, "handler": handler(app.view_functions.get(rule.endpoint), cwd)}
                  for rule in app.url_map.iter_rules() for parts, arguments in [parameters(rule)]]
        document = json.dumps({"called": True, "dispatch": dispatch(app, flask), "routes": routes})
    except BaseException as error:  # the project's own code runs while its module loads: whatever it raises is the cause
        leave(3, f"{type(error).__name__}: {error}\n")
    try:
        now = os.fstat(answer)
        if (now.st_dev, now.st_ino) != (kept.st_dev, kept.st_ino):
            raise OSError(f"descriptor {answer} is not the one saved: the project closed or replaced it")
        with os.fdopen(answer, "w", encoding="utf-8") as out:
            out.write(document)
    except BaseException as error:  # the pipe broke, or the project closed the descriptor: still no interpreter exit, no `atexit`, no thread
        leave(4, f"could not write the answer: {type(error).__name__}: {error}\n")
    leave(0)


if __name__ == "__main__":
    main()
