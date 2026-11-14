"""TypeScript: the final configuration of every tsconfig as `tsc --showConfig -p <file>` reports it.

Every `tsconfig*.json` outside node_modules and dot directories is shown (the root `tsconfig.json` files and their
`references`, followed, are among them). Each tsconfig belongs to the unit of its nearest folder with a
`project.json` (nx-project), `deno.json` (deno-project) or `package.json` (npm-package); a unit's `config.tsconfig`
lists its files (the folder's `tsconfig.json`, then its references in the written order, then the others) and
`config.paths` merges their `compilerOptions.paths`, each target resolved against `baseUrl` when the shown
configuration has one, otherwise against the folder of the tsconfig, and written relative to the project root.
tsc reads JSON only (`plugins` are for the language service); an `extends` into an absent node_modules is an error.
"""
from __future__ import annotations

import os
from pathlib import Path

import native_common as common

VERSION = "TypeScript 6.0.3 on Node v22.23.4"
VERSION_COMMAND = ["tsc", "--version"]
TRIGGERS = ("tsconfig.json", "tsconfig.base.json", "tsconfig.app.json", "tsconfig.lib.json", "tsconfig.node.json",
            "tsconfig.build.json", "tsconfig.spec.json")  # which fixtures to run on; run() itself walks every tsconfig*
COMMAND = "tsc --showConfig -p <each tsconfig*.json>"
OWNERS = (("project.json", "nx-project"), ("deno.json", "deno-project"), ("deno.jsonc", "deno-project"),
          ("package.json", "npm-package"))
PRUNE = common.PRUNE | {"bower_components"}


def _is_tsconfig(name: str) -> bool:
    return name.startswith("tsconfig") and name.endswith(".json")


def _owner(root: Path, rel: str) -> tuple[str, str]:
    folder = common.parent(rel)
    while True:
        for marker, kind in OWNERS:
            if (root / folder / marker).is_file():
                return folder, kind
        if folder == ".":
            return ".", "npm-package"
        folder = common.parent(folder)


def _resolve(root: Path, base: Path, target: str) -> str:
    return common.rel(Path(os.path.normpath(base / target)), root)


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    files = []
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in PRUNE)
        files += [common.rel(Path(base) / n, root) for n in sorted(names) if _is_tsconfig(n)]
    if not files:
        return {}
    shown, errors, raw = {}, [], {"references": {}, "paths_base": {}}
    for rel in files:
        done = common.run(["tsc", "--showConfig", "-p", str(root / rel)], root / common.parent(rel),
                          name="tsc --showConfig")
        data = common.json_or_none(done.stdout)
        if done.returncode != 0 or not isinstance(data, dict):
            errors.append(f"{rel}: {common.error_of(done)}")
            continue
        shown[rel] = data
    units: dict[tuple[str, str], dict] = {}
    for rel in files:
        folder, kind = _owner(root, rel)
        unit = units.setdefault((folder, kind), {"kind": kind, "root": folder, "config": {"tsconfig": []}})
        order = unit["config"]["tsconfig"]
        if rel not in order:
            order.append(rel)
    for (folder, _kind), unit in units.items():
        order = unit["config"]["tsconfig"]
        first = [r for r in order if Path(r).name == "tsconfig.json" and common.parent(r) == folder]
        refs = []
        for start in first:
            for ref in (shown.get(start) or {}).get("references") or []:
                target = common.rel(Path(os.path.normpath(root / common.parent(start) / ref.get("path", ""))), root)
                target = common.join(target, "tsconfig.json") if (root / target).is_dir() else target
                raw["references"].setdefault(start, []).append(target)
                if target in order and target not in refs:
                    refs.append(target)
        unit["config"]["tsconfig"] = first + refs + sorted(r for r in order if r not in first and r not in refs)
        paths = {}
        for rel in unit["config"]["tsconfig"]:
            options = (shown.get(rel) or {}).get("compilerOptions") or {}
            if not isinstance(options.get("paths"), dict):
                continue
            folder_of = root / common.parent(rel)
            base = folder_of / options["baseUrl"] if isinstance(options.get("baseUrl"), str) else folder_of
            raw["paths_base"][rel] = "baseUrl" if isinstance(options.get("baseUrl"), str) else "tsconfig folder"
            for key, targets in options["paths"].items():
                paths.setdefault(key, [_resolve(root, base, t) for t in targets if isinstance(t, str)])
        if paths:
            unit["config"]["paths"] = paths
        unit["config"]["tsconfig_files"] = {r: len((shown.get(r) or {}).get("files") or []) for r in unit["config"]["tsconfig"]
                                            if r in shown}
    common.NOTES.update(errors=errors, raw=raw)
    return {"units": list(units.values())}
