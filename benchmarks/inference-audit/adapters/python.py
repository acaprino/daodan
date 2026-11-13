"""scip-python for Python: how the indexer runs and what its index leaves to the reader.

`index` installs scip-python when missing, installs the project's declared dependencies in a virtual
environment and indexes a copy of the checkout. `hops` reads, from `scip_graph.Index`, what scip-python leaves
implicit; each hop carries its own tag:
- `import-binding`: an imported name (`from m import a`, `a as b`) is a `local` the index defines nowhere, with
  no tie to `m`; it leads to the module occurrence of the same one-line statement;
- `builtin`: a builtin function (`isinstance`, `len`) is such a `local` too, while a builtin class has its
  `builtins/` symbol; an unbound bare name the interpreter's `builtins` holds, neither an attribute nor a
  keyword argument's name, leads to that module's symbol, in the package the index gives `builtins`;
- `classmethod-cls`: the first parameter of a method decorated `classmethod` (the decorator lies in the
  method's enclosing range) leads to the method's class;
- `type-of-self`: a local assigned `type(<first parameter of a method>)` leads to the method's class.
A `src` layout is not found unless Pyright is told: without it no absolute import of the project's own package
resolves. The copy gets a `pyrightconfig.json` with `src` as a root and an extra path when `src` holds a
package and the project declares no Pyright configuration.
"""
from __future__ import annotations

import collections
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scip_graph  # noqa: E402

VERSION = "0.6.8"  # @sourcegraph/scip-python on npm, released 2026-10-22
NODE = ("v22.23.4", "1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce")
LAUNCHER = "/opt/node/bin/scip-python"
APT = ("git", "curl", "ca-certificates", "xz-utils")
SRC_LAYOUT = {"executionEnvironments": [{"root": "src"}, {"root": ".", "extraPaths": ["src"]}]}


def install_commands() -> list[str]:
    """Node at its pinned release, then scip-python from npm without install scripts."""
    version, sha = NODE
    archive = f"node-{version}-linux-x64.tar.xz"
    return [f"curl -fsSL https://nodejs.org/dist/{version}/{archive} -o /tmp/{archive}",
            f"echo '{sha}  /tmp/{archive}' | sha256sum -c -",
            f"mkdir -p /opt/node && tar -xJf /tmp/{archive} -C /opt/node --strip-components=1 && rm /tmp/{archive}",
            f"PATH=/opt/node/bin:$PATH npm install -g --ignore-scripts --no-audit --no-fund "
            f"@sourcegraph/scip-python@{VERSION}"]


def requirements(project: Path) -> list[str]:
    """What the project declares it needs: dependencies, optional ones, dependency groups, requirements files."""
    import tomllib
    out = []
    pyproject = project / "pyproject.toml"
    if pyproject.is_file():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        declared = data.get("project", {})
        out += declared.get("dependencies", [])
        for group in (*declared.get("optional-dependencies", {}).values(), *data.get("dependency-groups", {}).values()):
            out += [item for item in group if isinstance(item, str)]  # `{include-group = ...}` names another group
    for path in sorted(project.glob("requirements*.txt")):
        out += [line.split("#", 1)[0].strip() for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith(("#", "-"))]
    return list(dict.fromkeys(out))


def _identity(project: Path) -> tuple[str, str]:
    """The project's declared name (else its directory's) and its commit (else `_`): scip-python stops on an
    undefined project version (`normalizeNameOrVersion`)."""
    import tomllib
    name = project.resolve().name
    if (project / "pyproject.toml").is_file():
        name = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8")).get("project", {}).get(
            "name", name)
    commit = subprocess.run(["git", "-C", str(project), "rev-parse", "--short=12", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    return name, commit or "_"


def _pyright_config(mirror: Path) -> dict | None:
    """The `src` layout declared to Pyright, unless the project configures Pyright itself."""
    if (mirror / "pyrightconfig.json").exists():
        return None
    pyproject = mirror / "pyproject.toml"
    if pyproject.is_file() and "[tool.pyright]" in pyproject.read_text(encoding="utf-8"):
        return None
    if not any((mirror / "src").glob("*/__init__.py")):
        return None
    (mirror / "pyrightconfig.json").write_text(json.dumps(SRC_LAYOUT, indent=1), encoding="utf-8")
    return SRC_LAYOUT


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    """The scip-python index of a copy of `project_dir`, with the project's dependencies installed.

    The dependencies go into `work_dir/venv`, one installer call for all of them, then one per package when
    that call fails, so one package that does not install leaves the others.
    """
    if not Path(LAUNCHER).is_file():
        for command in install_commands():
            subprocess.run(command, shell=True, check=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    mirror = work_dir / "mirror"
    shutil.copytree(project_dir, mirror, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    venv = work_dir / "venv"
    subprocess.run(["uv", "venv", "--seed", "--python", sys.executable, str(venv)], check=True, capture_output=True)
    python = str(venv / "bin/python")
    wanted, installs = requirements(mirror), []
    if wanted:
        done = subprocess.run(["uv", "pip", "install", "--python", python, *wanted], capture_output=True, text=True)
        installs.append({"packages": "all", "returncode": done.returncode, "stderr_tail": done.stderr[-800:]})
        if done.returncode:
            for package in wanted:
                one = subprocess.run(["uv", "pip", "install", "--python", python, package], capture_output=True,
                                     text=True)
                installs.append({"packages": package, "returncode": one.returncode})
    listed = subprocess.run([python, "-m", "pip", "list", "--format=json"], capture_output=True, text=True)
    environment = {row["name"]: row["version"] for row in json.loads(listed.stdout or "[]")}
    config = _pyright_config(mirror)
    env = dict(os.environ, PATH=f"{venv}/bin:/opt/node/bin:" + os.environ["PATH"], VIRTUAL_ENV=str(venv),
               NODE_OPTIONS="--max-old-space-size=4096")
    output = work_dir / "scip-python-0.scip"
    name, version = _identity(project_dir)
    run = {"prefix": "", **scip_graph.measured(
        [LAUNCHER, "index", ".", "--project-name", name, "--project-version", version, "--output", str(output)],
        str(mirror), env, 3000)}
    run["index"] = str(output) if output.is_file() and run["returncode"] == 0 else None
    run["index_bytes"] = output.stat().st_size if output.is_file() else 0
    return {"indexes": [[run["index"], ""]] if run["index"] else [], "runs": [run],
            "indexer": {"name": "scip-python", "version": VERSION, "seconds": run["seconds"], "peak_mb": run["peak_mb"]},
            "requirements": wanted, "installs": installs, "environment": environment, "pyrightconfig": config,
            "project": [name, version]}


ASSIGNED_TYPE = re.compile(r"^\s*(\w+)\s*=\s*type\(\s*(\w+)\s*\)\s*(#.*)?$")
FROM_IMPORT = re.compile(r"^\s*from\s+\S+\s+import\s+[^()]+$")
METHOD = re.compile(r"#[^#/().]+\(\)\.$")


def _text(index, rel: str, occurrence) -> tuple[str, str]:
    """(the line an occurrence starts on, the source text of its range on that line)."""
    line = index.line(rel, occurrence.line) or ""
    begin = index.to_bytes(rel, occurrence.line, occurrence.start)
    stop = index.to_bytes(rel, occurrence.line, occurrence.end) if occurrence.end_line == occurrence.line else None
    data = line.encode("utf-8")
    return line, data[begin:stop].decode("utf-8", errors="replace") if begin is not None else ""


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
