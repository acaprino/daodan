"""The exploration of a running app, on Modal (plan task 11.5): the dynamic step (`dynamic.run`, as the pipeline runs it)
starts the project's app in the pipeline's sandboxes, opens a headless browser on it and presses each control once; what
it finds is compared with the static reader's candidates and links of an analysis made earlier.

Nothing of the project runs on this PC. The source and the earlier analysis are folders of the volume
`daodan-flow-results` (the analysis' `manifest.sqlite`, `engine-edges.sqlite` and the files beside them):

    modal run benchmarks/project-model/modal_explore.py::explore_main --source possible-in/phazly3-src \
        --analysis possible-in/phazly5 --out benchmarks/project-model/results/explore/phazly.json

What is measured (README, «Esplorazione dell'app avviata»): whether the app starts, the pages and controls found, the
controls pressed and the functions each ran, and, against the static candidates, how many controls with an effect the
static reader has no candidate for (`recovered`), how many it has by name (`matched`), and how many of the events it
discarded on a component (`component_gap`) a pressed control of the same name stands for. Its entries against a
reference's flows are `entries_vs_reference.py`'s.
"""
from __future__ import annotations

import collections
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import modal_pipeline
from modal_pipeline import REMOTE_SCRIPTS, app, volume

SAMPLE = 20


# the image of the pipeline, with its driver beside this file: the function imports it by name
@app.function(image=modal_pipeline.image.add_local_file(Path(modal_pipeline.__file__), "/root/modal_pipeline.py"),
              cpu=(0.5, 8.0), memory=(2048, 16384), timeout=7200, volumes={"/results": volume})
def explore_folder(source: str, analysis: str) -> dict:
    sys.path[:0] = [REMOTE_SCRIPTS]
    import entries
    import observed_entries
    import premap
    import snapshot
    modal_pipeline._engine()
    started = time.monotonic()
    project, manifest, out = Path("/cases/explore"), Path("/runs/explore/manifest.sqlite"), Path("/runs/explore/run")
    shutil.rmtree(project, ignore_errors=True)
    shutil.rmtree(manifest.parent, ignore_errors=True)
    # `folder`: the folder of DAODAN_FOLDER the image carries; anything else, a folder of the volume
    origin = Path(modal_pipeline.REMOTE_FOLDER) if source == "folder" else Path("/results") / source
    shutil.copytree(origin, project, ignore=shutil.ignore_patterns("node_modules", ".git"))
    if not (project / ".git").exists():  # the upload leaves `.git` out: a checkout of the folder, as the CI has one
        for command in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x"]):
            subprocess.run(["git", *command], cwd=project, check=True)
    snapshot.write_snapshot(project, manifest)
    import dynamic
    from pipeline import events
    bus, said = events.Bus(), []
    bus.subscribe(said.append)
    answer = dynamic.run(manifest, bus)  # the step as the pipeline runs it: the app is planned, started, explored, kept and said
    record = premap.ensure(manifest)
    seen = answer["app"]
    gaps = [event["data"]["gap"] for event in said if event["kind"] == "gap" and event["data"]["gap"].get("kind") != "no-static-graph"]
    out = manifest.parent / dynamic.RUNS / dynamic.APP
    result = {"source": source, "analysis": analysis, "starts": record.get("starts", []), "builds": record.get("builds", []),
              "state": seen["state"], "apps": seen["apps"], "reused": seen.get("reused", False), "gaps": gaps,
              "gap_kinds": dict(collections.Counter(gap["kind"] for gap in gaps)),
              **{key: seen[key] for key in ("cause", "remedy") if key in seen}}
    pages = [page for number in range(seen["apps"]) for page in _explored(out, number).get("pages", [])]
    pressed = [c for page in pages for c in _flat(page["controls"]) if c.get("state") == "pressed"]
    result["explored"] = {"pages": len(pages), "controls": sum(len(_flat(page["controls"])) for page in pages),
                          "revealed": sum(1 for page in pages for c in _flat(page["controls"]) if c.get("opened_by")),
                          "pressed": len(pressed),
                          "with_effect": sum(1 for c in pressed if c.get("calls") or c.get("requests")),
                          "with_handler": sum(1 for c in pressed if c.get("handler")),
                          "skipped": dict(collections.Counter(c.get("reason") for page in pages for c in _flat(page["controls"])
                                                              if c.get("state") == "skipped")),
                          "failed": sum(1 for page in pages for c in _flat(page["controls"]) if c.get("state") == "failed"),
                          "urls": [page["url"] for page in pages][:SAMPLE]}
    base = Path("/runs/analysis")
    shutil.rmtree(base, ignore_errors=True)
    shutil.copytree(Path("/results") / analysis, base)
    static = entries.cached_syntax(base / "manifest.sqlite")
    from snapshot_store import open_snapshot
    with open_snapshot(base / "manifest.sqlite") as store:
        files = set(store.iter_paths())
    apps = json.loads((manifest.parent / observed_entries.FILE).read_text(encoding="utf-8"))["apps"] \
        if (manifest.parent / observed_entries.FILE).is_file() else []
    recovered = observed_entries.candidates(apps, static, files)
    labels = {(row.get("label") or "").strip().lower() for row in static if row.get("label") and row.get("event") == "click"}
    discarded = [row for row in static if row.get("component_gap")]
    names = {(c["name"] or "").strip().lower() for c in pressed if c.get("calls") or c.get("requests")}
    result["analysis_top_folders"] = dict(collections.Counter(path.split("/")[0] for path in files).most_common(12))
    result["pressed_sample"] = [{"page": page["url"], "name": c["name"], "role": c["role"], "calls": len(c.get("calls", [])),
                                 "requests": len(c.get("requests", [])), "handler": c.get("handler"),
                                 "first_calls": [[call["source"], call["line"], call["name"]] for call in c.get("calls", [])[:3]]}
                                for page in pages for c in _flat(page["controls"]) if c.get("state") == "pressed"][:SAMPLE]
    result["not_pressed_sample"] = [{"page": page["url"], "name": c["name"], "role": c["role"], "state": c["state"],
                                     "reason": c.get("reason")}
                                    for page in pages for c in _flat(page["controls"]) if c.get("state") in ("failed", "skipped")]
    result["not_pressed_sample"].sort(key=lambda row: row["state"] != "failed")  # the failures first: they are the ones to read
    result["not_pressed_sample"] = result["not_pressed_sample"][:SAMPLE]
    result["page_errors"] = [{"page": page["url"], "errors": page.get("errors", [])} for page in pages if page.get("errors")][:SAMPLE]
    result["structure"] = [{"page": page["url"], "name": c["name"][:40], **c["structure"]}  # the rule that reads a press as a redrawn page
                           for page in pages for c in _flat(page["controls"]) if c.get("structure") and c["structure"]["renamed"]][:SAMPLE]
    result["revealed"] = [{"page": page["url"], "opened_by": c["opened_by"], "role": c["role"], "name": c["name"],
                           "state": c.get("state"), "handler": (c.get("handler") or {}).get("name")}
                          for page in pages for c in _flat(page["controls"]) if c.get("opened_by")]  # all of them: what a press shows
    result["against_static"] = {
        "static_candidates": len(static), "static_labelled_click": len(labels),
        "recovered": len(recovered), "recovered_with_handler": sum(1 for row in recovered if row.get("handler")),
        "matched": sum(1 for n in names if n in labels),
        "discarded_on_a_component": len(discarded),
        "discarded_with_a_label": sum(1 for row in discarded if row.get("label")),
        "discarded_with_a_pressed_control_of_the_same_name": sum(
            1 for row in discarded if (row.get("label") or "").strip().lower() in names),
        "recovered_sample": [{key: row.get(key) for key in ("site", "label", "role", "handler", "observed_calls", "requests")}
                             for row in recovered[:SAMPLE]]}
    result["against_static"]["links"] = _links(manifest, base, recovered)
    result["seconds"] = round(time.monotonic() - started, 1)
    return result


def _links(explored: Path, base: Path, recovered: list[dict]) -> dict:
    """What the links of the earlier analysis (`flows.link_facts` with no rule) make of the pressed controls: how many of
    the isolated handlers are the function of the snapshot an entry starts at (`flows._observed_entries`), as a function
    that is named or an inline arrow, and how many controls the entries stand for."""
    import flows
    import observed_entries
    shutil.copy(explored.parent / observed_entries.FILE, base / observed_entries.FILE)  # the pages beside the analysis' manifest
    links = flows.link_facts(base / "manifest.sqlite", [])
    started = [entry for entry in links["entries"] if entry.get("reader") == "observed"]
    isolated = [row for row in recovered if row.get("handler")]
    from snapshot_store import open_snapshot
    with open_snapshot(base / "manifest.sqlite") as store:  # the lines a handler spans: where a flow's first step falls
        spans = []
        for entry in started:
            file, _, line = entry["site"].rpartition(":")
            ends = [row[0] for row in store.connection.execute(
                "SELECT l1 FROM sem_declarations WHERE file = ? AND l0 = ? AND kind IN ('function', 'method')", (file, int(line)))]
            spans.append({"file": file, "line": int(line), "end": max(ends, default=int(line)), "label": entry.get("label")})
    static = [entry for entry in links["entries"] if entry.get("reader") != "observed"]
    return {"controls_with_an_isolated_handler": len(isolated),
            "handlers": len({row["handler"].partition(" ")[0] for row in isolated}),
            "entries": len(started), "entries_inline": sum(1 for entry in started if entry["handler_source"] == "inline"),
            "static_entries": len(static), "observed_spans": spans, "static_sites": sorted({entry["site"] for entry in static}),
            "sample": [{key: entry.get(key) for key in ("symbol", "site", "label", "handler_source")} for entry in started[:SAMPLE]]}


def _flat(controls: list) -> list:
    """The controls of a page and, under each, those its press revealed."""
    return [item for control in controls for item in (control, *_flat(control.get("revealed") or []))]


def _explored(out: Path, number: int) -> dict:
    try:
        return json.loads((out / "out" / f"explore-{number}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@app.local_entrypoint()
def explore_main(source: str, analysis: str, out: str = ""):
    answer = explore_folder.remote(source, analysis)
    text = json.dumps(answer, indent=1, default=str)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
    print(text[:6000], flush=True)
