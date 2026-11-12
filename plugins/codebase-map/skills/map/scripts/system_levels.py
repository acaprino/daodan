#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Levels of a flow of the system map: one flow, seen from persone, funzioni, dati, codice, infrastruttura.

Each level shows only its node types. An arrow between two shown nodes contracts a
path whose middle nodes are hidden: it stays declared when a step is declared and
keeps the proof of every step. A path enters and leaves an entity on the same
representation; when it does not, or a step is refused, it is a gap, never an arrow.
At `infrastruttura` a node is put on what it runs on; at `codice` a node becomes the
files of its members that the flow's links touch, never single symbols.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import system_map  # noqa: E402

LEVELS = ("persone", "funzioni", "dati", "codice", "infrastruttura")
_HOME = {"attore": "persone", "schermata": "persone", "entità": "dati", "database": "infrastruttura",
         "dispositivo": "infrastruttura"}
MAX_PATHS = 2000


def levels_of(node: dict) -> list[str]:
    """The levels a node is shown at: its home one, and `infrastruttura` for an external service."""
    home = _HOME.get(node["type"], "funzioni")
    return [home, "infrastruttura"] if node["position"] == "external" and home == "funzioni" else [home]


def _find(records: list[dict], name: str, what: str) -> dict:
    found = next((r for r in records if r["id"] == name or system_map.key(r["name"]) == system_map.key(name)), None)
    if found is None:
        raise ValueError(f"no {what} is called {name}")
    return found


def _item(node: dict) -> dict:
    """A node's members as `system_map._owns` reads them."""
    symbols = {tuple(m.split("::", 1)) for m in node["members"] if "::" in m and not m.startswith("store:")}
    others = {m for m in node["members"] if m.startswith("store:")}
    others |= {"module:" + system_map.modules.slug(m[7:]) for m in node["members"] if m.startswith("module:")}
    whole = set(node["files"]) - ({p for p, _ in symbols} - set(node["members"]))
    return {"whole": whole, "symbols": symbols, "others": others}


def _contract(visible: set[str], steps: list[dict], entities: set[str]) -> tuple[list[dict], list[dict]]:
    """Arrows between shown nodes through hidden ones, and the gaps where a path does not hold."""
    leaving = defaultdict(list)
    for step in steps:
        leaving[step["from"]].append(step)
    arrows, gaps, budget = {}, {}, MAX_PATHS
    for start in sorted(visible):
        stack = [(start, [], {start})]
        while stack and budget:
            node, path, seen = stack.pop()
            for step in leaving.get(node, []):
                if step["to"] in seen or not budget:
                    continue
                budget -= 1
                taken = path + [step]
                if step["to"] in visible:
                    _close(start, step["to"], taken, entities, arrows, gaps)
                else:
                    stack.append((step["to"], taken, seen | {step["to"]}))
    out = []
    for arrow in arrows.values():
        out.append({**arrow, "data": "; ".join(dict.fromkeys(d for d in arrow["data"] if d)),
                    "asserts": [k for k in system_map.ARROW_KINDS if k in arrow["asserts"]],
                    "via": sorted(arrow["via"]), "proof": list({tuple(p.values()): p for p in arrow["proof"]}.values()),
                    "through": list(dict.fromkeys(arrow["through"]))})
    order = lambda r: (r["from"], r["to"], r.get("status", ""), r.get("reason", ""))  # noqa: E731
    return sorted(out, key=order), sorted(gaps.values(), key=order)


def _close(start: str, end: str, taken: list[dict], entities: set[str], arrows: dict, gaps: dict) -> None:
    through = [s["to"] for s in taken[:-1]] + [n for s in taken for n in s["through"]]
    reasons = [f"step {s['from']} -> {s['to']} is refused" for s in taken if s["status"] == "refused"]
    for entering, leaving in zip(taken, taken[1:]):
        if entering["to"] in entities and entering["via"] and leaving["via"] and not set(entering["via"]) & set(leaving["via"]):
            reasons.append(f"{entering['to']}: {', '.join(entering['via'])} is written and {', '.join(leaving['via'])} "
                           "is read, and no link joins the two")
    if reasons:
        gap = {"from": start, "to": end, "reason": "; ".join(reasons), "through": list(dict.fromkeys(through))}
        gaps.setdefault((start, end, gap["reason"]), gap)
        return
    status = "declared" if any(s["status"] == "declared" for s in taken) else "proved"
    arrow = arrows.setdefault((start, end, status), {"from": start, "to": end, "data": [], "status": status,
                                                     "asserts": set(), "via": set(), "proof": [], "through": []})
    for step in taken:
        arrow["data"].append(step["data"])
        arrow["asserts"].update(step["asserts"])
        arrow["via"].update(step["via"])
        arrow["proof"] += step["proof"]
    arrow["through"] += through


def _step(arrow: dict) -> dict:
    return {"from": arrow["from"], "to": arrow["to"], "data": arrow["data"], "status": arrow["status"],
            "asserts": arrow.get("asserts", []), "via": arrow.get("via", []), "proof": arrow.get("proof", []),
            "through": []}


def _code_steps(flow: dict, nodes: dict, links: dict) -> tuple[list[dict], dict[str, list[str]]]:
    """Steps between files: the proof of the flow's arrows and the links inside each of its nodes."""
    items = {n: _item(nodes[n]) for n in flow["nodes"] if nodes[n]["position"] == "internal"}
    edges = [(p, a["data"]) for a in flow["arrows"] if a["status"] != "refused" for p in a.get("proof", [])]
    edges += [(e, "") for e in links["edges"]
              if any(system_map._owns(i, e["from"]) and system_map._owns(i, e["to"]) for i in items.values())]
    owners = defaultdict(set)

    def place(endpoint):
        if endpoint.startswith(("store:", "module:")):
            return endpoint
        path = endpoint.split("::", 1)[0]
        holding = [n for n, i in items.items() if system_map._owns(i, endpoint)]
        owners[path].update(holding)
        return path if holding else None

    steps = []
    for edge, data in edges:
        first, second = place(edge["from"]), place(edge["to"])
        if first and second and first != second:
            via = [e[6:] for e in (edge["from"], edge["to"]) if e.startswith("store:")]
            steps.append({"from": first, "to": second, "data": data, "status": "proved", "asserts": [edge["type"]],
                          "via": via, "proof": [{k: edge[k] for k in ("from", "to", "type", "site")}], "through": []})
    touched = {s[end] for s in steps for end in ("from", "to") if not s[end].startswith(("store:", "module:"))}
    return steps, {path: sorted(owners[path]) for path in sorted(touched)}


def view(system: dict, flow: str, levels: list[str], links: dict | None = None) -> dict:
    """A flow of `system_map.load` at one or more levels, by flow id or current name."""
    if not levels or any(level not in LEVELS for level in levels):
        raise ValueError(f"levels are one or more of {', '.join(LEVELS)}")
    if "codice" in levels and links is None:
        raise ValueError("the codice level needs the links of the snapshot")
    chosen = [level for level in LEVELS if level in levels]
    record = _find(system["flows"], flow, "flow")
    nodes = {n["name"]: n for n in system["nodes"]}
    pool = list(dict.fromkeys(record["nodes"] + ([o for n in record["nodes"] for o in nodes[n]["on"]]
                                                 if "infrastruttura" in chosen else [])))
    shown = {n: next((lv for lv in chosen if lv in levels_of(nodes[n])), None) for n in pool}
    visible = {n for n, level in shown.items() if level}
    steps = [_step(a) for a in record["arrows"]]
    if "infrastruttura" in chosen:  # a hidden node is put on what it runs on
        for name in pool:
            if name in visible or not nodes[name]["on"]:
                continue
            moved = []
            for step in steps:
                ends = [list(nodes[name]["on"]) if step[e] == name else [step[e]] for e in ("from", "to")]
                if step["from"] != name and step["to"] != name:
                    moved.append(step)
                    continue
                for first in ends[0]:
                    for second in ends[1]:
                        moved.append({**step, "from": first, "to": second, "through": step["through"] + [name],
                                      "status": "refused" if step["status"] == "refused" else "declared"})
            steps = [s for s in moved if s["from"] != s["to"]]
    entities = {n for n in pool if nodes[n]["type"] == "entità"}
    arrows, gaps = _contract(visible, steps, entities)
    out_nodes = [{"name": n, "type": nodes[n]["type"], "level": shown[n], "position": nodes[n]["position"],
                  "also": _also(nodes[n], shown[n], system["nodes"])} for n in pool if shown[n]]
    if "codice" in chosen:
        code_steps, files = _code_steps(record, nodes, links)
        code_arrows, code_gaps = _contract(set(files), code_steps, set())
        arrows, gaps = arrows + code_arrows, gaps + code_gaps
        out_nodes += [{"name": path, "type": "file", "level": "codice", "position": "internal",
                       "also": _grouped(nodes[o] for o in owners)} for path, owners in files.items()]
    out_nodes.sort(key=lambda n: (LEVELS.index(n["level"]), system_map.key(n["name"])))
    return {"flow": record["name"], "levels": chosen, "nodes": out_nodes, "arrows": arrows, "gaps": gaps,
            "absent": [level for level in chosen if not any(n["level"] == level for n in out_nodes)]}


def _grouped(found) -> dict[str, list[str]]:
    out = defaultdict(list)
    for node in found:
        out[levels_of(node)[0]].append(node["name"])
    return {level: sorted(names, key=system_map.key) for level, names in sorted(out.items(), key=lambda i: LEVELS.index(i[0]))}


def _also(node: dict, level: str, every: list[dict]) -> dict[str, list[str]]:
    """The same node at the other levels: its files, what it runs on, what runs on it."""
    out = defaultdict(set)
    for other in levels_of(node)[1:]:
        out[other].add(node["name"])
    if node["position"] == "internal" and level != "codice":
        out["codice"].update(node["files"])
    by_name = {n["name"]: n for n in every}
    for name in node["on"]:
        out[levels_of(by_name[name])[0]].add(name)
    for other in every:
        if node["name"] in other["on"]:
            out[levels_of(other)[0]].add(other["name"])
    out.pop(level, None)
    return {lv: sorted(out[lv], key=system_map.key) for lv in LEVELS if out.get(lv)}


def inside(system: dict, name: str, links: dict | None = None) -> dict:
    """A node opened: an entity's representations with who writes and reads them, a node's files and links."""
    node = _find(system["nodes"], name, "node")
    out = {"node": node["name"], "detail": "none", "members": [], "relations": [], "gaps": []}
    if node["position"] != "internal":
        return out
    out["detail"] = "available"
    stores = (links or {}).get("stores", {})
    if node["type"] == "entità":
        keys = [m[6:] for m in node["members"] if m.startswith("store:")]
        out["members"] = [{"id": f"store:{k}", "kind": "store", "writes": stores.get(k, {}).get("writes", []),
                           "reads": stores.get(k, {}).get("reads", [])} for k in keys]
        edges = (links or {}).get("edges", [])
        for first in keys:
            for second in keys:
                both = set(stores.get(first, {}).get("reads", [])) & set(stores.get(second, {}).get("writes", []))
                if first == second or not both:
                    continue
                proof = [{k: e[k] for k in ("from", "to", "type", "site")} for e in edges
                         if (e["from"] == f"store:{first}" and e["to"] in both)
                         or (e["to"] == f"store:{second}" and e["from"] in both and e["type"] == "scrive")]
                out["relations"].append({"from": f"store:{first}", "to": f"store:{second}", "status": "proved",
                                         "asserts": ["trasferisce"], "proof": proof})
        joined = {frozenset((r["from"], r["to"])) for r in out["relations"]}
        out["gaps"] = [{"from": f"store:{a}", "to": f"store:{b}",
                        "reason": f"no link joins {a} and {b}: who writes one does not read the other"}
                       for i, a in enumerate(keys) for b in keys[i + 1:] if frozenset((f"store:{a}", f"store:{b}")) not in joined]
        return out
    for path in node["files"]:
        def keys_of(kind, path=path):
            return sorted(k for k, v in stores.items() if any(s.split("::", 1)[0] == path for s in v[kind]))
        out["members"].append({"id": path, "kind": "file", "writes": keys_of("writes"), "reads": keys_of("reads")})
    for flow in system["flows"]:
        for arrow in flow["arrows"]:
            if node["name"] not in (arrow["from"], arrow["to"]):
                continue
            target = out["gaps"] if arrow["status"] == "refused" else out["relations"]
            target.append({"flow": flow["name"], **{k: arrow[k] for k in ("from", "to", "status") if k in arrow},
                           **{k: arrow[k] for k in ("proof", "cite", "reason") if k in arrow}})
    return out
