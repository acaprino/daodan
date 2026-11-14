"""The measurement on tududi, from the tools' output and the existing graph; reads no project source.

    python -I analyze.py TOOLS_JSON GRAPH_DIR OUT_JSON

TOOLS_JSON is what `modal_points.py tools` returns; GRAPH_DIR holds `graph-javascript.json.gz` and
`graph-typescript.json.gz` (`inference-audit/scip-inputs/tududi/plugin` on the volume).
"""
from __future__ import annotations

import collections
import gzip
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # run with -I: only this folder joins the path
import points  # noqa: E402
TESTS = ("__tests__/", ".test.", ".spec.", "/tests/", "e2e/")


DATABASE = re.compile(r"^[A-Z]\w*\.(findAll|findOne|findByPk|findAndCountAll|findOrCreate|count|sum|max|min|create|"
                      r"bulkCreate|update|upsert|destroy|increment|decrement)$")


def graph(directory: Path):
    nodes, edges, holes = {}, [], []
    for language in ("javascript", "typescript"):
        data = json.load(gzip.open(directory / f"graph-{language}.json.gz"))
        for node in data["nodes"]:
            nodes.setdefault(node["id"], node)
        edges += [(e["from"], e["to"], e["site"], e["end"]) for e in data["edges"]]
        holes += data["holes"]
    return nodes, edges, holes


def callable_nodes(nodes: dict, edges: list) -> tuple[set, list]:
    """Code holders (the source of an edge) and the callables the graph reaches, types left out; the edges
    between them."""
    project = {k for k, n in nodes.items() if n["file"] and not n["external"] and n["kind"] not in ("type", "parameter")}
    held = {a for a, _b, _s, _e in edges if a in project}
    reached = {b for _a, b, _s, end in edges if end == "project-callable" and b in project}
    keep = held | reached
    return keep, [(a, b) for a, b, _s, _e in edges if a in keep and b in keep and a != b]


def compare_tools(tools: dict, exposed: list, calls: list) -> dict:
    """What each existing tool gives, against the recorder (routes) and the adapter (calls)."""
    routes = tools["express"]["routes"]
    recorded = {(r["method"], r["path"]) for r in routes if r["mounted"]}
    listed = {(m, e["path"]) for e in tools["express"].get("express_list_endpoints", ()) for m in e["methods"] or ["?"]}
    static = tools["ast_grep"]["routes"]
    sites = {r["site"] for r in routes}
    swagger = json.loads(tools["swagger"]) if tools["swagger"].startswith("[") else []
    shape = lambda p: re.sub(r"[:{][^/}]+}?", "{}", p).rstrip("/")  # noqa: E731
    documented = {(m.upper(), shape(p)) for p, methods in swagger for m in methods}
    served = {(m, shape(p)) for m, p in recorded}
    jsluice = tools["jsluice"]
    fetched = [j for j in jsluice if j["type"] == "fetch"]
    return {
        "recorder": {"keys": len(recorded), "registration_sites": len(sites)},
        "express_list_endpoints": {"keys": len(listed), "same_as_recorder": len(listed & recorded),
                                   "only_listed": sorted(map(list, listed - recorded)),
                                   "only_recorded": sorted(map(list, recorded - listed)), "sites": 0},
        "ast_grep": {"registrations": len(static), "literal_path": sum(1 for r in static if r["path"] is not None),
                     "not_literal": [[r["site"], r["text"]] for r in static if r["path"] is None],
                     "recorded_not_static": sorted(sites - {r["site"] for r in static}),
                     "static_not_recorded": sorted({r["site"] for r in static} - sites),
                     "fetch_sites": len(tools["ast_grep"]["fetch_sites"])},
        "swagger_jsdoc": {"operations": len(documented), "served": len(documented & served),
                          "not_served": sorted(map(list, documented - served))},
        "jsluice": {"records": len(jsluice), "by_type": dict(collections.Counter(j["type"] for j in jsluice)),
                    "fetch_records": len(fetched), "fetch_urls": sorted({j["url"] for j in fetched}),
                    "with_method": sum(1 for j in fetched if j["method"])},
        "adapter": {"sites": len(calls), "direct": sum(1 for c in calls if not c["via"]),
                    "through_wrappers": sum(1 for c in calls if c["via"])},
    }


def exposed_sides(routes: list, nodes: dict, edges: list) -> tuple[list, list]:
    by_file = collections.defaultdict(list)
    for a, b, site, _end in edges:
        by_file[site.rpartition(":")[0]].append((a, b, site))
    lines = {k: n["line"] for k, n in nodes.items() if n["line"]}
    modules = {n["file"]: k for k, n in nodes.items() if n["kind"] == "module" and n["file"]}
    sides, unmounted, seen = [], [], set()
    for route in routes:
        if not route["mounted"]:
            unmounted.append(route)
            continue
        handler = route["handler"]
        file = handler.get("file") or route["site"].rpartition(":")[0]
        start, end = handler.get("line") or 0, handler.get("end") or handler.get("line") or 0
        key = points.route_key(route["method"], route["path"])
        if (key, route["site"]) in seen:
            continue
        seen.add((key, route["site"]))
        holder = points.holder(file, start, end, by_file.get(file, []), lines, modules.get(file)) \
            if file in modules else None
        sides.append({"site": route["site"], "role": "exposes", "kind": "http", "keys": [key], "holder": holder,
                      "handler": f"{file}:{start}", "handler_name": handler.get("name")})
    return sides, unmounted


def score(expected: dict, joined: dict, calls: list, exposed: list) -> list:
    by_call = collections.defaultdict(list)
    for link in joined["links"]:
        by_call[link["call"]].append(link)
    uncertain = {u["call"]: u for u in joined["uncertain"]}
    missing = {m["site"]: m for m in joined["calls_only"]}
    holes = {h["site"]: h for h in joined["holes"]}
    sites = {s["site"]: s for s in calls}
    handlers = {s["site"]: s for s in exposed}
    rows = []
    for case in expected["links"] + expected["hard"]:
        want = points.route_key(case["method"], case["path"])
        if case["call_site"] is None:  # a route nobody calls
            alone = [r for r in joined["exposed_only"] if r["site"] == case["handler"] and r["key"] == want]
            rows.append({"id": case["id"], "result": "found" if alone else "wrong",
                         "detail": "route without callers" if alone else "someone calls it, or it is not exposed"})
            continue
        links = by_call.get(case["call_site"], [])
        right = [l for l in links if l["route"] == case["handler"] and l["route_key"] == want]
        if right:
            name = handlers[case["handler"]].get("handler_name")
            symbol = case.get("symbol", "").rpartition(".")[2]
            rows.append({"id": case["id"], "result": "found", "match": right[0]["match"],
                         "handler_name": name, "symbol_ok": (name == symbol) if symbol else None})
        elif links:
            rows.append({"id": case["id"], "result": "wrong", "got": [(l["route"], l["route_key"]) for l in links]})
        else:
            cause = (f"uncertain: {uncertain[case['call_site']]['candidates']}" if case["call_site"] in uncertain
                     else f"no route for {missing[case['call_site']]['key']}" if case["call_site"] in missing
                     else f"hole: {holes[case['call_site']]['reason']}" if case["call_site"] in holes
                     else f"no call side here; keys at the site: {sites.get(case['call_site'], {}).get('keys')}")
            rows.append({"id": case["id"], "result": "missed", "cause": cause})
    return rows


def chain(start_nodes: set, forward: dict, sites: dict, goal: set, limit: int = 200000):
    """The shortest path from any start to a goal node, as (node, site of the edge taken) steps."""
    previous, queue = {s: None for s in start_nodes}, collections.deque(start_nodes)
    while queue and len(previous) < limit:
        node = queue.popleft()
        if node in goal:
            steps = []
            while node is not None:
                steps.append(node)
                node = previous[node]
            steps.reverse()
            return [(a, sites.get((a, b))) for a, b in zip(steps, steps[1:])] + [(steps[-1], None)]
        for nxt in forward.get(node, ()):
            if nxt not in previous:
                previous[nxt] = node
                queue.append(nxt)
    return None


def main(tools_path: Path, graph_dir: Path, out_path: Path) -> dict:
    tools = json.loads(tools_path.read_text(encoding="utf-8"))
    expected = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
    nodes, edges, holes = graph(graph_dir)
    exposed, unmounted = exposed_sides(tools["express"]["routes"], nodes, edges)
    calls = tools["client"]["sites"]
    joined = points.join(exposed + calls)
    keyed = [s for s in calls if s["keys"]]
    by_base = collections.Counter("/api/v1" if s["keys"][0].split(" ")[1].startswith("/api/v1")
                                  else "/api" if s["keys"][0].split(" ")[1].startswith("/api") else "other"
                                  for s in exposed)
    linked_sites = {l["call"] for l in joined["links"]} | {u["call"] for u in joined["uncertain"]}
    alone = collections.Counter("/api/v1" if r["key"].split(" ")[1].startswith("/api/v1")
                                else "/api" if r["key"].split(" ")[1].startswith("/api") else "other"
                                for r in joined["exposed_only"])
    hole_reasons = collections.Counter(h["reason"].split(":")[0] if h["reason"] else "?" for h in joined["holes"])
    counts = {
        "routes_exposed": len(exposed), "routes_by_base": dict(by_base), "routes_unmounted": len(unmounted),
        "handlers": len({s["handler"] for s in exposed}),
        "call_sites": len(calls), "call_sites_with_key": len(keyed),
        "call_sites_linked": len(linked_sites),
        "links": len(joined["links"]), "links_by_match": dict(collections.Counter(l["match"] for l in joined["links"])),
        "routes_nobody_calls": len(joined["exposed_only"]), "routes_nobody_calls_by_base": dict(alone),
        "calls_to_missing_routes": len(joined["calls_only"]),
        "holes": len(joined["holes"]), "holes_by_reason": dict(hole_reasons),
        "uncertain": len(joined["uncertain"]),
        "routes_only_as_uncertain_candidates": len({c for u in joined["uncertain"] for c in u["candidate_keys"]}
                                                   - {l["route_key"] for l in joined["links"]}
                                                   - {r["key"] for r in joined["exposed_only"]}), "unmatched_candidates": len(joined["unmatched_candidates"]),
        "wrappers": len(tools["client"]["wrappers"]),
        "unconfirmed_sites": len({u["site"] for u in tools["client"]["unconfirmed"]}),
        "api_paths_outside_requests": len(tools["client"]["outside"]),
    }
    rows = score(expected, joined, calls, exposed)
    keep, links = callable_nodes(nodes, edges)
    before = points.islands(keep, links)
    point_nodes, point_edges = set(), []
    for side in exposed:
        point = f"point {side['keys'][0]}"
        point_nodes.add(point)
        if side["holder"]:
            point_edges.append((point, side["holder"]))
    for link in joined["links"]:
        point = f"point {link['route_key']}"
        if link["holder"]:
            point_edges.append((link["holder"], point))
    after = points.islands(keep | point_nodes, links + point_edges)
    front = {n for n in keep if (nodes.get(n, {}).get("file") or "").startswith("frontend/")
             and not any(t in nodes[n]["file"] for t in TESTS)}
    front_code = {n for n in front if nodes[n]["kind"] != "module" and "#local" not in n}  # locals hold no edge
    incoming = {b for a, b in links if a in front and a != b}
    roots = {n for n in front_code if n not in incoming}
    handlers = {s["holder"] for s in exposed if s["holder"]}
    reached = points.reach(front_code, links + point_edges, handlers)
    reached_roots = points.reach(roots, links + point_edges, handlers)
    reach = {"front_code_nodes": len(front_code), "reach_a_handler": len(reached),
             "roots": len(roots), "roots_reach_a_handler": len(reached_roots),
             "before": len(points.reach(front_code, links, handlers))}
    forward = collections.defaultdict(set)
    sites = {}
    for a, b, site, _end in edges:
        if a in keep and b in keep and a != b:
            forward[a].add(b)
            sites.setdefault((a, b), site)
    for (a, b) in point_edges:
        forward[a].add(b)
    for link in joined["links"]:
        sites.setdefault((link["holder"], f"point {link['route_key']}"), link["call"])
    for side in exposed:
        sites.setdefault((f"point {side['keys'][0]}", side["holder"]), side["handler"])
    # A model call is a hole of the graph (the model is `any` to the index): its holder is found like a handler's.
    by_file = collections.defaultdict(list)
    for a, b, site, _end in edges:
        by_file[site.rpartition(":")[0]].append((a, b, site))
    lines = {k: n["line"] for k, n in nodes.items() if n["line"]}
    modules = {n["file"]: k for k, n in nodes.items() if n["kind"] == "module" and n["file"]}
    database = {}
    for hole in holes:
        file, _, line = hole["site"].rpartition(":")
        if DATABASE.match(hole["name"]) and file.startswith("backend/") and "/tests/" not in file and file in modules:
            owner = points.holder(file, int(line), int(line), by_file[file], lines, modules[file])
            database.setdefault(owner, f"{hole['site']} {hole['name']}")
    named = {a: {b for b in targets if nodes.get(b, {}).get("kind") != "module"} for a, targets in forward.items()
             if nodes.get(a, {}).get("kind") != "module"}  # through named code, not a file's top level
    ui = {n for n in front_code if nodes[n]["file"].startswith("frontend/components/")}
    path = chain(ui, named, sites, set(database)) or chain(ui, forward, sites, set(database))
    example = None
    if path:
        example = [{"node": n, "at": f"{nodes[n]['file']}:{nodes[n]['line']}" if n in nodes else None,
                    "via": s} for n, s in path] + [{"database_call": database[path[-1][0]]}]
    result = {"counts": counts, "tools": compare_tools(tools, exposed, calls), "expected": rows,
              "expected_found": sum(1 for r in rows if r["result"] == "found"),
              "islands": {"before": before, "after": after}, "reach": reach, "example_chain": example,
              "join": joined, "unmounted": unmounted[:50], "outside": tools["client"]["outside"],
              "unconfirmed": tools["client"]["unconfirmed"], "wrappers": tools["client"]["wrappers"]}
    out_path.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    summary = main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(json.dumps({k: summary[k] for k in ("counts", "expected_found", "islands", "reach")}, indent=1))
