"""mapcli.py — i tool reali di Codebase Map su run `bench-model`, con traccia automatica.

Usata dal modello nell'esperimento model-in-the-loop: ogni chiamata è registrata in
results/model-runs/<session>/trace.jsonl (op, argomenti, lineage, esito, nodi toccati).
Nessun cap applicato: budget e protocollo si misurano dopo con model_eval.py.

  python mapcli.py SESSION modules [--query Q]
  python mapcli.py SESSION search QUERY [--limit N] [--lineage L] [--why T]
  python mapcli.py SESSION outline PATH [--pattern P] [--limit N]
  python mapcli.py SESSION graph PATH [PATH ...] [--hops N]
  python mapcli.py SESSION read PATH [--symbols a,b] [--ranges 10-40]
  python mapcli.py SESSION impact PATH::Symbol [PATH::Symbol ...] [--hops 1]
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from resolver import PREFIX  # noqa: E402
from mcp_service import MapService  # noqa: E402

RUN_ID = "bench-model"


class _LockBusy(Exception):
    """Il lock del progetto è occupato da un'altra sessione: non è un esito del tool."""


def _short(path):
    return path.split("app/", 1)[-1] if path else path


def _log(session, entry):
    out = HERE / "results" / "model-runs" / session
    out.mkdir(parents=True, exist_ok=True)
    with (out / "trace.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main(argv=None):
    for _ in range(60):
        try:
            return _run(argv)
        except _LockBusy:
            time.sleep(0.5)
    print(json.dumps({"error": "project lock still busy after 30 s"}))
    return 1


def _run(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("session")
    sub = parser.add_subparsers(dest="op", required=True)
    for name in ("modules", "search", "outline", "graph", "read", "impact"):
        p = sub.add_parser(name)
        p.add_argument("--lineage", default=None)
        p.add_argument("--why", default="")
        if name == "modules":
            p.add_argument("--query", default=None)
        if name == "search":
            p.add_argument("query")
            p.add_argument("--limit", type=int, default=20)
        if name == "outline":
            p.add_argument("path")
            p.add_argument("--pattern", default=None)
            p.add_argument("--limit", type=int, default=100)
        if name == "graph":
            p.add_argument("paths", nargs="+")
            p.add_argument("--hops", type=int, default=1)
        if name == "read":
            p.add_argument("path")
            p.add_argument("--symbols", default=None)
            p.add_argument("--ranges", default=None)
        if name == "impact":
            p.add_argument("targets", nargs="+")
            p.add_argument("--hops", type=int, default=1)
    args = parser.parse_args(argv)
    service = MapService(project_root=HERE / "app")
    entry = {"op": args.op, "lineage": args.lineage, "motivation": args.why, "nodes": [], "result_kind": "hits"}
    try:
        if args.op == "modules":
            res = service.modules(RUN_ID, query=args.query)
            entry["args"] = {"query": args.query} if args.query else {"list": True}
            if args.query:
                cands = res.get("candidates") or []
                entry["nodes"] = [f for c in cands for f in c.get("files", [])]
                view = {"status": res.get("status"), "reason": res.get("reason"),
                        "candidates": [{"name": c.get("name"), "match": c.get("match"),
                                        "files": [_short(f) for f in c.get("files", [])]} for c in cands]}
            else:
                mods = res.get("modules") or []
                entry["nodes"] = [m for mod in mods for m in mod.get("paths", []) if m != "."]
                view = {"graph_state": res.get("graph_state"),
                        "modules": [{"name": m.get("name"), "paths": [_short(p) for p in m.get("paths", [])],
                                     "status": m.get("status")} for m in mods]}
            if not entry["nodes"] and args.query:
                entry["result_kind"] = "empty"
        elif args.op == "search":
            entry["args"] = {"query": args.query, "limit": args.limit}
            res = service.search(RUN_ID, args.query, limit=args.limit)
            gaps = res.get("gaps") or []
            results = res.get("results") or []
            entry["nodes"] = [r.get("entity_id") or r.get("path") for r in results]
            if any("retrieval_" in g for g in gaps):
                entry["result_kind"] = "gap"
            elif not results:
                entry["result_kind"] = "empty"
            view = {"matched": res.get("matched"), "returned": res.get("returned"),
                    "truncated": res.get("truncated"), "gaps": gaps,
                    "results": [f"{_short(r.get('path'))}:{r.get('start_line')}-{r.get('end_line')} "
                                f"{r.get('kind')} {r.get('entity_id', '').split('::')[-1]} score={r.get('score')}"
                                for r in results]}
        elif args.op == "outline":
            full = args.path if args.path.startswith(PREFIX) else PREFIX + args.path
            entry["args"] = {"path": full, "limit": args.limit}
            res = service.outline(RUN_ID, path=full, pattern=args.pattern, limit=args.limit)
            items = res.get("items") or []
            entry["nodes"] = [full]
            entry["truncated"] = bool(res.get("truncated"))
            if not items:
                entry["result_kind"] = "empty"
            view = {"matched": res.get("matched"), "truncated": res.get("truncated"),
                    "items": [f"{i.get('symbol')} {i.get('kind')} {i.get('start')}-{i.get('end')}" for i in items]}
        elif args.op == "graph":
            fulls = [p if p.startswith(PREFIX) else PREFIX + p for p in args.paths]
            entry["args"] = {"paths": fulls, "hops": args.hops}
            res = service.graph(RUN_ID, paths=fulls, hops=args.hops)
            calls = res.get("calls") or []
            entry["nodes"] = sorted({(c.get("caller") or c.get("file") or "").split("::")[0] for c in calls}
                                    | {(c.get("target_id") or "").split("::")[0] for c in calls} - {""})
            entry["truncated"] = bool(res.get("truncated"))
            resolved = [f"{_short(c.get('caller') or c.get('file'))} -> {_short(c.get('target_id'))}"
                        for c in calls if c.get("resolution") == "resolved"]
            unresolved = [f"{_short(c.get('caller') or c.get('file'))} -> {'.'.join(c.get('parts') or []) or '?'} "
                          f"[{c.get('resolution')}]" for c in calls if c.get("resolution") != "resolved"]
            view = {"truncated": res.get("truncated"), "resolved_calls": resolved,
                    "unresolved_calls": unresolved,
                    "imports": [f"{_short(r.get('source'))} -> {_short(r.get('target'))}" for r in res.get("imports", [])]}
        elif args.op == "impact":
            fulls = [t if t.startswith(PREFIX) else PREFIX + t for t in args.targets]
            entry["op"] = "graph"  # stessa classe di costo: una interrogazione al grafo
            entry["args"] = {"impact_targets": fulls, "hops": args.hops}
            res = service.edit_impact(RUN_ID, fulls, hops=args.hops, include_source=False)
            view = {"unknown_targets": res.get("unknown_targets"), "targets": []}
            touched = set()
            for tgt in res.get("targets", []):
                callers = [{"symbol": _short(c.get("symbol_id")), "sites": [f"{_short(s.get('file'))}:{s.get('start_line')}"
                            for e in c.get("edges", []) for s in e.get("sites", [])]}
                           for c in tgt.get("callers", {}).get("listed", [])]
                callees = [_short(c.get("symbol_id")) for c in tgt.get("callees", {}).get("listed", [])]
                tests = [_short(t.get("file") or t.get("symbol_id") or "") for t in (tgt.get("tests") or {}).get("listed", [])] if isinstance(tgt.get("tests"), dict) else []
                touched |= {c.get("file") for c in tgt.get("callers", {}).get("listed", [])} | {tgt.get("file")}
                view["targets"].append({"symbol": _short(tgt.get("symbol_id")), "callers": callers, "callees": callees,
                                        "callers_total": tgt.get("callers", {}).get("total"), "tests": tests,
                                        "unresolved": tgt.get("unresolved")})
            entry["nodes"] = sorted(x for x in touched if x)
        else:
            full = args.path if args.path.startswith(PREFIX) else PREFIX + args.path
            request = {"path": full}
            if args.symbols:
                request["symbols"] = args.symbols.split(",")
            if args.ranges:
                start, _, end = args.ranges.partition("-")
                request["ranges"] = [{"start": int(start), "end": int(end)}]
            entry["args"] = {"requests": [request]}
            entry["nodes"] = [full]
            res = service.read(RUN_ID, [request])
            view = {"files": [{"path": _short(f.get("path")),
                               "blocks": [b.get("source") for b in f.get("blocks", [])]}
                              for f in res.get("files", [])]}
    except ValueError as exc:
        if "project lock" in str(exc):
            raise _LockBusy from exc
        entry["result_kind"] = "error"
        entry.setdefault("args", {})
        view = {"error": str(exc)}
    _log(args.session, entry)
    print(json.dumps(view, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
