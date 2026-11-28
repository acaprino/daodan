"""`recognize_stack` and `find_modules` run on the inventory, before `link_calls` needs the files read (spec of the pipeline, 8.2
and 8.11 step 5, piece D).

They read no symbol (pieces A, B and C), so on a store that holds only the inventory they write the same pre-map, module graph
and technologies as on the store the reading has written (`snapshot.read_project`, the one reading); and since those are bound
to the inventory's digest, reading the files afterwards leaves them fresh.
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
import entry_points  # noqa: E402
import premap  # noqa: E402
import stack_recognition  # noqa: E402
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
    """The four files `stack` and `scan` write, without what names this very snapshot file."""
    out = {}
    for name in (stack_recognition.FILE, premap.FILE, modules.graph_name(manifest).name, technologies.path(manifest).name):
        record = json.loads(manifest.with_name(name).read_text(encoding="utf-8"))
        for key in ("binding",):
            record.pop(key, None)
        if "sources" in record and isinstance(record["sources"], list):
            record["sources"] = [{k: v for k, v in s.items() if k != "seconds"} for s in record["sources"]]
        out[name] = json.loads(json.dumps(record).replace(str(manifest.parent), "<OUT>"))
    return out


def test_the_steps_are_the_stack_the_modules_the_entry_points_then_the_calls():
    assert [step.NAME for step in pipeline.STEPS][:4] == ["recognize_stack", "find_modules", "find_entry_points", "link_calls"]


def test_scan_and_stack_write_the_same_on_the_inventory_as_on_the_read_snapshot(real_stack, tmp_path):
    root = _project(tmp_path)
    read, listed = tmp_path / "read" / "manifest.sqlite", tmp_path / "listed" / "manifest.sqlite"
    snapshot.read_project(root, read)
    file_inventory.write(root, listed)
    for manifest in (read, listed):
        result = pipeline.run(manifest, stop="find_modules", fast_scan=True)
        assert "failed" not in result["find_modules"] and "failed" not in result["recognize_stack"], result
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
    snapshot.read_project(root, read)
    file_inventory.write(root, listed)
    gits = []
    for manifest in (read, listed):
        pipeline.run(manifest, start="find_modules", stop="find_modules", fast_scan=True)
        gits.append(json.loads(modules.graph_name(manifest).read_text(encoding="utf-8"))["binding"]["git"])
    assert gits[0] is not None and gits[1] == gits[0]


def test_what_scan_and_stack_wrote_stays_fresh_once_the_files_are_read(tmp_path):
    root = _project(tmp_path)
    manifest = tmp_path / "out" / "manifest.sqlite"
    file_inventory.write(root, manifest)
    result = pipeline.run(manifest, stop="find_modules", fast_scan=True)
    assert "failed" not in result["find_modules"] and "failed" not in result["recognize_stack"], result
    snapshot.read_project(root, manifest)  # the reading replaces the store that held only the inventory
    assert premap.state(manifest)["state"] == "fresh"
    assert modules.graph_state(manifest)["state"] == "fresh"
    assert technologies.state(manifest) == "fresh"


def _premap_on_both(tmp_path, files: dict, sources: tuple, runner) -> list[dict]:
    """The entry points of `sources` on a store `parse` has read and on one that holds only the inventory, of the same files."""
    records, root = [], tmp_path / "proj"
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="\n")
    for name, write in (("read", snapshot.read_project), ("listed", file_inventory.write)):
        manifest = tmp_path / name / "manifest.sqlite"
        write(root, manifest)
        record = entry_points.write(manifest, sources=sources, runner=runner)
        record["sources"] = [{k: v for k, v in s.items() if k != "seconds"} for s in record["sources"]]
        records.append(json.loads(json.dumps({k: v for k, v in record.items() if k not in ("binding", "bound")}).replace(str(manifest.parent), "<OUT>")))  # `bound`: the binder needs the read store
    return records


def test_angulars_templates_are_found_on_the_inventory(tmp_path):
    """Which files hold components comes from the file's own syntax tree, not from the imports `parse` writes."""
    import test_codebase_map_premap_angular as angular_tests
    files = {rel: text for rel, text in angular_tests.project_files().items() if text is not None}
    read, listed = _premap_on_both(tmp_path, files, (entry_points.angular,), lambda commands: angular_tests.recorded("fixture.json"))
    assert read["framework_entries"] and listed == read


def test_noirs_absent_line_is_told_on_the_inventory(tmp_path):
    """A line Noir cites is checked against the file's text, not against the line count `parse` writes."""
    endpoints = [{"protocol": "http", "url": url, "method": "POST", "handler": {"path": "/work/api.py", "line": line, "name": "submit"}}
                 for url, line in (("/submit", 1), ("/gone", 99))]
    read, listed = _premap_on_both(tmp_path, {"api.py": "def submit():\n    pass\n"}, (entry_points.noir,), lambda commands: [
        {"root": "/work", "returncode": 0, "stdout": json.dumps({"endpoints": endpoints}), "stderr": ""}])
    assert any("absent line: 99" in gap.get("detail", "") for gap in read["gaps"]) and listed == read


def test_a_declared_symbol_member_is_checked_once_the_file_is_read(tmp_path):
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
    snapshot.read_project(root, read)
    file_inventory.write(root, listed)
    pipeline.run(read, start="find_modules", stop="find_modules", fast_scan=True)
    with mock.patch.object(snapshot_store.SnapshotStore, "get_file", side_effect=AssertionError("scan read a file's symbols")):
        pipeline.run(listed, start="find_modules", stop="find_modules", fast_scan=True)
    snapshot.read_project(root, listed)

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


def test_a_file_the_pre_map_excludes_is_read_like_any_other_and_the_plan_counts_it(tmp_path):
    """The `excluded` facet of the pre-map is a label, not a choice of the reading (the owner's decision of 24 November
    2026): the one reading, `read_project`, reads a submodule's file, and the plan counts it."""
    from pipeline import plan as planning
    from snapshot_store import open_snapshot
    root = tmp_path / "proj"
    for rel, text in SUBMODULE.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(root, manifest)
    result = pipeline.run(manifest, start="find_modules", stop="find_modules", fast_scan=True)
    assert "failed" not in result["find_modules"], result
    record = json.loads(premap.path(manifest).read_text(encoding="utf-8"))
    assert [(entry["path"], entry["why"]) for entry in record["excluded"]] == [("lib/", "submodule"),
                                                                              (".gitmodules", "vendored")]
    with open_snapshot(manifest) as store:
        assert "f" in store.get_file("lib/x.py")["symbols"] and "g" in store.get_file("app.py")["symbols"]
        planned = planning.plan(planning.stored(store))
    assert {node["id"]: node["on"]["files"] for node in planned["nodes"]}["parse:python"] == 2
