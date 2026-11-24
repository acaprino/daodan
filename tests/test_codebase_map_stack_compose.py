"""A configured service is an instance declared at a site; only a registry match identifies a technology."""
import importlib
from importlib import metadata
import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import premap
from premap import compose
import snapshot
import technologies


def test_stack_keeps_compose_declarations_local_even_without_a_catalog_entry(real_stack, tmp_path):
    project = tmp_path / "project"
    files = {
        "api/pyproject.toml": '[project]\nname = "api"\n',
        "web/package.json": '{"name": "web"}',
        "api/compose.override.yml": """x-defaults: &defaults
  image: postgres:16
services:
  db: {<<: *defaults}
  mailpit:
    image: company/mailpit:v1
    profiles: [test]
    environment:
      EXAMPLE: private_for_test
  worker: {build: .}
  custom: {image: '${REGISTRY:-docker.io}/redis'}
  cache: {image: 'redis:${TAG:-7}'}
  pending: {image: 'registry:${PORT}/kafka'}
x-example: {image: bitnami/kafka}
""",
        "web/compose.yml": "services: {worker: {image: company/frontend:v1}}",
        "docs/compose.example.yml": "services: {example: {image: company/doc:v1}}",
    }
    for rel, content in files.items():
        file = project / rel
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    facts = premap.write(manifest)
    # Bind these workflow declarations to their own sites independently of the Compose files.
    facts["excluded"] = [{"path": "docs/", "why": "documentation"}]
    facts["services"] = [
        {"name": "ci_mail", "image": "company/mail:v2", "env": {"X": "private_for_test"},
         "declared_in": ".github/workflows/test.yml#jobs.ci.services.ci_mail"},
        {"name": "testing", "image": "company/testing:v3", "declared_in": "web/package.json#scripts.test.services.testing"},
    ]
    record = technologies.ensure(manifest, facts=facts)
    by_name = {m["name"]: m for m in record["units"]}
    api = {s["name"]: s for s in by_name["api"]["configured_services"]}
    assert set(api) == {"db", "mailpit", "worker", "custom", "cache", "pending"}
    assert api["mailpit"] == {"name": "mailpit", "image": "company/mailpit:v1", "profiles": ["test"],
                              "path": "api/compose.override.yml", "line": 5, "declared_in": "api/compose.override.yml#L5"}
    assert api["db"]["image"] == "postgres:16"
    assert "image" not in api["worker"]
    assert api["custom"]["image"] == "${REGISTRY:-docker.io}/redis"
    assert {"postgresql", "redis"} <= set(by_name["api"]["services"])
    assert not {"kafka", "mailpit"} & set(by_name["api"]["services"])
    # the release reads the Compose file by itself (no line) and is given the pre-map's declaration (with its line)
    assert {(s["line"], s["source"].partition("@")[0]) for entry in record["technologies"] if entry["id"] == "redis"
            for s in entry["signs"] if s["sign"] == "package"} == {(12, "modules.py"), (None, "stack-analyser")}
    assert {(s["line"], s["source"].partition("@")[0]) for entry in record["technologies"] if entry["id"] == "postgresql"
            for s in entry["signs"] if s["sign"] == "package" and s["path"] == "api/compose.override.yml"} == {
        (2, "modules.py"), (None, "stack-analyser")}
    assert {s["name"] for s in by_name["web"]["configured_services"]} == {"worker", "testing"}
    public = record["configured_services"]
    assert any(s["name"] == "ci_mail" and s["path"] == ".github/workflows/test.yml" for s in public)
    assert all(s["name"] != "ci_mail" for s in api.values())
    assert not any(s["name"] == "example" for s in public)
    assert "private_for_test" not in json.dumps(public)


def test_two_compose_invocations_share_the_declaring_script_but_keep_their_sites():
    path = "api/scripts/check.sh"
    step = ["docker", "compose", "up", "-d", "mailpit"]
    steps = compose.facts([(path, step), (path, step)], "api")
    context = SimpleNamespace(stated={"compose": steps})
    result = {"returncode": 0, "stdout": '{"services":{"mailpit":{"image":"axllent/mailpit"}}}'}
    facts = compose.read(context, compose.commands(context), [result, result])["facts"]
    declarations = technologies._configured_services(facts, ())
    assert {s["path"] for s in declarations} == {path}
    assert {s["declared_in"] for s in declarations} == {f"{path}.services.mailpit", f"{path}.1.services.mailpit"}


def test_compose_reports_a_gap_for_unavailable_or_malformed_yaml(monkeypatch):
    rows, gaps = compose.file_services("compose.yml", 'services: {db: [')
    assert not rows and gaps[0]["kind"] == "compose_not_read"
    monkeypatch.setitem(sys.modules, "yaml", None)
    rows, gaps = compose.file_services("compose.yml", "services: {db: {image: postgres:16}}")
    assert not rows and gaps[0]["kind"] == "source_unavailable"


def test_installing_yaml_refreshes_a_cached_scan_with_an_unavailable_reader(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "compose.yml").write_text("services: {mailpit: {image: axllent/mailpit}}", encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    reader = premap.module_graph
    real_version = metadata.version

    def without_yaml(package):
        if package == "PyYAML":
            raise metadata.PackageNotFoundError(package)
        return real_version(package)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(metadata, "version", without_yaml)
            patch.setitem(sys.modules, "yaml", None)
            importlib.reload(reader)
            cold = premap.write(manifest, sources=(reader,))
            assert not cold.get("configured_services")
            assert any(g["kind"] == "source_unavailable" and g["path"] == "compose.yml" for g in cold["gaps"])
    finally:
        importlib.reload(reader)
    assert premap.state(manifest, sources=(reader,))["state"] == "stale"
    warm = premap.ensure(manifest, sources=(reader,))
    assert [s["name"] for s in warm["configured_services"]] == ["mailpit"]
