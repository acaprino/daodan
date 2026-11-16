"""Source: how a Python project says its tests run, read from its files, never run.

pytest, where the project declares or configures it: a pytest configuration (`pytest.ini`, `.pytest.ini`,
`pytest.toml`, `.pytest.toml`, the `[tool.pytest]` table of `pyproject.toml`, `[pytest]` in `tox.ini`,
`[tool:pytest]` in `setup.cfg`), pytest or one of its plugins (`pytest-*`) among the dependencies a manifest
declares (`pyproject.toml`: the project's, its extras and groups, Poetry's, PDM's, uv's, Hatch's environments; a
requirements file), or a `conftest.py`. A configuration or a manifest gives the folder pytest runs in. A
`conftest.py` under no such folder gives the folder pytest is given (`args`), run from the nearest folder above
it with a Python manifest, else from the project's root: the outermost `conftest.py` only, one entry per folder
it runs from.

unittest, only where a file of the project writes the command: a `python -m unittest ...` line in `tox.ini` or in
a makefile, run in that file's folder with the arguments written (`{posargs}` dropped). A line with a variable or
a substitution states nothing, and so does a folder where pytest is declared: pytest runs unittest's tests too.

Each is a `tests` entry `{root, runner, declared_in, args}`. A project with neither states nothing: the dynamic
step's gap, never a guessed command.
"""
from __future__ import annotations

import configparser
from pathlib import PurePosixPath
import re
import shlex
import tomllib

from premap import requirements

NAME, VERSION, RANK = "python-tests", "daodan/premap/v1", "reader"
CONFIGS = ("pytest.ini", ".pytest.ini", "pytest.toml", ".pytest.toml")
MANIFESTS = ("pyproject.toml", "setup.py", "setup.cfg")
MAKEFILES = ("GNUmakefile", "makefile", "Makefile")
PYTEST = re.compile(r"^pytest(-[a-z0-9-]+)?$")  # pytest itself, or a plugin of it
NAMED = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")  # the name a requirement starts with (PEP 508)
UNITTEST = re.compile(r"(?:^|[\s;&|=@])python[0-9.]*\s+-m\s+unittest\b([^\n;&|#<>]*)")
PLAIN = re.compile(r"^[A-Za-z0-9_./:=,*\"'-]+$")  # an argument written as it is given, no variable in it


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _inside(rel: str, root: str) -> bool:
    return root == "." or rel == root or rel.startswith(root + "/")


def _is_pytest(requirement) -> bool:
    name = NAMED.match(requirement) if isinstance(requirement, str) else None
    return bool(name and PYTEST.match(re.sub(r"[-_.]+", "-", name.group(1)).lower()))


def _lists(data: dict):
    """`(where, requirements)` of each list of dependencies a `pyproject.toml` declares."""
    def table(value):
        return value if isinstance(value, dict) else {}

    project, tool = table(data.get("project")), table(data.get("tool"))
    yield "project.dependencies", project.get("dependencies")
    for name, items in table(project.get("optional-dependencies")).items():
        yield f"project.optional-dependencies.{name}", items
    for name, items in table(data.get("dependency-groups")).items():
        yield f"dependency-groups.{name}", items
    yield "tool.uv.dev-dependencies", table(tool.get("uv")).get("dev-dependencies")
    poetry = table(tool.get("poetry"))
    for where, items in (("dependencies", poetry.get("dependencies")),
                         ("dev-dependencies", poetry.get("dev-dependencies")),
                         *((f"group.{name}.dependencies", table(group).get("dependencies"))
                           for name, group in table(poetry.get("group")).items())):
        yield f"tool.poetry.{where}", list(items) if isinstance(items, dict) else None  # Poetry's tables: the names
    for name, items in table(table(tool.get("pdm")).get("dev-dependencies")).items():
        yield f"tool.pdm.dev-dependencies.{name}", items
    for name, env in table(table(tool.get("hatch")).get("envs")).items():
        yield f"tool.hatch.envs.{name}.dependencies", table(env).get("dependencies")


def _pyproject(text: str) -> str | None:
    """Where a `pyproject.toml` declares pytest: its configuration table, else the first list naming it."""
    data = tomllib.loads(text)
    configured = (data.get("tool") or {}).get("pytest")
    if isinstance(configured, dict):
        return "tool.pytest.ini_options" if "ini_options" in configured else "tool.pytest"
    return next((where for where, items in _lists(data)
                 if isinstance(items, list) and any(_is_pytest(item) for item in items)), None)


def _section(text: str, name: str) -> bool:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read_string(text)
    return parser.has_section(name)


def _pytest(rel: str, text: str) -> str | None:
    """`declared_in` when the file declares pytest, None otherwise."""
    name = PurePosixPath(rel).name
    if name in CONFIGS:
        return rel
    if name == "pyproject.toml":
        where = _pyproject(text)
        return f"{rel}#{where}" if where else None
    if name in ("tox.ini", "setup.cfg"):
        section = "pytest" if name == "tox.ini" else "tool:pytest"
        return f"{rel}#{section}" if _section(text, section) else None
    if requirements.is_requirements(rel) and any(_is_pytest(line) for line in requirements._lines(text)):
        return rel
    return None


def _unittest(text: str) -> list[str] | None:
    """The arguments of the first `python -m unittest` line written without a variable, None when there is none."""
    for written in UNITTEST.findall(text):
        try:
            words = [word for word in shlex.split(written) if word != "{posargs}"]
        except ValueError:
            continue
        if all(PLAIN.match(word) for word in words):
            return words
    return None


def run(context):
    inventory = context.inventory
    found: dict[tuple[str, str], dict] = {}
    conftests, manifests = [], set()
    for rel in inventory.files:
        name = PurePosixPath(rel).name
        if name in MANIFESTS:
            manifests.add(_folder(rel))
        elif requirements.is_requirements(rel):
            manifests.add(requirements._home(rel))
        if name == "conftest.py":
            conftests.append(_folder(rel))
            continue
        wanted = name in CONFIGS or name in ("pyproject.toml", "tox.ini", "setup.cfg") or name in MAKEFILES \
            or requirements.is_requirements(rel)
        if not wanted:
            continue
        try:
            text = inventory.text(rel)
            declared = _pytest(rel, text)
            args = _unittest(text) if name == "tox.ini" or name in MAKEFILES else None
        except (ValueError, configparser.Error):
            continue  # an unreadable manifest is the module graph's gap
        root = requirements._home(rel) if requirements.is_requirements(rel) else _folder(rel)
        if declared:
            entry = found.setdefault((root, "pytest"), {"root": root, "runner": "pytest", "declared_in": declared,
                                                         "args": []})
            if "#tool.pytest" in declared or PurePosixPath(declared).name in CONFIGS:
                entry["declared_in"] = declared  # the configuration, before a dependency that names pytest
        if args is not None:
            found.setdefault((root, "unittest"), {"root": root, "runner": "unittest", "declared_in": rel,
                                                  "args": args})
    declared_roots = [root for root, runner in found if runner == "pytest"]
    outer = sorted(folder for folder in conftests if not any(other != folder and _inside(folder, other)
                                                             for other in conftests))
    for folder in outer:
        if any(_inside(folder, root) for root in declared_roots):
            continue  # that folder's pytest collects it
        above = [root for root in manifests if _inside(folder, root)]
        root = max(above, key=lambda r: (r != ".", len(r))) if above else "."
        entry = found.setdefault((root, "pytest"), {"root": root, "runner": "pytest",
                                                     "declared_in": f"{folder}/conftest.py".removeprefix("./"),
                                                     "args": []})
        if folder != root:
            entry["args"].append(folder if root == "." else folder[len(root) + 1:])
    tests = [entry for (root, runner), entry in sorted(found.items())
             if runner == "pytest" or (root, "pytest") not in found]
    return {"facts": {"tests": tests}} if tests else None
