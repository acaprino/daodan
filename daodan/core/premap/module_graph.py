"""Source: the build modules of the module graph (`module_derive.build_graph`, in memory), its units as the pre-map names them.

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
from pathlib import Path, PurePosixPath
import re

import modules
from build_units import normalize_pypi_name

NAME, VERSION, RANK = "modules.py", f"{modules.SCHEMA}.unit-resolution.2", "reader"
PACKAGE_ECOSYSTEM = {
    "npm": "npm", "pnpm": "npm", "lerna": "npm", "nx": "npm", "angular": "npm", "deno": "npm",
    "python": "pypi", "cargo": "crates", "go": "go", "maven": "maven", "gradle": "maven", "sbt": "maven",
    "dotnet": "nuget", "composer": "composer", "bundler": "rubygems", "rubygems": "rubygems",
    "pub": "pub", "melos": "pub", "swiftpm": "swiftpm", "mix": "hex", "terraform": "terraform",
}
_FROM = re.compile(r"^\s*FROM\s+(?:--\S+\s+)*([^\s#]+)(?:\s+AS\s+([^\s#]+))?", re.I)
_IMAGE = re.compile(r"^\s*image:\s*['\"]?([^\s'\"#]+)")
_FLUTTER_SDK = re.compile(r"^\s*sdk\s*:\s*flutter\b")


def normalize_image(reference: str) -> str:
    """An image reference without registry host, tag or digest: `docker.io/library/postgres:16` is `postgres`."""
    name = reference.split("@", 1)[0]
    if ":" in name.rsplit("/", 1)[-1]:
        name = name.rsplit(":", 1)[0]
    parts = name.split("/")
    if len(parts) > 1 and ("." in parts[0] or ":" in parts[0] or parts[0] == "localhost"):
        parts = parts[1:]
    if parts[:1] == ["library"]:
        parts = parts[1:]
    return "/".join(parts).lower()
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


def external_packages(graph: dict, packages: list[dict]) -> list[dict]:
    """Discard PyPI signs at the pyproject that explicitly resolves them to a local workspace member or directory."""
    python = {m["id"]: m for m in graph["modules"] if "python" in m.get("ecosystems", ())}
    local = set()
    for edge in graph["edges"]:
        if edge["kind"] != "declares" or edge["source"] not in python or edge["target"] not in python:
            continue
        source, target = python[edge["source"]], python[edge["target"]]
        target_name = normalize_pypi_name(target["name"])
        external = {normalize_pypi_name(name) for name in source["external"]}
        workspace = {_root(source), *source["registered_by"]} & {_root(target), *target["registered_by"]}
        for dep in source["path_dependencies"]:
            name = normalize_pypi_name(dep["name"])
            if name not in external and (dep["path"] == _root(target) or
                                         (dep.get("workspace") and workspace and name == target_name)):
                local.update((rel, name) for rel in source["manifests"] if PurePosixPath(rel).name == "pyproject.toml")
    if not local:
        return packages
    return [p for p in packages if p["ecosystem"] != "pypi" or
            ((p.get("declared_in") or "").partition("#")[0], normalize_pypi_name(p["name"])) not in local]


def _declared_packages(graph: dict, inventory) -> list[dict]:
    """Declared package and container image signs from manifests, pubspec SDKs, Dockerfiles and Compose files; a
    manifest's package has the `version` its reader read there (`build_units`), none where it gives none."""
    units = [m for m in graph["modules"] if m["provenance"] == "build"]
    lines_cache: dict[str, list[str]] = {}

    def lines_of(rel: str) -> list[str]:
        if rel not in lines_cache:
            try:
                lines_cache[rel] = inventory.text(rel).splitlines()
            except (KeyError, OSError, ValueError):
                lines_cache[rel] = []
        return lines_cache[rel]

    packages: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add(ecosystem: str, name: str, path: str, line: int | None, version: str | None = None) -> None:
        if not name or not path:
            return
        declared_in = f"{path}#L{line}" if line else path
        key = (ecosystem, name.casefold(), path)
        if key not in seen:
            seen.add(key)
            packages.append({"ecosystem": ecosystem, "name": name, "declared_in": declared_in,
                             **({"version": version} if version else {})})

    for unit in units:
        ecosystems = sorted({PACKAGE_ECOSYSTEM[e] for e in unit.get("ecosystems", []) if e in PACKAGE_ECOSYSTEM})
        for ecosystem in ecosystems:
            # Python signs are resolved per declaring manifest by external_packages after joining all readers.
            dependencies = unit["dependencies"] if ecosystem == "pypi" else unit["external"]
            for name in dependencies:
                needle = name.split(":", 1)[-1] if ecosystem == "maven" and ":" in name else name
                path, line = next(
                    ((p, n) for p in unit["manifests"] for n, text in enumerate(lines_of(p), 1)
                     if re.search(rf"""(^|[\s"'/:>]){re.escape(name)}($|[\s"'=<>~^@:,\[/])""", text)
                     or (needle != name and re.search(rf"""(^|[\s"'/:>]){re.escape(needle)}($|[\s"'=<>~^@:,\[/<])""", text))),
                    (unit["manifests"][0] if unit["manifests"] else None, None),
                )
                add(ecosystem, name, path, line, ((unit.get("versions") or {}).get(path) or {}).get(name))

    for rel in inventory.files:
        base = PurePosixPath(rel).name
        if base == "pubspec.yaml":
            for n, text in enumerate(lines_of(rel), 1):
                if _FLUTTER_SDK.match(text):
                    add("pub", "flutter", rel, n)
        elif base == "Dockerfile" or base.endswith(".Dockerfile"):
            stages: set[str] = set()
            for n, text in enumerate(lines_of(rel), 1):
                if match := _FROM.match(text):
                    raw, alias = match.group(1), match.group(2)
                    if raw.lower() != "scratch" and raw.lower() not in stages and not raw.startswith("$"):
                        add("docker", normalize_image(raw), rel, n)
                    if alias:
                        stages.add(alias.lower())
        elif base.startswith(("docker-compose", "compose")) and base.endswith((".yml", ".yaml")):
            for n, text in enumerate(lines_of(rel), 1):
                if (match := _IMAGE.match(text)) and not match.group(1).startswith("$"):
                    add("docker", normalize_image(match.group(1)), rel, n)
    return packages


def package_facts(manifest: Path) -> list[dict]:
    """Fast reader-only package signs of `manifest` without running any container command."""
    import premap
    from snapshot_store import open_snapshot
    manifest = Path(manifest).resolve()
    parts = []
    with open_snapshot(manifest) as store:
        context = premap.Context(manifest, store)
        for source in (premap.module_graph, premap.requirements, premap.jvm_files, premap.project_files):
            result = source.run(context)
            if result and (result.get("facts") or {}).get("packages"):
                parts.append({"source": premap.label(source), "rank": source.RANK,
                              "facts": {"packages": result["facts"]["packages"]}})
        return external_packages(context.graph, premap.join(parts).get("packages", [])) if parts else []


def run(context) -> dict:
    graph = context.graph
    ref = references(graph)
    gaps = [dict(gap) for gap in graph.get("gaps") or []]
    gaps += [{**gap, "unit": ref[module["id"]]} for module in graph["modules"] if module["provenance"] == "build"
             for gap in module.get("gaps") or []]
    found = facts(graph)
    packages = _declared_packages(graph, context.inventory)
    out = {"units": found["units"], "workspace": found["workspace"],
           **({"packages": packages} if packages else {})}
    return {"facts": out, "gaps": gaps}
