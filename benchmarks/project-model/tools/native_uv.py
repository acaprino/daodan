"""uv: the project model as uv reports it from uv.lock, never locking again (`--frozen`).

Where a uv.lock or pyproject.toml sits that no earlier answer covered: `uv export --frozen --all-packages
--no-hashes --format pylock.toml` (the local packages with their directories: the units), `uv tree --frozen
--depth 1` (each member's direct dependencies with resolved version and group or extra), `uv python pin`
(the pinned interpreter request) and `uv python find` (the interpreter uv would use). Without uv.lock every
`--frozen` command refuses.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import native_common as common

VERSION = "uv 0.11.28"
VERSION_COMMAND = ["uv", "--version"]
TRIGGERS = ("uv.lock", "pyproject.toml")
COMMAND = ("uv export --frozen --all-packages --no-hashes --format pylock.toml; uv tree --frozen --depth 1; "
           "uv python pin; uv python find")
LINE = re.compile(r"^(?P<prefix>[\s│├└─]*)(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])? v(?P<version>\S+)"
                  r"(?P<rest>.*)$")


def _tree(text: str) -> dict[str, list[dict]]:
    """`{root package: [direct dependency]}` from `uv tree --depth 1`."""
    out, current = {}, None
    for line in text.splitlines():
        match = LINE.match(line)
        if not match:
            continue
        if not match.group("prefix"):
            current = match.group("name")
            out.setdefault(current, [])
            continue
        if current is None:
            continue
        rest = match.group("rest")
        scope = "runtime"
        group = re.search(r"\(group: ([^)]+)\)", rest)
        if group:
            scope = "test" if group.group(1).strip() == "test" else "dev"
        if re.search(r"\(extra: ([^)]+)\)", rest):
            scope = "optional"
        out[current].append({"name": match.group("name"), "version": match.group("version"), "scope": scope,
                             "group": group.group(1).strip() if group else None})
    return out


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    places = sorted({common.parent(p) for p in common.find(root, set(TRIGGERS))}, key=lambda d: (d.count("/"), d))
    units, workspaces, toolchains, dependencies, errors, raw = [], [], [], [], [], {}
    covered: set[str] = set()
    for directory in places:
        if directory in covered:
            continue
        here = root / directory
        export = common.run(["uv", "export", "--frozen", "--all-packages", "--no-hashes", "--format", "pylock.toml"],
                            here, name="uv export --frozen")
        if export.returncode != 0:
            errors.append(f"{directory}: uv export: {common.error_of(export)}")
            covered.add(directory)
            continue
        try:
            lock = tomllib.loads(export.stdout)
        except tomllib.TOMLDecodeError as error:
            errors.append(f"{directory}: uv export output: {error}")
            continue
        local = {p["name"]: common.rel(here / p["directory"]["path"], root)
                 for p in lock.get("packages") or [] if isinstance(p.get("directory"), dict)}
        tree = common.run(["uv", "tree", "--frozen", "--depth", "1"], here, name="uv tree --frozen")
        if tree.returncode != 0:
            errors.append(f"{directory}: uv tree: {common.error_of(tree)}")
        trees = _tree(tree.stdout) if tree.returncode == 0 else {}
        for name in sorted(set(local) | set(trees)):
            unit_root = local.get(name)
            covered.add(unit_root or directory)
            manifest = common.join(unit_root, "pyproject.toml") if unit_root else None
            depends, unit_deps = [], []
            for dep in trees.get(name, []):
                if dep["name"] in local or dep["name"] in trees:
                    depends.append(dep["name"])
                    continue
                item = {"unit": name, "name": dep["name"], "resolved": dep["version"], "scope": dep["scope"]}
                if manifest:
                    item["declared_in"] = manifest
                unit_deps.append(item)
            dependencies.extend(unit_deps)
            unit = {"name": name, "kind": "python-project", "depends_on": sorted(set(depends))}
            if unit_root:
                unit.update(root=unit_root, manifest=manifest)
            units.append(unit)
        members = sorted(v for v in local.values() if v != common.rel(here, root))
        if members:
            workspaces.append({"tool": "uv", "root": common.rel(here, root), "members": members})
        pin = common.run(["uv", "python", "pin"], here, name="uv python pin")
        if pin.returncode == 0 and pin.stdout.strip():
            toolchains.append({"tool": "python", "version": pin.stdout.strip().splitlines()[-1],
                               "declared_in": common.join(common.rel(here, root), ".python-version")})
        found = common.run(["uv", "python", "find"], here, name="uv python find")
        raw.setdefault("uv python find", {})[directory] = (found.stdout.strip() or common.error_of(found))[:200]
    common.NOTES.update(errors=errors, raw=raw)
    return {"units": units, "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
            "toolchains": toolchains, "dependencies": dependencies}
