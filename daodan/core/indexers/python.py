"""scip-python for Python: how it runs, and what its index leaves to the reader.

`index` runs scip-python (npm, without install scripts, on Daodan's Node) in a mirror of the project, once per
Python project it is given (`units`; the whole checkout when none is), its documents named from the root by
that project's folder. A file outside every project has no document (`missing` says so). The adapter finds no
project itself. Run from the root, a Python project kept in a folder (`svc/app`, imported as `app`) would name
its modules differently where they are defined and where they are imported. Each run has that project's
declared packages, from the manifests its unit states (`manifests`), in the engine pass's environment
(`python_environment`: wheels only, by Daodan's pinned uv, never the PATH's: without it Python is `unavailable`)
described to it as an environment file, so it never asks pip. The
environment's interpreter is Daodan's, else, where Daodan's is not one it admits, the Python the unit's folder
states first as uv reads it (`structure`: a version file, else requires-python), which uv resolves as `uv sync`
does; the run says the version it ran with (`python`) and that statement (`python_request`). A source
root is not found unless Pyright is told: without it no absolute import of the project's own package resolves.
The mirror gets a `pyrightconfig.json` with the source roots the unit states (`source_roots`), else `src`
where it holds a package, each as a root and an extra path, unless the project declares a Pyright
configuration. What a run lacks is a gap of the contract (`gaps`): an environment that failed, a stated
manifest the environment does not read. No project code runs, nor any of its environment's where the checkers
start its interpreter to ask its paths (`python_environment` removes what it would run as it starts: `.pth`
import lines, `sitecustomize`). The project's version is `_` in every run: it
is part of each project symbol, so node ids stay the same from one snapshot to the next.

Where scip-python cannot start (Windows: `RUNS_HERE`), it runs in a container (`container.run_in_container`,
`IMAGE`) over the copy of the project, with no network: the copy carries Node for Linux, checked like the
host's, scip-python and Pyright as npm installed them on the host, and the site-packages of the host's
environment, which the image's Python adds to its path. The image's Python reads the copy, the checker's pass
after the index too: a Python the unit states that it is not is a gap. Without a container engine Python is
`unavailable`, and nothing is downloaded.

`hops` reads, from `code_graph.Index`, what scip-python leaves implicit; each hop carries its own tag:
- `import-binding`: an imported name (`from m import a`, `a as b`) is a `local` the index defines nowhere, with
  no tie to `m`; it leads to the module occurrence of the same one-line statement;
- `builtin`: a builtin function (`isinstance`, `len`) is such a `local` too, while a builtin class has its
  `builtins/` symbol; an unbound bare name the interpreter's `builtins` holds, neither an attribute nor a
  keyword argument's name, leads to that module's symbol, in the package the index gives `builtins`;
- `classmethod-cls`: the first parameter of a method decorated `classmethod` (the decorator lies in the
  method's enclosing range) leads to the method's class;
- `type-of-self`: a local assigned `type(<first parameter of a method>)` leads to the method's class.
- `initializer`: a name assigned a bare or dotted name alone (`f = area`, `f = shapes.area`, `self.f = area`,
  `f: T = area`), never a call's result, leads to what the last name refers to.
- `rebinding`: a function whose first `def` is a stub decorated `overload` (from `typing` or
  `typing_extensions`, by name, alias or attribute) is bound at run time by its last `def` without
  that decorator; the index defines the symbol at the first `def` only. A symbol with stubs alone keeps
  them.
- `source-root`: a module imported through a source root the run tells Pyright (`semver`, under `src`) is named
  by its import where it is imported and by its path (`src.semver`) where it is defined: it leads to that one.
- `deferred-annotation`: a bare name in an annotation that the module defines once at its top level, below it
  (`items: list[Item]` above `class Item`), is a `local` the index defines nowhere: Python 3.14 evaluates an
  annotation when it is read (PEP 649), and scip-python's Pyright predates 3.14. It leads to that definition.

`classify` reads what scip-python labels wrongly (0.6.8): a symbol of the project's package whose module is a
file of a distribution the run's environment lists (a name the package's `__init__` re-exports: `sa.UUID`,
`typer.Typer`, `pytest.fail`) is that distribution's; the namespace alone of a module, which it gives the
attributes the interpreter sets on every module (`__name__`, `__file__`, `__doc__`), is the interpreter's
(`python-stdlib`). After the index, the checker's pass (`python_unbound.py`: Pyright `PYRIGHT`'s language server
over the same environment, the files parsed by its interpreter) says of each member the project reads what the
checker gives it, beside the index (`<index>.unbound.jsonl`): a member where the index has no occurrence
(`unanswered`) or gives a local it defines nowhere (`classify`) carries that cause (`UNBOUND_CAUSES`). A type after
the first of a Python 3.14 `except A, B:`, which scip-python's parser does not read, carries that (`NEWER_SYNTAX`).
"""
from __future__ import annotations

import collections
import csv
import email.parser
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import code_graph

VERSION = "0.6.8"  # @sourcegraph/scip-python on npm
# A second Pyright beside the one inside scip-python, kept on purpose: it alone gives the cause of a hole (its
# language server's hover: `Any`, `Unknown`, `bound`, `UNBOUND_CAUSES`); scip-python embeds its Pyright and exposes
# no hover or type of a member, only the index.
PYRIGHT = "1.1.414"  # pyright on npm: the checker's pass (`python_unbound.py`)
UNBOUND = Path(__file__).with_name("python_unbound.py")
# Why the index names nothing at a member, by what the checker says of it (`python_unbound.py`).
UNBOUND_CAUSES = {"Any": "a member the checker types Any (a dynamic attribute, `__getattr__`): only execution knows it",
                  "Unknown": "a member of a value the checker types Unknown: only execution knows it",
                  "bound": "the checker binds the {} and scip-python names nothing there"}
# `except A, B:` without parentheses (PEP 758, Python 3.14), which the snapshot reads with the Python the project
# states: scip-python's parser predates 3.14 and gives the types after the first no occurrence (fastapi's deps.py).
EXCEPT_TYPES = re.compile(r"\s*except\*?\s+[^\s(][^:#]*,")
NEWER_SYNTAX = (f"an `except A, B:` of Python 3.14 (PEP 758): scip-python {VERSION}'s parser predates it and gives "
                "the types after the first no occurrence")
# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
NAME, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-python", ("python",), frozenset({"python-project"}), False
MIN_FREE = 1920 * 2**20  # 1,852 MB peak on a private case, 350 MB on python-semver (benchmarks/inference-audit, 14 November 2026)
# scip-python builds `new RegExp(path.sep, 'g')` when it loads (`PythonEnvironment.ts`): with Windows' `\` it
# stops there, before reading anything (0.6.8, 14 November 2026).
RUNS_HERE = os.sep == "/"
IMAGE = "python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90"  # 3.13.18
CONTAINER_MEMORY = 2 * 2**30
OUT = "/daodan/out"
# The container's script: $1 the project's name, $2 its version, $3 its folder. The image's Python adds the host
# environment's site-packages (`/daodan/env`), where Pyright asks it for its search paths; after the index, the
# checker's pass, where its Pyright was carried (`pyright.path`).
BOX = r'''set -u
mkdir -p /daodan/node /daodan/out || exit 70
tar -xzf /daodan/tools/node.tar.gz -C /daodan/node --strip-components=1 || exit 70
site=$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])') || exit 70
echo "import site; site.addsitedir('/daodan/env')" > "$site/daodan-env.pth" || exit 70
echo "DAODAN_PYTHON $(python3 -c 'import platform; print(platform.python_version())')"
cd "/work/$3" || exit 70
if [ -f /daodan/tools/pyrightconfig.json ] && [ ! -e pyrightconfig.json ]; then
  cp /daodan/tools/pyrightconfig.json . || exit 70
fi
export NODE_OPTIONS=--max-old-space-size=1536
/daodan/node/bin/node "$(cat /daodan/tools/scip-python.path)" index . \
  --project-name "$1" --project-version "$2" --output /daodan/out/index.scip --environment /daodan/tools/environment.json
code=$?
echo "DAODAN_PEAK $(cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo -)"
if [ $code -eq 0 ] && [ -f /daodan/tools/pyright.path ]; then
  python3 -I -S /daodan/tools/python_unbound.py /daodan/node/bin/node "$(cat /daodan/tools/pyright.path)" . \
    "$(command -v python3)" > /daodan/out/unbound.jsonl || echo "DAODAN_UNBOUND $?"
fi
exit $code
'''
ASSIGNED_TYPE = re.compile(r"^\s*(\w+)\s*=\s*type\(\s*(\w+)\s*\)\s*(#.*)?$")
FROM_IMPORT = re.compile(r"^\s*from\s+\S+\s+import\s+[^()]+$")
METHOD = re.compile(r"#[^#/().]+\(\)\.$")
HOLDER = re.compile(rb"^\s*(?:(?:self|cls)\s*\.\s*)?$")  # what may precede an assigned name
DEF = re.compile(rb"^\s*(?:async\s+)?def\s+$")  # what precedes the name of a `def` statement
OVERLOAD = (" typing/overload().", " typing_extensions/overload().")
TYPING = (" typing/__init__:", " typing_extensions/__init__:")
INITIALIZER = re.compile(rb"\s*(?::[^=]*)?=\s*([A-Za-z_]\w*(?:\s*\.\s*[A-Za-z_]\w*)*)\s*(?:#.*)?$")


def _text(index, rel: str, occurrence) -> tuple[str, str]:
    """(the line an occurrence starts on, the source text of its range on that line)."""
    line = index.line(rel, occurrence.line) or ""
    begin = index.to_bytes(rel, occurrence.line, occurrence.start)
    stop = index.to_bytes(rel, occurrence.line, occurrence.end) if occurrence.end_line == occurrence.line else None
    data = line.encode("utf-8")
    return line, data[begin:stop].decode("utf-8", errors="replace") if begin is not None else ""


def static(index) -> set:
    """`(rel, line, byte column)` of member references Python binds without dispatch: `C.m` on a class symbol
    the index names right before the dot, and `super().m`. An override in a subclass never runs there."""
    out = set()
    for rel, occurrences in index.documents.items():
        ends = {(o.line, o.end): o.key for o in occurrences if not o.definition and o.end_line == o.line}
        for o in occurrences:
            if o.definition or o.start < 2:
                continue
            line = index.line(rel, o.line) or ""
            begin = index.to_bytes(rel, o.line, o.start)
            head = line.encode("utf-8")[:begin].decode("utf-8", errors="ignore") if begin is not None else ""
            if not head.endswith("."):
                continue
            receiver = ends.get((o.line, o.start - 1), "")
            if head[:-1].rstrip().endswith("super()") or (receiver.endswith("#") and "#local " not in receiver):
                out.add((rel, o.line, begin))
    return out


def _initialized(index, rel: str, ordered: list, by_line: dict) -> list:
    """(the key the last name refers to, the definition) for each `name = a.b` statement: a defined name alone
    on the left (after `self.` or `cls.` at most, with an annotation or not), a bare or dotted name alone on
    the right."""
    out = []
    for o in ordered:
        if not o.definition or o.end_line != o.line:
            continue
        data = (index.line(rel, o.line) or "").encode("utf-8")
        begin, stop = index.to_bytes(rel, o.line, o.start), index.to_bytes(rel, o.line, o.end)
        if begin is None or stop is None or not HOLDER.match(data[:begin]):
            continue
        found = INITIALIZER.match(data, stop)
        if not found:
            continue
        last = [item for item in by_line[o.line] if not item.definition and item.key != o.key
                and index.to_bytes(rel, item.line, item.end) == found.end(1)]
        out += [(item.key, o) for item in last]
    return out


def _overload(index, rel: str, by_line: dict, line: int) -> bool:
    """Whether the decorator lines right above `line` hold `typing`'s `overload`."""
    number = line - 1
    while number >= 1 and (index.line(rel, number) or "").lstrip().startswith("@"):
        items = sorted(by_line.get(number, ()), key=lambda o: o.start)
        for position, item in enumerate(items):
            if item.key.endswith(OVERLOAD) or (item.key.endswith(TYPING) and position + 1 < len(items)
                                               and _text(index, rel, items[position + 1])[1] == "overload"):
                return True
        number -= 1
    return False


def _implementations(index, rel: str, ordered: list, by_line: dict) -> list:
    """(the definition, the implementation's name) for each function of the document whose first `def` is an
    `overload` stub and a later `def` of the same symbol is not."""
    statements = collections.defaultdict(list)
    for o in ordered:
        begin = index.to_bytes(rel, o.line, o.start) if o.key.endswith(").") else None
        if begin is not None and DEF.match((index.line(rel, o.line) or "").encode("utf-8")[:begin]):
            statements[o.key].append(o)
    out = []
    for found in statements.values():
        plain = [o for o in found[1:] if not o.definition and not _overload(index, rel, by_line, o.line)]
        if found[0].definition and plain and _overload(index, rel, by_line, found[0].line):
            out.append((found[0], plain[-1]))
    return out


def _beside(path: Path, what: str):
    """What a run left beside its index `scip-python-<n>.scip`: the environment scip-python was told
    (`environment`), the Pyright configuration it read (`config`), the checker's lines (`unbound`); None without."""
    number = path.stem.rsplit("-", 1)[-1]
    side = {"environment": path.with_name(f"scip-python-environment-{number}.json"),
            "config": path.with_name(f"pyrightconfig-{number}.json"), "unbound": path.with_suffix(".unbound.jsonl")}[what]
    try:
        text = side.read_text(encoding="utf-8")
    except OSError:
        return None
    if what != "unbound":
        return json.loads(text)
    rows = []
    for line in text.splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:  # a line the pass cut short says nothing
            continue
    return rows


def _module(key: str) -> tuple[str, str, str] | None:
    """`(what precedes the module, the module, the descriptors after it)` of a global key."""
    parts = code_graph.split_symbol(key)
    if not parts:
        return None
    descriptors = parts[4]
    if descriptors.startswith("`"):
        module, _, rest = descriptors[1:].partition("`/")
    else:
        module, _, rest = descriptors.partition("/")
    return key[:len(key) - len(descriptors)], module, rest


def _own(index) -> set:
    """The packages of the project: those of the symbols the index defines."""
    return {tuple(parts[1:4]) for parts in map(code_graph.split_symbol, index.defs) if parts}


def _checked(index) -> dict:
    """`(rel, line, column)` -> the cause the checker's pass gives a member (`UNBOUND_CAUSES`)."""
    causes = {}
    for path, prefix in index.sources:
        for row in _beside(path, "unbound") or ():
            try:
                rel, line, column, kind, said = row
                causes[(f"{prefix}/{rel}" if prefix else rel, line, column)] = UNBOUND_CAUSES[kind].format(said)
            except (ValueError, KeyError, TypeError):
                continue
    return causes


def unanswered(index):
    """Why the index has no occurrence at a site: what the checker's pass said there, else, on a clause of Python
    3.14 scip-python's parser does not read (`EXCEPT_TYPES`), that."""
    causes = _checked(index)

    def cause(site):
        rel, line, _column = site
        return causes.get(site) or (NEWER_SYNTAX if EXCEPT_TYPES.match(index.line(rel, line) or "") else None)
    return cause


def classify(index):
    """What scip-python labels wrongly, by key (see the module's docstring), and the cause the checker gives a
    local it defines nowhere; None for the rest."""
    own, causes, modules, stdlib = _own(index), _checked(index), {}, None
    for path, _prefix in index.sources:
        for package in _beside(path, "environment") or ():
            for file in package.get("files") or ():
                stem, _, suffix = str(file).rpartition(".")
                if suffix in ("py", "pyi") and stem:
                    modules.setdefault(stem.replace("/", ".").removesuffix(".__init__"), package)
    for occurrences in index.documents.values():
        for o in occurrences:
            parts = None if "#local " in o.key else code_graph.split_symbol(o.key)
            if parts and parts[2] == "python-stdlib":
                stdlib = parts[3]
                break
        if stdlib:
            break

    def stated(key: str):
        if key in index.defs:
            return None
        if "#local " in key:
            rel = key.split("#local ", 1)[0]
            return next((causes[(rel, o.line, o.start)] for o in index.documents.get(rel, ())
                         if o.key == key and (rel, o.line, o.start) in causes), None)
        parts, split = code_graph.split_symbol(key), _module(key)
        if not parts or not split or tuple(parts[1:4]) not in own:
            return None
        if not split[2]:  # a module's namespace alone: an attribute the interpreter sets on it
            return {"manager": parts[1], "package": "python-stdlib", "version": stdlib}
        found = modules.get(split[1])
        return {"manager": parts[1], "package": found["name"], "version": found["version"]} if found else None
    return stated


def _rooted(index) -> dict:
    """`{key: defined key}` for a project module named by its import (`semver`) where it is defined under a source
    root the run told Pyright (`src.semver`)."""
    roots = [str(environment.get("root")).replace("/", ".") for path, _prefix in index.sources
             for environment in (_beside(path, "config") or {}).get("executionEnvironments", ())
             if environment.get("root") not in (None, ".")]
    own, out = _own(index), {}
    for occurrences in index.documents.values() if roots else ():
        for o in occurrences:
            if o.definition or o.key in index.defs or "#local " in o.key or o.key in out:
                continue
            parts, split = code_graph.split_symbol(o.key), _module(o.key)
            if not parts or not split or tuple(parts[1:4]) not in own:
                continue
            head, module, rest = split
            for root in roots:
                name = f"{root}.{module}"
                candidate = f"{head}`{name}`/{rest}"
                if candidate in index.defs:
                    out[o.key] = candidate
                    break
    return out


def _annotation(index, rel: str, occurrence) -> bool:
    """Whether an occurrence lies in an annotation: tree-sitter's `type`, a variable's, a parameter's, a return's."""
    node = index.node(rel, occurrence, "python")
    while node is not None and node.type != "type":
        node = node.parent
    return node is not None


def hops(index) -> dict:
    """Hops `{key: [(target key, tag)]}` for what scip-python leaves implicit; see the module's docstring."""
    import builtins
    out = collections.defaultdict(list)
    for key, defined in _rooted(index).items():
        out[key].append((defined, "source-root"))
    stdlib = next((key.split(" builtins/")[0] for occurrences in index.documents.values() for o in occurrences
                   for key in (o.key,) if " builtins/" in key), None)
    for rel, occurrences in index.documents.items():
        ordered = sorted(occurrences, key=lambda o: (o.line, o.start))
        methods = {}  # method key -> [its class, decorated classmethod, first parameter]
        for o in ordered:
            if o.definition and o.enclosing and METHOD.search(o.key):
                start, head = (o.line, o.start), (o.enclosing[0], o.enclosing[1])
                decorated = any(d.key.endswith(" builtins/classmethod#") and not d.definition
                                and head <= (d.line, d.start) < start for d in ordered)
                methods[o.key] = [o.key[:o.key.rindex("#") + 1], decorated, None]
        for o in ordered:
            owner = o.key.rsplit("(", 1)[0] if o.key.endswith(")") else None
            if o.definition and owner in methods and methods[owner][2] is None:
                methods[owner][2] = o.key
        first = {parameter: (cls, decorated) for cls, decorated, parameter in methods.values() if parameter}
        for parameter, (cls, decorated) in first.items():
            if decorated:
                out[parameter].append((cls, "classmethod-cls"))
        by_line = collections.defaultdict(list)
        for o in ordered:
            by_line[o.line].append(o)
        for o, implementation in _implementations(index, rel, ordered, by_line):
            out[o.key].append(((rel, implementation.line, index.to_bytes(rel, implementation.line,
                                                                         implementation.start)), "rebinding"))
        for target, o in _initialized(index, rel, ordered, by_line):
            out[o.key].append((target, "initializer"))
        top = collections.defaultdict(set)  # a name -> the keys the module defines it with at its top level
        for o in ordered:
            split = _module(o.key) if o.definition and "#local " not in o.key else None
            named = code_graph.descriptors(split[2]) if split and split[2] else []
            if len(named) == 1 and named[0][1] in ("type", "method", "term"):
                top[named[0][0]].add(o.key)
        seen = set()
        for position, o in enumerate(ordered):
            if "#local " not in o.key:
                continue
            line, name = _text(index, rel, o)
            if o.definition:
                found, following = ASSIGNED_TYPE.match(line), ordered[position + 1:position + 3]
                if found and found.group(1) == name and len(following) == 2 \
                        and following[0].key.endswith(" builtins/type#") and following[1].key in first:
                    out[o.key].append((first[following[1].key][0], "type-of-self"))
                continue
            if o.key in index.defs or o.key in seen:
                continue
            seen.add(o.key)  # the first occurrence of an undefined local decides
            if FROM_IMPORT.match(line):
                module = [m.key for m in ordered[:position] if m.line == o.line and m.key.endswith("/__init__:")
                          and not m.definition]
                if module:
                    out[o.key].append((module[-1], "import-binding"))
                continue
            if len(top.get(name, ())) == 1 and _annotation(index, rel, o):
                out[o.key].append((next(iter(top[name])), "deferred-annotation"))
                continue
            begin = index.to_bytes(rel, o.line, o.start) or 0
            before = line.encode("utf-8")[:begin].decode("utf-8", errors="ignore").rstrip()[-1:]
            after = line.encode("utf-8")[begin + len(name.encode("utf-8")):].decode("utf-8", errors="ignore").lstrip()[:2]
            keyword = after[:1] == "=" and after != "=="  # `f(help=...)` names a parameter, not a value
            if stdlib and name.isidentifier() and not name.startswith("_") and before != "." and not keyword \
                    and hasattr(builtins, name):
                suffix = "#" if isinstance(getattr(builtins, name), type) else "()."
                out[o.key].append((f"{stdlib} builtins/{name}{suffix}", "builtin"))
    return {key: list(dict.fromkeys(items)) for key, items in out.items()}


def _manifests(project: Path) -> list[str]:
    """The project's files that may declare packages, for `python_environment` to choose from: for a run whose
    unit states none (no pre-map)."""
    names = []
    for current, directories, found in os.walk(project):
        directories[:] = [name for name in directories if not name.startswith(".")
                          and name not in ("node_modules", "__pycache__")]
        here = Path(current).relative_to(project)
        names += [(here / name).as_posix() for name in found if name in ("pyproject.toml", "uv.lock")
                  or (name.startswith("requirements") and name.endswith(".txt"))]
    return sorted(names)


def _sites(environment: Path | None) -> list[Path]:
    """The site-packages of `environment`, in a POSIX or a Windows layout."""
    if environment is None:
        return []
    return [*Path(environment).glob("lib/python*/site-packages"), *Path(environment).glob("Lib/site-packages")]


def _packages(environment: Path | None) -> list[dict]:
    """What `pip show -f` tells scip-python, read from the environment's own records: each installed
    distribution's name, version and the files its RECORD lists, relative to `site-packages`."""
    out = []
    for site in _sites(environment):
        for info in sorted(site.glob("*.dist-info")):
            try:
                metadata = email.parser.HeaderParser().parsestr((info / "METADATA").read_text(encoding="utf-8"))
                record = (info / "RECORD").read_text(encoding="utf-8") if (info / "RECORD").is_file() else ""
            except (OSError, UnicodeError):
                continue
            if not metadata["Name"]:
                continue
            out.append({"name": metadata["Name"], "version": metadata["Version"],
                        "files": [row[0] for row in csv.reader(record.splitlines()) if row]})
    return out


def _identity(project: Path, given: str | None = None) -> tuple[str, str]:
    """The project's name, `given` else declared else its directory's, and its version, always `_` (see the
    module's docstring; scip-python stops on an undefined one, `normalizeNameOrVersion`)."""
    import tomllib
    if given:
        return given, "_"
    name = project.name
    if (project / "pyproject.toml").is_file():
        try:
            name = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8")).get("project", {}).get(
                "name", name)
        except (OSError, ValueError):
            pass
    return name, "_"


def _pyright_config(root: Path, target: Path, source_roots=(), unit_roots=()) -> dict | None:
    """The source roots of the project at `root` declared to Pyright in `target`, unless the project configures
    Pyright: the ones its unit states (`source_roots`, from its folder), else `src` where it holds a package.
    Each is a root that also sees the others, and the project's folder sees them all."""
    if (root / "pyrightconfig.json").exists():
        return None
    pyproject = root / "pyproject.toml"
    if pyproject.is_file() and "[tool.pyright]" in pyproject.read_text(encoding="utf-8"):
        return None
    roots = sorted(set(source_roots) - {"."}) if source_roots else \
        ["src"] if any((root / "src").glob("*/__init__.py")) else []
    units = sorted(set(unit_roots) - {".", *roots})
    if not roots and not units:
        return None
    # A project folded into this run (`unit_roots`) is the root of its own imports and sees the declared source
    # roots; the code outside it does not see it: a module found there by name would be a guess.
    config = {"executionEnvironments": [
        *[{"root": one, **({"extraPaths": others} if others else {})}
          for one in roots for others in [[other for other in roots if other != one]]],
        *[{"root": one, **({"extraPaths": roots} if roots else {})} for one in units],
        {"root": ".", **({"extraPaths": roots} if roots else {})}]}
    target.write_text(json.dumps(config, indent=1), encoding="utf-8")
    return config


def _uv() -> None:
    """Daodan's pinned uv, which builds the environments, installed once: Unavailable when it cannot be had. The
    uv on the PATH is never used: no Python is analyzed without the pin."""
    import engine_tools
    from indexers import runtime
    if engine_tools.uv_binary(fetch=False) is None:
        runtime.room()
    with runtime.fetching(f"uv {engine_tools.UV_VERSION}", "github.com/astral-sh/uv/releases"):
        engine_tools.uv_binary()


def _prepared(project_dir: Path, unit: dict, environment: Path | None) -> tuple[Path | None, list[dict],
                                                                                 dict | None]:
    """`environment`, else the one `python_environment` builds from the manifests the unit states, named from
    the checkout's root (without them, from the ones under its folder), on the Python the unit states where
    Daodan's interpreter is not one it admits; its gaps: a stated manifest the environment does not read, an
    environment that failed, a declared package it does not hold (one without a wheel is never built), with uv's
    words; and that statement, where it chose the interpreter."""
    import resolve_edges as rx
    from dynamic import python as observer  # it imports this module: imported here, once this one is loaded
    if environment is not None:
        return Path(environment), [], None
    stated = unit.get("python")
    if not stated or observer.admits(str(stated["version"]), sys.version_info[:3]) is not False:
        stated = None
    here = project_dir / unit["root"]
    root, names = (project_dir, unit["manifests"]) if "manifests" in unit else (here, _manifests(here))
    read = rx.python_manifests(root, names)
    gaps = [{"kind": "manifest_unread", "path": name,
             "detail": "the environment reads pyproject.toml, uv.lock and requirements*.txt: the packages this "
                       "file declares are not installed"} for name in names if name not in read]
    try:
        used = rx.python_environment(root, names, stated and str(stated["version"]))
        try:
            failed = json.loads((Path(used) / "daodan-environment.json").read_text(encoding="utf-8"))["failed"]
        except (OSError, TypeError, ValueError, KeyError):
            failed = []
        gaps += [{"kind": "restore_failed", "manager": "uv", "path": unit["root"] or ".", "package": item["requirement"],
                  "detail": f"{item['requirement']} is not installed: {item['cause']}"} for item in failed]
        return used, gaps, stated if used else None
    except (OSError, subprocess.SubprocessError) as error:
        return None, gaps + [{"kind": "restore_failed", "manager": "uv", "path": unit["root"] or ".",
                              "detail": str(error)[:600]}], None


def _version(environment: Path | None) -> str | None:
    """The version of an environment's interpreter, as its `pyvenv.cfg` records it (uv and virtualenv write
    `version_info`, venv `version`)."""
    try:
        text = (Path(environment) / "pyvenv.cfg").read_text(encoding="utf-8")
    except (OSError, TypeError):
        return None
    found = re.search(r"^version(?:_info)?\s*=\s*(\S+)", text, re.M)
    return found.group(1) if found else None


def _facts(environment: Path | None, packages: list[dict], config: dict | None, project: tuple[str, str],
           stated: dict | None = None) -> dict:
    """What one run read: its project's name and version, environment and its Python (`python`; the statement
    that chose it, `python_request`), declared requirements, packages and Pyright configuration."""
    listed = Path(environment) / "daodan-requirements.txt" if environment else None
    return {"project": list(project), "environment": str(environment) if environment else None,
            "python": _version(environment), **({"python_request": stated} if stated else {}),
            "requirements": listed.read_text(encoding="utf-8").splitlines() if listed and listed.is_file() else [],
            "packages": {package["name"]: package["version"] for package in packages}, "pyrightconfig": config}


def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: one run per outermost Python project, with its manifests, source
    roots and the Python its folder states first as uv reads it (`python`, `dynamic.python.stated_python`, of the
    statements at or above its folder and in its manifests)."""
    import premap
    from dynamic import python as observer  # it imports this module: imported here, once this one is loaded
    stated = [item for item in record.get("toolchains", []) if item.get("tool") == "python" and item.get("version")
              and item.get("declared_in")]
    units = []
    for unit in premap.python_runs(record):
        folder = unit["root"] or "."
        python = observer.stated_python([item for item in stated if observer._above(folder, item["declared_in"])
                                         or item["declared_in"].split("#", 1)[0] in unit["manifests"]], folder)
        units.append({**unit, **({"python": python} if python else {})})
    return {"units": units}


def tasks(configs) -> list[str]:
    """The folders of the Python projects the runs read (`configs` of the contract), for `missing`."""
    return list(configs or ())


def missing(index, rels: list[str], roots: list[str] | None = None) -> dict:
    """Why a Python file has no document: it lies outside every project the runs read (`roots`)."""
    if not roots or "" in roots:
        return {}
    return {rel: "outside every Python project the pre-map states" for rel in rels
            if not any(rel.startswith(f"{root}/") for root in roots)}


def _outcome(runs: list[dict], units: list[dict]) -> dict:
    """The runs' contract, with the gaps of their environments (`gaps`) and the folders they read (`configs`)."""
    from indexers import runtime
    gaps = [gap for run in runs for gap in run.pop("gaps")]
    return {**runtime.outcome("scip-python", VERSION, runs), "configs": [unit["root"] for unit in units],
            **({"gaps": gaps} if gaps else {})}


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, environment: Path | None = None,
          *, engine=None, units: list[dict] | None = None) -> dict:
    """The scip-python index of each Python project of `units` (`root`: its folder from the checkout's root, ''
    for the root; `name`, else the one its `pyproject.toml` declares, else its folder's; `manifests` and
    `source_roots` as the pre-map states them), the whole checkout when none is given (`files` is not needed:
    scip-python reads each project); with `environment`, else the one `python_environment` builds for each; in
    a container where scip-python cannot start, or with `engine`, a container engine; see the module's
    docstring. Each run holds its project's facts (`_facts`)."""
    import resolve_edges as rx
    from indexers import runtime
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    units = units or [{"root": ""}]
    if not RUNS_HERE or engine is not None:
        return _contained(project_dir, work_dir, environment, engine, units)
    tool = runtime.Tool(project_dir, "scip-python", VERSION)
    try:
        runtime.memory("scip-python", MIN_FREE)
        directory = runtime.node(project_dir)
        script = runtime.npm_package(project_dir, directory, "@sourcegraph/scip-python", VERSION)
        if environment is None:
            _uv()
    except runtime.Unavailable as error:
        return runtime.refused("scip-python", VERSION, error)
    runtime.clear(work_dir, "scip-python")
    runs = []
    with runtime.mirrored(tool, runtime.real([unit["root"] for unit in units], work_dir)) as mirror:
        for number, unit in enumerate(units):
            prefix = unit["root"]
            here, cwd = project_dir / prefix, mirror / prefix
            used, gaps, stated = _prepared(project_dir, unit, environment)
            packages = _packages(used)
            described = work_dir / f"scip-python-environment-{number}.json"
            described.write_text(json.dumps(packages), encoding="utf-8")
            name, version = _identity(here, unit.get("name"))
            output = work_dir / f"scip-python-{number}.scip"
            # Read from the project: the mirror only links its folders, and a walk does not enter a link.
            config = _pyright_config(here, cwd / "pyrightconfig.json", unit.get("source_roots") or (),
                                     unit.get("unit_roots") or ())
            if config:  # beside the index too, where `hops` reads the source roots
                (work_dir / f"pyrightconfig-{number}.json").write_text(json.dumps(config), encoding="utf-8")
            paths = [Path(used) / ("Scripts" if os.name == "nt" else "bin")] if used else []
            variables = {"VIRTUAL_ENV": str(used)} if used else {}
            env = runtime.environment(*paths, directory, NODE_OPTIONS="--max-old-space-size=4096", **variables)
            run = {"prefix": prefix, **code_graph.measured(
                [str(directory / rx.executable_name("node")), str(script), "index", ".", "--project-name", name,
                 "--project-version", version, "--output", str(output), "--environment", str(described)],
                str(cwd), env, 3000)}
            run["index"] = str(output) if output.is_file() and run["returncode"] == 0 else None
            run["index_bytes"] = output.stat().st_size if output.is_file() else 0
            if run["index"]:
                gaps += _unbound(project_dir, directory, cwd, used, env, output.with_suffix(".unbound.jsonl"), prefix)
            runs.append({**run, **_facts(used, packages, config, (name, version), stated), "gaps": gaps})
    return _outcome(runs, units)


def _unbound(project_dir: Path, directory: Path, cwd: Path, used: Path | None, env: dict, target: Path,
             prefix: str) -> list[dict]:
    """The checker's pass over the run's folder `cwd` (`python_unbound.py`), its lines written to `target`; a gap
    when it could not run, and the holes keep `no-occurrence`. It parses the project with the environment's
    interpreter, the project's Python, without `site` (`-I -S`): no package's code runs."""
    import resolve_edges as rx
    from indexers import runtime
    python = Path(used) / "bin" / "python" if used else None
    try:
        langserver = runtime.npm_package(project_dir, directory, "pyright", PYRIGHT).with_name("langserver.index.js")
        done = subprocess.run([str(python or sys.executable), "-I", "-S", str(UNBOUND),
                               str(directory / rx.executable_name("node")), str(langserver), str(cwd),
                               str(python or "-")], capture_output=True, text=True, timeout=1800, env=env)
    except (runtime.Unavailable, OSError, subprocess.SubprocessError) as error:
        return [{"kind": "checker_not_run", "path": prefix or ".",
                 "detail": f"Pyright {PYRIGHT}'s pass did not run ({error}): a member the index names nothing at "
                           "keeps no cause"}]
    target.write_text(done.stdout, encoding="utf-8")
    return [] if done.returncode == 0 else [{"kind": "checker_not_run", "path": prefix or ".",
                                            "detail": f"Pyright {PYRIGHT}'s pass ended with code {done.returncode}: "
                                                      f"{done.stderr.strip()[-300:]}"}]


def _contained(project_dir: Path, work_dir: Path, environment: Path | None, engine, units: list[dict]) -> dict:
    """scip-python in a container over the copy of the project, a run per Python project (`_boxed`)."""
    from indexers import runtime
    runtime.clear(work_dir, "scip-python")
    try:
        runs = [_boxed(project_dir, unit, number, work_dir, environment, engine)
                for number, unit in enumerate(units)]
    except runtime.Unavailable as error:
        return runtime.refused("scip-python", VERSION, error)
    return _outcome(runs, units)


def _boxed(project_dir: Path, unit: dict, number: int, work_dir: Path, environment: Path | None, engine) -> dict:
    """One project's run in a container (`IMAGE`, `BOX`), with what the copy carries prepared on the host only
    once an engine answers; Unavailable when none answers. The image's Python reads the copy: a Python the unit
    states that it is not is a gap."""
    import container
    from dynamic import python as observer  # it imports this module: imported here, once this one is loaded
    from indexers import runtime
    prefix = unit["root"]
    here = project_dir / prefix
    name, version = _identity(here, unit.get("name"))
    held: dict = {"environment": None, "packages": [], "config": None, "gaps": []}

    def inputs() -> dict[str, Path]:
        try:
            directory = runtime.node(project_dir)  # the host's, for npm
            script = runtime.npm_package(project_dir, directory, "@sourcegraph/scip-python", VERSION)
            archive = runtime.node_archive(project_dir, f"linux-{container.architecture()}")
            if environment is None:
                _uv()
        except runtime.Unavailable as error:
            raise container.Gap(error.reason, error.install) from error
        held["environment"], held["gaps"], _stated = _prepared(project_dir, unit, environment)
        held["packages"] = _packages(held["environment"])
        described = work_dir / f"scip-python-environment-{number}.json"
        described.write_text(json.dumps(held["packages"]), encoding="utf-8")
        home = runtime.Tool(project_dir, "scip-python", VERSION).home()
        located = work_dir / "scip-python.path"
        located.write_text(f"/daodan/scip-python/{script.relative_to(home).as_posix()}", encoding="utf-8")
        carried = {"/daodan/tools/node.tar.gz": archive, "/daodan/tools/environment.json": described,
                   "/daodan/tools/scip-python.path": located}
        configured = work_dir / f"pyrightconfig-{number}.json"
        held["config"] = _pyright_config(here, configured, unit.get("source_roots") or (),
                                         unit.get("unit_roots") or ())
        if held["config"]:
            carried["/daodan/tools/pyrightconfig.json"] = configured
        for path in (home / "node_modules").rglob("*"):
            if path.is_file():
                carried[f"/daodan/scip-python/{path.relative_to(home).as_posix()}"] = path
        for site in _sites(held["environment"]):
            for path in site.rglob("*"):
                if path.is_file() and "__pycache__" not in path.relative_to(site).parts:
                    carried[f"/daodan/env/{path.relative_to(site).as_posix()}"] = path
        try:  # the checker's pass, as on the host: without its Pyright the index still runs
            langserver = runtime.npm_package(project_dir, directory, "pyright", PYRIGHT).with_name(
                "langserver.index.js")
        except runtime.Unavailable as error:
            held["gaps"].append({"kind": "checker_not_run", "path": prefix or ".",
                                 "detail": f"Pyright {PYRIGHT}'s pass did not run ({error.reason}): a member the "
                                           "index names nothing at keeps no cause"})
            return carried
        checker = runtime.Tool(project_dir, "pyright", PYRIGHT).home()
        served = work_dir / "pyright.path"
        served.write_text(f"/daodan/pyright/{langserver.relative_to(checker).as_posix()}", encoding="utf-8")
        carried.update({"/daodan/tools/pyright.path": served, "/daodan/tools/python_unbound.py": UNBOUND})
        for path in (checker / "node_modules").rglob("*"):
            if path.is_file():
                carried[f"/daodan/pyright/{path.relative_to(checker).as_posix()}"] = path
        return carried

    out = work_dir / f"container-{number}"
    shutil.rmtree(out, ignore_errors=True)
    command = ["bash", "-c", BOX, "scip-python", name, version, prefix]
    result = container.run_in_container(project_dir, command, image=IMAGE, out_dir=out, outputs=[OUT],
                                        env={"HOME": "/root"}, timeout=3000, memory=CONTAINER_MEMORY, engine=engine,
                                        inputs=inputs)
    if result["state"] == "gap":
        cause = (f"scip-python {VERSION} does not start on Windows (it builds a regular expression from the path "
                 f"separator `\\`), so it runs in a container: {result['cause']}")
        raise runtime.Unavailable(cause, result["remedy"])
    log = out / "execute.log"
    text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    record = out / container.RECORD_NAME
    rows = [json.loads(line) for line in record.read_text(encoding="utf-8").splitlines()
            if line.strip()] if record.is_file() else []
    peak = re.findall(r"DAODAN_PEAK (\d+)", text)
    errors = [line[line.find(" ERROR ") + 7:][:200] for line in text.splitlines() if " ERROR " in line]
    output = work_dir / f"scip-python-{number}.scip"
    if (out / "out/index.scip").is_file():
        os.replace(out / "out/index.scip", output)
    if (out / "out/unbound.jsonl").is_file():  # beside its index, where `unanswered` reads it
        os.replace(out / "out/unbound.jsonl", output.with_suffix(".unbound.jsonl"))
    gaps = [{"kind": "checker_not_run", "path": prefix or ".",
             "detail": f"Pyright {PYRIGHT}'s pass ended with code {code} in the container: a member the index names "
                       "nothing at keeps no cause"} for code in re.findall(r"DAODAN_UNBOUND (\d+)", text)]
    ran = (re.findall(r"DAODAN_PYTHON (\S+)", text) or [None])[-1]
    stated, numbers = unit.get("python"), tuple(int(n) for n in re.findall(r"\d+", ran or "")[:3])
    if stated and numbers and observer.admits(str(stated["version"]), numbers) is False:
        gaps.append({"kind": "python_unavailable", "path": stated["declared_in"],
                     "detail": f"the project states Python {stated['version']} ({stated['declared_in']}) and the "
                               f"container reads it on the image's {ran}: the copy runs with no network to bring "
                               "another"})
    done = result["state"] == "done" and result.get("exit_code") == 0 and output.is_file()
    run = {"prefix": prefix, "command": command[:2] + ["BOX", *command[3:]], "returncode": result.get("exit_code"),
           "seconds": rows[-1].get("duration_seconds", 0) if rows else 0,
           "peak_mb": round(int(peak[-1]) / 2**20) if peak else None, "stdout_tail": "",
           "stderr_tail": "\n".join(part for part in (result.get("cause"), text[-2500:]) if part),
           "stderr_errors": len(errors), "stderr_error_examples": list(dict.fromkeys(errors))[:5],
           "image": IMAGE, "index": str(output) if done else None,
           "index_bytes": output.stat().st_size if output.is_file() else 0}
    return {**run, **_facts(held["environment"], held["packages"], held["config"], (name, version)), "python": ran,
            "gaps": [*held["gaps"], *(result.get("gaps") or ()), *gaps]}  # and what the copy left out
