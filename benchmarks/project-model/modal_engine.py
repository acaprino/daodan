"""The exploration through Daodan's own container code, on a real Docker daemon (plan task 11.2's open point).

`modal_explore.py` runs the app with `modal_pipeline.sandbox_run`, the Modal substitute of `container.run_in_container`.
This starts Docker's daemon (with its default networking) in a Modal VM Sandbox, as `modal_pipeline` does for the
services, and runs `dynamic.app.observe` there with `container.find_engine()`: the preparation with the registries,
`keep_root`, the execution with no network, the outputs fetched, as a Linux user with Docker gets them.
It is not the Windows path (Daodan's own engine in WSL, `container.own_engine`): that one stays on the owner's PC.

    python -m modal run benchmarks/project-model/modal_engine.py --out benchmarks/project-model/results/explore/engine.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DOCKER = "https://download.docker.com/linux/static/stable/x86_64/docker-29.10.0.tgz"
FIXTURE = HERE / "explore-fixtures" / "vite-react"

image = (modal.Image.debian_slim(python_version="3.13")
         .apt_install("ca-certificates", "curl", "iptables", "xz-utils", "procps", "git")
         .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
         .run_commands(f"curl -fsSL {DOCKER} -o /tmp/d.tgz && mkdir -p /opt/docker && "
                       "tar -xzf /tmp/d.tgz -C /opt/docker --strip-components=1")
         .add_local_dir(REPO / "daodan/core", "/daodan/map/core", copy=True, ignore=["**/__pycache__/**"])
         .add_local_dir(REPO / "daodan/data", "/daodan/map/data", copy=True)
         .add_local_dir(FIXTURE, "/work/project", copy=True, ignore=["**/node_modules/**"])
         .add_local_file(HERE / "engine_explore_driver.py", "/daodan/driver.py", copy=True))
app = modal.App("daodan-engine-explore", image=image)


@app.local_entrypoint()
def main(out: str = ""):
    boxes = modal.App.lookup("daodan-engine-explore-boxes", create_if_missing=True)
    box = modal.Sandbox.create(image=image, app=boxes, cpu=4, memory=16384, timeout=3600,
                               experimental_options={"vm_runtime": True})
    result = None
    try:
        box.exec("sh", "-c", "PATH=/opt/docker:$PATH nohup dockerd > /tmp/dockerd.log 2>&1 &")
        for _ in range(90):
            if box.exec("/opt/docker/docker", "info", timeout=30).wait() == 0:
                break
            time.sleep(1)
        process = box.exec("python", "/daodan/driver.py", timeout=3300)
        for line in process.stdout:
            print(line.rstrip()[:400], flush=True)
            if line.startswith("RESULT "):
                result = json.loads(line[len("RESULT "):])
        code = process.wait()
        print("driver exit", code, process.stderr.read()[-1500:], flush=True)
    finally:
        box.terminate()
    if out and result:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(result, indent=1), encoding="utf-8")
