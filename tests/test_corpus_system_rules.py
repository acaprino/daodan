"""Native packages from archived project manifests and SDKs declared directly in source."""
import gzip
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

CORE = Path(__file__).resolve().parents[1] / "daodan/core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))
import snapshot  # noqa: E402
import stack_recognition  # noqa: E402
import technologies  # noqa: E402
from premap import renovate  # noqa: E402
from test_codebase_map_stack_recognition import package_signs, recognized  # noqa: E402

BENCH = CORE.parents[1] / "benchmarks/project-model"


@pytest.mark.parametrize(("fixture", "ecosystem", "labels"), [
    ("real-stack-atuin", "crates", {
        "ratatui": "ratatui", "ratatui-core": "ratatui", "sqlx": "sqlx-rust", "rstest": "rstest",
        "proptest": "proptest", "wiremock": "wiremock-rs", "minijinja": "minijinja",
        "prost": "protobuf", "prost-types": "protobuf", "tonic": "grpc",
    }),
    ("real-app-hoppscotch", "crates", {"clap": "clap", "tempfile": "tempfile-rust", "windows-sys": "windows-rs"}),
    ("real-stack-lldap", "crates", {"juniper": "juniper", "sea-orm": "sea-orm", "graphql_client": "graphql-client-rust",
                                    "mockall": "mockall", "yew": "yew"}),
    ("real-stack-localsend", "crates", {"hyper": "hyper-rust", "flutter_rust_bridge": "flutter-rust-bridge"}),
    ("real-stack-localsend", "pub", {"flutter_rust_bridge": "flutter-rust-bridge", "test": "dart-test",
                                    "refena_flutter": "refena", "dart_mappable": "dart-mappable",
                                    "dart_mappable_builder": "dart-mappable", "routerino": "routerino"}),
    ("mix-poly-firebase", "crates", {"serde_json": "serde-json", "tauri-build": "tauri"}),
    ("real-app-memos", "go", {"github.com/stretchr/testify": "testify", "connectrpc.com/connect": "connectrpc",
                             "github.com/grpc-ecosystem/grpc-gateway/v2": "grpc-gateway",
                             "github.com/testcontainers/testcontainers-go/modules/postgres": "testcontainers"}),
    ("real-stack-fiber-go-template", "go", {"github.com/gofiber/fiber/v2": "fiber", "github.com/jmoiron/sqlx": "sqlx-go"}),
    ("real-stack-gin-vue-admin", "go", {"github.com/qiniu/qmgo": "qmgo", "github.com/casbin/casbin/v3": "casbin"}),
    ("real-stack-opengist", "go", {"github.com/urfave/cli/v2": "urfave-cli"}),
    ("real-stack-owncast", "go", {"github.com/oapi-codegen/oapi-codegen/v2": "oapi-codegen", "github.com/sqlc-dev/sqlc": "sqlc"}),
    ("real-stack-hexpm", "hex", {"ecto": "ecto", "ecto_sql": "ecto", "oban": "oban", "broadway": "broadway",
                                 "esbuild": "esbuild", "tailwind": "tailwind"}),
])
def test_packages_have_their_native_identity_and_source_in_the_archive(real_stack, tmp_path, fixture, ecosystem, labels):
    with gzip.open(BENCH / "results/premap-runs" / f"{fixture}.json.gz", "rt", encoding="utf-8") as stream:
        runs = json.load(stream)["runs"]
    context = SimpleNamespace(inventory=SimpleNamespace(text=lambda _: ""), stated={})  # the pre-map's reader of Renovate's answer
    packages = [{**p, "sources": ["renovate@1"]} for run in runs
                if run["command"]["argv"][0] == "renovate" and run["result"]["returncode"] == 0
                for p in renovate.read(context, [], [run["result"]])["facts"].get("packages", ())
                if p["ecosystem"] == ecosystem and p["name"] in labels]
    matches = package_signs(recognized(tmp_path, packages=packages))
    actual = {(name, ident) for ident, name, path, _ in matches if path}
    assert set(labels.items()) <= actual


def test_sdk_dependencies_and_windows_bindings_are_matched_at_their_manifests(real_stack, tmp_path):
    root = tmp_path / "project"
    manifests = {
        # Imago's Windows bindings are target dependencies. LocalSend's flutter_test comes from the SDK.
        "shell/Cargo.toml": '[package]\nname="shell"\nversion="0.1.0"\n[target.\'cfg(windows)\'.dependencies]\n'
                            'webview2-com = "0.38"\nwindows-core = "0.62"\n',
        "app/pubspec.yaml": 'name: app\ndev_dependencies:\n  flutter_test:\n    sdk: flutter\n',
    }
    for path, content in manifests.items():
        file = root / path
        file.parent.mkdir(parents=True)
        file.write_text(content, encoding="utf-8")
    manifest = tmp_path / "out/manifest.sqlite"
    snapshot.read_project(root, manifest)
    entries = stack_recognition.run(manifest, facts={})["found"]
    actual = {(item["id"], sign["value"], sign["path"]) for item in entries for sign in item["signs"]
              if sign["sign"] == "package"}
    assert actual == {("webview2-com", "webview2-com", "shell/Cargo.toml"), ("windows-rs", "windows-core", "shell/Cargo.toml"),
                      ("flutter-test", "flutter_test", "app/pubspec.yaml")}


def test_source_only_frameworks_have_module_evidence_and_no_invented_packages(real_stack, tmp_path):
    root = tmp_path / "project"
    manifest = tmp_path / "out/manifest.sqlite"
    files = {
        "app/Package.swift": 'import PackageDescription\nlet package = Package(name: "Reader")\n',
        "app/ContentView.swift": '// import UIKit\nlet note = "import Flutter"\nimport SwiftUI\n'
                                 'import struct MapKit.MKMapRect\nimport SwiftUIExtras\n',
        "app/example/Example.swift": 'import UIKit\n',
        "server/mix.exs": 'defmodule Demo.MixProject do\n  def project, do: [app: :server]\nend\n',
        "server/test/test_helper.exs": '# ExUnit.start()\n"ExUnit.configuration()"\nMy.ExUnit.start()\n'
                                       'ExUnit.start()\nif true, do: ExUnit.configuration()\n',
    }
    for path, content in files.items():
        file = root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
    snapshot.read_project(root, manifest)
    facts = {"packages": [], "excluded": [{"path": "app/example/", "why": "example"}]}
    record = technologies.ensure(manifest, facts=facts)
    actual = {(entry["id"], s["value"], s["path"], s["line"]) for entry in record["technologies"]
              for s in entry["signs"] if s["sign"] == "source" and s["strength"] == "declared"}
    assert actual == {
        ("swiftui", "SwiftUI", "app/ContentView.swift", 3), ("mapkit", "MapKit", "app/ContentView.swift", 4),
        ("exunit", "ExUnit.start", "server/test/test_helper.exs", 4),
        ("exunit", "ExUnit.configuration", "server/test/test_helper.exs", 5),
    }
    owners = {tuple(unit["paths"]): set(unit["frameworks"]) for unit in record["units"]}
    assert {"swiftui", "mapkit"} <= owners[("app",)]
    assert "exunit" in owners[("server",)]
    assert all(not unit["libraries"] for unit in record["units"])
