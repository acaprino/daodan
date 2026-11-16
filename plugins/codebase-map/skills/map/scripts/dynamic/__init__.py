"""The dynamic step: the project's tests run in a container under a recorder, and what they call enters the graph.

An observer is one module of this package per technology. It declares `ENTRY`, `VERSION` (its recorder's: the
observed rows' resolver is `ENTRY@VERSION`) and `LANGUAGES`, and gives:

    plan(record, files, read) -> {"runs": [...], "gaps": [...]}   what to run, from the pre-map alone
    observe(project, planned, out_dir, engine) -> {"state", "sites", "sampled", "runs", "gaps"}   in the container
    external(callee) -> {"manager", "package", "version"}          the package of a callee outside the project

`plan` takes the command that runs the tests from what the project declares (the pre-map's `tests`), never from a
convention; with nothing to run it says why, and no container starts. `observe` runs project code, so only through
`container.run_in_container`: the dependencies restored the project's own way in the preparation, with the
registries, the tests in the execution, with no network. `state` is `ran`, or `gap` with `cause` and `remedy`
when no container could run. A site is `{file, line, column, name, role, callees}`: the file from the project's
root, the line from 0 and the byte column of the callee's name; a callee is `{kind: "project", file, line,
column, name, type}` (the declaration's line from 0 and byte column, as the snapshot has it; with no column,
the one function of that name on that line) or one outside the project, and may carry `wraps` (the callee it
stands for) or `mock`.

`sites` are an exact recorder's: every call, with its caller and callee, at its site. A sampling profiler of
the toolchain is a second source, declared apart: its pairs are `sampled`, each `{caller, callee, line}` of one
stack, `caller` a project function as a callee is written, `callee` a callee, `line` the line from 0 of the call
in the caller's file, or None when the profiler gives none. An observer gives what it has; with no exact site,
the run says nothing of the files it did not execute.

`run` is the step (`pipeline.Dynamic`); `join` places the sites on the snapshot's references, by position,
`join_sampled` the pairs, by line and name, and `code_graph.write_observed` saves the rows. An observed end
holds for the run that produced it: it proves that a call can arrive there, not that it arrives only there, and
a call no test executed stays as the static steps left it. A sampled one says the same with resolver
`ENTRY@VERSION:sampled` and confidence `sampled`; it is never set against a proven edge and says nothing of the
calls and files no sample named. A language with no observer, a project with no declared test command, a run
with no container engine are gaps, never silence. `DAODAN_DYNAMIC=off` skips the step.

See docs/specs/2026-11-12-passo-dinamico.md, sections 5 and 7.
"""
from __future__ import annotations

import collections
import json
import os
from datetime import datetime, timezone
from pathlib import Path

STEP = "dynamic"
RUNS = "dynamic-runs"  # beside the manifest: each observer's container record, logs and observation files
EXAMPLES = 20


def observers() -> list:
    """Every module of this package that declares itself an observer, by its entry's name."""
    import importlib
    import pkgutil
    found = []
    for item in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{item.name}")
        if hasattr(module, "ENTRY"):
            found.append(module)
    return sorted(found, key=lambda module: module.ENTRY)


def resolver(observer, sampled: bool = False) -> str:
    """The resolver of an observer's rows, named as an analyzer's: the recorder and its version; of its sampled
    rows, the same with `:sampled`."""
    return f"{observer.ENTRY}@{observer.VERSION}" + (":sampled" if sampled else "")


def _declared(snapshot, rel: str, line: int, column: int | None, name: str) -> str | None:
    """The snapshot's declaration at a function's line from 1 and byte column; with no column (a profiler's
    frame), the only one of that name on that line."""
    if column is not None:
        return snapshot.function_at(rel, line, column)
    found = snapshot.connection.execute(
        "SELECT id FROM sem_declarations WHERE file = ? AND l0 = ? AND name = ? AND kind IN ('function','method',"
        "'class')", (rel, line, name)).fetchall()
    return found[0][0] if len(found) == 1 else None


def _end(snapshot, callee: dict, external) -> dict:
    """The end a callee is: the project function it wraps when it is a wrapper, a declaration of the snapshot
    (`project-callable`), a project callable the snapshot does not declare (`project-value`), or an external."""
    inner, depth = callee, 0
    while inner.get("wraps"):
        inner, depth = inner["wraps"], depth + 1
    chain, detail = [], ""
    if depth and inner["kind"] == "project":
        chain, detail = ["wraps"] * depth, f"through {callee.get('file') or callee.get('module')}::{callee['name']}"
        callee = inner
    if callee["kind"] != "project":
        package = external(callee)
        return {"verdict": "external", "target_id": None, "external": package, "chain": chain, "detail": detail,
                "symbol": f"{package['manager']} {package['package']} {package['version']} "
                          f"{callee.get('module')}.{callee['name']}"}
    rel = snapshot.rel.get(callee["file"], callee["file"])
    target = _declared(snapshot, rel, callee["line"] + 1, callee.get("column"), callee["name"])
    target = snapshot.constructs.get(target, target)
    return {"verdict": "project-callable" if target else "project-value", "target_id": target, "external": None,
            "symbol": f"{callee['file']}::{callee['name']}", "chain": chain,
            "detail": detail or ("" if target else f"{callee['type']} without a declaration in the snapshot")}


def join(snapshot, language: str, sites: list[dict], edges: list[dict], observer) -> tuple[list[dict], dict]:
    """The observed rows of `language` and what the join says of itself.

    A site answers the reference whose callee name is at the same place (file, line, byte column) with the same
    name: a call reference takes the sites reached as calls, a read any (a property runs on a read); a reference
    with a computed callee takes the call site that starts where it does. Each callee is an end (`_end`), one row
    per end; a mock is no destination. Against the proven rows of the same reference in `edges` (the static
    ones, `confirmed`): an observed end among the proven targets agrees (`wider` when the run saw others too); a
    proven target with no observed end among them, or a proven external where the run reached the project, is a
    conflict, counted with examples and marked on the rows, which are saved all the same: neither side is chosen.

    The facts: `recorded` sites of the language's files, `placed` on a reference and `unjoined` by role (implicit
    calls the snapshot lists no reference for), `joined` references, `agree`, `wider`, `mocked`, `conflicts`
    and `files`, the ones a run executed against the ones with calls that none did.
    """
    from edge_store import OBSERVED
    name = resolver(observer)
    at = collections.defaultdict(list)
    for site in sites:
        rel = snapshot.rel.get(site["file"])
        if rel is not None and snapshot.languages.get(rel) == language:
            at[(rel, site["line"] + 1, site["column"])].append(site)
    proven = collections.defaultdict(list)
    for edge in edges:
        if edge.get("reference_id") is not None and edge["confidence"] == "confirmed":
            proven[edge["reference_id"]].append(edge)
    callers = dict(snapshot.connection.execute("SELECT id, caller FROM sem_references"))
    rows, placed, called = [], set(), set()
    counts, conflicts = collections.Counter(), []
    for identity, rel, kind, _resolution, _target, span, parts, _reason in snapshot.references(language):
        if kind == "call":
            called.add(rel)
        position = snapshot.callee(rel, span, parts)
        if position is not None:
            found = [site for site in at.get((rel, *position), ()) if site["name"] == parts[-1]
                     and (kind == "read" or site["role"] == "call")]
        else:
            found = [site for site in at.get((rel, span[0], span[1]), ()) if not parts and site["name"] == ""
                     and site["role"] == "call"]
        if not found:
            continue
        placed.update(id(site) for site in found)
        callees = list({json.dumps(callee, sort_keys=True): callee
                        for site in found for callee in site["callees"]}.values())
        real = [callee for callee in callees if not callee.get("mock")]
        if not real:
            counts["mocked"] += 1
            continue
        ends = list({(end["verdict"], end["symbol"], tuple(end["chain"])): end
                     for end in (_end(snapshot, callee, observer.external) for callee in real)}.values())
        counts["joined"] += 1
        targets = {row["target_id"] for row in proven[identity] if row["verdict"] == "project-callable"}
        packages = {(row.get("external") or {}).get("package") or "external"
                    for row in proven[identity] if row["verdict"] == "external"}
        reached = {end["target_id"] for end in ends if end["verdict"] == "project-callable"}
        conflict = bool(targets and not targets & reached) or bool(
            not targets and packages and any(end["verdict"] != "external" for end in ends))
        if conflict:
            site = f"{snapshot.checkout.get(rel, rel)}:{span[0]} {parts[-1] if parts else ''}".rstrip()
            conflicts.append({"site": site, "proven": sorted(targets) or sorted(packages),
                              "observed": sorted(end["target_id"] or end["symbol"] for end in ends)})
        elif targets:
            counts["wider" if reached - targets else "agree"] += 1
        elif packages:
            counts["agree"] += 1
        place = {"reference_id": identity, "file": rel, "language": language, "kind": kind,
                 "caller": callers[identity], "l0": span[0], "c0": span[1], "resolver": name, "confidence": OBSERVED}
        rows += [{**place, "verdict": end["verdict"], "target_id": end["target_id"], "symbol": end["symbol"],
                  "external": end["external"], "payload": {"chain": end["chain"], "detail": end["detail"],
                                                           **({"conflict": True} if conflict else {})}}
                 for end in ends]
    recorded = [site for group in at.values() for site in group]
    executed = {rel for rel, _line, _column in at}
    facts = {"recorded": len(recorded), "placed": len(placed), "joined": counts["joined"],
             "unjoined": dict(sorted(collections.Counter(site["role"] for site in recorded
                                                         if id(site) not in placed).items())),
             "agree": counts["agree"], "wider": counts["wider"], "mocked": counts["mocked"],
             "conflicts": {"count": len(conflicts), "examples": conflicts[:EXAMPLES]},
             "files": {"executed": len(executed),
                       "not_executed": sorted(snapshot.checkout.get(rel, rel) for rel in called - executed)}}
    return rows, facts


def join_sampled(snapshot, language: str, pairs: list[dict], observer) -> tuple[list[dict], dict]:
    """The sampled rows of `language` and what the join says of itself.

    A pair whose caller is a function of the language's files answers the reference of that caller whose span
    holds the pair's line and whose last name is the callee's, when there is one only. Any other is a row with no
    reference: an edge between the caller's declaration (`caller`, None at a module's top) and the callee's end
    (`_end`), with the line when the profiler gave it, that answers no reference and closes no hole; its
    `payload.unplaced` says why: `no-line`, `not-found` (no call of that name there), `ambiguous`. No pair is
    set against a proven row: what a sample did not see is no fact.

    The facts: the `pairs` of the language's files, `placed` on a reference, `unplaced` by cause.
    """
    from edge_store import SAMPLED
    name = resolver(observer, sampled=True)
    callers = dict(snapshot.connection.execute("SELECT id, caller FROM sem_references"))
    named = collections.defaultdict(list)
    for identity, rel, kind, _resolution, _target, span, parts, _reason in snapshot.references(language):
        if parts:
            named[(rel, parts[-1])].append((identity, kind, span))
    rows, counts, unplaced = {}, collections.Counter(), collections.Counter()
    for pair in pairs:
        caller, callee, line = pair["caller"], pair["callee"], pair.get("line")
        rel = snapshot.rel.get(caller["file"])
        if rel is None or snapshot.languages.get(rel) != language:
            continue
        counts["pairs"] += 1
        source = _declared(snapshot, rel, caller["line"] + 1, caller.get("column"), caller["name"])
        found = [(identity, kind, span) for identity, kind, span in named[(rel, callee["name"])]
                 if line is not None and span[0] <= line + 1 <= span[2] and callers[identity] == source]
        end = _end(snapshot, callee, observer.external)
        payload = {"chain": end["chain"], "detail": end["detail"]}
        if len(found) == 1:
            [(identity, kind, span)] = found
            counts["placed"] += 1
            place = {"reference_id": identity, "kind": kind, "caller": source, "l0": span[0], "c0": span[1]}
        else:
            cause = "no-line" if line is None else "ambiguous" if found else "not-found"
            unplaced[cause] += 1
            place = {"reference_id": None, "kind": "call", "caller": source, "l0": None if line is None else line + 1,
                     "c0": None}
            payload["unplaced"] = cause
        row = {**place, "file": rel, "language": language, "verdict": end["verdict"], "target_id": end["target_id"],
               "symbol": end["symbol"], "external": end["external"], "resolver": name, "confidence": SAMPLED,
               "payload": payload}
        rows.setdefault((row["reference_id"], source, row["l0"], end["verdict"], end["symbol"]), row)
    return list(rows.values()), {"pairs": counts["pairs"], "placed": counts["placed"],
                                 "unplaced": dict(sorted(unplaced.items()))}


def run(manifest: Path, bus) -> dict:
    """The step on the snapshot `manifest`, said on `bus` (`pipeline.events`): `{"languages": {language: outcome}}`.

    Each observer whose languages have a static graph in the store plans its runs from the pre-map, runs them in
    the container (the engine is asked once, when the first observer has something to run) and saves what the
    join places. An outcome's `state` is `observed` (with the `sites`, `edges` and `closed` holes of the store's
    coverage), or why nothing was: `no-observer`, `no-static-graph`, `not-run` (nothing to run: the plan's
    gaps), `unavailable` (no container), `failed`; those carry the `reason`. A language already observed with
    the same recorder is not observed again: the observation holds for its snapshot's store.
    """
    import code_graph
    import container
    import premap
    import resolve_edges as rx
    manifest = Path(manifest).resolve()
    outcomes: dict = {}

    def say(detail: str, gap: dict, analyzer: str | None = None, language: str | None = None) -> None:
        bus.emit("gap", detail, step=STEP, analyzer=analyzer, gap=gap, **({"language": language} if language else {}))

    def left(languages, state: str, reason: str) -> None:
        outcomes.update({language: {"state": state, "reason": reason} for language in languages})

    if os.environ.get("DAODAN_DYNAMIC") == "off":
        detail = "the dynamic step is off (DAODAN_DYNAMIC=off): no test runs, the graph stays static"
        say(detail, {"kind": "dynamic-off", "detail": detail})
        return {"languages": outcomes}
    found = observers()
    served = {language for module in found for language in module.LANGUAGES}
    asked: dict = {}
    with code_graph.Snapshot(manifest) as snapshot:
        store = rx.default_edge_store(manifest)
        edges, binding, reason = rx.read_edge_store(store, snapshot.store)
        graphs = {language: entry for language, entry in ((binding or {}).get("languages") or {}).items()
                  if reason is None and entry.get("state") == "fresh"}
        for language in sorted(set(graphs) - served):
            detail = f"{language}: no observer runs its tests, so its graph holds no observed edge"
            say(detail, {"kind": "no-observer", "language": language, "detail": detail}, language=language)
            left([language], "no-observer", "no observer runs this language's tests")
        present = set(snapshot.languages.values())
        waiting = [module for module in found if present & set(module.LANGUAGES)]
        for number, module in enumerate(waiting):
            name, entry = resolver(module), module.ENTRY
            wanted = sorted(present & set(module.LANGUAGES))
            for language in (language for language in wanted if language not in graphs):
                detail = (f"{language}: the store holds no static graph of it ({reason or 'its analyzer left none'}): "
                          "an observed edge answers a reference of a graph that is there")
                say(detail, {"kind": "no-static-graph", "language": language, "detail": detail}, entry, language)
                left([language], "no-static-graph", detail)
            wanted = [language for language in wanted if language in graphs]
            if not wanted:
                continue
            bus.progress(STEP, number, len(waiting), analyzer=entry, phase="plan", message=f"{entry}: the plan")
            seen = {language: graphs[language].get("coverage") or {} for language in wanted}
            if all((item.get("observed") or {}).get("resolver") == name for item in seen.values()):
                outcomes.update({language: _outcome(item) for language, item in seen.items()})
                bus.emit("analyzer.finished", f"{entry}: already observed", step=STEP, analyzer=entry,
                         languages=wanted, fresh=True)
                continue
            bus.emit("analyzer.started", f"{entry} for {', '.join(wanted)}", step=STEP, analyzer=entry,
                     languages=wanted)

            def read(rel: str) -> str:
                try:
                    return (snapshot.root / rel).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    return ""

            planned = module.plan(premap.ensure(manifest), sorted(snapshot.checkout.values()), read)
            for gap in planned["gaps"]:
                say(gap["detail"], gap, entry)
            if not planned["runs"]:
                left(wanted, "not-run", "; ".join(gap["detail"] for gap in planned["gaps"]))
                bus.emit("analyzer.finished", f"{entry}: nothing to run", step=STEP, analyzer=entry, languages=wanted)
                continue
            if not asked:  # the engine found goes to the first run, which ends it; the next ones find their own
                asked["once"] = True
                try:
                    asked["engine"] = container.find_engine()
                except container.Gap as gap:
                    asked["gap"] = gap
            result = {"state": "gap", "cause": asked["gap"].cause, "remedy": asked["gap"].remedy} \
                if "gap" in asked else None
            if result is None:
                bus.progress(STEP, number, len(waiting), analyzer=entry, phase="tests",
                             message=f"{entry}: {len(planned['runs'])} runs of the tests in the container")
                result = module.observe(snapshot.root, planned, manifest.parent / RUNS / entry,
                                        asked.pop("engine", None))
            if result["state"] != "ran":
                cause = result["cause"] if result["state"] == "failed" else \
                    f"the tests run only in a container: {result['cause']}"
                for gap in result.get("gaps") or ():
                    say(gap["detail"], gap, entry)
                bus.emit(*(("analyzer.finished", f"{entry} failed") if result["state"] == "failed" else
                           ("analyzer.unavailable", f"{entry} cannot run here")), step=STEP, analyzer=entry,
                         level="error" if result["state"] == "failed" else "warning", cause=cause,
                         remedy=result["remedy"], languages=wanted)
                left(wanted, "failed" if result["state"] == "failed" else "unavailable", cause)
                continue
            for gap in result["gaps"]:
                say(gap["detail"], gap, entry)
            sites, pairs = result.get("sites") or [], result.get("sampled") or []
            bus.progress(STEP, number, len(waiting), analyzer=entry, phase="join",
                         message=f"{entry}: {len(sites)} observed sites and {len(pairs)} sampled pairs to place")
            at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            for language in wanted:
                # With no exact site, nothing is said of what the run did not execute: a sample misses calls.
                rows, facts = join(snapshot, language, sites, edges, module) if sites or not pairs else ([], {})
                facts = {"resolver": name, "at": at, "tests": result["runs"], **facts}
                if pairs:
                    more, said = join_sampled(snapshot, language, pairs, module)
                    rows, facts["sampled"] = rows + more, {"resolver": resolver(module, sampled=True), **said}
                outcomes[language] = _outcome(code_graph.write_observed(snapshot, store, language, rows, facts))
            told = ", ".join(f"{language}: {_told(outcomes[language])}" for language in wanted)
            bus.emit("analyzer.finished", f"{entry}: {told}", step=STEP, analyzer=entry, languages=wanted)
        bus.progress(STEP, len(waiting), len(waiting))
    return {"languages": outcomes}


def _outcome(coverage: dict) -> dict:
    """A language's outcome from its coverage: the sites with an exact observed end, the rows, the holes they
    close, and the same of the sampled ones apart, when there are."""
    def counted(item: dict) -> dict:
        return {"sites": item.get("sites", 0), "edges": item.get("edges", 0),
                "closed": sum((item.get("closed") or {}).values())}
    sampled = coverage.get("sampled")
    return {"state": "observed", **counted(coverage.get("observed") or {}),
            **({"sampled": counted(sampled)} if sampled else {})}


def _told(outcome: dict) -> str:
    sampled = outcome.get("sampled")
    return (f"{outcome['sites']} sites observed" + (f", {sampled['sites']} sampled" if sampled else "")
            + f", {outcome['closed'] + (sampled or {}).get('closed', 0)} holes closed")
