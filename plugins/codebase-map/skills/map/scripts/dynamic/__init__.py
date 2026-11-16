"""The dynamic step: the project's tests run in a container under a recorder, and what they call enters the graph.

An observer is one module of this package per technology. It declares `ENTRY`, `VERSION` (its recorder's: the
observed rows' resolver is `ENTRY@VERSION`) and `LANGUAGES`, and gives:

    plan(record, files, read) -> {"runs": [...], "gaps": [...]}   what to run, from the pre-map alone
    observe(project, planned, out_dir, engine) -> {"state", "sites", "sampled", "runs", "gaps"}   in the container
    external(callee) -> {"manager", "package", "version"}          the package of a callee outside the project

`plan` takes the command that runs the tests from what the project declares (the pre-map's `tests`), never from a
convention; with nothing to run it says why, and no container starts. `observe` runs project code, so only through
`container.run_in_container`: the dependencies restored the project's own way in the preparation, with the
registries, the tests in the execution, with no network. `state` is `ran`, `gap` with `cause` and `remedy`
when no container could run, or `failed` with `cause` and `remedy` when the preparation or the engine failed.
`runs` has one entry per planned run, `{root, runner, state, ...}`: the folder from the project's root, what
ran (`pytest`, `npm test`, `go test`, `gradle`), and how its tests ended, one of `TESTS` (`ran` to their end,
some failed or not; `timeout` and `killed`, stopped after some ran; `not_started`; `no_tests`); any other key
is the observer's own (`exit_code`, `seconds`). `gaps` are `{kind, detail, ...}`. A site is `{file, line,
column, name, role, callees}`: the file from the project's root, the line from 0 and the byte column of the
callee's name; a callee is `{kind: "project", file, line, column, name, type}` (the declaration's line from 0
and byte column, as the snapshot has it; with no column, the one function of that name on that line) or one
outside the project, and may carry `wraps` (the callee it stands for) or `mock`.

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
with no container engine are gaps, never silence; so are a result that breaks this contract (`observer-malformed`,
`failed`), a run where no test ran (`not-run`) and one that placed no row of a language (`not-observed`): of
those nothing is kept, and the next analysis tries again. `DAODAN_DYNAMIC=off` skips the step.

Every plan also gets `declared` (`preparation.declared`): the hosts the project declares for its dependencies,
which the observer's preparation reaches beside the registries, as a CI does; a failed restore whose words name one
it could not reach is a `host_unreachable` gap naming the host and the files that declare it (`preparation.unreached`).

The services the project's CI starts beside its tests (the pre-map's `services`) start beside every container run
of an observer, with the variables its jobs give the tests (`services()`, `container.beside`), so no observer has
code of its own for them; a service that did not start, or a run that started none of them, is a gap naming the
service and its image (`service_unavailable`).

See docs/specs/2026-11-12-passo-dinamico.md, sections 5 and 7.
"""
from __future__ import annotations

import collections
import json
import os
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path

STEP = "dynamic"
RUNS = "dynamic-runs"  # beside the manifest: each observer's container record, logs and observation files
EXAMPLES = 20
TESTS = ("ran", "timeout", "killed", "not_started", "no_tests")  # how a run's tests ended; the first three ran
HEALTH = ("--health-cmd", "--health-interval", "--health-timeout", "--health-retries", "--health-start-period",
          "--health-start-interval")  # the options of a service passed to the engine: its health check
EXPRESSION = re.compile(r"\$\{\{.*?\}\}", re.S)  # GitHub's expressions, which Daodan does not evaluate
PORT = re.compile(r"\$\{\{\s*job\.services\.[\w-]+\.ports\[\s*['\"]?(\d+)['\"]?\s*\]\s*\}\}")  # but this one
KEYS = {"runs": {"root", "runner", "state"}, "sites": {"file", "line", "column", "name", "role", "callees"},
        "sampled": {"caller", "callee", "line"}, "gaps": {"kind", "detail"}}  # what each item of a result holds


def malformed(result) -> str | None:
    """What an observer's result breaks of the contract (the module's docstring), None when it keeps it."""
    if not isinstance(result, dict) or result.get("state") not in ("ran", "gap", "failed"):
        return "its state is none of ran, gap, failed"
    if result["state"] != "ran":
        return None if result.get("cause") and result.get("remedy") else f"a {result['state']} without cause and remedy"
    for key, need in KEYS.items():
        items = result.get(key, [] if key == "sampled" else None)
        if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
            return f"its {key} is not a list of entries"
        short = sorted({name for item in items for name in need - item.keys()})
        if short:
            return f"an entry of its {key} has no {', '.join(short)}"
    states = sorted({str(test["state"]) for test in result["runs"]} - set(TESTS))
    return f"a run's state is {', '.join(states)}, none of {', '.join(TESTS)}" if states else None


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


def _given(value) -> str | None:
    """A value as GitHub gives it to a process (`true`, `5432`); a service's port where an expression names one,
    since beside the tests a service answers on its own ports; None where the CI computes the value otherwise."""
    text = "" if value is None else json.dumps(value) if isinstance(value, bool) else str(value)
    text = PORT.sub(lambda match: match.group(1), text)
    return None if EXPRESSION.search(text) else text


def _health(options) -> tuple[list[str], str]:
    """The health check among a service's options, as `create` takes it, and the other options, as written."""
    try:
        words = iter(shlex.split(str(options or "")))
    except ValueError:
        return [], str(options)
    kept, other = [], []
    for word in words:
        flag, equal, value = word.partition("=")
        if flag in HEALTH:
            kept += [flag, value if equal else next(words, "")]
        elif word == "--no-healthcheck":
            kept.append(word)
        else:
            other.append(word)
    return kept, shlex.join(other)


def services(record: dict) -> dict:
    """What the project's CI starts beside its tests, from the pre-map's `services` (GitHub Actions' service
    containers, GitLab's services), as `container.beside` takes it: `services`, each `{name, image, host, env, args,
    command}`, with `aliases` and `wait` where the fact has them; `env`, the variables the jobs that declare them
    give their steps, for the tests, without those the fact says the CI computes (`computed`); `gaps`, what cannot
    run as declared, each naming the service, its image and its declaration (`path`): `service_unavailable` for one
    that does not start (an image the CI computes, a second definition of a name, which the first's start keeps
    out), `service_incomplete` for one that starts without part of what its job declares (a port mapped to another,
    volumes, options other than its health check, variables the CI computes or two jobs set apart)."""
    planned, env, gaps, jobs, first, apart = [], {}, [], set(), {}, set()
    for entry in sorted(record.get("services") or [], key=lambda item: item["declared_in"]):
        name, image, path = entry["name"], entry["image"], entry["declared_in"]
        notes, job, computed = [], path.split(".services.", 1)[0], set(entry.get("computed") or ())
        for key, value in (entry.get("job_env") or {}).items() if job not in jobs else ():
            text = None if key in computed else _given(value)
            if text is None:
                notes.append(f"the tests do not get {key}, which the CI computes ({value})")
            elif key in env and env[key] != text:
                notes.append(f"the tests get no {key}: its job gives them {text}, another job {env.pop(key)}")
                apart.add(key)
            elif key not in apart:
                env[key] = text
        jobs.add(job)

        def gap(kind: str, said: list[str]) -> None:
            gaps.append({"kind": kind, "name": name, "image": image, "path": path,
                         "detail": f"{name} ({image}), {path}: {'; '.join(said)}"})

        if EXPRESSION.search(image) or "$" in image:  # an expression, or a GitLab variable the CI defines
            gap("service_unavailable", ["the CI computes its image, which Daodan does not evaluate: it does not "
                                        "start", *notes])
            continue
        given = {key: None if key in computed else _given(value) for key, value in (entry.get("env") or {}).items()}
        notes[:0] = [f"it does not get {key}, which the CI computes ({entry['env'][key]})"
                     for key, value in given.items() if value is None]
        for port in entry.get("ports") or ():
            mapped = str(port).split("/")[0].split(":")
            if len(mapped) > 1 and mapped[-2] != mapped[-1]:
                notes.append(f"its job maps port {mapped[-2]} to its port {mapped[-1]}: beside the tests it answers "
                             f"on {mapped[-1]}")
        if entry.get("volumes"):
            notes.append("its volumes are not mounted: " + ", ".join(map(str, entry["volumes"])))
        args, other = _health(entry.get("options"))
        if other:
            notes.append(f"options passed to no engine (only the health check is): {other}")
        # GitHub writes a command and an entrypoint as one string each, GitLab as lists: the engine takes one
        # program as the entrypoint, the rest of the list before the command
        entry_point = entry.get("entrypoint")
        entry_point = [str(word) for word in entry_point] if isinstance(entry_point, list) else \
            [str(entry_point)] if entry_point else []
        command = entry.get("command")
        command = [str(word) for word in command] if isinstance(command, list) else \
            shlex.split(str(command)) if command else []
        spec = {"name": name, "image": image, "host": entry.get("host") or "localhost",
                **({"aliases": list(entry["aliases"])} if entry.get("aliases") else {}),
                "env": {key: value for key, value in given.items() if value is not None},
                "args": [*args, *(("--entrypoint", entry_point[0]) if entry_point else ())],
                "command": [*entry_point[1:], *command], **({"wait": entry["wait"]} if entry.get("wait") else {})}
        if name in first and first[name][0] != spec:
            gap("service_unavailable", [f"the service of {first[name][1]} has its name and starts: this one does "
                                        "not"])
            if notes:
                gap("service_incomplete", notes)
            continue
        if name not in first:
            first[name] = (spec, path)
            planned.append(spec)
        if notes:
            gap("service_incomplete", notes)
    return {"services": planned, "env": env, "gaps": gaps}


def _service_gaps(started: list[dict], planned: list[dict], paths: dict, entry: str) -> list[dict]:
    """The gaps of the services of an observer that ran: one that did not start in one of its container runs
    (`started`, what `container.beside` yields), once per cause; every one when its runs started none."""
    def gap(name: str, image: str, said: str) -> dict:
        return {"kind": "service_unavailable", "name": name, "image": image, "path": paths.get(name),
                "detail": f"{name} ({image}), {paths.get(name)}: {said}; the tests ran without it"}

    if not started:
        return [gap(service["name"], service["image"], f"{entry} starts no service") for service in planned]
    failed = dict.fromkeys((row["name"], row["image"], row.get("cause")) for row in started
                           if row.get("outcome") != "ready")
    return [gap(name, image, f"it did not start: {cause}") for name, image, cause in failed]


def run(manifest: Path, bus) -> dict:
    """The step on the snapshot `manifest`, said on `bus` (`pipeline.events`): `{"languages": {language: outcome}}`.

    Each observer whose languages have a static graph in the store plans its runs from the pre-map, runs them in
    the container (the engine is asked once, when the first observer has something to run) and saves what the
    join places. An outcome's `state` is `observed` (with the `sites`, `edges` and `closed` holes of the store's
    coverage, and `sampled` apart), or why nothing was: `no-observer`, `no-static-graph`, `not-run` (nothing to
    run, the plan's gaps, or no test ran, the run's), `unavailable` (no container), `failed` (the run, or a result
    that breaks the contract), `not-observed` (the tests ran and placed no row of the language); those carry the
    `reason`. A language already observed with
    the same recorder is not observed again: the observation holds for its snapshot's store.
    """
    import code_graph
    import container
    import premap
    import preparation
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
    declared, paths = None, {}  # the services of the project's CI (`services`), and where each is declared
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

            record = premap.ensure(manifest)
            planned = module.plan(record, sorted(snapshot.checkout.values()), read)
            planned["declared"] = preparation.declared(record)  # the hosts its preparation reaches, as a CI does
            for gap in planned["gaps"]:
                say(gap["detail"], gap, entry)
            if not planned["runs"]:
                left(wanted, "not-run", "; ".join(gap["detail"] for gap in planned["gaps"]))
                bus.emit("analyzer.finished", f"{entry}: nothing to run", step=STEP, analyzer=entry, languages=wanted)
                continue
            if declared is None:  # the project's services, the same for every observer: planned and said once
                declared = services(record)
                for gap in declared["gaps"]:
                    say(gap["detail"], gap)
                for item in sorted(record.get("services") or [], key=lambda item: item["declared_in"]):
                    paths.setdefault(item["name"], item["declared_in"])
            started: list[dict] = []  # the outcomes of the services its container runs started
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
                with container.beside(declared["services"], declared["env"]) as started:
                    result = module.observe(snapshot.root, planned, manifest.parent / RUNS / entry,
                                            asked.pop("engine", None))
            broken = malformed(result)
            if broken:
                detail = f"{entry} returned a result that breaks the observer contract: {broken}; nothing is kept"
                say(detail, {"kind": "observer-malformed", "detail": detail}, entry)
                bus.emit("analyzer.finished", f"{entry} failed", step=STEP, analyzer=entry, level="error",
                         cause=detail, remedy="fix the observer's result (the contract is dynamic/__init__.py's)",
                         languages=wanted)
                left(wanted, "failed", detail)
                continue
            # a declared host a failed restore of the run could not reach: one gap naming it, whichever observer ran
            result["gaps"] = [*(result.get("gaps") or ()),
                              *preparation.unreached(result.get("gaps") or (), planned["declared"])]
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
            if declared["services"]:
                for gap in _service_gaps(started, declared["services"], paths, entry):
                    say(gap["detail"], gap, entry)
            for gap in result["gaps"]:
                say(gap["detail"], gap, entry)
            why = "; ".join(gap["detail"] for gap in result["gaps"])
            if not any(test["state"] in TESTS[:3] for test in result["runs"]):
                left(wanted, "not-run", f"no test ran: {why or 'the observer ran none'}")
                bus.emit("analyzer.finished", f"{entry}: no test ran", step=STEP, analyzer=entry, level="warning",
                         cause=outcomes[wanted[0]]["reason"], remedy="see the gaps of the run", languages=wanted)
                continue
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
                if not rows:  # nothing is kept: the next analysis observes again
                    placed = _unplaced(snapshot, language, sites, facts)
                    outcomes[language] = {"state": "not-observed", "reason": placed + (f"; {why}" if why else "")}
                    continue
                outcomes[language] = _outcome(code_graph.write_observed(snapshot, store, language, rows, facts))
            told = ", ".join(f"{language}: {_told(outcomes[language])}" for language in wanted)
            bus.emit("analyzer.finished", f"{entry}: {told}", step=STEP, analyzer=entry, languages=wanted)
        bus.progress(STEP, len(waiting), len(waiting))
    return {"languages": outcomes}


def _unplaced(snapshot, language: str, sites: list[dict], facts: dict) -> str:
    """Why tests that ran gave no row of `language`, from what the recorder saw: sites in its files at no
    reference, sites only in files the snapshot does not hold, or no call from its files at all."""
    if facts.get("recorded"):
        roles = ", ".join(f"{role} {count}" for role, count in facts["unjoined"].items())
        return (f"the tests ran and the recorder saw {facts['recorded']} call sites in {language} files, none at a "
                f"reference of the static graph ({roles})")
    if not sites and "sampled" in facts:
        return f"the tests ran and no sampled pair has its caller in a {language} file of the snapshot"
    said = f"the tests ran and made no call from a {language} file of the project"
    outside = sorted({site["file"] for site in sites if site["file"] not in snapshot.rel})
    if outside:
        listed = ", ".join(outside[:3])
        said += f" (the recorder saw calls in {len(outside)} files the snapshot does not hold: {listed})"
    missed = (facts.get("files") or {}).get("not_executed")
    return said + (f"; the files with calls, which no test executed: {', '.join(missed[:5])}" if missed else "")


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
    if outcome["state"] != "observed":
        return outcome["reason"]
    sampled = outcome.get("sampled")
    return (f"{outcome['sites']} sites observed" + (f", {sampled['sites']} sampled" if sampled else "")
            + f", {outcome['closed'] + (sampled or {}).get('closed', 0)} holes closed")
