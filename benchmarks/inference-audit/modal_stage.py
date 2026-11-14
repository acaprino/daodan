"""The engine pass's indexer stages on Modal, against the graph the benchmark builds from the same index. No model.

One container per case (`chi`, `semver`, `tududi`), with the base system only, over the snapshot and road A that
`modal_scip.py` keeps under `scip-inputs/<case>` and the case's checkout at its commit:
1. the stage of each indexer entry of `resolve_edges.ENGINES` serving a language of the snapshot
   (`resolve_edges.index_stage`): it installs and runs the indexer, builds the graph and writes the store; a copy of
   each index it reads is kept;
2. the benchmark's build of the same languages from those copies, as `modal_scip.join` builds them: the graph's
   counts, the comparison with road A and the hand checks, which `fetch` sets beside
   `results/scip-<case>-confirm.json`;
3. the store the benchmark writes from that build (`code_graph.write_store`) beside the stage's, row by row;
4. every call only road A resolves, and what the stage's store holds for it: a hole with its class, or an edge
   with its verdict.

    modal deploy benchmarks/inference-audit/modal_stage.py
    python benchmarks/inference-audit/modal_stage.py spawn --cases chi,semver,tududi
    python benchmarks/inference-audit/modal_stage.py fetch --cases chi,semver,tududi
"""
from __future__ import annotations

import collections
import importlib
import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
SCRIPTS = str(PLUGIN / "scripts")
RESULTS = HERE / "results"
TAG = "inference-audit"
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
import plugin_scripts  # noqa: E402
from modal_audit import CASES, _source  # noqa: E402

AUDIT = ("modal_audit.py", "modal_scip.py", "plugin_scripts.py", "probe.py")


def _image():
    """The base system: each indexer module downloads what it runs (`indexers/runtime.py`)."""
    image = (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "ca-certificates")
        .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
    )
    for name in AUDIT:
        image = image.add_local_file(HERE / name if LOCAL else Path("/audit") / name, f"/audit/{name}")
    return image


app = modal.App("daodan-stage-audit", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def _rows(path: Path) -> dict:
    """Every row of a store's edge, hole and external tables, sorted."""
    import sqlite3
    connection = sqlite3.connect(path)
    try:
        return {table: sorted(tuple("" if value is None else str(value) for value in row)
                              for row in connection.execute(f"SELECT * FROM {table}"))
                for table in ("edges", "holes", "externals")}
    finally:
        connection.close()


def _counts(path: Path) -> dict:
    import sqlite3
    connection = sqlite3.connect(path)
    try:
        return {"edges": {f"{language} {verdict}": count for language, verdict, count in connection.execute(
                    "SELECT language, verdict, count(*) FROM edges GROUP BY 1, 2 ORDER BY 1, 2")},
                "holes": {f"{language} {cls}": count for language, cls, count in connection.execute(
                    "SELECT language, class, count(*) FROM holes GROUP BY 1, 2 ORDER BY 1, 2")}}
    finally:
        connection.close()


def _only_a(references: dict, answers: dict, store: Path) -> dict:
    """Each call only road A gives a project target, by what the stage's store holds for it."""
    import sqlite3
    import modal_scip as ms
    connection = sqlite3.connect(store)
    found = collections.Counter()
    examples = collections.defaultdict(list)
    try:
        for identity, reference in references.items():
            if reference["kind"] == "read":
                continue
            lexical = reference["lexical"] if reference["resolution"] == "resolved" else None
            _a_cls, a_target, _source_name = ms._road_a(answers.get(identity), lexical)
            _b_cls, b_targets, _detail, _best = ms._road_b(reference)
            if not a_target or b_targets:
                continue
            holes = [row[0] for row in connection.execute("SELECT class FROM holes WHERE reference_id=?",
                                                          (identity,))]
            edges = [row[0] for row in connection.execute("SELECT verdict FROM edges WHERE reference_id=?",
                                                          (identity,))]
            key = f"hole {holes[0]}" if holes else f"edge {sorted(set(edges))[0]}" if edges else "absent"
            found[key] += 1
            if len(examples[key]) < 5:
                examples[key].append(f"{reference['site']} {reference['name']}")
    finally:
        connection.close()
    return {"by_store": dict(found.most_common()), "examples": dict(examples)}


@app.function(cpu=4, memory=12288, timeout=1800, volumes={"/results": volume})
def stage_case(name: str) -> dict:
    """One case: the product's stages, the benchmark's build of the same index, the two stores, road A's own."""
    import shutil
    import time
    import code_graph
    import modal_scip as ms
    import resolve_edges as rx
    from snapshot_store import open_snapshot
    code = plugin_scripts.code_sha256()
    print("code", code, flush=True)  # compared with the checkout before trusting the run
    started = time.time()
    work = Path("/work") / name  # the kept snapshot binds its sources here
    shutil.rmtree(work, ignore_errors=True)
    kept = Path("/results") / TAG / "scip-inputs" / name
    case = CASES[name]
    target = _source(work / "src", case, None)
    manifest = work / "snapshot/manifest.sqlite"
    manifest.parent.mkdir(parents=True)
    shutil.copyfile(kept / "manifest.sqlite", manifest)
    answers_path = work / "answers.sqlite"
    shutil.copyfile(kept / "answers.sqlite", answers_path)
    with open_snapshot(manifest) as store:
        present = rx.snapshot_languages(store.connection)
    specs = [spec for spec in rx.ENGINES if spec.indexer
             and any(rx.ENGINE_LANGUAGES.get(language) is spec for language in present)]
    result = {"case": name, "commit": case["commit"], "code": code, "stages": {}}
    stage_store, copies = work / "stage-edges.sqlite", []
    for spec in specs:
        module = importlib.import_module(f"indexers.{spec.indexer}")
        original = module.index

        def keeping(*args, _original=original, _spec=spec, **kwargs):
            out = _original(*args, **kwargs)
            for number, (path, prefix) in enumerate(out.get("indexes", ())):
                copy = work / "indexes" / _spec.name / f"{number}.scip"
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, copy)
                copies.append((copy, prefix, _spec, out.get("indexer")))
            return out

        module.index = keeping
        begun = time.time()
        try:
            report = rx.index_stage(spec, manifest, target, out=stage_store)
        finally:
            module.index = original
        result["stages"][spec.name] = {"seconds": round(time.time() - begun, 1),
                                       "report": {key: report.get(key) for key in (
                                           "available", "engine", "indexer", "languages", "reason", "install")}}
        print("stage", spec.name, json.dumps(result["stages"][spec.name])[:600], flush=True)
    if not copies:
        result["error"] = "no stage wrote an index"
        return _save(name, result, started)
    import sqlite3
    db = sqlite3.connect(answers_path)
    answers = {row[0]: row[1:] for row in db.execute(
        "SELECT reference_id, verdict, target_id, file, line, column FROM answers")}
    db.close()
    bench_store = work / "bench-edges.sqlite"
    with code_graph.Snapshot(manifest) as snap:
        index = code_graph.Index(snap.root)
        for path, prefix, _spec, _indexer in copies:
            index.load(path, prefix)
        languages = sorted({language for rel, language in snap.languages.items()
                            if language in ms.ADAPTERS and rel in snap.inventory
                            and rx.ENGINE_LANGUAGES.get(language) is not None
                            and rx.ENGINE_LANGUAGES[language].indexer})
        hops = {}
        for adapter in sorted({ms.ADAPTERS[language] for language in languages}):
            hops.update(importlib.import_module(f"indexers.{adapter}").hops(index))
        traversal = code_graph.Traversal(index, snap, hops)
        built, references_all, result["graphs"] = {}, {}, {}
        indexers = {spec.indexer: indexer for _path, _prefix, spec, indexer in copies}
        for language in languages:
            adapter = importlib.import_module(f"indexers.{ms.ADAPTERS[language]}")
            rels = sorted(snap.checkout[rel] for rel in snap.inventory
                          if snap.languages.get(rel) == language and rel in snap.checkout)
            absent = [rel for rel in rels if rel not in index.documents]
            reasons = adapter.missing(index, absent) if hasattr(adapter, "missing") and absent else {}
            static = adapter.static(index) if hasattr(adapter, "static") else None
            graph, references = code_graph.build(index, snap, language, hops, indexers[ms.ADAPTERS[language]],
                                                 reasons, traversal, static)
            built[language] = (graph, references)
            references_all.update(references)
            result["graphs"][language] = {"report": code_graph.report(graph),
                                          "road_a": ms._compare(references, answers)}
        resolver = {language: rx.ENGINE_LANGUAGES[language].name for language in languages}
        for spec_name in sorted(set(resolver.values())):
            engine = result["stages"][spec_name]["report"]["engine"]
            code_graph.write_store(snap, bench_store,
                                   {language: built[language] for language in languages
                                    if resolver[language] == spec_name}, engine)
    result["hand"] = ms._hand(list(ms.HAND.get(name, ())), references_all, answers)
    result["hand_score"] = {"checks": len(result["hand"]), "b_right": sum(row["b_right"] for row in result["hand"]),
                            "a_right": sum(row["a_right"] for row in result["hand"])}
    stage_rows, bench_rows = _rows(stage_store), _rows(bench_store)
    result["stores"] = {"equal": stage_rows == bench_rows, "stage": _counts(stage_store),
                        "bench": _counts(bench_store),
                        "differences": {table: {"only_stage": len(set(stage_rows[table]) - set(bench_rows[table])),
                                                "only_bench": len(set(bench_rows[table]) - set(stage_rows[table]))}
                                        for table in stage_rows}}
    result["only_a"] = _only_a(references_all, answers, stage_store)
    return _save(name, result, started)


def _save(name: str, result: dict, started: float) -> dict:
    import time
    result["seconds"] = round(time.time() - started, 1)
    destination = Path("/results") / TAG / f"scip-{name}-stage.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    return result


def against_confirm(result: dict, confirm: dict) -> dict:
    """The stage run's graph counts, road A cells and hand score beside the confirmation's."""
    out = {}
    for language, graph in result.get("graphs", {}).items():
        before = confirm["join"]["languages"][language]
        out[language] = {key: [graph["report"][key], before["graph"][key]] for key in ("nodes", "edges")}
        out[language]["road_a_cells_equal"] = graph["road_a"]["cells"] == before["road_a"]["cells"]
    out["hand_b_right"] = [result.get("hand_score", {}).get("b_right"), confirm["join"]["hand_score"]["b_right"]]
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch"))
    parser.add_argument("--cases", default="chi,semver,tududi")
    args = parser.parse_args()
    chosen = [c.strip() for c in args.cases.split(",") if c.strip()]
    if args.command == "spawn":
        print("local code", plugin_scripts.code_sha256(), flush=True)
        function = modal.Function.from_name("daodan-stage-audit", "stage_case")
        for name in chosen:
            print(name, function.spawn(name).object_id)
    else:
        RESULTS.mkdir(parents=True, exist_ok=True)
        for name in chosen:
            result = json.loads(b"".join(volume.read_file(f"{TAG}/scip-{name}-stage.json")))
            confirm = json.loads((RESULTS / f"scip-{name}-confirm.json").read_text(encoding="utf-8"))
            result["against_confirm"] = against_confirm(result, confirm)
            (RESULTS / f"scip-{name}-stage.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n",
                                                             encoding="utf-8", newline="\n")
            print(name, json.dumps({"stores_equal": result.get("stores", {}).get("equal"),
                                    "only_a": result.get("only_a", {}).get("by_store"),
                                    "against_confirm": result["against_confirm"],
                                    "stages": {key: {"seconds": value["seconds"],
                                                     "indexer": value["report"].get("indexer")}
                                               for key, value in result.get("stages", {}).items()}}))
