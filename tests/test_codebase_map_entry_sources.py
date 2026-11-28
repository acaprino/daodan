"""A manifest alone cannot certify the wrong package, or hide the failure of another reader."""
import json
from unittest.mock import Mock

import pytest

from test_codebase_map_container_runner import manifest_of, entry_points, premap
import flows
from premap import cargo, python_build, renovate
from entry_points import nextjs, noir, react_router
from entry_points.flow_entries import evidence


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
    from entry_points.flow_entries import declarations
    from snapshot_store import open_snapshot
    with open_snapshot(manifest) as store:  # an older pre-map carried the declared entries, bound to the symbols
        report["declared_entries"] = declarations(report["units"], store)
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
    entry_points.write(manifest, sources=(noir,), runner=run)
    for _ in range(2):
        rows, gaps = evidence(manifest)
        assert [(r["path"], r["symbol"]) for r in rows] == [("/save", "api.py::save")]
        assert [(g["kind"], g.get("path")) for g in gaps] == [("outside_snapshot", "/other/api.py")]
        links = flows.cached_links(manifest, [])
        assert gaps[0] in links["source_gaps"]
        assert any(row["symbol"] == "api.py::save" and row.get("path") == "/save" for row in links["entries"])
    assert run.call_count == 1


def test_a_framework_source_runs_only_for_a_framework_the_stack_found():
    """`find_entry_points` follows the stack: a source `registry_build.READERS` names runs for an id of it the stack found, Noir
    on every project, and without the stack's ids (None) every source runs. Each source READERS names is one of `SOURCES`."""
    from registry_build import READERS
    readers = {entry_points._reader(source) for source in entry_points.SOURCES}
    assert {path for path in READERS.values() if path.startswith("entry_points/")} == readers - {"entry_points/noir.py"}
    assert entry_points._chosen(None, None) == entry_points.SOURCES
    assert entry_points._chosen(None, []) == (noir,)
    assert entry_points._chosen(None, ["remixrun", "tailwind"]) == (noir, react_router)


def test_the_entry_points_follow_the_frameworks_of_the_stack_record_of_its_inventory(tmp_path):
    """A stack record of this inventory chooses the sources, and the record is stale once it names other frameworks; a stack
    that did not run, or a record of another inventory, chooses nothing."""
    import stack_recognition
    from snapshot_store import inventory_digest, open_snapshot
    _, manifest = manifest_of(tmp_path, {"web/package.json": '{"dependencies": {"next": "15.0.0"}}\n'})
    with open_snapshot(manifest) as store:
        digest = inventory_digest(store)
    asked = []

    def run(commands):
        asked.extend(command["tool"] for command in commands)
        return [{"root": "/work", "returncode": 1, "stdout": "", "stderr": "no tool here"} for _ in commands]

    def stack(ids, inventory=digest, ran="ran"):
        stack_recognition.path(manifest).write_text(json.dumps({
            "schema": stack_recognition.SCHEMA, "inventory_digest": inventory,
            "checkers": [{"checker": "stack-analyser", "state": ran}],
            "found": [{"id": ident, "category": "framework", "signs": [{"source": "stack-analyser"}]} for ident in ids]}),
            encoding="utf-8")

    stack(["nodejs"])
    record = entry_points.ensure(manifest, sources=(noir, nextjs), runner=run)
    assert [s["source"].partition("@")[0] for s in record["sources"]] == ["noir"] and nextjs.NAME not in asked
    assert entry_points.state(manifest, sources=(noir, nextjs), runner=run)["state"] == "fresh"
    stack(["nextjs", "nodejs"])
    assert entry_points.state(manifest, sources=(noir, nextjs), runner=run)["state"] == "stale"
    record = entry_points.ensure(manifest, sources=(noir, nextjs), runner=run)
    assert [s["source"].partition("@")[0] for s in record["sources"]] == ["noir", "next"] and nextjs.NAME in asked
    for other in ({"inventory": "another"}, {"ran": "failed"}):  # every source again
        stack([], **other)
        assert entry_points.state(manifest, sources=(noir, nextjs), runner=run)["state"] == "fresh"


def test_the_entry_points_are_a_step_of_their_own_after_scan(tmp_path):
    """`scan` writes the pre-map and no entry point; `find_entry_points`, the step after it, writes their record and says what
    it does under its own name."""
    import pipeline
    _, manifest = manifest_of(tmp_path, {"api.py": "def submit():\n    pass\n"})
    result = pipeline.run(manifest, start="scan", stop="scan", fast_scan=True)
    assert "failed" not in result["scan"] and not entry_points.path(manifest).exists()
    seen = []
    result = pipeline.run(manifest, listeners=[seen.append], start="find_entry_points", stop="find_entry_points",
                          fast_scan=True)
    assert result["find_entry_points"]["entry_points"] == str(entry_points.path(manifest))
    assert entry_points.state(manifest)["state"] == "fresh"
    assert {event["step"] for event in seen} == {"find_entry_points"}
