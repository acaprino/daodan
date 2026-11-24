"""The analysis pipeline: its steps in one place, in order, up to the complete graph.

Each step has the same contract: `NAME`, `INPUTS` (what it reads, written by the steps before it), `OUTPUTS`
(what it writes), `WITHOUT` (what the pipeline does when the step fails: None where the steps after it need it and
stop, else the words that say how it goes on) and `run(context)`; it says what it does on the context's event bus
(`pipeline.events`). The snapshot is the pipeline's input; the flows read the complete graph after it.

1. `scan`: the module graph and the pre-map, the project's modules and technologies; the pre-map's model
   commands run in Daodan's container (`premap.container_runner`). It reads only the inventory
   (`file_inventory.write`), so it runs before the files are read.
2. `stack`: the technologies of each build unit, frameworks, libraries, tools and services, from the registry's
   signs (`technologies.ensure`); it too reads only the inventory, the modules and the pre-map.
3. `parse`: says the plan (`pipeline.plan`, spec 8.4): which adapter runs on which files, executed by
   `snapshot.write_reading`, `engine_pass.pass_plan` and `dynamic.run`. It reads no file: the one reading is
   `snapshot.write_snapshot`, which every caller runs first, and a store that holds only its inventory stops the step.
4. `analyze`: one analyzer per technology of the pre-map, each with its adapter's tool (`resolve_edges.run_pass`).
5. `dynamic`: one observer per technology with a static graph (`dynamic.run`): the project's tests run in
   Daodan's container under a recorder, and the calls they execute enter the store as observed edges. With no
   container engine, no observer for a language or no test command the project declares, it says the gap and
   the pipeline goes on. The same step starts the app the project declares and explores it in a browser: the controls
   it pressed are entries of the links (`dynamic/app.py`). `DAODAN_DYNAMIC=off` skips it.
6. `union`: the graphs of the technologies as the complete graph. Until the connection points exist, it is the
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
    fast_scan: bool = False  # reader-only scan without container commands, for interactive/hook callers
    results: dict = field(default_factory=dict)  # each step's result by its name, for the steps after it


def _reading_pending(manifest: Path) -> bool:
    """Whether the store's files are still to be read; a missing, unreadable or refused store stops the run."""
    import run_store
    from snapshot_store import open_snapshot
    try:
        with open_snapshot(manifest) as store:
            return store.metadata.get("reading") == "not-started"
    except run_store.RunControlError:  # a store that comes with the project: the caller is told as it is
        raise
    except (OSError, ValueError) as error:  # a missing, unreadable or refused store
        raise StepFailed(f"the snapshot cannot be read: {error}", "write the snapshot again") from error


class Parse:
    NAME, INPUTS, OUTPUTS, WITHOUT = "parse", ("snapshot",), ("plan",), None

    @staticmethod
    def run(context: Context) -> dict:
        from snapshot_store import open_snapshot
        # The reading is `write_snapshot`'s alone (the owner's decision of 24 November 2026): this step finds the store read
        # and says the plan. A store with only the inventory is a caller that skipped it: the run stops, and is not read here.
        if _reading_pending(context.manifest):
            raise StepFailed("the snapshot holds only its inventory: its files are not read", "write the snapshot again")
        from . import plan as planning
        with open_snapshot(context.manifest) as store:
            planned = planning.plan(planning.stored(store))
        context.bus.emit("log", "the plan", step=Parse.NAME, plan=planned)
        return {"plan": {"nodes": len(planned["nodes"]), "gaps": len(planned["gaps"])}}


class Scan:
    NAME, INPUTS, OUTPUTS, WITHOUT = "scan", ("inventory",), ("modules", "premap"), None

    @staticmethod
    def run(context: Context) -> dict:
        import modules
        import premap
        _reading_pending(context.manifest)  # the first step: a store that cannot be read stops the run here
        bus, manifest = context.bus, context.manifest
        graph = modules.ensure_structure(manifest)
        if graph["state"] != "fresh":
            raise StepFailed(f"the module graph is {graph['state']}: {graph.get('reason', '')}",
                             "write the snapshot again")
        bus.emit("log", f"module graph: {graph.get('modules', 0)} modules", step=Scan.NAME, level="debug")

        def source(status: dict, done: int, total: int) -> None:
            bus.progress(Scan.NAME, done, total, phase=status["source"],
                         message=f"{status['source']}: {status['state']}")

        record = premap.ensure(manifest, report=source, runner=None if context.fast_scan else _runner(manifest))
        synced = modules.sync_with_premap(manifest, record)
        for gap in record.get("gaps", []):
            bus.emit("gap", gap.get("detail") or gap["kind"], step=Scan.NAME, gap=gap)
        return {"modules": len(synced["modules"]), "graph": graph["graph"], "action": graph.get("action"),
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

    run.uses_default_container = True
    return run


class Stack:
    NAME, INPUTS, OUTPUTS = "stack", ("inventory", "modules", "premap"), ("technologies",)
    WITHOUT = "the analysis goes on; scan again to recognize the technologies"  # the analysis needs no technology

    @staticmethod
    def run(context: Context) -> dict:
        import technologies
        record = technologies.ensure(context.manifest)
        return {"technologies": len(record["technologies"]), "units": len(record["units"]),
                "modules": len(record["modules"]), "path": str(technologies.path(context.manifest))}


class Analyze:
    NAME, INPUTS, OUTPUTS, WITHOUT = "analyze", ("snapshot", "premap"), ("edges",), None

    @staticmethod
    def run(context: Context) -> dict:
        import resolve_edges
        report = resolve_edges.run_pass(context.manifest,
                                        context.report_path or context.manifest.with_name(resolve_edges.REPORT_NAME),
                                        bus=context.bus)
        return report


class Dynamic:
    NAME, INPUTS, OUTPUTS = "dynamic", ("snapshot", "premap", "edges"), ("observed",)
    WITHOUT = "the graph is the static one; run the analysis again"  # what a run observes is added to that graph

    @staticmethod
    def run(context: Context) -> dict:
        import dynamic
        return dynamic.run(context.manifest, context.bus)


class Union:
    NAME, INPUTS, OUTPUTS, WITHOUT = "union", ("edges", "observed"), ("graph",), None
    # Languages two analyzers index apart that call each other (Java and Kotlin in one build, cgo, a Python C
    # extension, JNI): each stage loads only its own index, so no edge joins them.
    APART = (("java", "kotlin"), ("go", "c"), ("python", "c"), ("python", "cpp"), ("java", "c"), ("java", "cpp"))

    @staticmethod
    def run(context: Context) -> dict:
        import collections
        import modules
        import resolve_edges
        graph = modules.ensure_graph(context.manifest)  # `imports` and `calls`, which `scan` leaves out
        if graph["state"] != "fresh":
            context.bus.emit("log", f"the module graph is {graph['state']}: {graph.get('reason', '')}", step=Union.NAME,
                             level="error", cause=graph.get("reason", graph["state"]),
                             remedy="scan again: the step that writes the module graph writes it again")
        state = resolve_edges.edge_state(context.manifest)
        languages = state.get("languages") or {}

        def say(message: str, gap: dict, language: str | None = None) -> None:
            context.bus.emit("gap", message, step=Union.NAME, gap=gap, **({"language": language} if language else {}))

        dynamic = context.results.get(Dynamic.NAME)
        outcomes = (dynamic or {}).get("languages") or {}
        # Why no language has a reason of its own: the step that gives it did not run here, or failed.
        absent = ("the dynamic step did not run in this analysis" if dynamic is None else
                  f"the dynamic step failed: {dynamic['failed']}" if dynamic.get("failed") else None)
        for language, entry in sorted(languages.items()):
            if entry.get("state") != "fresh":
                continue
            try:
                Union.observed(language, entry.get("coverage") or {},
                               (outcomes.get(language) or {}).get("reason") or absent, context.bus, say)
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
        ui_controls = (dynamic or {}).get("ui_controls", [])
        ui_gaps = (dynamic or {}).get("ui_gaps", [])
        context.bus.emit("graph.ready", "the complete graph is ready", step=Union.NAME,
                         **({"ui_controls": ui_controls} if ui_controls else {}),
                         **({"ui_gaps": ui_gaps} if ui_gaps else {}),
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


STEPS = (Scan, Stack, Parse, Analyze, Dynamic, Union)
# What the pipeline is given, the snapshot `write_snapshot` wrote (its inventory, and the files read): every other input of a
# step is the output of a step before it.
INPUTS = ("inventory", "snapshot")


class StepFailed(Exception):
    def __init__(self, cause: str, remedy: str):
        super().__init__(cause)
        self.cause, self.remedy = cause, remedy


def run(manifest: Path, listeners=(), *, start: str | None = None, stop: str | None = None,
        report_path: Path | None = None, fast_scan: bool = False) -> dict:
    import node_preparation
    with node_preparation.analysis():
        return _run(manifest, listeners, start=start, stop=stop, report_path=report_path, fast_scan=fast_scan)


def _run(manifest: Path, listeners, *, start, stop, report_path, fast_scan: bool) -> dict:
    """The steps in order on the snapshot `manifest`, from `start` through `stop` (default: all), with
    `listeners` on the bus and the journal beside it; each step's result by its name. A step that fails says
    why and stops the ones after it: its result is `{"failed": cause, "remedy": ...}`. One the others can do
    without (`WITHOUT`) says why as an error and the run goes on: its result is `{"failed": cause}`, and its
    `step.finished` carries `failed`. An error a step the others need does not foresee is said as `step.failed`
    and reaches the caller, and so is an interruption (Ctrl-C, the interpreter's exit). A `start` or `stop` that
    names no step is refused before any event."""
    names = [step.NAME for step in STEPS]
    for asked in (start, stop):
        if asked is not None and asked not in names:
            raise ValueError(f"no step {asked!r}: the steps are {', '.join(names)}")
    manifest = Path(manifest).resolve()
    bus = events.Bus(manifest.with_name(events.JOURNAL))
    for listener in listeners:
        bus.subscribe(listener)
    context = Context(manifest, bus, report_path, fast_scan=fast_scan)
    chosen = STEPS[names.index(start) if start else 0:names.index(stop) + 1 if stop else len(STEPS)]
    results = context.results
    for step in chosen:
        bus.emit("step.started", step.NAME, step=step.NAME, inputs=list(step.INPUTS))
        failed = None
        try:
            results[step.NAME] = step.run(context)
        except StepFailed as failure:
            bus.emit("step.failed", failure.cause, step=step.NAME, level="error", cause=failure.cause,
                     remedy=failure.remedy)
            results[step.NAME] = {"failed": failure.cause, "remedy": failure.remedy}
            break
        except Exception as error:  # noqa: BLE001 - every step's failure is said, whatever it is
            cause = f"{type(error).__name__}: {error}"
            if step.WITHOUT is None:
                bus.emit("step.failed", cause, step=step.NAME, level="error", cause=cause,
                         remedy="an error the step does not foresee: report it with its cause")
                raise
            bus.emit("log", f"the {step.NAME} step failed: {error}", step=step.NAME, level="error", cause=cause,
                     remedy=step.WITHOUT)
            failed = cause
            results[step.NAME] = {"failed": cause}
        except BaseException as stop:  # an interruption: the step says it ends here, then the run leaves
            cause = f"interrupted: {type(stop).__name__}"
            bus.emit("step.failed", cause, step=step.NAME, level="error", cause=cause,
                     remedy="run the analysis again: this step did not end")
            raise
        bus.emit("step.finished", step.NAME, step=step.NAME, outputs=list(step.OUTPUTS),
                 **({"failed": failed} if failed else {}))
    report = results.get(Analyze.NAME, {})
    if report.get("pass") and Union.NAME in results and "failed" not in results[Union.NAME]:
        import engine_pass
        report["pipeline_complete"] = True
        engine_pass._write_report(report_path or manifest.with_name(engine_pass.REPORT_NAME), report)
    return results


def follow(manifest: Path, after: int = 0, limit: int | None = None) -> tuple[list[dict], int]:
    """The run's events from the cursor `after`, for a listener in another process."""
    return events.read(Path(manifest).resolve().with_name(events.JOURNAL), after, limit)


# The union's gaps that say what a run did not observe (`Union.observed`).
RUNTIME_GAPS = ("tests-not-run", "not-observed", "files-not-executed", "observed-conflict")


def runtime(manifest: Path) -> dict:
    """What the last analysis's dynamic step observed, for a report's runtime coverage: `state` (`running` while
    the analysis may still observe, `not-run` before any union, else `observed` or `none`), per observed
    language its recorder (`resolver`), `sites`, `edges` and holes `closed`, the `files` with calls its tests
    `executed` and those `not_executed` (counts), how each test run ended (`tests`), and the union's `gaps` of
    what stayed unobserved, each with its `language`. `ui_controls`, when present, counts Playwright's
    control/event/state observations independently of placed call edges."""
    import resolve_edges
    manifest = Path(manifest).resolve()
    state = resolve_edges.edge_state(manifest)
    if state.get("state") == "running":
        return {"state": "running", "languages": {}, "gaps": []}
    recorded, _ = events.read(manifest.with_name(events.JOURNAL))
    ready = [n for n, event in enumerate(recorded) if event["kind"] == "graph.ready"]  # each union's last event
    if not ready:
        return {"state": "not-run", "languages": {}, "gaps": []}
    last = recorded[ready[-2] + 1 if len(ready) > 1 else 0:ready[-1]]
    gaps = [{**event["data"]["gap"], "language": event["data"].get("language") or event["data"]["gap"].get("language")}
            for event in last if event["kind"] == "gap" and event["step"] == Union.NAME
            and event["data"].get("gap", {}).get("kind") in RUNTIME_GAPS]
    languages = {}
    for language, entry in sorted((state.get("languages") or {}).items()):
        coverage = entry.get("coverage") or {}
        seen, sampled = coverage.get("observed") or {}, coverage.get("sampled") or {}
        if seen.get("edges") or sampled.get("edges"):
            files = seen.get("files") or {}
            languages[language] = {
                "resolver": seen.get("resolver"), "sites": seen.get("sites", 0), "edges": seen.get("edges", 0),
                "closed": sum((seen.get("closed") or {}).values()),
                "files": {"executed": files.get("executed", 0), "not_executed": len(files.get("not_executed") or ())},
                "tests": [{key: test.get(key) for key in ("root", "runner", "state")}
                          for test in seen.get("tests") or ()]}
            if sampled.get("edges"):
                languages[language]["sampled"] = {"resolver": sampled.get("resolver"), "sites": sampled["sites"],
                                                  "edges": sampled["edges"],
                                                  "closed": sum((sampled.get("closed") or {}).values())}
    last_union = recorded[ready[-1]]["data"]
    ui_controls = last_union.get("ui_controls", [])
    gaps.extend(last_union.get("ui_gaps", []))
    observed = bool(languages) or any(run.get("observed", 0) for run in ui_controls)
    return {"state": "observed" if observed else "none", "languages": languages, "gaps": gaps,
            **({"ui_controls": ui_controls} if ui_controls else {})}
