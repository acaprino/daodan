"""Flow starts that a tool or manifest declares, resolved only at their snapshot destinations."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import entries
import flows
import premap
import snapshot
from premap import python_build


def test_manifest_declarations_survive_reopening_without_a_source_read(tmp_path, monkeypatch):
    app = tmp_path / "project"
    source = app / "src"
    source.mkdir(parents=True)
    (app / "pyproject.toml").write_text(
        '[project.scripts]\ncheck="entry:check"\nverify="entry:check"\nwrong="entry:missing"\n[project.gui-scripts]\n'
        'viewer="entry:show"\n[tool.setuptools.package-dir]\n""="src"\n')
    (source / "entry.py").write_text("def check(): pass\ndef show(): pass\n")
    (source / "other.py").write_text("def missing(): pass\n")
    (source / "binary.rs").write_text("fn main() {}\n")
    (app / "Cargo.toml").write_text('[package]\nname="reader"\nversion="1.0.0"\n')
    manifest = tmp_path / "manifest.sqlite"
    snapshot.write_snapshot(app, manifest)
    # The saved form of cargo metadata: tests and custom build scripts are not product commands.
    unit = {"kind": "cargo-crate", "root": ".", "manifest": "Cargo.toml", "name": "reader",
            "config": {"targets": [{"kind": kind, "name": kind, "path": "src/binary.rs"}
                                   for kind in ("bin", "test", "custom-build")]}}
    cargo = SimpleNamespace(NAME="cargo", VERSION="fixture", RANK="model", run=lambda _ctx: {"facts": {"units": [unit]}})
    premap.write(manifest, sources=(python_build, cargo))
    premap.modules.ensure_graph(manifest)
    monkeypatch.setattr(premap.modules._Inventory, "text", Mock(side_effect=AssertionError("source read")))
    from premap.flow_entries import evidence
    rows, gaps = evidence(manifest)
    rows = [r for r in rows if r["reader"] == "manifesto"]
    assert {(r["label"], r["symbol"], r["site"], r["kind"]) for r in rows if "gap" not in r} == {
        ("check", "src/entry.py::check", "src/entry.py:1", "comando"),
        ("verify", "src/entry.py::check", "src/entry.py:1", "comando"),
        ("viewer", "src/entry.py::show", "src/entry.py:2", "avvio di un processo"),
        ("bin", "src/binary.rs::main", "src/binary.rs:1", "avvio di un processo")}
    assert [r["label"] for r in rows if r.get("gap")] == ["wrong"]
    assert any(g["kind"] == "noir_unavailable" for g in gaps)
    links = flows.cached_links(manifest, [])
    assert {r["label"] for r in links["entries"] if r.get("reader") == "manifesto"} == {"check", "verify", "viewer", "bin"}
    assert any("entry:missing" in g["reason"] for g in links["gaps"])
    assert rows == [r for r in entries.candidates(links, manifest) if r["reader"] == "manifesto"]


def test_frozen_workflow_triggers_and_service_sites_do_not_guess_a_function_from_a_command(tmp_path, monkeypatch):
    from premap import module_graph, renovate
    from premap.flow_entries import evidence
    from test_codebase_map_premap_container_runner import manifest_of

    workflow = ".github/workflows/sync.yml"
    triggers = {"push": None, "workflow_dispatch": None, "schedule": [{"cron": "0 4 * * *"}]}
    _, manifest = manifest_of(tmp_path, {
        workflow: "on:\n  push:\n  workflow_dispatch:\n  schedule:\n    - cron: '0 4 * * *'\n"
                  "jobs:\n  sync:\n    uses: org/tools/.github/workflows/sync.yaml@v1\n",
        "compose.yaml": "services:\n  jobs:\n    image: queue\n    command: sync\n",
        "sync.py": "def sync(): pass\n"})
    document = {"on": triggers, "jobs": {"sync": {"uses": "org/tools/.github/workflows/sync.yaml@v1"}}}
    run = Mock(return_value=[
        {"returncode": 0, "stdout": "{}", "stderr": "", "root": "/work"},
        {"returncode": 0, "stdout": f"{workflow}\n{json.dumps(document)}\n", "stderr": "", "root": "/work"}])
    premap.write(manifest, sources=(module_graph, renovate), runner=run)
    premap.modules.ensure_graph(manifest)
    monkeypatch.setattr(premap.modules._Inventory, "text", Mock(side_effect=AssertionError("manifest reread")))
    rows, _ = evidence(manifest)
    assert {(r["label"], r["kind"], r["declared_in"]) for r in rows} == {
        ("push", "evento del repository", f"{workflow}#on.push"),
        ("workflow_dispatch", "comando", f"{workflow}#on.workflow_dispatch"),
        ("0 4 * * *", "orario", f"{workflow}#on.schedule.0.cron"),
        ("jobs", "avvio di un processo", "compose.yaml#L2")}
    assert all(row.get("gap") for row in rows)
    assert next(row for row in rows if row["label"] == "jobs")["site"] == "compose.yaml:2"
    assert all(row["symbol"] != "sync.py::sync" for row in rows)
    assert not any(e["to"] == "sync.py::sync" for e in flows.cached_links(manifest, [])["edges"])
    assert evidence(manifest)[0] == rows
    assert run.call_count == 1
