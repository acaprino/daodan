"""The test suites on Modal: pytest in a Linux container over the working tree, nothing on this PC.

    python tests/modal_pytest.py tests/test_codebase_map_premap.py -q -k toolchains
    python tests/modal_pytest.py --shards 32 -q -n 2     # every suite under tests/, in 32 containers at once

Behind a proxy (a cloud session): `pip install 'modal[api-proxy-support]'`, and `modal run tests/modal_pytest.py --args "<tests> -q"`
instead of the launcher, which drops the proxy variables of the shell.

The launcher starts `modal run` on this file with the arguments as given; the container holds the checkout as it
is on disk (daodan, plugins, tests, benchmarks, docs), runs `python -B -m pytest -p no:cacheprovider` in
it, streams the output and ends with pytest's exit code. Several suites at once: `-n 8`, one per core (pytest-xdist is there).

`--shards N` (taken out of the arguments before pytest) is for the whole suite: pytest-split cuts the tests into N groups
of about the same time, by the seconds in `tests/.test_durations` (a test with none gets the average one), each group
runs in a container of its own (`SHARD_CPU` cores, `-n` workers inside), all at once; the launcher prints the groups'
outputs in order, one line with the counts of all and the real time, and ends with the worst exit code (5, a group with
no test to run, is not one). `--store-durations` refreshes that file from the run (a passing one only; `--clean-durations`
drops the tests that are gone): do it after the suite has changed much, and commit the file. One group again, alone:
`-q -n 2 --splits 32 --group 14 --splitting-algorithm least_duration`.

# measured: the whole suite, 23 November 2026, seconds from the start to the end of the run (3919-3920 passed, 75 skipped,
# 1202 subtests, no failure unless said). No shards: 8 cores, -n 8: 604 (the owner's), 506 (mine, pytest's own time);
# 32 cores, -n 32: 618 (the owner's).
#   --shards 4, 8 cores, -n 8: 155      --shards 8, 8 cores, -n 8: 122, 141
#   --shards 16, 4 cores, -n 4: 107, 149; 8 cores, -n 8: 106
#   --shards 32, 2 cores, -n 2: 111, 85, 93 (one failed test, see below);
#                4 cores, -n 2: 90, 106, 112, 117 (storing the durations of this setting), 87, 108, 99 (one failed test)
#                4 cores, no -n: 116, 116
#   --shards 64, 1 core, no -n: 98
# `test_playwright_keeps_control_event_and_state_after_the_page_closes` (a real browser) failed in two of the 10 runs with
# -n 2, never alone (3) or in the 3 runs without -n, and passed when its group ran again: if it bothers, leave `-n 2` out.
# Two tests are the floor, each alone in a group: `test_on_modal_eshop_s_tests_are_five_test_projects_and_the_rest_needs_a_container_engine`
# (81-106 s) and `test_on_modal_tududi_s_jest_scripts_run` (73-93 s), both a clone, a snapshot and a pre-map of a real project.
# The slowest group of a 32 run was eshop's (94 s of pytest), then tududi's (85 s), then 69 s: more groups do not pay.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
REMOTE = "/repo"  # a container path: a POSIX string, whatever runs the client
PROXIES = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")

if __name__ == "__main__":  # the launcher: Modal's client does not go through a proxy of this shell
    environment = {key: value for key, value in os.environ.items() if key not in PROXIES}
    environment.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    raise SystemExit(subprocess.run(["modal", "run", str(Path(__file__).resolve()), "--args",
                                     shlex.join(sys.argv[1:])], env=environment, cwd=REPO).returncode)

import modal  # noqa: E402

LOCAL = (REPO / "AGENTS.md").is_file()
# Daodan's Node (`preparation.NODE`, checked by its sha256) runs `indexers/components.cjs` in its own tests
# (test_codebase_map_components.py), over the packages its recorded outputs were made with, in /opt/components.
NODE = ("https://nodejs.org/dist/v24.22.3/node-v24.22.3-linux-x64.tar.gz",
        "061ec3e3062115705b56b51fa9cc330ab50d34b6969387d4e4b1a50c6809acc2")
FETCH_NODE = ("python -c \"import hashlib, urllib.request; data = urllib.request.urlopen('%s').read(); "
              "assert hashlib.sha256(data).hexdigest() == '%s'; open('/tmp/node.tar.gz', 'wb').write(data)\"" % NODE)
COMPONENTS = ("vue@3.5.22", "typescript@5.6.3", "@vue/language-core@3.3.14", "svelte2tsx@0.7.63")
# Vue's tool 2.x (js-vue-pnpm's 2.2.12) with the indexer, in /opt/components-vue2, where its recording is made again.
COMPONENTS_VUE2 = ("vue@3.5.22", "typescript@5.6.3", "@vue/language-core@2.2.12", "@sourcegraph/scip-typescript@0.6.2")
# The @babel/core the JavaScript recorder prints with, as the observer installs it (`dynamic/javascript.py`: its
# BABEL, from npm without install scripts), in a layer of its own: the recorder's tests under a real Node
# (test_codebase_map_dynamic_javascript.py) find it through DAODAN_TEST_BABEL.
OBSERVER = REPO / "daodan/core/dynamic/javascript.py"
BABEL = (re.search(r'^BABEL = "([^"]+)"', OBSERVER.read_text(encoding="utf-8"), re.M)[1] if LOCAL else "",
         "/opt/babel/node_modules/@babel/core")
# Secretlint's own executable (`secret_mask.ASSETS`, checked by its sha256): the test that starts the real tool on a
# trap project (test_codebase_map_host_programs.py) finds it through DAODAN_SECRETLINT.
SECRETLINT = ("https://github.com/secretlint/secretlint/releases/download/v14.0.1/secretlint-14.0.1-linux-x64",
              "4fe869e7fe3d1bb3bf24003bea6b556d3a6d5343c393ca85301cae70c935fa98", "/opt/secretlint")
FETCH_SECRETLINT = ("python -c \"import hashlib, urllib.request; data = urllib.request.urlopen('%s').read(); "
                    "assert hashlib.sha256(data).hexdigest() == '%s'; open('%s', 'wb').write(data)\"" % SECRETLINT)
# The stack-analyser release (`daodan/core/stack_analyser.py`: its URL and SHA256, repeated here because this launcher
# does not import daodan/core; tests/test_codebase_map_stack_analyser.py compares them) in /opt/stack-analyser, the
# archive kept beside what it unpacks to: `real_stack` (conftest.py) and the naive starts of the proof on a trap project
# (test_codebase_map_host_programs.py) find it through DAODAN_STACK_ANALYSER, and the proof checks the archive's sha256
# again. The proof itself installs the release and Daodan's Node the product's way (`stack_analyser.cli` and `node`, into a
# folder of the test): the container needs github.com and nodejs.org when it runs: the image's Node is another one and its copy of the release
# serves the naive starts.
STACK_ANALYSER = ("https://github.com/acaprino/stack-analyser-daodan/releases/download/v1.27.6-daodan.5/"
                  "stack-analyser-daodan-1.27.6-daodan.5.tgz",
                  "e87658b2d630df6cb90de21070e86f91efdbe6a7b841dbeb3aab6add6332475c", "/opt/stack-analyser")
FETCH_STACK_ANALYSER = ("python -c \"import hashlib, urllib.request; data = urllib.request.urlopen('%s').read(); "
                        "assert hashlib.sha256(data).hexdigest() == '%s'; open('%s/release.tgz', 'wb').write(data)\""
                        % STACK_ANALYSER)
# Debian's headless JDK 17 builds and runs the JVM recorder in its own tests (test_codebase_map_dynamic_jvm.py);
# its package wants the manual folder the slim image leaves out.
image = (modal.Image.debian_slim(python_version="3.13")
         .run_commands("mkdir -p /usr/share/man/man1")
         .apt_install("git", "ca-certificates", "xz-utils", "openjdk-17-jdk-headless")
         .run_commands(FETCH_NODE, "tar -xzf /tmp/node.tar.gz -C /opt && rm /tmp/node.tar.gz",
                       "ln -s /opt/node-v24.22.3-linux-x64/bin/node /usr/local/bin/node",
                       "ln -s /opt/node-v24.22.3-linux-x64/bin/npm /usr/local/bin/npm",
                       "npm install --prefix /opt/components --no-audit --no-fund --ignore-scripts "
                       + " ".join(COMPONENTS))
         .run_commands(f"npm install --prefix /opt/babel --no-audit --no-fund --ignore-scripts @babel/core@{BABEL[0]}")
         # Playwright's client and its headless Chromium with the system libraries it needs (the exploration's own tests,
         # test_codebase_map_dynamic_explore.py): in the image, since several workers installing at once break apt
         .run_commands("npm install --prefix /opt/playwright --no-audit --no-fund --ignore-scripts playwright-core@1.64.1",
                       "node /opt/playwright/node_modules/playwright-core/cli.js install --with-deps --only-shell chromium")
         .run_commands("npm install --prefix /opt/components-vue2 --no-audit --no-fund --ignore-scripts "
                       + " ".join(COMPONENTS_VUE2))
         .pip_install("pytest", "pytest-xdist", "pytest-split==0.11.0", "uv==0.11.28", "tree-sitter==0.26.0",
                      "tree-sitter-language-pack==1.13.5",
                      "sqlglot>=30", "keyring>=25", "PyYAML>=6")
         .run_commands(FETCH_SECRETLINT, f"chmod +x {SECRETLINT[2]}")
         .run_commands(f"mkdir -p {STACK_ANALYSER[2]}", FETCH_STACK_ANALYSER,
                       f"tar -xzf {STACK_ANALYSER[2]}/release.tgz -C {STACK_ANALYSER[2]}"))
if LOCAL:
    # The results stay: suites replay the recorded answers kept there. The explorer's sources are no suite's.
    skipped = ["**/__pycache__/**", "**/node_modules/**", "**/.pytest_cache/**", "codebase-explorer/**",
               # private projects' reference maps and what was measured on them: out of git, and out of the container
               "system-map/expected/*-system.json", "system-map/results/system/**"]
    # The project-model fixtures go up as they are (mix-edge-vendored commits node_modules/ on purpose), in a
    # folder of their own: a "!" exception in `skipped` would stop Modal pruning the skipped folders.
    fixtures = "project-model/fixtures"
    for folder in ("daodan", "plugins", "tests", "benchmarks", "docs"):
        image = image.add_local_dir(REPO / folder, f"{REMOTE}/{folder}", ignore=[*skipped, fixtures])
    image = image.add_local_dir(REPO / "benchmarks" / fixtures, f"{REMOTE}/benchmarks/{fixtures}")
    for file in ("AGENTS.md", "pyproject.toml", "README.md", "LICENSE", "viewer/pipeline/data.ts"):
        image = image.add_local_file(REPO / file, f"{REMOTE}/{file}")
app = modal.App("daodan-tests", image=image)
DURATIONS = "tests/.test_durations"  # pytest-split's seconds per test id: in git, loaded by the image, refreshed by --store-durations
CAPTURE = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
SHARD_CPU = 4  # per container of a `--shards` run (a single run keeps the decorator's 8); measured: see the top
# One line of pytest's own summary: "3914 passed, 75 skipped, 1202 subtests passed in 618.78s (0:10:18)". A log line
# has no grammar, so a regular expression reads it; pytest's junit XML does not count subtests, which this line does.
SUMMARY = re.compile(r"(\d+) ([a-z][a-z ]*?)(?=,| in \d)")
SINGULAR = {"warnings": "warning", "errors": "error"}  # pytest writes "1 warning" and "2 warnings": one count


# A fresh container per call: a group that found its predecessor's `--store-durations` file in /repo would split by it
@app.function(cpu=8, memory=16384, timeout=3600, single_use_containers=True)
def pytest(arguments: list, capture: bool = False) -> tuple:
    """pytest over the checkout in the container: (exit code, its output if `capture`, else streamed, and the durations
    it stored if `--store-durations` is among the arguments: only the tests it ran, for the launcher to merge)."""
    subprocess.run(["git", "init", "-q", REMOTE], check=False)  # suites that ask for the work tree's root
    storing = "--store-durations" in arguments
    command = [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", *arguments]
    if storing or "--splits" in arguments:
        command += ["--durations-path", f"{REMOTE}/{DURATIONS}"]
    if storing:
        command.append("--clean-durations")
    print("$", shlex.join(command), flush=True)
    environment = {**os.environ, "PYTHONUTF8": "1", "DAODAN_TEST_BABEL": BABEL[1], "DAODAN_SECRETLINT": SECRETLINT[2],
                   "DAODAN_STACK_ANALYSER": "/opt/stack-analyser/package/dist/cli.mjs"}
    started = time.monotonic()
    done = subprocess.run(command, cwd=REMOTE, env=environment, **(CAPTURE if capture else {}))
    if capture:
        print(f"exit {done.returncode} in {time.monotonic() - started:.0f} s", flush=True)
    stored = Path(REMOTE, DURATIONS)
    durations = json.loads(stored.read_text(encoding="utf-8")) if storing and stored.is_file() else {}
    return done.returncode, done.stdout or "", durations


def shards_of(arguments: list) -> tuple:
    """`--shards N` out of the arguments: (the rest, N or 0)."""
    if "--shards" not in arguments:
        return arguments, 0
    at = arguments.index("--shards")
    if at + 1 == len(arguments) or not arguments[at + 1].isdigit() or not int(arguments[at + 1]):
        raise SystemExit("--shards takes the number of containers: --shards 8")
    return arguments[:at] + arguments[at + 2:], int(arguments[at + 1])


def sharded(arguments: list, shards: int) -> list:
    """The suite over `shards` containers at once, each on its group of tests (pytest-split, by the durations in
    `DURATIONS`); the groups' outputs in order, then one line for all: [(code, output, durations)]."""
    started = time.monotonic()
    groups = [([*arguments, "--splits", str(shards), "--group", str(group), "--splitting-algorithm", "least_duration"], True)
              for group in range(1, shards + 1)]
    done = list(pytest.with_options(cpu=SHARD_CPU, memory=2048 * SHARD_CPU).starmap(groups, return_exceptions=True))
    results = [(1, f"{type(result).__name__}: {result}", {}) if isinstance(result, BaseException) else result
               for result in done]
    total = Counter()
    for group, (code, output, _) in enumerate(results, 1):
        print(f"\n===== group {group}/{shards}: exit {code} =====\n{output}")
        summary = next((line for line in reversed(output.splitlines()) if SUMMARY.search(line) and " in " in line), "")
        for count, outcome in SUMMARY.findall(summary):
            total[SINGULAR.get(outcome, outcome)] += int(count)
    counts = ", ".join(f"{count} {outcome}" for outcome, count in total.items() if outcome != "deselected")
    print(f"\n===== {shards} groups: {counts} in {time.monotonic() - started:.0f} s, exits {[code for code, *_ in results]} =====")
    return results


@app.local_entrypoint()
def main(args: str = ""):
    arguments, shards = shards_of(shlex.split(args))
    results = sharded(arguments, shards) if shards else [pytest.remote(arguments)]
    # exit 5 is a group with no test to run (few tests, many groups): not a failure unless every group has none
    code = max((code for code, *_ in results if code != 5), default=5)
    stored = [durations for _, _, durations in results if durations]
    if stored and not code:  # a failing run keeps the file as it was; the groups return only what they ran
        path = REPO / DURATIONS
        merged = {} if "--clean-durations" in arguments or not path.is_file() else json.loads(path.read_text(encoding="utf-8"))
        for durations in stored:
            merged.update(durations)
        path.write_text(json.dumps(merged, sort_keys=True, indent=4) + "\n", encoding="utf-8", newline="\n")
        print(f"{len(merged)} durations in {path}")
    if code:
        raise SystemExit(code)
