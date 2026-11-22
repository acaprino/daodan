"""A manifest alone cannot certify the wrong package, or hide the failure of another reader."""
import json
from unittest.mock import Mock

import pytest

from test_codebase_map_premap_container_runner import manifest_of, premap
import flows
from premap import cargo, noir, python_build, renovate
from premap.flow_entries import evidence


@pytest.mark.parametrize("extra", [
    {"pyproject.toml": '[tool.setuptools.package-dir]\n""="lib"\npkg="src/real"\n"pkg.deep"="relocated"\n'},
    {"setup.cfg": "[options]\npackage_dir =\n    =lib\n    pkg=src/real\n    pkg.deep=relocated\n"},
])
def test_setuptools_uses_the_longest_package_mapping_after_reopen(tmp_path, extra, monkeypatch):
    scripts = '[project.scripts]\nrun="pkg.cli:main"\ninside="pkg.deep:main"\nother="pkgx.cli:main"\nmissing="pkg.ghost:main"\n'
    files = {"sub/" + p: "def main(): pass\n" for p in (
        "src/real/cli.py", "pkg/cli.py", "lib/pkg/cli.py", "lib/pkg/ghost.py",
        "relocated/__init__.py", "relocated.py", "lib/pkgx/cli.py")}
    files.update({"sub/" + p: value for p, value in extra.items()})
    files["sub/pyproject.toml"] = scripts + files.get("sub/pyproject.toml", "")
    _, manifest = manifest_of(tmp_path, files)
    premap.write(manifest, sources=(python_build,))
    monkeypatch.setattr(premap.modules._Inventory, "text", Mock(side_effect=AssertionError("source reread")))
    rows, _ = evidence(manifest)
    assert {r["label"]: r["symbol"] for r in rows if not r.get("gap")} == {
        "run": "sub/src/real/cli.py::main", "inside": "sub/relocated/__init__.py::main",
        "other": "sub/lib/pkgx/cli.py::main"}
    assert [r["label"] for r in rows if r.get("gap")] == ["missing"]


def test_legacy_python_entries_wait_for_refresh_but_cargo_stays_available(tmp_path):
    _, manifest = manifest_of(tmp_path, {"pkg/cli.py": "def main(): pass\n", "pyproject.toml":
        '[project.scripts]\nrun="pkg.cli:main"\n[tool.setuptools.package-dir]\npkg="src/real"\n'})
    report = premap.write(manifest, sources=(python_build,))
    report["sources"][0]["source"] = "python-build@daodan/premap/v2"
    report["declared_entries"][0].update(symbol="pkg/cli.py::main", site="pkg/cli.py:1")
    report["declared_entries"][0].pop("gap", None)
    report["declared_entries"].append({"reader": "manifesto", "shape": "cargo.bin", "label": "worker",
                                      "site": "bin.rs:1", "symbol": "bin.rs::main", "declared_in": "Cargo.toml"})
    premap.path(manifest).write_text(json.dumps(report))
    rows, gaps = evidence(manifest)
    assert [r["symbol"] for r in rows if not r.get("gap")] == ["bin.rs::main"]
    assert any(g["kind"] == "declared_entries_unavailable" and g["source"] == "python-build" for g in gaps)


def test_failed_cargo_and_yaml_return_the_original_gaps_without_rerunning(tmp_path):
    workflow = ".github/workflows/task.yml"
    _, manifest = manifest_of(tmp_path, {"Cargo.toml": "[package]\nname='sample'\nversion='0.1.0'\n",
                                         "src/main.rs": "fn main() {}\n", workflow: "on: [\n"})
    def run(commands):
        return [{"root": "/work", **({"returncode": 1, "stdout": "", "stderr": "invalid Cargo manifest"}
                if cmd["tool"] == "cargo" else {"returncode": 0, "stdout": "{}", "stderr": ""}
                if cmd["argv"][0] == "renovate" else {"returncode": 0, "stdout": f"{workflow}\nnull\n",
                 "stderr": f"{workflow}: YAMLParseError: expected a closing bracket"})} for cmd in commands]
    record = premap.write(manifest, sources=(cargo, renovate), runner=run)
    failed = [g for g in record["gaps"] if g["kind"] == "model_failed"]
    assert {g["path"] for g in failed} == {".", workflow}
    for _ in range(2):
        _, gaps = evidence(manifest)
        assert all(g in gaps for g in failed)
        links = flows.cached_links(manifest, [])
        assert all(g in links["source_gaps"] for g in failed)


def test_one_endpoint_outside_the_project_survives_as_a_gap_beside_the_valid_route(tmp_path):
    _, manifest = manifest_of(tmp_path, {"api.py": "def save(): pass\n"})
    def route(url, file):
        return {"protocol": "http", "method": "POST", "url": url,
                "handler": {"path": file, "name": "save", "line": 1}}
    run = Mock(return_value=[{"root": "/work", "returncode": 0, "stderr": "", "stdout": json.dumps({"endpoints": [
        route("/bad", "/other/api.py"), route("/save", "/work/api.py")]})}])
    premap.write(manifest, sources=(noir,), runner=run)
    for _ in range(2):
        rows, gaps = evidence(manifest)
        assert [(r["path"], r["symbol"]) for r in rows] == [("/save", "api.py::save")]
        assert [(g["kind"], g.get("path")) for g in gaps] == [("outside_snapshot", "/other/api.py")]
        links = flows.cached_links(manifest, [])
        assert gaps[0] in links["source_gaps"]
        assert any(row["symbol"] == "api.py::save" and row.get("path") == "/save" for row in links["entries"])
    assert run.call_count == 1
