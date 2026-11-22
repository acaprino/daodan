from unittest.mock import patch

from test_codebase_map_trace_cards import edge, traces


def test_write_coverage_distinguishes_writers_and_reopens_pages_on_the_same_snapshot(tmp_path):
    root = "ui.py::save"
    links = {"entries": [{"symbol": root, "site": "ui.py:1", "kind": "azione"}], "gaps": [], "edges": [
        edge(root, "job.py::save"), edge("job.py::save", "store:db/orders", "scrive", 2),
        edge("job.py::other", "store:db/orders", "scrive", 4),  # same key, no call
        edge(root, "job.py::sample", confidence="sampled"), edge("job.py::sample", "job.py::flush"),
        edge("job.py::flush", "store:db/orders", "scrive", 5),
        edge(root, "job.py::diverged", conflict=True), edge("job.py::diverged", "store:db/status", "scrive", 6),
        edge("job.py::save", "store:db/orders", "scrive", 2),  # duplicate evidence at one site
        edge("job.py::save", "store:db/orders", "scrive", 7),  # a distinct write at a second site
    ]}
    manifest = tmp_path / "manifest.sqlite"
    with patch.object(traces.flows, "cached_links", return_value=("snap1", links)):
        page = traces.orphan_effects(manifest, [], limit=1)
        assert (page["writes"], page["reached"], page["without_entry"], page["count"], page["next_offset"]) == (5, 2, 3, 3, 1)
        with patch.object(traces, "_write_coverage", side_effect=AssertionError("repeat traversal")):
            rest = traces.orphan_effects(manifest, [], offset=page["next_offset"], limit=10)
            assert rest["next_offset"] is None
            counts = traces.next_question(manifest, [])["effect_coverage"]
        assert counts == {"writes": 5, "reached": 2, "without_entry": 3}
    rows = {r["writer"]: r for r in page["effects"] + rest["effects"]}
    assert set(rows) == {"job.py::other", "job.py::flush", "job.py::diverged"}
    assert rows["job.py::other"]["site"] == "a.py:4" and rows["job.py::other"]["effect"] == "store:db/orders"
    assert "sampled" in rows["job.py::flush"]["reason"] and "conflict" in rows["job.py::diverged"]["reason"]
    links["edges"].append(edge(root, "job.py::other"))
    with patch.object(traces.flows, "cached_links", return_value=("snap2", links)):
        assert traces.orphan_effects(manifest, [])["reached"] == 3
