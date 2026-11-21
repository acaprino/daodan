"""Project declarations and Cargo's resolved package versions in the pre-map view."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan" / "core"))

import app_view  # noqa: E402


def _view(resolved):
    module = {"id": "app", "name": "app", "paths": ["app"], "libraries": [
        {"name": "shared", "ecosystem": "crates", "version": "^2", "path": "app/Cargo.toml", "line": 7},
        {"name": "shared", "ecosystem": "npm", "version": "*", "path": "app/package.json"}],
        "resolved_libraries": [{"name": name, "ecosystem": "crates", "version": version, "direct": direct,
                                "path": "Cargo.toml"} for name, version, direct in resolved]}
    stack = {"technologies": [], "modules": [module]}
    return app_view.premap(stack, {}, {})["units"][0]["dependencies"]


def test_direct_resolution_joins_the_declaration_while_a_transitive_version_keeps_its_own_evidence():
    rows = _view([("shared", "2.1", True), ("shared", "1.3", False)])
    assert rows == [
        {"name": "shared", "scope": "crates", "state": "declared_resolved", "version": "^2",
         "source": "app/Cargo.toml:7", "resolution_source": "Cargo.toml", "resolved_version": "2.1", "direct": True},
        {"name": "shared", "scope": "npm", "state": "declared", "version": "*", "source": "app/package.json"},
        {"name": "shared", "scope": "crates", "state": "resolved", "resolved_version": "1.3",
         "source": "Cargo.toml", "direct": False}]


def test_a_declaration_with_multiple_direct_versions_keeps_its_own_row():
    rows = _view([("shared", "2.1", True), ("shared", "2.2", True)])
    assert [row["state"] for row in rows] == ["declared", "declared", "resolved", "resolved"]
    assert [row["resolved_version"] for row in rows[2:]] == ["2.1", "2.2"]
