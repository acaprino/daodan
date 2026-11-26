"""The pre-map's `starts` and `builds` facets for a Node package: the commands it declares, read from the syntax
tree of each script (tree-sitter bash), never run (spec of the project's interfaces, section 5).

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_premap_npm_start.py
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import premap  # noqa: E402
from premap import npm_start  # noqa: E402
import snapshot  # noqa: E402

READERS = tuple(source for source in premap.SOURCES if not hasattr(source, "commands"))
FIXTURES = Path(__file__).resolve().parents[1] / "benchmarks/project-model/fixtures"


def premapped(tmp_path, files: dict) -> dict:
    project = tmp_path / "proj"
    for rel, text in files.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    record = premap.write(manifest, sources=READERS)
    assert not [gap for gap in record["gaps"] if gap["kind"] == "source_failed"]
    return record


def plain(entries: list[dict]) -> list[dict]:
    return [{key: value for key, value in entry.items() if key != "sources"} for entry in entries]


def package(**scripts: str) -> str:
    return json.dumps({"name": "p", "scripts": scripts})


def starts(tmp_path, files: dict) -> list[dict]:
    return plain(premapped(tmp_path, files).get("starts", []))


def test_the_reader_is_a_source_of_the_pre_map():
    assert npm_start in premap.SOURCES and npm_start.RANK == "reader"
    assert premap.IDENTITY["starts"] == premap.IDENTITY["builds"] == (("root", "declared_in"),)


def test_a_vite_app_declares_its_dev_server_and_its_build(tmp_path):
    files = {"package.json": (FIXTURES / "js-vite-react-ts/package.json").read_text(encoding="utf-8")}
    record = premapped(tmp_path, files)
    assert plain(record["starts"]) == [
        {"root": ".", "mode": "dev", "runner": "npm", "declared_in": "package.json#scripts.dev", "port": None,
         "needs_build": False}]
    assert plain(record["builds"]) == [{"root": ".", "runner": "npm", "declared_in": "package.json#scripts.build"}]


def test_a_production_server_of_the_closed_table_needs_the_build(tmp_path):
    files = {"package.json": (FIXTURES / "js-nextjs/package.json").read_text(encoding="utf-8")}
    found = {entry["mode"]: entry["needs_build"] for entry in starts(tmp_path, files)}
    assert found == {"dev": False, "start": True}
    record = premapped(tmp_path / "again", {"package.json": package(start="node server.js", preview="vite preview"),
                                            "server.js": ""})
    assert plain(record["starts"]) == [
        {"root": ".", "mode": "start", "runner": "npm", "declared_in": "package.json#scripts.start", "port": None,
         "needs_build": False}]


def test_a_start_that_runs_a_file_the_snapshot_does_not_hold_needs_the_build(tmp_path):
    """A built file is no part of the checkout (`dist/` is ignored): a start that points at one needs `build` first."""
    found = starts(tmp_path, {
        "a/package.json": package(start="node dist/server.js", dev="vite", build="tsc"),
        "b/package.json": package(start="node ./lib/server.js"), "b/lib/server.js": "// held",
        "c/package.json": package(start="node $ENTRY"),
        "d/package.json": package(start="node --enable-source-maps lib/main.js", build="tsc")})
    assert {(entry["root"], entry["mode"]): entry["needs_build"] for entry in found} == {
        ("a", "start"): True, ("a", "dev"): False, ("b", "start"): False, ("c", "start"): False,
        ("d", "start"): True}


def test_a_start_that_needs_a_build_the_package_does_not_declare_is_a_gap(tmp_path):
    record = premapped(tmp_path, {"package.json": package(start="next start")})
    assert [gap["kind"] for gap in record["gaps"]] == ["build_command_missing"]
    assert record["gaps"][0]["path"] == "package.json"
    assert "builds" not in record


def test_the_port_comes_only_from_a_literal(tmp_path):
    found = starts(tmp_path, {
        "a/package.json": package(dev="next dev -p 3001"),
        "b/package.json": package(dev="vite --port 4000"),
        "c/package.json": package(dev="vite --port=4100"),
        "d/package.json": package(start="PORT=3002 node server.js"),
        "e/package.json": package(dev="vite --port $PORT"),
        "f/package.json": package(dev="PORT=$PORT node server.js"),
        "g/package.json": package(dev="vite --port abc")})
    assert {entry["root"]: entry["port"] for entry in found} == {
        "a": 3001, "b": 4000, "c": 4100, "d": 3002, "e": None, "f": None, "g": None}


def test_the_script_is_read_from_the_syntax_not_from_its_words(tmp_path):
    """A quoted word or a comment is not a command: it does not make a production server of `node`."""
    found = starts(tmp_path, {
        "q/package.json": package(start="node server.js 'next start'"), "q/server.js": "",
        "c/package.json": package(start="node server.js # next start"), "c/server.js": ""})
    assert [(entry["root"], entry["needs_build"]) for entry in found] == [("c", False), ("q", False)]


def test_a_script_that_only_tests_checks_or_names_no_subcommand_is_not_a_start(tmp_path):
    record = premapped(tmp_path, {
        "t/package.json": package(dev="vitest"),
        "w/package.json": package(dev="tsc --watch"),
        "b/package.json": package(dev="tauri"),
        "ok/package.json": package(dev="tauri dev"),
        "mix/package.json": package(dev="tsc -b && vite")})
    assert [entry["root"] for entry in plain(record["starts"])] == ["mix", "ok"]
    assert sorted(gap["path"] for gap in record["gaps"] if gap["kind"] == "no_start_command") == [
        "b/package.json", "t/package.json", "w/package.json"]


def test_the_executor_is_the_one_of_the_lockfile_of_the_folder_or_above(tmp_path):
    found = starts(tmp_path, {
        "package.json": package(dev="vite"), "pnpm-lock.yaml": "",
        "web/package.json": package(dev="vite"), "web/yarn.lock": "",
        "app/package.json": package(dev="vite"), "app/bun.lockb": "",
        "plain/package.json": package(dev="vite"), "plain/package-lock.json": "{}"})
    assert {entry["root"]: entry["runner"] for entry in found} == {
        ".": "pnpm", "web": "yarn", "app": "bun", "plain": "npm"}


def test_a_package_without_scripts_or_with_none_of_them_states_nothing(tmp_path):
    record = premapped(tmp_path, {"package.json": json.dumps({"name": "p"}), "lib/package.json": package(lint="eslint .")})
    assert "starts" not in record and "builds" not in record
    assert not [gap for gap in record["gaps"] if gap["kind"] in ("no_start_command", "build_command_missing")]
