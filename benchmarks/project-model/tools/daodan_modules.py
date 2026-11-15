"""Baseline: Daodan's own module reader (`modules.py`, provenance `build`), read as it is.

`snapshot.py write <fixture> --no-engine --no-index` builds the snapshot and `modules.json` beside it, as the
plugin does; the build modules are converted to the shared shape. modules.py gives unit roots, names, the
manifests, workspace registrations, declared edges between units and the names (no versions, no scope) of
external dependencies; it reads no toolchain, no source root and no indexer configuration. The conversion
writes each name as the schema does (`_names`) and states nothing the graph does not hold.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path, PurePosixPath

import native_common as common

VERSION = "modules.py of the checkout (daodan/module-graph/v1)"
COMMAND = "snapshot.py write <fixture> --out <work>/manifest.sqlite --no-engine --no-index; modules.json"
SCRIPTS = next((p / "plugins/codebase-map/skills/map/scripts" for p in Path(__file__).resolve().parents
                if (p / "plugins/codebase-map/skills/map/scripts").is_dir()), Path("/daodan/map/scripts"))
KIND = {"npm-package": "npm-package", "python-package": "python-project", "cargo-crate": "cargo-crate",
        "go-module": "go-module", "maven-module": "maven-module", "gradle-project": "gradle-project",
        "gradle-build": "gradle-project", "dotnet-project": "dotnet-project", "cmake-project": "cmake-target",
        "composer-package": "composer-package", "ruby-gem": "gem", "ruby-bundle": "bundler-project", "dart-package": "pub-package",
        "swift-package": "swift-package", "mix-project": "mix-project", "deno-package": "deno-project",
        "nx-project": "nx-project", "sbt-project": "sbt-project", "cabal-package": "cabal-package",
        "dune-project": "dune-project", "zig-package": "zig-package", "julia-package": "julia-package",
        "terraform-root": "terraform-module", "maven-aggregator": "maven-module", "mix-umbrella": "mix-project",
        "angular-project": "angular-project", "msbuild-project": "msbuild-project", "buf-module": "buf-module"}
ROOT_PACKAGE = {"uv-workspace": "python-project", "cargo-workspace": "cargo-crate"}  # a unit only when a file names it
WORKSPACE = {"pnpm-workspace": "pnpm", "lerna-workspace": "lerna", "npm-workspace": "npm", "go-workspace": "go",
             "melos-workspace": "melos", "stack-workspace": "stack", "dotnet-solution": "dotnet",
             "uv-workspace": "uv", "angular-workspace": "angular"}
JS_WORKSPACES = {"npm-workspace", "pnpm-workspace", "lerna-workspace"}
MANIFEST = {"npm": "package.json", "python": ("pyproject.toml", "setup.py", "setup.cfg"), "cargo": "Cargo.toml",
            "go": "go.mod", "maven": "pom.xml", "gradle": ("build.gradle.kts", "build.gradle", "settings.gradle.kts",
                                                         "settings.gradle"),
            "composer": "composer.json", "pub": "pubspec.yaml", "swiftpm": "Package.swift", "mix": "mix.exs",
            "cmake": "CMakeLists.txt", "bundler": "Gemfile", "deno": ("deno.json", "deno.jsonc"), "nx": "project.json",
            "angular": "angular.json"}
ECOSYSTEM = {"npm-package": "npm", "python-project": "python", "cargo-crate": "cargo",
             "go-module": "go", "maven-module": "maven", "gradle-project": "gradle", "composer-package": "composer",
             "pub-package": "pub", "swift-package": "swiftpm", "mix-project": "mix", "cmake-target": "cmake", "bundler-project": "bundler",
             "gem": "bundler", "deno-project": "deno", "nx-project": "nx", "angular-project": "angular"}
LAST: dict = {}


def _manifest(module: dict, ecosystem: str) -> str | None:
    wanted = MANIFEST.get(ecosystem, ())
    wanted = (wanted,) if isinstance(wanted, str) else wanted
    for name in wanted:
        for manifest in module["manifests"]:
            if PurePosixPath(manifest).name == name:
                return manifest
    return module["manifests"][0] if module["manifests"] else None


def _root(module: dict) -> str:
    return module["members"][0]["path"]


def _included(module: dict) -> bool:
    return "gradle-build" in module["kind"].split("+")


def _names(build: list[dict], holder: dict) -> dict:
    """A unit's name as the schema writes it: Maven `groupId:artifactId`, the alias the pom gives; Gradle the
    project path, `:` for the root of a build, the build path for an included build and `buildSrc`; null when
    no file names the unit."""
    names = {}
    for module in build:
        name = module["name"] if module.get("named", True) else None
        if "maven" in module["ecosystems"]:
            name = next((alias for alias in module["aliases"] if ":" in alias), name)
        elif "gradle" in module["ecosystems"]:
            parent = holder.get(module["id"])
            if parent is None:
                name = ":buildSrc" if PurePosixPath(_root(module)).name == "buildSrc" else ":"
            elif _included(module):
                name = ":" + module["name"]
            else:
                inside = _root(module) if _root(parent) == "." else _root(module)[len(_root(parent)) + 1:]
                name = ":" + inside.replace("/", ":")
        names[module["id"]] = name
    return names


def _unit_kinds(module: dict) -> list[str]:
    kinds = module["kind"].split("+")
    found = [KIND[k] for k in kinds if k in KIND]
    if module.get("named", True):
        found += [ROOT_PACKAGE[k] for k in kinds if k in ROOT_PACKAGE]
    if any(k in JS_WORKSPACES for k in kinds) and any(PurePosixPath(m).name == "package.json" for m in module["manifests"]):
        found = ["npm-package"] + [k for k in found if k != "npm-package"]
    if "angular-project" in kinds and "angular-workspace" not in kinds:  # a library's package.json is its manifest
        found = [k for k in found if k != "npm-package"]
    return list(dict.fromkeys(found))


def convert(graph: dict) -> dict:
    build = [m for m in graph["modules"] if m["provenance"] == "build"]
    by_id = {m["id"]: m for m in build}
    edges = [e for e in graph.get("edges") or [] if e["source"] in by_id and e["target"] in by_id]
    names = _names(build, {e["target"]: by_id[e["source"]] for e in edges if e["kind"] == "contains"})
    kinds_of = {m["id"]: _unit_kinds(m) for m in build}
    same_name = Counter((names[i], kind) for i, kinds in kinds_of.items() for kind in kinds)
    same_root = Counter((_root(by_id[i]), kind) for i, kinds in kinds_of.items() for kind in kinds)
    # how another entry refers to a unit: its name, or its root when the name is null or a unit of the same kind
    # has it too (three separate Gradle builds are all `:`) and the root tells them apart
    ref = {i: _root(by_id[i]) if n is None or any(same_name[n, k] > 1 and same_root[_root(by_id[i]), k] == 1
                                                   for k in kinds_of[i]) else n for i, n in names.items()}
    units, dependencies = [], []
    for module in build:
        found = [{"name": names[module["id"]], "kind": kind, "root": _root(module),
                  "manifest": _manifest(module, ECOSYSTEM.get(kind, "")),
                  "depends_on": sorted({ref[e["target"]] for e in edges if e["kind"] == "declares"
                                        and e["source"] == module["id"]})} for kind in kinds_of[module["id"]]]
        units += found
        if found:  # once per module, in the manifest that declares them: angular.json declares none
            declared_in = next((u["manifest"] for u in found if u["kind"] != "angular-project"), _manifest(module, "npm"))
            dependencies += [{"unit": ref[module["id"]], "name": name, "declared_in": declared_in}
                             for name in module.get("external") or []]
    workspaces = {}
    for edge in edges:
        if edge["kind"] != "contains" or _included(by_id[edge["target"]]):  # an included build is not a member
            continue
        parent = by_id[edge["source"]]
        kinds = parent["kind"].split("+")
        tool = next((WORKSPACE[k] for k in WORKSPACE if k in kinds), parent["ecosystems"][0] if parent["ecosystems"] else "")
        entry = workspaces.setdefault(parent["id"], {"tool": tool, "root": _root(parent), "members": []})
        entry["members"].append(_root(by_id[edge["target"]]))
    ws = list(workspaces.values())
    return {"units": units, "workspace": ws[0] if len(ws) == 1 else (ws or None), "dependencies": dependencies}


def run(fixture_dir, work_dir) -> dict:
    work = Path(work_dir)
    manifest = work / "daodan" / "manifest.sqlite"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    done = common.run([sys.executable, "-I", str(SCRIPTS / "snapshot.py"), "write", str(fixture_dir), "--out",
                       str(manifest), "--no-engine", "--no-index"], SCRIPTS, name="snapshot.py write (modules.py)")
    graph_file = manifest.with_name("modules.json")
    LAST.clear()
    LAST.update(rc=done.returncode, stderr=done.stderr[-1500:])
    if not graph_file.is_file():
        raise RuntimeError(f"snapshot.py write exit {done.returncode}: {done.stderr[-600:]}")
    graph = json.loads(graph_file.read_text(encoding="utf-8"))
    LAST["gaps"] = graph.get("gaps", [])[:20]
    return convert(graph)
