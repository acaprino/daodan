"""The part of the C and C++ index that runs in the container: each unit's compilation database from its own build,
then scip-clang over it. Standard library only: the image's python3 runs it.

    python3 clang_run.py UNITS_JSON OUT_DIR JOBS [CMAKE]    # the execution, with no network
    python3 clang_run.py prepare UNITS_JSON [CMAKE]         # in the preparation, through the proxy

JOBS is how many compiler processes scip-clang and make run at once: the container's share of the machine, as the
caller gives it, never the machine's processor count.

A unit is `{"root", "build"}`, the folder its build runs in and the build, `cmake` when none is given. `meson`:
`meson setup`, wraps never downloaded, whose Ninja backend writes the database. `make` (`targets`): the project's
make under Bear, every target remade, after the project's own configure with `configure`. `autotools`: `autoreconf`, the configure in a build folder of its own,
and make under Bear there. `go` (`packages`, `download`): the go command builds the cgo packages under
Bear's compiler wrappers, with the modules the preparation downloaded when the unit requires some; only commands for
files of the copy are kept. Bear is Ubuntu's package, installed with dpkg from the copy. `bazel`: the compile
actions of the workspace's own targets, which the preparation's `bazel aquery` gave (it fetches what the analysis
reads), run from the workspace's root. A build that ends with an error keeps the commands it ran, its end the cause
of the files without one; a build that writes no database is `failed` with the tool's own output.

A `cmake` unit is configured from its root, with `init`, the initial cache the preparation's restore of
vcpkg or Conan writes, read when it is there, and `absent`, the submodules the pre-map finds not checked out. In
the execution a dependency the project fetches is never downloaded: CMake runs with FETCHCONTENT_FULLY_DISCONNECTED,
and CMake's dependency provider interface (`PROVIDER`, given through CMAKE_PROJECT_TOP_LEVEL_INCLUDES) records each
dependency the project asks FetchContent_MakeAvailable for, with the URLs it declares, and supplies none. A unit
whose configure then fails is not indexed: `unavailable` with the absent submodule CMake's output names, or with
what CMake recorded when it asked for a download, else `failed`; CMake's own output, unparsed, either way.
`file(DOWNLOAD)` and ExternalProject are not recorded. A unit marked `fetch`, whose recorded hosts the user allows
(`indexers/clang.py`, `approved`), is configured in the preparation instead, FetchContent downloading through the
proxy into a folder of its own (FETCHCONTENT_BASE_DIR); the execution takes that configure's database without the
commands of the dependencies' files, which are not the project's (`downloaded`).

scip-clang reads each database with the commands of a compiler that is not clang reading the builtin headers of
the clang scip-clang is built on, which the copy carries (`builtin_headers`): with GCC's, which scip-clang gives
them, clang stops on the intrinsics.

`OUT_DIR/result.json` holds, per unit, its state, its steps (`returncode`, `seconds`, the output's tail), the
files of the compilation database with how many commands compile each, and the index it wrote
(`index-<n>.scip`), with the container's memory peak.
"""
from __future__ import annotations

import collections
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.parse
import zipfile
from pathlib import Path

TOOLS = Path("/daodan/state/clang")  # where the copy carries CMake and scip-clang (indexers/clang.py, TOOLS)
WORK = Path("/work")  # the project's copy
SCRATCH = Path("/tmp/daodan-clang")
T = Path("/daodan/state/tools")  # what the preparation installs, mise's toolchains (preparation.T)
GOPATH = "/daodan/state/go"  # Go's module cache, which the preparation's download fills (preparation.ENV)
PREPARED = Path("/daodan/state/clang-prepared")  # what the preparation recorded per unit, for the execution
BAZEL_QUERY = 'mnemonic("CppCompile", //...)'  # the compile actions of the workspace's own targets
DEPENDENCY_FILE = ("-MD", "-fno-canonical-system-headers")  # with `-MF FILE`: what writes a Bazel action's .d file
BEAR_BUILDS = ("make", "go", "autotools")
WHAT = {"cmake": "the configure", "meson": "meson setup", "make": "make under Bear", "bazel": "bazel aquery",
        "go": "go build under Bear", "autotools": "make under Bear"}  # what writes each build's compilation database
OUTSIDE = "download-outside-registries"  # the cause the map-driven round counts
ABSENT = "submodule-absent"  # a folder the configure reads is a submodule the checkout lacks
OWN_BUILTINS = {"-nostdinc", "-nobuiltininc"}  # a command that drops the builtin headers itself
# The project's own configure (no Autotools'), as the pre-map ran it (`premap/make.py`, CONFIGURE).
CONFIGURE = "if [ -x ./configure ]; then ./configure; else sh ./configure; fi"
ERROR_TAIL = 4000
UNCOVERED = "FetchContent asked for nothing; file(DOWNLOAD) and ExternalProject are not recorded"
PROVIDER = r"""# Written by Daodan: records each dependency the project asks FetchContent_MakeAvailable
# for, with the URLs it declares, and supplies none, so FetchContent goes on with downloads disabled.
function(daodan_record_fetch method name)
  cmake_parse_arguments(PARSE_ARGV 2 dep "" "GIT_REPOSITORY;SVN_REPOSITORY;HG_REPOSITORY" "URL")
  string(JOIN "\t" line "${name}" ${dep_URL} ${dep_GIT_REPOSITORY} ${dep_SVN_REPOSITORY} ${dep_HG_REPOSITORY})
  file(APPEND "${DAODAN_FETCH_LOG}" "${line}\n")
endfunction()
cmake_language(SET_DEPENDENCY_PROVIDER daodan_record_fetch SUPPORTED_METHODS FETCHCONTENT_MAKEAVAILABLE_SERIAL)
"""


def run(command: list[str], cwd: Path, timeout: float = 3600, stdout: Path | None = None
        ) -> tuple[int | None, str, float]:
    """`(returncode, output, seconds)`; None as returncode on a timeout. With `stdout`, the command's standard
    output goes into that file and `output` is its standard error."""
    started = time.monotonic()
    handle = open(stdout, "wb") if stdout else None
    try:
        done = subprocess.run(command, cwd=cwd, timeout=timeout, stdout=handle or subprocess.PIPE,
                              stderr=subprocess.PIPE if handle else subprocess.STDOUT)
        code, output = done.returncode, done.stderr if handle else done.stdout
    except subprocess.TimeoutExpired as error:
        code, output = None, error.stderr if handle else error.stdout
    finally:
        if handle:
            handle.close()
    return code, (output or b"").decode("utf-8", errors="replace"), round(time.monotonic() - started, 1)


def configure_command(cmake: str, unit: dict, build: Path, log: Path, deps: Path | None = None) -> list[str]:
    """CMake's configure of a unit, the provider recording what FetchContent is asked for: with no download
    (FETCHCONTENT_FULLY_DISCONNECTED), or, with `deps`, FetchContent downloading into it (FETCHCONTENT_BASE_DIR)."""
    init = unit.get("init")  # the initial cache the preparation's restore writes, naming the toolchain file
    return [cmake, *(["-C", init] if init and Path(init).is_file() else []), "-S", str(WORK / unit.get("root", ".")),
            "-B", str(build), "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            f"-DFETCHCONTENT_BASE_DIR={deps}" if deps else "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
            f"-DCMAKE_PROJECT_TOP_LEVEL_INCLUDES={SCRATCH / 'provider.cmake'}", f"-DDAODAN_FETCH_LOG={log}"]


def fetch_record(log: Path) -> list[dict]:
    """What the provider recorded: each dependency once, `{name, urls}`; one declared without a URL downloads
    nothing and is left out."""
    if not log.is_file():
        return []
    out: dict[str, list[str]] = {}
    for line in log.read_text(encoding="utf-8", errors="replace").split("\n"):
        name, *urls = line.split("\t")
        if name and urls:
            out.setdefault(name, urls)
    return [{"name": name, "urls": urls} for name, urls in out.items()]


def _host(url: str) -> str | None:
    """The host of an https URL at port 443, the only downloads the proxy opens (`urllib.parse.urlsplit`); None for
    any other: git's scp form (`git@host:path`), which urlsplit reads as no URL, a local path, another scheme or
    port."""
    try:
        split = urllib.parse.urlsplit(url)
        return split.hostname if split.scheme == "https" and split.port in (None, 443) else None
    except ValueError:  # a port that is no number, a bracketed host that is no address
        return None


def hosts(fetched: list[dict]) -> tuple[list[str], list[str]]:
    """The hosts the provider's record (`fetch_record`) downloads from, and its URLs the proxy cannot open."""
    urls = [url for item in fetched for url in item["urls"]]
    return sorted({_host(url) for url in urls} - {None}), [url for url in urls if _host(url) is None]


def configure(runner, cmake: str, unit: dict, build: Path, log: Path,
              deps: Path | None = None) -> tuple[list[dict], dict]:
    """One unit's configure step and its state: `configured`, else `unavailable` or `failed` with the cause and
    CMake's output (`error`), as CMake wrote it. With `deps`, the configure that downloads (`configure_command`):
    its failure after a download is `failed`, the hosts allowed."""
    log.unlink(missing_ok=True)
    code, output, seconds = runner(configure_command(cmake, unit, build, log, deps), WORK)
    steps = [_step("configure", code, output, seconds)]
    if code == 0:
        return steps, {"state": "configured"}
    error, fetched = output[-ERROR_TAIL:], fetch_record(log)
    absent = [path for path in unit.get("absent", ()) if re.search(rf"(?<![\w.-]){re.escape(path)}(?![\w.-])", output)]
    if absent:
        return steps, {"state": "unavailable", "kind": ABSENT, "error": error,
                       "cause": f"the configure reads {' and '.join(absent)}: "
                                f"{'a git submodule' if len(absent) == 1 else 'git submodules'} not checked out "
                                "(git submodule update --init)"}
    ended = "timed out" if code is None else f"ended with exit code {code}"
    if not fetched:
        return steps, {"state": "failed", "error": error, "cause": f"the configure {ended}; {UNCOVERED}"}
    named = ", ".join(sorted({_host(url) or url for item in fetched for url in item["urls"]}))
    if deps:
        return steps, {"state": "failed", "fetched": fetched, "error": error,
                       "cause": f"the configure {ended}, FetchContent downloading from {named} through the proxy"}
    return steps, {"state": "unavailable", "kind": OUTSIDE, "fetched": fetched, "error": error,
                   "cause": f"the configure needs what FetchContent would download from {named}, outside the allowed "
                            "registries"}


def _file(entry: dict) -> Path:
    return Path(os.path.normpath(Path(entry["directory"], entry["file"])))


def compiled(compdb: Path) -> dict[str, int]:
    """Checkout-relative files of a compilation database, with how many commands compile each."""
    out = collections.Counter()
    for entry in json.loads(compdb.read_text(encoding="utf-8")):
        path = _file(entry)
        try:
            out[path.relative_to(WORK).as_posix()] += 1
        except ValueError:
            out[path.as_posix()] += 1
    return dict(sorted(out.items()))


def _search_dirs(compiler: str, language: str) -> list[str]:
    err = subprocess.run([compiler, f"-x{language}", "-E", "-v", "-"], input="", capture_output=True,
                         text=True).stderr.split("\n")
    try:
        start, end = err.index("#include <...> search starts here:") + 1, err.index("End of search list.")
    except ValueError:
        return []
    return [os.path.realpath(line.strip()) for line in err[start:end] if line.strip()]


def _clean(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.\-]", "_", text)


def package_map(project: str) -> list[dict]:
    """The copy's root as the project, each directory under the system include paths as the Debian package
    owning most of its direct files (dpkg's file lists): the package identity scip-clang writes in symbols."""
    owners = collections.defaultdict(set)
    for listing in Path("/var/lib/dpkg/info").glob("*.list"):
        name = listing.stem.split(":")[0]
        for line in listing.read_text(encoding="utf-8", errors="replace").split("\n"):
            if line:
                owners[os.path.realpath(line)].add(name)
    versions = dict(line.split(" ", 1) for line in subprocess.run(
        ["dpkg-query", "-W", "-f", "${Package} ${Version}\\n"], capture_output=True, text=True).stdout.split("\n")
        if " " in line)
    entries = [{"path": ".", "package": project}]
    for root in dict.fromkeys(_search_dirs("cc", "c") + _search_dirs("c++", "c++")):
        for here, _dirs, names in os.walk(root):
            votes = collections.Counter(owner for name in names
                                        for owner in owners.get(os.path.realpath(os.path.join(here, name)), ()))
            if votes:
                owner = votes.most_common(1)[0][0]
                entries.append({"path": here, "package": f"{_clean(owner)}@{_clean(versions.get(owner, 'unknown'))}"})
    return entries


def _diagnostics(text: str) -> dict:
    return {"errors": len(re.findall(r": (?:fatal )?error: ", text)), "warnings": len(re.findall(r": warning: ", text)),
            "error_examples": list(dict.fromkeys(re.findall(r"\S+: (?:fatal )?error: .*", text)))[:8]}


def _peak() -> int | None:
    for name in ("/sys/fs/cgroup/memory.peak", "/sys/fs/cgroup/memory/memory.max_usage_in_bytes"):
        try:
            return round(int(Path(name).read_text().strip()) / 2**20)
        except (OSError, ValueError):
            continue
    return None


def index_command(scip_clang: Path, compdb: Path, packages: Path, jobs: int) -> list[str]:
    return [str(scip_clang), f"--compdb-path={compdb}", f"--package-map-path={packages}", f"--jobs={jobs}",
            "--show-compiler-diagnostics"]


def unpack_headers() -> tuple[Path, str]:
    """Clang's builtin headers, from the tar the copy carries (`indexers/clang.py`, `clang_headers`), unpacked into
    the scratch folder: their folder, and clang's version, which the tar's name gives."""
    archive = next(TOOLS.glob("clang-*-headers.tar"))
    with tarfile.open(archive) as bundle:
        bundle.extractall(SCRATCH / "clang", filter="data")
    return SCRATCH / "clang" / "include", archive.name.removeprefix("clang-").removesuffix("-headers.tar")


def builtin_headers(runner, compdb: Path, target: Path, headers: Path) -> None:
    """`compdb` into `target`, each command of a compiler that is not clang reading clang's own builtin headers.
    scip-clang gives such a command, as clang's resource folder, the GCC install folder, whose builtin headers
    (mmintrin.h, xmmintrin.h and on) call builtins clang lacks: `-nobuiltininc` drops them, `-isystem` reads
    clang's (`headers`), and `-idirafter` the compiler's own include folder last, for the headers clang has none
    of (omp.h, quadmath.h). A clang, which answers `-print-resource-dir`, keeps its own; a command that drops the
    builtin headers itself is left as it is. Each compiler is asked once."""
    asked: dict[str, list[str] | None] = {}

    def answer(command: list[str], cwd: Path) -> tuple[int | None, str]:
        try:
            code, output, _seconds = runner(command, cwd)
        except OSError:  # no such compiler, or no such folder
            return None, ""
        return code, output

    entries = json.loads(compdb.read_text(encoding="utf-8"))
    for entry in entries:
        words = list(entry["arguments"]) if "arguments" in entry else shlex.split(entry.get("command", ""))
        if not words or OWN_BUILTINS & set(words):
            continue
        cwd, compiler = Path(entry.get("directory") or WORK), words[0]
        key = str(cwd / compiler) if "/" in compiler and not os.path.isabs(compiler) else compiler
        if key not in asked:
            if answer([compiler, "-print-resource-dir"], cwd)[0] == 0:
                asked[key] = None
            else:
                code, output = answer([compiler, "-print-file-name=include"], cwd)
                folder = (output.strip().splitlines() or [""])[-1]
                asked[key] = ["-nobuiltininc", "-isystem", str(headers),
                              *(["-idirafter", folder] if code == 0 and os.path.isabs(folder)
                                and os.path.isdir(folder) else [])]
        if asked[key] is None:
            continue
        at = words.index("--") if "--" in words else len(words)
        words[at:at] = asked[key]
        if "arguments" in entry:
            entry["arguments"] = words
        else:
            entry["command"] = shlex.join(words)
    target.write_text(json.dumps(entries, indent=1) + "\n", encoding="utf-8")


def cmake_tool(given: str | None, scratch: Path) -> str:
    """The CMake the preparation installed (`given`, when it is there), else the pinned one unpacked in `scratch`."""
    if given and Path(given).is_file():
        return given
    return str(next(scratch.glob("cmake-*/bin/cmake"), Path("cmake")))


def cmake_ready(given: str | None) -> str:
    """The CMake a configure runs (`cmake_tool`), the pin unpacked into the scratch folder when `given` is not there,
    with the provider the configure includes beside it."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    if not (given and Path(given).is_file()):
        run(["tar", "-xzf", str(TOOLS / "cmake.tar.gz"), "-C", str(SCRATCH)], SCRATCH)
    (SCRATCH / "provider.cmake").write_text(PROVIDER, encoding="utf-8")
    return cmake_tool(given, SCRATCH)


def downloaded(number: int, build: Path) -> tuple[list[dict], dict]:
    """Unit `number` as the preparation configured it, FetchContent downloading (`prepare`): its steps and state,
    and, once it configured, its compilation database in `build` without the commands of the files of the
    dependencies it downloaded, which are not the project's."""
    folder = PREPARED / str(number)
    try:
        held = json.loads((folder / "configure.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], {"state": "failed", "cause": "the preparation recorded no configure: its output is in the run's "
                                               "prepare.log"}
    database = folder / "build" / "compile_commands.json"
    if held["state"]["state"] == "configured" and database.is_file():
        deps = folder / "deps"
        build.mkdir(parents=True, exist_ok=True)
        entries = [entry for entry in json.loads(database.read_text(encoding="utf-8"))
                   if deps not in _file(entry).parents]
        (build / "compile_commands.json").write_text(json.dumps(entries, indent=1) + "\n", encoding="utf-8")
    return held["steps"], held["state"]


# ---------------------------------------------------------------------------------------------------------
# The other builds: each writes `compile_commands.json` into the unit's build folder


def _step(name: str, code: int | None, output: str, seconds: float) -> dict:
    return {"step": name, "returncode": code, "seconds": seconds, "tail": output[-2500:]}


def _ended(what: str, code: int | None, output: str) -> dict:
    """A step that gave no database: `failed`, with the tool's output and, in the cause, its first line naming an
    error, else its last line."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    line = next((line for line in lines if re.search(r"(?i)\berror\b", line)), lines[-1] if lines else "")
    ended = "timed out" if code is None else f"ended with exit code {code}"
    return {"state": "failed", "error": output[-ERROR_TAIL:],
            "cause": f"{what} {ended}" + (f": {line[:300]}" if line else "")}


def _recorded(out: Path, tool: str, code: int | None, output: str) -> dict:
    """A build Bear recorded into `out`: configured, the build's own end the cause of the files it did not compile
    when it failed; failed, with Bear's output, when Bear wrote nothing."""
    if not out.is_file():
        return _ended(f"{tool} under Bear", code, output)
    ended = "timed out" if code is None else f"ended with exit code {code}"
    return {"state": "configured", **({"cause": f"{tool} {ended}"} if code != 0 else {})}


def meson(runner, unit: dict, build: Path, env: dict[str, str]) -> tuple[list[dict], dict]:
    """Meson's setup, whose Ninja backend writes the compilation database; wraps are never downloaded."""
    code, output, seconds = runner(["env", *(f"{key}={value}" for key, value in env.items()), "python3", "-m",
                                    "mesonbuild.mesonmain", "setup", "--wrap-mode", "nodownload", str(build)],
                                   WORK / unit.get("root", "."))
    return [_step("meson setup", code, output, seconds)], {"state": "configured"} if code == 0 else \
        _ended("meson setup", code, output)


def _under_bear(runner, name: str, first: list[str], again: list[str],
                cwd: Path) -> tuple[list[dict], int | None, str]:
    """A build under Bear, and once more, appending to its database (`again`), when it ends with an error: in
    gVisor, Modal's sandboxes, Bear's report of a process fails now and then (one build in ten, measured) and the
    process with it; a real error ends the second pass too. The steps, and the last pass's end and output."""
    code, output, seconds = runner(first, cwd)
    steps = [_step(name, code, output, seconds)]
    if code != 0:
        code, output, seconds = runner(again, cwd)
        steps.append(_step(f"{name} again", code, output, seconds))
    return steps, code, output


def make(runner, unit: dict, build: Path, jobs: int) -> tuple[list[dict], dict]:
    """The project's make under Bear in the unit's folder: the targets the pre-map states, each remade, the build
    going on past an error; its second pass makes only what is not made. With `configure`, the project's own
    configure first, with its defaults, which writes the Makefile."""
    build.mkdir(parents=True, exist_ok=True)
    out, folder, configured = build / "compile_commands.json", WORK / unit.get("root", "."), []
    if unit.get("configure"):
        code, output, seconds = runner(["sh", "-c", CONFIGURE], folder)
        configured.append(_step("configure", code, output, seconds))
        if code != 0:
            return configured, _ended("configure", code, output)
    targets = [f"-j{jobs}", *unit.get("targets", ())]
    steps, code, output = _under_bear(runner, "make under Bear",
                                      ["bear", "--output", str(out), "--", "make", "-B", "-k", *targets],
                                      ["bear", "--append", "--output", str(out), "--", "make", "-k", *targets],
                                      folder)
    return configured + steps, _recorded(out, "make", code, output)


def autotools(runner, unit: dict, build: Path, jobs: int) -> tuple[list[dict], dict]:
    """An Autotools build: `autoreconf -fi` writes the configure script a checkout lacks, in the unit's folder; the
    configure runs in a build folder of its own (a VPATH build: the copy's own Makefile, if any, stays the
    project's), with its defaults; make runs there under Bear, going on past an error."""
    source = WORK / unit.get("root", ".")
    steps = []
    for name, command, cwd in (("autoreconf", ["autoreconf", "-fi"], source),
                               ("configure", [str(source / "configure")], build)):
        build.mkdir(parents=True, exist_ok=True)
        code, output, seconds = runner(command, cwd)
        steps.append(_step(name, code, output, seconds))
        if code != 0:
            return steps, _ended(name, code, output)
    out = build / "compile_commands.json"
    made, code, output = _under_bear(runner, "make under Bear", ["bear", "--output", str(out), "--", "make", "-k",
                                                                  f"-j{jobs}"],
                                     ["bear", "--append", "--output", str(out), "--", "make", "-k", f"-j{jobs}"],
                                     build)
    return steps + made, _recorded(out, "make", code, output)


def go(runner, go_path: str, unit: dict, build: Path, prepared: dict | None) -> tuple[list[dict], dict]:
    """The cgo packages built by the go command under Bear's compiler wrappers (the go command starts the C
    compiler without the C library's exec, which Bear's preload intercepts), with the modules the preparation
    downloaded (`prepared`, its step) and no network. Only the commands for files of the copy are kept: the
    standard library's C files and the files cgo generates are not the project's."""
    if unit.get("download") and prepared is None:
        return [], {"state": "failed", "cause": "the preparation recorded no go mod download: its output is in the "
                                               "run's prepare.log"}
    if unit.get("download") and prepared["returncode"] != 0:
        return [prepared], _ended("go mod download", prepared["returncode"], prepared["tail"])
    build.mkdir(parents=True, exist_ok=True)
    out = build / "compile_commands.json"
    command = ["env", "CGO_ENABLED=1", "GOFLAGS=", f"GOPATH={GOPATH}", f"GOCACHE={SCRATCH / 'go-cache'}",
               "GOPROXY=off", "GOTOOLCHAIN=local", go_path, "build", "-work", *unit["packages"]]
    steps, code, output = _under_bear(runner, "go build under Bear",
                                      ["bear", "--force-wrapper", "--output", str(out), "--", *command],
                                      ["bear", "--force-wrapper", "--append", "--output", str(out), "--", *command],
                                      WORK / unit.get("root", "."))
    if out.is_file():
        entries = [entry for entry in json.loads(out.read_text(encoding="utf-8")) if WORK in _file(entry).parents]
        out.write_text(json.dumps(entries, indent=1) + "\n", encoding="utf-8")
    return [*([prepared] if prepared else []), *steps], _recorded(out, "go build", code, output)


def _compiles(arguments: list[str]) -> list[str]:
    """A compile action's arguments without the dependency file Bazel's gcc toolchain has it write (`-MD`, `-MF
    FILE` under a `bazel-out` nothing built, and gcc's `-fno-canonical-system-headers`, which clang rejects): what
    it compiles is the same."""
    out, skip = [], False
    for argument in arguments:
        if skip:
            skip = False
        elif argument == "-MF":
            skip = True
        elif argument not in DEPENDENCY_FILE:
            out.append(argument)
    return out


def aquery_database(actions: list[dict], workspace: Path) -> list[dict]:
    """Bazel's compile actions as commands run from the workspace's root, each its source the file after `-c`."""
    return [{"directory": str(workspace), "arguments": _compiles(action["arguments"]),
             "file": action["arguments"][action["arguments"].index("-c") + 1]}
            for action in actions if "-c" in (action.get("arguments") or [])[:-1]]


def bazel_prepare(runner, bazel_path: str, unit: dict, folder: Path) -> dict:
    """In the preparation: the compile actions of the workspace's own targets (`bazel aquery`, which fetches what
    their analysis reads) into `folder`, with the output base that holds the external repositories; its step."""
    folder.mkdir(parents=True, exist_ok=True)
    workspace = WORK / unit.get("root", ".")
    code, output, seconds = runner([bazel_path, "--max_idle_secs=5", "aquery", BAZEL_QUERY, "--output=jsonproto",
                                    "--include_artifacts=false", "--keep_going"], workspace,
                                   stdout=folder / "aquery.json")
    runner([bazel_path, "--max_idle_secs=5", "info", "output_base"], workspace, stdout=folder / "output_base")
    return _step("bazel aquery", code, output, seconds)


def bazel(unit: dict, build: Path, prepared: dict | None, folder: Path) -> tuple[list[dict], dict]:
    """The actions the preparation's aquery gave (`prepared`, its step; `folder`, its output), as commands run from
    the workspace's root, where `external` leads to the output base's external repositories, as in Bazel's
    execution root (hedron's extractor links it so). Exit code 3 is `--keep_going`'s: a package did not load."""
    if prepared is None:
        return [], {"state": "failed", "cause": "the preparation recorded no bazel aquery: its output is in the "
                                               "run's prepare.log"}
    try:
        actions = json.loads((folder / "aquery.json").read_text(encoding="utf-8") or "{}").get("actions", [])
    except (OSError, ValueError):
        actions = None
    if prepared["returncode"] not in (0, 3) or actions is None:
        return [prepared], _ended("bazel aquery", prepared["returncode"], prepared["tail"])
    workspace, base = WORK / unit.get("root", "."), (folder / "output_base").read_text(encoding="utf-8").strip()
    link = workspace / "external"
    if base and not (link.exists() or link.is_symlink()):
        link.symlink_to(Path(base) / "external")
    build.mkdir(parents=True, exist_ok=True)
    (build / "compile_commands.json").write_text(json.dumps(aquery_database(actions, workspace), indent=1) + "\n",
                                                 encoding="utf-8")
    code = prepared["returncode"]
    return [prepared], {"state": "configured",
                        **({"cause": f"bazel aquery ended with exit code {code}"} if code else {})}


def go_tool() -> str:
    """The Go the preparation installed with mise, else the pin, unpacked once."""
    for path in (T / "bin/go", T / "go/bin/go"):
        if path.is_file():
            return str(path)
    T.mkdir(parents=True, exist_ok=True)
    run(["tar", "-xzf", str(TOOLS / "go.tar.gz"), "-C", str(T)], T)
    return str(T / "go/bin/go")


def bazel_tool() -> str:
    """The Bazel the preparation installed with mise, at the version the project states, else the pin."""
    if (T / "bin/bazel").is_file():
        return str(T / "bin/bazel")
    T.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TOOLS / "bazel", T / "bazel")
    (T / "bazel").chmod(0o755)
    return str(T / "bazel")


def meson_tools() -> dict[str, str]:
    """Meson and its Ninja, unpacked from the wheels the copy carries: the environment Meson runs with."""
    zipfile.ZipFile(TOOLS / "meson.whl").extractall(SCRATCH / "meson")
    with zipfile.ZipFile(TOOLS / "ninja.whl") as wheel:
        (SCRATCH / "ninja").write_bytes(wheel.read(next(name for name in wheel.namelist()
                                                        if name.endswith("/scripts/ninja"))))
    (SCRATCH / "ninja").chmod(0o755)
    return {"PYTHONPATH": str(SCRATCH / "meson"), "NINJA": str(SCRATCH / "ninja")}


def install_bear(runner) -> dict:
    """Bear, from the Ubuntu packages the copy carries (`indexers/clang.py`, BEAR): its step."""
    code, output, seconds = runner(["sh", "-c", f"dpkg -i {TOOLS}/bear/*.deb"], SCRATCH)
    return _step("install Bear", code, output, seconds)


def _prepared(number: int) -> dict | None:
    """The step the preparation recorded for unit `number`, if it ran one."""
    try:
        return json.loads((PREPARED / str(number) / "step.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def prepare(units: list[dict], given: str | None = None) -> int:
    """The preparation's part, through the proxy: what each unit's build downloads (Bazel's aquery, Go's modules),
    its step in `PREPARED/<n>/step.json`, and the configure of a `fetch` unit, FetchContent downloading into
    `PREPARED/<n>/deps` with the CMake `given` (else the pin), its steps and state in `PREPARED/<n>/configure.json`:
    for the execution, which has no network."""
    cmake = None
    for number, unit in enumerate(units):
        folder = PREPARED / str(number)
        if unit.get("fetch"):
            cmake = cmake or cmake_ready(given)
            folder.mkdir(parents=True, exist_ok=True)
            steps, state = configure(run, cmake, unit, folder / "build", folder / "fetch.log", folder / "deps")
            (folder / "configure.json").write_text(json.dumps({"steps": steps, "state": state}) + "\n",
                                                   encoding="utf-8")
            continue
        if unit.get("build") == "bazel":
            step = bazel_prepare(run, bazel_tool(), unit, folder)
        elif unit.get("build") == "go" and unit.get("download"):
            folder.mkdir(parents=True, exist_ok=True)
            code, output, seconds = run(["env", f"GOPATH={GOPATH}", "GOFLAGS=-mod=mod", "GOTOOLCHAIN=local",
                                         go_tool(), "mod", "download"], WORK / unit.get("root", "."))
            step = _step("go mod download", code, output, seconds)
        else:
            continue
        (folder / "step.json").write_text(json.dumps(step) + "\n", encoding="utf-8")
    return 0


def main(argv: list[str]) -> int:
    if argv[1] == "prepare":
        return prepare(json.loads(Path(argv[2]).read_text(encoding="utf-8")), argv[3] if len(argv) > 3 else None)
    units, out, jobs = json.loads(Path(argv[1]).read_text(encoding="utf-8")), Path(argv[2]), int(argv[3])
    shutil.rmtree(SCRATCH, ignore_errors=True)
    SCRATCH.mkdir(parents=True)
    out.mkdir(parents=True, exist_ok=True)  # once the scratch folder is emptied: OUT_DIR may lie in it
    builds = {unit.get("build", "cmake") for unit in units}
    cmake = cmake_ready(argv[4] if len(argv) > 4 else None) if "cmake" in builds else "cmake"
    meson_env = meson_tools() if "meson" in builds else {}
    scip_clang = SCRATCH / "scip-clang"
    shutil.copyfile(TOOLS / "scip-clang", scip_clang)
    scip_clang.chmod(0o755)
    headers, version = unpack_headers()
    packages = SCRATCH / "package-map.json"
    packages.write_text(json.dumps([*package_map("project@0"), {"path": str(headers), "package": f"clang@{version}"}],
                                   indent=1) + "\n", encoding="utf-8")
    results, installed = [], None  # Bear's install, once, before the first build that runs under it
    for number, unit in enumerate(units):
        build, kind, steps = SCRATCH / f"build-{number}", unit.get("build", "cmake"), []
        if kind in BEAR_BUILDS and installed is None:
            installed = install_bear(run)
            steps.append(installed)
        if kind in BEAR_BUILDS and installed["returncode"] != 0:
            state = _ended("install Bear", installed["returncode"], installed["tail"])
        else:
            done, state = (downloaded(number, build) if kind == "cmake" and unit.get("fetch")
                           else configure(run, cmake, unit, build, SCRATCH / f"fetch-{number}.log") if kind == "cmake"
                           else meson(run, unit, build, meson_env) if kind == "meson"
                           else make(run, unit, build, jobs) if kind == "make"
                           else autotools(run, unit, build, jobs) if kind == "autotools"
                           else bazel(unit, build, _prepared(number), PREPARED / str(number)) if kind == "bazel"
                           else go(run, go_tool(), unit, build, _prepared(number)))
            steps += done
        record = {"root": unit.get("root", "."), "build": kind, **state, "steps": steps, "compiled": {},
                  "index": None}
        compdb = build / "compile_commands.json"
        if state["state"] == "configured" and not compdb.is_file():
            record.update(state="failed", cause=f"no compilation database: {WHAT[kind]} wrote no "
                                                "compile_commands.json")
        elif state["state"] == "configured" and not compiled(compdb):
            record.update(state="failed", cause=f"{WHAT[kind]} gave no compile command" + (
                f" ({state['cause']})" if state.get("cause") else ""))
        elif state["state"] == "configured":
            record["compiled"] = compiled(compdb)
            (WORK / "index.scip").unlink(missing_ok=True)
            given = SCRATCH / f"builtin-{number}.json"
            builtin_headers(run, compdb, given, headers)
            code, output, seconds = run(index_command(scip_clang, given, packages, jobs), WORK)
            steps.append({"step": "index", "returncode": code, "seconds": seconds, "tail": output[-2500:],
                          "diagnostics": _diagnostics(output)})
            if (WORK / "index.scip").is_file():
                record.update(state="indexed", index=f"index-{number}.scip")
                shutil.move(str(WORK / "index.scip"), str(out / record["index"]))
            else:
                record.update(state="failed", cause="scip-clang wrote no index")
        results.append(record)
    (out / "result.json").write_text(json.dumps({"units": results, "peak_mb": _peak()}, indent=1) + "\n",
                                     encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
