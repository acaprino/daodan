"""Task 3: Rationalized Step 2 (`stack`) — per-module frameworks, libraries, services, tools across concrete, logical, and virtual modules."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import modules  # noqa: E402
import premap  # noqa: E402
import registry_build  # noqa: E402
import service_registry  # noqa: E402
import snapshot  # noqa: E402
import technologies  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
if str(HERE / "benchmarks/project-model") not in sys.path:
    sys.path.insert(0, str(HERE / "benchmarks/project-model"))
import score  # noqa: E402


def _git_project(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"]):
        subprocess.run(cmd, cwd=root, check=True, capture_output=True)
    return root


def test_distributed_registry_supports_jvm_dotnet_pub_hex_swift_and_passes_check():
    reg = service_registry.load()
    assert registry_build.check(reg) == []
    by_id = {e["id"]: e for e in reg["entries"]}
    for ident in ("spring-boot", "junit-jupiter", "jackson", "hibernate", "aspnetcore",
                  "entity-framework-core", "xunit", "flutter", "phoenix", "chi", "sqlmodel"):
        assert ident in by_id, ident
    assert "maven" in by_id["spring-boot"]["signs"]["packages"]
    assert "nuget" in by_id["aspnetcore"]["signs"]["packages"]
    assert "pub" in by_id["flutter"]["signs"]["packages"]
    assert "hex" in by_id["phoenix"]["signs"]["packages"]
    assert "rubygems" in by_id["rails"]["signs"]["packages"]


def test_stack_emits_frameworks_libraries_services_and_tools_for_concrete_logical_and_virtual_modules(tmp_path):
    project = _git_project(tmp_path / "poly", {
        "api/pom.xml": (
            '<project xmlns="http://maven.apache.org/POM/4.0.0">'
            "<parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId></parent>"
            "<groupId>com.acme</groupId><artifactId>api</artifactId>"
            "<dependencies>"
            "<dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId></dependency>"
            "<dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId></dependency>"
            "<dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId></dependency>"
            "<dependency><groupId>com.acme.internal</groupId><artifactId>custom-util</artifactId></dependency>"
            "</dependencies></project>\n"
        ),
        "api/src/main/java/com/acme/Api.java": "package com.acme;\npublic class Api {}\n",
        "dotnet/Web.csproj": (
            '<Project Sdk="Microsoft.NET.Sdk.Web">\n'
            '  <PropertyGroup><TargetFramework>net8.0</TargetFramework></PropertyGroup>\n'
            '  <ItemGroup>'
            '    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.0" />'
            '    <PackageReference Include="xunit" Version="2.9.0" />'
            '    <PackageReference Include="Company.SecretLib" Version="1.0.0" />'
            "  </ItemGroup>\n</Project>\n"
        ),
        "dotnet/Program.cs": "class Program {}\n",
        "mobile/pubspec.yaml": "name: mob\ndependencies:\n  flutter:\n    sdk: flutter\n",
        "mobile/lib/main.dart": "void main() {}\n",
        "web/package.json": json.dumps({
            "name": "web",
            "dependencies": {"react": "^19.0.0", "passport-google-oauth20": "^2.0.0", "postman-collection": "^4.0.0"},
            "devDependencies": {"@playwright/test": "^1.48.0", "eslint": "^9.0.0"},
        }),
        "web/src/ui.tsx": "export const ZOOM_STEP = 2;\nexport const GHOST_CLASS = 'ghost';\n",
        "scripts/worker.py": "def run():\n    return 1\n",
        "Dockerfile": "FROM redis:7-alpine\n",
        "docs/examples/docker-compose.hosted.yml": "services:\n  proxy:\n    image: caddy:2\n",
        "renovate.json": "{}\n",
        "codebase-modules.json": json.dumps({
            "schema": "daodan/declared-modules/v1",
            "modules": [{
                "name": "Checkout Domain",
                "kind": "component",
                "location": "internal",
                "responsibility": "Handles API and web checkout",
                "members": ["api/src/main/java/com/acme/Api.java", "web/src/ui.tsx"],
                "evidence": ["api/pom.xml", "web/package.json"],
            }],
        }),
    })
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    facts = premap.write(manifest)
    facts["excluded"] = [{"path": "docs/examples/", "why": "documentation"}]
    Path(premap.path(manifest)).write_text(json.dumps(facts), encoding="utf-8")
    modules.sync_with_premap(manifest, facts)

    record = technologies.ensure(manifest)
    by_id = {m["id"]: m for m in record["modules"]}

    # Concrete JVM module: frameworks, services, and uncataloged libraries all present
    api = by_id["api"]
    assert api["nature"] == "concrete"
    assert {"spring-boot", "jackson", "junit-jupiter"} <= set(api["frameworks"])
    assert "postgresql" in api["services"]
    assert any(lib["name"] == "com.acme.internal:custom-util" and lib["ecosystem"] == "maven" for lib in api["libraries"])

    # Concrete .NET module
    web_cs = by_id["web@dotnet"] if "web@dotnet" in by_id else next(m for m in record["modules"] if m["paths"] == ["dotnet"])
    assert {"aspnetcore", "entity-framework-core", "xunit"} <= set(web_cs["frameworks"])
    assert any(lib["name"] == "Company.SecretLib" and lib["ecosystem"] == "nuget" for lib in web_cs["libraries"])

    # Concrete Flutter module
    mob = by_id["mob"]
    assert "flutter" in mob["frameworks"]

    # Web module: Playwright is framework/tool, NOT a service; ZOOM_STEP/GHOST_CLASS/passport-google/postman-collection NOT false services
    web = by_id["web"] if by_id.get("web", {}).get("paths") == ["web"] else next(m for m in record["modules"] if m["paths"] == ["web"])
    assert "react" in web["frameworks"]
    assert "playwright" in set(web["frameworks"]) | set(web["tools"])
    all_services = {e["id"] for e in record["technologies"] if e.get("category") == "service"}
    assert not ({"playwright", "zoom", "ghost", "gcp", "postman", "caddy", "renovate"} & all_services)

    # Virtual source-tree module (owns scripts/worker.py + root Dockerfile)
    virt = next(m for m in record["modules"] if m["nature"] == "virtual" and m["provenance"] == "virtual")
    assert virt["languages"] == {"python": 1}
    assert "redis" in virt["services"]

    # Logical declared module ("Checkout Domain") inherits/projects stack of its files & evidence
    logical = by_id["checkout-domain"]
    assert logical["nature"] == "logical"
    assert {"spring-boot", "react"} <= set(logical["frameworks"])
    assert logical["languages"] == {"java": 1, "tsx": 1} or "java" in logical["languages"]

    # Score compatibility: Playwright is offered as framework, not service
    faces = score.technologies_faces(record)
    service_names = {s["name"].lower() for s in faces["services"]}
    assert "playwright" not in service_names and "caddy" not in service_names


def _stack(tmp_path, files: dict[str, str]) -> dict:
    project = _git_project(tmp_path / "proj", files)
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    premap.write(manifest)
    return technologies.ensure(manifest)


def test_a_unit_of_the_stack_is_named_as_the_pre_map_refers_to_it_and_keeps_its_module_name_as_an_alias(tmp_path):
    """D-303: Maven's `groupId:artifactId`, Gradle's `:` for the root of a build, the root when two units share a
    name; the name of modules.json stays among the aliases."""
    record = _stack(tmp_path, {
        "pom.xml": '<project><groupId>com.acme</groupId><artifactId>shop</artifactId><packaging>pom</packaging>'
                   "<modules><module>svc</module></modules></project>\n",
        "svc/pom.xml": '<project><parent><groupId>com.acme</groupId><artifactId>shop</artifactId></parent>'
                       "<groupId>com.acme</groupId><artifactId>svc</artifactId><dependencies><dependency>"
                       "<groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId></dependency>"
                       "</dependencies></project>\n",
        "g/settings.gradle.kts": 'rootProject.name = "billing"\n',
        "g/build.gradle.kts": 'dependencies {\n    implementation("org.springframework.boot:spring-boot-starter-web:3.4.0")\n}\n',
        "tool/pyproject.toml": '[project]\nname = "kit"\ndependencies = ["fastapi"]\n',
        "ui/package.json": '{"name": "kit", "dependencies": {"vue": "^3.5.0"}}\n',
    })
    units = {u["paths"][0]: u for u in record["units"]}
    assert {root: units[root]["name"] for root in ("svc", "g", "tool", "ui")} == {
        "svc": "com.acme:svc", "g": ":", "tool": "tool", "ui": "ui"}
    assert "svc" in units["svc"]["aliases"] and "billing" in units["g"]["aliases"] and "kit" in units["ui"]["aliases"]
    faces = {(f["name"], f.get("unit")) for f in score.technologies_faces(record)["frameworks"]}
    assert {("JUnit Jupiter", "com.acme:svc"), ("Spring MVC", ":"), ("FastAPI", "tool")} <= faces
    assert any(unit == "ui" and name.startswith("Vue") for name, unit in faces)


def test_a_package_of_the_version_catalog_goes_to_the_build_script_that_uses_it_not_to_the_catalog_s_build(tmp_path):
    """D-303: `libs.junit.jupiter` in domain/build.gradle.kts is junit-jupiter declared there; the catalog only
    gives its version, so the root of the build, which holds the catalog, does not use it."""
    record = _stack(tmp_path, {
        "settings.gradle.kts": 'rootProject.name = "inventory"\ninclude(":domain", ":api")\n',
        "gradle/libs.versions.toml": (
            '[versions]\njackson = "2.18.1"\n\n[libraries]\n'
            'jackson-databind = { module = "com.fasterxml.jackson.core:jackson-databind", version.ref = "jackson" }\n'
            'junit_jupiter = { group = "org.junit.jupiter", name = "junit-jupiter", version = "5.11.3" }\n\n'
            '[plugins]\nspring-boot = { id = "org.springframework.boot", version = "3.4.0" }\n'),
        "domain/build.gradle.kts": "dependencies {\n    testImplementation(libs.junit.jupiter)\n}\n",
        "api/build.gradle.kts": ("plugins {\n    alias(libs.plugins.spring.boot)\n}\n"
                                 "dependencies {\n    implementation(libs.jackson.databind)\n}\n"),
    })
    units = {u["name"]: u for u in record["units"]}
    assert "junit-jupiter" in units[":domain"]["technologies"]
    assert {"jackson", "spring-boot"} <= set(units[":api"]["technologies"])
    assert not {"junit-jupiter", "jackson", "spring-boot"} & set(units[":"]["technologies"])
    assert [lib["path"] for lib in units[":domain"]["libraries"]] == ["domain/build.gradle.kts"]
    assert not units[":"]["libraries"]


def test_an_entry_a_line_only_mentions_is_no_module_s_and_stays_in_mentioned_with_its_signs(tmp_path):
    """A package or file the project declares is a `declared` sign, an env-prefix token in a line a `mentioned` one;
    an entry with no declared sign is in no module's lists, for every prefix of the registry alike."""
    record = _stack(tmp_path, {
        "pyproject.toml": '[project]\nname = "app"\ndependencies = ["fastapi"]\n',
        "app.py": "import os\n\nKEY = os.environ['STRIPE_SECRET_KEY']\nZOOM = os.environ['ZOOM_API_KEY']\n",
    })
    found = {e["id"]: e for e in record["technologies"]}
    mentioned = {e["id"]: e for e in record["mentioned"]}
    assert {s["strength"] for s in found["fastapi"]["signs"]} == {"declared"}
    assert {"stripe", "zoom"} <= set(mentioned) and not {"stripe", "zoom"} & set(found)
    assert [(s["sign"], s["value"], s["path"], s["line"], s["strength"]) for s in mentioned["stripe"]["signs"]] == [
        ("env", "STRIPE_SECRET_KEY", "app.py", 3, "mentioned")]
    for module in record["modules"]:
        held = module["frameworks"] + module["services"] + module["tools"] + module["technologies"]
        assert not {"stripe", "zoom"} & set(held), module["id"]
    assert "fastapi" in {i for module in record["modules"] for i in module["frameworks"]}


def test_the_record_gives_each_checker_s_status_and_what_the_registry_lacks(tmp_path):
    """MinIO is an entry with no PyPI sign: the package `minio` is a gap of the registry, not a guess."""
    record = _stack(tmp_path, {"pyproject.toml": '[project]\nname = "app"\ndependencies = ["fastapi", "minio"]\n',
                               "app.py": "import minio\n"})
    assert [(c["checker"], c["state"]) for c in record["checkers"]] == [("package", "ran"), ("file", "ran"),
                                                                         ("env", "ran")]
    gaps = [(g["kind"], g["checker"], g["entry"], g["ecosystem"], g["value"], g["path"]) for g in record["gaps"]]
    assert ("no_ecosystem_sign", "package", "minio", "pypi", "minio", "pyproject.toml") in gaps
    assert "fastapi" not in {g[2] for g in gaps}
    assert "minio" not in {e["id"] for e in record["technologies"] + record["mentioned"]}
    assert any(lib["name"] == "minio" and "id" not in lib for m in record["modules"] for lib in m["libraries"])
