"""From the answers of `modal_binding.py --mode after` (`<name>.after.json`: the tree's own binder, nothing substituted) to the numbers of the README's section
«Dopo la correzione»: per application and in total, the endpoints bound before (by the name at the line), after the first fix (the answers of the earlier run,
a folder given), and now; the rows the first fix bound and this one does not, with the cause the binder words; the nodes the bound ones end on, the largest group on
one node and whether its endpoints are one function; the rows bound before whose symbol changed; whether the links build; the edges of the newly bound outside their
function; and three doubts about the position rule, counted from the snapshot's spans and the syntax tree. Writes `results/after.json`.

    python -I benchmarks/noir-binding/summarize_after.py <the evidence folder> <the folder of the first fix's answers> <the folder of the node answers of the earlier binder> <the fingerprints file>
"""
import collections
import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apps  # noqa: E402

RESULTS = HERE / "results"
CAUSES = (("no function starts at the line", "no function starts at the line Noir cites for the handler"),
          ("several functions start there and none holds the others", "several functions start at the line and none holds the others"),
          ("the name disagrees with the function at the line", "Noir names "),
          ("folded into another node", "the function there is folded into"),
          ("anonymous, its route is another function's", "the function there is anonymous and its route is the route of another function"),
          ("shares its node", "the function there shares its node"),
          ("has no node", "the function there has no node"))
GROUPS = {"Express": ("anything-llm", "juice-shop", "node-express-boilerplate"), "Gin": ("go-admin", "gin-vue-admin", "go-gin-example"),
          "C#": ("eshop", "eshoponweb"), "DefectDojo": ("defectdojo",)}
SAMPLES = {"Express": 3, "Gin": 2, "C#": 2, "DefectDojo": 3}
KEY = lambda f: (f["site"], f["method"], f["path"], f["handler"])


def cause(item: dict) -> str:
    gap = item.get("gap")
    if not gap:
        return "null handler" if item["handler"] is None else "no cause worded (a name at its site that is not unique)"
    for label, start in CAUSES:
        if gap.startswith(start):
            if label.startswith("the name disagrees") and "a function that builds the handler" in gap:
                return "a factory whose returned function is not folded into it"
            return label
    return "other: " + gap[:60]


def stats(items: list[dict]) -> dict:
    by_node = collections.defaultdict(list)
    for item in items:
        by_node[item["symbol"]].append(item)
    largest = max(by_node.items(), key=lambda kv: len(kv[1]), default=(None, []))
    functions = lambda group: {d for item in group for d in item["decls"]}
    shared = {n: g for n, g in by_node.items() if len(functions(g)) > 1}
    return {"endpoints": len(items), "nodes": len(by_node),
            "largest_group": {"endpoints": len(largest[1]), "node": largest[0], "functions": len(functions(largest[1])),
                              "methods": sorted({(i["method"] or "") for i in largest[1]})[:8]},
            "nodes_with_several_functions": len(shared), "endpoints_on_them": sum(len(g) for g in shared.values()),
            "with_an_edge_out": sum(1 for i in items if i.get("edges_out")), "edges": sum(i.get("edges_out", 0) for i in items),
            "edges_outside_the_lines_of_the_function": sum(i.get("edges_outside_its_lines", 0) for i in items),
            "rows_with_an_edge_outside": sum(1 for i in items if i.get("edges_outside_its_lines"))}


def example(app: str, item: dict) -> dict:
    return {"app": app, "method": item["method"], "path": item["path"], "noir_handler": item["handler"], "site": item["site"], "registration": item.get("registration"),
            "function_at_the_line": item.get("function_at_the_line"), "written_directly_in_it": item.get("written_directly_in_it"), "gap": item.get("gap")}


def one(name: str, answer: dict, first: dict | None, earlier: dict | None) -> dict:
    out = {"name": name, "framework": apps.APPS[name][0]}
    if answer.get("failed"):
        return {**out, "failed": answer["failed"]}
    http = [f for f in answer["facts"] if f["shape"] == "http"]
    bound = [f for f in http if f["ok"]]
    before = [f for f in bound if f["by"] == "name"]
    new = [f for f in bound if f["by"] == "position"]
    unbound = [f for f in http if not f["ok"]]
    changed = [{"i": f["i"], "handler": f["handler"], "site": f["site"], "symbol_now": f["symbol"]} for f in before if f.get("same_node_as_before") is False]
    differ_from_the_earlier_run, missing = [], []
    if earlier:
        # the rows of Noir's answer come in another order from one run to the next (tRPC in uni-stack): a row is told by its handler's site, method, path and name
        old = collections.Counter((KEY(f), f["node"]) for f in earlier["facts"] if f.get("via") == "exact" and f["shape"] == "http")
        now = collections.Counter((KEY(f), f["symbol"]) for f in before)
        differ_from_the_earlier_run = [{"row": list(k[0]), "then": k[1], "now": None} for k in (old - now)] + [{"row": list(k[0]), "then": None, "now": k[1]} for k in (now - old)]
        missing = [list(k[0]) for k in (old - now) if not any(k[0] == m[0] for m in now)]
    lost, first_bound = [], None
    if first is not None:
        first_http = [f for f in first["facts"] if f["shape"] == "http" and f["ok"]]
        first_bound = len(first_http)
        had = collections.Counter(KEY(f) for f in first_http)
        has = collections.Counter(KEY(f) for f in bound)
        owed = had - has  # the first fix bound them, this one does not
        for f in unbound:
            if owed[KEY(f)] > 0:
                owed[KEY(f)] -= 1
                lost.append(f)
    out.update({
        "http_rows": len(http), "bound_before": len(before), "bound_after_the_first_fix": first_bound, "bound_now": len(bound), "newly_bound": len(new), "unbound_now": len(unbound),
        "lost_since_the_first_fix": {"endpoints": len(lost), "by_cause": dict(collections.Counter(cause(f) for f in lost)),
                                    "examples": {c: [example(name, f) for f in lost if cause(f) == c][:2] for c in {cause(f) for f in lost}}},
        "before": stats(before), "now": stats(bound), "new": stats(new),
        "unbound_by_cause": dict(collections.Counter(cause(f) for f in unbound).most_common()),
        "agreement_of_the_new": dict(collections.Counter(f["agrees"] for f in new).most_common()),
        "symbols_changed_against_the_untouched_facts": changed, "symbols_changed_against_the_earlier_run": differ_from_the_earlier_run, "bound_before_and_not_bound_now": missing,
        "named_by_their_route": answer.get("named_by_their_route"), "links": answer.get("links"), "links_failed": answer.get("links_failed")})
    return out


def doubts(answers: dict) -> dict:
    """The three doubts about the rule that a nameless function binds: counted from the snapshot's spans and the syntax tree of the function bound."""
    rows = [(n, f) for n, a in answers.items() if not a.get("failed") and n != "shhh" for f in a["facts"] if f["shape"] == "http" and f["ok"] and f["by"] == "position" and f.get("nameless")]
    guard, array, registrar, later = [], [], [], []
    for n, f in rows:
        s = f.get("syntax") or {}
        if s.get("earlier_with_a_function"):
            guard.append((n, f))
        if str(s.get("list", "")).startswith(("array", "collection", "initializer", "composite")):
            array.append((n, f))
        if s.get("later_with_a_function"):
            later.append((n, f))
        if any(d["held_by_the_chosen"] for d in f.get("starting_at_the_line", ())):
            registrar.append((n, f))
    by_function = collections.defaultdict(list)
    for n, f in rows:
        by_function[(n, f["decls"][0])].append(f)
    several_methods = {k: v for k, v in by_function.items() if len({x["method"] for x in v}) > 1}
    chained = []
    for (n, ident), group in several_methods.items():
        syntax = group[0].get("syntax") or {}
        methods = sorted({x["method"] for x in group})
        callee = (syntax.get("callee") or "").lower()
        chained.append({"app": n, "function": group[0]["decl_brief"][0], "file": group[0]["file"], "methods": methods, "endpoints": len(group), "paths": sorted({x["path"] for x in group})[:3],
                        "cited_lines": sorted({x["site"] for x in group})[:3], "registration_lines": sorted({str(x["registration"]) for x in group})[:3],
                        "callee": syntax.get("callee"), "callee_is_one_of_the_methods": callee.upper() in methods, "callee_answers_every_method": callee in ("all", "use", "route", "any", "handle", "map", "mapmethods"),
                        "parent": syntax.get("parent")})

    def short(n, f):
        return {"app": n, "method": f["method"], "path": f["path"], "noir_handler": f["handler"], "site": f["site"], "registration": f["registration"], "function": f["decl_brief"][0],
                "syntax": f.get("syntax"), "starting_at_the_line": f.get("starting_at_the_line")}
    coverage = collections.Counter()
    for _, f in rows:
        s = f.get("syntax") or {}
        coverage["parent: " + str(s.get("parent"))] += 1
        coverage["tree not read"] += "tree" in s
        coverage["the only argument" if s.get("elements") == 1 else "one of several arguments"] += s.get("list") in ("arguments", "argument_list")
        coverage["the last argument"] += s.get("list") in ("arguments", "argument_list") and s.get("index") == s.get("elements", 0) - 1
        coverage["no other function starts on its line"] += len(f.get("starting_at_the_line", ())) == 1
    return {"nameless_functions_bound_by_position": len(rows), "syntax_coverage": dict(coverage),
            "by_app": dict(collections.Counter(n for n, _ in rows)),
            "guard_or_middleware_before_in_the_same_call": {"endpoints": len(guard), "by_app": dict(collections.Counter(n for n, _ in guard)), "examples": [short(n, f) for n, f in guard[:6]]},
            "in_an_array": {"endpoints": len(array), "by_app": dict(collections.Counter(n for n, _ in array)), "examples": [short(n, f) for n, f in array[:6]]},
            "a_later_argument_holds_a_function": {"endpoints": len(later), "by_app": dict(collections.Counter(n for n, _ in later)), "examples": [short(n, f) for n, f in later[:6]]},
            "holds_a_function_that_starts_on_its_line": {"endpoints": len(registrar), "by_app": dict(collections.Counter(n for n, _ in registrar)), "examples": [short(n, f) for n, f in registrar[:8]]},
            "several_methods_on_one_function": {"functions": len(chained), "endpoints": sum(c["endpoints"] for c in chained), "groups": chained},
            "not_an_argument_of_a_call": dict(collections.Counter((f.get("syntax") or {}).get("parent") for _, f in rows if (f.get("syntax") or {}).get("list") is None).most_common(8))}


def main():
    evidence = pathlib.Path(sys.argv[1])
    first_dir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
    earlier_dir = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None
    results, answers = {}, {}
    for name in apps.APPS:
        path = evidence / f"{name}.after.json"
        if not path.is_file():
            continue
        answers[name] = json.loads(path.read_text(encoding="utf-8"))
        first = json.loads((first_dir / f"{name}.after.json").read_text(encoding="utf-8")) if first_dir and (first_dir / f"{name}.after.json").is_file() else None
        earlier = json.loads((earlier_dir / f"{name}.nodes.json").read_text(encoding="utf-8")) if earlier_dir and (earlier_dir / f"{name}.nodes.json").is_file() else None
        results[name] = one(name, answers[name], first, earlier)
    ok = {n: r for n, r in results.items() if not r.get("failed") and n != "shhh"}
    best = max(((r["new"]["largest_group"]["endpoints"], n) for n, r in ok.items()), default=(0, None))
    samples = []
    rng = random.Random(24)
    for label, names in GROUPS.items():
        pool = [(n, f) for n in names if n in answers for f in answers[n]["facts"] if f["shape"] == "http" and f["ok"] and f["by"] == "position" and f.get("edges_out")]
        rng.shuffle(pool)
        for n, f in pool[:SAMPLES[label]]:
            lines = f["lines"]
            samples.append({"group": label, "app": n, "method": f["method"], "path": f["path"], "handler": f["handler"], "node": f["symbol"], "function": f["decl_brief"][0],
                            "lines": lines, "edges_out": f["edges_out"], "edges": [{**e, "inside_the_function": e["site"].rpartition(":")[0] == f["file"] and e["site"].rpartition(":")[2].isdecimal()
                                                                                   and lines[0] <= int(e["site"].rpartition(":")[2]) <= lines[1]} for e in f["edges_sample"]]})
    lost_total = collections.Counter()
    lost_examples = collections.defaultdict(list)
    for n, r in ok.items():
        lost_total.update(r["lost_since_the_first_fix"]["by_cause"])
        for c, ex in r["lost_since_the_first_fix"]["examples"].items():
            lost_examples[c] += ex
    summary = {"applications": results, "samples": samples,
               "total": {k: sum(r[k] for r in ok.values()) for k in ("http_rows", "bound_before", "bound_after_the_first_fix", "bound_now", "newly_bound", "unbound_now")},
               "nodes_before": sum(r["before"]["nodes"] for r in ok.values()), "nodes_now": sum(r["now"]["nodes"] for r in ok.values()),
               "largest_group_among_the_new": {"endpoints": best[0], "application": best[1], "node": ok[best[1]]["new"]["largest_group"]["node"] if best[1] else None,
                                               "functions": ok[best[1]]["new"]["largest_group"]["functions"] if best[1] else None, "methods": ok[best[1]]["new"]["largest_group"]["methods"] if best[1] else None},
               "unbound_by_cause": dict(sum((collections.Counter(r["unbound_by_cause"]) for r in ok.values()), collections.Counter()).most_common()),
               "lost_since_the_first_fix": {"endpoints": sum(lost_total.values()), "by_cause": dict(lost_total.most_common()), "examples": {c: v[:2] for c, v in lost_examples.items()}},
               "agreement_of_the_new": dict(sum((collections.Counter(r["agreement_of_the_new"]) for r in ok.values()), collections.Counter()).most_common()),
               "symbols_changed": [x for r in ok.values() for x in r["symbols_changed_against_the_untouched_facts"]],
               "symbols_changed_against_the_earlier_run": [x for r in ok.values() for x in r["symbols_changed_against_the_earlier_run"]],
               "bound_before_and_not_bound_now": [x for r in ok.values() for x in r["bound_before_and_not_bound_now"]],
               "links_failed": {n: r["links_failed"] for n, r in results.items() if r.get("links_failed")},
               "links_with_other_symbols_than_the_binder": [n for n, r in results.items() if r.get("links") and not r["links"]["same_symbols_as_the_binder_rows"]],
               "edges_new": {k: sum(r["new"][k] for r in ok.values()) for k in ("with_an_edge_out", "edges", "edges_outside_the_lines_of_the_function", "rows_with_an_edge_outside")},
               "edges_before": {k: sum(r["before"][k] for r in ok.values()) for k in ("with_an_edge_out", "edges", "edges_outside_the_lines_of_the_function", "rows_with_an_edge_outside")},
               "doubts": doubts(answers)}
    if len(sys.argv) > 4:
        summary["fingerprints"] = {k: v for k, v in json.loads(pathlib.Path(sys.argv[4]).read_text(encoding="utf-8")).items() if k != "all"}
    (RESULTS / "after.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("| application | http | before | first fix | now | new | nodes before -> now | largest group of the new | lost | unbound |")
    for name, r in results.items():
        if r.get("failed"):
            print(f"| {name} | FAILED {r['failed'][:80]}")
            continue
        g = r["new"]["largest_group"]
        print(f"| {name} | {r['http_rows']} | {r['bound_before']} | {r['bound_after_the_first_fix']} | {r['bound_now']} | {r['newly_bound']} | {r['before']['nodes']} -> {r['now']['nodes']} | "
              f"{g['endpoints']} ({(g['node'] or '')[-45:]}; {g['functions']}) | {r['lost_since_the_first_fix']['endpoints']} | {r['unbound_now']} |")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("applications", "samples", "doubts")}, indent=1)[:5000])


if __name__ == "__main__":
    main()
