"""Java, the whole index read: scip-java on javapoet, every document, occurrence and symbol, rebuilt as a graph.

Wiring only: the Java adapter (`adapters/java.py`) builds and indexes, the shared `scip_graph.py` reads the
index and assembles the graph, this file runs them on Modal, keeps their inputs on the volume and checks the
case. One container: the checkout of the `javapoet` case of `modal_audit.py`, the snapshot as the other
benchmarks of this folder build it, then the adapter's index. Indexes, snapshot and checkout stay on the
volume; the graph is rebuilt from them, in the container or here, without running the indexer again. No model.

    modal deploy benchmarks/inference-audit/lang_java.py
    python benchmarks/inference-audit/lang_java.py spawn
    python benchmarks/inference-audit/lang_java.py fetch [--files DIR]
    python benchmarks/inference-audit/lang_java.py graph --dir DIR

`graph` writes `results/graph-java-javapoet.json` (the graph) and `results/graph-java-javapoet-checks.json`
(the shared report, agreement with the lexical resolver, overload check, hand check).
"""
from __future__ import annotations

import collections
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
import code_graph as scip_graph  # noqa: E402
import indexers.java  # noqa: E402
from adapters import java  # noqa: E402
from modal_audit import CASES, _source  # noqa: E402

CASE = "javapoet"
LANGUAGE = "java"
STORE = f"{TAG}/graph-java/{CASE}"
RESULT = f"graph-java-{CASE}.json"
CHECKS = f"graph-java-{CASE}-checks.json"
STORED = ("index.scip", "index-forward.scip", "engine.json", "javap.json", "run.json")

# ---------------------------------------------------------------------------------------------------------
# The case: the hand check

# Written from the source before the graph was read. Each site: file, line, the callee's name, which
# occurrence of that name on the line, what makes it hard, the expected target (descriptor without the
# overload disambiguator, parameter types) and the implementations the index should state for a dispatch
# (a local one by its definition's `file:line`).
# The `out.emit("")` site was first written with line 236, a typo for its line 235, fixed after run r1.
# The anonymous Appendable of JavaFile.java:48 was missed at first; added after run r2, read in the source.
JP = "com/squareup/javapoet/"
MAIN = "src/main/java/com/squareup/javapoet/"
HAND_CHECK = [
    (MAIN + "TypeName.java", 221, "emit", 0, "virtual call, five overrides",
     (JP + "TypeName#emit", "CodeWriter"),
     [(JP + c + "#emit", "CodeWriter") for c in
      ("ArrayTypeName", "ClassName", "ParameterizedTypeName", "TypeVariableName", "WildcardTypeName")]),
    (MAIN + "TypeName.java", 220, "CodeWriter", 1, "constructor, three overloads",
     (JP + "CodeWriter#<init>", "Appendable"), []),
    (MAIN + "TypeName.java", 252, "get", 0, "static overload, four candidates",
     (JP + "TypeName#get", "TypeMirror, Map"), []),
    (MAIN + "TypeName.java", 235, "emit", 0, "overload, four candidates",
     (JP + "CodeWriter#emit", "String"), []),
    (MAIN + "JavaFile.java", 169, "createSourceFile", 0, "call through a JDK interface implemented in tests",
     ("javax/annotation/processing/Filer#createSourceFile", "CharSequence, Element..."),
     [(JP + "TestFiler#createSourceFile", "CharSequence, Element...")]),
    (MAIN + "TypeName.java", 208, "toString", 0, "unqualified call to a final override of Object",
     (JP + "TypeName#toString", ""), []),
    (MAIN + "CodeBlock.java", 125, "add", 0, "method reference to a private nested class",
     (JP + "CodeBlock#CodeBlockJoiner#add", "CodeBlock"), []),
    (MAIN + "CodeBlock.java", 124, "builder", 0, "static call inside a lambda",
     (JP + "CodeBlock#builder", ""), []),
    (MAIN + "CodeBlock.java", 143, "add", 0, "overload inside a lambda",
     (JP + "CodeBlock#Builder#add", "CodeBlock"), []),
    (MAIN + "CodeBlock.java", 123, "of", 0, "JDK overload, two candidates",
     ("java/util/stream/Collector#of", "Supplier, BiConsumer, BinaryOperator, Function, Characteristics..."), []),
    (MAIN + "CodeWriter.java", 74, "this", 0, "this(...) constructor delegation",
     (JP + "CodeWriter#<init>", "Appendable, String, Set, Set"), []),
    (MAIN + "CodeWriter.java", 405, "join", 0, "static import of a JDK overload",
     ("java/lang/String#join", "CharSequence, Iterable"), []),
    (MAIN + "CodeWriter.java", 198, "add", 0, "generic private nested class inside a lambda",
     (JP + "CodeWriter#Multiset#add", "T"), []),
    (MAIN + "CodeWriter.java", 198, "forEach", 0, "default method inherited by List",
     ("java/lang/Iterable#forEach", "Consumer"), []),
    (MAIN + "ClassName.java", 82, "isAnnotated", 0, "super call, not dispatched",
     (JP + "TypeName#isAnnotated", ""), []),
    (MAIN + "ClassName.java", 82, "isAnnotated", 1, "call to the override in a final class",
     (JP + "ClassName#isAnnotated", ""), []),
    (MAIN + "ClassName.java", 59, "super", 0, "super(...) constructor call, three constructors",
     (JP + "TypeName#<init>", "List"), []),
    ("src/test/java/com/squareup/javapoet/AbstractTypesTest.java", 263, "box", 0,
     "inherited method on a subclass receiver", (JP + "TypeName#box", ""), []),
    ("src/test/java/com/squareup/javapoet/AbstractTypesTest.java", 263, "assertThat", 0,
     "static import, two imported classes", ("com/google/common/truth/Truth#assertThat", "Object"), []),
    (MAIN + "LineWrapper.java", 158, "append", 0, "call through a JDK interface implemented in the project",
     ("java/lang/Appendable#append", "CharSequence"),
     [(JP + "LineWrapper#RecordingAppendable#append", "CharSequence"), (MAIN + "JavaFile.java:48", "CharSequence")]),
]
# External classes the hand check names, whose class-file member order gives the overload of `name(+n)`.
HAND_CHECK_CLASSES = {
    "": ["java.lang.String", "java.util.stream.Collector", "java.lang.Iterable", "java.lang.Appendable",
         "javax.annotation.processing.Filer"],
    "com/google/truth/truth/1.4.4/truth-1.4.4.jar": ["com.google.common.truth.Truth"],
}

# ---------------------------------------------------------------------------------------------------------
# Modal wiring


def _image():
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "curl", "ca-certificates", *java.APT)
        .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .run_commands(*java.install_commands())
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(HERE / "modal_audit.py" if LOCAL else Path("/audit/modal_audit.py"), "/audit/modal_audit.py")
        .add_local_file(HERE / "probe.py" if LOCAL else Path("/audit/probe.py"), "/audit/probe.py")
        .add_local_file(HERE / "plugin_scripts.py" if LOCAL else Path("/audit/plugin_scripts.py"),
                        "/audit/plugin_scripts.py")
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
    )


app = modal.App("daodan-graph-java", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def _tar(source: Path, destination: Path, skip: tuple = ()) -> None:
    import tarfile
    with tarfile.open(destination, "w:gz") as tar:
        tar.add(source, arcname=".", filter=lambda info: None if any(
            part in skip for part in Path(info.name).parts) else info)


class _Peak:
    """The resident memory of every process of the container, summed, sampled twice a second."""

    def __init__(self):
        import threading
        self.peak, self.stop = 0, threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        import os
        while not self.stop.is_set():
            total = 0
            for pid in os.listdir("/proc"):
                if pid.isdigit():
                    try:
                        total += int(Path(f"/proc/{pid}/statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE")
                    except (OSError, ValueError, IndexError):
                        pass
            self.peak = max(self.peak, total)
            self.stop.wait(0.5)


@app.function(cpu=4, memory=8192, timeout=3600, volumes={"/results": volume})
def index_case(label: str = "") -> dict:
    import shutil
    import time
    started = time.time()
    print("code", plugin_scripts.code_sha256(), flush=True)  # compared with the checkout before trusting the run
    peak = _Peak()
    peak.thread.start()
    case = CASES[CASE]
    work = Path("/work") / CASE
    store = Path("/results") / STORE
    store.mkdir(parents=True, exist_ok=True)
    target = _source(work / "src", case, None)
    manifest = work / "snapshot/manifest.sqlite"
    run = {"case": CASE, "commit": case["commit"], "label": label}
    run["snapshot"] = scip_graph.measured([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out",
                                           str(manifest), "--no-engine", "--no-index"], SCRIPTS, None, 1800)
    engine = java.index(target, work, None, HAND_CHECK_CLASSES)
    engine["indexes"] = [[Path(path).name, prefix] for path, prefix in engine["indexes"]]
    (work / "engine.json").write_text(json.dumps(engine, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    _tar(manifest.parent, store / "snapshot.tar.gz")
    _tar(target, store / "source.tar.gz", skip=(".git",))
    peak.stop.set()
    run["container_processes_peak_mb"] = round(peak.peak / 2 ** 20)
    run["seconds"] = round(time.time() - started, 1)
    (work / "run.json").write_text(json.dumps(run, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for name in STORED:
        if (work / name).is_file():
            shutil.copyfile(work / name, store / name)
    if engine["indexes"]:
        try:
            write(work, manifest, target, store)
        except Exception:
            import traceback
            run["graph_error"] = traceback.format_exc()[-3000:]
    volume.commit()
    return run


# ---------------------------------------------------------------------------------------------------------
# The graph


def write(folder: Path, manifest: Path, source: Path, out: Path) -> tuple[Path, Path]:
    """The graph and its checks from the stored files of `folder`, written into `out`."""
    engine = json.loads((folder / "engine.json").read_text(encoding="utf-8"))
    index = scip_graph.Index(source)
    for name, prefix in engine["indexes"]:
        index.load(folder / name, prefix)
    hops, veto, sites = indexers.java.hops(index), indexers.java.same_range(index), indexers.java.static(index)
    with scip_graph.Snapshot(manifest) as snapshot:
        traversal = scip_graph.Traversal(index, snapshot, hops, same_range=veto)
        graph, references = scip_graph.build(index, snapshot, LANGUAGE, hops, engine["indexer"], None, traversal,
                                             static=sites)
        checks = {"report": scip_graph.report(graph),
                  "static": sorted(f"{rel}:{line}:{column}" for rel, line, column in sites),
                  "same_range_vetoed": len(veto),
                  "lexical_agreement": agreement(snapshot, references, traversal)}
    checks["overload_order"] = overload_check(index, folder)
    checks["hand_check"] = hand_check(index, traversal, sites, folder)
    run = folder / "run.json"
    checks["run"] = {"engine_runs": engine["runs"], **(json.loads(run.read_text(encoding="utf-8"))
                                                         if run.is_file() else {})}
    out.mkdir(parents=True, exist_ok=True)
    graph_path, checks_path = out / RESULT, out / CHECKS
    graph_path.write_text(dump(graph), encoding="utf-8", newline="\n")
    checks_path.write_text(json.dumps(checks, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return graph_path, checks_path


def dump(graph: dict) -> str:
    """The graph JSON with one node, edge or hole per line."""
    parts = []
    for name, value in graph.items():
        if isinstance(value, list):
            items = ",\n".join(json.dumps(item, ensure_ascii=False) for item in value)
            parts.append(f"{json.dumps(name)}: [\n{items}\n]" if value else f"{json.dumps(name)}: []")
        else:
            parts.append(f"{json.dumps(name)}: {json.dumps(value, ensure_ascii=False)}")
    return "{\n" + ",\n".join(parts) + "\n}\n"


# ---------------------------------------------------------------------------------------------------------
# The case's checks


def agreement(snapshot, references: dict, traversal) -> dict:
    """Calls the lexical resolver resolves: does the index's direct end name the same declaration?"""
    counts, examples = collections.Counter(), collections.defaultdict(list)
    for identity, _rel, kind, resolution, lexical, _span, _parts, _reason in snapshot.references(LANGUAGE):
        if kind != "call" or resolution != "resolved" or not lexical:
            continue
        entry = references[identity]
        direct = [end for end in entry["ends"] if not end.chain]
        if any(end.target == lexical for end in direct):
            verdict = "same declaration"
        elif any(end.key.endswith("#`<init>`().") or "#`<init>`(+" in end.key for end in direct) and any(
                owner.target == lexical for end in direct for owner in
                traversal.ends(end.key[:end.key.rindex("#") + 1]) if not owner.chain):
            verdict = "lexical the class, index its constructor"
        elif any(end.cls == "project-callable" for end in direct):
            verdict = "different project declaration"
        else:
            verdict = f"index end {'/'.join(sorted({end.cls for end in direct})) or 'none'}"
        counts[verdict] += 1
        if verdict != "same declaration" and len(examples[verdict]) < 5:
            examples[verdict].append(f"{entry['site']} {entry['name']} | lexical {lexical} | index "
                                     f"{[(end.key, end.target) for end in direct]}")
    return {"counts": dict(counts.most_common()), "examples": dict(examples)}


def _base(key: str) -> str:
    """`pkg/Class#method`: a global symbol's descriptors without the overload disambiguator."""
    parts = scip_graph.split_symbol(key)
    marks = {"namespace": "/", "type": "#", "term": ".", "meta": ":", "macro": "!", "method": ""}
    return "".join(name + marks.get(suffix, "") for name, suffix in scip_graph.descriptors(parts[4])).rstrip(".")


def _same(a: str | None, b: str | None) -> bool:
    return a is not None and b is not None and a.replace("...", "[]") == b.replace("...", "[]")


def overload_check(index, folder: Path) -> dict:
    """Project methods: the index signature against the class-file member `name(+n)` names."""
    counts, mismatches = collections.Counter(), []
    for key in index.defs:
        if "#local " in key or scip_graph.node_kind(key, index.info.get(key)) != "method" \
                or index.info.get(key, {}).get("kind") == 9:  # constructors: SymbolInformation.Kind 9
            continue
        name = _base(key).split("#")[-1]
        declaration = java.class_file_declaration(key, folder)
        if declaration is None:
            counts["class file member not found"] += 1
            continue
        a, b = java.parameters(index.info[key]["signature"], name), java.parameters(declaration, name)
        counts["same parameters" if _same(a, b) else "different parameters"] += 1
        if not _same(a, b) and len(mismatches) < 8:
            mismatches.append({"symbol": key, "index": a, "javap": b, "declaration": declaration})
    return {"counts": dict(counts), "mismatches": mismatches}


def hand_check(index, traversal, sites: set, folder: Path) -> dict:
    """The sites of `HAND_CHECK` against the ends the graph gives the same occurrences."""

    def label(key):
        if "#local " in key:
            rel, occurrence = index.defs[key][0] if key in index.defs else (key, None)
            return f"{rel}:{occurrence.line if occurrence else '?'}"
        return _base(key)

    def types(key):
        method = label(key).split("#")[-1]
        if method == "<init>":
            method = label(key).split("#")[-2]
        got = java.parameters(index.info.get(key, {}).get("signature"), method)
        if got is not None:
            return got, "index signature"
        declaration = java.class_file_declaration(key, folder)
        return (java.parameters(declaration, method), "class-file order (javap), not the index") if declaration \
            else (None, None)

    out = []
    for rel, line, name, nth, why, expected, expected_impls in HAND_CHECK:
        text = index.line(rel, line) or ""
        found = sorted((o for o in index.documents.get(rel, ()) if o.line == line == o.end_line
                        and not o.definition and text[o.start:o.end] == name), key=lambda o: o.start)
        row = {"site": f"{rel}:{line}", "name": name, "nth": nth, "why": why,
               "expected": {"target": expected, "implementations": expected_impls}}
        if len(found) <= nth:
            out.append({**row, "verdict": "miss", "reason": "no occurrence of the name on the line"})
            continue
        occurrence = found[nth]
        static = (rel, line, index.to_bytes(rel, line, occurrence.start)) in sites
        ends = [end for end in traversal.ends(occurrence.key) if not static or "implementation" not in end.chain]
        implementers = list(dict.fromkeys(end.key for end in ends if end.chain[:1] == ("implementation",)))
        got_params, overload_from = types(occurrence.key)
        rows = [(label(key), (types(key)[0] or "").replace("...", "[]")) for key in implementers]
        target_ok = label(occurrence.key) == expected[0] and _same(got_params, expected[1])
        impl_ok = sorted(rows) == sorted((b, p.replace("...", "[]")) for b, p in expected_impls)
        out.append({**row, "verdict": "right" if target_ok and impl_ok else "wrong", "target_ok": target_ok,
                    "implementations_ok": impl_ok,
                    "got": {"symbol": occurrence.key, "parameters": got_params, "overload_from": overload_from,
                            "ends": [[end.cls, end.key, list(end.chain)] for end in traversal.ends(occurrence.key)],
                            "implementations": rows, "static": static}})
    return {"right": sum(1 for row in out if row["verdict"] == "right"),
            "target_right": sum(1 for row in out if row.get("target_ok")), "total": len(out), "sites": out}


def local_manifest(folder: Path) -> Path:
    """A copy of the stored snapshot whose root is the checkout extracted into `folder/source`."""
    import shutil
    import sqlite3
    from snapshot_store import _pack
    copy = folder / "snapshot/manifest-local.sqlite"
    shutil.copyfile(folder / "snapshot/manifest.sqlite", copy)
    with sqlite3.connect(copy) as connection:
        connection.execute("UPDATE metadata SET value = ? WHERE key = 'root'", (_pack(str(folder / "source")),))
    return copy


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "graph"))
    parser.add_argument("--label", default="")
    parser.add_argument("--files", help="with fetch: download the stored files of the run here")
    parser.add_argument("--dir", help="with graph: a directory filled by fetch --files")
    args = parser.parse_args()
    if args.command == "spawn":
        function = modal.Function.from_name("daodan-graph-java", "index_case")
        print(CASE, function.spawn(args.label).object_id)
    elif args.command == "fetch":
        folder = Path(args.files or RESULTS)
        folder.mkdir(parents=True, exist_ok=True)
        for name in (RESULT, CHECKS) + (STORED if args.files else ()):
            try:
                data = b"".join(volume.read_file(f"{STORE}/{name}"))
            except Exception as error:
                print(name, "not on the volume:", type(error).__name__)
                continue
            (folder / name).write_bytes(data.replace(b"\r\n", b"\n") if name.endswith(".json") else data)
        if args.files:
            import io
            import tarfile
            for name, into in (("snapshot.tar.gz", "snapshot"), ("source.tar.gz", "source")):
                with tarfile.open(fileobj=io.BytesIO(b"".join(volume.read_file(f"{STORE}/{name}")))) as tar:
                    tar.extractall(folder / into, filter="data")
        print("files in", folder)
    else:
        folder = Path(args.dir).resolve()
        for path in write(folder, local_manifest(folder), folder / "source", RESULTS):
            print(path, path.stat().st_size)
