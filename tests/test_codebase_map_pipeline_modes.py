"""The two modes of the analysis give one model, and the fallback says where its data comes from (punto 17; proofs 2 and 5
of the pipeline's old spec), on the fixtures of the pre-map with the outputs a Linux container gave
(`tests/fixtures/premap/outputs`, saved by `benchmarks/project-model/modal_premap.py --store`).

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_pipeline_modes.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import entry_points  # noqa: E402
import engine_pass  # noqa: E402
import modules  # noqa: E402
import pipeline  # noqa: E402
import premap  # noqa: E402
from entry_points import flow_entries  # noqa: E402
from test_codebase_map_container_runner import manifest_of  # noqa: E402

FIXTURES = Path(__file__).with_name("fixtures") / "premap"
PROJECTS = json.loads((FIXTURES / "projects.json").read_text(encoding="utf-8"))
CASES = ("npm_workspace", "uv_workspace")


def replay(name: str):
    """The runner of the recorded outputs of `name`; a command with no recorded output (Noir's, which the store does not keep)
    finds no container, as `container_runner` says it, so both modes meet the same gap."""
    stored = json.loads((FIXTURES / "outputs" / f"{name}.json").read_text(encoding="utf-8"))
    table = {json.dumps(run["command"], sort_keys=True): run["result"] for run in stored["runs"]}

    def run(commands: list[dict]) -> list[dict]:
        keys = [json.dumps(command, sort_keys=True) for command in commands]
        if any(key not in table for key in keys):
            raise container.Gap(f"no recorded output for {commands[0]['tool']}", "record it from a Linux container")
        return [table[key] for key in keys]
    return run


def model(manifest: Path) -> dict:
    """What an analysis leaves of the project: the units of the pre-map, the modules, the rows of the entry points and the
    state of the edges, with the folders of this test written as placeholders."""
    graph = modules.load_graph(Path(modules.graph_state(manifest)["graph"]))
    edges = engine_pass.edge_state(manifest)
    found = {"units": json.loads(premap.path(manifest).read_text(encoding="utf-8"))["units"],
             "modules": graph["modules"],
             "entries": entry_points.rows(json.loads(entry_points.path(manifest).read_text(encoding="utf-8"))),
             "edges": {"state": edges["state"],
                       "languages": {language: entry["state"] for language, entry in edges["languages"].items()}}}
    text = json.dumps(found, sort_keys=True)
    for folder in (manifest.parent, manifest.parents[1] / "proj"):
        text = text.replace(folder.resolve().as_posix(), f"<{folder.name}>")
    return json.loads(text)


@pytest.mark.parametrize("name", CASES)
def test_a_quick_caller_then_the_whole_pipeline_gives_the_model_of_the_whole_pipeline_alone(tmp_path, name):
    """(a) The quick caller (`fast_scan`, stopped after the entry points, as the hook and the run's creation call it) leaves
    the model commands to do; the whole pipeline after it runs them, and the model is the one the whole pipeline gives alone."""
    runner = replay(name)
    with mock.patch.object(pipeline, "_runner", return_value=runner):
        _, quick = manifest_of(tmp_path / "quick", PROJECTS[name])
        pipeline.run(quick, stop="find_entry_points", fast_scan=True)
        deferred = json.loads(premap.path(quick).read_text(encoding="utf-8"))
        assert [source for source in deferred["sources"] if source.get("state") == "not_run"]  # the commands wait
        pipeline.run(quick)
        _, alone = manifest_of(tmp_path / "alone", PROJECTS[name])
        pipeline.run(alone)
    ran = json.loads(premap.path(quick).read_text(encoding="utf-8"))
    assert not [source for source in ran["sources"] if source.get("state") == "not_run"]
    assert model(quick) == model(alone)
    assert model(alone)["units"] and model(alone)["modules"]


@pytest.mark.parametrize("name", CASES)
def test_with_no_container_every_fallback_says_where_its_data_comes_from(tmp_path, monkeypatch, name):
    """(b) With `DAODAN_CONTAINER=off` each source with commands has `model_not_run` with cause and remedy, the modules come
    from the manifests (`provenance` `build`) and every unit names its sources; the entry points come from no tool, and their
    gap says so: what the flows have are the readers of the snapshot (`entries.candidates`, the queries)."""
    monkeypatch.setenv("DAODAN_CONTAINER", "off")
    _, manifest = manifest_of(tmp_path, PROJECTS[name])
    pipeline.run(manifest, stop="find_entry_points")
    record = json.loads(premap.path(manifest).read_text(encoding="utf-8"))
    deferred = [source for source in record["sources"] if source.get("state") == "not_run"]
    assert deferred
    said = {gap["source"]: gap for gap in record["gaps"] if gap["kind"] == "model_not_run"}
    for source in deferred:
        gap = said[source["source"]]
        assert (gap["cause"], bool(gap["remedy"])) == (container.OFF_CAUSE, True), source["source"]
    assert record["units"] and all(unit["sources"] for unit in record["units"])
    graph = modules.load_graph(Path(modules.graph_state(manifest)["graph"]))
    assert graph["modules"] and {module["provenance"] for module in graph["modules"]} == {"build"}
    tools, _ = entry_points.rows(json.loads(entry_points.path(manifest).read_text(encoding="utf-8")))
    assert tools == []  # neither Noir nor a framework's tool ran
    rows, gaps = flow_entries.evidence(manifest)
    assert all(row["reader"] == "manifesto" and row["declared_in"] for row in rows)  # each with the file that declares it
    noir = [gap for gap in gaps if gap["source"].startswith("noir@") and gap["kind"] == "model_not_run"]
    assert noir and all(gap["cause"] == container.OFF_CAUSE and gap["remedy"] for gap in noir)
    from pipeline import plan
    actions = {action["id"]: action for action in plan.current(manifest)["actions"]}
    for source in deferred:  # the plan says it as well: the action cannot run here, with why and what to do
        action = actions[f"find_modules:{source['source']}"]
        assert (action["state"], action["gap"], bool(action["cause"]), bool(action["remedy"])) == (
            "not_possible", "model_not_run", True, True)
