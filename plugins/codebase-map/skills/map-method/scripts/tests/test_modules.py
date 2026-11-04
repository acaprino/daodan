"""Module graph: build units per ecosystem, declared and proposed modules, edges, freshness, query."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import modules  # noqa: E402
import snapshot  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402


def write_tree(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def snap(project: Path, out: Path, previous: Path | None = None) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    if previous is None:
        snapshot.write_snapshot(project, out)
    else:
        with open_snapshot(previous) as old:
            snapshot.write_snapshot(project, out, previous=old)
    return out


def build(tmp_path: Path, files: dict[str, str]) -> tuple[Path, dict]:
    project = tmp_path / "proj"
    write_tree(project, files)
    manifest = snap(project, tmp_path / "out" / "manifest.sqlite")
    return manifest, modules.write_graph(manifest)


def by_id(graph: dict) -> dict[str, dict]:
    return {m["id"]: m for m in graph["modules"]}


def edges(graph: dict, kind: str) -> set[tuple[str, str]]:
    return {(e["source"], e["target"]) for e in graph["edges"] if e["kind"] == kind}


def assert_no_invented_paths(graph: dict, manifest: Path) -> None:
    with open_snapshot(manifest) as store:
        files = set(store.iter_paths())
    known = set(files) | {"."}
    for rel in files:
        parts = rel.split("/")
        known.update("/".join(parts[:d]) for d in range(1, len(parts)))
    for module in graph["modules"]:
        for path in [*module["paths"], *module["excluded"], *module["files"]]:
            assert path in known, (module["id"], path)
        for member in module["members"]:
            assert member["path"] in known or not member["resolved"], (module["id"], member)
        for item in module["evidence"]:
            assert item["path"] in files, (module["id"], item)
    for edge in graph["edges"]:
        for item in edge["evidence"]:
            assert item["path"] in files, edge["id"]


# ------------------------------------------------------------ ecosystems

ECOSYSTEMS = {
    "npm": ({
        "package.json": '{"name": "monorepo", "private": true, "workspaces": ["apps/*", "packages/*", "apps/legacy"]}\n',
        "apps/web/package.json": '{"name": "@acme/web", "description": "Customer web app", "dependencies": {"@acme/core": "*", "react": "19"}}\n',
        "apps/web/src/index.ts": 'import { total } from "@acme/core";\nexport const x = total(1);\n',
        "packages/core/package.json": '{"name": "@acme/core", "main": "src/index.ts"}\n',
        "packages/core/src/index.ts": "export function total(n: number) { return n; }\n",
    }, {"monorepo": (["."], ["apps/web", "packages/core"]), "acme-web": (["apps/web"], []), "acme-core": (["packages/core"], [])},
        {("acme-web", "acme-core")}, {("monorepo", "acme-web"), ("monorepo", "acme-core")}),
    "pnpm": ({
        "pnpm-workspace.yaml": "packages:\n  - 'libs/*'\n  - '!libs/private'\n",
        "package.json": '{"name": "root", "private": true}\n',
        "libs/ui/package.json": '{"name": "@acme/ui", "dependencies": {"@acme/util": "workspace:*"}}\n',
        "libs/ui/index.js": "export const a = 1;\n",
        "libs/util/package.json": '{"name": "@acme/util"}\n',
        "libs/util/index.js": "export const b = 1;\n",
    }, {"root": (["."], ["libs/ui", "libs/util"]), "acme-ui": (["libs/ui"], []), "acme-util": (["libs/util"], [])},
        {("acme-ui", "acme-util")}, {("root", "acme-ui"), ("root", "acme-util")}),
    "uv": ({
        "pyproject.toml": '[project]\nname = "shop"\ndependencies = ["shop-core"]\n\n[tool.uv.workspace]\nmembers = ["packages/*"]\n\n[tool.uv.sources]\nshop-core = { workspace = true }\n',
        "packages/core/pyproject.toml": '[project]\nname = "shop-core"\ndescription = "Core rules"\ndependencies = ["httpx>=0.27"]\n',
        "packages/core/src/shop_core/__init__.py": "def rule():\n    return 1\n",
        "app/main.py": "from shop_core import rule\n",
    }, {"shop": (["."], ["packages/core"]), "shop-core": (["packages/core"], [])},
        {("shop", "shop-core")}, {("shop", "shop-core")}),
    "cargo": ({
        "Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n',
        "crates/engine/Cargo.toml": '[package]\nname = "engine"\n\n[dependencies]\ncore-ffi = { path = "../core-ffi" }\nserde = "1"\n',
        "crates/engine/src/lib.rs": "pub fn run() {}\n",
        "crates/core-ffi/Cargo.toml": '[package]\nname = "core-ffi"\n',
        "crates/core-ffi/src/lib.rs": "pub fn ffi() {}\n",
    }, {"proj": (["."], ["crates/core-ffi", "crates/engine"]), "engine": (["crates/engine"], []), "core-ffi": (["crates/core-ffi"], [])},
        {("engine", "core-ffi")}, {("proj", "engine"), ("proj", "core-ffi")}),
    "go": ({
        "go.work": "go 1.22\n\nuse (\n\t./svc/api\n\t./svc/worker\n)\n",
        "svc/api/go.mod": "module example.com/api\n\ngo 1.22\n\nrequire example.com/worker v0.0.0\n\nreplace example.com/worker => ../worker\n",
        "svc/api/main.go": "package main\n\nfunc main() {}\n",
        "svc/worker/go.mod": "module example.com/worker\n\ngo 1.22\n",
        "svc/worker/worker.go": "package worker\n\nfunc Work() {}\n",
    }, {"proj": (["."], ["svc/api", "svc/worker"]), "example-com-api": (["svc/api"], []), "example-com-worker": (["svc/worker"], [])},
        {("example-com-api", "example-com-worker")}, {("proj", "example-com-api"), ("proj", "example-com-worker")}),
    "maven": ({
        "pom.xml": '<project xmlns="http://maven.apache.org/POM/4.0.0"><groupId>com.acme</groupId><artifactId>parent</artifactId>'
                   "<modules><module>core</module><module>web</module></modules></project>\n",
        "core/pom.xml": '<project xmlns="http://maven.apache.org/POM/4.0.0"><parent><groupId>com.acme</groupId><artifactId>parent</artifactId></parent>'
                        "<artifactId>core</artifactId></project>\n",
        "core/src/main/java/com/acme/Core.java": "package com.acme;\npublic class Core {}\n",
        "web/pom.xml": '<project xmlns="http://maven.apache.org/POM/4.0.0"><artifactId>web</artifactId><dependencies><dependency>'
                       "<groupId>com.acme</groupId><artifactId>core</artifactId></dependency></dependencies></project>\n",
        "web/src/main/java/com/acme/Web.java": "package com.acme;\npublic class Web {}\n",
    }, {"parent": (["."], ["core", "web"]), "core": (["core"], []), "web": (["web"], [])},
        {("web", "core")}, {("parent", "core"), ("parent", "web")}),
    "gradle": ({
        "settings.gradle.kts": 'rootProject.name = "shop"\ninclude(":app", ":lib:core")\n',
        "build.gradle.kts": "plugins { kotlin(\"jvm\") }\n",
        "app/build.gradle.kts": 'dependencies { implementation(project(":lib:core")) }\n',
        "app/src/main/kotlin/App.kt": "fun main() {}\n",
        "lib/core/build.gradle.kts": "plugins { kotlin(\"jvm\") }\n",
        "lib/core/src/main/kotlin/Core.kt": "class Core\n",
    }, {"shop": (["."], ["app", "lib/core"]), "app": (["app"], []), "core": (["lib/core"], [])},
        {("app", "core")}, {("shop", "app"), ("shop", "core")}),
    "dotnet": ({
        "Shop.sln": 'Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "Shop.Web", "src\\Shop.Web\\Shop.Web.csproj", "{1}"\nEndProject\n'
                    'Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "Shop.Core", "src\\Shop.Core\\Shop.Core.csproj", "{2}"\nEndProject\n',
        "src/Shop.Web/Shop.Web.csproj": '<Project Sdk="Microsoft.NET.Sdk"><ItemGroup><ProjectReference Include="..\\Shop.Core\\Shop.Core.csproj" />'
                                        '<PackageReference Include="Serilog" /></ItemGroup></Project>\n',
        "src/Shop.Web/Program.cs": "class Program {}\n",
        "src/Shop.Core/Shop.Core.csproj": "<Project Sdk=\"Microsoft.NET.Sdk\"><PropertyGroup><AssemblyName>Acme.Core</AssemblyName></PropertyGroup></Project>\n",
        "src/Shop.Core/Core.cs": "class Core {}\n",
    }, {"shop": (["."], ["src/Shop.Core", "src/Shop.Web"]), "shop-web": (["src/Shop.Web"], []), "shop-core": (["src/Shop.Core"], [])},
        {("shop-web", "shop-core")}, {("shop", "shop-web"), ("shop", "shop-core")}),
    "composer": ({
        "composer.json": '{"name": "acme/shop", "require": {"acme/billing": "*", "monolog/monolog": "^3"}, "repositories": [{"type": "path", "url": "packages/billing"}]}\n',
        "packages/billing/composer.json": '{"name": "acme/billing"}\n',
        "packages/billing/src/Invoice.php": "<?php class Invoice {}\n",
        "public/index.php": "<?php echo 1;\n",
    }, {"acme-shop": (["."], ["packages/billing"]), "acme-billing": (["packages/billing"], [])},
        {("acme-shop", "acme-billing")}, {("acme-shop", "acme-billing")}),
    "ruby": ({
        "Gemfile": "source 'https://rubygems.org'\ngem 'rails'\ngem 'acme_core', path: 'gems/acme_core'\n",
        "gems/acme_core/acme_core.gemspec": "Gem::Specification.new do |spec|\n  spec.name = 'acme_core'\n  spec.add_dependency 'zeitwerk'\nend\n",
        "gems/acme_core/lib/acme_core.rb": "module AcmeCore; end\n",
        "app/app.rb": "require 'acme_core'\n",
    }, {"proj": (["."], ["gems/acme_core"]), "acme-core": (["gems/acme_core"], [])},
        {("proj", "acme-core")}, set()),
    "dart": ({
        "melos.yaml": "name: shop\npackages:\n  - packages/**\n",
        "pubspec.yaml": "name: shop_root\n",
        "packages/app/pubspec.yaml": "name: shop_app\ndescription: The app\ndependencies:\n  shop_core:\n    path: ../core\n  http: ^1.0.0\n",
        "packages/app/lib/main.dart": "void main() {}\n",
        "packages/core/pubspec.yaml": "name: shop_core\n",
        "packages/core/lib/core.dart": "int rule() => 1;\n",
    }, {"shop": (["."], ["packages/app", "packages/core"]), "shop-app": (["packages/app"], []), "shop-core": (["packages/core"], [])},
        {("shop-app", "shop-core")}, {("shop", "shop-app"), ("shop", "shop-core")}),
    "swift": ({
        "Package.swift": '// swift-tools-version:5.9\nimport PackageDescription\nlet package = Package(\n    name: "Shop",\n    dependencies: [\n        .package(path: "Modules/Core"),\n        .package(url: "https://github.com/apple/swift-argument-parser.git", from: "1.0.0"),\n    ]\n)\n',
        "Modules/Core/Package.swift": 'import PackageDescription\nlet package = Package(name: "Core")\n',
        "Modules/Core/Sources/Core/Core.swift": "public func rule() {}\n",
        "Sources/Shop/main.swift": "print(1)\n",
    }, {"shop": (["."], ["Modules/Core"]), "core": (["Modules/Core"], [])},
        {("shop", "core")}, set()),
    "mix": ({
        "mix.exs": 'defmodule Shop.MixProject do\n  use Mix.Project\n  def project, do: [app: :shop, apps_path: "apps", deps: deps()]\n  defp deps, do: [{:jason, "~> 1.4"}]\nend\n',
        "apps/billing/mix.exs": 'defmodule Billing.MixProject do\n  def project, do: [app: :billing, deps: [{:core, path: "../core"}]]\nend\n',
        "apps/billing/lib/billing.ex": "defmodule Billing do\nend\n",
        "apps/core/mix.exs": "defmodule Core.MixProject do\n  def project, do: [app: :core]\nend\n",
        "apps/core/lib/core.ex": "defmodule Core do\nend\n",
    }, {"shop": (["."], ["apps/billing", "apps/core"]), "billing": (["apps/billing"], []), "core": (["apps/core"], [])},
        {("billing", "core")}, {("shop", "billing"), ("shop", "core")}),
    "cmake": ({
        "CMakeLists.txt": "cmake_minimum_required(VERSION 3.20)\nproject(Shop)\nadd_subdirectory(engine)\nadd_subdirectory(tools)\n",
        "engine/CMakeLists.txt": "project(Engine)\nadd_library(engine engine.cpp)\n",
        "engine/engine.cpp": "int run() { return 1; }\n",
        "tools/CMakeLists.txt": "add_executable(tool tool.cpp)\n",
        "tools/tool.cpp": "int main() {}\n",
    }, {"shop": (["."], ["engine", "tools"]), "engine": (["engine"], []), "tools": (["tools"], [])},
        set(), {("shop", "engine"), ("shop", "tools")}),
    "haskell": ({
        "stack.yaml": "resolver: lts-22.0\npackages:\n  - ./core\n  - location: ./web\n",
        "core/core.cabal": "name: core\nversion: 0.1\nlibrary\n  build-depends: base, text\n",
        "core/src/Core.hs": "module Core where\n",
        "web/web.cabal": "name: web\nversion: 0.1\nexecutable web\n  build-depends: base, core\n",
        "web/app/Main.hs": "main = pure ()\n",
    }, {"proj": (["."], ["core", "web"]), "core": (["core"], []), "web": (["web"], [])},
        {("web", "core")}, {("proj", "core"), ("proj", "web")}),
    "sbt": ({
        "build.sbt": 'lazy val core = (project in file("core"))\nlazy val web = (project in file("web")).dependsOn(core)\n'
                     'lazy val gone = (project in file("gone"))\n',
        "core/README.md": "# core\n",
        "web/README.md": "# web\n",
    }, {"core": (["core"], []), "web": (["web"], [])},
        {("web", "core")}, set()),
    "terraform": ({
        "main.tf": 'module "network" {\n  source = "./modules/network"\n}\n\nmodule "vpc" {\n  source = "terraform-aws-modules/vpc/aws"\n}\n',
        "modules/network/main.tf": 'resource "aws_vpc" "main" {}\n',
    }, {"proj": (["."], ["modules/network"]), "network": (["modules/network"], [])},
        {("proj", "network")}, {("proj", "network")}),
    "zig": ({
        "build.zig.zon": '.{\n    .name = "shop",\n    .dependencies = .{\n        .engine = .{ .path = "libs/engine" },\n    },\n}\n',
        "libs/engine/build.zig.zon": '.{ .name = .engine }\n',
        "libs/engine/src/root.zig": "pub fn run() void {}\n",
        "src/main.zig": "pub fn main() void {}\n",
    }, {"shop": (["."], ["libs/engine"]), "engine": (["libs/engine"], [])},
        {("shop", "engine")}, set()),
    "julia-dune-nx-deno-lerna-setup": ({
        "Project.toml": 'name = "Shop"\n\n[deps]\nJSON = "682c06a0"\n',
        "ocaml/dune-project": "(lang dune 3.0)\n(name shop_ocaml)\n",
        "ocaml/bin/main.ml": "let () = ()\n",
        "nx/project.json": '{"name": "nx-app", "implicitDependencies": ["nx-lib"]}\n',
        "nx/main.ts": "export const a = 1;\n",
        "nxlib/project.json": '{"name": "nx-lib"}\n',
        "nxlib/lib.ts": "export const b = 1;\n",
        "deno/deno.json": '{"name": "@acme/deno", "workspace": ["./tool"]}\n',
        "deno/tool/deno.json": '{"name": "@acme/tool"}\n',
        "deno/tool/mod.ts": "export const t = 1;\n",
        "lerna/lerna.json": '{"packages": ["pkgs/*"]}\n',
        "lerna/pkgs/a/package.json": '{"name": "lerna-a"}\n',
        "lerna/pkgs/a/index.js": "export const l = 1;\n",
        "legacy/setup.cfg": "[metadata]\nname = legacy-lib\n",
        "legacy/setup.py": "from setuptools import setup\nsetup(name='legacy-lib')\n",
        "legacy/legacy_lib/__init__.py": "",
        "plugins/map/plugin.toml": 'schema = "daodan/v1"\nname = "map"\ndescription = "Maps code"\n\n[dependencies]\nrequired = []\n',
        "plugins/review/plugin.toml": 'schema = "daodan/v1"\nname = "review"\n\n[dependencies]\nrequired = ["map"]\n',
    }, {"shop": (["."], ["deno", "legacy", "lerna", "nx", "nxlib", "ocaml", "plugins/map", "plugins/review"]),
        "shop-ocaml": (["ocaml"], []), "nx-app": (["nx"], []), "nx-lib": (["nxlib"], []),
        "acme-deno": (["deno"], ["deno/tool"]), "acme-tool": (["deno/tool"], []),
        "lerna": (["lerna"], ["lerna/pkgs/a"]), "lerna-a": (["lerna/pkgs/a"], []), "legacy-lib": (["legacy"], []),
        "map": (["plugins/map"], []), "review": (["plugins/review"], [])},
        {("nx-app", "nx-lib"), ("review", "map")}, {("acme-deno", "acme-tool"), ("lerna", "lerna-a")}),
}


@pytest.mark.parametrize("name", sorted(ECOSYSTEMS))
def test_build_units_per_ecosystem(tmp_path, name):
    files, expected, declares, contains = ECOSYSTEMS[name]
    manifest, graph = build(tmp_path, files)
    found = {m["id"]: (m["paths"], m["excluded"]) for m in graph["modules"]}
    assert found == expected, json.dumps(found, indent=1)
    assert all(m["provenance"] == "build" and m["status"] == "confirmed" for m in graph["modules"])
    assert edges(graph, "declares") == declares
    assert edges(graph, "contains") == contains
    assert all(e["evidence"] and e["evidence"][0]["path"] for e in graph["edges"])
    assert_no_invented_paths(graph, manifest)


def test_build_unit_details(tmp_path):
    manifest, graph = build(tmp_path, ECOSYSTEMS["npm"][0])
    web = by_id(graph)["acme-web"]
    assert web["description"] == "Customer web app" and "web" in web["aliases"]
    assert web["kind"] == "npm-package" and web["ecosystems"] == ["npm"]
    assert web["files"] == ["apps/web/package.json", "apps/web/src/index.ts"]
    assert web["external"] == ["react"] and web["registered_by"] == ["."]
    assert {e["path"] for e in web["evidence"]} == {"apps/web/package.json", "package.json"}
    root = by_id(graph)["monorepo"]
    assert root["files"] == ["package.json"]
    assert any(g["kind"] == "member_missing" and "apps/legacy" in g["detail"] for g in graph["gaps"])
    assert edges(graph, "imports") == {("acme-web", "acme-core")}
    edge = next(e for e in graph["edges"] if e["kind"] == "imports")
    assert edge["evidence"][0] == {"path": "apps/web/src/index.ts", "line": 1, "imported": "packages/core/src/index.ts"}
    maven = build(tmp_path / "m", ECOSYSTEMS["maven"][0])[1]
    assert "com.acme:core" in by_id(maven)["core"]["aliases"]
    assert modules.query(maven, "com.acme:core", state="fresh")["status"] == "resolved"
    sbt = build(tmp_path / "s", ECOSYSTEMS["sbt"][0])[1]
    assert any(g["kind"] == "directory_missing" and "gone" in g["detail"] for g in sbt["gaps"])
    dotnet = build(tmp_path / "d", ECOSYSTEMS["dotnet"][0])[1]
    assert by_id(dotnet)["shop-core"]["aliases"] == ["Acme.Core"] and by_id(dotnet)["shop-web"]["external"] == ["Serilog"]
    assert modules.query(dotnet, "Acme.Core", state="fresh")["candidates"][0]["match"] == "alias"


# -------------------------------------------------------- responsibility

SESSIONS = {
    "codebase-modules.json": json.dumps({"schema": "daodan/declared-modules/v1", "modules": [
        {"name": "Session management", "responsibility": "Create, validate and revoke user sessions",
         "members": ["src/auth/session.py::create_session", "src/auth/session.py::revoke_session",
                     "src/api/session_routes.py", "src/api/health.py", "tests/auth"],
         "evidence": ["docs/architecture.md#Autenticazione"]}]}, indent=1) + "\n",
    "pyproject.toml": '[project]\nname = "sessions"\n',
    "docs/architecture.md": "# Architecture\n\n## Autenticazione\n\nSessions are created in `src/auth/session.py`.\n",
    "src/auth/__init__.py": "",
    "src/auth/session.py": "from src.storage.store import save\n\n\ndef create_session(user):\n    return save(user)\n\n\n"
                           "def revoke_session(token):\n    return save(None)\n\n\ndef unrelated():\n    return 0\n",
    "src/api/__init__.py": "",
    "src/api/session_routes.py": "from src.auth.session import create_session\n\n\ndef login(user):\n    return create_session(user)\n",
    "src/api/health.py": "from src.storage.store import save\n\n\ndef ping():\n    return save(1)\n",
    "src/api/facade.py": "class Facade:\n    def sessions(self):\n        return 1\n\n    def storage(self):\n        return 2\n",
    "src/storage/__init__.py": "",
    "src/storage/store.py": "def save(value):\n    return value\n",
    "tests/auth/test_session.py": "from src.auth.session import create_session\nfrom src.api.facade import Facade\n\n\n"
                                  "def test_create():\n    assert create_session(1) and Facade\n",
}


def test_declared_and_proposed_modules(tmp_path):
    project = tmp_path / "proj"
    manifest, graph = build(tmp_path, SESSIONS)
    sessions = by_id(graph)["session-management"]
    assert sessions["provenance"] == "declared" and sessions["status"] == "confirmed" and sessions["kind"] == "responsibility"
    members = {m["id"]: m for m in sessions["members"]}
    assert members["src/auth/session.py::create_session"]["kind"] == "symbol"
    assert members["src/auth/session.py::create_session"]["start_line"] == 4 and members["src/auth/session.py::create_session"]["hash"]
    assert members["tests/auth"]["kind"] == "directory"
    assert sessions["files"] == ["src/api/health.py", "src/api/session_routes.py", "src/auth/session.py", "tests/auth/test_session.py"]
    assert sessions["paths"] == ["tests/auth", "src/api/health.py", "src/api/session_routes.py", "src/auth/session.py"]
    assert sessions["evidence"] == [{"path": "docs/architecture.md", "line": 3, "resolved": True}]
    assert sessions["gaps"] == [] and sessions["conflicts"] == []
    assert by_id(graph)["sessions"]["provenance"] == "build"
    assert_no_invented_paths(graph, manifest)

    proposals = [
        {"name": "Persistence", "responsibility": "Store values",
         "members": ["src/storage/store.py::save", "src/storage/missing.py", "src/api/facade.py::Facade.storage"],
         "evidence": ["docs/architecture.md#Storage"]},
        {"name": "Login", "members": ["src/auth/session.py::create_session"]},
    ]
    report = modules.propose(manifest, proposals)
    assert report["accepted"] == 2 and report["graph"]["state"] == "fresh"
    graph = modules.load_graph(modules.graph_name(manifest))
    persistence = by_id(graph)["persistence"]
    assert persistence["provenance"] == "proposed" and persistence["status"] == "inferred"
    assert [g["detail"] for g in persistence["gaps"]] == [
        "src/storage/missing.py: absent from the tree", "docs/architecture.md: heading #Storage not found in docs/architecture.md"]
    assert persistence["paths"] == ["src/api/facade.py", "src/storage/store.py"]
    login = by_id(graph)["login"]
    assert login["conflicts"] == [{"kind": "shared_member", "member": "src/auth/session.py::create_session", "others": ["session-management"]}]
    assert by_id(graph)["session-management"]["conflicts"][0]["others"] == ["login"]
    calls = {(e["source"], e["target"]): e for e in graph["edges"] if e["kind"] == "calls"}
    assert set(calls) >= {("session-management", "persistence"), ("login", "persistence")}
    assert {(i["path"], i["callee"]) for i in calls[("session-management", "persistence")]["evidence"]} == {
        ("src/api/health.py", "src/storage/store.py::save"), ("src/auth/session.py", "src/storage/store.py::save")}
    assert ("login", "session-management") not in calls
    # An import counts for modules owning the importing file, and on the imported
    # side only for the module owning the exact symbol the statement names.
    imports = {(e["source"], e["target"]): e for e in graph["edges"] if e["kind"] == "imports"}
    assert [i["path"] for i in imports[("session-management", "persistence")]["evidence"]] == ["src/api/health.py"]
    assert ("login", "persistence") not in imports
    assert_no_invented_paths(graph, manifest)

    asked = modules.query(graph, "session management", state="fresh")
    assert asked["status"] == "needs_clarification"
    assert {(r["relation"], r["module"]) for r in asked["candidates"][0]["read_scope"]} >= {("calls", "persistence"), ("owned_by", "sessions")}
    assert modules.query(graph, "Persistence", state="fresh")["status"] == "incomplete"
    assert modules.query(graph, "pagamenti", state="fresh")["status"] == "unknown"

    modules.propose(manifest, [proposals[0]], replace=True)
    graph = modules.load_graph(modules.graph_name(manifest))
    assert {m["id"]: m["status"] for m in graph["modules"] if m["provenance"] != "build"} == {
        "persistence": "inferred", "session-management": "confirmed"}
    assert modules.query_manifest(manifest, "session-management")["status"] == "resolved"

    # Editing a member symbol leaves the graph stale; the rebuild keeps the proposals and names the change.
    (project / "src/auth/session.py").write_text(SESSIONS["src/auth/session.py"].replace("save(None)", "save(0)"), encoding="utf-8")
    second = snap(project, tmp_path / "out" / "manifest.sqlite", previous=manifest)
    assert modules.graph_state(second)["state"] == "stale"
    assert modules.query_manifest(second, "session-management")["status"] == "incomplete"
    result = modules.ensure_graph(second)
    assert result["state"] == "fresh" and result["action"] == "refreshed"
    assert result["changes"]["changed"] == ["session-management"] and "persistence" in result["changes"]["unchanged"]

    # Promotion is explicit: the project declares the proposal, which is then confirmed and supersedes it.
    declared = json.loads((project / "codebase-modules.json").read_text(encoding="utf-8"))
    declared["modules"].append({"name": "Persistence", "responsibility": "Store values", "members": ["src/storage/store.py::save"]})
    (project / "codebase-modules.json").write_text(json.dumps(declared), encoding="utf-8")
    third = snap(project, tmp_path / "out" / "manifest.sqlite", previous=second)
    modules.ensure_graph(third)
    graph = modules.load_graph(modules.graph_name(third))
    assert {m["id"]: (m["provenance"], m["status"]) for m in graph["modules"] if m["provenance"] != "build"} == {
        "persistence": ("declared", "confirmed"), "session-management": ("declared", "confirmed")}
    assert any(g["kind"] == "proposal_superseded" for g in graph["gaps"])
    assert modules.load_ledger(third)[0]["name"] == "Persistence"
    the_brief = modules.brief(third)
    assert {m["id"] for m in the_brief["modules"]} == {"persistence", "session-management", "sessions"}
    assert the_brief["symbols"]["src/auth/session.py"] == ["create_session", "revoke_session", "unrelated"]
    assert the_brief["symbols_omitted"] == 0 and "symbols_hint" not in the_brief
    small = modules.brief(third, symbol_limit=3)
    assert small["symbols"] == {"src/api/facade.py": ["Facade", "Facade.sessions", "Facade.storage"]} and small["symbols_hint"]


def test_absence_reasons_and_validation(tmp_path):
    project = tmp_path / "proj"
    write_tree(project, {**SESSIONS, ".gitignore": "NOTES.md\n", "NOTES.md": "# Notes\n\n## Storage\n",
                         ".hidden/tool.py": "def run():\n    return 1\n"})
    subprocess.run(["git", "init", "-q", str(project)], check=True, capture_output=True)
    manifest = snap(project, tmp_path / "out" / "manifest.sqlite")
    modules.write_graph(manifest)
    report = modules.propose(manifest, [
        {"name": "Persistence", "members": ["src/storage/store.py::save", ".hidden/tool.py", "src/storage/store.py::load",
                                            "docs/storage.md", "node_modules/x/index.js"],
         "evidence": ["NOTES.md#Storage"]}])
    assert {g["detail"] for g in report["modules"][0]["gaps"]} == {
        ".hidden/tool.py: inside a dot directory, outside the map perimeter",
        "src/storage/store.py::load: symbol is not in the snapshot of this file",
        "docs/storage.md: absent from the tree",
        "node_modules/x/index.js: inside a dependency or build directory, outside the map perimeter",
        "NOTES.md: ignored by Git, outside the map perimeter"}
    for bad in ([{"name": "x", "members": []}], [{"name": "x", "members": ["a"], "extra": 1}],
                [{"name": "", "members": ["a"]}], [{"name": "A", "members": ["a"]}, {"name": "a", "members": ["b"]}]):
        with pytest.raises(ValueError):
            modules.propose(manifest, bad)
    (project / "codebase-modules.json").write_text("{not json", encoding="utf-8")
    again = snap(project, tmp_path / "again" / "manifest.sqlite")
    graph = modules.write_graph(again)
    assert not any(m["provenance"] == "declared" for m in graph["modules"])
    assert any(g["kind"] == "modules_unreadable" for g in graph["gaps"])


def test_deterministic_and_bound_to_snapshot_bytes(tmp_path):
    project = tmp_path / "proj"
    write_tree(project, {**ECOSYSTEMS["npm"][0], **{k: v for k, v in SESSIONS.items() if k != "pyproject.toml"}})
    manifest = snap(project, tmp_path / "out" / "manifest.sqlite")
    with open_snapshot(manifest) as store:
        first, second = modules.derive(store, ledger=[]), modules.derive(store, ledger=[])
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert modules.render(first) == modules.render(second)
    (project / "package.json").write_text('{"name": "renamed"}\n', encoding="utf-8")
    with open_snapshot(manifest) as store:
        with pytest.raises(ValueError, match="source changed since the snapshot"):
            modules.derive(store, ledger=[])


def test_cli_and_service(tmp_path):
    project = tmp_path / "proj"
    write_tree(project, SESSIONS)
    out = tmp_path / "out" / "manifest.sqlite"
    written = subprocess.run([sys.executable, str(SCRIPTS / "snapshot.py"), "write", str(project), "--out", str(out)],
                             capture_output=True, text=True, cwd=SCRIPTS)
    assert written.returncode == 0, written.stderr
    assert "modules: rebuilt" in written.stdout and modules.graph_name(out).is_file() and out.with_name("modules.md").is_file()
    check = subprocess.run([sys.executable, str(SCRIPTS / "modules.py"), "build", str(out), "--check"],
                           capture_output=True, text=True, cwd=SCRIPTS)
    assert check.returncode == 0 and json.loads(check.stdout)["state"] == "fresh"
    asked = subprocess.run([sys.executable, str(SCRIPTS / "modules.py"), "query", str(out), "session management"],
                           capture_output=True, text=True, cwd=SCRIPTS)
    assert json.loads(asked.stdout)["status"] == "resolved"
    missing = modules.query_manifest(snap(project, tmp_path / "bare" / "manifest.sqlite"), "sessions")
    assert missing["status"] == "unknown" and missing["gaps"][0]["kind"] == "graph_missing"

    from mcp_service import MapService
    service = MapService(project)
    service.create_run(".", "run-a")
    summary = service.modules("run-a")
    assert summary["graph_state"] == "fresh" and {m["id"] for m in summary["modules"]} == {"session-management", "sessions"}
    report = service.modules("run-a", proposals=[{"name": "Persistence", "members": ["src/storage/store.py::save"]}])
    assert report["accepted"] == 1 and report["modules"][0]["status"] == "inferred"
    assert service.modules("run-a", query="persistence")["status"] == "incomplete"
    assert "src/storage/store.py" in service.modules("run-a", brief=True)["symbols"]
    events = [event["event"] for event in service.events("run-a")["events"]]
    assert "modules_proposed" in events and "modules_failed" not in events
    with pytest.raises(ValueError):
        service.modules("run-a", query="")
