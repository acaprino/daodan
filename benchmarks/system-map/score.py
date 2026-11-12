#!/usr/bin/env python3
"""Score a system map against a reference made by hand, and a recognition of externals against a list.

    python score.py map MAP.json EXPECTED.json
    python score.py externals BRIEF.json EXPECTED.json [registry|stack-analyser|both]
    python score.py stable MAP1.json MAP2.json

MAP.json is what `system_map.load` returns, optionally with `refused_arrows` from the
record reports. A reference node with code is found when a proposed node shares at least
half of the union of their files and store keys (Jaccard index). A node without code is
found when a proposed node in the same position cites one of its evidence files; an
unseen node cites none, so a proposed unseen node of the same type finds it.
A reference flow is found when one proposed flow holds two thirds of its nodes, as
matched. Names never count: the project confirms names, the score only shapes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _files(node: dict) -> set[str]:
    return (set(node.get("files") or []) | {e.split("#")[0].split(":")[0] for e in node.get("evidence") or []}
            | {m for m in node.get("members") or [] if m.startswith("store:")})


def _jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def _likeness(proposed: dict, reference: dict) -> float:
    """How well a proposed node stands for a reference node; 0 when it does not."""
    position = reference.get("position", "internal")
    if position == "internal":
        share = _jaccard(_files(proposed), _files(reference))
        return share if share >= 0.5 else 0.0
    if proposed.get("position", "internal") != position:
        return 0.0
    if not (wanted := _files(reference)):
        return 1.0 if proposed.get("type") == reference.get("type") else 0.0
    return len(wanted & _files(proposed)) / len(wanted)


def score_map(proposed: dict, expected: dict) -> dict:
    match = {}
    for node in expected["nodes"]:
        best = max(proposed["nodes"], key=lambda n: _likeness(n, node), default=None)
        if best is not None and _likeness(best, node) > 0:
            match[node["name"]] = best["name"]
    flows_found = []
    for flow in expected["flows"]:
        wanted = [match.get(n) for n in flow["nodes"]]
        if any(sum(1 for n in wanted if n and n in f["nodes"]) * 3 >= len(flow["nodes"]) * 2 for f in proposed["flows"]):
            flows_found.append(flow["name"])
    states = [a["status"] for f in proposed["flows"] for a in f.get("arrows", [])]
    refused = proposed.get("refused_arrows", states.count("refused"))
    total = states.count("proved") + states.count("declared") + refused
    return {"nodes": {"found": len(match), "of": len(expected["nodes"]),
                      "missing": [n["name"] for n in expected["nodes"] if n["name"] not in match]},
            "flows": {"found": len(flows_found), "of": len(expected["flows"]),
                      "missing": [f["name"] for f in expected["flows"] if f["name"] not in flows_found]},
            "arrows": {"proved": states.count("proved"), "declared": states.count("declared"), "refused": refused,
                       "refused_share": round(refused / total, 3) if total else 0.0},
            "coverage": proposed.get("coverage", {})}


def stability(first: dict, second: dict) -> dict:
    """Nodes of two runs that are the same thing, compared as `score_map` compares a reference node."""
    same, taken = 0, set()
    for node in first["nodes"]:
        best = max((n for n in second["nodes"] if n["name"] not in taken), key=lambda n: _likeness(n, node), default=None)
        if best is not None and _likeness(best, node) > 0:
            same += 1
            taken.add(best["name"])
    of = max(len(first["nodes"]), len(second["nodes"]))
    return {"same": same, "of": of, "share": round(same / of, 3) if of else 0.0}


SOURCES = {"registry": {"registry"}, "stack-analyser": {"stack-analyser"}, "both": {"registry", "stack-analyser"}}


def score_externals(recognized: dict, expected: dict, source: str | None = None) -> dict:
    """Recall over the named externals; `also` lists what the project uses unnamed: neither found nor wrong."""
    found = {e["id"] for e in recognized["externals"] if source is None or SOURCES[source] & set(e.get("from", []))}
    wanted, also = set(expected["externals"]), set(expected.get("also", []))
    return {"recall": round(len(found & wanted) / len(wanted), 3) if wanted else 0.0, "found": sorted(found & wanted),
            "missed": sorted(wanted - found), "wrong": sorted(found - wanted - also)}


def main(argv: list[str]) -> int:
    if not (argv[:1] in (["map"], ["stable"]) and len(argv) == 3 or argv[:1] == ["externals"] and len(argv) in (3, 4)
            and argv[3:] in ([], *([s] for s in SOURCES))):
        print(__doc__)
        return 2
    first, second = (json.loads(Path(p).read_text(encoding="utf-8")) for p in argv[1:3])
    result = {"map": score_map, "stable": stability}[argv[0]](first, second) if argv[0] != "externals" \
        else score_externals(first, second, *argv[3:])
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
