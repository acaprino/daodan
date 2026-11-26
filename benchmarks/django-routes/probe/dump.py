"""Exploratory: what Django's loaded URLconf holds, level by level, written as one JSON document to descriptor 3
(run by `python manage.py shell -c "exec(open('<this file>').read())"` with `exec 3>&1 1>&2`, kind `dump` of `modal_probe.py`)."""
import inspect
import json
import os
import sysconfig
import time

import django

started = time.monotonic()
django.setup()
setup_seconds = round(time.monotonic() - started, 3)

from django.conf import settings
from django.urls import get_resolver
from django.utils import translation
from django.utils.regex_helper import normalize

PACKAGES = tuple({os.path.realpath(sysconfig.get_paths()[key]) for key in ("purelib", "platlib")})


def where(target):
    try:
        file = inspect.getsourcefile(target)
    except TypeError:
        file = None
    code = getattr(target, "__code__", None)
    real = os.path.realpath(file) if file else None
    return {"type": f"{type(target).__module__}.{type(target).__qualname__}", "module": getattr(target, "__module__", None),
            "qualname": getattr(target, "__qualname__", None), "file": os.path.relpath(file) if file else None,
            "line": code.co_firstlineno if code else None, "environment": bool(real) and any(real.startswith(p + os.sep) for p in PACKAGES)}


def callback(view):
    chain, seen = [], view
    while seen is not None and len(chain) < 8:
        chain.append(where(seen))
        seen = getattr(seen, "__wrapped__", None)
    out = {"chain": chain, "dict": sorted(vars(view)) if hasattr(view, "__dict__") else None,
           "closure": {name: repr(cell.cell_contents)[:60] for name, cell in zip(view.__code__.co_freevars, view.__closure__ or ())}
           if hasattr(view, "__code__") else None}
    cls = getattr(view, "view_class", None) or getattr(view, "cls", None)
    for name in ("view_class", "cls"):
        if getattr(view, name, None) is not None:
            out[name] = where(getattr(view, name))
    if cls is not None:
        out["http_method_names"] = list(getattr(cls, "http_method_names", ()))
        out["has"] = {m: where(inspect.unwrap(getattr(cls, m))) for m in getattr(cls, "http_method_names", ()) if hasattr(cls, m)}
        out["view_is_async"] = repr(getattr(cls, "view_is_async", None))
    actions = getattr(view, "actions", None)
    if actions is not None:
        out["actions"] = actions
        out["action_handlers"] = {m: where(inspect.unwrap(getattr(cls, a))) for m, a in actions.items() if cls is not None and hasattr(cls, a)}
    for name in ("initkwargs", "view_initkwargs", "suffix", "detail", "basename"):
        if hasattr(view, name):
            out[name] = repr(getattr(view, name))[:80]
    return out


def walk(patterns, prefix_regex, depth):
    found = []
    for p in patterns:
        regex = p.pattern.regex.pattern
        composed = prefix_regex + regex.removeprefix("^")
        node = {"depth": depth, "class": type(p).__name__, "pattern_class": type(p.pattern).__name__, "str": str(p.pattern), "regex": regex,
                "composed": composed, "converters": {n: [f"{type(c).__module__}.{type(c).__qualname__}", c.regex]
                                                     for n, c in getattr(p.pattern, "converters", {}).items()}}
        try:
            node["normalized"] = normalize(composed)
        except Exception as error:
            node["normalized"] = f"{type(error).__name__}: {error}"
        if hasattr(p, "url_patterns"):
            node.update(namespace=p.namespace, app_name=p.app_name, urlconf_name=repr(p.urlconf_name)[:80], default_kwargs=repr(p.default_kwargs))
            if hasattr(p.pattern, "language_prefix"):
                node["language_prefix"] = p.pattern.language_prefix
                node["prefix_default_language"] = p.pattern.prefix_default_language
                with translation.override("it"):
                    node["str_it"] = str(p.pattern)
                    node["regex_it"] = p.pattern.regex.pattern
            try:
                node["children"] = walk(p.url_patterns, composed, depth + 1)
            except BaseException as error:
                node["error"] = f"{type(error).__name__}: {error}"
        else:
            node.update(name=p.name, lookup_str=p.lookup_str, default_args=repr(p.default_args), callback=callback(p.callback))
            if hasattr(p.pattern, "_route") and not isinstance(p.pattern._route, str):
                node["lazy_route"] = True
                with translation.override("it"):
                    node["str_it"] = str(p.pattern)
        found.append(node)
    return found


from django.urls.converters import DEFAULT_CONVERTERS, get_converters

report = {"setup_seconds": setup_seconds, "version": django.get_version(), "language": translation.get_language(),
          "settings_module": os.environ.get("DJANGO_SETTINGS_MODULE"), "languages": settings.LANGUAGES,
          "default_converters": {n: [f"{type(c).__module__}.{type(c).__qualname__}", c.regex] for n, c in DEFAULT_CONVERTERS.items()},
          "all_converters": {n: [f"{type(c).__module__}.{type(c).__qualname__}", c.regex] for n, c in get_converters().items()}}
try:
    report["tree"] = walk(get_resolver().url_patterns, "", 0)
except BaseException as error:
    report["tree_error"] = f"{type(error).__name__}: {error}"

# the one function of Django that lists the views of a URLconf, and whether it can be used without the admin among the installed apps
admin_installed = "django.contrib.admin" in settings.INSTALLED_APPS
try:
    from django.contrib.admindocs.views import extract_views_from_urlpatterns, simplify_regex
    views = extract_views_from_urlpatterns(get_resolver().url_patterns)
    report["admindocs"] = {"admin_installed": admin_installed, "imported": True, "views": len(views),
                           "first": [(v[0].__qualname__, v[1], v[2], v[3]) for v in views[:6]], "simplify_regex": simplify_regex("^a/(?P<x>[0-9]+)/$")}
except BaseException as error:
    report["admindocs"] = {"admin_installed": admin_installed, "imported": False, "error": f"{type(error).__name__}: {str(error)[:200]}"}

with os.fdopen(3, "w", encoding="utf-8") as out:
    out.write(json.dumps(report, default=repr, indent=1))
os._exit(0)
