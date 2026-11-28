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
    bus.emit("step.started", "find_modules", step="find_modules")
    bus.progress("link_calls", 1, 3, analyzer="scip-go", phase="index")
    assert [(e["kind"], e["step"], e["level"]) for e in seen] == [("step.started", "find_modules", "info"),
                                                                  ("progress", "link_calls", "info")]
    assert seen[1]["data"] == {"done": 1, "total": 3, "phase": "index"} and seen[1]["analyzer"] == "scip-go"
    written, cursor = events.read(journal)
    assert [e["kind"] for e in written] == ["step.started", "progress"] and cursor == 2
    later, cursor = events.read(journal, after=1)
    assert [e["kind"] for e in later] == ["progress"] and cursor == 2


def test_a_line_still_being_written_is_read_next_time(tmp_path):
    journal = tmp_path / events.JOURNAL
    events.Bus(journal).emit("step.started", "find_modules", step="find_modules")
    with journal.open("a", encoding="utf-8") as stream:
        stream.write('{"kind": "prog')  # another process is appending
    written, cursor = events.read(journal)
    assert [e["kind"] for e in written] == ["step.started"] and cursor == 1


def test_a_broken_line_of_the_journal_is_skipped_and_hides_no_event_after_it(tmp_path):
    journal = tmp_path / events.JOURNAL
    bus = events.Bus(journal)
    bus.emit("step.started", "find_modules", step="find_modules")
    with journal.open("ab") as stream:
        stream.write(b'{"kind": "prog\n')  # a writer stopped in the middle of its line, and another went on
    bus.emit("step.finished", "find_modules", step="find_modules")
    written, cursor = events.read(journal)
    assert [e["kind"] for e in written] == ["step.started", "step.finished"] and cursor == 3
    assert events.read(journal, after=1, limit=1) == ([], 2)  # the broken line counts: the cursor stays a line count
    assert [e["kind"] for e in events.read(journal, after=2)[0]] == ["step.finished"]


def test_a_journal_that_cannot_be_written_stops_nothing_and_is_told_once(tmp_path):
    (tmp_path / "taken").write_text("", encoding="utf-8")  # a file where the journal's folder should be
    bus = events.Bus(tmp_path / "taken" / events.JOURNAL)
    seen = []
    bus.subscribe(seen.append)
    bus.emit("step.started", "find_modules", step="find_modules")
    bus.emit("step.finished", "find_modules", step="find_modules")
    assert [e["kind"] for e in seen] == ["step.started", "log", "step.finished"]
    assert seen[1]["level"] == "error" and seen[1]["data"]["cause"] and seen[1]["data"]["remedy"]


def test_what_an_ended_analysis_left_open_is_closed_with_the_cause_and_only_once(tmp_path):
    journal = tmp_path / events.JOURNAL
    bus = events.Bus(journal)
    bus.emit("step.started", "find_modules", step="find_modules")
    bus.emit("step.finished", "find_modules", step="find_modules")
    bus.emit("step.started", "link_calls", step="link_calls")
    bus.emit("analyzer.started", "scip-go for go", step="link_calls", analyzer="scip-go")
    bus.emit("analyzer.finished", "scip-go: go", step="link_calls", analyzer="scip-go")
    bus.emit("analyzer.started", "scip-rust for rust", step="link_calls", analyzer="scip-rust")
    assert events.close_open(journal, "its process is gone", "analyze again") == ["scip-rust", "link_calls"]
    closed = events.read(journal, after=6)[0]
    assert [(e["kind"], e["step"], e["analyzer"], e["level"]) for e in closed] == [
        ("analyzer.finished", "link_calls", "scip-rust", "error"), ("step.failed", "link_calls", None, "error")]
    assert all(e["data"] == {"cause": "its process is gone", "remedy": "analyze again"} for e in closed)
    assert events.close_open(journal, "its process is gone", "analyze again") == []
    assert events.close_open(tmp_path / "none.jsonl", "no journal", "nothing to close") == []


def test_a_journal_written_with_the_old_names_reads_with_the_ids(tmp_path):
    """A journal of an analysis before the eight ids (`events.LEGACY`): each old name reads as its id, `parse` as `read_code`,
    and what it left open is closed under the id."""
    journal = tmp_path / events.JOURNAL
    bus = events.Bus(journal)
    for old in ("stack", "scan", "parse", "analyze", "dynamic", "union"):
        bus.emit("step.started", old, step=old)
        bus.emit("step.finished", old, step=old)
    bus.emit("step.started", "analyze", step="analyze")
    written = events.read(journal)[0]
    assert [e["step"] for e in written[:12:2]] == ["recognize_stack", "find_modules", "read_code", "link_calls",
                                                   "run_and_observe", "assemble_graph"]
    assert [e["message"] for e in written[:12:2]] == ["stack", "scan", "parse", "analyze", "dynamic", "union"]
    assert events.close_open(journal, "its process is gone", "analyze again") == ["link_calls"]
    assert events.read(journal, after=13)[0][0]["step"] == "link_calls"


def test_an_unknown_kind_or_level_is_refused():
    bus = events.Bus()
    with pytest.raises(ValueError):
        bus.emit("whatever", "x", step="find_modules")
    with pytest.raises(ValueError):
        bus.emit("log", "x", step="find_modules", level="loud")


def test_a_listener_that_fails_stops_nothing_and_its_error_becomes_an_event(tmp_path):
    bus = events.Bus(tmp_path / events.JOURNAL)
    seen = []

    def broken(event):
        raise RuntimeError("listener down")

    bus.subscribe(broken)
    bus.subscribe(seen.append)
    bus.emit("step.started", "find_modules", step="find_modules")
    assert [e["kind"] for e in seen] == ["step.started", "log"]
    assert seen[1]["level"] == "error" and "listener down" in seen[1]["message"]


def test_a_warning_or_an_error_carries_its_cause_and_remedy():
    bus = events.Bus()
    with pytest.raises(ValueError):
        bus.emit("analyzer.unavailable", "no engine", step="link_calls", analyzer="scip-java", level="warning")
    event = bus.emit("analyzer.unavailable", "no engine", step="link_calls", analyzer="scip-java", level="warning",
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
    assert steps == [(kind, step.NAME) for step in pipeline.STEPS for kind in ("step.started", "step.finished")]
    analyzers = [(e["kind"], e["analyzer"]) for e in seen if e["kind"].startswith("analyzer.")
                 and e["step"] == "link_calls"]
    assert analyzers == [("analyzer.started", "scip-go"), ("analyzer.finished", "scip-go")]
    assert any(e["kind"] == "progress" and e["step"] == "link_calls" and e["data"]["total"] == 1 for e in seen)
    assert any(e["kind"] == "progress" and e["step"] == "find_modules" for e in seen)
    ready = [e for e in seen if e["kind"] == "graph.ready"]
    assert len(ready) == 1 and ready[0]["data"]["languages"]["go"]["state"] == "fresh"
    unobserved = [e["data"]["gap"] for e in seen if e["kind"] == "gap" and e["step"] == "assemble_graph"
                  and e["data"].get("language") == "go"]
    assert [gap["kind"] for gap in unobserved] == ["not-observed"]  # with the cause the dynamic step gave
    assert unobserved[0]["detail"] != "no edge observed in a run: the dynamic step has not observed this language"
    assert result["assemble_graph"]["languages"]["go"]["state"] == "fresh"
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
    result = pipeline.run(manifest, listeners=[seen.append], stop="find_modules")
    assert list(result) == ["recognize_stack", "find_modules"]
    assert [e["step"] for e in seen if e["kind"].startswith("step.")] == ["recognize_stack", "recognize_stack", "find_modules", "find_modules"]
    with mock.patch.object(pipeline.LinkCalls, "run", side_effect=pipeline.StepFailed("no store", "write it")):
        result = pipeline.run(manifest, listeners=[seen.append], start="link_calls")
    assert result == {"link_calls": {"failed": "no store", "remedy": "write it"}}
    assert seen[-1]["kind"] == "step.failed" and seen[-1]["data"]["remedy"] == "write it"


def test_a_step_whose_records_are_fresh_is_skipped_with_the_result_of_the_run_that_wrote_them(tmp_path):
    """Spec of the pipeline, 8.8: on the same snapshot the second run skips the three steps whose records are fresh
    (`step.skipped`, with their outputs), with the result the first run gave (the module graph untouched, `action` "none"),
    and starts the others; once a file changes no step is skipped. The union completes the module graph in between, and
    leaves it fresh."""
    import dynamic
    project, manifest = tmp_path / "p", tmp_path / "out" / "manifest.sqlite"
    project.mkdir()
    (project / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.read_project(project, manifest)
    fresh = ("recognize_stack", "find_modules", "find_entry_points")

    def analysis() -> tuple[dict, list[dict]]:
        seen = []
        with mock.patch.object(resolve_edges, "run_pass", return_value={}), mock.patch.object(dynamic, "run", return_value={}):
            result = pipeline.run(manifest, listeners=[seen.append])
        return result, [e for e in seen if e["kind"].startswith("step.")]

    first, steps = analysis()
    assert not [e for e in steps if e["kind"] == "step.skipped"]
    second, steps = analysis()
    assert [(e["kind"], e["step"]) for e in steps] == [
        *(("step.skipped", name) for name in fresh),
        *((kind, step.NAME) for step in pipeline.STEPS[3:] for kind in ("step.started", "step.finished"))]
    assert [e["data"] for e in steps[:3]] == [{"outputs": list(step.OUTPUTS), "reason": "inputs unchanged"}
                                             for step in pipeline.STEPS[:3]]
    assert first["find_modules"]["action"] != "none"
    assert {name: second[name] for name in fresh} == {
        name: {**first[name], **({"action": "none"} if name == "find_modules" else {})} for name in fresh}
    (project / "a.py").write_text("x = 2\ny = 3\n", encoding="utf-8")
    (project / "b.py").write_text("z = 1\n", encoding="utf-8")
    snapshot.read_project(project, manifest)
    _third, steps = analysis()
    assert [(e["kind"], e["step"]) for e in steps] == [
        (kind, step.NAME) for step in pipeline.STEPS for kind in ("step.started", "step.finished")]


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
        result = pipeline.run(manifest, listeners=[seen.append], start="run_and_observe")
    assert list(result) == ["run_and_observe", "assemble_graph"] and "the recorder's file is gone" in result["run_and_observe"]["failed"]
    [said] = [e for e in seen if e["level"] == "error"]
    assert said["step"] == "run_and_observe" and "RuntimeError" in said["data"]["cause"] and said["data"]["remedy"]
    assert seen[-1] == {**seen[-1], "kind": "step.finished", "step": "assemble_graph"}


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
        result = pipeline.run(manifest, listeners=[seen.append], stop="find_modules", fast_scan=True)
    assert result["recognize_stack"] == {"failed": "OSError: disk full"}
    assert "failed" not in result["find_modules"] and result["find_modules"]["technologies_failed"] == "OSError: disk full"
    said = [e for e in seen if e["level"] == "error"]
    assert [(e["kind"], e["step"], e["data"]["remedy"]) for e in said] == [
        ("log", "recognize_stack", pipeline.RecognizeStack.WITHOUT), ("log", "find_modules", pipeline.RecognizeStack.WITHOUT)]
    [ended] = [e for e in seen if e["kind"] == "step.finished" and e["step"] == "recognize_stack"]
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
        return [e["data"]["gap"]["detail"] for e in seen if e["kind"] == "gap" and e["step"] == "assemble_graph"]

    assert details(start="assemble_graph") == ["no edge observed in a run: the dynamic step did not run in this analysis"]
    with mock.patch.object(dynamic, "run", side_effect=RuntimeError("the recorder's file is gone")):
        assert details(start="run_and_observe") == ["no edge observed in a run: the dynamic step failed: RuntimeError: "
                                            "the recorder's file is gone"]


def test_the_union_counts_the_routes_of_the_static_links_and_says_the_calls_no_route_answers(tmp_path):
    """The union reads the static links with no rule (`flows.cached_links(manifest, [])`, the ones the envelope reads
    back): it reports the routes offered, called and linked, and a gap with the HTTP calls no single route answers;
    links that cannot be computed are an error that stops neither the other reports nor the graph."""
    import flows
    manifest = tmp_path / "out" / "manifest.sqlite"
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.read_project(tmp_path / "p", manifest)
    asked = []

    def links(path, rules):
        asked.append(rules)
        return {"routes": {"offered": 2, "called": 3, "linked": 1}}

    seen = []
    with mock.patch.object(flows, "cached_links", side_effect=links):
        result = pipeline.run(manifest, listeners=[seen.append], start="assemble_graph")
    assert asked == [[]] and result["assemble_graph"]["routes"] == {"offered": 2, "called": 3, "linked": 1}
    [gap] = [e["data"]["gap"] for e in seen if e["kind"] == "gap" and e["data"]["gap"]["kind"] == "routes-not-joined"]
    assert (gap["calls"], gap["called"], gap["offered"]) == (2, 3, 2)
    assert "2 of 3 HTTP calls are linked to no route" in gap["detail"]
    seen.clear()
    with mock.patch.object(flows, "cached_links", side_effect=ValueError("the inputs changed")):
        result = pipeline.run(manifest, listeners=[seen.append], start="assemble_graph")
    assert "routes" not in result["assemble_graph"]
    [said] = [e for e in seen if e["level"] == "error"]
    assert said["step"] == "assemble_graph" and "ValueError" in said["data"]["cause"] and said["data"]["remedy"]
    assert seen[-1] == {**seen[-1], "kind": "step.finished", "step": "assemble_graph"}
    assert any(e["kind"] == "graph.ready" for e in seen)


def test_an_interrupted_step_says_it_ends_before_the_interruption_leaves(tmp_path):
    manifest = tmp_path / "out" / "manifest.sqlite"
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "a.py").write_text("x = 1\n", encoding="utf-8")
    snapshot.read_project(tmp_path / "p", manifest)
    seen = []
    with mock.patch.object(pipeline.LinkCalls, "run", side_effect=KeyboardInterrupt), pytest.raises(KeyboardInterrupt):
        pipeline.run(manifest, listeners=[seen.append], start="link_calls")
    assert (seen[-1]["kind"], seen[-1]["step"]) == ("step.failed", "link_calls")
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
        events.Bus(journal).emit("step.started", "link_calls", step="link_calls")
        with mock.patch.object(engine_pass, "pass_state", return_value={"state": "running", "pid": 1}):
            assert engine_pass.stop_pass(manifest, "the person asked")["stopped"]
        assert last_step() == ("step.failed", "link_calls", "the analysis was stopped: the person asked")

        events.Bus(journal).emit("step.started", "run_and_observe", step="run_and_observe")
        with mock.patch.object(engine_pass, "edge_state", return_value={"state": "missing", "languages": {}}), \
                mock.patch.object(engine_pass, "pass_plan", return_value=([], {}, "digest")), \
                mock.patch.object(engine_pass, "engine_command", return_value=["pass"]), \
                mock.patch.object(engine_pass, "_spawn_detached", return_value=Child()):
            assert engine_pass.ensure_edges(manifest)["action"] == "started"
        assert last_step() == ("step.failed", "run_and_observe", "the analysis that started it ended without finishing it")


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
    with pytest.raises(ValueError, match="no step 'analyse': the steps are recognize_stack, find_modules, "
                                         "find_entry_points, link_calls, run_and_observe, assemble_graph"):
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
    with mock.patch.object(pipeline.LinkCalls, "run", side_effect=RuntimeError("the index is gone")), \
            pytest.raises(RuntimeError):
        pipeline.run(manifest, listeners=[seen.append], start="link_calls")
    assert seen[-1]["kind"] == "step.failed" and seen[-1]["step"] == "link_calls"
    assert seen[-1]["data"]["cause"] == "RuntimeError: the index is gone"


def test_the_pipeline_declares_its_steps_in_one_place():
    assert [step.NAME for step in pipeline.STEPS] == ["recognize_stack", "find_modules", "find_entry_points", "link_calls",
                                                      "run_and_observe", "assemble_graph"]
    # the eight ids: the first two run before the pipeline (`snapshot.read_project`)
    assert pipeline.IDS == ("list_files", "read_code", *(step.NAME for step in pipeline.STEPS))
    assert pipeline.RecognizeStack.INPUTS == ("inventory",)  # the stack takes no fact of the pre-map

    for step in pipeline.STEPS:
        assert step.INPUTS and step.OUTPUTS and callable(step.run)
    # what the pipeline does without a step that fails; None: the steps after it need it, and it stops them
    assert {step.NAME: bool(step.WITHOUT) for step in pipeline.STEPS} == {
        "find_modules": False, "recognize_stack": True, "find_entry_points": True, "link_calls": False,
        "run_and_observe": True, "assemble_graph": False}
    # the entry points are a step of their own, after the pre-map they read: `link_calls` does not read them
    assert "entry_points" not in pipeline.FindModules.OUTPUTS + pipeline.LinkCalls.INPUTS
    assert (pipeline.FindEntryPoints.INPUTS, pipeline.FindEntryPoints.OUTPUTS) == (
        ("inventory", "stack", "premap", "snapshot"), ("entry_points",))
    # the reading is `read_project`'s alone (the owner's decision of 24 November 2026): the pipeline is given the snapshot
    assert pipeline.INPUTS == ("inventory", "snapshot")


def test_link_calls_stops_on_a_store_that_holds_only_its_inventory(tmp_path):
    """The reading is `snapshot.read_project`'s alone (the owner's decision of 24 November 2026, spec 8.11 step 3): a store
    with the inventory and no reading (8.6, point 3) stops `link_calls`, the first step that needs it, with its remedy; no
    one reads it, and no analyzer starts."""
    import file_inventory
    from snapshot_store import open_snapshot
    project = tmp_path / "p"
    project.mkdir()
    (project / "a.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    listed = tmp_path / "listed" / "manifest.sqlite"
    file_inventory.write(project, listed)
    with open_snapshot(listed) as store:
        assert (store.metadata["reading"], store.file_count) == ("not-started", 0)
    kept = listed.read_bytes()
    seen = []
    with mock.patch.object(snapshot, "write_reading", side_effect=AssertionError("the step reads")), \
            mock.patch.object(resolve_edges, "run_pass", side_effect=AssertionError("an analyzer started")):
        result = pipeline.run(listed, listeners=[seen.append], start="link_calls", stop="link_calls")
    assert list(result) == ["link_calls"] and result["link_calls"]["remedy"] == "write the snapshot again"
    assert "only its inventory" in result["link_calls"]["failed"]
    assert [(e["kind"], e["step"]) for e in seen if e["kind"].startswith("step.")] == [
        ("step.started", "link_calls"), ("step.failed", "link_calls")]
    assert listed.read_bytes() == kept


def test_a_snapshot_that_cannot_be_read_stops_the_run_with_its_remedy(tmp_path):
    """The first step, `recognize_stack`, stops the run with the remedy: a step failure, not an error; so do the steps after
    it that read the store, where a run starts at one of them."""
    manifest = tmp_path / "out" / "manifest.sqlite"
    manifest.parent.mkdir()
    manifest.write_bytes(b"not a snapshot")
    for written in (True, False):
        if not written:
            manifest.unlink()
        for first in ("recognize_stack", "find_modules", "find_entry_points", "link_calls"):
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
    with mock.patch.object(pipeline.FindModules, "run", side_effect=stop):
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
    """The scan hands the pre-map the container runner, and the entry points the same one: each model source's commands go
    to one container run, the engine found once is given to the first run (it ends with that run), the others find their own."""
    import container
    import entry_points
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
        result = pipeline.run(manifest, listeners=[seen.append], stop="find_entry_points")
    assert "failed" not in result["find_modules"] and "failed" not in result["find_entry_points"]
    assert found.call_count == 1
    assert [tool for tool, _ in asked] == ["renovate", "go", "noir"]
    assert [given for _, given in asked] == [engine, None, None]
    ran = [*premap.ensure(manifest)["sources"], *entry_points.ensure(manifest)["sources"]]  # the entry points after the pre-map
    assert not [s for s in ran if s["state"] == "not_run"]
    sources = {e["data"]["phase"] for e in seen if e["kind"] == "progress" and e["step"] in ("find_modules", "find_entry_points")}
    assert {s["source"] for s in ran} == sources  # one progress event per source, under its step


def test_without_a_container_engine_the_model_sources_are_not_run_with_the_gap_and_no_wait(tmp_path):
    """No engine answers: the engine is asked once, every model source is `not_run` at once with a gap that names
    the missing engine and its remedy, nothing starts a container, and the next scan with an engine runs them."""
    import container
    import entry_points
    import premap
    manifest = _go_snapshot(tmp_path)
    gap = container.Gap("no container engine answers: neither docker nor podman", "start Docker or Podman")
    seen = []
    with mock.patch.object(container, "find_engine", side_effect=gap) as found, \
            mock.patch.object(container, "run_commands", side_effect=AssertionError("a container started")):
        result = pipeline.run(manifest, listeners=[seen.append], stop="find_entry_points")
    assert "failed" not in result["find_modules"] and found.call_count == 1  # once for the pre-map and the entry points
    record, found = premap.ensure(manifest), entry_points.ensure(manifest)
    model = [s for s in (*record["sources"], *found["sources"]) if s["state"] not in ("ran", "not_needed")]
    assert {s["source"].split("@")[0] for s in model} == {"renovate", "go", "noir"}
    assert {s["state"] for s in model} == {"not_run"}
    named = [g for g in (*record["gaps"], *found["gaps"]) if g["kind"] == "model_not_run"]
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
    misplaced = [pipeline.LinkCalls, *(step for step in pipeline.STEPS if step is not pipeline.LinkCalls)]
    assert ("link_calls", "premap") in _unmet(misplaced, pipeline.INPUTS)
    # `union` reads the symbols of the snapshot and the module graph `scan` wrote (`modules.ensure_graph`), not only the edges
    early = [pipeline.AssembleGraph, *(step for step in pipeline.STEPS if step is not pipeline.AssembleGraph)]
    assert ("assemble_graph", "modules") in _unmet(early, pipeline.INPUTS)
    # the entry points read the pre-map `scan` writes
    entries = [pipeline.FindEntryPoints, *(step for step in pipeline.STEPS if step is not pipeline.FindEntryPoints)]
    assert ("find_entry_points", "premap") in _unmet(entries, pipeline.INPUTS)
