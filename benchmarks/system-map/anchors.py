"""Flows built by code from anchors: what lies on a path from the start anchors to the end anchors.

The model names a flow and gives its anchors (entry points, store keys); the code takes every symbol that
a start anchor reaches and that reaches an end anchor, following calls, activations, writes and reads
(a reader reaches the key it reads). Symbols become files, files become the reference's nodes.

    python anchors.py LINKS.json EXPECTED.json ANCHORS.json
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path


def touches(links: dict) -> dict[str, set[str]]:
    out = collections.defaultdict(set)
    for edge in links["edges"]:
        if edge["type"] == "legge":  # the reader reaches what it reads
            out[edge["to"]].add(edge["from"])
        else:
            out[edge["from"]].add(edge["to"])
    return out


def reach(graph: dict[str, set[str]], starts: set[str]) -> set[str]:
    seen, stack = set(starts), list(starts)
    while stack:
        for nxt in graph.get(stack.pop(), ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def between(links: dict, starts: set[str], ends: set[str]) -> tuple[set[str], set[str], dict[str, set[str]]]:
    """Symbols on some path from a start to an end, the ends no start reaches, and for each start that
    reaches no end the files it does reach: where the graph stops."""
    forward = touches(links)
    backward = collections.defaultdict(set)
    for a, targets in forward.items():
        for b in targets:
            backward[b].add(a)
    ahead = reach(forward, starts)
    stuck = {}
    for start in starts:
        alone = reach(forward, {start})
        if not alone & ends:
            stuck[start] = {place(s) for s in alone} - {place(start)}
    return ahead & reach(backward, ends), ends - ahead, stuck


def place(end: str) -> str:
    return end if end.startswith("store:") else end.split("::")[0]


def main(argv: list[str]) -> int:
    links, expected, anchors = (json.loads(Path(p).read_text(encoding="utf-8")) for p in argv)
    owner = {}
    for node in expected["nodes"]:
        for member in (node.get("files") or []) + (node.get("members") or []):
            owner[member] = node["name"]
    by_name = {f["name"]: f for f in expected["flows"]}
    for flow in anchors["flows"]:
        on_path, missed, stuck = between(links, set(flow["from"]), set(flow["to"]))
        files = {place(s) for s in on_path}
        nodes = collections.Counter(owner.get(f, "(outside the reference)") for f in files)
        wanted = [n for n in by_name[flow["name"]]["nodes"]
                  if any(owner.get(m) == n for m in owner) and not n.startswith(("Utente", "Landing"))]
        with_code = [n for n in wanted if any(o == n for o in owner.values())]
        print(f"== {flow['name']}: {len(on_path)} symbols, {len(files)} files or keys on a path")
        print("   reference nodes with code reached:", sorted(n for n in with_code if n in nodes),
              "| not reached:", sorted(n for n in with_code if n not in nodes))
        print("   files per node:", dict(sorted(nodes.items())))
        print("   end anchors no start reaches:", sorted(missed))
        for start, reached in sorted(stuck.items()):
            print(f"   start that reaches no end: {start.split('/')[-1]}; the graph stops after",
                  sorted(r.split("/")[-1] for r in reached))
        outside = sorted(f.split("/")[-1] for f in files if f not in owner)
        print(f"   outside the reference ({len(outside)}):", ", ".join(outside[:40]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
