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
PROVENANCES = ("build", "declared", "proposed", "virtual")
PHYSICAL = ("build", "virtual")
NATURES = ("concrete", "logical", "virtual")
STATUSES = ("confirmed", "inferred", "incomplete")
MAX_EDGE_EVIDENCE = 20
VIRTUAL_BUILD_KINDS = frozenset({"go-workspace", "dotnet-solution", "stack-workspace", "pnpm-workspace",
                                 "lerna-workspace", "melos-workspace", "angular-workspace", "workspace-member",
                                 "gradle-build"})
WORKSPACE_PACKAGE_KINDS = frozenset({"cargo-workspace", "uv-workspace", "npm-workspace", "deno-workspace",
                                     "dart-workspace"})
ECOSYSTEM_TOOLS: dict[str, tuple[str, ...]] = {
    "npm": ("npm", "node"), "pnpm": ("pnpm", "node"), "lerna": ("npm", "node"), "nx": ("nx", "node"),
    "angular": ("npm", "node"), "deno": ("deno",), "python": ("python",), "cargo": ("cargo", "rust"),
    "go": ("go",), "maven": ("maven", "java"), "gradle": ("gradle", "java"), "sbt": ("sbt", "scala", "java"),
    "dotnet": ("dotnet",), "msbuild": ("msbuild",), "composer": ("composer", "php"),
    "bundler": ("bundler", "ruby"), "rubygems": ("rubygems", "ruby"), "pub": ("pub", "dart"),
    "melos": ("melos", "dart"), "swiftpm": ("swift",), "mix": ("mix", "elixir"), "cmake": ("cmake",),
    "meson": ("meson",), "bazel": ("bazel",), "make": ("make",), "autotools": ("autotools",),
    "cabal": ("cabal", "ghc"), "stack": ("stack", "ghc"), "terraform": ("terraform",), "zig": ("zig",),
    "julia": ("julia",), "dune": ("dune", "ocaml"), "buf": ("buf",),
}
JVM_TOOLS = ("java", "kotlin", "scala", "gradle", "maven", "android-sdk", "android-build-tools")
INHERITED_TOOLS: dict[str, tuple[str, ...]] = {  # per family, the other tools a module takes from an enclosing folder
    "gradle": JVM_TOOLS, "maven": JVM_TOOLS, "dotnet": ("dotnet", "dotnet-target", "c#"),
    "npm": ("node", "npm", "pnpm", "yarn", "bun", "typescript"), "python": ("uv",),
}
LANGUAGE_TOOLS: dict[str, str] = {
    "python": "python", "javascript": "node", "typescript": "typescript", "tsx": "typescript", "jsx": "node",
    "rust": "rust", "go": "go", "java": "java", "kotlin": "kotlin", "scala": "scala", "csharp": "c#",
    "c": "c", "cpp": "c++", "ruby": "ruby", "php": "php", "swift": "swift", "dart": "dart", "elixir": "elixir",
}
PREMAP_KIND_ECOSYSTEM: dict[str, str] = {
    "npm-package": "npm", "deno-project": "deno", "angular-project": "angular", "nx-project": "nx",
    "python-project": "python", "cargo-crate": "cargo", "go-module": "go", "maven-module": "maven",
    "gradle-project": "gradle", "sbt-project": "sbt", "dotnet-project": "dotnet", "msbuild-project": "msbuild",
    "cmake-target": "cmake", "meson-target": "meson", "bazel-target": "bazel", "bazel-module": "bazel",
    "make-target": "make", "autotools-project": "autotools", "composer-package": "composer", "gem": "rubygems",
    "bundler-project": "bundler", "pub-package": "pub", "swift-package": "swiftpm", "mix-project": "mix",
    "cabal-package": "cabal", "dune-project": "dune", "zig-package": "zig", "julia-package": "julia",
    "terraform-module": "terraform", "buf-module": "buf",
}


def _is_runtime_file(rel: str) -> bool:
    name = PurePosixPath(rel).name
    return (name == "Dockerfile" or name.endswith(".Dockerfile")
            or (name.startswith(("docker-compose", "compose")) and name.endswith((".yml", ".yaml")))
            or (name.startswith("requirements") and name.endswith(".txt")))


def _build_nature(kinds: list[str], named: bool) -> str:
    kind_set = set(kinds)
    if kind_set <= VIRTUAL_BUILD_KINDS:
        return "virtual"
    if not named and kind_set <= (VIRTUAL_BUILD_KINDS | WORKSPACE_PACKAGE_KINDS):
        return "virtual"
    return "concrete"


def _module_languages(headers: dict, files: list[str], excluded_paths: list[str] = (),
                      manifests: set[str] = frozenset()) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rel in files:
        if rel in manifests or any(_inside(rel, ex) for ex in excluded_paths):
            continue
        lang = (headers.get(rel) or {}).get("language")
        if lang:
            key = "html" if lang == "markup" else lang
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _baseline_tools(module: dict) -> list[tuple[str, str | None]]:
    """(tool, default_declared_in) required by a module's ecosystems, languages and runtime files."""
    if module.get("location") == "external":
        return []
    manifest = module["manifests"][0] if module.get("manifests") else (module["files"][0] if module.get("files") else None)
    found: dict[str, str | None] = {}
    for eco in module.get("ecosystems") or ():
        for tool in ECOSYSTEM_TOOLS.get(eco, ()):
            found.setdefault(tool, manifest)
    for lang in module.get("languages") or {}:
        if lang in LANGUAGE_TOOLS:
            found.setdefault(LANGUAGE_TOOLS[lang], manifest)
    for rel in module.get("files") or ():
        name = PurePosixPath(rel).name
        if name == "Dockerfile" or name.endswith(".Dockerfile") or (
                name.startswith(("docker-compose", "compose")) and name.endswith((".yml", ".yaml"))):
            found.setdefault("docker", rel)
    return list(found.items())


def attach_toolchains(modules: list[dict], stated: list[dict] = ()) -> None:
    """Resolve and attach `toolchains` to each module, inheriting from enclosing build/workspace roots."""
    physical_roots = sorted({m["members"][0]["path"] for m in modules if m["provenance"] in PHYSICAL and m["members"]},
                            key=lambda d: (-1 if d == "." else len(d)), reverse=True)

    def owner_dir(rel_file: str) -> str:
        if "/wrapper/" in f"/{rel_file}":  # gradle/wrapper/... or .mvn/wrapper/... speaks for the root above it
            prefix = rel_file.split("gradle/wrapper/", 1)[0] if "gradle/wrapper/" in rel_file else rel_file.split(".mvn/wrapper/", 1)[0]
            return prefix.rstrip("/") or "."
        return next((root for root in physical_roots if _inside(rel_file, root)), _dirname(rel_file))

    by_dir: dict[str, dict[str, dict]] = {}
    by_file: dict[str, list[dict]] = {}
    for item in stated:
        tool = item.get("tool")
        declared_in = item.get("declared_in")
        if not tool:
            continue
        entry = {"tool": tool, "version": item.get("version"), "declared_in": declared_in}
        rel_file = str(declared_in or "").split("#", 1)[0]
        if rel_file:
            by_file.setdefault(rel_file, []).append(entry)
            folder = owner_dir(rel_file)
            by_dir.setdefault(folder, {}).setdefault(tool, entry)

    for module in modules:
        if module.get("location") == "external":
            module["toolchains"] = []
            continue
        baseline = dict(_baseline_tools(module))
        chosen: dict[str, dict] = {}
        if module["provenance"] in PHYSICAL and module.get("members"):
            mod_dir = module["members"][0]["path"]
            ancestors = sorted([d for d in by_dir if _inside(mod_dir, d)],
                               key=lambda d: (-1 if d == "." else len(d)), reverse=True)
            relevant = set(baseline) | {t for eco in module.get("ecosystems", ()) for t in
                                        ECOSYSTEM_TOOLS.get(eco, ()) + INHERITED_TOOLS.get(_family(eco), ())}
            for anc in ancestors:
                for tool, entry in by_dir[anc].items():
                    if anc == mod_dir or tool in relevant or not relevant:
                        chosen.setdefault(tool, dict(entry))
        else:
            for rel in module.get("files") or ():
                for entry in by_file.get(rel, ()):
                    chosen.setdefault(entry["tool"], dict(entry))
            owners = [m for m in modules if m["provenance"] in PHYSICAL
                      and any(rel in m.get("files", ()) for rel in module.get("files", ()))]
            for owner in owners:
                for entry in owner.get("toolchains") or ():
                    if entry["tool"] in baseline:
                        chosen.setdefault(entry["tool"], dict(entry))
        for tool, default_decl in baseline.items():
            chosen.setdefault(tool, {"tool": tool, "version": None, "declared_in": default_decl})
        module["toolchains"] = [chosen[k] for k in sorted(chosen)]


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
                "dependencies": set(unit["dependencies"]), "versions": {unit["path"]: dict(unit["versions"])},
                "path_dependencies": list(unit["path_dependencies"]),
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
        merged["versions"].setdefault(unit["path"], {}).update(unit["versions"])
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
                        "evidence": [], "dependencies": set(), "versions": {}, "path_dependencies": [], "patterns": [],
                        "registered_by": []}
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
    kinds = sorted(set(merged["kinds"]))
    named = merged["name"] is not None
    return {
        "id": "", "name": name, "named": named, "nature": _build_nature(kinds, named),
        "aliases": sorted(dict.fromkeys(merged["aliases"])), "provenance": "build",
        "kind": kinds[0] if len(kinds) == 1 else "+".join(kinds),
        "location": "internal", "ecosystems": sorted(set(merged["ecosystems"])), "description": merged["description"],
        "responsibility": "", "members": [{"id": merged["directory"], "kind": "directory",
                                           "path": merged["directory"], "resolved": True}],
        "excluded": excluded, "manifests": sorted(merged["manifests"]),
        "registered_by": sorted({key[0] for key, _ in merged["registered_by"]}), "registrations": merged["registered_by"],
        "evidence": merged["evidence"], "dependencies": sorted(merged["dependencies"]),
        "versions": merged["versions"],  # manifest -> dependency -> its version requirement: the pre-map's, not modules.json's
        "path_dependencies": merged["path_dependencies"], "conflicts": [], "gaps": [], "status": "confirmed",
    }


def _virtual_source_tree(inventory: _Inventory, build_modules: list[dict]) -> list[dict]:
    """An implicit `source-tree` virtual module at `.` when source or runtime files lie outside all build modules."""
    build_dirs = sorted({m["members"][0]["path"] for m in build_modules if m["members"]})
    if "." in build_dirs:
        return []
    excluded = [d for d in build_dirs if not any(_inside(d, other) for other in build_dirs if other != d)]
    read_manifests = {mf for m in build_modules for mf in m["manifests"]} | {DECLARED_FILE}
    uncovered = [rel for rel in inventory.files
                 if rel not in read_manifests and not any(_inside(rel, d) for d in excluded)]
    meaningful = [rel for rel in uncovered if (inventory.headers.get(rel) or {}).get("language") or _is_runtime_file(rel)]
    if not meaningful:
        return []
    root_name = PurePosixPath(inventory.root).name or "root"
    first = meaningful[0]
    return [{
        "id": "", "name": root_name, "named": False, "nature": "virtual", "aliases": [],
        "provenance": "virtual", "kind": "source-tree", "location": "internal", "ecosystems": [],
        "description": None, "responsibility": "",
        "members": [{"id": ".", "kind": "directory", "path": ".", "resolved": True}],
        "excluded": excluded, "manifests": [], "registered_by": [], "registrations": [],
        "evidence": [{"path": first, "line": 1}], "dependencies": [], "external": [],
        "path_dependencies": [], "conflicts": [], "gaps": [], "status": "confirmed",
    }]


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
        "id": "", "name": record["name"], "named": True, "nature": "logical", "aliases": [],
        "provenance": provenance, "kind": record["kind"],
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
        anchor = module["members"][0]["path"] if module["provenance"] in PHYSICAL else module["provenance"]
        identity = key if counts[slug(module["name"])] == 1 and key not in taken else f"{key}@{anchor}"
        while identity in taken:
            identity += "+"
        module["id"] = identity
        taken.add(identity)


def _measure_modules(inventory: _Inventory, modules: list[dict], excluded_paths: list[str] = ()) -> None:
    """Shared members, files, review paths, languages, coverage and the members digest of every module."""
    claims: dict[str, list[str]] = {}
    for module in modules:
        if module["provenance"] not in PHYSICAL:
            for member in module["members"]:
                if member["resolved"]:
                    claims.setdefault(member["id"], []).append(module["id"])
    for module in modules:
        module["conflicts"] = []
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
        if module["provenance"] == "virtual":
            read_manifests = {mf for m in modules if m["provenance"] == "build" for mf in m["manifests"]} | {DECLARED_FILE}
            files -= read_manifests
        module["files"] = sorted(files)
        module["paths"] = (sorted(m["path"] for m in module["members"]) if module["provenance"] in PHYSICAL
                           else _review_paths(inventory, files))
        module["languages"] = _module_languages(inventory.headers, module["files"], excluded_paths,
                                                set(module.get("manifests") or ()))
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
                    if module["provenance"] in PHYSICAL:
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
        # Physical units and responsibility modules are two layers: a build/virtual unit
        # holds a module's files (`owned_by` in the query), it does not call it.
        # An external module sits outside both layers, so `uses` reaches it from either.
        if kind != "uses" and (self.by_id[source]["provenance"] in PHYSICAL) != (self.by_id[target]["provenance"] in PHYSICAL):
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
    if symbol_owner or any(m["provenance"] not in PHYSICAL for m in modules):
        try:
            for call in _call_edges(store, symbol_owner, file_owner):
                edges.add("calls", call["source"], call["target"], edges.status(call["source"], call["target"]),
                          {"path": call["path"], "line": call["line"], "caller": call["caller"], "callee": call["callee"]})
        except ValueError as error:
            gaps.append({"kind": "calls_unavailable", "detail": str(error)})
    _uses_edges(modules, edges)
    return edges.listed()


def _coverage_summary(inventory: _Inventory, modules: list[dict], edge_list: list[dict]) -> dict:
    return {
        "files": len(inventory.files), "ecosystems": ECOSYSTEMS,
        "modules": {p: sum(1 for m in modules if m["provenance"] == p) for p in PROVENANCES},
        "natures": {n: sum(1 for m in modules if m["nature"] == n) for n in NATURES},
        "statuses": {s: sum(1 for m in modules if m["status"] == s) for s in STATUSES},
        "edges": {k: sum(1 for e in edge_list if e["kind"] == k) for k in ("declares", "contains", "imports", "calls", "uses")},
    }


def _graph(store, inventory: _Inventory, modules: list[dict], edge_list: list[dict], gaps: list[dict]) -> dict:
    return {
        "schema": SCHEMA,
        "binding": {"manifest": str(Path(store.path).resolve()), "logical_digest": logical_digest(store),
                    "root": store["root"], "target": store["target"], "git": store.get("git")},
        "modules": modules,
        "edges": edge_list,
        "coverage": _coverage_summary(inventory, modules, edge_list),
        "gaps": gaps,
        "notes": [
            "Build units come from manifests and model tools; virtual modules cover workspaces and source trees outside "
            "manifests; declared modules come from codebase-modules.json; proposed modules stay inferred until declared.",
            "Static edges prove no runtime behavior; a missing call edge proves no independence (lexical resolver).",
        ],
    }


def _build_units(inventory: _Inventory):
    """The manifests' units merged per directory, the workspaces that register them, one build module each."""
    units, gaps = _read_units(inventory)
    by_directory = _merge_units(units)
    _register_members(inventory, by_directory, gaps)
    return units, by_directory, [_build_module(inventory, merged, by_directory) for merged in by_directory.values()], gaps


def build_graph(inventory: _Inventory) -> dict:
    """The build modules with their `declares` and `contains` edges and their gaps, `ownership_ambiguous` among
    them, in memory: what the pre-map reads (`premap.module_graph`), never `modules.json`, which
    `modules.sync_with_premap` writes from the pre-map."""
    units, by_directory, modules, gaps = _build_units(inventory)
    _assign_identities(modules)
    by_id = {m["id"]: m for m in modules}
    _ownership(inventory, modules, by_id, gaps)
    edges = _Edges(by_id)
    _build_edges(inventory, modules, units, {key: m["id"] for key, m in zip(by_directory, modules)}, edges)
    return {"modules": modules, "edges": edges.listed(), "gaps": gaps}


def derive(store, *, ledger: list[dict] | None = None) -> dict:
    """Derive the module graph of a snapshot; deterministic for the same inputs."""
    inventory = _Inventory(store)
    units, by_directory, build_modules, gaps = _build_units(inventory)
    modules = [*build_modules, *_virtual_source_tree(inventory, build_modules),
               *_declared_modules(inventory, store, ledger, gaps)]
    _assign_identities(modules)
    by_id = {m["id"]: m for m in modules}
    _measure_modules(inventory, modules)
    attach_toolchains(modules)
    file_owner, symbol_owner = _ownership(inventory, modules, by_id, gaps)
    build_by_key = {key: module["id"] for key, module in zip(by_directory, build_modules)}
    edge_list = _module_edges(store, inventory, modules, units, build_by_key, file_owner, symbol_owner, by_id, gaps)
    modules.sort(key=lambda m: m["id"])
    for module in modules:
        module.pop("path_dependencies", None)
        module.pop("versions", None)
    return _graph(store, inventory, modules, edge_list, gaps)


def enrich_with_premap(store, graph: dict, premap_record: dict) -> dict:
    """Align a derived module graph with pre-map model units, excluded paths and inherited toolchains."""
    inventory = _Inventory(store)
    modules = [dict(m) for m in graph["modules"]]
    excluded_paths = [item["path"].rstrip("/") for item in premap_record.get("excluded") or [] if item.get("path")]
    by_root_family: dict[tuple[str, str], dict] = {}
    by_root_any: dict[str, dict] = {}
    for module in modules:
        if module["provenance"] == "build" and module.get("members"):
            root = module["members"][0]["path"]
            by_root_any.setdefault(root, module)
            for eco in module.get("ecosystems") or ():
                by_root_family.setdefault((root, _family(eco)), module)

    unit_to_id: dict[str, str] = {}
    added_dirs: set[str] = set()
    taken_ids = {m["id"] for m in modules}
    for unit in premap_record.get("units") or []:
        root = unit.get("root") or "."
        eco = PREMAP_KIND_ECOSYSTEM.get(unit.get("kind") or "", "")
        fam = _family(eco) if eco else ""
        matched = by_root_family.get((root, fam)) or (by_root_any.get(root) if not fam else None)
        uname = unit.get("name")
        if matched is not None:
            if uname and uname != matched["name"] and uname not in matched["aliases"]:
                matched["aliases"] = sorted(dict.fromkeys([*matched["aliases"], uname]))
            if matched["nature"] == "virtual" and eco:
                matched["nature"] = "concrete"
            if uname:
                unit_to_id[uname] = matched["id"]
            unit_to_id.setdefault(root, matched["id"])
            continue
        if not eco or root not in inventory.directories:
            continue
        unit_sources = {s.split("@", 1)[0] for s in unit.get("sources") or ()}
        if unit_sources and unit_sources <= {"requirements"}:
            continue
        raw_name = (str(uname).lstrip(":").replace(":", "-") if uname else "") or PurePosixPath(root).name or PurePosixPath(inventory.root).name
        manifest_rel = unit.get("manifest")
        ev_file = manifest_rel if manifest_rel in inventory.headers else next(iter(inventory.files_under([root])), None)
        ident = slug(raw_name) or "unnamed"
        if ident in taken_ids:
            ident = f"{ident}@{root}"
        while ident in taken_ids:
            ident += "+"
        taken_ids.add(ident)
        created = {
            "id": ident, "name": raw_name, "named": bool(uname), "nature": "concrete",
            "aliases": sorted({a for a in (uname, PurePosixPath(root).name) if a and a != raw_name}),
            "provenance": "build", "kind": unit["kind"], "location": "internal", "ecosystems": [eco],
            "description": None, "responsibility": "",
            "members": [{"id": root, "kind": "directory", "path": root, "resolved": True}],
            "excluded": [], "manifests": [manifest_rel] if manifest_rel in inventory.headers else [],
            "registered_by": [], "evidence": [{"path": ev_file, "line": 1}] if ev_file else [],
            "dependencies": [], "external": [], "conflicts": [], "gaps": [], "status": "confirmed",
        }
        modules.append(created)
        by_root_family[(root, fam)] = created
        by_root_any.setdefault(root, created)
        added_dirs.add(root)
        if uname:
            unit_to_id[uname] = ident
        unit_to_id.setdefault(root, ident)

    if added_dirs:
        build_dirs = sorted({m["members"][0]["path"] for m in modules if m["provenance"] == "build" and m.get("members")})
        for module in modules:
            if module["provenance"] in PHYSICAL and module.get("members"):
                here = module["members"][0]["path"]
                nested = sorted(d for d in build_dirs if d != here and _inside(d, here))
                module["excluded"] = [d for d in nested if not any(_inside(d, other) for other in nested if other != d)]

    _measure_modules(inventory, modules, excluded_paths)
    modules = [m for m in modules if not (
        m["provenance"] == "virtual"
        and not any((inventory.headers.get(f) or {}).get("language") or _is_runtime_file(f) for f in m["files"]))]
    attach_toolchains(modules, premap_record.get("toolchains") or [])

    by_id = {m["id"]: m for m in modules}
    edge_map = {e["id"]: dict(e) for e in graph["edges"] if e["source"] in by_id and e["target"] in by_id}
    for unit in premap_record.get("units") or []:
        src_id = unit_to_id.get(unit.get("name") or "") or unit_to_id.get(unit.get("root") or ".")
        if not src_id or src_id not in by_id:
            continue
        src_mod = by_id[src_id]
        ev_path = (src_mod["manifests"][0] if src_mod["manifests"]
                   else (src_mod["files"][0] if src_mod["files"] else None))
        for dep_ref in unit.get("depends_on") or ():
            dst_id = unit_to_id.get(dep_ref)
            if not dst_id or dst_id == src_id or dst_id not in by_id or not ev_path:
                continue
            key = f"declares:{src_id}->{dst_id}"
            if key not in edge_map:
                edge_map[key] = {"id": key, "kind": "declares", "source": src_id, "target": dst_id,
                                 "status": "confirmed", "evidence": [{"path": ev_path, "line": None}],
                                 "evidence_total": 1}

    modules.sort(key=lambda m: m["id"])
    edge_list = [edge_map[k] for k in sorted(edge_map)]
    updated = {**graph, "modules": modules, "edges": edge_list,
               "coverage": _coverage_summary(inventory, modules, edge_list)}
    if premap_record.get("inputs_digest"):
        updated["premap_digest"] = premap_record["inputs_digest"]
    return updated
