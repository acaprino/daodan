"""The graph references of the real cases keep their shape, and the checker names a citation that does not hold."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import real_references  # noqa: E402


def test_every_case_has_its_two_references_and_the_graph_keeps_its_shape():
    sources = json.loads((real_references.REAL / "sources.json").read_text(encoding="utf-8"))
    assert real_references.cases() == sorted(sources)
    for case, source in sources.items():
        assert set(source) == {"repo", "commit", "licence", "why"} and len(source["commit"]) == 40, case
        system = json.loads((real_references.REAL.parent / f"{case}-system.json").read_text(encoding="utf-8"))
        assert (system["case"], system["commit"]) == (case, source["commit"])
        assert real_references.shape(case) == []


def test_a_place_that_is_not_in_the_checkout_is_named(tmp_path, monkeypatch):
    (tmp_path / "app").mkdir()
    (tmp_path / "app/main.go").write_text('package main\n\nfunc Home() {}\nrouter.GET("/home", Home)\n', encoding="utf-8")
    graph = {"schema": real_references.GRAPH_SCHEMA, "case": "x", "modules": [], "module_edges": [], "externals": [],
             "routes": [], "external_calls": [], "stores": {"db/t": {"writes": ["app/main.go::Gone"], "reads": []}},
             "config": [], "gaps": [], "entry_points": {"route": [
                 {"module": None, "method": "GET", "path": "/home", "handler": "app/main.go::Home", "at": "app/main.go:4"},
                 {"module": None, "method": "GET", "path": "/away", "handler": "app/missing.go::Home", "at": "app/main.go:4"},
                 {"module": None, "method": "GET", "path": "/home", "handler": "app/main.go::Home", "at": "app/main.go:9"}]}}
    monkeypatch.setattr(real_references, "_load", lambda case: graph)
    assert real_references.shape("x") == []
    assert real_references.cited("x", tmp_path) == [
        "x: app/main.go::Gone: Gone is not written in the file",
        "x: app/missing.go::Home: app/missing.go is not in the checkout",
        "x: app/main.go:9: no such line, or an empty one",
        "x: route /away: line app/main.go:4 does not hold /away"]
