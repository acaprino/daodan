"""What the real applications say, from `modal_real.py`'s answers and the sources at the pinned commits (text only, fetched on the host into a
folder outside the repository and never run): per application, the routes the framework's own objects give (the script of the source, read
by the source) and how many of them bind to one function with file and line (the links' binder, over the snapshot of the sources), the endpoints
of the pinned Noir bound the same way, and the two compared: by method and path schema (the routes both find, and for them whether the function
agrees), by function (the same function under another path), and what only one finds. Writes `results/real/<key>-summary.json` and prints it.

    python benchmarks/fastapi-routes/real_summary.py <a folder outside the repository: the sources are fetched into it at the commits of `apps.py`> <a working folder outside it>

Both sides go through Daodan's own code, the one the pre-map would run: `premap.write` with the recorded answers instead of the container
(`noir.read`, `fastapi_app.read`), then `binder.bind`. The path key is `flows.path_schema` of the path as each tool writes it (`/api/users/{user_id}` and
Noir's spelling are both `/api/users/{}`), so a difference is a difference of the route and not of its notation.
"""
import collections
import json
import pathlib
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
from premap import fastapi_app, noir  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

RESULTS = HERE / "results" / "real"
EXAMPLES = 6
# (summary name, application, the image's script variant, Noir's variant)
FIXTURE = ("path:" + str(HERE / "results/noir.json"), "path:" + str(HERE / "results/routes.json"))  # the whole answers (`stdout` is whole under 20,000 characters)
CASES = (("fixture", "fixture", FIXTURE[1], FIXTURE[0]), ("template", "template", "template-script", "template-noir"), ("template-env", "template", "template-script-env", "template-noir"),
         ("template-stub", "template", "template-script-stub", "template-noir"),
         ("users", "users", "users-script", "users-noir"), ("users-cli", "users", "users-cli-script", "users-noir"),
         ("users-declared", "users", "users-cli-script-declared", "users-noir"))


def answer(variant: str) -> dict:
    """The recorded answer of a variant: `results/real/<variant>.json`, or the file a `path:` names (the fixture's, from `modal_probe.py`)."""
    path = pathlib.Path(variant[5:]) if variant.startswith("path:") else RESULTS / f"{variant}.json"
    return {**json.loads(path.read_text(encoding="utf-8")), "root": "/work"}


def bind(manifest, rows):
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        return binder.bind(rows, flows.Facts(store, db), semantic_store._Resolver(db))


def key(row):
    return (row.get("method"), flows.path_schema(row["path"]) or row["path"])


def function(row):
    return None if row.get("gap") else row["symbol"]


def where(row):
    return f"{row['site']}"


def describe(row):
    return {"method": row.get("method"), "path": row["path"], "site": row["site"], "function": function(row), **({"gap": row["gap"]} if row.get("gap") else {})}


def compare(framework, noir_rows):
    """The two lists of bound rows compared: see the module's docstring."""
    ours, theirs = collections.defaultdict(list), collections.defaultdict(list)
    for row in framework:
        ours[key(row)].append(row)
    for row in noir_rows:
        theirs[key(row)].append(row)
    both, left_f, left_n = [], [], []
    for k in {*ours, *theirs}:
        pairs = min(len(ours.get(k, ())), len(theirs.get(k, ())))
        both += list(zip(ours.get(k, ())[:pairs], theirs.get(k, ())[:pairs]))
        left_f += ours.get(k, ())[pairs:]
        left_n += theirs.get(k, ())[pairs:]
    agree = collections.Counter()
    differ = []
    for ours_row, their_row in both:
        a, b = function(ours_row), function(their_row)
        verdict = ("same function" if a and a == b else "noir gives no function" if a and not b else "framework gives no function" if b and not a
                   else "neither gives a function" if not a and not b else "different function")
        agree[verdict] += 1
        agree["same site" if ours_row["site"] == their_row["site"] else "same file" if ours_row["site"].rpartition(":")[0] == their_row["site"].rpartition(":")[0]
              else "other file"] += 1
        if verdict != "same function" or len(differ) < EXAMPLES:
            differ.append({"verdict": verdict, "framework": describe(ours_row), "noir": describe(their_row)})
    other_path, by_function = [], collections.defaultdict(list)
    for row in left_n:
        if function(row):
            by_function[(row.get("method"), function(row))].append(row)
    only_f = []
    for row in left_f:
        found = by_function.get((row.get("method"), function(row))) if function(row) else None
        if found:
            other = found.pop()
            other_path.append({"framework": describe(row), "noir": describe(other)})
            left_n.remove(other)
        else:
            only_f.append(row)
    return {"both": len(both), "agreement": dict(agree), "differences": [d for d in differ if d["verdict"] != "same function"][:EXAMPLES * 2],
            "same_function_other_path": len(other_path), "other_path_examples": other_path[:EXAMPLES],
            "only_framework": len(only_f), "only_framework_examples": [describe(r) for r in only_f[:EXAMPLES]],
            "only_noir": len(left_n), "only_noir_examples": [describe(r) for r in left_n[:EXAMPLES]]}


def summarize(name: str, application: str, script: str, noir_variant: str, sources: pathlib.Path, work: pathlib.Path) -> dict:
    entries.QUERIES.setdefault("fastapi", {"route": {"kind": "rotta"}, "websocket": {"kind": "rotta"}})  # the table the wiring adds
    manifest = work / name / "manifest.sqlite"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    if application == "fixture":  # a copy outside this repository: its own files are not the snapshot's root
        import shutil
        project = work / name / "project"
        shutil.rmtree(project, ignore_errors=True)
        shutil.copytree(HERE / "fixture", project, ignore=shutil.ignore_patterns("__pycache__"))
    else:
        project = apps.fetch(application, sources)
    snapshot.write_snapshot(project, manifest)
    noir_answer, script_answer = answer(noir_variant), answer(script)

    def run(commands):
        return [noir_answer if command["tool"] == "noir" else script_answer for command in commands]
    record = premap.write(manifest, sources=(premap.module_graph, premap.requirements, noir, fastapi_app), runner=run)
    where = {"repository": apps.APPS[application][0], "commit": apps.APPS[application][1], "licence": apps.APPS[application][2],
             "folder": apps.APPS[application][3] or "."} if application != "fixture" else {"repository": "this repository: benchmarks/fastapi-routes/fixture"}
    out = {"name": name, "application": application, **where, "script": {"variant": script, "exit": script_answer["returncode"],
           "seconds": script_answer["seconds"], "peak_memory_mb": script_answer["max_rss_mb"]},
           "noir": {"variant": noir_variant, "exit": noir_answer["returncode"], "seconds": noir_answer["seconds"], "peak_memory_mb": noir_answer["max_rss_mb"]}}
    gaps = [g for g in record["gaps"] if g.get("source", "").startswith(("fastapi@", "noir@"))]
    out["gaps"] = [{"source": g["source"].partition("@")[0], "kind": g["kind"], "path": g.get("path"), "detail": g["detail"][:400]} for g in gaps]
    if script_answer["returncode"] == 0:
        document = json.loads(script_answer["stdout"])
        out["script"].update(application=document["application"], found=document["found"], root_path=document["root_path"],
                             routes=len(document["routes"]), http=sum(r["kind"] == "http" for r in document["routes"]),
                             websocket=sum(r["kind"] == "websocket" for r in document["routes"]), documentation=sum(r["docs"] for r in document["routes"]),
                             unread=document["unread"], competing=document["competing"])
    else:
        out["script"]["stopped"] = script_answer["stderr"].strip()[-300:] or f"exit {script_answer['returncode']}"
    framework_rows = bind(manifest, [r for r in record.get("framework_entries", []) if r["reader"] == "fastapi"])
    http = [r for r in framework_rows if r["shape"] == "route"]
    out["framework"] = {"rows": len(framework_rows), "http_rows": len(http), "bound_to_a_function": sum(not r.get("gap") for r in http),
                        "websocket_rows": len(framework_rows) - len(http),
                        "unbound": [{"path": r["path"], "method": r.get("method"), "gap": r["gap"][:120]} for r in http if r.get("gap")][:EXAMPLES]}
    noir_report = json.loads(noir_answer["stdout"])
    protocols = collections.Counter(e["protocol"] for e in noir_report["endpoints"])
    noir_rows = bind(manifest, [r for r in record.get("noir_entries", []) if r["shape"] == "http"])
    out["noir_report"] = {"endpoints": len(noir_report["endpoints"]), "protocols": dict(protocols), "errors": len(noir_report.get("errors") or ()),
                          "with_a_handler_name": sum(bool((e.get("handler") or {}).get("name")) for e in noir_report["endpoints"]),
                          "rows": len(noir_rows), "bound_to_a_function": sum(not r.get("gap") for r in noir_rows),
                          "unbound": [{"path": r["path"], "method": r.get("method"), "site": r["site"], "gap": r["gap"][:120]} for r in noir_rows if r.get("gap")][:EXAMPLES]}
    out["comparison"] = compare(http, noir_rows)
    return out


def main():
    sources, work = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    for name, application, script, noir_variant in CASES:
        if not (pathlib.Path(script[5:]) if script.startswith("path:") else RESULTS / f"{script}.json").is_file():
            continue
        summary = summarize(name, application, script, noir_variant, sources, work)
        (RESULTS / f"{name}-summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8", newline="\n")
        print(json.dumps(summary, indent=1)[:6000])


if __name__ == "__main__":
    main()
