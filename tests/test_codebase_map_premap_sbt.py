"""The sbt source of the pre-map: sbt's loaded build, recorded once in a Linux container, read into units.

The answers are in `tests/fixtures/premap/sbt/<case>.json`, captured with the sbt 1.13.1 launcher on Temurin 17
through the pre-map's container runner, from the projects beside them (`tests/fixtures/premap/sbt/<case>/`).
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import premap  # noqa: E402
from premap import sbt  # noqa: E402
import snapshot  # noqa: E402

ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "sbt"
LABEL = "sbt@1.13.1"


def replay(name):
    stored = json.loads((ANSWERS / f"{name}.json").read_text(encoding="utf-8"))
    table = {json.dumps(run["command"], sort_keys=True): run["result"] for run in stored["runs"]}
    return lambda commands: [table[json.dumps(command, sort_keys=True)] for command in commands]


def build(tmp_path, name, sources=(sbt,)):
    project = tmp_path / "proj"
    shutil.copytree(ANSWERS / name, project)
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    return premap.write(manifest, sources=sources, runner=replay(name))


def test_every_project_the_build_loads_is_a_unit_those_a_plugin_adds_too(tmp_path):
    """`core` and `api` come from an AutoPlugin's `extraProjects`: no `lazy val` of build.sbt names them."""
    record = build(tmp_path, "projects-in-code")
    units = {u["name"]: u for u in record["units"] if u["kind"] == "sbt-project"}
    assert {n: (u["root"], u["manifest"]) for n, u in units.items()} == {
        "root": (".", "build.sbt"), "core": ("modules/core", None), "api": ("modules/api", None)}
    assert units["api"]["depends_on"] == ["core"] and units["core"]["depends_on"] == []
    assert all(u["sources"] == [LABEL] for u in units.values())
    [workspace] = record["workspace"]
    assert (workspace["tool"], workspace["root"], workspace["members"]) == ("sbt", ".", ["modules/api", "modules/core"])
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_beside_the_file_readers_the_projects_only_sbt_knows_are_found(tmp_path):
    readers = tuple(s for s in premap.SOURCES if not hasattr(s, "commands"))
    before = build(tmp_path / "a", "projects-in-code", sources=readers)
    after = build(tmp_path / "b", "projects-in-code", sources=(*readers, sbt))
    names = lambda r: {u["name"] for u in r["units"] if u["kind"] == "sbt-project"}  # noqa: E731
    assert {"core", "api"} - names(before) and {"core", "api"} <= names(after)


def test_a_build_that_does_not_load_is_a_gap_and_states_no_unit():
    command = {"tool": "sbt", "argv": ["sh", "-c", sbt.SCRIPT], "cwd": ".", "env": {}, "network": "registries"}
    record = sbt.read(None, [command], [{"returncode": 1, "root": "/work", "stdout": "",
                                         "stderr": "[error] Type error in expression"}])
    assert record["facts"] == {} and record["gaps"][0]["kind"] == "model_failed"


def test_commands_load_each_top_build_with_the_registries_open():
    def commands(files):
        class Inventory:
            pass
        Inventory.files = files

        class Context:
            inventory = Inventory()
        return [(c["cwd"], c["network"], c["argv"][:2]) for c in sbt.commands(Context())]

    assert commands(["build.sbt", "project/build.properties", "tools/build.sbt"]) == [(".", "registries", ["sh", "-c"])]
    assert commands(["a/build.sbt", "b/project/build.properties"]) == [
        ("a", "registries", ["sh", "-c"]), ("b", "registries", ["sh", "-c"])]
