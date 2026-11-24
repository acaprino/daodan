"""The routes of a Django project from its own loaded URLconf (`premap/django_app.py`) and from OWASP Noir, side by side, over the same tree.

    python benchmarks/django-routes/compare.py <name> [<name> ...]        (Daodan's own Python dependencies; `name`: `fixture` or a project of `real_probe.py`)

It reads what `real_probe.py` kept (`<name>-script.json`, `<name>-noir.json` under `DAODAN_REAL_OUT`) and the local checkout of the same commit
(`DAODAN_REAL_DIR`; the fixture's own folder for `fixture`), and runs Daodan's code only: the snapshot of the tree, the two sources read over
the answers the container gave (`premap.write` with a runner that hands them back) and Daodan's binder (`binder.bind`, the one `flows.link_facts`
calls), which ties each row "a name at a position" to the one function of the snapshot that holds it. Nothing of the project is run, and
nothing of it is written: `results/real/<name>.json` has the counts and, for the differences, route texts and names of functions.

How the two lists are set side by side, in this order (each row of either list is used once):
  1. the same function (the symbol the binder gave) on the same path schema (`flows.path_schema` of the route as each tool writes it);
  2. the same function on another path (the tools spell the route differently, or one of them has no schema);
  3. what is left of each: found by one tool only.
A row is "bound" when the binder tied it to one function of the snapshot (no gap); a class row of the source (`ListView`'s `get` is Django's, so
the route is the project's class: file and line of the class, and a gap that says so) is counted apart.
"""
import functools
import json
import os
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "daodan/core"))

import binder  # noqa: E402
import entries  # noqa: E402
import flows  # noqa: E402
import premap  # noqa: E402
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from premap import django_app, noir  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

OUT = Path(os.environ.get("DAODAN_REAL_OUT", r"D:\daodan-work\django-probe\real-results"))
CHECKOUTS = Path(os.environ.get("DAODAN_REAL_DIR", r"D:\daodan-work\django-probe\real"))
RESULTS = HERE / "results" / "real"
LOCAL = {"fixture": HERE / "fixture", "drf": HERE / "layouts" / "drf"}  # trees of this repository: the fixture, and the DRF layout as the control with known routes
entries.QUERIES.setdefault("django", {"route": {"kind": "rotta"}})  # the table the wiring adds


def answer(name: str, kind: str) -> dict | None:
    path = OUT / f"{name}-{kind}.json"
    if not path.exists():
        return None
    saved = json.loads(path.read_text(encoding="utf-8"))
    return {k: saved[k] for k in ("returncode", "stdout", "stderr", "seconds", "max_rss_mb")} | {"root": "/work"}


def bind(manifest, rows):
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        return binder.bind(rows, flows.Facts(store, db), semantic_store._Resolver(db))


@functools.lru_cache(maxsize=None)
def definitions(path):
    """`{line: line of the def or class}` for every line from the first decorator to the `def` or `class` of a declaration of the Python file `path`
    (the interpreter's own parse): the tools do not cite the same one of those lines (Noir cites a decorator, Django's `def`, `inspect` a class's
    first decorator), and a position is compared by the declaration it is in."""
    import ast
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
        return {}
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for line in range(min([node.lineno, *(d.lineno for d in node.decorator_list)]), node.lineno + 1):
                found[line] = node.lineno
    return found


def canonical(root: Path, row: dict) -> dict:
    """The row with its site moved to the line of the `def` or `class` the cited line belongs to."""
    file, _, line = row["site"].rpartition(":")
    if not file or not line.isdecimal() or not file.endswith(".py"):
        return row
    return {**row, "site": f"{file}:{definitions(str(root / file)).get(int(line), int(line))}"}


def place(row):
    """`file:line` of the row's site, as the tool gave it."""
    return row.get("site")


def schema_of(row):
    return row.get("schema") or row.get("path")


def compare(name: str) -> dict:
    project = LOCAL.get(name) or CHECKOUTS / name
    root = project  # where the files of the tree are, for the lines of the declarations (`project` is a copy for the folders of this repository)
    as_is = answer(name, "script")
    fixed = answer(name, "script-fixed")  # where the pinned requirements do not all build in the image of the measurement (`real_probe.COMPILED`)
    ours, theirs = fixed or as_is, answer(name, "noir")
    out = {"name": name, "script_as_the_runner_restores": {"returncode": as_is["returncode"], "stderr_tail": (as_is["stderr"] or "")[-300:]} if fixed and as_is else None,
           "second_environment": bool(fixed)}
    with tempfile.TemporaryDirectory(dir=os.environ.get("DAODAN_PROBE_TMP")) as scratch:
        if name in LOCAL:  # a folder of this repository: the snapshot of a copy, outside the repository's git, holds all its files
            shutil.copytree(project, Path(scratch) / "project", ignore=shutil.ignore_patterns("__pycache__"))
            project = Path(scratch) / "project"
        manifest = Path(scratch) / "out" / "manifest.sqlite"
        snapshot.write_snapshot(project, manifest)

        def run(commands):
            tool = commands[0]["tool"]
            return [{"django": ours, "noir": theirs}[tool] for _ in commands]
        record = premap.write(manifest, sources=(premap.module_graph, premap.requirements, django_app, noir), runner=run)
        states = {s["source"].split("@")[0]: s["state"] for s in record["sources"] if s["source"].split("@")[0] in ("django", "noir")}
        out["sources"] = states
        out["gaps"] = Counter(f"{g.get('source', '?').split('@')[0]}/{g['kind']}" for g in record["gaps"] if g.get("source", "").split("@")[0] in ("django", "noir"))
        out["gap_details"] = [f"{g['source'].split('@')[0]}: {g['detail'][:400]}" for g in record["gaps"]
                              if g.get("source", "").split("@")[0] in ("django", "noir") and g["kind"] != "outside_snapshot"][:12]
        rows = [r for r in record.get("framework_entries", []) if r["reader"] == "django"]
        if states.get("django") == "not_needed" and ours and ours["returncode"] == 0:
            # the source gives no command for this project (Django is declared where the pre-map does not read it): the rows it would make from
            # the answer of the command it would give, read as `premap` reads them
            with open_snapshot(manifest) as store:
                command = {"tool": "django", "argv": ["sh", "-c", "", "django", "900", ""], "cwd": ".", "env": {}, "network": "none", "venv": "."}
                result = django_app.read(premap.Context(manifest, store), [command], [ours])
                rows = [{**r, "sources": [f"django@{django_app.VERSION}"]} for r in result["facts"].get("framework_entries", [])]
            out["source_state"] = "not_needed: the rows are those of the answer read as if the command were given"
        django_rows = bind(manifest, rows)
        noir_rows = bind(manifest, record.get("noir_entries", []))
    document = json.loads(ours["stdout"]) if ours and ours["returncode"] == 0 and ours["stdout"].strip().startswith("{") else None
    out["script"] = {"returncode": ours and ours["returncode"], "seconds": ours and ours["seconds"], "max_rss_mb": ours and ours["max_rss_mb"],
                     "stderr_tail": (ours["stderr"] or "")[-600:] if ours and ours["returncode"] else None}
    out["noir"] = {"returncode": theirs and theirs["returncode"], "seconds": theirs and theirs["seconds"], "max_rss_mb": theirs and theirs["max_rss_mb"],
                   "stderr_tail": (theirs["stderr"] or "")[-300:] if theirs and theirs["returncode"] else None}
    if document:
        routes = document["routes"]
        in_project = [r for r in routes if any(a["handler"] and not a["handler"]["environment"] for a in r["handlers"])
                      or (r["view"] and not r["view"]["environment"])]
        out["framework"] = {"routes": len(routes), "unread_includes": len(document["unread"]), "locale": document["locale"],
                            "environment_routes": len([r for r in routes if r not in in_project]),
                            "project_routes": len(in_project), "with_schema": len([r for r in routes if r["parts"] and all(
                                r["arguments"].get(p[1]) is True for p in r["parts"] if p[0])]),
                            "rows": len(django_rows)}
    bound_ours = [r for r in django_rows if not r.get("gap")]
    class_rows = [r for r in django_rows if r.get("gap") and "class-based view" in r["gap"] and ":" in r["site"]]
    out["framework"] = {**out.get("framework", {}), "rows_bound_to_a_function": len(bound_ours), "rows_on_a_class_with_file_and_line": len(class_rows),
                        "rows_unbound": len(django_rows) - len(bound_ours) - len(class_rows),
                        "routes_with_a_bound_row": len({r["path"] for r in bound_ours + class_rows})}
    bound_noir = [r for r in noir_rows if not r.get("gap")]
    out["noir"] = {**out["noir"], "endpoints": len(noir_rows), "with_handler_name": len([r for r in noir_rows if r.get("handler")]),
                   "bound_to_a_function": len(bound_noir), "unbound": len(noir_rows) - len(bound_noir),
                   "protocols": dict(Counter(r["shape"] for r in noir_rows)), "methods": dict(Counter(r.get("method") for r in noir_rows))}
    # a route of the framework (a path, as the rows of it carry it) is looked up in Noir's list by the position of its function: the site
    # `file:line` the two tools cite (the binder's name is not needed: Noir names a class where the function is a method of it). Then the path:
    # the same schema, or the same text; a `re_path` is a regular expression for Django and a template with `{name}` for Noir, and nothing here
    # reads one to make it the other, so those are counted as the same function written differently
    django_rows = [canonical(root, row) for row in django_rows]
    noir_rows = [canonical(root, row) for row in noir_rows]
    ours_sites, ours_schema = defaultdict(set), {}
    for row in django_rows:
        ours_sites[row["path"]].add(row["site"])
        ours_schema[row["path"]] = row.get("schema")
    http = [row for row in noir_rows if row["shape"] == "http"]
    noir_at = defaultdict(list)
    for row in http:
        noir_at[row["site"]].append(row)

    def agree(path, row):
        return (ours_schema[path] is not None and ours_schema[path] == row.get("schema")) or path == row["path"]
    same_path, other_spelling, only_ours = [], [], []
    for path, sites in sorted(ours_sites.items()):
        near = [n for site in sites for n in noir_at.get(site, ())]
        if not near:
            only_ours.append(path)
        else:
            (same_path if any(agree(path, n) for n in near) else other_spelling).append(path)
    ours_all_sites = set().union(*ours_sites.values()) if ours_sites else set()
    noir_distinct = {(n["site"], n["path"]) for n in http}
    noir_elsewhere = sorted((site, path) for site, path in noir_distinct if site not in ours_all_sites)
    functions = {r["path"] for r in django_rows if r.get("method") is None and not r.get("gap")}
    noir_sites = set(noir_at)
    code_sites = {s for s in noir_sites if not s.startswith("docs/")}  # a route Noir reads out of a documentation file is no function of the project
    functions_of_ours = {r["site"] for r in django_rows if not r.get("gap")}  # a row with a gap is a gap of the links, not an entry
    classes_of_ours = {r["site"] for r in django_rows if r.get("gap") and "class-based view" in r["gap"]}
    out["by_function"] = {  # the unit of an entry: a function at its file and line
        "framework_functions": len(functions_of_ours), "framework_classes_with_a_gap": len(classes_of_ours), "noir_sites": len(noir_sites),
        "functions_both": len(functions_of_ours & noir_sites), "functions_only_framework": len(functions_of_ours - noir_sites),
        "classes_noir_cites": len(classes_of_ours & noir_sites), "classes_only_framework": len(classes_of_ours - noir_sites),
        "only_noir": len(code_sites - functions_of_ours - classes_of_ours), "only_noir_in_documentation_files": len(noir_sites - code_sites)}
    out["comparison"] = {
        "framework_routes_with_a_row": len(ours_sites),
        "noir_cites_the_same_function": len(same_path) + len(other_spelling), "of_which_same_path": len(same_path),
        "of_which_path_written_differently": len(other_spelling), "only_framework": len(only_ours),
        "noir_http_endpoints_distinct_site_and_path": len(noir_distinct), "of_which_on_a_function_the_framework_lists": len(noir_distinct) - len(noir_elsewhere),
        "of_which_on_a_site_the_framework_does_not_list": len(noir_elsewhere),
        "noir_paths_with_an_unresolved_prefix": len([n for n in http if "{}" in n["path"]]),
        "function_views_the_framework_gives_no_method_for": len(functions),
        "of_which_noir_gives_a_method_at_that_function": len({path for path in functions if any(
            n.get("method") in ("GET", "POST", "PUT", "PATCH", "DELETE") for site in ours_sites[path] for n in noir_at.get(site, ()))})}
    out["examples"] = {
        "path_written_differently": [f"{p} {sorted(ours_sites[p])} | noir {[n['path'] for s in ours_sites[p] for n in noir_at.get(s, ())][:2]}" for p in other_spelling][:15],
        "only_framework": [f"{p} {sorted(ours_sites[p])}" for p in only_ours][:30],
        "only_noir_site": [f"{path} ({site})" for site, path in noir_elsewhere][:40],
        "noir_unbound": [f"{r.get('method')} {r['path']} ({r['site']}): {r['gap'][:90]}" for r in noir_rows if r.get("gap")][:12]}
    return out


if __name__ == "__main__":
    RESULTS.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:]:
        found = compare(name)
        (RESULTS / f"{name}.json").write_text(json.dumps(found, indent=1, default=dict), encoding="utf-8")
        print(json.dumps({k: v for k, v in found.items() if k != "examples"}, indent=1, default=dict))
