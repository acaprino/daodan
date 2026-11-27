"""Local dependencies: which official reader states each one (T3.A.7) and the refusal of those outside the copy (T3.A.8b).

The case `local_deps` of `tests/fixtures/premap/projects.json` holds, per format, a local dependency inside the copy of
the project and one outside it or at an absolute path: `file:` in `package-lock.json`, `link:`/`file:` in
`pnpm-lock.yaml`, `file:` in a Yarn 1 `yarn.lock`, `portal:`/`link:` in a Berry one, `-e`, bare paths and `file:` in
`requirements.txt`, `editable`/`directory` in `uv.lock`, `directory`/`file` and `develop` in `poetry.lock`. What
Renovate 44.239.1, `npm query :link` and `uv export --format pylock.toml` answered on it in a Linux container is in
`tests/fixtures/premap/outputs/local_deps.json` (`benchmarks/project-model/modal_premap.py --store local_deps`).
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tomllib

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

from premap import requirements  # noqa: E402

FIXTURES = Path(__file__).with_name("fixtures") / "premap"
CASE = json.loads((FIXTURES / "projects.json").read_text(encoding="utf-8"))["local_deps"]
RUNS = json.loads((FIXTURES / "outputs" / "local_deps.json").read_text(encoding="utf-8"))["runs"]


def _answer(argv0: str, cwd: str, *words: str) -> dict:
    return next(run["result"] for run in RUNS if run["command"]["argv"][:len(words) + 1] == [argv0, *words]
                and run["command"]["cwd"] == cwd)


# ------------------------------------------------------------ T3.A.7: what each reader states

def test_renovate_names_each_local_dependency_but_states_the_path_of_the_node_ones_only():
    """Renovate's extraction (`skipReason`): `file:` is `file`, `link:` and `portal:` are `unspecified-version` (the
    reason of any spec it cannot version), uv's and Poetry's `path` sources are `path-dependency` without the path, and
    a requirements file's `-e` and paths are left out: it cannot decide inside or outside alone."""
    report = json.loads(_answer("renovate", ".", "--platform=local")["stdout"])
    files = {f["packageFile"]: f for files in report["repositories"]["local"]["packageFiles"].values() for f in files}
    skipped = {(rel, dep["depName"]): (dep.get("skipReason"), dep.get("currentValue"))
               for rel, f in files.items() for dep in f["deps"] if dep.get("skipReason")}
    assert skipped[("npm/package.json", "out")] == ("file", "file:../../outside/out")
    assert skipped[("pnpm/package.json", "out")] == ("unspecified-version", "link:../../outside/out")
    assert skipped[("berry/package.json", "in")] == ("unspecified-version", "portal:./in")
    assert skipped[("py-uv/pyproject.toml", "outside")] == ("path-dependency", None)
    assert skipped[("py-poetry/pyproject.toml", "outside")] == ("path-dependency", None)
    assert [dep["depName"] for dep in files["py-req/requirements.txt"]["deps"]] == ["requests"]


def test_npm_query_link_and_uv_export_state_the_paths_of_their_lockfiles():
    """npm's own `npm query :link --package-lock-only` (Arborist) gives each linked package's location from the
    lockfile; `uv export --format pylock.toml` each local package's directory and whether it is editable."""
    linked = {node["name"]: node["location"] for node in json.loads(_answer("npm", "npm", "query", ":link")["stdout"])}
    assert linked == {"in": "packages/in", "sib": "../shared/sib", "out": "../../outside/out", "abs": "../../srv/abs/npm"}
    for folder in ("pnpm", "yarn1", "berry"):  # no package-lock.json: npm reads nothing there
        assert _answer("npm", folder, "query", ":link")["returncode"] != 0
    exported = tomllib.loads(_answer("uv", "py-uv", "export")["stdout"])
    assert {p["name"]: p["directory"] for p in exported["packages"]} == {
        "absolute": {"path": "/srv/abs/pkg", "editable": False}, "inside": {"path": "inside", "editable": True},
        "outside": {"path": "../../outside/pkg", "editable": False}}


def test_pip_s_parser_states_every_local_requirement_with_its_path():
    """pip's own parser (`pip-requirements-parser`): `-e PATH`, a bare path and a `file:` URL, each with the path pip
    installs; a pinned requirement is none."""
    stated = requirements.read(CASE["py-req/requirements.txt"]).requirements
    assert [(req.line, req.link and req.link.url) for req in stated] == [
        ("-e ./inside", "./inside"), ("../shared-py", "../shared-py"), ("../../outside/pkg", "../../outside/pkg"),
        ("/srv/abs/pkg", "/srv/abs/pkg"), ("file:../../outside/file.tar.gz", "../../outside/file.tar.gz"),
        ("requests==2.32.3", None)]
