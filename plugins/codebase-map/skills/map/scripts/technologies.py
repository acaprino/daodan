#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Step 2 (`stack`): per-module frameworks, libraries, services and tools from Step 1's map and facts.

Reads only Step 1's module graph and pre-map facts (`packages`, `services`, `docker_builds`, `excluded`, `toolchains`),
with zero tool execution and zero duplicate manifest parsing. Every concrete, logical and virtual module receives its
languages, toolchains, frameworks, declared libraries (cataloged or not), external services and tools.
An entry with no `declared` sign, only lines of text that mention it, is no module's: it stays in `mentioned` with its
signs. `checkers` gives each checker's status (`service_registry.CHECKERS`) and `gaps` what they could not establish.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_units import _family  # noqa: E402
import confinement  # noqa: E402
from module_derive import PREMAP_KIND_ECOSYSTEM  # noqa: E402
import modules  # noqa: E402
import premap  # noqa: E402
import service_registry  # noqa: E402
from snapshot_store import logical_digest, open_snapshot  # noqa: E402

SCHEMA, FILE = "daodan/technologies/v1", "technologies.json"


def _versions_only(rel: str | None) -> bool:
    """A Gradle version catalog or .NET central package versions: a package there has its version, and the module
    that uses it declares it in its own build file (`premap.jvm_files` reads `libs.*`), not the one holding the file."""
    name = Path(rel or "").name
    return name.endswith(".versions.toml") or name == "Directory.Packages.props"


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


def _references(graph: dict, units: list[dict]) -> dict[str, str]:
    """Build module id -> how the pre-map refers to its unit: the unit's name, or its root when no file names it or
    another unit has the same name. A module is the unit of its folder and ecosystem, or the folder's only unit."""
    count, by_root = Counter(u.get("name") for u in units), {}
    for unit in units:
        by_root.setdefault(unit["root"], []).append(unit)
    out = {}
    for module in graph["modules"]:
        if module["provenance"] != "build" or not module.get("members"):
            continue
        here = by_root.get(module["members"][0]["path"], [])
        families = {_family(e) for e in module.get("ecosystems") or ()}
        found = [u for u in here if _family(PREMAP_KIND_ECOSYSTEM.get(u["kind"], "")) in families] or here
        if len(found) == 1:
            out[module["id"]] = found[0]["name"] if found[0].get("name") and count[found[0]["name"]] == 1 \
                else found[0]["root"]
    return out


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
    recognized = service_registry.run(manifest, registry, facts)
    entries, mentioned = [], []
    for found in recognized["found"]:
        entry = {k: v for k, v in found.items() if k != "source"}
        (entries if any(s["strength"] == "declared" for s in entry["signs"]) else mentioned).append(entry)
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
    refs = _references(graph, facts.get("units") or [])
    all_modules, units = [], []
    for unit in graph["modules"]:
        name = refs.get(unit["id"], unit["name"])  # the pre-map's reference; the module's names stay aliases
        named = {"id": unit["id"], "name": name,
                 "aliases": sorted({unit["name"], *(unit.get("aliases") or ())} - {name})}
        if unit.get("location") == "external":
            item = {
                **named, "kind": unit["kind"],
                "nature": unit.get("nature", "logical"), "provenance": unit["provenance"],
                "paths": unit["paths"], "languages": {}, "toolchains": [],
                "frameworks": [], "libraries": [], "services": [], "tools": [], "technologies": [],
            }
            all_modules.append(item)
            continue
        owned = _module_files(unit, physical)
        matched = [e for e in entries if any(s["path"] in owned and not (s["sign"] == "package" and _versions_only(
            s["path"])) for s in e["signs"])]
        frameworks = [e["id"] for e in matched if e.get("category") == "framework"]
        services = [e["id"] for e in matched if e.get("category") == "service"]
        tools = [e["id"] for e in matched if e.get("category") == "tool"]
        libs = []
        seen_libs = set()
        for eco, pkg_name, pkg_path, pkg_line, version in raw_packages:
            if pkg_path in owned and not _versions_only(pkg_path) and (eco, pkg_name.casefold()) not in seen_libs:
                seen_libs.add((eco, pkg_name.casefold()))
                reg_entry = known_pkg.get((pkg_name.casefold(), pkg_path))
                libs.append({
                    "ecosystem": eco, "name": pkg_name, "path": pkg_path, "line": pkg_line,
                    **({"version": version} if version else {}),
                    **({"id": reg_entry["id"], "title": reg_entry["name"]} if reg_entry else {}),
                })
        libs.sort(key=lambda x: (x["ecosystem"], x["name"].casefold()))
        item = {
            **named, "kind": unit["kind"],
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
            "inputs_digest": digest, "technologies": entries, "mentioned": mentioned, "units": units,
            "modules": all_modules, "checkers": recognized["checkers"], "gaps": recognized["gaps"]}


def _read(manifest: Path, digest: str) -> dict | None:
    try:
        record = json.loads(path(manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return record if record.get("schema") == SCHEMA and record.get("inputs_digest") == digest and "checkers" in record else None


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
