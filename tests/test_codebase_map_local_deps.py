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

import preparation  # noqa: E402
from premap import requirements  # noqa: E402

FIXTURES = Path(__file__).with_name("fixtures") / "premap"
CASE = json.loads((FIXTURES / "projects.json").read_text(encoding="utf-8"))["local_deps"]
RUNS = json.loads((FIXTURES / "outputs" / "local_deps.json").read_text(encoding="utf-8"))["runs"]
REFUSED = {  # the declaring file -> its local dependencies outside the copy or absolute (decision of the owner)
    "npm/package.json": {"dependencies.out: file:../../outside/out", "dependencies.abs: file:/srv/abs/npm"},
    "npm/package-lock.json": {"packages.node_modules/out: ../../outside/out",
                              "packages.node_modules/abs: ../../srv/abs/npm"},
    "pnpm/package.json": {"dependencies.out: link:../../outside/out",
                          "dependencies.file-out: file:../../outside/file-out"},
    "pnpm/pnpm-lock.yaml": {"importers...dependencies.file-out: file:../../outside/file-out",
                            "importers...dependencies.out: link:../../outside/out",
                            "packages.file-out@file:../../outside/file-out"},
    "yarn1/package.json": {"dependencies.out: file:../../outside/out"},
    "berry/package.json": {"dependencies.out: portal:../../outside/out", "dependencies.abs: link:/srv/abs/berry"},
    "py-req/requirements.txt": {"../../outside/pkg", "/srv/abs/pkg", "file:../../outside/file.tar.gz"},
    "py-uv/pyproject.toml": {"outside", "absolute"},
    "py-uv/uv.lock": {"absolute: directory = /srv/abs/pkg", "outside: directory = ../../outside/pkg"},
    "py-poetry/pyproject.toml": {"outside"},
    "py-poetry/poetry.lock": {"outside: file = ../../outside/out.tar.gz"},
}


def _answer(argv0: str, cwd: str, *words: str) -> dict:
    return next(run["result"] for run in RUNS if run["command"]["argv"][:len(words) + 1] == [argv0, *words]
                and run["command"]["cwd"] == cwd)


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    for rel, text in CASE.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8", newline="\n")
    return project


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


# ------------------------------------------------------------ T3.A.8b: the refusal

def test_only_local_dependencies_outside_the_copy_or_absolute_are_refused(tmp_path):
    """Decision of the owner: a workspace or a member inside the copy (`packages/in`, `../shared/sib` from `npm/`,
    `./inside`, `../shared-py`) stays; one outside the copy or at an absolute path is a `local_dependency_refused`
    gap naming the file and the entry."""
    project = _project(tmp_path)
    files = sorted(CASE)

    def read(rel):
        return (project / rel).read_text(encoding="utf-8")

    gaps = [*preparation.local_dependencies(files, read, "node"), *preparation.local_dependencies(files, read, "python")]
    assert {gap["kind"] for gap in gaps} == {"local_dependency_refused"}
    found: dict[str, set] = {}
    for gap in gaps:
        found.setdefault(gap["file"], set()).add(gap["entry"])
        assert gap["path"] == gap["file"].rsplit("/", 1)[0] and gap["file"] in gap["detail"]
    assert found == REFUSED


def test_a_node_restore_with_a_local_dependency_outside_the_copy_does_not_run(tmp_path):
    """`node_prepare` launches no restore of a folder whose files state a local dependency outside the copy; the
    same folders with their dependencies inside the copy restore."""
    project = _project(tmp_path)
    files = sorted(CASE)

    def read(rel):
        return (project / rel).read_text(encoding="utf-8")

    planned = preparation.node_prepare(files, read)
    assert planned["restores"] == {"npm": ["shared/sib"]} and len(planned["lines"]) == 1  # a package of its own
    assert {gap["path"] for gap in planned["gaps"] if gap["kind"] == "local_dependency_refused"} == {
        "npm", "pnpm", "yarn1", "berry"}
    assert not [gap for gap in planned["gaps"] if gap["kind"] == "restore_failed"]
    inside = {rel: text for rel, text in CASE.items() if rel.startswith(("npm/packages", "shared/"))}
    inside["npm/package.json"] = json.dumps({"name": "npm-app", "dependencies": {
        "in": "file:packages/in", "sib": "file:../shared/sib"}})
    inside["npm/package-lock.json"] = json.dumps({"lockfileVersion": 3, "packages": {
        "": {"dependencies": {"in": "file:packages/in", "sib": "file:../shared/sib"}},
        "node_modules/in": {"resolved": "packages/in", "link": True},
        "node_modules/sib": {"resolved": "../shared/sib", "link": True}}})
    planned = preparation.node_prepare(sorted(inside), inside.get)
    assert planned["restores"] == {"npm": ["npm", "shared/sib"]}
    assert not [gap for gap in planned["gaps"] if gap["kind"] == "local_dependency_refused"]


def test_a_python_restore_with_a_local_dependency_outside_the_copy_does_not_run(tmp_path):
    """`python_restores` keeps the folders of the Python managers less those refused: here all but the package of
    its own `shared-py`, and with the outside requirements gone the pip folder restores."""
    project = _project(tmp_path)
    files = sorted(CASE)

    def read(rel):
        return (project / rel).read_text(encoding="utf-8")

    planned = preparation.python_restores(files, read)
    assert planned["restores"] == {"pip": ["shared-py"]}
    assert {gap["path"] for gap in planned["gaps"]} == {"py-req", "py-uv", "py-poetry"}
    inside = {"py-req/requirements.txt": "-e ./inside\n../shared-py\nrequests==2.32.3\n",
              "py-req/inside/pyproject.toml": CASE["py-req/inside/pyproject.toml"],
              "shared-py/pyproject.toml": CASE["shared-py/pyproject.toml"]}
    planned = preparation.python_restores(sorted(inside), inside.get)
    assert planned["gaps"] == [] and "py-req" in {f for folders in planned["restores"].values() for f in folders}


def test_a_git_or_url_address_is_no_local_dependency():
    """A `git+` or URL address is approved by its host (T0.C), never refused here."""
    texts = {"requirements.txt": "x @ git+https://github.com/acme/x\nhttps://files.example.org/y-1.0.tar.gz\n",
             "package.json": json.dumps({"dependencies": {"z": "git+https://github.com/acme/z.git",
                                                          "w": "https://example.org/w.tgz"}})}
    assert preparation.local_dependencies(sorted(texts), texts.get, "python") == []
    assert preparation.local_dependencies(sorted(texts), texts.get, "node") == []
