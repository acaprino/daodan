"""Specfy stack-analyser 1.27.6, the CLI Daodan already runs: components with technologies, dependencies, edges.

`stack-analyser <path> --output=out.json` (run in an empty working directory: the output path is joined to it).
The tool types every technology (`techs.generated.js`: `type` of each key). Normalisation, fixed here and not tuned:
frameworks are the types `framework`, `ui_framework` and `ssg`, plus the web frameworks the tool files under
`tool` (TOOL_FRAMEWORKS); services are the types of SERVICE_KINDS. Every other technology (languages, builders,
ORMs, CI, cloud, SaaS) is in `detail` only. A unit is a component whose path is a manifest file and which has no
technology of its own; its frameworks and dependencies are those of the component and its children.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import _fw

VERSION = "1.27.6"
PACKAGE = _fw.NODE_MODULES / "@specfy" / "stack-analyser"
FRAMEWORK_TYPES = {"framework", "ui_framework", "ssg"}
TOOL_FRAMEWORKS = {"express", "fastify", "koa", "honojs", "elysiajs", "adonisjs"}
SERVICE_KINDS = {"db": "database", "queue": "queue", "storage": "storage", "auth": "authentication",
                 "payment": "payment", "notification": "notification", "ai": "ai"}


def catalogue() -> dict[str, tuple[str, str]]:
    """key -> (name, type) of every technology the installed tool knows."""
    text = (PACKAGE / "dist" / "common" / "techs.generated.js").read_text(encoding="utf-8")
    return {key: (name, kind) for key, name, kind in re.findall(r"key: '([^']+)', name: '([^']+)', type: '([^']+)'", text)}


def normalise(payload: dict, known: dict) -> dict:
    units, frameworks, services, dependencies, seen = {}, {}, {}, [], {}

    def walk(node: dict, unit: str | None) -> None:
        paths = [_fw.posix(p) for p in node.get("path", [])]
        manifest = next((p for p in paths if _fw.unit_kind(p)), None)
        own = node.get("tech")
        if own is None and manifest and node.get("name") != "main":
            unit = node["name"]
            units.setdefault(manifest, {"name": unit, "kind": _fw.unit_kind(manifest), "root": _fw.parent(manifest),
                                        "manifest": manifest})
            for ecosystem, name, declared in node.get("dependencies", []):
                dependencies.append({"unit": unit, "name": name, "declared": declared, "declared_in": manifest})
        evidence = paths[0] if paths else None
        for key in [*node.get("techs", []), *([own] if own else [])]:
            name, kind = known.get(key, (key, "unknown"))
            seen.setdefault(key, {"name": name, "type": kind, "paths": []})
            if evidence and evidence not in seen[key]["paths"]:
                seen[key]["paths"].append(evidence)
            if kind in FRAMEWORK_TYPES or (kind == "tool" and key in TOOL_FRAMEWORKS):
                frameworks.setdefault((key, unit), {"name": name, **({"unit": unit} if unit else {}),
                                                    **({"evidence": evidence} if evidence else {})})
            elif kind in SERVICE_KINDS:
                services.setdefault(key, {"name": name, "kind": SERVICE_KINDS[kind],
                                          **({"evidence": evidence} if evidence else {})})
        for child in node.get("childs", []):
            walk(child, unit)

    walk(payload, None)
    return {"units": list(units.values()), "frameworks": list(frameworks.values()), "services": list(services.values()),
            "dependencies": dependencies,
            "detail": {"ids": sorted(seen), "technologies": {k: seen[k] for k in sorted(seen)}}}


def run(fixture_dir, work_dir) -> dict:
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    code, out, err = _fw.execute(["node", PACKAGE / "dist" / "cli.js", Path(fixture_dir).resolve(), "--output=out.json"],
                                 work)
    if code != 0:
        raise RuntimeError(f"stack-analyser exited {code}: {(err or out)[-400:]}")
    return normalise(json.loads((work / "out.json").read_text(encoding="utf-8")), catalogue())
