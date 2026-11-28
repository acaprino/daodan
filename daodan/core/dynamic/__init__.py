"""The dynamic step: the project's tests run in a container under a recorder, and what they call enters the graph.

An observer is one module of this package per technology. It declares `NAME`, `VERSION` (its recorder's: the
observed rows' resolver is `NAME@VERSION`) and `LANGUAGES`, and gives:

    plan(record, files, read) -> {"runs": [...], "gaps": [...]}   what to run, from the pre-map alone
    observe(project, planned, out_dir, engine) -> {"state", "sites", "runs", "gaps"}   in the container
    external(callee) -> {"manager", "package", "version"}          the package of a callee outside the project

`plan` takes the command that runs the tests from what the project declares (the pre-map's `tests`); for a folder and
a runner, an entry with an `argv` (`declared`: the user's, the assistant's, the CI's, in `PRECEDENCE`) comes before
the tool's convention (`go test ./...`); with nothing to run it says why, and no container starts. `observe` runs
project code, so only through `container.run_in_container`: the dependencies restored the project's own way in the preparation, with the
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

`sites` are an exact recorder's: every call, with its caller and callee, at its site. No observer has a second
source: a sampling profiler's stacks name no call site (each observer says why it is not one).

`run` is the step (`pipeline.RunAndObserve`); `join` places the sites on the snapshot's references, by position,
and `code_graph.write_observed` saves the rows. An observed end holds for the run that produced it: it proves that
a call can arrive there, not that it arrives only there, and a call no test executed stays as the static steps
left it. A language with no observer, a project with no declared test command, a run
with no container engine are gaps, never silence; so are a result that breaks this contract (`observer-malformed`,
`failed`), a run where no test ran (`not-run`) and one that placed no row of a language (`not-observed`).
Completed test commands can be reused even when they placed no row. Interrupted commands are retried on the next
analysis, together with the evidence they already produced. `DAODAN_DYNAMIC=off` skips the step.

Every plan also gets `declared` (`preparation.declared`): the hosts the project declares for its dependencies,
which the observer's preparation reaches beside the registries, as a CI does; a failed restore whose words name one
it could not reach is a `host_unreachable` gap naming the host and the files that declare it (`preparation.unreached`).
A declared host nobody decided (`egress`) stops the run before it starts, as an `approval_required` gap naming the files
(`egress.preflight`, `egress.declare`).

The services the project's CI starts beside its tests (the pre-map's `services`) start beside every container run
of an observer, with the variables its jobs give the tests (`services()`, `container.beside`), so no observer has
code of its own for them; a service that did not start, or a run that started none of them, is a gap naming the
service and its image (`service_unavailable`). The steps a CI job runs before the tests an observer runs (the
pre-map's `ci_steps`, `ci_steps()`) run at the end of each of its preparations, the services beside them; one that
fails is a `ci_step_failed` gap, one that cannot run a `ci_step_not_run` one.

After the observers the step starts the app the pre-map declares (`starts`) in the container and explores it in a headless
browser (`app.explore`, plan task 11): the controls it pressed are kept in `observed-controls.json` beside the manifest, for
the entry candidates (`observed_entries`) and the links (`flows._observed_entries`). It has its own record in `RUNS/app` and
is reused on the same snapshot; the step's result says it as `app`: `{state, apps, kept}`. A project that declares no app,
no container engine, an app that did not start and an exploration that failed are gaps (`no_start_command`,
`explore_failed`, `build_failed`, `app_not_started`, ...), never silence.

See docs/specs/2026-11-12-passo-dinamico.md, sections 5 and 7.
"""
from __future__ import annotations

import collections
import json
import os
import posixpath
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path

STEP = "run_and_observe"
APP = "app"  # the exploration of the started app, apart from the observers: its record is `RUNS/APP`
RUNS = "dynamic-runs"  # beside the manifest: each observer's container record, logs and observation files
EXAMPLES = 20
TESTS = ("ran", "timeout", "killed", "not_started", "no_tests")  # how a run's tests ended; the first three ran


def stopped(exit_code: int | None, seconds: int | None, limit: int) -> str | None:
    """How a run that was stopped ended, from its tests' exit code and the seconds they took: `timeout` at the
    limit (`timeout`'s own 124, or a KILL after it), `killed` before it (a KILL's 137: the container's memory
    limit, most often); None where nothing stopped it. An observer with no seconds cannot say a KILL came at the
    limit: its 137 is `killed`."""
    if exit_code == 124 or (exit_code == 137 and (seconds or 0) >= limit):
        return "timeout"
    return "killed" if exit_code == 137 else None
HEALTH = ("--health-cmd", "--health-interval", "--health-timeout", "--health-retries", "--health-start-period",
          "--health-start-interval")  # the options of a service passed to the engine: its health check
EXPRESSION = re.compile(r"\$\{\{.*?\}\}", re.S)  # GitHub's expressions, which Daodan does not evaluate
LOCAL = {"localhost", "127.0.0.1", "::1", "[::1]", "0.0.0.0"}  # the tests' own host, the pod's shared one
PORT = re.compile(r"\$\{\{\s*job\.services\.[\w-]+\.ports\[\s*['\"]?(\d+)['\"]?\s*\]\s*\}\}")  # but this one
KEYS = {"runs": {"root", "runner", "state"}, "sites": {"file", "line", "column", "name", "role", "callees"},
        "gaps": {"kind", "detail"}}  # what each item of a result holds


def malformed(result) -> str | None:
    """What an observer's result breaks of the contract (the module's docstring), None when it keeps it."""
    if not isinstance(result, dict) or result.get("state") not in ("ran", "gap", "failed"):
        return "its state is none of ran, gap, failed"
    if result["state"] != "ran":
        return None if result.get("cause") and result.get("remedy") else f"a {result['state']} without cause and remedy"
    for key, need in KEYS.items():
        items = result.get(key)
        if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
            return f"its {key} is not a list of entries"
        short = sorted({name for item in items for name in need - item.keys()})
        if short:
            return f"an entry of its {key} has no {', '.join(short)}"
    states = sorted({str(test["state"]) for test in result["runs"]} - set(TESTS))
    return f"a run's state is {', '.join(states)}, none of {', '.join(TESTS)}" if states else None


PRECEDENCE = ("user", "assistant", "ci")  # who states a command (its `by`, else its `source`), the first wins


def declared(record: dict, runner: str, root: str) -> dict | None:
    """The pre-map's `tests` entry that runs `runner` in `root` with its own words (`argv`), the first by
    `PRECEDENCE`; None where there is none, and the observer's convention runs. The pre-map names the project's
    root `.` or the empty path."""
    root = posixpath.normpath(root or ".")
    found = [test for test in record.get("tests") or () if test.get("runner") == runner
             and isinstance(test.get("argv"), list) and posixpath.normpath(test.get("root") or ".") == root]

    def rank(test: dict) -> int:
        who = test.get("by") or test.get("source")
        return PRECEDENCE.index(who) if who in PRECEDENCE else len(PRECEDENCE)
    return min(found, key=rank, default=None)


def arguments(argv: list[str], runner: str) -> list[str]:
    """The words of a command after the runner it starts (`pytest -m integration`: `-m integration`)."""
    return list(argv[len(runner.split()):])


def observers() -> list:
    """Every module of this package that declares itself an observer, by its entry's name."""
    import importlib
    import pkgutil
    found = []
    for item in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{item.name}")
        if hasattr(module, "NAME"):
            found.append(module)
    return sorted(found, key=lambda module: module.NAME)


def resolver(observer) -> str:
    """The resolver of an observer's rows, named as an analyzer's: the recorder and its version."""
    return f"{observer.NAME}@{observer.VERSION}"


def _declared(snapshot, rel: str, line: int, column: int | None, name: str) -> str | None:
    """The snapshot's declaration at a function's line from 1 and byte column; with no column (a callee a
    recorder gives without one), the only one of that name on that line."""
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


def _healthcheck(check) -> list[str]:
    """A Compose service's `healthcheck` as `create` takes it: `CMD-SHELL`'s line, or `CMD`'s words as one line
    (the engine runs `--health-cmd` with the image's shell), its times and retries; off where Compose disables it."""
    if not isinstance(check, dict) or not check:
        return []
    test = check.get("test") or []
    if check.get("disable") or test[:1] == ["NONE"]:
        return ["--no-healthcheck"]
    line = test[1] if test[:1] == ["CMD-SHELL"] and len(test) > 1 else shlex.join(test[1:]) if test[:1] == ["CMD"] \
        else ""
    return [*(("--health-cmd", line) if line else ()),
            *(item for key, flag in (("interval", "--health-interval"), ("timeout", "--health-timeout"),
                                     ("retries", "--health-retries"), ("start_period", "--health-start-period"),
                                     ("start_interval", "--health-start-interval"))
              if check.get(key) is not None for item in (flag, str(check[key])))]


def services(record: dict) -> dict:
    """What the project's CI starts beside its tests, from the pre-map's `services` (GitHub Actions' service
    containers, GitLab's services, those Compose starts for a step), as `container.beside` takes it: `services`,
    each `{name, image, host, env, args, command}`, with `aliases`, `wait`, `after` (Compose's `depends_on`) and
    `dotenv` (the tracked .env file of each `${NAME}` it holds, whose value the run puts in place: `container.filled`)
    where the fact has them and `files`, `[source in the project, target]` of its bind mounts inside it; `env`, the
    variables the jobs that declare them give their steps, for the tests, without those the fact says the CI
    computes (`computed`); `gaps`, what cannot run as declared, each naming the service, its image and its
    declaration (`path`): `service_unavailable` for one that does not start (an image the CI computes or Compose
    builds, a second definition of a name, which the first's start keeps out), `service_incomplete` for one that
    starts without part of what its job declares (a port mapped to another, volumes, bind mounts outside the
    project, options other than its health check, Compose keys no option applies, variables the CI computes or two
    jobs set apart)."""
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

        if entry.get("build"):
            gap("service_unavailable", [f"Compose builds its image from {entry['build']}: Daodan starts no image the "
                                        "project builds", *notes])
            continue
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
        binds = [(str(bind), *str(bind).split(":")[:2]) for bind in entry.get("binds") or ()]
        outside = [bind for bind, source, _ in binds if posixpath.isabs(source) or source.split("/")[0] == ".."]
        if outside:
            notes.append("its bind mounts outside the project are not mounted: " + ", ".join(outside))
        files = [[posixpath.normpath(source), target] for bind, source, target in binds if bind not in outside]
        args, other = _health(entry.get("options"))
        args += _healthcheck(entry.get("healthcheck"))
        if other:
            notes.append(f"options passed to no engine (only the health check is): {other}")
        if entry.get("ignored"):
            notes.append(f"its Compose keys apply to no engine here: {', '.join(entry['ignored'])}")
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
                "command": [*entry_point[1:], *command], **({"wait": entry["wait"]} if entry.get("wait") else {}),
                **({"after": dict(entry["after"])} if entry.get("after") else {}), **({"files": files} if files else {}),
                **({"dotenv": dict(entry["dotenv"])} if entry.get("dotenv") else {})}
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


def _unanswered(gap: dict, facts: list[dict]) -> dict:
    """An observer's `services_unreachable` `gap` with the local addresses of its `addresses` (the tests' localhost,
    a service's name or alias) no service the CI declares answers at: beside the tests each answers on its
    container's ports (`facts`, the pre-map's `services`); nothing is said when one declares none of its ports."""
    ports = {item["name"]: [str(port).split("/")[0].split(":")[-1] for port in item.get("ports") or ()]
             for item in facts}
    if not all(ports.values()):
        return gap
    hosts = LOCAL | {name for item in facts for name in (item.get("host"), item["name"], *(item.get("aliases") or ()))}
    answered = {port for each in ports.values() for port in each}
    unanswered = [address for address in gap.get("addresses") or () for host, _, port in [address.rpartition(":")]
                  if host.lower() in hosts and port and port not in answered]
    if not unanswered:
        return gap
    said = ", ".join(f"{name} on {', '.join(each)}" for name, each in ports.items()) or "it declares none"
    return {**gap, "detail": f"{gap['detail']}; no service the project's CI declares answers at "
                             f"{', '.join(unanswered)} ({said})"}


def _service_gaps(started: list[dict], planned: list[dict], paths: dict, entry: str) -> list[dict]:
    """The gaps of the services of an observer that ran: one that did not start in one of its container runs
    (`started`, `container.Said.services`), once per cause; every one when its runs started none."""
    def gap(name: str, image: str, said: str) -> dict:
        return {"kind": "service_unavailable", "name": name, "image": image, "path": paths.get(name),
                "detail": f"{name} ({image}), {paths.get(name)}: {said}; the tests ran without it"}

    if not started:
        return [gap(service["name"], service["image"], f"{entry} starts no service") for service in planned]
    failed = dict.fromkeys((row["name"], row["image"], row.get("cause")) for row in started
                           if row.get("outcome") != "ready")
    return [gap(name, image, f"it did not start: {cause}") for name, image, cause in failed]


def ci_steps(record: dict, runs: list[dict]) -> dict:
    """The steps the project's CI jobs run before the tests of `runs` (the pre-map's `ci_steps` whose `tests` is a
    run's `declared_in`), as `container.beside` takes them, once each and in each job's order: `steps`, each
    `{declared_in, cwd, run}` with `name`, `env` and `shell` where the fact has them; `env`, the variables their
    test steps (`test`) give the tests, as the CI gives its runner, for every run of the observer; `gaps`, a
    `ci_step_not_run` for one the fact gives a `cause`, a `ci_step_incomplete` for a test step whose variables
    the tests do not all get (one the CI or the shell computes, one two test steps give apart), a `tests_not_in_ci`
    for a run no fact names where the CI's jobs run other tests of the project."""
    wanted = {run.get("declared_in") for run in runs} - {None}
    ran = sorted({item["tests"] for item in record.get("ci_steps") or () if item.get("tests")})
    gaps = [{"kind": "tests_not_in_ci", "path": tests,
             "detail": f"{tests}: no workflow Daodan reads runs these tests (its CI runs {', '.join(ran)}): a failure "
                       "of theirs is one the project's CI never sees"} for tests in sorted(wanted) if ran
            and tests not in ran]

    def order(item: dict) -> tuple:
        where, _, number = item["declared_in"].rpartition(".steps.")
        return where, int(number) if number.isdigit() else 0

    steps, seen, env, apart = [], set(), {}, set()
    for item in sorted((item for item in record.get("ci_steps") or () if item.get("tests") in wanted), key=order):
        if item["declared_in"] in seen:
            continue
        seen.add(item["declared_in"])
        if item.get("test"):
            notes, computed = [], set(item.get("computed") or ())
            for key, value in (item.get("env") or {}).items():
                text = None if key in computed else _given(value)
                if text is None:
                    notes.append(f"the tests do not get {key}, which the CI or the shell computes ({value})")
                elif key in env and env[key] != text:
                    notes.append(f"the tests get no {key}: this step gives them {text}, another {env.pop(key)}")
                    apart.add(key)
                elif key not in apart:
                    env[key] = text
            if notes:
                gaps.append({"kind": "ci_step_incomplete", "path": item["declared_in"],
                             "detail": f"{item['declared_in']}: {'; '.join(notes)}"})
        elif item.get("cause"):
            name = f" ({item['name']})" if item.get("name") else ""
            gaps.append({"kind": "ci_step_not_run", "path": item["declared_in"],
                         "detail": f"{item['declared_in']}{name}: {item['cause']}: it does not run before the tests"})
        else:
            steps.append({key: item[key] for key in ("declared_in", "name", "cwd", "run", "env", "shell")
                          if item.get(key)})
    return {"steps": steps, "gaps": gaps, "env": env}


def _step_gaps(stepped: list[dict]) -> list[dict]:
    """The gaps of the CI's steps an observer's container runs ran (`container.Said.ci_steps`), once per cause:
    `ci_step_failed` for one that did not end with code 0, `ci_step_not_run` for one that started in none of them."""
    found: dict = {}
    started = {row["declared_in"] for row in stepped if row.get("outcome") != "not_run"}
    for row in stepped:
        if row.get("outcome") == "exited" and row.get("exit_code") == 0 or (
                row.get("outcome") == "not_run" and row["declared_in"] in started):
            continue
        kind = "ci_step_not_run" if row.get("outcome") == "not_run" else "ci_step_failed"
        name = f" ({row['name']})" if row.get("name") else ""
        found.setdefault((kind, row["declared_in"], row.get("cause")), {
            "kind": kind, "path": row["declared_in"],
            **({"exit_code": row["exit_code"]} if row.get("exit_code") is not None else {}),
            "detail": f"{row['declared_in']}{name}: {row.get('cause')}; the tests ran "
                      + ("without it" if kind == "ci_step_not_run" else "after it")})
    return list(found.values())


def _control_counts(tests: list[dict]) -> list[dict]:
    return [{**{key: test[key] for key in ("root", "declared_in") if key in test}, **test["controls"]}
            for test in tests if test.get("runner") == "playwright" and "controls" in test]


def run(manifest: Path, bus) -> dict:
    """The step on the snapshot `manifest`, said on `bus` (`pipeline.events`): `{"languages": {language: outcome}}`.

    Each observer whose languages have a static graph in the store plans its runs from the pre-map, runs them in
    the container (the engine is asked once, when the first observer has something to run) and saves what the
    join places. An outcome's `state` is `observed` (with the `sites`, `edges` and `closed` holes of the store's
    coverage), or why nothing was: `no-observer`, `no-static-graph`, `not-run` (nothing to
    run, the plan's gaps, or no test ran, the run's), `unavailable` (no container), `failed` (the run, or a result
    that breaks the contract), `not-observed` (the tests ran and placed no row of the language); those carry the
    `reason`. Completed commands are reused on the same snapshot, static analyzers, recorder and plan.
    """
    import code_graph
    import container
    import premap
    import egress
    import preparation
    import resolve_edges as rx
    from . import execution_cache
    manifest = Path(manifest).resolve()
    outcomes: dict = {}
    ui_controls, ui_gaps = [], []

    def say(detail: str, gap: dict, analyzer: str | None = None, language: str | None = None) -> None:
        bus.emit("gap", detail, step=STEP, analyzer=analyzer, gap=gap, **({"language": language} if language else {}))

    def left(languages, state: str, reason: str) -> None:
        outcomes.update({language: {"state": state, "reason": reason} for language in languages})

    if os.environ.get("DAODAN_DYNAMIC") == "off":
        detail = "the dynamic step is off (DAODAN_DYNAMIC=off): no test runs, the graph stays static"
        say(detail, {"kind": "dynamic-off", "detail": detail})
        return {"languages": outcomes}
    from pipeline import plan as planning
    asked: dict = {}
    declared, paths = None, {}  # the services of the project's CI (`services`), and where each is declared
    with code_graph.Snapshot(manifest) as snapshot:
        project = str(Path(snapshot.store["root"]).resolve())  # the name `egress` asks under (`egress.project_of`)
        store = rx.default_edge_store(manifest)
        edges, binding, reason = rx.read_edge_store(store, snapshot.store)
        import engine_pass
        entries = (binding or {}).get("languages") or {}
        obsolete = engine_pass.superseded_languages(entries)
        graphs = {language: entry for language, entry in entries.items()
                  if reason is None and language not in obsolete and entry.get("state") == "fresh"}
        layout = planning.plan(planning.stored(snapshot.store))
        for gap in layout["gaps"]:  # the observers the plan holds are the ones that start
            if gap["kind"] == "no-observer" and gap["language"] in graphs:
                say(gap["detail"], {key: gap[key] for key in ("kind", "language", "detail")}, language=gap["language"])
                left([gap["language"]], "no-observer", "no observer runs this language's tests")
        by_entry = {module.NAME: module for module in observers()}
        waiting = [node for node in layout["nodes"] if node["step"] == STEP]
        for number, node in enumerate(waiting):
            module = by_entry[node["adapter"]]
            name, entry = resolver(module), module.NAME
            failed: dict = {}  # the resolver node of each language whose graph the store does not hold
            for language in node["on"]["languages"]:
                if language not in graphs:
                    detail = (f"{language}: the store holds no static graph of it "
                              f"({reason or 'its analyzer left none'}): an observed edge answers a reference of a "
                              "graph that is there")
                    failed.setdefault(planning.need(node, language), {})[language] = detail
            for language, (needed, detail) in sorted(planning.blocked(node, failed).items()):
                say(detail, {"kind": "no-static-graph", "language": language, "need": needed, "detail": detail},
                    entry, language)
                outcomes[language] = {"state": "no-static-graph", "need": needed, "reason": detail}
            wanted = [language for language in node["on"]["languages"] if language in graphs]
            if not wanted:
                continue
            bus.progress(STEP, number, len(waiting), analyzer=entry, phase="plan", message=f"{entry}: the plan")
            seen = {language: graphs[language].get("coverage") or {} for language in wanted}
            def read(rel: str) -> str:
                try:
                    return (snapshot.root / rel).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    return ""

            record = premap.ensure(manifest)
            planned = module.plan(record, sorted(snapshot.checkout.values()), read)
            planned["declared"] = preparation.declared(record)  # the hosts its preparation reaches, as a CI does
            egress.declare(project, planned["declared"]["where"])  # the requests name the files
            folder = manifest.parent / RUNS / entry
            cache_file = folder / "execution.json"
            expected = execution_cache.key(binding, graphs, wanted, module, planned)
            cached = execution_cache.read(cache_file, expected, seen, len(planned["runs"]))
            tests = cached.get("tests", [None] * len(planned["runs"]))
            retry = [i for i, test in enumerate(tests) if not execution_cache.finished(test)]
            if cached and not retry:
                outcomes.update(cached["outcomes"])
                ui_controls.extend(_control_counts(tests))
                ui_gaps.extend(cached.get("ui_gaps", []))
                bus.emit("analyzer.finished", f"{entry}: test execution reused", step=STEP, analyzer=entry,
                         languages=wanted, fresh=True)
                continue
            bus.emit("analyzer.started", f"{entry} for {', '.join(wanted)}", step=STEP, analyzer=entry,
                     languages=wanted)
            planned = {**planned, "runs": [planned["runs"][i] for i in retry]}
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
            stepped = ci_steps(record, planned["runs"])  # the CI's steps before the tests it runs
            for gap in stepped["gaps"]:
                say(gap["detail"], gap, entry)
            said = container.Said([], [])  # what its container runs say of the services and the steps
            if not asked:  # the engine found goes to the first run, which ends it; the next ones find their own
                asked["once"] = True
                try:
                    asked["engine"] = container.find_engine()
                except container.Gap as gap:
                    asked["gap"] = gap
            result = {"state": "gap", "cause": asked["gap"].cause, "remedy": asked["gap"].remedy} \
                if "gap" in asked else None
            if result is None:  # a host the project declares that nobody decided: the runs do not start
                with egress.asking(entry):  # the observer's hosts are asked about together
                    waiting, said_hosts = egress.preflight(project, planned["declared"]["hosts"])
                if waiting:
                    result = {"state": "failed", "cause": said_hosts[0]["detail"],
                              "remedy": "answer in the app, then analyze again", "gaps": said_hosts}
            if result is None:
                bus.progress(STEP, number, len(waiting), analyzer=entry, phase="tests",
                             message=f"{entry}: {len(planned['runs'])} runs of the tests in the container")
                with container.beside(declared["services"], {**declared["env"], **stepped["env"]},
                                      stepped["steps"]) as said, egress.asking(entry), egress.within(project):
                    # Preserve the first attempt's raw per-process files and logs for audit.
                    output = folder / f"retry-{cached['attempt'] + 1}" if cached else folder
                    result = module.observe(snapshot.root, planned, output,
                                            asked.pop("engine", None))
            broken = malformed(result)
            if broken:
                detail = f"{entry} returned a result that breaks the observer contract: {broken}; nothing is kept"
                say(detail, {"kind": "observer-malformed", "detail": detail}, entry)
                bus.emit("analyzer.finished", f"{entry} failed", step=STEP, analyzer=entry, level="error",
                         cause=detail, remedy="fix the observer's result (the contract is dynamic/__init__.py's)",
                         languages=wanted)
                left(wanted, "failed", detail)
                if cached:
                    ui_controls.extend(_control_counts([test for test in tests if test]))
                    ui_gaps.extend(cached.get("ui_gaps", []))
                    outcomes.update({language: outcome for language, outcome in cached["outcomes"].items()
                                     if outcome["state"] == "observed"})
                continue
            # a declared host a failed restore of the run could not reach: one gap naming it, whichever observer ran
            result["gaps"] = [*(result.get("gaps") or ()),
                              *preparation.unreached(result.get("gaps") or (), planned["declared"])]
            result["gaps"] = [_unanswered(gap, record.get("services") or [])
                              if gap.get("kind") == "services_unreachable" else gap for gap in result["gaps"]]
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
                if cached:
                    ui_controls.extend(_control_counts([test for test in tests if test]))
                    ui_gaps.extend(cached.get("ui_gaps", []))
                    # An unavailable retry cannot invalidate calls already observed on this snapshot.
                    outcomes.update({language: outcome for language, outcome in cached["outcomes"].items()
                                     if outcome["state"] == "observed"})
                continue
            attempt_tests = result["runs"]
            execution_cache.update_tests(tests, retry, planned["runs"], result)
            combined_tests = [test for test in tests if test and "state" in test]
            ui_controls.extend(_control_counts(combined_tests or attempt_tests))
            refreshed = {test.get("declared_in") or test["root"] for test in combined_tests
                         if (test.get("controls") or {}).get("status") == "observed"}
            control_gaps = [gap for gap in cached.get("ui_gaps", []) if gap.get("path") not in refreshed]
            control_gaps.extend(gap for gap in result["gaps"] if gap["kind"].startswith("ui_controls_")
                                or gap["kind"] == "browser_unavailable")
            control_gaps = list({(gap["kind"], gap.get("path"), gap["detail"]): gap for gap in control_gaps}.values())
            ui_gaps.extend(control_gaps)
            if declared["services"]:
                for gap in _service_gaps(said.services, declared["services"], paths, entry):
                    say(gap["detail"], gap, entry)
            for gap in _step_gaps(said.ci_steps):
                say(gap["detail"], gap, entry)
            for gap in result["gaps"]:
                say(gap["detail"], gap, entry)
            why = "; ".join(gap["detail"] for gap in result["gaps"])
            if not any(test["state"] in TESTS[:3] for test in result["runs"]):
                left(wanted, "not-run", f"no test ran: {why or 'the observer ran none'}")
                if cached:
                    outcomes.update({language: outcome for language, outcome in cached["outcomes"].items()
                                     if outcome["state"] == "observed"})
                bus.emit("analyzer.finished", f"{entry}: no test ran", step=STEP, analyzer=entry, level="warning",
                         cause=f"no test ran: {why or 'the observer ran none'}",
                         remedy="see the gaps of the run", languages=wanted)
                continue
            sites = execution_cache.merge_sites(cached.get("sites", []), result.get("sites") or [])
            bus.progress(STEP, number, len(waiting), analyzer=entry, phase="join",
                         message=f"{entry}: {len(sites)} observed sites to place")
            at = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
            for language in wanted:
                rows, facts = join(snapshot, language, sites, edges, module)
                facts = {"resolver": name, "at": at, "tests": combined_tests or attempt_tests, **facts}
                if not rows:
                    if seen[language].get("observed"):
                        code_graph.write_observed(snapshot, store, language, [], facts)
                    placed = _unplaced(snapshot, language, sites, facts)
                    outcomes[language] = {"state": "not-observed", "reason": placed + (f"; {why}" if why else "")}
                    continue
                outcomes[language] = _outcome(code_graph.write_observed(snapshot, store, language, rows, facts))
            execution_cache.save(cache_file, expected, tests, {language: outcomes[language] for language in wanted},
                                 at, sites, cached.get("attempt", 0) + 1, control_gaps)
            told = ", ".join(f"{language}: {_told(outcomes[language])}" for language in wanted)
            bus.emit("analyzer.finished", f"{entry}: {told}", step=STEP, analyzer=entry, languages=wanted)
        bus.progress(STEP, len(waiting), len(waiting))
        explored = _app(manifest, snapshot, bus, say)
    return {"languages": outcomes, "app": explored, **({"ui_controls": ui_controls} if ui_controls else {}),
            **({"ui_gaps": ui_gaps} if ui_gaps else {})}


def _app(manifest: Path, snapshot, bus, say) -> dict:
    """The app the project declares, started and explored in the container (`app.explore`): the controls it showed
    are kept beside the manifest for the entries. What did not run is a gap with its cause, never silence; a failure
    of the exploration stops no other part of the step. `{state, apps, kept}`, with `cause` and `remedy` where it did
    not run, and `reused` where the run of the same snapshot was kept."""
    import entry_points
    import premap
    from snapshot_store import logical_digest
    from . import app
    record = premap.ensure(manifest)
    try:  # the pages the frameworks declare, which the exploration opens too: none without the record of the entry points
        pages = entry_points.read_record(manifest).get("framework_entries", [])
    except (OSError, KeyError, TypeError, ValueError):
        pages = []
    if record.get("starts"):
        bus.emit("analyzer.started", f"{APP}: the app started and explored", step=STEP, analyzer=APP)
    try:
        seen = app.explore(manifest, snapshot.root, record, logical_digest(snapshot.store), manifest.parent / RUNS / APP,
                           pages=pages)
    except Exception as error:  # noqa: BLE001 - the exploration is one part of the step: the others stay
        cause = f"{type(error).__name__}: {error}"
        seen = {"state": "failed", "cause": cause, "remedy": "explore again", "apps": [], "kept": 0,
                "gaps": [{"kind": "explore_failed", "detail": f"the app could not be explored: {cause}"}]}
    for gap in seen["gaps"]:
        say(gap["detail"], gap, APP)
    if seen["state"] != "ran":
        bus.emit(*(("analyzer.finished", f"{APP} failed") if seen["state"] == "failed" else
                   ("analyzer.unavailable", f"{APP} cannot run here")), step=STEP, analyzer=APP,
                 level="error" if seen["state"] == "failed" else "warning", cause=seen["cause"], remedy=seen["remedy"])
    elif seen["apps"]:
        bus.emit("analyzer.finished", f"{APP}: {len(seen['apps'])} apps started, {seen['kept']} explored", step=STEP,
                 analyzer=APP, fresh=bool(seen.get("reused")))
    return {key: seen[key] for key in ("state", "cause", "remedy", "reused") if key in seen} | {
        "apps": len(seen["apps"]), "kept": seen["kept"]}


def _unplaced(snapshot, language: str, sites: list[dict], facts: dict) -> str:
    """Why tests that ran gave no row of `language`, from what the recorder saw: sites in its files at no
    reference, sites only in files the snapshot does not hold, or no call from its files at all."""
    if facts.get("recorded"):
        roles = ", ".join(f"{role} {count}" for role, count in facts["unjoined"].items())
        return (f"the tests ran and the recorder saw {facts['recorded']} call sites in {language} files, none at a "
                f"reference of the static graph ({roles})")
    said = f"the tests ran and made no call from a {language} file of the project"
    outside = sorted({site["file"] for site in sites if site["file"] not in snapshot.rel})
    if outside:
        listed = ", ".join(outside[:3])
        said += f" (the recorder saw calls in {len(outside)} files the snapshot does not hold: {listed})"
    missed = (facts.get("files") or {}).get("not_executed")
    return said + (f"; the files with calls, which no test executed: {', '.join(missed[:5])}" if missed else "")


def _outcome(coverage: dict) -> dict:
    """A language's outcome from its coverage: the sites with an exact observed end, the rows, the holes they
    close."""
    seen = coverage.get("observed") or {}
    return {"state": "observed", "sites": seen.get("sites", 0), "edges": seen.get("edges", 0),
            "closed": sum((seen.get("closed") or {}).values())}


def _told(outcome: dict) -> str:
    if outcome["state"] != "observed":
        return outcome["reason"]
    return f"{outcome['sites']} sites observed, {outcome['closed']} holes closed"
