"""CLI degli strumenti Codebase Map per l'esperimento model-in-the-loop.

Ogni chiamata è registrata in results/model/<case>.jsonl (traccia oggettiva, non
autodichiarata). Il modello usa solo questo comando; nessun accesso diretto ad app/.

  python maptool.py --case C1 search  "pay_online" [--limit 20]
  python maptool.py --case C1 modules [--query NAME]
  python maptool.py --case C1 outline PATH
  python maptool.py --case C1 graph   PATH [PATH ...] [--hops 1]
  python maptool.py --case C1 read    PATH [--symbols A,B] [--full]
  python maptool.py --case C1 budget
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from resolver import PREFIX, POLICY, ensure_run  # noqa: E402
from mcp_service import MapService  # noqa: E402

RUN_ID = "bench-model"
LOG_DIR = HERE / "results" / "model"
QUERY_OPS = ("search", "modules", "outline", "graph")


def _service():
    service = MapService(project_root=HERE / "app")
    if not (service.root / "runs" / RUN_ID).exists():
        ensure_run(HERE, RUN_ID)
    return service


def _full(path):
    return path if path.startswith(PREFIX) else PREFIX + path.lstrip("./")


def _short(path):
    return path[len(PREFIX):] if isinstance(path, str) and path.startswith(PREFIX) else path


def _log(case, op, args, result_kind, nodes):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / f"{case}.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"ts": time.time(), "op": op, "args": args,
                                 "result_kind": result_kind, "nodes": nodes}, ensure_ascii=False) + "\n")


def _budget(case):
    path = LOG_DIR / f"{case}.jsonl"
    steps = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
    queries = sum(1 for s in steps if s["op"] in QUERY_OPS)
    reads = len({p for s in steps if s["op"] == "read" for p in s["args"].get("paths", [])})
    return {"queries": queries, "reads": reads, "max_queries": POLICY["max_queries"],
            "max_reads": POLICY["max_reads"], "steps": len(steps)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case", required=True)
    sub = parser.add_subparsers(dest="op", required=True)
    p = sub.add_parser("search"); p.add_argument("query"); p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("modules"); p.add_argument("--query", default=None)
    p = sub.add_parser("outline"); p.add_argument("path")
    p = sub.add_parser("graph"); p.add_argument("paths", nargs="+"); p.add_argument("--hops", type=int, default=1)
    p = sub.add_parser("read"); p.add_argument("path"); p.add_argument("--symbols", default=None); p.add_argument("--full", action="store_true")
    sub.add_parser("budget")
    a = parser.parse_args(argv)

    if a.op == "budget":
        print(json.dumps(_budget(a.case), indent=1))
        return 0
    service = _service()
    try:
        if a.op == "search":
            env = service.search(RUN_ID, a.query, limit=a.limit)
            results = [{"path": _short(r["path"]), "entity": _short(r.get("entity_id")), "kind": r.get("kind"),
                        "lines": [r.get("start_line"), r.get("end_line")], "score": r.get("score")}
                       for r in env.get("results", [])]
            kind = "gap" if any("retrieval_" in g for g in env.get("gaps", [])) else ("hits" if results else "empty")
            _log(a.case, "search", {"query": a.query, "limit": a.limit}, kind, [r["entity"] or r["path"] for r in results])
            print(json.dumps({"matched": env.get("matched"), "truncated": env.get("truncated"),
                              "gaps": env.get("gaps"), "results": results}, indent=1, ensure_ascii=False))
        elif a.op == "modules":
            res = service.modules(RUN_ID, query=a.query) if a.query else service.modules(RUN_ID)
            if a.query:
                out = {"status": res.get("status"), "reason": res.get("reason"),
                       "candidates": [{"name": c.get("name"), "match": c.get("match"), "status": c.get("status"),
                                       "files": [_short(f) for f in c.get("files", [])]} for c in res.get("candidates", [])]}
                nodes = [f for c in out["candidates"] for f in c["files"]]
            else:
                out = {"graph_state": res.get("graph_state"),
                       "modules": [{"name": m.get("name"), "kind": m.get("kind"), "status": m.get("status"),
                                    "paths": [_short(_full(p)) if p != "." else "." for p in m.get("paths", [])],
                                    "responsibility": m.get("responsibility")} for m in res.get("modules", [])]}
                nodes = [p for m in out["modules"] for p in m["paths"] if p != "."]
            _log(a.case, "modules", {"query": a.query, "list": a.query is None},
                 "hits" if nodes else "empty", nodes)
            print(json.dumps(out, indent=1, ensure_ascii=False))
        elif a.op == "outline":
            res = service.outline(RUN_ID, path=_full(a.path), limit=100)
            items = [{"symbol": i.get("symbol"), "kind": i.get("kind"), "lines": [i.get("start"), i.get("end")]}
                     for i in res.get("items", [])]
            _log(a.case, "outline", {"path": _full(a.path)}, "hits" if items else "empty", [_full(a.path)])
            print(json.dumps({"path": a.path, "matched": res.get("matched"), "truncated": res.get("truncated"),
                              "items": items}, indent=1, ensure_ascii=False))
        elif a.op == "graph":
            paths = [_full(p) for p in a.paths]
            res = service.graph(RUN_ID, paths=paths, hops=a.hops)
            calls = [{"caller": _short(c.get("caller") or c.get("file")), "callee": ".".join(c.get("parts") or []),
                      "resolution": c.get("resolution"), "target": _short(c.get("target_id")), "line": (c.get("span") or [None])[0]}
                     for c in res.get("calls", [])]
            imports = [{"source": _short(r.get("source")), "target": _short(r.get("target"))} for r in res.get("imports", [])]
            nodes = sorted({c["caller"] for c in calls if c["caller"]} | {c["target"].split("::")[0] for c in calls if c["target"]}
                           | {i["source"] for i in imports} | {i["target"] for i in imports})
            _log(a.case, "graph", {"paths": paths, "hops": a.hops}, "hits", nodes)
            print(json.dumps({"truncated": res.get("truncated"), "calls": calls, "imports": imports}, indent=1, ensure_ascii=False))
        elif a.op == "read":
            req = {"path": _full(a.path)}
            if a.symbols:
                req["symbols"] = [s.strip() for s in a.symbols.split(",") if s.strip()]
            if a.full:
                req["full_file"] = True
            res = service.read(RUN_ID, [req])
            _log(a.case, "read", {"paths": [req["path"]], "symbols": req.get("symbols"), "full": a.full}, "hits", [req["path"]])
            for f in res.get("files", []):
                print(f"# {_short(f['path'])}")
                for block in f.get("blocks", []):
                    print(block.get("source", ""), end="")
        print(json.dumps({"budget": _budget(a.case)}))
        return 0
    except ValueError as exc:
        _log(a.case, a.op, vars(a), "error", [])
        print(json.dumps({"error": str(exc), "budget": _budget(a.case)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
