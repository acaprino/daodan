"""Three runs of the pipeline on one project, one after the other: from scratch, unchanged, and after one module
changed (task 2b of the plan of the unified analysis, spec of the pipeline 7.4).

The project is the fixture `mix-poly-firebase`: a React page with two buttons, a Tauri shell with a native command, and
Python functions of a backend. What a run costs is read from the events of the pipeline and from the records of its
containers (`score.py runs` of `benchmarks/system-map` puts the three side by side); beside it, the links that a person
expects there and that the run found (`EXPECTED`: the interface to its handler, the handler to the native command, the
handler to the backend).

Where this runs, the containers are Modal Sandboxes (`modal_pipeline.sandbox_run`), which share no volume from one
sandbox to the next: each step restores the Node dependencies for itself, as before the shared restore of the task 1b
(`node_preparation`). What this measures is that base, and what the pipeline reuses from one run to the next; the gain
of the shared restore is measured by a real engine, not here. The CPU, the peak of memory and the temporary space are
those of the sandboxes, which no event carries: they are not measured.

    python -m modal run benchmarks/project-model/modal_runs.py [--tag three-runs]

The result lands in `benchmarks/project-model/results/runs/<tag>/<run>/`. It is also written, run by run, on the
volume `daodan-flow-results` under `runs/<tag>/`, so that a client that loses its connection (`modal run --detach`) does
not lose it: `modal volume get daodan-flow-results runs/<tag> benchmarks/project-model/results/runs/`.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import modal_pipeline as mp

HERE = Path(__file__).resolve().parent
image = mp.image.add_local_file(HERE / "modal_pipeline.py", "/root/modal_pipeline.py")
app = mp.app

CASE = "mix-poly-firebase"
CHANGED = "react-app/src/checkout.ts"  # the one module the third run changes
RUNS = ("from-scratch", "unchanged", "one-module")
# What a person who knows the project expects to find, as (file, name or None) at each end: the buttons reach their
# handlers, the handler of the receipt invokes the native command, the handler of the checkout calls the backend.
EXPECTED = (
    {"what": "the Buy button reaches its handler", "from": ("react-app/src/App.tsx", None),
     "to": ("react-app/src/checkout.ts", "startCheckout")},
    {"what": "the Receipt button reaches its handler", "from": ("react-app/src/App.tsx", None),
     "to": ("react-app/src/checkout.ts", "saveReceipt")},
    {"what": "the receipt handler invokes the native command", "from": ("react-app/src/checkout.ts", "saveReceipt"),
     "to": ("react-app/src-tauri/src/lib.rs", "save_receipt")},
    {"what": "the checkout handler calls the Python backend", "from": ("react-app/src/checkout.ts", "startCheckout"),
     "to": ("functions-python/main.py", "create_checkout_session")},
)


def _at(symbol: str, place: tuple) -> bool:
    """Whether `symbol` (`file::name`) is `place`: that file, and that name, or any when `place` names none."""
    file, _, name = (symbol or "").partition("::")
    return file == place[0] and (place[1] is None or name == place[1] or name.endswith("." + place[1]))


def expected_links(edges: list[dict]) -> dict:
    """`{found, of, missing}`: the expected links (`EXPECTED`) that an edge of the links joins, whatever its type."""
    found = [item for item in EXPECTED
             if any(_at(edge["from"], item["from"]) and _at(edge["to"], item["to"]) for edge in edges)]
    return {"found": len(found), "of": len(EXPECTED),
            "missing": [item["what"] for item in EXPECTED if item not in found]}


def new_lines(before: dict[str, int], files: dict[str, list[str]]) -> list[str]:
    """The lines the files gained since `before` (their line counts), in order of file."""
    return [line for name in sorted(files) for line in files[name][before.get(name, 0):] if line.strip()]


def _records(root: Path) -> dict[str, list[str]]:
    return {str(path): path.read_text(encoding="utf-8").splitlines() for path in sorted(root.rglob("container-runs.jsonl"))}


def step_seconds(events: list[dict]) -> dict[str, float]:
    """Seconds from the start to the end of each step, from its events."""
    from datetime import datetime
    stamp = lambda event: datetime.strptime(event["at"], "%Y-%m-%dT%H:%M:%S.%fZ")  # noqa: E731
    started, seconds = {}, {}
    for event in events:
        if event["kind"] == "step.started":
            started[event["step"]] = stamp(event)
        elif event["kind"] in ("step.finished", "step.failed", "step.skipped") and event["step"] in started:
            seconds[event["step"]] = round((stamp(event) - started[event["step"]]).total_seconds(), 1)
    return seconds


def write_run(folder: Path, run: dict) -> None:
    """One run's files, as `score.py runs` reads them: its events, its container records, its links (none when they
    could not be read) and the rest of what it measured."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "pipeline-events.jsonl").write_text(run["events"], encoding="utf-8")
    (folder / "container-runs.jsonl").write_text(run["containers"] + "\n", encoding="utf-8")
    if "error" not in run["links"]:  # no file when the links could not be read: `score.py runs` says «non misurato»
        (folder / "links.json").write_text(json.dumps(run["links"]), encoding="utf-8")
    rest = {key: value for key, value in run.items() if key not in ("events", "containers")}
    (folder / "run.json").write_text(json.dumps(rest, indent=1), encoding="utf-8")


@app.function(image=image, cpu=(2.0, 16.0), memory=(4096, 32768), timeout=3 * 3600, volumes={"/results": mp.volume})
def three_runs(tag: str) -> dict:
    """The three runs, in this order, on one folder: each run's events, container records, expected links and times."""
    sys.path[:0] = [mp.REMOTE_SCRIPTS, mp.REMOTE_PM]
    mp._engine()
    import flows
    import pipeline
    import resolve_edges
    import snapshot
    from snapshot_store import open_snapshot
    project = mp._project(CASE)
    manifest = Path("/runs") / CASE / "manifest.sqlite"
    shutil.rmtree(manifest.parent, ignore_errors=True)
    snapshot.write_snapshot(project, manifest)
    journal, out = manifest.with_name("pipeline-events.jsonl"), {}
    for label in RUNS:
        if label == "one-module":  # as the refresh of a working run does: the pass cleared, the snapshot rewritten on the old
            resolve_edges.reset_pass(manifest)
            with (project / CHANGED).open("a", encoding="utf-8") as file:
                file.write("\n// one module changed for the measure\n")
            with open_snapshot(manifest) as base:
                snapshot.write_snapshot(project, manifest, previous=base)
        before = {name: len(lines) for name, lines in _records(manifest.parent).items()}
        offset = journal.stat().st_size if journal.is_file() else 0
        started, events = time.monotonic(), []
        try:
            steps = json.loads(json.dumps(pipeline.run(manifest, listeners=[events.append]), default=str))
        except Exception as error:  # noqa: BLE001 - a run that fails is a result: the next one still runs
            steps = {"error": f"{type(error).__name__}: {error}"}
        seconds = round(time.monotonic() - started, 1)
        try:
            links = expected_links(flows.link_facts(manifest, [])["edges"])
        except Exception as error:  # noqa: BLE001 - the links are read after the run; their failure is said
            links = {"error": f"{type(error).__name__}: {error}"}
        out[label] = {"seconds": seconds, "step_seconds": step_seconds(events), "steps": steps, "links": links,
                      "events": journal.read_bytes()[offset:].decode("utf-8") if journal.is_file() else "",
                      "containers": "\n".join(new_lines(before, _records(manifest.parent)))}
        write_run(Path("/results") / "runs" / tag / label, out[label])  # at once: the next run may take an hour
        mp.volume.commit()
    return out


@app.local_entrypoint()
def runs(tag: str = "three-runs"):
    answer = three_runs.remote(tag)
    root = HERE / "results" / "runs" / tag
    for label, run in answer.items():
        shutil.rmtree(root / label, ignore_errors=True)
        write_run(root / label, run)
        links = run["links"]
        print(label, run["seconds"], "s; links", links.get("found"), "of", links.get("of"), flush=True)
    print("->", root)
