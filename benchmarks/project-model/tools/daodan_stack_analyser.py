"""Baseline, read only: Daodan's wrapper `stack_analyser.py`, called the way `system_brief.py` calls it.

`stack_analyser.run(root, cache, files)` with `files` the paths of the fixture (a snapshot's file list), the cache
holding the same CLI version the wrapper pins (1.27.6), installed once in the image. The wrapper keeps the
technologies whose path is a file of the project and gives no type: as `system_brief._externals` does, the registry
entry of the technology decides, and an entry of kind `service` is a service (name and kind from the registry, as in
`daodan_registry`); frameworks are not given. Every technology found is in `detail.ids`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import _fw
from daodan_registry import RANK_KINDS, SCRIPTS

VERSION = "wrapper stack_analyser.py over stack-analyser 1.27.6"
CACHE = Path(os.environ.get("PM_STACK_CACHE", "/opt/cache"))


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir).resolve()
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import stack_analyser
    files = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}
    result = stack_analyser.run(root, CACHE, files)
    if result["status"] != "ok":
        raise RuntimeError(f"wrapper unavailable: {result.get('reason')}")
    registry = {e["id"]: e for e in json.loads((SCRIPTS.parent / "data" / "service-registry.json").read_text(encoding="utf-8"))["entries"]}
    services = []
    for found in result["found"]:
        entry = registry.get(found["tech"])
        if entry and entry["kind"] == "service":
            kind = RANK_KINDS.get(entry["type"])
            services.append({"name": entry["name"], **({"kind": kind} if kind else {}),
                             **({"evidence": found["paths"][0]} if found["paths"] else {})})
    return {"services": services,
            "detail": {"ids": sorted(f["tech"] for f in result["found"]),
                       "not_in_registry": sorted(f["tech"] for f in result["found"] if f["tech"] not in registry),
                       "seconds": result["seconds"]}}
