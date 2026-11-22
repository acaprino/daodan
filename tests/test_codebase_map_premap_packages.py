"""Task 2: Step 1 `packages` facet in `premap.json` across static readers and container model outputs."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import premap  # noqa: E402
import modules  # noqa: E402
from pipeline import Context, Scan, Stack, events  # noqa: E402
from premap import dotnet, gradle, jvm_files, maven, module_graph, project_files, renovate, requirements  # noqa: E402
import snapshot  # noqa: E402
import technologies  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402


def test_scan_and_stack_resolve_a_dependency_at_its_declaring_package(tmp_path):
    files = {
        "package.json": '{"name":"root","workspaces":["packages/**/client"]}',
        "packages/client/package.json": '{"name":"direct"}',
        "packages/team/client/package.json": '{"name":"nested"}',
        "a/package.json": '{"name":"worker","dependencies":{"left":"file:../l"}}',
        "b/package.json": '{"name":"worker","dependencies":{"right":"file:../r"}}',
        "l/package.json": '{"name":"left"}',
        "r/package.json": '{"name":"right"}',
        "samples/react/package.json": '{"name":"@sample/widget"}',
        "web/package.json": '{"name":"web","dependencies":{"react":"^18"}}',
        "packages/sdk/pyproject.toml": '[project]\nname="sentry_sdk"\n',
        "separate/pyproject.toml": '[project]\nname="separate"\ndependencies=["sentry-sdk"]\n'
                                  '[tool.uv.sources]\nsentry-sdk={workspace=true}\n',
        "app/pyproject.toml": '[project]\nname="remote"\ndependencies=["sentry-sdk>=2"]\n'
                              '[tool.uv.sources]\nsentry-sdk={index="public"}\n'
                              '[[tool.uv.index]]\nname="public"\nurl="https://pypi.org/simple"\n',
    }
    project = tmp_path / "project"
    for rel, text in files.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    context = Context(manifest, events.Bus(), fast_scan=True)
    graph = modules.load_graph(Path(Scan.run(context)["graph"]))
    record = json.loads(Path(Stack.run(context)["path"]).read_text(encoding="utf-8"))
    edges = [(e["kind"], e["source"], e["target"]) for e in graph["edges"]]
    assert {(src, dst) for kind, src, dst in edges if kind == "declares"} == {
        ("worker@a", "left"), ("worker@b", "right")}
    assert {dst for kind, src, dst in edges if src == "root" and kind == "contains"} == {"direct", "nested"}
    libs = {unit["id"]: {lib["name"] for lib in unit["libraries"]} for unit in record["units"]}
    assert libs["web"] == {"react"}
    assert libs["remote"] == {"sentry-sdk"}
    assert not libs["worker@a"] and not libs["worker@b"]


def _versions(tmp_path, files, source) -> dict:
    """(ecosystem, name, declared file) -> the `version` one source states for that package, None for none."""
    project = tmp_path / "proj"
    for rel, text in files.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    with open_snapshot(manifest) as store:
        result = source.run(premap.Context(manifest, store)) or {}
    return {(p["ecosystem"], p["name"], p["declared_in"].split("#", 1)[0]): p.get("version")
            for p in (result.get("facts") or {}).get("packages") or []}


@pytest.mark.parametrize("source", ['workspace = true', 'path = "../sdk"'])
def test_local_python_distribution_is_internal_only_for_its_declaring_consumer(tmp_path, source):
    project = tmp_path / "project"
    local_manifest = "packages/app/pyproject.toml"
    external_manifest = "remote/requirements.txt"
    files = {
        "pyproject.toml": '[tool.uv.workspace]\nmembers = ["packages/*"]\n',
        local_manifest: '[project]\nname = "app"\ndependencies = ["sentry-sdk"]\n'
                        f'[tool.uv.sources]\nsentry-sdk = {{ {source} }}\n',
        "packages/sdk/pyproject.toml": '[project]\nname = "sentry_sdk"\n',
        "remote/pyproject.toml": '[project]\nname = "remote"\ndependencies = ["sentry-sdk"]\n'
                                 '[tool.uv.sources]\nsentry-sdk = { index = "public" }\n',
        external_manifest: 'sentry-sdk>=2\n',
        "web/package.json": '{"name": "web", "dependencies": {"sentry_sdk": "1"}}',
    }
    for rel, body in files.items():
        path = project / rel
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(body, encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    report = {"repositories": {"local": {"packageFiles": {"pep621": [
        {"packageFile": local_manifest, "deps": [{"depName": "sentry-sdk", "currentValue": "*"}]}]}}}}
    facts = premap.write(manifest, sources=(module_graph, requirements, renovate),
                         runner=lambda commands: [{"returncode": 0, "stdout": json.dumps(report), "stderr": ""}])
    assert not any(item["state"] == "failed" for item in facts["sources"])
    assert any(unit["name"] == "app" and "sentry_sdk" in unit["depends_on"] for unit in facts["units"])
    assert {p["declared_in"].split("#")[0] for p in facts["packages"] if p["ecosystem"] == "pypi"} == {
        external_manifest, "remote/pyproject.toml"}
    assert not any(p["declared_in"].split("#")[0] == local_manifest for p in module_graph.package_facts(manifest))
    stack = technologies.ensure(manifest, facts=facts)
    units = {m["name"]: m for m in stack["units"]}
    assert "sentry" not in units["app"]["services"] and not units["app"]["libraries"]
    assert "sentry" in units["remote"]["services"]
    assert [lib["name"] for lib in units["web"]["libraries"]] == ["sentry_sdk"]


def test_module_graph_packages_carry_the_version_each_manifest_writes(tmp_path):
    files = {
        "web/package.json": '{"name": "web", "dependencies": {"react": "^18.2.0", "lodash": "catalog:",'
                            ' "left": "github:acme/left"}, "devDependencies": {"vitest": "1.6.0"}}',
        "deno/deno.json": '{"name": "@acme/deno", "imports": {"preact": "npm:preact@^10.19.0",'
                          ' "assert": "jsr:@std/assert@^1.0.0", "oak": "https://deno.land/x/oak@v12/mod.ts"}}',
        "py/pyproject.toml": '[project]\nname = "py"\ndependencies = ["requests>=2.31,<3", "rich",'
                             ' "httpx[http2] (>=0.27) ; python_version >= \'3.9\'", "wheel @ https://x.org/w.whl"]\n'
                             '[tool.poetry.dependencies]\npython = "^3.11"\nclick = "^8.1"\n'
                             'pydantic = { version = "^2.0", extras = ["email"] }\n',
        "cfg/setup.cfg": "[metadata]\nname = cfg\n[options]\ninstall_requires =\n    attrs>=23\n",
        "rs/Cargo.toml": '[package]\nname = "rs"\n[dependencies]\nserde = "1.0"\n'
                         'tokio = { version = "1", features = ["full"] }\nshared = { workspace = true }\n',
        "go/go.mod": "module example.com/go\n\ngo 1.22\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.1\n)\n",
        "php/composer.json": '{"name": "acme/php", "require": {"php": ">=8.1", "symfony/console": "^7.0"}}',
        "dart/pubspec.yaml": "name: dart\ndependencies:\n  dio: ^5.0.0\n  http:\n    hosted: https://pub.dev\n"
                             "    version: ^1.2.0\n  local:\n    path: ../local\n",
        "rb/Gemfile": 'source "https://rubygems.org"\ngem "rails", "~> 7.1"\ngem "puma", ">= 6", "< 7"\ngem "pry"\n',
        "gem/acme.gemspec": 'Gem::Specification.new do |s|\n  s.name = "acme"\n  s.add_dependency "thor", "~> 1.3"\nend\n',
        "ex/mix.exs": 'defmodule Ex.MixProject do\n  def project, do: [app: :ex, deps: deps()]\n'
                      '  defp deps, do: [{:phoenix, "~> 1.7.0"}, {:jason, ">= 0.0.0", only: :test}]\nend\n',
        "swift/Package.swift": '// swift-tools-version:5.9\nimport PackageDescription\nlet package = Package(name: "sw",'
                               ' dependencies: [.package(url: "https://github.com/apple/swift-nio.git", from: "2.62.0")])\n',
        "jvm/pom.xml": '<project xmlns="http://maven.apache.org/POM/4.0.0"><groupId>com.acme</groupId>'
                       "<artifactId>jvm</artifactId><properties><jackson.version>2.17.0</jackson.version></properties>"
                       "<dependencies>"
                       "<dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId>"
                       "<version>${jackson.version}</version></dependency>"
                       "<dependency><groupId>com.google.guava</groupId><artifactId>guava</artifactId>"
                       "<version>33.0.0-jre</version></dependency>"
                       "<dependency><groupId>org.slf4j</groupId><artifactId>slf4j-api</artifactId>"
                       "<version>${slf4j.version}</version></dependency>"
                       "<dependency><groupId>org.springframework</groupId><artifactId>spring-web</artifactId></dependency>"
                       "</dependencies></project>",
        "cs/App.csproj": '<Project Sdk="Microsoft.NET.Sdk"><ItemGroup>'
                         '<PackageReference Include="Serilog" Version="3.1.1" />'
                         '<PackageReference Include="Polly"><Version>8.2.0</Version></PackageReference>'
                         '<PackageReference Include="Dapper" Version="$(DapperVersion)" />'
                         '<PackageReference Include="xunit" /></ItemGroup></Project>',
    }
    got = _versions(tmp_path, files, module_graph)
    assert {key: version for key, version in got.items() if version} == {
        ("npm", "react", "web/package.json"): "^18.2.0",
        ("npm", "vitest", "web/package.json"): "1.6.0",
        ("npm", "preact", "deno/deno.json"): "^10.19.0",
        ("npm", "assert", "deno/deno.json"): "^1.0.0",
        ("pypi", "requests", "py/pyproject.toml"): ">=2.31,<3",
        ("pypi", "httpx", "py/pyproject.toml"): ">=0.27",
        ("pypi", "click", "py/pyproject.toml"): "^8.1",
        ("pypi", "pydantic", "py/pyproject.toml"): "^2.0",
        ("pypi", "attrs", "cfg/setup.cfg"): ">=23",
        ("crates", "serde", "rs/Cargo.toml"): "1.0",
        ("crates", "tokio", "rs/Cargo.toml"): "1",
        ("go", "github.com/gin-gonic/gin", "go/go.mod"): "v1.9.1",
        ("composer", "symfony/console", "php/composer.json"): "^7.0",
        ("pub", "dio", "dart/pubspec.yaml"): "^5.0.0",
        ("pub", "http", "dart/pubspec.yaml"): "^1.2.0",
        ("rubygems", "rails", "rb/Gemfile"): "~> 7.1",
        ("rubygems", "puma", "rb/Gemfile"): ">= 6, < 7",
        ("rubygems", "thor", "gem/acme.gemspec"): "~> 1.3",
        ("hex", "phoenix", "ex/mix.exs"): "~> 1.7.0",
        ("hex", "jason", "ex/mix.exs"): ">= 0.0.0",
        ("swiftpm", "swift-nio", "swift/Package.swift"): 'from: "2.62.0"',
        ("maven", "com.fasterxml.jackson.core:jackson-databind", "jvm/pom.xml"): "2.17.0",
        ("maven", "com.google.guava:guava", "jvm/pom.xml"): "33.0.0-jre",
        ("nuget", "Serilog", "cs/App.csproj"): "3.1.1",
        ("nuget", "Polly", "cs/App.csproj"): "8.2.0",
    }
    for absent in [("npm", "lodash", "web/package.json"), ("npm", "left", "web/package.json"),
                   ("npm", "oak", "deno/deno.json"), ("pypi", "rich", "py/pyproject.toml"),
                   ("pypi", "wheel", "py/pyproject.toml"), ("crates", "shared", "rs/Cargo.toml"),
                   ("rubygems", "pry", "rb/Gemfile"), ("maven", "org.slf4j:slf4j-api", "jvm/pom.xml"),
                   ("maven", "org.springframework:spring-web", "jvm/pom.xml"), ("nuget", "Dapper", "cs/App.csproj"),
                   ("nuget", "xunit", "cs/App.csproj")]:
        assert absent in got and got[absent] is None, absent


def test_requirements_files_carry_each_line_s_specifier(tmp_path):
    files = {"requirements.txt": "fastapi>=0.115,<1\nuvicorn[standard] == 0.30.1 ; python_version >= '3.9'\n"
                                 "httpx==0.27.0 --hash=sha256:abc\nanyio==4.4.0 \\\n    --hash=sha256:def\n"
                                 "rich\npkg @ https://x.org/pkg.whl\n-r dev.txt\n",
             "dev.txt": "pytest~=8.0  # tests\n"}
    got = _versions(tmp_path, files, requirements)
    assert got == {("pypi", "fastapi", "requirements.txt"): ">=0.115,<1",
                   ("pypi", "uvicorn", "requirements.txt"): "== 0.30.1",
                   ("pypi", "httpx", "requirements.txt"): "==0.27.0",
                   ("pypi", "anyio", "requirements.txt"): "==4.4.0",
                   ("pypi", "rich", "requirements.txt"): None,
                   ("pypi", "pkg", "requirements.txt"): None,
                   ("pypi", "pytest", "dev.txt"): "~=8.0"}


def test_jvm_files_carry_pom_and_gradle_versions_and_the_catalog_s(tmp_path):
    files = {
        "pom.xml": '<project xmlns="http://maven.apache.org/POM/4.0.0">'
                   "<parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId>"
                   "<version>3.2.0</version></parent><groupId>com.acme</groupId><artifactId>api</artifactId>"
                   "<properties><jackson.version>2.17.0</jackson.version></properties><dependencies>"
                   "<dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId>"
                   "<version>${jackson.version}</version></dependency>"
                   "<dependency><groupId>org.slf4j</groupId><artifactId>slf4j-api</artifactId>"
                   "<version>${slf4j.version}</version></dependency>"
                   "<dependency><groupId>org.springframework</groupId><artifactId>spring-web</artifactId></dependency>"
                   "</dependencies><build><plugins><plugin><artifactId>maven-compiler-plugin</artifactId>"
                   "<version>3.13.0</version></plugin></plugins></build></project>\n",
        "g/settings.gradle.kts": 'rootProject.name = "g"\n',
        "g/gradle/libs.versions.toml": (
            '[versions]\nktor = "3.0.0"\n[libraries]\n'
            'ktor-core = { module = "io.ktor:ktor-server-core", version.ref = "ktor" }\n'
            'junit = { group = "org.junit.jupiter", name = "junit-jupiter", version = "5.11.0" }\n'
            'slf4j = { module = "org.slf4j:slf4j-api" }\n'
            'strict = { module = "a.b:c", version = { strictly = "1.0" } }\n'
            '[plugins]\nspring = { id = "org.springframework.boot", version = "3.4.0" }\n'),
        "g/build.gradle.kts": (
            'plugins {\n  id("org.springframework.boot") version "3.4.0"\n  kotlin("plugin.serialization") version "2.0.0"\n'
            '  id("io.spring.dependency-management")\n}\n'
            'dependencies {\n  implementation("org.junit.jupiter:junit-jupiter:5.11.0")\n'
            '  implementation("com.squareup.okhttp3:okhttp")\n  implementation("io.x:y:$yVersion")\n'
            '  implementation(libs.ktor.core)\n}\n'),
        "h/settings.gradle": "rootProject.name = 'h'\n",
        "h/build.gradle": "plugins {\n  id 'org.flywaydb.flyway' version '10.0.0'\n}\n",
    }
    got = _versions(tmp_path, files, jvm_files)
    toml, kts = "g/gradle/libs.versions.toml", "g/build.gradle.kts"
    assert got == {
        ("maven", "org.springframework.boot:spring-boot-starter-parent", "pom.xml"): "3.2.0",
        ("maven", "com.fasterxml.jackson.core:jackson-databind", "pom.xml"): "2.17.0",
        ("maven", "org.slf4j:slf4j-api", "pom.xml"): None,
        ("maven", "org.springframework:spring-web", "pom.xml"): None,
        ("maven", "org.apache.maven.plugins:maven-compiler-plugin", "pom.xml"): "3.13.0",
        ("maven", "io.ktor:ktor-server-core", toml): "3.0.0",
        ("maven", "org.junit.jupiter:junit-jupiter", toml): "5.11.0",
        ("maven", "org.slf4j:slf4j-api", toml): None,
        ("maven", "a.b:c", toml): None,
        ("maven", "org.springframework.boot", toml): "3.4.0",
        ("maven", "org.springframework.boot", kts): "3.4.0",
        ("maven", "org.jetbrains.kotlin.plugin.serialization", kts): "2.0.0",
        ("maven", "io.spring.dependency-management", kts): None,
        ("maven", "org.junit.jupiter:junit-jupiter", kts): "5.11.0",
        ("maven", "com.squareup.okhttp3:okhttp", kts): None,
        ("maven", "io.x:y", kts): None,
        ("maven", "io.ktor:ktor-server-core", kts): "3.0.0",
        ("maven", "org.flywaydb.flyway", "h/build.gradle"): "10.0.0",
    }


def test_project_files_carry_the_project_s_version_or_the_central_one(tmp_path):
    files = {
        "Directory.Packages.props": '<Project><ItemGroup><PackageVersion Include="xunit" Version="2.9.0" />'
                                    '<PackageVersion Include="Polly" Version="8.2.0" /></ItemGroup></Project>',
        "src/App/App.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web"><ItemGroup>'
                              '<PackageReference Include="Serilog" Version="3.1.1" />'
                              '<PackageReference Include="Dapper"><Version>2.1.35</Version></PackageReference>'
                              '<PackageReference Include="xunit" />'
                              '<PackageReference Include="Polly" VersionOverride="8.4.0" />'
                              '<PackageReference Include="Npgsql" Version="$(NpgsqlVersion)" />'
                              '<PackageReference Include="Humanizer" /></ItemGroup></Project>',
        "other/Other.csproj": '<Project Sdk="Microsoft.NET.Sdk"><ItemGroup><PackageReference Include="xunit" />'
                              "</ItemGroup></Project>",
        "other/Directory.Packages.props": '<Project><ItemGroup><PackageVersion Include="xunit" Version="2.8.0" />'
                                          "</ItemGroup></Project>",
    }
    got = _versions(tmp_path, files, project_files)
    app = "src/App/App.csproj"
    assert got == {
        ("nuget", "xunit", "Directory.Packages.props"): "2.9.0",
        ("nuget", "Polly", "Directory.Packages.props"): "8.2.0",
        ("nuget", "Microsoft.AspNetCore.App", app): None,
        ("nuget", "Serilog", app): "3.1.1",
        ("nuget", "Dapper", app): "2.1.35",
        ("nuget", "xunit", app): "2.9.0",
        ("nuget", "Polly", app): "8.4.0",
        ("nuget", "Npgsql", app): None,
        ("nuget", "Humanizer", app): None,
        ("nuget", "xunit", "other/Directory.Packages.props"): "2.8.0",
        ("nuget", "xunit", "other/Other.csproj"): "2.8.0",  # the nearest Directory.Packages.props above the project
    }


def test_readers_collect_declared_packages_across_jvm_dotnet_flutter_pip_and_docker(tmp_path):
    project = tmp_path / "proj"
    files = {
        "pom.xml": (
            '<project xmlns="http://maven.apache.org/POM/4.0.0">'
            "<parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId></parent>"
            "<groupId>com.acme</groupId><artifactId>api</artifactId>"
            "<dependencies><dependency><groupId>com.fasterxml.jackson.core</groupId>"
            "<artifactId>jackson-databind</artifactId></dependency></dependencies>"
            "</project>\n"
        ),
        "gradle-app/settings.gradle.kts": 'rootProject.name = "gapp"\n',
        "gradle-app/gradle/libs.versions.toml": (
            '[libraries]\nktor-core = { module = "io.ktor:ktor-server-core", version = "3.0.0" }\n'
            '[plugins]\nspring = { id = "org.springframework.boot", version = "3.4.0" }\n'
        ),
        "gradle-app/build.gradle.kts": (
            'plugins {\n  id("org.springframework.boot") version "3.4.0"\n  kotlin("plugin.serialization") version "2.0.0"\n}\n'
            'dependencies {\n  implementation("org.junit.jupiter:junit-jupiter:5.11.0")\n}\n'
        ),
        "dotnet-app/App.csproj": (
            '<Project Sdk="Microsoft.NET.Sdk.Web">\n'
            '  <PropertyGroup><TargetFramework>net8.0</TargetFramework></PropertyGroup>\n'
            '  <ItemGroup><PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.0" /></ItemGroup>\n'
            "</Project>\n"
        ),
        "dotnet-app/Directory.Packages.props": (
            '<Project><ItemGroup><PackageVersion Include="xunit" Version="2.9.0" /></ItemGroup></Project>\n'
        ),
        "mobile/pubspec.yaml": "name: mob\ndependencies:\n  flutter:\n    sdk: flutter\n  dio: ^5.0.0\n",
        "mobile_test/pubspec.yaml": "name: mob_test\ndev_dependencies:\n  flutter_test:\n    sdk: flutter\n",
        "py/requirements.txt": "fastapi>=0.115\n# comment\n-r extra.txt\n",
        "py/extra.txt": "sqlmodel==0.0.22\n",
        "Dockerfile": "FROM node:22-alpine AS build\nFROM build AS final\nFROM postgres:16-alpine\n",
        "docker-compose.yml": "services:\n  cache:\n    image: redis:7-alpine\n",
    }
    for rel, text in files.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    record = premap.write(manifest)
    got = {(p["ecosystem"], p["name"], p["declared_in"].split("#", 1)[0]) for p in record.get("packages") or []}
    assert ("maven", "org.springframework.boot:spring-boot-starter-parent", "pom.xml") in got
    assert ("maven", "com.fasterxml.jackson.core:jackson-databind", "pom.xml") in got
    assert ("maven", "io.ktor:ktor-server-core", "gradle-app/gradle/libs.versions.toml") in got
    assert ("maven", "org.springframework.boot", "gradle-app/build.gradle.kts") in got
    assert ("maven", "org.junit.jupiter:junit-jupiter", "gradle-app/build.gradle.kts") in got
    assert ("nuget", "Microsoft.AspNetCore.App", "dotnet-app/App.csproj") in got
    assert ("nuget", "Microsoft.EntityFrameworkCore", "dotnet-app/App.csproj") in got
    assert ("nuget", "xunit", "dotnet-app/Directory.Packages.props") in got
    assert ("pub", "flutter", "mobile/pubspec.yaml") in got
    assert ("pub", "flutter_test", "mobile_test/pubspec.yaml") in got
    assert ("pub", "flutter", "mobile_test/pubspec.yaml") not in got
    assert ("pub", "dio", "mobile/pubspec.yaml") in got
    assert ("pypi", "fastapi", "py/requirements.txt") in got
    assert ("pypi", "sqlmodel", "py/extra.txt") in got
    assert ("docker", "node", "Dockerfile") in got
    assert ("docker", "postgres", "Dockerfile") in got
    assert ("docker", "build", "Dockerfile") not in got
    assert ("docker", "redis", "docker-compose.yml") in got
    assert {(p["ecosystem"], p["name"]) for p in module_graph.package_facts(manifest)} >= {
        ("pub", "flutter"), ("pypi", "fastapi"), ("docker", "redis")
    }


def test_model_sources_emit_packages_without_changing_recorded_commands(tmp_path):
    class Inv:
        files = ["pom.xml", "build.gradle.kts", "App.csproj"]
        directories = {"."}
        def text(self, _rel):
            return ""
    class Ctx:
        root = tmp_path
        inventory = Inv()
        stated = {}

    assert dotnet.ITEMS == ("ProjectReference", "Compile")
    assert [c["argv"][0] for c in maven.commands(Ctx())] == ["sh"]
    assert [c["tool"] for c in gradle.commands(Ctx())] == ["gradle"]
    assert renovate.commands(Ctx())[0]["tool"] == "renovate"

    ren_out = json.dumps({"repositories": {"local": {"packageFiles": {
        "gradle": [{"packageFile": "build.gradle.kts", "deps": [
            {"depName": "org.hibernate.orm:hibernate-core", "currentValue": "6.6.0"},
        ]}],
        "nuget": [{"packageFile": "App.csproj", "deps": [
            {"depName": "Serilog.AspNetCore", "currentValue": "8.0.0"},
        ]}],
        "hex": [{"packageFile": "mix.exs", "deps": [{"depName": "phoenix", "currentValue": "1.7.0"}]}],
    }}}})
    ren_read = renovate.read(Ctx(), [{"tool": "renovate"}], [{"returncode": 0, "stdout": ren_out, "stderr": ""}])
    ren_pkgs = {(p["ecosystem"], p["name"], p["declared_in"]) for p in ren_read["facts"]["packages"]}
    assert ("maven", "org.hibernate.orm:hibernate-core", "build.gradle.kts") in ren_pkgs
    assert ("nuget", "Serilog.AspNetCore", "App.csproj") in ren_pkgs
    assert ("hex", "phoenix", "mix.exs") in ren_pkgs

    pom_xml = (
        '<project xmlns="http://maven.apache.org/POM/4.0.0">'
        "<groupId>com.acme</groupId><artifactId>svc</artifactId>"
        "<build><directory>/work/target</directory></build>"
        "<dependencies><dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId></dependency></dependencies>"
        "</project>"
    )
    mvn_read = maven.read(Ctx(), [{"cwd": "."}], [{"returncode": 0, "stdout": pom_xml, "stderr": "", "root": "/work"}])
    assert ("maven", "org.postgresql:postgresql", "pom.xml") in {
        (p["ecosystem"], p["name"], p["declared_in"]) for p in mvn_read["facts"]["packages"]
    }


def test_renovate_carries_the_value_the_file_writes_and_maven_s_effective_pom_none(tmp_path):
    class Ctx:
        root, stated = tmp_path, {}
        inventory = type("Inv", (), {"files": ["pom.xml"], "directories": {"."}, "text": lambda self, _rel: ""})()

    report = json.dumps({"repositories": {"local": {"packageFiles": {
        "npm": [{"packageFile": "package.json", "deps": [
            {"depName": "react", "currentValue": "^18.2.0"},
            {"depName": "@acme/lib", "currentValue": "file:../lib", "skipReason": "file"},
            {"depName": "is-number", "currentValue": "7.0.0", "skipReason": "github-token-required",
             "currentRawValue": "git+https://github.com/jonschlinkert/is-number.git#7.0.0"},
            {"depName": "left", "currentValue": "^1.0.0", "currentRawValue": "npm:right@^1.0.0"},
            {"depName": "vitest"}]}],
        "gradle": [{"packageFile": "gradle/libs.versions.toml", "deps": [
            {"depName": "io.coil-kt.coil3:coil-compose", "currentValue": "3.6.3", "sharedVariableName": "coil"}]}],
        "dockerfile": [{"packageFile": "Dockerfile", "deps": [
            {"depName": "docker.io/library/postgres", "currentValue": "16-alpine"},
            {"depName": "registry.internal:5000/library/postgres", "currentValue": "16"},
            {"depName": "redis", "currentDigest": "sha256:ab"}]}],
    }}}})
    got = renovate.read(Ctx(), [{"tool": "renovate"}], [{"returncode": 0, "stdout": report, "stderr": ""}])
    assert {(p["name"], p.get("version")) for p in got["facts"]["packages"]} == {
        ("react", "^18.2.0"), ("@acme/lib", None), ("is-number", None), ("left", None), ("vitest", None),
        ("io.coil-kt.coil3:coil-compose", None), ("postgres", "16-alpine"),
        ("registry.internal:5000/library/postgres", "16"), ("redis", None)}

    effective = ('<project xmlns="http://maven.apache.org/POM/4.0.0"><groupId>com.acme</groupId><artifactId>svc</artifactId>'
                 "<build><directory>/work/target</directory></build><dependencies><dependency><groupId>com.fasterxml"
                 ".jackson.core</groupId><artifactId>jackson-databind</artifactId><version>2.17.2</version></dependency>"
                 "</dependencies></project>")
    model = maven.read(Ctx(), [{"cwd": "."}], [{"returncode": 0, "stdout": effective, "stderr": "", "root": "/work"}])
    assert [p.get("version") for p in model["facts"]["packages"]] == [None]  # inherited and interpolated: not written
    reader = {"ecosystem": "maven", "name": "com.fasterxml.jackson.core:jackson-databind", "declared_in": "pom.xml",
              "version": "2.17.0"}
    joined = premap.join([{"source": "maven@3.10.0", "rank": "model", "facts": model["facts"]},
                          {"source": "jvm_files@1", "rank": "reader", "facts": {"packages": [reader]}}])["packages"]
    assert [(p["version"], p.get("conflicts")) for p in joined] == [("2.17.0", None)]
