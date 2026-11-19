"""The derived pass: its analyzers, built from the adapters' declarations (`ENGINES`), its plan, one
stage after another in its own process (`run_pass`), an indexer's stage (`index_stage`), and the pass's state and
lifecycle beside the snapshot (`edge_state`, `ensure_edges`, `reset_pass`, `stop_pass`).

`ENGINES` is built last: an adapter imports `resolve_edges` back, which takes this module's other names."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import NamedTuple

import engine_tools
from snapshot_store import logical_digest, open_snapshot
from engine_tools import free_memory, node_environment
from edge_store import default_edge_store, read_edge_store
from position_stage import MEMORY_EXHAUSTED
from tree_scope import program

SCRIPT_DIR = Path(__file__).resolve().parent


# Files the derived pass leaves beside the edge store.
REPORT_NAME = "engine-report.json"


def running_record(manifest: Path) -> Path:
    """Where the pass over `manifest` records its process, by the manifest's path: in Daodan's shared directory,
    never beside the manifest. The store lies in the analyzed project's folder, where any file may have come with
    the project, and the process this record names is the one a new snapshot ends."""
    key = os.path.normcase(str(Path(manifest).resolve())).encode("utf-8")
    return engine_tools.shared_cache_dir() / "passes" / f"{hashlib.sha256(key).hexdigest()[:32]}.json"


LOG_NAME = "engine-pass.log"


# What to do for a language the snapshot holds and did not parse (`unparsed`).
PARSER_INSTALL = ("install the snapshot's parser packages (requirements.txt beside snapshot.py) and write the "
                  "snapshot again")


def _statuses(connection) -> dict[str, dict[str, int]]:
    """The snapshot's files per language and parse status."""
    held: dict[str, dict[str, int]] = {}
    for language, status, files in connection.execute(
            "SELECT language, status, COUNT(*) FROM sem_coverage WHERE language IS NOT NULL GROUP BY language, status"):
        held.setdefault(language, {})[status] = files
    return held


def pass_languages(connection) -> list[str]:
    """The languages the pass serves: every one the snapshot holds a file of, parsed or not (`unparsed`), and those
    of an analyzer whose graph is built from files of other languages (`SNAPSHOT_LANGUAGES`, the stylesheet graph)
    when the snapshot holds one."""
    import indexers
    held = _statuses(connection)
    present = {language for language, files in held.items() if set(files) - {"excluded"}}
    for analyzer in indexers.analyzers():
        if set(held) & set(getattr(analyzer, "SNAPSHOT_LANGUAGES", ())):
            present.update(analyzer.LANGUAGES)
    return sorted(present)


def unparsed(connection) -> dict[str, str]:
    """The snapshot's languages without one parsed file, each with why: a stage places an index on the snapshot's
    references, which only a parsed file has, so no stage starts for them."""
    out = {}
    for language, files in _statuses(connection).items():
        rest = {status: count for status, count in sorted(files.items()) if status != "excluded"}
        if rest and not {"ast", "partial"} & set(rest):  # a partial file is read around its syntax error
            out[language] = (f"none of the {sum(rest.values())} {language} files was parsed by the snapshot ("
                             + ", ".join(f"{status}: {count}" for status, count in rest.items()) + ")")
    return out


def no_analyzer(connection) -> dict[str, int]:
    """The snapshot's languages no analyzer lists, each with its files: in the snapshot, in no graph. A graph built
    from files of other languages (`SNAPSHOT_LANGUAGES`, the stylesheet graph's) serves a language whose files the
    snapshot reads no code of; the code of one it does read (an Astro file's script) needs an analyzer of its own."""
    import indexers
    from semantic_store import READ
    styles = {language for analyzer in indexers.analyzers() for language in getattr(analyzer, "SNAPSHOT_LANGUAGES", ())}
    counts = {language: sum(count for status, count in files.items() if status != "excluded")
              for language, files in _statuses(connection).items()
              if language not in ENGINE_LANGUAGES and (language not in styles or set(files) & set(READ))}
    return {language: count for language, count in sorted(counts.items()) if count}


def _process_alive(pid: int) -> bool:
    if type(pid) is not int or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def pass_state(manifest: Path) -> dict | None:
    """The pass in flight or the last one finished beside the manifest, without opening it.

    `running` while the recorded process lives; `finished` after a pass that
    reported, with its per-language outcomes; `stopped` after `stop_pass`;
    `failed` when it ended without a report. None when no pass ever started.
    """
    manifest = Path(manifest)
    running = running_record(manifest)
    report = manifest.with_name(REPORT_NAME)
    if running.is_file():
        try:
            marker = json.loads(running.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            marker = {}
        if _process_alive(marker.get("pid")):
            return {"state": "running", "pid": marker.get("pid"), "started_at": marker.get("started_at")}
    if report.is_file():
        try:
            last = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            last = {}
        if last.get("stopped"):
            return {"state": "stopped", "reason": last.get("reason")}
        return {"state": "finished", "languages": last.get("languages") or {}}
    if running.is_file():
        code = marker.get("exit_code")
        return {"state": "failed", "reason": "the engine pass ended without a report"
                + (f" (exit code {code})" if type(code) is int else "") + "; see " + LOG_NAME}
    return None


STATE_ORDER = ("missing", "failed", "fresh", "unavailable")


def edge_state(manifest: Path) -> dict:
    """Report the derived edge store and its pass without touching either.

    `languages` holds one state per snapshot language an engine covers: `fresh`
    from the store, with its `coverage`; `unavailable` or `failed` from the last
    pass; `running` while a pass may still reach it; `missing` otherwise, also when
    the store's entry came from a former source. The overall state is `running`,
    `stopped` or `stale` (store bound to another revision) when one applies, else
    the first of missing, failed, fresh and unavailable that a language holds.
    Every state carries `coverage`, each store entry's by language, and `no_analyzer`
    when the snapshot holds languages no engine covers, each with its files.
    """
    manifest = Path(manifest)
    store_path = default_edge_store(manifest)
    base = {"edges_store": store_path.as_posix()}
    with open_snapshot(manifest) as store:
        if store.format != "sqlite" or store.connection is None:
            return {**base, "state": "unavailable", "format": store.format,
                    "reason": "a JSON manifest holds no reference table"}
        binding, stale = None, None
        if store_path.is_file():
            _edges, loaded, reason = read_edge_store(store_path, store)
            binding, stale = (loaded, None) if reason is None else (None, reason)
        last = pass_state(manifest) or {}
        running = last.get("state") == "running"
        entries = (binding or {}).get("languages") or {}
        outcomes = last.get("languages") or {}
        languages = {}
        for language in pass_languages(store.connection):
            if language not in ENGINE_LANGUAGES:
                continue
            if language in entries and from_source(language, entries[language]):
                entry = entries[language]
                state, outcome = entry["state"], outcomes.get(language) or {}
                if state == "partial":
                    # A pass publishes as it goes: running, then what its stage ended as.
                    state = "running" if running else \
                        outcome["state"] if outcome.get("state") in ("failed", "unavailable") else "failed"
                languages[language] = {"state": state, "engine": entry["engine"], "coverage": entry.get("coverage")}
                if state in ("failed", "unavailable"):
                    languages[language]["reason"] = outcome.get("reason") or (
                        "the pass ended before this language's stage finished; the next pass resumes from what it "
                        "proved")
            elif language in outcomes and not running and outcomes[language]["state"] != "fresh":
                # Only the store proves edges; a report can only say why there are none.
                languages[language] = dict(outcomes[language])
            elif last.get("state") == "failed":
                languages[language] = {"state": "failed", "reason": last.get("reason")}
            else:
                languages[language] = {"state": "running" if running else "missing"}
        if running:
            result = {**base, "state": "running", "pid": last.get("pid"), "started_at": last.get("started_at")}
        elif last.get("state") == "stopped":
            result = {**base, "state": "stopped", "reason": last.get("reason")}
        elif stale is not None:
            result = {**base, "state": "stale", "reason": stale}
        else:
            states = {value["state"] for value in languages.values()}
            state = next((name for name in STATE_ORDER if name in states), "fresh")
            result = {**base, "state": state}
            first = next((value for value in languages.values() if value["state"] == state), {})
            for key in ("reason", "install"):
                if first.get(key):
                    result[key] = first[key]
            if state == "missing" and "reason" not in result:
                result["reason"] = "no engine pass has run for this snapshot"
        if binding is not None:
            result.update(engine=binding.get("engine"), created_at=binding.get("created_at"))
        result["languages"] = languages
        result["coverage"] = {language: entry["coverage"] for language, entry in entries.items()
                              if entry.get("coverage")}
        unserved = no_analyzer(store.connection)
        if unserved:
            result["no_analyzer"] = unserved
        return result


INDEXER_INSTALL = "check the network: Daodan downloads its uv, which runs the pass with the snapshot's parser"


class EngineSpec(NamedTuple):
    """One analyzer of the derived pass: its languages and what its stage environment needs.

    The entry names its adapter module under `indexers/` (`indexer`): its stage runs that indexer and builds
    the graph of its languages (`index_stage`). One that `needs_container` builds the project, which happens
    only in a container: the stage finds the container engine before the indexer starts. A stage needs the
    snapshot's parser, plus the adapter's `REQUIREMENTS` when it declares them (`IMPORT` is the module that
    shows they are there, `INSTALL` what to do without them).
    """

    name: str
    languages: tuple[str, ...]
    requirements: tuple[str, ...]
    module: str
    install: str
    indexer: str = ""
    needs_container: bool = False

    @property
    def min_free(self) -> int:
        """The free memory the stage starts with: its adapter's `MIN_FREE`."""
        return importlib.import_module(f"indexers.{self.indexer}").MIN_FREE


def from_source(language: str, entry: dict) -> bool:
    """Whether a store entry came from the entry that serves `language` now: a stage names its entry
    (`scip-go@v0.2.9`). An entry from a former source is not fresh, so the next pass replaces it."""
    spec = ENGINE_LANGUAGES.get(language)
    return spec is not None and str(entry.get("engine") or "").split("@", 1)[0] == spec.name


def stage_command(spec: EngineSpec, manifest: Path, report_path: Path, *, offline: bool = False) -> list[str] | None:
    """The command that runs one engine's stage with the snapshot's parser set.

    uv gives the stage an environment with the engine's requirements plus this
    interpreter's Python minor and exact parser packages, so the stage reproduces
    the parser fingerprint of the snapshot whichever environment wrote it, and the
    environment lives exactly as long as the stage. `offline` keeps uv from the
    network, for an environment already in its cache. uv is Daodan's pin, never the
    PATH's, run as Daodan's own (`engine_tools.uv_options`) outside the project (the
    stage's folder). Without the pin, this interpreter runs the stage when it can
    import the engine. None when neither can.
    """
    import contextlib
    import engine_tools
    import snapshot
    script = [str(SCRIPT_DIR / "resolve_edges.py"), str(manifest), "--engine", spec.name, "--compact",
              "--report-out", str(report_path)]
    try:
        with contextlib.redirect_stdout(sys.stderr):  # its first install's line is no server's output
            uv = str(engine_tools.uv_binary())
    except OSError:
        uv = None
    if uv:
        pins = []
        for package in snapshot.PARSER_PACKAGES:
            try:
                pins.extend(["--with", f"{package}=={metadata.version(package)}"])
            except metadata.PackageNotFoundError:
                continue
        requirements = [item for requirement in spec.requirements for item in ("--with", requirement)]
        return [uv, "run", "--quiet", *engine_tools.uv_options(), "--no-project",
                *(["--offline"] if offline else []),
                "--python", f"{sys.version_info[0]}.{sys.version_info[1]}",
                *requirements, *pins, "python", "-B", "-X", "faulthandler", *script]
    if importlib.util.find_spec(spec.module) is not None:
        # faulthandler puts a hard crash's traceback in the pass log.
        return [sys.executable, "-B", "-X", "faulthandler", *script]
    return None


def cached_offline(spec: EngineSpec, manifest: Path, report_path: Path) -> bool:
    """Whether the stage's environment is already in uv's cache, so the stage runs with no network at all.

    Only the first stage of an engine on a machine reaches the package index.
    """
    command = stage_command(spec, manifest, report_path, offline=True)
    if not command or "--offline" not in command:
        return False
    head = command[:command.index("python") + 1]
    try:
        return subprocess.run([*head, "-c", f"import {spec.module}"], cwd=str(SCRIPT_DIR), stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=120).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def engine_command(manifest: Path, report_path: Path) -> list[str]:
    """The detached pass: this interpreter runs one stage per engine, one after another."""
    return [sys.executable, "-B", "-X", "faulthandler", str(SCRIPT_DIR / "resolve_edges.py"), str(manifest),
            "--pass", "--report-out", str(report_path)]


def pass_plan(manifest: Path) -> tuple[list[tuple[EngineSpec, list[str]]], dict, str]:
    """The engines whose languages the snapshot holds parsed, with the entries already fresh."""
    manifest = Path(manifest)
    with open_snapshot(manifest) as store:
        present = set(pass_languages(store.connection)) - set(unparsed(store.connection))
        digest = logical_digest(store)
        fresh = {}
        if default_edge_store(manifest).is_file():
            _edges, binding, reason = read_edge_store(default_edge_store(manifest), store)
            if reason is None:
                fresh = {language: entry for language, entry in (binding.get("languages") or {}).items()
                         if entry.get("state") == "fresh" and from_source(language, entry)}
    plan = [(spec, [language for language in spec.languages
                    if language in present and ENGINE_LANGUAGES.get(language) is spec]) for spec in ENGINES]
    return [(spec, wanted) for spec, wanted in plan if wanted], fresh, digest


def run_pass(manifest: Path, report_path: Path, bus=None) -> dict:
    """Run each engine's stage in turn and record per language what came of it.

    A language already fresh in the store is not asked again; one the snapshot did
    not parse is `unavailable`, with no stage. Before a stage the free memory is
    checked; after a stage that ran out of memory no other starts.
    The report is rewritten after every stage, so the state shows progress, and
    each analyzer says on `bus` (`pipeline.events`) when it starts and how it ends.
    """
    from pipeline import events
    manifest = Path(manifest).resolve()
    bus = bus or events.Bus(manifest.with_name(events.JOURNAL))
    plan, fresh, digest = pass_plan(manifest)
    report = {"pass": True, "manifest_digest": digest, "languages": {}, "engines": {},
              "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    outcomes = report["languages"]
    with open_snapshot(manifest) as store:
        skipped = unparsed(store.connection)
    for language, reason in sorted(skipped.items()):
        if language in ENGINE_LANGUAGES:
            _not_fresh(bus, ENGINE_LANGUAGES[language], [language], outcomes, "unavailable", reason, PARSER_INSTALL)
    exhausted = None
    for number, (spec, wanted) in enumerate(plan, 1):
        bus.progress("analyze", number - 1, len(plan), analyzer=spec.name, message=f"{spec.name}: {', '.join(wanted)}")
        if all(language in fresh for language in wanted):
            outcomes.update({language: {"state": "fresh", "engine": fresh[language]["engine"]} for language in wanted})
            bus.emit("analyzer.finished", f"{spec.name}: already fresh", step="analyze", analyzer=spec.name,
                     languages=wanted, fresh=True)
            continue
        bus.emit("analyzer.started", f"{spec.name} for {', '.join(wanted)}", step="analyze", analyzer=spec.name,
                 languages=wanted)
        free = free_memory()
        if exhausted:
            reason, state, install = f"not started: {exhausted}", "failed", None
        elif free is not None and free < spec.min_free:
            reason, state, install = (f"{free / 2**30:.1f} GB of memory free; {spec.name} starts with at least "
                                      f"{spec.min_free / 2**30:.1f} GB"), "failed", None
        else:
            state, reason, install, stage = _launch(spec, wanted, manifest)
            if stage is not None:
                report["engines"][spec.name] = compact_report(stage)
                for gap in stage.get("gaps") or ():
                    bus.emit("gap", gap.get("detail") or gap["kind"], step="analyze", analyzer=spec.name, gap=gap)
                if stage.get("memory_exhausted"):
                    exhausted = f"the {spec.name} engine ran out of memory"
            if state is None:
                for language in wanted:
                    # Only what the stage reports is fresh: a language it does not list has no outcome.
                    entry = (stage.get("languages") or {}).get(language) or {
                        "state": "missing", "reason": f"the {spec.name} stage reported no outcome for {language}"}
                    outcomes[language] = {"state": entry["state"], "engine": stage.get("engine"),
                                          **({"reason": entry["reason"]} if entry.get("reason") else {})}
                _write_report(report_path, report)
                bus.emit("analyzer.finished", f"{stage.get('engine')}: {', '.join(wanted)}", step="analyze",
                         analyzer=spec.name, languages=wanted, engine=stage.get("engine"))
                continue
        _not_fresh(bus, spec, wanted, outcomes, state, reason, install)
        _write_report(report_path, report)
    report["available"] = any(outcome["state"] == "fresh" for outcome in outcomes.values())
    report["finished_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bus.progress("analyze", len(plan), len(plan))
    _write_report(report_path, report)
    return report


def _launch(spec: EngineSpec, wanted: list[str], manifest: Path) -> tuple[str | None, str | None, str | None,
                                                                       dict | None]:
    """One stage in its own process: its state (None once it succeeded), reason, install and report."""
    stage_report = manifest.with_name(f".engine-stage-{spec.name}.json")
    stage_report.unlink(missing_ok=True)
    command = stage_command(spec, manifest, stage_report, offline=cached_offline(spec, manifest, stage_report))
    if command is None:
        return "unavailable", f"neither uv nor {spec.module} is available to {sys.executable}", spec.install, None
    print(f"engine pass: {spec.name} for {', '.join(wanted)}", flush=True)
    completed = subprocess.run(command, stdin=subprocess.DEVNULL, cwd=str(SCRIPT_DIR),
                               env={**os.environ, **node_environment()})
    try:
        stage = json.loads(stage_report.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stage = None
    stage_report.unlink(missing_ok=True)
    if stage is None:
        return "failed", (f"the {spec.name} stage exited with code {completed.returncode} without a report; "
                          f"see {LOG_NAME}"), None, {"memory_exhausted": bool(MEMORY_EXHAUSTED.search(
                              _log_tail(manifest)))}
    if stage.get("available"):
        return None, None, None, stage
    install = stage.get("install")
    return ("unavailable" if install else "failed"), stage.get("reason"), install, stage


def _not_fresh(bus, spec: EngineSpec, wanted: list[str], outcomes: dict, state: str, reason, install) -> None:
    """A stage that is unavailable here or failed: its event and its languages' outcomes."""
    if state == "unavailable":
        bus.emit("analyzer.unavailable", f"{spec.name} cannot run here", step="analyze", analyzer=spec.name,
                 level="warning", cause=reason, remedy=install, languages=wanted)
    else:
        bus.emit("analyzer.finished", f"{spec.name} failed", step="analyze", analyzer=spec.name, level="error",
                 cause=reason, remedy=f"see {LOG_NAME} beside the snapshot", languages=wanted)
    for language in wanted:
        outcomes[language] = {key: value for key, value in
                              (("state", state), ("engine", spec.name), ("reason", reason), ("install", install))
                              if value is not None}


def index_stage(spec: EngineSpec, manifest: Path, project_root: Path, out: Path | None = None) -> dict:
    """An indexer's stage: its index of the project, the graph of each of its languages the snapshot holds,
    saved in the store beside the other languages' entries (`code_graph.write_store`).

    The indexer works in a directory removed after the stage. One that `needs_container` gets its engine here:
    without one its languages are `unavailable` and the indexer never starts. The report holds `available`,
    `engine` (the resolver: the entry's name, `@`, the indexer's version), `indexer` and `languages`; without
    an index, the indexer's `reason` and, when it is `unavailable`, its `install`; `gaps`, what the indexer's
    preparation could not do (a restore, a toolchain) and each build, unit or run that gave no index
    (`_not_indexed`), which the pass says on the bus. A language none of whose files is in the index is `failed`
    with the commonest cause, and the store gets no entry for it: a gap too, beside a language that is fresh.

    An analyzer that `READS` files by suffix is handed the snapshot's (`files`); one whose outcome is a `graph` of
    its own, no index (`indexers/css.py`), gives the store's rows itself (`rows`).
    """
    import code_graph
    import premap
    module = importlib.import_module(f"indexers.{spec.indexer}")
    # The pre-map first: an indexer takes the project's structure from it and looks for no manifest itself.
    import preparation
    record = premap.ensure(Path(manifest))
    options = module.structure(record) if hasattr(module, "structure") else {}
    # The hosts the project declares for its dependencies, which the preparation of an indexer that builds in a
    # container reaches, as a CI does.
    declared = preparation.declared(record)
    if spec.needs_container:
        options["declared"] = declared
    if hasattr(module, "READS"):
        with code_graph.Snapshot(manifest) as snap:
            options["files"] = sorted(rel for rel in snap.checkout.values() if Path(rel).suffix.lower() in module.READS)
    if spec.needs_container:
        import container
        try:
            options["engine"] = container.find_engine()
        except container.Gap as gap:
            if options.get("roots") or options.get("units"):  # with nothing to build, the indexer says that
                return {"available": False, "engine": spec.name,
                        "reason": f"the build runs only in a container: {gap.cause}", "install": gap.remedy}
    work = Path(tempfile.mkdtemp(prefix=f"daodan-{spec.name}-"))
    try:
        result = module.index(Path(project_root), work, **options)
        indexer = result.get("indexer") or {}
        # The entry names the source: rust-analyzer is also an engine, and scip-java indexes Kotlin too.
        resolver = f"{spec.name}@{indexer.get('version')}"
        gaps = [*(result.get("gaps") or ()), *_not_indexed(result, options.get("roots"))]
        gaps += preparation.unreached(gaps, declared)
        gaps = {"gaps": gaps} if gaps else {}
        if result.get("state"):
            return {"available": False, "engine": resolver, "indexer": indexer, "reason": result.get("reason"),
                    **({"install": result.get("install")} if result["state"] == "unavailable" else {}), **gaps}
        built, rows = {}, {}
        try:
            with code_graph.Snapshot(manifest) as snap:
                if result.get("graph"):
                    rows[result["graph"]["language"]] = (*module.rows(result["graph"], resolver), indexer)
                else:
                    index = code_graph.Index(snap.root)
                    for path, prefix in result["indexes"]:
                        index.load(Path(path), prefix)
                    hops, traversal, _prepared = code_graph.adapter_traversal(module, index, snap)
                    static = module.static(index) if hasattr(module, "static") else None
                    # Kotlin's `missing` and `refine` also read the compile tasks its run brought back.
                    extra = (module.tasks(result.get("configs")),) if hasattr(module, "tasks") else ()
                    refine = (lambda read, graph: module.refine(read, graph, *extra)) if hasattr(module, "refine") \
                        else None
                    for language in spec.languages:
                        rels = sorted(snap.checkout[rel] for rel in snap.inventory
                                      if snap.languages.get(rel) == language and rel in snap.checkout)
                        if not rels:
                            continue
                        absent = [rel for rel in rels if rel not in index.documents]
                        reasons = module.missing(index, absent, *extra) if hasattr(module, "missing") and absent \
                            else {}
                        built[language] = code_graph.build(index, snap, language, hops, indexer, reasons, traversal,
                                                           static, refine=refine)
                # An index that holds none of a language's files proves nothing of it; when the adapter says
                # nothing failed for any of them (`nothing_failed`: no build compiles one), it is `unavailable`.
                failed = {language: _none_indexed(language, graph["files"])
                          for language, (graph, _references) in built.items() if not graph["files"]["indexed"]}
                quiet = {language for language in failed if hasattr(module, "nothing_failed") and all(
                    module.nothing_failed(item["reason"]) for item in built[language][0]["files"]["missing"])}
                built = {language: made for language, made in built.items() if language not in failed}
                if built or rows or not failed:
                    code_graph.write_store(snap, out or default_edge_store(manifest), built, resolver, rows)
        except ValueError as error:  # a changed source, or a store that would break sites = answered + holes
            return {"available": False, "engine": resolver, "indexer": indexer, "reason": str(error)}
        if failed and not (built or rows):
            return {"available": False, "engine": resolver, "indexer": indexer, "reason": "; ".join(failed.values()),
                    **({"install": "none: no build compiles these files"} if set(failed) <= quiet else {}), **gaps}
        states = {**{language: {"state": "fresh"} for language in {**built, **rows}},
                  **{language: {"state": "unavailable" if language in quiet else "failed", "reason": reason}
                     for language, reason in failed.items()}}
        noted = [*gaps.get("gaps", ()), *({"kind": "language_not_indexed", "language": language, "detail": reason}
                                          for language, reason in failed.items())]
        return {"available": True, "engine": resolver, "indexer": indexer, "languages": states,
                **({"gaps": noted} if noted else {})}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _none_indexed(language: str, files: dict) -> str:
    """Why a language is not fresh when the index holds none of its files: their count and the commonest causes."""
    import collections
    causes = collections.Counter(item["reason"] for item in files["missing"]).most_common(3)
    return (f"none of the {files['snapshot']} {language} files is in the index: "
            + ", ".join(f"{reason} ({count})" for reason, count in causes))


def _not_indexed(result: dict, roots) -> list[dict]:
    """The builds, units and runs of an indexer's contract that gave no index, each as a gap: another one's index
    keeps the language fresh, and this one's cause would be gone. A contract that names its `builds` or `units`
    gives their state; one with `runs` only, the runs without an index. A cause the contract's `reason` already
    says is not said twice. `code_graph.module_runs` runs first at the checkout's root whatever it holds: where no
    manifest is there (`roots`), that run's failure is no loss."""
    said, gaps = result.get("reason") or "", []
    named = [*(result.get("builds") or ()), *(result.get("units") or ())]
    for item in named:
        cause = item.get("reason") or item.get("cause") or "no index"
        if item["state"] not in ("done", "indexed") and cause not in said:
            gaps.append({"kind": "build_not_indexed", "path": item["root"], "state": item["state"],
                         "detail": f"{item['root'] or '.'}: {item['state']}: {cause}"})
    for run in () if named else result.get("runs") or ():
        if "index" not in run or run["index"] or (not run.get("prefix") and roots and "" not in roots):
            continue
        tail = (run.get("stderr_tail") or run.get("stdout_tail") or "").strip().splitlines()
        if tail and tail[-1] in said:
            continue
        gaps.append({"kind": "build_not_indexed", "path": run.get("prefix") or "", "state": "failed",
                     "detail": f"{run.get('prefix') or '.'}: no index (exit code {run.get('returncode')})"
                               + (f": {tail[-1][:300]}" if tail else "")})
    return gaps


def _log_tail(manifest: Path, size: int = 65536) -> str:
    try:
        with manifest.with_name(LOG_NAME).open("rb") as log:
            log.seek(0, os.SEEK_END)
            log.seek(max(log.tell() - size, 0))
            return log.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def _spawn_detached(command: list[str], log) -> subprocess.Popen:
    options = {"stdin": subprocess.DEVNULL, "stdout": log, "stderr": log, "cwd": str(SCRIPT_DIR),
               "close_fds": True}
    if os.name != "nt":
        return subprocess.Popen(command, start_new_session=True, **options)
    detached = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    try:
        # Outlive a host that closes its job object when the calling command ends.
        return subprocess.Popen(command, creationflags=detached | 0x01000000, **options)
    except OSError:
        # The job forbids breaking away: the pass lives as long as the host.
        return subprocess.Popen(command, creationflags=detached, **options)


def _terminate_tree(pid: int) -> None:
    """End the pass and the interpreter it started, which a plain kill would orphan."""
    if os.name == "nt":
        taskkill = program("taskkill")  # never the name alone: Windows looks for it in the working directory first
        if taskkill is None:
            raise OSError("taskkill is in no folder of the PATH")
        result = subprocess.run([taskkill, "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)
        if result.returncode and _process_alive(pid):
            raise OSError(result.stderr.strip() or result.stdout.strip())
        return
    os.killpg(pid, signal.SIGTERM)


def _write_report(path: Path, report: dict) -> None:
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_edges(manifest: Path, *, check: bool = False) -> dict:
    """Start the pass unless `check`, when some engine language is neither fresh nor settled.

    The pass is a detached child (`engine_command`) that runs one stage per engine
    and leaves the store, its report and a log beside the manifest, so a run is
    usable at once and its graph gains each language's edges as its stage lands.
    `fresh`, `running`, `stopped` and `unavailable` start nothing: only a new
    snapshot reopens them. When no stage could start, the report says so and no
    process is spawned. Returns the state plus `action`: `none`, `reported` or `started`.
    """
    manifest = Path(manifest).resolve()
    before = edge_state(manifest)
    if before["state"] in ("fresh", "running", "stopped", "unavailable") or before.get("format") == "json":
        return {**before, "action": "none"}
    if check:
        return {**before, "action": "reported"}
    report_path = manifest.with_name(REPORT_NAME)
    running_path = running_record(manifest)
    for leftover in (report_path, running_path):
        leftover.unlink(missing_ok=True)
    plan, fresh, digest = pass_plan(manifest)
    pending = [(spec, wanted) for spec, wanted in plan if not all(language in fresh for language in wanted)]
    if pending and all(stage_command(spec, manifest, report_path) is None for spec, _ in pending):
        outcomes = {language: {"state": "fresh", "engine": entry["engine"]} for language, entry in fresh.items()}
        for spec, wanted in pending:
            outcomes.update({language: {"state": "unavailable", "engine": spec.name, "install": spec.install,
                                        "reason": f"neither uv nor {spec.module} is available to {sys.executable}"}
                             for language in wanted})
        _write_report(report_path, {"pass": True, "manifest_digest": digest, "available": False,
                                    "languages": outcomes, "engines": {}})
        return {**edge_state(manifest), "action": "none"}
    with manifest.with_name(LOG_NAME).open("ab") as log:
        try:
            running_path.parent.mkdir(parents=True, exist_ok=True)  # before the pass: one started is one recorded
            child = _spawn_detached(engine_command(manifest, report_path), log)
        except OSError as error:
            _write_report(report_path, {"pass": True, "manifest_digest": digest, "available": False,
                                        "languages": {language: {"state": "failed", "reason":
                                                                 f"could not start the engine pass: {error}"}
                                                      for _spec, wanted in pending for language in wanted},
                                        "engines": {}})
            return {**edge_state(manifest), "action": "none"}
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    running_path.write_text(json.dumps({"pid": child.pid, "started_at": started}) + "\n", encoding="utf-8")
    threading.Thread(target=_note_exit, args=(child, running_path), daemon=True).start()
    return {**edge_state(manifest), "action": "started"}


def deaf_to_console_break() -> None:
    """On Windows a Ctrl+Break sent to a console ends, with no word and exit code 0xC000013A, every Python attached
    to it that does not handle it: so ended the pass on 18 November 2026, beside the programs it starts. The pass
    is no console program: it says that one came and goes on. Elsewhere there is no such signal."""
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, lambda number, frame: print(
            "a console break reached the pass and was ignored", file=sys.stderr, flush=True))


def _note_exit(child, record: Path) -> None:
    """While the process that started the pass lives, it waits for it and keeps its exit code in the record: a
    pass ended from outside writes nothing, and on POSIX one nobody waits for stays a process that answers."""
    code = child.wait()
    try:
        marker = json.loads(record.read_text(encoding="utf-8"))
        if type(code) is int and marker.get("pid") == child.pid:
            record.write_text(json.dumps({**marker, "exit_code": code}) + "\n", encoding="utf-8")
    except (OSError, ValueError):
        pass  # the record is another pass's by now, or gone with its snapshot


def reset_pass(manifest: Path) -> dict | None:
    """Clear the previous revision's pass before a snapshot replaces its manifest.

    A running pass holds the manifest open, which on Windows refuses the
    replacement, and its result would describe the old revision anyway. Ends it,
    removes its marker, report, stage reports and partial store, and returns what it found.
    """
    manifest = Path(manifest)
    last = pass_state(manifest)
    if last is not None and last["state"] == "running":
        _terminate_tree(last["pid"])
    for record in (running_record(manifest), manifest.with_name(REPORT_NAME)):
        record.unlink(missing_ok=True)
    for pattern in (f".{default_edge_store(manifest).name}.*.partial", ".engine-stage-*.json"):
        for leftover in manifest.parent.glob(pattern):
            leftover.unlink(missing_ok=True)
    return last


def stop_pass(manifest: Path, reason: str) -> dict:
    """End a running pass with its stages and servers, and record it as stopped, so no repair restarts it."""
    manifest = Path(manifest).resolve()
    last = pass_state(manifest)
    if last is None or last["state"] != "running":
        return {"stopped": False, "state": (last or {}).get("state", "missing")}
    try:
        _terminate_tree(last["pid"])
    except OSError as error:
        return {"stopped": False, "state": "running", "reason": f"could not stop pid {last['pid']}: {error}"}
    _write_report(manifest.with_name(REPORT_NAME),
                  {"pass": True, "available": False, "stopped": True, "reason": f"stopped: {reason}"})
    # The report is the record now; a dying process must not read as running.
    running_record(manifest).unlink(missing_ok=True)
    return {"stopped": True, "state": "stopped", "pid": last["pid"]}


def compact_report(report: dict, *, report_out: Path | None = None) -> dict:
    """Bounded summary for CLI/coordinator callers when the full report is on disk."""
    summary = {
        key: report[key]
        for key in (
            "engine", "available", "reason", "stage", "install", "project_root", "languages",
            "population", "population_language", "selected", "asked", "reused", "answer_cache", "stride",
            "confirmed_edges", "candidates", "no_edges_reason", "position_unverified",
            "excluded_classes", "coverage", "verdicts", "memory_exhausted",
            "source_verification", "probe_init_elapsed_ms", "inference_elapsed_ms",
            "total_elapsed_ms", "latency_mean_ms", "latency_p95_ms", "dry_run",
            "edges_store", "coverage", "indexer", "gaps",
        )
        if key in report
    }
    if report_out is not None:
        summary["report_out"] = report_out.as_posix()
    return summary


# The analyzers (docs/plans/2026-11-14-grafo-dall-indice.md), each from its adapter's own declaration.
ENGINES = tuple(EngineSpec(analyzer.ENTRY, tuple(analyzer.LANGUAGES), tuple(getattr(analyzer, "REQUIREMENTS", ())),
                           getattr(analyzer, "IMPORT", "tree_sitter"), getattr(analyzer, "INSTALL", INDEXER_INSTALL),
                           analyzer.__name__.rsplit(".", 1)[-1], needs_container=analyzer.NEEDS_CONTAINER)
                for analyzer in __import__("indexers").analyzers())
# Each language's engine: the first entry that lists it.
ENGINE_LANGUAGES = {language: spec for spec in reversed(ENGINES) for language in spec.languages}
