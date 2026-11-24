"""From the answers of `modal_binding.py --mode nodes` (`<name>.nodes.json` in the evidence folder) to the node level of the binding: for each application, the
endpoints the binder ties today and the ones the candidate rule (`handler.line` = the line a function starts at) would tie, and for each group the
nodes they end on, the largest group of endpoints on one node, and how many endpoints land on a node that is not the matched function's own.
Writes `results/nodes.json` and prints the tables.

    python -I benchmarks/noir-binding/summarize_nodes.py <the evidence folder of modal_binding.py>

The words: a row is on a node that is **its own** when `facts.node(declaration)` is the declaration's own named symbol (`facts.named`); it is **folded** when the
node is another symbol (an anonymous function counts as the function that owns it) or **none** (an anonymous function with no named owner); it **collides**
when two or more declarations end on the same node (their qualified names are equal, or both fold into one owner). One function that answers several routes is
not a collision: it is one declaration.
"""
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apps  # noqa: E402

RESULTS = HERE / "results"


def handler_class(item: dict) -> str:
    handler = item["handler"] or ""
    return "closure" if handler == "closure" else "call parentheses" if "(" in handler else "named" if handler else "none"


def stats(items: list[dict]) -> dict:
    """The facts of a group of endpoints that ended on a node."""
    by_node = collections.defaultdict(list)
    for item in items:
        by_node[item["node"]].append(item)
    real = {n: v for n, v in by_node.items() if n is not None}
    largest = max(real.items(), key=lambda kv: len(kv[1]), default=(None, []))
    collide = {n for n, v in real.items() if len({i["decl_id"] for i in v}) > 1}
    return {"endpoints": len(items), "nodes": len(real), "no_node": len(by_node.get(None, ())),
            "largest_group": {"endpoints": len(largest[1]), "node": largest[0], "declarations": len({i["decl_id"] for i in largest[1]})},
            "not_its_own_node": sum(1 for i in items if i["node"] is None or i["folded"]),
            "folded_into_another_node": sum(1 for i in items if i["node"] is not None and i["folded"]),
            "on_a_node_shared_by_several_declarations": sum(len(real[n]) for n in collide), "nodes_shared_by_several_declarations": len(collide),
            "its_own_node_and_no_other_function_of_that_name": sum(1 for i in items if i["node"] and not i["folded"] and i.get("own_holders") == 1),
            "with_an_edge_out": sum(1 for i in items if i.get("edges_out")), "without_an_edge_out": sum(1 for i in items if i["node"] and not i.get("edges_out"))}


def routed(items: list[dict]) -> dict:
    """The anonymous functions the rule finds, if the binder named each by its route (`Facts.route_named`) before asking for its node."""
    items = [i for i in items if "node_routed" in i]
    by_node = collections.defaultdict(set)
    for i in items:
        by_node[i["node_routed"]].add((i["decl_id"], i["method"], i["path"]))
    return {"endpoints": len(items), "nodes": len(by_node), "largest_group": max((len(v) for v in by_node.values()), default=0),
            "on_a_node_of_two_or_more_routes": sum(len(v) for v in by_node.values() if len(v) > 1), "no_node": sum(1 for i in items if i["node_routed"] is None),
            "with_an_edge_out_in_the_links": sum(1 for i in items if i.get("edges_out_routed")), "in_the_links_without_an_edge_out": sum(1 for i in items if "edges_out_routed" in i and not i["edges_out_routed"])}


def one(name: str, answer: dict) -> dict:
    out = {"name": name, "framework": apps.APPS[name][0]}
    if answer.get("failed"):
        return {**out, "failed": answer["failed"]}
    http = [f for f in answer["facts"] if f["shape"] == "http"]
    bound = [f for f in http if f["via"] in ("exact", "start", "start-no-node")]
    base = [f for f in bound if f["via"] == "exact"]
    new = [f for f in bound if f["via"] != "exact"]  # `start-no-node`: the rule finds the function, and its node is none: counted here, not bound
    ambiguous = [f for f in http if f["via"] == "ambiguous"]
    classes = {}
    for cls in sorted({handler_class(f) for f in new}):
        classes[cls] = stats([f for f in new if handler_class(f) == cls])
    out.update({
        "http_rows": len(http), "baseline": stats(base), "new": stats(new), "new_anonymous_named_by_their_route": routed(new), "baseline_and_new": stats(bound), "new_by_class": classes,
        "ambiguous_start": {"endpoints": len(ambiguous), "of_which_all_candidates_on_one_node": sum(1 for f in ambiguous if len({c["node"] for c in f["candidates"]}) == 1)},
        "links": answer.get("links"), "links_failed": answer.get("links_failed"), "samples": answer.get("samples", [])})
    return out


def pooled(results: list[dict]) -> dict:
    out = {}
    for which in ("baseline", "new"):
        acc = collections.Counter()
        largest = (0, None, None)
        for r in results:
            s = r[which]
            for k in ("endpoints", "nodes", "no_node", "not_its_own_node", "folded_into_another_node", "on_a_node_shared_by_several_declarations", "its_own_node_and_no_other_function_of_that_name", "with_an_edge_out", "without_an_edge_out"):
                acc[k] += s[k]
            if s["largest_group"]["endpoints"] > largest[0]:
                largest = (s["largest_group"]["endpoints"], r["name"], s["largest_group"]["node"])
        out[which] = {**acc, "largest_group": {"endpoints": largest[0], "app": largest[1], "node": largest[2]}}
    classes = collections.defaultdict(collections.Counter)
    for r in results:
        for cls, s in r["new_by_class"].items():
            for k in ("endpoints", "nodes", "no_node", "not_its_own_node", "on_a_node_shared_by_several_declarations", "its_own_node_and_no_other_function_of_that_name"):
                classes[(r["framework"], cls)][k] += s[k]
    acc = collections.Counter()
    for r in results:
        for k, v in r["new_anonymous_named_by_their_route"].items():
            if k != "largest_group":
                acc[k] += v
        acc["largest_group"] = max(acc["largest_group"], r["new_anonymous_named_by_their_route"]["largest_group"])
    out["new_anonymous_named_by_their_route"] = dict(acc)
    out["new_by_framework_and_class"] = {f"{fw} / {cls}": dict(c) for (fw, cls), c in sorted(classes.items())}
    return out


def main():
    evidence = pathlib.Path(sys.argv[1])
    results = {}
    for name in apps.APPS:
        path = evidence / f"{name}.nodes.json"
        if path.is_file():
            results[name] = one(name, json.loads(path.read_text(encoding="utf-8")))
    ok = [r for n, r in results.items() if not r.get("failed") and n != "shhh"]
    summary = {"applications": results, "pooled": pooled(ok)}
    (RESULTS / "nodes.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("| app | today: endpoints / nodes / largest group / not its own node | new: endpoints / nodes / largest group (node) / no node / folded / on a shared node |")
    for name, r in results.items():
        if r.get("failed"):
            print(f"| {name} | FAILED {r['failed'][:80]} |")
            continue
        b, n = r["baseline"], r["new"]
        print(f"| {name} | {b['endpoints']} / {b['nodes']} / {b['largest_group']['endpoints']} / {b['not_its_own_node']} | "
              f"{n['endpoints']} / {n['nodes']} / {n['largest_group']['endpoints']} ({(n['largest_group']['node'] or '')[-60:]}) / {n['no_node']} / {n['folded_into_another_node']} / "
              f"{n['on_a_node_shared_by_several_declarations']} |")
    print(json.dumps(summary["pooled"], indent=1))


if __name__ == "__main__":
    main()
