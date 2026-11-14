"""scip-go: how the indexer runs. What its index states its own way is the plugin's `indexers/go.py`.

`index` runs scip-go over a copy of the checkout, at the root and once more in each nested module that holds
snapshot files the root run left out, with Go's ignored directories (`_x`, `.x`, `testdata`) named as
explicit packages.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph  # noqa: E402

VERSION = "v0.2.9"  # github.com/scip-code/scip-go, built with the Go release the engine pass pins
GO = Path(os.environ.get("DAODAN_GO_ROOT", "/opt/go"))
SCIP_GO = Path(os.environ.get("DAODAN_SCIP_GO", "/opt/scip/bin/scip-go"))


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    import resolve_edges as rx
    mirror = work_dir / "mirror-scip-go"
    if not mirror.exists():
        shutil.copytree(project_dir, mirror, symlinks=True)
    cache = rx.shared_cache_dir() / "go"
    env = dict(os.environ, GOROOT=str(GO), GOPATH=str(cache / "path"), GOCACHE=str(cache / "build"),
               GOTOOLCHAIN="local", GOFLAGS="-mod=readonly", GOTELEMETRY="off")
    env["PATH"] = f"{GO / 'bin'}{os.pathsep}{SCIP_GO.parent}{os.pathsep}{env.get('PATH', '')}"
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*.go"))
    roots = code_graph.manifest_dirs(mirror, "go.mod")

    def command(prefix, output):
        subprocess.run([str(GO / "bin/go"), "mod", "download"], cwd=mirror / prefix, env=env, capture_output=True,
                       timeout=1800)
        skip = len(prefix) + 1 if prefix else 0
        ignored = sorted({rel.rsplit("/", 1)[0][skip:] for rel in files
                          if "/" in rel and code_graph.owner(rel, roots) == prefix and any(
                              part.startswith(("_", ".")) or part == "testdata" for part in rel.split("/")[:-1])})
        return [str(SCIP_GO), f"--output={output}", "./...", *[f"./{directory}" for directory in ignored]]

    runs = code_graph.module_runs("scip-go", roots, command, files, mirror, work_dir, env)
    return {"indexes": [[run["index"], run["prefix"]] for run in runs if run["index"]], "runs": runs,
            "indexer": code_graph.indexer("scip-go", VERSION, runs)}
