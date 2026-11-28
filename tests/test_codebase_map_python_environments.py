"""Which Python environment a command in a folder uses: the restore makes environments only for the root, for a folder with a
lockfile of its own, for a folder marked only by a requirements file and for the folders no marked folder holds (`preparation.restores`); a folder inside another runs in the one of
the nearest folder above that was restored, and Poetry's lives in Poetry's own cache. One piece of code says it, for the dynamic step
of the Python tests (`dynamic/python.py`) and for the Flask source (`premap/flask_app.py`)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import preparation  # noqa: E402
from dynamic import python as dynamic  # noqa: E402


def held(files, locks=()):
    """The folder -> manager of what the restore makes, the lockfiles being the ones the checkout holds (`locks`)."""
    return preparation.python_environments(files, lambda rel: rel in locks)


def test_a_plain_root_project_has_the_environment_of_the_root_and_every_folder_below_it_runs_in_it():
    environments = held(["pyproject.toml", "requirements.txt", "wsgi.py", "api/app.py"])
    assert environments == {".": "pip"}
    assert [preparation.python_environment(environments, folder) for folder in (".", "api", "api/v1")] == [".", ".", "."]


def test_a_uv_workspace_is_one_environment_at_its_root_and_a_member_runs_in_it():
    environments = held(["pyproject.toml", "api/pyproject.toml", "api/wsgi.py"], locks={"uv.lock"})
    assert environments == {".": "uv"}  # `uv sync --all-packages`: the members' dependencies are in the root's environment
    assert preparation.python_environment(environments, "api") == "."


def test_a_requirements_file_in_a_subfolder_of_a_root_pyproject_is_an_environment_of_its_own():
    environments = held(["pyproject.toml", "api/requirements.txt", "api/wsgi.py"])
    assert environments == {".": "pip", "api": "pip"}  # a folder marked only by a requirements file is a project of its own (T1.10)
    assert [preparation.python_environment(environments, folder) for folder in (".", "api", "api/v1")] == [".", "api", "api"]


def test_a_poetry_project_is_an_environment_and_its_manager_says_where_the_python_is():
    environments = held(["pyproject.toml", "wsgi.py"], locks={"poetry.lock"})
    assert environments == {".": "poetry"}
    assert preparation.python_interpreter(".", "poetry", "/work") == '"$(cd /work/. && poetry env info -e)"'


def test_a_folder_with_its_own_lockfile_is_an_environment_and_the_nearest_one_above_serves_the_folders_below():
    environments = held(["pyproject.toml", "api/pyproject.toml", "api/v1/wsgi.py", "worker/main.py"], locks={"api/uv.lock"})
    assert environments == {".": "pip", "api": "uv"}
    assert [preparation.python_environment(environments, folder) for folder in (".", "api", "api/v1", "worker")] == [".", "api", "api", "."]


def test_a_project_with_no_python_manifest_has_no_environment():
    assert held(["main.go", "go.mod"]) == {} and preparation.python_environment({}, "api") is None


def test_the_interpreter_of_an_environment_is_in_the_venvs_the_restore_makes_unless_poetry_keeps_it():
    assert preparation.python_interpreter("api", "uv", "/work") == f"{preparation.VENVS}/api/bin/python"
    assert preparation.python_interpreter(".", "pip", "/work") == f"{preparation.VENVS}/./bin/python"
    assert preparation.python_interpreter("api", "poetry", "/work") == '"$(cd /work/api && poetry env info -e)"'


def test_the_dynamic_step_takes_the_interpreter_and_the_environment_from_the_same_code():
    """`dynamic/python.py` does not keep its own copy: its word for a run's Python is `preparation.python_interpreter`."""
    for env, manager in ((".", "pip"), ("api", "uv"), ("api", "poetry")):
        assert dynamic._interpreter(0, {"env": env, "manager": manager}) == preparation.python_interpreter(env, manager, "/work")
    assert dynamic._interpreter(3, {"env": None, "manager": None}) == f"{preparation.VENVS}/.daodan-3/bin/python"
