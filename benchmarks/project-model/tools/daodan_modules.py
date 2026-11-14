"""Baseline: Daodan's own module reader (`modules.py`, provenance `build`), read as it is.

`snapshot.py write <fixture> --no-engine --no-index` builds the snapshot and `modules.json` beside it, as the
plugin does; the build modules are converted to the shared shape. modules.py gives unit roots, names, the
manifests, workspace registrations, declared edges between units and the names (no versions, no scope) of
external dependencies; it reads no toolchain, no source root and no indexer configuration.
"""
from __future__ import annotations

import json
import sys
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
        "terraform-root": "terraform-module"}
WORKSPACE = {"npm-workspace": "npm", "pnpm-workspace": "pnpm", "lerna-workspace": "lerna", "go-workspace": "go",
             "melos-workspace": "melos", "stack-workspace": "stack", "dotnet-solution": "dotnet"}
JS_WORKSPACES = {"npm-workspace", "pnpm-workspace", "lerna-workspace"}
MANIFEST = {"npm": "package.json", "python": ("pyproject.toml", "setup.py", "setup.cfg"), "cargo": "Cargo.toml",
            "go": "go.mod", "maven": "pom.xml", "gradle": ("build.gradle.kts", "build.gradle", "settings.gradle.kts",
                                                         "settings.gradle"),
            "composer": "composer.json", "pub": "pubspec.yaml", "swiftpm": "Package.swift", "mix": "mix.exs",
            "cmake": "CMakeLists.txt", "bundler": "Gemfile", "deno": ("deno.json", "deno.jsonc"), "nx": "project.json"}
ECOSYSTEM = {"npm-package": "npm", "python-project": "python", "cargo-crate": "cargo",
             "go-module": "go", "maven-module": "maven", "gradle-project": "gradle", "composer-package": "composer",
             "pub-package": "pub", "swift-package": "swiftpm", "mix-project": "mix", "cmake-target": "cmake", "bundler-project": "bundler",
             "gem": "bundler", "deno-project": "deno", "nx-project": "nx"}
LAST: dict = {}


def _manifest(module: dict, ecosystem: str) -> str | None:
    wanted = MANIFEST.get(ecosystem, ())
    wanted = (wanted,) if isinstance(wanted, str) else wanted
    for name in wanted:
        for manifest in module["manifests"]:
            if PurePosixPath(manifest).name == name:
                return manifest
    return module["manifests"][0] if module["manifests"] else None


def convert(graph: dict) -> dict:
    build = [m for m in graph["modules"] if m["provenance"] == "build"]
    by_id = {m["id"]: m for m in build}
    units, names = [], {}
    for module in build:
        kinds = module["kind"].split("+")
        root = module["members"][0]["path"]
        unit_kinds = [KIND[k] for k in kinds if k in KIND]
        if any(k in JS_WORKSPACES for k in kinds) and any(PurePosixPath(m).name == "package.json"
                                                          for m in module["manifests"]):
            unit_kinds = ["npm-package"] + [k for k in unit_kinds if k != "npm-package"]
        for kind in dict.fromkeys(unit_kinds):
            units.append({"name": module["name"], "kind": kind, "root": root,
                          "manifest": _manifest(module, ECOSYSTEM.get(kind, "")), "depends_on": [],
                          "_id": module["id"]})
        names[module["id"]] = module["name"]
    edges = graph.get("edges") or []
    for unit in units:
        unit["depends_on"] = sorted({names[e["target"]] for e in edges
                                     if e["kind"] == "declares" and e["source"] == unit["_id"] and e["target"] in names})
    workspaces = {}
    for edge in edges:
        if edge["kind"] != "contains" or edge["source"] not in by_id or edge["target"] not in by_id:
            continue
        parent = by_id[edge["source"]]
        kinds = parent["kind"].split("+")
        tool = next((WORKSPACE[k] for k in kinds if k in WORKSPACE), parent["ecosystems"][0] if parent["ecosystems"] else "")
        entry = workspaces.setdefault(parent["id"], {"tool": tool, "root": parent["members"][0]["path"], "members": []})
        entry["members"].append(by_id[edge["target"]]["members"][0]["path"])
    dependencies = []
    for unit in units:
        module = by_id[unit["_id"]]
        for name in module.get("external") or []:
            dependencies.append({"unit": unit["name"], "name": name, "declared_in": unit["manifest"]})
    for unit in units:
        unit.pop("_id")
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
