"""The go command and scip-go run only in Daodan's container: the scip-go stage on a probe module, on Modal.

A module whose go.mod names a toolchain newer than Daodan's Go and whose package imports "C". On the machine,
`go`, a Go of that toolchain's name, `scip-go` and the C compilers on the PATH, and Daodan's own Go where a host
run found it, are shims that write a marker; `git` is a shim that records its arguments, then runs git. The stage
runs as the pipeline runs it, Daodan's container on Modal Sandboxes (`modal_pipeline.engine_on_modal`):

    modal run benchmarks/project-model/modal_go_container.py::go_container
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
    "go.mod": "module example.com/probe\n\ngo 1.22\n\ntoolchain go1.99.0\n",
    "main.go": 'package main\n\n/*\n#cgo CFLAGS: -DPROBE=1\nint one(void) { return PROBE; }\n*/\nimport "C"\n\n'
               "func main() { println(int(C.one()) + twice(1)) }\n",
    "plain.go": "package main\n\nfunc twice(n int) int { return double(n) }\n\n"
                "func double(n int) int { return n * 2 }\n"}
HOST, GIT = "/tmp/daodan-probe-host", "/tmp/daodan-probe-git"


@app.function(image=image, cpu=(0.5, 8.0), memory=(2048, 16384), timeout=7200, volumes={"/results": mp.volume})
def probe() -> dict:
    """The scip-go stage on the probe module, with the shims on this machine."""
    import os
    sys.path[:0] = [mp.REMOTE_SCRIPTS, mp.REMOTE_PM]
    mp._engine()
    import engine_pass
    import engine_tools
    import premap
    import resolve_edges
    import snapshot
    shims, git = Path("/tmp/daodan-shims"), shutil.which("git")
    own = engine_tools.shared_engine_dir("go") / engine_tools.GO_VERSION / "go" / "bin" / "go"
    for path in (*(shims / name for name in ("go", "go1.99.0", "scip-go", "gcc", "cc", "clang")), own):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'#!/bin/sh\necho "$0 $*" >> {HOST}\nexit 1\n')
        path.chmod(0o755)
    (shims / "git").write_text(f'#!/bin/sh\necho "$*" >> {GIT}\nexec {git} "$@"\n')
    (shims / "git").chmod(0o755)
    os.environ["PATH"] = f"{shims}:{os.environ['PATH']}"
    for marker in (HOST, GIT):
        Path(marker).unlink(missing_ok=True)
    project = Path("/cases/go-probe")
    shutil.rmtree(project, ignore_errors=True)
    for rel, text in PROBE.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    manifest = Path("/runs/go-probe/manifest.sqlite")
    shutil.rmtree(manifest.parent, ignore_errors=True)
    snapshot.read_project(project, manifest)
    record = premap.ensure(manifest)
    spec = next(item for item in engine_pass.ENGINES if item.name == "scip-go")
    result = engine_pass.index_stage(spec, manifest, project)
    coverage = ((resolve_edges.edge_state(manifest).get("languages") or {}).get("go") or {}).get("coverage") or {}
    said = {marker: Path(marker).read_text().splitlines() if Path(marker).exists() else [] for marker in (HOST, GIT)}
    return {"units": [(unit["kind"], unit["root"], unit.get("name")) for unit in record.get("units", [])],
            "toolchains": record.get("toolchains"), "needs container": spec.needs_container,
            "stage": {key: result.get(key) for key in ("available", "engine", "reason", "gaps", "languages")},
            "sites": coverage.get("sites"), "answered": coverage.get("answered"), "holes": coverage.get("holes"),
            "files": coverage.get("files"), "host shims called": said[HOST],
            "git on the machine": sorted(set(said[GIT])),
            "project files": sorted(path.relative_to(project).as_posix() for path in project.rglob("*")
                                    if path.is_file())}


@app.local_entrypoint()
def go_container():
    print(json.dumps(probe.remote(), indent=1, default=str), flush=True)
