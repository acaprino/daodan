"""The analysis pipeline: its steps in order and the events a listener gets, from the first file to the complete graph.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_pipeline.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import pipeline  # noqa: E402
import resolve_edges  # noqa: E402
import engine_pass  # noqa: E402
import subprocess  # noqa: E402
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


def test_a_line_still_being_written_is_read_next_time(tmp_path):
    journal = tmp_path / events.JOURNAL
    events.Bus(journal).emit("step.started", "scan", step="scan")
    with journal.open("a", encoding="utf-8") as stream:
        stream.write('{"kind": "prog')  # another process is appending
    written, cursor = events.read(journal)
    assert [e["kind"] for e in written] == ["step.started"] and cursor == 1


def test_a_broken_line_of_the_journal_is_skipped_and_hides_no_event_after_it(tmp_path):
    journal = tmp_path / events.JOURNAL
    bus = events.Bus(journal)
    bus.emit("step.started", "scan", step="scan")
    with journal.open("ab") as stream:
        stream.write(b'{"kind": "prog\n')  # a writer stopped in the middle of its line, and another went on
    bus.emit("step.finished", "scan", step="scan")
    written, cursor = events.read(journal)
    assert [e["kind"] for e in written] == ["step.started", "step.finished"] and cursor == 3
    assert events.read(journal, after=1, limit=1) == ([], 2)  # the broken line counts: the cursor stays a line count
    assert [e["kind"] for e in events.read(journal, after=2)[0]] == ["step.finished"]


def test_a_journal_that_cannot_be_written_stops_nothing_and_is_told_once(tmp_path):
    (tmp_path / "taken").write_text("", encoding="utf-8")  # a file where the journal's folder should be
    bus = events.Bus(tmp_path / "taken" / events.JOURNAL)
    seen = []
    bus.subscribe(seen.append)
    bus.emit("step.started", "scan", step="scan")
    bus.emit("step.finished", "scan", step="scan")
    assert [e["kind"] for e in seen] == ["step.started", "log", "step.finished"]
    assert seen[1]["level"] == "error" and seen[1]["data"]["cause"] and seen[1]["data"]["remedy"]


def test_what_an_ended_analysis_left_open_is_closed_with_the_cause_and_only_once(tmp_path):
    journal = tmp_path / events.JOURNAL
    bus = events.Bus(journal)
    bus.emit("step.started", "scan", step="scan")
    bus.emit("step.finished", "scan", step="scan")
    bus.emit("step.started", "analyze", step="analyze")
    bus.emit("analyzer.started", "scip-go for go", step="analyze", analyzer="scip-go")
    bus.emit("analyzer.finished", "scip-go: go", step="analyze", analyzer="scip-go")
    bus.emit("analyzer.started", "scip-rust for rust", step="analyze", analyzer="scip-rust")
    assert events.close_open(journal, "its process is gone", "analyze again") == ["scip-rust", "analyze"]
    closed = events.read(journal, after=6)[0]
    assert [(e["kind"], e["step"], e["analyzer"], e["level"]) for e in closed] == [
        ("analyzer.finished", "analyze", "scip-rust", "error"), ("step.failed", "analyze", None, "error")]
    assert all(e["data"] == {"cause": "its process is gone", "remedy": "analyze again"} for e in closed)
    assert events.close_open(journal, "its process is gone", "analyze again") == []
    assert events.close_open(tmp_path / "none.jsonl", "no journal", "nothing to close") == []


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
    """Scan, analysis, the dynamic step, then the union: each step starts and finishes, each analyzer of a
    technology the pre-map found says it started and finished with progress, and the run ends with the complete
    graph. No test of the fixture runs (the suites start no container): the union says its graph is static only."""
    import shutil
    from indexers import go
    project = tmp_path / "go"
    shutil.copytree(FIXTURES / "go", project, ignore=shutil.ignore_patterns("index.scip", "expected.json"))
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    indexer = {"name": "scip-go", "version": "v0.2.9", "seconds": 1.0, "peak_mb": None}

    def index(project_dir, work_dir, files=None, **given):
        return {"indexes": [[str(FIXTURES / "go" / "index.scip"), ""]], "runs": [], "indexer": indexer}

    seen = []
    go_spec = next(spec for spec in resolve_edges.ENGINES if spec.name == "scip-go")
    real = subprocess.run

    def stage(command, **options):  # the analyzer's stage in this process, as its own process runs it
        if command[1:2] != ["--engine"]:
            return real(command, **options)
        with mock.patch("container.find_engine", return_value="the engine"):  # its build runs in a container
            resolve_edges.main(command)
        return subprocess.CompletedProcess(command, 0)

    with mock.patch.object(engine_pass, "ENGINES", (go_spec,)), \
            mock.patch.object(engine_pass, "ENGINE_LANGUAGES", {"go": go_spec}), \
            mock.patch.object(engine_pass, "stage_command", side_effect=lambda spec, manifest, path,
                              offline=False: [str(manifest), "--engine", spec.name, "--report-out", str(path)]), \
            mock.patch.object(engine_pass, "cached_offline", return_value=False), \
            mock.patch.object(subprocess, "run", side_effect=stage), \
            mock.patch.object(go, "index", side_effect=index), \
            mock.patch.object(engine_pass, "free_memory", return_value=64 * 2**30):
        result = pipeline.run(manifest, listeners=[seen.append])
    steps = [(e["kind"], e["step"]) for e in seen if e["kind"].startswith("step.")]
    assert steps == [("step.started", "stack"), ("step.finished", "stack"), ("step.started", "scan"),
                     ("step.finished", "scan"), ("step.started", "parse"), ("step.finished", "parse"),
                     ("step.started", "analyze"),
                     ("step.finished", "analyze"), ("step.started", "dynamic"), ("step.finished", "dynamic"),
                     ("step.started", "union"), ("step.finished", "union")]
    analyzers = [(e["kind"], e["analyzer"]) for e in seen if e["kind"].startswith("analyzer.")
                 and e["step"] == "analyze"]
    assert analyzers == [("analyzer.started", "scip-go"), ("analyzer.finished", "scip-go")]
    assert any(e["kind"] == "progress" and e["step"] == "analyze" and e["data"]["total"] == 1 for e in seen)
    assert any(e["kind"] == "progress" and e["step"] == "scan" for e in seen)
    ready = [e for e in seen if e["kind"] == "graph.ready"]
    assert len(ready) == 1 and ready[0]["data"]["languages"]["go"]["state"] == "fresh"
    unobserved = [e["data"]["gap"] for e in seen if e["kind"] == "gap" and e["step"] == "union"
                  and e["data"].get("language") == "go"]
    assert [gap["kind"] for gap in unobserved] == ["not-observed"]  # with the cause the dynamic step gave
    assert unobserved[0]["detail"] != "no edge observed in a run: the dynamic step has not observed this language"
    assert result["union"]["languages"]["go"]["state"] == "fresh"
    journal, _cursor = events.read(manifest.with_name(events.JOURNAL))
    assert [e["kind"] for e in journal] == [e["kind"] for e in seen]


def test_a_run_can_start_and_stop_at_a_step_and_a_failed_step_stops_the_rest(tmp_path):
    """The snapshot runs the scan and leaves the rest to the analysis in its own process, which goes from the
    analysis to the union; a step that fails stops what comes after it and says why."""
    manifest = tmp_path / "out" / "manifest.sqlite"
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.read_project(tmp_path / "p", manifest)
    seen = []
    result = pipeline.run(manifest, listeners=[seen.append], stop="scan")
    assert list(result) == ["stack", "scan"]
    assert [e["step"] for e in seen if e["kind"].startswith("step.")] == ["stack", "stack", "scan", "scan"]
    with mock.patch.object(pipeline.Analyze, "run", side_effect=pipeline.StepFailed("no store", "write it")):
        result = pipeline.run(manifest, listeners=[seen.append], start="analyze")
    assert result == {"analyze": {"failed": "no store", "remedy": "write it"}}
    assert seen[-1]["kind"] == "step.failed" and seen[-1]["data"]["remedy"] == "write it"


def test_a_failure_of_the_dynamic_step_is_said_and_the_union_still_ends_the_run(tmp_path):
    """What a run observes is added to the static graph: a dynamic step that breaks leaves that graph, says why,
    and the pipeline goes on to the union."""
    import dynamic
    manifest = tmp_path / "out" / "manifest.sqlite"
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.read_project(tmp_path / "p", manifest)
    seen = []
    with mock.patch.object(dynamic, "run", side_effect=RuntimeError("the recorder's file is gone")):
        result = pipeline.run(manifest, listeners=[seen.append], start="dynamic")
    assert list(result) == ["dynamic", "union"] and "the recorder's file is gone" in result["dynamic"]["failed"]
    [said] = [e for e in seen if e["level"] == "error"]
    assert said["step"] == "dynamic" and "RuntimeError" in said["data"]["cause"] and said["data"]["remedy"]
    assert seen[-1] == {**seen[-1], "kind": "step.finished", "step": "union"}


def test_writing_a_snapshot_runs_the_scan_through_the_pipeline_and_the_pass_runs_the_rest():
    """One way in: `snapshot.py write` and a run's refresh run the scan step, the detached pass the analysis
    and the union."""
    import inspect
    assert "pipeline.run(" in inspect.getsource(snapshot.cmd_write)
    assert "premap.ensure" not in inspect.getsource(snapshot.cmd_write)
    assert "pipeline.run(" in inspect.getsource(resolve_edges.main)


def test_a_failing_stack_step_says_why_and_does_not_stop_the_steps_after_it(tmp_path):
    """The scan goes on without the stack's build tools (every source of `find_modules` runs), and says that the
    technologies of the modules failed as the stack step did."""
    import stack_recognition
    manifest = tmp_path / "out" / "manifest.sqlite"
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.read_project(tmp_path / "p", manifest)
    seen = []
    with mock.patch.object(stack_recognition, "ensure", side_effect=OSError("disk full")):
        result = pipeline.run(manifest, listeners=[seen.append], stop="scan", fast_scan=True)
    assert result["stack"] == {"failed": "OSError: disk full"}
    assert "failed" not in result["scan"] and result["scan"]["technologies_failed"] == "OSError: disk full"
    said = [e for e in seen if e["level"] == "error"]
    assert [(e["kind"], e["step"], e["data"]["remedy"]) for e in said] == [
        ("log", "stack", pipeline.Stack.WITHOUT), ("log", "scan", pipeline.Stack.WITHOUT)]
    [ended] = [e for e in seen if e["kind"] == "step.finished" and e["step"] == "stack"]
    assert ended["data"]["failed"] == "OSError: disk full"  # a listener of the step's end alone knows how it ended


def test_the_union_says_why_no_run_was_observed_when_the_dynamic_step_gave_no_reason(tmp_path):
    """A dynamic step that did not run in this analysis, or failed, leaves no reason per language: the union's
    gap carries that cause, not the words of a language no observer has."""
    import dynamic
    manifest = tmp_path / "out" / "manifest.sqlite"
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.read_project(tmp_path / "p", manifest)

    def details(**asked) -> list[str]:
        seen = []
        with mock.patch.object(resolve_edges, "edge_state",
                               return_value={"languages": {"python": {"state": "fresh", "coverage": {}}}}):
            pipeline.run(manifest, listeners=[seen.append], **asked)
        return [e["data"]["gap"]["detail"] for e in seen if e["kind"] == "gap" and e["step"] == "union"]

    assert details(start="union") == ["no edge observed in a run: the dynamic step did not run in this analysis"]
    with mock.patch.object(dynamic, "run", side_effect=RuntimeError("the recorder's file is gone")):
        assert details(start="dynamic") == ["no edge observed in a run: the dynamic step failed: RuntimeError: "
                                            "the recorder's file is gone"]


def test_an_interrupted_step_says_it_ends_before_the_interruption_leaves(tmp_path):
    manifest = tmp_path / "out" / "manifest.sqlite"
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.read_project(tmp_path / "p", manifest)
    seen = []
    with mock.patch.object(pipeline.Analyze, "run", side_effect=KeyboardInterrupt), pytest.raises(KeyboardInterrupt):
        pipeline.run(manifest, listeners=[seen.append], start="analyze")
    assert (seen[-1]["kind"], seen[-1]["step"]) == ("step.failed", "analyze")
    assert seen[-1]["data"]["cause"] == "interrupted: KeyboardInterrupt" and seen[-1]["data"]["remedy"]


def test_a_stopped_pass_and_one_that_ended_without_a_word_leave_no_step_open(tmp_path):
    """Who knows the pass is over says the end of what it left started: `stop_pass` after it ended it, and
    `ensure_edges` before it starts the next one."""
    manifest = (tmp_path / "manifest.sqlite").resolve()
    journal = manifest.with_name(events.JOURNAL)

    class Child:
        pid = 4321

        def wait(self):
            return 0

    def last_step():
        last = [e for e in events.read(journal)[0] if e["kind"].startswith("step.")][-1]
        return last["kind"], last["step"], last["data"].get("cause")

    with mock.patch.object(engine_pass, "running_record", return_value=tmp_path / "running.json"), \
            mock.patch.object(engine_pass, "_terminate_tree"):
        events.Bus(journal).emit("step.started", "analyze", step="analyze")
        with mock.patch.object(engine_pass, "pass_state", return_value={"state": "running", "pid": 1}):
            assert engine_pass.stop_pass(manifest, "the person asked")["stopped"]
        assert last_step() == ("step.failed", "analyze", "the analysis was stopped: the person asked")

        events.Bus(journal).emit("step.started", "dynamic", step="dynamic")
        with mock.patch.object(engine_pass, "edge_state", return_value={"state": "missing", "languages": {}}), \
                mock.patch.object(engine_pass, "pass_plan", return_value=([], {}, "digest")), \
                mock.patch.object(engine_pass, "engine_command", return_value=["pass"]), \
                mock.patch.object(engine_pass, "_spawn_detached", return_value=Child()):
            assert engine_pass.ensure_edges(manifest)["action"] == "started"
        assert last_step() == ("step.failed", "dynamic", "the analysis that started it ended without finishing it")


def test_the_pass_records_how_long_each_stage_took(tmp_path):
    """The measure a time limit per analyzer needs: the report keeps the seconds of every stage that reported."""
    manifest = tmp_path / "out" / "manifest.sqlite"
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.read_project(tmp_path / "p", manifest)
    spec = engine_pass.ENGINE_LANGUAGES["go"]
    stage = {"available": True, "engine": "scip-go", "languages": {"go": {"state": "fresh"}}}
    with mock.patch.object(engine_pass, "pass_plan", return_value=([(spec, ["go"])], {}, "digest")), \
            mock.patch.object(engine_pass, "free_memory", return_value=64 * 2**30), \
            mock.patch.object(engine_pass, "_launch", return_value=(None, None, None, stage)):
        report = engine_pass.run_pass(manifest, tmp_path / "out" / "report.json")
    assert report["languages"]["go"]["state"] == "fresh" and report["engines"]["scip-go"]["seconds"] >= 0


def test_a_start_or_stop_that_names_no_step_is_refused_before_any_event(tmp_path):
    seen = []
    with pytest.raises(ValueError, match="no step 'analyse': the steps are stack, scan, parse, analyze, dynamic, union"):
        pipeline.run(tmp_path / "manifest.sqlite", listeners=[seen.append], start="analyse")
    assert seen == [] and not (tmp_path / events.JOURNAL).exists()


def test_a_stage_whose_program_does_not_start_or_reports_no_report_fails_alone(tmp_path):
    """One stage's failure to start, or a report that is not one, is that stage's outcome: the pass goes on to
    the next analyzer instead of ending the analysis."""
    spec, manifest = engine_pass.ENGINES[0], tmp_path / "manifest.sqlite"

    def launch(run) -> tuple:
        with mock.patch.object(engine_pass, "stage_command", return_value=["no-such-program"]), \
                mock.patch.object(engine_pass, "cached_offline", return_value=False), \
                mock.patch.object(engine_pass, "node_environment", return_value={}), \
                mock.patch.object(engine_pass.subprocess, "run", side_effect=run):
            return engine_pass._launch(spec, list(spec.languages), manifest)

    state, reason, install, stage = launch(FileNotFoundError("no-such-program"))
    assert (state, install, stage) == ("failed", None, None) and "could not start: FileNotFoundError" in reason

    def not_a_report(command, **_options):
        manifest.with_name(f".engine-stage-{spec.name}.json").write_text("[]", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    state, reason, _install, stage = launch(not_a_report)
    assert state == "failed" and "without a report" in reason and stage == {"memory_exhausted": False}


def test_an_error_a_step_the_others_need_does_not_foresee_is_said_before_it_leaves(tmp_path):
    """A step the pipeline cannot do without (`WITHOUT` is None) that raises anything else than `StepFailed` still
    says `step.failed` with the cause, and the error reaches the caller as before."""
    manifest = tmp_path / "out" / "manifest.sqlite"
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.read_project(tmp_path / "p", manifest)
    seen = []
    with mock.patch.object(pipeline.Analyze, "run", side_effect=RuntimeError("the index is gone")), \
            pytest.raises(RuntimeError):
        pipeline.run(manifest, listeners=[seen.append], start="analyze")
    assert seen[-1]["kind"] == "step.failed" and seen[-1]["step"] == "analyze"
    assert seen[-1]["data"]["cause"] == "RuntimeError: the index is gone"


def test_the_pipeline_declares_its_steps_in_one_place():
    assert [step.NAME for step in pipeline.STEPS] == ["stack", "scan", "parse", "analyze", "dynamic", "union"]
    assert pipeline.Stack.INPUTS == ("inventory",)  # the stack takes no fact of the pre-map

    for step in pipeline.STEPS:
        assert step.INPUTS and step.OUTPUTS and callable(step.run)
    # what the pipeline does without a step that fails; None: the steps after it need it, and it stops them
    assert {step.NAME: bool(step.WITHOUT) for step in pipeline.STEPS} == {
        "scan": False, "stack": True, "parse": False, "analyze": False, "dynamic": True, "union": False}
    # the reading is `read_project`'s alone (the owner's decision of 24 November 2026): the step takes the read snapshot,
    # which the pipeline is given, and says the plan
    assert (pipeline.Parse.INPUTS, pipeline.Parse.OUTPUTS) == (("snapshot",), ("plan",))
    assert pipeline.INPUTS == ("inventory", "snapshot")


def test_the_parse_step_stops_on_a_store_that_holds_only_its_inventory_and_only_says_the_plan_of_a_read_one(tmp_path):
    """The reading is `snapshot.read_project`'s alone (the owner's decision of 24 November 2026, spec 8.11 step 3): a store
    with the inventory and no reading (8.6, point 3) stops the step with its remedy, read by no one; a read store is found as
    it is, and the step writes nothing."""
    import file_inventory
    from snapshot_store import open_snapshot
    project = tmp_path / "p"
    project.mkdir()
    (project / "a.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    (project / "b.py").write_text("from a import answer\n\nVALUE = answer()\n", encoding="utf-8")
    listed, read = tmp_path / "listed" / "manifest.sqlite", tmp_path / "read" / "manifest.sqlite"
    file_inventory.write(project, listed)
    snapshot.read_project(project, read)
    with open_snapshot(listed) as store:
        assert (store.metadata["reading"], store.file_count) == ("not-started", 0)
    kept = {path: path.read_bytes() for path in (listed, read)}
    seen = []
    with mock.patch.object(snapshot, "write_reading", side_effect=AssertionError("the parse step reads")):
        result = pipeline.run(listed, listeners=[seen.append], start="parse", stop="parse")
        assert list(result) == ["parse"] and result["parse"]["remedy"] == "write the snapshot again"
        assert "only its inventory" in result["parse"]["failed"]
        assert [(e["kind"], e["step"]) for e in seen if e["kind"].startswith("step.")] == [
            ("step.started", "parse"), ("step.failed", "parse")]
        seen.clear()
        result = pipeline.run(read, listeners=[seen.append], start="parse", stop="parse")
    assert list(result["parse"]) == ["plan"] and set(result["parse"]["plan"]) == {"nodes", "gaps"}
    assert result["parse"]["plan"]["nodes"] > 0
    assert [(e["kind"], e["step"]) for e in seen if e["kind"].startswith("step.")] == [
        ("step.started", "parse"), ("step.finished", "parse")]
    assert {path: path.read_bytes() for path in kept} == kept


def test_a_snapshot_that_cannot_be_read_stops_the_run_with_its_remedy(tmp_path):
    """The first step, the stack, stops the run with the remedy: a step failure, not an error; so do the scan and the parse
    step, where a run starts at one of them."""
    manifest = tmp_path / "out" / "manifest.sqlite"
    manifest.parent.mkdir()
    manifest.write_bytes(b"not a snapshot")
    for written in (True, False):
        if not written:
            manifest.unlink()
        for first in ("stack", "scan", "parse"):
            seen = []
            result = pipeline.run(manifest, listeners=[seen.append], start=first, stop=first)
            assert list(result) == [first] and result[first]["remedy"] == "write the snapshot again"
            assert result[first]["failed"].startswith("the snapshot cannot be read")
            assert seen[-1]["kind"] == "step.failed" and seen[-1]["step"] == first


def test_the_callers_say_a_failure_of_the_scan_step(tmp_path, capsys):
    """The command line and the MCP service run the pipeline to the stack and read the scan's result, the first
    step's: the failure is said, never a KeyError."""
    import mcp_service
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    stop = pipeline.StepFailed("the snapshot cannot be read: broken", "write the snapshot again")
    with mock.patch.object(pipeline.Scan, "run", side_effect=stop):
        status = snapshot.main(["write", str(project / "src"), "--out", str(tmp_path / "out" / "manifest.sqlite"),
                                "--no-index", "--no-engine"])
        assert status == 1 and "modules: the snapshot cannot be read: broken" in capsys.readouterr().err
        service = mcp_service.MapService(project)
        service.create_run("src", "example", engine=False)
    said = [event for event in service.events("example")["events"] if event["event"] == "modules_failed"]
    assert said and said[0]["message"].startswith("the snapshot cannot be read: broken")


def test_every_analyzer_declares_itself_and_the_pass_is_built_from_the_declarations():
    """An analyzer is one adapter module under `indexers/`: it says its name, the languages it indexes, the unit
    kinds it takes its structure from and whether its build runs only in a container, and gives its index. No
    hand-written list names them: a module that declares itself is an analyzer of the pass. Its name is `NAME`, as
    every adapter's, the observers' too (spec of the pipeline, 8.8 point 1), not `ENTRY`."""
    import importlib
    import dynamic
    import indexers
    assert [module.NAME for module in dynamic.observers() if not hasattr(module, "ENTRY")] == [
        "dynamic-callgrind-clang", "dynamic-callgrind-rust", "dynamic-record-dotnet", "dynamic-record-go",
        "dynamic-record-javascript", "dynamic-record-jvm", "dynamic-record-python"]
    declared = indexers.analyzers()
    assert {module.NAME for module in declared} == {
        "scip-go", "scip-rust", "scip-typescript", "scip-python", "scip-java", "scip-kotlin", "scip-clang",
        "scip-dotnet", "stylesheet"}
    for module in declared:
        assert not hasattr(module, "ENTRY")
        assert module.LANGUAGES and isinstance(module.UNIT_KINDS, frozenset)
        assert isinstance(module.NEEDS_CONTAINER, bool)
        assert module.MIN_FREE > 0
        assert callable(module.structure) and callable(module.index)
        spec = next(spec for spec in resolve_edges.ENGINES if spec.name == module.NAME)
        assert (spec.languages, spec.indexer, spec.needs_container) == (
            tuple(module.LANGUAGES), module.__name__.rsplit(".", 1)[-1], module.NEEDS_CONTAINER)
    source = importlib.util.find_spec("resolve_edges").origin
    assert 'EngineSpec("' not in Path(source).read_text(encoding="utf-8")


def test_an_analyzer_takes_the_units_of_the_kinds_it_declares():
    import indexers
    for module in indexers.analyzers():
        if module.NAME == "scip-python":
            continue  # its runs are the outermost Python projects (`premap.python_runs`)
        if not module.UNIT_KINDS:
            continue  # one run over the snapshot's files (`indexers/css.py`): it takes no unit
        record = {"units": [{"kind": kind, "root": f"u{number}", "name": f"u{number}"}
                            for number, kind in enumerate(sorted(module.UNIT_KINDS))], "workspace": []}
        given = module.structure(record)
        folders = given.get("roots") or {unit["root"] for unit in given.get("units", [])}
        assert folders, module.NAME



def _go_snapshot(tmp_path):
    import shutil
    project = tmp_path / "go"
    shutil.copytree(FIXTURES / "go", project, ignore=shutil.ignore_patterns("index.scip", "expected.json"))
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    return manifest


def test_the_scan_runs_the_model_commands_in_daodans_container_with_the_engine_found_once(tmp_path):
    """The scan hands the pre-map the container runner: each model source's commands go to one container run,
    the engine found once is given to the first run (it ends with that run), the others find their own."""
    import container
    import premap
    import container_runner
    manifest = _go_snapshot(tmp_path)
    engine = container.Engine("fake", ("fake",))
    asked = []

    def runner(manifest_given, engine=None, toolchains=()):
        def run(commands, toolchains=()):
            asked.append((commands[0]["tool"], engine))
            return [{"returncode": 1, "stdout": "", "stderr": "", "root": str(tmp_path / "go")} for _ in commands]
        return run

    seen = []
    with mock.patch.object(container, "find_engine", return_value=engine) as found, \
            mock.patch.object(container_runner, "runner", side_effect=runner):
        result = pipeline.run(manifest, listeners=[seen.append], stop="scan")
    assert "failed" not in result["scan"]
    assert found.call_count == 1
    assert [tool for tool, _ in asked] == ["renovate", "go", "noir"]
    assert [given for _, given in asked] == [engine, None, None]
    record = premap.ensure(manifest)
    assert not [s for s in record["sources"] if s["state"] == "not_run"]
    sources = {e["data"]["phase"] for e in seen if e["kind"] == "progress" and e["step"] == "scan"}
    assert {s["source"] for s in record["sources"]} == sources  # one progress event per source


def test_without_a_container_engine_the_model_sources_are_not_run_with_the_gap_and_no_wait(tmp_path):
    """No engine answers: the engine is asked once, every model source is `not_run` at once with a gap that names
    the missing engine and its remedy, nothing starts a container, and the next scan with an engine runs them."""
    import container
    import premap
    manifest = _go_snapshot(tmp_path)
    gap = container.Gap("no container engine answers: neither docker nor podman", "start Docker or Podman")
    seen = []
    with mock.patch.object(container, "find_engine", side_effect=gap) as found, \
            mock.patch.object(container, "run_commands", side_effect=AssertionError("a container started")):
        result = pipeline.run(manifest, listeners=[seen.append], stop="scan")
    assert "failed" not in result["scan"] and found.call_count == 1
    record = premap.ensure(manifest)
    model = [s for s in record["sources"] if s["state"] not in ("ran", "not_needed")]
    assert {s["source"].split("@")[0] for s in model} == {"renovate", "go", "noir"}
    assert {s["state"] for s in model} == {"not_run"}
    named = [g for g in record["gaps"] if g["kind"] == "model_not_run"]
    assert len(named) == 3 and all(gap.cause in g["detail"] and g["remedy"] == gap.remedy for g in named)
    assert sum(1 for e in seen if e["kind"] == "gap" and gap.cause in e["message"]) == len(named)
    assert premap.state(manifest, runner=lambda commands: [])["state"] == "stale"  # retried once one answers


def test_the_tests_start_no_container():
    """The suites write snapshots in this process and in `snapshot.py` subprocesses: the engine is off for both."""
    import os
    import container
    assert os.environ.get("DAODAN_CONTAINER") == "off"
    with pytest.raises(container.Gap, match="DAODAN_CONTAINER=off"):
        container.find_engine()


def _unmet(steps, given) -> list[tuple[str, str]]:
    """Each input of a step that no step before it writes and the pipeline is not given."""
    available, unmet = set(given), []
    for step in steps:
        unmet += [(step.NAME, name) for name in step.INPUTS if name not in available]
        available |= set(step.OUTPUTS)
    return unmet


def test_every_input_of_a_step_is_written_by_a_step_before_or_given_to_the_pipeline():
    """Spec of the pipeline, 8.8 point 3, proof 6: the order of the steps is the one their inputs ask for."""
    assert _unmet(pipeline.STEPS, pipeline.INPUTS) == []
    # the check sees a step out of place: `analyze` first reads a pre-map no step has written yet
    misplaced = [pipeline.Analyze, *(step for step in pipeline.STEPS if step is not pipeline.Analyze)]
    assert ("analyze", "premap") in _unmet(misplaced, pipeline.INPUTS)
    # `union` reads the symbols of the snapshot and the module graph `scan` wrote (`modules.ensure_graph`), not only the edges
    early = [pipeline.Union, *(step for step in pipeline.STEPS if step is not pipeline.Union)]
    assert ("union", "modules") in _unmet(early, pipeline.INPUTS)
