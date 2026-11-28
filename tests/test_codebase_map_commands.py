"""The commands of the user (`confermato`) and of the assistant (`proposto`), kept in the shared folder (`commands`).

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_commands.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import commands  # noqa: E402
import dynamic  # noqa: E402
import egress  # noqa: E402
from dynamic import app  # noqa: E402

NPM_START = {"root": "web", "mode": "start", "runner": "npm", "declared_in": "web/package.json#scripts.start",
             "port": 3000, "needs_build": False}
CI_TESTS = {"root": ".", "runner": "pytest", "argv": ["pytest", "-q"], "source": "ci",
            "declared_in": ".github/workflows/ci.yml#jobs.t.steps.1"}


@pytest.fixture
def project(tmp_path):
    folder = tmp_path / "project"
    (folder / "web").mkdir(parents=True)
    return str(folder.resolve())


def test_the_user_s_command_is_confermato_and_kept_in_the_shared_folder_never_in_the_project(project):
    kept = commands.set(project, {"kind": "tests", "root": "./", "argv": ["pytest", "-m", "integration"]}, "user")
    assert kept == [{"kind": "tests", "root": ".", "argv": ["pytest", "-m", "integration"], "by": "user",
                     "grade": "confermato", "runner": "pytest"}]
    held = json.loads((egress.shared_cache_dir() / commands.FILE).read_text(encoding="utf-8"))
    assert held == {project: kept}
    assert [path.name for path in Path(project).rglob("*")] == ["web"]  # nothing is written in the project
    assert commands.listed(project) == kept and commands.listed(project + "-other") == []


def test_the_assistant_proposes_never_replaces_the_user_s_and_the_user_confirms_or_removes(project):
    commands.set(project, {"kind": "starts", "root": "web", "argv": ["npm", "run", "serve"], "port": 4000}, "assistant")
    assert commands.listed(project) == [{"kind": "starts", "root": "web", "argv": ["npm", "run", "serve"],
                                         "by": "assistant", "grade": "proposto", "port": 4000}]
    commands.set(project, {"kind": "starts", "root": "web", "argv": ["npm", "run", "dev"]}, "assistant")  # its own
    confirmed = commands.confirm(project, "starts", "web")
    assert confirmed == [{"kind": "starts", "root": "web", "argv": ["npm", "run", "dev"], "by": "user",
                          "grade": "confermato", "proposed_by": "assistant"}]
    with pytest.raises(ValueError, match="does not replace"):
        commands.set(project, {"kind": "starts", "root": "web", "argv": ["npm", "start"]}, "assistant")
    with pytest.raises(ValueError, match="nothing to confirm"):
        commands.confirm(project, "starts", "web")
    commands.set(project, {"kind": "starts", "root": "web", "argv": ["npm", "start"]}, "user")  # the user's own
    assert [row["argv"] for row in commands.listed(project)] == [["npm", "start"]]
    assert commands.remove(project, "starts", "web") == [] and commands.listed(project) == []
    with pytest.raises(ValueError, match="no single starts command"):
        commands.remove(project, "starts", "web")


def test_a_surface_is_one_of_the_registry_s_and_is_kept(project):
    """`surface` is a name of `registry_build.SURFACES`, the ones the registry's entries carry."""
    import registry_build
    for surface in registry_build.SURFACES:
        kept = commands.set(project, {"kind": "starts", "root": "web", "argv": ["npm", "start"], "surface": surface},
                            "user")
        assert [row.get("surface") for row in kept] == [surface]


def test_a_start_the_user_states_on_a_surface_not_run_yet_is_its_gap_and_does_not_start(project):
    """The user's start stands before the pre-map's of the same folder, and a surface the exploration does not run yet
    keeps it from starting: `ui_execution_deferred:<surface>`, naming this file."""
    import registry_build
    surface = next(surface for surface in registry_build.SURFACES if surface not in app.ACTIVE)
    commands.set(project, {"kind": "starts", "root": "web", "argv": ["npm", "run", "phone"], "surface": surface},
                 "user")
    planned = app.plan(commands.merged({"starts": [NPM_START]}, project))
    assert planned["apps"] == []
    assert [(gap["kind"], gap["root"], gap["path"]) for gap in planned["gaps"]] == [
        (f"ui_execution_deferred:{surface}", "web", commands.FILE)]


@pytest.mark.parametrize("given, said", [
    ({"kind": "tests", "root": ".", "argv": "pytest -q"}, "argv must be"),
    ({"kind": "tests", "root": ".", "argv": []}, "argv must be"),
    ({"kind": "tests", "root": ".", "argv": ["pytest", 3]}, "argv must be"),
    ({"kind": "lint", "root": ".", "argv": ["ruff"]}, "kind must be"),
    ({"kind": "tests", "root": "../elsewhere", "argv": ["pytest"]}, "outside the project"),
    ({"kind": "tests", "root": "web/../..", "argv": ["pytest"]}, "outside the project"),
    ({"kind": "tests", "root": "/etc", "argv": ["pytest"]}, "relative to its root"),
    ({"kind": "starts", "root": "web", "argv": ["npm", "start"], "port": 0}, "port must be"),
    ({"kind": "starts", "root": "web", "argv": ["npm", "start"], "port": "80"}, "port must be"),
    ({"kind": "starts", "root": "web", "argv": ["npm", "start"], "surface": "ios"}, "surface must be one of web, "),
    ({"kind": "starts", "root": "web", "argv": ["npm", "start"], "surface": ""}, "surface must be one of"),
    ("npm start", "an object"),
])
def test_a_command_that_is_not_well_formed_is_refused_and_nothing_is_kept(project, given, said):
    with pytest.raises(ValueError, match=said):
        commands.set(project, given, "user")
    with pytest.raises(ValueError, match="by must be"):
        commands.set(project, {"kind": "tests", "root": ".", "argv": ["pytest"]}, "ci")
    assert commands.listed(project) == []


def test_merged_puts_them_before_the_pre_map_s_and_the_observers_and_the_app_take_them_first(project):
    record = {"tests": [CI_TESTS], "starts": [NPM_START]}
    assert commands.merged(record, project) is record  # none kept: the record as it is
    commands.set(project, {"kind": "tests", "root": ".", "argv": ["pytest", "-m", "slow"]}, "assistant")
    commands.set(project, {"kind": "starts", "root": "web", "argv": ["npm", "run", "serve"], "port": 4000}, "user")
    merged = commands.merged(record, project)
    assert record == {"tests": [CI_TESTS], "starts": [NPM_START]}  # not changed
    assert merged["tests"][1:] == [CI_TESTS] and merged["starts"][1:] == [NPM_START]
    assert dynamic.declared(merged, "pytest", "")["argv"] == ["pytest", "-m", "slow"]  # the assistant before the CI
    assert dynamic.declared(merged, "pytest", "")["grade"] == "proposto"
    planned = app.plan(merged)
    assert [(one["root"], one["by"], one["port"]) for one in planned["apps"]] == [("web", "user", 4000)]
    assert app._command(planned["apps"][0]) == "npm run serve"
    assert app._command(NPM_START) == "npm run start"
    commands.set(project, {"kind": "starts", "root": "web", "argv": ["pnpm", "dev"]}, "user")
    planned = app.plan(commands.merged(record, project))  # the user's command stands, even where it cannot run yet
    assert planned["apps"] == [] and [gap["kind"] for gap in planned["gaps"]] == ["start_runner_not_supported"]
    assert planned["gaps"][0]["path"] == commands.FILE
