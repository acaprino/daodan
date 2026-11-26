"""Daodan's script, run in the container by the project's own Python (`premap/django_app.py`): it loads a Django project the way its own
`manage.py` does and prints the routes of its loaded URLconf.

    python -I django_routes.py        (cwd: the folder of manage.py)

The settings module is the one the project's own `manage.py` sets, and the script does not read `manage.py`: it runs it (`runpy`, as
`__main__`, after putting its folder first on `sys.path` as `python manage.py` does) with the arguments `shell -c "<call back into this
script>"`, Django's documented command `django-admin shell --command`. Whatever `manage.py` does to find its settings (`os.environ.setdefault`,
a launcher of its own such as django-configurations', a path added to `sys.path`) runs as the project wrote it, and Django's own
`ManagementUtility` calls `django.setup()` and the command; the call back is `deliver`, which reads `django.urls.get_resolver()`. Measured
on Modal (Django 6.1.3, 5.2.19 and 4.2.30, `benchmarks/django-routes/README.md`): the same document in the three, for a `manage.py` that calls
`execute_from_command_line` and for one that calls `ManagementUtility` itself.

The routes are the leaves of `get_resolver().url_patterns`, found by recursion through every `URLResolver` (`include()`, `admin.site.urls`,
`i18n_patterns`, a router's `urls`): each `URLPattern` with the text of its path (`str(pattern)` of each level), the converter of each
argument it declares (`RoutePattern.converters`, the converters of the levels above it too: `<str:tenant>/dash/`) and the view
(`callback`). The parts of the path come from Django's own `django.utils.regex_helper.normalize`, the function `reverse()` uses to turn the
compiled regular expression of a route (the ones of `_populate` composed) into a format with a hole for each argument, and are given only
for a route whose every level is a `RoutePattern` (`path()`), where normalize gives one form. The view is what Django's own `lookup_str` takes it
for (`functools.partial.func`, the class `view_class`), then `inspect.unwrap` (what `functools.wraps` ties to a wrapper), a bound method as its
function. A class-based view is read as Django's own `dispatch` reads it (`http_method_names`, each name the class has as an attribute; the rule
`View.view_is_async` applies), and a Django REST framework viewset as its own `as_view` maps it (`actions`, the HTTP method to the name of the
method of `cls`): each HTTP method with the function that answers it. `options` is dropped where the class has Django's own (every `View` has
one), `head` where it is the function of `get` (`View.setup` makes it so). A function view declares no method (`require_http_methods` keeps
its list in a closure): the route has one handler with no method.

The file of a function is the interpreter's (`inspect.getsourcefile`), relative to the folder the script runs in, its line the line of its `def`
(`definition_line`), whether the file is in the packages the interpreter installs and, when it is, the distribution that holds it (`owners`,
`importlib.metadata.packages_distributions`) and, where PEP 610's `direct_url.json` says it was installed from a local directory, that one.

Evaluated and not used: no command of `django-admin` lists the URLs (`show_urls` is django-extensions', third-party); `django.contrib.admindocs.
views.extract_views_from_urlpatterns` (Django's own recursion, which gives the callback, the text `str(pattern)` joined and the namespaces, and
none of the converters); `URLResolver.reverse_dict` (the same forms, keyed by callback and by name, not by route); running `manage.py` with
`execute_from_command_line` replaced by this script's own function (it never gets the call from a `manage.py` that uses `ManagementUtility`
itself: measured).

The answer is one JSON document, `{"called": true, "routes": [...], "unread": [...], "locale": null}`, and the only thing on the standard
output: before the project's code runs, the script saves descriptor 1 and points it at the standard error, so whatever the project prints (or its
child processes, or a replaced `sys.stdout`) goes there; the document is written to the saved descriptor and the script leaves with `os._exit`, so
a thread that does not end or an `atexit` function of the project cannot hold it or write after it. A failure writes `Type: message` to the
standard error and exits with 3 (the project's own error while its settings, its apps or its URLconf load), 4 when `manage.py` ran and the
command was never given, 5 when `manage.py` ended with `SystemExit` before it.
"""
import ast
import functools
import importlib.metadata
import inspect
import json
import os
import runpy
import sys
import sysconfig
import tokenize

# ---- begin: what `flask_routes.py` and this script share (one module for the two scripts, the day they are merged) ----

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


def leave(code, text=None):
    """Write `text` to the standard error, as bytes (the project may have replaced `sys.stderr`), and leave at once."""
    if text:
        os.write(2, text.encode("utf-8", "replace"))
    os._exit(code)


# ---- end of the shared block ----

ANSWER = None  # the descriptor the answer goes to: descriptor 1 as it was before the project's code ran
DEPTH = 40  # the includes nested deeper than this are not followed: a URLconf that includes itself would never end
OWN = "daodan_django_routes"  # the name this script has for the `shell -c` code that calls back into it


class Marks:
    """The mapping `normalize`'s forms (`shop/products/%(pk)s/`) are formatted with: each argument becomes its name between two NULs, which no
    route holds, so the form splits into its static texts and its arguments without reading its text."""

    def __getitem__(self, name):
        return f"\0{name}\0"


def isolating(converter):
    """Whether the argument of a converter is one segment of the path: False where Django's own pattern for it accepts a path of two segments,
    True for one of Django's own converters that does not, None for a project's own, which no official datum describes. The question is put to
    Django: a `RoutePattern` of one argument of that converter (`<name:x>`, the name the converter is registered under) and its `match` of
    `a/b`, the method the resolver uses to match a route (`FourDigits`, `[0-9]{4}`, may be one segment and nothing says so; `path` accepts
    the probe, and so does a project's converter whose pattern holds a `/`). `str`, `int`, `slug` and `uuid` are Django's own."""
    from django.urls.converters import DEFAULT_CONVERTERS, get_converters
    from django.urls.resolvers import RoutePattern
    names = [name for name, known in get_converters().items() if known is converter]
    if not names:
        return None
    try:
        if RoutePattern(f"<{names[0]}:x>", is_endpoint=True).match("a/b") is not None:
            return False
    except Exception:  # a `to_python` of the project raised on the probe: nothing is proved
        return None
    return True if any(converter is known for known in DEFAULT_CONVERTERS.values()) else None


def parts_of(pieces):
    """`(parts, arguments)` of the route made by the levels `pieces` (resolvers and the pattern, from the root's first child down):
    `parts` is the path as `[dynamic, text]` pairs, from Django's own `normalize` of the compiled regular expressions of the levels, composed as
    `URLResolver._populate` composes them, for a route whose every level is a `RoutePattern`; None for any other (`re_path`, `i18n_patterns`, a
    pattern class of the project) and where normalize gives not exactly one form. `arguments` maps each argument of the route to
    `isolating` of its converter; every converter of every level is there, whether or not `parts` is."""
    from django.urls.resolvers import RoutePattern
    from django.utils.regex_helper import normalize
    converters = {}
    for piece in pieces:
        converters.update(getattr(piece.pattern, "converters", {}))
    arguments = {name: isolating(converter) for name, converter in converters.items()}
    if not all(type(piece.pattern) is RoutePattern for piece in pieces):
        return None, arguments
    try:
        forms = normalize("".join(piece.pattern.regex.pattern.removeprefix("^") for piece in pieces))
        if len(forms) != 1:
            return None, arguments
        texts = (forms[0][0] % Marks()).split("\0")
    except (ValueError, TypeError, KeyError, NotImplementedError):  # a literal `%` in a route, or a form normalize cannot make
        return None, arguments
    texts[0] = "/" + texts[0]
    return [[index % 2 == 1, text] for index, text in enumerate(texts) if text or index % 2 == 1], arguments


@functools.lru_cache(maxsize=None)
def class_definitions(file):
    """`{first line: line of the class}` of each class in the module `file`, as `definitions` does for the functions: `inspect.getsourcelines` of a
    decorated class starts at its first decorator."""
    try:
        with tokenize.open(file) as source:
            tree = ast.parse(source.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return {}
    return {min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)]): node.lineno for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)}


def describe(target, cwd, kind="function"):
    """`{kind, type, module, qualname, file, line, environment, distribution, owners}` of a function or a class; `type` is the class of the
    object (an object with `__call__` has no `qualname` and no `file`: it is what a gap can say it is), `file` is None where the interpreter gives
    none, `environment` whether it is in the packages the interpreter installs, `distribution` the local directory it was installed from and
    `owners` the distributions that hold its module."""
    try:
        file = inspect.getsourcefile(target)
    except TypeError:  # a built-in or a callable object: no source file
        file = None
    real = os.path.realpath(file) if file else None
    environment = bool(real) and any(real.startswith(packages + os.sep) for packages in PACKAGES)
    module = getattr(target, "__module__", None)
    line = None
    if file and kind == "function":
        line = definition_line(target, file)
    elif file:
        try:
            first = inspect.getsourcelines(target)[1]  # the first line of the class statement, decorators included
            line = class_definitions(file).get(first, first)
        except (OSError, TypeError):
            pass
    return {"kind": kind, "type": f"{type(target).__module__}.{type(target).__qualname__}", "module": module,
            "qualname": getattr(target, "__qualname__", None), "file": os.path.relpath(file, cwd).replace(os.sep, "/") if file else None,
            "line": line, "environment": environment, "distribution": installed_from(module) if environment else None,
            "owners": sorted(packages_distributions().get((module or "").split(".")[0], ())) if environment else []}


def function(view):
    """The function a view stands for: Django's own steps (`functools.partial.func`, as `URLPattern.lookup_str` takes it), then
    `inspect.unwrap` (what `functools.wraps` ties to the wrapper), a bound method as its function."""
    target = view.func if isinstance(view, functools.partial) else view
    try:
        target = inspect.unwrap(target)
    except ValueError:  # a cycle of `__wrapped__`
        pass
    return getattr(target, "__func__", target)


def handlers(view, cwd):
    """`(class, [{method, handler}])` of a view: for a class-based view (`view_class`, Django's `as_view`; `cls`, Django REST framework's) the
    class and, for each HTTP method, the function that answers it; for a function view, no class and one handler with no method."""
    cls = getattr(view, "view_class", None) or getattr(view, "cls", None)
    if not inspect.isclass(cls):
        return None, [{"method": None, "handler": describe(function(view), cwd)}]
    actions = getattr(view, "actions", None)  # a viewset: the HTTP method to the name of the method of the class that answers it
    names = ({method.upper(): name for method, name in actions.items() if isinstance(name, str)} if isinstance(actions, dict) else
             {name.upper(): name for name in getattr(cls, "http_method_names", ()) if hasattr(cls, name)})
    found = {method: function(getattr(cls, name)) for method, name in names.items() if hasattr(cls, name)}
    answers = []
    for method, answer in found.items():
        described = describe(answer, cwd)
        if method == "HEAD" and answer is found.get("GET"):
            continue  # `View.setup` and a viewset's `as_view` give HEAD the function of GET: the framework's own
        if method == "OPTIONS" and described["environment"]:
            continue  # every `View` has one: only a project's own is a method the class declares
        answers.append({"method": method, "handler": described})
    return describe(cls, cwd, "class"), answers or [{"method": None, "handler": None}]


def text_of(pieces):
    """The route as Django writes it: the text of each level, the `^` Django drops where it composes the levels left off."""
    return "/" + "".join(str(piece.pattern).removeprefix("^") for piece in pieces)


def walk(patterns, pieces, routes, unread, cwd, seen):
    from django.urls import URLResolver
    for pattern in patterns:
        here = [*pieces, pattern]
        if isinstance(pattern, URLResolver):  # an `include()`, an app's URLs, `i18n_patterns` (not `hasattr(.., "url_patterns")`: that property raises)
            if len(here) > DEPTH:
                unread.append({"route": text_of(here), "error": f"includes nested deeper than {DEPTH} levels"})
                continue
            try:
                children = pattern.url_patterns
            except Exception as error:  # this URLconf does not load: its routes are the gap, the others' stay
                unread.append({"route": text_of(here), "error": f"{type(error).__name__}: {error}"})
                continue
            seen.update(type(piece.pattern).__name__ for piece in here)
            walk(children, here, routes, unread, cwd, seen)
        else:
            parts, arguments = parts_of(here)
            view, answers = handlers(pattern.callback, cwd)
            routes.append({"path": text_of(here), "parts": parts, "arguments": arguments, "view": view, "handlers": answers})


def collect(cwd):
    import django
    from django.conf import settings
    from django.urls import get_resolver
    from django.utils import translation
    django.setup()  # the command already did it; a settings error `ManagementUtility` kept to itself is raised here, with its own words
    routes, unread, seen = [], [], set()
    walk(get_resolver().url_patterns, [], routes, unread, cwd, seen)
    active = translation.get_language()  # the language the routes' texts and prefixes were made in: the one of the settings, nothing activated it
    locale = {"active": active, "others": len([code for code, _name in settings.LANGUAGES if code != active])} if "LocalePrefixPattern" in seen else None
    return {"called": True, "routes": routes, "unread": unread, "locale": locale}


def deliver():
    """What `manage.py shell -c` calls once Django has loaded the project: the document goes to the descriptor saved before the project ran."""
    try:
        document = json.dumps(collect(os.getcwd()))
    except BaseException as error:  # the project's own code runs while its settings, its apps and its URLconf load: whatever it raises is the cause
        leave(3, f"{type(error).__name__}: {error}\n")
    with os.fdopen(ANSWER, "w", encoding="utf-8") as out:
        out.write(document)
    leave(0)


def main():
    global ANSWER
    ANSWER = os.dup(1)  # the descriptor the answer goes to: kept before the project's code can reach it
    os.dup2(2, 1)  # whatever the project prints, and its children, goes to the standard error
    sys.path.insert(0, os.getcwd())  # what `python manage.py` does: the folder of the script first
    sys.modules[OWN] = sys.modules[__name__]
    sys.argv = ["manage.py", "shell", "-c", f"import {OWN}; {OWN}.deliver()"]
    try:
        runpy.run_path("manage.py", run_name="__main__")
    except SystemExit as error:
        leave(5, f"manage.py ended with exit {error.code} before the command ran\n")
    except BaseException as error:
        leave(3, f"{type(error).__name__}: {error}\n")
    leave(4, "manage.py ran and did not run the shell command\n")


if __name__ == "__main__":
    main()
