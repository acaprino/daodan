"""scip-typescript and scip-python take the project's structure from the pre-map and state what they could not
do: the aliases, workspace members, source roots and manifests the pre-map names reach the tools' own
configuration, and an install or an environment that fails is a gap of the analyzer's contract. Programs and
URLs are the fakes of `test_codebase_map_indexers`.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

import test_codebase_map_indexers as base
from test_codebase_map_indexers import FIXTURES, Box, _environment, _node_release, _project, _tools
import engine_tools  # noqa: E402
import resolve_edges as rx  # noqa: E402
from indexers import python, typescript  # noqa: E402

sandbox = base.sandbox  # the fixture, for this module's tests
ALIASED = {"extends": "../../tsconfig.base.json", "compilerOptions": {"paths": {"@/*": ["./src/*"]}}}

# A workspace of two packages that share an alias, one reaching the other by name, and a package outside it.
MONOREPO = {
    "package.json": {"name": "root", "private": True, "workspaces": ["packages/*"]},
    "tsconfig.base.json": {"compilerOptions": {"strict": True}},
    "packages/ui/package.json": {"name": "@acme/ui"},
    "packages/ui/tsconfig.json": ALIASED,
    "packages/ui/src/index.ts": "export const b = 1;\n",
    "packages/web/package.json": {"name": "@acme/web", "dependencies": {
        "@acme/ui": "workspace:*", "left": "link:../../vendor/left", "react": "18.3.1"}},
    "packages/web/tsconfig.json": ALIASED,
    "packages/web/src/main.ts": 'import { b } from "@acme/ui";\nimport { x } from "@/x";\nexport const y = b + x;\n',
    "packages/web/src/x.ts": "export const x = 1;\n",
    "tools/gen/package.json": {"name": "gen", "dependencies": {"chalk": "5.3.0"}},
    "tools/gen/run.js": "console.log(1);\n",
}
# What the pre-map states of it (`premap/npm.py`, `premap/tsc.py`): each alias's targets from the project's root.
RECORD = {
    "units": [
        {"kind": "npm-package", "name": "gen", "root": "tools/gen"},
        {"kind": "npm-package", "name": "@acme/web", "root": "packages/web", "depends_on": ["@acme/ui"],
         "config": {"tsconfig": ["packages/web/tsconfig.json"],
                    "paths": {"@/*": ["packages/web/src/*"], "~lib": ["packages/web/lib/index.ts"]}}},
        {"kind": "npm-package", "name": "@acme/ui", "root": "packages/ui",
         "config": {"tsconfig": ["packages/ui/tsconfig.json"], "paths": {"@/*": ["packages/ui/src/*"]}}},
        {"kind": "npm-package", "name": "root", "root": ".", "config": {"tsconfig": ["tsconfig.base.json"]}}],
    "workspace": [{"tool": "npm", "root": ".", "members": ["packages/ui", "packages/web"]}],
}


def _written(root: Path, files: dict) -> Path:
    for rel, content in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
    return root


# ------------------------------------------------------------ TypeScript

def test_typescript_takes_the_tsconfig_the_aliases_and_the_reachable_packages_from_the_pre_map():
    assert typescript.structure(RECORD) == {
        "roots": {"", "packages/ui", "packages/web", "tools/gen"},
        "tsconfig": "tsconfig.base.json",  # the root unit's first
        "paths": [["packages/ui", {"@/*": ["packages/ui/src/*"]}],
                  ["packages/web", {"@/*": ["packages/web/src/*"], "~lib": ["packages/web/lib/index.ts"]}]],
        "members": {"@acme/ui": "packages/ui", "@acme/web": "packages/web"}}  # `gen`: no member, nobody's dependency
    # Without a root unit that states one, only a single unit's tsconfig can be the one a program extends.
    nested = [unit for unit in RECORD["units"] if unit["root"] != "."]
    assert "tsconfig" not in typescript.structure({"units": nested})
    assert typescript.structure({"units": nested[1:2]})["tsconfig"] == "packages/web/tsconfig.json"
    # A package another unit depends on (a `file:` link) is reachable by its name without a workspace.
    linked = [{"kind": "npm-package", "name": "app", "root": "app", "depends_on": ["lib"]},
              {"kind": "npm-package", "name": "lib", "root": "vendor/lib"}]
    assert typescript.structure({"units": linked}) == {"roots": {"app", "vendor/lib"}, "members": {"lib": "vendor/lib"}}
    assert typescript.structure({"units": [{"kind": "npm-package", "root": "web"}]}) == {"roots": {"web"}}


def test_the_generated_tsconfig_carries_the_aliases_from_the_mirror(tmp_path):
    aliases, gaps = typescript._aliases(typescript.structure(RECORD)["paths"], {"@acme/ui": "packages/ui"})
    assert aliases == {"@/*": ["packages/ui/src/*", "packages/web/src/*"], "~lib": ["packages/web/lib/index.ts"],
                       "@acme/ui": ["packages/ui"], "@acme/ui/*": ["packages/ui/*"]}
    assert [(gap["kind"], gap["alias"], gap["paths"]) for gap in gaps] == [
        ("alias_ambiguous", "@/*", ["packages/ui", "packages/web"])]
    typescript._tsconfig(tmp_path, ["a.ts"], None, aliases)
    written = json.loads((tmp_path / "tsconfig.json").read_text(encoding="utf-8"))["compilerOptions"]["paths"]
    # Absolute: an inherited `baseUrl` would move a relative target.
    assert written == {key: [(tmp_path / target).as_posix() for target in targets] for key, targets in aliases.items()}
    (tmp_path / "plain").mkdir()
    typescript._tsconfig(tmp_path / "plain", ["a.ts"])
    assert "paths" not in json.loads((tmp_path / "plain/tsconfig.json").read_text(encoding="utf-8"))["compilerOptions"]


def test_a_workspace_resolves_its_members_by_alias_and_states_what_no_install_holds(sandbox):
    project = _written(sandbox["root"] / "project" / "mono", MONOREPO)
    _tools(project, "ts")
    sandbox["fake"].index = FIXTURES / "ts/index.scip"
    seen = {}
    real = typescript._tsconfig

    def spy(mirror, *rest):
        extends = real(mirror, *rest)
        seen.update(mirror=Path(mirror), config=json.loads((mirror / "tsconfig.json").read_text(encoding="utf-8")))
        return extends

    sandbox["monkeypatch"].setattr(typescript, "_tsconfig", spy)
    result = typescript.index(project, sandbox["root"] / "work", **typescript.structure(RECORD))
    assert "state" not in result, result.get("reason")
    mirror, config = seen["mirror"], seen["config"]
    assert config["extends"] == "./tsconfig.base.json" == result["tsconfig_extends"]
    paths = config["compilerOptions"]["paths"]
    assert paths["@acme/ui"] == [(mirror / "packages/ui").as_posix()]
    assert paths["@acme/ui/*"] == [(mirror / "packages/ui/*").as_posix()]
    assert paths["@/*"] == [(mirror / "packages/ui/src/*").as_posix(), (mirror / "packages/web/src/*").as_posix()]
    gaps = {(gap["kind"], gap.get("path") or gap.get("alias")): gap for gap in result["gaps"]}
    # `@acme/ui` (workspace:) is left out of the install and resolved by its alias: no gap. `left` is a gap.
    assert sorted(gaps) == [("alias_ambiguous", "@/*"), ("dependency_not_installed", "packages/web/package.json"),
                            ("restore_failed", "tools/gen")]
    assert "left" in gaps["dependency_not_installed", "packages/web/package.json"]["detail"]
    assert gaps["restore_failed", "tools/gen"]["manager"] == "npm"


def test_an_install_that_fails_is_a_gap_with_npms_error(sandbox):
    project = _project(sandbox, "ts")
    _tools(project, "ts")
    shutil.rmtree(rx.shared_cache_dir() / "npm" / rx.npm_key(project))
    sandbox["fake"].index = FIXTURES / "ts/index.scip"
    fake = sandbox["fake"]

    def run(command, *args, **kwargs):
        command = [str(part) for part in command]
        if command[1:2] in (["install"], ["ci"]) and "--prefix" not in command:
            return subprocess.CompletedProcess(command, 1, "", "npm error 404 no-such-package")
        return fake(command, *args, **kwargs)

    sandbox["monkeypatch"].setattr(subprocess, "run", run)
    result = typescript.index(project, sandbox["root"] / "work", roots={""})
    assert "state" not in result, result.get("reason")
    assert result["node_modules"] == {"": None}
    assert result["gaps"] == [{"kind": "restore_failed", "manager": "npm", "path": ".",
                               "detail": "npm error 404 no-such-package"}]


def test_the_local_packages_an_install_leaves_out_are_named(tmp_path):
    project = _written(tmp_path, MONOREPO)
    assert engine_tools.npm_local_packages(project) == [
        ("packages/web/package.json", "@acme/ui", "workspace:*"),
        ("packages/web/package.json", "left", "link:../../vendor/left")]
    rewritten = json.loads(engine_tools._without_local_packages(project / "packages/web/package.json"))
    assert rewritten["dependencies"] == {"react": "18.3.1"}
    assert engine_tools._without_local_packages(project / "packages/ui/package.json") is None


# ---------------------------------------------------------------- Python

def test_the_declared_source_roots_are_told_to_pyright(tmp_path):
    target = tmp_path / "written.json"
    assert python._pyright_config(tmp_path, target, ["python"]) == {
        "executionEnvironments": [{"root": "python"}, {"root": ".", "extraPaths": ["python"]}]}
    assert json.loads(target.read_text(encoding="utf-8"))["executionEnvironments"][0] == {"root": "python"}
    # Two roots import each other's packages; the project's own folder ('.') needs no telling.
    assert python._pyright_config(tmp_path, target, [".", "lib", "tools/probe/src"]) == {"executionEnvironments": [
        {"root": "lib", "extraPaths": ["tools/probe/src"]}, {"root": "tools/probe/src", "extraPaths": ["lib"]},
        {"root": ".", "extraPaths": ["lib", "tools/probe/src"]}]}
    # The project's own Pyright configuration stays.
    (tmp_path / "pyrightconfig.json").write_text("{}", encoding="utf-8")
    assert python._pyright_config(tmp_path, tmp_path / "other.json", ["python"]) is None


@pytest.mark.parametrize("contained", [False, True])
def test_python_takes_its_runs_roots_and_manifests_and_states_what_its_environment_lacks(sandbox, contained):
    project = _written(sandbox["root"] / "project" / "py", {
        "svc/pyproject.toml": '[project]\nname = "svc"\n', "svc/setup.py": "from setuptools import setup\nsetup()\n",
        "svc/lib/app/__init__.py": "", "tools/x.py": "print(1)\n"})
    _tools(project, "python")
    units = [{"root": "svc", "name": "svc", "manifests": ["svc/pyproject.toml", "svc/setup.py"],
              "source_roots": ["lib"]}]
    asked = []

    def environment(root, names):
        asked.append((Path(root), list(names)))
        raise OSError("no room for the environment")

    sandbox["monkeypatch"].setattr(rx, "python_environment", environment)
    if contained:
        import container
        sandbox["web"].pages.update(_node_release(platform=f"linux-{container.architecture()}"))
        sandbox["monkeypatch"].setattr(python, "RUNS_HERE", False)
        sandbox["monkeypatch"].setattr(container, "run_in_container", Box(FIXTURES / "python/index.scip"))
    else:
        sandbox["fake"].index = FIXTURES / "python/index.scip"
    result = python.index(project, sandbox["root"] / "work", units=units)
    assert "state" not in result, result.get("reason")
    # The manifests are the pre-map's, from the checkout's root: the adapter walks for none.
    assert asked == [(project.resolve(), ["svc/pyproject.toml", "svc/setup.py"])]
    [run] = result["runs"]
    assert run["pyrightconfig"] == {"executionEnvironments": [{"root": "lib"}, {"root": ".", "extraPaths": ["lib"]}]}
    assert "gaps" not in run
    assert [(gap["kind"], gap["path"]) for gap in result["gaps"]] == [("manifest_unread", "svc/setup.py"),
                                                                     ("restore_failed", "svc")]
    assert result["gaps"][1]["manager"] == "uv" and "no room for the environment" in result["gaps"][1]["detail"]
    # The folders the runs read reach `missing` the way the stage hands them (`tasks`).
    roots = python.tasks(result["configs"])
    assert python.missing(None, ["svc/lib/app/late.py", "tools/x.py"], roots) == {
        "tools/x.py": "outside every Python project the pre-map states"}


def test_a_run_of_the_whole_checkout_leaves_no_python_file_outside(sandbox):
    project = _project(sandbox, "python")
    _tools(project, "python")
    sandbox["fake"].index = FIXTURES / "python/index.scip"
    result = python.index(project, sandbox["root"] / "work", environment=_environment(sandbox["root"]))
    assert result["configs"] == [""] and "gaps" not in result
    assert python.missing(None, ["tools/x.py"], python.tasks(result["configs"])) == {}
    assert python.missing(None, ["tools/x.py"]) == {}
