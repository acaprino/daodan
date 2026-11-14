"""scip-python for Python: how the indexer runs. What its index leaves to the reader is the plugin's
`indexers/python.py`.

`index` installs scip-python when missing, installs the project's declared dependencies in a virtual
environment and indexes a copy of the checkout. A `src` layout is not found unless Pyright is told: without it
no absolute import of the project's own package resolves. The copy gets a `pyrightconfig.json` with `src` as a
root and an extra path when `src` holds a package and the project declares no Pyright configuration.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph  # noqa: E402

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
    run = {"prefix": "", **code_graph.measured(
        [LAUNCHER, "index", ".", "--project-name", name, "--project-version", version, "--output", str(output)],
        str(mirror), env, 3000)}
    run["index"] = str(output) if output.is_file() and run["returncode"] == 0 else None
    run["index_bytes"] = output.stat().st_size if output.is_file() else 0
    return {"indexes": [[run["index"], ""]] if run["index"] else [], "runs": [run],
            "indexer": {"name": "scip-python", "version": VERSION, "seconds": run["seconds"], "peak_mb": run["peak_mb"]},
            "requirements": wanted, "installs": installs, "environment": environment, "pyrightconfig": config,
            "project": [name, version]}
