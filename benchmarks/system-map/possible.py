#!/usr/bin/env python3
"""Of the arrows and entries a reference holds, those the certain links prove and those only a possible link gives.

    python possible.py MANIFEST LINKS.json EXPECTED-system.json [--generators ritorno,incerto]

No model. LINKS.json is `flows.py links` on the snapshot of MANIFEST, with the current schema; EXPECTED is a
whole-system reference (README, «Collegamenti possibili»). A possible link is one the machine could propose from
the links alone and does not assert, named by its generator (`--generators ""` measures the certain links alone):

- `ritorno`: a service of others calls a route of the project. A route of an `offre` rule that no call of the
  project reaches, not even as a candidate, in a file that uses an external module (its `usa` links), is called by
  that module. A route a reader found (Noir) has no offer to join a call to: it is counted apart, never a return.
- `incerto`: a call whose route meets several handlers goes to each of them.

An arrow between nodes with code is checked by `system_map.verify`, once with the certain links and once with the
possible ones added. An arrow from or to a service of others, and an entry of a flow on one, are checked here, on
the symbols each node holds: from the module to the node for an incoming arrow or an entry; from the node to the
module for an outgoing one, where a `usa` link of a symbol that only receives the service's call does not count.
Each arrow and entry lands in one bucket:

- `certo`, `possibile:<generator>`;
- `mancante con lacuna` (a gap of the links sits in a file of the arrow's first node with code), `mancante`;
- `con collegamento incerto`: the certain links hold one, but it is conflicting or sampled;
- `non misurabile`: an end with code that verify refused;
- `dichiarata`: an end that is a person or a device, two services of others, or `stessa informazione`;
- `non visto`: an end outside the snapshot;
- `senza modulo`: a service of others no external module of the links stands for, so no generator can reach it.

`services` says which modules stand for each service: by name or registry id, else by an evidence file no other
service of the reference cites, and only when the evidence gives that module to no other service. `reachability` says, before and with the possible links, whether every effect of
the flow is reached from an entry along arrows that stand (`certo`, `dichiarata`, `non visto`, then `possibile`).
Per generator, `outside_reference` counts the possible links that lie on no arrow or entry of the reference, whatever
its bucket: they may be links the reference lacks, not wrong ones; `inside_node` those between two symbols of one
node, which no arrow can express.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "daodan" / "core"))
import flows  # noqa: E402
import modules  # noqa: E402
import system_map  # noqa: E402

GENERATORS = ("ritorno", "incerto")
STANDING = {"certo", "dichiarata", "non visto"}
# A reference cites evidence as `path`, `path:line` or `path#heading` (reference-brief.md): a citation, not code.
CITED_FILE = re.compile(r"(?:#.*|:\d+)$")


def _file(end: str) -> str:
    return end.partition("::")[0]


def _edge(source: str, target: str, site: str, generator: str) -> dict:
    return {"from": source, "to": target, "type": "chiama", "site": site, "origin": f"possibile:{generator}"}


def _receivers(links: dict) -> tuple[list[tuple[str, str]], int]:
    """Routes of an `offre` rule no call reaches, even as a candidate, with their site; the reader routes counted."""
    called = {edge["to"] for edge in links["edges"] if edge.get("route")}
    called |= {target for gap in links["gaps"] for target in gap.get("candidates", ())}
    routes = [entry for entry in links["entries"] if entry["kind"] == "rotta"]
    found = [entry for entry in routes if entry.get("reader")]
    uncalled = {entry["symbol"]: entry["site"] for entry in routes if not entry.get("reader") and entry["symbol"] not in called}
    return sorted(uncalled.items()), len(found)


def possible(links: dict, generators=GENERATORS) -> list[dict]:
    """The possible links of each generator, read from the links alone, once each."""
    out = []
    if "ritorno" in generators:
        used = defaultdict(set)
        for edge in links["edges"]:
            if edge["type"] == "usa":
                used[_file(edge["from"])].add(edge["to"])
        out += [_edge(module, symbol, site, "ritorno")
                for symbol, site in _receivers(links)[0] for module in sorted(used[_file(symbol)])]
    if "incerto" in generators:
        out += [_edge(gap["symbol"], target, gap["site"], "incerto")
                for gap in links["gaps"] if gap.get("symbol") for target in gap.get("candidates", ())]
    return list({(e["from"], e["to"]): e for e in out}.values())


def _cited(evidence) -> list[str]:
    return [CITED_FILE.sub("", item) for item in evidence or []]


def _as_map(expected: dict) -> dict:
    """The reference as `system_map.validate` takes it, with only what the proof of an arrow reads: `on`, `inside`
    and the fields of a service would refuse nodes for reasons the links do not judge."""
    nodes = [{"name": n["name"], "type": n["type"], "position": n.get("position", "internal"),
              "members": n.get("members") or [], "evidence": _cited(n.get("evidence")),
              **({"where": n["where"]} if n.get("where") else {})} for n in expected["nodes"]]
    flow_list = []
    for flow in expected["flows"]:
        ends = {field: list(dict.fromkeys(item["node"] for item in flow.get(field) or [])) for field in ("entries", "effects")}
        arrows = [{"from": a["from"], "to": a["to"], "data": "-", **{k: a[k] for k in ("kind", "cite") if k in a}}
                  for a in flow.get("arrows", [])]
        flow_list.append({"name": flow["name"], "area": system_map.AREAS[0], "types": ["funzionale"],
                          "nodes": flow["nodes"], "arrows": arrows, **(ends if all(ends.values()) else {})})
    return {"nodes": nodes, "flows": flow_list, "areas": [{"name": a, "present": True} for a in system_map.AREAS]}


def _module_sites(links: dict) -> dict[str, set[str]]:
    """Per external module of the links, the files it cites as evidence: the sites of its `usa` links."""
    sites = defaultdict(set)
    for edge in links["edges"]:
        if edge["type"] == "usa":
            sites[edge["to"]].add(edge["site"])
    return sites


def _modules(node: dict, sites: dict[str, set[str]], shared: set[str]) -> tuple[set[str], bool]:
    """The modules that stand for a service of others, and whether by name: same name or registry id; when none has
    it, those citing a file or folder of the node's evidence that no other service of the reference cites."""
    names = {modules.slug(n) for n in (node.get("name"), node.get("registry")) if n}
    named = {m for m in sites if modules.slug(m[7:]) in names}
    own = [c.rstrip("/") for c in _cited(node.get("evidence")) if c not in shared]
    return named or {m for m, files in sites.items() if any(f == c or f.startswith(c + "/") for f in files for c in own)}, bool(named)


def _reaches(arrows: list[tuple[str, str]], entries: set[str], effects: set[str]) -> str:
    seen, stack = set(entries), list(entries)
    while stack:
        node = stack.pop()
        for a, b in arrows:
            if a == node and b not in seen:
                seen.add(b)
                stack.append(b)
    return "verified" if entries and effects and effects <= seen else "unproved"


def measure(manifest: Path, links: dict, expected: dict, generators=GENERATORS) -> dict:
    if links.get("schema") != flows.LINKS_SCHEMA:
        raise ValueError(f"links schema {links.get('schema')}, expected {flows.LINKS_SCHEMA}: run flows.py links again")
    extra = possible(links, generators)
    nodes_in, records = system_map._by_key(system_map.validate(_as_map(expected)))
    headers = system_map._headers(manifest)
    certain, items = system_map._verify(manifest, links, nodes_in, records, headers)
    widened, _ = system_map._verify(manifest, {**links, "edges": links["edges"] + extra}, nodes_in, records, headers)
    nodes = {system_map.key(n["name"]): n for n in expected["nodes"]}
    accepted = {k for k, item in items.items() if item["report"]["status"] == "accepted"}
    gap_files = {system_map._site_file(gap["site"]) for gap in links["gaps"]}
    receivers = {symbol for symbol, _ in _receivers(links)[0]}
    sites = _module_sites(links)

    def outside(node: dict) -> bool:
        return node.get("position", "internal") != "internal"

    def service(node: dict) -> bool:
        return node.get("position") == "external" and node.get("type") not in system_map.NOT_SERVICES

    cites = Counter(c.rstrip("/") for n in expected["nodes"] if service(n) for c in set(_cited(n.get("evidence"))))
    shared = {c for c, n in cites.items() if n > 1}
    matched = {system_map.key(n["name"]): _modules(n, sites, shared) for n in expected["nodes"] if service(n)}
    by_evidence = Counter(m for found, named in matched.values() if not named for m in found)
    # A module the evidence gives to two services stands for neither: which one it binds is not in the links.
    stands = {k: found if named else {m for m in found if by_evidence[m] == 1} for k, (found, named) in matched.items()}

    def owns(k: str, end: str) -> bool:
        return k in accepted and system_map._owns(items[k], end)

    def missing(first: str) -> str:
        return "mancante con lacuna" if first in accepted and set(items[first]["report"]["files"]) & gap_files else "mancante"

    def across(into: set[str], out_of: set[str], holders: list[str], first: str | None) -> str:
        """A service's link into the holders' symbols (`into`), or from their symbols out to it (`out_of`)."""
        if not (into or out_of):
            return "senza modulo"
        if not any(k in accepted for k in holders):
            return "non misurabile"
        for edges, bucket in ((links["edges"], "certo"), (extra, None)):
            found = [e for e in edges if (e["from"] in into and any(owns(k, e["to"]) for k in holders))
                     or (e["to"] in out_of and e["from"] not in receivers and any(owns(k, e["from"]) for k in holders))]
            if found:
                return bucket or "possibile:" + "+".join(sorted({e["origin"][10:] for e in found}))
        return missing(first) if first else "mancante"

    served, totals, out = set(), {"arrows": Counter(), "entries": Counter()}, []
    for flow, before, after in zip(expected["flows"], certain["flows"], widened["flows"]):
        arrows, entries, lost, standing = Counter(), Counter(), [], {"before": [], "after": []}
        for arrow, first, second in zip(flow.get("arrows", []), before["arrows"], after["arrows"]):
            ka, kb = system_map.key(arrow["from"]), system_map.key(arrow["to"])
            a, b = nodes[ka], nodes[kb]
            for e in extra:  # a possible link along this arrow serves it, whatever the bucket
                if ((owns(ka, e["from"]) or e["from"] in stands.get(ka, ())) and owns(kb, e["to"])) \
                        or (owns(ka, e["from"]) and e["to"] in stands.get(kb, ())):
                    served.add((e["from"], e["to"]))
            if any(n.get("position") == "unseen" for n in (a, b)):
                bucket = "non visto"
            elif (any(outside(n) and not service(n) for n in (a, b)) or (service(a) and service(b))
                  or arrow.get("kind") == "stessa informazione"):
                bucket = "dichiarata"
            elif service(a):
                bucket = across(stands[ka], set(), [kb], None)
            elif service(b):
                bucket = across(set(), stands[kb], [ka], ka)
            elif first["status"] == "proved":
                bucket = "certo"
            elif first.get("reason", "").startswith("nodes refused"):
                bucket = "non misurabile"
            elif second["status"] == "proved":
                bucket = "possibile:" + "+".join(sorted({p["origin"][10:] for p in second["proof"]
                                                         if p.get("origin", "").startswith("possibile:")}))
            elif first.get("proof"):
                bucket = "con collegamento incerto"
            else:
                bucket = missing(ka)
            arrows[bucket] += 1
            if bucket.startswith("mancante"):
                lost.append(f"{arrow['from']} -> {arrow['to']}")
            for when in ("before", "after"):
                if bucket in STANDING or (when == "after" and bucket.startswith("possibile:")):
                    standing[when].append((ka, kb))
        inner = [system_map.key(n) for n in flow["nodes"] if not outside(nodes[system_map.key(n)])]
        for item in flow.get("entries") or []:
            k = system_map.key(item["node"])
            if nodes[k].get("position") == "unseen":
                entries["non visto"] += 1
            elif service(nodes[k]):
                served.update((e["from"], e["to"]) for e in extra
                              if e["from"] in stands[k] and any(owns(i, e["to"]) for i in inner))
                bucket = across(stands[k], set(), inner, None)
                entries[bucket] += 1
                if bucket.startswith("mancante"):
                    lost.append(f"ingresso da {item['node']}")
        starts = {system_map.key(i["node"]) for i in flow.get("entries") or []}
        ends = {system_map.key(i["node"]) for i in flow.get("effects") or []}
        totals["arrows"].update(arrows)
        totals["entries"].update(entries)
        out.append({"name": flow["name"], "arrows": dict(arrows), "entries_from_others": dict(entries),
                    "reachability": [_reaches(standing[w], starts, ends) for w in ("before", "after")], "missing": lost})
    within = {(e["from"], e["to"]) for e in extra if any(owns(k, e["from"]) and owns(k, e["to"]) for k in accepted)}
    by_generator = {}
    for g in generators:
        mine = [(e["from"], e["to"]) for e in extra if e["origin"] == f"possibile:{g}"]
        by_generator[g] = {"links": len(mine), "inside_node": sum(p in within for p in mine),
                           "outside_reference": sum(p not in served and p not in within for p in mine)}
    return {"possible": by_generator, "reader_routes_apart": _receivers(links)[1],
            "services": {nodes[k]["name"]: sorted(m) for k, m in stands.items()},
            "arrows": dict(totals["arrows"]), "entries_from_others": dict(totals["entries"]), "flows": out}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("links", type=Path)
    parser.add_argument("expected", type=Path)
    parser.add_argument("--generators", default=",".join(GENERATORS),
                        help="comma-separated, among " + ", ".join(GENERATORS) + "; empty for the certain links alone")
    args = parser.parse_args(argv)
    chosen = tuple(g for g in args.generators.split(",") if g)
    if set(chosen) - set(GENERATORS):
        parser.error(f"--generators: {', '.join(sorted(set(chosen) - set(GENERATORS)))} is no generator")
    links, expected = (json.loads(p.read_text(encoding="utf-8")) for p in (args.links, args.expected))
    print(json.dumps(measure(args.manifest, links, expected, chosen), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
