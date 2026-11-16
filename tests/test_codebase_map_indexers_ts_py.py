"""scip-typescript and scip-python take the project's structure from the pre-map and state what they could not
do: the aliases, workspace members, source roots and manifests the pre-map names reach the tools' own
configuration, and a restore or an environment that fails is a gap of the analyzer's contract. scip-typescript
runs only in a container, after the project's own restore: `Container` stands in for the container operation,
so each test reads the two scripts it was sent and plays their logs. Programs and URLs are the fakes of
`test_codebase_map_indexers`.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import test_codebase_map_indexers as base
from test_codebase_map_indexers import FIXTURES, Box, _environment, _node_release, _project, _tools
import code_graph  # noqa: E402
import container  # noqa: E402
import preparation  # noqa: E402
import resolve_edges as rx  # noqa: E402
from indexers import python, typescript  # noqa: E402

sandbox = base.sandbox  # the fixture, for this module's tests
T, IN = preparation.T, preparation.IN
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

class Container:
    """`container.run_in_container`: with `gap`, no engine answers; else it asks for the inputs, as a run does
    once an engine answers, and plays the two phases: each one's log, exit code (`codes`; None: cut off) and record
    row, and `index` brought back when the execution exits with 0, with the checker's `unbound` lines when given."""

    def __init__(self, index: Path | None = None, gap: tuple[str, str] | None = None, prepare: str = "",
                 execute: str = "", codes: tuple = (0, 0), unbound: str | None = None):
        self.index, self.gap, self.logs, self.codes, self.asked = index, gap, (prepare, execute), codes, []
        self.unbound = unbound

    def __call__(self, project, command, **options):
        self.asked.append({"project": Path(project), "command": command, **options})
        if self.gap:
            return {"state": "gap", "cause": self.gap[0], "remedy": self.gap[1], "outputs": []}
        self.asked[-1]["inputs"] = options["inputs"]()
        out = Path(options["out_dir"])
        out.mkdir(parents=True, exist_ok=True)
        rows, result = [], {"state": "failed", "exit_code": None, "outputs": [], "engine": "test"}
        for phase, text, code, seconds, peak in zip(("prepare", "execute"), self.logs, self.codes, (40.0, 12.5),
                                                    (300, 900)):
            (out / f"{phase}.log").write_text(f"{text}DAODAN_PEAK {peak * 2**20}\n", encoding="utf-8")
            rows.append({"phase": phase, "exit_code": code, "duration_seconds": seconds,
                         "outcome": "timeout" if code is None else "exited"})
            if phase == "prepare" and code != 0:
                result["cause"] = f"preparation {rows[-1]['outcome']}; see {out / 'prepare.log'}"
                break
        else:
            result.update(state="done" if self.codes[1] is not None else "timeout", exit_code=self.codes[1])
            if self.index is not None and self.codes[1] == 0:
                (out / "out").mkdir()
                shutil.copyfile(self.index, out / "out/index.scip")
                result["outputs"] = ["out/index.scip"]
                if self.unbound is not None:
                    (out / "out/unbound.jsonl").write_text(self.unbound, encoding="utf-8")
                    result["outputs"].append("out/unbound.jsonl")
        (out / container.RECORD_NAME).write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return result


def _contained(sandbox, **played) -> Container:
    """The container operation and the preparation's downloads as fakes; `sandbox["fetched"]` names the downloads."""
    box, sandbox["fetched"] = Container(**played), []

    def fetched(url, digest, name):
        sandbox["fetched"].append(name)
        return sandbox["root"] / "fetched" / name

    sandbox["monkeypatch"].setattr(container, "run_in_container", box)
    sandbox["monkeypatch"].setattr(preparation, "fetched", fetched)
    return box


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
    # The Node the pre-map states is the analyzer's toolchain; another tool's is not.
    stated = [{"tool": "node", "version": "20.11.1", "declared_in": ".nvmrc"},
              {"tool": "pnpm", "version": "9.12.2", "declared_in": "package.json#packageManager"},
              {"tool": "go", "version": "1.22", "declared_in": "go.mod"}]
    assert typescript.structure({"units": [], "toolchains": stated}) == {"roots": set(), "toolchains": stated[:1]}
    assert typescript.NEEDS_CONTAINER is True


def test_the_generated_tsconfig_carries_the_aliases_from_the_copys_root(tmp_path):
    aliases, gaps = typescript._aliases(typescript.structure(RECORD)["paths"], {"@acme/ui": "packages/ui"})
    assert aliases == {"@/*": ["packages/ui/src/*", "packages/web/src/*"], "~lib": ["packages/web/lib/index.ts"],
                       "@acme/ui": ["packages/ui"], "@acme/ui/*": ["packages/ui/*"]}
    assert [(gap["kind"], gap["alias"], gap["paths"]) for gap in gaps] == [
        ("alias_ambiguous", "@/*", ["packages/ui", "packages/web"])]
    target = tmp_path / "generated.json"
    typescript._tsconfig(tmp_path, target, ["a.ts"], None, aliases)
    written = json.loads(target.read_text(encoding="utf-8"))["compilerOptions"]["paths"]
    # Absolute, under the copy: an inherited `baseUrl` would move a relative target.
    assert written == {key: [f"/work/{name}" for name in targets] for key, targets in aliases.items()}
    assert sorted(path.name for path in tmp_path.iterdir()) == ["generated.json"]  # nothing beside it
    # The file that names the type packages the preparation added (`typescript_types.py`), when it is there.
    assert json.loads(target.read_text(encoding="utf-8"))["include"] == ["a.ts", typescript.REFERENCES]
    typescript._tsconfig(tmp_path, target, ["a.ts"])
    assert "paths" not in json.loads(target.read_text(encoding="utf-8"))["compilerOptions"]


def test_the_packages_are_restored_the_projects_own_way_and_the_index_follows_in_the_same_container(sandbox):
    project = _written(sandbox["root"] / "project" / "mono", {**MONOREPO, "pnpm-lock.yaml": "lockfileVersion: 9\n"})
    unbound = '["packages/web/src/main.ts", 3, 20, "index", "NodeJS.ProcessEnv"]\n'
    box = _contained(sandbox, index=FIXTURES / "ts/index.scip", unbound=unbound)
    before, engine, work = base._hashes(project), object(), sandbox["root"] / "work"
    result = typescript.index(project, work, engine=engine, **typescript.structure(RECORD))
    assert "state" not in result, result.get("reason")
    # Nothing ran or was written on the host: the restore and the indexer are the container's.
    assert base._hashes(project) == before and sandbox["fake"].calls == [] and sandbox["web"].asked == []
    [asked] = box.asked
    assert asked["project"] == project.resolve() and asked["engine"] is engine
    assert (asked["image"], asked["outputs"], asked["memory"]) == (typescript.IMAGE, [typescript.OUT],
                                                                 typescript.MIN_FREE)
    assert asked["registries"] == preparation.NODE_REGISTRIES  # npm's only: no stated Node, no Yarn
    assert asked["env"]["PATH"] == preparation.PATH and asked["env"]["HOME"] == preparation.ENV["HOME"]
    (shell, flag, prepare), (_shell, _flag, execute) = asked["prepare"], asked["command"]
    assert (shell, flag) == ("bash", "-c")
    # The preparation, with the registries: Daodan's Node, the indexer without its install scripts, then the
    # workspace's own restore from its root, with the lifecycle scripts where a framework generates its files.
    lines = prepare.splitlines()
    assert preparation.setup(["node"])["lines"][0] in lines
    assert any(f"npm install -g --prefix {T}/npm --ignore-scripts" in line
               and f"@sourcegraph/scip-typescript@{typescript.VERSION}" in line for line in lines)
    assert f"{preparation.COREPACK_INSTALL}; " + preparation.restore("pnpm", ["."], scripts=True) in lines
    assert "mise" not in prepare and "npm ci" not in prepare
    # The execution, without network: the generated tsconfig takes the place of the project's, then the indexer
    # runs on Daodan's Node and its index goes where the outputs come back from.
    assert "mv tsconfig.json tsconfig.project.json" in execute and f"cp {typescript.CONFIG} tsconfig.json" in execute
    assert (f'{T}/node/bin/node "$(readlink -f {T}/npm/bin/scip-typescript)" index --cwd /work'
            f" --output {typescript.OUT}/index.scip --no-progress-bar") in execute
    # After the index, the checker's pass over the same program: the members it binds no declaration to, and why;
    # the run's exit code stays the indexer's.
    assert (f'{T}/node/bin/node {typescript.UNBOUND} /work "$(readlink -f {T}/npm/bin/scip-typescript)"'
            f" > {typescript.OUT}/unbound.jsonl") in execute and execute.rstrip().endswith('exit "$indexed"')
    assert "install" not in execute
    inputs = asked["inputs"]
    assert set(inputs) == {f"{IN}/node.tar.gz", typescript.CONFIG, typescript.TYPES, typescript.UNBOUND}
    assert Path(inputs[typescript.UNBOUND]) == Path(typescript.__file__).with_name("typescript_unbound.js")
    assert sandbox["fetched"] == ["node.tar.gz"]
    config = json.loads(Path(inputs[typescript.CONFIG]).read_text(encoding="utf-8"))
    assert config["extends"] == "./tsconfig.base.json" == result["tsconfig_extends"]
    paths = config["compilerOptions"]["paths"]
    assert paths["@acme/ui"] == ["/work/packages/ui"] and paths["@acme/ui/*"] == ["/work/packages/ui/*"]
    assert paths["@/*"] == ["/work/packages/ui/src/*", "/work/packages/web/src/*"]
    assert "packages/web/src/main.ts" in config["include"] and "tools/gen/run.js" in config["include"]
    # The contract: the index, a run per phase, the restores, and what no restore serves.
    assert result["indexes"] == [[str(work / "scip-typescript-0.scip"), ""]]
    assert (work / "scip-typescript-0.scip").read_bytes() == (FIXTURES / "ts/index.scip").read_bytes()
    assert (work / "scip-typescript-0.unbound.jsonl").read_text(encoding="utf-8") == unbound  # beside its index
    assert [(run["phase"], run["returncode"], run["seconds"], run["peak_mb"]) for run in result["runs"]] == [
        ("prepare", 0, 40.0, 300), ("execute", 0, 12.5, 900)]
    assert result["indexer"] == {"name": "scip-typescript", "version": typescript.VERSION, "seconds": 52.5,
                                 "peak_mb": 900, "types": []}  # the preparation added no type package
    assert result["restores"] == {"pnpm": ["."]}
    gaps = {(gap["kind"], gap.get("path") or gap.get("alias")): gap for gap in result["gaps"]}
    # `@acme/ui` (workspace:) and `left` (link:) are the manager's to install; `tools/gen` is no member.
    assert sorted(gaps) == [("alias_ambiguous", "@/*"), ("restore_failed", "tools/gen")]
    assert gaps["restore_failed", "tools/gen"]["manager"] == "pnpm"
    assert "no workspace" in gaps["restore_failed", "tools/gen"]["detail"]


def test_the_index_the_container_brings_back_feeds_the_graph(sandbox):
    project = _project(sandbox, "ts")
    box = _contained(sandbox, index=FIXTURES / "ts/index.scip")
    result = typescript.index(project, sandbox["root"] / "work", roots={""})
    assert "state" not in result, result.get("reason")
    assert result["restores"] == {"npm": ["."]}
    assert preparation.restore("npm", ["."], scripts=True) in box.asked[0]["prepare"][2]
    assert result["tsconfig_extends"] == "./tsconfig.project.json"  # the project's own, renamed in the copy
    assert "gaps" not in result
    languages = ("javascript", "typescript")
    built = base._graphs(project, result["indexes"], languages, result["indexer"])
    expected = base._graphs(project, [(FIXTURES / "ts/index.scip", "")], languages, result["indexer"])
    for language in languages:
        assert built[language]["edges"] == expected[language]["edges"]
        assert built[language]["files"] == expected[language]["files"]
        assert built[language]["indexer"]["name"] == "scip-typescript"
    assert any(built[language]["edges"] for language in languages)


FOLDERS = ["api/package-lock.json", "api/package.json", "cli/package.json", "site/package.json", "site/yarn.lock",
           "web/package.json"]


def test_a_folder_without_a_lockfile_restores_with_the_manager_its_manifest_names():
    named = {"web": "pnpm", "api": "yarn", "cli": "npm"}  # `api` has npm's lockfile: the lockfile names the manager
    assert preparation.node_restores(FOLDERS, named) == [
        ("npm", ["api", "cli"], False), ("pnpm", ["web"], True), ("yarn", ["site"], False)]
    assert preparation.node_restores(FOLDERS) == [("npm", ["api", "cli", "web"], False), ("yarn", ["site"], False)]
    assert preparation.node_restores(["pom.xml", "go.mod", "svc/pyproject.toml"]) == []
    # Without a lockfile the manager resolves; with one, the recorded line, which fails where it is out of date.
    assert "corepack pnpm install --no-frozen-lockfile --ignore-scripts" in preparation.restore("pnpm", ["web"], True)
    assert "--frozen-lockfile --ignore-scripts" in preparation.restore("pnpm", ["web"])
    assert "--immutable" not in preparation.restore("yarn", ["site"], True)
    assert "--mode=skip-build" in preparation.restore("yarn", ["site"], True)
    assert preparation.restore("npm", ["api"], False) == preparation.restore("npm", ["api"])


def _folders(root: Path) -> Path:
    """`FOLDERS` on disk: `web` names pnpm and `api` Yarn in their manifests (`packageManager`, corepack's field)."""
    named = {"web": "pnpm@9.12.2", "api": "yarn@4.5.0"}
    manifests = {rel: {"name": rel.split("/")[0], **({"packageManager": named[rel.split("/")[0]]}
                                                    if rel.split("/")[0] in named else {})}
                 for rel in FOLDERS if rel.endswith("package.json")}
    return _written(root, {**dict.fromkeys(FOLDERS, ""), **manifests,
                           "web/tsconfig.app.json": {"compilerOptions": {"strict": True}},
                           "web/src/a.ts": "export const a = 1;\n"})


def test_the_node_preparation_restores_each_folder_with_its_manager_and_its_lifecycle_scripts(tmp_path):
    project = _folders(tmp_path)
    plan = preparation.node_prepare(FOLDERS, lambda rel: (project / rel).read_text(encoding="utf-8"))
    assert plan["restores"] == {"npm": ["api", "cli"], "pnpm": ["web"], "yarn": ["site"]}
    # Each line is whole on its own: pnpm and Yarn install the corepack they run, Yarn takes the proxy from its own
    # settings, set in its line.
    corepack, yarn = f"{preparation.COREPACK_INSTALL}; ", f"{preparation.YARN_PROXY}; "
    assert plan["lines"] == [preparation.restore("npm", ["api", "cli"], scripts=True),
                             corepack + preparation.restore("pnpm", ["web"], True, scripts=True),
                             corepack + yarn + preparation.restore("yarn", ["site"], scripts=True)]
    assert plan["hosts"] == ("repo.yarnpkg.com",)  # where corepack takes Yarn 2 and later
    assert preparation.node_prepare(["go.mod"], None) == {"restores": {}, "lines": [], "gaps": [], "hosts": ()}
    # A manifest that is not JSON names no manager: npm.
    assert preparation.node_prepare(["package.json"], lambda rel: "{ not json")["restores"] == {"npm": ["."]}


def test_a_package_folder_that_declares_dependencies_no_restore_installs_is_a_gap():
    """A folder whose manifest declares dependencies is restored, or is a member its restore's workspaces name (the
    manifest's `workspaces`, a `pnpm-workspace.yaml`), or is a gap: never silence."""
    manifests = {
        "package.json": {"name": "root", "workspaces": {"packages": ["packages/*", "!packages/legacy"]}},
        "pnpm-workspace.yaml": "packages:\n  - 'apps/**'\n  - \"libs/core\"  # the core\n\ncatalog:\n  ms: ^2\n",
        "pnpm-lock.yaml": "",
        "packages/ui/package.json": {"dependencies": {"ms": "2.1.3"}},
        "packages/legacy/package.json": {"dependencies": {"ms": "2.1.3"}},
        "packages/ui/deep/package.json": {"devDependencies": {"ms": "2.1.3"}},
        "apps/web/site/package.json": {"dependencies": {"ms": "2.1.3"}},
        "libs/core/package.json": {"optionalDependencies": {"ms": "2.1.3"}},
        "libs/other/package.json": {"dependencies": {"ms": "2.1.3"}},
        "libs/bare/package.json": {"name": "bare"},
        "own/package.json": {"dependencies": {"ms": "2.1.3"}}, "own/yarn.lock": "",
    }
    plan = preparation.node_prepare(list(manifests), lambda rel: manifests[rel] if isinstance(manifests[rel], str)
                                    else json.dumps(manifests[rel]))
    assert plan["restores"] == {"pnpm": ["."], "yarn": ["own"]}
    assert [(gap["kind"], gap["manager"], gap["path"]) for gap in plan["gaps"]] == [
        ("restore_failed", "pnpm", "libs/other"), ("restore_failed", "pnpm", "packages/legacy"),
        ("restore_failed", "pnpm", "packages/ui/deep")]
    assert "no workspace above names this folder" in plan["gaps"][0]["detail"]


SVELTEKIT = Path(__file__).resolve().parents[1] / "benchmarks/project-model/fixtures/js-sveltekit"


def test_a_package_with_only_its_manifest_is_installed_by_npm_with_its_lifecycle_scripts(sandbox):
    """js-sveltekit: a package.json with devDependencies, no lockfile and no `packageManager`: npm, the default
    manager, resolves and installs there with the lifecycle scripts, where SvelteKit writes its tsconfig."""
    project = sandbox["root"] / "project" / "sveltekit"
    shutil.copytree(SVELTEKIT, project, ignore=shutil.ignore_patterns("expected.json"))
    units = json.loads((SVELTEKIT / "expected.json").read_text(encoding="utf-8"))["units"]
    box = _contained(sandbox, index=FIXTURES / "ts/index.scip")
    result = typescript.index(project, sandbox["root"] / "work", **typescript.structure({"units": units}))
    assert "state" not in result and "gaps" not in result
    assert result["restores"] == {"npm": ["."]}
    assert preparation.restore("npm", ["."], scripts=True) in box.asked[0]["prepare"][2].splitlines()


def _package(root: Path, rel: str, manifest: dict, *files: str) -> None:
    _written(root, {f"{rel}/package.json": manifest, **{f"{rel}/{name}": "" for name in files}})


def test_the_type_packages_are_nodes_and_those_of_the_declared_packages_that_ship_none(tmp_path):
    """`@types/node` unless the copy's root has it; then each package a root declares that is installed with no
    types of its own and no `@types` package within its reach; never one of the project's own packages."""
    from indexers import typescript_types
    work = tmp_path / "work"
    _written(work, {"package.json": {"dependencies": {
        "ms": "2", "clsx": "2", "vue": "3", "left": "link:./vendor/left", "@acme/ui": "workspace:*", "@scope/pkg": "1",
        "lodash": "4", "chalk": "5", "absent": "1", "@types/react": "18"}, "devDependencies": {"typed": "1", "ms": "2"}},
        "packages/app/package.json": {"dependencies": {"debug": "4", "member": "*"}},
        "packages/member/package.json": {"name": "member"}})
    _package(work, "node_modules/ms", {"main": "index.js"})
    _package(work, "node_modules/clsx", {"types": "clsx.d.ts"})
    _package(work, "node_modules/vue", {"exports": {".": {"types": "./dist/vue.d.ts", "import": "./index.mjs"}}})
    _package(work, "node_modules/@scope/pkg", {})
    _package(work, "node_modules/lodash", {})
    _package(work, "node_modules/@types/lodash", {})
    _package(work, "node_modules/chalk", {}, "index.d.ts")
    _package(work, "node_modules/typed", {"main": "lib/main.js"}, "lib/main.d.ts")
    _package(work, "packages/app/node_modules/debug", {})  # pnpm's layout: beside the package that declares it
    (work / "packages/app/node_modules/member").symlink_to(work / "packages/member", target_is_directory=True)
    assert typescript_types.wanted(str(work), "24", [".", "packages/app"]) == [
        "@types/node@24", "@types/scope__pkg", "@types/ms", "@types/debug"]
    _package(work, "node_modules/@types/node", {})  # the project's own
    assert "@types/node@24" not in typescript_types.wanted(str(work), "24", ["."])


NPM = """#!/bin/sh
while [ $# -gt 0 ]; do [ "$1" = --prefix ] && prefix=$2; p=$1; shift; done
case "$p" in
  @types/nope) echo "npm error code E404" >&2; exit 1;;
  @types/down) echo "npm error code ECONNRESET" >&2; exit 1;;
esac
n=$p; case "$n" in @*@*) n=${n%@*};; esac
mkdir -p "$prefix/node_modules/$n" && printf '{"version": "9.1.0"}' > "$prefix/node_modules/$n/package.json"
"""


def test_each_type_package_is_installed_apart_and_linked_where_typescript_looks_last(tmp_path, monkeypatch, capsys):
    """npm installs into the folder apart, never into the project's tree; one the registry lacks is no error, one
    it could not install is what the preparation could not install."""
    import os
    from indexers import typescript_types
    work, types, programs = tmp_path / "work", tmp_path / "types", tmp_path / "bin"
    _written(work, {"package.json": {"dependencies": {"ms": "2", "nope": "1", "down": "1"}}})
    for name in ("ms", "nope", "down"):
        _package(work, f"node_modules/{name}", {})
    _written(programs, {"npm": NPM})
    (programs / "npm").chmod(0o755)
    monkeypatch.setenv("PATH", f"{programs}{os.pathsep}{os.environ['PATH']}")
    assert typescript_types.main(["typescript_types.py", str(work), "24", str(types), "."]) == 0
    said = capsys.readouterr().err
    assert [line for line in said.splitlines() if line.startswith("DAODAN-")] == [
        "DAODAN-TYPES-ADDED @types/node@9.1.0", "DAODAN-MISSING @types/down@latest",
        "DAODAN-TYPES-ADDED @types/ms@9.1.0", "DAODAN-TYPES-ABSENT @types/nope"]
    assert "ECONNRESET" in said
    for name in ("node", "ms"):
        assert (work / "node_modules/@types" / name).resolve() == (types / "node_modules/@types" / name).resolve()
    assert sorted(path.name for path in (work / "node_modules/@types").iterdir()) == ["ms", "node"]
    assert [gap["tool"] for gap in preparation.missing(said)] == ["@types/down"]
    # TypeScript 6, scip-typescript's, loads no @types package unless named (`types` defaults to []): Node's own
    # API is named in a file the generated tsconfig includes, beside the project's `types`, never in their place.
    assert (types / "references.d.ts").read_text(encoding="utf-8") == '/// <reference types="node" />\n'
    (work / "node_modules/@types/node").unlink()  # the link
    (types / "references.d.ts").unlink()
    _written(programs, {"npm": "#!/bin/sh\necho 'npm error code ECONNRESET' >&2\nexit 1\n"})
    (programs / "npm").chmod(0o755)  # Node's types not installed: no reference to them
    typescript_types.main(["typescript_types.py", str(work), "24", str(types)])
    assert not (types / "references.d.ts").exists()


def test_a_restore_runs_the_lifecycle_scripts_first_and_falls_back_to_the_install_without_them():
    """The install's own lifecycle is where a framework generates what the compiler reads (a dependency's
    `postinstall`, the package's `postinstall` and `prepare`): project code, so for a container only. One that
    fails, or outlasts the limit, is said and costs the generation only: the folder is restored without scripts."""
    plain, line = preparation.restore("npm", ["a", "b"]), preparation.restore("npm", ["a", "b"], scripts=True)
    first = (f"timeout {preparation.LIMIT} sh -c 'if [ -f package-lock.json ] || [ -f npm-shrinkwrap.json ];"
             " then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi'")
    assert first in line and "DAODAN-GENERATE-FAILED npm %s" in line
    assert line.index(first) < line.index("DAODAN-GENERATE-FAILED") < line.index("npm ci --ignore-scripts")
    assert line.index("npm ci --ignore-scripts") < line.index("DAODAN-RESTORE-FAILED") and line.endswith("done; true")
    assert "timeout" not in plain and "GENERATE" not in plain  # the default is the line without project code
    assert "corepack pnpm install --frozen-lockfile'" in preparation.restore("pnpm", ["."], scripts=True)
    berry = preparation.restore("yarn", ["."], scripts=True)
    assert "corepack yarn install --immutable; else corepack yarn install --frozen-lockfile; fi'" in berry
    # A manager whose restore runs no project code has one line.
    assert preparation.restore("go", ["."], scripts=True) == preparation.restore("go", ["."])
    stderr = ("DAODAN-GENERATE-FAILED npm web/app\nnpm error code 1\nnpm error command sh -c svelte-kit sync\n"
              "DAODAN-GENERATE-END\nDAODAN-RESTORE-FAILED npm api\nnpm error code E404\nDAODAN-RESTORE-END\n")
    assert preparation.generation_gaps(stderr) == [{
        "kind": "generation_failed", "manager": "npm", "path": "web/app",
        "detail": "npm error code 1 | npm error command sh -c svelte-kit sync"}]
    assert [gap["path"] for gap in preparation.restore_gaps(stderr)] == ["api"]
    # An install that fails without its scripts too did not fail for them: one gap, the restore's.
    assert preparation.generation_gaps(stderr.replace("npm web/app", "npm api")) == []


def test_each_package_folder_restores_with_the_manager_its_lockfile_or_its_manifest_names(sandbox):
    """Without a root package.json each outermost package is restored where it starts, as the pre-map names it."""
    project = _folders(sandbox["root"] / "project" / "folders")
    box = _contained(sandbox, index=FIXTURES / "ts/index.scip")
    result = typescript.index(project, sandbox["root"] / "work", tsconfig="web/tsconfig.app.json",
                              roots={"api", "cli", "site", "web"})
    assert "state" not in result, result.get("reason")
    plan = preparation.node_prepare(FOLDERS, lambda rel: (project / rel).read_text(encoding="utf-8"))
    assert result["restores"] == plan["restores"] == {"npm": ["api", "cli"], "pnpm": ["web"], "yarn": ["site"]}
    assert result["tsconfig_extends"] == "./web/tsconfig.app.json" and "gaps" not in result
    lines = box.asked[0]["prepare"][2].splitlines()
    assert all(line in lines for line in plan["lines"])
    assert box.asked[0]["registries"] == (*preparation.NODE_REGISTRIES, "repo.yarnpkg.com")


def test_a_yarn_project_on_plug_n_play_is_laid_out_in_node_modules_for_the_index_and_says_so(sandbox):
    """D-157, measured on Modal with Yarn 4.9.1 and scip-typescript 0.6.2: under Plug'n'Play (Yarn 2 and later
    with no `nodeLinker`, or `pnp`) the install leaves .pnp.cjs and no node_modules, and scip-typescript names no
    symbol of a package (TypeScript's resolver does not read Plug'n'Play); with `nodeLinker: node-modules` it names
    `npm clsx 2.1.1`. So the index's restore lays the same lockfile out in node_modules (YARN_NODE_LINKER), in the
    container's copy only, and a `build_edited` gap says so. A folder that already says node-modules, and Yarn 1
    (no .yarnrc.yml), keep their restore as it is."""
    project = _written(sandbox["root"] / "project" / "pnp", {
        "package.json": {"name": "app", "packageManager": "yarn@4.9.1", "dependencies": {"clsx": "2.1.1"}},
        "yarn.lock": "", ".yarnrc.yml": "enableTelemetry: false\n", "src/a.ts": "import clsx from 'clsx';\n",
        "linked/package.json": {"name": "linked", "packageManager": "yarn@4.9.1"}, "linked/yarn.lock": "",
        "linked/.yarnrc.yml": "nodeLinker: node-modules\n"})
    box = _contained(sandbox, index=FIXTURES / "ts/index.scip")
    result = typescript.index(project, sandbox["root"] / "work", roots={"", "linked"})
    assert result["restores"] == {"yarn": [".", "linked"]}
    lines = box.asked[0]["prepare"][2]
    assert "export YARN_NODE_LINKER=node-modules" in lines
    assert lines.index("export YARN_NODE_LINKER=node-modules") < lines.index("corepack yarn install")
    assert [gap for gap in result.get("gaps", ()) if gap["kind"] == "build_edited"] == [{
        "kind": "build_edited", "path": ".", "detail": (
            "Yarn's Plug'n'Play (.yarnrc.yml sets no nodeLinker, or pnp): the index's restore lays the same lockfile "
            "out in node_modules (YARN_NODE_LINKER=node-modules) in the container's copy, as TypeScript's resolver "
            "reads no .pnp.cjs")}]


def test_the_project_runs_on_the_node_it_states_and_the_indexer_on_daodans(sandbox):
    project = _project(sandbox, "ts")
    box = _contained(sandbox, index=FIXTURES / "ts/index.scip")
    stated = [{"tool": "node", "version": "20.11.1", "declared_in": ".nvmrc"},
              {"tool": "node", "version": ">=18", "declared_in": "package.json#engines"}]
    result = typescript.index(project, sandbox["root"] / "work", roots={""}, toolchains=stated)
    assert "state" not in result and "gaps" not in result  # a range is no version to install: no gap, the pin
    chains = preparation.toolchains(stated[:1])
    asked = box.asked[0]
    prepare, lines = asked["prepare"][2], asked["prepare"][2].splitlines()
    assert all(line in lines for line in chains["lines"]) and "mise install node@20.11.1" in prepare
    # The indexer is installed before the project's Node is first on the path, and runs on Daodan's.
    assert prepare.index("@sourcegraph/scip-typescript@") < prepare.index("mise install node@20.11.1")
    assert prepare.index("mise install node@20.11.1") < prepare.index(preparation.restore("npm", ["."], scripts=True))
    assert f"{T}/node/bin/node " in asked["command"][2]
    assert asked["registries"] == (*preparation.NODE_REGISTRIES, *chains["hosts"])
    assert set(asked["inputs"]) == {f"{IN}/node.tar.gz", f"{IN}/mise", typescript.CONFIG, typescript.TYPES,
                                    typescript.UNBOUND}
    typescript.index(project, sandbox["root"] / "work", roots={""}, toolchains=stated[1:])
    assert "mise" not in box.asked[1]["prepare"][2] and f"{IN}/mise" not in box.asked[1]["inputs"]


def test_the_type_packages_follow_the_restore_and_the_prepare_run_lists_those_added(sandbox):
    """At the major of the Node the project states, else of Daodan's; the script travels with the copy."""
    project = _project(sandbox, "ts")
    log = ("DAODAN-TYPES-ADDED @types/node@20.19.2\nDAODAN-TYPES-ABSENT @types/nope\n"
           "DAODAN-TYPES-ADDED @types/ms@2.1.0\n")
    box = _contained(sandbox, index=FIXTURES / "ts/index.scip", prepare=log)
    result = typescript.index(project, sandbox["root"] / "work", roots={"", "web"},
                              toolchains=[{"tool": "node", "version": "v20.11.1", "declared_in": ".nvmrc"}])
    asked = box.asked[0]
    prepare, line = asked["prepare"][2], f"python3 {typescript.TYPES} /work 20 {typescript.TYPES_DIR} . web"
    assert line in prepare.splitlines()
    assert prepare.index(preparation.restore("npm", ["."], scripts=True)) < prepare.index(line)
    assert Path(asked["inputs"][typescript.TYPES]) == Path(typescript.__file__).with_name("typescript_types.py")
    # On the indexer's record, which the stage's report and each language's store entry carry.
    assert result["indexer"]["types"] == ["@types/node@20.19.2", "@types/ms@2.1.0"] and "gaps" not in result
    typescript.index(project, sandbox["root"] / "work", roots={""})
    major = preparation.NEEDS["node"]["version"].split(".")[0]
    assert f"python3 {typescript.TYPES} /work {major} {typescript.TYPES_DIR} ." in box.asked[1]["prepare"][2].splitlines()


def test_a_tsconfig_extending_a_file_no_install_step_generates_is_a_gap_that_names_the_cause(sandbox):
    """js-sveltekit: the root tsconfig extends `.svelte-kit/tsconfig.json`, which `svelte-kit sync` writes; no
    lifecycle script of the project runs it (it is only in `check`), so TypeScript cannot read the configuration."""
    project = sandbox["root"] / "project" / "sveltekit"
    shutil.copytree(SVELTEKIT, project, ignore=shutil.ignore_patterns("expected.json"))
    units = json.loads((SVELTEKIT / "expected.json").read_text(encoding="utf-8"))["units"]
    said = "error TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'.\n"
    _contained(sandbox, index=FIXTURES / "ts/index.scip", execute=said, codes=(0, 1))
    result = typescript.index(project, sandbox["root"] / "work", **typescript.structure({"units": units}))
    assert result["state"] == "failed" and "error TS5083" in result["reason"]
    assert result["gaps"] == [{
        "kind": "config_not_generated", "path": "tsconfig.json", "file": ".svelte-kit/tsconfig.json",
        "detail": "tsconfig.json extends .svelte-kit/tsconfig.json, a file the framework generates (`svelte-kit "
                  "sync`), which no install step of the project runs (no `prepare` script; it is only in `check`)"}]
    # Without a generator Daodan knows, the gap still names the file no install step wrote.
    (project / "tsconfig.json").write_text('{"extends": "./gen/base.json"}', encoding="utf-8")
    _contained(sandbox, execute=said.replace(".svelte-kit/tsconfig", "gen/base"), codes=(0, 1))
    result = typescript.index(project, sandbox["root"] / "work", **typescript.structure({"units": units}))
    assert [gap["detail"] for gap in result["gaps"]] == [
        "tsconfig.json extends gen/base.json, which the snapshot does not hold and no install step wrote"]


VUE = {"src/main.ts": 'import { createApp } from "vue";\nimport App from "@/App.vue";\n\ncreateApp(App).mount("#app");\n',
       "src/App.vue": "<template><p>x</p></template>\n"}


def test_a_name_an_untyped_module_binds_is_a_hole_with_the_cause(tmp_path):
    """js-vue-pnpm: no declaration of `*.vue` modules, so TypeScript types no import of a component; the index
    references the import's name as a local it defines nowhere. The hole says why, not `dangling-local`."""
    import test_codebase_map_code_graph as graphs
    _written(tmp_path, VUE)
    app, ref = "local 0", "local 1"
    index = graphs.load(tmp_path, graphs.document("src/main.ts", [
        graphs.occurrence(4, 10, 13, app), graphs.occurrence(4, 0, 9, "scip-typescript npm vue 3.5.12 createApp()."),
        graphs.occurrence(1, 9, 18, ref)]))
    _hops, traversal, _prepared = code_graph.adapter_traversal(typescript, index, graphs.Snapshot({}))
    assert [(end.cls, end.detail) for end in traversal.ends(f"src/main.ts#{app}")] == [
        ("dead-end", "no declaration of *.vue modules: the import is not typed")]
    # A local of a typed module, or of none, stays what the index makes of it.
    assert [end.detail for end in traversal.ends(f"src/main.ts#{ref}")] == ["dangling-local"]


CJS = {"src/index.js": 'const _ = require("lodash");\n\nmodule.exports = { first: (xs) => _.head(xs) };\n'}
REQUIRE = 'scip-typescript npm @types/node 24.10.1 `module.d.ts`/`"node:module"`/global/require.'


def test_the_module_of_a_commonjs_export_is_nodes_module_object(tmp_path):
    """js-npm-single, js-yarn-berry: in a JavaScript file TypeScript reads `module.exports = …` as the file's own
    export, and the index names its `module` with a local it defines nowhere, while `require` beside it resolves
    to the Node types. The read is of Node's module object, which those types declare with `require`: external,
    at their version. Without Node types in the index no package declares it: a hole that says so."""
    import test_codebase_map_code_graph as graphs
    _written(tmp_path, CJS)
    exported = "scip-typescript npm fx 1.0.0 src/`index.js`/"
    index = graphs.load(tmp_path, graphs.document("src/index.js", [
        graphs.occurrence(1, 10, 17, REQUIRE), graphs.occurrence(3, 0, 6, "local 3"),
        graphs.occurrence(3, 7, 14, exported)]))
    _hops, traversal, _prepared = code_graph.adapter_traversal(typescript, index, graphs.Snapshot({}))
    assert [(end.cls, end.detail) for end in traversal.ends("src/index.js#local 3")] == [
        ("external", "npm @types/node@24.10.1")]
    index = graphs.load(tmp_path, graphs.document("src/index.js", [graphs.occurrence(3, 0, 6, "local 3")]))
    _hops, traversal, _prepared = code_graph.adapter_traversal(typescript, index, graphs.Snapshot({}))
    assert [(end.cls, end.detail) for end in traversal.ends("src/index.js#local 3")] == [
        ("dead-end", "module.exports: the index names `module` with a local it defines nowhere, and references "
                     "no Node types that declare it")]
    # A `module` the file declares is the file's own: the index defines it, and the default rule holds.
    _written(tmp_path, {"src/index.js": "function f(module) {\n  module.exports = 1;\n}\n"})
    index = graphs.load(tmp_path, graphs.document("src/index.js", [
        graphs.occurrence(1, 11, 17, "local 0", True), graphs.occurrence(2, 2, 8, "local 0"),
        graphs.occurrence(1, 9, 10, REQUIRE)]))
    _hops, traversal, _prepared = code_graph.adapter_traversal(typescript, index, graphs.Snapshot({}))
    assert [end.cls for end in traversal.ends("src/index.js#local 0")] == ["project-value"]
    # tududi's backend/app.js: `require.main === module` reads the same object, wherever the file names it.
    _written(tmp_path, {"src/index.js": "if (require.main === module) {}\n"})
    index = graphs.load(tmp_path, graphs.document("src/index.js", [
        graphs.occurrence(1, 4, 11, REQUIRE), graphs.occurrence(1, 21, 27, "local 3")]))
    _hops, traversal, _prepared = code_graph.adapter_traversal(typescript, index, graphs.Snapshot({}))
    assert [(end.cls, end.detail) for end in traversal.ends("src/index.js#local 3")] == [
        ("external", "npm @types/node@24.10.1")]


def test_a_name_bound_to_a_member_the_index_names_nowhere_ends_at_its_own_definition(tmp_path):
    """tududi: `const { t } = useTranslation()`, `const { person: result } = await update()` and
    `const width = size().width` bind a name to a member of an anonymous type another file declares, which the
    index names with a local of this file it defines nowhere (the shorthand's key shares the name's range). That
    alias leads nowhere: the name ends at its own definition, a value, as a name bound to what the index does not
    name."""
    import test_codebase_map_code_graph as graphs
    _written(tmp_path, {"a.ts": "const { t } = useTranslation();\nconst { person: result } = await update();\n"
                                "const width = size().width;\nt(result, width);\n"})
    index = graphs.load(tmp_path, graphs.document("a.ts", [
        graphs.occurrence(1, 8, 9, "local 1", True), graphs.occurrence(1, 8, 9, "local 2"),
        graphs.occurrence(2, 8, 14, "local 3"), graphs.occurrence(2, 16, 22, "local 4", True),
        graphs.occurrence(3, 6, 11, "local 5", True), graphs.occurrence(3, 21, 26, "local 6"),
        graphs.occurrence(4, 0, 1, "local 1"), graphs.occurrence(4, 2, 8, "local 4"),
        graphs.occurrence(4, 10, 15, "local 5")]))
    _hops, traversal, _prepared = code_graph.adapter_traversal(typescript, index, graphs.Snapshot({}))
    assert {local: [end.cls for end in traversal.ends(f"a.ts#local {local}")] for local in (1, 4, 5)} == {
        1: ["project-value"], 4: ["project-value"], 5: ["project-value"]}


def test_a_member_the_index_names_with_a_local_it_defines_nowhere_is_a_hole_with_the_cause(tmp_path):
    """tududi's routes: `controller.list` reads a member of the object literal controller.js exports, which the index
    names with a local of this file it defines nowhere, as it names a member of an anonymous type or an index
    signature another file declares. A name the file reads bare keeps the default rule."""
    import test_codebase_map_code_graph as graphs
    _written(tmp_path, {"routes.js": 'router.get("/x", controller.list);\nx;\n'})
    index = graphs.load(tmp_path, graphs.document("routes.js", [
        graphs.occurrence(1, 17, 27, "scip-typescript npm fx 1.0.0 `controller.js`/controller."),
        graphs.occurrence(1, 28, 32, "local 7"), graphs.occurrence(2, 0, 1, "local 9")]))
    _hops, traversal, _prepared = code_graph.adapter_traversal(typescript, index, graphs.Snapshot({}))
    assert [(end.cls, end.detail) for end in traversal.ends("routes.js#local 7")] == [("dead-end", typescript.MEMBER)]
    assert [(end.cls, end.detail) for end in traversal.ends("routes.js#local 9")] == [("dead-end", "dangling-local")]


def test_a_member_the_checker_binds_no_declaration_to_is_the_hole_it_says(tmp_path):
    """tududi: `process.env.APP_URL` reads NodeJS.ProcessEnv's index signature, `req.body.title` a member of an any;
    the index has no occurrence there, and the checker's pass in the container says why, beside the index
    (`unbound.jsonl`); a site it says nothing of stays `no-occurrence`."""
    import test_codebase_map_code_graph as graphs
    _written(tmp_path, {"a.ts": "process.env.APP_URL;\nreq.body.title;\nfire.click;\nuser.nick;\nz.w;\n"})
    (tmp_path / "index.unbound.jsonl").write_text("\n".join(json.dumps(line) for line in (
        ["a.ts", 1, 12, "index", "NodeJS.ProcessEnv"], ["a.ts", 2, 9, "any", ""], ["a.ts", 3, 5, "mapped", "FireObject"],
        ["a.ts", 4, 5, "undeclared", "Model<any, any>"])) + "\n", encoding="utf-8")
    index = graphs.load(tmp_path, graphs.document("a.ts", [graphs.occurrence(5, 0, 1, "local 1", True)]))
    snapshot = graphs.Snapshot({}, [(n, "a.ts", "read", line, column) for n, (line, column) in enumerate(
        ((1, 12), (2, 9), (3, 5), (4, 5), (5, 2)))])
    _hops, traversal, _prepared = code_graph.adapter_traversal(typescript, index, snapshot)
    graph, _ = code_graph.build(index, snapshot, "x", {}, {}, traversal=traversal)
    assert [(hole["site"], hole["class"]) for hole in graph["holes"]] == [
        ("a.ts:1", "NodeJS.ProcessEnv's index signature: only execution knows the value"),
        ("a.ts:2", "a member of a value of type any: only execution knows it"),
        ("a.ts:3", "FireObject's member has no declaration, the checker made it: the index names nothing there"),
        ("a.ts:4", "Model<any, any> declares no such member: only execution knows it"),
        ("a.ts:5", "no-occurrence")]


LINK = {"kind": "link_outside", "path": "shared", "detail": "a tracked link to a path outside the project"}


def test_a_gap_the_container_run_reports_is_a_gap_of_the_index_run(sandbox):
    """A tracked link the copy left out, since it points outside the project, is the run's own gap: the index
    run's contract carries it beside the preparation's."""
    project = _project(sandbox, "ts")
    box = _contained(sandbox, index=FIXTURES / "ts/index.scip")
    sandbox["monkeypatch"].setattr(container, "run_in_container",
                                   lambda *args, **options: {**box(*args, **options), "gaps": [LINK]})
    result = typescript.index(project, sandbox["root"] / "work", roots={""})
    assert "state" not in result, result.get("reason")
    assert LINK in result["gaps"]


def test_without_a_container_engine_typescript_is_unavailable_with_the_gaps_cause_and_remedy(sandbox):
    project = _project(sandbox, "ts")
    _contained(sandbox, gap=("no container engine answers: neither docker nor podman", "start Docker or Podman"))
    result = typescript.index(project, sandbox["root"] / "work", roots={""})
    assert (result["state"], result["reason"], result["install"]) == (
        "unavailable", "no container engine answers: neither docker nor podman", "start Docker or Podman")
    assert result["indexes"] == [] and result["runs"] == []
    # Nothing is downloaded or started without an engine.
    assert sandbox["fetched"] == [] and sandbox["fake"].calls == [] and sandbox["web"].asked == []


def test_what_the_preparation_could_not_install_restore_or_generate_is_a_gap_and_the_index_run_goes_on(sandbox):
    project = _project(sandbox, "ts")
    generated = "DAODAN-GENERATE-FAILED npm .\nnpm error command sh -c svelte-kit sync\nDAODAN-GENERATE-END\n"
    log = ("DAODAN-MISSING node@20.11.1\n" + generated.replace("svelte-kit sync", "npm error code E404")
           + "DAODAN-RESTORE-FAILED npm .\nnpm error code E404\nnpm error 404 no-such-package\nDAODAN-RESTORE-END\n")
    _contained(sandbox, index=FIXTURES / "ts/index.scip", prepare=log)
    result = typescript.index(project, sandbox["root"] / "work", roots={""},
                              toolchains=[{"tool": "node", "version": "20.11.1", "declared_in": ".nvmrc"}])
    assert "state" not in result and len(result["indexes"]) == 1
    assert [(gap["kind"], gap.get("tool") or gap.get("manager")) for gap in result["gaps"]] == [
        ("toolchain_unavailable", "node"), ("restore_failed", "npm")]
    assert result["gaps"][1] == {"kind": "restore_failed", "manager": "npm", "path": ".",
                                 "detail": "npm error code E404 | npm error 404 no-such-package"}
    # A lifecycle script that fails costs the generation only: the folder is restored without it, and it is said.
    _contained(sandbox, index=FIXTURES / "ts/index.scip", prepare=generated)
    result = typescript.index(project, sandbox["root"] / "work", roots={""})
    assert "state" not in result and result["gaps"] == [{
        "kind": "generation_failed", "manager": "npm", "path": ".", "detail": "npm error command sh -c svelte-kit sync"}]


def test_an_indexer_the_preparation_cannot_install_is_unavailable_with_its_cause(sandbox):
    project = _project(sandbox, "ts")
    log = f"npm error network ECONNREFUSED\nDAODAN-MISSING scip-typescript@{typescript.VERSION}\n"
    _contained(sandbox, prepare=log, codes=(70, None))
    result = typescript.index(project, sandbox["root"] / "work", roots={""})
    assert result["state"] == "unavailable" and result["indexes"] == []
    assert f"scip-typescript {typescript.VERSION} could not be installed" in result["reason"]
    assert "npm error network ECONNREFUSED" in result["reason"] and "npm registry" in result["install"]


@pytest.mark.parametrize("codes, said", [((0, 1), "exit code 1"), ((None, None), "preparation timeout")])
def test_a_run_that_brings_no_index_back_is_failed_with_its_cause_and_last_words(sandbox, codes, said):
    project = _project(sandbox, "ts")
    words = "2026-11-16 ERROR one thing\nerror TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'.\n"
    _contained(sandbox, index=FIXTURES / "ts/index.scip", prepare=words, execute=words, codes=codes)
    result = typescript.index(project, sandbox["root"] / "work", roots={""})
    assert result["state"] == "failed" and result["indexes"] == []
    assert said in result["reason"] and "error TS5083" in result["reason"] and result["errors"] >= 1
    assert [run["phase"] for run in result["runs"]] == ["prepare", "execute"][:1 if codes[0] is None else 2]
    assert not list((sandbox["root"] / "work").glob("*.scip"))


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

    def environment(root, names, python=None):
        asked.append((Path(root), list(names)))
        raise OSError("no room for the environment")

    sandbox["monkeypatch"].setattr(rx, "python_environment", environment)
    if contained:
        import container
        sandbox["web"].pages.update(_node_release(platform=f"linux-{container.architecture()}"))
        sandbox["monkeypatch"].setattr(python, "RUNS_HERE", False)
        box = Box(FIXTURES / "python/index.scip")
        sandbox["monkeypatch"].setattr(container, "run_in_container",
                                       lambda *args, **options: {**box(*args, **options), "gaps": [LINK]})
    else:
        sandbox["fake"].index = FIXTURES / "python/index.scip"
    result = python.index(project, sandbox["root"] / "work", units=units)
    assert "state" not in result, result.get("reason")
    # The manifests are the pre-map's, from the checkout's root: the adapter walks for none.
    assert asked == [(project.resolve(), ["svc/pyproject.toml", "svc/setup.py"])]
    [run] = result["runs"]
    assert run["pyrightconfig"] == {"executionEnvironments": [{"root": "lib"}, {"root": ".", "extraPaths": ["lib"]}]}
    assert "gaps" not in run
    # A gap the container run reports itself (a tracked link it did not copy) rides on the contract.
    assert (LINK in result["gaps"]) == contained
    gaps = [gap for gap in result["gaps"] if gap != LINK]
    assert [(gap["kind"], gap["path"]) for gap in gaps] == [("manifest_unread", "svc/setup.py"),
                                                            ("restore_failed", "svc")]
    assert gaps[1]["manager"] == "uv" and "no room for the environment" in gaps[1]["detail"]
    # The folders the runs read reach `missing` the way the stage hands them (`tasks`).
    roots = python.tasks(result["configs"])
    assert python.missing(None, ["svc/lib/app/late.py", "tools/x.py"], roots) == {
        "tools/x.py": "outside every Python project the pre-map states"}


@pytest.mark.parametrize("contained", [False, True])
def test_without_daodan_s_uv_python_is_unavailable_with_the_cause(sandbox, contained):
    """The environment is built by Daodan's pinned uv, never the PATH's: one that cannot be had leaves Python
    unanalyzed, with the cause, and no index runs."""
    import engine_tools
    project = _project(sandbox, "python")
    _tools(project, "python")
    shutil.rmtree(rx.shared_engine_dir("uv"))

    def refused(fetch=True):
        if fetch:
            raise ValueError("checksum mismatch for uv-x86_64-unknown-linux-gnu.tar.gz")

    sandbox["monkeypatch"].setattr(engine_tools, "uv_binary", refused)
    if contained:
        box = Box(FIXTURES / "python/index.scip")

        def gap(project, command, **options):  # what `run_in_container` makes of a preparation's Gap
            try:
                return box(project, command, **options)
            except container.Gap as error:
                return {"state": "gap", "cause": error.cause, "remedy": error.remedy, "outputs": []}

        sandbox["web"].pages.update(_node_release(platform=f"linux-{container.architecture()}"))
        sandbox["monkeypatch"].setattr(python, "RUNS_HERE", False)
        sandbox["monkeypatch"].setattr(container, "run_in_container", gap)
    result = python.index(project, sandbox["root"] / "work")
    assert result["state"] == "unavailable", result
    assert f"uv {engine_tools.UV_VERSION}" in result["reason"] and "checksum mismatch" in result["reason"]
    assert sandbox["fake"].runs() == []


def test_a_run_of_the_whole_checkout_leaves_no_python_file_outside(sandbox):
    project = _project(sandbox, "python")
    _tools(project, "python")
    sandbox["fake"].index = FIXTURES / "python/index.scip"
    result = python.index(project, sandbox["root"] / "work", environment=_environment(sandbox["root"]))
    assert result["configs"] == [""] and "gaps" not in result
    assert python.missing(None, ["tools/x.py"], python.tasks(result["configs"])) == {}
    assert python.missing(None, ["tools/x.py"]) == {}


@pytest.mark.parametrize("contained", [False, True])
def test_python_reads_the_project_on_the_python_its_folder_states_and_says_which(sandbox, contained):
    """Where Daodan's interpreter is not one the run's folder states (`python`, from `structure`), the environment
    is built on the statement (uv resolves it, `rx.python_environment`), and the run says the version it ran with
    and the statement it came from; the checker's pass parses the project with that interpreter. In a container
    the image's Python reads the copy, the checker's pass beside scip-python: a statement it does not admit is a
    gap."""
    project = _project(sandbox, "python")
    _tools(project, "python")
    built, env = [], _environment(sandbox["root"])
    (env / "pyvenv.cfg").write_text("home = /opt/python/bin\nversion_info = 3.99.1\n", encoding="utf-8")

    def environment(root, names, python=None):
        built.append(python)
        return env

    sandbox["monkeypatch"].setattr(rx, "python_environment", environment)
    stated = {"version": "3.99", "declared_in": ".python-version"}
    units = [{"root": "", "manifests": [], "python": stated}]
    unbound = '["app.py", 1, 2, "Unknown", ""]\n'
    if contained:
        sandbox["web"].pages.update(_node_release(platform=f"linux-{container.architecture()}"))
        sandbox["monkeypatch"].setattr(python, "RUNS_HERE", False)
        box = _contained(sandbox, index=FIXTURES / "python/index.scip", execute="DAODAN_PYTHON 3.13.18\n",
                         unbound=unbound)
    else:
        sandbox["fake"].index = FIXTURES / "python/index.scip"
    work = sandbox["root"] / "work"
    result = python.index(project, work, units=units)
    [run] = result["runs"]
    assert built == ["3.99"]
    if not contained:
        assert run["python"] == "3.99.1" and run["python_request"] == stated and "gaps" not in result
        checker = next(command for command, _cwd in sandbox["fake"].calls if str(python.UNBOUND) in command)
        assert checker[:4] == [str(env / "bin" / "python"), "-I", "-S", str(python.UNBOUND)]
        return
    assert run["python"] == "3.13.18" and "python_request" not in run
    [gap] = result["gaps"]
    assert gap["kind"] == "python_unavailable" and gap["path"] == ".python-version"
    assert "3.99" in gap["detail"] and "3.13.18" in gap["detail"]
    inputs = box.asked[0]["inputs"]
    assert inputs["/daodan/tools/python_unbound.py"] == python.UNBOUND
    langserver = Path(inputs["/daodan/tools/pyright.path"]).read_text(encoding="utf-8")
    assert langserver == "/daodan/pyright/node_modules/pyright/langserver.index.js"
    assert "/daodan/pyright/node_modules/pyright/package.json" in inputs
    assert (work / "scip-python-0.unbound.jsonl").read_text(encoding="utf-8") == unbound  # beside its index
