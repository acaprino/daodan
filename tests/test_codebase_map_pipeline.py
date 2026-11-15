"""The analysis pipeline: its steps in order and the events a listener gets, from the first file to the complete graph.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_pipeline.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))

import pipeline  # noqa: E402
import resolve_edges  # noqa: E402
import snapshot  # noqa: E402
from pipeline import events  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures/code-graph"


def test_an_event_has_its_step_kind_level_and_message_and_goes_to_every_listener_and_the_journal(tmp_path):
    journal = tmp_path / events.JOURNAL
    bus = events.Bus(journal)
    seen = []
    bus.subscribe(seen.append)
    bus.emit("step.started", "scan", step="scan")
    bus.progress("analyze", 1, 3, analyzer="scip-go", phase="index")
    assert [(e["kind"], e["step"], e["level"]) for e in seen] == [("step.started", "scan", "info"),
                                                                  ("progress", "analyze", "info")]
    assert seen[1]["data"] == {"done": 1, "total": 3, "phase": "index"} and seen[1]["analyzer"] == "scip-go"
    written, cursor = events.read(journal)
    assert [e["kind"] for e in written] == ["step.started", "progress"] and cursor == 2
    later, cursor = events.read(journal, after=1)
    assert [e["kind"] for e in later] == ["progress"] and cursor == 2


def test_an_unknown_kind_or_level_is_refused():
    bus = events.Bus()
    with pytest.raises(ValueError):
        bus.emit("whatever", "x", step="scan")
    with pytest.raises(ValueError):
        bus.emit("log", "x", step="scan", level="loud")


def test_a_listener_that_fails_stops_nothing_and_its_error_becomes_an_event(tmp_path):
    bus = events.Bus(tmp_path / events.JOURNAL)
    seen = []

    def broken(event):
        raise RuntimeError("listener down")

    bus.subscribe(broken)
    bus.subscribe(seen.append)
    bus.emit("step.started", "scan", step="scan")
    assert [e["kind"] for e in seen] == ["step.started", "log"]
    assert seen[1]["level"] == "error" and "listener down" in seen[1]["message"]


def test_a_warning_or_an_error_carries_its_cause_and_remedy():
    bus = events.Bus()
    with pytest.raises(ValueError):
        bus.emit("analyzer.unavailable", "no engine", step="analyze", analyzer="scip-java", level="warning")
    event = bus.emit("analyzer.unavailable", "no engine", step="analyze", analyzer="scip-java", level="warning",
                     cause="no container engine answers", remedy="start Kiri")
    assert event["data"] == {"cause": "no container engine answers", "remedy": "start Kiri"}


def test_the_steps_run_in_order_to_the_complete_graph_and_say_what_they_do(tmp_path):
    """Scan, analysis, then the union: each step starts and finishes, each analyzer of a technology the pre-map
    found says it started and finished with progress, and the run ends with the complete graph."""
    import shutil
    from indexers import go
    project = tmp_path / "go"
    shutil.copytree(FIXTURES / "go", project, ignore=shutil.ignore_patterns("index.scip", "expected.json"))
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    indexer = {"name": "scip-go", "version": "v0.2.9", "seconds": 1.0, "peak_mb": None}

    def index(project_dir, work_dir, files=None, **given):
        return {"indexes": [[str(FIXTURES / "go" / "index.scip"), ""]], "runs": [], "indexer": indexer}

    seen = []
    go_spec = next(spec for spec in resolve_edges.ENGINES if spec.name == "scip-go")
    real = resolve_edges.subprocess.run

    def stage(command, **options):  # the analyzer's stage in this process, as its own process runs it
        if command[1:2] != ["--engine"]:
            return real(command, **options)
        resolve_edges.main(command)
        return resolve_edges.subprocess.CompletedProcess(command, 0)

    with mock.patch.object(resolve_edges, "ENGINES", (go_spec,)), \
            mock.patch.object(resolve_edges, "ENGINE_LANGUAGES", {"go": go_spec}), \
            mock.patch.object(resolve_edges, "stage_command", side_effect=lambda spec, manifest, path, environments,
                              offline=False: [str(manifest), "--engine", spec.name, "--report-out", str(path)]), \
            mock.patch.object(resolve_edges, "cached_offline", return_value=False), \
            mock.patch.object(resolve_edges.subprocess, "run", side_effect=stage), \
            mock.patch.object(go, "index", side_effect=index), \
            mock.patch.object(resolve_edges, "free_memory", return_value=64 * 2**30):
        result = pipeline.run(manifest, listeners=[seen.append])
    steps = [(e["kind"], e["step"]) for e in seen if e["kind"].startswith("step.")]
    assert steps == [("step.started", "scan"), ("step.finished", "scan"), ("step.started", "analyze"),
                     ("step.finished", "analyze"), ("step.started", "union"), ("step.finished", "union")]
    analyzers = [(e["kind"], e["analyzer"]) for e in seen if e["kind"].startswith("analyzer.")]
    assert analyzers == [("analyzer.started", "scip-go"), ("analyzer.finished", "scip-go")]
    assert any(e["kind"] == "progress" and e["step"] == "analyze" and e["data"]["total"] == 1 for e in seen)
    assert any(e["kind"] == "progress" and e["step"] == "scan" for e in seen)
    ready = [e for e in seen if e["kind"] == "graph.ready"]
    assert len(ready) == 1 and ready[0]["data"]["languages"]["go"]["state"] == "fresh"
    assert any(e["kind"] == "gap" and e["data"].get("language") == "go" for e in seen)  # no observed edges yet
    assert result["union"]["languages"]["go"]["state"] == "fresh"
    journal, _cursor = events.read(manifest.with_name(events.JOURNAL))
    assert [e["kind"] for e in journal] == [e["kind"] for e in seen]


def test_a_run_can_start_and_stop_at_a_step_and_a_failed_step_stops_the_rest(tmp_path):
    """The snapshot runs the scan and leaves the rest to the analysis in its own process, which goes from the
    analysis to the union; a step that fails stops what comes after it and says why."""
    manifest = tmp_path / "out" / "manifest.sqlite"
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.write_snapshot(tmp_path / "p", manifest)
    seen = []
    result = pipeline.run(manifest, listeners=[seen.append], stop="scan")
    assert list(result) == ["scan"] and [e["step"] for e in seen if e["kind"].startswith("step.")] == ["scan", "scan"]
    with mock.patch.object(pipeline.Analyze, "run", side_effect=pipeline.StepFailed("no store", "write it")):
        result = pipeline.run(manifest, listeners=[seen.append], start="analyze")
    assert result == {"analyze": {"failed": "no store", "remedy": "write it"}}
    assert seen[-1]["kind"] == "step.failed" and seen[-1]["data"]["remedy"] == "write it"


def test_writing_a_snapshot_runs_the_scan_through_the_pipeline_and_the_pass_runs_the_rest():
    """One way in: `snapshot.py write` and a run's refresh run the scan step, the detached pass the analysis
    and the union."""
    import inspect
    assert "pipeline.run(" in inspect.getsource(snapshot.cmd_write)
    assert "premap.ensure" not in inspect.getsource(snapshot.cmd_write)
    assert "pipeline.run(" in inspect.getsource(resolve_edges.main)


def test_the_pipeline_declares_its_steps_in_one_place():
    assert [step.NAME for step in pipeline.STEPS] == ["scan", "analyze", "union"]
    for step in pipeline.STEPS:
        assert step.INPUTS and step.OUTPUTS and callable(step.run)


def test_every_analyzer_declares_itself_and_the_pass_is_built_from_the_declarations():
    """An analyzer is one adapter module under `indexers/`: it says its entry, the languages it indexes, the unit
    kinds it takes its structure from and whether its build runs only in a container. No hand-written list
    names them: a module that declares itself is an analyzer of the pass."""
    import importlib
    import indexers
    declared = indexers.analyzers()
    assert {module.ENTRY for module in declared} == {
        "scip-go", "scip-rust", "scip-typescript", "scip-python", "scip-java", "scip-kotlin", "scip-clang"}
    for module in declared:
        assert module.LANGUAGES and isinstance(module.UNIT_KINDS, frozenset)
        assert isinstance(module.NEEDS_CONTAINER, bool)
        assert callable(module.structure) and callable(module.index) and module.MIN_FREE > 0
        spec = next(spec for spec in resolve_edges.ENGINES if spec.name == module.ENTRY)
        assert (spec.languages, spec.indexer, spec.needs_container) == (
            tuple(module.LANGUAGES), module.__name__.rsplit(".", 1)[-1], module.NEEDS_CONTAINER)
    source = importlib.util.find_spec("resolve_edges").origin
    assert 'EngineSpec("scip-' not in Path(source).read_text(encoding="utf-8")


def test_an_analyzer_takes_the_units_of_the_kinds_it_declares():
    import indexers
    for module in indexers.analyzers():
        if module.ENTRY == "scip-python":
            continue  # its runs are the outermost Python projects (`premap.python_runs`)
        record = {"units": [{"kind": kind, "root": f"u{number}", "name": f"u{number}"}
                            for number, kind in enumerate(sorted(module.UNIT_KINDS))], "workspace": []}
        given = module.structure(record)
        folders = given.get("roots", {unit["root"] for unit in given.get("units", [])})
        assert folders, module.ENTRY

