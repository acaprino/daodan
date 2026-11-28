"""view_scale.py of benchmarks/codebase-explorer: the archive and the views it measures are the ones it says."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "benchmarks/codebase-explorer/view_scale.py"
spec = importlib.util.spec_from_file_location("view_scale", SCRIPT)
view_scale = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view_scale)
app_view = view_scale.app_view


@pytest.fixture(scope="module")
def envelope():
    return view_scale.envelope()


def test_the_archive_holds_80000_entities_and_the_first_graph_300_nodes(envelope):
    assert len(envelope["entities"]) >= 80_000
    assert len(app_view.view(envelope)["nodes"]) == 300


def test_the_wide_group_opens_in_blocks_that_add_up_to_its_files(envelope):
    first = app_view.view(envelope, (view_scale.WIDE_GROUP,))
    inside = [node for node in first["nodes"] if node["group"] == view_scale.WIDE_GROUP]
    more = [node for node in inside if node["kind"] == "more"]
    assert len(inside) == app_view.BLOCK + 1 and [node["name"] for node in more] == [
        f"altri {view_scale.WIDE - app_view.BLOCK}"]
    groups, natures, mode = view_scale.CASES["blocco «altri N»"]
    second = app_view.view(envelope, groups, natures=natures, mode=mode)
    files = [node for node in second["nodes"] if node["kind"] == "file" and node["group"] == view_scale.WIDE_GROUP]
    assert len(files) == view_scale.WIDE and not any(node["kind"] == "more" for node in second["nodes"])


def test_the_filters_keep_or_dim_the_other_natures(envelope):
    hidden = app_view.view(envelope, (), natures=["logico"], mode="hide")
    lit = app_view.view(envelope, (), natures=["logico"], mode="highlight")
    assert hidden["nodes"] and all(node["location"] == "external" for node in hidden["nodes"])
    assert len(lit["nodes"]) == 300 and sum(bool(node.get("dim")) for node in lit["nodes"]) == 300 - len(hidden["nodes"])
