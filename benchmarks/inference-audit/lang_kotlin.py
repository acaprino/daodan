"""Kotlin code graph from scip-java's whole-project index, on Modal: the wiring of adapter, reader and volume.

The plugin's `indexers/kotlin.py` runs scip-java (its two phases run by `adapters/jvm_here.py` in this
function's container, on the plugin's image) and holds what this engine's index states its own way;
`code_graph.py` reads the index and assembles the graph. The volume keeps `inference-audit/graph-kotlin/klaxon/`:
index.scip (as scip-java writes it), index-forward.scip (without the aggregator's reverse relationships),
manifest.sqlite, indexer.json, kotlin-configs/ and graph.json (nodes, edges with chain and uncertainty, holes).
`--stage graph` rebuilds the graph from them without the indexer; `graph` does the same locally.

    modal deploy benchmarks/inference-audit/lang_kotlin.py
    python benchmarks/inference-audit/lang_kotlin.py spawn [--stage index|graph]
    python benchmarks/inference-audit/lang_kotlin.py fetch [--artifacts DIR]
    python benchmarks/inference-audit/lang_kotlin.py graph --index I --manifest M --source S --configs C --out O
"""
from __future__ import annotations

import collections
import json
import re
import sys
import tempfile
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
SCRIPTS = str(PLUGIN / "scripts")
RESULTS = HERE / "results"
TAG = "inference-audit"
STORE = f"{TAG}/graph-kotlin"
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
import plugin_scripts  # noqa: E402
import code_graph as scip_graph  # noqa: E402
import indexers.kotlin  # noqa: E402
from indexers import jvm  # noqa: E402
from adapters import kotlin as adapter  # noqa: E402
from modal_audit import CASES, _run, _source  # noqa: E402

CASE = "klaxon"

# Twenty call sites read in the source before the graph was built: (file, line, token, nth occurrence of the
# token on the line, expected end, what makes the site hard). `project` names the definition line of the
# expected symbol, `external` a pattern of its symbol, `impls` definition lines the graph must also report.
HAND_CHECK = [
    ("klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt", 23, "create", 1,
     {"project": "klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt:43"},
     "companion object method through the class name"),
    ("klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt", 72, "parseJsonObject", 1,
     {"project": "klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt:79"},
     "lambda with receiver: the private KlaxonJson extension, not the same-named top-level function"),
    ("klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt", 86, "obj", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/KlaxonJson.kt:19"},
     "member of the extension receiver, Iterable overload"),
    ("klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt", 58, "codec", 1,
     {"external": r"com/fasterxml/jackson/core/JsonParser#(getCodec\(\)|codec)"},
     "Java getter read as a Kotlin property"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/JsonArray.kt", 8, "JsonArray", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/JsonArray.kt:10"},
     "primary constructor chosen over the same-named top-level function"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/JsonArray.kt", 53, "[", 1,
     {"external": r"kotlin/collections/(Mutable)?Map#get\("},
     "operator get through a delegated MutableMap"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/Klaxon.kt", 268, "canConvert", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/Converter.kt:10",
      "impls": ["klaxon/src/main/kotlin/com/beust/klaxon/DefaultConverter.kt:16",
                "klaxon/src/main/kotlin/com/beust/klaxon/EnumConverter.kt:21"]},
     "call through an interface"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/Klaxon.kt", 31, "parse", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/Parser.kt:27",
      "impls": ["klaxon/src/main/kotlin/com/beust/klaxon/KlaxonParser.kt:23",
                "klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt:38"]},
     "interface overload, implementations in two modules"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/Klaxon.kt", 308, "verbose", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/Debug.kt:5"},
     "companion property through the class name"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/Klaxon.kt", 160, "add", 1,
     {"external": r"java/util/ArrayList#add\("},
     "member of kotlin.collections.ArrayList, a typealias of java.util.ArrayList"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/KlaxonJson.kt", 27, "init", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/KlaxonJson.kt:25"},
     "invoke of a function-type parameter with receiver"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/KlaxonJson.kt", 59, "theKlaxonJson", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/KlaxonJson.kt:42"},
     "internal companion property through the class name"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/KlaxonJson.kt", 23, "obj", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/KlaxonJson.kt:19"},
     "overload chosen by the argument type"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/KlaxonJson.kt", 30, "[", 1,
     {"external": r"kotlin/collections/(MapsKt#)?set\("},
     "indexed assignment: the stdlib operator extension MutableMap.set"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/Render.kt", 28, "renderString", 2,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/Render.kt:57"},
     "private generic extension, not the same-named member it is called from"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/Render.kt", 23, "toJson", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/Converter.kt:15",
      "impls": ["klaxon/src/main/kotlin/com/beust/klaxon/DefaultConverter.kt:50",
                "klaxon/src/main/kotlin/com/beust/klaxon/EnumConverter.kt:7"]},
     "call through an interface on a returned value"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/Annotations.kt", 113, "nameInitialized", 1,
     {"project": "klaxon/src/main/java/com/beust/klaxon/Json.kt:39"},
     "extension on an annotation class, declared in a .kt under src/main/java"),
    ("klaxon/src/main/kotlin/com/beust/klaxon/KlaxonParser.kt", 84, "tokenType", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/token/Token.kt:30"},
     "property with a custom getter, read on an object"),
    ("klaxon/src/test/kotlin/com/beust/klaxon/JazzerTest.kt", 9, "default", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/Parser.kt:56"},
     "companion of an interface, from a test source"),
    ("src/test/kotlin/com/beust/klaxon/KlaxonTest.kt", 276, "lookup", 1,
     {"project": "klaxon/src/main/kotlin/com/beust/klaxon/Lookup.kt:9"},
     "extension function, from the root project's tests"),
]


def _image():
    return (
        # The plugin's image (JDK 17); scip-java and the build tool come from `jvm.tools`, as in the plugin.
        modal.Image.from_registry(jvm.IMAGE, add_python="3.13").apt_install("git")  # the checkout
        .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(HERE / "modal_audit.py" if LOCAL else Path("/audit/modal_audit.py"), "/audit/modal_audit.py")
        .add_local_file(HERE / "probe.py" if LOCAL else Path("/audit/probe.py"), "/audit/probe.py")
        .add_local_file(HERE / "plugin_scripts.py" if LOCAL else Path("/audit/plugin_scripts.py"),
                        "/audit/plugin_scripts.py")
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
    )


app = modal.App("daodan-graph-kotlin", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def hand_check(index, traversal, graph: dict) -> dict:
    """The ends the graph gives at each hand-read site, against the target written before it was built."""
    uncertain = collections.defaultdict(set)
    for edge in graph["edges"]:
        if edge.get("uncertain"):
            uncertain[(edge["site"], edge["to"])].add(edge["uncertain"]["reason"])
    sites = []
    for rel, line, token, nth, expected, why in HAND_CHECK:
        text = index.line(rel, line) or ""
        pattern = rf"\b{re.escape(token)}\b" if token.isidentifier() else re.escape(token)
        columns = [match.start() for match in re.finditer(pattern, text)]
        native = (index.from_bytes(rel, line, len(text[:columns[nth - 1]].encode("utf-8")))
                  if len(columns) >= nth else None)
        keys = [item.key for item in index.at.get((rel, line, native), ()) if not item.definition]
        ends = list(dict.fromkeys(end for key in dict.fromkeys(keys) for end in traversal.ends(key)))

        def where(key):
            return [f"{place}:{occurrence.line}" for place, occurrence in index.defs.get(key, ())]

        direct = [end for end in ends if "implementation" not in end.chain]
        if "project" in expected:
            right = any(expected["project"] in where(end.key) for end in direct)
        else:
            right = any(end.cls == "external" and re.search(expected["external"], end.key) for end in direct)
        implementations = all(any(want in where(end.key) for end in ends if "implementation" in end.chain)
                              for want in expected.get("impls", ()))
        sites.append({"site": f"{rel}:{line} {token}", "hard": why, "expected": expected,
                      "occurrence_found": bool(keys), "right": right and implementations,
                      "target_right": right, "implementations_right": implementations,
                      "graph": [{"to": end.key[-140:], "end": end.cls, "defined_at": where(end.key),
                                 "chain": list(end.chain),
                                 "uncertain": sorted(uncertain.get((f"{rel}:{line}", end.key), ()))}
                                for end in ends]})
    return {"right": sum(1 for site in sites if site["right"]), "of": len(sites), "sites": sites}


def graph(index_path: Path, manifest: Path, source: Path, configs: Path | None, indexer: dict) -> tuple[dict, dict]:
    """The graph, and what the result file reports of it."""
    index = scip_graph.Index(source)
    index.load(index_path, "")
    compiled = indexers.kotlin.tasks(configs)
    hops = indexers.kotlin.hops(index)
    with scip_graph.Snapshot(manifest) as snapshot:
        traversal = scip_graph.Traversal(index, snapshot, hops, classify=indexers.kotlin.classify(index))
        absent = [snapshot.checkout[rel] for rel in snapshot.inventory if snapshot.languages.get(rel) == "kotlin"
                  and rel in snapshot.checkout and snapshot.checkout[rel] not in index.documents]
        built, _references = scip_graph.build(index, snapshot, "kotlin", hops, indexer,
                                              indexers.kotlin.missing(index, absent, compiled), traversal,
                                              refine=lambda read, graph: indexers.kotlin.refine(read, graph, compiled))
        checks = hand_check(index, traversal, built)
    edges = built["edges"]
    uncertain = [edge for edge in edges if edge.get("uncertain")]
    summary = {
        "report": scip_graph.report(built),
        "edges_certain": len(edges) - len(uncertain),
        "uncertain_examples": [{key: edge[key] for key in ("site", "symbol", "to", "uncertain")}
                               for edge in uncertain[:: max(1, len(uncertain) // 6)]][:6],
        "holes": dict(collections.Counter(hole["class"] for hole in built["holes"])),
        "hand_check": checks,
    }
    return built, summary


def _indexer(record: dict) -> dict:
    """The graph's indexer entry, also from the record of the first run (summed RSS of all processes)."""
    if "name" in record:
        return {key: record[key] for key in ("name", "version", "seconds", "peak_mb")}
    return {"name": "scip-java", "version": record["scip_java"], "seconds": record["seconds"],
            "peak_mb": record["peak_rss_mb_all_processes"]}


@app.function(cpu=4, memory=8192, timeout=3600, volumes={"/results": volume})
def kotlin_case(stage: str = "graph") -> dict:
    import shutil
    import time
    started = time.time()
    print("code", plugin_scripts.code_sha256(), flush=True)  # compared with the checkout before trusting the run
    case = CASES[CASE]
    work = Path("/work") / CASE
    engine = work / "engine"
    engine.mkdir(parents=True, exist_ok=True)
    store = Path("/results") / STORE / CASE
    store.mkdir(parents=True, exist_ok=True)
    target = _source(work / "src", case, None)
    manifest = work / "snapshot/manifest.sqlite"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    if stage == "index":
        _run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out", str(manifest),
              "--no-engine", "--no-index"])
        shutil.copyfile(manifest, store / "manifest.sqlite")
        ran = adapter.index(target, engine)
        if not ran["indexes"]:  # never the graph of an index an earlier run left on the volume
            volume.commit()
            return {"code": plugin_scripts.code_sha256(),
                    **{key: ran.get(key) for key in ("state", "reason", "refused", "runs")}}
        shutil.copyfile(engine / "scip-java-0.scip", store / "index.scip")
        shutil.rmtree(store / "kotlin-configs", ignore_errors=True)
        if (engine / "kotlin-configs").is_dir():
            shutil.copytree(engine / "kotlin-configs", store / "kotlin-configs")
        (store / "indexer.json").write_text(json.dumps({**ran["indexer"], "runs": ran["runs"],
                                                        "refused": ran.get("refused"), "state": ran.get("state"),
                                                        "reason": ran.get("reason")}, indent=1),
                                            encoding="utf-8")
    else:
        shutil.copyfile(store / "manifest.sqlite", manifest)
    indexer = _indexer(json.loads((store / "indexer.json").read_text(encoding="utf-8")))
    result = {"case": CASE, "commit": case["commit"], "stage": stage, "indexer": indexer,
              "code": plugin_scripts.code_sha256()}
    begun = time.time()
    forward = engine / "index-forward.scip"
    result["reverse_relationships_dropped"] = indexers.kotlin.forward_only(store / "index.scip", forward)
    shutil.copyfile(forward, store / "index-forward.scip")
    built, summary = graph(forward, manifest, target, store / "kotlin-configs", indexer)
    (store / "graph.json").write_text(json.dumps(built, ensure_ascii=False), encoding="utf-8")
    result.update(summary, graph_seconds=round(time.time() - begun, 1), seconds=round(time.time() - started, 1))
    (Path("/results") / TAG / f"graph-kotlin-{CASE}.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    return {"seconds": result["seconds"], "edges_certain": result["edges_certain"]}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "graph"))
    parser.add_argument("--stage", choices=("index", "graph"), default="graph")
    parser.add_argument("--artifacts")
    parser.add_argument("--index", help="the index as scip-java writes it")
    parser.add_argument("--manifest")
    parser.add_argument("--source")
    parser.add_argument("--configs")
    parser.add_argument("--indexer", help="indexer.json from the volume")
    parser.add_argument("--out")
    args = parser.parse_args()
    if args.command == "spawn":
        function = modal.Function.from_name("daodan-graph-kotlin", "kotlin_case")
        print(CASE, function.spawn(args.stage).object_id)
    elif args.command == "fetch":
        RESULTS.mkdir(parents=True, exist_ok=True)
        data = b"".join(volume.read_file(f"{TAG}/graph-kotlin-{CASE}.json"))
        (RESULTS / f"graph-kotlin-{CASE}.json").write_bytes(data.replace(b"\r\n", b"\n"))
        print("result", len(data))
        if args.artifacts:
            out = Path(args.artifacts)
            for entry in volume.listdir(f"{STORE}/{CASE}", recursive=True):
                if entry.type == modal.volume.FileEntryType.FILE:
                    path = out / Path(entry.path).relative_to(f"{STORE}/{CASE}")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b"".join(volume.read_file(entry.path)))
                    print(path, path.stat().st_size)
    else:
        record = json.loads(Path(args.indexer).read_text(encoding="utf-8")) if args.indexer else None
        indexer = _indexer(record) if record else {"name": "scip-java", "version": jvm.VERSION}
        with tempfile.TemporaryDirectory() as folder:
            forward = Path(folder) / "index-forward.scip"
            indexers.kotlin.forward_only(Path(args.index), forward)
            built, summary = graph(forward, Path(args.manifest), Path(args.source),
                                   Path(args.configs) if args.configs else None, indexer)
        out = Path(args.out)
        out.write_text(json.dumps({"indexer": indexer, **summary}, indent=1, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        out.with_suffix(".graph.json").write_text(json.dumps(built, ensure_ascii=False), encoding="utf-8")
        print(out, summary["edges_certain"], summary["report"]["edges_uncertain"], summary["holes"],
              summary["hand_check"]["right"])
