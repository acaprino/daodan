"""Swift Package Manager: `swift package describe --type json` (targets, products, declared dependencies,
tools version) and `swift package show-dependencies --format json` (the resolved graph; it fetches the
dependencies, honouring Package.resolved). Both compile and run Package.swift.
"""
from __future__ import annotations

from pathlib import Path

import native_common as common

VERSION = "Swift 5.10.1"
VERSION_COMMAND = ["swift", "--version"]
TRIGGERS = ("Package.swift",)
COMMAND = "swift package describe --type json; swift package show-dependencies --format json"


def _requirement(dep: dict) -> str | None:
    requirement = dep.get("requirement") or {}
    if requirement.get("range"):
        r = requirement["range"][0]
        return f">={r.get('lower_bound')},<{r.get('upper_bound')}"
    for key in ("exact", "branch", "revision"):
        if requirement.get(key):
            value = requirement[key]
            return f"{key} {value[0] if isinstance(value, list) else value}"
    return None


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    units, toolchains, dependencies, errors = [], [], [], []
    for manifest in common.find(root, {"Package.swift"}):
        here, directory = root / common.parent(manifest), common.parent(manifest)
        done = common.run(["swift", "package", "describe", "--type", "json"], here, name="swift package describe")
        data = common.json_or_none(done.stdout[done.stdout.find("{"):] if "{" in done.stdout else "")
        if done.returncode != 0 or not isinstance(data, dict):
            errors.append(f"{manifest}: describe: {common.error_of(done)}")
            continue
        targets = data.get("targets") or []
        config = {"source_sets": {t["name"]: [common.join(directory, t["path"])] for t in targets},
                  "packages": sorted(p["name"] for p in data.get("products") or []
                                     if "library" in (p.get("type") or {}))}
        units.append({"name": data.get("name"), "kind": "swift-package", "root": directory, "manifest": manifest,
                      "source_roots": sorted(common.join(directory, t["path"]) for t in targets), "config": config})
        if data.get("tools_version"):
            toolchains.append({"tool": "swift", "version": data["tools_version"], "declared_in": manifest})
        shown = common.run(["swift", "package", "show-dependencies", "--format", "json"], here,
                           name="swift package show-dependencies")
        tree = common.json_or_none(shown.stdout[shown.stdout.find("{"):] if "{" in shown.stdout else "")
        versions = {d.get("identity"): d.get("version") for d in (tree or {}).get("dependencies") or []} \
            if shown.returncode == 0 and isinstance(tree, dict) else None
        if versions is None:
            errors.append(f"{manifest}: show-dependencies: {common.error_of(shown)}")
        for dep in data.get("dependencies") or []:
            item = {"unit": data.get("name"), "name": dep.get("identity"), "declared": _requirement(dep),
                    "scope": "runtime", "declared_in": manifest}
            if versions is not None:
                item["resolved"] = versions.get(dep.get("identity"))
            dependencies.append(item)
    common.NOTES.update(errors=errors, raw={})
    return {"units": units, "toolchains": toolchains, "dependencies": dependencies}
