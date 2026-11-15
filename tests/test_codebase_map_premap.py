"""The pre-map: its record, the join of sources, model commands read from stored outputs, the declared gaps."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))

import premap  # noqa: E402
from premap import cargo, enry, go, npm, renovate, tsc, uv  # noqa: E402
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
    snapshot.write_snapshot(project, manifest)
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
    for facet in ("units", "dependencies"):
        assert record[facet] and all(item["sources"] and all("@" in s for s in item["sources"]) for item in record[facet])
    assert "languages" not in record  # go-enry runs in the container only
    assert {(d["unit"], d["name"]) for d in record["dependencies"]} >= {("acme", "requests"), ("@acme/web", "react")}
    assert {s["source"].split("@")[0]: s["state"] for s in record["sources"]} == {
        "modules.py": "ran", "python-build": "not_needed", "requirements": "not_needed", "npm-files": "ran", "jvm-files": "not_needed",
        "gitmodules": "not_needed",
        "go-enry": "not_run", "renovate": "not_run", "go": "not_needed", "cargo": "not_needed", "uv": "not_needed",
        "tsc": "not_needed", "npm": "not_run"}
    assert all(u["run"] == {"executes_project_code": False, "reason": ""} for u in record["units"])
    assert "needs" not in record


def test_fresh_until_the_snapshot_changes(tmp_path):
    project, manifest, _ = build(tmp_path, "mixed")
    assert premap.state(manifest)["state"] == "fresh"
    (project / "web" / "index.js").write_text("export const b = 2;\n", encoding="utf-8")
    snapshot.write_snapshot(project, manifest)
    assert premap.state(manifest)["state"] == "stale"
    assert premap.ensure(manifest)["schema"] == premap.SCHEMA
    assert premap.state(manifest)["state"] == "fresh"


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
    joined = premap.join([part("a@1", "reader", dependencies=[{"unit": "u", "name": "Requests", "declared_in": "pyproject.toml"}]),
                          part("b@1", "model", dependencies=[{"unit": "u", "name": "requests", "declared": ">=2",
                                                              "resolved": "2.32.0", "declared_in": "pyproject.toml"}])])
    [only] = joined["dependencies"]
    assert only["resolved"] == "2.32.0" and "conflicts" not in only and only["sources"] == ["b@1", "a@1"]


def test_config_keys_join_one_by_one():
    joined = premap.join([part("a@1", "reader", units=[unit("app", "npm-package", "app", config={"tsconfig": ["app/tsconfig.json"]})]),
                          part("b@1", "model", units=[unit("app", "npm-package", "app", config={"paths": {"@/*": ["app/src/*"]},
                                                                                             "tsconfig": ["app/tsconfig.json"]})])])
    [only] = joined["units"]
    assert only["config"] == {"paths": {"@/*": ["app/src/*"]}, "tsconfig": ["app/tsconfig.json"]}
    assert "conflicts" not in only


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


def test_every_command_is_data_with_its_network():
    for source in (go, cargo, uv, renovate, tsc, enry, npm):
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


def test_package_folders_come_only_from_what_a_build_configuration_declares(tmp_path):
    _, _, record = build(tmp_path, "declared_package_dirs")
    units = by_root(record, "python-project")
    assert units["."]["source_roots"] == ["src"] and units["tools"]["source_roots"] == ["tools/lib"]
    assert all(any(s.startswith("python-build@") for s in u["sources"]) for u in units.values())
    _, _, plain = build(tmp_path / "plain", "mixed")
    assert all("source_roots" not in u for u in plain["units"] if u["kind"] == "python-project")


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


def test_cargo_reader_gives_crates_and_the_build_script_as_a_fact(tmp_path):
    _, _, record = build(tmp_path, "rust_buildrs", runner=replay("rust_buildrs"))
    crates = by_root(record, "cargo-crate")
    assert set(crates) == {"gen", "flags"} and all(premap.label(cargo) in c["sources"] for c in crates.values())
    assert crates["gen"]["config"]["build_script"] == "gen/build.rs" and crates["gen"]["source_roots"] == ["gen/src"]
    assert all(c["run"]["executes_project_code"] is False for c in crates.values())
    assert sorted(g["path"] for g in gaps(record, "not_executed")) == ["flags/build.rs", "gen/build.rs"]
    assert [t["version"] for t in record["toolchains"] if t["declared_in"] == "flags/Cargo.toml"] == ["1.80"]
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


def test_tsc_reader_gives_the_tsconfigs_in_reference_order_and_their_aliases(tmp_path):
    _, _, record = build(tmp_path, "tsc_alias", runner=replay("tsc_alias"))
    [web] = by_root(record, "npm-package").values()
    assert premap.label(tsc) in web["sources"]
    assert web["config"]["tsconfig"] == ["tsconfig.json", "tsconfig.app.json", "tsconfig.node.json", "tools/tsconfig.json"]
    assert web["config"]["paths"] == {"@/*": ["src/*"]}
    [failed] = [g for g in gaps(record, "model_failed") if g["source"] == premap.label(tsc)]
    assert failed["path"] == "tools/tsconfig.json"


def test_enry_reader_gives_languages_and_the_files_to_leave_out_with_why(tmp_path):
    _, _, record = build(tmp_path, "enry_files", runner=replay("enry_files"))
    label = premap.label(enry)
    assert {(e["path"], e["why"]) for e in record["excluded"] if label in e["sources"]} == {
        ("vendor/", "vendored"), ("docs/", "documentation"), ("README.md", "documentation"), ("gen/", "generated")}
    languages = {item["language"]: item["files"] for item in record["languages"]}
    assert languages["TypeScript"] == 1 and languages["JavaScript"] == 1 and "Go" not in languages
    assert not any(e["path"].startswith(".github") for e in record["excluded"])


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
            for source in (go, cargo, uv, tsc, npm, renovate, enry):
                commands = source.commands(context)
                if not commands:
                    continue
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


def test_renovate_reader_gives_declared_toolchains_and_ranges_on_their_unit(tmp_path):
    _, _, record = build(tmp_path, "versions", runner=replay("versions"))
    label = premap.label(renovate)
    node = {(t["declared_in"], t["version"]) for t in record["toolchains"] if t["tool"] == "node" and label in t["sources"]}
    assert node >= {(".nvmrc", "20.11.0"), ("package.json", ">=20")}
    [ms] = [d for d in record["dependencies"] if d["name"] == "ms"]
    assert (ms["unit"], ms["declared"], ms["resolved"], ms["scope"]) == ("site", "^2.1.0", "2.1.3", "runtime")
    assert label in ms["sources"] and any(s.startswith("modules.py@") for s in ms["sources"])


# -------------------------------------------------------- requirements files

def requirement_deps(record):
    return {(d["name"], d.get("declared"), d["declared_in"], d.get("unit"), d.get("resolved"))
            for d in record["dependencies"] if any(s.startswith("requirements@") for s in d["sources"])}


def test_a_requirements_file_alone_makes_a_unit_and_its_includes_belong_to_it(tmp_path):
    _, _, record = build(tmp_path, "req_includes")
    units = by_root(record, "python-project")
    assert set(units) == {".", "libs/localpkg"}
    root = units["."]
    assert (root["name"], root["manifest"], root["depends_on"]) == (None, "requirements.txt", ["localpkg"])
    assert root["config"]["requirements"] == ["requirements-dev.txt", "requirements.txt", "requirements/base.txt"]
    assert root["registries"] == ["https://pypi.example.org"]
    assert requirement_deps(record) == {
        ("requests", ">=2.31,<3", "requirements/base.txt", None, None),
        ("click", "==8.1.7", "requirements/base.txt", None, None),
        ("numpy", ">=1.26", "requirements/base.txt", None, None),
        ("mylib", "git+https://github.com/example/mylib.git@v1.4.0", "requirements/base.txt", None, None),
        ("gunicorn", "==22.0.0", "requirements.txt", None, None),
        ("pytest", "==8.3.3", "requirements-dev.txt", None, None)}  # a constraint is no dependency


def test_a_pip_compile_output_is_the_lock_of_its_in_file(tmp_path):
    _, _, record = build(tmp_path, "req_pip_tools")
    [unit] = by_root(record, "python-project").values()
    assert unit["manifest"] == "requirements.in"
    assert requirement_deps(record) == {("django", ">=4.2,<5.1", "requirements.in", None, "4.2.16"),
                                        ("ruff", None, "dev-requirements.in", None, "0.6.9")}


def test_service_folders_with_requirements_are_units_and_one_beside_a_pyproject_joins_it(tmp_path):
    _, _, record = build(tmp_path, "req_services")
    units = by_root(record, "python-project")
    assert set(units) == {"vote", "load-gen", "functions-python"}
    assert units["vote"]["manifest"] == "vote/requirements.txt" and units["vote"]["name"] is None
    assert units["functions-python"]["manifest"] == "functions-python/pyproject.toml"
    assert units["functions-python"]["config"]["requirements"] == ["functions-python/requirements-test.txt"]
    assert ("pytest", ">=8", "functions-python/requirements-test.txt", "shop-functions", None) in requirement_deps(record)
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

def test_an_absent_submodule_is_excluded_declared_and_a_gap(tmp_path):
    _, _, record = build(tmp_path, "submodule_absent")
    [excluded] = record["excluded"]
    assert excluded["path"] == "vendor/logfmt/" and excluded["why"] == "submodule"
    [dependency] = [d for d in record["dependencies"] if d["declared_in"].startswith(".gitmodules")]
    assert dependency["name"] == "https://github.com/example/logfmt.git" and dependency["declared"] == "main"
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
