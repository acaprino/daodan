"""Task 2: Step 1 `packages` facet in `premap.json` across static readers and container model outputs."""
from __future__ import annotations

import json
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import premap  # noqa: E402
from premap import dotnet, gradle, maven, module_graph, renovate  # noqa: E402
import snapshot  # noqa: E402


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
