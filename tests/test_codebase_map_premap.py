"""The pre-map: its record, the join of sources, model commands read from stored outputs, the declared gaps."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))

import premap  # noqa: E402
from premap import cargo, enry, go, module_graph, npm, renovate, tsc, uv  # noqa: E402
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
    assert all(item["sources"] and all("@" in s for s in item["sources"]) for item in record["units"])
    assert "languages" not in record  # go-enry runs in the container only
    assert {s["source"].split("@")[0]: s["state"] for s in record["sources"]} == {
        "modules.py": "ran", "python-build": "not_needed", "requirements": "not_needed", "npm-files": "ran", "jvm-files": "not_needed",
        "gitmodules": "not_needed",
        "go-enry": "not_run", "renovate": "not_run", "go": "not_needed", "cargo": "not_needed", "uv": "not_needed",
        "tsc": "not_needed", "npm": "not_run", "cmake": "not_needed", "meson": "not_needed", "bazel": "not_needed",
        "make": "not_needed", "project-files": "not_needed", "gradle": "not_needed", "maven": "not_needed",
        "sbt": "not_needed", "dotnet": "not_needed"}
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
    snapshot.write_snapshot(project, manifest)
    report = {"repositories": {"local": {"packageFiles": package_files}}}
    with open_snapshot(manifest) as store:
        context = premap.Context(manifest, store)
        return renovate.read(context, [], [{"returncode": 0, "stdout": json.dumps(report), "stderr": ""}])["facts"]


def test_a_constraint_renovate_extracts_from_the_file_is_a_toolchain_not_a_package(tmp_path):
    """Poetry's `python`, Composer's `php`, pub's `dart` and `flutter`, global.json's SDK: the same file states
    them as constraints. Not packages a unit uses."""
    files = {"pyproject.toml": '[tool.poetry]\nname = "app"\n[tool.poetry.dependencies]\npython = "^3.10"\nrich = "^13"\n'}
    facts = _renovate(tmp_path, files, {"poetry": [{"packageFile": "pyproject.toml", "extractedConstraints": {"python": "^3.10"},
                                                    "deps": [{"depName": "python", "currentValue": "^3.10", "depType": "dependencies"},
                                                             {"depName": "rich", "currentValue": "^13", "depType": "dependencies"}]}]})
    assert facts == {"toolchains": [{"tool": "python", "version": "^3.10", "declared_in": "pyproject.toml"}]}


def test_the_sdk_of_global_json_is_the_dotnet_toolchain(tmp_path):
    """Renovate names it `dotnet-sdk`: the tool the build runs on is `dotnet`, the name the preparation installs."""
    files = {"global.json": '{"sdk": {"version": "8.0.404", "rollForward": "latestFeature"}}\n'}
    facts = _renovate(tmp_path, files, {"nuget": [{"packageFile": "global.json", "deps": [
        {"depName": "dotnet-sdk", "depType": "dotnet-sdk", "currentValue": "8.0.404"}],
        "extractedConstraints": {"dotnet-sdk": "8.0.404"}}]})
    assert facts == {"toolchains": [{"tool": "dotnet", "version": "8.0.404", "declared_in": "global.json"}]}


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


# -------------------------------------------------------- requirements files

def test_a_requirements_file_alone_makes_a_unit_and_its_includes_belong_to_it(tmp_path):
    _, _, record = build(tmp_path, "req_includes")
    units = by_root(record, "python-project")
    assert set(units) == {".", "libs/localpkg"}
    root = units["."]
    assert (root["name"], root["manifest"], root["depends_on"]) == (None, "requirements.txt", ["localpkg"])
    assert root["config"]["requirements"] == ["requirements-dev.txt", "requirements.txt", "requirements/base.txt"]
    assert root["registries"] == ["https://pypi.example.org"]


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
    [excluded] = record["excluded"]
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
