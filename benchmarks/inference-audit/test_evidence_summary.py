"""The evidence summary's arithmetic, on example rows (the recorded results are not read here).

    python -B -m pytest -q -p no:cacheprovider benchmarks/inference-audit/test_evidence_summary.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidence_summary as summary  # noqa: E402


def test_cells_count_confirmed_false_arcs_and_holes_and_leave_silent_sides_out():
    cells = {"same project target": 10, "both none": 7, "both external": 5,
             "different project target": 2,
             "mixed: A project-other, B parameter": 3,  # both answered, differ: false
             "mixed: A external, B none": 4,  # the index is silent: not false
             "mixed: A not-asked, B external": 6,  # the second source did not ask: not false
             "only A has a project target": 8, "only B has a project target": 9}
    row = summary.cells_row(cells, {"seconds": 12.8, "peak_rss_mb": 338})
    assert row == {"confirmed": 10, "false": 5, "holes": 8, "seconds": 12.8, "mb": 338}


def test_a_report_sums_uncertain_edges_and_the_count_of_each_hole_group():
    report = {"indexer": {"name": "scip-clang", "seconds": 4.8, "peak_mb": 69},
              "edges_uncertain": {"one symbol defined at several places": 4, "another reason": 1},
              "holes": [{"class": "no-document", "count": 2044}, {"class": "no-occurrence", "count": 237}]}
    assert summary.report_row(report) == {"uncertain": 5, "holes": 2281, "seconds": 4.8, "mb": 69}
    assert summary.report_row({"indexer": {}, "edges_uncertain": {}, "holes": []}) == {
        "uncertain": 0, "holes": 0, "seconds": None, "mb": None}


def test_rows_read_full_scip_files_and_reports_and_skip_the_rest(tmp_path):
    (tmp_path / "scip-x-full.json").write_text(json.dumps({
        "indexers": {"scip-ts": {"seconds": 1.5, "peak_rss_mb": 20}},
        "join": {"languages": {"javascript": {"cells": {"same project target": 2}},
                               "typescript": {"cells": {"different project target": 1}}}}}))
    (tmp_path / "graph-y-checks.json").write_text(json.dumps({"report": {
        "language": "c", "indexer": {"name": "scip-clang", "seconds": 2.0, "peak_mb": 9},
        "edges_uncertain": {"r": 3}, "holes": [{"count": 4}]}}))
    (tmp_path / "scip-x.json").write_text(json.dumps({"indexers": {}, "join": {"languages": {}}}))
    (tmp_path / "graph-y.json").write_text(json.dumps({"language": "c", "holes": [{}] * 9}))
    (tmp_path / "strong-z.json").write_text(json.dumps({"engine": {}}))
    found = summary.rows(tmp_path)
    assert [(r["file"], r["indexer"], r["language"]) for r in found] == [
        ("graph-y-checks.json", "scip-clang", "c"),
        ("scip-x-full.json", "scip-ts", "javascript"),
        ("scip-x-full.json", "scip-ts", "typescript")]
    assert found[0]["uncertain"] == 3 and found[0]["holes"] == 4
    assert (found[1]["confirmed"], found[1]["false"]) == (2, 0)
    assert (found[2]["confirmed"], found[2]["false"]) == (0, 1)
