"""Yarn (Berry): workspaces as `yarn workspaces list --json --verbose` reports them, external dependencies as
`yarn info --all --dependents --json` reports them from yarn.lock.

Run where a yarn.lock or .yarnrc.yml sits (a walk by file name). `workspaceDependencies` (locations) give
`depends_on`; each `yarn info` entry is a resolved locator with the workspaces that depend on it.
"""
from __future__ import annotations

import re
from pathlib import Path

import native_common as common

VERSION = "yarn 4.9.2"
VERSION_COMMAND = ["yarn", "--version"]
TRIGGERS = ("yarn.lock", ".yarnrc.yml")
COMMAND = "yarn workspaces list --json --verbose; yarn info --all --dependents --json"


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    places = sorted({common.parent(p) for p in common.find(root, set(TRIGGERS))}, key=lambda d: (d.count("/"), d))
    units, workspaces, dependencies, errors = [], [], [], []
    covered: set[str] = set()
    for directory in places:
        if directory in covered:
            continue
        here = root / directory
        done = common.run(["yarn", "workspaces", "list", "--json", "--verbose"], here, name="yarn workspaces list")
        listed = [w for w in common.json_stream(done.stdout) if isinstance(w, dict) and "location" in w]
        if done.returncode != 0 or not listed:
            errors.append(f"{directory}: yarn workspaces list: {common.error_of(done)}")
            continue
        by_location = {w["location"]: w for w in listed}
        for w in listed:
            unit_root = common.rel(here / w["location"], root)
            covered.add(unit_root)
            depends = [by_location[d].get("name") for d in w.get("workspaceDependencies") or [] if d in by_location]
            kind = "npm-package"
            units.append({"name": w.get("name"), "kind": kind, "root": unit_root,
                          "manifest": common.join(unit_root, "package.json"), "depends_on": sorted(depends)})
        if len(listed) > 1:
            workspaces.append({"tool": "yarn", "root": common.rel(here, root),
                               "members": [common.rel(here / w["location"], root) for w in listed if w["location"] != "."]})
        info = common.run(["yarn", "info", "--all", "--dependents", "--json"], here, name="yarn info --all")
        if info.returncode != 0:
            errors.append(f"{directory}: yarn info: {common.error_of(info)}")
            continue
        names = {w.get("name") for w in listed}
        by_ident = {f"{w.get('name')}@workspace:{w['location']}": w for w in listed}
        for entry in common.json_stream(info.stdout):
            if not isinstance(entry, dict) or "value" not in entry:
                continue
            match = re.match(r"^(@?[^@]+)@(.+)$", entry["value"])
            if not match or match.group(1) in names:
                continue
            children = entry.get("children") or {}
            for dependent in children.get("Dependents") or [None]:
                owner = by_ident.get(dependent) if dependent else None
                item = {"name": match.group(1), "resolved": children.get("Version")}
                if owner is not None:
                    item["unit"] = owner.get("name")
                    item["declared_in"] = common.join(common.rel(here / owner["location"], root), "package.json")
                dependencies.append(item)
    common.NOTES.update(errors=errors, raw={})
    return {"units": units, "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
            "dependencies": dependencies}
