"""rust-analyzer runs only in Daodan's container: the scip-rust stage on a probe crate, on Modal.

A crate whose build script sets a cfg and a procedural macro that generates a function, each writing a marker in
/tmp where it runs; cargo, rustc, rust-analyzer and rustup on the machine's PATH are shims that write one too. The
stage runs as the pipeline runs it, Daodan's container on Modal Sandboxes (`modal_pipeline.engine_on_modal`):

    modal run benchmarks/project-model/modal_rust_container.py::rust_container

Measured on 16 November 2026: on the machine no marker and no shim called, the project's files unchanged; in the
container's index the cfg-gated function resolves (the build script ran there) and the generated one is named (the
macro expanded there), defined in no file (`undefined-project-symbol`).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import modal_pipeline as mp

HERE = Path(__file__).resolve().parent
image = mp.image.add_local_file(HERE / "modal_pipeline.py", "/root/modal_pipeline.py")
app = mp.app


PROBE = {
    "Cargo.toml": '[package]\nname = "probe"\nversion = "0.1.0"\nedition = "2021"\nbuild = "build.rs"\n\n'
                  '[dependencies]\nprobe-macros = { path = "macros" }\n\n[workspace]\nmembers = ["macros"]\n',
    "build.rs": 'fn main() {\n    let _ = std::fs::write("/tmp/daodan-probe-build", "ran");\n'
                '    println!("cargo:rustc-check-cfg=cfg(from_build)");\n'
                '    println!("cargo:rustc-cfg=from_build");\n}\n',
    "src/lib.rs": "probe_macros::make!();\n\n#[cfg(from_build)]\npub fn gated() -> i32 {\n    1\n}\n\n"
                  "pub fn run() -> i32 {\n    gated() + generated()\n}\n",
    "macros/Cargo.toml": '[package]\nname = "probe-macros"\nversion = "0.1.0"\nedition = "2021"\n\n'
                         '[lib]\nproc-macro = true\n',
    "macros/src/lib.rs": "use proc_macro::TokenStream;\n\n#[proc_macro]\n"
                         "pub fn make(_input: TokenStream) -> TokenStream {\n"
                         '    let _ = std::fs::write("/tmp/daodan-probe-macro", "ran");\n'
                         '    "pub fn generated() -> i32 { 2 }".parse().unwrap()\n}\n'}
MARKERS = ("/tmp/daodan-probe-build", "/tmp/daodan-probe-macro", "/tmp/daodan-probe-host")


@app.function(image=image, cpu=(0.5, 8.0), memory=(2048, 16384), timeout=7200, volumes={"/results": mp.volume})
def probe() -> dict:
    """The scip-rust stage on a crate whose build script sets a cfg and a procedural macro that generates a function,
    each writing a marker in /tmp where it runs; cargo, rustc, rust-analyzer and rustup on this machine's PATH are
    shims that write one too."""
    import os
    sys.path[:0] = [mp.REMOTE_SCRIPTS, mp.REMOTE_PM]
    mp._engine()
    shims = Path("/tmp/daodan-shims")
    shims.mkdir(exist_ok=True)
    for name in ("cargo", "rustc", "rust-analyzer", "rustup"):
        (shims / name).write_text(f"#!/bin/sh\necho {name} >> /tmp/daodan-probe-host\nexit 1\n")
        (shims / name).chmod(0o755)
    os.environ["PATH"] = f"{shims}:{os.environ['PATH']}"
    for marker in MARKERS:
        Path(marker).unlink(missing_ok=True)
    project = Path("/cases/rust-probe")
    shutil.rmtree(project, ignore_errors=True)
    for rel, text in PROBE.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    import engine_pass
    import premap
    import resolve_edges
    import snapshot
    manifest = Path("/runs/rust-probe/manifest.sqlite")
    shutil.rmtree(manifest.parent, ignore_errors=True)
    snapshot.write_snapshot(project, manifest)
    record = premap.ensure(manifest)
    spec = next(item for item in engine_pass.ENGINES if item.name == "scip-rust")
    result = engine_pass.index_stage(spec, manifest, project)
    coverage = ((resolve_edges.edge_state(manifest).get("languages") or {}).get("rust") or {}).get("coverage") or {}
    return {"units": [(unit["kind"], unit["root"], unit.get("name")) for unit in record.get("units", [])],
            "stage": {key: result.get(key) for key in ("available", "engine", "reason", "gaps", "languages")},
            "sites": coverage.get("sites"), "answered": coverage.get("answered"), "holes": coverage.get("holes"),
            "host markers": [marker for marker in MARKERS if Path(marker).exists()],
            "host shims called": Path(MARKERS[2]).read_text() if Path(MARKERS[2]).exists() else "",
            "project files": sorted(path.relative_to(project).as_posix() for path in project.rglob("*")
                                    if path.is_file())}


@app.local_entrypoint()
def rust_container():
    print(json.dumps(probe.remote(), indent=1, default=str), flush=True)
