"""Vue and Svelte components for scip-typescript: the index of the TypeScript their framework's tool generates,
given back to each component through the tool's map, on the tools' real output.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_components.py

`fixtures/components` holds two components and a module importing them, the report `components.cjs` wrote for them
(@vue/language-core 3.3.14, the project's own there; the svelte2tsx 0.7.63 scip-typescript depends on), and the
index scip-typescript 0.6.2 wrote of the program (Vue's generated file, the Svelte component itself), all recorded
once in a Linux container with Node 24.22.3 (the bundler resolution). Where the runner's image holds Node and those
packages (`tests/modal_pytest.py`), the script runs again and must write what was recorded.

`fixtures/components-vue2` holds js-vue-pnpm's Counter.vue as @vue/language-core 2.2.12, the project's there, turns
it, and scip-typescript 0.6.2's index of it, made with vue 3.5.22's types; the runner's image holds those packages
too (`/opt/components-vue2`), where both are made again and must be what was recorded.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import code_graph  # noqa: E402
import container  # noqa: E402
import preparation  # noqa: E402
from indexers import components, typescript  # noqa: E402

FIXTURE = HERE / "fixtures/components"
SVELTEKIT = HERE.parent / "benchmarks/project-model/fixtures/js-sveltekit"
INDEXER = f"{preparation.T}/npm/lib/node_modules/@sourcegraph/scip-typescript"
PACKAGES = Path("/opt/components")  # the runner image's: the packages the recording was made with
LISTED = [{"rel": "src/App.vue", "kind": "vue", "ts": True}, {"rel": "src/Panel.svelte", "kind": "svelte", "ts": True}]
# The program of the recording: the bundler resolution, the module and the components' entries.
CONFIG = {"compilerOptions": {"allowJs": True, "noEmit": True, "skipLibCheck": True, "target": "es2022",
                              "module": "esnext", "moduleResolution": "bundler"},
          "include": ["src/main.ts", "src/App.vue.ts", "src/App.vue.tsx", "src/Panel.svelte"]}
VUE2, VUE2_PACKAGES = HERE / "fixtures/components-vue2", Path("/opt/components-vue2")
COUNTER = "src/components/Counter.vue"


def _vue2_made(tmp_path: Path) -> Path:
    """The Vue 2 recording made again: `components.cjs` with the project's 2.2.12, then scip-typescript over the
    program of the generated file; its report and index in `tmp_path`, the project returned."""
    project = tmp_path / "project"
    shutil.copytree(VUE2 / "src", project / "src")
    os.symlink(VUE2_PACKAGES / "node_modules", project / "node_modules")
    (project / "package.json").write_text('{"name": "probe", "version": "1.0.0", "private": true}', encoding="utf-8")
    config = {**CONFIG, "include": [COUNTER + ".ts", COUNTER + ".tsx"]}
    (project / "tsconfig.json").write_text(json.dumps(config), encoding="utf-8")
    (tmp_path / "list.json").write_text(json.dumps([{"rel": COUNTER, "kind": "vue", "ts": True}]), encoding="utf-8")
    modules = VUE2_PACKAGES / "node_modules"
    for command in (["node", str(SCRIPTS / "indexers/components.cjs"), str(tmp_path / "list.json"), str(project),
                     str(tmp_path / "ours"), str(tmp_path / "components.json"),
                     str(modules / "@sourcegraph/scip-typescript")],
                    ["node", os.path.realpath(modules / ".bin/scip-typescript"), "index", "--cwd", str(project),
                     "--output", str(tmp_path / "index.scip"), "--no-progress-bar"]):
        done = subprocess.run(command, capture_output=True, text=True, env={**os.environ, "NODE_OPTIONS": ""})
        assert done.returncode == 0, done.stderr
    return project


def _vue2_rewritten(tmp_path: Path) -> code_graph.Index:
    """The Vue 2 recording's index given back to its component."""
    project = tmp_path / "project"
    shutil.copytree(VUE2 / "src", project / "src")
    shutil.copyfile(VUE2 / "index.scip", tmp_path / "index.scip")
    components.rewrite(tmp_path / "index.scip", VUE2 / "components.json", project)
    index = code_graph.Index(project)
    index.load(tmp_path / "index.scip")
    return index


def _rewritten(tmp_path: Path) -> code_graph.Index:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE / "src", project / "src")
    index = tmp_path / "index.scip"
    shutil.copyfile(FIXTURE / "index.scip", index)
    report = components.rewrite(index, FIXTURE / "components.json", project)
    assert set(report["tools"]) == {"svelte2tsx@0.7.63", "@vue/language-core@3.3.14"}
    loaded = code_graph.Index(project)
    loaded.load(index)
    return loaded


def _at(rel: str, line: int, text: str) -> tuple[int, int]:
    row = (FIXTURE / rel).read_text(encoding="utf-8").split("\n")[line - 1]
    return line, row.index(text)


def _defined(index, rel: str, line: int, column: int) -> set:
    """Where the symbols referenced at a position are defined: `(document, line, column)`."""
    keys = {item.key for item in index.at.get((rel, line, column), ()) if not item.definition}
    return {(place, item.line, item.start) for key in keys for place, item in index.defs.get(key, ())}


@pytest.mark.skipif(not (shutil.which("node") and (PACKAGES / "node_modules").is_dir()),
                    reason="the runner's image holds Node and the recording's packages")
def test_the_script_writes_what_was_recorded(tmp_path):
    """`components.cjs` on the fixture, with the recording's packages as the project's: the same generated code's
    map, tools and whose, and no import left unresolved by the bundler resolution."""
    project = tmp_path / "project"
    shutil.copytree(FIXTURE / "src", project / "src")
    shutil.copytree(PACKAGES / "node_modules", project / "node_modules", symlinks=True)
    (project / "package.json").write_text('{"name": "probe", "version": "1.0.0", "private": true}', encoding="utf-8")
    (project / "tsconfig.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    (tmp_path / "list.json").write_text(json.dumps(LISTED), encoding="utf-8")
    done = subprocess.run(["node", str(SCRIPTS / "indexers/components.cjs"), str(tmp_path / "list.json"),
                           str(project), str(tmp_path / "ours"), str(tmp_path / "out.json"), str(project)],
                          capture_output=True, text=True, env={**os.environ, "NODE_OPTIONS": ""})
    assert done.returncode == 0, done.stderr
    written = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    recorded = json.loads((FIXTURE / "components.json").read_text(encoding="utf-8"))
    # Here svelte2tsx is the image's: in the run it is the one of scip-typescript's package.
    assert written == recorded
    assert (project / "src/App.vue.ts").is_file() and not (project / "src/Panel.svelte.ts").exists()


@pytest.mark.skipif(not (shutil.which("node") and (PACKAGES / "node_modules").is_dir()),
                    reason="the runner's image holds Node and the recording's packages")
def test_a_projects_vue_tool_older_than_its_language_plugin_gives_way_to_daodans_and_is_said(tmp_path):
    """hoppscotch holds @vue/language-core 1.8.8 too (round 2026-11-17-vue-svelte), which exports createVueLanguage
    and no createVueLanguagePlugin: Daodan's pin turns its components, and the record says which it stands for."""
    project = tmp_path / "project"
    shutil.copytree(FIXTURE / "src", project / "src")
    old = project / "node_modules/@vue/language-core"
    old.mkdir(parents=True)
    (old / "package.json").write_text('{"name": "@vue/language-core", "version": "1.8.8", "main": "index.js"}',
                                      encoding="utf-8")
    (old / "index.js").write_text("exports.createVueLanguage = () => null;\n", encoding="utf-8")
    (project / "package.json").write_text('{"name": "probe", "version": "1.0.0", "private": true}', encoding="utf-8")
    (project / "tsconfig.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    (tmp_path / "list.json").write_text(json.dumps(LISTED[:1]), encoding="utf-8")
    done = subprocess.run(["node", str(SCRIPTS / "indexers/components.cjs"), str(tmp_path / "list.json"),
                           str(project), str(PACKAGES), str(tmp_path / "out.json"), str(PACKAGES)],
                          capture_output=True, text=True, env={**os.environ, "NODE_OPTIONS": ""})
    assert done.returncode == 0, done.stderr
    written = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert written["tools"] == {"@vue/language-core@3.3.14": {"tool": "@vue/language-core", "version": "3.3.14",
                                                              "from": "daodan", "instead": ["1.8.8"]}}
    assert written["components"]["src/App.vue"]["generated"] == "src/App.vue.ts"


def test_a_default_import_of_a_vue_component_reaches_it_as_one_of_a_svelte_component_does(tmp_path):
    """js-vue-pnpm `src/main.ts:4 App` (round 2026-11-17-vue-svelte, D-290). The recording holds the same: the
    importer names `App` with a local it defines nowhere (Vue's default export is an expression), and the import's
    module is the generated file's, which the indexer defines at its start, where the map holds nothing. Given back
    at the component's start, the module is what the name reaches; `Panel` reaches its Svelte component's."""
    import test_codebase_map_code_graph as graphs
    index = _rewritten(tmp_path)
    _hops, traversal, _prepared = code_graph.adapter_traversal(typescript, index, graphs.Snapshot({}))

    def reached(line: int, column: int) -> list:
        return sorted({(end.cls, end.key) for item in index.at[("src/main.ts", line, column)]
                       for end in traversal.ends(item.key)})

    [module] = {item.key for item in index.at[("src/main.ts", 1, 16)]}
    [panel] = {item.key for item in index.at[("src/main.ts", 2, 18)]}
    assert [(rel, item.line, item.start) for rel, item in index.defs[module]] == [("src/App.vue", 1, 0)]
    assert reached(1, 7) == reached(3, 22) == [("project-value", module)]
    assert reached(2, 7) == [("project-value", panel)]


@pytest.mark.skipif(not (shutil.which("node") and (VUE2_PACKAGES / "node_modules").is_dir()),
                    reason="the runner's image holds Node, Vue's tool 2.2.12 and scip-typescript 0.6.2")
def test_the_vue2_recording_is_what_its_tools_write_again(tmp_path):
    project = _vue2_made(tmp_path)
    assert json.loads((tmp_path / "components.json").read_text(encoding="utf-8")) == json.loads(
        (VUE2 / "components.json").read_text(encoding="utf-8"))

    def occurrences(path: Path) -> dict:
        index = code_graph.Index(project)
        index.load(path)
        return {rel: sorted(item[:6] for item in items) for rel, items in index.documents.items()}

    assert occurrences(tmp_path / "index.scip") == occurrences(VUE2 / "index.scip")


def test_a_template_read_vue2_writes_through_its_setups_property_reaches_the_binding(tmp_path):
    """js-vue-pnpm `src/components/Counter.vue:9 n` (round 2026-11-17-vue-svelte, D-290): Vue's tool 2.x reads a
    binding in the template as a property of the generated `setup`'s return (`__VLS_ctx.n`), which it writes as
    `n: n as typeof n`, outside the map. Given back, the template reads the binding the property holds, as 3.x
    reads it itself (`src/App.vue:10 n` of the other recording)."""
    index = _vue2_rewritten(tmp_path)
    rows = (VUE2 / COUNTER).read_text(encoding="utf-8").split("\n")
    binding = (COUNTER, 5, rows[4].index("n ="))
    assert _defined(index, COUNTER, 9, rows[8].index("n++")) == {binding}
    assert _defined(index, COUNTER, 9, rows[8].index("{{ n }}") + 3) == {binding}


def test_a_macro_vues_tool_declares_in_generated_code_is_vues_own(tmp_path):
    """js-vue-pnpm `src/components/Counter.vue:4 defineProps` (`dangling-local`, D-290): Vue's tool declares the
    compiler's macros in generated code (2.2.12 `declare const { defineProps, … }: typeof import('vue');`), outside
    the map, where the index defines each name with a local and, at the same range, references Vue's own function.
    Given back, the component's call is of Vue's `defineProps`: an external, not a local defined nowhere."""
    import test_codebase_map_code_graph as graphs
    index = _vue2_rewritten(tmp_path)
    _hops, traversal, _prepared = code_graph.adapter_traversal(typescript, index, graphs.Snapshot({}))
    row = (VUE2 / COUNTER).read_text(encoding="utf-8").split("\n")[3]
    assert {(end.cls, end.key) for item in index.at[(COUNTER, 4, row.index("defineProps"))]
            for end in traversal.ends(item.key)} == {
        ("external", "scip-typescript npm @vue/runtime-core 3.5.22 dist/`runtime-core.d.ts`/defineProps().")}


def test_the_index_of_the_generated_typescript_is_the_components(tmp_path):
    index = _rewritten(tmp_path)
    assert {"src/App.vue", "src/Panel.svelte", "src/main.ts"} <= set(index.documents)
    assert not {rel for rel in index.documents if rel.endswith((".vue.ts", ".svelte.ts"))}
    vue, svelte = "src/App.vue", "src/Panel.svelte"
    # The template's calls and reads reach the script's definitions, the v-for alias its own.
    assert _defined(index, vue, *_at(vue, 10, "inc(1)")) == {(vue, *_at(vue, 4, "inc"))}
    assert _defined(index, vue, *_at(vue, 10, "label(n)")) == {(vue, *_at(vue, 5, "label"))}
    assert _defined(index, vue, *_at(vue, 11, "label(item")) == {(vue, *_at(vue, 5, "label"))}
    assert _defined(index, vue, *_at(vue, 11, "items")) == {(vue, *_at(vue, 6, "items"))}
    assert _defined(index, vue, *_at(vue, 11, "item.id")) == {(vue, *_at(vue, 11, "item in"))}
    assert _defined(index, svelte, *_at(svelte, 8, "select(2)")) == {(svelte, *_at(svelte, 3, "select"))}
    assert _defined(index, svelte, *_at(svelte, 8, "title")) == {(svelte, *_at(svelte, 4, "title"))}
    assert _defined(index, svelte, *_at(svelte, 8, "count}")) == {(svelte, *_at(svelte, 2, "count"))}
    assert _defined(index, svelte, *_at(svelte, 10, "title")) == {(svelte, *_at(svelte, 4, "title"))}
    assert _defined(index, svelte, *_at(svelte, 9, "item.id")) == {(svelte, *_at(svelte, 9, "item ("))}
    # Nothing of the generated code is left: every occurrence lies in its component's text.
    for rel in (vue, svelte):
        rows = (FIXTURE / rel).read_text(encoding="utf-8").split("\n")
        assert all(item.end <= len(rows[item.end_line - 1]) for item in index.documents[rel])


def test_a_component_the_tool_could_not_turn_has_no_document_and_the_checkers_pass_follows_the_map(tmp_path):
    project = tmp_path / "project"
    shutil.copytree(FIXTURE / "src", project / "src")
    shutil.copyfile(FIXTURE / "index.scip", tmp_path / "index.scip")
    # The checker's pass names a member at a generated position, which is the template's `item.name`.
    generated = json.loads((FIXTURE / "components.json").read_text(encoding="utf-8"))["components"]["src/App.vue"]
    line, column = _at("src/App.vue", 11, "name }}")
    row, start = next((row, start + column - source_column) for row, items in components.segments(
        generated["map"], (FIXTURE / "src/App.vue").read_text(encoding="utf-8")).items()
        for start, source_row, source_column, run in items
        if source_row + 1 == line and source_column <= column < source_column + run)
    (tmp_path / "index.unbound.jsonl").write_text(
        json.dumps(["src/App.vue.ts", row + 1, start, "any", ""]) + "\n" + json.dumps(["src/main.ts", 3, 0, "any", ""])
        + "\n" + json.dumps(["src/App.vue.ts", 1, 0, "any", ""]) + "\n", encoding="utf-8")
    components.rewrite(tmp_path / "index.scip", FIXTURE / "components.json", project)
    assert [json.loads(text)[:3] for text in (tmp_path / "index.unbound.jsonl").read_text().splitlines()] == [
        ["src/App.vue", line, column], ["src/main.ts", 3, 0]]  # the generated header's line maps nowhere
    report = json.loads((FIXTURE / "components.json").read_text(encoding="utf-8"))
    report["components"]["src/App.vue"] = {"tool": "@vue/language-core@3.3.14", "error": "Unexpected token"}
    (tmp_path / "report.json").write_text(json.dumps(report), encoding="utf-8")
    shutil.copyfile(FIXTURE / "index.scip", tmp_path / "again.scip")
    components.rewrite(tmp_path / "again.scip", tmp_path / "report.json", project)
    index = code_graph.Index(project)
    index.load(tmp_path / "again.scip")
    assert "src/Panel.svelte" in index.documents and "src/App.vue" not in index.documents


def test_an_import_of_a_component_typescript_resolves_to_nothing_is_a_counted_gap():
    report = {"unresolved": {"src/main.ts": ["./App.vue"], "src/b.ts": ["./A.vue", "./B.vue"]},
              "resolution": "NodeNext"}
    assert components.gaps(report) == [{
        "kind": "component_import_unresolved", "count": 3, "files": ["src/b.ts", "src/main.ts"],
        "detail": "3 imports of a .vue component TypeScript resolves to nothing (module resolution NodeNext: an "
                  "ECMAScript module's import adds no .ts to the name), in src/b.ts, src/main.ts"}]
    assert components.gaps({"unresolved": {}, "resolution": "Bundler"}) == []


def _indexed(tmp_path: Path, monkeypatch, project: Path, prepared: str = "", executed: str = "",
             brought: bool = True) -> tuple[dict, dict]:
    """`typescript.index` over `project` with a container run that plays the two logs and brings back the
    recorded index and report."""
    seen: dict = {}

    def run(_project, command, **options):
        seen.update(options, command=command, inputs=options["inputs"]())
        out = Path(options["out_dir"])
        out.mkdir(parents=True, exist_ok=True)
        (out / "prepare.log").write_text(prepared, encoding="utf-8")
        (out / "execute.log").write_text(executed, encoding="utf-8")
        (out / container.RECORD_NAME).write_text("".join(json.dumps(
            {"phase": phase, "exit_code": 0, "duration_seconds": 1.0, "outcome": "exited"}) + "\n"
            for phase in ("prepare", "execute")), encoding="utf-8")
        if brought:
            (out / "out").mkdir()
            shutil.copyfile(FIXTURE / "index.scip", out / "out/index.scip")
            shutil.copyfile(FIXTURE / "components.json", out / "out/components.json")
        return {"state": "done", "exit_code": 0, "outputs": [], "engine": "test"}

    monkeypatch.setattr(container, "run_in_container", run)
    monkeypatch.setattr(preparation, "fetched", lambda url, digest, name: tmp_path / name)
    return typescript.index(project, tmp_path / "work", roots={""}), seen


def test_the_components_are_turned_into_typescript_in_the_run_and_their_index_given_back(tmp_path, monkeypatch):
    project = tmp_path / "project"
    shutil.copytree(FIXTURE / "src", project / "src")
    (project / "package.json").write_text('{"name": "probe", "private": true}', encoding="utf-8")
    result, seen = _indexed(tmp_path, monkeypatch, project)
    assert {"vue", "svelte"} <= set(typescript.LANGUAGES)
    prepare, execute = seen["prepare"][2], seen["command"][2]
    # Daodan's Vue tool, installed after the restore: the execution takes the project's where it has one.
    [install] = components.install(LISTED)
    assert prepare.index(install) > prepare.index(preparation.restore("npm", ["."], scripts=True))
    # The generated files come before the indexer, in the copy, with no network, once the tsconfig is in place.
    generate = execute.index(components.generate(typescript.WORK, INDEXER))
    assert execute.index(f"cp {typescript.CONFIG} tsconfig.json") < generate < execute.index('scip-typescript)" index')
    assert json.loads(Path(seen["inputs"][components.LIST]).read_text(encoding="utf-8")) == LISTED
    assert seen["inputs"][components.SCRIPT].name == "components.cjs"
    config = json.loads(Path(seen["inputs"][typescript.CONFIG]).read_text(encoding="utf-8"))
    assert set(CONFIG["include"]) <= set(config["include"])
    # The index the graph reads holds the components, and the record names whose tools turned them.
    index = code_graph.Index(project)
    index.load(Path(result["indexes"][0][0]))
    assert {"src/App.vue", "src/Panel.svelte"} <= set(index.documents)
    assert result["indexer"]["frameworks"] == [
        {"tool": "@vue/language-core", "version": "3.3.14", "from": "project"},
        {"tool": "svelte2tsx", "version": "0.7.63", "from": "scip-typescript"}]
    # A component the tool could not turn says so where it has no document.
    configs = typescript.tasks({"components": {
        **result["configs"]["components"], "src/Broken.vue": {"tool": "@vue/language-core@3.3.14",
                                                              "error": "Unexpected token"},
        "src/Alone.vue": {"error": "@vue/language-core is installed neither by the project nor by Daodan"}}})
    assert typescript.missing(index, ["src/Broken.vue", "src/Alone.vue", "src/x.ts"], configs) == {
        "src/Broken.vue": "@vue/language-core@3.3.14 could not turn it into TypeScript: Unexpected token",
        "src/Alone.vue": "@vue/language-core is installed neither by the project nor by Daodan"}


def test_without_components_the_run_is_the_same(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src/main.ts").write_text("export const x = 1;\n", encoding="utf-8")
    (project / "package.json").write_text('{"name": "probe", "private": true}', encoding="utf-8")
    result, seen = _indexed(tmp_path, monkeypatch, project, brought=False)
    assert "components.cjs" not in seen["command"][2] and components.OURS not in seen["prepare"][2]
    assert not {components.LIST, components.SCRIPT} & set(seen["inputs"])
    assert "frameworks" not in result["indexer"]


def test_sveltekit_writes_its_tsconfig_in_the_preparation_with_the_projects_kit(tmp_path, monkeypatch):
    """svelte.dev/docs/kit/cli: `svelte-kit sync` creates the tsconfig.json and the generated types; a project
    runs it as its `prepare` script, js-sveltekit only in `check`, so the preparation runs it after the restore."""
    project = tmp_path / "project"
    shutil.copytree(SVELTEKIT, project, ignore=shutil.ignore_patterns("expected.json"))
    result, seen = _indexed(tmp_path, monkeypatch, project, prepared="DAODAN-GENERATED . 2.8.0 svelte-kit sync\n",
                            brought=False)
    prepare = seen["prepare"][2]
    sync = typescript.generator(".", typescript.GENERATORS[".svelte-kit"])
    assert prepare.index(sync) > prepare.index(preparation.restore("npm", ["."], scripts=True))
    assert "npx --no -- svelte-kit sync" in sync and "npx --no -- svelte-kit --version" in sync  # the project's kit
    assert result["indexer"]["generated"] == [{"command": "svelte-kit sync", "path": ".", "version": "2.8.0"}]
    assert not [gap for gap in result.get("gaps", ()) if gap["kind"] == "config_not_generated"]
    # One that fails is the generation's gap, and the configuration it did not write is said with it.
    failed = ("DAODAN-GENERATE-FAILED svelte-kit .\nError: Cannot find package '@sveltejs/adapter-auto'\n"
              "DAODAN-GENERATE-END\n")
    result, _seen = _indexed(tmp_path / "again", monkeypatch, project, prepared=failed, brought=False,
                             executed="error TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'.\n")
    gaps = {gap["kind"]: gap for gap in result["gaps"]}
    assert gaps["generation_failed"]["manager"] == "svelte-kit" and "adapter-auto" in gaps["generation_failed"]["detail"]
    assert gaps["config_not_generated"]["detail"] == (
        "tsconfig.json extends .svelte-kit/tsconfig.json, which `svelte-kit sync` did not write in the preparation")


@pytest.mark.skipif(not shutil.which("bash"), reason="the preparation's lines are bash")
def test_the_generators_line_says_what_the_projects_command_wrote_or_why_not(tmp_path, monkeypatch):
    """The line as the preparation runs it, with an `npx` that stands for the project's installed kit."""
    bin_dir, work = tmp_path / "bin", tmp_path / "work"
    bin_dir.mkdir()
    (work / "app").mkdir(parents=True)
    monkeypatch.setattr(typescript, "WORK", str(work))
    line = typescript.generator("app", "svelte-kit sync")

    def played(npx: str) -> str:
        (bin_dir / "npx").write_text(f"#!/bin/sh\n{npx}\n", encoding="utf-8")
        (bin_dir / "npx").chmod(0o755)
        done = subprocess.run(["bash", "-c", line], capture_output=True, text=True,
                              env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"})
        assert done.returncode == 0
        return done.stderr

    said = played('if [ "$4" = --version ]; then echo "svelte-kit, 2.8.0"; else touch .svelte-kit-synced; fi')
    assert said == "DAODAN-GENERATED app 2.8.0 svelte-kit sync\n" and (work / "app/.svelte-kit-synced").is_file()
    said = played("exit 1")
    assert preparation.generation_gaps(said) == [{"kind": "generation_failed", "manager": "svelte-kit", "path": "app",
                                                  "detail": "the project installs no svelte-kit here"}]


NODE_BIN = Path(os.path.realpath(shutil.which("node"))).parent if shutil.which("node") else Path("/nowhere")


@pytest.mark.skipif(not (NODE_BIN / "npx").is_file(), reason="npm's npx, beside Node, runs the line")
def test_the_generators_line_reads_the_kits_version_not_npms(tmp_path, monkeypatch):
    """npm reads `--version` wherever it stands, so `npx svelte-kit --version` printed npm's 11.19.1 on js-sveltekit
    (round 2026-11-17-vue-svelte): after `--` the flag is the kit's. The kit here is the project's installed bin."""
    work = tmp_path / "work"
    kit = work / "app/node_modules/.bin/svelte-kit"
    kit.parent.mkdir(parents=True)
    kit.write_text('#!/bin/sh\nif [ "$1" = --version ]; then echo "svelte-kit, 2.8.0"; else touch synced; fi\n',
                   encoding="utf-8")
    kit.chmod(0o755)
    monkeypatch.setattr(typescript, "WORK", str(work))
    done = subprocess.run(["bash", "-c", typescript.generator("app", "svelte-kit sync")], capture_output=True,
                          text=True, env={**os.environ, "npm_config_cache": str(tmp_path / "npm-cache"),
                                          "PATH": f"{NODE_BIN}{os.pathsep}{os.environ['PATH']}"})
    assert done.stderr == "DAODAN-GENERATED app 2.8.0 svelte-kit sync\n" and (work / "app/synced").is_file()


MARKED = {  # the project's code a component or SvelteKit brings, each leaving a mark beside it when executed
    "svelte.config.js": "require('fs').writeFileSync(__dirname + '/MARK-svelte-config', '1');\nmodule.exports = {};\n",
    "node_modules/@vue/language-core/package.json": '{"name": "@vue/language-core", "version": "9.9.9"}',
    "node_modules/@vue/language-core/index.js": "require('fs').writeFileSync(__dirname + '/MARK-language-core', '1');\n",
    "node_modules/.bin/svelte-kit": "#!/usr/bin/env node\nrequire('fs').writeFileSync(__dirname + '/MARK-svelte-kit', '1');\n",
}


def test_no_code_of_the_project_runs_on_the_host(tmp_path, monkeypatch):
    """Vue's tool and SvelteKit's sync are the project's code: the snapshot, the plan and the map back read their
    files as text, and only the container's two scripts name them (AGENTS.md, the inviolable rule)."""
    project = tmp_path / "project"
    shutil.copytree(FIXTURE / "src", project / "src")
    for rel, text in {**MARKED, "package.json": '{"name": "probe", "private": true}',
                      "tsconfig.json": '{"extends": "./.svelte-kit/tsconfig.json"}'}.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    if shutil.which("node"):  # each file leaves its mark when executed: in a copy, so the project keeps none
        probe = tmp_path / "probe"
        shutil.copytree(project, probe)
        for rel in MARKED:
            if rel.endswith((".js", "svelte-kit")):
                subprocess.run(["node", str(probe / rel)], check=True, capture_output=True)
        assert len(list(probe.rglob("MARK-*"))) == 3
    import snapshot
    snapshot.build_manifest(project)
    result, seen = _indexed(tmp_path / "run", monkeypatch, project)
    components.rewrite(Path(result["indexes"][0][0]), FIXTURE / "components.json", project)
    assert not list(project.rglob("MARK-*")) and not list((tmp_path / "run").rglob("MARK-*"))
    prepare, execute = seen["prepare"][2], seen["command"][2]
    assert "npx --no -- svelte-kit sync" in prepare and components.SCRIPT in execute


def test_vue_and_svelte_have_no_engine_on_the_host():
    """The position engine Vue and Svelte had ran the project's `npm ci` and its own TypeScript's tsserver on the
    host (D-258): scip-typescript serves them in the container alone, no entry of the pass asks an engine on the
    host, and a store entry that engine left is not fresh."""
    import importlib
    import importlib.util
    import engine_pass
    import engine_tools
    for language in ("vue", "svelte"):
        spec = engine_pass.ENGINE_LANGUAGES[language]
        assert (spec.name, spec.needs_container) == ("scip-typescript", True)
    assert not [spec.name for spec in engine_pass.ENGINES
                if hasattr(importlib.import_module(f"indexers.{spec.indexer}"), "engine")]
    assert importlib.util.find_spec("language_servers") is None and not hasattr(engine_tools, "npm_modules")
    assert not engine_pass.from_source("vue", {"engine": "typescript@typescript-language-server@4.3.3"})


def test_the_components_and_the_lines_that_turn_them_into_typescript(tmp_path):
    (tmp_path / "A.vue").write_text('<script lang="ts">\nexport default {}\n</script>\n', encoding="utf-8")
    (tmp_path / "B.svelte").write_text("<p>{x}</p>\n", encoding="utf-8")
    found = components.listed(tmp_path, ["A.vue", "B.svelte", "c.ts"])
    assert found == [{"rel": "A.vue", "kind": "vue", "ts": True}, {"rel": "B.svelte", "kind": "svelte", "ts": False}]
    assert components.include(found) == ["A.vue.ts", "A.vue.tsx", "B.svelte"]
    [line] = components.install(found)
    assert f"--ignore-scripts --no-audit --no-fund --loglevel=error {components.PIN}" in line
    assert f"DAODAN-MISSING {components.PIN}" in line
    assert components.install(found[1:]) == components.install([]) == [] and components.include([]) == []
