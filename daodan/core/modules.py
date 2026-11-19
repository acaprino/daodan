"""Modules of a snapshot: build units read from manifests, modules declared by
the project, modules proposed by a model. All verified against the snapshot.

Three provenances, one record:

- `build`: what the build system declares. Workspaces, packages, crates,
  Maven and Gradle modules, Go modules, .NET projects, Composer, Gems,
  pubspec, Swift, Mix, Deno, Nx, Angular, Lerna, CMake, Cabal and Stack, sbt,
  Terraform, Zig, Julia, dune, buf and Visual Studio C++ projects. `named`
  says whether a file names the unit or its folder does. Read
  programmatically, no heuristics,
  status `confirmed`.
- `declared`: `codebase-modules.json` at the project root, written by the
  project: name, responsibility and members (`path::Symbol`, files,
  directories). `confirmed` when every member resolves.
- `proposed`: the proposals ledger beside the manifest, written from a model's
  answer. Every member is verified; the module stays `inferred`.

Edges: declared dependencies between build units, resolved imports and calls
between members. Markdown is never interpreted here: a model reads it and
proposes. Deterministic for the same snapshot, ledger and declared file; no
model or network call.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from snapshot_store import logical_digest, open_snapshot  # noqa: E402
from module_inventory import (EMPTY_DIRECTORY, StaleSource, _Inventory, _digest, _inside, _join,  # noqa: E402,F401
                              _json, _plain, _posix, slug)
from build_units import ECOSYSTEMS, READERS, SUFFIX_READERS  # noqa: E402,F401
from module_records import (DECLARED_FILE, DECLARED_SCHEMA, LEDGER_FILE, LEDGER_SCHEMA, LOCATIONS,  # noqa: E402,F401
                            MAX_MEMBERS, MAX_MODULES, MODULE_KINDS, ledger_name, load_ledger, resolve_evidence,
                            resolve_members, validate_module, validate_modules, write_ledger)
from module_derive import (MAX_EDGE_EVIDENCE, NATURES, PHYSICAL, PROVENANCES, SCHEMA, STATUSES,  # noqa: E402,F401
                           derive, enrich_with_premap)

GRAPH_FILE = "modules.json"
VIEW_FILE = "modules.md"
MAX_BRIEF_SYMBOLS = 2000


# ----------------------------------------------------------- lifecycle

def graph_name(manifest: Path) -> Path:
    return Path(manifest).with_name(GRAPH_FILE)


def load_graph(path: Path) -> dict:
    _plain(path)
    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"not a readable module graph: {error}") from error
    if not isinstance(graph, dict) or graph.get("schema") != SCHEMA or not isinstance(graph.get("modules"), list):
        raise ValueError("not a module graph of this schema")
    return graph


def _inputs_digest(manifest: Path, store) -> str:
    return _digest([logical_digest(store), store["root"], _digest(load_ledger(manifest))])


def graph_state(manifest: Path) -> dict:
    """fresh, stale, missing or corrupt, without touching the graph."""
    manifest = Path(manifest).resolve()
    graph_path = graph_name(manifest)
    _plain(manifest)
    if not manifest.is_file():
        raise ValueError(f"manifest does not exist: {manifest}")
    report = {"graph": str(graph_path), "manifest": str(manifest)}
    if not graph_path.exists():
        return {**report, "state": "missing", "reason": "no module graph beside the manifest"}
    try:
        graph = load_graph(graph_path)
    except ValueError as error:
        return {**report, "state": "corrupt", "reason": str(error)}
    with open_snapshot(manifest) as store:
        try:
            current = _inputs_digest(manifest, store)
        except ValueError as error:
            return {**report, "state": "stale", "reason": f"proposals ledger unreadable: {error}", "modules": len(graph["modules"])}
    if graph.get("inputs_digest") == current:
        return {**report, "state": "fresh", "modules": len(graph["modules"])}
    return {**report, "state": "stale", "reason": "snapshot or proposals changed since the graph was derived",
            "modules": len(graph["modules"])}


def _changes(graph: dict, previous: dict | None) -> dict:
    before = {m["id"]: m for m in (previous or {}).get("modules", [])} if isinstance(previous, dict) else {}
    now = {m["id"]: m for m in graph["modules"]}
    return {"added": sorted(set(now) - set(before)), "removed": sorted(set(before) - set(now)),
            "changed": sorted(i for i in now if i in before and before[i].get("members_digest") != now[i]["members_digest"]),
            "unchanged": sorted(i for i in now if i in before and before[i].get("members_digest") == now[i]["members_digest"])}


def write_graph(manifest: Path) -> dict:
    """Derive and publish `modules.json` and `modules.md` beside the manifest."""
    manifest = Path(manifest).resolve()
    graph_path, view_path = graph_name(manifest), Path(manifest).with_name(VIEW_FILE)
    _plain(graph_path)
    _plain(view_path)
    previous = None
    if graph_path.exists():
        try:
            previous = load_graph(graph_path)
        except ValueError:
            previous = None
    with open_snapshot(manifest) as store:
        before = _inputs_digest(manifest, store)
        graph = derive(store, ledger=load_ledger(manifest))
        graph["inputs_digest"] = before
        if _inputs_digest(manifest, store) != before:
            raise ValueError("snapshot or ledger changed during derivation; retry")
    graph["changes"] = _changes(graph, previous)
    view = render(graph)
    for path, data in ((graph_path, _json(graph).encode("utf-8")), (view_path, view.encode("utf-8"))):
        descriptor, name = tempfile.mkstemp(prefix=".modules-", dir=path.parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(name, path)
    return graph


def ensure_graph(manifest: Path, *, check: bool = False) -> dict:
    before = graph_state(manifest)
    if before["state"] == "fresh" or check:
        return {**before, "action": "none" if before["state"] == "fresh" else "reported"}
    try:
        graph = write_graph(manifest)
    except (OSError, ValueError) as error:
        return {**before, "state": "failed", "action": "none", "reason": str(error)}
    return {**graph_state(manifest), "action": "rebuilt" if before["state"] != "stale" else "refreshed",
            "changes": graph["changes"]}


def sync_with_premap(manifest: Path, premap_record: dict) -> dict:
    """Align `modules.json` and `modules.md` with pre-map model units, exclusions and toolchains."""
    manifest = Path(manifest).resolve()
    ensured = ensure_graph(manifest)
    if ensured["state"] != "fresh":
        raise ValueError(f"module graph is {ensured['state']}: {ensured.get('reason', '')}")
    graph_path, view_path = graph_name(manifest), Path(manifest).with_name(VIEW_FILE)
    _plain(graph_path)
    _plain(view_path)
    previous = load_graph(graph_path)
    if premap_record.get("inputs_digest") and previous.get("premap_digest") == premap_record.get("inputs_digest"):
        return previous
    with open_snapshot(manifest) as store:
        before = _inputs_digest(manifest, store)
        base = derive(store, ledger=load_ledger(manifest))
        base["inputs_digest"] = before
        graph = enrich_with_premap(store, base, premap_record)
        if _inputs_digest(manifest, store) != before:
            raise ValueError("snapshot or ledger changed during pre-map sync; retry")
    graph["changes"] = _changes(graph, previous)
    view = render(graph)
    for path, data in ((graph_path, _json(graph).encode("utf-8")), (view_path, view.encode("utf-8"))):
        descriptor, name = tempfile.mkstemp(prefix=".modules-", dir=path.parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(name, path)
    return graph


# ---------------------------------------------------------------- query

def _match(module: dict, key: str) -> str | None:
    names = [module["name"], *module["aliases"]]
    if key == module["id"] or any(slug(n) == key for n in names):
        return "exact" if key == module["id"] or slug(module["name"]) == key else "alias"
    if any(key == slug(p) or slug(PurePosixPath(p).name) == key for p in module["paths"]):
        return "path"
    if any(key in slug(n) for n in names):
        return "partial"
    return None


def _owners_of(graph: dict, rel: str) -> list[str]:
    """The most specific physical scopes holding a file, including colocated units."""
    best, depth = [], -2
    for module in graph["modules"]:
        if module["provenance"] not in PHYSICAL or any(_inside(rel, p) for p in module["excluded"]):
            continue
        for path in module["paths"]:
            candidate_depth = -1 if path == "." else len(path)
            if _inside(rel, path) and candidate_depth > depth:
                best, depth = [module["id"]], candidate_depth
            elif _inside(rel, path) and candidate_depth == depth:
                best.append(module["id"])
    return best


def query(graph: dict, name: str, *, state: str = "unverified", limit: int = 10) -> dict:
    """Candidates for a name or alias with paths, files, members, relations as read scope, gaps."""
    if not isinstance(name, str) or not name.strip() or len(name) > 1000:
        raise ValueError("query name must be text of at most 1000 characters")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 through 100")
    key = slug(name) or _posix(name)
    order = {"exact": 0, "alias": 1, "path": 2, "partial": 3}
    by_id = {m["id"]: m for m in graph["modules"]}
    matched = sorted(((order[kind], STATUSES.index(m["status"]), m["id"], kind, m)
                      for m in graph["modules"] if (kind := _match(m, key))), key=lambda i: i[:3])
    candidates = []
    for _, _, _, kind, module in matched[:limit]:
        relations, scope = [], []
        for item in graph["edges"]:
            if module["id"] not in (item["source"], item["target"]):
                continue
            outgoing = item["source"] == module["id"]
            other = item["target"] if outgoing else item["source"]
            relations.append({"kind": item["kind"], "direction": "outgoing" if outgoing else "incoming", "module": other,
                              "status": item["status"], "evidence": item["evidence"][:5], "evidence_total": item["evidence_total"]})
            if other in by_id:
                scope.append({"module": other, "name": by_id[other]["name"], "relation": item["kind"],
                              "direction": relations[-1]["direction"], "status": by_id[other]["status"],
                              "paths": by_id[other]["paths"], "excluded": by_id[other]["excluded"]})
        if module["provenance"] not in PHYSICAL:
            # The physical units whose directories hold the member files: read scope, not target.
            for owner in sorted({owner for rel in module["files"] for owner in _owners_of(graph, rel)}):
                scope.append({"module": owner, "name": by_id[owner]["name"], "relation": "owned_by", "direction": "outgoing",
                              "status": by_id[owner]["status"], "paths": by_id[owner]["paths"], "excluded": by_id[owner]["excluded"]})
        candidates.append({**{k: module[k] for k in ("id", "name", "aliases", "provenance", "kind", "location", "description",
                                                      "responsibility", "status", "paths", "excluded", "files", "members",
                                                      "manifests", "evidence", "conflicts", "gaps", "coverage")},
                           "nature": module.get("nature"),
                           "languages": module.get("languages", {}),
                           "toolchains": module.get("toolchains", []),
                           "match": kind, "relations": relations,
                           "read_scope": sorted(scope, key=lambda r: (r["module"], r["relation"], r["direction"]))})
    direct = [c for c in candidates if c["match"] in ("exact", "alias")]
    if not candidates:
        status, reason = "unknown", "no module, alias or path matches the name"
    elif len(direct) == 1 and direct[0]["status"] == "confirmed" and not direct[0]["conflicts"] and state == "fresh":
        status, reason = "resolved", "one confirmed module matches the name"
    elif len(direct) == 1 and direct[0]["conflicts"]:
        status, reason = "needs_clarification", "the matching module shares members with another module"
    elif len(direct) == 1:
        status = "incomplete"
        reason = f"the matching module is {direct[0]['status']}" if state == "fresh" else f"the module graph is {state}"
    elif len(direct) > 1:
        status, reason = "needs_clarification", "several modules match the name"
    else:
        status, reason = "needs_clarification", "only partial or path matches exist"
    gaps = [] if state == "fresh" else [{"kind": f"graph_{state}", "detail": "rebuild the module graph",
                                         "repair": f"{Path(__file__).name} build <manifest>"}]
    if len(matched) > limit:
        gaps.append({"kind": "limit", "detail": f"{len(matched) - limit} further candidates omitted"})
    return {"schema": "daodan/module-query/v1", "query": name, "status": status, "reason": reason,
            "candidates": candidates, "total_matches": len(matched), "gaps": gaps, "graph_state": state,
            "binding": graph.get("binding")}


def query_manifest(manifest: Path, name: str, *, limit: int = 10) -> dict:
    state = graph_state(manifest)
    if state["state"] in ("missing", "corrupt"):
        return {"schema": "daodan/module-query/v1", "query": name, "status": "unknown", "reason": state["reason"],
                "candidates": [], "total_matches": 0, "graph_state": state["state"], "binding": None,
                "gaps": [{"kind": f"graph_{state['state']}", "detail": state["reason"],
                          "repair": f"{Path(__file__).name} build {manifest}"}]}
    return query(load_graph(Path(state["graph"])), name, state=state["state"], limit=limit)


# ------------------------------------------------------------ proposals

def propose(manifest: Path, value: object, *, replace: bool = False) -> dict:
    """Validate proposals, record them beside the manifest, rebuild; report each against the snapshot."""
    manifest = Path(manifest).resolve()
    records = validate_modules(value, source="proposals")
    write_ledger(manifest, records, replace=replace)
    graph = write_graph(manifest)
    names = {slug(r["name"]) for r in records}
    keys = ("id", "name", "kind", "nature", "location", "status", "provenance", "paths", "files", "languages",
            "toolchains", "coverage", "gaps", "conflicts")
    return {"schema": LEDGER_SCHEMA, "manifest": str(manifest), "accepted": len(records),
            "modules": [{k: m.get(k) for k in keys} for m in graph["modules"] if slug(m["name"]) in names],
            "graph": graph_state(manifest), "changes": graph["changes"]}


def brief(manifest: Path, *, symbol_limit: int = MAX_BRIEF_SYMBOLS) -> dict:
    """What a model needs before proposing: modules so far, symbols per file, member format, rule."""
    manifest = Path(manifest).resolve()
    if type(symbol_limit) is not int or not 0 <= symbol_limit <= 20_000:
        raise ValueError("symbol_limit must be an integer from 0 through 20000")
    state = graph_state(manifest)
    if state["state"] in ("missing", "corrupt"):
        return {"schema": "daodan/modules-brief/v1", "graph_state": state["state"], "reason": state["reason"],
                "repair": f"{Path(__file__).name} build {manifest}", "modules": [], "symbols": {}}
    graph = load_graph(Path(state["graph"]))
    by_file: dict[str, list[tuple[int, str]]] = {}
    with open_snapshot(manifest) as store:
        for record in store.iter_symbols():
            if record["name"].count(".") <= 1:
                by_file.setdefault(record["path"], []).append((record.get("start") or 0, record["name"]))
    symbols, kept = {}, 0
    total = sum(len(v) for v in by_file.values())
    for path in sorted(by_file):
        names = [n for _, n in sorted(by_file[path])]
        if kept + len(names) > symbol_limit:
            break
        symbols[path] = names
        kept += len(names)
    keys = ("id", "name", "provenance", "nature", "kind", "location", "responsibility", "status", "paths",
            "excluded", "languages", "toolchains", "coverage", "gaps")
    return {"schema": "daodan/modules-brief/v1", "graph_state": state["state"],
            "modules": [{k: m.get(k) for k in keys} | {"members": [x["id"] for x in m["members"]]} for m in graph["modules"]],
            "symbols": symbols, "symbols_omitted": total - kept,
            **({"symbols_hint": "files past the limit are omitted whole; list them with codebase_map_outline(path=...)"}
               if total > kept else {}),
            "member_format": "path::Symbol for a snapshot symbol, a file path, or a directory path; evidence as path or path#heading",
            "declared_file": DECLARED_FILE,
            "rule": (
                "Propose responsibility modules from an already inventoried snapshot: components, macro-features and "
                "other parts of the system, also when they cut across directories and build units. Do not recreate "
                "build units: manifests already define them. Group by responsibility, not by directory or folder name. "
                "For each candidate, identify the design decision, protocol, feature or domain state it hides and what "
                "could change independently. Include a member only when imports, calls, routes, naming or project "
                "documents connect it to the others, and cite the supporting paths in evidence: at least one, or the "
                "module stays incomplete. In responsibility, use one plain sentence, then "
                "name the incoming contract (symbols used from outside) and exclusions with reasons. When a member "
                "is shared by two modules, list it in the members of both instead of forcing one owner. Do not propose "
                "physical nodes from this brief: it contains no deployment evidence. Return records with exactly the fields "
                "name, kind, location, responsibility, members, evidence. kind is required: component (a part with its "
                "own boundary, a node of the map) or feature (a macro-feature across components, a highlight on the "
                "map, not a node). location is internal (default) or external (a service, database or device outside "
                "the repository: a component with no members, its evidence are the files that bind to it, each giving "
                "a uses edge from the module owning that file). List "
                "unassigned files and reasons separately from the proposal array. A proposal becomes an inferred module "
                f"after every member is verified; only the project's {DECLARED_FILE} confirms a module")}


# ----------------------------------------------------------------- view

def _text(value) -> str:
    return re.sub(r"([\\`*_{}\[\]|])", r"\\\1", str(value).replace("\n", " "))


def _code(value) -> str:
    return "`" + str(value).replace("`", "'") + "`"


def render(graph: dict) -> str:
    c = graph["coverage"]
    lines = ["# Modules", "", f"Snapshot digest {_code(graph['binding']['logical_digest'])}. Files: {c['files']}. "
             + "Modules: " + "; ".join(f"{p}: {c['modules'][p]}" for p in PROVENANCES) + ". "
             + "Statuses: " + "; ".join(f"{s}: {c['statuses'][s]}" for s in STATUSES) + ". "
             + "Edges: " + "; ".join(f"{k}: {v}" for k, v in c["edges"].items()) + ".", "",
             "| Id | Name | Provenance | Kind | Status | Paths | Files | Gaps |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for m in graph["modules"]:
        lines.append("| " + " | ".join([_code(m["id"]), _text(m["name"]), m["provenance"], m["kind"], m["status"],
                                        ", ".join(_code(p) for p in m["paths"]) or "none", str(m["coverage"]["files"]),
                                        str(len(m["gaps"]) + len(m["conflicts"]))]) + " |")
    for m in graph["modules"]:
        lines.extend(["", f"## {_code(m['id'])}", "", f"- Name: {_text(m['name'])}"
                      + (f"; aliases: {', '.join(_text(a) for a in m['aliases'])}" if m["aliases"] else "")
                      + f"; {m['provenance']}, {m['kind']}, {m['location']}, {m['status']}"])
        if m["description"] or m["responsibility"]:
            lines.append(f"- {_text(m['description'] or m['responsibility'])}")
        lines.append(f"- Paths: {', '.join(_code(p) for p in m['paths']) or 'none'}"
                     + (f"; excluded: {', '.join(_code(p) for p in m['excluded'])}" if m["excluded"] else "")
                     + f"; {m['coverage']['files']} files")
        if m["provenance"] not in PHYSICAL:
            lines.append("- Members: " + (", ".join(_code(x["id"]) + ("" if x["resolved"] else " (unresolved)") for x in m["members"]) or "none"))
        if m["evidence"]:
            lines.append("- Evidence: " + ", ".join(_code(e["path"] + (f":{e['line']}" if e.get("line") else "")) for e in m["evidence"]))
        for item in m["conflicts"]:
            lines.append(f"- Conflict: {_code(item['member'])} also in {', '.join(_code(o) for o in item['others'])}")
        for item in m["gaps"]:
            lines.append(f"- Gap {item['kind']}: {_text(item['detail'])}")
        related = [e for e in graph["edges"] if m["id"] in (e["source"], e["target"])]
        for e in related:
            lines.append(f"- {e['kind']} ({e['status']}): {_code(e['source'])} -> {_code(e['target'])}, evidence {e['evidence_total']}")
    lines.extend(["", "## Gaps", ""])
    lines.extend(f"- {g['kind']}: {_text(g.get('path', ''))} {_text(g['detail'])}" for g in graph["gaps"]) if graph["gaps"] else lines.append("- none")
    if "changes" in graph:
        lines.extend(["", "## Changes", ""] + [f"- {k}: {', '.join(_code(i) for i in v) or 'none'}" for k, v in graph["changes"].items()])
    lines.extend(["", "## Notes", ""] + [f"- {_text(n)}" for n in graph["notes"]])
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ CLI

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Modules of a Codebase Map snapshot: build units, declared and proposed modules.")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="derive modules.json and modules.md beside the manifest")
    build.add_argument("manifest", type=Path)
    build.add_argument("--check", action="store_true", help="report the graph state and write nothing")
    build.add_argument("--force", action="store_true", help="rebuild even when fresh")
    ask = sub.add_parser("query", help="candidates for a module name, alias or path")
    ask.add_argument("manifest", type=Path)
    ask.add_argument("name")
    ask.add_argument("--limit", type=int, default=10)
    info = sub.add_parser("brief", help="what a model needs before proposing modules")
    info.add_argument("manifest", type=Path)
    info.add_argument("--symbol-limit", type=int, default=MAX_BRIEF_SYMBOLS)
    prop = sub.add_parser("propose", help="validate and record a model's proposals, then rebuild")
    prop.add_argument("manifest", type=Path)
    prop.add_argument("proposals", help="JSON file (a list or {\"modules\": [...]}), or - for stdin")
    prop.add_argument("--replace", action="store_true", help="drop earlier proposals first")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            if args.force:
                graph = write_graph(args.manifest)
                result = {**graph_state(args.manifest), "action": "rebuilt", "changes": graph["changes"]}
            else:
                result = ensure_graph(args.manifest, check=args.check)
            code = 0 if result["state"] == "fresh" else 1
        elif args.command == "query":
            result, code = query_manifest(args.manifest, args.name, limit=args.limit), 0
        elif args.command == "brief":
            result, code = brief(args.manifest, symbol_limit=args.symbol_limit), 0
        else:
            text = sys.stdin.read() if args.proposals == "-" else Path(args.proposals).read_text(encoding="utf-8")
            result, code = propose(args.manifest, json.loads(text), replace=args.replace), 0
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return code
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
