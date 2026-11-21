"""Run the complete pipeline twice on one JavaScript snapshot: with Daodan's container switched off, or, with
`--container`, with the engine this machine has (the restore, the indexer and the tests then really run)."""
from __future__ import annotations

import atexit
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

CORE = Path(__file__).resolve().parents[2] / "daodan/core"
FIXTURE = Path(__file__).resolve().parents[1] / "project-model/fixtures/js-npm-single"
CALLS = {("premap", "derive"): "premaps_derived", ("entries", "_syntax"): "entry_ast_inventories",
         ("engine_pass", "_launch"): "indexer_launch_attempts", ("engine_pass", "index_stage"): "index_stages",
         ("container", "find_engine"): "engine_probes", ("container", "run_in_container"): "container_requests",
         ("container", "copy_perimeter"): "container_copies", ("preparation", "fetched"): "pinned_inputs_requested",
         ("engine_tools", "download"): "download_calls", ("snapshot", "write_snapshot"): "snapshots_written"}


def started(args) -> str:
    """The name of the program a `subprocess.Popen` audit event starts. Windows gives no executable and one
    command line: its first word, quoted or not (an audit hook must not raise on a line it cannot split)."""
    line = args[0] or (args[1] if isinstance(args[1], str) else args[1][0])
    if not args[0]:
        line = line[1:].partition('"')[0] if line.startswith('"') else (line.split(None, 1) or [""])[0]
    return Path(line).stem


def observe():
    """Install in every benchmark Python process, including the real out-of-process index stage."""
    root = os.environ["DAODAN_MEASURE_TARGET"] + os.sep
    counts = Counter(dict.fromkeys([*CALLS.values(), "source_opens", "source_listings", "tree_parses"], 0))
    processes, source_files = Counter(), Counter()

    def audit(event, args):
        if event == "subprocess.Popen":
            name = started(args)
            if name == "uv" and "--offline" in args[1]:
                name = "uv --offline"
            processes[name] += 1
        if event in ("open", "os.scandir", "os.listdir") and isinstance(args[0], str):
            path = os.path.abspath(args[0])
            if path.startswith(root) or path + os.sep == root:
                counts["source_opens" if event == "open" else "source_listings"] += 1
                if event == "open":
                    source_files[os.path.relpath(path, root)] += 1

    def profile(frame, event, value):
        if event == "call":
            key = CALLS.get((frame.f_globals.get("__name__"), frame.f_code.co_name))
            if key:
                counts[key] += 1
        elif event == "c_call" and getattr(value, "__name__", "") == "parse":
            if type(getattr(value, "__self__", None)).__module__ == "tree_sitter":
                counts["tree_parses"] += 1

    def finish():
        sys.setprofile(None)
        path = Path(os.environ["DAODAN_MEASURE_OUTPUT"]) / f"{os.getpid()}.json"
        path.write_text(json.dumps({"counts": counts, "processes": processes, "source_files": source_files}))

    sys.addaudithook(audit)
    sys.setprofile(profile)
    atexit.register(finish)


def measure(manifest, output):
    import pipeline
    import premap
    events = []
    result = pipeline.run(manifest, listeners=[events.append])
    assert list(result) == ["scan", "stack", "analyze", "dynamic", "union"]
    report = json.loads(premap.path(manifest).read_text())
    summary = {"events": [f"{e['step']}.{e['kind']}" for e in events if e["kind"].startswith("step.")],
               "gaps_by_step": Counter(e["step"] for e in events if e["kind"] == "gap"),
               "unrun_sources": [s["source"] for s in report["sources"] if s["state"] == "not_run"],
               "module_graph_action": result["scan"]["action"], "technologies": result["stack"]["technologies"],
               "analyze": result["analyze"]["languages"], "dynamic": result["dynamic"]["languages"],
               "union": result["union"]["languages"]}
    output.write_text(json.dumps(summary))


def main(container: bool = False):
    import shutil
    import snapshot
    with tempfile.TemporaryDirectory() as work:
        tmp = Path(work).resolve()
        target = tmp / "target"
        shutil.copytree(FIXTURE, target, ignore=shutil.ignore_patterns("expected.json"))
        manifest = tmp / "out/manifest.sqlite"
        snapshot.write_snapshot(target, manifest)
        # A trusted benchmark hook outside the project observes child Python processes, too.
        (tmp / "sitecustomize.py").write_text(
            f"import runpy; runpy.run_path({str(Path(__file__).resolve())!r})['observe']()\n")
        reports = []
        for n in (1, 2):
            folder = tmp / str(n)
            folder.mkdir()
            env = {**os.environ, "DAODAN_CONTAINER": "off", "DAODAN_MEASURE_TARGET": str(target),
                   "DAODAN_MEASURE_OUTPUT": str(folder),
                   "PYTHONPATH": os.pathsep.join([str(tmp), os.environ.get("PYTHONPATH", "")])}
            if container:
                del env["DAODAN_CONTAINER"]
            summary = tmp / f"pipeline-{n}.json"
            started = time.monotonic()
            subprocess.run([sys.executable, __file__, str(manifest), str(summary)], env=env,
                           stdout=sys.stderr, check=True)
            seconds = round(time.monotonic() - started, 1)
            counters, processes, sources = Counter(), Counter(), Counter()
            samples = list(folder.glob("*.json"))
            for sample in samples:
                data = json.loads(sample.read_text())
                counters.update(data["counts"])
                processes.update(data["processes"])
                sources.update(data["source_files"])
            reports.append({**json.loads(summary.read_text()), "seconds": seconds, "counts": counters,
                            "source_files_opened": sources, "subprocesses": processes,
                            "instrumented_python_processes": len(samples)})
        print(json.dumps({"fixture": FIXTURE.name, "runs": reports}, indent=2))


if __name__ == "__main__":
    sys.path.insert(0, str(CORE))
    if len(sys.argv) == 3:
        measure(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        main("--container" in sys.argv)
