"""Python, the whole index read: scip-python on python-semver, every document, occurrence and symbol, as a graph.

Wiring only: the Python adapter (`adapters/python.py`: dependencies, index, the engine's hops), the shared
`scip_graph.py` (reading, traversal, graph) and the volume. One container per case: the checkout at its pinned
commit, the snapshot as the other benchmarks of this folder build it, then the adapter's index. `snapshot.py
write` crashes on a symlinked file (UNIQUE constraint failed: files.path), so the snapshot reads a copy where each
link is a regular file; the adapter reads the checkout itself. Index, engine record, snapshot and checkout stay
on the volume; the graph is rebuilt from them, in the container (`spawn --graph-only`) or here (`graph --dir`),
without running the indexer again. No model.

    modal deploy benchmarks/inference-audit/lang_python.py
    python benchmarks/inference-audit/lang_python.py spawn --cases semver [--graph-only]
    python benchmarks/inference-audit/lang_python.py fetch --cases semver [--files DIR]
    python benchmarks/inference-audit/lang_python.py graph --cases semver --dir DIR

Writes `results/graph-python-<case>.json` (the graph) and `results/graph-python-<case>-checks.json` (the shared
report, the hand check, the run).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
SCRIPTS = str(PLUGIN / "scripts")
RESULTS = HERE / "results"
TAG = "inference-audit"
STORE = f"{TAG}/graph-python"  # per case: engine.json, the index files, run.json, work.tar.gz
LANGUAGE = "python"
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
import scip_graph  # noqa: E402
from adapters import python as adapter  # noqa: E402
from modal_audit import _run, _source  # noqa: E402

CASES = {
    "semver": {"repo": "https://github.com/python-semver/python-semver.git", "target": ".",
               "commit": "b6e83e3e40d3a7570386e8d694ae8011477a55c1"},
}

# Twenty call sites read in the source before any graph existed: (file, line, name, nth on the line, expected).
HAND = [
    ("src/semver/_deprecated.py", 113, "parse", 0, "project src/semver/version.py::Version.parse"),
    ("src/semver/_deprecated.py", 113, "compare", 0,
     "project src/semver/version.py::Version.compare (method of a call result, parse returns T bound to Version)"),
    ("src/semver/_deprecated.py", 399, "deprecated", 0, "project src/semver/_deprecated.py::deprecated"),
    ("src/semver/_deprecated.py", 399, "cmd_bump", 1, "project src/semver/cli.py::cmd_bump (callback passed as value)"),
    ("src/semver/_deprecated.py", 81, "func", 0,
     "dead end: parameter func of deprecated (runtime: the decorated function)"),
    ("src/semver/version.py", 68, "operator", 0,
     "dead end: parameter operator of _comparator (shadows the module operator)"),
    ("src/semver/version.py", 65, "cls", 0,
     "project src/semver/version.py::Version (class, through local cls = type(self))"),
    ("src/semver/version.py", 592, "_comparator", 0, "project src/semver/version.py::_comparator (decorator)"),
    ("src/semver/version.py", 594, "compare", 0,
     "project src/semver/version.py::Version.compare (inside a decorated method)"),
    ("src/semver/version.py", 576, "replace", 0,
     "project src/semver/version.py::Version.replace (method of a call result of a local)"),
    ("src/semver/version.py", 307, "search", 0, "external python-stdlib re.Pattern.search"),
    ("src/semver/version.py", 769, "_native_parse_parts", 0,
     "external fast-semver-rs-backend parse_parts (import alias inside try)"),
    ("src/semver/cli.py", 152, "func", 0,
     "no static target: dynamic attribute of argparse.Namespace (runtime: a cli.cmd_* set by set_defaults)"),
    ("src/semver/cli.py", 101, "cmd_compare", 0, "project src/semver/cli.py::cmd_compare (callback as keyword value)"),
    ("src/semver/__main__.py", 25, "main", 0, "project src/semver/cli.py::main (module attribute of `from semver import cli`)"),
    ("tests/test_pysemver-cli.py", 109, "main", 0,
     "project src/semver/_deprecated.py::main (value deprecated(cli.main), re-exported by semver/__init__)"),
    ("tests/test_subclass.py", 13, "parse", 0, "project src/semver/version.py::Version.parse (super())"),
    ("tests/test_subclass.py", 62, "parse", 0, "project src/semver/version.py::Version.parse (inherited by SemVerSubclass)"),
    ("docs/advanced/coerce.py", 42, "Version", 0,
     "project src/semver/version.py::Version (class re-exported by semver/__init__)"),
    ("tests/test_deprecated_functions.py", 70, "deprecated", 0,
     "project src/semver/_deprecated.py::deprecated (decorator without arguments)"),
]


def _image():
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install(*adapter.APT)
        .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .run_commands(*adapter.install_commands())
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(HERE / "modal_audit.py" if LOCAL else Path("/audit/modal_audit.py"), "/audit/modal_audit.py")
        .add_local_file(HERE / "probe.py" if LOCAL else Path("/audit/probe.py"), "/audit/probe.py")
        .add_local_file(HERE / "scip_graph.py" if LOCAL else Path("/audit/scip_graph.py"), "/audit/scip_graph.py")
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
    )


app = modal.App("daodan-graph-python", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def hand_check(index, traversal, hand: list, sites: set) -> list:
    """The graph's ends at the hand-checked sites, beside what the source reading expected; at a static site
    without the ends reached through an implementation, as `build` leaves them out."""
    out = []
    for rel, line, name, nth, expected in hand:
        text = index.line(rel, line) or ""
        found = [m.start() for m in re.finditer(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", text)]
        column = index.from_bytes(rel, line, len(text[:found[nth]].encode("utf-8"))) if len(found) > nth else None
        found_at = [o for o in index.at.get((rel, line, column), ()) if not o.definition]
        out.append({"site": f"{rel}:{line} {name}", "expected": expected,
                    "graph": [{"symbol": o.key, "ends": [[end.cls, end.key, end.target, end.detail, list(end.chain)]
                                                         for end in traversal.ends(o.key)
                                                         if not ("implementation" in end.chain and
                                                                 (rel, line, index.to_bytes(rel, line, o.start)) in sites)]}
                              for o in found_at]
                    or "no occurrence"})
    return out


def write(folder: Path, manifest: Path, source: Path, name: str) -> tuple[dict, dict]:
    """The graph and its checks from the stored files of `folder`."""
    engine = json.loads((folder / "engine.json").read_text(encoding="utf-8"))
    index = scip_graph.Index(source)
    for path, prefix in engine["indexes"]:
        index.load(folder / Path(path).name, prefix)
    hops = adapter.hops(index)
    with scip_graph.Snapshot(manifest) as snapshot:
        traversal = scip_graph.Traversal(index, snapshot, hops)
        sites = adapter.static(index)
        graph, _ = scip_graph.build(index, snapshot, LANGUAGE, hops, engine["indexer"], None, traversal,
                                    static=sites)
        checks = {"report": scip_graph.report(graph),
                  "hand_check": hand_check(index, traversal, HAND if name == "semver" else [], sites),
                  "static_sites": len(sites), "unknown_fields": dict(index.unknown),
                  "engine": {key: engine.get(key) for key in ("runs", "requirements", "installs", "environment",
                                                              "pyrightconfig", "project")}}
    run = folder / "run.json"
    checks["run"] = json.loads(run.read_text(encoding="utf-8")) if run.is_file() else None
    return graph, checks


def _dump(graph: dict, checks: dict, out: Path, name: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / f"graph-python-{name}.json").write_text(json.dumps(graph, ensure_ascii=False) + "\n", encoding="utf-8",
                                                   newline="\n")
    (out / f"graph-python-{name}-checks.json").write_text(json.dumps(checks, indent=1, ensure_ascii=False) + "\n",
                                                          encoding="utf-8", newline="\n")


def local_manifest(folder: Path) -> Path:
    """A copy of the stored snapshot whose root is the snapshot's source extracted into `folder/snapshot-src`."""
    import shutil
    import sqlite3
    from snapshot_store import _pack
    copy = folder / "snapshot/manifest-local.sqlite"
    shutil.copyfile(folder / "snapshot/manifest.sqlite", copy)
    with sqlite3.connect(copy) as connection:
        connection.execute("UPDATE metadata SET value = ? WHERE key = 'root'",
                           (_pack(str((folder / "snapshot-src").resolve())),))
    return copy


def _tar(work: Path, destination: Path, folders: tuple) -> None:
    import tarfile
    with tarfile.open(destination, "w:gz") as tar:
        for folder in folders:
            tar.add(work / folder, arcname=folder,
                    filter=lambda item: None if ".git" in Path(item.name).parts else item)


@app.function(cpu=2, memory=6144, timeout=3600, volumes={"/results": volume})
def index_case(name: str) -> dict:
    import hashlib
    import os
    import shutil
    import time
    started = time.time()
    print("code", scip_graph.code_sha256(), flush=True)  # compared with the checkout before trusting the run
    loaded = Path(adapter.__file__)
    case = CASES[name]
    work = Path("/work") / name
    shutil.rmtree(work, ignore_errors=True)  # a warm container keeps the previous call's files
    target = _source(work / "src", case, None)
    links = {p.relative_to(target).as_posix(): os.readlink(p) for p in target.rglob("*")
             if p.is_symlink() and ".git" not in p.relative_to(target).parts}
    shutil.copytree(work / "src", work / "snapshot-src", symlinks=False)
    _run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(work / "snapshot-src" / case["target"]), "--out",
          str(work / "snapshot" / "manifest.sqlite"), "--no-engine", "--no-index"])
    run = {"case": name, "repo": case["repo"], "commit": case["commit"], "adapter": str(loaded),
           "adapter_sha256": hashlib.sha256(loaded.read_bytes()).hexdigest(), "symlinks_copied_for_snapshot": links,
           "snapshot_seconds": round(time.time() - started, 1)}
    engine = adapter.index(target, work / "engine")
    run["seconds"] = round(time.time() - started, 1)
    store = Path("/results") / STORE / name
    store.mkdir(parents=True, exist_ok=True)
    for path, _prefix in engine["indexes"]:
        shutil.copyfile(path, store / Path(path).name)
        shutil.copyfile(path, work / Path(path).name)
    for folder, item in ((store, "engine.json"), (work, "engine.json")):
        (folder / item).write_text(json.dumps(engine, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for folder in (store, work):
        (folder / "run.json").write_text(json.dumps(run, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    _tar(work, store / "work.tar.gz", ("src", "snapshot-src", "snapshot"))
    volume.commit()
    if not engine["indexes"]:
        return {**run, "error": "no index", "runs": engine["runs"]}
    graph, checks = write(work, work / "snapshot" / "manifest.sqlite", work / "snapshot-src" / case["target"], name)
    _dump(graph, checks, Path("/results") / TAG, name)
    volume.commit()
    return {**run, "edges": len(graph["edges"]), "holes": len(graph["holes"])}


@app.function(cpu=1, memory=3072, timeout=1800, volumes={"/results": volume})
def graph_case(name: str) -> dict:
    """The graph again from the stored index, engine record, snapshot and checkout."""
    import shutil
    import tarfile
    store = Path("/results") / STORE / name
    work = Path("/work") / name
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    with tarfile.open(store / "work.tar.gz") as tar:
        tar.extractall(work, filter="tar")
    for item in store.iterdir():
        if item.is_file() and item.name != "work.tar.gz":
            shutil.copyfile(item, work / item.name)
    target = CASES[name]["target"]
    graph, checks = write(work, work / "snapshot" / "manifest.sqlite", work / "snapshot-src" / target, name)
    _dump(graph, checks, Path("/results") / TAG, name)
    volume.commit()
    return {"case": name, "edges": len(graph["edges"]), "holes": len(graph["holes"])}


if __name__ == "__main__":
    import argparse
    import hashlib

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "graph"))
    parser.add_argument("--cases", default="semver")
    parser.add_argument("--graph-only", action="store_true")
    parser.add_argument("--files", help="with fetch: also copy each case's stored files into this directory")
    parser.add_argument("--dir", help="with graph: a directory filled by fetch --files, work.tar.gz extracted")
    args = parser.parse_args()
    chosen = [c.strip() for c in args.cases.split(",") if c.strip()]
    if args.command == "spawn":
        print("local adapter", hashlib.sha256((HERE / "adapters" / "python.py").read_bytes()).hexdigest())
        function = modal.Function.from_name("daodan-graph-python", "graph_case" if args.graph_only else "index_case")
        for name in chosen:
            print(name, function.spawn(name).object_id)
    elif args.command == "fetch":
        for name in chosen:
            for suffix in ("", "-checks"):
                data = b"".join(volume.read_file(f"{TAG}/graph-python-{name}{suffix}.json"))
                (RESULTS / f"graph-python-{name}{suffix}.json").write_bytes(data.replace(b"\r\n", b"\n"))
                print(name + suffix, len(data))
            if args.files:
                folder = Path(args.files) / name
                folder.mkdir(parents=True, exist_ok=True)
                for entry in volume.listdir(f"{STORE}/{name}"):
                    item = Path(entry.path).name
                    (folder / item).write_bytes(b"".join(volume.read_file(f"{STORE}/{name}/{item}")))
    else:
        for name in chosen:
            folder = Path(args.dir) / name
            graph, checks = write(folder, local_manifest(folder), folder / "snapshot-src" / CASES[name]["target"], name)
            _dump(graph, checks, RESULTS, name)
            print(name, len(graph["nodes"]), len(graph["edges"]), len(graph["holes"]))
