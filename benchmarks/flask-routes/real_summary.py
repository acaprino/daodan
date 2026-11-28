"""What the real applications say, from `modal_real.py`'s answers and the sources at the pinned commits (text only, fetched on the host into a
folder outside the repository and never run): per application and variant of the script, the routes Flask's own `url_map` gives (the script of the
source), what the source of the pre-map makes of them (the rows, the gaps and why, and how many rows bind to one function with file and line: the
links' binder, over the snapshot of the sources), the endpoints of the pinned Noir bound the same way, and the two compared: by method and path schema
(the routes both find, and for them whether the function and its file and line agree), by function (the same function under another path), and what
only one finds. Writes `results/real/<name>-summary.json` and prints it.

    python -I benchmarks/flask-routes/real_summary.py <a folder outside the repository: the sources are fetched into it at the commits of `apps.py`> <a working folder>

Both sides go through Daodan's own code, the one the pre-map would run: `premap.write` with the recorded answers instead of the container
(`noir.read`, `flask_app.read`), then `binder.bind`. The path key is `flows.path_schema` of the path as each tool writes it (`/api/users/<int:id>` and
Noir's spelling are both `/api/users/{}`), so a difference is a difference of the route and not of its notation; it is made from the rule's own text
here, which the source's `schema` does not do for an argument that may hold a `/`. The Noir endpoints counted are the ones of a Python file: the
JavaScript of a front end in the same repository is not Flask.
"""
import collections
import json
import pathlib
import posixpath
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "daodan/core"))
import apps  # noqa: E402
import binder  # noqa: E402
import entries  # noqa: E402
import flows  # noqa: E402
import premap  # noqa: E402
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from entry_points import flask_app, noir  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

RESULTS = HERE / "results" / "real"
EXAMPLES = 8
FIXTURE = "path:" + str(HERE / "results/routes.json")  # the script's answer of `modal_probe.py` on the fixture
# (summary name, application, the script's variant, Noir's variant)
CASES = (("fixture", "fixture", FIXTURE, "fixture-noir"),
         ("ctfd", "ctfd", "ctfd-script", "ctfd-noir"),
         ("redash", "redash", "redash-script", "redash-noir"),
         ("redash-frozen", "redash", "redash-frozen-script", "redash-noir"),
         ("redash-declared", "redash", "redash-frozen-script-declared", "redash-noir"),
         ("redash-secret", "redash", "redash-frozen-script-secret", "redash-noir"),
         ("redash-redis", "redash", "redash-frozen-script-redis", "redash-noir"),
         ("shhh", "shhh", "shhh-script", "shhh-noir"),
         ("shhh-testing", "shhh", "shhh-script-testing", "shhh-noir"),
         ("microblog-api", "microblog-api", "microblog-api-script", "microblog-api-noir"))


def answer(variant: str) -> dict:
    """The recorded answer of a variant: `results/real/<variant>.json`, or the file a `path:` names (the fixture's, from `modal_probe.py`)."""
    path = pathlib.Path(variant[5:]) if variant.startswith("path:") else RESULTS / f"{variant}.json"
    return {**json.loads(path.read_text(encoding="utf-8")), "root": "/work"}


def present(variant: str) -> bool:
    return (pathlib.Path(variant[5:]) if variant.startswith("path:") else RESULTS / f"{variant}.json").is_file()


def bind(manifest, rows):
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        return binder.bind(rows, flows.Facts(store, db), semantic_store._Resolver(db))


def _position_before(row: dict, facts) -> dict:
    """`binder._position` as it was before the qualified-name match (the commit this benchmark measured first): the row's handler is the snapshot
    declaration's `name`, at the row's line."""
    file, _, line = row["site"].rpartition(":")
    at = int(line) if line.isdecimal() else 0
    matches = [d for d in facts.functions.get(file, ()) if row["handler"] == d["name"] and d["line"] <= at <= (d["end"] or d["line"])]
    if len(matches) == 1:
        return {**row, "symbol": facts.node(matches[0]["id"]), "handler_source": row["reader"]}
    return {**row, "gap": f"{row['reader']} reports this entry without a unique snapshot handler at its site"}


def bind_before(manifest, rows):
    """`bind` with the earlier `_position`, for the table of what the qualified-name match changed."""
    current = binder._position
    binder._position = _position_before
    try:
        return bind(manifest, rows)
    finally:
        binder._position = current


def why_unbound(manifest, rows):
    """For each row the binder leaves without a function: what the snapshot holds at its file and line: the declarations that cover the line, and the
    ones elsewhere in the file with the handler's name or qualified name."""
    out = []
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        facts = flows.Facts(store, db)
        for row in rows:
            file, _, line = row["site"].rpartition(":")
            at = int(line) if line.isdecimal() else 0
            handler = row.get("handler")
            last = (handler or "").rpartition(".")[2]
            functions = facts.functions.get(file, ())
            describe_one = lambda d: {"name": d["name"], "qualified_name": d.get("qualified_name"), "line": d["line"], "end": d["end"]}
            out.append({"method": row.get("method"), "path": row["path"], "site": row["site"], "handler": handler,
                        "covering_the_line": [describe_one(d) for d in functions if d["line"] <= at <= (d["end"] or d["line"])],
                        "same_name_elsewhere": [describe_one(d) for d in functions if handler and last in (d["name"], (d.get("qualified_name") or "").rpartition(".")[2])
                                                and not d["line"] <= at <= (d["end"] or d["line"])][:4]})
    return out


def schema(path: str) -> str:
    return flows.path_schema(path) or path


def function(row):
    return None if row is None or row.get("gap") else row["symbol"]


def site(row) -> str:
    return row["site"]


def describe(row):
    return {"method": row.get("method"), "path": row["path"], "site": row["site"], "function": function(row), **({"gap": row["gap"][:160]} if row.get("gap") else {})}


def routes_of(document: dict, headers: set[str], folder: str = ".") -> list[dict]:
    """Each route Flask serves (a rule with a view, not `build_only` and not a redirect) with what the source makes of it: the project's function, a
    class-based view, a view of a package of the restored environment (an extension's, with the package), Flask's own static rule, or a view with no
    file of the snapshot. The same decision `flask_app._rules` takes; the rows and gaps of the source itself are counted from its own output."""
    out = []
    for route in document["routes"]:
        if route["build_only"] or route["redirect_to"]:
            continue
        handler = route["handler"]
        file = posixpath.normpath(posixpath.join(folder, handler["file"])) if handler and handler.get("file") else None
        outside = file is None or file.startswith("..") or file not in headers
        if outside and handler and handler["environment"]:
            what = "static" if route["static"] else "installed copy" if handler.get("distribution") else "package view"
            module = (handler.get("module") or "?").split(".")[0]
        elif outside:
            what, module = "no function" if handler is None else "no file", None
        else:
            what, module = ("class-based view" if handler["kind"] == "class" else "project function"), None
        out.append({"rule": route["rule"], "methods": route["methods"] or [None], "category": what, "package": module,
                    "view": (handler or {}).get("qualname"), "file": file if what in ("project function", "class-based view") else None,
                    "line": (handler or {}).get("line")})
    return out


def compare(flask_routes, framework_rows, noir_rows):
    """Flask's routes (`routes_of`, each by method) against Noir's bound rows. A Flask route that is a project function or a class-based view has
    its row of the source (`framework_rows`, bound), the others are gaps or silent."""
    theirs = collections.defaultdict(list)
    for row in noir_rows:
        theirs[(row.get("method"), schema(row["path"]))].append(row)
    rows_of = collections.defaultdict(list)
    for row in framework_rows:
        rows_of[(row.get("method"), row["path"])].append(row)
    both, only_flask = [], []
    agreement = collections.Counter()
    differences, class_mismatches = [], []
    used = set()
    for route in flask_routes:
        if route["category"] == "static":
            continue
        for method in route["methods"]:
            key = (method, schema(route["rule"]))
            row = (rows_of.get((method, route["rule"])) or [None])[0]
            found = [r for r in theirs.get(key, ()) if id(r) not in used]
            item = {"method": method, "path": route["rule"], "category": route["category"], "view": route["view"], "package": route["package"], "row": row}
            if not found:
                only_flask.append(item)
                continue
            other = found[0]
            used.add(id(other))
            ours, theirs_function = function(row), function(other)
            verdict = ("same function" if ours and ours == theirs_function else "framework gives no function" if theirs_function and not ours
                       else "noir gives no function" if ours and not theirs_function else "neither gives a function" if not ours and not theirs_function
                       else "different function")
            agreement[verdict] += 1
            if row is not None and row.get("gap") and " is a class-based view" in row["gap"] and theirs_function:
                # the source's gap names the view's class and its file; Noir's function, once bound, carries its class and its file
                file, _, qualified = theirs_function.partition("::")
                same_class = file == row["site"] and qualified.rpartition(".")[0] == row["gap"].partition(" is a class-based view")[0]
                agreement["class view: same class and file" if same_class else "class view: another class or file"] += 1
                if not same_class and len(class_mismatches) < EXAMPLES:
                    class_mismatches.append({"flask": describe(row), "noir": describe(other)})
            if row is not None:
                agreement["same site" if site(row) == site(other) else "same file" if site(row).rpartition(":")[0] == site(other).rpartition(":")[0]
                          or site(row) == site(other).rpartition(":")[0] else "other file"] += 1
            both.append(item)
            if verdict != "same function" and len(differences) < EXAMPLES * 2:
                differences.append({"verdict": verdict, "flask": {"method": method, "path": route["rule"], "category": route["category"],
                                                                   **({"row": describe(row)} if row else {})}, "noir": describe(other)})
    only_noir = [r for rows in theirs.values() for r in rows if id(r) not in used]
    by_function = collections.defaultdict(list)
    for row in only_noir:
        if function(row):
            by_function[(row.get("method"), function(row))].append(row)
    other_path, truly_only_flask = [], []
    for item in only_flask:
        found = by_function.get((item["method"], function(item["row"]))) if function(item["row"]) else None
        if found:
            other = found.pop()
            other_path.append({"flask": {"method": item["method"], "path": item["path"], **describe(item["row"])}, "noir": describe(other)})
            only_noir.remove(other)
        else:
            truly_only_flask.append(item)
    categories = collections.Counter(item["category"] for item in truly_only_flask)
    packages = collections.Counter(item["package"] for item in truly_only_flask if item["category"] == "package view")
    return {"both": len(both), "agreement": dict(agreement), "class_view_mismatches": class_mismatches, "differences": differences[:EXAMPLES * 2],
            "same_function_other_path": len(other_path), "other_path_examples": other_path[:EXAMPLES],
            "only_flask": len(truly_only_flask), "only_flask_by_category": dict(categories), "only_flask_packages": dict(packages.most_common(8)),
            "only_flask_examples": [{"method": i["method"], "path": i["path"], "category": i["category"], "view": i["view"], "package": i["package"]}
                                    for i in truly_only_flask[:EXAMPLES]],
            "only_noir": len(only_noir), "only_noir_examples": [describe(r) for r in only_noir[:EXAMPLES]]}


def summarize(name: str, application: str, script: str, noir_variant: str, sources: pathlib.Path, work: pathlib.Path) -> dict:
    entries.QUERIES.setdefault("flask", {"route": {"kind": "rotta"}})  # the table `entry-queries.json` no longer has: the source is not wired
    manifest = work / name / "manifest.sqlite"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    if application == "fixture":  # a copy outside this repository: its own files are not the snapshot's root
        import shutil
        project = work / name / "project"
        shutil.rmtree(project, ignore_errors=True)
        shutil.copytree(HERE / "fixture", project, ignore=shutil.ignore_patterns("__pycache__"))
        manifest.unlink(missing_ok=True)
    else:
        project = apps.fetch(application, sources)
    if not manifest.exists():  # a large project takes minutes to write: the manifest of an earlier case of the same application is kept
        shared = work / application / "manifest.sqlite"
        if application != "fixture" and shared.exists():
            manifest = shared
        else:
            snapshot.read_project(project, manifest)
    noir_answer, script_answer = answer(noir_variant), answer(script)

    def run(commands):
        return [noir_answer if command["tool"] == "noir" else script_answer for command in commands]
    record = premap.write(manifest, sources=(premap.module_graph, premap.requirements, noir, flask_app), runner=run)
    where = {"repository": apps.APPS[application][0], "commit": apps.APPS[application][1], "licence": apps.APPS[application][2],
             "folder": apps.APPS[application][3] or "."} if application != "fixture" else {"repository": "this repository: benchmarks/flask-routes/fixture"}
    out = {"name": name, "application": application, **where, "script": {"variant": pathlib.Path(script[5:]).name if script.startswith("path:") else script,
                                                                           "exit": script_answer["returncode"],
           "seconds": script_answer["seconds"], "peak_memory_mb": script_answer["max_rss_mb"]},
           "noir": {"variant": noir_variant, "exit": noir_answer["returncode"], "seconds": noir_answer["seconds"], "peak_memory_mb": noir_answer["max_rss_mb"]}}
    if script_answer.get("left_in_the_project"):
        out["script"]["left_in_the_project"] = [f for f in script_answer["left_in_the_project"] if "__pycache__" not in f][:10]
    gaps = [g for g in record["gaps"] if g.get("source", "").startswith(("flask@", "noir@"))]
    out["gaps"] = [{"source": g["source"].partition("@")[0], "kind": g["kind"], "path": g.get("path"), "detail": g["detail"][:500]} for g in gaps]
    framework_rows, flask_routes = [], []
    if script_answer["returncode"] == 0:
        document = json.loads(script_answer["stdout"])
        with open_snapshot(manifest) as store:
            headers = set(store.iter_paths())  # the files the snapshot holds: what `context.inventory.headers` is made of
        flask_routes = routes_of(document, headers)
        served = [r for r in flask_routes if r["category"] != "static"]
        out["flask"] = {"rules": len(document["routes"]), "not_served": len(document["routes"]) - len(flask_routes), "static": len(flask_routes) - len(served),
                        "dispatch": document["dispatch"],
                        "by_category": dict(collections.Counter(r["category"] for r in served)),
                        "package_views": dict(collections.Counter(r["package"] for r in served if r["category"] == "package view").most_common(10)),
                        "routes_by_method": sum(len(r["methods"]) for r in served)}
        framework_rows = bind(manifest, [r for r in record.get("framework_entries", []) if r["reader"] == "flask"])
        out["source"] = {"rows": len(framework_rows), "bound_to_a_function": sum(not r.get("gap") for r in framework_rows),
                         "class_based_gap_rows": sum(bool(r.get("gap")) and "class-based view" in r["gap"] for r in framework_rows),
                         "other_unbound": [{"path": r["path"], "method": r.get("method"), "gap": r["gap"][:140]} for r in framework_rows
                                           if r.get("gap") and "class-based view" not in r["gap"]][:EXAMPLES]}
    else:
        out["script"]["stopped"] = script_answer["stderr"].strip()[-400:] or f"exit {script_answer['returncode']}"
    noir_report = json.loads(noir_answer["stdout"])
    protocols = collections.Counter(e["protocol"] for e in noir_report["endpoints"])
    noir_http = [r for r in record.get("noir_entries", []) if r["shape"] == "http"]
    noir_all = bind(manifest, noir_http)
    python = [r for r in noir_all if r["site"].partition(":")[0].endswith(".py")]
    # Noir names a method `Class.method` (`Api.get`): the binder matched it against the declaration's `name` (`get`) only, and now against its qualified
    # name too. Before: the earlier match; plain: the same rows with the name of the method alone, to tell what Noir's own file and line are worth
    before = [r for r in bind_before(manifest, noir_http) if r["site"].partition(":")[0].endswith(".py")]
    plain = bind(manifest, [{**r, "handler": r["handler"].rpartition(".")[2]} if r.get("handler") else r for r in noir_http])
    plain_python = [r for r in plain if r["site"].partition(":")[0].endswith(".py")]
    key = lambda r: (r["path"], r.get("method"), r["site"], r.get("handler"))
    bound_after = {key(r) for r in python if not r.get("gap")}
    lost = [r for r in plain_python if not r.get("gap") and key({**r, "handler": next((q["handler"] for q in python if (q["path"], q.get("method"), q["site"]) == (r["path"], r.get("method"), r["site"])), r.get("handler"))}) not in bound_after]
    out["noir_report"] = {"endpoints": len(noir_report["endpoints"]), "protocols": dict(protocols), "errors": len(noir_report.get("errors") or ()),
                          "python_files": collections.Counter(pathlib.PurePosixPath(
                              (e.get("handler") or {}).get("path") or ((e.get("details") or {}).get("code_paths") or [{}])[0].get("path") or "").suffix
                              for e in noir_report["endpoints"]).most_common(6),
                          "http_rows": len(noir_all), "python_rows": len(python), "python_bound_to_a_function": sum(not r.get("gap") for r in python),
                          "python_with_a_handler_name": sum(bool(r.get("handler")) for r in python),
                          "python_with_a_qualified_name": sum("." in (r.get("handler") or "") for r in python),
                          "python_bound_before_the_qualified_name_match": sum(not r.get("gap") for r in before),
                          "python_bound_with_the_method_name_alone": sum(not r.get("gap") for r in plain_python),
                          "unbound_after": why_unbound(manifest, [r for r in python if r.get("gap")]),
                          "bound_by_the_name_alone_and_not_by_the_qualified_name": why_unbound(manifest, [
                              next(q for q in python if (q["path"], q.get("method"), q["site"]) == (r["path"], r.get("method"), r["site"])) for r in lost])}
    out["comparison"] = compare(flask_routes, framework_rows, python) if flask_routes else None
    out["comparison_with_the_method_name_alone"] = compare(flask_routes, framework_rows, plain_python) if flask_routes else None
    return out


def main():
    sources, work = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    for name, application, script, noir_variant in CASES:
        if (only and name not in only) or not present(script) or not present(noir_variant):
            continue
        summary = summarize(name, application, script, noir_variant, sources, work)
        (RESULTS / f"{name}-summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
        print(json.dumps(summary, indent=1)[:5000])


if __name__ == "__main__":
    main()
