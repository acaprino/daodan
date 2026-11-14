"""scip-python for Python: how it runs, and what its index leaves to the reader.

`index` runs scip-python (npm, without install scripts, on Daodan's Node) in a mirror of the project, with
the project's declared packages in the engine pass's environment (`python_environment`: wheels only) described
to it as an environment file, so it never asks pip. A `src` layout is not found unless Pyright is told: without
it no absolute import of the project's own package resolves. The mirror gets a `pyrightconfig.json` with `src`
as a root and an extra path when `src` holds a package and the project declares no Pyright configuration. No
project code runs. The project's version is `_` in every run: it is part of each project symbol, so node ids
stay the same from one snapshot to the next.

Where scip-python cannot start (Windows: `RUNS_HERE`), it runs in a container (`container.run_in_container`,
`IMAGE`) over the copy of the project, with no network: the copy carries Node for Linux, checked like the
host's, scip-python as npm installed it on the host, and the site-packages of the host's environment, which the
image's Python adds to its path. Without a container engine Python is `unavailable`, and nothing is downloaded.

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
from pathlib import Path

import code_graph

VERSION = "0.6.8"  # @sourcegraph/scip-python on npm
MIN_FREE = 512 * 2**20  # 369 MB peak on python-semver (benchmarks/inference-audit, 13 November 2026)
SRC_LAYOUT = {"executionEnvironments": [{"root": "src"}, {"root": ".", "extraPaths": ["src"]}]}
# scip-python builds `new RegExp(path.sep, 'g')` when it loads (`PythonEnvironment.ts`): with Windows' `\` it
# stops there, before reading anything (0.6.8, 14 November 2026).
RUNS_HERE = os.sep == "/"
IMAGE = "python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90"  # 3.13.18
CONTAINER_MEMORY = 2 * 2**30
OUT = "/daodan/out"
# The container's script: $1 the project's name, $2 its version. The image's Python adds the host environment's
# site-packages (`/daodan/env`), where Pyright asks it for its search paths.
BOX = r'''set -u
mkdir -p /daodan/node /daodan/out || exit 70
tar -xzf /daodan/tools/node.tar.gz -C /daodan/node --strip-components=1 || exit 70
site=$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])') || exit 70
echo "import site; site.addsitedir('/daodan/env')" > "$site/daodan-env.pth" || exit 70
cd /work || exit 70
if [ -f /daodan/tools/pyrightconfig.json ] && [ ! -e pyrightconfig.json ]; then
  cp /daodan/tools/pyrightconfig.json . || exit 70
fi
NODE_OPTIONS=--max-old-space-size=1536 /daodan/node/bin/node "$(cat /daodan/tools/scip-python.path)" index . \
  --project-name "$1" --project-version "$2" --output /daodan/out/index.scip --environment /daodan/tools/environment.json
code=$?
echo "DAODAN_PEAK $(cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo -)"
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


def hops(index) -> dict:
    """Hops `{key: [(target key, tag)]}` for what scip-python leaves implicit; see the module's docstring."""
    import builtins
    out = collections.defaultdict(list)
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
    """The project's files that may declare packages, for `python_environment` to choose from."""
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


def _identity(project: Path) -> tuple[str, str]:
    """The project's declared name (else its directory's) and its version, always `_` (see the module's
    docstring; scip-python stops on an undefined one, `normalizeNameOrVersion`)."""
    import tomllib
    name = project.name
    if (project / "pyproject.toml").is_file():
        try:
            name = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8")).get("project", {}).get(
                "name", name)
        except (OSError, ValueError):
            pass
    return name, "_"


def _pyright_config(root: Path, target: Path) -> dict | None:
    """The `src` layout declared to Pyright in `target`, unless the project at `root` configures Pyright."""
    if (root / "pyrightconfig.json").exists():
        return None
    pyproject = root / "pyproject.toml"
    if pyproject.is_file() and "[tool.pyright]" in pyproject.read_text(encoding="utf-8"):
        return None
    if not any((root / "src").glob("*/__init__.py")):
        return None
    target.write_text(json.dumps(SRC_LAYOUT, indent=1), encoding="utf-8")
    return SRC_LAYOUT


def _prepared(project_dir: Path, environment: Path | None) -> Path | None:
    """`environment`, else the one `python_environment` builds from the project's declared packages."""
    import resolve_edges as rx
    if environment is not None:
        return Path(environment)
    try:
        return rx.python_environment(project_dir, _manifests(project_dir))
    except (OSError, subprocess.SubprocessError) as error:
        print(f"the project's Python packages were not installed: {error}", flush=True)
        return None


def _contract(runs: list[dict], environment: Path | None, packages: list[dict], config: dict | None,
              project: tuple[str, str]) -> dict:
    from indexers import runtime
    listed = Path(environment) / "daodan-requirements.txt" if environment else None
    return {**runtime.outcome("scip-python", VERSION, runs), "environment": str(environment) if environment else None,
            "requirements": listed.read_text(encoding="utf-8").splitlines() if listed and listed.is_file() else [],
            "packages": {package["name"]: package["version"] for package in packages}, "pyrightconfig": config,
            "project": list(project)}


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, environment: Path | None = None,
          *, engine=None) -> dict:
    """The scip-python index of the whole of `project_dir` (`files` is not needed: scip-python reads the
    project), with `environment`, else the one `python_environment` builds; in a container where scip-python
    cannot start, or with `engine`, a container engine; see the module's docstring."""
    import resolve_edges as rx
    from indexers import runtime
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    if not RUNS_HERE or engine is not None:
        return _contained(project_dir, work_dir, environment, engine)
    tool = runtime.Tool(project_dir, "scip-python", VERSION)
    try:
        runtime.memory("scip-python", MIN_FREE)
        directory = runtime.node(project_dir)
        script = runtime.npm_package(project_dir, directory, "@sourcegraph/scip-python", VERSION)
    except runtime.Unavailable as error:
        return runtime.refused("scip-python", VERSION, error)
    environment = _prepared(project_dir, environment)
    packages = _packages(environment)
    described = work_dir / "scip-python-environment.json"
    described.write_text(json.dumps(packages), encoding="utf-8")
    name, version = _identity(project_dir)
    output = work_dir / "scip-python-0.scip"
    runtime.clear(work_dir, "scip-python")
    paths = [Path(environment) / ("Scripts" if os.name == "nt" else "bin")] if environment else []
    variables = {"VIRTUAL_ENV": str(environment)} if environment else {}
    env = runtime.environment(*paths, directory, NODE_OPTIONS="--max-old-space-size=4096", **variables)
    with runtime.mirrored(tool) as mirror:
        config = _pyright_config(mirror, mirror / "pyrightconfig.json")
        run = {"prefix": "", **code_graph.measured(
            [str(directory / rx.executable_name("node")), str(script), "index", ".", "--project-name", name,
             "--project-version", version, "--output", str(output), "--environment", str(described)],
            str(mirror), env, 3000)}
    run["index"] = str(output) if output.is_file() and run["returncode"] == 0 else None
    run["index_bytes"] = output.stat().st_size if output.is_file() else 0
    return _contract([run], environment, packages, config, (name, version))


def _contained(project_dir: Path, work_dir: Path, environment: Path | None, engine) -> dict:
    """scip-python in a container over the copy of the project (`IMAGE`, `BOX`), with what the copy carries
    prepared on the host only once an engine answers."""
    import container
    from indexers import runtime
    name, version = _identity(project_dir)
    held: dict = {"environment": None, "packages": [], "config": None}

    def inputs() -> dict[str, Path]:
        try:
            directory = runtime.node(project_dir)  # the host's, for npm
            script = runtime.npm_package(project_dir, directory, "@sourcegraph/scip-python", VERSION)
            archive = runtime.node_archive(project_dir, f"linux-{container.architecture()}")
        except runtime.Unavailable as error:
            raise container.Gap(error.reason, error.install) from error
        held["environment"] = _prepared(project_dir, environment)
        held["packages"] = _packages(held["environment"])
        described = work_dir / "scip-python-environment.json"
        described.write_text(json.dumps(held["packages"]), encoding="utf-8")
        home = runtime.Tool(project_dir, "scip-python", VERSION).home()
        located = work_dir / "scip-python.path"
        located.write_text(f"/daodan/scip-python/{script.relative_to(home).as_posix()}", encoding="utf-8")
        carried = {"/daodan/tools/node.tar.gz": archive, "/daodan/tools/environment.json": described,
                   "/daodan/tools/scip-python.path": located}
        held["config"] = _pyright_config(project_dir, work_dir / "pyrightconfig.json")
        if held["config"]:
            carried["/daodan/tools/pyrightconfig.json"] = work_dir / "pyrightconfig.json"
        for path in (home / "node_modules").rglob("*"):
            if path.is_file():
                carried[f"/daodan/scip-python/{path.relative_to(home).as_posix()}"] = path
        for site in _sites(held["environment"]):
            for path in site.rglob("*"):
                if path.is_file() and "__pycache__" not in path.relative_to(site).parts:
                    carried[f"/daodan/env/{path.relative_to(site).as_posix()}"] = path
        return carried

    out = work_dir / "container"
    shutil.rmtree(out, ignore_errors=True)
    command = ["bash", "-c", BOX, "scip-python", name, version]
    result = container.run_in_container(project_dir, command, image=IMAGE, out_dir=out, outputs=[OUT],
                                        env={"HOME": "/root"}, timeout=3000, memory=CONTAINER_MEMORY, engine=engine,
                                        inputs=inputs)
    if result["state"] == "gap":
        cause = (f"scip-python {VERSION} does not start on Windows (it builds a regular expression from the path "
                 f"separator `\\`), so it runs in a container: {result['cause']}")
        return runtime.refused("scip-python", VERSION, runtime.Unavailable(cause, result["remedy"]))
    log = out / "execute.log"
    text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    record = out / container.RECORD_NAME
    rows = [json.loads(line) for line in record.read_text(encoding="utf-8").splitlines()
            if line.strip()] if record.is_file() else []
    peak = re.findall(r"DAODAN_PEAK (\d+)", text)
    errors = [line[line.find(" ERROR ") + 7:][:200] for line in text.splitlines() if " ERROR " in line]
    runtime.clear(work_dir, "scip-python")
    output = work_dir / "scip-python-0.scip"
    if (out / "out/index.scip").is_file():
        os.replace(out / "out/index.scip", output)
    done = result["state"] == "done" and result.get("exit_code") == 0 and output.is_file()
    run = {"prefix": "", "command": command[:2] + ["BOX", *command[3:]], "returncode": result.get("exit_code"),
           "seconds": rows[-1].get("duration_seconds", 0) if rows else 0,
           "peak_mb": round(int(peak[-1]) / 2**20) if peak else None, "stdout_tail": "",
           "stderr_tail": "\n".join(part for part in (result.get("cause"), text[-2500:]) if part),
           "stderr_errors": len(errors), "stderr_error_examples": list(dict.fromkeys(errors))[:5],
           "image": IMAGE, "index": str(output) if done else None,
           "index_bytes": output.stat().st_size if output.is_file() else 0}
    return _contract([run], held["environment"], held["packages"], held["config"], (name, version))
