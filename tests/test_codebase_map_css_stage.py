"""The stylesheet analyzer in the engine pass: one `stylesheet` entry written from the graph's own rows.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_css_stage.py

The engines replay the runs recorded for the fixture `css` (`test_codebase_map_css_graph.py`) through the runner the
analyzer builds (`css.node_runner`), patched here.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
for path in (str(SCRIPTS), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)
import resolve_edges  # noqa: E402
import snapshot  # noqa: E402
from indexers import css, runtime  # noqa: E402
from test_codebase_map_css_graph import project_copy, replayer  # noqa: E402

SPEC = next(spec for spec in resolve_edges.ENGINES if spec.name == "stylesheet")


@pytest.fixture()
def project(tmp_path):
    """The fixture `css` with the package files its recording holds, its snapshot and its recorded runs."""
    root, recording = project_copy("css", tmp_path)
    manifest = tmp_path / "manifest.sqlite"
    snapshot.write_snapshot(root, manifest)
    return root, manifest, replayer(recording)


def stage(root, manifest, runner):
    """The stage with `runner` for the engines on the host and for Tailwind's, the container's (`tailwind_runner`)."""
    with mock.patch.object(css, "node_runner", return_value=runner), \
            mock.patch.object(css, "tailwind_runner", return_value=runner):
        return resolve_edges.index_stage(SPEC, manifest, root)


def test_the_pass_serves_stylesheets_the_snapshot_reads_lexically(project):
    _root, manifest, _runner = project
    plan, _fresh, _digest = resolve_edges.pass_plan(manifest)
    assert [(spec.name, languages) for spec, languages in plan if "stylesheet" in languages] == [
        ("stylesheet", ["stylesheet"])]


def test_the_stage_writes_one_stylesheet_entry_with_its_coverage(project):
    root, manifest, runner = project
    report = stage(root, manifest, runner)
    assert report["available"], report
    assert report["languages"] == {"stylesheet": {"state": "fresh"}}
    assert report["engine"].startswith("stylesheet@")
    state = resolve_edges.edge_state(manifest)["languages"]["stylesheet"]
    assert state["state"] == "fresh" and state["engine"] == report["engine"]
    coverage = state["coverage"]
    assert "violations" not in coverage and coverage["sites"] > 0
    assert coverage["sites"] == sum(coverage["answered"].values()) + sum(
        item["count"] for item in coverage["holes"].values())
    with snapshot.open_snapshot(manifest) as store:
        edges, _binding, reason = resolve_edges.read_edge_store(resolve_edges.default_edge_store(manifest), store)
        holes = resolve_edges.read_edge_holes(resolve_edges.default_edge_store(manifest))
    assert reason is None and edges and {edge["language"] for edge in edges} == {"stylesheet"}
    assert holes and {hole["language"] for hole in holes} == {"stylesheet"}
    assert any(edge["symbol"] == "src/styles/base.css" and edge["kind"] == "import" for edge in edges)


def test_an_engine_that_cannot_run_leaves_the_entry_unavailable(project):
    root, manifest, _runner = project

    def runner(script, payload):
        raise runtime.Unavailable("Node could not be downloaded", "check the network")
    report = stage(root, manifest, runner)
    assert not report["available"] and report["reason"] == "Node could not be downloaded"
    assert report["install"] == "check the network"
    assert not resolve_edges.default_edge_store(manifest).exists()
