"""Derivation of the module graph from one snapshot: build units merged per
directory, declared and proposed modules verified, identities, file ownership
and the edges between modules. Deterministic for the same inputs."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

import snapshot
from build_units import ECOSYSTEMS, _dependency_name, _family, _read_units
from module_inventory import _Inventory, _digest, _dirname, _inside, _join, _line_of, slug
from module_records import DECLARED_FILE, _evidence, _member, load_ledger, validate_modules
from snapshot_store import logical_digest

SCHEMA = "daodan/module-graph/v1"
PROVENANCES = ("build", "declared", "proposed")
STATUSES = ("confirmed", "inferred", "incomplete")
MAX_EDGE_EVIDENCE = 20


def _review_paths(inventory: _Inventory, files: set[str]) -> list[str]:
    """Member files, collapsed to a directory only when every inventoried file in it is a member."""
    paths: list[str] = []
    for directory in sorted({_dirname(f) for f in files if _dirname(f) != "."}, key=lambda d: (d.count("/"), d)):
        if not any(_inside(directory, p) for p in paths) and set(inventory.files_under([directory])) <= files:
            paths.append(directory)
    paths.extend(f for f in sorted(files) if not any(_inside(f, p) for p in paths))
    return paths


def _call_edges(store, symbol_owner: dict[str, dict[str, list[str]]], file_owner: dict[str, list[str]]) -> list[dict]:
    """Resolved calls between members of different modules, from the semantic store."""
    from semantic_store import _ImpactIndex, install_edge_view, semantic_reader

    def owners(row):
        file, name = row[1], row[2]
        found = set(file_owner.get(file, []))
        for module_id, names in symbol_owner.get(file, {}).items():
            if any(name == n or name.startswith(n + ".") for n in names):
                found.add(module_id)
        return sorted(found)

    calls = []
    with semantic_reader(store) as db:
        install_edge_view(db, store)
        index = _ImpactIndex(db)
        for file, line, target in db.execute(
                "SELECT file,l0,target_id FROM effective_references WHERE kind='call' AND resolution='resolved' "
                "ORDER BY file,l0,c0,l1,c1,id"):
            caller = index.enclosing(file, line)
            callee = index.symbol_for_declaration(target) if target else None
            if caller is None or callee is None:
                continue
            for source in owners(caller):
                for destination in owners(callee):
                    if source != destination:
                        calls.append({"source": source, "target": destination, "path": file, "line": line,
                                      "caller": caller[2], "callee": f"{callee[1]}::{callee[2]}"})
    return calls


def _merge_units(units: list[dict]) -> dict[tuple[str, str, str | None], dict]:
    """Complementary manifests share a unit; independent build systems do not."""
    by_directory: dict[tuple[str, str, str | None], dict] = {}
    for unit in sorted(units, key=lambda u: (u["directory"].count("/"), u["directory"], u["path"])):
        key = (unit["directory"], _family(unit["ecosystem"]), unit.get("slot"))
        merged = by_directory.get(key)
        if merged is None:
            by_directory[key] = {
                "directory": unit["directory"], "name": unit["name"], "aliases": list(unit["aliases"]),
                "kinds": [unit["kind"]], "ecosystems": [unit["ecosystem"]], "description": unit["description"],
                "manifests": [unit["path"]], "evidence": [{"path": unit["path"], "line": unit["line"]}],
                "dependencies": set(unit["dependencies"]), "path_dependencies": list(unit["path_dependencies"]),
                "patterns": [(pattern, unit["path"]) for pattern in unit["members"]], "registered_by": []}
            continue
        if merged["name"] is None:
            merged["name"] = unit["name"]
        elif unit["name"] and unit["name"] != merged["name"] and unit["name"] not in merged["aliases"]:
            merged["aliases"].append(unit["name"])
        merged["aliases"].extend(a for a in unit["aliases"] if a not in merged["aliases"])
        merged["kinds"].append(unit["kind"])
        merged["ecosystems"].append(unit["ecosystem"])
        merged["description"] = merged["description"] or unit["description"]
        merged["manifests"].append(unit["path"])
        merged["evidence"].append({"path": unit["path"], "line": unit["line"]})
        merged["dependencies"].update(unit["dependencies"])
        merged["path_dependencies"].extend(unit["path_dependencies"])
        merged["patterns"].extend((pattern, unit["path"]) for pattern in unit["members"])
    return by_directory


def _register_members(inventory: _Inventory, by_directory: dict, gaps: list[dict]) -> None:
    """Workspace member patterns: each member unit records the workspace that registers it."""
    for key, merged in list(by_directory.items()):
        directory, family, _ = key
        excluded_members = {d for pattern, _ in merged["patterns"] if pattern.startswith("!")
                            for d in inventory.glob_directories(directory, pattern[1:])}
        for pattern, manifest in dict.fromkeys(p for p in merged["patterns"] if not p[0].startswith("!")):
            found = [directory] if _join(directory, pattern) == directory else inventory.glob_directories(directory, pattern)
            if not found and not any(ch in pattern for ch in "*?["):
                gaps.append({"kind": "member_missing", "path": manifest,
                             "detail": f"workspace member {pattern}: {inventory.absence(_join(directory, pattern))}"})
            for member in found:
                if member in excluded_members:
                    continue
                member_key = (member, family, None)
                if member_key not in by_directory:
                    if any(ch in pattern for ch in "*?["):
                        continue  # a glob selects the units it finds; it declares none
                    by_directory[member_key] = {
                        "directory": member, "name": None, "aliases": [], "kinds": ["workspace-member"],
                        "ecosystems": [merged["ecosystems"][0]], "description": None, "manifests": [],
                        "evidence": [], "dependencies": set(), "path_dependencies": [], "patterns": [], "registered_by": []}
                site = {"path": manifest, "line": _line_of(inventory.text(manifest), pattern)}
                by_directory[member_key]["registered_by"].append((key, site))
                by_directory[member_key]["evidence"].append(site)


def _build_module(inventory: _Inventory, merged: dict, by_directory: dict) -> dict:
    name = merged["name"] or PurePosixPath(merged["directory"]).name or PurePosixPath(inventory.root).name
    basename = PurePosixPath(merged["directory"]).name
    if basename and basename != name and basename not in merged["aliases"]:
        merged["aliases"].append(basename)
    nested = sorted({d for d, *_ in by_directory if d != merged["directory"] and _inside(d, merged["directory"])})
    excluded = [d for d in nested if not any(_inside(d, other) for other in nested if other != d)]
    return {
        "id": "", "name": name, "named": merged["name"] is not None,
        "aliases": sorted(dict.fromkeys(merged["aliases"])), "provenance": "build",
        "kind": sorted(set(merged["kinds"]))[0] if len(set(merged["kinds"])) == 1 else "+".join(sorted(set(merged["kinds"]))),
        "location": "internal", "ecosystems": sorted(set(merged["ecosystems"])), "description": merged["description"],
        "responsibility": "", "members": [{"id": merged["directory"], "kind": "directory",
                                           "path": merged["directory"], "resolved": True}],
        "excluded": excluded, "manifests": sorted(merged["manifests"]),
        "registered_by": sorted({key[0] for key, _ in merged["registered_by"]}), "registrations": merged["registered_by"],
        "evidence": merged["evidence"], "dependencies": sorted(merged["dependencies"]),
        "path_dependencies": merged["path_dependencies"], "conflicts": [], "gaps": [], "status": "confirmed",
    }


def _verified_module(inventory: _Inventory, store, provenance: str, record: dict) -> dict:
    """A declared or proposed module with every member and evidence resolved against the snapshot."""
    members = [_member(inventory, store, text) for text in record["members"]]
    evidence = [_evidence(inventory, text) for text in record["evidence"]]
    module_gaps = [{"kind": "member_missing", "detail": f"{m['id']}: {m['reason']}"} for m in members if not m["resolved"]]
    module_gaps.extend({"kind": "evidence_missing", "detail": f"{e['path']}: {e['reason']}"} for e in evidence if not e["resolved"])
    if not evidence:
        module_gaps.append({"kind": "evidence_missing", "detail": "no evidence cited"})
    # What anchors the module to the snapshot: its members, or for an external one the files binding to it.
    anchors = evidence if record["location"] == "external" else members
    if not evidence or not any(a["resolved"] for a in anchors):
        status = "incomplete"
    elif provenance == "declared":
        status = "confirmed" if all(a["resolved"] for a in anchors) else "incomplete"
    else:
        status = "inferred"
    return {
        "id": "", "name": record["name"], "named": True, "aliases": [], "provenance": provenance, "kind": record["kind"],
        "location": record["location"], "ecosystems": [], "description": None, "responsibility": record["responsibility"],
        "members": members, "excluded": [], "manifests": [DECLARED_FILE] if provenance == "declared" else [],
        "registered_by": [], "evidence": evidence, "dependencies": [], "path_dependencies": [],
        "conflicts": [], "gaps": module_gaps, "status": status,
    }


def _declared_modules(inventory: _Inventory, store, ledger: list[dict] | None, gaps: list[dict]) -> list[dict]:
    """Declared and proposed modules, every member verified."""
    declared: list[dict] = []
    if DECLARED_FILE in inventory.headers:
        try:
            declared = validate_modules(json.loads(inventory.text(DECLARED_FILE)), source=DECLARED_FILE)
        except ValueError as error:
            gaps.append({"kind": "modules_unreadable", "path": DECLARED_FILE, "detail": str(error)})
    proposals = load_ledger(Path(store.path)) if ledger is None else ledger
    declared_names = {slug(r["name"]) for r in declared}
    for record in proposals:
        if slug(record["name"]) in declared_names:
            gaps.append({"kind": "proposal_superseded", "detail": f"proposal {record['name']} is now declared in {DECLARED_FILE}"})
    return [_verified_module(inventory, store, provenance, record)
            for provenance, records in (("declared", declared),
                                        ("proposed", [r for r in proposals if slug(r["name"]) not in declared_names]))
            for record in records]


def _assign_identities(modules: list[dict]) -> None:
    counts: dict[str, int] = {}
    for module in modules:
        counts[slug(module["name"])] = counts.get(slug(module["name"]), 0) + 1
    taken: set[str] = set()
    for module in modules:
        key = slug(module["name"]) or "unnamed"
        anchor = module["members"][0]["path"] if module["provenance"] == "build" else module["provenance"]
        identity = key if counts[slug(module["name"])] == 1 and key not in taken else f"{key}@{anchor}"
        while identity in taken:
            identity += "+"
        module["id"] = identity
        taken.add(identity)


def _measure_modules(inventory: _Inventory, modules: list[dict]) -> None:
    """Shared members, files, review paths, coverage and the members digest of every module."""
    claims: dict[str, list[str]] = {}
    for module in modules:
        if module["provenance"] != "build":
            for member in module["members"]:
                if member["resolved"]:
                    claims.setdefault(member["id"], []).append(module["id"])
    for module in modules:
        for member in module["members"]:
            others = [o for o in claims.get(member["id"], []) if o != module["id"]]
            if others and member["resolved"]:
                module["conflicts"].append({"kind": "shared_member", "member": member["id"], "others": others})
        files = set()
        for member in module["members"]:
            if not member["resolved"]:
                continue
            files.update(inventory.files_under([member["path"]], module["excluded"]) if member["kind"] == "directory"
                         else [member["path"]])
        module["files"] = sorted(files)
        module["paths"] = (sorted(m["path"] for m in module["members"]) if module["provenance"] == "build"
                           else _review_paths(inventory, files))
        module["coverage"] = {"members": len(module["members"]),
                              "resolved": sum(1 for m in module["members"] if m["resolved"]),
                              "files": len(files),
                              "source_files": sum(1 for f in files if inventory.headers[f].get("language"))}
        module["members_digest"] = _digest([[m["id"], m.get("hash"), inventory.hash(m["path"])] for m in module["members"]]
                                           + [module["files"]])


def _ownership(inventory: _Inventory, modules: list[dict], by_id: dict, gaps: list[dict]):
    """Ownership of files: the most specific directory or file member; symbols on their own."""
    file_owner: dict[str, list[str]] = {}
    specific: dict[str, tuple[int, list[str]]] = {}
    symbol_owner: dict[str, dict[str, list[str]]] = {}
    for module in modules:
        for member in module["members"]:
            if not member["resolved"]:
                continue
            if member["kind"] == "symbol":
                symbol_owner.setdefault(member["path"], {}).setdefault(module["id"], []).append(member["symbol"])
            elif member["kind"] == "file":
                file_owner.setdefault(member["path"], []).append(module["id"])
            else:
                for rel in inventory.files_under([member["path"]], module["excluded"]):
                    depth = -1 if member["path"] == "." else len(member["path"])
                    if module["provenance"] == "build":
                        if rel not in specific or depth > specific[rel][0]:
                            specific[rel] = (depth, [module["id"]])
                        elif depth == specific[rel][0]:
                            specific[rel][1].append(module["id"])
                    else:
                        file_owner.setdefault(rel, []).append(module["id"])
    ambiguous_owners = set()
    for rel, (_, owners) in specific.items():
        if len(owners) == 1:
            file_owner.setdefault(rel, []).extend(owners)
        else:
            ambiguous_owners.add(tuple(sorted(owners)))
    for owners in sorted(ambiguous_owners):
        gaps.append({"kind": "ownership_ambiguous", "path": by_id[owners[0]]["members"][0]["path"],
                     "detail": "Directory scope cannot distinguish build ownership: " + ", ".join(owners)})
    return {rel: sorted(set(ids)) for rel, ids in file_owner.items()}, symbol_owner


class _Edges:
    """Edges keyed by kind, source and target, each with bounded evidence."""

    def __init__(self, by_id: dict):
        self.by_id = by_id
        self.edges: dict[str, dict] = {}

    def add(self, kind, source, target, status, evidence) -> None:
        # Build units and responsibility modules are two layers: a build unit
        # holds a module's files (`owned_by` in the query), it does not call it.
        # An external module sits outside both layers, so `uses` reaches it from either.
        if kind != "uses" and (self.by_id[source]["provenance"] == "build") != (self.by_id[target]["provenance"] == "build"):
            return
        key = f"{kind}:{source}->{target}"
        record = self.edges.setdefault(key, {"id": key, "kind": kind, "source": source, "target": target,
                                             "status": status, "evidence": [], "evidence_total": 0})
        record["evidence_total"] += 1
        if evidence not in record["evidence"] and len(record["evidence"]) < MAX_EDGE_EVIDENCE:
            record["evidence"].append(evidence)

    def status(self, source: str, target: str) -> str:
        """`confirmed` only between two confirmed modules."""
        return "confirmed" if self.by_id[source]["status"] == self.by_id[target]["status"] == "confirmed" else "inferred"

    def listed(self) -> list[dict]:
        return [self.edges[k] for k in sorted(self.edges)]


def _names_by_package(units: list[dict], build_by_key: dict) -> dict[tuple[str, str], set[str]]:
    by_name: dict[tuple[str, str], set[str]] = {}
    # Query aliases (including directory basenames) are not package identities.
    for unit in units:
        family = _family(unit["ecosystem"])
        module_id = build_by_key[(unit["directory"], family, unit.get("slot"))]
        for name in [unit["name"], *unit["aliases"]]:
            if name:
                by_name.setdefault((family, _dependency_name(name, family)), set()).add(module_id)
    return by_name


def _path_dependency_edges(module: dict, text: str, family: str, build_by_key: dict, by_name: dict,
                           edges: _Edges) -> tuple[set[str], set[str]]:
    """Dependencies declared with a path or a repository; returns the names they settle and the remote ones."""
    path_names = set()  # settled by path; a path that holds no unit leaves its name a declared dependency
    remote = set()  # taken from another repository: never the unit that has the same name here
    for item in module["path_dependencies"]:
        if item.get("git"):
            remote.add(_dependency_name(item["name"], family))
            continue
        if item["path"]:
            target = build_by_key.get((item["path"], family, item.get("slot")))
            targets = {target} if target else set()
        else:
            targets = by_name.get((family, _dependency_name(item["name"], family)), set())
        targets = targets - {module["id"]}
        site = {"path": module["manifests"][0] if module["manifests"] else module["members"][0]["path"],
                "line": _line_of(text, item["name"])}
        if len(targets) == 1:
            edges.add("declares", module["id"], next(iter(targets)), "confirmed", site)
        elif len(targets) > 1:
            module["gaps"].append({"kind": "dependency_ambiguous", "detail": f"{item['name']}: several build units match"})
        elif build_by_key.get((item["path"], family, item.get("slot"))) != module["id"]:
            module["gaps"].append({"kind": "dependency_unresolved",
                                   "detail": f"{item['name']} -> {item['path'] or 'no path'}: no build unit there"})
            continue
        path_names.add(_dependency_name(item["name"], family))
    return path_names, remote


def _build_edges(inventory: _Inventory, modules: list[dict], units: list[dict], build_by_key: dict,
                 edges: _Edges) -> None:
    """`declares` between build units from their manifests, `contains` from workspace registrations."""
    by_name = _names_by_package(units, build_by_key)
    for module in modules:
        if module["provenance"] != "build":
            continue
        text = inventory.text(module["manifests"][0]) if module["manifests"] else ""
        family = _family(module["ecosystems"][0])
        external = []
        path_names, remote = _path_dependency_edges(module, text, family, build_by_key, by_name, edges)
        for name in module["dependencies"]:
            if _dependency_name(name, family) in path_names:
                continue
            targets = (set() if _dependency_name(name, family) in remote
                       else by_name.get((family, _dependency_name(name, family)), set()) - {module["id"]})
            if family == "go":
                targets = {t for t in targets if set(module["registered_by"]) & set(edges.by_id[t]["registered_by"])}
            if len(targets) == 1:
                edges.add("declares", module["id"], next(iter(targets)), "confirmed",
                          {"path": module["manifests"][0], "line": _line_of(text, name)})
            elif not targets:
                external.append(name)
            else:
                module["gaps"].append({"kind": "dependency_ambiguous", "detail": f"{name}: several build units match"})
        module["external"] = external
        for parent, site in module.pop("registrations"):
            if parent in build_by_key and build_by_key[parent] != module["id"]:
                edges.add("contains", build_by_key[parent], module["id"], "confirmed", site)


def _import_edges(store, file_owner: dict, symbol_owner: dict, edges: _Edges) -> None:
    """`imports` from resolved imports between files of different modules."""
    resolved_imports = snapshot.resolved_imports(store)
    for importer in sorted(resolved_imports):
        entry = None
        sources = file_owner.get(importer, [])
        if not sources:
            continue
        for specifier, targets in sorted(resolved_imports[importer].items()):
            for target in targets:
                if target == importer:
                    continue
                if entry is None:
                    entry = store.get_file(importer) or {}
                line = next((i["span"][0] for i in entry.get("semantic", {}).get("imports", [])
                             if i.get("module") == specifier and i.get("span")), None)
                named = {n.split(" as ", 1)[0].strip() for b in entry.get("import_bindings", [])
                         if b.get("from") and b.get("module") == specifier for n in b.get("names", [])}
                destinations = set(file_owner.get(target, []))
                destinations.update(mid for mid, names in symbol_owner.get(target, {}).items() if set(names) & named)
                for source in sources:
                    for destination in sorted(destinations):
                        if source != destination:
                            edges.add("imports", source, destination, edges.status(source, destination),
                                      {"path": importer, "line": line, "imported": target})


def _uses_edges(modules: list[dict], edges: _Edges) -> None:
    """`uses` from the files that bind to an external module, as its evidence cites them."""
    for module in modules:
        if module["location"] != "external":
            continue
        for site in module["evidence"]:
            if not site["resolved"]:
                continue
            for owner in modules:
                if owner["id"] != module["id"] and site["path"] in owner["files"]:
                    status = "confirmed" if owner["status"] == module["status"] == "confirmed" else "inferred"
                    edges.add("uses", owner["id"], module["id"], status, {"path": site["path"], "line": site["line"]})


def _module_edges(store, inventory: _Inventory, modules: list[dict], units: list[dict], build_by_key: dict,
                  file_owner: dict, symbol_owner: dict, by_id: dict, gaps: list[dict]) -> list[dict]:
    edges = _Edges(by_id)
    _build_edges(inventory, modules, units, build_by_key, edges)
    _import_edges(store, file_owner, symbol_owner, edges)
    if symbol_owner or any(m["provenance"] != "build" for m in modules):
        try:
            for call in _call_edges(store, symbol_owner, file_owner):
                edges.add("calls", call["source"], call["target"], edges.status(call["source"], call["target"]),
                          {"path": call["path"], "line": call["line"], "caller": call["caller"], "callee": call["callee"]})
        except ValueError as error:
            gaps.append({"kind": "calls_unavailable", "detail": str(error)})
    _uses_edges(modules, edges)
    return edges.listed()


def _graph(store, inventory: _Inventory, modules: list[dict], edge_list: list[dict], gaps: list[dict]) -> dict:
    return {
        "schema": SCHEMA,
        "binding": {"manifest": str(Path(store.path).resolve()), "logical_digest": logical_digest(store),
                    "root": store["root"], "target": store["target"], "git": store.get("git")},
        "modules": modules,
        "edges": edge_list,
        "coverage": {"files": len(inventory.files), "ecosystems": ECOSYSTEMS,
                     "modules": {p: sum(1 for m in modules if m["provenance"] == p) for p in PROVENANCES},
                     "statuses": {s: sum(1 for m in modules if m["status"] == s) for s in STATUSES},
                     "edges": {k: sum(1 for e in edge_list if e["kind"] == k) for k in ("declares", "contains", "imports", "calls", "uses")}},
        "gaps": gaps,
        "notes": [
            "Build units come from manifests only; declared modules from codebase-modules.json; proposed modules from "
            "the ledger beside the snapshot and stay inferred until declared. No Markdown is interpreted here.",
            "Static edges prove no runtime behavior; a missing call edge proves no independence (lexical resolver).",
        ],
    }


def derive(store, *, ledger: list[dict] | None = None) -> dict:
    """Derive the module graph of a snapshot; deterministic for the same inputs."""
    inventory = _Inventory(store)
    units, gaps = _read_units(inventory)
    by_directory = _merge_units(units)
    _register_members(inventory, by_directory, gaps)
    modules = [_build_module(inventory, merged, by_directory) for merged in by_directory.values()]
    modules.extend(_declared_modules(inventory, store, ledger, gaps))
    _assign_identities(modules)
    by_id = {m["id"]: m for m in modules}
    _measure_modules(inventory, modules)
    file_owner, symbol_owner = _ownership(inventory, modules, by_id, gaps)
    build_by_key = {key: module["id"] for key, module in zip(by_directory, modules)}  # build modules come first, in this order
    edge_list = _module_edges(store, inventory, modules, units, build_by_key, file_owner, symbol_owner, by_id, gaps)
    modules.sort(key=lambda m: m["id"])
    for module in modules:
        module.pop("path_dependencies", None)
    return _graph(store, inventory, modules, edge_list, gaps)
