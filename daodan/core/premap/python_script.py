"""What Daodan's container scripts for Python frameworks share (`fastapi_routes.py`; the Flask and Django ones can take it too): the
descriptor dance that keeps the answer one JSON document, the line of a `def`, the description of a view and the check of where it
lives. Standard library only: a script of this folder loads it by its path (`importlib.util`) and never puts its folder on `sys.path`,
where a project's own import could meet it.

The scripts run by the Python of the project's restored environment, under `python -I` (isolated: neither the script's folder nor the
current directory is on `sys.path`), so nothing here may be imported by name.

`run(build)` is the whole of a script's `main`: before the project's code runs it saves descriptor 1 and points it at the standard
error, so whatever the project prints (or its child processes, or a replaced `sys.stdout`) goes there; `build(cwd)`'s document is
written to the saved descriptor and the script leaves with `os._exit`, so a thread that does not end or an `atexit` function of the
project cannot hold it or write after it. A failure writes `Type: message` to the standard error and exits with 3.
"""
import ast
import functools
import importlib.metadata
import inspect
import json
import os
import sysconfig
import tokenize

# where the interpreter installs packages (`sysconfig`, documented): a view whose file is there is the framework's or a library's
PACKAGES = tuple({os.path.realpath(sysconfig.get_paths()[key]) for key in ("purelib", "platlib")})


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


def function_of(view):
    """The function a view stands for: after `inspect.unwrap` (what `functools.wraps` ties to the wrapper), a bound method as its
    function."""
    try:
        target = inspect.unwrap(view)
    except ValueError:  # a cycle of `__wrapped__`
        target = view
    return getattr(target, "__func__", target)


def describe(target, kind, cwd):
    """`{kind, type, module, qualname, file, line, environment, distribution}` of what a view stands for: `kind` is `function` or
    `class` (a class-based view), `type` the class of the object (a `functools.partial` and an object with `__call__` have no `qualname`
    and no `file`: it is what a gap can say they are), `file` is None where the interpreter gives none (relative to `cwd`),
    `environment` whether it is in the packages the interpreter installs, `distribution` the local directory it was installed from."""
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


def leave(code, text=None):
    """Write `text` to the standard error, as bytes (the project may have replaced `sys.stderr`), and leave at once."""
    if text:
        os.write(2, text.encode("utf-8", "replace"))
    os._exit(code)


def run(build):
    """The script's `main`: see the module's docstring. `build(cwd)` loads the project and returns the document, a dict."""
    cwd = os.getcwd()
    answer = os.dup(1)  # the descriptor the answer goes to: kept before the project's code can reach it
    os.dup2(2, 1)  # whatever the project prints, and its children, goes to the standard error
    try:
        document = json.dumps(build(cwd))
    except BaseException as error:  # the project's own code runs while its module loads: whatever it raises is the cause
        leave(3, f"{type(error).__name__}: {error}\n")
    with os.fdopen(answer, "w", encoding="utf-8") as out:
        out.write(document)
    leave(0)
