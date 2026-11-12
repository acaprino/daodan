"""Dynamic step on Modal: tududi's Jest suite in parallel shards under dynamic_record.js.

    modal run --detach benchmarks/call-provenance/modal_dynamic.py --shards 12 --out <dir> --tag <name>

Each shard runs in a container of its own with its own Postgres and the network blocked.
The image holds the commit's archive and its `npm ci`, built once. Writes into <dir> the
observed-<shard>-<pid>.json files of the recorder, jest-<shard>.log and run.log, with
one line per shard and the wall time of the whole run. Each shard also keeps its files
on the volume daodan-flow-results, under dynamic/<tag>/, so a local failure loses nothing.
"""
from __future__ import annotations

import time
from pathlib import Path

import modal

COMMIT = "71da9d7b34dfd1600657e9c5ddf40420206fd263"
HERE = Path(__file__).resolve().parent

image = (
    modal.Image.from_registry("node:22-bookworm", add_python="3.12")
    .apt_install("postgresql")
    .run_commands(
        f"mkdir -p /work/src && curl -sSL https://github.com/chrisvel/tududi/archive/{COMMIT}.tar.gz"
        " | tar -xz --strip-components=1 -C /work/src",
        "cd /work/src && npm ci --no-audit --no-fund",
    )
    .add_local_file(HERE / "dynamic_record.js", "/tool/dynamic_record.js")
    .add_local_file(HERE / "dynamic_tests.sh", "/tool/dynamic_tests.sh")
)
app = modal.App("daodan-dynamic-step", image=image)
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


@app.function(cpu=2, memory=4096, timeout=3600, block_network=True, volumes={"/results": volume})
def shard(index: int, total: int, tag: str) -> dict:
    import os
    import subprocess

    subprocess.run("service postgresql start", shell=True, check=True, capture_output=True)
    subprocess.run(["su", "postgres", "-c", "psql -q -c \"CREATE ROLE tududi LOGIN SUPERUSER PASSWORD 'tududi'\""],
                   check=True, capture_output=True)
    env = dict(os.environ, NODE_ENV="test", DYN_ONLY=str(index),
               DATABASE_URL="postgres://tududi:tududi@localhost:5432/tududi_test")
    started = time.time()
    subprocess.run(["sh", "/tool/dynamic_tests.sh", "/work/src", "backend", "/out", str(total), "exact"], env=env)
    out = Path("/out")
    files = {path.name: path.read_text(encoding="utf-8") for path in out.glob("observed-*.json")}
    files[f"jest-{index}.log"] = (out / f"jest-{index}.log").read_text(encoding="utf-8", errors="replace")
    log = (out / "run.log").read_text(encoding="utf-8").splitlines()
    line = next((entry for entry in log if entry.startswith("shard")), f"shard {index}/{total} no log line")
    kept = Path("/results/dynamic") / tag
    kept.mkdir(parents=True, exist_ok=True)
    for name, text in {**files, f"run-{index}.log": line + "\n"}.items():
        (kept / name).write_text(text, encoding="utf-8")
    volume.commit()
    return {"index": index, "seconds": round(time.time() - started), "files": files, "log": line}


@app.local_entrypoint()
def main(shards: int = 12, out: str = "modal-dynamic", tag: str = "exact"):
    target = Path(out)
    target.mkdir(parents=True, exist_ok=True)
    started = time.time()
    lines = []
    for result in shard.starmap([(i, shards, tag) for i in range(1, shards + 1)], return_exceptions=True):
        if isinstance(result, BaseException):
            lines.append(f"error {result!r}")
            continue
        try:
            for name, text in result["files"].items():
                (target / name).write_text(text, encoding="utf-8")
        except OSError as error:
            lines.append(f"local write failed, files kept on the volume: {error}")
        lines.append(f"{result['log']} container_seconds={result['seconds']} at_seconds={round(time.time() - started)}")
    lines.append(f"done wall_seconds={round(time.time() - started)}")
    (target / "run.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
