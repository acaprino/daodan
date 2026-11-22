"""The exploration of a running app, on Modal (plan task 11.5): start the project's app in the pipeline's sandboxes, open
a headless browser on it, press each control once, and compare what it finds with the static reader's candidates of an
analysis made earlier.

Nothing of the project runs on this PC. The source and the earlier analysis are folders of the volume
`daodan-flow-results` (the analysis' `manifest.sqlite`, `engine-edges.sqlite` and the files beside them):

    python -m modal run benchmarks/project-model/modal_explore.py::explore_main --source possible-in/phazly3-src \
        --analysis possible-in/phazly5 --out benchmarks/project-model/results/explore/phazly.json

What is measured (README, «Esplorazione dell'app avviata»): whether the app starts, the pages and controls found, the
controls pressed and the functions each ran, and, against the static candidates, how many controls with an effect the
static reader has no candidate for (`recovered`), how many it has by name (`matched`), and how many of the events it
discarded on a component (`component_gap`) a pressed control of the same name stands for. It measures no flow.
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
def explore_folder(source: str, analysis: str, seeds: list | None = None) -> dict:
    sys.path[:0] = [REMOTE_SCRIPTS]
    import entries
    import observed_entries
    import premap
    import snapshot
    from dynamic import app as explorer
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
    record = premap.write(manifest, sources=[item for item in premap.SOURCES if not hasattr(item, "commands")])
    planned = explorer.plan(record, explore=True, seeds=tuple(seeds or ()))
    result = {"source": source, "analysis": analysis, "starts": record.get("starts", []), "builds": record.get("builds", []),
              "plan_gaps": planned["gaps"], "apps_planned": [one["declared_in"] for one in planned["apps"]]}
    seen = explorer.observe(project, planned, out)
    explorer.record(manifest, planned, out)
    result.update(state=seen["state"], apps=seen["apps"], gaps=seen["gaps"],
                  gap_kinds=dict(collections.Counter(gap["kind"] for gap in seen["gaps"])),
                  **{key: seen[key] for key in ("cause", "remedy") if key in seen})
    pages = [page for number in range(len(planned["apps"]))
             for page in _explored(out, number).get("pages", [])]
    pressed = [c for page in pages for c in page["controls"] if c.get("state") == "pressed"]
    result["explored"] = {"pages": len(pages), "controls": sum(len(page["controls"]) for page in pages),
                          "pressed": len(pressed),
                          "with_effect": sum(1 for c in pressed if c.get("calls") or c.get("requests")),
                          "skipped": dict(collections.Counter(c.get("reason") for page in pages for c in page["controls"]
                                                              if c.get("state") == "skipped")),
                          "failed": sum(1 for page in pages for c in page["controls"] if c.get("state") == "failed"),
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
                                 "requests": len(c.get("requests", [])),
                                 "first_calls": [[call["source"], call["line"], call["name"]] for call in c.get("calls", [])[:3]]}
                                for page in pages for c in page["controls"] if c.get("state") == "pressed"][:SAMPLE]
    result["not_pressed_sample"] = [{"page": page["url"], "name": c["name"], "role": c["role"], "state": c["state"],
                                     "reason": c.get("reason")}
                                    for page in pages for c in page["controls"] if c.get("state") in ("failed", "skipped")][:SAMPLE]
    result["page_errors"] = [{"page": page["url"], "errors": page.get("errors", [])} for page in pages if page.get("errors")][:SAMPLE]
    result["against_static"] = {
        "static_candidates": len(static), "static_labelled_click": len(labels),
        "recovered": len(recovered), "matched": sum(1 for n in names if n in labels),
        "discarded_on_a_component": len(discarded),
        "discarded_with_a_label": sum(1 for row in discarded if row.get("label")),
        "discarded_with_a_pressed_control_of_the_same_name": sum(
            1 for row in discarded if (row.get("label") or "").strip().lower() in names),
        "recovered_sample": [{key: row.get(key) for key in ("site", "label", "role", "observed_calls", "requests")}
                             for row in recovered[:SAMPLE]]}
    result["seconds"] = round(time.monotonic() - started, 1)
    return result


def _explored(out: Path, number: int) -> dict:
    try:
        return json.loads((out / "out" / f"explore-{number}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@app.local_entrypoint()
def explore_main(source: str, analysis: str, out: str = "", seeds: str = ""):
    answer = explore_folder.remote(source, analysis, [item for item in seeds.split(",") if item])
    text = json.dumps(answer, indent=1, default=str)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
    print(text[:6000], flush=True)
