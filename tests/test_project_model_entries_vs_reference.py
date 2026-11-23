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
    assert (seen["cites"], seen["static"], seen["observed"], seen["both"], seen["none"]) == (5, 1, 1, 0, 3)  # F.tsx is no entry arrow
    assert seen["by_folder"] == {"web": {"static": 1, "observed": 1, "none": 3}}


def test_a_cite_at_the_line_that_names_an_observed_handler_is_covered_by_it():
    reference = {"flows": [flow("web/Form.tsx:144", "web/Form.tsx:300")]}
    links = {"static_sites": [], "observed_spans": [{"file": "web/Form.tsx", "line": 90, "end": 120}],
             "observed_binding_sites": ["web/Form.tsx:145"]}  # `<form onSubmit={handleSubmit}>` one line from the cite
    seen = compare.compare(reference, links)
    assert (seen["observed"], seen["none"]) == (1, 1)


def test_a_cite_inside_the_function_a_static_entry_starts_from_is_covered_by_it():
    reference = {"flows": [flow("web/Login.tsx:19")]}
    links = {"static_sites": ["web/Login.tsx:64"], "static_spans": [{"file": "web/Login.tsx", "line": 15, "end": 30}],
             "observed_spans": []}  # the binding is at 64; the cite is the call the handler makes
    assert compare.compare(reference, links)["static"] == 1


def test_a_cite_a_static_entry_and_the_browser_both_reach_is_counted_once_as_both():
    reference = {"flows": [flow("web/Nav.tsx:125")]}
    links = {"static_sites": ["web/Nav.tsx:125"], "observed_spans": [{"file": "web/Nav.tsx", "line": 125, "end": 125}]}
    seen = compare.compare(reference, links)
    assert (seen["static"], seen["observed"], seen["both"], seen["none"]) == (0, 0, 1, 0)


def test_a_cite_without_a_line_is_left_out():
    seen = compare.compare({"flows": [flow("build.bat", "x/Y.ts:2")]}, {"static_sites": [], "observed_spans": []})
    assert seen["cites"] == 1 and seen["none"] == 1
