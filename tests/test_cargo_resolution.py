"""Resolve Cargo's archived container output, without running the project or fetching crates."""
import gzip
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

from premap import cargo  # noqa: E402


def workspace_answers():
    path = ROOT / "benchmarks/project-model/results/premap-runs/sys-rust-workspace.json.gz"
    runs = json.loads(gzip.decompress(path.read_bytes()))["runs"]
    return [r for r in runs if r["command"]["tool"] == "cargo"]


def read(runs):
    context = SimpleNamespace(inventory=SimpleNamespace(headers={}))
    return cargo.read(context, [r["command"] for r in runs], [r["result"] for r in runs])


def test_workspace_graph_preserves_which_member_introduces_each_dependency():
    result = read(workspace_answers())
    graph, = result["facts"]["package_graphs"]
    assert (graph["ecosystem"], graph["path"]) == ("crates", "Cargo.toml")
    nodes = graph["nodes"]
    members = {node["manifest"]: node for node in nodes if "manifest" in node}
    assert sorted(members) == [f"crates/{member}/Cargo.toml" for member in ("cli", "core", "macros")]
    assert [(node["name"], node["version"]) for node in nodes if "manifest" not in node] == [
        ("cfg-if", "1.0.0"), ("itoa", "1.0.19")]
    assert {name: [nodes[e["to"]]["name"] for e in node["dependencies"]] for name, node in members.items()} == {
        "crates/cli/Cargo.toml": ["ledger-core"],
        "crates/core/Cargo.toml": ["cfg-if", "itoa", "ledger-macros"],
        "crates/macros/Cargo.toml": [],
    }
    assert "file:///" not in json.dumps(graph)


def test_a_member_can_supply_the_resolved_graph_after_the_root_falls_back_to_no_deps():
    runs = workspace_answers()
    root = [r for r in runs if r["command"]["cwd"] == "."]
    locked = next(r for r in root if "--locked" in r["command"]["argv"])
    locked["result"].update(returncode=101, stderr="missing lockfile")
    partial = read(root)
    assert "package_graphs" not in partial["facts"]
    assert any("missing lockfile" in gap["detail"] for gap in partial["gaps"])

    later = next(r for r in runs if r["command"]["cwd"] == "crates/core" and "--locked" in r["command"]["argv"])
    graph, = read([*root, later])["facts"]["package_graphs"]
    assert graph == read([later])["facts"]["package_graphs"][0]
    assert graph["resolved_in"] == "crates/core"


def test_a_different_member_resolution_reports_which_graph_was_chosen():
    runs = workspace_answers()
    root, member = (next(r for r in runs if r["command"]["cwd"] == folder and "--locked" in r["command"]["argv"])
                    for folder in (".", "crates/core"))
    data = json.loads(member["result"]["stdout"])
    next(n for n in data["resolve"]["nodes"] if n["deps"])["deps"].clear()
    member["result"]["stdout"] = json.dumps(data)
    result = read([member, root])
    assert result["facts"]["package_graphs"] == read([root])["facts"]["package_graphs"]
    gap, = result["gaps"]
    assert (gap["kind"], gap["path"]) == ("model_partial", "crates/core")


def test_edges_keep_build_development_targets_and_distinct_package_identities():
    run = next(r for r in workspace_answers() if r["command"]["cwd"] == "." and "--locked" in r["command"]["argv"])
    data = json.loads(run["result"]["stdout"])
    core = next(n for n in data["resolve"]["nodes"] if n["id"] in data["workspace_members"] and len(n["deps"]) == 3)
    release = next(p for p in data["packages"] if p["name"] == "itoa")
    local_id = "path+file:///local/path/unpublished#itoa"
    data["packages"].append({**release, "id": local_id, "source": None})
    data["resolve"]["nodes"].append({"id": local_id, "deps": []})
    core["deps"].append({"name": "renamed", "pkg": local_id, "dep_kinds": [
        {"kind": "dev", "target": None}, {"kind": "build", "target": "cfg(unix)"}]})
    run["result"]["stdout"] = json.dumps(data)
    graph, = read([run])["facts"]["package_graphs"]
    nodes = graph["nodes"]
    local, = (i for i, n in enumerate(nodes) if n.get("local"))
    owner = next(n for n in nodes if n.get("manifest") == "crates/core/Cargo.toml")
    assert sum(n["name"] == "itoa" and n["version"] == release["version"] for n in nodes) == 2
    assert [e for e in owner["dependencies"] if e["to"] == local] == [
        {"to": local, "kind": "build", "target": "cfg(unix)"}, {"to": local, "kind": "dev"}]
    assert local_id not in json.dumps(graph)


def test_dangling_edges_leave_a_gap_without_discarding_the_workspace_model():
    run = next(r for r in workspace_answers() if r["command"]["cwd"] == "." and "--locked" in r["command"]["argv"])
    data = json.loads(run["result"]["stdout"])
    data["resolve"]["nodes"][0]["deps"].append({"pkg": "absent", "dep_kinds": [{"kind": None, "target": None}]})
    run["result"]["stdout"] = json.dumps(data)
    result = read([run])
    assert "package_graphs" not in result["facts"]
    assert result["facts"]["units"]
    assert [g["kind"] for g in result["gaps"]] == ["model_partial"]
