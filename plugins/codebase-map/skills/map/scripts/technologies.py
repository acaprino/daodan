#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Step 2 (`stack`): per-module frameworks, libraries, services and tools from Step 1's map and facts.

Reads only Step 1's module graph and pre-map facts (`packages`, `services`, `docker_builds`, `excluded`, `toolchains`),
with zero tool execution and zero duplicate manifest parsing. Every concrete, logical and virtual module receives its
languages, toolchains, frameworks, declared libraries (cataloged or not), external services and tools.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import confinement  # noqa: E402
import modules  # noqa: E402
import premap  # noqa: E402
import service_registry  # noqa: E402
from snapshot_store import logical_digest, open_snapshot  # noqa: E402

SCHEMA, FILE = "daodan/technologies/v1", "technologies.json"


def path(manifest: Path) -> Path:
    return Path(manifest).with_name(FILE)


def _inputs(manifest: Path, registry: dict, facts: dict) -> tuple[str, str, str]:
    """The digest of what the record is derived from, and the snapshot's root and target."""
    graph_digest = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"])).get("inputs_digest")
    with open_snapshot(manifest) as store:
        root, target = store["root"], store.get("target") or "."
        value = [logical_digest(store), graph_digest, root, registry.get("versions"), SCHEMA,
                 facts.get("packages"), facts.get("services"), facts.get("docker_builds"),
                 facts.get("excluded"), facts.get("toolchains"), facts.get("units")]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest(), root, target


def _module_files(module: dict, physical: list[dict]) -> set[str]:
    files = set(module.get("files") or ()) | set(module.get("manifests") or ())
    if module["provenance"] not in modules.PHYSICAL:
        for ev in module.get("evidence") or ():
            if ev.get("resolved") and ev.get("path"):
                files.add(ev["path"])
        for owner in physical:
            if any(rel in owner.get("files", ()) for rel in module.get("files") or ()):
                files.update(owner.get("manifests") or ())
    return files


def derive(manifest: Path, registry: dict, facts: dict) -> dict:
    """The stack record of `manifest` from the registry and Step 1's `facts`."""
    entries = [{k: v for k, v in e.items() if k != "source"}
               for e in service_registry.recognize(manifest, registry, facts)]
    if "sources" in facts:
        graph = modules.sync_with_premap(manifest, facts)
    else:
        graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
    left_out = tuple(item["path"] for item in facts.get("excluded") or () if item.get("path"))
    raw_packages = [s for s in service_registry.step1_packages(manifest, facts)
                    if s[0] != "docker" and not service_registry._is_excluded(s[2], left_out)]
    known_pkg: dict[tuple[str, str | None], dict] = {}
    for entry in entries:
        for sign in entry["signs"]:
            if sign["sign"] == "package":
                known_pkg.setdefault((sign["value"].casefold(), sign["path"]), entry)

    physical = [m for m in graph["modules"] if m["provenance"] in modules.PHYSICAL]
    all_modules, units = [], []
    for unit in graph["modules"]:
        if unit.get("location") == "external":
            item = {
                "id": unit["id"], "name": unit["name"], "kind": unit["kind"],
                "nature": unit.get("nature", "logical"), "provenance": unit["provenance"],
                "paths": unit["paths"], "languages": {}, "toolchains": [],
                "frameworks": [], "libraries": [], "services": [], "tools": [], "technologies": [],
            }
            all_modules.append(item)
            continue
        owned = _module_files(unit, physical)
        matched = [e for e in entries if any(s["path"] in owned for s in e["signs"])]
        frameworks = [e["id"] for e in matched if e.get("category") == "framework"]
        services = [e["id"] for e in matched if e.get("category") == "service"]
        tools = [e["id"] for e in matched if e.get("category") == "tool"]
        libs = []
        seen_libs = set()
        for eco, pkg_name, pkg_path, pkg_line in raw_packages:
            if pkg_path in owned and (eco, pkg_name.casefold()) not in seen_libs:
                seen_libs.add((eco, pkg_name.casefold()))
                reg_entry = known_pkg.get((pkg_name.casefold(), pkg_path))
                libs.append({
                    "ecosystem": eco, "name": pkg_name, "path": pkg_path, "line": pkg_line,
                    **({"id": reg_entry["id"], "title": reg_entry["name"]} if reg_entry else {}),
                })
        libs.sort(key=lambda x: (x["ecosystem"], x["name"].casefold()))
        item = {
            "id": unit["id"], "name": unit["name"], "kind": unit["kind"],
            "nature": unit.get("nature", "concrete"), "provenance": unit["provenance"],
            "paths": unit["paths"], "languages": unit.get("languages", {}),
            "toolchains": unit.get("toolchains", []),
            "frameworks": frameworks, "libraries": libs, "services": services, "tools": tools,
            "technologies": [e["id"] for e in matched],
        }
        all_modules.append(item)
        if unit["provenance"] in modules.PHYSICAL:
            units.append(item)
    digest, root, target = _inputs(manifest, registry, facts)
    return {"schema": SCHEMA, "manifest": manifest.as_posix(), "root": root, "target": target,
            "inputs_digest": digest, "technologies": entries, "units": units, "modules": all_modules}


def _read(manifest: Path, digest: str) -> dict | None:
    try:
        record = json.loads(path(manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return record if record.get("schema") == SCHEMA and record.get("inputs_digest") == digest and "modules" in record else None


def state(manifest: Path, *, facts: dict | None = None) -> str:
    """fresh, stale or missing."""
    manifest = Path(manifest).resolve()
    if not path(manifest).is_file():
        return "missing"
    facts = premap.ensure(manifest) if facts is None else facts
    digest = _inputs(manifest, service_registry.load(), facts)[0]
    return "fresh" if _read(manifest, digest) else "stale"


def ensure(manifest: Path, *, facts: dict | None = None) -> dict:
    """The record of `manifest`, derived and written again when it is not fresh."""
    manifest = Path(manifest).resolve()
    registry = service_registry.load()
    facts = premap.ensure(manifest) if facts is None else facts
    record = _read(manifest, _inputs(manifest, registry, facts)[0])
    if record is None:
        target = path(manifest)
        confinement.reject_link_chain(target)
        record = derive(manifest, registry, facts)
        descriptor, name = tempfile.mkstemp(prefix=".technologies-", dir=target.parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(json.dumps(record, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        os.replace(name, target)
    return record
