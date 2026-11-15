"""The GNU Make source of the pre-map: `make -pn` answers, recorded once in a Linux container, read into units.

The answers are in `tests/fixtures/premap/make/<case>.json`, captured with GNU Make 4.3 in `buildpack-deps:noble`
from the benchmark fixture of the same name (`benchmarks/project-model/fixtures/`) or from the project beside
the answers (`tests/fixtures/premap/make/<case>/`).
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import premap  # noqa: E402
from premap import make  # noqa: E402
import snapshot  # noqa: E402
import source_files  # noqa: E402

CORPUS = ROOT / "benchmarks/project-model/fixtures"
ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "make"
LABEL = "make@4.3"


def replay(name):
    stored = json.loads((ANSWERS / f"{name}.json").read_text(encoding="utf-8"))
    table = {json.dumps(run["command"], sort_keys=True): run["result"] for run in stored["runs"]}
    return lambda commands: [table[json.dumps(command, sort_keys=True)] for command in commands]


def build(tmp_path, name):
    project = tmp_path / "proj"
    own = ANSWERS / name
    shutil.copytree(own if own.is_dir() else CORPUS / name, project, ignore=shutil.ignore_patterns("expected.json"))
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    return premap.write(manifest, sources=(make,), runner=replay(name))


def targets(record):
    return {u["name"]: u for u in record["units"] if u["kind"] == "make-target"}


def test_each_file_a_rule_writes_is_a_unit_with_its_sources_and_edges(tmp_path):
    record = build(tmp_path, "sys-make-plain")
    units = targets(record)
    assert set(units) == {"build/mini", "build/libmini.a"}
    app, lib = units["build/mini"], units["build/libmini.a"]
    assert (app["root"], app["manifest"], app["depends_on"]) == (".", "Makefile", ["build/libmini.a"])
    assert lib["depends_on"] == [] and lib["source_roots"] == ["include", "lib"]
    assert lib["config"]["sources"] == ["include/mini.h", "lib/log.c", "lib/vec.c"]
    assert app["config"]["sources"] == ["app/main.c"]
    assert all(u["sources"] == [LABEL] and u["run"]["executes_project_code"] for u in units.values())
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_actions_and_steps_are_no_units_and_other_dialects_are_gaps(tmp_path):
    """`prog` links through GNU Make's built-in rule; `all`, `test` and `sublib` write no file of their name, the
    objects are steps of `prog`; `sub/` is its own folder's unit, the recursive make's database left aside;
    `win32/Makefile.msc` is nmake's."""
    record = build(tmp_path, "dialects")
    units = targets(record)
    assert {n: (u["root"], u["config"]["sources"]) for n, u in units.items()} == {
        "prog": (".", ["prog.c", "util.c"]),
        "libsub.a": ("sub", ["sub/sub.c"])}
    [gap] = [g for g in record["gaps"] if g["kind"] == "not_executed"]
    assert gap["path"] == "win32/Makefile.msc" and gap["source"] == LABEL


def test_commands_run_a_dry_run_in_each_folder_with_a_makefile():
    class Inventory:
        files = ["Makefile", "lib/GNUmakefile", "win32/Makefile.msc", "doc/rules.mk"]

    class Context:
        inventory = Inventory()

    commands = make.commands(Context())
    assert [c["cwd"] for c in commands] == [".", "lib"] and {c["network"] for c in commands} == {"none"}
    assert commands[0]["argv"][:2] == ["make", "-pnk"]


def test_the_snapshot_records_every_makefile_gnu_make_reads_and_the_other_dialects():
    for name in ("Makefile", "makefile", "GNUmakefile", "Makefile.msc", "makefile.wat", "nmake.mak", "descrip.mms",
                 "Makefile.in", "Makefile.am"):
        assert source_files.is_build_file(name), name
    assert not source_files.is_build_file("make.py") and not source_files.is_build_file("rules.mk")
