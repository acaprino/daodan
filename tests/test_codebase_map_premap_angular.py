"""The events an Angular project's own compiler reads in its templates, read from its output and bound to the snapshot.

`parseTemplate` of the project's `@angular/compiler` runs in Daodan's container (`premap/angular_templates.mjs`); the
container is a fake here: the answers are the ones the real script printed on Modal for
`benchmarks/angular-compiler/fixture` (`tests/fixtures/premap/angular/`, recorded by
`benchmarks/angular-compiler/modal_probe.py`). The components, their templates and where an inline template lies are read
from the files' syntax trees (`QUERIES["components"]`), and each position is checked against the text itself.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_codebase_map_premap_container_runner import container, container_runner, manifest_of, premap, recorder

import preparation  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[1] / "benchmarks/angular-compiler/fixture"
RECORDED = Path(__file__).parent / "fixtures/premap/angular"
SOURCE = "angular@daodan/premap/v2"


def project_files(**changes) -> dict[str, str | None]:
    """The fixture as the benchmark runs it: `crlf.component.ts` has Windows line ends (git keeps every text with `\\n`)."""
    files = {path.relative_to(FIXTURE).as_posix(): path.read_text(encoding="utf-8")
             for path in FIXTURE.rglob("*") if path.is_file() and path.name != "package-lock.json"}
    files["src/app/crlf.component.ts"] = files["src/app/crlf.component.ts"].replace("\n", "\r\n")
    files.update(changes)
    return {rel: text for rel, text in files.items() if text is not None}


def commands_of(tmp_path, files):
    from snapshot_store import open_snapshot
    project, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        return project, manifest, premap.angular.commands(premap.Context(manifest, store))


def position(text: str, offset: int) -> list[int]:
    """Row and column of `offset` the way JavaScript counts them: rows by `\\n`, a column in UTF-16 code units."""
    before = text[:offset]
    row = before.count("\n")
    return [row, len(before.rsplit("\n", 1)[-1].encode("utf-16-le")) // 2]


def inline_range(text: str, opening: str, closing: str) -> list[int]:
    """Where the content of the literal that opens with `opening` ends with `closing` lies, from the text itself."""
    start = text.index(opening) + len(opening)
    return [*position(text, start), *position(text, text.index(closing, start))]


def listed(command) -> list[dict]:
    """The templates a command lists: the file the container is given (`inputs`), which its argument names."""
    [(name, text)] = command["inputs"].items()
    assert command["argv"][-1] == f"{preparation.IN}/{name}"
    return json.loads(text)


def parsing(asked) -> list[dict]:
    """The commands that parse the templates: each folder has one, and one that asks the type-checker (`typing`)."""
    return [c for c in asked if c["argv"][0] == "daodan-angular"]


def typing(asked) -> list[dict]:
    return [c for c in asked if "--types" in c["argv"]]


def jobs(asked) -> list[tuple]:
    return sorted((job["f"], tuple(job.get("r", ()))) for command in parsing(asked) for job in listed(command))


def test_each_template_of_a_component_is_a_job_with_where_an_inline_one_lies_checked_against_the_text(tmp_path):
    files = project_files()
    _, _, asked = commands_of(tmp_path, files)
    [command] = parsing(asked)
    assert (command["tool"], command["cwd"], command["network"], command["env"]) == ("angular", ".", "none", {})
    assert command["argv"][0] == "daodan-angular" and len(command["argv"]) == 2
    app = "src/app/"
    text = lambda name: files[app + name].replace("\r\n", "\n")
    assert jobs(asked) == sorted([
        (app + "app.component.html", ()), (app + "bad.component.html", ()), (app + "legacy.component.html", ()),
        (app + "accents.component.ts", tuple(inline_range(text("accents.component.ts"), "template: `", "`,\n"))),
        (app + "crlf.component.ts", tuple(inline_range(text("crlf.component.ts"), "template: `", "`,\n"))),
        (app + "editor.component.ts", tuple(inline_range(text("editor.component.ts"), "template: `", "`,\n"))),
        (app + "gone.component.ts", tuple(inline_range(text("gone.component.ts"), "template: '", "',\n"))),
        (app + "orders.component.ts", tuple(inline_range(text("orders.component.ts"), "template: '", "',\n"))),
        (app + "unreached.component.ts", tuple(inline_range(text("unreached.component.ts"), "template: '", "',\n"))),
        (app + "scoped.component.ts", tuple(inline_range(text("scoped.component.ts"), "template: `", "`,\n"))),
        (app + "callee.component.ts", tuple(inline_range(text("callee.component.ts"), "template: `", "`,\n"))),
        (app + "inline.component.ts", tuple(inline_range(text("inline.component.ts"), "template: `", "`,\n"))),
        (app + "inline.component.ts", tuple(inline_range(text("inline.component.ts"), "template: '", "',\n"))),
        (app + "inline.component.ts", tuple(inline_range(text("inline.component.ts"), 'template: "', '",\n'))),
    ])


def test_the_range_the_real_compiler_got_for_the_fixture_s_first_inline_template_is_the_one_read_from_the_tree(tmp_path):
    """The compiler's own `getTemplateLocation` and range, measured on Modal (`results/02_inline.txt`): the template literal of
    `inline.component.ts` starts at line 5, column 13 (0-based) and ends at offset 359."""
    files = project_files()
    _, _, asked = commands_of(tmp_path, files)
    ranges = {tuple(job["r"]) for command in parsing(asked) for job in listed(command)
              if job["f"] == "src/app/inline.component.ts" and "r" in job}
    text = files["src/app/inline.component.ts"]
    start, end = position(text, 197), position(text, 359)
    assert start == [5, 13] and tuple([*start, *end]) in ranges


def test_the_commands_run_daodans_script_on_the_projects_own_packages_without_network_and_the_setup_installs_no_package(tmp_path):
    import preparation
    from snapshot_store import open_snapshot
    project, manifest = manifest_of(tmp_path, project_files())
    with open_snapshot(manifest) as store:
        asked = premap.angular.commands(premap.Context(manifest, store))
    spec = container_runner.TOOLS["angular"]
    assert (spec["restores"], spec["runs_on"]) == ("node", ("node",))  # the project's `@angular/compiler` is in its packages
    assert any(item[2] == "angular_templates.mjs" and item[0] is None for item in spec["files"])  # Daodan's own file, beside the source
    assert (container_runner.Path(container_runner.__file__).parent / "angular_templates.mjs").is_file()
    calls, fake = recorder()
    carried = {}

    def spy(project, commands, **options):  # what the container is given, read while the run holds it (the files are temporary)
        carried.update({destination: (path.read_bytes() if path.is_file() else path) for destination, path in options["inputs"]().items()})
        return fake(project, commands, **options)
    with patch.object(container, "run_commands", spy), patch.object(container_runner, "fetched", lambda url, sha, name: Path("/host") / name
                                                                    if url or name != "angular_templates.mjs" else Path(container_runner.__file__).with_name(name)):
        container_runner.runner(manifest)(asked)
    first, *rest = calls[0]["commands"]
    plan = preparation.node_prepare(["package.json"], lambda rel: (project / rel).read_text(encoding="utf-8"))
    setup = first["argv"][-1]
    assert len(rest) == 2 and rest[1]["argv"][:4] == ["timeout", "--kill-after=10", str(premap.angular.types_seconds(1)), "daodan-angular"]
    assert f"( {plan['lines'][0]} )" in setup and "install -g" not in setup  # the restore of the project's packages, nothing else
    assert f"{container_runner.T}/bin/daodan-angular" in setup and "angular_templates.mjs" in setup
    assert [c["network"] for c in rest] == ["none", "none"] and rest[0]["argv"][0] == "daodan-angular"
    assert carried[f"{preparation.IN}/angular_templates.mjs"] == Path(container_runner.__file__).with_name("angular_templates.mjs").read_bytes()
    assert carried[f"{preparation.IN}/angular-jobs-0.json"].decode("utf-8") == next(iter(asked[0]["inputs"].values()))
    assert "inputs" not in rest[0]  # what the engine is asked to run is the command alone


def test_a_project_without_angular_or_without_components_runs_nothing(tmp_path):
    from snapshot_store import open_snapshot
    files = {"package.json": '{"dependencies": {"react": "19.3.1"}}\n', "web/package.json": "{",
             "tools/package.json": '["@angular/core"]\n', "src/app.component.ts": "export class A {}\n",
             "ng/package.json": '{"dependencies": {"@angular/core": "22.3.0"}}\n', "ng/src/plain.ts": "export const x = 1;\n"}
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        assert premap.angular.commands(premap.Context(manifest, store)) is None
    record = premap.write(manifest, sources=(premap.angular,), runner=lambda commands: 1 / 0)
    assert record["sources"][0]["state"] == "not_needed" and "framework_entries" not in record


def test_each_package_json_declaring_angular_among_its_dependencies_or_dev_dependencies_is_one_command_for_its_own_files(tmp_path):
    component = ("import { Component } from '@angular/core';\n@Component({selector: 'a', template: '<b (click)=\"go()\"></b>'})\n"
                 "export class A { go() {} }\n")
    files = {"apps/a/package.json": '{"dependencies": {"@angular/core": "22.3.0"}}\n', "apps/a/src/a.component.ts": component,
             "apps/b/package.json": '{"devDependencies": {"@angular/compiler": "22.3.0"}}\n', "apps/b/b.component.ts": component,
             "apps/b/inner/package.json": '{"dependencies": {"@angular/core": "22.3.0"}}\n', "apps/b/inner/c.component.ts": component,
             "apps/c/package.json": '{"dependencies": {"react": "19.3.1"}}\n', "apps/c/c.component.ts": component}
    _, _, asked = commands_of(tmp_path, files)
    assert [(c["cwd"], [job["f"] for job in listed(c)]) for c in parsing(asked)] == [
        ("apps/a", ["src/a.component.ts"]), ("apps/b", ["b.component.ts"]), ("apps/b/inner", ["c.component.ts"])]


# ---------------------------------------------------------------- what the recorded script answers
APP = "src/app/app.component.ts"


def recorded(name: str) -> list[dict]:
    """The answers of the real script on Modal (`benchmarks/angular-compiler/modal_probe.py --mode source`), as the container
    runner returns them for each command."""
    return [{"root": "/work", **answer} for answer in json.loads((RECORDED / name).read_text(encoding="utf-8"))]


def read(tmp_path, answers=None, files=None):
    _, manifest = manifest_of(tmp_path, files or project_files())
    record = premap.write(manifest, sources=(premap.angular,), runner=lambda commands: answers or recorded("fixture.json"))
    return record, [g for g in record["gaps"] if g.get("source") == SOURCE], manifest


def column(files, file, line, text) -> int:
    """Where `text` starts in the line, in bytes: the column the snapshot's readers write."""
    return len(files[file].replace("\r\n", "\n").split("\n")[line - 1].split(text)[0].encode("utf-8"))


def bound(record, manifest) -> dict:
    """The record with its Angular rows bound to the snapshot's declarations, as `entries.compiled` binds them when the links are made."""
    from snapshot_store import open_snapshot
    with open_snapshot(manifest) as store:
        return {**record, "framework_entries": premap.angular.bind(record["framework_entries"], store)}


def seen(record) -> dict:
    out = {}
    for row in record["framework_entries"]:
        out.setdefault((row["site"], row["column"]), []).append((row["symbol"], row.get("gap")))
    return out


def test_the_events_of_the_three_cases_are_rows_on_the_methods_of_their_classes_with_the_file_and_line_of_the_event(tmp_path):
    files = project_files()
    record, _, manifest = read(tmp_path)
    record = bound(record, manifest)
    html = "src/app/app.component.html"
    on = lambda cls, name, file=APP: (f"{file}::{cls}.{name}", None)
    at = lambda file, line, text: (f"{file}:{line}", column(files, file, line, text))
    inline = "src/app/inline.component.ts"
    expected = {
        at(html, 2, "(click)"): [on("AppComponent", "save")],  # `save()`
        at(html, 3, "(click)"): [on("AppComponent", "save")],  # `this.save()`
        at(html, 4, "(click)"): [on("OrderService", "cancel", "src/app/order.service.ts")],  # `svc.cancel()`: the type-checker says which
        at(html, 5, "(click)"): [on("AppComponent", "save")],  # `!busy && save()`
        at(html, 6, "(click)"): [on("AppComponent", "close"), on("AppComponent", "reopen")],
        at(html, 7, "(click)"): [on("AppComponent", "save"), on("AppComponent", "close")],
        at(html, 10, "(click)"): [on("AppComponent", "pay")],
        at(html, 11, "(click)"): [on("AppComponent", "withIcon")],
        at(html, 12, "(ngSubmit)"): [on("AppComponent", "submit")],
        at(html, 13, "(keyup.enter)"): [on("AppComponent", "search")],
        at(html, 17, "(click)"): [on("AppComponent", "inIf")],  # inside `@if`
        at(html, 20, "(click)"): [on("AppComponent", "liClick")],  # on the `li` with `*ngFor`: one row, not two
        at(html, 21, "(click)"): [on("AppComponent", "remove")],
        at(html, 25, "(click)"): [on("AppComponent", "removeFor")],  # inside `@for`
        at(html, 28, "(click)"): [on("AppComponent", "inTpl")],  # inside `ng-template`
        at(html, 30, "(window:resize)"): [on("AppComponent", "onResize")],
        at(html, 31, "(saved)"): [on("AppComponent", "onSaved")],
        at("src/app/legacy.component.html", 1, "(click)"): [on("LegacyComponent", "legacySave", "src/app/legacy.component.ts")],
        # a template written in the decorator: the file and line are the `.ts`'s
        at(inline, 9, "(click)"): [on("InlineComponent", "go", inline)],
        at(inline, 10, "(click)"): [on("InlineComponent", "goThis", inline)],
        at(inline, 24, '(click)="esc()'): [on("InlineEscapedComponent", "esc", inline)],
        at(inline, 24, '(click)="esc2()'): [on("InlineEscapedComponent", "esc2", inline)],
        at(inline, 33, "(click)"): [on("InlineDoubleQuotedComponent", "dq", inline)],
        at("src/app/accents.component.ts", 6, "(click)"): [on("AccentsComponent", "brew", "src/app/accents.component.ts")],
        at("src/app/crlf.component.ts", 6, "(click)"): [on("CrlfComponent", "go", "src/app/crlf.component.ts")],
        at("src/app/crlf.component.ts", 7, "(click)"): [on("CrlfComponent", "stop", "src/app/crlf.component.ts")],
        at("src/app/bad.component.html", 1, "(click)"): [on("BadComponent", "oops", "src/app/bad.component.ts")],
    }
    found = {key: rows for key, rows in seen(record).items() if not key[0].startswith(("src/app/scoped.component.ts", "src/app/callee.component.ts"))}  # tests of their own
    assert {key: rows for key, rows in found.items() if key in expected} == expected
    gaps = {key: rows for key, rows in found.items() if key not in expected}
    assert sorted(gaps) == sorted([at(html, 9, "(click)"), at("src/app/editor.component.ts", 5, "(click)"),
                                   at("src/app/gone.component.ts", 5, "(click)"), at("src/app/unreached.component.ts", 6, "(click)")])
    assert all(len(rows) == 1 and rows[0][1] for rows in gaps.values())
    row = next(r for r in record["framework_entries"] if r["site"] == f"{html}:2")
    assert (row["reader"], row["shape"], row["event"], row["handler_source"], row["owner"], row["sources"]) == (
        "attributo", "(click)", "click", "angular", f"{APP}::AppComponent", [SOURCE])


def test_an_event_that_calls_nothing_is_no_row_and_a_call_the_type_checker_places_outside_the_snapshot_or_cannot_place_is_a_gap_that_says_why(tmp_path):
    record, _, manifest = read(tmp_path)
    record = bound(record, manifest)
    html = "src/app/app.component.html"
    assert not [r for r in record["framework_entries"] if r["site"] == f"{html}:8"]  # `open = !open`
    assert not [r for r in record["framework_entries"] if r["site"] == f"{html}:13" and r["shape"] != "(keyup.enter)"]  # `[(ngModel)]`
    gap = {r["site"]: r["gap"] for r in record["framework_entries"] if r.get("gap")}
    assert "router.navigate is declared in node_modules/@angular/router" in gap[f"{html}:9"] and "does not hold" in gap[f"{html}:9"]
    assert "saved.emit is declared in node_modules/@angular/core" in gap["src/app/editor.component.ts:5"]
    assert "UnreachedComponent" in gap["src/app/unreached.component.ts:6"] and "tsconfig.json" in gap["src/app/unreached.component.ts:6"]
    assert "GoneComponent does not declare gone" in gap["src/app/gone.component.ts:5"]
    assert f"{html}:4" not in gap  # `svc.cancel()` is the method the type-checker places in order.service.ts, no gap
    owner = {r["site"]: r["symbol"] for r in record["framework_entries"] if r.get("gap")}
    assert owner[f"{html}:9"] == f"{APP}::AppComponent"  # the gap stays with the component whose template holds the event


def test_what_is_read_before_the_run_and_what_the_compiler_reports_are_gaps_with_their_cause(tmp_path):
    _, gaps, _ = read(tmp_path)
    assert sorted((g["kind"], g["path"]) for g in gaps) == [
        ("model_partial", "src/app/bad.component.html"), ("model_partial", "src/app/computed.component.ts"),
        ("outside_snapshot", "src/app/nowhere.component.html")]
    detail = {g["path"]: g["detail"] for g in gaps}
    assert "oops(" in detail["src/app/bad.component.html"] and "2 errors" in detail["src/app/bad.component.html"]
    assert "ComputedComponent" in detail["src/app/computed.component.ts"] and "${...}" in detail["src/app/computed.component.ts"]
    assert "MissingComponent" in detail["src/app/nowhere.component.html"]


def test_a_project_that_declares_angular_and_does_not_install_the_compiler_is_a_gap_with_the_causes_words(tmp_path):
    record, gaps, _ = read(tmp_path, recorded("not-installed.json"))
    [failed] = [g for g in gaps if g["kind"] == "model_failed"]
    assert failed["path"] == "." and "exited with 3" in failed["detail"]
    assert "@angular/compiler is not installed" in failed["detail"] and "Cannot find module" in failed["detail"]
    assert "framework_entries" not in record  # no row is guessed where the compiler gave none


def test_an_answer_that_is_not_the_scripts_json_is_a_gap_and_no_row(tmp_path):
    for number, stdout in enumerate(("", "not json", '{"templates": 3}', '{"compiler": "22.3.0"}')):
        printed = {"root": "/work", "returncode": 0, "stdout": stdout, "stderr": ""}
        record, gaps, _ = read(tmp_path / str(number), [printed, printed])
        assert any(g["kind"] == "model_failed" and "JSON" in g["detail"] for g in gaps) and "framework_entries" not in record


def test_a_template_the_script_could_not_read_is_that_template_s_gap_and_the_others_are_still_read(tmp_path):
    answer, types = recorded("fixture.json")
    printed = json.loads(answer["stdout"])
    broken = next(t for t in printed["templates"] if t["f"] == "src/app/app.component.html")
    broken["events"], broken["error"] = [], "ENOENT: no such file or directory, open 'src/app/app.component.html'"
    record, gaps, _ = read(tmp_path, [{**answer, "stdout": json.dumps(printed)}, types])
    assert any(g["kind"] == "model_failed" and g["path"] == "src/app/app.component.html" and "ENOENT" in g["detail"] for g in gaps)
    assert not [r for r in record["framework_entries"] if r["site"].startswith("src/app/app.component.html")]
    assert any(r["site"].startswith("src/app/legacy.component.html") for r in record["framework_entries"])


def test_a_project_of_many_templates_gives_the_container_the_whole_list_as_a_file_and_no_gap(tmp_path):
    """The list does not travel in the command's argument (a command line has a limit): it is a file the container is given
    beside Daodan's script, and what the command names is that file's path."""
    from snapshot_store import open_snapshot
    files = {"package.json": '{"dependencies": {"@angular/core": "22.3.0"}}\n'}
    for number in range(400):
        files[f"src/features/feature-{number}/very-long-feature-name-{number}.component.ts"] = (
            "import { Component } from '@angular/core';\n@Component({selector: 'a', templateUrl: './the-template-of-the-feature/template.html'})\n"
            f"export class Feature{number} {{ go() {{}} }}\n")
        files[f"src/features/feature-{number}/the-template-of-the-feature/template.html"] = "<b (click)=\"go()\"></b>\n"
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        context = premap.Context(manifest, store)
        [command, _] = premap.angular.commands(context)
        gaps = premap.angular._plan(context)["gaps"]
    assert len(command["argv"]) == 2 and len(command["argv"][-1]) < 100  # a path
    assert len(listed(command)) == 400 and len(command["inputs"]["angular-jobs-0.json"]) > 20000 and gaps == []


def test_nothing_of_angular_starts_on_the_host_without_an_engine(tmp_path, monkeypatch):
    """A project that declares Angular has, on this machine, all a build would start: packages with the compiler, the compiler-cli
    and TypeScript, and scripts that run at install. With no container engine the source states nothing, and none of it starts:
    not node, npx, npm, ngc, tsc, `timeout` nor Daodan's own `daodan-angular` (each leaves a mark in a folder if it starts), not a
    package of the project (each leaves a mark if it is loaded), and no process is started at all (AGENTS.md: the project's code
    runs only in Daodan's container)."""
    import subprocess
    marks, tools = tmp_path / "marks", tmp_path / "bin"
    marks.mkdir()
    for name in ("node", "npx", "npm", "ngc", "tsc", "timeout", "daodan-angular"):
        tools.mkdir(exist_ok=True)
        (tools / name).write_text(f'#!/bin/sh\necho "$0 $*" >> "{marks}/{name}"\n', encoding="utf-8", newline="\n")
        (tools / name).chmod(0o755)
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ['PATH']}")
    manifest_text = json.dumps({"dependencies": {"@angular/core": "22.3.0"}, "devDependencies": {"@angular/compiler-cli": "22.3.0"},
                                "scripts": {"postinstall": "node mark.js", "prepare": "ngc -p tsconfig.json"}})
    project, manifest = manifest_of(tmp_path, project_files(**{"package.json": manifest_text}))
    for name in ("@angular/compiler", "@angular/compiler-cli", "typescript"):
        folder = project / "node_modules" / name
        folder.mkdir(parents=True)
        (folder / "package.json").write_text(json.dumps({"name": name, "main": "index.js", "version": "0.0.0"}), encoding="utf-8")
        (folder / "index.js").write_text(f"require('fs').writeFileSync({json.dumps((marks / ('loaded-' + name.replace('/', '-'))).as_posix())}, 'ran');\n",
                                         encoding="utf-8")
    started, run, popen = [], subprocess.run, subprocess.Popen
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: started.append(args) or run(*args, **kwargs))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: started.append(args) or popen(*args, **kwargs))
    monkeypatch.setattr(container, "run_in_container", lambda *args, **kwargs: {"state": "gap", "cause": "no engine", "remedy": "start one"})
    record = premap.write(manifest, sources=(premap.angular,), runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record
    # Daodan's own git lists the files of the perimeter (hooks and fsmonitor off); the project's code, nothing else, is what must not start
    assert {Path(argv[0]).stem for (argv, *_) in started} <= {"git"}
    assert all("core.hooksPath=/dev/null" in argv and "core.fsmonitor=false" in argv for (argv, *_) in started)
    assert sorted(path.name for path in marks.iterdir()) == []


def test_the_source_is_registered_with_a_facet_that_joins_nothing():
    assert premap.angular in premap.SOURCES and premap.IDENTITY["framework_entries"] == ()


def test_a_premap_made_before_the_source_is_stale(tmp_path):
    _, manifest = manifest_of(tmp_path, project_files())
    before = tuple(source for source in premap.SOURCES if source is not premap.angular)
    premap.write(manifest, sources=before)
    assert premap.state(manifest, sources=before)["state"] == "fresh"
    assert premap.state(manifest)["state"] == "stale"


def test_in_the_links_the_compilers_rows_replace_the_tree_readers_at_the_same_event_and_the_label_stays(tmp_path):
    """Both read `(click)="save()"` of a `.html`: the tree reader gives a gap (it cannot tell which class's method), the compiler
    the method. Where both read an event the links hold one row, the compiler's, with the label the tree reader read."""
    import entries
    import flows
    _, _, manifest = read(tmp_path)
    links = flows.cached_links(manifest, [])
    html = "src/app/app.component.html"
    by_site = {}
    for found in links["entries"]:
        by_site.setdefault(found["site"], []).append(found)
    [save] = by_site[f"{html}:2"]
    assert (save["symbol"], save["label"], save["handler_source"], save["reader"], save["shape"]) == (
        f"{APP}::AppComponent.save", "Save order", "angular", "attributo", "(click)")
    assert [(e["symbol"], e["label"]) for e in by_site[f"{html}:10"]] == [(f"{APP}::AppComponent.pay", "Pay for the order")]
    assert sorted(e["symbol"] for e in by_site[f"{html}:7"]) == [f"{APP}::AppComponent.close", f"{APP}::AppComponent.save"]
    [brew] = by_site["src/app/accents.component.ts:6"]  # a template the tree reader never read: no label either
    assert (brew["symbol"], brew.get("label")) == ("src/app/accents.component.ts::AccentsComponent.brew", None)
    reasons = {(g["site"], g["reason"]) for g in links["gaps"]}
    assert not [r for _, r in reasons if "not resolved" in r and "handler" in r and "save" in r]  # the tree reader's gaps are gone
    assert [(e["symbol"], e.get("label")) for e in by_site[f"{html}:4"]] == [("src/app/order.service.ts::OrderService.cancel", None)]  # no tree row, no label
    assert any(site == f"{html}:9" and "router.navigate" in why for site, why in reasons)
    assert not [site for site, _ in reasons if site == f"{html}:2"]
    assert {g["path"] for g in links["source_gaps"] if g.get("source") == SOURCE} == {
        "src/app/bad.component.html", "src/app/computed.component.ts", "src/app/nowhere.component.html"}
    assert (len(links["entries"]), len(links["gaps"])) == (28, 9)  # the `(click)` events that call a method; router, saved.emit, gone, unreached, and the scoped and callee components'
    shown = [c for c in entries.cached_syntax(manifest) if c["site"] == f"{html}:2"]
    assert [(c["symbol"], c["label"], c["handler_source"]) for c in shown] == [(f"{APP}::AppComponent.save", "Save order", "angular")]


def test_without_the_compilers_rows_the_tree_readers_stay_as_they_were(tmp_path):
    import entries
    import flows
    _, manifest = manifest_of(tmp_path, project_files())
    assert {r["site"] for r in entries._cached_rows(manifest)} >= {"src/app/app.component.html:2", "src/app/app.component.html:10"}
    before = flows.cached_links(manifest, [])
    assert (len(before["entries"]), len(before["gaps"])) == (0, 11)  # the tree reader alone: every handler "not resolved"
    premap.write(manifest, sources=(premap.angular,), runner=lambda commands: recorded("not-installed.json"))  # the compiler gave nothing
    rows = [r for r in entries._cached_rows(manifest) if r["site"] == "src/app/app.component.html:2"]
    assert [(r["symbol"], r["gap"]) for r in rows] == [("src/app/app.component.html::<module>", "handler save not resolved")]
    after = flows.cached_links(manifest, [])
    assert (len(after["entries"]), len(after["gaps"])) == (0, 11)


def test_a_file_belongs_to_the_nearest_package_json_that_declares_angular_even_when_its_folder_name_is_one_character(tmp_path):
    component = ("import { Component } from '@angular/core';\n@Component({selector: 'a', template: '<b (click)=\"go()\"></b>'})\n"
                 "export class A { go() {} }\n")
    angular = '{"dependencies": {"@angular/core": "22.3.0"}}\n'
    files = {"package.json": angular, "root.component.ts": component, "a/package.json": angular, "a/x.component.ts": component}
    _, _, asked = commands_of(tmp_path, files)
    assert [(c["cwd"], [job["f"] for job in listed(c)]) for c in parsing(asked)] == [
        (".", ["root.component.ts"]), ("a", ["x.component.ts"])]


def test_the_premap_the_whole_pipeline_wrote_on_modal_holds_the_rows_of_the_recorded_answer(tmp_path):
    """`benchmarks/angular-compiler/results/pipeline-scan.json`: the `scan` step of `modal_pipeline.py --folder-stop scan` on the
    fixture, in Daodan's container (the packages restored from the lockfile, the script with no network): its state for the source,
    its rows and its gaps are what the script's recorded answer gives here."""
    scan = json.loads((FIXTURE.parent / "results/pipeline-scan.json").read_text(encoding="utf-8"))
    record, gaps, manifest = read(tmp_path)
    assert scan["framework_entries"] == record["framework_entries"]
    key = lambda row: (row["site"], row["column"], row["shape"], row["event"], row["owner"], row["symbol"], row.get("gap"))
    assert sorted(map(key, bound(scan, manifest)["framework_entries"])) == sorted(map(key, bound(record, manifest)["framework_entries"]))
    assert len(scan["framework_entries"]) == 41 and all(SOURCE in row["sources"] for row in scan["framework_entries"])
    assert {s["source"]: s["state"] for s in scan["sources"]}[SOURCE] == "ran"
    assert sorted((g["kind"], g["path"], g["detail"]) for g in scan["gaps"]) == sorted((g["kind"], g["path"], g["detail"]) for g in gaps)


HEAD = "import { Component } from '@angular/core';\n"


def _imports_the_decorator(context, rel: str) -> bool:
    import entries
    source = context.inventory.text(rel).encode("utf-8")
    found = entries._matches(source, "typescript", "components", entries._parse(source, "typescript"))
    return bool(premap.angular._decorator_names(source, found))


def test_every_file_the_import_chooses_is_read_or_a_gap_that_names_its_site_or_applies_no_decorator(tmp_path):
    """A `Component` imported from `@angular/core` chooses a file. Each decorator it applies gives the components read or a gap
    with the file and line: an alias, an abstract class and a default export are read; `@Component(meta)`, an anonymous class
    and a `{ template }` that is no text are gaps."""
    from snapshot_store import open_snapshot
    angular = '{"dependencies": {"@angular/core": "22.3.0"}}\n'
    go = "<b (click)=\"go()\"></b>"
    files = {
        "package.json": angular,
        "ok.component.ts": HEAD + f"@Component({{selector: 'a', template: '{go}'}})\nexport class Plain {{ go() {{}} }}\n",
        "alias.component.ts": "import { Component as C } from '@angular/core';\n"
                              f"@C({{selector: 'a', template: '{go}'}})\nexport class Aliased {{ go() {{}} }}\n",
        "default.component.ts": HEAD + f"@Component({{template: '{go}'}})\nexport default class Defaulted {{ go() {{}} }}\n",
        "abstract.component.ts": HEAD + f"@Component({{template: '{go}'}})\nexport abstract class Abstracted {{ go() {{}} }}\n",
        "meta.component.ts": HEAD + "const meta = {template: '<b></b>'};\n\n@Component(meta)\nexport class Meta {}\n",
        "anonymous.component.ts": HEAD + "@Component({template: '<b></b>'})\nexport default class {}\n",
        "shorthand.component.ts": HEAD + "const template = '<b></b>';\n@Component({ template })\nexport class Short {}\n",
        "two.component.ts": HEAD + "@Component({template: '<i></i>'})\nexport class One {}\n\n@Component(meta)\nexport class Two {}\n",
        "type-only.ts": HEAD + "export const kept = Component;\n",
    }
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        context = premap.Context(manifest, store)
        plan = premap.angular._plan(context)
        chosen = {rel for rel in context.inventory.files if rel.endswith(".ts") and _imports_the_decorator(context, rel)}
    read = {member["file"]: member["class"] for items in plan["jobs"].values() for _, members in items for member in members}
    gaps = {}
    for gap in plan["gaps"]:
        gaps.setdefault(gap["path"], []).append(gap["detail"])
    assert read == {"ok.component.ts": "Plain", "alias.component.ts": "Aliased", "default.component.ts": "Defaulted",
                    "abstract.component.ts": "Abstracted", "two.component.ts": "One"}
    assert chosen == set(files) - {"package.json"}
    assert chosen == set(read) | set(gaps) | {"type-only.ts"}  # no file the import chose is lost without a word
    assert [d for d in gaps["meta.component.ts"] if "meta.component.ts:4" in d and "no object written in place" in d]
    assert [d for d in gaps["anonymous.component.ts"] if "anonymous.component.ts:2" in d and "has no name" in d]
    assert [d for d in gaps["shorthand.component.ts"] if "Short" in d and "no text" in d]
    assert [d for d in gaps["two.component.ts"] if "two.component.ts:5" in d]  # the second decorator of the file, by its line


def test_each_folder_has_a_command_that_parses_and_one_that_asks_the_type_checker_under_a_time_limit_with_the_same_list(tmp_path):
    files = project_files()
    _, _, asked = commands_of(tmp_path, files)
    [parse], [types] = parsing(asked), typing(asked)
    assert asked == [parse, types]
    assert parse["argv"] == ["daodan-angular", f"{preparation.IN}/angular-jobs-0.json"]
    assert types["argv"] == ["timeout", "--kill-after=10", str(premap.angular.types_seconds(1)), "daodan-angular", "--types",
                             f"{preparation.IN}/angular-jobs-0.json"]
    assert (types["cwd"], types["network"], types["inputs"]) == (parse["cwd"], "none", parse["inputs"])
    # the components a template belongs to ride with it: file, class and line, relative to the folder the commands run in
    members = {(job["f"], tuple(job.get("r", ()))): job["c"] for job in listed(parse)}
    assert members[("src/app/app.component.html", ())] == [["src/app/app.component.ts", "AppComponent", 13]]
    assert members[("src/app/legacy.component.html", ())] == [["src/app/legacy.component.ts", "LegacyComponent", 8]]
    assert all(job["c"] for job in listed(parse))


def test_the_source_and_its_script_are_part_of_the_key_of_the_cached_links():
    import flows
    from pathlib import Path as Reader
    seen = []
    with patch.object(Reader, "read_bytes", autospec=True, side_effect=lambda self: seen.append(self.name) or b""):
        flows._links_reader_digest.__wrapped__()
    assert "angular.py" in seen and "angular_templates.mjs" in seen


def test_where_the_type_checker_gave_nothing_the_calls_on_another_object_are_gaps_that_name_the_package_the_file_or_the_time(tmp_path):
    """The recorded answers of the script (`modal_probe.py --mode source`) in a project without `@angular/compiler-cli`, without
    its `tsconfig.json`, and with the type-checker given 0.05 seconds (`timeout` ends it: exit 124). The rows of the methods
    of the component and the parse itself are as they were; only what the type-checker tells is a gap."""
    html = "src/app/app.component.html"
    for name, cause in (("no-compiler-cli.json", "@angular/compiler-cli is not installed"), ("no-tsconfig.json", "tsconfig.json is not in"),
                        ("timeout.json", f"did not end in {premap.angular.types_seconds(1)} seconds")):
        record, gaps, manifest = read(tmp_path / name, recorded(name))
        record = bound(record, manifest)
        rows = {r["site"]: r for r in record["framework_entries"]}
        assert rows[f"{html}:2"]["symbol"] == f"{APP}::AppComponent.save"  # the method of the component: no tool needed
        assert cause in rows[f"{html}:4"]["gap"] and "svc.cancel" in rows[f"{html}:4"]["gap"], name  # `svc.cancel()`, now a gap with the cause
        assert cause in rows[f"{html}:9"]["gap"]
        [stated] = [g for g in gaps if "not resolved" in g["detail"]]
        assert stated["kind"] == "model_partial" and stated["path"] == "." and cause in stated["detail"], name
        assert not [g for g in gaps if g["kind"] == "model_failed"]  # the parse itself is read


def test_a_folder_with_no_call_on_another_object_asks_the_type_checker_for_nothing_and_has_no_gap_for_it(tmp_path):
    answers = [{"root": "/work", "returncode": 0, "stderr": "", "stdout": json.dumps({"compiler": "22.3.0", "templates": []})},
               {"root": "/work", "returncode": 0, "stderr": "", "stdout": json.dumps({"compiler_cli": "22.3.0", "seconds": 0, "resolved": [],
                                                                                       "note": "no call is made on another object"})}]
    _, gaps, _ = read(tmp_path, answers)
    assert not [g for g in gaps if "not resolved" in g["detail"]]


def test_the_type_checker_time_is_shared_between_the_folders_and_every_parse_command_comes_before_the_first_of_it(tmp_path):
    """A run lasts 1800 seconds, the restore of the packages in it: one slow folder must not take the rows of the others."""
    component = ("import { Component } from '@angular/core';\n@Component({selector: 'a', template: '<b (click)=\"go()\"></b>'})\n"
                 "export class A { go() {} }\n")
    angular = '{"dependencies": {"@angular/core": "22.3.0"}}\n'
    files = {f"apps/{name}/{rel}": text for name in "abc" for rel, text in (("package.json", angular), ("a.component.ts", component))}
    _, _, asked = commands_of(tmp_path, files)
    assert [c["argv"][0] == "daodan-angular" for c in asked] == [True] * 3 + [False] * 3  # the parses, then the type-checker's
    seconds = {int(c["argv"][2]) for c in typing(asked)}
    assert seconds == {premap.angular.types_seconds(3)} and 3 * min(seconds) <= premap.angular.TYPES_TOTAL < 1800
    assert premap.angular.types_seconds(1) == premap.angular.TYPES_TOTAL and premap.angular.types_seconds(1000) >= 10


def test_a_type_checker_killed_may_have_run_out_of_memory_and_the_gap_says_both(tmp_path):
    parsed, types = recorded("fixture.json")
    record, gaps, _ = read(tmp_path, [parsed, {**types, "returncode": 137, "stdout": ""}])
    [stated] = [g for g in gaps if "not resolved" in g["detail"]]
    assert "exit 137" in stated["detail"] and f"did not end in {premap.angular.types_seconds(1)} seconds" in stated["detail"]
    assert f"ran out of memory ({premap.angular.MEMORY_GB} GB)" in stated["detail"]
    assert container_runner.TOOLS["angular"]["memory"] == premap.angular.MEMORY_GB  # what the message says is what the container has


def test_an_answer_of_the_type_checker_that_lacks_a_call_says_so_and_not_none(tmp_path):
    parsed, types = recorded("fixture.json")
    empty = json.dumps({"compiler_cli": "22.3.0", "seconds": 0, "resolved": []})
    record, gaps, manifest = read(tmp_path, [parsed, {**types, "stdout": empty}])
    record = bound(record, manifest)
    gap = {r["site"]: r["gap"] for r in record["framework_entries"] if r.get("gap")}
    assert "the type-checker's answer lacks this call" in gap["src/app/app.component.html:4"] and "None" not in gap["src/app/app.component.html:4"]


def test_a_declaration_the_type_checker_names_is_the_method_whose_lines_hold_its_line_not_another_of_the_same_name(tmp_path):
    """Two classes of one file have a `cancel`: the answer names the line of one, and the row is on that one's method."""
    service = ("import { Injectable } from '@angular/core';\n\n@Injectable()\nexport class First {\n  cancel() {}\n}\n\n"
               "@Injectable()\nexport class Second {\n  cancel() {}\n}\n")
    parsed, types = recorded("fixture.json")
    for line, expected in ((5, "First"), (10, "Second")):
        answer = json.loads(types["stdout"])
        [item] = [r for r in answer["resolved"] if r["line"] == 4 and r["c"][1] == "AppComponent"]
        item["decl"] = {"f": "src/app/order.service.ts", "l": line, "n": "cancel"}
        record, _, manifest = read(tmp_path / expected, [parsed, {**types, "stdout": json.dumps(answer)}], project_files(**{"src/app/order.service.ts": service}))
        record = bound(record, manifest)
        row = next(r for r in record["framework_entries"] if r["site"] == "src/app/app.component.html:4")
        assert row["symbol"] == f"src/app/order.service.ts::{expected}.cancel" and "gap" not in row


def test_a_label_gap_the_tree_reader_read_stays_with_the_compilers_row(tmp_path, monkeypatch):
    import entries
    tree = [{"reader": "attributo", "shape": "(click)", "site": "a.html:1", "column": 3, "symbol": "a.html::<module>", "label_gap": "the key stays"}]
    row = {"reader": "attributo", "shape": "(click)", "site": "a.html:1", "column": 3, "symbol": "a.ts::A.go", "event": "click"}
    monkeypatch.setattr(premap.angular, "recorded", lambda manifest: [row])
    monkeypatch.setattr(premap.angular, "bind", lambda rows, store: rows)  # the row is bound already: the merge is what is checked
    _, manifest = manifest_of(tmp_path, project_files())
    assert entries.compiled(tree, manifest) == [{**row, "label_gap": "the key stays"}]


def test_the_names_the_source_looks_for_are_data_not_code(tmp_path, monkeypatch):
    """The module, the decorator and the properties a framework's component is written with are the data of `components` in
    `entry-queries.json`: another set of names reads another framework's decorator, with no change of code."""
    import entries
    from snapshot_store import open_snapshot
    data = dict(entries.QUERIES["components"]["typescript"])
    assert {data["module"], data["decorator"], data["template"], data["url"]} == {"@angular/core", "Component", "template", "templateUrl"}
    monkeypatch.setitem(entries.QUERIES["components"], "typescript", {**data, "module": "@widgets/core", "decorator": "Widget",
                                                                       "template": "view", "url": "viewUrl"})
    files = {"package.json": '{"dependencies": {"@angular/core": "22.3.0"}}\n',
             "w.ts": "import { Widget } from '@widgets/core';\n@Widget({view: '<b (click)=\"go()\"></b>'})\nexport class W { go() {} }\n",
             "c.ts": "import { Component } from '@angular/core';\n@Component({template: '<i></i>'})\nexport class C {}\n"}
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        plan = premap.angular._plan(premap.Context(manifest, store))
    assert {m["class"] for items in plan["jobs"].values() for _, members in items for m in members} == {"W"}


def test_the_activation_edge_of_an_event_starts_from_the_class_of_the_component_and_ends_on_its_handler(tmp_path):
    import flows
    _, _, manifest = read(tmp_path)
    edges = {(e["site"], e["to"]): e for e in flows.cached_links(manifest, [])["edges"] if e["type"] == "attiva"}
    html = "src/app/app.component.html"
    assert edges[f"{html}:2", f"{APP}::AppComponent.save"]["from"] == f"{APP}::AppComponent"
    assert edges[f"{html}:4", "src/app/order.service.ts::OrderService.cancel"]["from"] == f"{APP}::AppComponent"  # a method of another class
    assert edges["src/app/accents.component.ts:6", "src/app/accents.component.ts::AccentsComponent.brew"]["from"] == "src/app/accents.component.ts::AccentsComponent"


def test_the_recorded_answers_carry_the_print_of_the_script_that_made_them():
    """If the script changes the answers are recorded again (`modal_probe.py --mode source` writes the print)."""
    script = Path(container_runner.__file__).with_name("angular_templates.mjs").read_bytes().replace(b"\r\n", b"\n")
    recorded_print = json.loads((RECORDED / "script.json").read_text(encoding="utf-8"))
    assert recorded_print == {"angular_templates.mjs": hashlib.sha256(script).hexdigest()}


def line_of(files, file: str, needle: str) -> int:
    return next(number for number, line in enumerate(files[file].replace("\r\n", "\n").split("\n"), 1) if needle in line)


def test_a_call_with_no_object_before_it_is_a_method_of_the_class_unless_the_template_declares_the_name(tmp_path):
    """The compiler's own binder (`R3TargetBinder`) says which names a template declares: `let-c` of an `ng-template`, an `@let`,
    the variable of an `@for` (here named like methods of the class). Such a call is not a method of the component, and is no row on
    one: a gap at the event. `real()` and `this.save()` stay on the class."""
    files = project_files()
    record, _, manifest = read(tmp_path)
    record = bound(record, manifest)
    scoped = "src/app/scoped.component.ts"
    rows = {}
    for row in record["framework_entries"]:
        rows.setdefault(row["site"], []).append(row)
    at = lambda needle: rows[f"{scoped}:{line_of(files, scoped, needle)}"]
    [variable], [let], [loop] = at("(click)=\"c('x')\""), at("(click)=\"save()\""), at("(click)=\"go()\"")
    for row, name, kind in ((variable, "c", "variable"), (let, "save", "@let"), (loop, "go", "variable")):
        assert f"{name} is a template {kind}" in row["gap"] and "not a method of ScopedComponent" in row["gap"], row
        assert row["symbol"] == f"{scoped}::ScopedComponent"  # the gap is the component's: no method of the class is claimed
    assert [r["symbol"] for r in at("(click)=\"real()\"")] == [f"{scoped}::ScopedComponent.real"]
    assert [r["symbol"] for r in at("(click)=\"this.save()\"")] == [f"{scoped}::ScopedComponent.save"]  # `this.` is the class, whatever the template declares


def test_a_callee_that_is_no_name_is_a_gap_at_the_event_and_the_call_inside_it_is_still_read(tmp_path):
    files = project_files()
    record, _, manifest = read(tmp_path)
    record = bound(record, manifest)
    callee = "src/app/callee.component.ts"
    rows = {}
    for row in record["framework_entries"]:
        rows.setdefault(row["site"], []).append(row)
    [keyed] = rows[f"{callee}:{line_of(files, callee, '(click)="handlers[0]()"')}"]
    assert "handlers[0]()" in keyed["gap"] and "no name (KeyedRead)" in keyed["gap"]
    factory = rows[f"{callee}:{line_of(files, callee, '(click)="factory()()"')}"]
    assert sorted((r["symbol"], bool(r.get("gap"))) for r in factory) == [
        (f"{callee}::CalleeComponent", True), (f"{callee}::CalleeComponent.factory", False)]
    assert "no name (Call)" in next(r["gap"] for r in factory if r.get("gap"))


def test_a_call_the_script_says_it_could_not_read_is_a_gap_whatever_the_reason(tmp_path):
    """Angular up to 12 writes a call as `MethodCall`: the script cannot read it, says so, and the source never keeps silent."""
    parsed, types = recorded("fixture.json")
    printed = json.loads(parsed["stdout"])
    legacy = next(t for t in printed["templates"] if t["f"] == "src/app/legacy.component.html")
    legacy["events"][0]["calls"] = []
    legacy["events"][0]["unread"] = ["this version of Angular writes a call as MethodCall: it is not read"]
    record, _, manifest = read(tmp_path, [{**parsed, "stdout": json.dumps(printed)}, types])
    record = bound(record, manifest)
    [row] = [r for r in record["framework_entries"] if r["site"] == "src/app/legacy.component.html:1"]
    assert "MethodCall" in row["gap"] and "legacySave()" in row["gap"] and row["symbol"] == "src/app/legacy.component.ts::LegacyComponent"


def test_a_solution_style_tsconfig_is_asked_through_the_project_it_references(tmp_path):
    """`tsconfig.json` with `files: []` and `references`: no root file of its own. The recorded answers (Modal) are the fixture's
    in a copy with such a `tsconfig.json` and the real one as `tsconfig.app.json`."""
    record, gaps, manifest = read(tmp_path, recorded("solution.json"))
    record = bound(record, manifest)
    row = next(r for r in record["framework_entries"] if r["site"] == "src/app/app.component.html:4")
    assert row["symbol"] == "src/app/order.service.ts::OrderService.cancel" and "gap" not in row
    assert not [g for g in gaps if "not resolved" in g["detail"]]
    assert not [r for r in record["framework_entries"] if "(0 root files)" in (r.get("gap") or "")]


def test_the_script_gives_in_angular_20_the_events_and_the_rows_it_gives_in_22(tmp_path):
    """The recorded answers of the same commands in an image of Angular 20 (20.3.35, TypeScript 5.9.3; `modal_probe.py`): the same
    events with the same calls, and the same rows. What is not shown here: a version before 20, where `getTsSymbolOfSymbol` may
    be absent (the script falls back to the symbol's `tsSymbol`), and where `parseTemplate` writes a call as `MethodCall` (12)."""
    old = recorded("fixture-angular20.json")
    assert json.loads(old[0]["stdout"])["compiler"].startswith("20.") and json.loads(old[1]["stdout"])["compiler_cli"].startswith("20.")
    key = lambda row: (row["site"], row["column"], row["shape"], row["symbol"], bool(row.get("gap")))
    rows = lambda *args: (lambda record, _, manifest: bound(record, manifest)["framework_entries"])(*read(*args))
    assert sorted(map(key, rows(tmp_path / "20", old))) == sorted(map(key, rows(tmp_path / "22")))
