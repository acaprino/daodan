"""rust-analyzer's SCIP output: how the indexer runs. What its index states its own way is the plugin's
`indexers/rust.py`.

`index` runs `rust-analyzer scip` over a copy of the checkout with the engine pass's options (all features,
no build script, no procedural macro), at the root and once more in each crate directory that holds snapshot
files the root run left out.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph  # noqa: E402

RUST_ANALYZER = Path(os.environ.get("DAODAN_RUST_ANALYZER", "/opt/scip/bin/rust-analyzer"))
# The engine pass's own rust-analyzer options: all features, no build script, no procedural macro.
CONFIG = {"cargo": {"buildScripts": {"enable": False}, "features": "all"}, "procMacro": {"enable": False}}


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    import resolve_edges as rx
    mirror = work_dir / "mirror-rust-analyzer"
    if not mirror.exists():
        shutil.copytree(project_dir, mirror, symlinks=True)
    toolchain = rx.rust_toolchain()
    env = dict(os.environ, CARGO_HOME=str(rx.shared_cache_dir() / "cargo"), CARGO_TARGET_DIR=str(work_dir / "rust-target"))
    if toolchain is not None:
        env["PATH"] = f"{toolchain / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    version = subprocess.run([str(RUST_ANALYZER), "--version"], env=env, capture_output=True, text=True).stdout.strip()
    config = work_dir / "rust-analyzer.json"
    config.write_text(json.dumps(CONFIG), encoding="utf-8")
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*.rs")
                       if "target" not in path.parts)

    def command(prefix, output):
        return [str(RUST_ANALYZER), "scip", ".", "--output", str(output), "--config-path", str(config)]

    runs = code_graph.module_runs("rust-analyzer", code_graph.manifest_dirs(mirror, "Cargo.toml"), command, files,
                                  mirror, work_dir, env, fallback=lambda prefix, output: command(prefix, output)[:-2])
    return {"indexes": [[run["index"], run["prefix"]] for run in runs if run["index"]], "runs": runs,
            "indexer": code_graph.indexer("rust-analyzer", version, runs), "toolchain": rx.RUST_VERSION,
            "config": CONFIG}
