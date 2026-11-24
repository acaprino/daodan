"""`scan` and `stack` run on the inventory, before `parse` (spec of the pipeline, 8.2 and 8.11 step 5, piece D).

They read no symbol (pieces A, B and C), so on a store that holds only the inventory they write the same pre-map, module graph
and technologies as on the store `parse` has read; and since those are bound to the inventory's digest, `parse` reading the
files afterwards leaves them fresh.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import file_inventory  # noqa: E402
import modules  # noqa: E402
import pipeline  # noqa: E402
import premap  # noqa: E402
import snapshot  # noqa: E402
import technologies  # noqa: E402
from test_codebase_map_module_edges_in_connect import FILES  # noqa: E402

MORE = {"pyproject.toml": '[project]\nname = "tool"\ndependencies = ["flask"]\n\n[project.scripts]\ntool = "tool.cli:main"\n',
        "tool/__init__.py": "", "tool/cli.py": "import os\n\nKEY = 'https://api.pushbullet.com/v2'\n\ndef main():\n    return 0\n",
        "package.json": '{"name":"root","private":true,"workspaces":["libs/*"]}'}


def _project(tmp_path) -> Path:
    root = tmp_path / "proj"
    for rel, text in {**FILES, **MORE}.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="\n")
    return root


def _written(manifest: Path) -> dict:
    """The three files `scan` and `stack` write, without what names this very snapshot file."""
    out = {}
    for name in (premap.FILE, modules.graph_name(manifest).name, technologies.path(manifest).name):
        record = json.loads(manifest.with_name(name).read_text(encoding="utf-8"))
        for key in ("binding",):
            record.pop(key, None)
        if "sources" in record and isinstance(record["sources"], list):
            record["sources"] = [{k: v for k, v in s.items() if k != "seconds"} for s in record["sources"]]
        out[name] = json.loads(json.dumps(record).replace(str(manifest.parent), "<OUT>"))
    return out


def test_the_steps_are_scan_stack_then_parse():
    assert [step.NAME for step in pipeline.STEPS][:3] == ["scan", "stack", "parse"]


def test_scan_and_stack_write_the_same_on_the_inventory_as_on_the_read_snapshot(real_stack, tmp_path):
    root = _project(tmp_path)
    read, listed = tmp_path / "read" / "manifest.sqlite", tmp_path / "listed" / "manifest.sqlite"
    snapshot.write_snapshot(root, read)
    file_inventory.write(root, listed)
    for manifest in (read, listed):
        result = pipeline.run(manifest, start="scan", stop="stack", fast_scan=True)
        assert "failed" not in result["scan"] and "failed" not in result["stack"], result
    assert "pushbullet" in {item["id"] for item in _written(read)[technologies.path(read).name]["mentioned"]}  # a sign read in the text
    assert _written(listed) == _written(read)


def test_the_module_graph_names_the_same_git_state_on_the_inventory(tmp_path):
    """The commit and the dirtiness of the work tree are the tree's, so the inventory records them as the reading does."""
    import subprocess
    root = _project(tmp_path)
    git = ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "one"]):
        subprocess.run([*git, *args], check=True)
    read, listed = tmp_path / "read" / "manifest.sqlite", tmp_path / "listed" / "manifest.sqlite"
    snapshot.write_snapshot(root, read)
    file_inventory.write(root, listed)
    gits = []
    for manifest in (read, listed):
        pipeline.run(manifest, start="scan", stop="scan", fast_scan=True)
        gits.append(json.loads(modules.graph_name(manifest).read_text(encoding="utf-8"))["binding"]["git"])
    assert gits[0] is not None and gits[1] == gits[0]


def test_what_scan_and_stack_wrote_stays_fresh_once_parse_has_read_the_files(tmp_path):
    root = _project(tmp_path)
    manifest = tmp_path / "out" / "manifest.sqlite"
    file_inventory.write(root, manifest)
    result = pipeline.run(manifest, start="scan", stop="parse", fast_scan=True)
    assert result["parse"]["action"] == "read"
    assert premap.state(manifest)["state"] == "fresh"
    assert modules.graph_state(manifest)["state"] == "fresh"
    assert technologies.state(manifest) == "fresh"


def _premap_on_both(tmp_path, files: dict, sources: tuple, runner) -> list[dict]:
    """The pre-map of `sources` on a store `parse` has read and on one that holds only the inventory, of the same files."""
    records, root = [], tmp_path / "proj"
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="\n")
    for name, write in (("read", snapshot.write_snapshot), ("listed", file_inventory.write)):
        manifest = tmp_path / name / "manifest.sqlite"
        write(root, manifest)
        record = premap.write(manifest, sources=sources, runner=runner)
        record["sources"] = [{k: v for k, v in s.items() if k != "seconds"} for s in record["sources"]]
        records.append(json.loads(json.dumps({k: v for k, v in record.items() if k != "binding"}).replace(str(manifest.parent), "<OUT>")))
    return records


def test_angulars_templates_are_found_on_the_inventory(tmp_path):
    """Which files hold components comes from the file's own syntax tree, not from the imports `parse` writes."""
    import test_codebase_map_premap_angular as angular_tests
    files = {rel: text for rel, text in angular_tests.project_files().items() if text is not None}
    read, listed = _premap_on_both(tmp_path, files, (premap.angular,), lambda commands: angular_tests.recorded("fixture.json"))
    assert read["framework_entries"] and listed == read


def test_noirs_absent_line_is_told_on_the_inventory(tmp_path):
    """A line Noir cites is checked against the file's text, not against the line count `parse` writes."""
    endpoints = [{"protocol": "http", "url": url, "method": "POST", "handler": {"path": "/work/api.py", "line": line, "name": "submit"}}
                 for url, line in (("/submit", 1), ("/gone", 99))]
    read, listed = _premap_on_both(tmp_path, {"api.py": "def submit():\n    pass\n"}, (premap.noir,), lambda commands: [
        {"root": "/work", "returncode": 0, "stdout": json.dumps({"endpoints": endpoints}), "stderr": ""}])
    assert any("absent line: 99" in gap.get("detail", "") for gap in read["gaps"]) and listed == read


def test_a_declared_symbol_member_is_checked_once_parse_has_read_the_file(tmp_path):
    """A member `path::symbol` of a declared module: `scan` finds its file in the inventory and leaves the symbol pending,
    reading no symbol; the whole graph checks the symbol, as a whole derivation of the read store does."""
    from unittest import mock
    import snapshot_store
    declared = {"name": "Greeting", "kind": "component", "members": ["app.py::greet", "app.py::gone"], "evidence": ["app.py"]}
    files = {"app.py": "def greet():\n    return 1\n",
             "codebase-modules.json": json.dumps({"schema": modules.DECLARED_SCHEMA, "modules": [declared]})}
    root = tmp_path / "proj"
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="\n")
    read, listed = tmp_path / "read" / "manifest.sqlite", tmp_path / "listed" / "manifest.sqlite"
    snapshot.write_snapshot(root, read)
    file_inventory.write(root, listed)
    pipeline.run(read, start="scan", stop="scan", fast_scan=True)
    with mock.patch.object(snapshot_store.SnapshotStore, "get_file", side_effect=AssertionError("scan read a file's symbols")):
        pipeline.run(listed, start="scan", stop="scan", fast_scan=True)
    pipeline.run(listed, start="parse", stop="parse")

    def greeting(graph):
        return next(m for m in graph["modules"] if m["name"] == "Greeting")
    wholes = [modules.load_graph(Path(modules.ensure_graph(manifest)["graph"])) for manifest in (read, listed)]
    with snapshot_store.open_snapshot(read) as store:
        derived = greeting(modules.derive(store, ledger=[]))
    assert greeting(wholes[0]) == greeting(wholes[1]) == derived
    assert derived["status"] == "incomplete" and [m["resolved"] for m in derived["members"]] == [True, False]
    assert wholes[0]["coverage"] == wholes[1]["coverage"]


SUBMODULE = {".gitmodules": '[submodule "lib"]\n\tpath = lib\n\turl = https://example.invalid/lib.git\n',
             "lib/x.py": "def f():\n    return 1\n", "app.py": "def g():\n    return 2\n"}


def _inventoried(tmp_path, name: str) -> Path:
    root = tmp_path / "proj"
    if not root.exists():
        for rel, text in SUBMODULE.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / name / "manifest.sqlite"
    file_inventory.write(root, manifest)
    return manifest


def test_a_file_the_pre_map_excludes_is_read_by_no_language_adapter_and_says_why(tmp_path):
    """Spec 8.3, point 3, and 8.11 step 5, piece E1: `parse` takes the exclusions from `scan`. A submodule's file keeps its
    inventory language and a file-level entry with the reason; the plan puts it in no parse node."""
    from pipeline import plan as planning
    from snapshot_store import open_snapshot
    manifest = _inventoried(tmp_path, "out")
    result = pipeline.run(manifest, start="scan", stop="parse", fast_scan=True)
    assert result["parse"]["action"] == "read"
    record = premap.ensure(manifest)
    with open_snapshot(manifest) as store:
        excluded, kept = store.get_file("lib/x.py"), store.get_file("app.py")
        rows = list(store.iter_inventory())
    assert excluded["language"] == "python" and not excluded["symbols"] and "excluded: submodule" in excluded["parser_notes"]
    assert "g" in kept["symbols"]
    nodes = {node["id"]: node["on"]["files"] for node in planning.parse_nodes(rows, record)}
    assert nodes.get("parse:python") == 1  # app.py; lib/x.py is in no node, and its entry says why
    assert premap.state(manifest)["state"] == "fresh"  # the exclusion is not written in the inventory's rows


def test_without_the_pre_map_the_reading_is_the_one_of_before(tmp_path):
    manifest = _inventoried(tmp_path, "out")
    snapshot.write_reading(manifest, manifest)
    from snapshot_store import open_snapshot
    with open_snapshot(manifest) as store:
        assert "f" in store.get_file("lib/x.py")["symbols"]


def test_the_plan_parse_tells_after_reading_counts_no_excluded_file(tmp_path):
    """The plan the step says once the files are read (`plan.stored`, the coverage of the read snapshot) agrees with the
    reading: the excluded file is in no parse node, and the step says how many it left out."""
    from pipeline import plan as planning
    from snapshot_store import open_snapshot
    manifest = _inventoried(tmp_path, "out")
    result = pipeline.run(manifest, start="scan", stop="parse", fast_scan=True)
    assert result["parse"]["excluded"] == 1
    with open_snapshot(manifest) as store:
        nodes = {node["id"]: node["on"]["files"] for node in planning.plan(planning.stored(store))["nodes"]}
    assert nodes["parse:python"] == 1


def test_an_excluded_entry_is_never_reused_as_a_reading(tmp_path):
    """A later reading with no pre-map (`write_snapshot`) reads the file again: an entry the plan left out says nothing of
    the file's symbols."""
    from snapshot_store import open_snapshot
    manifest = _inventoried(tmp_path, "out")
    pipeline.run(manifest, start="scan", stop="parse", fast_scan=True)
    again = tmp_path / "again" / "manifest.sqlite"
    with open_snapshot(manifest) as previous:
        snapshot.write_snapshot(tmp_path / "proj", again, previous=previous)
    with open_snapshot(again) as store:
        assert "f" in store.get_file("lib/x.py")["symbols"]


def test_go_enrys_folders_and_files_are_left_out_of_the_reading(tmp_path):
    from snapshot_store import open_snapshot
    root = tmp_path / "proj"
    for rel, text in {"third_party/a.py": "def a():\n    pass\n", "gen.py": "def b():\n    pass\n",
                      "app.py": "def c():\n    pass\n"}.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / "out" / "manifest.sqlite"
    file_inventory.write(root, manifest)
    record = {"excluded": [{"path": "third_party/", "why": "vendored"}, {"path": "gen.py", "why": "generated"}]}
    assert snapshot.write_reading(manifest, manifest, record=record)["excluded"] == 2
    with open_snapshot(manifest) as store:
        notes = {rel: store.get_file(rel)["parser_notes"] for rel in ("third_party/a.py", "gen.py")}
        assert "c" in store.get_file("app.py")["symbols"]
    assert "excluded: vendored" in notes["third_party/a.py"] and "excluded: generated" in notes["gen.py"]


def test_a_reading_with_no_fresh_pre_map_says_it_excludes_nothing(tmp_path):
    manifest = _inventoried(tmp_path, "out")
    seen = []
    result = pipeline.run(manifest, listeners=[seen.append], start="parse", stop="parse")
    assert result["parse"]["excluded"] == 0
    assert [e for e in seen if e["kind"] == "log" and e["level"] == "warning" and "pre-map" in e["message"]]
