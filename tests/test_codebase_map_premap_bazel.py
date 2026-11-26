"""The Bazel source of the pre-map: `bazel query` and `bazel mod graph` answers, recorded once in a Linux
container, read into units.

The answers are in `tests/fixtures/premap/bazel/<fixture>.json`, captured from the benchmark fixture of the same
name (`benchmarks/project-model/fixtures/`) with Bazel 9.3.1 in `buildpack-deps:noble`.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import premap  # noqa: E402
from premap import bazel  # noqa: E402
import snapshot  # noqa: E402

CORPUS = ROOT / "benchmarks/project-model/fixtures"
ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "bazel"
LABEL = "bazel@9.3.1"


def replay(name, change=None):
    stored = json.loads((ANSWERS / f"{name}.json").read_text(encoding="utf-8"))
    table = {json.dumps(run["command"], sort_keys=True): (change or (lambda c, r: r))(run["command"], run["result"])
             for run in stored["runs"]}
    return lambda commands: [table[json.dumps(command, sort_keys=True)] for command in commands]


def build(tmp_path, name, change=None):
    project = tmp_path / "proj"
    shutil.copytree(CORPUS / name, project, ignore=shutil.ignore_patterns("expected.json"))
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    return premap.write(manifest, sources=(bazel,), runner=replay(name, change))


def by_name(record, kind):
    return {u["name"]: u for u in record["units"] if u["kind"] == kind}


def test_each_rule_is_a_unit_in_its_package_with_its_sources_and_edges(tmp_path):
    record = build(tmp_path, "sys-bazel")
    units = by_name(record, "bazel-target")
    assert set(units) == {"//lib:greet", "//app:app", "//test:greet_test"}
    lib, app, test = units["//lib:greet"], units["//app:app"], units["//test:greet_test"]
    assert (lib["root"], lib["manifest"], lib["source_roots"]) == ("lib", "lib/BUILD", ["lib"])
    assert app["depends_on"] == test["depends_on"] == ["//lib:greet"] and lib["depends_on"] == []
    assert (lib["config"]["rule"], app["config"]["rule"], test["config"]["rule"]) == ("cc_library", "cc_binary",
                                                                                    "cc_test")
    assert lib["config"]["sources"] == ["lib/greet.cc", "lib/greet.h"] and app["config"]["sources"] == ["app/main.cc"]
    assert lib["config"]["build_tags"] == ["GREET_LOUD=1"]
    assert all(u["sources"] == [LABEL] and u["run"]["executes_project_code"] for u in units.values())
    [workspace] = record["workspace"]
    assert workspace["tool"] == "bazel" and workspace["root"] == "." and sorted(workspace["members"]) == [
        "app", "lib", "test"]
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_the_root_module_is_a_unit_without_its_external_modules(tmp_path):
    [module] = by_name(build(tmp_path, "sys-bazel"), "bazel-module").values()
    assert (module["name"], module["root"], module["manifest"]) == ("greeter", ".", "MODULE.bazel")
    assert module["depends_on"] == []


def test_a_failed_query_is_a_gap_and_states_no_target(tmp_path):
    def fail(command, result):
        return {**result, "returncode": 7, "stdout": "", "stderr": "ERROR: no such package '@@rules_cc+//cc'"} \
            if "query" in command["argv"] else result
    record = build(tmp_path, "sys-bazel", fail)
    assert by_name(record, "bazel-target") == {}
    [gap] = [g for g in record["gaps"] if g["kind"] == "model_failed"]
    assert gap["path"] == "." and "rules_cc" in gap["detail"]


def test_commands_run_where_the_workspace_is_declared():
    class Inventory:
        files = ["MODULE.bazel", "lib/BUILD", "third_party/x/WORKSPACE", "app/BUILD.bazel"]

    class Context:
        inventory = Inventory()

    commands = bazel.commands(Context())
    assert {c["cwd"] for c in commands} == {"."} and {c["tool"] for c in commands} == {"bazel"}
    assert {c["network"] for c in commands} == {"registries"}  # Bazel fetches the module graph and the rules
