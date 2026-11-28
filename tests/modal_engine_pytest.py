"""The tests that need a container engine (`DAODAN_<NAME>_SMOKE=1`), on Modal: pytest over the checkout in a VM
Sandbox with Docker's daemon, as `benchmarks/egress/modal_probe.py` runs Daodan's container code there.
`tests/modal_pytest.py` has no engine, and those tests skip there.

    modal run tests/modal_engine_pytest.py --smoke CLANG --args "tests/test_codebase_map_indexers_clang.py -k smoke -q"

Daodan's runs go through `container.find_engine()`: the preparation behind Daodan's proxy on its internal network,
the execution with no network, as a Linux user with Docker gets them. The output is streamed; the exit code is
pytest's.
"""
from __future__ import annotations

import shlex
import time
from pathlib import Path

import modal

REPO = Path(__file__).resolve().parents[1]
DOCKER = "https://download.docker.com/linux/static/stable/x86_64/docker-29.10.0.tgz"
REMOTE = "/repo"

image = (modal.Image.debian_slim(python_version="3.13")
         .apt_install("ca-certificates", "curl", "iptables", "xz-utils", "procps", "git")
         .pip_install("pytest", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6",
                      "protobuf==7.36.2", "pip-requirements-parser==32.0.1", "jsonpointer==3.0.0")
         .run_commands(f"curl -fsSL {DOCKER} -o /tmp/d.tgz && mkdir -p /opt/docker && "
                       "tar -xzf /tmp/d.tgz -C /opt/docker --strip-components=1"))
if (REPO / "AGENTS.md").is_file():
    for folder in ("daodan", "tests"):
        image = image.add_local_dir(REPO / folder, f"{REMOTE}/{folder}", copy=True,
                                    ignore=["**/__pycache__/**", "**/node_modules/**", "**/.pytest_cache/**"])
app = modal.App("daodan-engine-tests", image=image)


@app.local_entrypoint()
def main(args: str, smoke: str):
    boxes = modal.App.lookup("daodan-engine-tests-boxes", create_if_missing=True)
    box = modal.Sandbox.create(image=image, app=boxes, cpu=4, memory=16384, timeout=3600, runtime="vm")
    try:
        box.exec("sh", "-c", "PATH=/opt/docker:$PATH nohup dockerd > /tmp/dockerd.log 2>&1 &")
        for _ in range(90):
            if box.exec("/opt/docker/docker", "info", timeout=30).wait() == 0:
                break
            time.sleep(1)
        command = ["python", "-B", "-m", "pytest", "-p", "no:cacheprovider", "-s", *shlex.split(args)]
        print("$", shlex.join(command), flush=True)
        process = box.exec("env", f"DAODAN_{smoke.upper()}_SMOKE=1", "PATH=/opt/docker:/usr/local/bin:/usr/bin:/bin",
                           *command, workdir=REMOTE, timeout=3300)
        for line in process.stdout:
            print(line.rstrip(), flush=True)
        code = process.wait()
        print(process.stderr.read()[-3000:], flush=True)
    finally:
        box.terminate()
    if code:
        raise SystemExit(code)
