"""The Python observer: the project's tests under the exact recorder (`python_record.py`, sys.monitoring).

`plan` reads the pre-map alone. The command is the one the project declares (its `tests` entries, from
`premap/python_tests.py`): `python -m pytest` or `python -m unittest` with the arguments written, in the folder
stated, pytest with its own `KEEP_GOING` so a module that does not import stops no other; a project that
declares neither is a `no_test_command` gap, never a command of ours. A pytest entry
inside the folders another one is given is collected by that one, and makes no run. Each run uses the
environment of the Python folder that holds it (`preparation.restores`: the folder with the manifest, restored
by uv, Poetry or pip as its lockfile says), else the project's only one (a manifest inside the test folders is
a fixture's, not the tests'), else an empty one. The recorder needs
sys.monitoring, Python 3.12 or later: a project that states an older Python (a version, or a range that ends
below 3.12) is a `python_too_old` gap and its tests do not run. In a folder uv restores, uv picks the interpreter
as `uv sync` does (a version file, else requires-python; downloaded when none installed has it), and a run whose
request excludes the image's Python says it (`python_request`: a version file's, else the pyproject's) beside the
version it ran on; elsewhere an exact version the image does not hold is installed by the preparation (mise,
`preparation.toolchains`), and a range that excludes the image's Python and names no version is a
`python_unavailable` gap.

`observe` is one container run (`container.run_in_container`, `IMAGE`). The preparation, with the registries and
the hosts the project declares (the plan's `declared`, which `dynamic.run` adds): the toolchain, uv, where the
project declares VCS requirements git and the hosts their URLs name (`preparation.python_vcs`), the restore of
each environment (one whose install fails is installed again without
the VCS requirements, `vcs_not_installed`), the tests' dependencies their entry declares apart (`deps`, installed
by uv sync and uv pip, `_installs`; a line with a tox substitution or factor condition, or an install that fails,
is `test_dependencies_not_installed`), the project itself installed in it where the folder has a
build configuration (editable, without dependencies: the tests import it as installed), and pytest at Daodan's
pin (`PYTEST`) where the project declares it as its runner and its environment does not hold it, which is said
(`runner_brought`). The execution, with no network: each run under the recorder, loaded through a
`sitecustomize.py` on PYTHONPATH so it starts before any project code and in subprocesses, stopped by an
interrupt after `LIMIT` seconds so the recorder still writes what it saw. Back come the observation files, one
per process, and each run's log. What did not happen is a gap with its cause: tests that did not start (the
log's tail), that failed, that found no test, test modules pytest could not import (`tests_not_collected`, each
with its error's first line), that outlasted the limit, that reached for a service or the
network (the execution has no network, only the services the project's CI declares, which the step starts beside
it: `dynamic.services`), a project that could not be installed.
"""
from __future__ import annotations

import json
import posixpath
import re
import shlex
from pathlib import Path

import dynamic
import preparation
from dynamic import python_record
from indexers.python import IMAGE  # the image the Python analyzer runs in

# The observer this module is (`dynamic.observers`): its entry, its recorder's version, the languages it observes.
NAME, VERSION, LANGUAGES = "dynamic-record-python", python_record.VERSION, ("python",)
RECORDER = Path(python_record.__file__).resolve()
RUNNERS = ("pytest", "unittest")  # the runners of the pre-map's `tests` it starts, each as `python -m <runner>`
# pytest's own option: a module that does not import (an optional dependency, a service) stops no other one.
# unittest needs none: it loads each module apart, and a failed import is a test in error.
KEEP_GOING = "--continue-on-collection-errors"
PYTHON, PYTHON3 = (3, 13, 18), "/usr/local/bin/python3"  # IMAGE's: its version, and where it is
MONITORING = (3, 12)  # sys.monitoring, which the recorder is built on
VERIFIED = ((3, 12), (3, 13))  # the releases the recorder's placing of a `with` block's exit is verified on
NEWER = ((3, 12, 0), (3, 12, 99), (3, 13, 0), (3, 14, 0), (3, 15, 0), (3, 20, 0), (4, 0, 0))
PYTEST = "9.1.1"  # brought where the project declares pytest and its environment does not hold it
MEMORY = 3 * 2**30
LIMIT = 3600  # the seconds one run of the tests may take: the recorder costs 6 to 10 times the suite's time
OUT, SITE = "/daodan/out", "/daodan/site"
IN, VENVS = preparation.IN, preparation.VENVS
BARE = re.compile(r"^v?(\d+(?:\.\d+){0,2})(?:[-+][0-9A-Za-z.-]+)?$")  # a version alone, an image's tag included
CLAUSE = re.compile(r"\s*(~=|===?|!=|<=|>=|<|>|\^|~)?\s*v?(\d+(?:\.\d+)*)(?:\.\*)?\s*,?")
UNREACHABLE = re.compile(r"ConnectionRefusedError|Connection refused|Network is unreachable|"
                         r"Temporary failure in name resolution|Name or service not known")
MARK = re.compile(r"^DAODAN-DYNAMIC (\d+) (\S+) ?(.*)$", re.M)
COLLECTING = re.compile(r"^_+ ERROR collecting (.+?) _+$", re.M)  # pytest's header of a module it could not collect
SUMMARY = re.compile(r"^=*\s*((?:\d+ \w+, )*\d+ \w+) in [\d.]+s\b", re.M)  # pytest's last line: `1 failed, 2 passed`
RAN = ("passed", "failed", "xfailed", "xpassed")
# what the preparation could not install for a run: the project, or its tests' dependencies; then the install's tail
NOT_INSTALLED = re.compile(r"DAODAN-DYNAMIC (\d+) (not-installed|deps-failed)\n((?:.*\n)*?)DAODAN-DYNAMIC-END")
VERSION_FILES = (".python-version", ".python-versions")  # what uv reads before a pyproject's requires-python
TOX_ONLY = re.compile(r"\{|^[!\w,.-]+:\s")  # a tox substitution, or a factor's condition: Daodan evaluates neither


def external(callee: dict) -> dict:
    """The package of a callee outside the project, named as the static graph names Python's: the standard
    library and the builtins are `python-stdlib` at the interpreter's version, a distribution is itself, and
    code of neither is its top module, with no version."""
    if callee["kind"] == "runtime":
        return {"manager": "python", "package": "python-stdlib", "version": callee.get("version")}
    package = callee.get("package") or str(callee.get("module") or "").split(".")[0]
    return {"manager": "python", "package": package.lower().replace("_", "-"), "version": callee.get("version")}


def admits(stated: str, version: tuple) -> bool | None:
    """Whether a stated Python (a version, a range of PEP 440 or Poetry clauses) admits `version`; None when it
    is not written as versions and operators."""
    text = BARE.sub(r"\1", stated.strip())
    found, at = [], 0
    while at < len(text):
        clause = CLAUSE.match(text, at)
        if clause is None or clause.end() == at:
            return None
        found.append(clause.group(1, 2))
        at = clause.end()
    for operator, numbers in found:
        want = tuple(int(number) for number in numbers.split("."))
        whole, same = want + (0,) * (3 - len(want)), version[:len(want)] == want
        # the numbers a release keeps: all but the last for `~=`, the minor at most for Poetry's `~`, the major for `^`
        compatible, tilde = max(1, len(want) - 1), min(2, len(want))
        if not {None: same, "==": same, "===": same, "!=": not same, ">=": version >= whole, ">": version > whole,
                "<=": version <= whole, "<": version < whole,
                "~=": version >= whole and version[:compatible] == want[:compatible],
                "~": version >= whole and version[:tilde] == want[:tilde],
                "^": version >= whole and version[0] == want[0]}[operator]:
            return False
    return bool(found)


def _inside(folder: str, root: str) -> bool:
    return root == "." or folder == root or folder.startswith(root + "/")


def _above(folder: str, declared_in: str) -> bool:
    """Whether a file declares for `folder`: it lies in it or in a folder above it."""
    return _inside(folder, posixpath.dirname(declared_in.split("#", 1)[0]) or ".")


def _given(test: dict) -> list[str]:
    """The folders a pytest entry collects: the ones it is given, else the one it runs in."""
    return [posixpath.normpath(f"{test['root']}/{arg}") for arg in test.get("args", ())] or [test["root"]]


def _python(stated: list[dict], picked: bool = False) -> tuple[dict | None, dict | None]:
    """`(gap, toolchain)` of the Pythons a run's folders state: the gap that keeps the run from starting, else
    the exact version the preparation installs when the image's is not it. `picked`: uv picks the interpreter,
    and only a Python older than the recorder's is a gap."""
    install = None
    for item in stated:
        version, where = str(item["version"]), item.get("declared_in")
        bare = BARE.match(version.strip())
        admitted = admits(version, PYTHON)
        if bare:
            numbers = tuple(int(number) for number in bare.group(1).split("."))
            if numbers[:2] < MONITORING[:len(numbers[:2])]:
                admitted = False
            elif not admitted:
                install = install or {**item, "version": bare.group(1)}
                continue
        if admitted is not False:
            continue
        if bare or not any(admits(version, newer) for newer in NEWER):
            return {"kind": "python_too_old", "path": where,
                    "detail": f"the project states Python {version} ({where}): the recorder needs sys.monitoring, "
                              "Python 3.12 or later, and the tests are not run on a Python the project does not "
                              "state"}, None
        if not picked:
            return {"kind": "python_unavailable", "path": where,
                    "detail": f"the project states Python {version} ({where}): a range that excludes the image's "
                              f"{'.'.join(map(str, PYTHON))} and names no version to install"}, None
    return None, None if picked else install


def stated_python(stated: list[dict], env: str) -> dict | None:
    """The stated Python uv sync reads first in `env`, its folder: the nearest version file there or above, else
    the nearest requires-python. The Python analyzer reads the project on it too (`indexers.python`)."""
    def read(names, where=None):
        found = [item for item in stated if posixpath.basename(item["declared_in"].split("#", 1)[0]) in names
                 and (where is None or _above(where, item["declared_in"]))]
        return sorted(found, key=lambda item: -item["declared_in"].count("/"))
    item = next(iter(read(VERSION_FILES, env) or read(("pyproject.toml",))), None)
    return {"version": item["version"], "declared_in": item["declared_in"]} if item else None


def _request(stated: list[dict], env: str) -> dict | None:
    """`stated_python` when the image's Python is not one it admits."""
    item = stated_python(stated, env)
    return item if item and admits(str(item["version"]), PYTHON) is False else None


def plan(record: dict, files: list[str], read) -> dict:
    """`{runs, gaps, toolchains}` from the pre-map `record`, the snapshot's `files` and `read(rel)`, a file's
    text: see the module's docstring. A run is `{root, runner, declared_in, argv, env, manager, install}`:
    `argv` follows the environment's Python, `env` is the folder whose environment it uses (None: an empty
    one), `manager` what restores it, `install` whether the folder's project is installed in it; `deps` are the
    entry's, and `python_request` is said where uv picks the Python (`_request`)."""
    tests = sorted((test for test in record.get("tests", []) if test.get("runner") in RUNNERS),
                   key=lambda test: (test["root"], test["runner"]))
    if not tests:
        return {"runs": [], "toolchains": [], "gaps": [{
            "kind": "no_test_command",
            "detail": "no file of the project declares how its Python tests run (a pytest configuration, a "
                      "conftest.py, pytest among the declared dependencies, a `python -m unittest` line in tox.ini "
                      "or a makefile): nothing is observed"}]}
    # The snapshot keeps no lockfile: the ones the checkout holds beside a manifest name the folder's manager.
    files = [*files, *preparation.python_locks(files, read)]
    held = preparation.python_environments(files)
    files, runs, gaps, toolchains = set(files), [], [], []
    for test in tests:
        root = test["root"]
        # A folder inside what another pytest run is given is collected by that run: a fixture project, or a member.
        if test["runner"] == "pytest" and any(
                other is not test and other["runner"] == "pytest" and folder != root and _inside(root, folder)
                for other in tests for folder in _given(other)):
            continue
        # Outside every Python folder: the project's only one, the manifests inside the test folders apart.
        apart = [folder for folder in held if test["runner"] != "pytest"
                 or not any(_inside(folder, given) for given in _given(test))]
        env = preparation.python_environment(held, root)
        if env is None:
            env = apart[0] if len(apart) == 1 else None
        stated = [item for item in record.get("toolchains", []) if item.get("tool") == "python"
                  and item.get("version") and item.get("declared_in")
                  and (_above(root, item["declared_in"]) or (env is not None and _above(env, item["declared_in"])))]
        picked = held.get(env) == "uv"
        gap, install = _python(stated, picked)
        if gap:
            gaps.append(gap)
            continue
        if install and install not in toolchains:
            toolchains.append(install)
        request = _request(stated, env) if picked else None
        deps = test.get("deps")
        unexpanded = [line for line in (deps or {}).get("requirements", ()) if TOX_ONLY.search(line)]
        if unexpanded:
            gaps.append({"kind": "test_dependencies_not_installed", "path": deps["declared_in"],
                         "detail": f"{deps['declared_in']} declares {', '.join(unexpanded)} for the tests: a tox "
                                   "substitution or factor condition Daodan does not evaluate, so it is not "
                                   "installed"})
        manifest = posixpath.normpath(f"{env}/pyproject.toml") if env is not None else None
        packaged = env is not None and (posixpath.normpath(f"{env}/setup.py") in files or (
            manifest in files and "[build-system]" in read(manifest)))
        runs.append({"root": root, "runner": test["runner"], "declared_in": test.get("declared_in"),
                     "argv": ["-m", test["runner"], *(dynamic.arguments(test["argv"], test["runner"])
                                                       if test.get("argv") else test.get("args", ())), *(
                         [KEEP_GOING] if test["runner"] == "pytest" else [])],
                     "env": env, "manager": held.get(env), "install": bool(packaged),
                     **({"deps": deps} if deps else {}), **({"python_request": request} if request else {})})
    # an environment whose restore would install a local dependency outside the copy is not made: its runs do not run
    local = preparation.local_dependencies(sorted(files), read, "python")
    blocked = preparation.refused({run["env"] for run in runs if run["env"] is not None}, local)
    runs = [run for run in runs if run["env"] not in blocked]
    return {"runs": runs, "gaps": gaps + local, "toolchains": toolchains,
            "vcs": preparation.python_vcs(sorted(files), read)}


def _interpreter(number: int, run: dict) -> str:
    """The shell word of a run's Python: its environment's, as the shared restore makes it."""
    if run["env"] is None:
        return f"{VENVS}/.daodan-{number}/bin/python"
    return preparation.python_interpreter(run["env"], run["manager"], "/work")


def _installs(run: dict, python: str) -> list[tuple[str, str]]:
    """`(folder, command)` of what installs a run's `deps` in its environment. In a folder uv restores, its
    groups and extras are uv sync's, from the lock and the workspace; the rest is `uv pip install`'s, from the
    folder of the file that declares them, where its relative paths start: an option line split as a shell would,
    a requirement as written, the extras with the project, the groups by name. A line `TOX_ONLY` stays out."""
    deps, found = run.get("deps") or {}, []
    named = [word for key, flag in (("groups", "--group"), ("extras", "--extra")) for name in deps.get(key, ())
             for word in (flag, name)]
    if run["manager"] == "uv" and named:
        venv = shlex.quote(f"{VENVS}/{run['env']}")
        found.append((run["env"], f"UV_PROJECT_ENVIRONMENT={venv} uv sync -q --locked --inexact --all-packages"
                                  f" --no-install-project {shlex.join(named)}"))
        deps = {"requirements": deps.get("requirements", ())}
    words = [word for line in deps.get("requirements", ()) if not TOX_ONLY.search(line)
             for word in (shlex.split(line) if line.startswith("-") else [line])]
    words += ["-e", f".[{','.join(deps['extras'])}]"] if deps.get("extras") else []
    words += [word for group in deps.get("groups", ()) for word in ("--group", group)]
    if words:
        found.append((posixpath.dirname(run["deps"]["declared_in"].split("#", 1)[0]) or ".",
                      f"uv pip install -q --python {python} {shlex.join(words)}"))
    return found


def scripts(planned: dict) -> tuple[str, str, dict]:
    """The preparation's script, the execution's, and what the preparation needs beside them (`{files, hosts,
    gaps, tools}`: the downloads the copy carries, the hosts beside the registries, the toolchains no installer has,
    the recipes of `preparation.NEEDS` installed as root before the preparation, which then runs as
    `container.NOBODY`; None where git, which apt installs into the image, keeps the preparation one, as root)."""
    runs = planned["runs"]
    chains = preparation.toolchains(planned.get("toolchains") or [])
    restores: dict[str, list[str]] = {}
    for run in runs:
        if run["env"] is not None and run["env"] not in restores.setdefault(run["manager"], []):
            restores[run["manager"]].append(run["env"])
    vcs = planned.get("vcs") or {"names": [], "hosts": []}
    needs = preparation.setup({"uv", *(["git"] if vcs["names"] or vcs["hosts"] else []),
                               *(need for manager in restores
                                 for need in preparation.RESTORES[manager].get("needs", ()))})
    apart = not vcs["names"] and not vcs["hosts"]  # no git (`preparation.IMAGE_NEEDS`)
    prepare = ["set -u", f"mkdir -p {preparation.T}/bin {preparation.ENV['HOME']} {VENVS}", *chains["lines"],
               *([] if apart else needs["lines"]), preparation.UV_ENV, *([preparation.without(vcs["names"])] if vcs["names"] else []),
               *(preparation.restore(manager, folders) for manager, folders in restores.items())]
    execute = ["set -u", f"mkdir -p {OUT}", f"{PYTHON3} {IN}/{RECORDER.name} site {SITE} || exit 70",
               # $1 the run, $2 its folder, $3 its Python, then the runner's arguments
               "run() {", "  n=$1; folder=$2; py=$3; shift 3",
               '  [ -x "$py" ] || { echo "DAODAN-DYNAMIC $n no-python"; return; }',
               "  echo \"DAODAN-DYNAMIC $n python $(\"$py\" -c 'import sys; print(\"%d.%d.%d\" % "
               "sys.version_info[:3], int(hasattr(sys, \"monitoring\")))')\"",
               "  \"$py\" -c 'import sys; sys.exit(not hasattr(sys, \"monitoring\"))' || return",
               "  start=$(date +%s)",
               f'  ( cd "/work/$folder" && exec env PYTHONPATH={SITE} DYN_ROOT=/work DYN_OUT={OUT}/observed-$n-%p.json'
               f' timeout -s INT -k 30 {LIMIT} "$py" "$@" ) > {OUT}/tests-$n.log 2>&1',
               '  echo "DAODAN-DYNAMIC $n exit $? $(( $(date +%s) - start ))"', "}"]
    for number, run in enumerate(runs):
        python = _interpreter(number, run)
        if run["env"] is None:
            prepare.append(f"uv venv -q --python python3 {VENVS}/.daodan-{number} >&2")
        for folder, command in _installs(run, python):
            prepare.append(f"( cd {shlex.quote('/work/' + folder)} && {command} ) > /tmp/daodan-deps.log 2>&1 || {{"
                           f" echo 'DAODAN-DYNAMIC {number} deps-failed'; tail -n 8 /tmp/daodan-deps.log;"
                           " echo DAODAN-DYNAMIC-END; } >&2")
        if run["install"]:  # project code (its build backend): the preparation's, with the registries only
            prepare.append(f"uv pip install -q --python {python} --no-deps -e {shlex.quote('/work/' + run['env'])}"
                           f" > /tmp/daodan-install.log 2>&1 || {{ echo 'DAODAN-DYNAMIC {number} not-installed';"
                           " tail -n 8 /tmp/daodan-install.log; echo DAODAN-DYNAMIC-END; } >&2")
        if run["runner"] == "pytest":
            prepare.append(f"{python} -c 'import pytest' 2>/dev/null || {{ uv pip install -q --python {python}"
                           f" pytest=={PYTEST} >&2 && echo 'DAODAN-DYNAMIC {number} brought pytest {PYTEST}' >&2; }}")
        execute.append(f"run {number} {shlex.quote(run['root'])} {python} {shlex.join(run['argv'])}")
    declared = (planned.get("declared") or {}).get("hosts", ())
    return ("\n".join([*prepare, "exit 0"]) + "\n", "\n".join([*execute, "exit 0"]) + "\n",
            {"files": [*chains["files"], *needs["files"]], "gaps": chains["gaps"],
             "tools": {"lines": needs["lines"], "caps": needs["caps"]} if apart else None,
             "hosts": (*chains["hosts"], *needs["hosts"], *vcs["hosts"], *declared,
                       *(host for manager in restores for host in preparation.RESTORES[manager]["hosts"]))})


def sites(folder: Path, run: int | None = None) -> list[dict]:
    """The sites of the observation files in `folder` (one per process, `observed-<run>-<pid>.json`; of one run
    or of all), each site once with every callee a process saw there."""
    merged: dict = {}
    for path in sorted(Path(folder).glob(f"observed-{'*' if run is None else run}-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue  # a process killed while it wrote: its file is no observation
        for site in data.get("sites") or ():
            key = (site["file"], site["line"], site["column"], site["name"], site["role"])
            entry = merged.setdefault(key, {**site, "callees": {}})
            entry["callees"].update({json.dumps(callee, sort_keys=True): callee for callee in site["callees"]})
    return [{**entry, "callees": list(entry["callees"].values())} for _key, entry in sorted(merged.items())]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _uncollected(log: str) -> list[dict]:
    """The test modules pytest could not collect, as it names them, each with its error's first line."""
    headers = list(COLLECTING.finditer(log))
    found = []
    for number, header in enumerate(headers):
        block = log[header.end():headers[number + 1].start() if number + 1 < len(headers) else len(log)]
        error = next((line[1:].strip() for line in block.splitlines() if line.startswith("E ")), "")
        found.append({"file": header.group(1), "error": error[:200]})
    return found


def _outcome(run: dict, marks: dict, log: str, processes: int, ended: str) -> tuple[dict, list[dict]]:
    """One run's entry and its gaps, from the marks its script printed and its tests' log. The runner's exit code
    says how the tests ended (pytest's: 1 some failed or a module could not be collected, 5 none found, any other
    the run did not start; `timeout`'s 124); a runner the environment does not hold never started them. The
    modules pytest could not collect are one gap; with no other test run, the tests did not start."""
    entry = {key: run[key] for key in ("root", "runner", "declared_in", "python_request") if key in run}
    version, _, monitored = marks.get("python", "").partition(" ")
    code, _, seconds = marks.get("exit", "").partition(" ")
    entry.update(state="not_started", exit_code=int(code) if code else None,
                 seconds=int(seconds) if seconds.isdigit() else None, python=version or None, processes=processes)
    tail = " | ".join(line.strip() for line in log.strip().splitlines()[-8:])[-600:]

    def gap(kind: str, detail: str) -> dict:
        return {"kind": kind, "path": run["root"], "detail": detail}

    command = f"python {' '.join(run['argv'])} in {run['root']}"
    if "no-python" in marks:
        return entry, [gap("tests_not_started", f"{command}: no Python environment to run it in (its restore "
                                                "failed, or the manager made none)")]
    if monitored == "0":
        return entry, [gap("python_too_old", f"{command}: its environment's Python is {version}, and the "
                                             "recorder needs sys.monitoring, Python 3.12 or later")]
    if not code:
        return entry, [gap("tests_not_started", f"{command}: the run ended before the tests' exit ({ended})")]
    gaps = []
    stop = dynamic.stopped(entry["exit_code"], entry["seconds"], LIMIT)
    if stop == "timeout":
        entry["state"] = "timeout"
        gaps.append(gap("tests_timeout", f"{command} did not end in {LIMIT} s: what ran until then is observed"))
    elif stop == "killed":
        entry["state"] = "killed"
        gaps.append(gap("tests_killed", f"{command} was killed after {entry['seconds']} s, as a process is when the "
                                        f"container's memory limit ({MEMORY // 2**30} GB) is reached: {tail}"))
    elif entry["exit_code"] == 5:
        entry["state"] = "no_tests"
        gaps.append(gap("no_tests", f"{command} found no test to run: {tail}"))
    elif entry["exit_code"] == 0 or (entry["exit_code"] == 1 and f"No module named {run['runner']}" not in log):
        entry["state"] = "ran"
        uncollected = _uncollected(log) if run["runner"] == "pytest" else []
        summary = SUMMARY.findall(log)
        counts = {{"errors": "error"}.get(name, name): int(count)
                  for count, name in re.findall(r"(\d+) (\w+)", summary[-1] if summary else "")}
        beyond = counts.get("failed") or counts.get("error", 0) > len(uncollected)  # more than the modules' errors
        if entry["exit_code"] and (not uncollected or beyond):
            gaps.append(gap("tests_failed", f"{command}: some tests failed, and a test that fails may stop before "
                                            f"its calls: {tail}"))
        if uncollected:
            if counts and not any(counts.get(name) for name in RAN):
                entry["state"] = "not_started"
            said = "; ".join(f"{item['file']} ({item['error']})" for item in uncollected[:5])
            gaps.append({**gap("tests_not_collected",
                               f"{command}: {len(uncollected)} test modules could not be imported, so their tests did "
                               f"not run{'' if entry['state'] == 'ran' else ', nor did any other'}: {said}"),
                         "count": len(uncollected), "modules": uncollected[:60]})
    else:
        gaps.append(gap("tests_not_started", f"{command} exited with code {code}: {tail}"))
    refused = sum(1 for line in log.splitlines() if UNREACHABLE.search(line))
    if refused:
        gaps.append(gap("services_unreachable",
                        f"{command}: {refused} lines of its log report a refused connection or an unreachable "
                        "network: the tests run with no network, beside only the services the project's CI "
                        "declares"))
    if version and tuple(int(number) for number in version.split(".")[:2]) not in VERIFIED:
        gaps.append(gap("recorder_unverified",
                        f"{command} ran on Python {version}: the recorder is verified on CPython 3.12 and 3.13, and "
                        "may misplace a with block's exit on another"))
    return entry, gaps


def observe(project: Path, planned: dict, out_dir: Path, engine=None) -> dict:
    """The planned runs in one container run over a copy of `project`, read back from `out_dir`:
    `{state, sites, runs, gaps}`, `state` `ran`, `gap` (no container: `cause`, `remedy`) or `failed` (the
    preparation or the engine failed: `cause`, `remedy`, and nothing of the run is kept)."""
    import shutil
    import container
    out_dir = Path(out_dir)
    shutil.rmtree(out_dir / Path(OUT).name, ignore_errors=True)  # a former run's outputs are not this one's
    for phase in ("prepare", "execute"):
        (out_dir / f"{phase}.log").unlink(missing_ok=True)
    prepare, execute, needs = scripts(planned)
    runs = planned["runs"]

    def inputs() -> dict:
        return {f"{IN}/{RECORDER.name}": RECORDER,
                **{f"{IN}/{name}": preparation.fetched(url, digest, name) for url, digest, name in needs["files"]}}

    result = container.run_in_container(
        project, ["sh", "-c", execute], image=IMAGE, out_dir=out_dir, prepare=["sh", "-c", prepare], outputs=[OUT],
        env={**preparation.ENV, "LANG": "C.UTF-8"}, timeout=len(runs) * (LIMIT + 120), memory=MEMORY,
        registries=container.REGISTRIES + tuple(dict.fromkeys(needs["hosts"])), engine=engine, inputs=inputs,
        tools=needs["tools"])
    if result["state"] == "gap":
        return {"state": "gap", "cause": result["cause"], "remedy": result["remedy"], "sites": [], "runs": [],
                "gaps": []}
    prepared = _text(out_dir / "prepare.log")
    gaps = [*needs["gaps"], *preparation.missing(prepared), *preparation.restore_gaps(prepared),
            *(result.get("gaps") or ())]  # and what the copy left out (`container.copy_perimeter`)
    if result["state"] == "failed":
        return {"state": "failed", "cause": result.get("cause") or "the container run failed",
                "remedy": f"see prepare.log and execute.log in {out_dir}", "sites": [], "runs": [], "gaps": gaps}
    for number, what, lines in NOT_INSTALLED.findall(prepared):
        said = " | ".join(line.strip() for line in lines.splitlines() if line.strip())[:600]
        run = runs[int(number)]
        if what == "deps-failed":
            deps = run["deps"]
            named = [*deps.get("requirements", ()), *(f"group {name}" for name in deps.get("groups", ())),
                     *(f"extra {name}" for name in deps.get("extras", ()))]
            gaps.append({"kind": "test_dependencies_not_installed", "path": deps["declared_in"],
                         "detail": f"the tests' dependencies {deps['declared_in']} declares ({', '.join(named)}) "
                                   f"could not be installed: {said}"})
            continue
        gaps.append({"kind": "project_not_installed", "path": run["env"],
                     "detail": "the project could not be installed in its environment, so tests that import it as "
                               f"installed fail: {said}"})
    marks: dict[int, dict] = {}
    for number, mark, rest in MARK.findall(prepared + "\n" + _text(out_dir / "execute.log")):
        marks.setdefault(int(number), {})[mark] = rest.strip()
    back, entries = out_dir / Path(OUT).name, []
    for number, run in enumerate(runs):
        found = marks.get(number, {})
        if "brought" in found:
            gaps.append({"kind": "runner_brought", "path": run["root"],
                         "detail": f"{run['declared_in']} declares pytest and the restored environment does not hold "
                                   f"it: Daodan's {found['brought']} ran the tests"})
        entry, own = _outcome(run, found, _text(back / f"tests-{number}.log"),
                              len(list(back.glob(f"observed-{number}-*.json"))), result["state"])
        entries.append(entry)
        gaps += own
    return {"state": "ran", "sites": sites(back), "runs": entries, "gaps": gaps}
