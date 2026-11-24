"""From the answers of `modal_binding.py` (one file per application in the evidence folder) to the counts of `results/`: per application, how many endpoints
Noir gives, how many have a handler name, how many Daodan's binder ties to one function, the causes of the others, and what each candidate fix of
`causes.FIXES` would do (on the unbound endpoints: bind to one function, to several, to none; on the bound ones: agree with the binding, or differ).
Writes `results/<name>.json` and `results/summary.json` and prints the table.

    python -I benchmarks/noir-binding/summarize.py <the evidence folder of modal_binding.py> [name,name,...]

The evidence is not in the repository (it holds Noir's endpoints); the results keep the counts and a few endpoints per cause, as Noir wrote them.
"""
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apps  # noqa: E402
import causes  # noqa: E402

RESULTS = HERE / "results"
EXAMPLES = 3


def example(row: dict) -> dict:
    """An endpoint as Noir wrote it and what the snapshot holds at its line: a few fields, no source."""
    handler = row.get("handler") or {}
    out = {"method": row.get("method"), "url": row.get("url"), "site": row.get("site"),
           "noir_handler": {k: v for k, v in handler.items() if v is not None} or None}
    for key in ("covering", "named_in_file", "after"):
        if row.get(key):
            out[key] = [f"{d['qn'] or d['name']} {d['line']}-{d['end']}" for d in row[key][:2]]
    if row.get("named_elsewhere"):
        out["named_elsewhere"] = [f"{d['file']}: {d['qn'] or d['name']} {d['line']}" for d in row["named_elsewhere"][:2]]
    if row.get("file_header") is not None:
        out["file_language"] = row["file_header"].get("language")
    return out


def form(name: str | None) -> str:
    """How Noir writes a handler's name: none, the word `closure`, or the characters that join its parts."""
    if not name:
        return "none"
    if name == causes.CLOSURE:
        return "closure"
    joined = "".join(sorted({c for c in name if not (c.isalnum() or c in "_$")}))
    return f"name joined by {joined!r}" if joined else "name"


def unique(declarations: list[dict], row: dict) -> list[dict]:
    seen = {}
    for d in declarations:
        seen[(d.get("file") or row["file"], d["name"], d["line"])] = d
    return list(seen.values())


def anonymous(d: dict) -> bool:
    return d["name"].startswith("(")  # the snapshot's name for a function with none: `(anonymous)`, `(lambda)`, `(func)`


def fixes(rows: list[dict]) -> dict:
    out = {}
    for fix in causes.FIXES:
        unbound, bound = collections.Counter(), collections.Counter()
        functions = set()
        for row in rows:
            found = unique(causes.candidates(row, fix), row)
            if row["ok"]:
                truth = [d for d in row["covering"] if row["row_handler"] in (d["name"], d["qn"])]
                bound["none" if not found else "many" if len(found) > 1 else "same" if truth and causes.same(found[0], truth[0]) else "different"] += 1
                continue
            if fix in causes.FOR_NO_HANDLER and row["row_handler"] is not None:
                continue  # a fix for the endpoints Noir gives no handler is not asked of the others
            unbound["none" if not found else "many" if len(found) > 1 else "one"] += 1
            if len(found) == 1:
                if "(" in (row["row_handler"] or ""):
                    unbound["one, the name has call parentheses (the function bound makes the handler)"] += 1
                functions.add((row["file"] if not found[0].get("file") else found[0]["file"], found[0]["name"], found[0]["line"]))
                if (row["row_handler"] not in (None, causes.CLOSURE) and not anonymous(found[0]) and causes.last_of(found[0]) != causes.tail(row["row_handler"])
                        and not causes.candidates(row, "class-of-covering")):
                    unbound["one, and the function has another name than the handler's"] += 1
        out[fix] = {"unbound": dict(unbound), "bound": dict(bound), "distinct_functions_of_the_unbound_one": len(functions)}
    return out


def agreement(rows: list[dict], a: str, b: str) -> dict:
    """On the unbound rows both fixes bind to one function: whether it is the same."""
    out = collections.Counter()
    for row in rows:
        if row["ok"]:
            continue
        fa, fb = unique(causes.candidates(row, a), row), unique(causes.candidates(row, b), row)
        if len(fa) == 1 and len(fb) == 1:
            out["both bind, same function" if causes.same(fa[0], fb[0]) else "both bind, different functions"] += 1
        elif len(fa) == 1 or len(fb) == 1:
            out[f"only {a if len(fa) == 1 else b} binds"] += 1
    return dict(out)


def summarize(name: str, answer: dict) -> dict:
    framework, repository, commit, licence, licence_file, note = apps.APPS[name]
    out = {"name": name, "framework": framework, "repository": repository, "commit": commit, "licence": licence, "licence_file": licence_file}
    if answer.get("failed") or answer["noir"]["returncode"] != 0:
        return {**out, "failed": answer.get("failed") or answer["noir"]}
    if answer["noir_pin"] != apps.NOIR[1]:
        raise ValueError(f"{name}: the Noir that ran is not the one `apps.NOIR` pins ({answer['noir_pin']})")
    rows = answer["rows"]
    stages = collections.Counter(causes.stage(r) for r in rows)
    http = [r for r in rows if causes.stage(r) == "http"]
    bound = [r for r in http if r["ok"]]
    unbound = [r for r in http if not r["ok"]]
    by_suffix = collections.defaultdict(collections.Counter)
    for r in http:
        s = by_suffix[causes.suffix(r)]
        s["endpoints"] += 1
        s["with_handler_name"] += bool(r["row_handler"])
        s["bound"] += r["ok"]
    grouped = collections.defaultdict(list)
    for r in unbound:
        grouped[causes.cause(r)].append(r)
    groups = collections.Counter(group for group, _ in (causes.cause(r) for r in unbound))
    left = [r for r in rows if causes.stage(r) in ("dropped", "no path")]
    out.update({
        "noir": {**{k: answer["noir"][k] for k in ("endpoints", "protocols", "errors", "seconds", "peak_memory_mb")}, "pin": answer["noir_pin"],
                 "handler_forms": dict(collections.Counter(form((r.get("handler") or {}).get("name")) for r in rows).most_common()),
                 "http_handler_forms": dict(collections.Counter(form((r.get("handler") or {}).get("name")) for r in rows if r.get("protocol") == "http").most_common()),
                 "http_endpoints_in_the_json": sum(r.get("protocol") == "http" for r in rows),
                 "tagged_spec_only": sum("spec-only" in (r.get("tags") or ()) for r in rows),
                 "with_handler_name_in_the_json": sum(bool((r.get("handler") or {}).get("name")) for r in rows),
                 "with_name_and_path_and_line": sum(bool((r.get("handler") or {}).get("name") and (r.get("handler") or {}).get("path") and (r.get("handler") or {}).get("line")) for r in rows)},
        "before_the_binder": {"other_protocol": stages["other protocol"], "no_path": stages["no path"], "dropped": stages["dropped"],
                              "dropped_by_reason": {f"{k[0]} ({k[1]})": v for k, v in collections.Counter(
                                  (r["dropped"].partition(":")[0], causes.suffix(r)) for r in left if not r["dropped"].startswith("no path")).most_common(6)},
                              "dropped_with_name_and_path": sum(bool((r.get("handler") or {}).get("name") and (r.get("handler") or {}).get("path")) for r in left)},
        "checkout": {"files": answer["files"], "left_in_the_project": answer["left_in_the_project"], "changed_in_the_project": answer["changed_in_the_project"]},
        "snapshot": {**{k: answer["snapshot"][k] for k in ("files", "functions", "functions_by_suffix", "files_by_suffix")}, "seconds": answer["snapshot_seconds"]},
        "http": {"endpoints": len(http), "with_handler_name": sum(bool(r["row_handler"]) for r in http), "bound_to_one_function": len(bound),
                 "unbound": len(unbound), "by_file_suffix": {s: dict(c) for s, c in sorted(by_suffix.items(), key=lambda kv: -kv[1]["endpoints"])[:12]}},
        "unbound_by_group": dict(groups.most_common()),
        "causes": {c: {"group": g, "endpoints": len(rs), "by_file_suffix": dict(collections.Counter(causes.suffix(r) for r in rs).most_common(4)), "examples": [example(r) for r in rs[:EXAMPLES]]}
                   for (g, c), rs in sorted(grouped.items(), key=lambda kv: -len(kv[1]))},
        "fixes": fixes(http),
        "fixes_agree": agreement(http, "last-part-covering", "starts-at-line"),
        "code": answer["daodan"],
    })
    return out


def pooled(results: list[dict]) -> dict:
    http = [r["http"] for r in results if r.get("http")]
    fixes_total = {}
    for fix in causes.FIXES:
        unbound, bound, distinct = collections.Counter(), collections.Counter(), 0
        for r in results:
            if r.get("fixes"):
                unbound.update(r["fixes"][fix]["unbound"])
                bound.update(r["fixes"][fix]["bound"])
                distinct += r["fixes"][fix]["distinct_functions_of_the_unbound_one"]
        fixes_total[fix] = {"unbound": dict(unbound), "bound": dict(bound), "distinct_functions_of_the_unbound_one": distinct}
    cause_total, group_total = collections.Counter(), collections.Counter()
    for r in results:
        for c, found in (r.get("causes") or {}).items():
            cause_total[f"{found['group']}: {c}"] += found["endpoints"]
            group_total[found["group"]] += found["endpoints"]
    suffixes = collections.defaultdict(collections.Counter)
    for r in results:
        for s, c in ((r.get("http") or {}).get("by_file_suffix") or {}).items():
            suffixes[s].update(c)
    return {"applications": len(results), "noir_endpoints": sum(r["noir"]["endpoints"] for r in results if r.get("noir")),
            "http_endpoints": sum(h["endpoints"] for h in http), "with_handler_name": sum(h["with_handler_name"] for h in http),
            "bound_to_one_function": sum(h["bound_to_one_function"] for h in http), "unbound": sum(h["unbound"] for h in http),
            "by_file_suffix": {s: dict(c) for s, c in sorted(suffixes.items(), key=lambda kv: -kv[1]["endpoints"])[:14]}, "unbound_by_group": dict(group_total.most_common()), "causes": dict(cause_total.most_common()), "fixes": fixes_total}


GROUPS = (causes.NOT_CODE, causes.NO_FUNCTION, causes.NO_HANDLER, causes.MISMATCH, causes.OTHER)


def table(results: dict) -> str:
    """The table of the README: one line per application."""
    head = ["application", "framework", "Noir endpoints", "before the binder", "http", "with a name", "bound", "unbound", *[g.split(":")[0][:28] for g in GROUPS]]
    lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head)]
    for name, r in results.items():
        if r.get("failed"):
            lines.append(f"| {name} | {r['framework']} | failed |" + " |" * (len(head) - 3))
            continue
        h, b = r["http"], r["before_the_binder"]
        groups = r["unbound_by_group"]
        lines.append(f"| {name} | {r['framework']} | {r['noir']['endpoints']} | {b['other_protocol'] + b['no_path'] + b['dropped']} | {h['endpoints']} | {h['with_handler_name']} | {h['bound_to_one_function']} | "
                     f"{h['unbound']} | " + " | ".join(str(groups.get(g, 0)) for g in GROUPS) + " |")
    return "\n".join(lines)


def main():
    evidence = pathlib.Path(sys.argv[1])
    only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    RESULTS.mkdir(exist_ok=True)
    results = {}
    for name in apps.APPS:
        path = evidence / f"{name}.json"
        if (only and name not in only) or not path.is_file():
            continue
        result = summarize(name, json.loads(path.read_text(encoding="utf-8")))
        (RESULTS / f"{name}.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        results[name] = result
    by_framework = collections.defaultdict(list)
    for name, result in results.items():
        by_framework[result["framework"]].append(result)
    summary = {"noir": apps.NOIR, "by_framework": {f: pooled([r for r in rs if not r.get("failed")]) for f, rs in by_framework.items()},
               "all": pooled([r for rs in by_framework.values() for r in rs if not r.get("failed") and r["framework"] != "flask"]),
               "failed": {n: r["failed"] for n, r in results.items() if r.get("failed")}}
    if not only:
        (RESULTS / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(table(results))
    for name, result in results.items():
        http = result.get("http") or {}
        print(f"{name:26} {result['framework']:14} noir={result.get('noir', {}).get('endpoints')} http={http.get('endpoints')} named={http.get('with_handler_name')} "
              f"bound={http.get('bound_to_one_function')} unbound={http.get('unbound')}" + (f" FAILED {result['failed']}" if result.get("failed") else ""))
        for cause, found in (result.get("causes") or {}).items():
            print(f"    {found['endpoints']:5}  [{found['group'][:22]}] {cause}  {found['by_file_suffix']}")


if __name__ == "__main__":
    main()
