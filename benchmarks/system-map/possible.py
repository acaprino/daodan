#!/usr/bin/env python3
"""Of the arrows and entries a reference holds, those the certain links prove and those only a possible link gives.

    python possible.py MANIFEST LINKS.json EXPECTED-system.json

No model. LINKS.json is `flows.py links` on the snapshot of MANIFEST, with the current schema; EXPECTED is a
whole-system reference (README, «Collegamenti possibili»). A possible link is one the machine could propose from
the links alone and does not assert, named by its generator:

- `ritorno`: a service of others calls a route of the project. A route nobody in the project calls, in a file that
  uses an external module (its `usa` links), is called by that module.
- `incerto`: a call whose route meets several handlers goes to each of them.

An arrow between nodes with code is checked by `system_map.verify`, once with the certain links and once with the
possible ones added. An arrow from or to a service of others, and an entry of a flow on one, are checked here,
in their direction: a link from the module to a symbol of a node of the flow, or from a symbol of the node to the
module. Each arrow and entry lands in one bucket: `certo`, `possibile:<generator>`, `mancante con lacuna` (a gap
of the links sits in a file of the arrow's first node), `mancante`, `non misurabile` (an end refused by verify),
`dichiarata` (an end that is a person or a device), `non visto` (an end outside the snapshot), `senza modulo` (a
service of others that no external module of the links stands for: no generator can reach it). `services` says
which modules stand for each service of others. A possible link that serves no arrow or entry of the reference
is counted `fuori dal riferimento`: it may be a link the reference lacks, not a wrong one.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "daodan" / "core"))
import flows  # noqa: E402
import modules  # noqa: E402
import system_map  # noqa: E402

GENERATORS = ("ritorno", "incerto")


def _file(end: str) -> str:
    return end.partition("::")[0]


def _edge(source: str, target: str, site: str, generator: str) -> dict:
    return {"from": source, "to": target, "type": "chiama", "site": site, "origin": f"possibile:{generator}"}


def possible(links: dict, generators=GENERATORS) -> list[dict]:
    """The possible links of each generator, read from the links alone."""
    out = []
    if "ritorno" in generators:
        called = {edge["to"] for edge in links["edges"] if edge.get("route")}
        used = defaultdict(set)
        for edge in links["edges"]:
            if edge["type"] == "usa":
                used[_file(edge["from"])].add(edge["to"])
        for entry in links["entries"]:
            if entry["kind"] == "rotta" and entry["symbol"] not in called:
                out += [_edge(module, entry["symbol"], entry["site"], "ritorno")
                        for module in sorted(used[_file(entry["symbol"])])]
    if "incerto" in generators:
        out += [_edge(gap["symbol"], target, gap["site"], "incerto")
                for gap in links["gaps"] if gap.get("symbol") for target in gap.get("candidates", ())]
    return out


def _as_map(expected: dict) -> dict:
    """The reference in the form `system_map.validate` takes: its fields, entries and effects as node names."""
    nodes = [{k: v for k, v in node.items() if k in system_map._NODE_FIELDS} for node in expected["nodes"]]
    flow_list = []
    for flow in expected["flows"]:
        ends = {field: list(dict.fromkeys(item["node"] for item in flow.get(field) or [])) for field in ("entries", "effects")}
        flow_list.append({"name": flow["name"], "area": system_map.AREAS[0], "types": flow.get("types") or ["funzionale"],
                          "nodes": flow["nodes"], "arrows": [{k: v for k, v in a.items() if k in system_map._ARROW_FIELDS}
                                                             for a in flow.get("arrows", [])],
                          **(ends if all(ends.values()) else {})})
    return {"nodes": nodes, "flows": flow_list, "areas": [{"name": a, "present": True} for a in system_map.AREAS]}


def _modules(node: dict, links: dict) -> set[str]:
    """The external modules of the links that stand for a node of others: same name or registry id; when none has
    it, those that cite as evidence (the sites of their `usa` links) a file of the node's evidence."""
    names = {modules.slug(n) for n in (node.get("name"), node.get("registry")) if n}
    sites = defaultdict(set)
    for edge in links["edges"]:
        if edge["type"] == "usa":
            sites[edge["to"]].add(edge["site"])
    named = {m for m in sites if modules.slug(m[7:]) in names}
    return named or {m for m in sites if sites[m] & set(node.get("evidence") or [])}


def measure(manifest: Path, links: dict, expected: dict, generators=GENERATORS) -> dict:
    if links.get("schema") != flows.LINKS_SCHEMA:
        raise ValueError(f"links schema {links.get('schema')}, expected {flows.LINKS_SCHEMA}: run flows.py links again")
    extra = possible(links, generators)
    value = system_map.validate(_as_map(expected))
    certain = system_map.verify(manifest, links, value)
    widened = system_map.verify(manifest, {**links, "edges": links["edges"] + extra}, value)
    files = {system_map.key(n["name"]): set(n["files"]) for n in certain["nodes"] if n["status"] == "accepted"}
    nodes = {system_map.key(n["name"]): n for n in expected["nodes"]}
    gap_files = {gap["site"].rpartition(":")[0] for gap in links["gaps"]}  # a gap's symbol can be null, its site not
    services = {n["name"]: sorted(_modules(n, links)) for n in expected["nodes"]
                if n.get("position") == "external" and n.get("type") not in system_map.NOT_SERVICES}
    served, totals, out = set(), {"arrows": Counter(), "entries": Counter()}, []

    def missing(first: str) -> str:
        return "mancante con lacuna" if files.get(first, set()) & gap_files else "mancante"

    def across(source: str | None, target: str | None, holders: set[str]) -> str:
        """An arrow or entry on a service of others: a link from the module into the holders' files, or back."""
        if not (source or target):
            return "senza modulo"
        for edges, bucket in ((links["edges"], "certo"), (extra, None)):
            found = [e for e in edges if (source and e["from"] in source and _file(e["to"]) in holders)
                     or (target and e["to"] in target and _file(e["from"]) in holders)]
            if found:
                served.update((e["from"], e["to"], e["site"]) for e in found if bucket is None)
                return bucket or "possibile:" + "+".join(sorted({e["origin"][10:] for e in found}))
        return "mancante"

    def outside(node: dict) -> bool:
        return node.get("position", "internal") != "internal"

    for flow, before, after in zip(expected["flows"], certain["flows"], widened["flows"]):
        arrows, entries, lost = Counter(), Counter(), []
        for arrow, first, second in zip(flow.get("arrows", []), before["arrows"], after["arrows"]):
            a, b = nodes[system_map.key(arrow["from"])], nodes[system_map.key(arrow["to"])]
            if any(n.get("position") == "unseen" for n in (a, b)):
                bucket = "non visto"
            elif any(outside(n) and n.get("type") in system_map.NOT_SERVICES for n in (a, b)):
                bucket = "dichiarata"
            elif outside(a) or outside(b):
                inner = files.get(system_map.key((b if outside(a) else a)["name"]), set())
                bucket = across(_modules(a, links) if outside(a) else None, _modules(b, links) if outside(b) else None, inner)
            elif first["status"] == "proved":
                bucket = "certo"
            elif first.get("reason", "").startswith("nodes refused"):
                bucket = "non misurabile"
            elif second["status"] == "proved":
                origins = {p.get("origin", "") for p in second["proof"]}
                served.update((p["from"], p["to"], p["site"]) for p in second["proof"] if p.get("origin", "").startswith("possibile:"))
                bucket = "possibile:" + "+".join(sorted(o[10:] for o in origins if o.startswith("possibile:")))
            else:
                bucket = missing(system_map.key(arrow["from"]))
            arrows[bucket] += 1
            if bucket.startswith("mancante"):
                lost.append(f"{arrow['from']} -> {arrow['to']}")
        inner = set().union(*(files.get(system_map.key(n), set()) for n in flow["nodes"]))
        for item in flow.get("entries") or []:
            node = nodes[system_map.key(item["node"])]
            if node.get("position") == "unseen":
                entries["non visto"] += 1
            elif outside(node) and node.get("type") not in system_map.NOT_SERVICES:
                bucket = across(_modules(node, links), None, inner)
                entries[bucket] += 1
                if bucket == "mancante":
                    lost.append(f"ingresso da {item['node']}")
        totals["arrows"].update(arrows)
        totals["entries"].update(entries)
        out.append({"name": flow["name"], "arrows": dict(arrows), "entries_from_others": dict(entries),
                    "reachability": [before["reachability"], after["reachability"]], "missing": lost})
    by_generator = {g: {"links": sum(e["origin"] == f"possibile:{g}" for e in extra),
                        "outside_reference": sum(e["origin"] == f"possibile:{g}" and (e["from"], e["to"], e["site"]) not in served
                                                 for e in extra)} for g in generators}
    return {"possible": by_generator, "services": services, "arrows": dict(totals["arrows"]), "entries_from_others": dict(totals["entries"]),
            "flows": out}


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__)
        return 2
    links, expected = (json.loads(Path(p).read_text(encoding="utf-8")) for p in argv[2:])
    print(json.dumps(measure(Path(argv[1]), links, expected), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
