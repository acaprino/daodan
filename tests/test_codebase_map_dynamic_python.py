"""The Python observer of the dynamic step: what it runs, from the pre-map alone, and what it reads back.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_dynamic_python.py

No container starts: `container.run_in_container` is a fake that keeps what it is given (the two scripts, the
image, the limits) and plays a run's outputs into the output folder, as the engine would bring them back.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import preparation  # noqa: E402
from dynamic import python as observer  # noqa: E402

PYTEST = {"root": ".", "runner": "pytest", "declared_in": "pyproject.toml#tool.pytest.ini_options", "args": []}
PACKAGED = '[project]\nname = "a"\n[build-system]\nrequires = ["hatchling"]\nbuild-backend = "hatchling.build"\n'


def plan(tests, files, toolchains=(), texts=None):
    record = {"tests": list(tests), "toolchains": list(toolchains)}
    return observer.plan(record, sorted(files), lambda rel: (texts or {}).get(rel, ""))


def kinds(found: dict) -> list[str]:
    return [gap["kind"] for gap in found["gaps"]]


# ------------------------------------------------------------------ what to run

def test_no_declared_test_command_is_a_gap_and_nothing_runs():
    found = plan([], ["pyproject.toml", "tests/test_a.py"])
    assert found["runs"] == [] and kinds(found) == ["no_test_command"]
    assert "declares" in found["gaps"][0]["detail"]


def test_pytest_runs_where_the_project_declares_it_in_the_environment_of_its_folder():
    found = plan([PYTEST], ["pyproject.toml", "uv.lock", "tests/test_a.py"], texts={"pyproject.toml": PACKAGED})
    assert found["gaps"] == []
    assert found["runs"] == [{"root": ".", "runner": "pytest", "declared_in": PYTEST["declared_in"],
                              "argv": ["-m", "pytest", observer.KEEP_GOING], "env": ".", "manager": "uv",
                              "install": True}]


def test_a_test_folder_outside_every_python_project_uses_the_only_environment_the_project_restores():
    """Daodan's own shape: the tests beside the scripts, whose folder holds the requirements."""
    tests = [{"root": ".", "runner": "pytest", "declared_in": "tests/conftest.py", "args": ["tests"]}]
    found = plan(tests, ["scripts/requirements.txt", "scripts/lib.py", "tests/conftest.py", "tests/test_a.py"])
    assert found["gaps"] == []
    assert found["runs"] == [{"root": ".", "runner": "pytest", "declared_in": "tests/conftest.py",
                              "argv": ["-m", "pytest", "tests", observer.KEEP_GOING], "env": "scripts",
                              "manager": "pip", "install": False}]


def test_manifests_inside_the_test_folders_are_fixtures_not_the_environment_nor_tests_of_their_own():
    """A test tree holds fixture projects: their manifests are not where the tests' dependencies are declared, and
    a pytest declared inside the folders another pytest run is given is collected by that run."""
    tests = [{"root": ".", "runner": "pytest", "declared_in": "tests/conftest.py", "args": ["tests"]},
             {"root": "tests/fixtures/app", "runner": "pytest", "declared_in": "tests/fixtures/app/pytest.ini",
              "args": []},
             {"root": "tools", "runner": "pytest", "declared_in": "tools/pytest.ini", "args": []}]
    files = ["scripts/requirements.txt", "tests/conftest.py", "tests/fixtures/app/pyproject.toml",
             "tests/fixtures/app/pytest.ini", "tests/fixtures/lib/requirements.txt", "tools/pytest.ini"]
    found = plan(tests, files)
    assert [(run["root"], run["env"]) for run in found["runs"]] == [(".", "scripts"), ("tools", None)]
    assert found["gaps"] == []


def test_without_a_manifest_the_tests_run_in_an_empty_environment():
    tests = [{"root": ".", "runner": "unittest", "declared_in": "tox.ini", "args": ["discover", "-s", "tests"]}]
    [run] = plan(tests, ["tox.ini", "tests/test_a.py"])["runs"]
    assert (run["env"], run["manager"], run["argv"]) == (None, None, ["-m", "unittest", "discover", "-s", "tests"])


@pytest.mark.parametrize("stated, kind", [
    ("3.11", "python_too_old"), ("3.11.9", "python_too_old"), ("3.11-slim", "python_too_old"),
    (">=3.8,<3.12", "python_too_old"), ("~3.10", "python_too_old"), ("^2.7", "python_too_old"),
    (">=3.15", "python_unavailable"), (">=3.9", None), ("^3.9", None), ("~=3.12", None), ("3.13", None),
    (">=3.12,<3.14", None), ("==3.13.*", None), ("~3", None), ("3", None), ("whatever", None)])
def test_a_python_the_recorder_cannot_run_on_is_a_gap_and_its_tests_do_not_run(stated, kind):
    """sys.monitoring is Python 3.12's: a project that states an older one is not run on a newer one."""
    chains = [{"tool": "python", "version": stated, "declared_in": "pyproject.toml"}]
    found = plan([PYTEST], ["pyproject.toml", "tests/test_a.py"], chains)
    assert kinds(found) == ([kind] if kind else [])
    assert bool(found["runs"]) is (kind is None)
    if kind:
        assert stated in found["gaps"][0]["detail"] and found["gaps"][0]["path"] == "pyproject.toml"


def test_an_exact_python_the_image_does_not_hold_is_installed_at_that_version():
    chains = [{"tool": "python", "version": "3.12.4", "declared_in": ".python-version"},
              {"tool": "node", "version": "22.1.0", "declared_in": ".nvmrc"},
              {"tool": "python", "version": "3.9", "declared_in": "elsewhere/.python-version"}]
    found = plan([PYTEST], ["pyproject.toml", "tests/test_a.py"], chains)
    assert found["toolchains"] == [chains[0]] and len(found["runs"]) == 1 and found["gaps"] == []


# ------------------------------------------------------------------ the two scripts

def scripts_of(tests, files, **given):
    planned = plan(tests, files, **given)
    return planned, *observer.scripts(planned)[:2]


def test_the_preparation_restores_the_declared_dependencies_and_the_execution_runs_the_declared_command():
    tests = [{"root": ".", "runner": "pytest", "declared_in": "tests/conftest.py", "args": ["tests"]}]
    planned, prepare, execute = scripts_of(tests, ["scripts/requirements.txt", "tests/conftest.py"])
    assert preparation.restore("pip", ["scripts"]) in prepare  # the shared preparation's own line
    assert preparation.UNPACK_UV in prepare
    venv = f"{preparation.VENVS}/scripts/bin/python"
    # the runner the project declares and does not install is brought at Daodan's pin, and said
    assert f"pytest=={observer.PYTEST}" in prepare and "brought pytest" in prepare
    assert " -e " not in prepare  # nothing to install: the folder has no build configuration
    assert f"run 0 . {venv} -m pytest tests" in execute
    assert "DYN_ROOT=/work" in execute and f"PYTHONPATH={observer.SITE}" in execute
    assert f"timeout -s INT -k 30 {observer.LIMIT}" in execute  # an interrupt: the recorder writes on exit
    assert "pip install" not in execute and "uv " not in execute  # no network there: nothing is fetched


def test_a_project_with_a_build_configuration_is_installed_as_its_tests_import_it():
    planned, prepare, execute = scripts_of([PYTEST], ["pyproject.toml", "uv.lock"],
                                           texts={"pyproject.toml": PACKAGED})
    assert preparation.restore("uv", ["."]) in prepare
    assert "--no-deps -e /work/." in prepare
    assert f"run 0 . {preparation.VENVS}/./bin/python -m pytest" in execute


def test_poetry_runs_the_tests_in_the_environment_poetry_made():
    planned, prepare, execute = scripts_of([PYTEST], ["pyproject.toml", "poetry.lock"])
    assert preparation.restore("poetry", ["."]) in prepare
    assert 'run 0 . "$(cd /work/. && poetry env info -e)" -m pytest' in execute


def test_an_empty_environment_is_made_for_tests_no_manifest_holds():
    tests = [{"root": "old", "runner": "unittest", "declared_in": "old/tox.ini", "args": []}]
    planned, prepare, execute = scripts_of(tests, ["old/tox.ini", "old/test_a.py"])
    venv = f"{preparation.VENVS}/.daodan-0"
    assert f"uv venv -q --python python3 {venv}" in prepare
    assert f"run 0 old {venv}/bin/python -m unittest" in execute
    assert "pytest" not in prepare


# ------------------------------------------------------------------ the run, played

SITE = {"file": "tests/test_a.py", "line": 3, "column": 4, "name": "f", "role": "call", "end": [4, 4, 4, 7],
        "callees": [{"kind": "project", "file": "lib.py", "line": 0, "column": 0, "name": "f", "type": "function",
                     "native": False}]}


class Played:
    """The fake `container.run_in_container`: what it was given, and the outputs of the run it plays."""

    def __init__(self, execute: str = "DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 0 12\n",
                 prepare: str = "", tests: str = "1 passed in 0.10s\n", observations=(SITE,), state: str = "done",
                 **result):
        self.execute, self.prepare, self.tests, self.observations = execute, prepare, tests, observations
        self.result = {"state": state, "exit_code": 0, "outputs": [], **result}
        self.calls: list[dict] = []

    def __call__(self, project, command, **given):
        self.calls.append({"project": project, "command": command, **given})
        if self.result["state"] == "gap":
            return self.result
        out_dir = Path(given["out_dir"])
        (out_dir / "out").mkdir(parents=True, exist_ok=True)
        (out_dir / "prepare.log").write_text(self.prepare, encoding="utf-8")
        (out_dir / "execute.log").write_text(self.execute, encoding="utf-8")
        (out_dir / "out" / "tests-0.log").write_text(self.tests, encoding="utf-8")
        for number, site in enumerate(self.observations):
            (out_dir / "out" / f"observed-0-{number}.json").write_text(json.dumps(
                {"exact": True, "python": "3.13.18", "stats": {}, "sites": [site]}), encoding="utf-8")
        return self.result


def observe(tmp_path, played: Played, tests=(PYTEST,), files=("pyproject.toml", "tests/test_a.py")):
    planned = plan(tests, files)
    with mock.patch.object(container, "run_in_container", side_effect=played):
        return observer.observe(tmp_path / "project", planned, tmp_path / "out", engine="the engine")


def test_the_tests_run_only_in_the_container_prepared_with_the_registries_and_run_with_no_network(tmp_path):
    played = Played()
    result = observe(tmp_path, played)
    [call] = played.calls
    assert call["project"] == tmp_path / "project" and call["engine"] == "the engine"
    assert call["image"] == observer.IMAGE and call["memory"] == observer.MEMORY
    assert call["command"][:2] == ["sh", "-c"] and call["prepare"][:2] == ["sh", "-c"]  # the two phases
    assert call["outputs"] == [observer.OUT] and call["out_dir"] == tmp_path / "out"
    assert call["env"]["PATH"] == preparation.PATH and call["timeout"] > observer.LIMIT
    with mock.patch.object(preparation, "fetched", side_effect=lambda url, digest, name: Path(name)):
        carried = call["inputs"]()
    assert carried[f"{preparation.IN}/python_record.py"] == observer.RECORDER  # the recorder rides with the copy
    assert carried[f"{preparation.IN}/uv.tar.gz"] == Path("uv.tar.gz")
    assert result["state"] == "ran" and result["gaps"] == []
    assert result["sites"] == [SITE]
    assert result["runs"] == [{"root": ".", "runner": "pytest", "declared_in": PYTEST["declared_in"],
                               "state": "ran", "exit_code": 0, "seconds": 12, "python": "3.13.18",
                               "processes": 1}]


def test_a_site_two_processes_saw_is_one_site_with_the_callees_of_both(tmp_path):
    other = {**SITE, "callees": [{**SITE["callees"][0], "name": "g", "line": 4}]}
    result = observe(tmp_path, Played(observations=(SITE, other)))
    [site] = result["sites"]
    assert [callee["name"] for callee in site["callees"]] == ["f", "g"] and result["runs"][0]["processes"] == 2


def test_without_a_container_engine_the_observer_states_the_gap_and_runs_nothing_on_the_host(tmp_path):
    played = Played(state="gap", cause="no container engine answers", remedy="start Docker or Podman")
    with mock.patch("subprocess.run", side_effect=AssertionError("something ran on the host")), \
            mock.patch("subprocess.Popen", side_effect=AssertionError("something ran on the host")):
        result = observe(tmp_path, played)
    assert result == {"state": "gap", "cause": "no container engine answers", "remedy": "start Docker or Podman",
                      "sites": [], "runs": [], "gaps": []}


@pytest.mark.parametrize("execute, tests, kind, state, said", [
    ("DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 5 1\n", "no tests ran in 0.01s\n",
     "no_tests", "no_tests", "no test"),
    ("DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 2 1\n",
     "ERROR collecting tests/test_a.py\nModuleNotFoundError: No module named 'acme'\n",
     "tests_not_started", "not_started", "No module named 'acme'"),
    ("DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 1 9\n", "FAILED tests/test_a.py::test_x\n"
     "=== 1 failed, 4 passed in 2.1s ===\n", "tests_failed", "ran", "1 failed, 4 passed"),
    ("DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 1 0\n", "/venv/bin/python: No module named pytest\n",
     "tests_not_started", "not_started", "No module named pytest"),
    ("DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 124 3600\n", "tests/test_a.py ..\n",
     "tests_timeout", "timeout", str(observer.LIMIT)),
    ("DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 137 3630\n", "tests/test_a.py ..\n",
     "tests_timeout", "timeout", str(observer.LIMIT)),  # the interrupt was not enough: killed after the limit
    ("DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 137 41\n", "tests/test_a.py ..\n",
     "tests_killed", "killed", "memory"),
    ("DAODAN-DYNAMIC 0 python 3.11.9 0\n", "", "python_too_old", "not_started", "3.11.9"),
    ("DAODAN-DYNAMIC 0 no-python\n", "", "tests_not_started", "not_started", "no Python environment"),
    ("DAODAN-DYNAMIC 0 python 3.13.18 1\n", "", "tests_not_started", "not_started", "ended before"),
])
def test_tests_that_do_not_run_to_their_end_are_a_gap_with_the_cause(tmp_path, execute, tests, kind, state, said):
    result = observe(tmp_path, Played(execute=execute, tests=tests))
    assert result["state"] == "ran" and result["runs"][0]["state"] == state
    [gap] = result["gaps"]
    assert gap["kind"] == kind and said in gap["detail"] and gap["path"] == "."


@pytest.mark.parametrize("tests, state, kinds", [
    ("__ ERROR collecting tests/test_b.py __\nE   ModuleNotFoundError: No module named 'acme'\n"
     "__ ERROR collecting tests/test_c.py __\nE   RuntimeError: no service\n=== 4 passed, 2 errors in 0.5s ===\n",
     "ran", ["tests_not_collected"]),
    ("__ ERROR collecting tests/test_b.py __\nE   ModuleNotFoundError: No module named 'acme'\n"
     "FAILED tests/test_a.py::test_x\n=== 1 failed, 3 passed, 1 error in 0.5s ===\n",
     "ran", ["tests_failed", "tests_not_collected"]),
    ("__ ERROR collecting tests/test_b.py __\nE   ModuleNotFoundError: No module named 'acme'\n"
     "__ ERROR collecting tests/test_c.py __\nE   RuntimeError: no service\n=== 2 errors in 0.5s ===\n",
     "not_started", ["tests_not_collected"])])
def test_test_modules_pytest_could_not_collect_are_one_gap_and_the_others_run(tmp_path, tests, state, kinds):
    result = observe(tmp_path, Played(execute="DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 1 3\n",
                                      tests=tests))
    assert result["runs"][0]["state"] == state and [gap["kind"] for gap in result["gaps"]] == kinds
    gap = result["gaps"][-1]
    assert gap["modules"][0] == {"file": "tests/test_b.py", "error": "ModuleNotFoundError: No module named 'acme'"}
    assert gap["count"] == len(gap["modules"]) and "tests/test_b.py" in gap["detail"]


@pytest.mark.parametrize("runner, args", [("pytest", ["tests"]), ("unittest", ["discover", "-s", "tests"])])
def test_a_test_module_that_does_not_import_leaves_the_others_running(tmp_path, runner, args):
    """Real runs of both runners on one module that imports and one that does not. pytest stops at a collection
    error unless it is told not to, with its own option (`KEEP_GOING`); unittest loads each module apart and makes
    a failed import a test in error, so it needs nothing."""
    project = tmp_path / "project"
    (project / "tests").mkdir(parents=True)
    (project / "tests" / "test_good.py").write_text(
        "import unittest\n\n\nclass Good(unittest.TestCase):\n    def test_it(self):\n        self.assertTrue(True)\n",
        encoding="utf-8")
    (project / "tests" / "test_bad.py").write_text("import acme_missing\n", encoding="utf-8")
    test = {"root": ".", "runner": runner, "declared_in": "tox.ini", "args": args}
    [run] = plan([test], ["tox.ini", "tests/test_good.py", "tests/test_bad.py"])["runs"]
    env = {key: value for key, value in os.environ.items() if not key.startswith(("PYTEST", "PYTHON"))}
    done = subprocess.run([sys.executable, *run["argv"]], cwd=project, env=env, capture_output=True, text=True)
    log = done.stdout + done.stderr
    assert done.returncode == 1, log  # 2 is pytest's interrupted collection: nothing ran
    played = Played(execute=f"DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit {done.returncode} 1\n",
                    tests=log)
    result = observe(tmp_path, played, tests=[test], files=["tox.ini", "tests/test_good.py"])
    assert result["runs"][0]["state"] == "ran"
    if runner == "pytest":
        [gap] = result["gaps"]
        assert gap["kind"] == "tests_not_collected" and gap["modules"] == [
            {"file": "tests/test_bad.py", "error": "ModuleNotFoundError: No module named 'acme_missing'"}]
    else:
        assert "Ran 2 tests" in log and [gap["kind"] for gap in result["gaps"]] == ["tests_failed"]


def test_what_the_preparation_could_not_do_is_a_gap_of_the_run(tmp_path):
    prepare = ("DAODAN-MISSING python@3.12.4\n"
               "DAODAN-RESTORE-FAILED uv .\nerror: No solution found\nDAODAN-RESTORE-END\n"
               "DAODAN-DYNAMIC 0 not-installed\nerror: build backend failed\nDAODAN-DYNAMIC-END\n"
               f"DAODAN-DYNAMIC 0 brought pytest {observer.PYTEST}\n")
    result = observe(tmp_path, Played(prepare=prepare))
    found = {gap["kind"]: gap for gap in result["gaps"]}
    assert set(found) == {"toolchain_unavailable", "restore_failed", "project_not_installed", "runner_brought"}
    assert "build backend failed" in found["project_not_installed"]["detail"]
    assert observer.PYTEST in found["runner_brought"]["detail"]


def test_tests_that_reach_for_a_service_or_the_network_are_said(tmp_path):
    """The execution has no network and starts no service: a project that needs one must declare how it starts,
    and the step starts none."""
    tests = ("E   ConnectionRefusedError: [Errno 111] Connection refused\n"
             "E   socket.gaierror: [Errno -3] Temporary failure in name resolution\n=== 2 failed, 1 passed ===\n")
    result = observe(tmp_path, Played(execute="DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 1 4\n",
                                      tests=tests))
    assert [gap["kind"] for gap in result["gaps"]] == ["tests_failed", "services_unreachable"]
    assert "2 lines" in result["gaps"][1]["detail"]


def test_a_preparation_that_fails_or_a_run_the_engine_ends_is_a_gap_with_its_cause(tmp_path):
    """Nothing is kept of such a run: the next one tries again."""
    result = observe(tmp_path, Played(state="failed", cause="preparation exited with code 70; see prepare.log",
                                      prepare="DAODAN-MISSING uv@0.11.28\n", execute="", observations=()))
    assert result["state"] == "failed" and result["sites"] == [] and result["runs"] == []
    assert "preparation exited with code 70" in result["cause"] and str(tmp_path / "out") in result["remedy"]
    assert [gap["kind"] for gap in result["gaps"]] == ["toolchain_unavailable"]


def test_a_python_the_recorder_is_not_verified_on_is_said(tmp_path):
    result = observe(tmp_path, Played(execute="DAODAN-DYNAMIC 0 python 3.14.1 1\nDAODAN-DYNAMIC 0 exit 0 2\n"))
    [gap] = result["gaps"]
    assert gap["kind"] == "recorder_unverified" and "3.14.1" in gap["detail"]
