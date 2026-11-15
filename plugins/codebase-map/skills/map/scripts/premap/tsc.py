"""Source: TypeScript's own reading of every tsconfig, `tsc --showConfig -p <file>`, run in Daodan's container.

`commands` describes one `tsc --showConfig` per `tsconfig*.json` of the snapshot, in its folder: tsc reads JSON
only, follows `extends`, and runs nothing of the project. `read` gives each tsconfig to the unit of its nearest
folder holding a `project.json` (nx-project), a `deno.json` or `deno.jsonc` (deno-project) or a `package.json`
(npm-package): the unit's `config.tsconfig` lists its files (the folder's `tsconfig.json`, then the references it
names in their order, then the others) and `config.paths` merges their `compilerOptions.paths`, each target
resolved against `baseUrl` when the shown configuration has one, else against the tsconfig's folder, relative to
the project's root. A tsconfig tsc refuses (an `extends` into an absent `node_modules`) is a `model_failed` gap;
one no unit holds is a `config_outside_units` gap.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

NAME, VERSION, RANK = "tsc", "6.0.3", "model"  # typescript@6.0.3, pinned by the pre-map
OWNERS = (("project.json", "nx-project"), ("deno.json", "deno-project"), ("deno.jsonc", "deno-project"),
          ("package.json", "npm-package"))


def _parent(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _join(folder: str, name: str) -> str:
    return posixpath.normpath(name if folder == "." else f"{folder}/{name}")


def commands(context):
    files = [rel for rel in context.inventory.files
             if PurePosixPath(rel).name.startswith("tsconfig") and rel.endswith(".json")]
    return [{"tool": "tsc", "argv": ["tsc", "--showConfig", "-p", PurePosixPath(rel).name], "cwd": _parent(rel),
             "env": {}, "network": "none"} for rel in files] or None


def _owner(context, rel: str):
    folder = _parent(rel)
    while True:
        for marker, kind in OWNERS:
            if _join(folder, marker) in context.inventory.headers:
                return folder, kind
        if folder == ".":
            return None
        folder = _parent(folder)


def read(context, commands, results):
    shown, gaps = {}, []
    for command, result in zip(commands, results):
        rel = _join(command["cwd"], command["argv"][-1])
        data = None
        if result["returncode"] == 0:
            try:
                data = json.loads(result["stdout"])
            except ValueError:
                pass
        if isinstance(data, dict):
            shown[rel] = data
        else:
            gaps.append({"kind": "model_failed", "path": rel,
                         "detail": f"tsc --showConfig: {(result['stderr'] or result['stdout']).strip()[-400:]}"})
    units: dict[tuple, dict] = {}
    for rel in sorted({_join(c["cwd"], c["argv"][-1]) for c in commands}):
        owner = _owner(context, rel)
        if owner is None:
            gaps.append({"kind": "config_outside_units", "path": rel,
                         "detail": "no package.json, deno.json or project.json above this tsconfig: no unit holds it"})
            continue
        folder, kind = owner
        unit = units.setdefault(owner, {"root": folder, "kind": kind, "config": {"tsconfig": []}})
        unit["config"]["tsconfig"].append(rel)
    for (folder, _), unit in units.items():
        order = unit["config"]["tsconfig"]
        first = [r for r in order if PurePosixPath(r).name == "tsconfig.json" and _parent(r) == folder]
        references = []
        for start in first:
            for reference in (shown.get(start) or {}).get("references") or []:
                target = _join(_parent(start), reference.get("path", ""))
                target = target if target.endswith(".json") else _join(target, "tsconfig.json")
                if target in order and target not in references:
                    references.append(target)
        unit["config"]["tsconfig"] = first + references + sorted(r for r in order if r not in first and r not in references)
        paths = {}
        for rel in unit["config"]["tsconfig"]:
            options = (shown.get(rel) or {}).get("compilerOptions") or {}
            if not isinstance(options.get("paths"), dict):
                continue
            base = _join(_parent(rel), options["baseUrl"]) if isinstance(options.get("baseUrl"), str) else _parent(rel)
            for key, targets in options["paths"].items():
                paths.setdefault(key, [_join(base, t) for t in targets if isinstance(t, str)])
        if paths:
            unit["config"]["paths"] = paths
    return {"facts": {"units": list(units.values())}, "gaps": gaps}
