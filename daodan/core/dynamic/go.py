"""The Go observer: the modules' tests under the exact recorder (`go_record.go`, a rewrite of the copy's sources).

The recorder. The Go toolchain has no hook that reports calls (`go doc cmd/compile`: coverage counters, the race
detector's and the sanitizers' instrumentation, none gives caller and callee) and pprof samples. What it has is
what `go test -cover` itself does, a rewrite of the sources it compiles, and two documented features that make
the rewrite exact: `runtime.Callers` with `runtime.CallersFrames`, the caller's frame with inlined calls
accounted for, and line directives (`/*line :line:col*/`, `go doc cmd/compile`), which give one call a line
number of its own. `go_record.go` says how; it is built by Daodan's Go with the standard library alone and
rewrites the copy inside the container, never the project.

`plan` reads the pre-map alone: `go test ./...` in each `go-module` unit that holds a `_test.go` file of its own,
on the Go the pre-map states (`preparation.toolchains`), else Daodan's. `observe` is one container run
(`container.run_in_container`, `IMAGE`). The preparation, with the registries: the toolchains and `go mod
download` in each module (`preparation.restore`). The execution, with no network: the recorder is built and
rewrites every planned module, then each module's tests run with `-vet=off` (vet reads the rewritten sources)
under `DAODAN_GO_RECORD`, stopped after `LIMIT` seconds; a record is on disk as soon as its call happens, so a
run that is cut keeps what it saw. Back come the recorder's table, the calls and each module's log.

A site is a call expression, at its callee's name token as the snapshot's reference has it (or where a callee
with no name starts), with the functions entered from it: two calls on one line are two sites, and a call no
function of the modules was entered from has no site. What the recorder does not see is in `go_record.go`: callees
outside the modules, functions started by the runtime or called back by foreign code, deferred calls, files it
could not give site numbers. `read` counts those entries by cause and never places them.
"""
from __future__ import annotations

import collections
import json
import posixpath
import re
import shlex
from pathlib import Path

import dynamic
import preparation
from container_runner import IMAGE  # gcc for cgo, git, timeout

# The observer this module is (`dynamic.observers`): its entry, its recorder's version, the languages it observes.
NAME, VERSION, LANGUAGES = "dynamic-record-go", "1", ("go",)
UNIT_KINDS = frozenset({"go-module"})
RECORDER = Path(__file__).with_name("go_record.go")
RUNNER, ARGV = "go test", ["go", "test", "-vet=off", "./..."]
MEMORY = 4 * 2**30
LIMIT = 1800  # the seconds one module's tests may take
BUILD = 600  # the seconds the recorder's build and its rewrite may take
OUT, IN, T, WORK = "/daodan/out/dynamic-go", preparation.IN, preparation.T, "/work"
PACKAGE = re.compile(r"^(ok  |FAIL|\?   )\t(\S+)(?:\t| )?(.*)$", re.M)
OUTSIDE, NO_CALL = "called from outside the modules", "not at a call (a deferred call)"


def external(callee: dict) -> dict:
    """No callee is outside the project: only the modules' own functions say they were entered."""
    return {"manager": "go", "package": callee.get("module"), "version": None}


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def plan(record: dict, files: list[str], read) -> dict:
    """`{runs, gaps, toolchains}` from the pre-map `record` and the snapshot's `files`: a run is `{root, runner,
    argv}`, a module with no test file of its own a `no_tests` gap. The pre-map names the project's root `.` or
    the empty path: one root."""
    roots = sorted({posixpath.normpath(unit["root"] or ".") for unit in record.get("units", [])
                    if unit["kind"] in UNIT_KINDS})
    if not roots:
        return {"runs": [], "toolchains": [], "gaps": [{
            "kind": "no_tests", "detail": "the pre-map names no Go module (a go.mod): no `go test` to run"}]}
    runs, gaps = [], []
    for root in roots:
        nested = [other for other in roots if other != root and _inside(other, root)]
        tested = any(rel.endswith("_test.go") and _inside(rel, root) and "testdata" not in rel.split("/")
                     and not any(_inside(rel, other) for other in nested) for rel in files)
        if tested:
            runs.append({"root": root, "runner": RUNNER, "argv": ARGV})
        else:
            gaps.append({"kind": "no_tests", "path": root,
                         "detail": f"the Go module in {root} holds no _test.go file: no test runs its code"})
    return {"runs": runs, "gaps": gaps,
            "toolchains": [item for item in record.get("toolchains", []) if item.get("tool") == "go"]}


def scripts(planned: dict) -> tuple[str, str, dict]:
    """The preparation's script, the execution's, and what the preparation needs beside them (`{files, hosts,
    gaps, tools}`: the downloads the copy carries, the hosts beside the registries, the toolchains no installer has,
    Daodan's Go, installed as root before the preparation, which runs as `container.NOBODY`)."""
    roots = [run["root"] for run in planned["runs"]]
    chains = preparation.toolchains(planned.get("toolchains") or [])
    needs = preparation.setup(["go"])  # Daodan's Go builds the recorder, and runs the tests where none is stated
    prepare = ["# dynamic-go prepare", "set -u", f"mkdir -p {T}/bin {preparation.ENV['HOME']}",
               *chains["lines"], preparation.restore("go", roots)]
    words = " ".join(shlex.quote(root) for root in roots)
    own = "GOTOOLCHAIN=local GOFLAGS= GOWORK=off"  # the recorder's build is no build of the project
    execute = ["# dynamic-go execute", "set -u", "export GOPROXY=off", f"OUT={OUT}", "mkdir -p $OUT",
               f"{{ ( cd {IN} && {own} {T}/go/bin/go build -o {T}/bin/daodan-go-record {RECORDER.name} )"
               f" && daodan-go-record {WORK} $OUT/table.json {words}; }} > $OUT/recorder.log 2>&1",
               "echo $? > $OUT/recorder.code",
               'if [ "$(cat $OUT/recorder.code)" = 0 ]; then']
    for number, run in enumerate(planned["runs"]):
        folder = shlex.quote(posixpath.normpath(f"{WORK}/{run['root']}"))
        execute += [f"  ( cd {folder} && DAODAN_GO_RECORD=$OUT/calls.tsv exec timeout -k 30 {LIMIT}"
                    f" {shlex.join(run['argv'])} ) > $OUT/tests-{number}.log 2>&1",
                    f"  echo $? > $OUT/tests-{number}.code"]
    return ("\n".join([*prepare, "exit 0"]) + "\n", "\n".join([*execute, "fi", "exit 0"]) + "\n",
            {"files": [*needs["files"], *chains["files"]], "hosts": (*needs["hosts"], *chains["hosts"]),
             "gaps": chains["gaps"], "tools": {"lines": needs["lines"], "caps": needs["caps"]}})


def read(folder: Path, root: str = WORK) -> tuple[list[dict], dict]:
    """The sites of an observation, the recorder's `table.json` and `calls.tsv` in `folder`, and what it says of
    itself: `functions` rewritten and `entered`, the `records` read, the entries with no site by cause
    (`unplaced`) and the files whose sites the recorder left alone (`skipped`). `root` is the copy's folder,
    which the compiler's file names start with; under `-trimpath` they start with the module's path."""
    folder = Path(folder)
    try:
        table = json.loads((folder / "table.json").read_text(encoding="utf-8"))
        lines = (folder / "calls.tsv").read_text(encoding="utf-8", errors="replace").split("\n")[:-1]
    except (OSError, ValueError):
        return [], {}
    prefixes = [(root.rstrip("/") + "/", "")] + [
        (module + "/", "" if home == "." else home + "/") for home, module in table["modules"].items()]
    functions, files, skipped = table["functions"], table["files"], table["skipped"]
    found, unplaced, entered, records = collections.defaultdict(dict), collections.Counter(), set(), 0
    for line in lines:
        identity, _, rest = line.partition("\t")
        file, _, number = rest.rpartition("\t")
        if not (identity.isdigit() and number.isdigit() and int(identity) < len(functions)):
            continue  # a line a killed process cut
        records += 1
        entered.add(int(identity))
        rel = next((home + file[len(prefix):] for prefix, home in prefixes if file.startswith(prefix)), None)
        at = files.get(rel)
        if at is None:
            unplaced[OUTSIDE] += 1
        elif not at["lines"] < int(number) <= at["lines"] + len(at["calls"]):
            unplaced[skipped.get(rel, NO_CALL)] += 1
        else:
            row, column, name = at["calls"][int(number) - at["lines"] - 1]
            file, declared, start, called = functions[int(identity)]
            found[(rel, row - 1, column - 1, name)][int(identity)] = {
                "kind": "project", "file": file, "line": declared - 1, "column": start - 1, "name": called,
                "type": "function"}
    sites = [{"file": rel, "line": row, "column": column, "name": name, "role": "call",
              "callees": [callee for _identity, callee in sorted(callees.items())]}
             for (rel, row, column, name), callees in sorted(found.items())]
    return sites, {"functions": len(functions), "entered": len(entered), "records": records,
                   "unplaced": dict(sorted(unplaced.items())), "skipped": skipped}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _outcome(run: dict, code: str, log: str, ended: str) -> tuple[dict, list[dict]]:
    """One module's entry and its gaps, from its tests' exit code and their log: `go test` prints a line per
    package (`ok`, `FAIL`, `?`), `[build failed]` or `[setup failed]` where a package's tests did not start. Its
    `state` (`dynamic.TESTS`) is `ran` where a package's tests ran, whatever the others did."""
    packages = collections.Counter()
    for mark, _package, rest in PACKAGE.findall(log):
        packages["no_tests" if mark.startswith("?") else "passed" if mark.startswith("ok") else
                 "not_built" if rest.startswith("[") else "failed"] += 1
    packages.pop("no_tests", None)
    entry = {"root": run["root"], "runner": run["runner"], "argv": run["argv"],
             "exit_code": int(code) if code.strip().isdigit() else None, "packages": dict(sorted(packages.items()))}
    stop = dynamic.stopped(entry["exit_code"], None, LIMIT)
    entry["state"] = ("not_started" if entry["exit_code"] is None else stop if stop
                      else "ran" if packages["passed"] or packages["failed"] else
                      "no_tests" if entry["exit_code"] == 0 else "not_started")
    command, tail = f"{' '.join(run['argv'])} in {run['root']}", " | ".join(
        line.strip() for line in log.strip().splitlines() if not line.startswith(("ok  ", "?   ")))[-600:]

    def gap(kind: str, detail: str) -> dict:
        return {"kind": kind, "path": run["root"], "detail": detail}

    gaps = []
    if entry["exit_code"] is None:
        gaps.append(gap("tests_not_started", f"{command}: the run ended before the tests' exit ({ended})"))
    elif stop == "timeout":
        gaps.append(gap("tests_timeout", f"{command} did not end in {LIMIT} s: what ran until then is observed"))
    elif stop == "killed":
        gaps.append(gap("tests_killed", f"{command} was killed before its end, at the container's memory limit "
                                        f"({MEMORY // 2**30} GB) or {LIMIT} s: what ran until then is observed: "
                                        f"{tail}"))
    elif packages["not_built"] or (entry["exit_code"] and not packages["failed"]):
        gaps.append(gap("tests_not_started", f"{command}: {packages['not_built'] or 'its'} packages' tests did not "
                                             f"start (exit code {entry['exit_code']}): {tail}"))
    elif entry["state"] == "no_tests":
        gaps.append(gap("no_tests", f"{command}: no package had a test to run"))
    if packages["failed"]:
        gaps.append(gap("tests_failed", f"{command}: the tests of {packages['failed']} packages failed, and a test "
                                        f"that fails may stop before its calls: {tail}"))
    return entry, gaps


def observe(project: Path, planned: dict, out_dir: Path, engine=None) -> dict:
    """The planned runs in one container run over a copy of `project`, read back from `out_dir`:
    `{state, sites, runs, gaps, facts}`, `state` `ran`, `gap` (no container: `cause`, `remedy`) or `failed`
    (the preparation or the engine failed: `cause`, `remedy`, and nothing of the run is kept). `facts` is what
    the recorder says of itself (`read`)."""
    import shutil
    import container
    out_dir, runs = Path(out_dir), planned["runs"]
    if not runs:
        return {"state": "ran", "sites": [], "runs": [], "gaps": [], "facts": {}}  # the plan's gaps say why
    back = out_dir / Path(OUT).name
    shutil.rmtree(back, ignore_errors=True)  # a former run's outputs are not this one's
    for phase in ("prepare", "execute"):
        (out_dir / f"{phase}.log").unlink(missing_ok=True)
    prepare, execute, needs = scripts(planned)

    def inputs() -> dict:
        return {f"{IN}/{RECORDER.name}": RECORDER,
                **{f"{IN}/{name}": preparation.fetched(url, digest, name) for url, digest, name in needs["files"]}}

    result = container.run_in_container(
        project, ["sh", "-c", execute], image=IMAGE, out_dir=out_dir, prepare=["sh", "-c", prepare], outputs=[OUT],
        env=preparation.ENV, timeout=BUILD + len(runs) * (LIMIT + 60), memory=MEMORY, engine=engine, inputs=inputs,
        tools=needs["tools"],
        registries=container.REGISTRIES + tuple(dict.fromkeys(  # with the hosts the project declares (`dynamic.run`)
            [*needs["hosts"], *(planned.get("declared") or {}).get("hosts", ())])))
    if result["state"] == "gap":
        return {"state": "gap", "cause": result["cause"], "remedy": result["remedy"], "sites": [], "runs": [],
                "gaps": [], "facts": {}}
    prepared = _text(out_dir / "prepare.log")
    gaps = [*needs["gaps"], *preparation.missing(prepared), *preparation.restore_gaps(prepared),
            *(result.get("gaps") or ())]  # and what the copy left out (`container.copy_perimeter`)
    if result["state"] == "failed":
        return {"state": "failed", "cause": result.get("cause") or "the container run failed",
                "remedy": f"see prepare.log and execute.log in {out_dir}", "sites": [], "runs": [], "gaps": gaps,
                "facts": {}}
    if _text(back / "recorder.code").strip() != "0":
        said = " | ".join(line.strip() for line in _text(back / "recorder.log").strip().splitlines()[-8:])[-600:]
        gaps.append({"kind": "recorder_failed", "detail":
                     f"the recorder did not rewrite the modules, so no test ran ({result['state']}): {said}"})
        return {"state": "ran", "sites": [], "runs": [], "gaps": gaps, "facts": {}}
    entries = []
    for number, run in enumerate(runs):
        entry, own = _outcome(run, _text(back / f"tests-{number}.code"), _text(back / f"tests-{number}.log"),
                              result["state"])
        entries.append(entry)
        gaps += own
    sites, facts = read(back)
    skipped = facts.get("skipped") or {}
    for why, count in sorted(collections.Counter(skipped.values()).items()):
        first = min(rel for rel, reason in skipped.items() if reason == why)
        gaps.append({"kind": "sites_unrecorded", "path": first,
                     "detail": f"{count} Go files ({why}) have no site numbers, {first} among them: the calls "
                               "made from them are not observed"})
    return {"state": "ran", "sites": sites, "runs": entries, "gaps": gaps, "facts": facts}
