"""The comparison of an analysis' entries with a reference's flows (plan task 11.5): on made-up data, no reference."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks/project-model"))

import entries_vs_reference as compare  # noqa: E402


def flow(*cites: str, kind="attiva") -> dict:
    return {"name": "F", "arrows": [{"kind": kind, "cite": cite} for cite in cites]}


def test_a_cite_is_covered_by_a_static_entry_near_it_else_by_the_lines_an_observed_handler_spans_else_by_none():
    reference = {"flows": [flow("web/A.tsx:10", "web/B.tsx:40", "web/C.tsx:7", "web/D.tsx:3", "web/E.tsx:1", kind="attiva"),
                           flow("web/F.tsx:9", kind="chiama")]}
    links = {"static_sites": ["web/A.tsx:12", "web/C.tsx:30"],
             "observed_spans": [{"file": "web/B.tsx", "line": 38, "end": 44}, {"file": "web/D.tsx", "line": 5, "end": 9}]}
    seen = compare.compare(reference, links)
    assert (seen["cites"], seen["static"], seen["observed"], seen["none"]) == (5, 1, 1, 3)  # F.tsx is no entry arrow
    assert seen["by_folder"] == {"web": {"static": 1, "observed": 1, "none": 3}}


def test_a_cite_without_a_line_is_left_out():
    seen = compare.compare({"flows": [flow("build.bat", "x/Y.ts:2")]}, {"static_sites": [], "observed_spans": []})
    assert seen["cites"] == 1 and seen["none"] == 1
