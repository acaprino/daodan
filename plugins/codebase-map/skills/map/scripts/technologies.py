#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""The project's technologies, per build unit: frameworks, libraries, tools and services. The pipeline's `stack` step.

The registry's signs (`service_registry.recognize`, the pre-map's services among them), with no tool run on the
project. `technologies.json` (`daodan/technologies/v1`) sits beside the manifest and is derived again when the
snapshot, the registry or the pre-map's services changed. A unit holds a technology with a sign in a file the
unit owns.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import modules  # noqa: E402
import premap  # noqa: E402
import service_registry  # noqa: E402
from snapshot_store import logical_digest, open_snapshot  # noqa: E402

SCHEMA, FILE = "daodan/technologies/v1", "technologies.json"


def path(manifest: Path) -> Path:
    return Path(manifest).with_name(FILE)


def _inputs(manifest: Path, registry: dict) -> str:
    with open_snapshot(manifest) as store:
        value = [logical_digest(store), store["root"], registry.get("versions"), SCHEMA,
                 premap.ensure(manifest).get("services")]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def derive(manifest: Path) -> dict:
    manifest = Path(manifest).resolve()
    registry = service_registry.load()
    entries = [{k: v for k, v in e.items() if k != "source"} for e in service_registry.recognize(manifest, registry)]
    graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
    units = []
    for unit in graph["modules"]:
        if unit["provenance"] == "build":
            files = set(unit.get("files", []))
            units.append({"id": unit["id"], "name": unit["name"], "kind": unit["kind"], "paths": unit["paths"],
                          "technologies": [e["id"] for e in entries if any(s["path"] in files for s in e["signs"])]})
    return {"schema": SCHEMA, "manifest": manifest.as_posix(), "inputs_digest": _inputs(manifest, registry),
            "technologies": entries, "units": units}


def state(manifest: Path) -> str:
    """fresh, stale or missing."""
    try:
        record = json.loads(path(manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "missing"
    fresh = record.get("schema") == SCHEMA and record.get("inputs_digest") == _inputs(manifest, service_registry.load())
    return "fresh" if fresh else "stale"


def ensure(manifest: Path) -> dict:
    """The record of `manifest`, derived and written again when it is not fresh."""
    manifest = Path(manifest).resolve()
    if state(manifest) != "fresh":
        temporary = path(manifest).with_name("." + FILE)
        temporary.write_text(json.dumps(derive(manifest), indent=1, ensure_ascii=False, sort_keys=True),
                             encoding="utf-8", newline="\n")
        temporary.replace(path(manifest))
    return json.loads(path(manifest).read_text(encoding="utf-8"))
