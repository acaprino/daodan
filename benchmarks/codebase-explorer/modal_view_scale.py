"""`view_scale.py` on Modal: the app's view from 80,000 entities, on a fixed machine, no model.

    modal run benchmarks/codebase-explorer/modal_view_scale.py [--reps 5]

The container holds the `daodan` folder of this checkout and the two scripts; it prints the measure as JSON
(README, «Vista dal servizio»).
"""
from __future__ import annotations

import json
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
CPU, MEMORY = 2.0, 4096  # the function's cores and megabytes (request = limit)

image = modal.Image.debian_slim(python_version="3.13")
if modal.is_local():
    ROOT = HERE.parents[1]
    image = (image.pip_install_from_pyproject(str(ROOT / "pyproject.toml"))
             .add_local_dir(ROOT / "daodan", "/daodan/daodan", ignore=["**/__pycache__/**"])
             .add_local_file(HERE / "scale.py", "/daodan/benchmarks/codebase-explorer/scale.py")
             .add_local_file(HERE / "view_scale.py", "/daodan/benchmarks/codebase-explorer/view_scale.py"))
app = modal.App("daodan-view-scale", image=image)


@app.function(cpu=(CPU, CPU), memory=(MEMORY, MEMORY), timeout=1800)
def run(reps: int) -> dict:
    import sys
    sys.path.insert(0, "/daodan/benchmarks/codebase-explorer")
    import view_scale
    return view_scale.measure(reps)


@app.local_entrypoint()
def main(reps: int = 5) -> None:
    print(json.dumps(run.remote(reps), ensure_ascii=False, indent=1))
