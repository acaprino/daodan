"""The engine pass's indexer stages on Modal, against the graph the benchmark builds from the same index. No model.

One container per case (`chi`, `semver`, `tududi`), with the base system only, over the snapshot and
road A that `modal_scip.py` keeps under `scip-inputs/<case>` and the case's checkout at its commit (a case that comes
as an archive from its archive there); `python-semver` over the checkout, its copy with each link a regular file and the snapshot of that
copy that `lang_python.py` keeps (`snapshot.py write` stops on a linked file), without road A:
1. the stage of each indexer entry of `resolve_edges.ENGINES` serving a language of the snapshot
   (`resolve_edges.index_stage`): it installs and runs the indexer, builds the graph and writes the store; a copy of
   each index it reads is kept;
2. the benchmark's build of the same languages from those copies, as `modal_scip.join` builds them: the graph's
   counts, the comparison with road A and the hand checks, which `fetch` sets beside
   `results/scip-<case>-confirm.json`;
3. the store the benchmark writes from that build (`code_graph.write_store`) beside the stage's, row by row;
4. every call only road A resolves, and what the stage's store holds for it: a hole with its class, or an edge
   with its verdict;
5. each graph's edges and holes per top folder of the checkout.

`--entries` limits the stages to those entries, and each language an entry lists reads from it in this run
(`_serving`): `--entries scip-python` runs scip-python's stage alone. The
driver gives scip-python its Python projects (`UNITS`), as the pre-map will. A private case's result keeps no
indexer log. `fetch` sets beside each result the stored one it confirms: `results/scip-<case>-confirm.json`,
`CONFIRM` for the others.

`--change` measures the incremental stage instead (`change_case`): each stage whole, again unchanged, after the
case's hand change (`CHANGES`), and whole on the changed copy; `fetch --change` writes
`results/scip-<case>-incremental.json`.

    modal deploy benchmarks/inference-audit/modal_stage.py
    python benchmarks/inference-audit/modal_stage.py spawn --cases chi,semver,tududi [--entries scip-python]
    python benchmarks/inference-audit/modal_stage.py fetch --cases chi,semver,tududi
    python benchmarks/inference-audit/modal_stage.py spawn --cases chi,tududi --change
    python benchmarks/inference-audit/modal_stage.py fetch --cases chi,tududi --change
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
PLUGIN = HERE.parents[1] / "daodan" if LOCAL else Path("/daodan/map")
SCRIPTS = str(PLUGIN / "core")
RESULTS = HERE / "results"
TAG = "inference-audit"
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
import plugin_scripts  # noqa: E402
from modal_audit import CASES, _source  # noqa: E402

# The pipeline benchmark's Modal Sandboxes, where `--change` runs the indexers that build in a container.
PIPELINE = HERE.parents[1] / "benchmarks/project-model/modal_pipeline.py" if LOCAL else Path("/pm/modal_pipeline.py")
AUDIT = ("modal_audit.py", "modal_scip.py", "plugin_scripts.py", "lang_python.py")
# The cases `lang_python.py` keeps on the volume: its work folder (checkout, copy, snapshot) and its case there.
KEPT = {"python-semver": ("graph-python/semver-plugin/work.tar.gz", "semver")}
# The stored result each case's run is set beside, when it is not `scip-<case>-confirm.json`.
CONFIRM = {"python-semver": "graph-python-semver-plugin-checks.json"}
# Each case's Python projects, given to scip-python.
UNITS = {"python-semver": [{"root": ""}]}
# What a run's log holds: a private case's result keeps neither.
LOGS = ("stdout_tail", "stderr_tail")


def _serving(rx, entries: set[str]) -> None:
    """Each language an entry of `entries` lists reads from that entry, in this container only."""
    chosen = [spec for spec in rx.ENGINES if spec.name in entries]
    taken = {language for spec in chosen for language in spec.languages}
    rx.ENGINES = tuple(spec if spec in chosen else spec._replace(
        languages=tuple(language for language in spec.languages if language not in taken)) for spec in rx.ENGINES)
    rx.ENGINE_LANGUAGES = {language: spec for spec in reversed(rx.ENGINES) for language in spec.languages}


def _image():
    """The base system: each indexer module downloads what it runs (`indexers/runtime.py`)."""
    image = (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "ca-certificates", "xz-utils")
        .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "protobuf==7.36.2")
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
        .add_local_file(PIPELINE, "/pm/modal_pipeline.py")
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


def _folders(graph: dict) -> dict:
    """The graph's edges by end and holes by class, per top folder of the sites."""
    out = collections.defaultdict(lambda: {"edges": collections.Counter(), "holes": collections.Counter()})
    for edge in graph["edges"]:
        out[edge["site"].split("/", 1)[0]]["edges"][f"{edge['end']} {edge['kind']}"] += 1
    for hole in graph["holes"]:
        out[hole["site"].split("/", 1)[0]]["holes"][f"{hole['class']} {hole['kind']}"] += 1
    return {folder: {"edges": sum(counts["edges"].values()), "holes": sum(counts["holes"].values()),
                     "edges_by_end": dict(sorted(counts["edges"].items())),
                     "holes_by_class": dict(sorted(counts["holes"].items()))} for folder, counts in sorted(out.items())}


def _prepare(name: str) -> tuple:
    """The case's checkout and its kept snapshot (and road A's answers, when kept) in `/work/<case>`: the work
    folder, the target, the manifest, the answers' path, the commit and whether the case is private."""
    import shutil
    import tarfile
    import modal_scip as ms
    if name in KEPT:  # the folder the kept snapshot binds its sources in
        stored, folder = KEPT[name]
        work = Path("/work") / folder
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        with tarfile.open(Path("/results") / TAG / stored) as tar:
            tar.extractall(work, filter="tar")
        target, manifest, answers_path = work / "src", work / "snapshot/manifest.sqlite", None
        commit = json.loads((Path("/results") / TAG / Path(stored).parent / "run.json").read_text())["commit"]
        private = False
    else:
        work = Path("/work") / name  # the kept snapshot binds its sources here
        shutil.rmtree(work, ignore_errors=True)
        kept = Path("/results") / TAG / "scip-inputs" / name
        case = {**CASES[name], "commit": CASES[name].get("commit") or ms.OPTIONS.get(name, {}).get("commit")}
        archive = (kept / "source.tar").read_bytes() if case.get("tar") else None
        target, commit, private = _source(work / "src", case, archive), case["commit"], archive is not None
        manifest = work / "snapshot/manifest.sqlite"
        manifest.parent.mkdir(parents=True)
        shutil.copyfile(kept / "manifest.sqlite", manifest)
        answers_path = work / "answers.sqlite"
        shutil.copyfile(kept / "answers.sqlite", answers_path)
    return work, target, manifest, answers_path, commit, private


@app.function(cpu=4, memory=12288, timeout=1800, volumes={"/results": volume})
def stage_case(name: str, entries: str = "") -> dict:
    """One case: the product's stages, the benchmark's build of the same index, the two stores, road A's own."""
    import shutil
    import tarfile
    import time
    import code_graph
    import modal_scip as ms
    import resolve_edges as rx
    from snapshot_store import open_snapshot
    code = plugin_scripts.code_sha256()
    print("code", code, flush=True)  # compared with the checkout before trusting the run
    started = time.time()
    work, target, manifest, answers_path, commit, private = _prepare(name)
    with open_snapshot(manifest) as store:
        present = rx.snapshot_languages(store.connection)
    chosen = {entry for entry in entries.split(",") if entry}
    _serving(rx, chosen)
    specs = [spec for spec in rx.ENGINES if spec.indexer and (not chosen or spec.name in chosen)
             and any(rx.ENGINE_LANGUAGES.get(language) is spec for language in present)]
    result = {"case": name, "commit": commit, "code": code, "stages": {}, "contracts": {}}
    stage_store, copies = work / "stage-edges.sqlite", []
    for spec in specs:
        module = importlib.import_module(f"indexers.{spec.indexer}")
        original = module.index

        def keeping(*args, _original=original, _spec=spec, **kwargs):
            if _spec.indexer == "python" and name in UNITS:
                kwargs.setdefault("units", UNITS[name])
            out = _original(*args, **kwargs)
            kept_here = Path("/results") / TAG / "stage-indexes" / name / _spec.name
            kept_here.mkdir(parents=True, exist_ok=True)
            for number, (path, prefix) in enumerate(out.get("indexes", ())):
                copy = work / "indexes" / _spec.name / f"{number}.scip"
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, copy)
                shutil.copyfile(path, kept_here / f"{number}.scip")
                copies.append((copy, prefix, _spec, out.get("indexer")))
            # What the indexer's contract says beyond the index: its environment, its runs.
            result["contracts"][_spec.name] = {key: value for key, value in out.items() if key != "indexes"}
            if private:
                result["contracts"][_spec.name]["runs"] = [{key: value for key, value in run.items()
                                                            if key not in LOGS} for run in out.get("runs", ())]
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
    answers = {}
    if answers_path is not None:
        db = sqlite3.connect(answers_path)
        answers = {row[0]: row[1:] for row in db.execute(
            "SELECT reference_id, verdict, target_id, file, line, column FROM answers")}
        db.close()
    bench_store = work / "bench-edges.sqlite"
    with code_graph.Snapshot(manifest) as snap:
        index = code_graph.Index(snap.root)
        for path, prefix, _spec, _indexer in copies:
            index.load(path, prefix)
        ran = {spec.name for spec in specs}
        languages = sorted({language for rel, language in snap.languages.items()
                            if language in ms.ADAPTERS and rel in snap.inventory
                            and rx.ENGINE_LANGUAGES.get(language) is not None
                            and rx.ENGINE_LANGUAGES[language].name in ran})
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
            result["graphs"][language] = {"report": code_graph.report(graph), "folders": _folders(graph),
                                          "road_a": ms._compare(references, answers) if answers else None}
        resolver = {language: rx.ENGINE_LANGUAGES[language].name for language in languages}
        for spec_name in sorted(set(resolver.values())):
            engine = result["stages"][spec_name]["report"]["engine"]
            code_graph.write_store(snap, bench_store,
                                   {language: built[language] for language in languages
                                    if resolver[language] == spec_name}, engine)
        hand = [check for check in ms.HAND.get(name, ()) if snap.languages.get(check[0]) in languages]
        if name in KEPT:  # lang_python's hand check: the graph's ends at twenty sites read in the source
            import lang_python
            sites = importlib.import_module("indexers.python").static(index)
            result["hand_check"] = lang_python.hand_check(index, traversal, lang_python.HAND, sites)
    result["hand"] = ms._hand(hand, references_all, answers)
    result["hand_score"] = {"checks": len(result["hand"]), "b_right": sum(row["b_right"] for row in result["hand"]),
                            "a_right": sum(row["a_right"] for row in result["hand"])}
    stage_rows, bench_rows = _rows(stage_store), _rows(bench_store)
    result["stores"] = {"equal": stage_rows == bench_rows, "stage": _counts(stage_store),
                        "bench": _counts(bench_store),
                        "differences": {table: {"only_stage": len(set(stage_rows[table]) - set(bench_rows[table])),
                                                "only_bench": len(set(bench_rows[table]) - set(stage_rows[table]))}
                                        for table in stage_rows}}
    result["only_a"] = _only_a(references_all, answers, stage_store) if answers else None
    return _save(name, result, started)


# The hand change of each case for `--change`, written in the README before the run: the file, the text it is
# inserted before, the inserted text (a new function calling one of the file's own, which moves the lines below).
CHANGES = {
    "chi": ("middleware/nocache.go", "// Unix epoch time\n",
            "// NoCacheTwice wraps a handler in NoCache twice (the incremental benchmark's change).\n"
            "func NoCacheTwice(h http.Handler) http.Handler { return NoCache(NoCache(h)) }\n\n"),
    "tududi": ("backend/utils/timezone-utils.js", "/**\n * Convert a date string from user timezone to UTC",
               "// The start of a day in UTC (the incremental benchmark's change).\n"
               "function dayStartUTC(dateString, userTimezone) {\n"
               "    return dateStringToUTC(dateString, userTimezone, 'start');\n}\n\n"),
}
def _on_modal() -> None:
    """An indexer that builds in a container runs in the pipeline benchmark's Modal Sandbox (`engine_on_modal`);
    the hosts the project declares are taken as approved (`egress.preflight`): the measure is of the index, not of
    the approval."""
    sys.path.insert(0, "/pm")
    import container
    import egress
    import modal_pipeline
    modal_pipeline.engine_on_modal(container)
    egress.preflight = lambda project, hosts: ([], [])


def _step(spec_name: str, manifest: Path, target: Path, store: Path) -> dict:
    """One stage: its seconds, its report, the `subset` of each indexer run (None: the whole language; no run: the
    cache), the indexer's peak (`peak_mb` of its report: it runs in a sandbox, not as a child of this process)."""
    import time
    import resolve_edges as rx
    spec = next(spec for spec in rx.ENGINES if spec.name == spec_name)
    module = importlib.import_module(f"indexers.{spec.indexer}")
    original, runs = module.index, []

    def counting(*args, **kwargs):
        subset = kwargs.get("subset")
        runs.append({"subset": None} if subset is None else {"subset": len(subset), "files": subset[:30]})
        return original(*args, **kwargs)

    module.index = counting
    begun = time.time()
    try:
        report = rx.index_stage(spec, manifest, target, out=store)
    except Exception as error:  # noqa: BLE001 - the stage's failure is the step's outcome
        return {"error": f"{type(error).__name__}: {error}", "runs": runs}
    finally:
        module.index = original
    return {"seconds": round(time.time() - begun, 1), "runs": runs,
            "report": {key: report.get(key) for key in ("available", "engine", "indexer", "languages", "reason")}}


@app.function(cpu=4, memory=12288, timeout=3600, volumes={"/results": volume})
def change_case(name: str) -> dict:
    """The incremental stage on one case: each indexer stage of its languages whole (no `index-cache/`), again with
    nothing changed (the language's cache), after the hand change of `CHANGES` (the files it moves: `subset`), and
    whole on the changed copy without the cache, whose store must equal the incremental one row by row."""
    import shutil
    import time
    import resolve_edges as rx
    import snapshot
    from snapshot_store import open_snapshot
    code = plugin_scripts.code_sha256()
    print("code", code, flush=True)
    started = time.time()
    _on_modal()
    work, target, manifest, _answers, commit, _private = _prepare(name)
    # The snapshot read again by this code, so that only the change moves a digest between the steps.
    snapshot.read_project(target, manifest)
    with open_snapshot(manifest) as store:
        present = rx.snapshot_languages(store.connection)
    specs = [spec.name for spec in rx.ENGINES if spec.indexer
             and any(rx.ENGINE_LANGUAGES.get(language) is spec for language in present)]
    rel, before, inserted = CHANGES[name]
    result = {"case": name, "commit": commit, "code": code, "change": {"file": rel, "inserted": inserted},
              "steps": {}}

    def step(label: str) -> Path:
        store = work / f"{label}-edges.sqlite"
        result["steps"][label] = {spec: _step(spec, manifest, target, store) for spec in specs}
        print(label, json.dumps(result["steps"][label])[:1500], flush=True)
        return store

    step("whole")
    step("unchanged")
    path = target / rel
    text = path.read_text(encoding="utf-8")
    assert text.count(before) == 1, f"{rel}: the anchor is not there once"
    path.write_text(text.replace(before, inserted + before), encoding="utf-8")
    begun = time.time()
    snapshot.read_project(target, manifest)
    result["snapshot_seconds"] = round(time.time() - begun, 1)
    changed = step("changed")
    shutil.rmtree(manifest.parent / "index-cache", ignore_errors=True)
    whole = step("changed_whole")
    import sqlite3
    try:
        changed_rows, whole_rows = _rows(changed), _rows(whole)
    except sqlite3.Error as error:  # a step wrote no store: its report says why
        result["stores"] = {"error": f"{type(error).__name__}: {error}"}
        return _save(name, result, started, "incremental")
    result["stores"] = {"equal": changed_rows == whole_rows, "changed": _counts(changed),
                        "differences": {table: {"only_changed": len(set(changed_rows[table]) - set(whole_rows[table])),
                                                "only_whole": len(set(whole_rows[table]) - set(changed_rows[table])),
                                                # the first rows of each side, to read the cause
                                                "examples": {"only_changed": sorted(set(changed_rows[table])
                                                                                    - set(whole_rows[table]))[:20],
                                                             "only_whole": sorted(set(whole_rows[table])
                                                                                  - set(changed_rows[table]))[:20]}}
                                        for table in changed_rows}}
    return _save(name, result, started, "incremental")


def _save(name: str, result: dict, started: float, kind: str = "stage") -> dict:
    import time
    result["seconds"] = round(time.time() - started, 1)
    destination = Path("/results") / TAG / f"scip-{name}-{kind}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    return result


def against_confirm(result: dict, confirm: dict) -> dict:
    """The stage run's graph counts, road A cells and hand score beside the confirmation's: a `modal_scip.py`
    result, or `lang_python.py`'s checks (its report and its hand check, the project's version set to `_`)."""
    out = {}
    if "report" in confirm:
        graph, before = result["graphs"]["python"]["report"], confirm["report"]
        out["python"] = {key: [graph[key], before[key]] for key in ("nodes", "edges")}
        out["python"]["report_keys_differing"] = sorted(key for key in before if key != "indexer"
                                                        and graph.get(key) != before[key])
        version = f" {confirm['engine']['project'][1]} "
        stored = json.loads(json.dumps(confirm["hand_check"]).replace(version, " _ "))
        out["hand_check_equal"] = result.get("hand_check") == stored
        return out
    for language, graph in result.get("graphs", {}).items():
        before = confirm["join"]["languages"][language]
        out[language] = {key: [graph["report"][key], before["graph"][key]] for key in ("nodes", "edges")}
        out[language]["road_a_cells_equal"] = graph["road_a"]["cells"] == before["road_a"]["cells"]
    sites = {row["site"] for row in result.get("hand", ())}
    out["hand_b_right"] = [result.get("hand_score", {}).get("b_right"),
                           sum(row["b_right"] for row in confirm["join"]["hand"] if row["site"] in sites)]
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch"))
    parser.add_argument("--cases", default="chi,semver,tududi")
    parser.add_argument("--entries", default="")
    parser.add_argument("--change", action="store_true", help="the incremental stage around each case's CHANGES")
    args = parser.parse_args()
    chosen = [c.strip() for c in args.cases.split(",") if c.strip()]
    if args.command == "spawn":
        print("local code", plugin_scripts.code_sha256(), flush=True)
        function = modal.Function.from_name("daodan-stage-audit", "change_case" if args.change else "stage_case")
        for name in chosen:
            print(name, (function.spawn(name) if args.change else function.spawn(name, args.entries)).object_id)
    elif args.change:
        RESULTS.mkdir(parents=True, exist_ok=True)
        for name in chosen:
            result = json.loads(b"".join(volume.read_file(f"{TAG}/scip-{name}-incremental.json")))
            (RESULTS / f"scip-{name}-incremental.json").write_text(
                json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            print(name, json.dumps({"stores": result.get("stores"), "snapshot_seconds": result.get("snapshot_seconds"),
                                    "steps": {label: {spec: {key: value.get(key) for key in (
                                        "seconds", "runs", "error")}
                                        for spec, value in specs.items()}
                                        for label, specs in result.get("steps", {}).items()}}))
    else:
        RESULTS.mkdir(parents=True, exist_ok=True)
        for name in chosen:
            result = json.loads(b"".join(volume.read_file(f"{TAG}/scip-{name}-stage.json")))
            confirm = json.loads((RESULTS / CONFIRM.get(name, f"scip-{name}-confirm.json")).read_text(
                encoding="utf-8"))
            result["against_confirm"] = against_confirm(result, confirm)
            (RESULTS / f"scip-{name}-stage.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n",
                                                             encoding="utf-8", newline="\n")
            print(name, json.dumps({"stores_equal": result.get("stores", {}).get("equal"),
                                    "only_a": (result.get("only_a") or {}).get("by_store"),
                                    "against_confirm": result["against_confirm"],
                                    "stages": {key: {"seconds": value["seconds"],
                                                     "indexer": value["report"].get("indexer")}
                                               for key, value in result.get("stages", {}).items()}}))
