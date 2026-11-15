"""Baseline: Daodan's own module reader (`modules.py`, provenance `build`), read as it is.

`snapshot.py write <fixture> --no-engine --no-index` builds the snapshot and `modules.json` beside it, as the
plugin does; the build modules are converted to the shared shape. modules.py gives unit roots, names, the
manifests, workspace registrations, declared edges between units and the names (no versions, no scope) of
external dependencies; it reads no toolchain, no source root and no indexer configuration. The conversion
is the product's (`premap/module_graph.py`): nothing is converted here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import native_common as common

VERSION = "modules.py of the checkout (daodan/module-graph/v1)"
COMMAND = "snapshot.py write <fixture> --out <work>/manifest.sqlite --no-engine --no-index; modules.json"
SCRIPTS = next((p / "plugins/codebase-map/skills/map/scripts" for p in Path(__file__).resolve().parents
                if (p / "plugins/codebase-map/skills/map/scripts").is_dir()), Path("/daodan/map/scripts"))
LAST: dict = {}


def convert(graph: dict) -> dict:
    """The graph in the shared shape: the pre-map's own conversion (`premap/module_graph.py`), with the workspace
    as the schema writes it (one entry, a list of several, or none)."""
    sys.path.insert(0, str(SCRIPTS))
    from premap import module_graph
    facts = module_graph.facts(graph)
    workspaces = facts["workspace"]
    return {"units": facts["units"], "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
            "dependencies": facts["dependencies"]}


def run(fixture_dir, work_dir) -> dict:
    work = Path(work_dir)
    manifest = work / "daodan" / "manifest.sqlite"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    done = common.run([sys.executable, "-I", str(SCRIPTS / "snapshot.py"), "write", str(fixture_dir), "--out",
                       str(manifest), "--no-engine", "--no-index"], SCRIPTS, name="snapshot.py write (modules.py)")
    graph_file = manifest.with_name("modules.json")
    LAST.clear()
    LAST.update(rc=done.returncode, stderr=done.stderr[-1500:])
    if not graph_file.is_file():
        raise RuntimeError(f"snapshot.py write exit {done.returncode}: {done.stderr[-600:]}")
    graph = json.loads(graph_file.read_text(encoding="utf-8"))
    LAST["gaps"] = graph.get("gaps", [])[:20]
    return convert(graph)
