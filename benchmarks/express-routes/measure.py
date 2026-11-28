"""What runs in the container for one application, for Express (`modal_compare.py`) and for Hono (`hono-routes/modal_probe.py --compare`):
the checkout is at `/work` and nothing of it runs. Daodan's snapshot (`snapshot.read_project`), `noir scan` as `noir.commands` gives it,
its answer recorded and bound as the step does (`entry_points.write` with Noir alone), the module's rows of `sections` (`express.rows`)
bound by `binder.bind` on new `flows.Facts`, and `counts.compare`; with `packages`, only Noir's rows in the files that import one of
them are compared (a monorepo's routes of other libraries do not count); with `rules`, the links with those rules alone (`flows.link_facts`).
"""
import os
import pathlib
import sys



def brief(row: dict) -> dict:
    return {k: row[k] for k in ("reader", "shape", "method", "path", "schema", "site", "registered", "span", "handler", "symbol", "function", "gap")
            if row.get(k) is not None}


def identify(rows: list[dict], facts) -> None:
    """Each bound row's `function`: the declaration whose own node is the row's symbol (one function, whatever name a route gave it), else
    the symbol (a node several functions share)."""
    own = {}
    for declared in facts.functions.values():
        for function in declared:
            node = facts.own_node(function["id"])
            if node is not None:
                own.setdefault(node, []).append(function["id"])
    for row in rows:
        if not row.get("gap") and row.get("symbol"):
            found = own.get(row["symbol"], ())
            row["function"] = found[0] if len(found) == 1 else row["symbol"]


def importing(db, packages) -> set[str]:
    """The files of the snapshot that import one of `packages` (the snapshot's own import bindings)."""
    import semantic_store
    return {file for file, payload in db.execute("SELECT file, payload FROM sem_bindings WHERE kind='import'")
            if (semantic_store._unpack(payload) or {}).get("module") in packages}


def run(name: str, sections: tuple, rules: list[dict] = (), packages=None) -> dict:
    import resource
    import subprocess
    import time
    import types

    os.chdir("/")
    sys.path[:0] = ["/daodan/core", str(pathlib.Path(__file__).resolve().parent)]  # its own counts.py, beside it
    import binder
    import entry_points
    import flows
    import premap
    import semantic_store
    import snapshot
    import counts
    from entry_points import express, noir
    from snapshot_store import open_snapshot

    root = pathlib.Path("/work")
    manifest = pathlib.Path("/tmp/express-routes/manifest.sqlite")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    snapshot.read_project(root, manifest)
    out = {"name": name, "sections": list(sections), "snapshot_seconds": round(time.monotonic() - started, 1)}
    [command] = noir.commands(types.SimpleNamespace(inventory=types.SimpleNamespace(files=True)))
    env = {"PATH": os.environ["PATH"], "HOME": "/tmp/noir-home", "LANG": "C.UTF-8"}
    os.makedirs(env["HOME"], exist_ok=True)
    started = time.monotonic()
    r = subprocess.run(command["argv"], cwd=root / command["cwd"], env=env, capture_output=True, text=True, timeout=3000, stdin=subprocess.DEVNULL)
    out["noir"] = {"argv": command["argv"], "returncode": r.returncode, "seconds": round(time.monotonic() - started, 1), "stderr_tail": r.stderr[-300:]}
    if r.returncode != 0:
        return out
    answer = {"returncode": 0, "stdout": r.stdout, "stderr": "", "root": str(root)}
    premap.write(manifest, sources=())  # the pre-map with no source of its own: the record of the entry points reads it
    record = entry_points.write(manifest, sources=(noir,), runner=lambda commands: [answer])
    kept = [row for row in record["bound"]["rows"] if row.get("shape") == "http"]
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        # each binding on its own `Facts`, as the step binds: a function written with no name takes the name of its route, and the
        # two readers give the same function different routes (Noir loses prefixes), so the function is compared by its declaration
        facts = flows.Facts(store, db)
        noir_rows = binder.bind([row for row in entry_points.rows(record)[0] if row.get("shape") == "http"], facts, facts.resolver)
        assert [row.get("symbol") for row in noir_rows] == [row.get("symbol") for row in kept]  # the step's own binding
        identify(noir_rows, facts)
        facts = flows.Facts(store, db)
        started = time.monotonic()
        found = express.rows(facts, sections)
        out["express_seconds"] = round(time.monotonic() - started, 1)
        out["express_peak_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
        express_rows = binder.bind(found, facts, facts.resolver)
        identify(express_rows, facts)
        out["sites"] = {row["function"]: [row["site"], row["span"]] for row in express_rows if not row.get("gap")}
        if packages is not None:
            files = importing(db, packages)
            out["noir_outside"] = sum(1 for row in noir_rows if row["site"].rpartition(":")[0] not in files)
            noir_rows = [row for row in noir_rows if row["site"].rpartition(":")[0] in files]
    out["compare"] = counts.compare(express_rows, noir_rows, flows.path_schema)
    out["express_rows"] = [brief(row) for row in express_rows]
    out["noir_rows"] = [brief(row) for row in noir_rows]
    if rules:  # the links with these rules alone: the routes they offer, by the line each is registered at
        try:
            started = time.monotonic()
            links = flows.link_facts(manifest, list(rules))
            out["links_seconds"] = round(time.monotonic() - started, 1)
            offered = {e["site"] for e in links["entries"] if e["kind"] == "rotta" and "reader" not in e}
            read = {row.get("registered") or row["site"] for row in express_rows}
            ours = {row["registered"] for row in express_rows if not row.get("gap")}
            out["rule"] = {"offered": len(offered), "read_by_express": len(offered & read), "bound_by_express": len(offered & ours),
                           "only_rule": sorted(offered - read), "only_express": sorted(read - offered)}
        except Exception as error:  # the links of this snapshot did not build: the third comparison is missing, with its cause
            out["rule"] = {"failed": f"{type(error).__name__}: {str(error)[:400]}"}
    return out


def lines(wanted: list) -> dict:
    """The source's lines `[file, first, last]` of each item, from the checkout at `/work`: for a person to read, never kept."""
    out = []
    for file, first, last in wanted:
        text = pathlib.Path("/work", file).read_text(encoding="utf-8", errors="replace").split("\n")
        out.append([f"{n}: {text[n - 1].rstrip()[:160]}" for n in range(max(1, first), min(last, len(text)) + 1)])
    return {"lines": out}
