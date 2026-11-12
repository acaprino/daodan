#!/usr/bin/env python3
"""Score a system map against a reference made by hand, and a recognition of externals against a list.

    python score.py map MAP.json EXPECTED.json
    python score.py externals RECOGNIZED.json EXPECTED.json

MAP.json is what `system_map.load` returns, optionally with `refused_arrows` from the
record reports. A reference node is found when a proposed node shares at least half
of the union of their files (Jaccard index); a node without code compares its evidence.
A reference flow is found when one proposed flow holds two thirds of its nodes, as
matched. Names never count: the project confirms names, the score only shapes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _files(node: dict) -> set[str]:
    return set(node.get("files") or []) | {e.split("#")[0] for e in node.get("evidence") or []}


def _jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def score_map(proposed: dict, expected: dict) -> dict:
    match = {}
    for node in expected["nodes"]:
        best = max(proposed["nodes"], key=lambda n: _jaccard(_files(n), _files(node)), default=None)
        if best is not None and _jaccard(_files(best), _files(node)) >= 0.5:
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


def score_externals(recognized: dict, expected: dict) -> dict:
    found = {e["id"] for e in recognized["externals"]}
    wanted = set(expected["externals"])
    return {"recall": round(len(found & wanted) / len(wanted), 3) if wanted else 0.0, "found": sorted(found & wanted),
            "missed": sorted(wanted - found), "wrong": sorted(found - wanted)}


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] not in ("map", "externals"):
        print(__doc__)
        return 2
    first, second = (json.loads(Path(p).read_text(encoding="utf-8")) for p in argv[1:])
    print(json.dumps((score_map if argv[0] == "map" else score_externals)(first, second), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
