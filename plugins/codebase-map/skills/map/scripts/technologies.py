#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""The project's technologies, per build unit: frameworks, libraries, tools and services. The pipeline's `stack` step.

Two sources joined by id: the registry's signs (`service_registry.recognize`, the pre-map's services among them)
and stack-analyser run on the project (`stack_analyser.run`), which needs Node and, once, the network: without
`tool` it is `not_run`. `technologies.json` (`daodan/technologies/v1`) sits beside the manifest and is derived
again when the snapshot, the registry, the pre-map's services or the tool's version changed, or when the tool is
asked and has not answered yet. A unit holds a technology with a sign in a file the unit owns.
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
import stack_analyser  # noqa: E402
from snapshot_store import logical_digest, open_snapshot  # noqa: E402

SCHEMA, FILE = "daodan/technologies/v1", "technologies.json"


def path(manifest: Path) -> Path:
    return Path(manifest).with_name(FILE)


def _inputs(manifest: Path, registry: dict) -> str:
    with open_snapshot(manifest) as store:
        value = [logical_digest(store), store["root"], registry.get("versions"), stack_analyser.VERSION, SCHEMA,
                 premap.ensure(manifest).get("services")]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _tool(manifest: Path) -> dict:
    """stack-analyser on the snapshot's target; its paths count from the target, the snapshot's from the root."""
    from embedding_worker import shared_cache_dir
    with open_snapshot(manifest) as store:
        target = store.get("target") or "."
        root, files = Path(store["root"]) / target, sorted(dict(store.iter_file_headers_only()))
    prefix = "" if target in ("", ".") else target.strip("/") + "/"
    answer = stack_analyser.run(root, shared_cache_dir() / "stack-analyser",
                                {f[len(prefix):] for f in files if f.startswith(prefix)})
    return {**answer, "found": [{**f, "paths": [prefix + p for p in f["paths"]]} for f in answer.get("found", [])]}


def derive(manifest: Path, tool: bool = False) -> dict:
    manifest = Path(manifest).resolve()
    registry = service_registry.load()
    known = {e["id"]: e for e in registry["entries"]}
    found = {e["id"]: {**{k: v for k, v in e.items() if k != "source"}, "from": ["registry"]}
             for e in service_registry.recognize(manifest, registry)}
    answer = _tool(manifest) if tool else {"status": "not_run"}
    for seen in answer.pop("found", []):
        entry = found.setdefault(seen["tech"], {
            "id": seen["tech"], **{k: known.get(seen["tech"], {}).get(k) for k in ("name", "kind", "type", "site", "icon")},
            "from": [], "signs": []})
        entry["name"] = entry["name"] or seen["tech"]
        entry["from"].append("stack-analyser")
        entry["signs"] += [{"sign": "stack-analyser", "value": seen["tech"], "path": p, "line": None} for p in seen["paths"]]
    entries = [found[ident] for ident in sorted(found)]
    graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
    units = []
    for unit in graph["modules"]:
        if unit["provenance"] == "build":
            files = set(unit.get("files", []))
            units.append({"id": unit["id"], "name": unit["name"], "kind": unit["kind"], "paths": unit["paths"],
                          "technologies": [e["id"] for e in entries if any(s["path"] in files for s in e["signs"])]})
    return {"schema": SCHEMA, "manifest": manifest.as_posix(), "inputs_digest": _inputs(manifest, registry),
            "stack_analyser": answer, "technologies": entries, "units": units}


def state(manifest: Path, tool: bool = False) -> str:
    """fresh, stale or missing; with `tool`, a record stack-analyser has not answered is stale."""
    try:
        record = json.loads(path(manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "missing"
    if record.get("schema") != SCHEMA or record.get("inputs_digest") != _inputs(manifest, service_registry.load()):
        return "stale"
    return "stale" if tool and record["stack_analyser"].get("status") != "ok" else "fresh"


def ensure(manifest: Path, tool: bool = False) -> dict:
    """The record of `manifest`, derived and written again when it is not fresh."""
    manifest = Path(manifest).resolve()
    if state(manifest, tool) != "fresh":
        temporary = path(manifest).with_name("." + FILE)
        temporary.write_text(json.dumps(derive(manifest, tool), indent=1, ensure_ascii=False, sort_keys=True),
                             encoding="utf-8", newline="\n")
        temporary.replace(path(manifest))
    return json.loads(path(manifest).read_text(encoding="utf-8"))
