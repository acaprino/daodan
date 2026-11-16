"""The C and C++ observer: the tests a CMake build declares, run by CTest under Valgrind's Callgrind.

The recorder, compared on each candidate's own documentation for an exact record (every call, its caller and
callee, the call site's position) in an unprivileged container (no ptrace, perf event or eBPF granted):

- Callgrind (valgrind.org/docs/manual/cl-manual.html, manual-core.html): every executed call instruction with the
  function it enters, function pointers and virtual calls included, on the binaries as the build makes them;
  the call's address is mapped to file, line and column by their DWARF. It runs the program in its own process:
  no ptrace. Slow (tens of times), one thread at a time. Adopted, the recorder of the Rust observer too
  (`callgrind.py`).
- uftrace (doc/uftrace-record.md): entry and exit of the functions the build instruments (`-pg`,
  `-finstrument-functions`) or that it patches at load time where its disassembler can; the call site only
  through its `callsite` trigger, named per function. Exact only with every compile flag of the project changed
  and a trigger on every function: Callgrind sees as much on the build as it is.
- LLVM XRay (llvm.org/docs/XRay.html): clang's `-fxray-instrument`, entry and exit only, no call site, and by
  default only functions of 200 instructions or a loop. Fails on the call site.
- `-finstrument-functions` alone (GCC's and clang's): `__cyg_profile_func_enter(this_fn, call_site)` gives both
  ends, but a recorder would be Daodan's to write, and one exists.
- perf, the sampler, needs `perf_event_open`, which Docker's default seccomp profile blocks: no second source.

`plan` reads the pre-map alone: each top CMake folder (a CMakeLists.txt no other one's folder holds, as
`premap.cmake` names a top) that holds a `cmake-target` and whose CMake files declare a test (`add_test` or a test
framework's discovery) and turn testing on (`enable_testing`, `include(CTest)`): its configure reaches what it
adds below it. A unit another build makes is a `runner_not_observed` gap.
`observe` is one container run (`IMAGE`). The preparation, with the registries: CMake at the indexer's pin
(`indexers.clang.CMAKE`, or with mise the minimum the pre-map states above it), Valgrind unpacked, and each
root's dependencies restored as the C and C++ analyzer restores them (`indexers.clang.restores`: vcpkg or Conan,
the pre-map's choice). The
execution, with no network: per root a Debug build (`-g -O0`, so calls stay calls and have lines) outside the
copy, then CTest under Callgrind, which traces each test it starts (`--trace-children`), stopped after `LIMIT`
seconds; then the traces are read in the container (`callgrind.symbolize`).

Not observed, beside what `callgrind.py` says: a test CTest runs through a shell or an interpreter (Valgrind
skips the system's programs and what they start); a test CTest stops at its own `TIMEOUT` (killed, it writes no
trace); a dependency CMake fetches at configure (no network then: the configure fails, a gap).
"""
from __future__ import annotations

import posixpath
import re
import shlex
from pathlib import Path

import preparation
from dynamic import callgrind
from indexers import clang as index
from premap import cmake as premap_cmake
from premap.container_runner import IMAGE  # Ubuntu 24.04: gcc, g++, make, dpkg, python3

# The observer this module is (`dynamic.observers`): its entry, its recorder's version, the languages it observes.
ENTRY, VERSION, LANGUAGES = "dynamic-callgrind-clang", f"{callgrind.VALGRIND_VERSION}+1", ("c", "cpp")
RUNNER, ARGV = "ctest", ["ctest", "--output-on-failure", "--timeout", "1800"]  # a test's own TIMEOUT stays its own
TESTS = re.compile(r"(?im)^[ \t]*(?:add_test|gtest_discover_tests|gtest_add_tests|catch_discover_tests"
                   r"|doctest_discover_tests)[ \t]*\(")
TESTING = re.compile(r"(?im)^[ \t]*(?:enable_testing[ \t]*\(|include[ \t]*\([ \t]*CTest\b)")
CMAKE = (index.CMAKE[1], index.CMAKE[2], "cmake.tar.gz")
CMAKE_SETUP = (f"{{ tar -xzf {preparation.IN}/cmake.tar.gz -C {preparation.T} && mv {preparation.T}/cmake-"
               f"{index.CMAKE[0]}-linux-x86_64 {preparation.T}/cmake ; }} >&2"
               f" || echo 'DAODAN-MISSING cmake@{index.CMAKE[0]}' >&2")
BUILDS = f"{preparation.STATE}/build"  # each root's build folder, outside the copy
MEMORY = 6 * 2**30
LIMIT = 3600  # the seconds one root's configure, build and tests under Callgrind may take
BUILD = 600  # the seconds the execution's own lines may take beside the runs
OUT, WORK = "/daodan/out/dynamic-clang", callgrind.WORK
STARTED, NONE = "Test project ", "No tests were found"
SUMMARY = re.compile(r"(\d+)% tests passed, (\d+) tests? failed out of (\d+)")
NOISE = ("-- ", "[", "Scanning ", "Consolidate ", "gmake", "make[")  # CMake's and make's progress lines
external = callgrind.external


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def plan(record: dict, files: list[str], read) -> dict:
    """`{runs, gaps, toolchains}` from the pre-map `record`, the snapshot's `files` and `read(rel)` their text: a
    run is `{root, runner, argv}`, a root that declares no test a `no_tests` gap."""
    units, states = index.configure_roots(record.get("units"), record.get("workspace"))
    gaps = [{"kind": "runner_not_observed", "path": state["root"],
             "detail": f"{state['root']}: {state['cause']}; its tests are not observed"} for state in states]
    lists = sorted({posixpath.dirname(rel) or "." for rel in files if posixpath.basename(rel) == premap_cmake.FILE},
                   key=lambda folder: (folder.count("/"), folder))
    roots = [top for top in lists if not any(other != top and _inside(top, other) for other in lists)
             and any(_inside(unit, top) for unit in units)]  # a top configure reaches what it adds below it
    if not roots:
        return {"runs": [], "toolchains": [], "gaps": gaps or [{
            "kind": "no_tests", "detail": "the pre-map names no C or C++ unit built with CMake: no ctest to run"}]}
    runs = []
    for root in roots:
        texts = [read(rel) or "" for rel in files if _inside(rel, root)
                 and (posixpath.basename(rel) == premap_cmake.FILE or rel.endswith(".cmake"))]
        if not (any(TESTS.search(text) for text in texts) and any(TESTING.search(text) for text in texts)):
            gaps.append({"kind": "no_tests", "path": root, "detail": f"no CMake file of {root} declares a test "
                         "(add_test, with enable_testing or include(CTest)): no ctest to run"})
            continue
        runs.append({"root": root, "runner": RUNNER, "argv": ARGV})
    wanted = index.wanted_cmake([item for item in record.get("toolchains") or [] if item.get("tool") == "cmake"])
    return {"runs": runs, "gaps": gaps, "toolchains": [wanted] if wanted and runs else []}


def scripts(planned: dict, restored: dict) -> tuple[str, str, dict]:
    """The preparation's script, the execution's, and what the preparation needs beside them (`{files, hosts,
    gaps}`: the downloads the copy carries, the hosts beside the registries, the toolchains no installer has);
    `restored` is the analyzer's restore of each root (`indexers.clang.restores`)."""
    chains = preparation.toolchains(planned.get("toolchains") or [])
    needs = preparation.setup(sorted({item["manager"] for item in restored.values()}))
    prepare = ["# dynamic-clang prepare", "set -u", f"mkdir -p {preparation.T}/bin {preparation.ENV['HOME']}",
               CMAKE_SETUP, *needs["lines"], callgrind.SETUP, *chains["lines"],
               *(item["line"] for item in restored.values())]
    valgrind = shlex.join([callgrind.VALGRIND_BIN, *callgrind.OPTIONS])
    execute = ["# dynamic-clang execute", "set -u", f"OUT={OUT}", "mkdir -p $OUT", *callgrind.recorder("$OUT"),
               'if [ "$(cat $OUT/recorder.code)" = 0 ]; then',
               f"  CTEST=$(ls -d {preparation.T}/mise/installs/cmake/*/bin/ctest 2>/dev/null | head -n 1)",
               f'  [ -n "$CTEST" ] || CTEST={preparation.T}/cmake/bin/ctest; export CTEST']
    for number, run in enumerate(planned["runs"]):
        key = premap_cmake._key(run["root"])
        build = f"{BUILDS}/{key}"
        steps = (f'i={premap_cmake.PREP}/{key}/init.cmake; if [ -f "$i" ]; then set -- -C "$i"; else set --; fi;'
                 f' cmake "$@" -S . -B {build} -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON'
                 f' && cmake --build {build} -j "$(nproc)" && cd {build}'
                 f' && {valgrind} "$CTEST" {shlex.join(run["argv"][1:])}')
        folder = shlex.quote(posixpath.normpath(f"{WORK}/{run['root']}"))
        execute += callgrind.timed(number, f"( cd {folder} && exec timeout -k 30 {LIMIT} sh -c {shlex.quote(steps)} )")
    execute += [f"  {line}" for line in callgrind.symbolize("$OUT")]
    return ("\n".join([*prepare, "exit 0"]) + "\n", "\n".join([*execute, "fi", "exit 0"]) + "\n",
            {"files": [CMAKE, *needs["files"], *chains["files"]], "hosts": (*needs["hosts"], *chains["hosts"]),
             "gaps": chains["gaps"]})


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _outcome(run: dict, code: str, log: str, ended: str) -> tuple[dict, list[dict]]:
    """One root's entry and its gaps, from its exit code and its log: CTest says `Test project` when it starts
    and ends with a summary line; before it, the configure's and the build's words."""
    found = SUMMARY.findall(log)
    failed, total = (int(found[-1][1]), int(found[-1][2])) if found else (0, 0)
    entry = {"root": run["root"], "runner": run["runner"], "argv": run["argv"], "state": "not_started",
             "tests": {"passed": total - failed, "failed": failed}}
    stop = callgrind.stopped(entry, code, LIMIT, MEMORY)
    command = f"{' '.join(run['argv'])} in {run['root']}"
    tail = " | ".join(line.strip() for line in log.strip().splitlines()
                      if line.strip() and not line.startswith(NOISE))[-600:]

    def gap(kind: str, detail: str) -> dict:
        return {"kind": kind, "path": run["root"], "detail": detail}

    if entry["exit_code"] is None:
        return entry, [gap("tests_not_started", f"{command}: the run ended before the tests' exit ({ended})")]
    if stop:
        if STARTED not in log:  # stopped in the configure or the build: no test ran
            entry["state"] = "not_started"
        return entry, [stop]
    if STARTED not in log:
        return entry, [gap("tests_not_started", f"the configure or the build of {run['root']} failed (exit code "
                                                f"{entry['exit_code']}), so no test ran: {tail}")]
    if NONE in log:
        entry["state"] = "no_tests"
        return entry, [gap("no_tests", f"{command}: the build declares no test with the options given "
                                       "(BUILD_TESTING on, the project's defaults otherwise)")]
    entry["state"] = "ran"
    if failed or entry["exit_code"]:
        return entry, [gap("tests_failed", f"{command}: {failed} tests failed, and a test that fails may stop "
                                           f"before its calls: {tail}")]
    return entry, []


def observe(project: Path, planned: dict, out_dir: Path, engine=None) -> dict:
    """The planned runs in one container run over a copy of `project`, read back from `out_dir`:
    `{state, sites, runs, gaps, facts}`, `state` `ran`, `gap` (no container: `cause`, `remedy`) or `failed`
    (the preparation or the engine failed: `cause`, `remedy`, and nothing of the run is kept). `facts` is what
    the readers say of themselves (`callgrind.read`)."""
    import shutil
    import container
    out_dir, runs = Path(out_dir), planned["runs"]
    if not runs:
        return {"state": "ran", "sites": [], "runs": [], "gaps": [], "facts": {}}  # the plan's gaps say why
    back = out_dir / Path(OUT).name
    shutil.rmtree(back, ignore_errors=True)  # a former run's outputs are not this one's
    for phase in ("prepare", "execute"):
        (out_dir / f"{phase}.log").unlink(missing_ok=True)
    prepare, execute, needs = scripts(planned, index.restores(project, [run["root"] for run in runs]))

    def inputs() -> dict:
        return {**callgrind.inputs(),
                **{f"{preparation.IN}/{name}": preparation.fetched(url, digest, name)
                   for url, digest, name in needs["files"]}}

    result = container.run_in_container(
        project, ["sh", "-c", execute], image=IMAGE, out_dir=out_dir, prepare=["sh", "-c", prepare], outputs=[OUT],
        env=preparation.ENV, timeout=BUILD + callgrind.SYMBOLIZE + len(runs) * (LIMIT + 60), memory=MEMORY,
        registries=container.REGISTRIES + tuple(dict.fromkeys(needs["hosts"])), engine=engine, inputs=inputs)
    if result["state"] == "gap":
        return {"state": "gap", "cause": result["cause"], "remedy": result["remedy"], "sites": [], "runs": [],
                "gaps": [], "facts": {}}
    prepared = _text(out_dir / "prepare.log")
    gaps = [*needs["gaps"], *preparation.missing(prepared), *preparation.restore_gaps(prepared)]
    if result["state"] == "failed":
        return {"state": "failed", "cause": result.get("cause") or "the container run failed",
                "remedy": f"see prepare.log and execute.log in {out_dir}", "sites": [], "runs": [], "gaps": gaps,
                "facts": {}}
    failed = callgrind.recorder_failed(back, result["state"])
    if failed:
        return {"state": "ran", "sites": [], "runs": [], "gaps": [*gaps, failed], "facts": {}}
    entries = []
    for number, run in enumerate(runs):
        entry, own = _outcome(run, _text(back / f"tests-{number}.code"), _text(back / f"tests-{number}.log"),
                              result["state"])
        entries.append(entry)
        gaps += own
    sites, facts = callgrind.read(back, project)
    return {"state": "ran", "sites": sites, "runs": entries, "gaps": [*gaps, *callgrind.gaps(back)], "facts": facts}
