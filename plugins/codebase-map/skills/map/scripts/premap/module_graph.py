"""Source: Daodan's module graph (`modules.py`), its build units as the pre-map names them.

Units, the workspaces that contain them, the declared edges between units (`depends_on`) and the names of
their external dependencies, each declared in the unit's manifest. A module of several kinds in one folder
(settings and build script, `package.json` beside a workspace file) is one unit per kind the pre-map knows;
a Maven aggregator is a `maven-module` too, and a Maven unit is named `groupId:artifactId`, the alias the pom
gives; a workspace member without its own manifest is a member, not a unit. The graph's gaps are kept.
"""
from __future__ import annotations

from pathlib import PurePosixPath

import modules

NAME, VERSION, RANK = "modules.py", modules.SCHEMA, "reader"
KIND = {"npm-package": "npm-package", "python-package": "python-project", "cargo-crate": "cargo-crate",
        "go-module": "go-module", "maven-module": "maven-module", "maven-aggregator": "maven-module",
        "gradle-project": "gradle-project",
        "gradle-build": "gradle-project", "dotnet-project": "dotnet-project", "cmake-project": "cmake-target",
        "composer-package": "composer-package", "ruby-gem": "gem", "ruby-bundle": "bundler-project",
        "dart-package": "pub-package", "swift-package": "swift-package", "mix-project": "mix-project",
        "deno-package": "deno-project", "nx-project": "nx-project", "sbt-project": "sbt-project",
        "cabal-package": "cabal-package", "dune-project": "dune-project", "zig-package": "zig-package",
        "julia-package": "julia-package", "terraform-root": "terraform-module"}
WORKSPACE = {"npm-workspace": "npm", "pnpm-workspace": "pnpm", "lerna-workspace": "lerna", "go-workspace": "go",
             "melos-workspace": "melos", "stack-workspace": "stack", "dotnet-solution": "dotnet",
             "uv-workspace": "uv"}
JS_WORKSPACES = {"npm-workspace", "pnpm-workspace", "lerna-workspace"}
MANIFEST = {"npm-package": ("package.json",), "python-project": ("pyproject.toml", "setup.py", "setup.cfg"),
            "cargo-crate": ("Cargo.toml",), "go-module": ("go.mod",), "maven-module": ("pom.xml",),
            "gradle-project": ("build.gradle.kts", "build.gradle", "settings.gradle.kts", "settings.gradle"),
            "composer-package": ("composer.json",), "pub-package": ("pubspec.yaml",),
            "swift-package": ("Package.swift",), "mix-project": ("mix.exs",), "cmake-target": ("CMakeLists.txt",),
            "bundler-project": ("Gemfile",), "gem": ("Gemfile",), "deno-project": ("deno.json", "deno.jsonc"),
            "nx-project": ("project.json",)}


def _manifest(module: dict, kind: str) -> str | None:
    for name in MANIFEST.get(kind, ()):
        for manifest in module["manifests"]:
            if PurePosixPath(manifest).name == name:
                return manifest
    return module["manifests"][0] if module["manifests"] else None


def _name(module: dict) -> str:
    """The unit's name as its ecosystem writes it: Maven's `groupId:artifactId`, the alias the pom gives."""
    if "maven" in module["ecosystems"]:
        return next((alias for alias in module["aliases"] if ":" in alias), module["name"])
    return module["name"]


def run(context) -> dict:
    graph = context.graph
    build = [m for m in graph["modules"] if m["provenance"] == "build"]
    by_id = {m["id"]: m for m in build}
    edges = graph.get("edges") or []
    units, dependencies = [], []
    for module in build:
        kinds = module["kind"].split("+")
        found = [KIND[k] for k in kinds if k in KIND]
        if any(k in JS_WORKSPACES for k in kinds) and any(PurePosixPath(m).name == "package.json"
                                                          for m in module["manifests"]):
            found = ["npm-package"] + [k for k in found if k != "npm-package"]
        depends = sorted({_name(by_id[e["target"]]) for e in edges if e["kind"] == "declares"
                          and e["source"] == module["id"] and e["target"] in by_id})
        for kind in dict.fromkeys(found):
            unit = {"name": _name(module), "kind": kind, "root": module["members"][0]["path"],
                    "manifest": _manifest(module, kind), "depends_on": depends}
            units.append(unit)
            dependencies += [{"unit": unit["name"], "name": name, "declared_in": unit["manifest"]}
                             for name in module.get("external") or []]
    workspaces: dict[str, dict] = {}
    for edge in edges:
        if edge["kind"] != "contains" or edge["source"] not in by_id or edge["target"] not in by_id:
            continue
        parent = by_id[edge["source"]]
        kinds = parent["kind"].split("+")
        tool = next((WORKSPACE[k] for k in kinds if k in WORKSPACE), parent["ecosystems"][0] if parent["ecosystems"] else "")
        entry = workspaces.setdefault(parent["id"], {"tool": tool, "root": parent["members"][0]["path"], "members": []})
        entry["members"].append(by_id[edge["target"]]["members"][0]["path"])
    gaps = [dict(gap) for gap in graph.get("gaps") or []]
    gaps += [{**gap, "unit": module["name"]} for module in build for gap in module.get("gaps") or []]
    return {"facts": {"units": units, "workspace": list(workspaces.values()), "dependencies": dependencies},
            "gaps": gaps}
