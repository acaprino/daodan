"""The Rust observer: each crate's or workspace's `cargo test`, its test executables under Valgrind's Callgrind.

The recorder, compared on each candidate's own documentation for an exact record (every call, its caller and
callee, the call site's position) in an unprivileged container (no ptrace, perf event or eBPF granted):

- Callgrind (valgrind.org/docs/manual/cl-manual.html, manual-core.html): every executed call instruction with the
  function it enters, on the executables as built ("You don't need to recompile"), the call's address mapped
  to file, line and column by the executable's DWARF; it runs the program in its own process, no ptrace. Slow
  (tens of times) and one thread at a time. Adopted (`callgrind.py`).
- uftrace (doc/uftrace-record.md): entry and exit of functions built with `-pg` or `-finstrument-functions`,
  which rustc has only on nightly (`-Z instrument-mcount`), else patched at load time where its disassembler
  can, so not every function; the call site only through its `callsite` trigger. Not exact here.
- LLVM XRay (llvm.org/docs/XRay.html): entry and exit only, no call site, and by default only functions of 200
  instructions or a loop; rustc's `-Z instrument-xray` is nightly. Fails on the call site.
- rustc's stable options: `-C instrument-coverage` counts regions, not calls; `#[track_caller]` gives a callee
  its caller's place but would need a rewrite of every function and is refused on closures (nightly) and on
  `extern` functions. A recorder of Daodan's would see less than Callgrind.
- perf, the sampler the toolchain documents, needs `perf_event_open`, which Docker's default seccomp profile
  blocks, and misses short calls: no second source is needed beside an exact one.

`plan` reads the pre-map alone: `cargo test --workspace --no-fail-fast` at the root of each Cargo workspace,
and of each crate outside one, whose crates hold a test (a `#[test]`-like attribute, or a file in `tests/`); the
Rust a `rust-toolchain` file names, else Daodan's (`rust-version` is a minimum, never installed). `observe` is
one container run (`IMAGE`). The preparation, with the registries: Rust, Valgrind unpacked, `cargo fetch` in each
root. The execution, with no network: Cargo runs each test executable under Callgrind (its runner,
`CARGO_TARGET_<triple>_RUNNER`, which `cargo test` applies to the executables it runs, never to build scripts),
with line tables in every build (`ENV`), each root stopped after `LIMIT` seconds; Valgrind writes its trace
when the process ends, a stopped one included. Then the traces are read in the container (`callgrind.symbolize`).

Not observed, beside what `callgrind.py` says: a doctest (rustdoc runs it, not Cargo's runner); a closure that
the standard library calls (its call site is there: the closure is entered with no site); a closure made a
function pointer, which a shim of `core` enters (the site's callee is the shim, external).
"""
from __future__ import annotations

import collections
import posixpath
import re
import shlex
from pathlib import Path

import preparation
from dynamic import callgrind
from premap.container_runner import IMAGE  # Ubuntu 24.04: gcc for linking, dpkg, python3

# The observer this module is (`dynamic.observers`): its entry, its recorder's version, the languages it observes.
ENTRY, VERSION, LANGUAGES = "dynamic-callgrind-rust", f"{callgrind.VALGRIND_VERSION}+1", ("rust",)
UNIT_KINDS = frozenset({"cargo-crate"})
RUNNER, ARGV = "cargo test", ["cargo", "test", "--workspace", "--no-fail-fast"]
ENV = {"CARGO_NET_OFFLINE": "true", "CARGO_TERM_COLOR": "never", "CARGO_PROFILE_DEV_DEBUG": "line-tables-only",
       "CARGO_PROFILE_TEST_DEBUG": "line-tables-only"}  # the execution's: Callgrind's columns need line tables
RUNNER_VARIABLE = "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUNNER"
RUSTUP_FILES = ("rust-toolchain", "rust-toolchain.toml")  # rustup reads the first where both are
TEST = re.compile(r"#\[[\w:]*test\b")
MEMORY = 6 * 2**30
LIMIT = 3600  # the seconds one root's build and tests under Callgrind may take
BUILD = 600  # the seconds the execution's own lines may take beside the runs
OUT, WORK = "/daodan/out/dynamic-rust", callgrind.WORK
RESULT = re.compile(r"^test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed;", re.M)
STARTED = "\nrunning "  # what a test executable prints first
external = callgrind.external


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def _toolchain(stated: list[dict], root: str) -> list[dict]:
    """The Rust a rustup file names for `root`: the nearest folder's, `rust-toolchain` before its `.toml`."""
    found = [item for item in stated if item.get("tool") == "rust"
             and posixpath.basename(item.get("declared_in") or "") in RUSTUP_FILES
             and _inside(root, posixpath.dirname(item["declared_in"]) or ".")]
    found.sort(key=lambda item: (-item["declared_in"].count("/"),
                                 RUSTUP_FILES.index(posixpath.basename(item["declared_in"]))))
    return found[:1]


def plan(record: dict, files: list[str], read) -> dict:
    """`{runs, gaps, toolchains}` from the pre-map `record`, the snapshot's `files` and `read(rel)` their text: a
    run is `{root, argv}`, a root whose crates hold no test a `no_tests` gap."""
    crates = sorted({unit["root"] for unit in record.get("units", []) if unit["kind"] in UNIT_KINDS})
    if not crates:
        return {"runs": [], "toolchains": [], "gaps": [{
            "kind": "no_tests", "detail": "the pre-map names no Cargo package (a Cargo.toml): no `cargo test` to run"}]}
    homes = {member: item["root"] for item in record.get("workspace") or [] if item.get("tool") == "cargo"
             for member in item.get("members") or ()}
    roots = collections.defaultdict(list)
    for crate in crates:
        roots[homes.get(crate, crate)].append(crate)

    def tested(crate: str) -> bool:
        nested = [other for other in crates if other != crate and _inside(other, crate)]
        own = [rel for rel in files if rel.endswith(".rs") and _inside(rel, crate)
               and not any(_inside(rel, other) for other in nested)]
        tests = posixpath.normpath(f"{crate}/tests")
        return any(_inside(rel, tests) for rel in own) or any(TEST.search(read(rel) or "") for rel in own)

    runs, gaps, chains = [], [], []
    for root, members in sorted(roots.items()):
        if any(tested(crate) for crate in members):
            runs.append({"root": root, "runner": RUNNER, "argv": ARGV})
            chains += [item for item in _toolchain(record.get("toolchains") or [], root) if item not in chains]
        else:
            gaps.append({"kind": "no_tests", "path": root, "detail": f"the crates of {root} hold no test (no "
                         "#[test] attribute, no file in tests/): no test runs their code"})
    return {"runs": runs, "gaps": gaps, "toolchains": chains}


def scripts(planned: dict) -> tuple[str, str, dict]:
    """The preparation's script, the execution's, and what the preparation needs beside them (`{files, hosts,
    gaps}`: the downloads the copy carries, the hosts beside the registries, the toolchains no installer has)."""
    roots = [run["root"] for run in planned["runs"]]
    chains = preparation.toolchains(planned.get("toolchains") or [])
    needs = preparation.setup(["rust"])  # Daodan's Rust runs the tests where no rustup file names one
    prepare = ["# dynamic-rust prepare", "set -u", f"mkdir -p {preparation.T}/bin {preparation.ENV['HOME']}",
               *needs["lines"], callgrind.SETUP, *chains["lines"], preparation.restore("cargo", roots)]
    runner = " ".join([callgrind.VALGRIND_BIN, *callgrind.OPTIONS])
    execute = ["# dynamic-rust execute", "set -u", *(f"export {key}={value}" for key, value in ENV.items()),
               f"export {RUNNER_VARIABLE}={shlex.quote(runner)}", f"OUT={OUT}", "mkdir -p $OUT",
               *callgrind.recorder("$OUT"), 'if [ "$(cat $OUT/recorder.code)" = 0 ]; then']
    for number, run in enumerate(planned["runs"]):
        folder = shlex.quote(posixpath.normpath(f"{WORK}/{run['root']}"))
        execute += callgrind.timed(number, f"( cd {folder} && exec timeout -k 30 {LIMIT} {shlex.join(run['argv'])} )")
    execute += [f"  {line}" for line in callgrind.symbolize("$OUT")]
    return ("\n".join([*prepare, "exit 0"]) + "\n", "\n".join([*execute, "fi", "exit 0"]) + "\n",
            {"files": [*needs["files"], *chains["files"]], "hosts": (*needs["hosts"], *chains["hosts"]),
             "gaps": chains["gaps"]})


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _outcome(run: dict, code: str, log: str, ended: str) -> tuple[dict, list[dict]]:
    """One root's entry and its gaps, from its exit code and its log: each test executable ends with a
    `test result:` line; none where the build failed."""
    results = RESULT.findall(log)
    tests = {"passed": sum(int(passed) for passed, _ in results), "failed": sum(int(failed) for _, failed in results)}
    entry = {"root": run["root"], "runner": run["runner"], "argv": run["argv"], "state": "not_started",
             "tests": tests}
    stop = callgrind.stopped(entry, code, LIMIT, MEMORY)
    command = f"{' '.join(run['argv'])} in {run['root']}"
    tail = " | ".join(line.strip() for line in log.strip().splitlines()
                      if line.strip() and not line.startswith(("test ", "running ", "   Compiling")))[-600:]

    def gap(kind: str, detail: str) -> dict:
        return {"kind": kind, "path": run["root"], "detail": detail}

    if entry["exit_code"] is None:
        return entry, [gap("tests_not_started", f"{command}: the run ended before the tests' exit ({ended})")]
    if stop:
        if STARTED not in "\n" + log:  # stopped in the build: no test ran
            entry["state"] = "not_started"
        return entry, [stop]
    if not results:
        if entry["exit_code"]:
            return entry, [gap("tests_not_started", f"{command}: the tests did not start (exit code "
                                                    f"{entry['exit_code']}): {tail}")]
        entry["state"] = "no_tests"
        return entry, [gap("no_tests", f"{command} built no test executable to run")]
    entry["state"] = "ran"
    if entry["exit_code"]:
        return entry, [gap("tests_failed", f"{command}: {tests['failed']} tests failed, and a test that fails may "
                                           f"stop before its calls: {tail}")]
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
    prepare, execute, needs = scripts(planned)

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
