#!/usr/bin/env python3
"""For each flow of a whole-system reference, whether a product path card proves it and, if not, why: a hole of the
graph or a limit of the card format, told apart before any model is paid.

    python card_ceiling.py MANIFEST LINKS.json EXPECTED-system.json

No model. LINKS.json is `flows.py links` on the snapshot of MANIFEST, with the current schema; EXPECTED is a
whole-system reference.

- An entry node is an entry of the flow that is internal and accepted by `system_map.verify`; for an entry that is not
  internal (a person, a device, a service of others, an unseen node), the internal accepted nodes its arrows lead to.
  A refused internal node gives none.
- A card is at the entry when an entry node holds its handler or the file of its binding site (`cards_by_site_only`
  counts those matched by the site alone).
- A store effect is an effect node of the flow that holds a `store:` key, the only effect a card has. A card proves it
  with an `effetto` step (a write into a `store:` key) that the node holds, unless the card is uncertain
  (`edge_view.uncertainty`: a sampled handler). `effects_proved` is [proved, store effects].

A flow lands in the first bucket that applies:

- `provata`: it has a store effect and a card at the entry proves each of them;
- `effetto non esprimibile`: it has no store effect;
- `nessuna scheda all'ingresso`: no card is at the entry;
- `tagliata dalla scheda`: the links from the handlers of the cards at the entry reach every store effect not proved,
  so the card dropped them;
- `buco del grafo`: they do not reach some store effect not proved.

That walk follows every link type but `attiva`, whatever its certainty; a link leaving a `store:` key (a read) only when
a node of the flow holds that key. A row with no card at the entry says in `detail` whether no entry node has code or no
card is there, whatever its bucket. A `provata` row says how much a model reads before it meets the last proof it needs:
the fields of the store effect whose earliest step is the longest read, and `cards_needed`, the distinct cards the proofs
come from. Effects are counted once per flow that names them.

The count is not comparable as a total with the `reachability` of `possible.py`: that walks the reference's arrows from
node to node and needs every effect, screens included; this follows the links from a card's handler and needs every
store effect.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "daodan" / "core"))
from edge_view import uncertainty  # noqa: E402
import flow_paths  # noqa: E402
import flows  # noqa: E402
import possible  # noqa: E402
import system_map  # noqa: E402

BUCKETS = ("provata", "effetto non esprimibile", "nessuna scheda all'ingresso", "tagliata dalla scheda", "buco del grafo")
key = system_map.key


def _depth(steps: list[dict], n: int) -> int:
    """Steps on the parent chain from the handler to step `n`, both included."""
    depth = 0
    while n:
        depth, n = depth + 1, steps[n - 1]["parent"]
    return depth


def measure(manifest: Path, links: dict, expected: dict) -> dict:
    if links.get("schema") != flows.LINKS_SCHEMA:
        raise ValueError(f"links schema {links.get('schema')}, expected {flows.LINKS_SCHEMA}: run flows.py links again")
    nodes_in, records = system_map._by_key(system_map.validate(possible._as_map(expected)))
    _, items = system_map._verify(manifest, links, nodes_in, records, system_map._headers(manifest))
    nodes = {key(n["name"]): n for n in expected["nodes"]}
    code = {k for k, item in items.items()
            if item["report"]["status"] == "accepted" and nodes[k].get("position", "internal") == "internal"}
    graph = flow_paths._build_graph(links)
    cards = flow_paths._inventory(links, graph)
    steps = {ident: flow_paths._steps(graph, card) for ident, card in cards.items()}
    onward, readers = defaultdict(set), defaultdict(set)  # a read leaves its store for the reader, and joins two writers
    for edge in links["edges"]:
        if edge["type"] != "attiva":
            (readers if edge["from"].startswith("store:") else onward)[edge["from"]].add(edge["to"])

    def owns(holders: set[str], end: str) -> bool:
        return any(system_map._owns(items[k], end) for k in holders)

    def reading(n: int, ident: str) -> int:
        return sum(len(json.dumps(step)) + 2 for step in steps[ident][:n])

    rows = []
    for flow in expected["flows"]:
        arrows = flow.get("arrows", [])
        entry_nodes = set()
        for item in flow.get("entries") or []:
            k = key(item["node"])
            if k in code:
                entry_nodes.add(k)
            elif nodes[k].get("position", "internal") != "internal":
                entry_nodes |= {t for t in (key(a["to"]) for a in arrows if key(a["from"]) == k) if t in code}
        by_handler = {ident for ident, card in cards.items() if owns(entry_nodes, card["handler"])}
        at_entry = [ident for ident, card in cards.items()
                    if ident in by_handler or owns(entry_nodes, system_map._site_file(card["site"]))]
        effects = [{"node": item["node"], "kind": item.get("kind"),
                    "expressible": any(o.startswith("store:") for o in items[key(item["node"])]["others"])}
                   for item in flow.get("effects") or []]
        holders = {key(e["node"]) for e in effects if e["expressible"]}
        best = {}  # per store effect, the earliest step of a certain card at the entry that writes into it
        for holder in holders:
            found = [(step["n"], ident) for ident in at_entry if not uncertainty(cards[ident]) for step in steps[ident]
                     if step["end"] == "effetto" and owns({holder}, step["to"])]
            if found:
                best[holder] = min(found, key=lambda proof: proof[0])
        row = {"name": flow["name"], "cards_at_entry": len(at_entry), "cards_by_site_only": len(at_entry) - len(by_handler),
               "effects": effects, "effects_proved": [len(best), len(holders)]}
        if not at_entry:
            row["detail"] = "no card at the entry" if entry_nodes else "no entry node with code"
        if holders and len(best) == len(holders):
            n, ident = max(best.values(), key=lambda proof: reading(*proof))
            row |= {"bucket": "provata", "card_id": ident, "steps": len(steps[ident]), "effect_n": n,
                    "depth": _depth(steps[ident], n), "bytes_to_effect": reading(n, ident),
                    "cards_needed": len({ident for _, ident in best.values()})}
        elif not holders:
            row["bucket"] = "effetto non esprimibile"
        elif not at_entry:
            row["bucket"] = "nessuna scheda all'ingresso"
        else:
            flow_nodes = {key(n) for n in flow["nodes"]}
            adjacent = defaultdict(set, {**onward, **{s: readers[s] for s in readers if owns(flow_nodes, s)}})
            reached = system_map._reachable({cards[i]["handler"] for i in at_entry}, adjacent)
            cut = all(any(end.startswith("store:") and owns({h}, end) for end in reached) for h in holders - set(best))
            row["bucket"] = "tagliata dalla scheda" if cut else "buco del grafo"
        rows.append(row)
    counted = Counter(row["bucket"] for row in rows)
    every = [effect for row in rows for effect in row["effects"]]
    sizes = [len(path) for path in steps.values()]
    return {"flows": {bucket: counted[bucket] for bucket in BUCKETS},
            "effects": {"expressible": sum(e["expressible"] for e in every),
                        "not_expressible": dict(Counter(e["kind"] or "-" for e in every if not e["expressible"]))},
            "deck": {"cards": len(cards), "with_effect": sum(any(s["end"] == "effetto" for s in path) for path in steps.values()),
                     "steps_median": statistics.median(sizes or [0]), "steps_max": max(sizes, default=0)},
            "per_flow": rows}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("links", type=Path)
    parser.add_argument("expected", type=Path)
    args = parser.parse_args(argv)
    links, expected = (json.loads(p.read_text(encoding="utf-8")) for p in (args.links, args.expected))
    print(json.dumps(measure(args.manifest, links, expected), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
