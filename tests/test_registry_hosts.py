"""An endpoint can be mentioned without proving that a module runs the service."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import registry_hosts
import service_registry


HOST = "api.example.org"
ENTRIES = [{"id": "example", "signs": {"hosts": [HOST]}}]


def check(files):
    project = service_registry.Project([], list(files), lambda path: files[path].splitlines())
    return registry_hosts.check_hosts(ENTRIES, project)


def test_configuration_mentions_preserve_location_and_hide_url_credentials():
    config = """# https://api.example.org/comment
endpoint: &url https://user:private@API.EXAMPLE.ORG:443/v2?token=private
more:
  - *url
  - https://api.example.org.evil.test/path
  - https://api.example.org@elsewhere.test/path
  - https://elsewhere.test/?redirect=https://api.example.org
  - https://api.example.org:bad/path
  - https://unrelated.test\\@api.example.org
  - ftp://api.example.org/file
https://api.example.org/as-key: unrelated
"""
    result = check({"settings.yml": config, "package-lock.json": '{"uri": "https://api.example.org"}',
                    "review.md": "https://api.example.org", "app.json": '{"x": ["https://api.example.org."]}'})
    assert result == {"signs": [("example", HOST, "app.json", 1), ("example", HOST, "settings.yml", 2)], "gaps": []}
    assert dict((name, strength) for name, strength, _ in service_registry.CHECKERS)["host"] == "mentioned"


@pytest.mark.parametrize(("grammar", "path", "source"), [
    ("python", "app.py", '# "https://api.example.org"\nx = f"https://api.example.org/{token}"'),
    ("typescript", "app.ts", '// "https://api.example.org"\nconst x = `https://api.example.org/?t=${token}`;'),
    ("php", "app.php", '<?php // https://api.example.org\n$x = "https://api.example.org/$token";'),
    ("elixir", "app.ex", '# https://api.example.org\nu = "https://api.example.org/#{token}"'),
    ("csharp", "App.cs", '// https://api.example.org\nvar u = $"https://api.example.org/{token}";'),
    ("kotlin", "App.kt", '// https://api.example.org\nval u = "https://api.example.org/$token"'),
    ("rust", "app.rs", '// https://api.example.org\nconst U: &str = r#"https://api.example.org/"#;'),
    ("go", "app.go", 'package app // https://api.example.org\nconst U = `https://api.example.org/`'),
])
def test_source_literals_and_comments(grammar, path, source):
    if not registry_hosts.ts.get_parser(grammar):
        pytest.skip(f"missing {grammar} grammar")
    assert check({path: source}) == {"signs": [("example", HOST, path, 2)], "gaps": []}


def test_interpolation_cannot_complete_a_hostname():
    if not registry_hosts.ts.get_parser("javascript"):
        pytest.skip("missing JavaScript grammar")
    source = 'const a = `https://api.example.org${suffix}/`; const b = `https://${user}@api.example.org`;'
    assert check({"app.js": source}) == {"signs": [], "gaps": []}


def test_unreadable_input_returns_a_gap_without_sensitive_values(monkeypatch):
    monkeypatch.setattr(registry_hosts.ts, "get_parser", lambda *_: None)
    result = check({"app.py": 'url = "https://api.example.org/private"', "app.yaml": 'url: ["https://api.example.org/private"'})
    assert not result["signs"]
    assert {gap["path"] for gap in result["gaps"]} == {"app.py", "app.yaml"}
    assert "private" not in repr(result)


def test_host_evidence_reaches_the_stack_without_claiming_a_configured_service(tmp_path):
    import snapshot
    import technologies

    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text('{"name":"worker"}', encoding="utf-8")
    (project / "settings.yaml").write_text('url: https://api.telegram.org/bot/credential', encoding="utf-8")
    (project / ".env").write_text('URL=https://api.telegram.org/not-read', encoding="utf-8")
    manifest = tmp_path / "output" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    result = technologies.ensure(manifest)
    mention = next(e for e in result["mentioned"] if e["id"] == "telegram")
    assert mention["signs"] == [{"sign": "host", "strength": "mentioned", "value": "api.telegram.org",
                                 "path": "settings.yaml", "line": 1}]
    assert "telegram" not in {e["id"] for e in result["technologies"]}
    assert not any("telegram" in unit["services"] for unit in result["units"])
    assert result["configured_services"] == []
