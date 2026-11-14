"""npm: the package model as npm reports it from the lockfile, without installing.

In each directory with a package.json that no earlier answer covered: `npm query ":root, .workspace"
--package-lock-only` (units, their manifests' fields and declared ranges, workspace members) and
`npm ls --json --all --package-lock-only` (the versions the lock resolved). Without a lockfile npm refuses
both, so each is asked again without `--package-lock-only`: npm then reads the actual tree, which here holds
only the manifests (no node_modules). The mode used is kept in the notes.
"""
from __future__ import annotations

from pathlib import Path

import native_common as common

VERSION = "npm bundled with Node v22.23.4"
VERSION_COMMAND = ["npm", "--version"]
TRIGGERS = ("package.json",)
COMMAND = 'npm query ":root, .workspace" --package-lock-only; npm ls --json --all --package-lock-only'
SECTIONS = (("dependencies", "runtime"), ("devDependencies", "dev"), ("optionalDependencies", "optional"),
            ("peerDependencies", "peer"))
CONFIG = ("main", "bin", "type", "module", "types", "exports", "private", "files", "browser")
PRUNE = common.PRUNE | {"bower_components"}


def _ask(args, cwd, name):
    done = common.run(["npm", *args, "--package-lock-only"], cwd, name=name + " --package-lock-only")
    data = common.json_or_none(done.stdout)
    if done.returncode == 0 and data is not None:
        return data, "lockfile", None
    first = common.error_of(done)
    again = common.run(["npm", *args], cwd, name=name)
    data = common.json_or_none(again.stdout)
    if data is not None:
        return data, "actual tree", first
    return None, None, f"{first}; without --package-lock-only: {common.error_of(again)}"


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    manifests = common.find(root, {"package.json"}, prune=PRUNE)
    units, workspaces, toolchains, dependencies, errors, modes = [], [], [], [], [], {}
    covered: set[str] = set()
    for manifest in manifests:
        directory = common.parent(manifest)
        if directory in covered:
            continue
        nodes, mode, error = _ask(["query", ":root, .workspace"], root / directory, "npm query")
        if error:
            errors.append(f"{directory}: npm query: {error}")
        if not isinstance(nodes, list):
            covered.add(directory)
            continue
        tree, tree_mode, error = _ask(["ls", "--json", "--all"], root / directory, "npm ls --json --all")
        if error:
            errors.append(f"{directory}: npm ls: {error}")
        modes[directory] = {"query": mode, "ls": tree_mode}
        tree = tree if isinstance(tree, dict) else {}
        locals_ = [n for n in nodes if isinstance(n, dict) and "node_modules/" not in f"/{n.get('location', '')}/"]
        names = {n.get("name") for n in locals_ if n.get("name")}
        member_dirs = []
        for node in locals_:
            unit_root = common.rel(root / directory / node.get("location", ""), root)
            covered.add(unit_root)
            is_root = node.get("location", "") == ""
            if not is_root:
                member_dirs.append(unit_root)
            manifest_rel = common.join(unit_root, "package.json")
            name = node.get("name")
            edges = tree.get("dependencies") or {} if is_root else \
                ((tree.get("dependencies") or {}).get(name) or {}).get("dependencies") or {}
            depends = []
            for section, scope in SECTIONS:
                for dep, spec in (node.get(section) or {}).items():
                    if dep in names:
                        depends.append(dep)
                        continue
                    item = {"unit": name, "name": dep, "declared": spec, "scope": scope, "declared_in": manifest_rel}
                    if tree_mode == "lockfile":
                        item["resolved"] = (edges.get(dep) or {}).get("version")
                    dependencies.append(item)
            kind = "npm-package"  # a workspace root is a package too (SCHEMA.md)
            units.append({"name": name, "kind": kind, "root": unit_root, "manifest": manifest_rel,
                          "depends_on": sorted(set(depends)),
                          "config": {k: node[k] for k in CONFIG if k in node}})
            engines = node.get("engines") if isinstance(node.get("engines"), dict) else {}
            for tool, version in engines.items():
                toolchains.append({"tool": tool, "version": version, "declared_in": manifest_rel})
            manager = node.get("packageManager")
            if isinstance(manager, str) and "@" in manager.lstrip("@"):
                tool, _, version = manager.rpartition("@")
                toolchains.append({"tool": tool, "version": version.split("+", 1)[0], "declared_in": manifest_rel})
        root_node = next((n for n in locals_ if n.get("location", "") == ""), None)
        if root_node is not None and root_node.get("workspaces"):
            workspaces.append({"tool": "npm", "root": common.rel(root / directory, root), "members": member_dirs})
    common.NOTES.update(errors=errors, raw={"mode per directory": modes})
    return {"units": units, "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
            "toolchains": toolchains, "dependencies": dependencies}
