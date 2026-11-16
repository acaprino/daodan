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
import os
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import confinement  # noqa: E402
import modules  # noqa: E402
import premap  # noqa: E402
import service_registry  # noqa: E402
from snapshot_store import logical_digest, open_snapshot  # noqa: E402

SCHEMA, FILE = "daodan/technologies/v1", "technologies.json"


def path(manifest: Path) -> Path:
    return Path(manifest).with_name(FILE)


def _inputs(manifest: Path, registry: dict, facts: dict) -> tuple[str, str, str]:
    """The digest of what the record is derived from, and the snapshot's root and target."""
    with open_snapshot(manifest) as store:
        root, target = store["root"], store.get("target") or "."
        value = [logical_digest(store), root, registry.get("versions"), SCHEMA, facts.get("services"),
                 facts.get("excluded")]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest(), root, target


def derive(manifest: Path, registry: dict, facts: dict) -> dict:
    """The record of `manifest` from the registry and the pre-map's `facts`."""
    entries = [{k: v for k, v in e.items() if k != "source"}
               for e in service_registry.recognize(manifest, registry, facts)]
    graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
    units = []
    for unit in graph["modules"]:
        if unit["provenance"] == "build":
            files = set(unit.get("files", []))
            units.append({"id": unit["id"], "name": unit["name"], "kind": unit["kind"], "paths": unit["paths"],
                          "technologies": [e["id"] for e in entries if any(s["path"] in files for s in e["signs"])]})
    digest, root, target = _inputs(manifest, registry, facts)
    return {"schema": SCHEMA, "manifest": manifest.as_posix(), "root": root, "target": target,
            "inputs_digest": digest, "technologies": entries, "units": units}


def _read(manifest: Path, digest: str) -> dict | None:
    try:
        record = json.loads(path(manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return record if record.get("schema") == SCHEMA and record.get("inputs_digest") == digest else None


def state(manifest: Path) -> str:
    """fresh, stale or missing."""
    manifest = Path(manifest).resolve()
    if not path(manifest).is_file():
        return "missing"
    digest = _inputs(manifest, service_registry.load(), premap.ensure(manifest))[0]
    return "fresh" if _read(manifest, digest) else "stale"


def ensure(manifest: Path) -> dict:
    """The record of `manifest`, derived and written again when it is not fresh."""
    manifest = Path(manifest).resolve()
    registry, facts = service_registry.load(), premap.ensure(manifest)
    record = _read(manifest, _inputs(manifest, registry, facts)[0])
    if record is None:
        target = path(manifest)
        confinement.reject_link_chain(target)
        record = derive(manifest, registry, facts)
        descriptor, name = tempfile.mkstemp(prefix=".technologies-", dir=target.parent)  # one per writer
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(json.dumps(record, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        os.replace(name, target)
    return record
