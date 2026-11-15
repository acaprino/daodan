"""The Meson source of the pre-map: `meson introspect` answers, recorded once in a Linux container, read into units.

The answers are in `tests/fixtures/premap/meson/<fixture>.json`, captured from the benchmark fixture of the same
name (`benchmarks/project-model/fixtures/`) with Meson 1.12.1 in `buildpack-deps:noble`.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import premap  # noqa: E402
from premap import meson  # noqa: E402
import snapshot  # noqa: E402

CORPUS = ROOT / "benchmarks/project-model/fixtures"
ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "meson"
LABEL = "meson@1.12.1"


def replay(name, change=None):
    stored = json.loads((ANSWERS / f"{name}.json").read_text(encoding="utf-8"))
    table = {json.dumps(run["command"], sort_keys=True): (change or (lambda c, r: r))(run["command"], run["result"])
             for run in stored["runs"]}
    return lambda commands: [table[json.dumps(command, sort_keys=True)] for command in commands]


def build(tmp_path, name, change=None):
    project = tmp_path / "proj"
    own = ANSWERS / name  # a project written for this source, beside its answers
    shutil.copytree(own if own.is_dir() else CORPUS / name, project, ignore=shutil.ignore_patterns("expected.json"))
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    return premap.write(manifest, sources=(meson,), runner=replay(name, change))


def targets(record):
    return {u["name"]: u for u in record["units"] if u["kind"] == "meson-target"}


def test_each_configured_target_is_a_unit_with_its_build_file_sources_and_links(tmp_path):
    record = build(tmp_path, "sys-meson")
    units = targets(record)
    assert set(units) == {"imgconv", "img", "roundtrip"}
    app, lib, test = units["imgconv"], units["img"], units["roundtrip"]
    assert (app["root"], app["manifest"], app["source_roots"]) == (".", "meson.build", ["src"])
    assert (lib["root"], lib["manifest"], lib["source_roots"]) == ("libimg", "libimg/meson.build", ["libimg"])
    assert (test["root"], test["manifest"]) == ("tests", "tests/meson.build")
    assert app["depends_on"] == test["depends_on"] == ["img"] and lib["depends_on"] == []
    assert app["config"]["type"] == "executable" and lib["config"]["type"] == "static library"
    assert app["config"]["sources"] == ["src/main.c"] and lib["config"]["sources"] == ["libimg/img.c"]
    # what the compiler is given, Meson's own folders of each target included (`implicit_include_directories`)
    assert lib["config"]["include_dirs"] == ["libimg", "libimg/include"]
    assert app["config"]["include_dirs"] == [".", "libimg/include"]
    assert lib["config"]["build_tags"] == ["IMG_MAX_SIDE=4096", "_FILE_OFFSET_BITS=64"]
    assert all(u["sources"] == [LABEL] and u["run"]["executes_project_code"] for u in units.values())
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_a_failed_setup_falls_back_to_the_source_tree_answer_with_a_gap(tmp_path):
    """`meson setup` fails (a dependency it cannot find, a wrap it may not download): the targets come from
    `meson introspect meson.build`, which reads the build files without configuring, and a gap says so."""
    def fail_setup(command, result):
        setup = "setup" in " ".join(command["argv"])
        return {**result, "returncode": 1, "stdout": "", "stderr": "ERROR: Dependency \"zlib\" not found"} \
            if setup else result
    record = build(tmp_path, "sys-meson", fail_setup)
    units = targets(record)
    assert set(units) == {"imgconv", "img", "roundtrip"}
    assert units["img"]["root"] == "libimg" and units["img"]["config"]["sources"] == ["libimg/img.c"]
    [gap] = [g for g in record["gaps"] if g["kind"] == "model_partial"]
    assert gap["path"] == "." and "zlib" in gap["detail"]


def test_commands_configure_each_top_meson_folder_with_the_network_closed():
    class Inventory:
        files = ["meson.build", "lib/meson.build", "subprojects/zlib.wrap", "src/a.c"]

    class Context:
        inventory = Inventory()

    commands = meson.commands(Context())
    assert {c["cwd"] for c in commands} == {"."} and {c["network"] for c in commands} == {"none"}
    assert {c["tool"] for c in commands} == {"meson"} and len(commands) == 2


def test_each_cross_file_is_configured_with_the_compiler_it_names_and_its_targets_say_so(tmp_path):
    """`firmware` exists only when cross compiling; the Arm cross file's compiler comes from the preparation, the
    RISC-V one's from nowhere: its configure is a gap naming the compiler, and the host configure still counts."""
    record = build(tmp_path, "cross-file")
    units = targets(record)
    assert set(units) == {"driver", "host_tests", "firmware"}
    assert units["firmware"]["depends_on"] == ["driver"]
    assert units["firmware"]["config"]["cross_files"] == ["cross/arm-none-eabi.txt"]
    assert units["driver"]["config"]["cross_files"] == ["cross/arm-none-eabi.txt"]
    assert "cross_files" not in units["host_tests"]["config"]
    [gap] = [g for g in record["gaps"] if g["kind"] == "model_failed"]
    assert gap["cross_file"] == "cross/riscv.ini" and "riscv64-unknown-elf-gcc" in gap["detail"]


def test_commands_configure_each_cross_file_with_the_needs_of_its_compilers():
    texts = {"meson.build": "project('a', 'c')\n",
             "cross/arm.txt": "[binaries]\nc = 'arm-none-eabi-gcc'\n[host_machine]\nsystem = 'none'\n",
             "native.ini": "[binaries]\nc = 'gcc'\n", "doc/notes.txt": "x"}

    class Inventory:
        files = list(texts)
        headers = dict.fromkeys(texts)
        text = staticmethod(texts.__getitem__)

    class Context:
        inventory = Inventory()

    commands = meson.commands(Context())
    cross = [c for c in commands if "--cross-file" in c["argv"][2]]
    assert [(c["argv"][-1], c.get("needs")) for c in cross] == [("cross/arm.txt", ["arm-none-eabi"])]
