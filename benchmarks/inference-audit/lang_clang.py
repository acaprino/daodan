"""C and C++, the whole index read: scip-clang on zlib (C) and tinyxml2 (C++), every document, occurrence and
symbol, rebuilt as a graph.

Wiring only: the adapter (`adapters/clang.py`) builds, indexes and stands in for the snapshot, which reads no
C or C++; the shared `scip_graph.py` reads the index and assembles the graph; this file runs them on Modal,
keeps their inputs on the volume and checks each case. One container per case: the checkout, the product's
snapshot (kept to show what it holds), then the adapter's index. Index, compilation database, package map,
snapshot and checkout stay on the volume (`inference-audit/graph-clang/<case>/`); the graph is rebuilt from
them, in the container or here, without running the indexer again. No model.

    modal deploy benchmarks/inference-audit/lang_clang.py
    python benchmarks/inference-audit/lang_clang.py spawn [--cases zlib,tinyxml2] [--fixtures]
    python benchmarks/inference-audit/lang_clang.py fetch [--cases ...] [--files DIR] [--fixtures]
    python benchmarks/inference-audit/lang_clang.py graph --case zlib --dir DIR

`graph` writes `results/graph-<c|cpp>-<case>.json` (the graph) and `results/graph-<c|cpp>-<case>-checks.json`
(the shared report, the counts proper to C and C++, the hand check). `--fixtures` indexes `fixtures/c` and
`fixtures/cpp`, whose indexes the tests read.
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
AUDIT = HERE if LOCAL else Path("/audit")
TAG = "inference-audit"
sys.path.insert(0, str(AUDIT))
sys.path.insert(0, SCRIPTS)
import scip_graph  # noqa: E402
from adapters import clang as adapter  # noqa: E402
from modal_audit import _source  # noqa: E402

CASES = {
    # C: zlib 1.3.1, CMake; function pointers in its stream and configuration table, macros, `#ifdef` branches.
    "zlib": {"repo": "https://github.com/madler/zlib.git", "commit": "51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf",
             "target": ".", "language": "c"},
    # C++: tinyxml2 11.0.0, CMake; a virtual visitor hierarchy, overloads, templates, operators, namespaces.
    "tinyxml2": {"repo": "https://github.com/leethomason/tinyxml2.git",
                 "commit": "9148bdf719e997d1f474be6bcc7943881046dba1", "target": ".", "language": "cpp"},
}
FIXTURES = {"c": "cfixture@0", "cpp": "cppfixture@0"}
STORE = f"{TAG}/graph-clang"
STORED = ("index.scip", "engine.json", "run.json", "compile_commands.json", "package-map.json", "scip-clang.log")

# ---------------------------------------------------------------------------------------------------------
# The cases: the hand check, written from the source before the graph was read. Each site: file, line, the
# callee's name as written, which occurrence of that name on the line, what makes it hard, and every end
# expected: a project declaration by `file:line` of its body (or prototype), `impl file:line` for an override
# reached through dispatch, `external <name>` for a library function, `value` when the call reaches no
# function (through data, or a macro that calls nothing), `no occurrence` for code the build does not compile.

T = "tinyxml2.cpp"
H = "tinyxml2.h"
X = "xmltest.cpp"
HAND_CHECK: dict[str, list] = {
    "zlib": [
        ("deflate.c", 373, "deflateInit2_", 0, "exported function, same file", ["deflate.c:379"]),
        ("deflate.c", 432, "ZALLOC", 0, "function-like macro calling through strm->zalloc", ["value"]),
        ("deflate.c", 587, "fill_window", 0, "static function (`local` is a macro for static)", ["deflate.c:251"]),
        ("deflate.c", 665, "_tr_init", 0, "defined in trees.c, prototype in deflate.h", ["trees.c:455"]),
        ("deflate.c", 1185, "func", 0, "function pointer in a struct table, through `(*...)`", ["value"]),
        ("deflate.c", 1888, "_tr_tally_lit", 0, "macro with three definitions under #ifdef; the active one calls "
         "nothing", ["value"]),
        ("inflate.c", 1257, "UPDATE_CHECK", 0, "macro whose body calls crc32 or adler32",
         ["adler32.c:128", "crc32.c:1015"]),
        ("inflate.c", 1029, "inflate_fast", 0, "other file", ["inffast.c:50"]),
        ("inflate.c", 391, "zmemcpy", 0, "object-like macro aliasing memcpy", ["external memcpy"]),
        ("crc32.c", 1017, "crc32_z", 0, "defined twice, under #ifdef ARMCRC32 and its #else", ["crc32.c:694"]),
        ("infback.c", 612, "out", 0, "function pointer parameter (callback)", ["value"]),
        ("gzread.c", 184, "gz_error", 0, "ZLIB_INTERNAL function of another file", ["gzlib.c:529"]),
        ("gzread.c", 28, "zstrerror", 0, "macro: strerror(errno), errno a macro calling __errno_location",
         ["external __errno_location", "external strerror"]),
        ("gzlib.c", 235, "open", 0, "libc, after an #ifdef inside the expression", ["external open"]),
        ("zutil.c", 288, "malloc", 0, "libc", ["external malloc"]),
        ("zutil.c", 123, "fprintf", 0, "inside #ifdef ZLIB_DEBUG, not compiled", ["no occurrence"]),
        ("trees.c", 775, "send_bits", 0, "macro chain send_bits, put_short, put_byte: no function", ["value"]),
        ("test/example.c", 175, "deflateInit", 0, "zlib.h macro for deflateInit_", ["deflate.c:371"]),
        ("test/example.c", 184, "CHECK_ERR", 0, "macro calling fprintf and exit", ["external exit", "external fprintf"]),
        ("test/example.c", 523, "test_compress", 0, "file compiled twice (example, example64)", ["test/example.c:60"]),
    ],
    "tinyxml2": [
        (T, 787, "Accept", 0, "virtual, pure in XMLNode, six overrides",
         [f"{H}:934"] + [f"impl {T}:{line}" for line in (782, 1279, 1327, 1377, 1424, 2143)]),
        # The overrides in xmltest.cpp (a visitor class local to main) were missed at first; added after r1,
        # read in the source.
        (T, 1282, "Visit", 0, "virtual and overloaded: Visit(const XMLText&)",
         [f"{H}:505", f"impl {T}:2993", f"impl {X}:2584"]),
        (T, 785, "VisitEnter", 0, "virtual and overloaded: VisitEnter(const XMLDocument&)",
         [f"{H}:483", f"impl {T}:2960", f"impl {X}:2567"]),
        (T, 1199, "~", 0, "explicit call of a virtual destructor",
         [f"{T}:811", f"impl {H}:1020"] + [f"impl {T}:{line}" for line in (1293, 1341, 1390, 1606, 2205)]),
        (T, 1200, "Free", 0, "pure virtual, override in a class template", [f"{H}:334", f"impl {H}:397"]),
        (H, 1992, "Alloc", 0, "member of a dependent type MemPoolT<PoolElementSize>", [f"{H}:371"]),
        (H, 1992, "NodeType", 0, "placement new of a template parameter: no constructor before instantiation",
         ["value"]),
        (H, 1996, "Push", 0, "member of a class template instance", [f"{H}:223"]),
        (T, 2217, "[", 0, "operator[] of a class template, non-const", [f"{H}:253"]),
        (T, 560, "TIXML_SNPRINTF", 0, "object-like macro for snprintf", ["external snprintf"]),
        (T, 1281, "TIXMLASSERT", 0, "macro for assert, itself a macro calling __assert_fail",
         ["external __assert_fail"]),
        (H, 1474, "SetAttribute", 0, "overload (int) among eight", [f"{T}:1545"]),
        (T, 708, "SkipWhiteSpace", 0, "static, overloaded on const: char* argument", [f"{H}:562"]),
        (T, 2742, "PrintSpace", 0, "virtual without override", [f"{T}:2656"]),
        (X, 117, "doc", 0, "default constructor of a declared variable", [f"{T}:2183"]),
        (X, 118, "LoadFile", 0, "overload (const char*)", [f"{T}:2344"]),
        (X, 164, "FirstChildElement", 0, "const and non-const overloads, non-const object", [f"{H}:784"]),
        (X, 166, "printf", 0, "C library", ["external printf"]),
        (X, 489, "XMLTest", 0, "overloads and a template: (int, int) picks the template", [f"{X}:75"]),
        (X, 502, "XMLTest", 0, "overloads and a template: (bool, bool) picks the overload", [f"{X}:70"]),
    ],
}

# ---------------------------------------------------------------------------------------------------------
# Modal wiring


def _image():
    # Ubuntu 24.04: the scip-clang v0.4.1 binary needs glibc 2.38 (Debian 12 has 2.36), whatever its notes say.
    return (
        modal.Image.from_registry("ubuntu:24.04", add_python="3.13")
        .apt_install("git", "curl", "ca-certificates", *adapter.APT)
        .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .run_commands(*adapter.install_commands())
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(AUDIT / "modal_audit.py", "/audit/modal_audit.py")
        .add_local_file(AUDIT / "scip_graph.py", "/audit/scip_graph.py")
        .add_local_dir(AUDIT / "adapters", "/audit/adapters", ignore=["**/__pycache__/**"])
        .add_local_dir(AUDIT / "fixtures/c", "/audit/fixtures/c", ignore=["index.scip"])
        .add_local_dir(AUDIT / "fixtures/cpp", "/audit/fixtures/cpp", ignore=["index.scip"])
    )


app = modal.App("daodan-graph-clang", image=_image())
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


def snapshot_facts(manifest: Path) -> dict:
    """What the product's snapshot holds for the case: files, and those of C or C++."""
    import sqlite3
    with sqlite3.connect(manifest) as connection:
        files = [row[0] for row in connection.execute("SELECT path FROM files")]
        languages = collections.Counter(row[0] for row in connection.execute("SELECT language FROM sem_coverage"))
        references = connection.execute("SELECT count(*) FROM sem_references").fetchone()[0]
    clike = [rel for rel in files if adapter.language_of(rel, "c")]
    return {"files": len(files), "c_or_cpp_files": len(clike), "examples": clike[:5],
            "coverage_languages": {str(key): value for key, value in languages.items()}, "references": references}


@app.function(cpu=4, memory=8192, timeout=3600, volumes={"/results": volume})
def index_case(case: str, label: str = "") -> dict:
    import shutil
    import time
    started = time.time()
    print("code", scip_graph.code_sha256(), flush=True)  # compared with the checkout before trusting the run
    peak = _Peak()
    peak.thread.start()
    spec = CASES[case]
    work = Path("/work") / case
    store = Path("/results") / STORE / case
    store.mkdir(parents=True, exist_ok=True)
    target = _source(work / "src", spec, None)
    manifest = work / "snapshot/manifest.sqlite"
    run = {"case": case, "commit": spec["commit"], "label": label, "code": scip_graph.code_sha256()}
    run["snapshot"] = scip_graph.measured([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out",
                                           str(manifest), "--no-engine", "--no-index"], SCRIPTS, None, 1800)
    run["snapshot_facts"] = snapshot_facts(manifest) if manifest.is_file() else None
    files = adapter.perimeter(target, spec["language"])
    engine = adapter.index(target, work, files, project=f"{case}@{spec['commit'][:12]}")
    engine.update(indexes=[[Path(path).name, prefix] for path, prefix in engine["indexes"]], perimeter=files,
                  mirror=str(work / "mirror"), project=f"{case}@{spec['commit'][:12]}", language=spec["language"])
    (work / "engine.json").write_text(json.dumps(engine, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if manifest.is_file():
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
            write(work, target, store, case)
        except Exception:
            import traceback
            run["graph_error"] = traceback.format_exc()[-3000:]
            (store / "graph-error.txt").write_text(run["graph_error"], encoding="utf-8")
    volume.commit()
    return run


@app.function(cpu=2, memory=4096, timeout=1200, volumes={"/results": volume})
def index_fixtures(label: str = "") -> dict:
    """The two fixtures indexed as the cases are; their indexes and the indexer's help land on the volume."""
    import shutil
    print("code", scip_graph.code_sha256(), flush=True)
    out = {"label": label, "code": scip_graph.code_sha256()}
    for name, project in FIXTURES.items():
        work = Path("/work/fixtures") / name
        source = work / "source"
        shutil.copytree(Path("/audit/fixtures") / name, source)
        engine = adapter.index(source, work, None, project=project)
        store = Path("/results") / STORE / "fixtures" / name
        store.mkdir(parents=True, exist_ok=True)
        for item in ("index.scip", "compile_commands.json", "package-map.json", "scip-clang.log"):
            if (work / item).is_file():
                shutil.copyfile(work / item, store / item)
        engine["indexes"] = [[Path(path).name, prefix] for path, prefix in engine["indexes"]]
        (store / "engine.json").write_text(json.dumps(engine, indent=1) + "\n", encoding="utf-8")
        out[name] = {"index_bytes": engine["runs"][-1]["index_bytes"], "runs": [
            {key: run.get(key) for key in ("step", "returncode", "seconds", "peak_mb", "diagnostics", "stderr_tail")}
            for run in engine["runs"]]}
    volume.commit()
    return out


# ---------------------------------------------------------------------------------------------------------
# The graph


def write(folder: Path, source: Path, out: Path, case: str) -> list[Path]:
    """The graph and its checks from the stored files of `folder`, written into `out`."""
    engine = json.loads((folder / "engine.json").read_text(encoding="utf-8"))
    primary, project, files = engine["language"], engine["project"], engine["perimeter"]
    index = scip_graph.Index(source)
    for name, prefix in engine["indexes"]:
        index.load(folder / name, prefix)
    dropped = adapter.dedupe(index)
    compiled = adapter.compiled_files(folder / "compile_commands.json", engine["mirror"]) \
        if (folder / "compile_commands.json").is_file() else collections.Counter()
    generated = sorted(rel for rel in index.documents if rel not in set(files))
    snapshot = adapter.SyntaxSnapshot(source, files, primary, generated)
    columns = adapter.byte_columns(index)
    adapter.utf8_columns(index)
    enclosed = adapter.enclose(index, snapshot)
    hops = adapter.hops(index, primary)
    veto = adapter.same_range(index)
    traversal = scip_graph.Traversal(index, snapshot, hops, same_range=veto, classify=adapter.classifier(project))
    written, results = [], {}
    for language in sorted(set(snapshot.languages.values())):
        absent = [rel for rel in files if snapshot.languages[rel] == language and not index.documents.get(rel)]
        reasons = adapter.missing(index, absent, compiled, engine.get("removed_by_build", ()))
        graph, references = scip_graph.build(index, snapshot, language, hops, engine["indexer"], reasons, traversal,
                                             refine=adapter.refine)
        results[language] = (graph, references)
    graph, references = results[primary]
    checks = {"report": scip_graph.report(graph),
              "other_languages": {language: scip_graph.report(item[0]) for language, item in results.items()
                                  if language != primary},
              "index": {**index_facts(index, folder, engine, files, compiled), "non_ascii_columns": columns,
                        "enclosing_ranges_set": enclosed, "occurrences_repeated_dropped": dropped,
                        "generated_documents": generated},
              "undeclared_definitions": undeclared(index, snapshot),
              "same_range": {"alias": sum(veto.values()), "never": len(veto) - sum(veto.values())},
              "calls": call_ends(snapshot, references, traversal, primary),
              "constructs": constructs(index, snapshot, traversal, hops, files, primary),
              "holes_by_cause": hole_causes(index, snapshot, references),
              "hand_check": hand_check(index, traversal, HAND_CHECK.get(case, ()))}
    run = folder / "run.json"
    checks["run"] = {"engine_runs": engine["runs"], "package_map": engine.get("package_map"),
                     **(json.loads(run.read_text(encoding="utf-8")) if run.is_file() else {})}
    out.mkdir(parents=True, exist_ok=True)
    name = {"c": "c", "cpp": "cpp"}[primary]
    graph_path, checks_path = out / f"graph-{name}-{case}.json", out / f"graph-{name}-{case}-checks.json"
    graph_path.write_text(dump(graph), encoding="utf-8", newline="\n")
    checks_path.write_text(json.dumps(checks, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    written += [graph_path, checks_path]
    return written


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
# The checks proper to C and C++


def index_facts(index, folder: Path, engine: dict, files: list, compiled: collections.Counter) -> dict:
    perimeter = set(files)
    raw = adapter.roles(folder / engine["indexes"][0][0]) if engine["indexes"] else {}
    sources = [rel for rel in files if Path(rel).suffix.lower() in adapter.C_SUFFIXES | adapter.CPP_SOURCES]
    return {"tools": index.tools, "documents": len(index.documents),
            "documents_outside_perimeter": sorted(rel for rel in index.documents if rel not in perimeter)[:40],
            "documents_repeated": {rel: count for rel, count in index.repeated.items() if count > 1},
            "occurrences": sum(len(items) for items in index.documents.values()),
            "definitions": sum(len(items) for items in index.defs.values()), "symbol_informations": len(index.info),
            "unread_fields": dict(index.unknown), **raw,
            "compilation_database": {
                "generator": "CMake (cmake -S . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON), then cmake --build",
                "commands": sum(compiled.values()), "files": len(compiled),
                "compiled_more_than_once": {rel: count for rel, count in compiled.items() if count > 1},
                "outside_perimeter": sorted(rel for rel in compiled if rel not in perimeter)[:20],
                "perimeter_sources_without_command": len([rel for rel in sources if rel not in compiled]),
                "examples_without_command": [rel for rel in sources if rel not in compiled][:12],
                "removed_by_build": engine.get("removed_by_build"),
                "created_by_build": engine.get("created_by_build")}}


def _label(end, traversal) -> str:
    if end.cls == "project-callable":
        place = end.target.split(" ")[0] if end.target else end.key
        return ("impl " if "implementation" in end.chain else "") + place
    if end.cls == "external":
        return f"external {traversal.package(end.key)['package']}"
    return "value" if end.cls == "project-value" else end.cls


def _target(end) -> str | None:
    """A hand-check label: a project function by `file:line`, an external function by name, else None."""
    if end.cls == "project-callable":
        return ("impl " if "implementation" in end.chain else "") + (end.target.split(" ")[0] if end.target else end.key)
    parts = scip_graph.split_symbol(scip_graph._global(end.key)) if end.cls == "external" else None
    items = scip_graph.descriptors(parts[4]) if parts else []
    return f"external {items[-1][0]}" if items and items[-1][1] == "method" else None


def call_ends(snapshot, references: dict, traversal, language: str) -> dict:
    """Each syntactic call site by what its ends are, and the calls through data by callee shape and value kind."""
    by_end, through_data, examples = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    for entry in references.values():
        ends = entry["ends"]
        if entry["hole"]:
            verdict = f"hole {entry['hole']}"
        elif any(end.cls == "project-callable" and not end.chain for end in ends):
            verdict = "project function, direct" + (" + implementations" if any(
                "implementation" in end.chain for end in ends) else "")
        elif any(end.cls == "project-callable" for end in ends):
            verdict = "project function through " + "/".join(sorted({end.chain[0] for end in ends
                                                                     if end.cls == "project-callable"}))
        elif any(end.cls == "external" for end in ends):
            verdict = "external"
        elif all(end.cls == "project-value" for end in ends):
            verdict = "value only"
            kinds = {end.detail for end in ends}
            through_data["macro expanding to no function call" if "macro" in kinds else
                         "C cast written as a call" if entry["reason"] == "parenthesized" and kinds <= {"class"} else
                         "struct field (function pointer)" if "property" in kinds else
                         "variable or parameter (function pointer)" if kinds & {"variable", "parameter"} else
                         "/".join(sorted(kinds))] += 1
        else:
            verdict = "/".join(sorted({end.cls for end in ends}))
        by_end[verdict] += 1
        if len(examples[verdict]) < 3:
            examples[verdict].append(f"{entry['site']} {entry['name']}")
    shapes = collections.Counter(entry["reason"] for entry in references.values())
    return {"sites": len(references), "by_shape": dict(shapes.most_common()), "by_end": dict(by_end.most_common()),
            "value_only_sites": dict(through_data.most_common()), "examples": dict(examples)}


def constructs(index, snapshot, traversal, hops: dict, files: list, language: str) -> dict:
    """What C and C++ raise, counted: macros, declarations, overloads, dispatch, constructors, operators."""
    syntax = collections.Counter()
    for rel in files:
        found = snapshot.syntax(rel)
        if found is not None:
            syntax.update(found.counts)
    tags = collections.Counter(tag for items in hops.values() for _target, tag in items)
    names = collections.defaultdict(set)
    kinds = collections.Counter()
    for key in index.defs:
        if "#local " in key:
            continue
        parts = scip_graph.split_symbol(key)
        items = scip_graph.descriptors(parts[4]) if parts else []
        if items and items[-1][1] == "method":
            names["/".join(name for name, _ in items[:-1]) + "/" + items[-1][0]].add(key)
        kinds[scip_graph.node_kind(key, index.info.get(key))] += 1
    overloads = {name: len(keys) for name, keys in names.items() if len(keys) > 1}
    implemented = {key: sorted(items) for key, items in index.implementers.items()}
    occurrences = collections.Counter()
    for items in index.documents.values():
        for item in items:
            text = item.key.rsplit(" ", 1)[-1]
            if "operator" in text:
                occurrences["operator" + (" definition" if item.definition else " reference")] += 1
            if "~" in text:
                occurrences["destructor" + (" definition" if item.definition else " reference")] += 1
    return {"syntax": dict(syntax), "hops": dict(tags), "hop_examples": {key: items[:2] for key, items in
                                                                        list(hops.items())[:6]},
            "macros_defined": sum(1 for key in index.defs if key.endswith("!")),
            "project_symbols_by_kind": dict(kinds.most_common()),
            "overloaded_names": len(overloads), "overload_examples": dict(list(overloads.items())[:8]),
            "symbols_with_implementations": len(implemented),
            "implementation_examples": dict(list(implemented.items())[:6]),
            "occurrences": dict(occurrences)}


def undeclared(index, snapshot) -> dict:
    """Project definitions of a function, method or type the syntax stand-in declares nowhere: they grade as
    values, so this is the stand-in's own miss."""
    counts, examples = collections.Counter(), collections.defaultdict(list)
    for key, places in index.defs.items():
        parts = scip_graph.split_symbol(scip_graph._global(key)) if "#local " not in key else None
        items = scip_graph.descriptors(parts[4]) if parts else []
        if not items or items[-1][1] not in ("method", "type"):
            continue
        for rel, occurrence in places:
            if rel not in snapshot.paths:
                continue
            column = index.to_bytes(rel, occurrence.line, occurrence.start)
            kind = items[-1][1]
            if snapshot.function_at(rel, occurrence.line, column):
                counts[f"{kind} declared"] += 1
                continue
            counts[f"{kind} not declared"] += 1
            if len(examples[kind]) < 6:
                examples[kind].append(f"{rel}:{occurrence.line} {items[-1][0]}")
    return {"counts": dict(counts), "examples": dict(examples)}


def hole_causes(index, snapshot, references: dict) -> dict:
    """`no-occurrence` holes by cause: inside a macro's arguments (the index reports the inner references at the
    macro's name, or drops them with the expansion), a preprocessor branch with no occurrence at all (not
    compiled), or other."""
    causes, examples, names = collections.Counter(), collections.defaultdict(list), collections.defaultdict(
        collections.Counter)
    for identity, entry in references.items():
        if entry["hole"] != "no-occurrence":
            continue
        rel, line, column = identity.rsplit(":", 2)
        line, column, found = int(line), int(column), snapshot.syntax(rel)
        node = next((call for call, _name, _shape, at in found.calls if at is not None
                     and (at.start_point[0] + 1, at.start_point[1]) == (line, column)), None) if found else None
        macro = None
        while node is not None and macro is None:
            node = node.parent
            if node is not None and node.type == "call_expression":
                name, _shape = adapter._callee(node.child_by_field_name("function"))
                here = adapter._at(index, rel, name.start_point[0] + 1, name.start_point[1], False) if name else []
                if any(item.key.endswith("!") for item in here):
                    macro = (name, here)
        branch = found.branch(line) if found else None
        if macro is not None:
            named = {scip_graph.descriptors(parts[4])[-1][0] for parts in
                     (scip_graph.split_symbol(scip_graph._global(item.key)) for item in macro[1]) if parts
                     and scip_graph.descriptors(parts[4])}
            cause = "inside a macro's arguments, " + ("reported at the macro's name" if entry["name"] in named
                                                      else "absent from the expansion")
        elif branch and not any(branch[0] <= item.line <= branch[1] for item in index.documents.get(rel, ())):
            cause = "preprocessor branch without any occurrence"
        else:
            cause = f"other, callee {entry['reason']}"
        causes[cause] += 1
        names[cause][entry["name"]] += 1
        if len(examples[cause]) < 3:
            examples[cause].append(f"{entry['site']} {entry['name']}")
    return {"counts": dict(causes.most_common()), "examples": dict(examples),
            "names": {cause: dict(counter.most_common(30)) for cause, counter in names.items()}}


def hand_check(index, traversal, sites) -> dict:
    """Each site: every symbol the index references where the nth occurrence of the name starts (a macro's
    expansion is referenced there too), and the functions their ends reach; `value` when none is reached."""
    out = []
    for rel, line, name, nth, why, expected in sites:
        text = index.line(rel, line) or ""
        starts = sorted({o.start for o in index.documents.get(rel, ()) if o.line == line == o.end_line
                         and not o.definition and text[o.start:o.end] == name})
        row = {"site": f"{rel}:{line}", "name": name, "nth": nth, "why": why, "expected": sorted(expected)}
        if len(starts) <= nth:
            got = ["no occurrence"]
            out.append({**row, "verdict": "right" if got == sorted(expected) else "miss", "got": got})
            continue
        keys = sorted({o.key for o in index.at.get((rel, line, starts[nth]), ()) if not o.definition})
        ends = [end for key in keys for end in traversal.ends(key)]
        got = sorted({label for label in map(_target, ends) if label}) or ["value"]  # no function reached
        out.append({**row, "verdict": "right" if got == sorted(expected) else "wrong", "got": got, "symbols": keys,
                    "ends": [[end.cls, end.key, list(end.chain), end.detail] for end in ends][:12]})
    return {"right": sum(1 for row in out if row["verdict"] == "right"), "total": len(out), "sites": out}


def local_folder(folder: Path) -> Path:
    return folder / "source"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "graph"))
    parser.add_argument("--cases", default=",".join(CASES))
    parser.add_argument("--case")
    parser.add_argument("--label", default="")
    parser.add_argument("--fixtures", action="store_true")
    parser.add_argument("--files", help="with fetch: download the stored files of the run here")
    parser.add_argument("--dir", help="with graph: a directory filled by fetch --files")
    args = parser.parse_args()
    if args.command == "spawn":
        print("local code", scip_graph.code_sha256())
        if args.fixtures:
            print("fixtures", modal.Function.from_name("daodan-graph-clang", "index_fixtures").spawn(args.label).object_id)
        else:
            function = modal.Function.from_name("daodan-graph-clang", "index_case")
            for case in args.cases.split(","):
                print(case, function.spawn(case, args.label).object_id)
    elif args.command == "fetch" and args.fixtures:
        for name in FIXTURES:
            for item in ("index.scip", "engine.json", "scip-clang.log", "compile_commands.json"):
                try:
                    data = b"".join(volume.read_file(f"{STORE}/fixtures/{name}/{item}"))
                except Exception as error:
                    print(name, item, "not on the volume:", type(error).__name__)
                    continue
                into = HERE / "fixtures" / name if item == "index.scip" else Path(args.files or RESULTS) / f"fixture-{name}"
                into.mkdir(parents=True, exist_ok=True)
                (into / item).write_bytes(data)
                print(into / item, len(data))
    elif args.command == "fetch":
        for case in args.cases.split(","):
            language = CASES[case]["language"]
            names = [f"graph-{language}-{case}.json", f"graph-{language}-{case}-checks.json", "graph-error.txt"]
            folder = Path(args.files) / case if args.files else RESULTS
            folder.mkdir(parents=True, exist_ok=True)
            for name in names + (list(STORED) if args.files else []):
                try:
                    data = b"".join(volume.read_file(f"{STORE}/{case}/{name}"))
                except Exception as error:
                    print(case, name, "not on the volume:", type(error).__name__)
                    continue
                (folder / name).write_bytes(data.replace(b"\r\n", b"\n") if name.endswith(".json") else data)
                print(folder / name, len(data))
            if args.files:
                import io
                import tarfile
                for name, into in (("snapshot.tar.gz", "snapshot"), ("source.tar.gz", "source")):
                    with tarfile.open(fileobj=io.BytesIO(b"".join(volume.read_file(f"{STORE}/{case}/{name}")))) as tar:
                        tar.extractall(folder / into, filter="data")
    else:
        folder = Path(args.dir).resolve()
        folder = folder / args.case if (folder / args.case).is_dir() else folder  # as `fetch --files` fills it
        for path in write(folder, local_folder(folder), RESULTS, args.case):
            print(path, path.stat().st_size)
