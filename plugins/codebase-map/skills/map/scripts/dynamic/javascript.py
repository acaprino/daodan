"""The JavaScript and TypeScript observer: the project's tests under the exact recorder (`javascript_record.js`).

The recorder is Daodan's: no existing one qualifies, that is records every call with its caller, its callee and
the call's place, by their own documentation. njsTrace (MIT, 3.0.0) rewrites through `Module._compile` the entry
and exit of each function: no call's place, no ES module, nothing a runner evaluates with `vm`. Jalangi2
(Apache-2.0, 0.2.6 of 2020) has the call's place and the callee, on ECMAScript 5.1 only; NodeProf needs GraalVM's
Node, not the project's. The Babel and SWC plugins for calls log (babel-plugin-trace) or count coverage
(babel-plugin-istanbul, swc-plugin-coverage-instrument): statements, branches, functions, no edge. V8's inspector
samples (Profiler: a function's callers without the call's line) or counts functions and blocks (precise
coverage); its Debugger would pause at every call. OpenTelemetry's auto-instrumentation patches libraries
(http, pg, express...): their boundaries only. So the recorder is a Babel plugin that passes every callee
through a function of its own, and asks the inspector where the function called is defined; it prints with
@babel/core (`BABEL`, MIT, from npm at that version). V8's sampling profiler (`--cpu-prof`) is the second source
the step takes (`sampled` pairs, `dynamic.join_sampled`) only where the recorder has no hook: the one runner of
that kind is Bun's, which is not V8, and the files the recorder misses are said (`not_observed`), so no run
takes it.

`plan` reads the pre-map alone. The command is the one the project declares: the `test` script of each package
and, for a folder and runner it does not reach, the package's script that starts that runner (its `tests`
entries, from `premap/npm_tests.py`: Jest, Vitest, Mocha, `node --test`, Turborepo, any other), run as `npm run`
of the script `declared_in` names in the package's folder; a project where no package declares one is a
`no_test_command` gap, never a command of ours. A script whose runner the recorder cannot hook (`NOT_OBSERVED`) is
a `runner_not_observed` gap, and it does not run. Where every script of a runner watches (the pre-map's
`tests_not_declared`), none runs: their gaps come back with the runs', which explain a language's outcome.

`observe` is one container run (`container.run_in_container`, the TypeScript analyzer's image). The preparation,
with the registries: Daodan's Node, the Babel the recorder prints with (from npm without its install scripts),
the Node the project states at an exact version (mise, `preparation.toolchains`), then the project's own restore
with its lifecycle scripts, as the analyzer's (`preparation.node_prepare`). The execution, with no network: each
script under the recorder, preloaded through NODE_OPTIONS so it starts before any project code, in every process
and thread the script starts, stopped after `LIMIT` seconds by a signal the recorder writes its sites on, with
TURBO_ENV_MODE=loose (Turborepo's documented setting: its default, strict, passes a task NODE_OPTIONS and not the
recorder's own variables). The project is not changed. The recorder puts its Babel plugin where the code is
compiled:

- a source Node runs as written (Mocha, `node --test`, any script on Node's own loaders) is printed by
  Daodan's Babel, TypeScript Node strips itself (`node --test "test/*.test.ts"`) once stripped as Node does;
- a @babel/core the run loads itself (Jest's babel-jest, @babel/register) gets the plugin in every transform;
- code another tool printed with its source map inline (ts-jest, Vitest's Vite in every pool, a TypeScript
  loader), on its way to Node's loaders or to the `vm` functions the runners evaluate with, is printed again
  through that map: a call is a site only where the map leads to the same name in the file as written.

Back come the observation files, one per process and thread, and each run's log. What did not happen is a gap
with its cause: tests that did not start (the log's tail), that failed, that outlasted the limit, that reached
for a service or the network (the execution has none, only the services the project's CI declares), that
found no test, a run
where the recorder saw no call (`nothing_recorded`, with the runner's reason: `UNREACHED`), the project files that
ran unrecorded (`not_observed`: printed with no inline map, or ES modules
under a Node without `module.registerHooks`, before 22.15), the project callees the recorder could not place
(`callee_unplaced`: the map of their code leads to no function's head in the file as written), a failed restore.
"""
from __future__ import annotations

import json
import re
import shlex
import shutil
from pathlib import Path

import preparation
from indexers import typescript  # the image, the unit kinds and the restores of the analyzer of the same languages

# The observer this module is (`dynamic.observers`): its entry, its recorder's version, the languages it observes.
ENTRY, VERSION, LANGUAGES = "dynamic-record-javascript", "1", ("javascript", "typescript")
RECORDER = Path(__file__).with_name("javascript_record.js").resolve()
RUNNERS = ("jest", "mocha", "node:test", "npm", "vitest", "turbo")  # the pre-map's runners, run through their script
NOT_OBSERVED = {"bun": "Bun runs the tests on its own engine, JavaScriptCore, where a Node preload and V8's "
                       "inspector do not exist"}
BABEL = "7.29.7"  # @babel/core on npm: the recorder prints with it the code it records
MOCKS = ("jest-mock", "sinon", "tinyspy", "@vitest/spy")  # a function of theirs stands for another: no destination
MEMORY = 4 * 2**30  # a Jest shard of the measure ran in 4 GB (benchmarks/call-provenance)
LIMIT = 3600  # the seconds one run of the tests may take
OUT = "/daodan/out"
IN, T = preparation.IN, preparation.T
CORE = f"{T}/npm/lib/node_modules/@babel/core"
UNREACHABLE = re.compile(r"ECONNREFUSED|ENOTFOUND|EAI_AGAIN|ENETUNREACH")
NO_TESTS = re.compile(r"^[ℹ#] tests 0$", re.M)  # Node's runner, spec or TAP reporter, that found no test file
# Why a runner's tests may run where the recorder's preload does not reach, beside the script's own NODE_OPTIONS.
UNREACHED = {"turbo": "Turborepo gives its tasks only the variables its env mode lets through, and strict, its "
                      "default, passes NODE_OPTIONS but not the recorder's own: the run sets TURBO_ENV_MODE=loose, "
                      "which turbo reads from 2.1.0; an older turbo, or a script that passes --env-mode=strict, "
                      "keeps them from the tests"}
ERROR = re.compile(r"^\s*(?:[\w.]*Error\b|npm (?:ERR!|error)\b)")  # the first line a thrown error or npm prints
MARK = re.compile(r"^DAODAN-DYNAMIC (\d+) (\S+) ?(.*)$", re.M)


def external(callee: dict) -> dict:
    """The package of a callee outside the project: an npm package is itself, at the version its `package.json`
    states (as the static graph names it); Node's modules and the language's builtins are `node` at the
    version that ran; code of neither is its file, with no version."""
    if callee["kind"] == "package":
        return {"manager": "npm", "package": callee["module"], "version": callee.get("version")}
    package = "node" if callee["kind"] in ("runtime", "native") else callee.get("module") or "unknown"
    return {"manager": "node", "package": package, "version": callee.get("version")}


def plan(record: dict, files: list[str], read) -> dict:
    """`{runs, gaps, roots, toolchains}` from the pre-map `record`: see the module's docstring. A run is
    `{root, runner, declared_in}`; `roots` are the package folders the restores run in and `toolchains` the Node
    the project states."""
    import premap
    tests = sorted((test for test in record.get("tests", []) if test.get("runner") in (*RUNNERS, *NOT_OBSERVED)),
                   key=lambda test: test["root"])
    # the pre-map's: tests of scripts no declared command runs, said again where the tests' outcome is
    unrun = [{key: value for key, value in gap.items() if key != "source"} for gap in record.get("gaps", [])
             if gap.get("kind") == "tests_not_declared"]
    if not tests:
        return {"runs": [], "roots": [], "toolchains": [], "gaps": [{
            "kind": "no_test_command",
            "detail": "no package.json of the project declares a test script (`scripts.test`): nothing is "
                      "observed"}, *unrun]}
    gaps = [{"kind": "runner_not_observed", "path": test.get("declared_in"), "runner": test["runner"],
             "detail": f"{test.get('declared_in')} runs {test['runner']}: {NOT_OBSERVED[test['runner']]}; its "
                       "tests do not run"} for test in tests if test["runner"] in NOT_OBSERVED]
    return {"runs": [{"root": test["root"], "runner": test["runner"], "declared_in": test.get("declared_in")}
                     for test in tests if test["runner"] in RUNNERS], "gaps": gaps, "unrun": unrun,
            "roots": sorted(premap.roots(record, typescript.UNIT_KINDS, typescript.WORKSPACES)),
            "toolchains": [item for item in record.get("toolchains", []) if item.get("tool") == "node"]}


def _script(run: dict) -> str:
    """The package script a run starts: the one its `declared_in` names (`package.json#scripts.<name>`)."""
    return (run.get("declared_in") or "").rpartition("#scripts.")[2] or "test"


def _command(run: dict) -> str:
    return "npm test" if _script(run) == "test" else f"npm run {_script(run)}"


def scripts(planned: dict, restores: list[str]) -> tuple[str, str, dict]:
    """The preparation's script, the execution's, and the stated Node's install (`preparation.toolchains`):
    `restores` are the lines of the project's own restore."""
    chains = preparation.toolchains([item for item in planned.get("toolchains") or ()
                                     if preparation.EXACT.match(str(item.get("version") or ""))])
    prepare = ["set -u", f'mkdir -p {T}/bin "$HOME"', *preparation.setup(["node"])["lines"],
               # before a stated Node is first on the path: Daodan's npm installs it
               f"{{ npm install -g --prefix {T}/npm --ignore-scripts --no-audit --no-fund --loglevel=error"
               f" @babel/core@{BABEL} ; }} >&2",
               f"[ -e {CORE}/package.json ] || {{ echo 'DAODAN-MISSING @babel/core@{BABEL}' >&2; exit 70; }}",
               *chains["lines"], "cd /work || exit 70", *restores]
    # TURBO_ENV_MODE: Turborepo's strict env mode passes its tasks NODE_OPTIONS but not the DYN_ variables
    execute = ["set -u", f"mkdir -p {OUT}", f"export DYN_ROOT=/work DYN_BABEL={CORE} TURBO_ENV_MODE=loose",
               "run() {",  # $1 the run, $2 its folder
               "  start=$(date +%s)",
               f'  ( cd "/work/$2" && NODE_OPTIONS="--require {IN}/{RECORDER.name}"'
               f' DYN_OUT={OUT}/observed-$1-%p.json exec timeout -k 30 {LIMIT} npm run "$3" )'
               f" > {OUT}/tests-$1.log 2>&1",
               '  echo "DAODAN-DYNAMIC $1 exit $? $(( $(date +%s) - start ))"', "}",
               *(f"run {number} {shlex.quote(run['root'])} {shlex.quote(_script(run))}"
                 for number, run in enumerate(planned["runs"]))]
    return "\n".join([*prepare, "exit 0"]) + "\n", "\n".join([*execute, "exit 0"]) + "\n", chains


def _observations(folder: Path, run: int | None = None) -> list[dict]:
    """The observation files in `folder` (one per process and thread, `observed-<run>-<pid>-<thread>.json`; of
    one run or of all), each as the recorder wrote it."""
    found = []
    for path in sorted(Path(folder).glob(f"observed-{'*' if run is None else run}-*.json")):
        try:
            found.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue  # a process killed while it wrote: its file is no observation
    return found


def _callee(callee: dict, node: str | None) -> dict:
    """A callee as the join reads it: a project one with its declaration's `column` (None where the recorder
    could not place it) and `type`, the runtime's at the version of the Node that ran, a mock marked."""
    if callee["kind"] == "project":
        return {"column": None, "type": "function", **callee}
    if callee["kind"] in ("runtime", "native"):
        return {**callee, "version": node}
    return {**callee, "mock": True} if callee.get("module") in MOCKS else callee


def sites(folder: Path, run: int | None = None) -> list[dict]:
    """The sites of the observation files in `folder` (`_observations`), each site once with every callee a
    process saw there. Every site of the recorder is a call: a call or a `new`."""
    merged: dict = {}
    for data in _observations(folder, run):
        for site in data.get("sites") or ():
            key = (site["file"], site["line"], site["column"], site["name"])
            entry = merged.setdefault(key, {**site, "role": "call", "callees": {}})
            for callee in (_callee(callee, data.get("node")) for callee in site["callees"]):
                entry["callees"][json.dumps(callee, sort_keys=True)] = callee
    return [{**entry, "callees": list(entry["callees"].values())} for _key, entry in sorted(merged.items())]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _outcome(run: dict, mark: str, log: str, observations: list[dict], processes: int, ended: str) \
        -> tuple[dict, list[dict]]:
    """One run's entry and its gaps, from the mark its script printed, its tests' log and what it recorded."""
    entry = {key: run[key] for key in ("root", "runner", "declared_in")}
    code, _, seconds = mark.partition(" ")
    entry.update(state="not_started", exit_code=int(code) if code else None,
                 seconds=int(seconds) if seconds.isdigit() else None, processes=processes)
    tail = " | ".join(line.strip() for line in log.strip().splitlines()[-8:])[-600:]
    error = next((line.strip() for line in log.splitlines() if ERROR.match(line)), None)
    if error and error not in tail:  # the cause, above a summary that fills the tail
        tail = f"{error[:300]} ... {tail}"
    recorded = sum(len(data.get("sites") or ()) for data in observations)

    def gap(kind: str, detail: str, **more) -> dict:
        return {"kind": kind, "path": run["root"], **more, "detail": detail}

    command = f"{_command(run)} in {run['root']}"
    if not code:
        return entry, [gap("tests_not_started", f"{command}: the run ended before the tests' exit ({ended})")]
    gaps = []
    if entry["exit_code"] in (124, 137):
        entry["state"] = "timeout"
        gaps.append(gap("tests_timeout", f"{command} did not end in {LIMIT} s: what ran until then is observed"))
    elif entry["exit_code"] == 0 or recorded:
        entry["state"] = "ran"
        if entry["exit_code"]:
            gaps.append(gap("tests_failed", f"{command} exited with code {code}: some tests failed, and a test "
                                            f"that fails may stop before its calls: {tail}"))
        elif not recorded and NO_TESTS.search(log):
            entry["state"] = "no_tests"
            gaps.append(gap("no_tests", f"{command} found no test to run: {tail}"))
        elif not recorded:
            cause = UNREACHED.get(run["runner"], "the script sets NODE_OPTIONS itself, or starts another engine")
            gaps.append(gap("nothing_recorded",
                            f"{command} ({run['runner']}) ended and the recorder saw no call and no file of the "
                            f"project run: the tests ran in processes the recorder's preload does not reach ({cause})",
                            runner=run["runner"]))
    else:
        gaps.append(gap("tests_not_started", f"{command} exited with code {code} and recorded no call: {tail}"))
    unobserved = sorted({rel for data in observations for rel in data.get("unobserved") or ()})
    if unobserved:
        gaps.append(gap("not_observed",
                        f"{command}: {len(unobserved)} files of the project ran unrecorded (printed by another "
                        f"tool with no source map inline, or loaded where the recorder has no hook): "
                        f"{', '.join(unobserved[:5])}", files=len(unobserved), examples=unobserved[:5]))
    refused = len(UNREACHABLE.findall(log))
    if refused:
        gaps.append(gap("services_unreachable",
                        f"{command}: {refused} lines of its log report a refused connection or an unreachable "
                        "host: the tests run with no network and with only the services the project's CI declares"))
    return entry, gaps


def observe(project: Path, planned: dict, out_dir: Path, engine=None) -> dict:
    """The planned runs in one container run over a copy of `project`, read back from `out_dir`:
    `{state, sites, runs, gaps}`, `state` `ran`, `gap` (no container: `cause`, `remedy`) or `failed` (the
    preparation or the engine failed: `cause`, `remedy`, and nothing of the run is kept)."""
    import container
    project, out_dir = Path(project).resolve(), Path(out_dir)
    shutil.rmtree(out_dir / Path(OUT).name, ignore_errors=True)  # a former run's outputs are not this one's
    for phase in ("prepare", "execute"):
        (out_dir / f"{phase}.log").unlink(missing_ok=True)
    restored = typescript._prepared(project, planned.get("roots") or ())
    prepare, execute, chains = scripts(planned, restored["lines"])
    runs = planned["runs"]

    def inputs() -> dict:
        return {f"{IN}/{RECORDER.name}": RECORDER,
                **{f"{IN}/{name}": preparation.fetched(url, digest, name)
                   for url, digest, name in (preparation.NODE, *chains["files"])}}

    result = container.run_in_container(
        project, ["sh", "-c", execute], image=typescript.IMAGE, out_dir=out_dir, prepare=["sh", "-c", prepare],
        outputs=[OUT], env={**preparation.ENV, "TERM": "dumb", "CI": "true"}, timeout=len(runs) * (LIMIT + 120),
        prepare_timeout=3600, memory=MEMORY, engine=engine, inputs=inputs,
        registries=tuple(dict.fromkeys([*preparation.NODE_REGISTRIES, *restored["hosts"], *chains["hosts"],
                                        *(planned.get("declared") or {}).get("hosts", ())])))  # `dynamic.run`'s
    unrun = list(planned.get("unrun") or ())
    if result["state"] == "gap":
        return {"state": "gap", "cause": result["cause"], "remedy": result["remedy"], "sites": [], "runs": [],
                "gaps": unrun}
    prepared = _text(out_dir / "prepare.log")
    missing = preparation.missing(prepared)
    gaps = [*unrun, *chains["gaps"], *missing, *preparation.restore_gaps(prepared),
            *preparation.generation_gaps(prepared)]
    if result["state"] == "failed":
        cause = result.get("cause") or "the container run failed"
        if any(gap["tool"] == "@babel/core" for gap in missing):
            cause = f"@babel/core {BABEL} could not be installed in the container (check the network): {cause}"
        return {"state": "failed", "cause": cause, "remedy": f"see prepare.log and execute.log in {out_dir}",
                "sites": [], "runs": [], "gaps": gaps}
    marks = {int(number): rest.strip() for number, mark, rest in MARK.findall(_text(out_dir / "execute.log"))
             if mark == "exit"}
    back, entries = out_dir / Path(OUT).name, []
    for number, run in enumerate(runs):
        entry, own = _outcome(run, marks.get(number, ""), _text(back / f"tests-{number}.log"),
                              _observations(back, number), len(list(back.glob(f"observed-{number}-*.json"))),
                              result["state"])
        entries.append(entry)
        gaps += own
    found = sites(back)
    unplaced = sum(1 for site in found for callee in site["callees"]
                   if callee["kind"] == "project" and callee["column"] is None)
    if unplaced:
        gaps.append({"kind": "callee_unplaced", "count": unplaced,
                     "detail": f"{unplaced} observed calls reach a project function the recorder could not place "
                               "in its source (the source map of the code that defines it leads to no function's "
                               "head in the file as written): the end is said without its declaration"})
    return {"state": "ran", "sites": found, "runs": entries, "gaps": gaps}
