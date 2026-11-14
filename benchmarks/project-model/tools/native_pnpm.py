"""pnpm: the workspace as `pnpm list --json -r --depth 0` reports it. pnpm 9 and 10 have no `--lockfile-only`
for `list` (it is refused as an unknown option), so without node_modules the versions come from nothing installed.

Run where a pnpm-workspace.yaml or a pnpm-lock.yaml sits (a walk by file name). Each listed project is a
unit; a dependency whose version is `link:` or `workspace:` is another unit, the rest are external with the
version the lockfile resolved. pnpm prints no declared range, no engines and no packageManager field.
"""
from __future__ import annotations

from pathlib import Path

import native_common as common

VERSION = "pnpm 10.33.2"
VERSION_COMMAND = ["pnpm", "--version"]
TRIGGERS = ("pnpm-workspace.yaml", "pnpm-lock.yaml")
COMMAND = "pnpm list --json -r --depth 0"
SECTIONS = (("dependencies", "runtime"), ("devDependencies", "dev"), ("optionalDependencies", "optional"))


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    places = sorted({common.parent(p) for p in common.find(root, set(TRIGGERS))}, key=lambda d: (d.count("/"), d))
    units, workspaces, dependencies, errors = [], [], [], []
    covered: set[str] = set()
    for directory in places:
        if directory in covered:
            continue
        done = common.run(["pnpm", "list", "--json", "-r", "--depth", "0"], root / directory,
                          name=COMMAND)
        projects = common.json_or_none(done.stdout)
        if done.returncode != 0 or not isinstance(projects, list):
            errors.append(f"{directory}: {common.error_of(done)}")
            continue
        names = {p.get("name") for p in projects if p.get("name")}
        here = common.rel(root / directory, root)
        member_dirs = []
        for project in projects:
            unit_root = common.rel(project.get("path") or root / directory, root)
            covered.add(unit_root)
            if unit_root != here:
                member_dirs.append(unit_root)
            depends = []
            for section, scope in SECTIONS:
                for dep, info in (project.get(section) or {}).items():
                    version = str(info.get("version", ""))
                    if dep in names or version.startswith(("link:", "workspace:", "file:")):
                        depends.append(dep)
                        continue
                    item = {"unit": project.get("name"), "name": dep, "resolved": version or None, "scope": scope,
                            "declared_in": common.join(unit_root, "package.json")}
                    if "specifier" in info:
                        item["declared"] = info["specifier"]
                    dependencies.append(item)
            kind = "npm-package"
            unit = {"name": project.get("name"), "kind": kind, "root": unit_root,
                    "manifest": common.join(unit_root, "package.json"), "depends_on": sorted(set(depends))}
            if "private" in project:
                unit["config"] = {"private": project["private"]}
            units.append(unit)
        if len(projects) > 1:
            workspaces.append({"tool": "pnpm", "root": here, "members": member_dirs})
    common.NOTES.update(errors=errors, raw={})
    return {"units": units, "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
            "dependencies": dependencies}
