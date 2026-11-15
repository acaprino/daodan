"""The analysis pipeline: its steps in one place, in order, up to the complete graph.

Each step has the same contract: `NAME`, `INPUTS` (what it reads, written by the steps before it), `OUTPUTS`
(what it writes) and `run(context)`; it says what it does on the context's event bus (`pipeline.events`). The
snapshot is the pipeline's input; the flows read the complete graph after it.

1. `scan`: the module graph and the pre-map, the project's modules and technologies.
2. `analyze`: one analyzer per technology of the pre-map, each with its adapter's tool (`resolve_edges.run_pass`).
3. `union`: the graphs of the technologies as the complete graph. Until the dynamic step and the connection
   points exist, it is the store of the static graphs, and it says so with a gap per language.

See docs/specs/2026-11-15-pipeline-di-analisi.md.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pipeline import events  # noqa: E402


@dataclass
class Context:
    manifest: Path
    bus: events.Bus
    environments: list = field(default_factory=list)
    report_path: Path | None = None  # the analysis's report, beside the snapshot by default


class Scan:
    NAME, INPUTS, OUTPUTS = "scan", ("snapshot",), ("modules", "premap")

    @staticmethod
    def run(context: Context) -> dict:
        import modules
        import premap
        bus, manifest = context.bus, context.manifest
        graph = modules.ensure_graph(manifest)
        if graph["state"] != "fresh":
            raise StepFailed(f"the module graph is {graph['state']}: {graph.get('reason', '')}",
                             "write the snapshot again")
        bus.emit("log", f"module graph: {graph.get('modules', 0)} modules", step=Scan.NAME, level="debug")

        def source(status: dict, done: int, total: int) -> None:
            bus.progress(Scan.NAME, done, total, phase=status["source"],
                         message=f"{status['source']}: {status['state']}")

        record = premap.ensure(manifest, report=source)
        for gap in record.get("gaps", []):
            bus.emit("gap", gap.get("detail") or gap["kind"], step=Scan.NAME, gap=gap)
        return {"modules": graph.get("modules", 0), "graph": graph["graph"], "action": graph.get("action"),
                "units": len(record["units"]), "gaps": len(record["gaps"]), "premap": str(premap.path(manifest))}


class Analyze:
    NAME, INPUTS, OUTPUTS = "analyze", ("snapshot", "premap"), ("edges",)

    @staticmethod
    def run(context: Context) -> dict:
        import resolve_edges
        report = resolve_edges.run_pass(context.manifest,
                                        context.report_path or context.manifest.with_name(resolve_edges.REPORT_NAME),
                                        context.environments, bus=context.bus)
        return report


class Union:
    NAME, INPUTS, OUTPUTS = "union", ("edges",), ("graph",)

    @staticmethod
    def run(context: Context) -> dict:
        import resolve_edges
        state = resolve_edges.edge_state(context.manifest)
        languages = state.get("languages") or {}
        for language, entry in sorted(languages.items()):
            if entry.get("state") == "fresh":
                context.bus.emit("gap", f"{language}: static graph only", step=Union.NAME, language=language,
                                 gap={"kind": "not-observed",
                                      "detail": "no edge observed in a run: the dynamic step is not built yet"})
        context.bus.emit("graph.ready", "the complete graph is ready", step=Union.NAME,
                         languages={language: {"state": entry.get("state"), "engine": entry.get("engine")}
                                    for language, entry in languages.items()})
        return {"languages": languages}


STEPS = (Scan, Analyze, Union)


class StepFailed(Exception):
    def __init__(self, cause: str, remedy: str):
        super().__init__(cause)
        self.cause, self.remedy = cause, remedy


def run(manifest: Path, listeners=(), environments=None, *, start: str | None = None, stop: str | None = None,
        report_path: Path | None = None) -> dict:
    """The steps in order on the snapshot `manifest`, from `start` through `stop` (default: all), with
    `listeners` on the bus and the journal beside it; each step's result by its name. A step that fails says
    why and stops the ones after it: its result is `{"failed": cause, "remedy": ...}`."""
    manifest = Path(manifest).resolve()
    bus = events.Bus(manifest.with_name(events.JOURNAL))
    for listener in listeners:
        bus.subscribe(listener)
    context = Context(manifest, bus, list(environments or []), report_path)
    names = [step.NAME for step in STEPS]
    chosen = STEPS[names.index(start) if start else 0:names.index(stop) + 1 if stop else len(STEPS)]
    results = {}
    for step in chosen:
        bus.emit("step.started", step.NAME, step=step.NAME, inputs=list(step.INPUTS))
        try:
            results[step.NAME] = step.run(context)
        except StepFailed as failure:
            bus.emit("step.failed", failure.cause, step=step.NAME, level="error", cause=failure.cause,
                     remedy=failure.remedy)
            results[step.NAME] = {"failed": failure.cause, "remedy": failure.remedy}
            break
        bus.emit("step.finished", step.NAME, step=step.NAME, outputs=list(step.OUTPUTS))
    return results


def follow(manifest: Path, after: int = 0, limit: int | None = None) -> tuple[list[dict], int]:
    """The run's events from the cursor `after`, for a listener in another process."""
    return events.read(Path(manifest).resolve().with_name(events.JOURNAL), after, limit)
