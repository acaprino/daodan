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

An entry has `deps` where the folder declares the tests' dependencies apart from what its restore installs:
`{declared_in, requirements, extras, groups}`, each list only when it has names. They are those of the tox
environment of its `tox.ini` whose commands run the runner, as a CI that runs tox has them ([testenv] first; a
named one takes from [testenv] what it does not set): its `deps` lines as written, `{toxinidir}` being the
folder of tox.ini, its `extras` and `dependency_groups`. Else, for pytest, the list that names it first: a
dependency group, an extra, a requirements file (`-r` it); the project's own dependencies, uv's dev dependencies
and Poetry's groups are their restore's.
"""
from __future__ import annotations

import configparser
from pathlib import PurePosixPath
import re
import tomllib

from premap import requirements, shell

NAME, VERSION, RANK = "python-tests", "daodan/premap/v1", "reader"
CONFIGS = ("pytest.ini", ".pytest.ini", "pytest.toml", ".pytest.toml")
MANIFESTS = ("pyproject.toml", "setup.py", "setup.cfg")
MAKEFILES = ("GNUmakefile", "makefile", "Makefile")
PYTEST = re.compile(r"^pytest(-[a-z0-9-]+)?$")  # pytest itself, or a plugin of it
NAMED = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")  # the name a requirement starts with (PEP 508)
UNITTEST = re.compile(r"(?:^|[\s;&|=@])python[0-9.]*\s+-m\s+unittest\b([^\n;&|#<>]*)")
PLAIN = re.compile(r"^[A-Za-z0-9_./:=,*\"'-]+$")  # an argument written as it is given, no variable in it
RUNS = {"pytest": re.compile(r"(?:^|[\s;&|(])(?:py\.test|pytest)(?=\s|$)|-m\s+pytest\b"),
        "unittest": re.compile(r"-m\s+unittest\b")}  # a tox command that runs the runner
TOX_ROOT = re.compile(r"\{(?:toxinidir|tox_root)\}")  # tox's names for the folder of its configuration
COMMENT = re.compile(r"(?:^|\s+)#.*")  # an ini line's comment: a `#` that starts it or follows a space
LISTS = (("dependency-groups.", "groups"), ("project.optional-dependencies.", "extras"))  # installed by their name


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


def _named(data: dict) -> str | None:
    """The first list of a `pyproject.toml` that names pytest."""
    return next((where for where, items in _lists(data)
                 if isinstance(items, list) and any(_is_pytest(item) for item in items)), None)


def _pyproject(text: str) -> str | None:
    """Where a `pyproject.toml` declares pytest: its configuration table, else the first list naming it."""
    data = tomllib.loads(text)
    configured = (data.get("tool") or {}).get("pytest")
    if isinstance(configured, dict):
        return "tool.pytest.ini_options" if "ini_options" in configured else "tool.pytest"
    return _named(data)


def _tox(rel: str, text: str, runner: str) -> dict | None:
    """The `deps` of the tox environment whose commands run `runner` (the module's docstring), None when it
    declares none."""
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read_string(text)
    base = dict(parser["testenv"]) if parser.has_section("testenv") else {}
    for name in sorted((name for name in parser.sections() if name == "testenv" or name.startswith("testenv:")),
                       key=lambda name: name != "testenv"):
        env = {**base, **parser[name]}
        if not RUNS[runner].search(env.get("commands", "")):
            continue
        lines = [TOX_ROOT.sub(".", line) for line in (COMMENT.sub("", line).strip()
                                                      for line in env.get("deps", "").splitlines()) if line]
        names = {key: [word for word in re.split(r"[\s,]+", env.get(option, "")) if word]
                 for key, option in (("extras", "extras"), ("groups", "dependency_groups"))}
        found = {key: value for key, value in {"requirements": lines, **names}.items() if value}
        return {"declared_in": f"{rel}#{name}", **found} if found else None
    return None


def _listed(rel: str, text: str) -> dict | None:
    """The `deps` a file lists for pytest (the module's docstring), None when its restore installs them."""
    if requirements.is_requirements(rel):
        return {"declared_in": rel, "requirements": [f"-r {PurePosixPath(rel).name}"]} if _pytest(rel, text) else None
    if PurePosixPath(rel).name != "pyproject.toml":
        return None
    where = _named(tomllib.loads(text)) or ""
    return next(({"declared_in": f"{rel}#{where}", key: [where[len(prefix):]]} for prefix, key in LISTS
                 if where.startswith(prefix)), None)


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
        said = shell.commands(written)
        if said is None:
            continue
        words = [word for _, command in said for word in command if word != "{posargs}"]
        if all(PLAIN.match(word) for word in words):
            return words
    return None


def run(context):
    inventory = context.inventory
    found: dict[tuple[str, str], dict] = {}
    conftests, manifests = [], set()
    tox: dict[str, tuple[str, str]] = {}  # folder -> its tox.ini and the text
    listed: dict[str, dict] = {}  # folder -> the first list that names pytest
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
            named = _listed(rel, text)
        except (ValueError, configparser.Error):
            continue  # an unreadable manifest is the module graph's gap
        root = requirements._home(rel) if requirements.is_requirements(rel) else _folder(rel)
        if name == "tox.ini":
            tox[root] = (rel, text)
        if named:
            listed.setdefault(root, named)
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
    for entry in tests:
        deps = (_tox(*tox[entry["root"]], entry["runner"]) if entry["root"] in tox else None) or (
            listed.get(entry["root"]) if entry["runner"] == "pytest" else None)
        if deps:
            entry["deps"] = deps
    return {"facts": {"tests": tests}} if tests else None
