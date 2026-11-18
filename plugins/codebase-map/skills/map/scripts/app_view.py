"""What the app's page draws, composed from a run: the pre-map's inventory and the graph's groups.

Composition only: the stack, the modules and the envelope are the service's; the files and their languages are the
run's snapshot headers. Nothing of the project runs. The graph groups files by module when the run has two or more,
otherwise by the directory that holds them, and counts the relations between groups.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import PurePosixPath

from premap.suffix_table import NAMES
from snapshot_store import open_snapshot, resolve_run_snapshot

STRUCTURE = ("file", "directory", "symbol")
EVIDENCE = 20  # sites kept per relation, as the envelope keeps


def headers(run_dir) -> dict:
    """The snapshot's file headers of the run in `run_dir`, by path."""
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    with open_snapshot(resolve_run_snapshot(run_dir, state)) as store:
        return dict(store.iter_file_headers_only())


def _inside(path: str, root: str) -> bool:
    return root in ("", ".") or path == root or path.startswith(root.rstrip("/") + "/")


def premap(stack: dict, modules: dict, files: dict) -> dict:
    """Files, languages, technologies and the units of the stack with their declared libraries."""
    if "modules" not in stack:  # the snapshot's gate answered in place of the stack
        raise ValueError(stack.get("reason") or "the stack of the run is not available")
    described = {module["id"]: module for module in modules.get("modules", [])}
    known = {item["id"]: item for item in stack["technologies"]}
    units, technologies = [], []
    for module in stack["modules"]:
        root = (module.get("paths") or ["."])[0]
        declared = [tool["declared_in"] for tool in module.get("toolchains", [])]
        units.append({
            "id": module["id"], "name": module["name"], "root": root, "kind": module.get("kind"),
            "status": described.get(module["id"], {}).get("status"),
            "description": described.get(module["id"], {}).get("description") or "",
            "manifest": next(iter(declared + [item["path"] for item in module.get("libraries", [])]), None),
            "dependencies": [{"name": item["name"], "scope": item["ecosystem"], "state": "declared",
                              "source": item["path"] + (f":{item['line']}" if item.get("line") else ""),
                              **({"version": item["version"]} if item.get("version") else {})}
                             for item in module.get("libraries", [])]})
        for ident in module.get("technologies", []):
            found = known.get(ident)
            if found is None:
                continue
            signs = found.get("signs") or [{}]
            sign = next((s for s in signs if _inside(s.get("path") or "", root)), signs[0])
            technologies.append({"name": found["name"], "category": found.get("category") or "tecnologia",
                                 "source": (sign.get("path") or "") + (f":{sign['line']}" if sign.get("line") else ""),
                                 "unit": root, "state": "recognized"})
        technologies.extend({"name": tool["tool"], "category": "toolchain", "version": tool.get("version") or "",
                             "source": tool["declared_in"], "unit": root, "state": "declared"}
                            for tool in module.get("toolchains", []))
    for unit in units:
        parents = [other for other in units if other is not unit and other["root"] != unit["root"]
                   and _inside(unit["root"], other["root"])]
        unit["parent"] = max(parents, key=lambda other: len(other["root"]))["id"] if parents else None
    languages = Counter(header["language"] for header in files.values() if header.get("language"))
    return {"files": sorted(files), "units": units, "technologies": technologies,
            "languages": [{"name": NAMES.get(name, name.capitalize()), "files": count}
                          for name, count in sorted(languages.items(), key=lambda item: (-item[1], item[0]))]}


def graph(envelope: dict) -> dict:
    """The envelope's files grouped into nodes, and the relations between groups with their counts and sites."""
    entities = {item["ref"]: item for item in envelope["entities"]}
    files = sorted(ref for ref, item in entities.items() if item["type"] == "file")
    # a virtual module is the tree no build names, not a group of its own: its files show by their directories
    groups = [ref for ref, item in entities.items() if item["type"] not in (*STRUCTURE, "virtual")]
    owner: dict[str, str] = {}
    if len(groups) >= 2:
        level = "modules"
        sizes = Counter(item["group"] for item in envelope["memberships"] if item["group"] in groups)
        for item in envelope["memberships"]:  # a file in nested modules belongs to the smallest
            if item["group"] in sizes and item["member"] in entities and entities[item["member"]]["type"] == "file":
                current = owner.get(item["member"])
                if current is None or sizes[item["group"]] < sizes[current]:
                    owner[item["member"]] = item["group"]
    else:
        level = "directories"
        for ref in files:
            parent = PurePosixPath(entities[ref]["path"]).parent.as_posix()
            owner[ref] = f"directory:{parent}"
            if owner[ref] not in entities:
                entities[owner[ref]] = {"ref": owner[ref], "type": "directory", "name": parent, "path": parent}
        groups = sorted(set(owner.values()))
    nodes = {ref: {"id": ref, "name": entities[ref]["path"] if level == "directories" else entities[ref]["name"],
                   "kind": entities[ref]["type"], "location": entities[ref].get("location", "internal"),
                   "status": entities[ref].get("status") or ("confirmed" if level == "directories" else None),
                   "provenance": entities[ref].get("provenance"),
                   "responsibility": entities[ref].get("description") or "",
                   "evidence": entities[ref].get("evidence", []), "files": []}
             for ref in groups}
    for ref in files:
        if ref in owner:
            nodes[owner[ref]]["files"].append(entities[ref]["path"])
    edges: dict[tuple, dict] = {}
    for relation in envelope["relations"]:
        source, target = relation["source"], relation["target"]
        if relation["kind"] in ("contains", "defines"):
            continue
        if source in nodes and target in nodes:  # a relation between modules, counted by the envelope
            counts, site = relation.get("counts") or {relation["kind"]: 1}, None
        elif source in owner and target in owner:  # a relation between files, counted once
            source, target, counts = owner[source], owner[target], {relation["kind"]: 1}
            site = {"kind": relation["kind"], "path": relation["source"].removeprefix("file:"), "line": None,
                    "target": relation["target"].removeprefix("file:")}
        else:
            continue
        if source == target:
            continue
        edge = edges.setdefault((source, target), {"id": f"{source}->{target}", "source": source, "target": target,
                                                   "counts": {}, "status": relation["status"], "evidence": []})
        for kind, count in counts.items():
            edge["counts"][kind] = edge["counts"].get(kind, 0) + count
        sites = relation.get("evidence", []) if site is None else [site]
        edge["evidence"].extend([{"kind": relation["kind"], **item} for item in sites][:EVIDENCE - len(edge["evidence"])])
    alone = [entities[ref]["path"] for ref in files if ref not in owner]
    areas = Counter(PurePosixPath(path).parent.as_posix() for path in alone)
    return {"level": level, "nodes": sorted(nodes.values(), key=lambda node: node["name"]),
            "edges": sorted(edges.values(), key=lambda edge: edge["id"]), "files": len(files),
            "symbols": sum(item["type"] == "symbol" for item in entities.values()),
            "unassigned": {"count": len(alone), "areas": areas.most_common(8)},
            "gaps": envelope.get("gaps", []), "meta": envelope.get("meta", {})}
