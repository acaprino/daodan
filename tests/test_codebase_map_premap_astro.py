"""The events an Astro project's own compiler reads in its templates, read from its output and given the snapshot's file, line and column.

`parse` of the compiler the project's `astro` depends on runs in Daodan's container (`premap/astro_templates.mjs`); the container is a
fake here: the answers are the ones the real script printed on Modal for `benchmarks/astro-compiler/fixture`, with Astro 5
(`@astrojs/compiler` 2.x), 6 (`@astrojs/compiler` 4.x) and 7 (`@astrojs/compiler-rs`), in a copy of the project, in a copy with Windows
line ends and in a copy without its packages (`tests/fixtures/premap/astro/`, recorded by `benchmarks/astro-compiler/modal_probe.py
--mode source`). What `parse` gives is the event and where it is; the function an attribute's string calls it does not give, so each
call is a gap with its cause: nothing is bound by name.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from test_codebase_map_container_runner import container, container_runner, manifest_of, premap, recorder

import preparation  # noqa: E402

BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks/astro-compiler"
FIXTURE = BENCHMARK / "fixture"
RECORDED = Path(__file__).parent / "fixtures/premap/astro"
SOURCE = f"astro@{premap.astro.VERSION}"
VERSIONS = ("astro5", "astro6", "astro7")
NODE20 = "astro5-node20"  # Astro 5 on Node 20: the oldest Node the script has to run on
INDEX, EDGE, BROKEN, UNICODE = "src/pages/index.astro", "src/pages/edge.astro", "src/pages/broken.astro", "src/pages/unicode.astro"
SVG, CALLS = "src/pages/svg.astro", "src/pages/calls.astro"


def project_files(version: str = "astro5", crlf: bool = False, **changes) -> dict[str, str | None]:
    """The fixture as the benchmark runs it: its files and the `package.json` of one Astro version (`crlf`: every `.astro` with
    Windows line ends: git keeps every text file with `\\n`)."""
    files = {path.relative_to(FIXTURE).as_posix(): path.read_text(encoding="utf-8") for path in FIXTURE.rglob("*") if path.is_file()}
    files["package.json"] = (BENCHMARK / "versions" / version / "package.json").read_text(encoding="utf-8")
    if crlf:
        files = {rel: text.replace("\n", "\r\n") if rel.endswith(".astro") else text for rel, text in files.items()}
    files.update(changes)
    return {rel: text for rel, text in files.items() if text is not None}


def commands_of(tmp_path, files):
    from snapshot_store import open_snapshot
    project, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        return project, manifest, premap.astro.commands(premap.Context(manifest, store))


def listed(command) -> dict:
    """The list a command is given as a file (`inputs`), which its argument names."""
    [(name, text)] = command["inputs"].items()
    assert command["argv"][-1] == f"{preparation.IN}/{name}"
    return json.loads(text)


def recorded(version: str, key: str = "installed") -> list[dict]:
    """The answers of the real script on Modal, as the container runner returns them for each command."""
    return [{"root": "/work", **answer} for answer in json.loads((RECORDED / f"{version}.json").read_text(encoding="utf-8"))[key]]


def read(tmp_path, answers, files=None):
    _, manifest = manifest_of(tmp_path, files or project_files())
    record = premap.write(manifest, sources=(premap.astro,), runner=lambda commands: answers)
    return record, [g for g in record["gaps"] if g.get("source") == SOURCE], manifest


def seen(record) -> dict:
    out = {}
    for row in record.get("framework_entries", ()):
        out.setdefault(row["site"], []).append(row)
    return out


def called(row) -> str:
    """The function a row says its attribute calls: the gap's third word."""
    return row["gap"].split(" calls ")[1].split(" ")[0]


# ---------------------------------------------------------------- what the source asks the container to run
def test_each_folder_that_declares_astro_is_one_command_given_its_astro_files_and_the_start_of_an_event_name_as_a_file(tmp_path):
    _, _, asked = commands_of(tmp_path, project_files())
    [command] = asked
    assert (command["tool"], command["cwd"], command["network"], command["env"]) == ("astro", ".", "none", {})
    assert command["argv"][:4] == ["timeout", "--kill-after=10", str(premap.astro.seconds(1)), "daodan-astro"] and len(command["argv"]) == 5
    expected = sorted(path.relative_to(FIXTURE).as_posix() for path in FIXTURE.rglob("*.astro"))
    assert listed(command) == {"prefix": "on", "jsx": "astro-jsx.d.ts", "files": expected} and len(expected) == 13
    assert not [f for f in listed(command)["files"] if not f.endswith(".astro")]  # the `.ts` endpoint is no template


def test_the_start_of_the_names_that_are_events_is_data_not_code(tmp_path, monkeypatch):
    import entries
    monkeypatch.setitem(entries.QUERIES, "astro", {**entries.QUERIES["astro"], "event_prefix": "x-on", "jsx": "other.d.ts"})
    _, _, asked = commands_of(tmp_path, project_files())
    assert (listed(asked[0])["prefix"], listed(asked[0])["jsx"]) == ("x-on", "other.d.ts")


def test_a_project_without_astro_runs_nothing_and_an_astro_file_no_folder_holds_is_a_gap(tmp_path):
    from snapshot_store import open_snapshot
    files = {"package.json": '{"dependencies": {"react": "19.3.1"}}\n', "web/package.json": "{", "tools/package.json": '["astro"]\n',
             "src/a.astro": "<p onclick=\"go()\">a</p>\n", "site/package.json": '{"dependencies": {"astro": "5.18.2"}}\n',
             "site/src/plain.ts": "export const x = 1;\n"}
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        assert premap.astro.commands(premap.Context(manifest, store)) is None  # `site` declares astro and holds no `.astro` file
    record = premap.write(manifest, sources=(premap.astro,), runner=lambda commands: 1 / 0)
    assert record["sources"][0]["state"] == "not_needed" and "framework_entries" not in record
    files["site/src/b.astro"] = "<p onclick=\"go()\">b</p>\n"
    _, manifest = manifest_of(tmp_path / "again", files)
    plan = None
    with open_snapshot(manifest) as store:
        plan = premap.astro._plan(premap.Context(manifest, store))
    assert plan["files"] == {"site": ["src/b.astro"]}
    assert [(g["path"], g["kind"]) for g in plan["gaps"]] == [("src/a.astro", "model_partial")]


def test_a_file_belongs_to_the_nearest_package_json_that_declares_astro(tmp_path):
    astro = '{"dependencies": {"astro": "5.18.2"}}\n'
    page = "<p onclick=\"go()\">a</p>\n"
    files = {"package.json": astro, "root.astro": page, "a/package.json": astro, "a/x.astro": page,
             "docs/package.json": '{"dependencies": {"react": "19"}}\n', "docs/y.astro": page}
    _, _, asked = commands_of(tmp_path, files)
    assert [(c["cwd"], listed(c)["files"]) for c in asked] == [(".", ["docs/y.astro", "root.astro"]), ("a", ["x.astro"])]


def test_the_commands_run_daodans_script_on_the_projects_own_packages_without_network_and_the_setup_installs_no_package(tmp_path):
    import preparation
    from snapshot_store import open_snapshot
    project, manifest = manifest_of(tmp_path, project_files())
    with open_snapshot(manifest) as store:
        asked = premap.astro.commands(premap.Context(manifest, store))
    spec = container_runner.TOOLS["astro"]
    assert (spec["restores"], spec["runs_on"]) == ("node", ("node",))  # the project's compiler is in its packages
    assert any(item[2] == "astro_templates.mjs" and item[0] is None for item in spec["files"])  # Daodan's own file, beside the source
    assert (container_runner.SCRIPTS / "astro_templates.mjs").is_file()
    calls, fake = recorder()
    carried = {}

    def spy(project, commands, **options):  # what the container is given, read while the run holds it (the files are temporary)
        carried.update({destination: (path.read_bytes() if path.is_file() else path) for destination, path in options["inputs"]().items()})
        return fake(project, commands, **options)
    with patch.object(container, "run_commands", spy), patch.object(container_runner, "fetched", lambda url, sha, name: Path("/host") / name
                                                                    if url or name != "astro_templates.mjs" else (container_runner.SCRIPTS / name)):
        container_runner.runner(manifest)(asked)
    first, *rest = calls[0]["commands"]
    plan = preparation.node_prepare(["package.json"], lambda rel: (project / rel).read_text(encoding="utf-8"))
    setup = first["argv"][-1]
    assert f"( {plan['lines'][0]} )" in setup and "install -g" not in setup  # the restore of the project's packages, nothing else
    assert f"{container_runner.T}/bin/daodan-astro" in setup and "astro_templates.mjs" in setup
    assert len(rest) == 1 and rest[0]["network"] == "none" and "inputs" not in rest[0]
    assert rest[0]["argv"][:4] == ["timeout", "--kill-after=10", str(premap.astro.seconds(1)), "daodan-astro"]  # a project's own code may not end
    assert premap.astro.MEMORY_GB == spec["memory"]  # what the gap of a killed run says the run has
    assert carried[f"{preparation.IN}/astro_templates.mjs"] == (container_runner.SCRIPTS / "astro_templates.mjs").read_bytes()
    assert carried[f"{preparation.IN}/astro-files-0.json"].decode("utf-8") == next(iter(asked[0]["inputs"].values()))


def test_the_recorded_answers_carry_the_print_of_the_script_that_made_them_and_the_version_of_the_source_they_were_made_for():
    """A pre-map is fresh while its source's `NAME@VERSION` is the one it was made by (`premap.state`): a script that changes with no
    new `VERSION` leaves stale rows in a project's pre-map. The recording holds both, so changing the script fails here until it is
    recorded again, and the record is made with the `VERSION` the source has then: raise it with the script."""
    script = container_runner.SCRIPTS / "astro_templates.mjs"
    printed = hashlib.sha256(script.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert json.loads((RECORDED / "script.json").read_text(encoding="utf-8")) == {"astro_templates.mjs": printed, "version": premap.astro.VERSION}, (
        "the script or the version changed: record the answers again (`benchmarks/astro-compiler/modal_probe.py --mode source`)")


# ---------------------------------------------------------------- what the recorded answers give
@pytest.mark.parametrize("version", VERSIONS)
def test_an_event_that_calls_a_named_function_is_a_row_at_its_file_line_and_column_with_a_gap_that_says_the_function_is_not_known(tmp_path, version):
    record, _, _ = read(tmp_path, recorded(version), project_files(version))
    rows = seen(record)
    owner = f"{INDEX}::<module>"
    [save] = rows[f"{INDEX}:14"]
    assert (save["reader"], save["shape"], save["event"], save["column"], save["owner"], save["symbol"]) == (
        "attributo", "onclick", "click", 20, owner, owner)
    assert called(save) == "save" and "handler_source" not in save and SOURCE in save["sources"]
    assert [(r["shape"], called(r)) for r in rows[f"{INDEX}:15"]] == [("onclick", "confirmOrder")]  # `this.disabled = true` calls nothing
    assert [(r["shape"], r["event"], called(r)) for r in sorted(rows[f"{INDEX}:22"], key=lambda r: r["column"])] == [
        ("onsubmit", "onsubmit", "validate"), ("oninput", "oninput", "update")]  # the registry classifies a shape once: only `onclick` is known
    assert [called(r) for r in rows[f"{INDEX}:16"]] == ["cancel"]  # a string with single quotes
    assert [called(r) for r in rows[f"{INDEX}:17"]] == ["go"]  # a value with no quotes
    assert [called(r) for r in rows[f"{INDEX}:20"]] == ["multiLine"] and rows[f"{INDEX}:20"][0]["column"] == 4  # the attribute of a tag over several lines
    assert [called(r) for r in rows[f"{INDEX}:28"]] == ["track"]  # inside an expression of the template
    assert [called(r) for r in rows[f"{INDEX}:33"]] == ["widget"] and [called(r) for r in rows[f"{INDEX}:34"]] == ["svgClick"]
    assert f"{INDEX}:29" not in rows  # `<Card onclick>` is a prop of a component, not an event of the page
    assert not [r for r in record["framework_entries"] if any(word in r["gap"] for word in ("inString", "inHtml", "commented"))]  # a string, a comment


@pytest.mark.parametrize("version", VERSIONS)
def test_a_value_that_is_not_a_string_written_in_place_is_a_gap_because_it_is_computed_when_the_page_is_rendered(tmp_path, version):
    record, _, _ = read(tmp_path, recorded(version), project_files(version))
    rows = seen(record)
    for site in (f"{INDEX}:25", f"{INDEX}:32"):  # `onclick={`pick(...)`}` and `{onclick}`
        [row] = rows[site]
        assert "not a string written in place" in row["gap"] and "computed when the page is rendered" in row["gap"]
        assert row["symbol"] == row["owner"] and "handler_source" not in row


@pytest.mark.parametrize("version", VERSIONS)
def test_nothing_is_bound_by_name_though_the_snapshot_holds_functions_of_those_names_the_page_cannot_reach(tmp_path, version):
    """The snapshot reads the frontmatter and every `<script>` of an `.astro` file as one module, so it declares `fromFrontmatter`
    (server code), `fromProcessedScript` (a module) and `fromModuleScript`; a lookup by name would bind the handlers to them. No row
    is bound: nothing the compiler gives says which of them the page's global scope holds."""
    from snapshot_store import open_snapshot
    record, _, manifest = read(tmp_path, recorded(version), project_files(version))
    with open_snapshot(manifest) as store:
        declared = {row[0] for row in store.connection.execute("SELECT name FROM sem_declarations WHERE file=? AND kind='function'", (EDGE,))}
    assert {"fromFrontmatter", "fromProcessedScript", "fromModuleScript"} <= declared
    edge = {called(r) for r in record["framework_entries"] if r["site"].startswith(EDGE)}
    assert edge == {"afterScripts", "afterString", "afterMultiline", "fromFrontmatter", "fromProcessedScript", "fromModuleScript", "fromLayout"}
    assert not [r for r in record["framework_entries"] if "handler_source" in r or r["symbol"] != r["owner"]]


@pytest.mark.parametrize("version", VERSIONS)
def test_the_column_is_in_bytes_where_the_compiler_counts_utf16_units_or_the_text_has_windows_line_ends(tmp_path, version):
    files = project_files(version)
    record, _, _ = read(tmp_path, recorded(version), files)
    line = files[UNICODE].split("\n")[3]  # `<p>héllo 日本語 😀</p><button onclick="afterText()">é</button>`
    [row] = [r for r in record["framework_entries"] if r["site"] == f"{UNICODE}:4"]
    assert row["column"] == len(line[:line.index("onclick")].encode("utf-8")) > line.index("onclick")
    crlf, _, _ = read(tmp_path / "crlf", recorded(version, "crlf"), project_files(version, crlf=True))
    key = lambda rows: sorted((r["site"], r["column"], r["shape"], called(r) if "calls" in r["gap"] else r["gap"]) for r in rows)
    assert key(crlf["framework_entries"]) == key(record["framework_entries"])


def test_the_three_compilers_give_the_same_rows_for_the_files_they_read(tmp_path):
    rows = {}
    for version in VERSIONS:
        record, _, _ = read(tmp_path / version, recorded(version), project_files(version))
        rows[version] = sorted((r["site"], r["column"], r["shape"], r["event"], r["symbol"]) for r in record["framework_entries"])
    assert rows["astro5"] == rows["astro6"]
    assert [r for r in rows["astro5"] if not r[0].startswith(BROKEN)] == [r for r in rows["astro7"] if not r[0].startswith(BROKEN)]
    assert len(rows["astro5"]) == 40 and len(rows["astro7"]) == 37  # the three handlers of `broken.astro`: Astro 7 reports an error and gives none
    assert [r[0] for r in rows["astro5"] if r[0].startswith(BROKEN)] == [f"{BROKEN}:5", f"{BROKEN}:7", f"{BROKEN}:8"]


# ---------------------------------------------------------------- what is a gap, and why
def test_the_go_compiler_reports_no_error_for_markup_that_does_not_close_and_compiler_rs_does_and_gives_no_events_for_that_file(tmp_path):
    go, go_gaps, _ = read(tmp_path / "go", recorded("astro5"), project_files("astro5"))
    assert go_gaps == [] and len(seen(go)[f"{BROKEN}:5"]) == 1  # the answer is the one Modal gave: no diagnostic, three rows
    rs, rs_gaps, _ = read(tmp_path / "rs", recorded("astro7"), project_files("astro7"))
    [gap] = rs_gaps
    assert (gap["kind"], gap["path"]) == ("model_partial", BROKEN)
    assert gap["detail"] == f"parse reported 2 errors in {BROKEN}, so events may be missing: Unterminated regular expression (line 9)"
    assert not [site for site in seen(rs) if site.startswith(BROKEN)]


@pytest.mark.parametrize("version", VERSIONS)
def test_a_project_that_declares_astro_and_does_not_install_it_is_a_gap_with_the_causes_words_and_no_row(tmp_path, version):
    record, gaps, _ = read(tmp_path, recorded(version, "not_installed"), project_files(version))
    [gap] = gaps
    assert gap["kind"] == "model_failed" and gap["path"] == "."
    assert "daodan-astro exited with 3" in gap["detail"] and "astro is not installed" in gap["detail"]
    assert "framework_entries" not in record


def test_an_answer_that_is_not_the_scripts_json_is_a_gap_and_no_row(tmp_path):
    record, [gap], _ = read(tmp_path, [{"root": "/work", "returncode": 0, "stdout": "not json", "stderr": ""}])
    assert gap["kind"] == "model_failed" and "printed no JSON of the known layout" in gap["detail"] and "framework_entries" not in record


def test_a_file_the_compiler_could_not_read_is_that_files_gap_and_the_others_are_still_read(tmp_path):
    [answer] = recorded("astro5")
    out = json.loads(answer["stdout"])
    for item in out["files"]:
        if item["f"] == "src/pages/about.astro":
            item["events"], item["error"] = [], "the WebAssembly instance crashed"
        if item["f"] == "src/pages/tabs.astro":
            item["unread"] = ["the position the compiler gives for onclick on <button> is not where it is written"]
            item["events"] = item["events"][1:]
    record, gaps, _ = read(tmp_path, [{**answer, "stdout": json.dumps(out)}])
    by_path = {g["path"]: g for g in gaps}
    assert by_path["src/pages/about.astro"] == {**by_path["src/pages/about.astro"], "kind": "model_failed",
                                                "detail": "parse gave nothing for src/pages/about.astro: the WebAssembly instance crashed"}
    assert by_path["src/pages/tabs.astro"]["kind"] == "model_partial" and "is not where it is written" in by_path["src/pages/tabs.astro"]["detail"]
    assert f"{INDEX}:14" in seen(record) and "src/pages/about.astro:6" not in seen(record)


def test_an_event_that_holds_nothing_is_no_row_and_each_callee_of_a_string_is_one_row_in_the_order_it_is_written(tmp_path):
    [answer] = recorded("astro5")
    out = json.loads(answer["stdout"])
    shown = {"src/pages/about.astro": [
        {"line": 6, "col": 14, "name": "onclick", "kind": "empty", "value": None, "tag": "a"},
        {"line": 6, "col": 30, "name": "onclick", "kind": "quoted", "value": "this.disabled = true", "tag": "a"},
        {"line": 6, "col": 40, "name": "onclick", "kind": "quoted", "value": "if (a) { one(); two(); one() }", "tag": "a"}]}
    out["files"] = [{**item, "events": shown.get(item["f"], [])} for item in out["files"]]
    record, gaps, _ = read(tmp_path, [{**answer, "stdout": json.dumps(out)}])
    assert gaps == [] and [called(r) for r in record["framework_entries"]] == ["one", "two"]  # each call once, in the order it is written


def test_nothing_of_astro_starts_on_the_host_without_an_engine(tmp_path, monkeypatch):
    """A project that declares Astro has, on this machine, all a build would start: its packages with the compiler and scripts that
    run at install. With no container engine the source states nothing, and none of it starts: not node, npx, npm, astro nor Daodan's
    own `daodan-astro` (each leaves a mark in a folder if it starts), not a package of the project (each leaves a mark if it is
    loaded), and no process is started at all (AGENTS.md: the project's code runs only in Daodan's container)."""
    import subprocess
    marks, tools = tmp_path / "marks", tmp_path / "bin"
    marks.mkdir()
    for name in ("node", "npx", "npm", "astro", "daodan-astro"):
        tools.mkdir(exist_ok=True)
        (tools / name).write_text(f'#!/bin/sh\necho "$0 $*" >> "{marks}/{name}"\n', encoding="utf-8", newline="\n")
        (tools / name).chmod(0o755)
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ['PATH']}")
    manifest_text = json.dumps({"dependencies": {"astro": "5.18.2"}, "scripts": {"postinstall": "node mark.js", "prepare": "astro sync"}})
    project, manifest = manifest_of(tmp_path, project_files(**{"package.json": manifest_text}))
    for name in ("astro", "@astrojs/compiler"):
        folder = project / "node_modules" / name
        folder.mkdir(parents=True)
        (folder / "package.json").write_text(json.dumps({"name": name, "main": "index.js", "version": "0.0.0"}), encoding="utf-8")
        (folder / "index.js").write_text(f"require('fs').writeFileSync({json.dumps((marks / ('loaded-' + name.replace('/', '-'))).as_posix())}, 'ran');\n",
                                         encoding="utf-8")
    started, run, popen = [], subprocess.run, subprocess.Popen
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: started.append(args) or run(*args, **kwargs))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: started.append(args) or popen(*args, **kwargs))
    monkeypatch.setattr(container, "run_in_container", lambda *args, **kwargs: {"state": "gap", "cause": "no engine", "remedy": "start one"})
    record = premap.write(manifest, sources=(premap.astro,), runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record
    # Daodan's own git lists the files of the perimeter (hooks and fsmonitor off); the project's code, nothing else, is what must not start
    assert {Path(argv[0]).stem for (argv, *_) in started} <= {"git"}
    assert all("core.hooksPath=/dev/null" in argv and "core.fsmonitor=false" in argv for (argv, *_) in started)
    assert sorted(path.name for path in marks.iterdir()) == []


@pytest.mark.parametrize("version", ("astro5", "astro7"))
def test_the_premap_the_whole_pipeline_wrote_on_modal_holds_the_rows_of_the_recorded_answer(tmp_path, version):
    """`benchmarks/astro-compiler/results/pipeline-scan-<version>.json`: the `scan` step of `modal_pipeline.py --folder-stop scan` on
    the fixture, in Daodan's container (the packages restored from the lockfile, the script with no network): its state for the source,
    its rows and its gaps are what the script's recorded answer gives here."""
    scan = json.loads((BENCHMARK / f"results/pipeline-scan-{version}.json").read_text(encoding="utf-8"))
    record, gaps, _ = read(tmp_path, recorded(version), project_files(version))
    key = lambda row: (row["site"], row["column"], row["shape"], row["event"], row["owner"], row["symbol"], row.get("gap"))
    assert sorted(map(key, scan["framework_entries"])) == sorted(map(key, record["framework_entries"]))
    assert all(SOURCE in row["sources"] for row in scan["framework_entries"]) and [s["state"] for s in scan["sources"]] == ["ran"]
    assert sorted((g["kind"], g["path"], g["detail"]) for g in scan["gaps"]) == sorted((g["kind"], g["path"], g["detail"]) for g in gaps)


# ---------------------------------------------------------------- the shapes of an event, and which names are events
@pytest.mark.parametrize("version", VERSIONS)
def test_an_svg_element_written_with_a_capital_letter_is_an_element_of_the_page_with_every_compiler(tmp_path, version):
    """`<foreignObject>` and `<textPath>` are elements, not components: the Go compiler says so, and compiler-rs, which gives only
    JSX, is told by the first letter of the name, as JSX tells a component (a capital letter) from an element."""
    record, _, _ = read(tmp_path, recorded(version), project_files(version))
    rows = seen(record)
    assert [called(r) for r in rows[f"{SVG}:5"]] == ["foreignClick"] and [called(r) for r in rows[f"{SVG}:7"]] == ["pathClick"]
    assert f"{SVG}:6" not in rows  # `<animate onend>`: `onend` is no event of the names Astro declares (`DOMAttributes`)
    assert f"{INDEX}:29" not in rows  # `<Card onclick>` is still a component: a capital letter is the only difference


@pytest.mark.parametrize("version", VERSIONS)
def test_a_call_on_an_object_and_a_callee_that_is_no_name_are_rows_with_a_gap_that_says_what_the_string_calls(tmp_path, version):
    record, _, _ = read(tmp_path, recorded(version), project_files(version))
    rows = seen(record)
    gaps = lambda line: sorted(r["gap"].split(" in a string of JavaScript")[0].split(" calls ", 1)[1] for r in rows[f"{CALLS}:{line}"])
    assert gaps(1) == ["cart.add on an object"]
    assert gaps(2) == ["save", "window.open on an object"]
    assert gaps(3) == ["items[0], a callee that is no name (subscript_expression)"]
    assert gaps(4) == ["factory", "factory(), a callee that is no name (call_expression)"]
    assert gaps(5) == ["(0, run), a callee that is no name (parenthesized_expression)"]
    assert f"{CALLS}:6" not in rows  # `new Thing()` is a constructor, not a call the query reads: a declared limit
    [one] = rows[f"{CALLS}:1"]
    assert one["symbol"] == one["owner"] and "handler_source" not in one


@pytest.mark.parametrize("version", VERSIONS)
def test_an_attribute_that_starts_with_on_is_an_event_only_when_astro_declares_it_for_every_element(tmp_path, version):
    """`one="two()"` and `onfoo` start with `on` and are no event: the names are the members of `DOMAttributes` in `astro-jsx.d.ts`,
    the declarations `astro` ships for its own JSX, which the script prints and the tree of TypeScript reads."""
    answer = json.loads(recorded(version)[0]["stdout"])
    names = premap.astro._declared(answer["jsx"])
    assert {"onclick", "onsubmit", "oninput", "onanimationend"} <= names and not {"one", "onfoo", "onend"} & names
    record, _, _ = read(tmp_path, recorded(version), project_files(version))
    assert f"{CALLS}:7" not in seen(record) and f"{CALLS}:8" not in seen(record)


def test_the_names_of_the_events_are_the_members_of_the_interface_astro_declares_them_in_and_of_no_other():
    text = ("declare namespace a.b { interface Other { onnope?: string } interface DOMAttributes { children?: any; "
            "onclick?: string | undefined | null; 'on:x'?: string; onfoo?: string } }\n")
    assert premap.astro._declared(text) == {"children", "onclick", "onfoo"}
    assert premap.astro._declared("interface Other { onnope?: string }") == set() and premap.astro._declared("") == set()


@pytest.mark.parametrize("jsx, cause", [(None, "astro-jsx.d.ts is not in the packages of astro"),
                                        ("interface Other { onnope?: string }", "declares no DOMAttributes")])
def test_without_the_names_astro_declares_no_event_is_known_and_the_gap_says_why(tmp_path, jsx, cause):
    [answer] = recorded("astro5")
    out = {**json.loads(answer["stdout"]), "jsx": jsx}
    record, gaps, _ = read(tmp_path, [{**answer, "stdout": json.dumps(out)}])
    assert "framework_entries" not in record
    [gap] = gaps
    assert gap["kind"] == "model_partial" and gap["path"] == "." and cause in gap["detail"] and "events" in gap["detail"]


# ---------------------------------------------------------------- Node, positions, time and the answer that lacks a file
def test_the_script_runs_on_node_20_with_astro_5_and_gives_the_rows_it_gives_on_node_24(tmp_path):
    """Astro 5 supports Node 20; `findPackageJSON` of `node:module` is from Node 22.14 and made the first script fail at its import
    (`benchmarks/astro-compiler/README.md`): the script finds the packages with `createRequire`, as the Angular one does."""
    [answer] = recorded(NODE20)
    assert answer["returncode"] == 0 and json.loads(answer["stdout"])["node"].startswith("v20.")
    assert json.loads(recorded("astro5")[0]["stdout"])["node"].startswith("v24.")
    on20, _, _ = read(tmp_path / "n20", recorded(NODE20), project_files("astro5"))
    on24, _, _ = read(tmp_path / "n24", recorded("astro5"), project_files("astro5"))
    key = lambda record: sorted((r["site"], r["column"], r["shape"], r["gap"]) for r in record["framework_entries"])
    assert key(on20) == key(on24) and len(key(on20)) == 40


@pytest.mark.parametrize("version", (*VERSIONS, NODE20))
@pytest.mark.parametrize("key", ("installed", "crlf"))
def test_every_position_the_script_printed_is_where_the_text_writes_the_name_of_the_attribute(version, key):
    """Line from 1 and column in UTF-16 code units from 0, against the file's own text (the script computes both from the offset it
    has checked, never from the line and column the compiler wrote beside it)."""
    files = project_files("astro5", crlf=key == "crlf")
    [answer] = recorded(version, key)
    printed = json.loads(answer["stdout"])["files"]
    assert len(printed) == 13
    for item in printed:
        lines = files[item["f"]].split("\n")
        for event in item["events"]:
            from_column = lines[event["line"] - 1].encode("utf-16-le")[2 * event["col"]:].decode("utf-16-le")
            assert from_column.startswith(event["name"]) and not from_column[len(event["name"]):][:1].isalnum(), (item["f"], event)  # `{onclick}` too


def test_a_command_the_time_limit_ends_or_kills_is_a_gap_with_the_limit_in_seconds_and_no_row(tmp_path):
    [ended] = recorded("astro5", "timeout")  # the real script with 0.05 seconds, on Modal: `timeout` ended it
    assert ended["returncode"] == 124 and ended["stdout"] == ""
    seconds = str(premap.astro.seconds(1))
    record, [gap], _ = read(tmp_path / "ended", [ended])
    assert (gap["kind"], gap["path"], gap["detail"]) == ("model_failed", ".", f"daodan-astro did not end in {seconds} seconds")
    assert "framework_entries" not in record
    record, [gap], _ = read(tmp_path / "killed", [{**ended, "returncode": 137}])
    assert gap["detail"] == (f"daodan-astro was killed (exit 137): it did not end in {seconds} seconds, "
                             f"or it ran out of memory ({premap.astro.MEMORY_GB} GB)")


def test_the_time_the_commands_have_is_shared_between_the_folders_with_a_least_for_each():
    assert premap.astro.seconds(1) == premap.astro.TOTAL_SECONDS
    assert premap.astro.seconds(4) * 4 <= premap.astro.TOTAL_SECONDS and premap.astro.seconds(10_000) == 10


def test_a_file_the_answer_does_not_hold_is_a_gap_and_not_a_silence_and_the_others_are_still_read(tmp_path):
    [answer] = recorded("astro5")
    out = json.loads(answer["stdout"])
    out["files"] = [f for f in out["files"] if f["f"] != "src/pages/about.astro"]
    record, gaps, _ = read(tmp_path, [{**answer, "stdout": json.dumps(out)}])
    assert [(g["kind"], g["path"], g["detail"]) for g in gaps] == [
        ("model_failed", "src/pages/about.astro", "parse gave nothing for src/pages/about.astro: it is not in the answer")]
    assert f"{INDEX}:14" in seen(record) and "src/pages/about.astro:6" not in seen(record)


def test_the_cause_a_failed_command_gives_is_both_ends_of_what_the_tool_said(tmp_path):
    said = "first cause " + "x" * 1000 + " last word"
    _, [gap], _ = read(tmp_path, [{"root": "/work", "returncode": 1, "stdout": "", "stderr": said}])
    assert gap["detail"].startswith("daodan-astro exited with 1: first cause ") and gap["detail"].endswith(" last word") and "[...]" in gap["detail"]


# ---------------------------------------------------------------- how it joins the rest
def test_the_source_is_registered_with_a_facet_that_joins_nothing_and_is_not_a_framework_source_of_routes():
    assert premap.astro in premap.SOURCES and premap.IDENTITY["framework_entries"] == ()
    assert premap.astro not in premap.FRAMEWORK_SOURCES  # its rows are the attribute reader's: `entries.compiled`


def test_a_premap_made_before_the_source_is_stale(tmp_path):
    _, manifest = manifest_of(tmp_path, project_files())
    before = tuple(source for source in premap.SOURCES if source is not premap.astro)
    premap.write(manifest, sources=before)
    assert premap.state(manifest, sources=before)["state"] == "fresh"
    assert premap.state(manifest)["state"] == "stale"


def test_in_the_links_each_row_is_a_gap_at_its_site_and_the_gaps_of_the_compiler_are_told_with_them(tmp_path):
    import entries
    import flows
    _, _, manifest = read(tmp_path, recorded("astro7"), project_files("astro7"))
    links = flows.cached_links(manifest, [])
    assert (len(links["entries"]), len(links["gaps"])) == (0, 35)  # no function is known for any row; 37 rows, but the two events of line 22 of `index.astro`
    # (`onsubmit`, `oninput`) are not in the links: their shapes are not in the registry, which classifies each shape once (`QUERIES["events"]`)
    sites = {g["site"]: g["reason"] for g in links["gaps"]}
    assert "calls save in a string of JavaScript" in sites[f"{INDEX}:14"]
    assert f"{BROKEN}:5" not in sites and {g["path"] for g in links["source_gaps"] if g.get("source") == SOURCE} == {BROKEN}
    assert {r["site"] for r in entries._cached_rows(manifest)} >= {f"{INDEX}:14", f"{EDGE}:17"}


def test_without_the_compilers_rows_the_template_of_an_astro_file_gives_no_row(tmp_path):
    import entries
    _, manifest = manifest_of(tmp_path, project_files())
    rows = [r for r in entries._cached_rows(manifest) if r["site"].partition(":")[0].endswith(".astro")]
    assert rows and not [r for r in rows if r["reader"] == "attributo"]  # the `<script>` blocks are JavaScript the language's reader has; no tree reader of the template


def test_the_source_is_part_of_the_key_of_the_cached_links_beside_the_other_sources_of_a_template():
    """`flows._links_reader_digest` hashes the files of every source whose rows join the tree reader's (`premap.TEMPLATE_SOURCES`).
    Its script is not in it: the pre-map is fresh for the `NAME@VERSION` that made it, and the version goes with the script (the
    test of the recorded print)."""
    import flows
    from pathlib import Path as Reader
    assert premap.TEMPLATE_SOURCES == (premap.angular, premap.astro)
    seen_files = []
    with patch.object(Reader, "read_bytes", autospec=True, side_effect=lambda self: seen_files.append(self.name) or b""):
        flows._links_reader_digest.__wrapped__()
    assert "astro.py" in seen_files and "angular.py" in seen_files
