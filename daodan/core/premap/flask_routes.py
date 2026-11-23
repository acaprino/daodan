"""Daodan's script, run in the container by the project's own Python (`premap/flask_app.py`): it loads the Flask application with
Flask's own loader and prints its routes.

    python -I flask_routes.py        (cwd: the folder of the project)

The application is found by Flask, not by this script: `ScriptInfo.load_app()` (documented, `flask.cli`) reads `wsgi.py`, then `app.py`,
then, in the module, `app`, `application`, the one Flask instance or the factory `create_app` / `make_app`; `FLASK_APP` (the
documented variable of `--app`) and the `.flaskenv` / `.env` files (`flask.cli.load_dotenv`, the loader of the `flask` command) are
honoured the way the command honours them. The routes are `app.url_map.iter_rules()` and, by endpoint, `app.view_functions`: the
rule as the framework writes it (`/users/<int:id>`), its methods without the `HEAD` and `OPTIONS` that `flask routes` hides by
default (`routes_command`, `ignored_methods`), the subdomain or host, and the handler: the function after `inspect.unwrap` (what
`functools.wraps` ties to the wrapper), a bound method as its function, or the class of a class-based view (`view_class`). The
file of the handler is the interpreter's (`inspect.getsourcefile`), relative to the folder the script runs in; the line is not
printed: the snapshot's own record of the function has it (a decorated function's `co_firstlineno` is the line of its first
decorator, not of the `def`).

Evaluated and not used: `flask routes` (an official command, but a text table of endpoint, methods and rule: no function, no file,
and no JSON; reading its columns would be a reader of a printed format); `flask.cli.find_best_app` (a step of `load_app`). Not
measured: this script has not run yet (`benchmarks/flask-routes/README.md`).

The last line of the standard output is the JSON `{"called": true, "routes": [...]}`; a project that prints before it is read
from the last line. A failure writes `Type: message` to the standard error and exits with 3 (Flask's own words for an application
it cannot find, or the project's own error while its module loads).
"""
import inspect
import json
import os
import sys

HIDDEN = {"HEAD", "OPTIONS"}  # `flask routes` shows them only with `--all-methods`


def handler(view, cwd):
    """`{kind, module, qualname, file}` of what a view function stands for; `file` is None where the interpreter gives none."""
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
    return {"kind": kind, "module": getattr(target, "__module__", None), "qualname": getattr(target, "__qualname__", None),
            "file": os.path.relpath(file, cwd).replace(os.sep, "/") if file else None}


def main() -> int:
    cwd = os.getcwd()
    try:
        from flask.cli import ScriptInfo, load_dotenv
        load_dotenv()
        app = ScriptInfo(app_import_path=os.environ.get("FLASK_APP")).load_app()
        rows = [{"rule": rule.rule, "methods": sorted((rule.methods or set()) - HIDDEN), "endpoint": rule.endpoint,
                 "host": (rule.host if app.url_map.host_matching else rule.subdomain) or None,
                 "handler": handler(app.view_functions.get(rule.endpoint), cwd)}
                for rule in app.url_map.iter_rules()]
    except BaseException as error:  # the project's own code runs while its module loads: whatever it raises is the cause
        sys.stderr.write(f"{type(error).__name__}: {error}\n")
        return 3
    print(json.dumps({"called": True, "routes": rows}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
