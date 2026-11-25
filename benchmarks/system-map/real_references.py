#!/usr/bin/env python3
"""Check the graph references written by hand for real projects (`expected/real/CASE-graph.json`).

    python real_references.py                 # the shape of every graph reference, no checkout needed
    python real_references.py CASE CHECKOUT   # also every path, symbol and line it cites, in a checkout of the case
                                              # at the commit `expected/real/sources.json` names

A case has two references. The system map (`expected/real/CASE-system.json`) is checked by `reference.py`. The graph
(`daodan/real-graph-expected/v1`) is what the eight steps should give below the map: modules, technologies, entry
points, the routes with their callers, the calls to externals, the stores and the gaps. In a checkout a cited `path`
exists, a `path:line` is a line of that file, the name after `path::` is written in that file, and a route's `at`
line holds its path (or its `literal`, where the framework takes the path from the file's place). Nothing here runs
the project's code.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "daodan/core"))
import system_map  # noqa: E402

REAL = HERE / "expected/real"
GRAPH_SCHEMA = "daodan/real-graph-expected/v1"
GRAPH_FIELDS = {"schema", "case", "modules", "module_edges", "externals", "entry_points", "routes", "external_calls",
                "stores", "config", "gaps"}
# A cited place, on text that has no grammar (a reference's own strings): `path`, `path:line` or `path::Symbol`.
PLACE = re.compile(r"(?P<path>[^:\s]+?)(?::(?P<line>\d+)|::(?P<symbol>\S+))?")
# The fields of a graph whose strings are places; the others are words (a method, a label, a sentence).
PLACES = {"manifest", "root", "declared_in", "at", "caller", "handler", "middleware", "used_by", "template", "in",
          "rendered_by", "symbol", "static", "reads", "writes"}


def cases() -> list[str]:
    """The cases whose graph reference is written."""
    return sorted(c for c in json.loads((REAL / "sources.json").read_text(encoding="utf-8")) if (REAL / f"{c}-graph.json").is_file())


def _load(case: str) -> dict:
    return json.loads((REAL / f"{case}-graph.json").read_text(encoding="utf-8"))


def shape(case: str) -> list[str]:
    """What is wrong in the graph reference of a case without reading its code."""
    graph, problems = _load(case), []
    if graph.get("schema") != GRAPH_SCHEMA or graph.get("case") != case or set(graph) != GRAPH_FIELDS:
        problems.append(f"{case}: schema {GRAPH_SCHEMA}, its case and the fields {', '.join(sorted(GRAPH_FIELDS))}")
    known = system_map._registry_names()
    problems += [f"{case}: {e['registry']} is not an id of the service registry"
                 for e in graph.get("externals", []) if e.get("registry") and e["registry"] not in known]
    names = {m["name"] for m in graph.get("modules", [])}
    problems += [f"{case}: {entry.get('module')} is not a module" for entries in graph.get("entry_points", {}).values()
                 for entry in entries if entry.get("module") is not None and entry["module"] not in names]
    return problems


def _places(value, field: str | None = None):
    """The strings of a graph that are places: those under a field of `PLACES`, at any depth below it."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _places(item, key if key in PLACES else field if key in ("writes", "reads") else None)
    elif isinstance(value, list):
        for item in value:
            yield from _places(item, field)
    elif isinstance(value, str) and field:
        yield value


def _place_problem(place: str, checkout: Path) -> str | None:
    found = PLACE.fullmatch(place)
    if not found:
        return f"{place}: not a path, a path:line or a path::Symbol"
    target = checkout / found["path"]
    if not target.exists():
        return f"{place}: {found['path']} is not in the checkout"
    if found["line"] or found["symbol"]:
        if not target.is_file():
            return f"{place}: {found['path']} is not a file"
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        if found["line"] and not (0 < int(found["line"]) <= len(lines) and lines[int(found["line"]) - 1].strip()):
            return f"{place}: no such line, or an empty one"
        if found["symbol"] and not any(found["symbol"].rsplit(".", 1)[-1] in line for line in lines):
            return f"{place}: {found['symbol']} is not written in the file"
    return None


def cited(case: str, checkout: Path) -> list[str]:
    """What the graph reference of a case cites that a checkout of the case does not hold."""
    graph = _load(case)
    problems = [f"{case}: {p}" for p in (_place_problem(place, checkout) for place in _places(graph)) if p]
    for route in graph["entry_points"].get("route", []):
        path, at = route["path"].split("*")[0].rstrip("/") or "/", PLACE.fullmatch(route["at"])
        if at and at["line"] and (checkout / at["path"]).is_file():
            lines = (checkout / at["path"]).read_text(encoding="utf-8", errors="replace").splitlines()
            if int(at["line"]) <= len(lines) and route.get("literal", path) not in lines[int(at["line"]) - 1]:
                problems.append(f"{case}: route {route['path']}: line {route['at']} does not hold {route.get('literal', path)}")
    return problems


def main(argv: list[str]) -> int:
    problems = [p for case in cases() for p in shape(case)] if not argv else shape(argv[0]) + cited(argv[0], Path(argv[1]))
    print("\n".join(problems) or "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
