"""The pass's states and events say what happened: no language is fresh without a file indexed, no build's
failure is dropped, no language of the snapshot goes without a state or a gap.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_honest_state.py
"""
from __future__ import annotations

import contextlib
import io
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))

import pipeline  # noqa: E402
import resolve_edges  # noqa: E402
import engine_pass  # noqa: E402
import snapshot  # noqa: E402
from pipeline import events  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures/code-graph"
POM = ("<project><modelVersion>4.0.0</modelVersion><groupId>g</groupId><artifactId>a</artifactId>"
       "<version>1</version></project>\n")
INDEXER = {"name": "scip-go", "version": "v0.2.9", "seconds": 1.0, "peak_mb": None}


def _project(tmp_path, extra: dict | None = None, fixture: str | None = "go") -> tuple[Path, Path]:
    project = tmp_path / "project"
    if fixture:
        shutil.copytree(FIXTURES / fixture, project, ignore=shutil.ignore_patterns("index.scip", "expected.json"))
    for rel, text in (extra or {}).items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    return project, manifest


def _contract(**outcome) -> dict:
    return {"indexes": [[str(FIXTURES / "go" / "index.scip"), ""]], "runs": [], "indexer": INDEXER, **outcome}


@contextlib.contextmanager
def _go_pass(index, languages=("go",)):
    """The pass with scip-go alone, serving `languages`, its stage run in this process and `index` standing in for
    the indexer."""
    from indexers import go
    spec = next(spec for spec in resolve_edges.ENGINES if spec.name == "scip-go")._replace(languages=languages)
    real = subprocess.run

    def stage(command, **options):
        if command[1:2] != ["--engine"]:
            return real(command, **options)
        with contextlib.redirect_stdout(io.StringIO()):
            resolve_edges.main(command)
        return subprocess.CompletedProcess(command, 0)

    with mock.patch.object(engine_pass, "ENGINES", (spec,)), \
            mock.patch.object(engine_pass, "ENGINE_LANGUAGES", dict.fromkeys(languages, spec)), \
            mock.patch.object(engine_pass, "stage_command", side_effect=lambda spec, manifest, path, offline=False:
                              [str(manifest), "--engine", spec.name, "--report-out", str(path)]), \
            mock.patch.object(engine_pass, "cached_offline", return_value=False), \
            mock.patch.object(subprocess, "run", side_effect=stage), \
            mock.patch.object(go, "index", side_effect=index), \
            mock.patch.object(engine_pass, "free_memory", return_value=64 * 2**30):
        yield spec


def _run(manifest: Path, index, languages=("go",), **options) -> tuple[dict, list[dict]]:
    seen = []
    with _go_pass(index, languages):
        result = pipeline.run(manifest, listeners=[seen.append], start="analyze", **options)
    return result, seen


def _gaps(seen: list[dict], step: str, kind: str) -> list[dict]:
    return [e["data"]["gap"] for e in seen if e["kind"] == "gap" and e["step"] == step
            and e["data"]["gap"]["kind"] == kind]


def test_a_language_with_no_file_in_the_index_is_failed_with_the_commonest_reason(tmp_path):
    """The indexer wrote an index that holds none of the language's files: the language is not fresh, the store
    holds no entry for it, and the reason counts the files and gives the commonest cause."""
    _project_dir, manifest = _project(tmp_path)
    empty = tmp_path / "empty.scip"
    empty.write_bytes(b"")
    result, seen = _run(manifest, lambda project_dir, work_dir, files=None, **given:
                        _contract(indexes=[[str(empty), ""]]))
    outcome = result["analyze"]["languages"]["go"]
    assert outcome["state"] == "failed"
    assert "none of the 2 go files" in outcome["reason"] and "no document in the index (2)" in outcome["reason"]
    assert result["analyze"]["available"] is False
    assert resolve_edges.edge_state(manifest)["languages"]["go"]["state"] == "failed"
    finished = [e for e in seen if e["kind"] == "analyzer.finished"]
    assert [e["level"] for e in finished] == ["error"] and "no document in the index" in finished[0]["data"]["cause"]
    assert result["union"]["languages"]["go"]["state"] == "failed"


def test_one_language_of_a_stage_without_a_file_indexed_is_failed_beside_the_fresh_one(tmp_path):
    """An analyzer of two languages whose index holds files of one only: that one is fresh, the other failed with
    its cause, and the stage says so on the bus."""
    _project_dir, manifest = _project(tmp_path, {"native/b.c": "int b(void) { return 1; }\n"})
    result, seen = _run(manifest, lambda project_dir, work_dir, files=None, **given: _contract(), ("go", "c"))
    languages = result["analyze"]["languages"]
    assert languages["go"]["state"] == "fresh" and result["analyze"]["available"] is True
    assert languages["c"]["state"] == "failed" and "none of the 1 c files" in languages["c"]["reason"]
    [gap] = _gaps(seen, "analyze", "language_not_indexed")
    assert gap["language"] == "c" and gap["detail"] == languages["c"]["reason"]
    state = resolve_edges.edge_state(manifest)["languages"]
    assert (state["go"]["state"], state["c"]["state"]) == ("fresh", "failed")


def test_the_files_the_index_does_not_hold_are_a_gap_of_the_union(tmp_path):
    """One file of three is not in the index: the language is fresh, a lower bound, and the union says how many
    files are missing and why."""
    _project_dir, manifest = _project(tmp_path, {"tools/tool.go": "package tools\n"})
    result, seen = _run(manifest, lambda project_dir, work_dir, files=None, **given: _contract())
    assert result["union"]["languages"]["go"]["state"] == "fresh"
    [gap] = _gaps(seen, "union", "files-missing")
    assert (gap["files"], gap["of"]) == (1, 3) and gap["reasons"] == {"no document in the index": 1}
    [event] = [e for e in seen if e["kind"] == "gap" and e["data"]["gap"]["kind"] == "files-missing"]
    assert event["data"]["language"] == "go" and "1 of 3" in event["message"]


def test_a_build_that_gave_no_index_is_a_gap_of_the_stage_beside_the_one_that_did(tmp_path):
    """Two builds, one failed and one indexed: the language is fresh from the one, and the other's cause is a gap
    of the stage's report, said on the bus."""
    _project_dir, manifest = _project(tmp_path)
    builds = [{"root": "", "state": "done"},
              {"root": "legacy", "state": "failed", "reason": "scip-java wrote no index (exit code 1): boom"}]
    result, seen = _run(manifest, lambda project_dir, work_dir, files=None, **given: _contract(builds=builds))
    assert result["analyze"]["languages"]["go"]["state"] == "fresh"
    [gap] = _gaps(seen, "analyze", "build_not_indexed")
    assert gap["path"] == "legacy" and gap["state"] == "failed" and "boom" in gap["detail"]
    assert result["analyze"]["engines"]["scip-go"]["gaps"] == [gap]


def test_a_unit_or_a_run_that_gave_no_index_is_a_gap_of_the_stage(tmp_path):
    """Clang's units and the runs of an indexer without builds: each one without an index is a gap; the probe run
    at a root that holds no manifest is not."""
    _project_dir, manifest = _project(tmp_path)
    units = [{"root": "lib", "state": "indexed"},
             {"root": "app", "state": "unavailable", "kind": "not-cmake", "cause": "built with make"}]
    _result, seen = _run(manifest, lambda project_dir, work_dir, files=None, **given: _contract(units=units))
    [gap] = _gaps(seen, "analyze", "build_not_indexed")
    assert (gap["path"], gap["state"]) == ("app", "unavailable") and "built with make" in gap["detail"]

    _project_dir, manifest = _project(tmp_path / "runs", {"tools/go.mod": "module example.com/tools\n\ngo 1.21\n",
                                                          "tools/tool.go": "package tools\n"})
    runs = [{"prefix": "", "returncode": 0, "index": "x.scip"},
            {"prefix": "tools", "returncode": 1, "index": None, "stderr_tail": "warning\npanic: no packages\n"}]
    _result, seen = _run(manifest, lambda project_dir, work_dir, files=None, **given: _contract(runs=runs))
    [gap] = _gaps(seen, "analyze", "build_not_indexed")
    assert gap["path"] == "tools" and "exit code 1" in gap["detail"] and "panic: no packages" in gap["detail"]

    _project_dir, manifest = _project(tmp_path / "probe", {"tools/go.mod": "module example.com/tools\n\ngo 1.21\n",
                                                           "tools/tool.go": "package tools\n"}, fixture=None)
    probe = [{"prefix": "", "returncode": 1, "index": None, "stderr_tail": "no go.mod"},
             {"prefix": "tools", "returncode": 0, "index": "x.scip"}]
    _result, seen = _run(manifest, lambda project_dir, work_dir, files=None, **given: _contract(runs=probe))
    assert not _gaps(seen, "analyze", "build_not_indexed")


def test_a_wanted_language_the_stage_does_not_report_is_missing(tmp_path):
    _project_dir, manifest = _project(tmp_path)
    stage = {"available": True, "engine": "scip-go@v0.2.9", "languages": {}}
    with _go_pass(None), mock.patch.object(engine_pass, "_launch", return_value=(None, None, None, stage)):
        report = engine_pass.run_pass(manifest, manifest.with_name(engine_pass.REPORT_NAME), bus=events.Bus())
    assert report["languages"]["go"]["state"] == "missing" and "scip-go" in report["languages"]["go"]["reason"]
    assert report["available"] is False


def test_without_a_container_an_analyzer_with_nothing_to_build_says_that(tmp_path):
    """Java files and no Gradle or Maven build: the cause is the missing build, which no container changes."""
    project, manifest = _project(tmp_path, {"src/A.java": "class A { void a() {} }\n"}, fixture=None)
    spec = next(spec for spec in resolve_edges.ENGINES if spec.name == "scip-java")
    report = engine_pass.index_stage(spec, manifest, project)
    assert report["available"] is False and "no Gradle or Maven build" in report["reason"]
    assert "container" not in report["reason"]
    with_build = _project(tmp_path / "built", {"src/A.java": "class A {}\n", "pom.xml": "<project/>\n"}, fixture=None)
    report = engine_pass.index_stage(spec, with_build[1], with_build[0])
    assert "the build runs only in a container" in report["reason"]


def test_a_language_with_no_parsed_file_is_unavailable_in_the_pass_with_the_reason(tmp_path):
    """A host without the grammar leaves a language's files `lexical`: the pass still names the language, starts
    no stage for it and says why, in its report, its state and on the bus."""
    _project_dir, manifest = _project(tmp_path)
    with contextlib.closing(sqlite3.connect(manifest)) as database:
        database.execute("UPDATE sem_coverage SET status='lexical' WHERE language='go'")
        database.commit()
    started = []
    result, seen = _run(manifest, lambda *given, **options: started.append(1) or _contract())
    assert not started
    outcome = result["analyze"]["languages"]["go"]
    assert outcome["state"] == "unavailable" and "none of the 2 go files" in outcome["reason"]
    assert "lexical" in outcome["reason"] and outcome["install"]
    [event] = [e for e in seen if e["kind"] == "analyzer.unavailable"]
    assert event["data"]["languages"] == ["go"] and event["data"]["cause"] == outcome["reason"]
    state = resolve_edges.edge_state(manifest)
    assert state["languages"]["go"]["state"] == "unavailable" and state["state"] == "unavailable"


def test_the_union_names_the_languages_no_analyzer_serves(tmp_path):
    """C# and SQL are in the snapshot and no analyzer lists them: one gap each with its files, in the union's
    result and in the pass's state; a stylesheet, which an analyzer reads by its own name, is not one."""
    _project_dir, manifest = _project(tmp_path, {"db/a.sql": "select 1;\n", "db/b.sql": "select 2;\n",
                                                 "X.cs": "class X { void M() {} }\n", "s.scss": "a { b: c }\n"})
    seen = []
    result = pipeline.Union.run(pipeline.Context(manifest, _bus(seen)))
    assert result["no_analyzer"] == {"csharp": 1, "sql": 2}
    gaps = {gap["language"]: gap for gap in _gaps(seen, "union", "no-analyzer")}
    assert set(gaps) == {"csharp", "sql"} and gaps["sql"]["files"] == 2 and "2 sql files" in gaps["sql"]["detail"]
    assert resolve_edges.edge_state(manifest)["no_analyzer"] == {"csharp": 1, "sql": 2}
    assert "no_analyzer" not in resolve_edges.edge_state(_project(tmp_path / "go")[1])


def test_the_union_says_calls_across_two_analyzers_are_not_resolved(tmp_path):
    """Go and C in one snapshot (cgo): each analyzer reads its own index, and the union says so; Go alone, and C
    with C++ (one index), say nothing."""
    _project_dir, manifest = _project(tmp_path, {"native/b.c": "int b(void) { return 1; }\n",
                                                 "native/c.cpp": "int c() { return 1; }\n"})
    seen = []
    result = pipeline.Union.run(pipeline.Context(manifest, _bus(seen)))
    [gap] = _gaps(seen, "union", "not-joined")
    assert gap["languages"] == ["go", "c"] and "not resolved" in gap["detail"]
    assert result["not_joined"] == [["go", "c"]]
    seen = []
    result = pipeline.Union.run(pipeline.Context(_project(tmp_path / "go")[1], _bus(seen)))
    assert not _gaps(seen, "union", "not-joined") and "not_joined" not in result


def _bus(seen: list) -> events.Bus:
    bus = events.Bus()
    bus.subscribe(seen.append)
    return bus
