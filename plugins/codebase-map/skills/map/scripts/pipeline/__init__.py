"""The analysis pipeline: its steps in one place, in order, up to the complete graph.

Each step has the same contract: `NAME`, `INPUTS` (what it reads, written by the steps before it), `OUTPUTS`
(what it writes) and `run(context)`; it says what it does on the context's event bus (`pipeline.events`). The
snapshot is the pipeline's input; the flows read the complete graph after it.

1. `scan`: the module graph and the pre-map, the project's modules and technologies; the pre-map's model
   commands run in Daodan's container (`premap.container_runner`).
2. `stack`: the technologies of each build unit, frameworks, libraries, tools and services, from the registry's
   signs (`technologies.ensure`).
3. `analyze`: one analyzer per technology of the pre-map, each with its adapter's tool (`resolve_edges.run_pass`).
4. `dynamic`: one observer per technology with a static graph (`dynamic.run`): the project's tests run in
   Daodan's container under a recorder, and the calls they execute enter the store as observed edges. With no
   container engine, no observer for a language or no test command the project declares, it says the gap and
   the pipeline goes on. `DAODAN_DYNAMIC=off` skips it.
5. `union`: the graphs of the technologies as the complete graph. Until the connection points exist, it is the
   store of each technology's graph: it says what a run observed (the sites, the holes closed, the sampled ones
   apart) and what stayed
   unobserved (a language with no observed edge, the tests that did not run, the files no test executed, an
   observed edge against a proven one), and what the graph does not hold: the files an index left out, the
   languages no analyzer lists, the calls between two analyzers' languages.

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
    report_path: Path | None = None  # the analysis's report, beside the snapshot by default
    results: dict = field(default_factory=dict)  # each step's result by its name, for the steps after it


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

        record = premap.ensure(manifest, report=source, runner=_runner(manifest))
        for gap in record.get("gaps", []):
            bus.emit("gap", gap.get("detail") or gap["kind"], step=Scan.NAME, gap=gap)
        return {"modules": graph.get("modules", 0), "graph": graph["graph"], "action": graph.get("action"),
                "units": len(record["units"]), "gaps": len(record["gaps"]), "premap": str(premap.path(manifest))}


def _runner(manifest: Path):
    """`container_runner.runner` with the engine asked once per scan, as an analyzer asks it once per stage
    (`container.find_engine`): the engine found goes to the first run, which ends it, and the next runs find their
    own; without one, every model source gets the same `container.Gap` at once, with no second wait."""
    import container
    from premap import container_runner
    asked: dict = {}

    def run(commands: list[dict], toolchains: list[dict] = ()) -> list[dict]:
        if not asked:
            asked["once"] = True
            try:
                asked["engine"] = container.find_engine()
            except container.Gap as gap:
                asked["gap"] = gap
        if "gap" in asked:
            raise asked["gap"]
        return container_runner.runner(manifest, engine=asked.pop("engine", None))(commands, toolchains)

    return run


class Stack:
    NAME, INPUTS, OUTPUTS = "stack", ("snapshot", "modules", "premap"), ("technologies",)

    @staticmethod
    def run(context: Context) -> dict:
        import technologies
        record = technologies.ensure(context.manifest)
        return {"technologies": len(record["technologies"]), "units": len(record["units"]),
                "path": str(technologies.path(context.manifest))}


class Analyze:
    NAME, INPUTS, OUTPUTS = "analyze", ("snapshot", "premap"), ("edges",)

    @staticmethod
    def run(context: Context) -> dict:
        import resolve_edges
        report = resolve_edges.run_pass(context.manifest,
                                        context.report_path or context.manifest.with_name(resolve_edges.REPORT_NAME),
                                        bus=context.bus)
        return report


class Dynamic:
    NAME, INPUTS, OUTPUTS = "dynamic", ("snapshot", "premap", "edges"), ("observed",)

    @staticmethod
    def run(context: Context) -> dict:
        import dynamic
        try:
            return dynamic.run(context.manifest, context.bus)
        except Exception as error:  # noqa: BLE001 - what a run observes is added to the static graph, which stays
            cause = f"{type(error).__name__}: {error}"
            context.bus.emit("log", f"the dynamic step failed: {error}", step=Dynamic.NAME, level="error",
                             cause=cause, remedy="the graph is the static one; run the analysis again")
            return {"languages": {}, "failed": cause}


class Union:
    NAME, INPUTS, OUTPUTS = "union", ("edges", "observed"), ("graph",)
    # Languages two analyzers index apart that call each other (Java and Kotlin in one build, cgo, a Python C
    # extension, JNI): each stage loads only its own index, so no edge joins them.
    APART = (("java", "kotlin"), ("go", "c"), ("python", "c"), ("python", "cpp"), ("java", "c"), ("java", "cpp"))

    @staticmethod
    def run(context: Context) -> dict:
        import collections
        import resolve_edges
        state = resolve_edges.edge_state(context.manifest)
        languages = state.get("languages") or {}

        def say(message: str, gap: dict, language: str | None = None) -> None:
            context.bus.emit("gap", message, step=Union.NAME, gap=gap, **({"language": language} if language else {}))

        outcomes = (context.results.get(Dynamic.NAME) or {}).get("languages") or {}
        for language, entry in sorted(languages.items()):
            if entry.get("state") != "fresh":
                continue
            try:
                Union.observed(language, entry.get("coverage") or {}, (outcomes.get(language) or {}).get("reason"),
                               context.bus, say)
                files = (entry.get("coverage") or {}).get("files") or {}
                if files.get("missing"):
                    reasons = dict(collections.Counter(item["reason"] for item in files["missing"]).most_common(3))
                    detail = (f"{len(files['missing'])} of {files['snapshot']} {language} files are not in the "
                              "index: " + ", ".join(f"{reason} ({count})" for reason, count in reasons.items()))
                    say(f"{language}: {detail}", {"kind": "files-missing", "files": len(files["missing"]),
                                                  "of": files["snapshot"], "reasons": reasons, "detail": detail},
                        language)
            except Exception as error:  # noqa: BLE001 - one language's report stops no other, nor the graph
                context.bus.emit("log", f"{language}: its report could not be read: {error!r}", step=Union.NAME,
                                 level="error", language=language, cause=f"{type(error).__name__}: {error}",
                                 remedy="analyze again: the step that wrote it writes it again")
        unserved = state.get("no_analyzer") or {}
        for language, files in unserved.items():
            detail = f"{files} {language} files are in the snapshot and no analyzer lists the language: no graph"
            say(detail, {"kind": "no-analyzer", "language": language, "files": files, "detail": detail}, language)
        apart = [list(pair) for pair in Union.APART if set(pair) <= set(languages)]
        for one, other in apart:
            detail = (f"calls between {one} and {other} are not resolved: each analyzer reads its own index, so a "
                      "project symbol of the other language can read as external")
            say(detail, {"kind": "not-joined", "languages": [one, other], "detail": detail})
        context.bus.emit("graph.ready", "the complete graph is ready", step=Union.NAME,
                         languages={language: {"state": entry.get("state"), "engine": entry.get("engine")}
                                    for language, entry in languages.items()})
        return {"languages": languages, **({"no_analyzer": unserved} if unserved else {}),
                **({"not_joined": apart} if apart else {})}

    @staticmethod
    def observed(language: str, coverage: dict, reason: str | None, bus, say) -> None:
        """What a run observed for `language` (its `coverage`'s `observed`, and `sampled` apart), and what stayed
        unobserved, each a gap: no edge of a run at all (with the dynamic step's `reason` when it gave one), the
        tests that did not run to their end, the files with calls no test executed, the observed edges against a
        proven one. A sample says nothing of what it did not see."""
        seen, sampled = coverage.get("observed") or {}, coverage.get("sampled") or {}
        for test in seen.get("tests") or ():
            if test["state"] != "ran":
                detail = (f"{language}: the tests of {test['root']} ({test['runner']}) ended {test['state']}: what "
                          "they call is not observed")
                say(detail, {"kind": "tests-not-run", "path": test["root"], "state": test["state"],
                             "detail": detail}, language)
        if not seen.get("edges") and not sampled.get("edges"):
            why = reason or ("a run placed no call on a reference of this language" if seen else
                             "the dynamic step has not observed this language")
            say(f"{language}: static graph only", {"kind": "not-observed", "detail":
                f"no edge observed in a run: {why}"}, language)
            return
        if seen.get("edges"):
            bus.emit("log", f"{language}: {seen['sites']} sites observed in a run, "
                            f"{sum(seen['closed'].values())} holes closed", step=Union.NAME, language=language,
                     resolver=seen.get("resolver"), sites=seen["sites"], edges=seen["edges"], closed=seen["closed"])
        if sampled.get("edges"):
            bus.emit("log", f"{language}: {sampled['sites']} sites and {sampled['edges']} edges sampled in a run, "
                            f"{sum(sampled['closed'].values())} holes closed", step=Union.NAME, language=language,
                     resolver=sampled.get("resolver"), sites=sampled["sites"], edges=sampled["edges"],
                     closed=sampled["closed"])
        idle = (seen.get("files") or {}).get("not_executed") or []
        if idle:
            detail = (f"{language}: no test executed {len(idle)} files with calls, which stay as the static steps "
                      f"left them: {', '.join(idle[:5])}")
            say(detail, {"kind": "files-not-executed", "count": len(idle), "files": idle[:60], "detail": detail},
                language)
        conflicts = seen.get("conflicts") or {}
        if conflicts.get("count"):
            detail = (f"{language}: {conflicts['count']} observed edges contradict a proven edge at the same call, "
                      f"a defect of one of the two steps; both are kept: {conflicts['examples'][0]['site']}")
            say(detail, {"kind": "observed-conflict", "count": conflicts["count"],
                         "examples": conflicts["examples"], "detail": detail}, language)


STEPS = (Scan, Stack, Analyze, Dynamic, Union)


class StepFailed(Exception):
    def __init__(self, cause: str, remedy: str):
        super().__init__(cause)
        self.cause, self.remedy = cause, remedy


def run(manifest: Path, listeners=(), *, start: str | None = None, stop: str | None = None,
        report_path: Path | None = None) -> dict:
    """The steps in order on the snapshot `manifest`, from `start` through `stop` (default: all), with
    `listeners` on the bus and the journal beside it; each step's result by its name. A step that fails says
    why and stops the ones after it: its result is `{"failed": cause, "remedy": ...}`."""
    manifest = Path(manifest).resolve()
    bus = events.Bus(manifest.with_name(events.JOURNAL))
    for listener in listeners:
        bus.subscribe(listener)
    context = Context(manifest, bus, report_path)
    names = [step.NAME for step in STEPS]
    chosen = STEPS[names.index(start) if start else 0:names.index(stop) + 1 if stop else len(STEPS)]
    results = context.results
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
