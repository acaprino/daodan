"""The pre-map: its record, the join of sources, model commands read from stored outputs, the declared gaps."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import premap  # noqa: E402
from premap import cargo, go, module_graph, npm, renovate, tsc, uv  # noqa: E402
import snapshot  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

FIXTURES = Path(__file__).with_name("fixtures") / "premap"
PROJECTS = json.loads((FIXTURES / "projects.json").read_text(encoding="utf-8"))


def build(tmp_path, name, *, sources=None, extra=None, runner=None):
    project = tmp_path / "proj"
    for rel, text in {**PROJECTS[name], **(extra or {})}.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    return project, manifest, premap.write(manifest, sources=sources, runner=runner)


def replay(name):
    """The runner of the outputs `benchmarks/project-model/modal_premap.py --store` saved from a Linux container."""
    stored = json.loads((FIXTURES / "outputs" / f"{name}.json").read_text(encoding="utf-8"))
    table = {json.dumps(run["command"], sort_keys=True): run["result"] for run in stored["runs"]}
    return lambda commands: [table[json.dumps(command, sort_keys=True)] for command in commands]


def part(source, rank, **facts):
    return {"source": source, "rank": rank, "facts": facts}


def unit(root, kind, name, **fields):
    return {"root": root, "kind": kind, "name": name, **fields}


def by_root(record, kind):
    return {u["root"]: u for u in record["units"] if u["kind"] == kind}


def gaps(record, kind):
    return [g for g in record["gaps"] if g["kind"] == kind]


class Missing(Exception):
    def __init__(self):
        super().__init__("no tool")
        self.reason, self.install = "tool not installed", "install the tool"


def fake(name, rank, run):
    return SimpleNamespace(NAME=name, VERSION="1", RANK=rank, run=run)


# ------------------------------------------------------------------ record

def test_premap_beside_the_manifest_every_fact_with_its_source(tmp_path):
    _, manifest, record = build(tmp_path, "mixed")
    on_disk = json.loads(premap.path(manifest).read_text(encoding="utf-8"))
    assert premap.path(manifest).parent == manifest.parent
    assert on_disk == record and record["schema"] == premap.SCHEMA
    assert {(u["root"], u["kind"], u["name"]) for u in record["units"]} == {
        (".", "python-project", "acme"), ("web", "npm-package", "@acme/web")}
    assert all(item["sources"] and all("@" in s for s in item["sources"]) for item in record["units"])
    assert {s["source"].split("@")[0]: s["state"] for s in record["sources"]} == {
        "modules.py": "ran", "python-build": "not_needed", "requirements": "not_needed", "npm-files": "ran", "jvm-files": "not_needed",
        "gitmodules": "not_needed", "python-tests": "not_needed", "npm-tests": "not_needed", "npm-start": "not_needed", "autotools": "not_needed",
        "renovate": "not_run", "compose": "not_needed", "buildkit": "not_needed",
        "go": "not_needed", "cargo": "not_needed",
        "uv": "not_needed",
        "tsc": "not_needed", "npm": "not_run", "cmake": "not_needed", "meson": "not_needed", "bazel": "not_needed",
        "make": "not_needed", "project-files": "not_needed", "gradle": "not_needed", "maven": "not_needed",
        "sbt": "not_needed", "dotnet": "not_needed"}
    assert all(u["run"] == {"executes_project_code": False, "reason": ""} for u in record["units"])
    assert "needs" not in record


def test_fresh_until_the_snapshot_changes(tmp_path):
    project, manifest, _ = build(tmp_path, "mixed")
    assert premap.state(manifest)["state"] == "fresh"
    (project / "web" / "index.js").write_text("export const b = 2;\n", encoding="utf-8")
    snapshot.read_project(project, manifest)
    assert premap.state(manifest)["state"] == "stale"
    assert premap.ensure(manifest)["schema"] == premap.SCHEMA
    assert premap.state(manifest)["state"] == "fresh"


def test_an_added_file_no_reader_reads_makes_the_premap_stale(tmp_path):
    """Unread files are no inventory rows, so the digest alone would keep a `no_analyzer` gap fresh and old."""
    project, manifest, _ = build(tmp_path, "mixed")
    assert premap.state(manifest)["state"] == "fresh"
    (project / "extra.rb").write_text("puts 1\n", encoding="utf-8")
    snapshot.read_project(project, manifest)
    assert premap.state(manifest)["state"] == "stale"
    assert premap.ensure(manifest)["schema"] == premap.SCHEMA
    assert premap.state(manifest)["state"] == "fresh"


def test_a_record_holds_no_dependencies_whatever_the_sources_say(tmp_path):
    """The libraries a unit uses are its analyzer's, resolved by the build tool while it indexes: a source that
    states them fails, and the record keeps the structure of the others."""
    stating = fake("lister", "reader", lambda context: {"facts": {
        "units": [unit(".", "python-project", "acme")],
        "dependencies": [{"unit": "acme", "name": "requests", "declared": ">=2", "declared_in": "pyproject.toml"}]}})
    _, _, record = build(tmp_path, "mixed", sources=[*premap.SOURCES, stating])
    assert "dependencies" not in record and record["units"]
    assert {s["source"]: s["state"] for s in record["sources"]}["lister@1"] == "failed"
    [gap] = [g for g in gaps(record, "source_failed") if g["source"] == "lister@1"]
    assert "dependencies" in gap["detail"]
    assert not any("lister@1" in u["sources"] for u in record["units"])


# -------------------------------------------------------------------- join

def test_two_sources_agreeing_make_one_fact_with_both_sources():
    joined = premap.join([part("a@1", "reader", units=[unit(".", "go-module", "example.com/m", manifest="go.mod")]),
                          part("b@2", "model", units=[unit(".", "go-module", "example.com/m", source_roots=["."])])])
    assert joined["units"] == [{"root": ".", "kind": "go-module", "name": "example.com/m", "source_roots": ["."],
                                "manifest": "go.mod", "sources": ["b@2", "a@1"]}]


def test_the_model_value_stays_and_the_reader_value_goes_to_conflicts():
    joined = premap.join([part("reader@1", "reader", units=[unit(".", "gradle-project", "shop")]),
                          part("gradle@9", "model", units=[unit(".", "gradle-project", ":")])])
    [only] = joined["units"]
    assert only["name"] == ":" and only["sources"] == ["gradle@9", "reader@1"]
    assert only["conflicts"] == [{"field": "name", "value": "shop", "source": "reader@1", "kept_from": "gradle@9"}]


def test_two_model_commands_disagreeing_keep_the_first_declared():
    joined = premap.join([part("cargo@1", "model", toolchains=[{"tool": "rust", "version": "1.80", "declared_in": "Cargo.toml"}]),
                          part("rustup@1", "model", toolchains=[{"tool": "rust", "version": "1.80.0", "declared_in": "Cargo.toml"}])])
    [only] = joined["toolchains"]
    assert only["version"] == "1.80" and only["sources"] == ["cargo@1", "rustup@1"]
    assert only["conflicts"] == [{"field": "version", "value": "1.80.0", "source": "rustup@1", "kept_from": "cargo@1"}]


def test_a_field_one_source_does_not_give_is_no_conflict():
    reader = unit(".", "python-project", "Acme_Cli", manifest="pyproject.toml")
    model = unit(".", "python-project", "acme-cli", manifest="pyproject.toml", source_roots=["src"])
    joined = premap.join([part("a@1", "reader", units=[reader]), part("b@1", "model", units=[model])])
    [only] = joined["units"]  # names fold as PEP 503 does
    assert only["source_roots"] == ["src"] and "conflicts" not in only and only["sources"] == ["b@1", "a@1"]


def test_the_origins_two_sources_state_for_one_unit_add_up():
    """`registries` is where some of a unit's dependencies come from, as each source reads it (a lock's indexes, a
    manifest's VCS URLs): two sources add up, and neither is a conflict."""
    reader = unit(".", "python-project", None, registries=["https://github.com"])
    model = unit(".", "python-project", None, registries=["https://github.com", "https://pypi.example.org"])
    [only] = premap.join([part("a@1", "reader", units=[reader]), part("b@1", "model", units=[model])])["units"]
    assert only["registries"] == ["https://github.com", "https://pypi.example.org"] and "conflicts" not in only


def test_config_keys_join_one_by_one():
    joined = premap.join([part("a@1", "reader", units=[unit("app", "npm-package", "app", config={"tsconfig": ["app/tsconfig.json"]})]),
                          part("b@1", "model", units=[unit("app", "npm-package", "app", config={"paths": {"@/*": ["app/src/*"]},
                                                                                             "tsconfig": ["app/tsconfig.json"]})])])
    [only] = joined["units"]
    assert only["config"] == {"paths": {"@/*": ["app/src/*"]}, "tsconfig": ["app/tsconfig.json"]}
    assert "conflicts" not in only


def test_a_source_that_covers_a_folder_supersedes_the_units_it_does_not_state_there():
    model = {**part("cmake@4", "model", units=[unit("core", "cmake-target", "calc_core")]),
             "covers": {"cmake-target": [".", "core"]}}
    reader = part("modules.py@1", "reader", units=[unit(".", "cmake-target", "calc"), unit("core", "cmake-target", None),
                                                   unit("tools", "cmake-target", "gen"), unit(".", "npm-package", "web")])
    joined = premap.join([reader, model])
    assert sorted((u["root"], u["kind"], u["name"]) for u in joined["units"]) == [
        (".", "npm-package", "web"), ("core", "cmake-target", "calc_core"), ("tools", "cmake-target", "gen")]
    [gap] = joined["superseded"]
    assert gap["path"] == "." and "calc" in gap["detail"] and "cmake@4" in gap["detail"]


def test_two_entries_of_one_source_never_merge():
    joined = premap.join([part("cmake@3", "model", units=[unit("lib", "cmake-target", "core"), unit("lib", "cmake-target", "cli")]),
                          part("reader@1", "reader", units=[unit("lib", "cmake-target", "core")])])
    assert sorted((u["name"], tuple(u["sources"])) for u in joined["units"]) == [
        ("cli", ("cmake@3",)), ("core", ("cmake@3", "reader@1"))]


def test_a_facet_no_source_gives_is_absent():
    joined = premap.join([part("a@1", "reader", units=[unit(".", "go-module", "m")])])
    assert "toolchains" not in joined and "excluded" not in joined


# ----------------------------------------------------------------- sources

def test_an_unavailable_or_failing_source_is_a_gap_and_states_nothing(tmp_path):
    def missing(context):
        raise Missing()

    def broken(context):
        raise RuntimeError("exit 2: bad flag")

    sources = [*premap.SOURCES, fake("tool", "model", missing), fake("other", "model", broken)]
    _, _, record = build(tmp_path, "mixed", sources=sources)
    states = {s["source"]: s for s in record["sources"]}
    assert states["tool@1"]["state"] == "unavailable" and states["other@1"]["state"] == "failed"
    found = {g["source"]: g for g in record["gaps"] if g["kind"] in ("source_unavailable", "source_failed")}
    assert found["tool@1"] == {"kind": "source_unavailable", "source": "tool@1", "detail": "tool not installed",
                               "remedy": "install the tool"}
    assert found["other@1"]["kind"] == "source_failed" and "bad flag" in found["other@1"]["detail"]
    assert not any(s in ("tool@1", "other@1") for item in record["units"] for s in item["sources"])


def test_no_source_of_the_premap_writes_the_rows_of_the_entry_points(tmp_path):
    """Noir and the frameworks' own tools are `find_entry_points`' (`entry_points.SOURCES`, `entry-points.json`): the pre-map has
    no facet for their rows, so a source of it that stated one fails as a source does, and the pre-map holds none."""
    import entry_points
    rows = {"noir_entries", "framework_entries"}
    assert not rows & set(premap.IDENTITY) and set(entry_points.IDENTITY) == rows
    assert not set(premap.SOURCES) & set(entry_points.SOURCES)
    stray = fake("stray", "reader", lambda context: {"facts": {"noir_entries": [{"site": "app.py:1"}]}})
    _, _, record = build(tmp_path, "mixed", sources=[*premap.SOURCES, stray])
    assert {s["source"]: s["state"] for s in record["sources"]}["stray@1"] == "failed" and not rows & set(record)


def test_a_source_with_nothing_to_read_is_not_needed(tmp_path):
    sources = [*premap.SOURCES, fake("extra", "reader", lambda context: None)]
    _, _, record = build(tmp_path, "mixed", sources=sources)
    assert {s["source"]: s["state"] for s in record["sources"]}["extra@1"] == "not_needed"


def test_model_commands_without_a_runner_are_not_run_and_a_gap(tmp_path):
    _, manifest, record = build(tmp_path, "go_nested")
    states = {s["source"].split("@")[0]: s for s in record["sources"]}
    assert states["go"]["state"] == "not_run" and states["go"]["commands"] > 0
    [gap] = [g for g in gaps(record, "model_not_run") if g["source"] == premap.label(go)]
    assert "container" in gap["detail"]
    assert set(by_root(record, "go-module")) == {".", "_examples/demo"}  # from modules.py alone
    assert premap.state(manifest)["state"] == "fresh"
    assert premap.state(manifest, runner=replay("go_nested"))["state"] == "stale"


def test_ensure_with_a_runner_runs_the_model_commands_a_fresh_premap_left_not_run(tmp_path):
    """Without a runner the pre-map stays as it is; with one, the sources left `not_run` run (the whole pre-map is
    derived again: the join needs every source's part), and the next `ensure` with a runner keeps it."""
    _, manifest, record = build(tmp_path, "go_nested")
    assert premap.ensure(manifest) == record
    asked = []
    runner = replay("go_nested")
    again = premap.ensure(manifest, runner=lambda commands: asked.append(len(commands)) or runner(commands))
    states = {s["source"].split("@")[0]: s["state"] for s in again["sources"]}
    assert states["go"] == "ran" and asked and not gaps(again, "model_not_run")
    assert premap.ensure(manifest, runner=lambda commands: pytest.fail("ran twice")) == again


def test_every_command_is_data_with_its_network():
    for source in (go, cargo, uv, renovate, tsc, npm):
        assert hasattr(source, "commands") and hasattr(source, "read")
    assert all(source.RANK == "model" for source in (go, cargo, uv, tsc, npm)) and renovate.RANK == "reader"
    import resolve_edges as rx
    assert (go.VERSION, cargo.VERSION) == (rx.GO_VERSION, rx.RUST_VERSION)


# -------------------------------------------------------- what the run needs

def test_a_build_that_runs_project_code_says_so_with_its_reason(tmp_path):
    _, _, record = build(tmp_path, "gradle")
    [shop] = [u for u in record["units"] if u["kind"] == "gradle-project"]
    assert shop["run"]["executes_project_code"] is True and shop["run"]["reason"].startswith("build.gradle")


def test_setup_py_read_and_not_run_is_a_gap(tmp_path):
    _, _, record = build(tmp_path, "setup_py")
    [legacy] = [u for u in record["units"] if u["kind"] == "python-project"]
    assert legacy["run"]["executes_project_code"] is False
    [gap] = gaps(record, "not_executed")
    assert gap["unit"] == "legacy" and gap["path"] == "setup.py"


def test_install_scripts_not_run_are_a_gap_and_the_lock_names_the_registry(tmp_path):
    _, _, record = build(tmp_path, "npm_scripts")
    [site] = record["units"]
    assert site["run"]["executes_project_code"] is False and site["registries"] == ["https://registry.npmjs.org"]
    [gap] = gaps(record, "not_executed")
    assert gap["path"] == "package.json" and "scripts.postinstall, esbuild" in gap["detail"]
    assert gap["source"].startswith("npm-files@")


def test_the_origins_of_git_and_url_dependencies_are_registries_from_the_lockfiles_and_the_manifest(tmp_path):
    """Where a Node package's dependencies come from, as npm, pnpm and Yarn record it in their lockfiles, Yarn's
    registries in `.yarnrc.yml`, and the manifest's own URLs with npm's shorthands for GitHub, GitLab and
    Bitbucket. A URL's credentials stay out."""
    def package(name, dependencies=None):
        return json.dumps({"name": name, "dependencies": dependencies or {}})
    lock = {"lockfileVersion": 3, "packages": {"": {"name": "a"}, "node_modules/tool": {
        "resolved": "git+ssh://git@github.com/acme/tool.git#0123"}, "node_modules/x": {
        "resolved": "https://user:token@npm.example.org/x/-/x-1.0.0.tgz", "funding": {"url": "https://fund.example"}}}}
    _, _, record = build(tmp_path, "npm_scripts", extra={
        "a/package.json": package("a"), "a/package-lock.json": json.dumps(lock),
        "b/package.json": package("b"), "b/pnpm-lock.yaml": (
            "packages:\n  tool@https://codeload.github.com/acme/tool/tar.gz/0123:\n"
            "    resolution: {tarball: https://codeload.github.com/acme/tool/tar.gz/0123}\n"
            "  lib@git+https://gitlab.com/acme/lib.git#4567:\n"
            "    resolution: {commit: 4567, repo: https://gitlab.com/acme/lib.git, type: git}\n"),
        "c/package.json": package("c"), "c/yarn.lock": (
            '# yarn lockfile v1\n\n"x@^1.0.0":\n  version "1.0.0"\n'
            '  resolved "https://npm.corp.example/x/-/x-1.0.0.tgz#abc"\n'),
        "d/package.json": package("d"), "d/.yarnrc.yml": (
            'npmRegistryServer: "https://registry.corp.example"\nnpmScopes:\n  acme:\n'
            '    npmRegistryServer: "https://acme.example/npm"\n'),
        "d/yarn.lock": ('__metadata:\n  version: 8\n\n"y@https://github.com/acme/y.git#commit=89ab":\n'
                        '  resolution: "y@https://github.com/acme/y.git#commit=89ab"\n'),
        "e/package.json": package("e", {"a": "github:acme/a#v1", "b": "acme/b", "c": "gitlab:acme/c",
                                         "d": "bitbucket:acme/d", "e": "git+https://git.example.org/e.git",
                                         "f": "https://cdn.example.com/f.tgz", "g": "^1.0.0", "h": "file:../h",
                                         "i": "npm:other@1", "j": "workspace:*"})})
    units = by_root(record, "npm-package")
    assert {root: units[root].get("registries") for root in "abcde"} == {
        "a": ["https://npm.example.org", "ssh://github.com"],
        "b": ["https://codeload.github.com", "https://gitlab.com"],
        "c": ["https://npm.corp.example"],
        "d": ["https://acme.example", "https://github.com", "https://registry.corp.example"],
        "e": ["https://bitbucket.org", "https://cdn.example.com", "https://git.example.org", "https://github.com",
              "https://gitlab.com"]}


def test_package_folders_come_only_from_what_a_build_configuration_declares(tmp_path):
    _, _, record = build(tmp_path, "declared_package_dirs")
    units = by_root(record, "python-project")
    assert units["."]["source_roots"] == ["src"] and units["tools"]["source_roots"] == ["tools/lib"]
    assert all(any(s.startswith("python-build@") for s in u["sources"]) for u in units.values())
    _, _, plain = build(tmp_path / "plain", "mixed")
    assert all("source_roots" not in u for u in plain["units"] if u["kind"] == "python-project")


def test_the_indexes_and_the_url_dependencies_a_python_build_configuration_declares_are_registries(tmp_path):
    """pyproject.toml's direct references (dependencies, extras, groups), uv's and Poetry's indexes and their git
    and URL sources, setup.cfg's requirements: where the restore fetches from, credentials left out."""
    pyproject = """[project]
name = "svc"
dependencies = ["mylib @ git+https://github.com/acme/mylib.git@v1", "click"]
[project.optional-dependencies]
fast = ["wheel1 @ https://files.example.net/w-1.0-py3-none-any.whl"]
[dependency-groups]
dev = ["tool @ git+ssh://git@gitlab.example.com/acme/tool.git", {include-group = "fast"}]
[tool.uv]
extra-index-url = ["https://user:secret@extra.example/simple"]
[[tool.uv.index]]
name = "internal"
url = "https://pypi.internal.example/simple"
[tool.uv.sources]
fast2 = { git = "https://git.example.org/fast2", tag = "v1" }
local = { path = "../local" }
[[tool.poetry.source]]
name = "corp"
url = "https://corp.example/simple"
[tool.poetry.dependencies]
pkg = { git = "https://git.corp.example/pkg.git" }
"""
    setup = "[metadata]\nname = old\n\n[options]\ninstall_requires =\n    old @ git+https://hg.example.org/old\n"
    _, _, record = build(tmp_path, "python_nested", extra={"svc/pyproject.toml": pyproject, "svc/app.py": "X = 1\n",
                                                          "old/setup.cfg": setup, "old/old.py": "Y = 2\n"})
    units = by_root(record, "python-project")
    assert units["svc"]["registries"] == [
        "https://corp.example", "https://extra.example", "https://files.example.net", "https://git.corp.example",
        "https://git.example.org", "https://github.com", "https://pypi.internal.example", "ssh://gitlab.example.com"]
    assert units["old"]["registries"] == ["https://hg.example.org"]
    assert "registries" not in units["utils/arena"]


def test_the_jvm_files_give_the_wrapper_and_the_java_a_pom_declares(tmp_path):
    _, _, record = build(tmp_path, "jvm_files")
    [shop] = [u for u in record["units"] if u["kind"] == "gradle-project"]
    assert shop["config"]["wrapper"] == {
        "file": "gradle/wrapper/gradle-wrapper.properties",
        "distribution_url": "https://services.gradle.org/distributions/gradle-8.10.2-bin.zip",
        "distribution_sha256": "31c55713e40233a8303827ceb42ca48a47267a0ad4bab9177123121e71524c26"}
    versions = {(t["tool"], t["declared_in"]): (t["version"], t["line"]) for t in record["toolchains"]}
    assert versions[("gradle", "gradle/wrapper/gradle-wrapper.properties#distributionUrl")] == ("8.10.2", 2)
    assert versions[("java", "api/pom.xml#properties.maven.compiler.release")] == ("17", 7)
    undeclared = {g["path"]: g["detail"] for g in gaps(record, "toolchain_undeclared")}
    assert "${jdk}" in undeclared["api/pom.xml"] and "Gradle" in undeclared["."]


DAEMON_JVM = ("#This file is generated by updateDaemonJvm\n"
              "toolchainUrl.FREE_BSD.AARCH64=https\\://api.foojay.io/disco/v3.0/ids/0a1b/redirect\n"
              "toolchainUrl.LINUX.X86_64=https\\://api.foojay.io/disco/v3.0/ids/398ffe3949748bfb1d5636f023d228fd/redirect\n"
              "toolchainVendor=JETBRAINS\n"
              "toolchainVersion=21\n")
DAEMON_FILE = "gradle/gradle-daemon-jvm.properties"


def test_a_gradle_build_s_daemon_jvm_file_states_its_java_with_the_vendor_and_the_gap_does_not_apply(tmp_path):
    """`gradle/gradle-daemon-jvm.properties`, which `updateDaemonJvm` writes, is the JDK the build runs on:
    `toolchainVersion` and `toolchainVendor` (Gradle's name for the vendor), on the line of the version. The
    `toolchainUrl` lines are where Gradle would download it: no part of the fact, Daodan installs through mise."""
    _, _, record = build(tmp_path, "jvm_files", extra={DAEMON_FILE: DAEMON_JVM})
    [java] = [t for t in record["toolchains"] if t["declared_in"].startswith(DAEMON_FILE)]
    assert {k: v for k, v in java.items() if k != "sources"} == {
        "tool": "java", "version": "21", "vendor": "JETBRAINS", "declared_in": f"{DAEMON_FILE}#toolchainVersion", "line": 5}
    assert "foojay" not in json.dumps(record["toolchains"])
    assert "." not in {g["path"] for g in gaps(record, "toolchain_undeclared")}


def test_a_nested_gradle_build_s_daemon_jvm_file_states_the_java_of_that_build_only(tmp_path):
    """A build below the project's root (an Android shell in `src-tauri/gen/android`) has its own `gradle/` folder."""
    nested = {"android/settings.gradle": "rootProject.name = 'android'\n", "android/build.gradle": "plugins {}\n",
              f"android/{DAEMON_FILE}": DAEMON_JVM}
    _, _, record = build(tmp_path, "jvm_files", extra=nested)
    [java] = [t for t in record["toolchains"] if t["declared_in"].startswith(f"android/{DAEMON_FILE}")]
    assert (java["version"], java["vendor"], java["line"]) == ("21", "JETBRAINS", 5)
    undeclared = {g["path"] for g in gaps(record, "toolchain_undeclared")}
    assert "android" not in undeclared and "." in undeclared  # the root build states none


def test_a_daemon_jvm_file_with_no_vendor_states_none_and_one_with_no_version_states_nothing(tmp_path):
    _, _, record = build(tmp_path, "jvm_files", extra={DAEMON_FILE: "toolchainVersion=17\n"})
    [java] = [t for t in record["toolchains"] if t["declared_in"].startswith(DAEMON_FILE)]
    assert (java["version"], "vendor" in java) == ("17", False)
    _, _, record = build(tmp_path / "again", "jvm_files", extra={DAEMON_FILE: "toolchainVendor=JETBRAINS\n"})
    assert not [t for t in record["toolchains"] if t["declared_in"].startswith(DAEMON_FILE)]
    assert "." in {g["path"] for g in gaps(record, "toolchain_undeclared")}


def test_a_compiler_plugin_setting_is_named_by_its_path_in_the_pom(tmp_path):
    """D-226: a toolchain's field is its path in the pom, as `properties.maven.compiler.release` is, the plugin
    named by its artifactId: `<configuration><source>` of maven-compiler-plugin is
    `maven-compiler-plugin.configuration.source` (jvm-ver-mvn-cfg6's expected.json)."""
    pom = ('<project xmlns="http://maven.apache.org/POM/4.0.0">\n  <modelVersion>4.0.0</modelVersion>\n'
           '  <groupId>acme</groupId>\n  <artifactId>legacy</artifactId>\n  <version>1</version>\n  <build>\n'
           '    <plugins>\n      <plugin>\n        <artifactId>maven-compiler-plugin</artifactId>\n'
           '        <configuration>\n          <source>1.6</source>\n          <target>1.6</target>\n'
           '        </configuration>\n      </plugin>\n    </plugins>\n  </build>\n</project>\n')
    _, _, record = build(tmp_path, "jvm_files", extra={"legacy/pom.xml": pom})
    versions = {(t["tool"], t["declared_in"]): (t["version"], t["line"]) for t in record["toolchains"]}
    assert versions[("java", "legacy/pom.xml#maven-compiler-plugin.configuration.source")] == ("1.6", 11)
    assert versions[("java", "legacy/pom.xml#maven-compiler-plugin.configuration.target")] == ("1.6", 12)


def test_the_jvm_target_kotlin_compiles_to_is_a_java_toolchain_of_the_pom(tmp_path):
    """jvm-mixed-java-kotlin: `<kotlin.compiler.jvmTarget>17</kotlin.compiler.jvmTarget>`, the property
    kotlin-maven-plugin reads for the bytecode level it writes, is a Java release the pom states, beside
    `maven.compiler.release` (its expected.json: `pom.xml#properties.kotlin.compiler.jvmTarget`)."""
    pom = ('<project xmlns="http://maven.apache.org/POM/4.0.0">\n  <modelVersion>4.0.0</modelVersion>\n'
           '  <groupId>acme</groupId>\n  <artifactId>mixed</artifactId>\n  <version>1</version>\n  <properties>\n'
           '    <kotlin.compiler.jvmTarget>17</kotlin.compiler.jvmTarget>\n'
           '    <maven.compiler.release>17</maven.compiler.release>\n  </properties>\n</project>\n')
    _, _, record = build(tmp_path, "jvm_files", extra={"mixed/pom.xml": pom})
    versions = {(t["tool"], t["declared_in"]): (t["version"], t["line"]) for t in record["toolchains"]}
    assert versions[("java", "mixed/pom.xml#properties.kotlin.compiler.jvmTarget")] == ("17", 7)
    assert versions[("java", "mixed/pom.xml#properties.maven.compiler.release")] == ("17", 8)


# ------------------------------------------------- model readers, stored outputs

def test_go_reader_gives_the_nested_module_and_what_the_build_leaves_out(tmp_path):
    _, _, record = build(tmp_path, "go_nested", runner=replay("go_nested"))
    label = premap.label(go)
    units = by_root(record, "go-module")
    assert set(units) == {".", "_examples/demo"} and all(label in u["sources"] for u in units.values())
    assert units["_examples/demo"]["depends_on"] == ["example.com/app"]
    assert units["."]["config"]["ignored_files"] == ["gen.go"]
    assert {"tool": "go", "version": "1.22", "declared_in": "go.mod",
            "sources": [label, premap.label(renovate)]} in record["toolchains"]  # the model first, Renovate agrees
    assert not gaps(record, "model_failed") and not gaps(record, "model_not_run")


def test_a_nested_go_module_without_a_replace_depends_on_the_published_module(tmp_path):
    """Without a `replace` to the folder or a `go.work` that lists both, Go builds the nested module against the
    module it requires as published, not against the folder beside it: never an edge."""
    _, _, record = build(tmp_path, "go_published", runner=replay("go_published"))
    units = by_root(record, "go-module")
    assert set(units) == {".", "_examples/use"} and units["_examples/use"]["depends_on"] == []


def test_cargo_reader_gives_crates_and_the_build_script_as_a_fact(tmp_path):
    _, _, record = build(tmp_path, "rust_buildrs", runner=replay("rust_buildrs"))
    crates = by_root(record, "cargo-crate")
    assert set(crates) == {"gen", "flags"} and all(premap.label(cargo) in c["sources"] for c in crates.values())
    assert crates["gen"]["config"]["build_script"] == "gen/build.rs" and crates["gen"]["source_roots"] == ["gen/src"]
    assert all(c["run"]["executes_project_code"] is False for c in crates.values())
    assert sorted(g["path"] for g in gaps(record, "not_executed")) == ["flags/build.rs", "gen/build.rs"]
    assert [(t["tool"], t["version"]) for t in record["toolchains"] if t["declared_in"] == "flags/Cargo.toml"] == [
        ("rust", "1.80"), ("rust-edition", "2021")]  # the compiler it asks for and the language edition it writes
    assert [sorted(w["members"]) for w in record["workspace"] if w["root"] == "."] == [["flags", "gen"]]
    assert not gaps(record, "model_failed") and not gaps(record, "model_partial")


def test_uv_reader_gives_members_and_their_edges(tmp_path):
    _, _, record = build(tmp_path, "uv_workspace", runner=replay("uv_workspace"))
    units = by_root(record, "python-project")
    assert set(units) == {"packages/core", "packages/app"}
    assert all(premap.label(uv) in u["sources"] for u in units.values())
    assert units["packages/app"]["depends_on"] == ["ws-core"]
    [workspace] = record["workspace"]
    assert workspace["tool"] == "uv" and sorted(workspace["members"]) == ["packages/app", "packages/core"]
    assert not gaps(record, "model_failed")


def test_uv_reader_gives_every_origin_the_lock_fetches_from():
    """The exported lock names where each package comes from: its index, its files, a git source, an archive."""
    lock = """lock-version = "1.0"
[[packages]]
name = "app"
directory = { path = ".", editable = true }
[[packages]]
name = "six"
index = "https://pypi.org/simple"
sdist = { url = "https://files.pythonhosted.org/packages/six-1.16.0.tar.gz" }
[[packages]]
name = "mylib"
vcs = { type = "git", url = "https://github.com/acme/mylib", commit-id = "0123" }
[[packages]]
name = "corp"
index = "https://pypi.corp.example/simple"
wheels = [{ url = "https://files.corp.example/corp-1.0-py3-none-any.whl" }]
[[packages]]
name = "direct"
archive = { url = "https://user:token@archive.example.org/direct-1.0.tar.gz" }
"""
    commands = [{"tool": "uv", "argv": argv, "cwd": ".", "env": uv.ENV, "network": "none"}
                for argv in (uv.EXPORT, uv.TREE)]
    answers = [{"returncode": 0, "stdout": text, "stderr": ""} for text in (lock, "app v0.1.0\n")]
    [app] = uv.read(None, commands, answers)["facts"]["units"]
    assert app["registries"] == ["https://archive.example.org", "https://files.corp.example",
                                 "https://files.pythonhosted.org", "https://github.com", "https://pypi.corp.example",
                                 "https://pypi.org"]


def test_uv_reader_makes_one_unit_without_a_name_of_a_root_that_is_no_package():
    """A workspace root with no `[project]` lists its dependency groups as roots of `uv tree` (`zizmor v1 (group: dev)`):
    they are dependencies, not packages, and the root is one unit with no name (the fastapi template)."""
    lock = ('lock-version = "1.0"\n[[packages]]\nname = "app"\ndirectory = { path = "backend", editable = true }\n'
            '[[packages]]\nname = "zizmor"\nindex = "https://pypi.org/simple"\n')
    tree = ("zizmor v1.30.1 (group: dev)\ntyper v0.27.2 (group: dev)\n├── rich v15.0.0\nprek v0.5.3 (group: dev)\n"
            "app v0.1.0\n├── alembic v1.20.0\n├── coverage v7.16.1 (group: dev)\n")
    commands = [{"tool": "uv", "argv": argv, "cwd": ".", "env": uv.ENV, "network": "none"} for argv in (uv.EXPORT, uv.TREE)]
    answers = [{"returncode": 0, "stdout": text, "stderr": ""} for text in (lock, tree)]
    facts = uv.read(None, commands, answers)["facts"]
    assert [(u.get("name"), u["root"]) for u in facts["units"]] == [("app", "backend"), (None, ".")]
    assert facts["workspace"] == [{"tool": "uv", "root": ".", "members": ["backend"]}]


def test_tsc_reader_gives_the_tsconfigs_in_reference_order_and_their_aliases(tmp_path):
    _, _, record = build(tmp_path, "tsc_alias", runner=replay("tsc_alias"))
    [web] = by_root(record, "npm-package").values()
    assert premap.label(tsc) in web["sources"]
    assert web["config"]["tsconfig"] == ["tsconfig.json", "tsconfig.app.json", "tsconfig.node.json", "tools/tsconfig.json"]
    assert web["config"]["paths"] == {"@/*": ["src/*"]}
    [failed] = [g for g in gaps(record, "model_failed") if g["source"] == premap.label(tsc)]
    assert failed["path"] == "tools/tsconfig.json"


def test_the_files_to_leave_out_come_from_list_files_with_why(tmp_path):
    """The snapshot's header leaves out what Linguist's expressions say (`file_inventory.excluded`), and the pre-map
    holds it with no command: `vendor/` is a dependency folder the walk never enters, named by Linguist's expression,
    `gen/` is generated only where `.gitattributes` says so, and a dot folder is outside the perimeter."""
    _, _, record = build(tmp_path, "enry_files")
    assert {(e["path"], e["why"]) for e in record["excluded"]} == {("docs/", "documentation"),
                                                                   ("README.md", "documentation"),
                                                                   ("vendor/", "vendored")}
    assert all(e["sources"] == [premap.LISTED] for e in record["excluded"])
    assert record["binding"]["excluded"] == [{"path": "README.md", "why": "documentation"},
                                             {"path": "docs/", "why": "documentation"},
                                             {"path": "vendor/", "why": "vendored"}]


def _stated_empty(facts) -> set:
    """Every list or mapping a source states empty, as (facet, entry identity, field)."""
    found = set()
    for facet, entries in (facts or {}).items():
        for entry in entries:
            identity = (facet, *(json.dumps(entry.get(k)) for k in ("root", "kind", "tool", "name", "path", "unit")))
            fields = {k: v for k, v in entry.items() if k != "config"}
            fields.update({f"config.{k}": v for k, v in (entry.get("config") or {}).items()})
            if "config" in entry and not entry["config"]:
                fields["config"] = entry["config"]
            found |= {(identity, field) for field, value in fields.items() if value in ([], {})}
    return found


def test_a_command_that_did_not_answer_never_states_a_fact_empty(tmp_path):
    """A failed command takes away the facts it gives; it never turns one into "none", which would win the join."""
    checked = 0
    for case in sorted(p.stem for p in (FIXTURES / "outputs").glob("*.json")):
        _, manifest, _ = build(tmp_path / case, case, sources=())
        runner = replay(case)
        with open_snapshot(manifest) as store:
            context = premap.Context(manifest, store)
            for source in (go, cargo, uv, tsc, npm, renovate):
                commands = source.commands(context)
                if not commands:
                    continue
                if case == "enry_files" and source is renovate:
                    # This historical Linux capture contains the extraction only. Its on: push file now
                    # selects a second YAML command, exercised separately by the workflow-entry replay.
                    commands = [c for c in commands if c["argv"] != ["sh", "-c", renovate.EACH]]
                results = runner(commands)
                answered = _stated_empty(source.read(context, commands, results).get("facts"))
                # One command failing, and one kind of command failing in every folder (a project without the
                # lockfile the command reads).
                kinds = {tuple(c["argv"]) + (c["env"].get("GOWORK"),) for c in commands}
                groups = [{i} for i in range(len(commands))] + [
                    {i for i, c in enumerate(commands) if tuple(c["argv"]) + (c["env"].get("GOWORK"),) == kind}
                    for kind in sorted(kinds, key=str)]
                for group in groups:
                    broken = [{**r, "returncode": 1, "stdout": "", "stderr": "failed"} if i in group else r
                              for i, r in enumerate(results)]
                    stated = _stated_empty(source.read(context, commands, broken).get("facts"))
                    assert stated <= answered, (case, source.NAME, [commands[i]["argv"] for i in sorted(group)],
                                                sorted(stated - answered))
                    checked += 1
    assert checked >= 80


def _module(ident, root, kind, ecosystem, name, *, named=True, aliases=(), manifests=(), external=()):
    return {"id": ident, "name": name, "named": named, "kind": kind, "ecosystems": [ecosystem],
            "aliases": list(aliases), "members": [{"path": root}], "manifests": list(manifests),
            "provenance": "build", "external": list(external)}


def test_a_unit_is_named_as_its_build_tool_names_it_and_referred_to_by_root_when_the_name_cannot_tell():
    """One conversion of the module graph, the product's: Gradle's project path, Maven's coordinates, no name
    where no file gives one; an entry refers to such a unit, or to one of several with the same name, by root."""
    graph = {"modules": [
        _module("g", ".", "gradle-project", "gradle", "billing", manifests=["settings.gradle.kts", "build.gradle.kts"],
                external=["org.postgresql:postgresql"]),
        _module("ga", "app/core", "gradle-project", "gradle", "core", manifests=["app/core/build.gradle.kts"]),
        _module("gi", "tools", "gradle-build", "gradle", "tools", manifests=["tools/settings.gradle.kts"]),
        _module("gb", "buildSrc", "gradle-project", "gradle", "buildSrc", manifests=["buildSrc/build.gradle.kts"]),
        _module("m", "svc", "maven-module", "maven", "svc", aliases=["com.acme:svc"], manifests=["svc/pom.xml"]),
        _module("p", "scripts", "python-package", "python", "scripts", named=False,
                manifests=["scripts/requirements.txt"], external=["requests"]),
        _module("other", "second", "gradle-project", "gradle", "second", manifests=["second/settings.gradle"]),
    ], "edges": [{"source": "g", "target": "ga", "kind": "contains"},
                 {"source": "g", "target": "gi", "kind": "contains"},
                 {"source": "ga", "target": "g", "kind": "declares"}]}
    facts = module_graph.facts(graph)
    names = {u["root"]: u["name"] for u in facts["units"]}
    assert names == {".": ":", "app/core": ":app:core", "tools": ":tools", "buildSrc": ":buildSrc",
                     "svc": "com.acme:svc", "scripts": None, "second": ":"}
    by_root = {u["root"]: u for u in facts["units"]}
    assert by_root["app/core"]["depends_on"] == ["."]  # two builds are `:`; the root tells them apart
    assert {(d["unit"], d["name"]) for d in facts["dependencies"]} == {(".", "org.postgresql:postgresql"),
                                                                    ("scripts", "requests")}
    # an included build is no member
    assert facts["workspace"] == [{"tool": "gradle", "root": ".", "members": ["app/core"]}]
    assert module_graph.references(graph) == {"g": ".", "ga": ":app:core", "gi": ":tools", "gb": ":buildSrc",
                                              "m": "com.acme:svc", "p": "scripts", "other": "second"}


def test_writing_a_snapshot_derives_the_pre_map_before_anything_reads_the_project(tmp_path):
    """The pre-map is the first thing an analysis knows about a project: `snapshot.py write` leaves it beside the
    manifest with the module graph it is built on, and fresh."""
    import subprocess
    project = tmp_path / "proj"
    for rel, text in PROJECTS["go_nested"].items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8", newline="\n")
    scripts = Path(premap.__file__).resolve().parents[1]
    for name, options, expected in (("with", [], True), ("without", ["--no-modules"], False)):
        manifest = tmp_path / name / "manifest.sqlite"
        done = subprocess.run([sys.executable, "-B", str(scripts / "snapshot.py"), "write", str(project), "--out",
                               str(manifest), "--no-engine", "--no-index", *options], cwd=scripts,
                              capture_output=True, text=True, timeout=300)
        assert done.returncode == 0, done.stderr
        assert premap.path(manifest).is_file() is expected
        if expected:
            assert premap.state(manifest)["state"] == "fresh"
            assert "premap:" in done.stdout
            assert premap.roots(premap.ensure(manifest), {"go-module"}, {"go"}) == {"", "_examples/demo"}


def test_the_folders_an_indexer_runs_in_come_from_the_units_and_the_workspaces(tmp_path):
    """Nothing downstream looks for manifests on its own: the roots of the units of the indexer's kinds, and of
    the workspaces of its tools (a virtual Cargo workspace is no crate, yet rust-analyzer starts there)."""
    _, _, go_record = build(tmp_path / "go", "go_nested", runner=replay("go_nested"))
    assert premap.roots(go_record, {"go-module"}, {"go"}) == {"", "_examples/demo"}
    _, _, rust_record = build(tmp_path / "rust", "rust_buildrs", runner=replay("rust_buildrs"))
    assert premap.roots(rust_record, {"cargo-crate"}, {"cargo"}) == {"", "flags", "gen"}
    assert premap.roots(rust_record, {"go-module"}, {"go"}) == set()
    _, _, mixed = build(tmp_path / "mixed", "mixed", sources=(module_graph,))
    assert premap.roots(mixed, {"npm-package"}, {"npm", "pnpm", "lerna"}) == {"web"}
    assert premap.roots(mixed, {"python-project"}, {"uv"}) == {""}


def test_npm_reader_gives_workspace_members_and_entry_files(tmp_path):
    _, _, record = build(tmp_path, "npm_workspace", runner=replay("npm_workspace"))
    units = by_root(record, "npm-package")
    assert set(units) == {".", "packages/a", "packages/b"}
    assert all(any(s.startswith("npm@") for s in u["sources"]) for u in units.values())
    assert units["packages/a"]["config"]["entry_files"] == [
        "packages/a/bin/a.js", "packages/a/dist/index.js", "packages/a/esm/index.mjs"]
    assert units["packages/b"]["depends_on"] == ["a"]
    assert [sorted(w["members"]) for w in record["workspace"] if w["tool"] == "npm"] == [["packages/a", "packages/b"]]


def test_npm_reader_links_a_package_to_the_local_folder_a_file_dependency_names(tmp_path):
    """No workspace: `packages/app` depends on `file:../lib`. npm knows the link from the lockfile; a source that
    asked only for the root and the workspaces would state no edge and hide the one `modules.py` reads."""
    _, _, record = build(tmp_path, "npm_local_link", runner=replay("npm_local_link"))
    units = by_root(record, "npm-package")
    assert set(units) == {"packages/app", "packages/lib"}
    assert units["packages/app"]["depends_on"] == ["@acme/lib"]
    assert units["packages/lib"]["depends_on"] == []
    assert [w for w in record["workspace"] if w["tool"] == "npm"] == []


def _renovate(tmp_path, files: dict, package_files: dict) -> dict:
    """What the Renovate reader keeps of a report, on a project of `files`."""
    project = tmp_path / "proj"
    for rel, text in files.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    report = {"repositories": {"local": {"packageFiles": package_files}}}
    with open_snapshot(manifest) as store:
        context = premap.Context(manifest, store)
        return renovate.read(context, [], [{"returncode": 0, "stdout": json.dumps(report), "stderr": ""}])["facts"]


def test_a_constraint_renovate_extracts_from_the_file_is_a_toolchain_not_a_package(tmp_path):
    """Poetry's `python`, Composer's `php`, pub's `dart` and `flutter`, global.json's SDK: the same file states
    them as constraints. Not packages a unit uses: `rich` is one."""
    files = {"pyproject.toml": '[tool.poetry]\nname = "app"\n[tool.poetry.dependencies]\npython = "^3.10"\nrich = "^13"\n'}
    facts = _renovate(tmp_path, files, {"poetry": [{"packageFile": "pyproject.toml", "extractedConstraints": {"python": "^3.10"},
                                                    "deps": [{"depName": "python", "currentValue": "^3.10", "depType": "dependencies"},
                                                             {"depName": "rich", "currentValue": "^13", "depType": "dependencies"}]}]})
    assert facts == {"toolchains": [{"tool": "python", "version": "^3.10", "declared_in": "pyproject.toml"}],
                     "packages": [{"ecosystem": "pypi", "name": "rich", "declared_in": "pyproject.toml",
                                   "version": "^13"}]}


def test_a_pub_sdk_is_the_module_graph_s_toolchain_and_no_package(tmp_path):
    """`flutter: {sdk: flutter}` is the Flutter SDK, which the pubspec's `sdk:` names: a toolchain, not the package
    Renovate's pub manager reports; `flutter_test`, a package the SDK ships, stays one."""
    files = {"pubspec.yaml": "name: app\ndependencies:\n  flutter:\n    sdk: flutter\n  dio: ^5.0.0\n"
                             "dev_dependencies:\n  flutter_test:\n    sdk: flutter\n"}
    facts = _renovate(tmp_path, files, {"pub": [{"packageFile": "pubspec.yaml", "deps": [
        {"depName": "flutter", "depType": "dependencies", "currentValue": "", "datasource": "dart"},
        {"depName": "dio", "depType": "dependencies", "currentValue": "^5.0.0", "datasource": "dart"},
        {"depName": "flutter_test", "depType": "dev_dependencies", "currentValue": "", "datasource": "dart"}],
        "extractedConstraints": {}}]})
    assert [p["name"] for p in facts["packages"]] == ["dio", "flutter_test"]
    with open_snapshot(tmp_path / "out" / "manifest.sqlite") as store:
        found = module_graph.run(premap.Context(tmp_path / "out" / "manifest.sqlite", store))["facts"]
    assert found["toolchains"] == [{"tool": "flutter", "declared_in": "pubspec.yaml"}]
    assert {p["name"] for p in found["packages"]} == {"dio", "flutter_test"}


def test_the_sdk_of_global_json_is_the_dotnet_toolchain(tmp_path):
    """Renovate names it `dotnet-sdk`: the tool the build runs on is `dotnet`, the name the preparation installs."""
    files = {"global.json": '{"sdk": {"version": "8.0.404", "rollForward": "latestFeature"}}\n'}
    facts = _renovate(tmp_path, files, {"nuget": [{"packageFile": "global.json", "deps": [
        {"depName": "dotnet-sdk", "depType": "dotnet-sdk", "currentValue": "8.0.404"}],
        "extractedConstraints": {"dotnet-sdk": "8.0.404"}}]})
    assert facts == {"toolchains": [{"tool": "dotnet", "version": "8.0.404", "declared_in": "global.json"}]}


def test_the_bun_a_workflow_sets_up_is_the_bun_toolchain(tmp_path):
    """real-app-full-stack-fastapi: Bun's version is only in its workflows, `oven-sh/setup-bun` with
    `bun-version`, which Renovate's github-actions manager reports as the npm package `bun` (`uses-with`,
    known-actions/npm.ts); the action itself is no toolchain."""
    files = {"package.json": '{"name": "a", "scripts": {"test": "bun run --filter frontend test"}}\n'}
    facts = _renovate(tmp_path, files, {"github-actions": [{"packageFile": ".github/workflows/playwright.yml", "deps": [
        {"depName": "oven-sh/setup-bun", "currentValue": "v2.2.0", "depType": "action"},
        {"depName": "bun", "packageName": "bun", "datasource": "npm", "currentValue": "1.3.12", "depType": "uses-with"},
        {"depName": "@biomejs/biome", "packageName": "@biomejs/biome", "currentValue": "2.6.3",
         "depType": "uses-with"}]}]})
    assert facts["toolchains"] == [{"tool": "bun", "version": "1.3.12",
                                    "declared_in": ".github/workflows/playwright.yml"}]


def test_a_constraint_no_file_writes_is_left_out_and_a_written_one_stays(tmp_path):
    """Renovate derives `npm >=7` from the lockfile's format and repeats the root's `packageManager` on every
    member: a toolchain is what a file writes."""
    files = {"package.json": '{"name": "a", "engines": {"node": ">=18"}}\n', "web/package.json": '{"name": "w"}\n'}
    facts = _renovate(tmp_path, files, {"npm": [
        {"packageFile": "package.json", "extractedConstraints": {"node": ">=18", "npm": ">=7"}, "deps": []},
        {"packageFile": "web/package.json", "extractedConstraints": {"npm": "10.8.2"}, "deps": []}]})
    assert facts["toolchains"] == [{"tool": "node", "version": ">=18", "declared_in": "package.json"}]


def test_the_maven_wrapper_gives_maven_and_not_its_own_version(tmp_path):
    files = {"pom.xml": "<project/>\n", ".mvn/wrapper/maven-wrapper.properties": "distributionUrl=x\n"}
    facts = _renovate(tmp_path, files, {"maven-wrapper": [{"packageFile": ".mvn/wrapper/maven-wrapper.properties", "deps": [
        {"depName": "maven", "currentValue": "3.9.9"}, {"depName": "maven-wrapper", "currentValue": "3.3.2"}]}]})
    assert [(t["tool"], t["version"]) for t in facts["toolchains"]] == [("maven", "3.9.9")]


def test_the_packages_a_file_declares_give_no_fact_and_its_runtime_is_a_toolchain(tmp_path):
    """A Bazel module, a Conan file, a Helm chart, a Terraform module: their packages are each analyzer's; the
    Terraform release a file requires is a toolchain."""
    files = {"MODULE.bazel": 'bazel_dep(name = "rules_cc", version = "0.0.9")\n', "conanfile.txt": "[requires]\nfmt/10.2.1\n",
             "main.tf": 'terraform {\n  required_version = ">= 1.6.0"\n}\n', "charts/shop/Chart.yaml": "name: shop\n"}
    facts = _renovate(tmp_path, files, {
        "bazel-module": [{"packageFile": "MODULE.bazel", "deps": [{"depName": "rules_cc", "currentValue": "0.0.9", "depType": "bazel_dep"}]}],
        "conan": [{"packageFile": "conanfile.txt", "deps": [{"depName": "fmt", "currentValue": "10.2.1", "depType": "requires"}]}],
        "terraform": [{"packageFile": "main.tf", "deps": [
            {"depName": "cloudposse/label/null", "currentValue": "0.25.0", "depType": "module"},
            {"depName": "hashicorp/terraform", "currentValue": ">= 1.6.0", "depType": "required_version"}]}],
        "helmv3": [{"packageFile": "charts/shop/Chart.yaml", "deps": [{"depName": "postgresql", "currentValue": "16.2.1"}]}]})
    assert facts == {"toolchains": [{"tool": "terraform", "version": ">= 1.6.0", "declared_in": "main.tf"}]}


def test_an_image_tag_gives_the_version_renovates_docker_versioning_reads_and_one_without_stays_a_gap(tmp_path):
    """mix-real-tududi's `FROM node:22-alpine`: Renovate's docker versioning reads a tag as a version, past a `v`, up
    to the first hyphen, and a compatibility suffix, the image's variant: Node 22 on Alpine. A tag whose first part
    is no version, or that looks like a commit hash, stays as the file writes it, which no preparation installs."""
    import preparation

    def image(name, tag):
        return {"depName": name, "currentValue": tag, "datasource": "docker", "depType": "final"}
    facts = _renovate(tmp_path, {"Dockerfile": "FROM node:22-alpine\n"}, {
        "dockerfile": [{"packageFile": "Dockerfile", "deps": [
            image("node", "22-alpine"), image("python", "v3.12.4-slim-bookworm"), image("eclipse-temurin", "21.0.5_11-jdk"),
            image("ruby", "alpine"), image("golang", "deadbee")]}],
        "docker-compose": [{"packageFile": "docker-compose.yml", "deps": [image("node", "lts-alpine")]}]})
    assert [(t["tool"], t["version"], t["declared_in"]) for t in facts["toolchains"]] == [
        ("node", "22", "Dockerfile"), ("python", "3.12.4", "Dockerfile"), ("java", "21.0.5_11", "Dockerfile"),
        ("ruby", "alpine", "Dockerfile"), ("go", "deadbee", "Dockerfile"), ("node", "lts-alpine", "docker-compose.yml")]
    plan = preparation.toolchains(facts["toolchains"])
    assert [line.split(" install ")[1].split(" ")[0] for line in plan["lines"] if " install " in line] == [
        "node@22", "python@3.12.4"]
    assert [(g["tool"], g["version"]) for g in plan["gaps"]] == [
        ("java", "21.0.5_11"), ("ruby", "alpine"), ("go", "deadbee"), ("node", "lts-alpine")]


def test_a_dev_container_image_s_tag_gives_its_language_s_version_by_that_image_family_s_scheme(tmp_path):
    """real-app-kotlinconf's devcontainer starts from mcr.microsoft.com/devcontainers/java:1-21. That family's tags
    are `<image version>-<Java version>[-<OS>]` or `<Java version>[-<OS>]` (devcontainers/images, src/java/README.md:
    `3.1.9-11-bookworm`, `25-trixie`): Java 21, not the image's own 1."""
    def image(tag):
        return {"depName": "mcr.microsoft.com/devcontainers/java", "currentValue": tag, "datasource": "docker",
                "depType": "image"}
    facts = _renovate(tmp_path, {".devcontainer/devcontainer.json": "{}\n"}, {"devcontainer": [
        {"packageFile": ".devcontainer/devcontainer.json",
         "deps": [image(tag) for tag in ("1-21", "3.1.9-11-bookworm", "25-trixie", "17", "latest")]}]})
    assert [t["version"] for t in facts["toolchains"]] == ["21", "11", "25", "17", "latest"]
    assert {t["tool"] for t in facts["toolchains"]} == {"java"}


def test_the_same_toolchain_in_one_file_is_one_fact_with_or_without_a_fragment():
    parts = [part("jvm-files", "reader", toolchains=[{"tool": "gradle", "version": "8.11.1",
                                                      "declared_in": "gradle/wrapper/gradle-wrapper.properties#distributionUrl"}]),
             part("renovate", "reader", toolchains=[{"tool": "gradle", "version": "8.11.1",
                                                     "declared_in": "gradle/wrapper/gradle-wrapper.properties"}])]
    [entry] = premap.join(parts)["toolchains"]
    assert entry["sources"] == ["jvm-files", "renovate"]


def test_renovate_reader_gives_declared_toolchains(tmp_path):
    _, _, record = build(tmp_path, "versions", runner=replay("versions"))
    label = premap.label(renovate)
    node = {(t["declared_in"], t["version"]) for t in record["toolchains"] if t["tool"] == "node" and label in t["sources"]}
    assert node >= {(".nvmrc", "20.11.0"), ("package.json", ">=20")}
    assert "dependencies" not in record


def test_a_repository_renovate_ends_before_reading_its_files_is_a_gap_not_an_empty_answer(tmp_path):
    """Renovate's local platform reads the project's config and resolves the presets it extends: with the network
    blocked one of GitHub's ends the repository, and so does a config that disables Renovate, each with exit 0 and no
    file read (answers recorded on Modal, `fixtures/premap/renovate/ended.json`). Each is a `model_failed` gap that says
    why, not an extraction that found nothing."""
    recorded = json.loads((FIXTURES / "renovate" / "ended.json").read_text(encoding="utf-8"))
    files = {"pyproject.toml": '[project]\nname = "syn"\nversion = "0"\nrequires-python = ">=3.12"\n',
             ".python-version": "3.12\n", "main.py": "print(1)\n"}
    for case, said in (("preset", "Host error: getaddrinfo EAI_AGAIN api.github.com: https://api.github.com/repos/"
                                  "GoogleCloudPlatform/kubernetes-engine-samples/contents/.github/renovate-configs/"
                                  "dee-platform-ops.json5"), ("disabled", "(disabled)")):
        project, manifest = tmp_path / case / "proj", tmp_path / case / "out" / "manifest.sqlite"
        for rel, text in {**files, "renovate.json": json.dumps(recorded[case]["renovate.json"])}.items():
            (project / rel).parent.mkdir(parents=True, exist_ok=True)
            (project / rel).write_text(text, encoding="utf-8", newline="\n")
        snapshot.read_project(project, manifest)
        answer = recorded[case]["answer"]
        assert answer["returncode"] == 0
        with open_snapshot(manifest) as store:
            result = renovate.read(premap.Context(manifest, store), [], [answer])
        assert "toolchains" not in result["facts"] and "packages" not in result["facts"]
        [gap] = [g for g in result["gaps"] if g["kind"] == "model_failed"]
        assert gap["detail"].startswith("renovate ended the repository (") and said in gap["detail"], gap


# -------------------------------------------------------- requirements files

def test_a_requirements_file_alone_makes_a_unit_and_its_includes_belong_to_it(tmp_path):
    _, _, record = build(tmp_path, "req_includes")
    units = by_root(record, "python-project")
    assert set(units) == {".", "libs/localpkg"}
    root = units["."]
    assert (root["name"], root["manifest"], root["depends_on"]) == (None, "requirements.txt", ["localpkg"])
    assert root["config"]["requirements"] == ["requirements-dev.txt", "requirements.txt", "requirements/base.txt"]
    assert root["registries"] == ["https://github.com", "https://pypi.example.org"]  # an index, a VCS requirement


def test_the_links_and_url_requirements_of_a_requirements_file_are_registries(tmp_path):
    extra = ("-f https://download.example.com/wheels\n-f ./wheels\n"
             "pkg @ https://user:secret@files.example.net/pkg-1.0-py3-none-any.whl\n"
             "-e git+ssh://git@gitlab.example.com/acme/tool.git#egg=tool\nhttps://archive.example.org/p-1.0.tar.gz\n")
    _, _, record = build(tmp_path, "req_includes", extra={"requirements-urls.txt": extra})
    assert by_root(record, "python-project")["."]["registries"] == [
        "https://archive.example.org", "https://download.example.com", "https://files.example.net",
        "https://github.com", "https://pypi.example.org", "ssh://gitlab.example.com"]


def test_a_requirement_path_outside_the_copy_is_refused_and_one_inside_is_unresolved(tmp_path):
    """The preparation's rule (`preparation.refusal`): a path outside the copy or absolute is
    `local_dependency_refused`; one inside the copy with no build unit there stays `dependency_unresolved`."""
    extra = {"requirements-local.txt": "../outside/pkg\n/srv/abs/pkg\n./missing\n"}
    _, _, record = build(tmp_path, "req_includes", extra=extra)
    assert {(g["entry"], g["file"], g["path"]) for g in gaps(record, "local_dependency_refused")} == {
        ("../outside/pkg", "requirements-local.txt", "."), ("/srv/abs/pkg", "requirements-local.txt", ".")}
    assert [g["detail"] for g in gaps(record, "dependency_unresolved")] == ["./missing: no build unit at missing"]


def test_a_pip_compile_output_is_the_lock_of_its_in_file(tmp_path):
    _, _, record = build(tmp_path, "req_pip_tools")
    [unit] = by_root(record, "python-project").values()
    assert unit["manifest"] == "requirements.in"
    assert unit["config"]["requirements"] == ["dev-requirements.in", "dev-requirements.txt", "requirements.in",
                                              "requirements.txt"]


def test_service_folders_with_requirements_are_units_and_one_beside_a_pyproject_joins_it(tmp_path):
    _, _, record = build(tmp_path, "req_services")
    units = by_root(record, "python-project")
    assert set(units) == {"vote", "load-gen", "functions-python"}
    assert units["vote"]["manifest"] == "vote/requirements.txt" and units["vote"]["name"] is None
    assert units["functions-python"]["manifest"] == "functions-python/pyproject.toml"
    assert units["functions-python"]["config"]["requirements"] == ["functions-python/requirements-test.txt"]
    assert [r["root"] for r in premap.python_runs(record)] == ["functions-python", "load-gen", "vote"]
    assert "functions-python/requirements-test.txt" in premap.python_runs(record)[0]["manifests"]
    assert not [g for g in gaps(record, "code_outside_units") if g["language"] == "Python"]


# ---------------------------------------------------------- the stage's views

def test_python_runs_are_the_outermost_python_roots_with_their_manifests(tmp_path):
    _, _, record = build(tmp_path, "python_nested")
    assert premap.python_runs(record) == [
        {"root": "functions-python", "name": "shop-functions",
         "manifests": ["functions-python/pyproject.toml", "functions-python/tools/probe/pyproject.toml"],
         "source_roots": ["tools/probe/src"]},
        {"root": "utils/arena", "name": "arena", "manifests": ["utils/arena/pyproject.toml"], "source_roots": []}]


def test_a_uv_workspace_is_one_python_run_at_its_root(tmp_path):
    _, _, record = build(tmp_path, "uv_workspace", runner=replay("uv_workspace"))
    assert premap.python_runs(record) == [
        {"root": "", "name": None, "source_roots": [],
         "manifests": ["packages/app/pyproject.toml", "packages/core/pyproject.toml", "pyproject.toml", "uv.lock"]}]


# -------------------------------------------------------------------- gaps

def test_an_absent_submodule_is_excluded_and_a_gap(tmp_path):
    _, _, record = build(tmp_path, "submodule_absent")
    [excluded] = [e for e in record["excluded"] if e["why"] == "submodule"]  # `.gitmodules` is Linguist's vendored
    assert excluded["path"] == "vendor/logfmt/" and excluded["why"] == "submodule"
    [gap] = gaps(record, "submodule_absent")
    assert gap["path"] == "vendor/logfmt" and gap["source"].startswith("gitmodules@")


def test_python_code_without_a_manifest_is_a_gap_not_a_unit(tmp_path):
    _, _, record = build(tmp_path, "loose_python")
    assert {u["kind"] for u in record["units"]} == {"npm-package"}
    [gap] = gaps(record, "code_outside_units")
    assert gap["path"] == "scripts" and gap["language"] == "Python" and gap["files"] == 2


def test_the_module_graph_gaps_are_kept_with_their_source(tmp_path):
    _, _, record = build(tmp_path, "mixed", extra={"broken/package.json": "{not json"})
    [gap] = gaps(record, "manifest_unreadable")
    assert gap["path"] == "broken/package.json" and gap["source"].startswith("modules.py@")


def test_a_unit_another_source_states_never_comes_back_as_a_fact_of_the_module_graph(tmp_path):
    """`modules.sync_with_premap` writes the pre-map's units into modules.json: the pre-map derived again states
    only what the manifests and its sources state, not what the previous pre-map put there."""
    import modules
    stating = fake("model-units", "model", lambda _: {"facts": {"units": [unit("lib", "cargo-crate", "gen")]}})
    _, manifest, first = build(tmp_path, "mixed", sources=(module_graph, stating), extra={"lib/src/lib.rs": "pub fn a() {}\n"})
    assert ("lib", "cargo-crate") in {(u["root"], u["kind"]) for u in first["units"]}
    modules.sync_with_premap(manifest, first)
    again = premap.write(manifest, sources=(module_graph,))
    assert {(u["root"], u["kind"]) for u in again["units"]} == {(".", "python-project"), ("web", "npm-package")}


def test_the_build_units_come_from_the_snapshot_never_from_modules_json(tmp_path, monkeypatch):
    """The pre-map derives the build units in memory (`module_derive.build_graph`): the units and workspaces of
    the module graph, no `modules.json` read or written, and no gap of the declared or proposed modules."""
    import module_derive
    import modules

    def refused(*_, **__):
        raise AssertionError("the pre-map reads modules.json")

    monkeypatch.setattr(modules, "ensure_graph", refused)
    shape = lambda u: json.dumps({k: u.get(k) for k in ("root", "kind", "name", "manifest", "depends_on")})  # noqa: E731
    members = lambda w: (w["tool"], w["root"], sorted(w["members"]))  # noqa: E731
    for name in ("mixed", "gradle", "npm_workspace", "uv_workspace", "go_nested", "jvm_files", "req_services"):
        extra = {"codebase-modules.json": "{not json"} if name == "mixed" else None
        _, manifest, record = build(tmp_path / name, name, sources=(module_graph,), extra=extra)
        with open_snapshot(manifest) as store:
            graph = module_graph.facts(module_derive.derive(store, ledger=[]))
        assert record["units"] and sorted(map(shape, record["units"])) == sorted(map(shape, graph["units"])), name
        assert sorted(map(members, record.get("workspace", []))) == sorted(map(members, graph["workspace"])), name
        assert not modules.graph_name(manifest).exists(), name
        assert name != "mixed" or not gaps(record, "modules_unreadable")


def test_two_build_units_in_one_folder_keep_their_ambiguous_ownership_as_a_gap(tmp_path):
    """Which of two units in one folder owns its files the build tells apart, not the folder: a fact of the build
    units that the pre-map keeps as the module graph states it."""
    extra = {"package.json": '{"name": "site"}', "main.py": "VALUE = 1\n"}
    _, _, record = build(tmp_path, "mixed", sources=(module_graph,), extra=extra)
    [gap] = gaps(record, "ownership_ambiguous")
    assert gap["path"] == "." and gap["source"].startswith("modules.py@")
    assert gap["detail"] == "Directory scope cannot distinguish build ownership: acme, site"


# ------------------------------------------------------------------ preparation

def model(name, commands, read):
    return SimpleNamespace(NAME=name, VERSION="1", RANK="model", commands=commands, read=read)


def test_the_readers_run_first_and_their_toolchains_go_to_the_runner(tmp_path):
    """The model source comes first in the sources, the reader stating Go 1.22.4 after it: the runner still gets
    that version, and the statuses keep the sources' order."""
    asked = []

    def runner(commands, toolchains=()):
        asked.append([(t["tool"], t["version"]) for t in toolchains])
        return [{"returncode": 0, "stdout": "", "stderr": "", "root": "/p"} for _ in commands]

    built = model("built", lambda context: [{"tool": "go", "argv": ["go"], "cwd": ".", "env": {}}],
                  lambda context, commands, results: {"facts": {}})
    declared = fake("declared", "reader", lambda context: {"facts": {"toolchains": [
        {"tool": "go", "version": "1.22.4", "declared_in": "go.mod#go"}]}})
    _, _, record = build(tmp_path, "mixed", sources=(built, declared), runner=runner)
    assert asked == [[("go", "1.22.4")]]
    assert [s["source"] for s in record["sources"]] == ["built@1", "declared@1"]


def test_a_runner_that_takes_no_toolchains_still_runs(tmp_path):
    built = model("built", lambda context: [{"tool": "go", "argv": ["go"], "cwd": ".", "env": {}}],
                  lambda context, commands, results: {"facts": {}})
    _, _, record = build(tmp_path, "mixed", sources=(built,), runner=lambda commands: [
        {"returncode": 0, "stdout": "", "stderr": "", "root": "/p"} for _ in commands])
    assert record["sources"][0]["state"] == "ran"


def test_the_gaps_the_runner_hands_back_are_the_sources_gaps(tmp_path):
    """The runner's preparation could not install Go 1.22.4: the gap rides on the answers and lands in the record
    with the source's label; the commands' answers still reach `read`."""
    gap = {"kind": "toolchain_unavailable", "tool": "go", "version": "1.22.4", "detail": "mise install failed"}

    def runner(commands, toolchains=()):
        return [{"returncode": 0, "stdout": "x", "stderr": "", "root": "/p", "gaps": [gap] if n == 0 else []}
                for n, _ in enumerate(commands)]

    read = []
    built = model("built", lambda context: [{"tool": "go", "argv": ["go"], "cwd": ".", "env": {}}] * 2,
                  lambda context, commands, results: read.append([r["stdout"] for r in results]) or {"facts": {}})
    _, _, record = build(tmp_path, "mixed", sources=(built,), runner=runner)
    assert read == [["x", "x"]]
    assert [g for g in record["gaps"] if g["kind"] == "toolchain_unavailable"] == [{**gap, "source": "built@1"}]


# ------------------------------------------------------------------ analyzers

def test_files_no_reader_reads_are_a_no_analyzer_gap_from_linguists_catalogue(tmp_path):
    """A Ruby file and a PHP file are counted by name and type from the catalogue alone; Markdown and JSON are not
    programming languages."""
    extra = {"lib/a.rb": "puts 1\n", "lib/b.rb": "puts 2\n", "web/index.php": "<?php\n", "NOTES.md": "# n\n",
             "data.json": "{}\n"}
    _, _, record = build(tmp_path, "mixed", extra=extra)
    assert "languages" not in record
    found = {gap["language"]: gap for gap in gaps(record, "no_analyzer")}
    assert found["Ruby"]["files"] == 2 and found["Ruby"]["source"] == premap.RULE
    assert found["Hack / PHP"]["files"] == 1  # `.php` is listed by two languages: Linguist's order, no guess
    assert set(found) == {"Ruby", "Hack / PHP"}  # `.md` is Markdown or GCC Machine Description: two types, no gap


def test_the_unit_kinds_able_to_index_a_language_are_the_ones_its_analyzer_declares(tmp_path):
    """The pre-map keeps no table of its own: a language is indexed by the unit kinds its analyzer declares, so a
    Java file whose only unit is of a kind no analyzer takes (sbt) is code outside the units; a language without
    an analyzer is no row (its gap is `no_analyzer`), nor is one whose analyzer takes no unit."""
    import indexers
    from premap import suffix_table
    table = premap.indexed_by()
    for analyzer in indexers.analyzers():
        for language in analyzer.LANGUAGES:
            name = suffix_table.NAMES.get(language, language)
            assert table.get(name, frozenset()) == frozenset(analyzer.UNIT_KINDS), name
    assert "SQL" not in table and table["Vue"] == table["Svelte"] == frozenset({"npm-package"})
    _, _, record = build(tmp_path, "mixed", extra={"legacy/build.sbt": 'name := "legacy"\n',
                                                   "legacy/src/main/java/A.java": "class A {}\n"})
    assert "legacy" in by_root(record, "sbt-project")
    [gap] = [g for g in gaps(record, "code_outside_units") if g["language"] == "Java"]
    assert gap["path"] == "legacy/src/main/java" and "sbt-project" not in gap["detail"]


def test_python_code_outside_every_project_makes_the_checkout_one_run():
    """Tests and scripts beside a Python project are code too: when the pre-map finds Python files no unit
    holds, the checkout is the run, and each project inside keeps its folder as the root of its own imports."""
    record = {"units": [{"kind": "python-project", "root": "pkg", "name": "pkg", "manifest": "pkg/pyproject.toml",
                         "sources": [], "source_roots": ["pkg/src"]}], "workspace": [],
              "gaps": [{"kind": "code_outside_units", "language": "Python", "path": "tests", "files": 3}]}
    assert premap.python_runs(record) == [{"root": "", "name": None, "manifests": ["pkg/pyproject.toml"],
                                           "source_roots": ["pkg/src"], "unit_roots": ["pkg"]}]
    record["gaps"] = [{"kind": "code_outside_units", "language": "Go", "path": "tools", "files": 1}]
    assert [run["root"] for run in premap.python_runs(record)] == ["pkg"]


# The sources with model commands that no build tool of the registry names, each with why.
NOT_A_BUILD_TOOL = {
    "renovate": "the declared files of every manager, not one build tool's model",
    "compose": "the services Compose declares, not a build",
    "buildkit": "the stages of a Dockerfile, the images: the stack's services",
    "cmake": "the registry has no entry for it until the fork's .6 (T1.B.4)",
    "meson": "the registry has no entry for it until the fork's .6 (T1.B.4)",
    "bazel": "the registry has no entry for it until the fork's .6 (T1.B.4)",
    "make": "the registry has no entry for it until the fork's .6 (T1.B.4)",
    "sbt": "the registry has no entry for it until the fork's .6 (T1.B.4)",
    "dotnet": "the registry has no entry for it until the fork's .6 (T1.B.4)",
}


def test_build_tools_names_registry_tools_and_pre_map_sources_and_every_model_source_has_a_tool():
    import service_registry
    tools = {e["id"] for e in service_registry.load()["entries"] if service_registry.entry_category(e) == "tool"}
    named = {name for names in premap.BUILD_TOOLS.values() for name in names}
    assert set(premap.BUILD_TOOLS) <= tools
    assert named <= {source.NAME for source in premap.SOURCES}
    modelled = {source.NAME for source in premap.SOURCES if hasattr(source, "commands")}
    assert modelled - named == set(NOT_A_BUILD_TOOL)


def test_a_source_build_tools_names_runs_only_for_a_tool_the_stack_found():
    """`find_modules` follows the stack: a source of `build-tools.json` runs for a tool the stack found, one it does not
    name runs on every project, and without the stack's tools (None) every source runs."""
    named = {name for names in premap.BUILD_TOOLS.values() for name in names}
    kept = {source.NAME for source in premap._chosen(None, ["cargo"])}
    assert "cargo" in kept and not (named - {"cargo"}) & kept
    assert {source.NAME for source in premap.SOURCES} - named <= kept  # renovate, compose, noir, cmake...
    assert premap._chosen(None, None) == premap.SOURCES
    assert {source.NAME for source in premap._chosen(None, ["nodejs"])} & named == {"npm", "npm-files", "npm-tests",
                                                                                   "npm-start"}


def test_the_pre_map_follows_the_build_tools_of_the_stack_record_of_its_inventory(tmp_path):
    """A stack record of this inventory chooses the sources, and the pre-map is stale once it names other tools; a
    record of another inventory chooses nothing."""
    import stack_recognition
    from snapshot_store import inventory_digest
    _, manifest, everything = build(tmp_path, "npm_workspace")
    assert "npm-files" in {s["source"].partition("@")[0] for s in everything["sources"]}
    with open_snapshot(manifest) as store:
        digest = inventory_digest(store)

    def stack(tools, inventory=digest):
        stack_recognition.path(manifest).write_text(json.dumps({
            "schema": stack_recognition.SCHEMA, "inventory_digest": inventory, "tools": tools}), encoding="utf-8")

    stack(["golang"])
    assert premap.state(manifest)["state"] == "stale"
    record = premap.ensure(manifest)
    stated = {s["source"].partition("@")[0] for s in record["sources"]}
    assert not {"npm", "npm-files", "npm-tests", "npm-start"} & stated and {"go", "renovate"} <= stated
    assert premap.state(manifest)["state"] == "fresh"
    stack(["golang"], inventory="another")
    assert premap.state(manifest)["state"] == "stale"  # every source again


def test_a_bom_and_a_pom_parent_are_dependencies_with_their_role(tmp_path):
    """Renovate's maven depTypes: `import` is a BOM of `dependencyManagement`, `parent` and `parent-root` the POM parent;
    both stay dependencies, with `role`; a dependency to compile with has none."""
    files = {"pom.xml": "<project/>\n"}
    facts = _renovate(tmp_path, files, {"maven": [{"packageFile": "pom.xml", "deps": [
        {"depName": "org.springframework.boot:spring-boot-starter-parent", "currentValue": "3.4.0", "depType": "parent"},
        {"depName": "org.acme:root", "currentValue": "1", "depType": "parent-root"},
        {"depName": "org.springframework.cloud:spring-cloud-dependencies", "currentValue": "2025.1.0", "depType": "import",
         "sharedVariableName": "spring-cloud.version"},
        {"depName": "junit:junit", "currentValue": "4.13.2", "depType": "test"}]}]})
    assert [(p["name"], p.get("role")) for p in facts["packages"]] == [
        ("org.springframework.boot:spring-boot-starter-parent", "parent"), ("org.acme:root", "parent"),
        ("org.springframework.cloud:spring-cloud-dependencies", "bom"), ("junit:junit", None)]


def test_a_composer_platform_requirement_is_no_package(tmp_path):
    """`php`, `ext-*` and `lib-*` are what the PHP running the project has (Composer's platform packages): no package a
    unit downloads. A vendor's package whose name starts the same way stays."""
    files = {"composer.json": '{"require": {"php": "^8.2", "ext-json": "*", "lib-icu": "*", "monolog/monolog": "^3"}}\n'}
    facts = _renovate(tmp_path, files, {"composer": [{"packageFile": "composer.json", "deps": [
        {"depName": "php", "currentValue": "^8.2", "depType": "require", "datasource": "github-tags"},
        {"depName": "ext-json", "currentValue": "*", "depType": "require", "skipReason": "unsupported"},
        {"depName": "lib-icu", "currentValue": "*", "depType": "require"},
        {"depName": "phpunit/phpunit", "currentValue": "^11", "depType": "require-dev"},
        {"depName": "php-http/client", "currentValue": "^1", "depType": "require"}]}]})
    assert [p["name"] for p in facts["packages"]] == ["phpunit/phpunit", "php-http/client"]
