"""The exploration of a running app, on Modal (plan task 11.5): the dynamic step (`dynamic.run`, as the pipeline runs it)
starts the project's app in the pipeline's sandboxes, opens a headless browser on it and presses each control once; what
it finds is compared with the static reader's candidates and links of an analysis made earlier.

Nothing of the project runs on this PC. The source and the earlier analysis are folders of the volume
`daodan-flow-results` (the analysis' `manifest.sqlite`, `engine-edges.sqlite` and the files beside them):

    modal run benchmarks/project-model/modal_explore.py::explore_main --source possible-in/CASE-src \
        --out benchmarks/project-model/results/explore/CASE.json

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
              cpu=(2.0, 16.0), memory=(4096, 32768), timeout=7200, volumes={"/results": volume})
def explore_folder(source: str) -> dict:
    sys.path[:0] = [REMOTE_SCRIPTS]
    import entries
    import observed_entries
    import pipeline
    import premap
    import snapshot
    modal_pipeline._engine()
    started = time.monotonic()
    project, manifest = Path("/cases/explore"), Path("/runs/explore/manifest.sqlite")
    shutil.rmtree(project, ignore_errors=True)
    shutil.rmtree(manifest.parent, ignore_errors=True)
    # `folder`: the folder of DAODAN_FOLDER the image carries; anything else, a folder of the volume
    origin = Path(modal_pipeline.REMOTE_FOLDER) if source == "folder" else Path("/results") / source
    shutil.copytree(origin, project, ignore=shutil.ignore_patterns("node_modules", ".git"))
    if not (project / ".git").exists():  # the upload leaves `.git` out: a checkout of the folder, as the CI has one
        for command in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x"]):
            subprocess.run(["git", *command], cwd=project, check=True)
    snapshot.read_project(project, manifest)
    import dynamic
    said = []
    steps = pipeline.run(manifest, listeners=[said.append])  # the whole pipeline on this one snapshot, as `run_folder` runs it
    record = premap.ensure(manifest)
    seen = (steps.get("run_and_observe") or {}).get("app") or {"state": "failed", "apps": 0, "kept": 0,
                                                               "cause": str(steps.get("run_and_observe")), "remedy": ""}
    gaps = [event["data"]["gap"] for event in said if event["kind"] == "gap" and event.get("analyzer") == dynamic.APP]
    out = manifest.parent / dynamic.RUNS / dynamic.APP
    result = {"source": source, "starts": record.get("starts", []), "builds": record.get("builds", []),
              "steps": {name: ("failed" if "failed" in (value or {}) else "ran") for name, value in steps.items()},
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
    from snapshot_store import open_snapshot
    kept = manifest.with_name(observed_entries.FILE)
    held = kept.with_name(kept.name + ".held")
    if kept.is_file():
        kept.rename(held)  # the baseline is this snapshot's own static candidates, links and cards: the controls hidden
    try:
        static = entries.cached_syntax(manifest)
        static_links, static_cards = _links_and_cards(manifest)
    finally:
        if held.is_file():
            held.rename(kept)
    with open_snapshot(manifest) as store:
        files = set(store.iter_paths())
    apps = json.loads(kept.read_text(encoding="utf-8"))["apps"] if kept.is_file() else []
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
    result["forms"] = [{"page": page["url"], "name": c["name"], "filled": [(f["type"], f["name"], f.get("error")) for f in c["filled"]],
                        "invalid": c.get("invalid"), "handler": (c.get("handler") or {}).get("name"),
                        "requests": [f"{r['method']} {r['url'].rpartition('/')[2]}" for r in c.get("requests", [])]}
                       for page in pages for c in _flat(page["controls"]) if c.get("filled")]
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
    result["against_static"]["links"] = _links(manifest, static_links, static_cards, recovered, static)
    result["seconds"] = round(time.monotonic() - started, 1)
    return result


def _links_and_cards(manifest: Path) -> tuple[dict, dict]:
    """The links (`flows.link_facts`, no rule) and the cards of the paths (`flow_paths`) of the snapshot as it stands."""
    import flow_paths
    import flows
    links = flows.link_facts(manifest, [])
    _cached, cards, _revision = flow_paths._deck(manifest, [])
    return links, cards


def _handlers(manifest: Path, rows: list[dict], starts: set[str], static: list[dict]) -> dict:
    """Where the handlers the browser isolated (`rows`, the observed candidates) stand in the snapshot: placed as a function
    (`flows._handler_at`, as the links place them), how many of those a static reader already starts from (`starts`, the
    symbols of the static entries), how many it does not place, and the `file:line` where the code names a placed handler
    (`onSubmit={handleSubmit}`), which is where a reference's cite stands, and the lines each placed handler's function spans
    (a cite on a call inside it, `await signIn(...)`, is a cite of the control that ran it), and the same for the functions
    the static entries start from, so that both sides are read by the same rule."""
    import edge_view
    import flows
    import semantic_store
    from snapshot_store import open_snapshot
    placed, unplaced, sites, spans, held, labels = set(), 0, set(), {}, {}, {}
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        facts = flows.Facts(store, db, view)
        for row in rows:
            handler = flows._handler_at(facts, row["at"]) if row.get("at") else None
            if handler is None:
                unplaced += row.get("at") is not None
                continue
            symbol = handler["id"] if handler["name"] == "(anonymous)" else facts.node(handler["id"])
            placed.add(symbol)
            labels.setdefault(symbol, set()).add((row.get("label") or "").strip().lower())
            spans[symbol] = {"file": handler["file"], "line": handler["line"], "end": handler["end"] or handler["line"]}
        for declaration in facts.declarations.values():  # the lines of the function each static entry starts from
            if declaration["kind"] in ("function", "method"):
                for name in {declaration["id"], facts.node(declaration["id"])} & starts:
                    held[name] = {"file": declaration["file"], "line": declaration["line"],
                                  "end": declaration["end"] or declaration["line"]}
        for read in view["reads"]:
            parts, span = read.get("parts") or [], read.get("span")
            if len(parts) == 1 and span and span[0]:
                found = facts.targets(str(parts[0]), read["file"], span[0], span[1], ("function", "method"))
                if len(found) == 1 and facts.node(found[0]) in placed:
                    sites.add(f"{read['file']}:{span[0]}")
    return {"handlers_placed": len(placed), "handlers_unplaced_controls": unplaced,
            "handlers_already_static": len(placed & starts), "handlers_new": len(placed - starts),
            "observed_binding_sites": sorted(sites), "observed_spans": list(spans.values()),
            "static_spans": list(held.values()),
            # the handlers no static entry starts from, with the static candidates of the same name: why they are not the same function
            "new_handlers": [{"symbol": symbol, "labels": sorted(labels[symbol]), "static_same_name": [
                {key: row.get(key) for key in ("reader", "site", "symbol", "handler_source", "gap", "label")} for row in static
                if (row.get("label") or "").strip().lower() in labels[symbol]][:5]} for symbol in sorted(placed - starts)]}


def _links(manifest: Path, static_links: dict, static_cards: dict, recovered: list[dict], static_rows: list[dict]) -> dict:
    """What the links and the cards of this snapshot make of the pressed controls, against the same snapshot without them:
    how many isolated handlers are a function of the snapshot (`flows._handler_at`, a named one or an inline arrow), how many
    of those a static reader already starts from, the entries and cards that come of the rest, and where they fall (the lines a
    handler spans, for `entries_vs_reference.py`)."""
    import observed_entries
    from snapshot_store import open_snapshot
    links, cards = _links_and_cards(manifest)
    started = [entry for entry in links["entries"] if entry.get("reader") == "observed"]
    isolated = [row for row in recovered if row.get("handler")]
    static = [entry for entry in static_links["entries"] if entry.get("reader") != "observed"]
    seen = [card for card in cards.values() if card.get("reader") == "observed"]
    with open_snapshot(manifest) as store:  # every pressed control with an effect, none left out for a name a static row has
        rows = observed_entries.rows(manifest, [], set(store.iter_paths()))
    handlers = _handlers(manifest, rows, {entry["symbol"] for entry in static_links["entries"]}, static_rows)
    return {"controls_with_an_isolated_handler": len(isolated),
            "handlers": len({row["handler"].partition(" ")[0] for row in isolated}),
            "entries": len(started), "entries_inline": sum(1 for entry in started if entry["handler_source"] == "inline"),
            "static_entries": len(static), "cards_without_the_controls": len(static_cards), "cards_with_the_controls": len(cards),
            "observed_cards": [{key: card.get(key) for key in ("label", "event", "handler", "site", "kind")} for card in seen][:SAMPLE],
            **handlers, "static_sites": sorted({entry["site"] for entry in static}),
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
def explore_main(source: str, out: str = ""):
    answer = explore_folder.remote(source)
    text = json.dumps(answer, indent=1, default=str)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
    print(text[:6000], flush=True)
