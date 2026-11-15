"""The Maven source of the pre-map: `help:effective-pom` answers, recorded once in a Linux container, read into units.

The answers are in `tests/fixtures/premap/maven/<case>.json`, captured with Maven 3.10.0 on Temurin 17 from the
project beside them (`tests/fixtures/premap/maven/<case>/`).
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import premap  # noqa: E402
from premap import maven  # noqa: E402
import snapshot  # noqa: E402

ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "maven"
LABEL = "maven@3.10.0"


def replay(name):
    stored = json.loads((ANSWERS / f"{name}.json").read_text(encoding="utf-8"))
    table = {json.dumps(run["command"], sort_keys=True): run["result"] for run in stored["runs"]}
    return lambda commands: [table[json.dumps(command, sort_keys=True)] for command in commands]


def build(tmp_path, name, sources=(maven,)):
    project = tmp_path / "proj"
    shutil.copytree(ANSWERS / name, project)
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    return premap.write(manifest, sources=sources, runner=replay(name))


def test_the_reactor_holds_the_module_a_default_profile_adds_and_not_the_others(tmp_path):
    """`extras` is a module only through a profile active by default; `legacy` only with `-Dlegacy`."""
    record = build(tmp_path, "profile-module")
    units = {u["name"]: u for u in record["units"] if u["kind"] == "maven-module"}
    assert {n: (u["root"], u["manifest"]) for n, u in units.items()} == {
        "com.example:shop": (".", "pom.xml"), "com.example:core": ("core", "core/pom.xml"),
        "com.example:extras": ("extras", "extras/pom.xml")}
    assert units["com.example:extras"]["depends_on"] == ["com.example:core"]
    assert units["com.example:core"]["depends_on"] == []
    assert all(u["sources"] == [LABEL] and u["run"]["executes_project_code"] for u in units.values())
    [workspace] = record["workspace"]
    assert (workspace["tool"], workspace["root"], workspace["members"]) == ("maven", ".", ["core", "extras"])
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_beside_the_file_reader_the_workspace_takes_the_profile_module(tmp_path):
    readers = tuple(s for s in premap.SOURCES if not hasattr(s, "commands"))
    record = build(tmp_path, "profile-module", sources=(*readers, maven))
    [workspace] = [w for w in record["workspace"] if w["tool"] == "maven"]
    assert workspace["members"] == ["core", "extras"] and LABEL in workspace["sources"]


def test_commands_evaluate_each_top_reactor_with_the_registries_open():
    class Inventory:
        files = ["pom.xml", "core/pom.xml", "tools/gen/pom.xml"]

    class Context:
        inventory = Inventory()

    commands = maven.commands(Context())
    assert [c["cwd"] for c in commands] == ["."] and commands[0]["network"] == "registries"
