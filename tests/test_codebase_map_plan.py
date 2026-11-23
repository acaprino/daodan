"""The plan (spec 8.4, 8.10 proofs 3 and 4, 8.11 step 4): the choice of adapters in one function, executed by the steps.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_plan.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import dynamic  # noqa: E402
import engine_pass  # noqa: E402
import pipeline  # noqa: E402
import resolve_edges  # noqa: E402
import snapshot  # noqa: E402
from dynamic import go as dynamic_go, python as dynamic_python  # noqa: E402
from languages import _treesitter  # noqa: E402
from pipeline import events  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GRAPHS = sorted(path for base in ("code-graph", "css-graph") for path in (FIXTURES / base).iterdir() if path.is_dir())
GO = "package billing\n\nfunc Pay(amount int) int {\n\treturn amount\n}\n"
PY = "def pay(amount):\n    return amount\n"


def _planning():
    from pipeline import plan
    return plan


def _project(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True)
    for rel, text in files.items():
        (root / rel).write_text(text, encoding="utf-8", newline="")
    return root


def _without(*ids: str):
    """`pipeline.plan.plan` as it is, minus the nodes `ids`: a plan that leaves an adapter out."""
    real = _planning().plan

    def plan(rows, record=None):
        planned = real(rows, record)
        return {**planned, "nodes": [node for node in planned["nodes"] if node["id"] not in ids]}
    return plan


# ---------------------------------------------------------------------------------------------------------------
# The function


def test_the_plan_names_each_adapter_on_what_it_runs_on_and_what_it_needs():
    planning = _planning()
    rows = [("a.py", {"language": "python"}), ("b.py", {"language": "python"}), ("c.go", {"language": "go"}),
            ("README", {"language": None}), ("q.sql", {"language": "sql"})]
    planned = planning.plan(rows)
    nodes = {node["id"]: node for node in planned["nodes"]}
    assert {"parse:python", "parse:go", "parse:file-level", "parse:sql", "resolve:scip-python", "resolve:scip-go",
            "observe:dynamic-record-python", "observe:dynamic-record-go"} == set(nodes)
    assert nodes["parse:python"]["on"] == {"languages": ["python"], "files": 2} and not nodes["parse:python"]["needs"]
    assert nodes["parse:file-level"]["on"] == {"languages": [], "files": 1}
    resolve = nodes["resolve:scip-go"]
    assert (resolve["step"], resolve["adapter"], resolve["container"], resolve["needs"]) == (
        "resolve", "scip-go", True, ["parse:go"])
    assert resolve["on"] == {"languages": ["go"], "files": 1, "unit_kinds": ["go-module"]} and resolve["version"]
    observe = nodes["observe:dynamic-record-go"]
    assert (observe["needs"], observe["on"]["languages"], observe["container"]) == (["resolve:scip-go"], ["go"], True)
    assert "version" not in nodes["parse:go"]  # only an adapter that declares one has it
    assert [planning.node_of(row) for _path, row in rows] == [
        "parse:python", "parse:python", "parse:go", "parse:file-level", "parse:sql"]
    assert {(gap["kind"], gap["language"], gap["files"]) for gap in planned["gaps"]} == {("no-analyzer", "sql", 1)}


def test_a_language_with_an_analyzer_and_no_observer_is_a_gap_and_a_resolver_is_the_first_to_list_it():
    planning = _planning()
    planned = planning.plan([("a.rs", {"language": "rust"}), ("b.c", {"language": "c"}), ("b.h", {"language": "c"})])
    gaps = {(gap["kind"], gap["language"]): gap for gap in planned["gaps"]}
    assert ("no-observer", "rust") not in gaps and ("no-observer", "c") not in gaps  # both have an observer
    planned = planning.plan([("a.css", {"language": "css"}), ("a.rb", {"language": "ruby"})])
    assert [(gap["kind"], gap["language"]) for gap in planned["gaps"] if gap["kind"] == "no-observer"] == [
        ("no-observer", "stylesheet")]
    assert "resolve:stylesheet" in {node["id"] for node in planned["nodes"]}  # a graph of other languages' files
    nodes = [node for node in planned["nodes"] if node["step"] == "resolve"]
    languages = [language for node in nodes for language in node["on"]["languages"]]
    assert len(languages) == len(set(languages))  # a language has one resolver


def test_a_node_whose_need_failed_is_blocked_per_language_and_says_which_need():
    planning = _planning()
    planned = planning.plan([("a.c", {"language": "c"}), ("a.cpp", {"language": "cpp"})])
    clang = next(node for node in planned["nodes"] if node["id"] == "resolve:scip-clang")
    assert planning.blocked(clang, {}) == {}
    assert planning.blocked(clang, {"parse:c": "no c file was parsed"}) == {"c": ("parse:c", "no c file was parsed")}
    watcher = next(node for node in planned["nodes"] if node["step"] == "observe" and "cpp" in node["on"]["languages"])
    failed = {"resolve:scip-clang": {"cpp": "no graph of cpp"}}
    assert planning.blocked(watcher, failed) == {"cpp": ("resolve:scip-clang", "no graph of cpp")}


# ---------------------------------------------------------------------------------------------------------------
# Proof 3: the plan covers everything, and nothing runs outside it


@pytest.mark.parametrize("fixture", GRAPHS, ids=lambda path: f"{path.parent.name}/{path.name}")
def test_every_file_of_the_inventory_is_in_a_parse_node(tmp_path, fixture):
    planning = _planning()
    root, manifest = tmp_path / "project", tmp_path / "out" / "manifest.sqlite"
    shutil.copytree(fixture, root)
    snapshot.write_snapshot(root, manifest)
    with open_snapshot(manifest) as store:
        rows = list(store.iter_inventory())
        entries = {path: entry for path, entry in store.iter_files(semantic=False)}
    planned = planning.plan(rows)
    parse = {node["id"]: node for node in planned["nodes"] if node["step"] == "parse"}
    assert rows and sum(node["on"]["files"] for node in parse.values()) == len(rows)
    assert {path for path, _row in rows} == set(entries)
    assert all(planning.node_of(row) in parse for _path, row in rows)
    assert all(planning.node_of(entry) in parse for entry in entries.values())  # the snapshot's own entries


def test_no_parser_runs_outside_the_plan(tmp_path):
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    parsed = []
    real = snapshot.get_adapter
    with mock.patch.object(_planning(), "plan", _without("parse:go")), \
            mock.patch.object(snapshot, "get_adapter", side_effect=lambda name: parsed.append(name) or real(name)):
        snapshot.write_snapshot(root, tmp_path / "out" / "manifest.sqlite")
    assert "python" in parsed and "go" not in parsed  # the spy sees the adapter that is in the plan


def test_no_resolver_runs_outside_the_plan(tmp_path):
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    manifest, launched = tmp_path / "out" / "manifest.sqlite", []
    snapshot.write_snapshot(root, manifest)

    def launch(spec, wanted, path):
        launched.append(spec.name)
        return None, None, None, {"available": True, "engine": spec.name,
                                  "languages": {language: {"state": "fresh"} for language in wanted}}

    with mock.patch.object(_planning(), "plan", _without("resolve:scip-go")), \
            mock.patch.object(engine_pass, "_launch", side_effect=launch), \
            mock.patch.object(engine_pass, "free_memory", return_value=64 * 2**30):
        report = engine_pass.run_pass(manifest, tmp_path / "out" / "report.json")
    assert launched == ["scip-python"] and "go" not in report["languages"]


@pytest.mark.parametrize("dropped, seen", [("observe:dynamic-record-go", "python"),
                                           ("observe:dynamic-record-python", "go")])
def test_no_observer_runs_outside_the_plan(tmp_path, dropped, seen):
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    manifest, asked = tmp_path / "out" / "manifest.sqlite", []
    snapshot.write_snapshot(root, manifest)
    graphs = {"manifest_digest": "d", "parser_fingerprint": "p", "resolver_version": 1,
              "languages": {language: {"state": "fresh", "engine": "x", "coverage": {}}
                            for language in ("go", "python")}}
    with mock.patch.object(_planning(), "plan", _without(dropped)), \
            mock.patch.object(resolve_edges, "read_edge_store", return_value=([], graphs, None)), \
            mock.patch.object(dynamic_go, "plan", side_effect=lambda *a: asked.append("go") or {"runs": [], "gaps": []}), \
            mock.patch.object(dynamic_python, "plan",
                              side_effect=lambda *a: asked.append("python") or {"runs": [], "gaps": []}):
        dynamic.run(manifest, events.Bus())
    assert asked == [seen]


# ---------------------------------------------------------------------------------------------------------------
# Proof 4: a failed need stops only what needs it


@pytest.fixture
def no_go_grammar():
    _treesitter.get_parser.cache_clear()
    with mock.patch.object(_treesitter, "place_grammars", lambda *args: "download failed: no network"), \
            mock.patch.object(_treesitter, "_GRAMMAR_MODULES", {}):
        _treesitter.get_parser.cache_clear()
        yield
    _treesitter.get_parser.cache_clear()


def test_a_parser_that_is_missing_stops_the_resolver_and_the_observer_of_its_language_only(tmp_path, no_go_grammar):
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(root, manifest)
    launched, asked, seen = [], [], []

    def launch(spec, wanted, path):
        launched.append(spec.name)
        return None, None, None, {"available": True, "engine": spec.name,
                                  "languages": {language: {"state": "fresh"} for language in wanted}}

    graphs = {"manifest_digest": "d", "parser_fingerprint": "p", "resolver_version": 1,
              "languages": {"python": {"state": "fresh", "engine": "scip-python", "coverage": {}}}}
    with mock.patch.object(engine_pass, "_launch", side_effect=launch), \
            mock.patch.object(engine_pass, "free_memory", return_value=64 * 2**30), \
            mock.patch.object(resolve_edges, "read_edge_store", return_value=([], graphs, None)), \
            mock.patch.object(dynamic_go, "plan", side_effect=lambda *a: asked.append("go") or {"runs": [], "gaps": []}), \
            mock.patch.object(dynamic_python, "plan",
                              side_effect=lambda *a: asked.append("python") or {"runs": [], "gaps": []}):
        results = pipeline.run(manifest, listeners=[seen.append], start="analyze", stop="dynamic")
    assert launched == ["scip-python"]  # scip-go does not start, with its parser missing
    languages = results["analyze"]["languages"]
    assert languages["go"]["state"] == "unavailable" and languages["go"]["need"] == "parse:go"
    assert "none of the 1 go files was parsed" in languages["go"]["reason"] and languages["python"]["state"] == "fresh"
    unavailable = [event for event in seen if event["kind"] == "analyzer.unavailable"]
    assert [(event["analyzer"], event["data"]["need"]) for event in unavailable] == [("scip-go", "parse:go")]
    assert asked == ["python"]  # the go observer does not plan its runs
    observed = results["dynamic"]["languages"]
    assert (observed["go"]["state"], observed["go"]["need"]) == ("no-static-graph", "resolve:scip-go")
    assert observed["python"]["state"] == "not-run"


def test_the_languages_no_analyzer_serves_are_the_plans_gaps(tmp_path):
    root = _project(tmp_path / "project", {
        "a.sql": "select 1;\n", "pay.py": PY, "page.html": '<p class="x">x</p>\n',
        "Page.astro": '---\nimport { f } from "./f";\nf();\n---\n<p class="x">x</p>\n<style>\n.x { color: red }\n</style>\n'})
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(root, manifest)
    with open_snapshot(manifest) as store:
        served = engine_pass.no_analyzer(store.connection)
        gaps = engine_pass.snapshot_plan(store.connection)["gaps"]
    assert served and {gap["language"]: gap["files"] for gap in gaps if gap["kind"] == "no-analyzer"} == served
