"""Source: Daodan's module graph (`modules.py`), its build units as the pre-map names them.

Units, the workspaces that contain them and the declared edges between units (`depends_on`). A module of
several kinds in one folder (settings and build script, `package.json` beside a workspace file) is one unit per
kind the pre-map knows; a
workspace member without its own manifest is a member, not a unit; an included Gradle build is a unit, not a
member. A unit is named as its build tool names it (`_names`), and has no name where no file gives one.
Another entry refers to a unit by `references`: its name, or its root when the name cannot tell it apart. The
graph's gaps are kept. This is the one conversion of the graph: the benchmark's adapter calls `facts`, which
also gives the names of each unit's external dependencies; the pre-map takes only its structure (`run`).
"""
from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath

import modules

NAME, VERSION, RANK = "modules.py", modules.SCHEMA, "reader"
KIND = {"npm-package": "npm-package", "python-package": "python-project", "cargo-crate": "cargo-crate",
        "go-module": "go-module", "maven-module": "maven-module", "maven-aggregator": "maven-module",
        "gradle-project": "gradle-project", "gradle-build": "gradle-project", "dotnet-project": "dotnet-project",
        "cmake-project": "cmake-target", "composer-package": "composer-package", "ruby-gem": "gem",
        "ruby-bundle": "bundler-project", "dart-package": "pub-package", "swift-package": "swift-package",
        "mix-project": "mix-project", "mix-umbrella": "mix-project", "deno-package": "deno-project",
        "nx-project": "nx-project", "sbt-project": "sbt-project", "cabal-package": "cabal-package",
        "dune-project": "dune-project", "zig-package": "zig-package", "julia-package": "julia-package",
        "terraform-root": "terraform-module", "angular-project": "angular-project",
        "msbuild-project": "msbuild-project", "buf-module": "buf-module"}
ROOT_PACKAGE = {"uv-workspace": "python-project", "cargo-workspace": "cargo-crate"}  # a unit only when a file names it
WORKSPACE = {"pnpm-workspace": "pnpm", "lerna-workspace": "lerna", "npm-workspace": "npm", "go-workspace": "go",
             "melos-workspace": "melos", "stack-workspace": "stack", "dotnet-solution": "dotnet",
             "uv-workspace": "uv", "angular-workspace": "angular"}
JS_WORKSPACES = {"npm-workspace", "pnpm-workspace", "lerna-workspace"}
MANIFEST = {"npm-package": ("package.json",), "python-project": ("pyproject.toml", "setup.py", "setup.cfg"),
            "cargo-crate": ("Cargo.toml",), "go-module": ("go.mod",), "maven-module": ("pom.xml",),
            "gradle-project": ("build.gradle.kts", "build.gradle", "settings.gradle.kts", "settings.gradle"),
            "composer-package": ("composer.json",), "pub-package": ("pubspec.yaml",),
            "swift-package": ("Package.swift",), "mix-project": ("mix.exs",), "cmake-target": ("CMakeLists.txt",),
            "bundler-project": ("Gemfile",), "gem": ("Gemfile",), "deno-project": ("deno.json", "deno.jsonc"),
            "nx-project": ("project.json",), "angular-project": ("angular.json",)}


def _manifest(module: dict, kind: str) -> str | None:
    for name in MANIFEST.get(kind, ()):
        for manifest in module["manifests"]:
            if PurePosixPath(manifest).name == name:
                return manifest
    return module["manifests"][0] if module["manifests"] else None


def _root(module: dict) -> str:
    return module["members"][0]["path"]


def _included(module: dict) -> bool:
    return "gradle-build" in module["kind"].split("+")


def _names(build: list[dict], holder: dict) -> dict:
    """A unit's name as its build tool writes it: Maven `groupId:artifactId`, the alias the pom gives; Gradle the
    project path, `:` for the root of a build, the build path for an included build and `buildSrc`; None when
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
    if any(k in JS_WORKSPACES for k in kinds) and any(PurePosixPath(m).name == "package.json"
                                                      for m in module["manifests"]):
        found = ["npm-package"] + [k for k in found if k != "npm-package"]
    if "angular-project" in kinds and "angular-workspace" not in kinds:  # a library's package.json is its manifest
        found = [k for k in found if k != "npm-package"]
    return list(dict.fromkeys(found))


def _read(graph: dict):
    build = [m for m in graph["modules"] if m["provenance"] == "build"]
    by_id = {m["id"]: m for m in build}
    edges = [e for e in graph.get("edges") or [] if e["source"] in by_id and e["target"] in by_id]
    names = _names(build, {e["target"]: by_id[e["source"]] for e in edges if e["kind"] == "contains"})
    kinds_of = {m["id"]: _unit_kinds(m) for m in build}
    same_name = Counter((names[i], kind) for i, kinds in kinds_of.items() for kind in kinds)
    same_root = Counter((_root(by_id[i]), kind) for i, kinds in kinds_of.items() for kind in kinds)
    # How another entry refers to a unit: its name, or its root when the name is None or a unit of the same kind
    # has it too (three separate Gradle builds are all ":") and the root tells them apart.
    ref = {i: _root(by_id[i]) if n is None or any(same_name[n, k] > 1 and same_root[_root(by_id[i]), k] == 1
                                                   for k in kinds_of[i]) else n for i, n in names.items()}
    return build, by_id, edges, names, kinds_of, ref


def references(graph: dict) -> dict:
    """Module id -> how an edge or a gap names that unit."""
    return _read(graph)[5]


def facts(graph: dict) -> dict:
    build, by_id, edges, names, kinds_of, ref = _read(graph)
    units, dependencies = [], []
    for module in build:
        found = [{"name": names[module["id"]], "kind": kind, "root": _root(module), "manifest": _manifest(module, kind),
                  "depends_on": sorted({ref[e["target"]] for e in edges if e["kind"] == "declares"
                                        and e["source"] == module["id"]})} for kind in kinds_of[module["id"]]]
        units += found
        if found:  # once per module; the graph knows the names, the file only when the module has one manifest
            declared_in = module["manifests"][0] if len(module["manifests"]) == 1 else None
            dependencies += [{"unit": ref[module["id"]], "name": name,
                              **({"declared_in": declared_in} if declared_in else {})}
                             for name in module.get("external") or []]
    workspaces: dict[str, dict] = {}
    for edge in edges:
        if edge["kind"] != "contains" or _included(by_id[edge["target"]]):  # an included build is not a member
            continue
        parent = by_id[edge["source"]]
        kinds = parent["kind"].split("+")
        tool = next((WORKSPACE[k] for k in WORKSPACE if k in kinds),
                    parent["ecosystems"][0] if parent["ecosystems"] else "")
        entry = workspaces.setdefault(parent["id"], {"tool": tool, "root": _root(parent), "members": []})
        entry["members"].append(_root(by_id[edge["target"]]))
    return {"units": units, "workspace": list(workspaces.values()), "dependencies": dependencies}


def run(context) -> dict:
    graph = context.graph
    ref = references(graph)
    gaps = [dict(gap) for gap in graph.get("gaps") or []]
    gaps += [{**gap, "unit": ref[module["id"]]} for module in graph["modules"] if module["provenance"] == "build"
             for gap in module.get("gaps") or []]
    found = facts(graph)
    return {"facts": {"units": found["units"], "workspace": found["workspace"]}, "gaps": gaps}
