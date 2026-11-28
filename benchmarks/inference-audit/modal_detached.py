"""The detached pass on Daodan's own code, eight times, and the Python `self.m()` calls its store leaves without an
edge (plan T2.B.18). No model.

The only source of the defect is the note of `3b856ab` (17 November): a detached pass that ran about six minutes and
ended without a store, once in four, and 154 `self.m()` calls without an edge. Each run is a container of its own:
Daodan's code (`daodan/`, tests left out, as the image carries it) copied, its snapshot written without the pass
(`snapshot.py write --no-engine --no-index`), then `engine_pass.ensure_edges`, the detached child the product
starts (`-X faulthandler`, its log beside the snapshot), polled until it is no longer `running` or `LIMIT` seconds
passed. An analyzer that builds in a container runs in the pipeline benchmark's Modal Sandbox
(`modal_pipeline._engine`), in this process and in the pass's.

Per run: the final state of the pass and of each language, the seconds, whether the store exists, the log's tail
when the pass did not end fresh, and the Python calls `self.m()` (the snapshot's own references, `kind` call, whose
parts are `self` and one name) with an edge, a hole by class, or no row in the store.

    modal deploy benchmarks/inference-audit/modal_detached.py
    python benchmarks/inference-audit/modal_detached.py spawn
    python benchmarks/inference-audit/modal_detached.py fetch

`fetch` writes `results/detached-pass.json`: the eight runs and their sum.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
PLUGIN = HERE.parents[1] / "daodan" if LOCAL else Path("/daodan/map")
SCRIPTS = str(PLUGIN / "core")
RESULTS = HERE / "results"
TAG = "inference-audit"
STORE = f"{TAG}/detached"
PIPELINE = HERE.parents[1] / "benchmarks/project-model/modal_pipeline.py" if LOCAL else Path("/pm/modal_pipeline.py")
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
import plugin_scripts  # noqa: E402

RUNS = 8
LIMIT = 1800  # seconds: the note's pass stopped at about six minutes


def _image():
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "ca-certificates", "xz-utils")
        # the plugin's requirements, all of them: a stage runs under uv over this interpreter's packages
        .pip_install("uv").pip_install_from_requirements(str(PLUGIN / "core/requirements.txt"))
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(PIPELINE, "/pm/modal_pipeline.py")
        .add_local_file(HERE / "plugin_scripts.py" if LOCAL else Path("/audit/plugin_scripts.py"),
                        "/audit/plugin_scripts.py")
    )


app = modal.App("daodan-detached-pass", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def self_calls(manifest: Path, store: Path) -> dict:
    """The Python calls `self.m()` of the snapshot with an edge, a hole by class, or no row in the store."""
    import sqlite3
    from snapshot_store import _unpack
    snapshot = sqlite3.connect(manifest)
    try:
        python = {file for file, in snapshot.execute("SELECT file FROM sem_coverage WHERE language='python'")}
        calls = [(identity, file, l0) for identity, file, l0, payload in snapshot.execute(
            "SELECT id, file, l0, payload FROM sem_references WHERE kind='call'")
            if file in python and (_unpack(payload).get("parts") or [])[:1] == ["self"]
            and len(_unpack(payload)["parts"]) == 2]
    finally:
        snapshot.close()
    edges, holes = set(), {}
    if store.is_file():
        connection = sqlite3.connect(store)
        try:
            edges = {identity for identity, in connection.execute("SELECT reference_id FROM edges")}
            holes = dict(connection.execute("SELECT reference_id, class FROM holes"))
        finally:
            connection.close()
    out = collections.Counter()
    unbound = []
    for identity, file, l0 in calls:
        verdict = "edge" if identity in edges else f"hole {holes[identity]}" if identity in holes else "no row"
        out[verdict] += 1
        if verdict != "edge" and len(unbound) < 20:
            unbound.append(f"{file}:{l0} {verdict}")
    return {"calls": len(calls), "by_verdict": dict(sorted(out.items())), "without_edge_examples": unbound}


@app.function(cpu=4, memory=12288, timeout=LIMIT + 900, volumes={"/results": volume})
def detached(number: int) -> dict:
    import shutil
    import subprocess
    import time
    sys.path.insert(0, "/pm")
    import modal_pipeline
    modal_pipeline._engine()
    import engine_pass
    started = time.time()
    work = Path("/work") / f"run-{number}"
    shutil.rmtree(work, ignore_errors=True)
    project = work / "daodan"
    shutil.copytree(PLUGIN, project, ignore=shutil.ignore_patterns("__pycache__"))
    manifest = work / "snapshot/manifest.sqlite"
    subprocess.run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(project), "--out", str(manifest),
                    "--no-engine", "--no-index"], check=True)
    snapshot_seconds = round(time.time() - started, 1)
    begun = time.time()
    first = engine_pass.ensure_edges(manifest)
    state = first
    while state["state"] == "running" and time.time() - begun < LIMIT:
        time.sleep(5)
        state = engine_pass.edge_state(manifest)
    seconds = round(time.time() - begun, 1)
    store = engine_pass.default_edge_store(manifest)
    log = manifest.with_name(engine_pass.LOG_NAME)
    result = {"run": number, "code": plugin_scripts.code_sha256(), "snapshot_seconds": snapshot_seconds,
              "action": first.get("action"), "state": state["state"], "seconds": seconds,
              "timed_out": state["state"] == "running",
              "languages": {language: {key: value for key, value in entry.items() if key in ("state", "reason")}
                            for language, entry in (state.get("languages") or {}).items()},
              "store": store.is_file()}
    if state["state"] != "fresh" and log.is_file():
        result["log_tail"] = log.read_text(encoding="utf-8", errors="replace")[-6000:]
    if state["state"] == "running":
        engine_pass.stop_pass(manifest, "the benchmark's limit")
    out = Path("/results") / STORE / f"{number}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.make_archive(str(out.with_suffix("")), "gztar", manifest.parent)  # snapshot, store, log: read again later
    result["self_calls"] = self_calls(manifest, store)
    out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    volume.commit()
    return {key: result[key] for key in ("run", "state", "seconds", "store")}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch"))
    args = parser.parse_args()
    if args.command == "spawn":
        print("local code", plugin_scripts.code_sha256())
        function = modal.Function.from_name("daodan-detached-pass", "detached")
        for number in range(RUNS):
            print(number, function.spawn(number).object_id)
    else:
        runs = []
        for number in range(RUNS):
            try:
                runs.append(json.loads(b"".join(volume.read_file(f"{STORE}/{number}.json"))))
            except Exception as error:  # noqa: BLE001 - a run still going or lost is said, not fatal
                print(number, "not on the volume:", type(error).__name__)
        summary = {"runs": len(runs), "fresh": sum(run["state"] == "fresh" for run in runs),
                   "without_store": sum(not run["store"] for run in runs),
                   "timed_out": sum(run["timed_out"] for run in runs),
                   "seconds": sorted(run["seconds"] for run in runs),
                   "codes": sorted({json.dumps(run["code"], sort_keys=True) for run in runs}),
                   "self_calls": sorted({json.dumps(run["self_calls"]["by_verdict"], sort_keys=True) for run in runs})}
        path = RESULTS / "detached-pass.json"
        path.write_text(json.dumps({"summary": summary, "runs": runs}, indent=1) + "\n", encoding="utf-8",
                        newline="\n")
        print(path, json.dumps(summary))
