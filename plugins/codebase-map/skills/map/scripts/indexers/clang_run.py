"""The part of the C and C++ index that runs in the container, with no network: each unit configured with CMake,
then scip-clang over its compilation database. Standard library only: the image's python3 runs it.

    python3 clang_run.py UNITS_JSON OUT_DIR

A unit is `{"root", "configure": [...], "generated": [...], "fetched": [{"name", "url"}]}`, as the pre-map
states it. A dependency the project fetches is never downloaded: CMake runs with FETCHCONTENT_FULLY_DISCONNECTED
and each fetched dependency's source directory on an empty one. A unit whose configure then fails is not indexed:
`unavailable` when it fetches something (the dependency lies outside the allowed registries), else `failed`, with
CMake's own output, unparsed, either way.

`OUT_DIR/result.json` holds, per unit, its state, its steps (`returncode`, `seconds`, the output's tail), the
files of the compilation database with how many commands compile each, and the index it wrote
(`index-<n>.scip`), with the container's memory peak.
"""
from __future__ import annotations

import collections
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path("/daodan/tools")  # where the copy carries CMake and scip-clang (indexers/clang.py, TOOLS)
WORK = Path("/work")  # the project's copy
SCRATCH = Path("/tmp/daodan-clang")
OUTSIDE = "download-outside-registries"  # the cause the map-driven round counts
ERROR_TAIL = 4000


def run(command: list[str], cwd: Path, timeout: float = 3600) -> tuple[int | None, str, float]:
    """`(returncode, output, seconds)`; None as returncode on a timeout."""
    started = time.monotonic()
    try:
        done = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        code, output = done.returncode, done.stdout.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired as error:
        code, output = None, (error.stdout or b"").decode("utf-8", errors="replace")
    return code, output, round(time.monotonic() - started, 1)


def configure_command(cmake: str, unit: dict, build: Path, empty: Path) -> list[str]:
    command = [cmake, "-S", str(WORK / unit.get("root", ".")), "-B", str(build),
               "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DFETCHCONTENT_FULLY_DISCONNECTED=ON"]
    for item in unit.get("fetched", ()):
        command.append(f"-DFETCHCONTENT_SOURCE_DIR_{item['name'].upper()}={empty / item['name']}")
    return command + list(unit.get("configure", ()))


def _host(url: str) -> str:
    match = re.match(r"(?:[a-z+]+://)?(?:[^@/]+@)?([^/:]+)", url)
    return match.group(1) if match else url


def second_attempt(unit: dict, output: str) -> list[str] | None:
    """The arguments a second configure would add after a failed one, or None for no second attempt: always None
    until the map-driven round measures how many units would need one."""
    return None


def configure(runner, cmake: str, unit: dict, build: Path, empty: Path) -> tuple[list[dict], dict]:
    """One unit's configure steps and its state: `configured`, else `unavailable` or `failed` with the cause and
    CMake's output (`error`), as CMake wrote it."""
    for item in unit.get("fetched", ()):
        (empty / item["name"]).mkdir(parents=True, exist_ok=True)
        (empty / item["name"] / "CMakeLists.txt").write_text(f"# Not downloaded by Daodan: {item['url']}\n",
                                                            encoding="utf-8")
    command = configure_command(cmake, unit, build, empty)
    code, output, seconds = runner(command, WORK)
    steps = [{"step": "configure", "returncode": code, "seconds": seconds, "tail": output[-2500:]}]
    again = second_attempt(unit, output) if code != 0 else None
    if again is not None:
        code, output, seconds = runner(command + again, WORK)
        steps.append({"step": "configure again", "returncode": code, "seconds": seconds, "tail": output[-2500:]})
    if code == 0:
        return steps, {"state": "configured"}
    error = output[-ERROR_TAIL:]
    fetched = unit.get("fetched") or ()
    if not fetched:
        return steps, {"state": "failed", "error": error, "cause": "the configure timed out" if code is None
                       else f"the configure ended with exit code {code}"}
    hosts = ", ".join(sorted({_host(item["url"]) for item in fetched}))
    return steps, {"state": "unavailable", "kind": OUTSIDE, "urls": [item["url"] for item in fetched], "error": error,
                   "cause": f"the configure needs what the unit downloads from {hosts}, outside the allowed registries"}


def compiled(compdb: Path) -> dict[str, int]:
    """Checkout-relative files of a compilation database, with how many commands compile each."""
    out = collections.Counter()
    for entry in json.loads(compdb.read_text(encoding="utf-8")):
        path = Path(os.path.normpath(Path(entry["directory"], entry["file"])))
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


def main(argv: list[str]) -> int:
    units, out = json.loads(Path(argv[1]).read_text(encoding="utf-8")), Path(argv[2])
    out.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(SCRATCH, ignore_errors=True)
    SCRATCH.mkdir(parents=True)
    run(["tar", "-xzf", str(TOOLS / "cmake.tar.gz"), "-C", str(SCRATCH)], SCRATCH)
    cmake = str(next(SCRATCH.glob("cmake-*/bin/cmake"), Path("cmake")))
    scip_clang = SCRATCH / "scip-clang"
    shutil.copyfile(TOOLS / "scip-clang", scip_clang)
    scip_clang.chmod(0o755)
    packages = SCRATCH / "package-map.json"
    packages.write_text(json.dumps(package_map("project@0"), indent=1) + "\n", encoding="utf-8")
    results = []
    for number, unit in enumerate(units):
        build = SCRATCH / f"build-{number}"
        steps, state = configure(run, cmake, unit, build, SCRATCH / f"empty-{number}")
        record = {"root": unit.get("root", "."), **state, "steps": steps, "compiled": {}, "index": None}
        compdb = build / "compile_commands.json"
        if state["state"] == "configured" and compdb.is_file():
            for target in unit.get("generated", ()):
                code, output, seconds = run([cmake, "--build", str(build), "--target", target], WORK)
                steps.append({"step": f"build {target}", "returncode": code, "seconds": seconds,
                              "tail": output[-2500:]})
            record["compiled"] = compiled(compdb)
            (WORK / "index.scip").unlink(missing_ok=True)
            code, output, seconds = run([str(scip_clang), f"--compdb-path={compdb}", f"--package-map-path={packages}",
                                         f"--jobs={os.cpu_count() or 2}", "--show-compiler-diagnostics"], WORK)
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
