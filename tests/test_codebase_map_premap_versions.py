"""The language versions of the pre-map: Renovate's packages that are the language or its build tool, the files that
declare the language version as data (Package.swift, .csproj), and Gradle's model of the Java and Kotlin targets.

Renovate's answers are the recorded ones of the corpus (`benchmarks/project-model/results/premap-runs/`), Gradle's
were recorded once in a Linux container (`tests/fixtures/premap/versions/gradle/<fixture>.json`).
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import premap  # noqa: E402
from premap import gradle, project_files, renovate  # noqa: E402
import snapshot  # noqa: E402

CORPUS = ROOT / "benchmarks/project-model/fixtures"
RUNS = ROOT / "benchmarks/project-model/results/premap-runs"
ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "versions"


def recorded(name: str) -> dict:
    own = ANSWERS / f"{name}.json"
    if own.is_file():
        return json.loads(own.read_text(encoding="utf-8"))
    return json.loads(gzip.decompress((RUNS / f"{name}.json.gz").read_bytes()).decode("utf-8"))


def replay(name: str):
    table = {json.dumps(run["command"], sort_keys=True): run["result"] for run in recorded(name)["runs"]}
    return lambda commands: [table[json.dumps(command, sort_keys=True)] for command in commands]


def build(tmp_path, name: str, sources, files: dict | None = None, answers: str | None = None) -> dict:
    project = tmp_path / "proj"
    if files is None:
        own = ANSWERS / name
        shutil.copytree(own if own.is_dir() else CORPUS / name, project, ignore=shutil.ignore_patterns("expected.json"))
    else:
        for rel, text in files.items():
            (project / rel).parent.mkdir(parents=True, exist_ok=True)
            (project / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    return premap.write(manifest, sources=sources, runner=replay(answers or name) if answers or files is None else None)


def toolchains(record: dict, *tools: str) -> list[tuple]:
    return sorted((t["tool"], t.get("version"), t["declared_in"]) for t in record.get("toolchains", [])
                  if t["tool"] in tools)


# ------------------------------------------------------------------ Renovate

def test_the_typescript_a_manifest_declares_is_a_toolchain(tmp_path):
    record = build(tmp_path, "js-vite-react-ts", (renovate,))
    assert toolchains(record, "typescript") == [("typescript", "~5.6.2", "package.json")]
    assert "dependencies" not in record


def test_a_catalog_reference_is_no_version_and_the_catalog_states_it(tmp_path):
    record = build(tmp_path, "js-pnpm-workspace", (renovate,))
    assert toolchains(record, "typescript") == [("typescript", "^5.6.2", "pnpm-workspace.yaml")]


def test_bun_reads_the_same_manifest(tmp_path):
    record = build(tmp_path, "js-bun", (renovate,))
    assert toolchains(record, "typescript") == [("typescript", "^5.6.0", "package.json")]


def test_a_kotlin_gradle_plugin_gives_the_kotlin_version_and_other_plugins_none(tmp_path):
    record = build(tmp_path, "jvm-android-app-lib", (renovate,))
    assert toolchains(record, "kotlin", "com.android.application") == [("kotlin", "2.0.21", "build.gradle.kts")]


def test_the_kotlin_plugins_of_one_catalog_are_one_kotlin_version(tmp_path):
    """KotlinConf's version catalog: six org.jetbrains.kotlin.* plugins share `kotlin`; kotlin-wrappers and
    kotlinx are libraries."""
    record = build(tmp_path, "kotlinconf-catalog", (renovate,))
    assert toolchains(record, "kotlin") == [("kotlin", "2.5.0-RC", "gradle/libs.versions.toml")]


def test_sbt_gives_the_scala_version_and_its_own(tmp_path):
    record = build(tmp_path, "jvm-sbt-two-subprojects", (renovate,))
    assert toolchains(record, "scala", "sbt", "org.typelevel:cats-core") == [
        ("sbt", "1.10.5", "project/build.properties"), ("scala", "3.3.4", "build.sbt")]


# ------------------------------------------------------------- project files

def test_package_swift_declares_its_tools_version_on_the_first_line(tmp_path):
    record = build(tmp_path, "mix-swift-spm", (project_files,))
    assert [t for t in record["toolchains"] if t["tool"] == "swift"] == [
        {"tool": "swift", "version": "5.9", "declared_in": "Package.swift", "line": 1,
         "sources": [premap.label(project_files)]}]


def test_the_tools_version_line_takes_spaces_and_a_line_further_down_is_no_declaration(tmp_path):
    record = build(tmp_path, "swift", (project_files,), files={
        "a/Package.swift": "// swift-tools-version: 6.0\nimport PackageDescription\n",
        "b/Package.swift": "import PackageDescription\n// swift-tools-version:5.9\n"})
    assert toolchains(record, "swift") == [("swift", "6.0", "a/Package.swift")]


def test_the_target_framework_of_directory_build_props(tmp_path):
    record = build(tmp_path, "mix-dotnet-central", (project_files,))
    # the framework a project targets is not the SDK that builds it (`global.json`, tool `dotnet`)
    assert toolchains(record, "dotnet-target", "c#") == [
        ("dotnet-target", "net8.0", "Directory.Build.props#TargetFramework")]


def test_a_csproj_gives_each_target_framework_and_the_language_version(tmp_path):
    csproj = ('<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n    <TargetFrameworks>net8.0;netstandard2.0'
              '</TargetFrameworks>\n    <LangVersion>12</LangVersion>\n  </PropertyGroup>\n</Project>\n')
    computed = ('<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n    <TargetFramework>$(NetCurrent)'
                '</TargetFramework>\n  </PropertyGroup>\n</Project>\n')
    record = build(tmp_path, "csproj", (project_files,), files={"lib/Lib.csproj": csproj, "app/App.csproj": computed})
    assert toolchains(record, "dotnet-target", "c#") == [
        ("c#", "12", "lib/Lib.csproj#LangVersion"), ("dotnet-target", "net8.0", "lib/Lib.csproj#TargetFrameworks"),
        ("dotnet-target", "netstandard2.0", "lib/Lib.csproj#TargetFrameworks")]
    lang = next(t for t in record["toolchains"] if t["tool"] == "c#")
    assert lang["line"] == 4
    [gap] = [g for g in record["gaps"] if g["kind"] == "toolchain_undeclared"]
    assert gap["path"] == "app/App.csproj" and "$(NetCurrent)" in gap["detail"]


# -------------------------------------------------------------------- Gradle

def gradle_build(tmp_path, name: str, sources=(gradle,)) -> dict:
    return build(tmp_path, name, sources, answers=f"gradle/{name}")


def projects(record: dict) -> dict:
    return {u["name"]: u for u in record["units"] if u["kind"] == "gradle-project"}


def test_gradle_runs_once_per_top_build_with_the_registries_open():
    class Context:
        class inventory:  # noqa: N801 - the shape Context gives a source
            files = ["settings.gradle.kts", "app/build.gradle.kts", "buildSrc/build.gradle.kts",
                     "libs/money/settings.gradle.kts", "tools/gen/build.gradle", "web/package.json"]

    [command] = gradle.commands(Context())  # buildSrc, an included build and a nested script are the top's
    assert command["cwd"] == "." and command["network"] == "registries"
    assert command["argv"][:2] == ["sh", "-c"] and command["argv"][-1] == gradle.INIT


def test_the_projects_the_settings_make_by_code_are_the_units(tmp_path):
    """The settings include `modules/*` by a loop that leaves `legacy` out, move `:api` to another folder and
    include a build: the parent `:modules` exists without a build file, `modules/legacy` is no project; `:api`
    uses `:modules:a`, an edge only the configured project states."""
    record = gradle_build(tmp_path, "computed-include")
    units = projects(record)
    assert {n: (u["root"], u["manifest"], u.get("depends_on")) for n, u in units.items()} == {
        ":": (".", None, []), ":modules": ("modules", None, []),
        ":modules:a": ("modules/a", "modules/a/build.gradle.kts", []),
        ":modules:b": ("modules/b", "modules/b/build.gradle.kts", []),
        ":api": ("services/api-v2", "services/api-v2/build.gradle.kts", [":modules:a"]),
        ":tooling": ("tooling", "tooling/build.gradle.kts", [])}
    assert all(u["sources"] == ["gradle@9.9.1"] and u["run"]["executes_project_code"] for u in units.values())
    assert {w["root"]: sorted(w["members"]) for w in record["workspace"] if w["tool"] == "gradle"} == {
        ".": [".", "modules", "modules/a", "modules/b", "services/api-v2"], "tooling": ["tooling"]}
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_the_model_names_the_projects_the_file_reader_found_and_drops_none(tmp_path):
    """Beside the file readers, each project the reader found under a folder keeps one entry, named by Gradle."""
    record = gradle_build(tmp_path, "computed-include",
                          sources=(*[s for s in premap.SOURCES if not hasattr(s, "commands")], gradle))
    by_root = {u["root"]: u["name"] for u in record["units"] if u["kind"] == "gradle-project"}
    assert by_root["modules/a"] == ":modules:a" and by_root["services/api-v2"] == ":api"


def test_the_java_version_a_gradle_build_sets_and_where(tmp_path):
    record = gradle_build(tmp_path, "jvm-gradle-groovy-wrapper")
    assert toolchains(record, "java") == [("java", "17", "build.gradle#java.sourceCompatibility"),
                                          ("java", "17", "build.gradle#java.targetCompatibility")]
    assert all(t["sources"] == ["gradle@9.9.1"] for t in record["toolchains"])


def test_a_toolchain_set_by_kotlin_or_a_convention_plugin_is_stated_per_project(tmp_path):
    assert toolchains(gradle_build(tmp_path / "k", "jvm-kotlin-source-sets"), "java") == [
        ("java", "21", "build.gradle.kts#java.toolchain.languageVersion")]
    assert toolchains(gradle_build(tmp_path / "c", "jvm-gradle-kts-catalog-composite"), "java") == [
        ("java", "17", "libs/money/build.gradle.kts#java.toolchain.languageVersion"),  # an included build
        ("java", "21", "api/build.gradle.kts#java.toolchain.languageVersion"),  # buildSrc's convention plugin
        ("java", "21", "domain/build.gradle.kts#java.toolchain.languageVersion")]


def test_the_kotlin_jvm_target_and_the_release_a_build_sets_and_no_convention(tmp_path):
    """`plain` applies Kotlin and sets nothing: its jvmTarget is a convention, and reading it would look up a JDK."""
    record = gradle_build(tmp_path, "gradle-jvm-target")
    assert toolchains(record, "java") == [("java", "17", "app/build.gradle.kts#kotlin.compilerOptions.jvmTarget"),
                                          ("java", "17", "app/build.gradle.kts#options.release")]


def test_a_failed_configure_keeps_the_projects_and_states_no_target(tmp_path):
    """Klaxon's buildSrc calls `jcenter()`, which Gradle 9 removed: the settings evaluated, the configure failed."""
    project = tmp_path / "proj"
    (project / "buildSrc").mkdir(parents=True)
    (project / "settings.gradle.kts").write_text('rootProject.name = "klaxon"\n', encoding="utf-8")
    (project / "buildSrc/build.gradle.kts").write_text("repositories {\n    jcenter()\n}\n", encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    record = premap.write(manifest, sources=(gradle,), runner=replay("gradle/mix-real-klaxon"))
    assert "toolchains" not in record
    gaps = [g for g in record["gaps"] if g["kind"].startswith("model_")]
    assert [(g["kind"], g["path"]) for g in gaps] == [("model_partial", ".")] and "jcenter" in gaps[0]["detail"]


# ------------------------------------------------------------ CMake and Cargo

def test_the_c_and_cxx_standard_cmake_applies_is_a_toolchain_where_the_target_is_defined(tmp_path):
    """`set(CMAKE_C_STANDARD 90)` and `set(CMAKE_CXX_STANDARD 17)` at the top reach each target's compile group as
    `languageStandard`; CMake's backtrace names the CMakeLists.txt that defines the target."""
    from premap import cmake
    record = build(tmp_path, "sys-c-macro-annotations", (cmake,), answers="../cmake/sys-c-macro-annotations")
    assert [(t["tool"], t["version"], t["declared_in"], t["line"]) for t in record["toolchains"]
            if t["tool"] in ("c", "c++")] == [("c", "90", "c/CMakeLists.txt#C_STANDARD", 1),
                                              ("c++", "17", "cpp/CMakeLists.txt#CXX_STANDARD", 1)]


def test_the_rust_edition_a_manifest_writes_is_a_toolchain_and_an_inherited_one_is_the_workspace_s(tmp_path):
    from premap import cargo
    record = build(tmp_path, "sys-rust-workspace", (cargo,))
    assert toolchains(record, "rust-edition") == [("rust-edition", "2021", "Cargo.toml"),
                                                  ("rust-edition", "2021", "crates/experimental/Cargo.toml")]
