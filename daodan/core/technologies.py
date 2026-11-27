#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Step 2 (`stack`): per-module frameworks, libraries, services and tools from Step 1's map and facts.

Reads the stack step's record (`stack_recognition.ensure`: what the project's files show, recognized only by the pinned
stack-analyser release, which reads files and executes nothing of the project, before `find_modules`), then Step 1's module
graph and pre-map facts (`packages`, `configured_services`, `services`, `docker_builds`, `excluded`, `toolchains`) without
parsing a manifest again, and gives each module the technologies its files declare; the registry gives each entry's name,
category, type, site and mark. Every concrete, logical and virtual module receives its
languages, toolchains, frameworks, declared libraries (cataloged or not), external services and tools.
`configured_services` preserves Compose and CI declarations, including names and images outside the registry.
For build modules with a native package graph, `resolved_libraries` records the reachable external packages
and their exact versions. A resolved package can be conditional on a target or feature.
An entry with no `declared` sign, only lines of text that mention it, is no module's: it stays in `mentioned` with its
signs. Every sign carries its `source` and the `scan` (the pre-map's `inputs_digest`) that produced it: a scan replaces the
signs of the sources it ran and keeps those of the stack step's other sources while their file exists and the pre-map does
not leave it out (`merge`), and says what it kept (`signs_kept`). The record follows the stack step's: one derived again
there is derived again here. `checkers` gives each checker's status (`stack-analyser`, `host`)
and `gaps` what they could not establish. The process: docs/plugins/codebase-map.md, «Lo step `stack`».
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
import stack_recognition  # noqa: E402
from snapshot_store import inventory_digest, open_snapshot  # noqa: E402

SCHEMA, FILE = "daodan/technologies/v1", "technologies.json"
MATCHER_VERSION = 5  # Cache identity for recognition and attribution changes within the v1 output format.


def _versions_only(rel: str | None) -> bool:
    """A Gradle version catalog or .NET central package versions: a package there has its version, and the module
    that uses it declares it in its own build file (`premap.jvm_files` reads `libs.*`), not the one holding the file."""
    name = Path(rel or "").name
    return name.endswith(".versions.toml") or name == "Directory.Packages.props"


def module_declaration(sign: dict) -> bool:
    """A sign whose owning module declares the technology."""
    return (sign.get("strength") == "declared" and bool(sign.get("path"))
            and not (sign.get("sign") == "package" and _versions_only(sign["path"])))


def sites(signs: list[dict]) -> list[dict]:
    """One sign per site of a technology, its kind, file and line: the record keeps each source's sign. A sign without a
    line (the tool reading a file by itself, the name as written) is the site of a line of its file when the file has
    one for this technology (a declaration of the pre-map, the name as it keeps it); in a file with none, each name is a
    site. In the order of kind, file and line, a site with its line before one without."""
    lined = {(sign.get("sign"), sign.get("path")) for sign in signs if sign.get("line")}
    out = {}
    for sign in signs:
        where = (sign.get("sign"), sign.get("path"))
        if sign.get("line") or where not in lined:
            out.setdefault((*where, sign.get("line") or sign.get("value")), dict(sign))
    return sorted(out.values(), key=lambda s: (s["sign"], s["path"] or "", not s["line"], s["line"] or 0, s["value"]))


def path(manifest: Path) -> Path:
    return Path(manifest).with_name(FILE)


def _inputs(manifest: Path, registry: dict, facts: dict, stack: dict) -> tuple[str, str, str]:
    """The digest of what the record is derived from (the stack step's record `stack` among it), and the snapshot's root
    and target."""
    graph_digest = modules.load_graph(Path(modules.ensure_structure(manifest)["graph"])).get("inputs_digest")
    with open_snapshot(manifest) as store:
        root, target = store["root"], store.get("target") or "."
        value = [inventory_digest(store), graph_digest, root, registry, SCHEMA, MATCHER_VERSION, stack,
                 facts.get("packages"), facts.get("package_graphs"), facts.get("services"), facts.get("configured_services"),
                 facts.get("docker_builds"), facts.get("excluded"), facts.get("toolchains"), facts.get("units")]
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


def _configured_services(facts: dict, excluded: tuple[str, ...]) -> list[dict]:
    """Service instances as declared, independent of registry membership and of any observed execution."""
    result = []
    for service in [*(facts.get("configured_services") or ()), *(facts.get("services") or ())]:
        site, name = service["declared_in"], service["name"]
        path, line = service_registry.service_site(service)
        if path and not service_registry._is_excluded(path, excluded):
            result.append({"name": name, "path": path, "declared_in": site,
                           **({"line": line} if line else {}),
                           **{key: service[key] for key in ("image", "profiles") if service.get(key)}})
    return sorted(result, key=lambda item: (item["path"], item.get("line", 0), item["declared_in"], item["name"]))


def _resolved_libraries(graph: dict, member: int) -> list[dict]:
    """The external packages reachable from a workspace member, including that member's own dev dependencies."""
    nodes = graph["nodes"]
    direct = {edge["to"] for edge in nodes[member]["dependencies"]}
    pending = list(direct)
    seen = {member}
    result = []
    while pending:
        index = pending.pop()
        if index in seen:
            continue
        seen.add(index)
        node = nodes[index]
        if "manifest" not in node and not node.get("local"):
            result.append({"ecosystem": graph["ecosystem"], "name": node["name"], "version": node["version"],
                           "direct": index in direct, "path": graph["path"]})
        # Cargo builds a dependency without that dependency's own development requirements.
        pending.extend(edge["to"] for edge in node["dependencies"] if edge.get("kind") != "dev")
    return sorted(result, key=lambda row: (not row["direct"], row["name"], row["version"]))


def _sign_key(ident: str, sign: dict) -> tuple:
    return ident, *(sign.get(key) for key in ("sign", "value", "path", "line", "source"))


def merge(found: list[dict], ran: set[str], previous: dict | None, scan: str, exists, registry: dict) -> tuple[list[dict], list[dict]]:
    """The entries of this scan's `found`, each sign with its `scan`, and those of the `previous` record whose source is
    one of the stack step's (`stack_recognition.SOURCES`) not in `ran` (the label up to `@`) and whose file `exists`. A
    sign with no path is kept; one with no source (a record of another shape) or of another source is not, nor one this
    scan made too. A kept entry has the registry's data of now. A gap says
    what was kept."""
    now = {e["id"]: {**e, "signs": [{**s, "scan": scan} for s in e["signs"]]} for e in found}
    made = {_sign_key(e["id"], s) for e in found for s in e["signs"]}
    kept, sources, scans = {}, set(), set()
    for old in [*(previous or {}).get("technologies", ()), *(previous or {}).get("mentioned", ())]:
        for sign in old.get("signs") or ():
            name = (sign.get("source") or "").partition("@")[0]
            if (name in stack_recognition.SOURCES and name not in ran and _sign_key(old["id"], sign) not in made
                    and (not sign.get("path") or exists(sign["path"]))):
                kept.setdefault(old["id"], []).append(sign)
                sources.add(name)
                scans.add(sign.get("scan"))
    for ident in kept:
        if ident in now:
            now[ident]["signs"] += kept[ident]
    entries, gaps = stack_recognition.found({}, registry, set(), (), [(i, s) for i in kept if i not in now for s in kept[i]])
    entries = [*now.values(), *entries]
    for item in entries:
        item["signs"].sort(key=lambda s: (s["sign"], s["path"] or "", s["line"] or 0, s["value"]))
    return sorted(entries, key=lambda e: e["id"]), gaps + (
        [{"kind": "signs_kept", "sources": sorted(sources), "scans": sorted(scans, key=str)}] if kept else [])


def _placed(sign: dict, declared: dict) -> dict:
    """`sign` with the line where the pre-map declares its package in its file (`declared_in`), when the tool read the
    file without one: the site of the module's technology."""
    if sign.get("line") or sign.get("sign") != "package":
        return sign
    line = next((line for eco, key, line in declared.get(sign.get("path"), ())
                 if service_registry.package_key(eco, sign["value"]) == key), None)
    return {**sign, "line": line} if line else sign


def derive(manifest: Path, registry: dict, facts: dict) -> dict:

    """The stack record of `manifest` from the registry, the stack step's record and Step 1's `facts`; the signs of the
    sources the recogniser did not run come from the record beside `manifest`, as it is before this one replaces it
    (`merge`)."""
    recognized = stack_recognition.ensure(manifest, registry)
    digest, root, target = _inputs(manifest, registry, facts, recognized)
    left_out = stack_recognition._left_out(facts)
    packages = service_registry.step1_packages(manifest, facts)
    declared: dict[str, list[tuple[str, str, int]]] = {}  # a file -> (ecosystem, package key, line) the pre-map declares
    for eco, pkg_name, pkg_path, pkg_line, _ in packages:
        if pkg_path and pkg_line:
            declared.setdefault(pkg_path, []).append((eco, service_registry.package_key(eco, pkg_name), pkg_line))
    # The stack's perimeter is the snapshot's; what the pre-map leaves out besides (a submodule) is no sign of the project.
    found = [{**entry, "signs": [_placed(s, declared) for s in signs]} for entry in recognized["found"]
             if (signs := [s for s in entry["signs"] if not service_registry._is_excluded(s.get("path"), left_out)])]
    merged, kept = merge(found, set(recognized.get("ran") or ()), recorded(manifest),
                         facts.get("inputs_digest"), registry=registry,
                         exists=lambda rel: Path(root, rel).is_file() and not service_registry._is_excluded(rel, left_out))
    entries, mentioned = [], []
    for found in merged:
        entry = {k: v for k, v in found.items() if k != "source"}
        (entries if any(s["strength"] == "declared" for s in entry["signs"]) else mentioned).append(entry)
    if "sources" in facts:
        graph = modules.sync_with_premap(manifest, facts)
    else:
        graph = modules.load_graph(Path(modules.ensure_structure(manifest)["graph"]))
    configured = _configured_services(facts, left_out)
    resolved_members = {node["manifest"]: (model, i) for model in facts.get("package_graphs", ())
                        for i, node in enumerate(model["nodes"]) if "manifest" in node}
    raw_packages = [s for s in packages
                    if s[0] != "docker" and not service_registry._is_excluded(s[2], left_out)]
    known_pkg: dict[tuple[str, str | None], dict] = {}
    declarations_by_path: dict[str, list[tuple[str, dict]]] = {}
    for entry in entries:
        for sign in entry["signs"]:
            if sign["sign"] == "package":
                known_pkg.setdefault((sign["value"].casefold(), sign["path"]), entry)
        for sign in sites(entry["signs"]):
            if module_declaration(sign):
                declarations_by_path.setdefault(sign["path"], []).append((entry["id"], sign))

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
                "configured_services": [],
                "frameworks": [], "libraries": [], "services": [], "tools": [], "technologies": [], "technology_evidence": {},
            }
            all_modules.append(item)
            continue
        owned = _module_files(unit, physical)
        evidence = {}
        for rel in sorted(owned & declarations_by_path.keys()):
            for ident, sign in declarations_by_path[rel]:
                if ident not in evidence:
                    evidence[ident] = {"path": rel, **({"line": sign["line"]} if sign.get("line") else {})}
        matched = [e for e in entries if e["id"] in evidence]
        frameworks = [e["id"] for e in matched if e.get("category") == "framework"]
        services = [e["id"] for e in matched if e.get("category") == "service"]
        tools = [e["id"] for e in matched if e.get("category") == "tool"]
        libraries = {}
        for eco, pkg_name, pkg_path, pkg_line, version in raw_packages:
            if pkg_path not in owned or _versions_only(pkg_path):
                continue
            key = (eco, service_registry.package_key(eco, pkg_name))
            previous = libraries.get(key)
            if previous and (eco != "pypi" or previous.get("version") or not version):
                continue
            reg_entry = known_pkg.get((pkg_name.casefold(), pkg_path))
            libraries[key] = {
                "ecosystem": eco, "name": pkg_name, "path": pkg_path, "line": pkg_line,
                **({"version": version} if version else {}),
                **({"id": reg_entry["id"], "title": reg_entry["name"]} if reg_entry else {}),
            }
        libs = sorted(libraries.values(), key=lambda x: (x["ecosystem"], x["name"].casefold()))
        item = {
            **named, "kind": unit["kind"],
            "nature": unit.get("nature", "concrete"), "provenance": unit["provenance"],
            "paths": unit["paths"], "languages": unit.get("languages", {}),
            "toolchains": unit.get("toolchains", []),
            "configured_services": [service for service in configured if service["path"] in owned],
            "frameworks": frameworks, "libraries": libs, "services": services, "tools": tools,
            "technologies": [e["id"] for e in matched], "technology_evidence": evidence,
        }
        if unit["provenance"] == "build":
            resolutions = [resolved_members[p] for p in unit.get("manifests", ()) if p in resolved_members
                           and not service_registry._is_excluded(p, left_out)]
            if resolutions:
                item["resolved_libraries"] = [row for model, i in resolutions for row in _resolved_libraries(model, i)]
        all_modules.append(item)
        if unit["provenance"] in modules.PHYSICAL:
            units.append(item)
    return {"schema": SCHEMA, "manifest": manifest.as_posix(), "root": root, "target": target,
            "inputs_digest": digest, "technologies": entries, "mentioned": mentioned, "units": units,
            "configured_services": configured, "modules": all_modules,
            "checkers": recognized["checkers"], "gaps": [*recognized["gaps"], *kept]}


def _read(manifest: Path, digest: str) -> dict | None:
    try:
        record = json.loads(path(manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if (isinstance(record, dict) and record.get("schema") == SCHEMA and record.get("inputs_digest") == digest
            and "checkers" in record and "configured_services" in record):
        return record
    return None


def recorded(manifest: Path) -> dict:
    """The record the stack step last wrote beside `manifest`, as written (`ensure` derives it, this only reads): empty
    when there is none, or not of this schema."""
    try:
        record = json.loads(path(manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"technologies": []}
    ok = isinstance(record, dict) and record.get("schema") == SCHEMA and isinstance(record.get("technologies"), list)
    return record if ok else {"technologies": []}


def externals(graph: dict, record: dict) -> list[dict]:
    """The services of others by id: the stack step's technologies (`record`) and the external modules of the module
    `graph`. A technology gives its name, kind, type and the files that declare it (`paths`); a module adds the files it
    cites, its own name (`module`, what the links call the node) and its `status`. The brief shows this list and the
    links (`flows._external_nodes`) hold it as nodes."""
    out = {found["id"]: {"id": found["id"], "name": found["name"], "kind": found["kind"],
                         "type": found["type"] or "altro", "from": ["registry"],
                         "paths": sorted({s["path"] for s in found["signs"] if s["strength"] == "declared" and s["path"]})}
           for found in record["technologies"]}
    for module in graph["modules"]:
        if module.get("location") == "external":
            ident = modules.slug(module["name"])
            cited = {str(e.get("path") if isinstance(e, dict) else e).split("#")[0] for e in module.get("evidence", [])}
            entry = out.setdefault(ident, {"id": ident, "name": module["name"], "kind": None, "type": "altro",
                                           "from": [], "paths": []})
            entry.update({"from": sorted({*entry["from"], "modules"}), "paths": sorted({*entry["paths"], *cited}),
                          "module": module["name"], "status": module.get("status")})
    return list(out.values())


def state(manifest: Path, *, facts: dict | None = None) -> str:
    """fresh, stale or missing; a read, which writes no pre-map and runs no tool: a stack step's record that is not fresh
    makes the record stale, and so, without `facts`, does a pre-map that is not fresh (a pass may be writing it)."""
    manifest = Path(manifest).resolve()
    if not path(manifest).is_file():
        return "missing"
    registry = service_registry.load()
    if stack_recognition.state(manifest, registry) != "fresh":
        return "stale"
    if facts is None:
        if premap.state(manifest)["state"] != "fresh":
            return "stale"
        facts = premap.ensure(manifest)
    digest = _inputs(manifest, registry, facts, stack_recognition.recorded(manifest))[0]
    return "fresh" if _read(manifest, digest) else "stale"


def ensure(manifest: Path, *, facts: dict | None = None) -> dict:
    """The record of `manifest`, derived and written again when it is not fresh: the stack step's record first, whose build
    tools choose the pre-map's sources, then the pre-map."""
    manifest = Path(manifest).resolve()
    registry = service_registry.load()
    stack = stack_recognition.ensure(manifest, registry)
    facts = premap.ensure(manifest) if facts is None else facts
    record = _read(manifest, _inputs(manifest, registry, facts, stack)[0])
    if record is None:
        target = path(manifest)
        confinement.reject_link_chain(target)
        record = derive(manifest, registry, facts)
        descriptor, name = tempfile.mkstemp(prefix=".technologies-", dir=target.parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(json.dumps(record, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        os.replace(name, target)
    return record
