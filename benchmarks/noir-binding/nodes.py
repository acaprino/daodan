"""The node level of the binding (`modal_binding.py --mode nodes` ships this file to `/daodan/measure/`; it runs in the container, over the checkout at `/work`, and
reads only: Noir and Daodan's snapshot code).

The binder does not return a declaration: `binder._position` returns `facts.node(declaration id)`, the named symbol the links use, and an anonymous function
counts as the function that owns it (`Facts.node` folds `(anonymous)` into its owner; two declarations with the same qualified name, such as the
`(lambda)` of one method, are the same string). A route bound to a node that many routes share would carry the steps of all of them: so what a candidate rule
binds is measured as the links hold it.

1. The pre-map of the snapshot is written with the recorded Noir answer (`premap.write`, as `real_summary.py` of flask-routes does).
2. `binder.bind` is run over the rows on a `flows.Facts` built as `flows.link_facts` builds it, with the candidate rule patched in here (not in the repository):
   the rule of today first (a unique function that has the handler's name at the row's line), then, for a row whose position is the handler's (`handler.path`
   of Noir's endpoint, never the `code_paths` fallback) and for which the first found none, the one function that starts at that line.
3. `flows.link_facts(manifest, [])` is run with that rule patched in, as the links are built; its entries and its edges say which node each route
   ends on and what leaves it.

Returns the facts of each row (how it was bound, the declaration, the node, whether the node is the matched function's own) and, for a few rows of each class,
what leaves the node.
"""
import collections
import json
import os
import pathlib
import subprocess
import sys
import time
import types

ROOT = "/work"
SAMPLES = 5


def brief(d: dict) -> dict:
    return {"name": d["name"], "qn": d.get("qualified_name"), "kind": d["kind"], "line": d["line"], "end": d["end"]}


def provenance(report: dict) -> dict:
    """Where each row of `noir.rows` takes its position from: `handler` when the endpoint's handler has a path, else the first of its `code_paths`."""
    out = collections.defaultdict(set)
    for endpoint in report.get("endpoints") or ():
        handler = endpoint.get("handler") or {}
        paths = (endpoint.get("details") or {}).get("code_paths") or [{}]
        where = handler if handler.get("path") else paths[0]
        if not where.get("path"):
            continue
        file = where["path"][len(ROOT) + 1:] if where["path"].startswith(ROOT + "/") else where["path"]
        site = f"{file}:{where['line']}" if where.get("line") else file
        out[(site, endpoint["method"], endpoint["url"])].add("handler" if where is handler else "code_paths")
    return out


def run(name: str) -> dict:
    os.chdir("/")
    sys.path[:0] = ["/daodan/core"]
    import binder
    import edge_view
    import entries
    import flows
    import premap
    import semantic_store
    import snapshot
    from premap import noir
    from snapshot_store import open_snapshot

    out = {"name": name}
    manifest = pathlib.Path("/tmp/noir-binding/nodes/manifest.sqlite")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    snapshot.write_snapshot(pathlib.Path(ROOT), manifest)
    out["snapshot_seconds"] = round(time.monotonic() - started, 1)
    [command] = noir.commands(types.SimpleNamespace(inventory=types.SimpleNamespace(files=True)))
    env = {"PATH": os.environ["PATH"], "HOME": "/tmp/noir-home", "LANG": "C.UTF-8"}
    os.makedirs(env["HOME"], exist_ok=True)
    result = subprocess.run(command["argv"], cwd=os.path.join(ROOT, command["cwd"]), env=env, capture_output=True, text=True, timeout=3000, stdin=subprocess.DEVNULL)
    if result.returncode != 0:
        return {**out, "failed": f"Noir exited with {result.returncode}"}
    report = json.loads(result.stdout)
    where = provenance(report)
    answer = {"returncode": 0, "stdout": result.stdout, "stderr": "", "root": ROOT}
    record = premap.write(manifest, sources=(noir,), runner=lambda commands: [answer])
    rows = record.get("noir_entries", [])
    out["rows"] = len(rows)

    original = binder._position
    order: list[dict] = []
    naming = {"routes": False}  # the second run of the links: an anonymous function the rule finds is named by its route before its node is asked for

    def candidate(row: dict, facts) -> dict:
        done = original(row, facts)
        file, separator, line = row["site"].rpartition(":")
        at = int(line) if line.isdecimal() else 0
        info = {"via": None}
        if not done.get("gap"):
            wanted = row["handler"]
            [found] = [d for d in facts.functions.get(file, ()) if wanted and wanted in (d["name"], d.get("qualified_name")) and d["line"] <= at <= (d["end"] or d["line"])]
            info = {"via": "exact", "decl": found["id"]}
        elif row["handler"] is not None and separator and where.get((row["site"], row.get("method"), row["path"])) == {"handler"}:
            starts = [d for d in facts.functions.get(file, ()) if d["line"] == at]
            if len(starts) == 1 and naming["routes"] and starts[0]["name"] == "(anonymous)":
                facts.route_named[starts[0]["id"]] = f"{(row.get('method') or 'ANY').upper()} {row['path']}"
                facts._nodes.pop(starts[0]["id"], None)
            if len(starts) == 1 and facts.node(starts[0]["id"]) is None:
                info = {"via": "start-no-node", "decl": starts[0]["id"]}  # an anonymous function with no named owner: a row bound to it would have no symbol, and one such row
                #                                                         makes `link_facts` fail (it sorts the entries by symbol): the rule does not bind it
            elif len(starts) == 1:
                done = {**row, "symbol": facts.node(starts[0]["id"]), "handler_source": row["reader"]}
                info = {"via": "start", "decl": starts[0]["id"]}
            elif starts:
                info = {"via": "ambiguous", "decls": [d["id"] for d in starts]}
        order.append(info)
        return done

    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        facts = flows.Facts(store, db, view)
        resolver = semantic_store._Resolver(db)
        binder._position = candidate
        try:
            bound = binder.bind(rows, facts, resolver)
        finally:
            binder._position = original
        assert len(bound) == len(order) == len(rows)
        refs_by_node = collections.defaultdict(list)
        refs_by_caller = collections.defaultdict(list)
        for ref in view["references"]:
            if ref.get("caller"):
                refs_by_caller[ref["caller"]].append(ref)
                node = facts.node(ref["caller"])
                if node:
                    refs_by_node[node].append(ref)
        holders = collections.Counter(node for node in (facts.node(d["id"]) for d in facts.declarations.values() if d["kind"] in ("function", "method", "class")) if node)
        own_holders = collections.Counter(facts.named(d["id"]) for d in facts.declarations.values() if d["kind"] in ("function", "method", "class"))  # declarations that are the node by name
        out["facts"] = []
        for i, (row, info, done) in enumerate(zip(rows, order, bound)):
            item = {"i": i, "shape": row["shape"], "handler": row["handler"], "site": row["site"], "method": row.get("method"), "path": row["path"], "via": info["via"]}
            if info["via"] in ("exact", "start", "start-no-node"):
                decl = facts.declarations[info["decl"]]
                node = done["symbol"] if info["via"] != "start-no-node" else None
                item.update({"decl_id": info["decl"], "decl": brief(decl), "node": node, "named": facts.named(info["decl"]), "folded": node != facts.named(info["decl"]),
                             "node_holders": holders[node] if node else 0,  # how many declarations of the snapshot end on that node
                             "own_holders": own_holders[facts.named(info["decl"])]})  # and how many of them are that node by their own name: more than one is two functions with one name
            elif info["via"] == "ambiguous":
                item["candidates"] = [{**brief(facts.declarations[d]), "node": facts.node(d)} for d in info["decls"]]
            out["facts"].append(item)
        # what the links already do for a function written in place as a route handler (`Facts.route_named`: it is named by its route, `GET /path`, and is its own node):
        # the node an anonymous function the rule found would have if the binder named it so before asking for its node
        for item in out["facts"]:
            if item["via"] in ("start", "start-no-node") and item["decl"]["name"] == "(anonymous)":
                facts.route_named[item["decl_id"]] = f"{(item['method'] or 'ANY').upper()} {item['path']}"
                facts._nodes.pop(item["decl_id"], None)
                item["node_routed"] = facts.node(item["decl_id"])
                del facts.route_named[item["decl_id"]]
                facts._nodes.pop(item["decl_id"], None)

        # the links, with the candidate rule in: which node each route ends on, and what leaves it; then again with the anonymous functions the rule finds named by their route
        def build(routes: bool):
            naming["routes"] = routes
            binder._position = candidate
            order.clear()
            try:
                started = time.monotonic()
                return flows.link_facts(manifest, []), round(time.monotonic() - started, 1), None
            except Exception as error:  # the links of this snapshot did not build: the facts of the binder remain
                return None, None, f"{type(error).__name__}: {str(error)[:300]}"
            finally:
                binder._position = original
                naming["routes"] = False

        def out_edges(links) -> dict:
            found = collections.defaultdict(list)
            for edge in links["edges"]:
                if edge["type"] in ("chiama", "attiva"):
                    found[edge["from"]].append(edge)
            return found
        links, seconds, failure = build(False)
        edges_from = collections.defaultdict(list)
        if failure:
            out["links_failed"] = failure
        else:
            out["links_seconds"] = seconds
            noir_entries = [e for e in links["entries"] if e.get("reader") == entries.NOIR]
            mine = collections.Counter(item["node"] for item in out["facts"] if item["via"] in ("exact", "start") and item["shape"] == "http")
            theirs = collections.Counter(e["symbol"] for e in noir_entries if e.get("shape") == "http")
            out["links"] = {"noir_entries": len(noir_entries), "same_nodes_as_the_binder_rows": mine == theirs,
                            "edges": len(links["edges"]), "gaps": len(links["gaps"])}
            edges_from = out_edges(links)
            for item in out["facts"]:
                if item.get("node"):
                    item["edges_out"] = len(edges_from.get(item["node"], ()))  # no node, no edges
        if any(item.get("node_routed") for item in out["facts"]):
            routed_links, seconds, failure = build(True)
            if failure:
                out["links_routed_failed"] = failure
            else:
                routed_from = out_edges(routed_links)
                routed_entries = [e for e in routed_links["entries"] if e.get("reader") == entries.NOIR and e.get("shape") == "http"]
                out["links_routed"] = {"noir_entries": len(routed_entries), "distinct_symbols": len({e["symbol"] for e in routed_entries}),
                                       "edges": len(routed_links["edges"]), "gaps": len(routed_links["gaps"])}
                for item in out["facts"]:
                    if item.get("node_routed"):
                        item["edges_out_routed"] = len(routed_from.get(item["node_routed"], ()))
                        item["routed_edges_sample"] = [{"to": e["to"], "site": e["site"]} for e in routed_from.get(item["node_routed"], ())[:3]]

        # a few rows of each class: what the node holds and what leaves it
        def klass(item: dict) -> str:
            handler = item["handler"] or ""
            return "closure" if handler == "closure" else "call parentheses" if "(" in handler else "other name" if item["via"] != "exact" and handler else item["via"] or "none"
        chosen = collections.defaultdict(list)
        for item in out["facts"]:
            if item["via"] in ("exact", "start", "start-no-node") and item["shape"] == "http" and len(chosen[(item["via"], klass(item))]) < SAMPLES:
                chosen[(item["via"], klass(item))].append(item)
        for item in out["facts"]:  # and a few more of each class whose node has an edge out, to see what the edges are
            group = chosen[(item["via"], klass(item))] if item["via"] in ("exact", "start", "start-no-node") and item["shape"] == "http" else None
            if group is not None and item.get("edges_out") and item not in group and sum(1 for g in group if g.get("edges_out")) < 3 and len(group) < SAMPLES + 3:
                group.append(item)
        samples = []
        for (via, cls), items in sorted(chosen.items()):
            for item in items:
                declaration = facts.declarations[item["decl_id"]]
                own = refs_by_caller.get(declaration["id"], [])
                held = {ref["caller"] for ref in refs_by_node.get(item["node"], ())} if item["node"] else set()
                nested = [d for d in facts.declarations.values() if d["file"] == declaration["file"] and d["kind"] in ("function", "method")
                          and d["line"] >= declaration["line"] and (d["end"] or d["line"]) <= (declaration["end"] or declaration["line"]) and d["id"] != declaration["id"]]
                samples.append({
                    "via": via, "class": cls, "i": item["i"], "method": item["method"], "path": item["path"], "handler": item["handler"], "site": item["site"],
                    "declaration": brief(declaration), "node": item["node"], "folded": item["folded"], "node_holders": item["node_holders"], "own_holders": item["own_holders"],
                    "own_calls": len(own), "own_calls_sample": [{"parts": ref.get("parts"), "line": (ref.get("span") or [None])[0], "resolution": ref["resolution"]} for ref in own[:3]],
                    "own_targets": sorted({facts.node(end["target_id"]) or "?" for ref in own for end in edge_view.call_ends(ref)})[:3],
                    "calls_of_the_node": len(refs_by_node.get(item["node"], ())) if item["node"] else None, "declarations_that_call_into_the_node": len(held),
                    "callers_in_the_node": [{"qn": facts.declarations[c].get("qualified_name") if c in facts.declarations else c, "line": facts.declarations[c]["line"] if c in facts.declarations else None,
                                             "calls": sum(1 for ref in refs_by_node[item["node"]] if ref["caller"] == c)} for c in sorted(held)[:4]] if item["node"] else [],
                    "nested_functions_in_the_declaration": [{**brief(d), "node": facts.node(d["id"]), "own_calls": len(refs_by_caller.get(d["id"], ()))} for d in nested[:3]],
                    "edges_out": len(edges_from.get(item["node"], ())) if links is not None and item["node"] else None,
                    "edges_sample": [{"to": e["to"], "site": e["site"], "type": e["type"]} for e in edges_from.get(item["node"], ())[:3]] if item["node"] else []})
        out["samples"] = samples
    return out
