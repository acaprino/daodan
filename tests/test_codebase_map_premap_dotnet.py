"""The .NET source of the pre-map: MSBuild evaluations, recorded once in a Linux container, read into units.

The answers are in `tests/fixtures/premap/dotnet/<case>.json`, captured with the .NET SDK 10.0.404 in
`buildpack-deps:noble` from the project beside them (`tests/fixtures/premap/dotnet/<case>/`).
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import premap  # noqa: E402
from premap import dotnet  # noqa: E402
import snapshot  # noqa: E402

ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "dotnet"
LABEL = "dotnet@10.0.404"


def replay(name):
    stored = json.loads((ANSWERS / f"{name}.json").read_text(encoding="utf-8"))
    table = {json.dumps(run["command"], sort_keys=True): run["result"] for run in stored["runs"]}
    return lambda commands: [table[json.dumps(command, sort_keys=True)] for command in commands]


def build(tmp_path, name, sources=(dotnet,)):
    project = tmp_path / "proj"
    shutil.copytree(ANSWERS / name, project)
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    return premap.write(manifest, sources=sources, runner=replay(name))


def test_a_reference_through_a_property_of_directory_build_props_is_an_edge(tmp_path):
    """`App` references `$(LibDir)Lib.csproj`, `LibDir` set in Directory.Build.props: only MSBuild expands it."""
    record = build(tmp_path, "property-reference")
    units = {u["name"]: u for u in record["units"] if u["kind"] == "dotnet-project"}
    assert {n: (u["root"], u["manifest"]) for n, u in units.items()} == {
        "App": ("src/App", "src/App/App.csproj"), "Lib": ("src/Lib", "src/Lib/Lib.csproj")}
    assert units["App"]["depends_on"] == ["Lib"] and units["Lib"]["depends_on"] == []
    assert units["App"]["source_roots"] == ["src/App"] and units["Lib"]["source_roots"] == ["src/Lib"]
    assert units["App"]["config"] == {"type": "Exe", "target_frameworks": ["net8.0"]}
    assert units["Lib"]["config"] == {"type": "Library", "target_frameworks": ["net8.0"]}
    assert all(u["sources"] == [LABEL] and u["run"]["executes_project_code"] for u in units.values())
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_beside_the_file_readers_the_edge_joins_the_reader_unit(tmp_path):
    readers = tuple(s for s in premap.SOURCES if not hasattr(s, "commands"))
    record = build(tmp_path, "property-reference", sources=(*readers, dotnet))
    [app] = [u for u in record["units"] if u["kind"] == "dotnet-project" and u["root"] == "src/App"]
    assert app["depends_on"] == ["Lib"] and LABEL in app["sources"]


def test_commands_evaluate_each_project_file_offline():
    class Inventory:
        files = ["Shop.sln", "src/App/App.csproj", "src/Fs/Fs.fsproj", "Directory.Build.props"]

    class Context:
        inventory = Inventory()

    commands = dotnet.commands(Context())
    assert [(c["cwd"], c["argv"][2]) for c in commands] == [("src/App", "App.csproj"), ("src/Fs", "Fs.fsproj")]
    assert {c["network"] for c in commands} == {"none"}


def test_the_feeds_a_nuget_config_declares_are_registries_of_the_projects_below_it(tmp_path):
    """NuGet reads the nuget.config of a project's folder and of each folder above it: their package sources, a
    `<clear />` dropping the ones above, a disabled source left out, a folder source no host."""
    project = tmp_path / "proj"
    shutil.copytree(ANSWERS / "property-reference", project)
    (project / "nuget.config").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<configuration>\n  <packageSources>\n'
        '    <add key="corp" value="https://user:token@nuget.corp.example/v3/index.json" />\n'
        '    <add key="local" value="./packages" />\n    <add key="off" value="https://off.example/v3/index.json" />\n'
        '  </packageSources>\n  <disabledPackageSources>\n    <add key="off" value="true" />\n'
        '  </disabledPackageSources>\n</configuration>\n', encoding="utf-8")
    (project / "src/Lib/NuGet.Config").write_text(
        '<configuration><packageSources><clear /><add key="lib" value="https://lib.example/nuget" />'
        '</packageSources></configuration>\n', encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    record = premap.write(manifest, sources=(dotnet,), runner=replay("property-reference"))
    units = {u["name"]: u for u in record["units"] if u["kind"] == "dotnet-project"}
    assert units["App"]["registries"] == ["https://nuget.corp.example"]
    assert units["Lib"]["registries"] == ["https://lib.example"]
