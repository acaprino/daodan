"""The pre-map's `tests` facet for Python: the command a project declares for its tests, never one of Daodan's.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_premap_python_tests.py
"""
from __future__ import annotations

from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))

import premap  # noqa: E402
from premap import python_tests  # noqa: E402
import snapshot  # noqa: E402

READERS = tuple(source for source in premap.SOURCES if not hasattr(source, "commands"))
TEST = "def test_it():\n    assert True\n"


def declared(tmp_path, files: dict) -> list[dict]:
    project = tmp_path / "proj"
    for rel, text in files.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    record = premap.write(manifest, sources=READERS)
    assert not [gap for gap in record["gaps"] if gap["kind"] == "source_failed"]
    return [{key: value for key, value in entry.items() if key != "sources"} for entry in record.get("tests", [])]


def test_the_reader_is_a_source_of_the_pre_map():
    assert python_tests in premap.SOURCES and python_tests.RANK == "reader" and "tests" in premap.IDENTITY


def test_a_pytest_configuration_gives_the_folder_pytest_runs_in(tmp_path):
    found = declared(tmp_path, {
        "pyproject.toml": '[project]\nname = "a"\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
        "tests/test_a.py": TEST, "tests/conftest.py": "",
        "svc/pytest.ini": "[pytest]\n", "svc/test_b.py": TEST,
        "old/setup.cfg": "[tool:pytest]\naddopts = -q\n", "old/test_c.py": TEST,
        "tox/tox.ini": "[pytest]\n", "tox/test_d.py": TEST})
    assert found == [
        {"root": ".", "runner": "pytest", "declared_in": "pyproject.toml#tool.pytest.ini_options", "args": []},
        {"root": "old", "runner": "pytest", "declared_in": "old/setup.cfg#tool:pytest", "args": []},
        {"root": "svc", "runner": "pytest", "declared_in": "svc/pytest.ini", "args": []},
        {"root": "tox", "runner": "pytest", "declared_in": "tox/tox.ini#pytest", "args": []}]


def test_pytest_among_the_declared_dependencies_declares_it(tmp_path):
    """The list that names pytest is where the tests' dependencies are (`deps`): a group, an extra, a requirements
    file; Poetry's groups are installed by its own restore."""
    found = declared(tmp_path, {
        "pyproject.toml": '[project]\nname = "a"\ndependencies = ["requests"]\n'
                          '[dependency-groups]\ndev = ["ruff", "pytest>=8"]\n',
        "extra/pyproject.toml": '[project]\nname = "b"\n[project.optional-dependencies]\ntest = ["pytest-asyncio"]\n',
        "poetry/pyproject.toml": '[tool.poetry]\nname = "c"\n[tool.poetry.group.dev.dependencies]\npytest = "^8"\n',
        "pip/requirements.txt": "requests\n", "pip/requirements-dev.txt": "-r requirements.txt\npytest==8.3.1\n",
        "none/pyproject.toml": '[project]\nname = "d"\ndependencies = ["pytestify"]\n'})
    assert found == [
        {"root": ".", "runner": "pytest", "declared_in": "pyproject.toml#dependency-groups.dev", "args": [],
         "deps": {"declared_in": "pyproject.toml#dependency-groups.dev", "groups": ["dev"]}},
        {"root": "extra", "runner": "pytest", "args": [],
         "declared_in": "extra/pyproject.toml#project.optional-dependencies.test",
         "deps": {"declared_in": "extra/pyproject.toml#project.optional-dependencies.test", "extras": ["test"]}},
        {"root": "pip", "runner": "pytest", "declared_in": "pip/requirements-dev.txt", "args": [],
         "deps": {"declared_in": "pip/requirements-dev.txt", "requirements": ["-r requirements-dev.txt"]}},
        {"root": "poetry", "runner": "pytest", "args": [],
         "declared_in": "poetry/pyproject.toml#tool.poetry.group.dev.dependencies"}]


def test_the_tests_dependencies_are_those_of_the_tox_environment_that_runs_them(tmp_path):
    """mix-real-python-semver: .pytest.ini configures pytest (its addopts need pytest-cov) and the CI runs the
    tests through tox, whose [testenv] declares their dependencies; the `test` group names pytest too, and tox's
    environment is the one that runs. A named environment falls back to [testenv] for what it does not set;
    `{toxinidir}` is the folder of tox.ini, where the install runs."""
    found = declared(tmp_path, {
        ".pytest.ini": "[pytest]\naddopts = --cov=a\n",
        "tox.ini": "[tox]\nenvlist = checks, py3{12,13}\n[testenv]\nskip_install = true\ncommands = pytest {posargs:}\n"
                   "deps =\n    pytest\n    # coverage\n    pytest-cov\n    -r{toxinidir}/requirements.txt\n"
                   "    setuptools>=70\n[testenv:checks]\ndeps = ruff\ncommands = ruff check\n",
        "pyproject.toml": '[project]\nname = "a"\n[dependency-groups]\ntest = ["pytest<=9.1.1"]\n',
        "named/pytest.ini": "[pytest]\n",
        "named/tox.ini": "[testenv]\ndeps = mock\n[testenv:unit]\nextras = test, cli\ndependency_groups = dev\n"
                         "commands = coverage run -m pytest tests\n",
        "group/pyproject.toml": '[project]\nname = "b"\n[tool.pytest.ini_options]\n[dependency-groups]\n'
                                'lint = ["ruff"]\ntest = ["pytest-asyncio"]\n'})
    assert found == [
        {"root": ".", "runner": "pytest", "declared_in": ".pytest.ini", "args": [],
         "deps": {"declared_in": "tox.ini#testenv",
                  "requirements": ["pytest", "pytest-cov", "-r./requirements.txt", "setuptools>=70"]}},
        {"root": "group", "runner": "pytest", "declared_in": "group/pyproject.toml#tool.pytest.ini_options",
         "args": [], "deps": {"declared_in": "group/pyproject.toml#dependency-groups.test", "groups": ["test"]}},
        {"root": "named", "runner": "pytest", "declared_in": "named/pytest.ini", "args": [],
         "deps": {"declared_in": "named/tox.ini#testenv:unit", "requirements": ["mock"], "extras": ["test", "cli"],
                  "groups": ["dev"]}}]


def test_a_conftest_alone_gives_its_folder_to_pytest_from_the_nearest_manifest_above_or_the_root(tmp_path):
    """Daodan's own shape: scripts with a requirements file in one folder, the tests with a conftest in another."""
    found = declared(tmp_path, {
        "scripts/requirements.txt": "sqlglot\n", "scripts/lib.py": "x = 1\n",
        "tests/conftest.py": "", "tests/test_a.py": TEST, "tests/deep/conftest.py": "",
        "checks/conftest.py": "",
        "pkg/setup.py": "from setuptools import setup\nsetup(name='p')\n", "pkg/tests/conftest.py": ""})
    assert found == [
        {"root": ".", "runner": "pytest", "declared_in": "checks/conftest.py", "args": ["checks", "tests"]},
        {"root": "pkg", "runner": "pytest", "declared_in": "pkg/tests/conftest.py", "args": ["tests"]}]


def test_a_conftest_at_the_root_runs_pytest_there(tmp_path):
    assert declared(tmp_path, {"conftest.py": "", "test_a.py": TEST}) == [
        {"root": ".", "runner": "pytest", "declared_in": "conftest.py", "args": []}]


def test_unittest_only_where_a_file_writes_its_command(tmp_path):
    found = declared(tmp_path, {
        "tox.ini": "[tox]\n[testenv]\ncommands = python -m unittest discover -s tests {posargs}\n",
        "tests/test_a.py": "import unittest\n",
        "make/Makefile": "test:\n\t@python3 -m unittest\n", "make/test_b.py": "import unittest\n",
        "var/Makefile": "test:\n\tpython -m unittest discover -s $(TESTS)\n", "var/test_c.py": "import unittest\n",
        "both/tox.ini": "[pytest]\n[testenv]\ncommands = python -m unittest\n"})
    assert found == [
        {"root": ".", "runner": "unittest", "declared_in": "tox.ini", "args": ["discover", "-s", "tests"]},
        {"root": "both", "runner": "pytest", "declared_in": "both/tox.ini#pytest", "args": []},
        {"root": "make", "runner": "unittest", "declared_in": "make/Makefile", "args": []}]


def test_a_project_that_declares_no_runner_states_nothing(tmp_path):
    """Test files alone are a convention, not a declaration: no entry, and the dynamic step says the gap."""
    assert declared(tmp_path, {"pyproject.toml": '[project]\nname = "a"\n', "tests/test_a.py": TEST,
                               "test_b.py": "import unittest\n"}) == []
