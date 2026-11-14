"""Second sources for the JVM graph: targeted Analysis API questions (Kotlin) and the bytecode call graph.

One container on Modal rebuilds both cases as the graph benchmarks do (`adapters/java.py` on javapoet,
`adapters/kotlin.py` on klaxon) and then:
- asks the Kotlin Analysis API (`adapters/kotlin_analysis.py`) only where klaxon's index graph is uncertain or
  silent: the arcs marked uncertain, the implicit-operator holes, the references without a package;
- builds WALA's CHA and RTA over the compiled classes of both (`adapters/jvm_callgraph.py`);
- compares both with the index graphs and scores the twenty hand-read sites of `HAND_CHECK`.
The index graphs and klaxon's index come from the volume (`inference-audit/graph-java/javapoet/`,
`inference-audit/graph-kotlin/klaxon/`); the raw answers of both engines stay in `inference-audit/strong-jvm/`,
so `compare` recomputes the comparison here without running anything again.

    modal deploy benchmarks/inference-audit/strong_jvm.py
    python benchmarks/inference-audit/strong_jvm.py spawn
    python benchmarks/inference-audit/strong_jvm.py fetch [--raw DIR]
    python benchmarks/inference-audit/strong_jvm.py compare --raw DIR --javapoet SRC --klaxon SRC
"""
from __future__ import annotations

import collections
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
STORE = f"{TAG}/strong-jvm"
RESULT = "strong-jvm.json"
RAW = ("jvm-javapoet.json", "jvm-klaxon.json", "kotlin-answers.json", "builds.json")
GRAPHS = {"javapoet": f"{TAG}/graph-java/javapoet/graph-java-javapoet.json",
          "klaxon": f"{TAG}/graph-kotlin/klaxon/graph.json"}
KOTLIN_INDEX = f"{TAG}/graph-kotlin/klaxon/index-forward.scip"
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
import resolve_edges  # noqa: E402
import scip_graph  # noqa: E402
from adapters import java, jvm_callgraph, kotlin, kotlin_analysis  # noqa: E402
from modal_audit import CASES, _source  # noqa: E402

# ---------------------------------------------------------------------------------------------------------
# The hand check, written from the source before any answer of the two new sources was read.
#
# kind `overload`: `def` is the declaration the call reaches, `jvm` the method the bytecode should call.
# kind `dispatch`: `impls` the declarations of the implementations that can run (`all-index`: every
#   implementation the index lists can run), `def` and `jvm` the declared target when it is also scored.
# kind `implicit`: `callable` the symbol the operator call reaches (a regex on the Analysis API's callable id,
#   `artifact` its jar), `jvm` the method the bytecode should call.
# kind `lambda`: `caller` and `impl` the method holding the lambda or method reference and its implementation
#   method (a prefix), `index` the name the index should link at that line.
KX = "klaxon/src/main/kotlin/com/beust/klaxon/"
KT = "klaxon/src/test/kotlin/com/beust/klaxon/"
RT = "src/test/kotlin/com/beust/klaxon/"
JP = "src/main/java/com/squareup/javapoet/"
HAND_CHECK = [
    {"case": "klaxon", "site": "klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt:86",
     "token": "obj", "kind": "overload", "def": KX + "KlaxonJson.kt:19",
     "jvm": "com/beust/klaxon/KlaxonJson.obj(Ljava/lang/Iterable;)",
     "why": "index miss: overload across tasks, `obj(pairs)` with a List of pairs takes obj(Iterable)"},
    {"case": "klaxon", "site": KX + "Klaxon.kt:31", "token": "parse", "kind": "dispatch", "def": KX + "Parser.kt:27",
     "jvm": "com/beust/klaxon/Parser.parse(Ljava/io/Reader;)",
     "impls": [KX + "KlaxonParser.kt:23", "klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt:38"],
     "why": "index miss: Parser.parse(Reader); the JacksonParser override is parse(Reader) at :38, not :29"},
    {"case": "klaxon", "site": KX + "JsonArray.kt:53", "token": "[", "kind": "implicit", "role": "get",
     "callable": r"^(com/beust/klaxon/JsonObject\.get|kotlin/collections/(Mutable)?Map\.get)$",
     "jvm": "com/beust/klaxon/JsonObject.get(",
     "why": "index miss: `it[key]` on a JsonObject, the get JsonObject delegates to its map"},
    {"case": "klaxon", "site": KX + "KlaxonJson.kt:30", "token": "[", "kind": "implicit", "role": "set",
     "callable": r"^kotlin/collections/set$", "artifact": "kotlin-stdlib",
     "jvm": "kotlin/collections/MapsKt",
     "why": "index miss: `newMap[key] = ...`, the stdlib inline operator MutableMap.set"},
    {"case": "klaxon", "site": KT + "JazzerTest.kt:9", "token": "parse", "kind": "overload", "def": KX + "Parser.kt:14",
     "jvm": "com/beust/klaxon/Parser.parse(Ljava/lang/StringBuilder;)",
     "why": "uncertain: `parse(StringBuilder(json))` from the test task"},
    {"case": "klaxon", "site": KT + "Issue167Test.kt:19", "token": "array", "kind": "overload",
     "def": KX + "KlaxonJson.kt:12", "jvm": "com/beust/klaxon/KlaxonJson.array([Ljava/lang/Object;)",
     "why": "uncertain: `array(\"a\", 1, false)` takes the vararg overload"},
    {"case": "klaxon", "site": KT + "Issue237Test.kt:28", "token": "array", "kind": "overload",
     "def": KX + "KlaxonJson.kt:14", "jvm": "com/beust/klaxon/KlaxonJson.array(Ljava/util/List;)",
     "why": "uncertain: `array(listOf(...))` takes array(List)"},
    {"case": "klaxon", "site": RT + "KlaxonTest.kt:103", "token": "JsonArray", "kind": "overload",
     "def": KX + "JsonArray.kt:11", "jvm": "com/beust/klaxon/JsonArray.<init>([Ljava/lang/Object;)",
     "why": "uncertain: `JsonArray(1, 2, 3)` from the root tests, the vararg secondary constructor"},
    {"case": "klaxon", "site": RT + "KlaxonTest.kt:118", "token": "obj", "kind": "overload",
     "def": KX + "KlaxonJson.kt:22", "jvm": "com/beust/klaxon/KlaxonJson.obj([Lkotlin/Pair;)",
     "why": "uncertain: `obj(\"b\" to 2)` from the root tests, the vararg Pair overload"},
    {"case": "klaxon", "site": KT + "BindingTest.kt:28", "token": "toJsonString", "kind": "overload",
     "def": KX + "Klaxon.kt:271", "jvm": "com/beust/klaxon/Klaxon.toJsonString(Ljava/lang/Object;Lkotlin/reflect/KProperty;)",
     "why": "uncertain: the public toJsonString(Any?, KProperty? = null), called with its default"},
    {"case": "klaxon", "site": RT + "TestTypes.kt:31", "token": "parse", "kind": "overload", "def": KX + "Parser.kt:25",
     "jvm": "com/beust/klaxon/Parser.parse(Ljava/io/InputStream;Ljava/nio/charset/Charset;)",
     "why": "uncertain: `parse(getResourceAsStream(name)!!)` takes parse(InputStream, Charset = UTF_8)"},
    {"case": "klaxon", "site": KX + "Klaxon.kt:24", "token": "parse", "kind": "dispatch", "def": KX + "Parser.kt:27",
     "jvm": "com/beust/klaxon/Parser.parse(Ljava/io/Reader;)",
     "impls": [KX + "KlaxonParser.kt:23", "klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt:38"],
     "why": "override across tasks: a JsonReader is a Reader, so JacksonParser.parse(Reader) at :38"},
    {"case": "klaxon", "site": KX + "Klaxon.kt:268", "token": "canConvert", "kind": "dispatch", "impls": "all-index",
     "why": "interface call: DefaultConverter and EnumConverter are created by Klaxon, every test Converter by an "
            "object expression or a constructor call"},
    {"case": "klaxon", "site": "klaxon/src/main/java/com/beust/klaxon/TypeFor.kt:8", "token": "classFor",
     "kind": "dispatch", "impls": "all-index",
     "why": "interface call: the eight test TypeAdapters run, created only by `createInstance()` "
            "(JsonObjectConverter.kt:237), never by a constructor call"},
    {"case": "javapoet", "site": JP + "TypeName.java:221", "token": "emit", "kind": "dispatch", "impls": "all-index",
     "why": "virtual call: the five subclasses are all created in the main code"},
    {"case": "javapoet", "site": "src/test/java/com/squareup/javapoet/AbstractTypesTest.java:75", "token": "getTypes",
     "kind": "dispatch", "impls": "all-index",
     "why": "abstract method: TypesTest and TypesEclipseTest run, created by JUnit through reflection"},
    {"case": "javapoet", "site": JP + "JavaFile.java:169", "token": "createSourceFile", "kind": "dispatch",
     "impls": "all-index", "why": "JDK interface: TestFiler, created in FileWritingTest"},
    {"case": "javapoet", "site": JP + "LineWrapper.java:158", "token": "append", "kind": "dispatch", "impls": "all-index",
     "why": "JDK interface: RecordingAppendable (LineWrapper.java:50) and the anonymous NULL_APPENDABLE (JavaFile.java:48)"},
    {"case": "javapoet", "site": JP + "CodeBlock.java:125", "token": "add", "kind": "lambda",
     "caller": "com/squareup/javapoet/CodeBlock.joining(",
     "impl": "com/squareup/javapoet/CodeBlock$CodeBlockJoiner.add(Lcom/squareup/javapoet/CodeBlock;)", "index": "add",
     "why": "method reference `CodeBlockJoiner::add` passed to Collector.of"},
    {"case": "javapoet", "site": JP + "CodeWriter.java:198", "token": "add", "kind": "lambda",
     "caller": "com/squareup/javapoet/CodeWriter.emitTypeVariables(",
     "impl": "com/squareup/javapoet/CodeWriter.lambda$emitTypeVariables$", "index": "add",
     "why": "lambda passed to List.forEach; its body calls Multiset.add"},
]
PRIMITIVE = {"plus", "minus", "times", "div", "rem", "inc", "dec", "unaryMinus", "unaryPlus", "not", "compareTo",
             "rangeTo", "and", "or", "xor", "shl", "shr", "ushr", "inv", "toInt", "toLong", "toFloat", "toDouble",
             "toShort", "toByte", "toChar"}
ALGORITHMS = ("cha", "rta", "rtat")  # rtat: RTA where the test runner also creates each @Test class
ROLES = {"indexed read": "get", "indexed assignment": "set", "for loop": "iterator", "property delegate": "getValue",
         "destructuring entry": "componentN"}

# ---------------------------------------------------------------------------------------------------------
# Modal wiring


def _image():
    edges = resolve_edges
    kaa = " ".join(f"--intransitive {item}" for item in dict.fromkeys(
        [edges.KOTLIN_ANALYSIS, *edges.KOTLIN_RUNTIME, *edges.KOTLIN_COMPILER]))
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "curl", "ca-certificates", "unzip", *java.APT)
        .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .run_commands(*java.install_commands())
        .run_commands(*kotlin.install_commands())
        .run_commands(*jvm_callgraph.install_commands(),
                      # The Analysis API and the compiler, where resolve_edges.maven_artifact looks for them.
                      f"/opt/jdk/bin/java -jar /opt/coursier.jar fetch --cache /root/.cache/daodan/coursier {kaa}")
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(HERE / "modal_audit.py" if LOCAL else Path("/audit/modal_audit.py"), "/audit/modal_audit.py")
        .add_local_file(HERE / "probe.py" if LOCAL else Path("/audit/probe.py"), "/audit/probe.py")
        .add_local_file(HERE / "scip_graph.py" if LOCAL else Path("/audit/scip_graph.py"), "/audit/scip_graph.py")
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
    )


app = modal.App("daodan-strong-jvm", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


class _Peak:
    """The resident memory of every process of the container, summed, sampled twice a second."""

    def __init__(self):
        import threading
        self.peak, self.stop = 0, threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

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


def _code() -> dict:
    """Digests of what the container runs, compared with the checkout before trusting a run."""
    import hashlib
    files = [HERE / "strong_jvm.py" if LOCAL else Path(__file__), *sorted((HERE / "adapters" if LOCAL else
                                                                           Path("/audit/adapters")).glob("*.*"))]
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()[:12] for path in files if path.is_file()}


def _javapoet(work: Path, builds: dict) -> tuple[Path, list, list, dict]:
    """The javapoet build of adapters/java.py, its class directories and its test classpath from Maven."""
    import subprocess
    target = _source(work / "src", CASES["javapoet"], None)
    engine = java.index(target, work, None, {})
    builds["javapoet"] = {"runs": [{key: run.get(key) for key in ("step", "returncode", "seconds", "peak_mb")}
                                   for run in engine["runs"]]}
    mirror = work / "mirror"
    out = work / "classpath.txt"
    done = subprocess.run(["mvn", "-q", "dependency:build-classpath", f"-Dmdep.outputFile={out}"], cwd=mirror,
                          capture_output=True, text=True, timeout=900)
    builds["javapoet"]["classpath_returncode"] = done.returncode
    jars = [item for item in out.read_text().strip().split(":") if item] if out.is_file() else []
    dirs = [mirror / "target/classes", mirror / "target/test-classes"]
    roots = {str(mirror / "target/classes"): ["src/main/java"], str(mirror / "target/test-classes"): ["src/test/java"]}
    return target, [str(path) for path in dirs if path.is_dir()], jars, roots


def _klaxon(work: Path, builds: dict) -> tuple[Path, Path, list, list, dict]:
    """The klaxon build of adapters/kotlin.py, its class directories and the jars its compile tasks list."""
    target = _source(work / "src", CASES["klaxon"], None)
    engine_dir = work / "engine"
    ran = kotlin.index(target, engine_dir)
    builds["klaxon"] = {"runs": [{key: run.get(key) for key in ("returncode", "seconds", "peak_mb")}
                                 for run in ran["runs"]]}
    mirror = engine_dir / "mirror-scip-java"
    dirs, roots = [], {}
    for path in sorted(mirror.glob("**/build/classes/*/*")):
        relative = path.relative_to(mirror).as_posix()
        if path.is_dir() and not relative.startswith("buildSrc/") and "/build/classes/" in f"/{relative}":
            project, _, rest = relative.partition("build/classes/")
            source_set = rest.split("/")[1]
            dirs.append(str(path))
            roots[str(path)] = [f"{project}src/{source_set}/kotlin", f"{project}src/{source_set}/java"]
    jars = set()
    for config in (engine_dir / "kotlin-configs").glob("*.txt"):
        for row in config.read_text(encoding="utf-8").splitlines():
            if row.startswith("classpath "):
                entry = row.split(" ", 1)[1]
                if entry.endswith(".jar") and not entry.startswith(str(mirror)) and "scip-plugin" not in entry \
                        and Path(entry).is_file():
                    jars.add(entry)
    return target, engine_dir, dirs, sorted(jars), roots


@app.function(cpu=4, memory=12288, timeout=3600, volumes={"/results": volume})
def strong_case() -> dict:
    import shutil
    import time
    import traceback
    started = time.time()
    code = _code()
    print("code", code, flush=True)
    shutil.rmtree("/work", ignore_errors=True)  # a warm container keeps the previous input's files
    peak = _Peak()
    store = Path("/results") / STORE
    store.mkdir(parents=True, exist_ok=True)
    builds, errors = {"code": code}, {}
    raw, targets = {}, {}
    engine_dir = Path("/work/klaxon/engine")
    for case in ("javapoet", "klaxon"):
        try:
            begun = time.time()
            if case == "javapoet":
                targets[case], dirs, jars, roots = _javapoet(Path("/work/javapoet"), builds)
            else:
                targets[case], engine_dir, dirs, jars, roots = _klaxon(Path("/work/klaxon"), builds)
            builds[case].update(seconds=round(time.time() - begun, 1), class_dirs=dirs, jars=len(jars))
            begun = time.time()
            raw[f"jvm-{case}"] = jvm_callgraph.analyze(dirs, jars, Path(f"/work/{case}/wala"), targets[case], roots)
            builds[case]["wala_seconds"] = round(time.time() - begun, 1)
            (store / f"jvm-{case}.json").write_text(json.dumps(raw[f"jvm-{case}"]), encoding="utf-8")
        except Exception:
            errors[f"jvm-{case}"] = traceback.format_exc()[-3000:]
            print(errors[f"jvm-{case}"], flush=True)
    try:
        index = scip_graph.Index(targets["klaxon"])
        index.load(Path("/results") / KOTLIN_INDEX)
        graph = json.loads((Path("/results") / GRAPHS["klaxon"]).read_text(encoding="utf-8"))
        sites = kotlin_sites(index, graph)
        answers = kotlin_analysis.ask(targets["klaxon"], engine_dir, sites, engine_dir / "kotlin-configs")
        engine = json.loads((engine_dir / "kotlin-analysis.json").read_text(encoding="utf-8"))
        raw["kotlin-answers"] = {"sites": sites, "answers": answers, "engine": engine}
        (store / "kotlin-answers.json").write_text(json.dumps(raw["kotlin-answers"]), encoding="utf-8")
    except Exception:
        errors["kotlin-answers"] = traceback.format_exc()[-3000:]
        print(errors["kotlin-answers"], flush=True)
    peak.stop.set()
    builds.update(errors=errors, container_peak_mb=round(peak.peak / 2 ** 20), seconds=round(time.time() - started, 1))
    (store / "builds.json").write_text(json.dumps(builds, indent=1), encoding="utf-8")
    try:
        sources = {"javapoet": Path("/work/javapoet/src"), "klaxon": Path("/work/klaxon/src")}
        graphs = {case: json.loads((Path("/results") / path).read_text(encoding="utf-8")) for case, path in GRAPHS.items()}
        result = compare(raw, graphs, sources, builds)
    except Exception:
        result = {"builds": builds, "compare_error": traceback.format_exc()[-3000:]}
    (Path("/results") / TAG / RESULT).write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    return {"seconds": builds["seconds"], "errors": sorted(errors), "compare_error": "compare_error" in result}


# ---------------------------------------------------------------------------------------------------------
# The questions to the Analysis API


def _occurrences(index, rel: str, line: int, key: str) -> list:
    return sorted((item for item in index.documents.get(rel, ()) if item.line == line and not item.definition
                   and item.key == key), key=lambda item: item.start)


def kotlin_sites(index, graph: dict) -> list[dict]:
    """The sites to ask: uncertain arcs, implicit-operator holes, packageless references, the hand check."""
    nodes = {node["id"]: node for node in graph["nodes"]}
    sites = {}

    def add(mode: str, rel: str, line: int, column: int, why: str, symbol: str | None = None) -> None:
        key = f"{mode}|{rel}|{line}|{column}"
        site = sites.setdefault(key, {"site": key, "mode": mode, "file": rel, "line": line, "column": column,
                                      "why": [], "symbols": []})
        if why not in site["why"]:
            site["why"].append(why)
        if symbol and symbol not in site["symbols"]:
            site["symbols"].append(symbol)

    for edge in graph["edges"]:
        rel, line = edge["site"].rsplit(":", 1)
        if edge.get("uncertain"):
            for item in _occurrences(index, rel, int(line), edge["symbol"]):
                add("ref", rel, int(line), item.start, "uncertain", edge["symbol"])
            if edge["uncertain"]["reason"] == "override-across-tasks" or "implementation" in edge["chain"]:
                for candidate in edge["uncertain"]["candidates"]:
                    for place, item in index.defs.get(candidate, ()):
                        add("overridden", place, item.line, item.start, "override candidate", candidate)
        elif edge["end"] == "external" and (nodes.get(edge["to"], {}).get("external") or {}).get("manager") == "unknown":
            for item in _occurrences(index, rel, int(line), edge["symbol"]):
                add("ref", rel, int(line), item.start, "packageless", edge["symbol"])
    for hole in graph["holes"]:
        if hole["class"] == "implicit-operator":
            rel, line = hole["site"].rsplit(":", 1)
            add("implicit", rel, int(line), 0, "implicit")
    for check in HAND_CHECK:
        if check["case"] != "klaxon":
            continue
        rel, line = check["site"].rsplit(":", 1)
        if check["token"] == "[":
            add("implicit", rel, int(line), 0, "hand check")
        else:
            text = index.line(rel, int(line)) or ""
            match = re.search(rf"\b{re.escape(check['token'])}\b", text)
            if match:
                add("ref", rel, int(line), len(text[:match.start()].encode("utf-16-le")) // 2, "hand check")
    return list(sites.values())


# ---------------------------------------------------------------------------------------------------------
# The comparison


def _jvm_name(name: str) -> str:
    """A JVM method name as the source writes it: Kotlin's `internal` mangling dropped."""
    return name if name.startswith(("lambda$", "access$", "<")) else name.split("$", 1)[0]


def _method(signature: str) -> str:
    return signature.split("(", 1)[0].rsplit(".", 1)[-1]


def _owner(signature: str) -> str:
    return signature.split("(", 1)[0].rsplit(".", 1)[0]


def _symbol_name(key: str) -> str | None:
    """The last descriptor's name of a global symbol: a method, a field or a type."""
    if "local " in key:
        return None
    parts = scip_graph.split_symbol(key)
    if not parts:
        return None
    found = scip_graph.descriptors(parts[4])
    return found[-1][0].strip("`") if found else None


class Bytecode:
    """The WALA records of one case, by call site and by class."""

    def __init__(self, raw: dict, source: Path):
        self.raw, self.source = raw, Path(source)
        self.files = raw["files"]
        self.classes = raw["classes"]
        self.methods = raw["methods"]
        self.instantiated = set(raw["instantiated"])
        self.at = collections.defaultdict(list)
        for call in raw["calls"]:
            self.at[(self.files.get(_owner(call["caller"])), call["line"])].append(call)
        self.lambdas = [edge for edge in raw["edges"] if edge["kind"] in ("lambda", "method-reference")]
        self.by_caller = collections.defaultdict(list)
        for call in raw["calls"]:
            self.by_caller[(call["alg"], call["caller"])].append(call)
        self.by_file_name = collections.defaultdict(list)
        for signature, method in self.methods.items():
            self.by_file_name[(self.files.get(_owner(signature)), _jvm_name(_method(signature)))].append((signature, method))
        self._lines = {}

    def lines(self, rel: str) -> int:
        if rel not in self._lines:
            try:
                self._lines[rel] = len((self.source / rel).read_text(encoding="utf-8").split("\n"))
            except (OSError, UnicodeError, TypeError):
                self._lines[rel] = 0
        return self._lines[rel]

    def class_at(self, rel: str, line: int, name: str) -> str | None:
        """The class whose method `name` begins nearest after a declaration at `rel:line`; for a method without
        lines (generated, abstract), the class declaring `name` whose constructor begins there."""
        best = None
        for signature, method in self.by_file_name.get((rel, name), ()):
            if method.get("bridge") or method["first"] < 0:
                continue
            distance = method["first"] - line
            if -1 <= distance <= 6 and (best is None or abs(distance) < best[0]):
                best = (abs(distance), _owner(signature))
        if best:
            return best[1]
        owners = {_owner(signature) for signature, _ in self.by_file_name.get((rel, name), ())}
        for signature, method in self.by_file_name.get((rel, "<init>"), ()):
            if _owner(signature) in owners and 0 <= method["first"] - line <= 2:
                return _owner(signature)
        return None

    def jvm_class(self, key: str, place: str | None, name: str) -> str | None:
        """The class of a SCIP symbol: from its descriptors for a global one, by position for a local one."""
        parts = scip_graph.split_symbol(key) if "local " not in key else None
        if parts:
            found = scip_graph.descriptors(parts[4])
            packages = "".join(item + "/" for item, kind in found if kind == "namespace")
            types = "$".join(item.strip("`") for item, kind in found if kind == "type")
            if types and packages + types in self.classes:
                return packages + types
        if place:
            file, at = place.rsplit(":", 1)
            return self.class_at(file, int(at), name)
        return None

    def subtype(self, child: str, parent: str) -> bool:
        """Whether a project class is a subtype of `parent`; a parent outside the project counts as a supertype."""
        if child == parent or parent in (self.classes.get(child, {}).get("ancestors") or ()):
            return True
        if parent not in self.classes:
            return "ancestors" not in self.classes.get(child, {})  # without ancestors, assume a supertype
        seen, stack = set(), [child]
        while stack:
            name = stack.pop()
            if name == parent:
                return True
            if name in seen or name not in self.classes:
                continue
            seen.add(name)
            item = self.classes[name]
            stack.extend([item.get("super")] if item.get("super") else [])
            stack.extend(item.get("interfaces") or ())
        return False

    def calls(self, rel: str, line: int, name: str, algorithm: str | None = None) -> list:
        return [call for call in self.at.get((rel, line), ()) if (algorithm is None or call["alg"] == algorithm)
                and _jvm_name(_method(call["declared"])) in (name, f"{name}$default")]

    def targets(self, calls: list, algorithm: str, name: str) -> set[str]:
        """Project classes whose method `name` the calls of one algorithm reach, one hop into a `$default`."""
        out = set()
        for call in calls:
            if call["alg"] != algorithm:
                continue
            for target in call["targets"]:
                if _method(target).endswith("$default"):
                    inner = [item for item in self.by_caller.get((algorithm, target), ())
                             if _jvm_name(_method(item["declared"])) == name]
                    out |= self.targets(inner, algorithm, name)
                elif _owner(target) in self.classes and _jvm_name(_method(target)) == name:
                    out.add(_owner(target))
        return out


def _project_place(target: dict) -> str | None:
    """`rel:line` of an answer with a source file, the file taken relative to the build's copy of the checkout."""
    file = target.get("file")
    return f"{file.split('/mirror-scip-java/', 1)[-1]}:{target.get('line')}" if file else None


def _place(nodes: dict, key: str) -> str | None:
    node = nodes.get(key)
    return f"{node['file']}:{node['line']}" if node and node.get("file") and node.get("line") else None


def dispatch(graph: dict, code: Bytecode) -> dict:
    """Index call sites with implementations against RTA and CHA at the same line and method name."""
    nodes = {node["id"]: node for node in graph["nodes"]}
    sites = collections.defaultdict(set)
    for edge in graph["edges"]:
        if "implementation" in edge["chain"]:
            sites[(edge["site"], edge["symbol"])].add(edge["to"])
    counts = collections.Counter()
    rows = []
    missing = collections.defaultdict(list)
    for (site, symbol), impls in sorted(sites.items()):
        name = _symbol_name(symbol)
        rel, line = site.rsplit(":", 1)
        calls = code.calls(rel, int(line), name) if name else []
        if not calls:
            here = {_method(call["declared"]) for call in code.at.get((rel, int(line)), ())}
            reason = ("`==` compiled to Intrinsics.areEqual" if name == "equals" and "areEqual" in here else
                      "`==` compiled to a comparison instruction, no call" if name == "equals" else
                      "no call of that name at that line")
            counts[f"sites without the call in the bytecode: {reason}"] += 1
            counts[f"implementations at those sites: {reason}"] += len(impls)
            if len(missing[reason]) < 3:
                missing[reason].append({"site": site, "symbol": symbol.split(" ")[-1], "bytecode": sorted(here)[:6]})
            continue
        expected = {impl: code.jvm_class(impl, _place(nodes, impl), name) for impl in impls}
        mapped = {cls for cls in expected.values() if cls}
        declared = {_owner(call["declared"]) for call in calls}
        counts["sites compared"] += 1
        counts["index implementations"] += len(impls)
        counts["index implementations without a class"] += sum(1 for cls in expected.values() if not cls)
        if all(call["invoke"] == "SPECIAL" for call in calls):
            counts["super calls (invokespecial): sites"] += 1
            counts["super calls (invokespecial): index implementations that cannot run"] += len(mapped)
            if len(missing["super call"]) < 3:
                missing["super call"].append({"site": site, "symbol": symbol.split(" ")[-1], "index": len(mapped)})
            continue
        row = {"site": site, "symbol": symbol.split(" ")[-1], "index": sorted(mapped),
               "unmapped": sorted(key.split(" ")[-1] for key, cls in expected.items() if not cls)}
        for algorithm in ALGORITHMS:
            mine = [call for call in calls if call["alg"] == algorithm]
            if not mine:
                counts[f"{algorithm}: caller not reached"] += 1
                counts[f"{algorithm}: implementations at unreached callers"] += len(mapped)
                row[f"{algorithm}_dropped"] = None
                continue
            got = code.targets(mine, algorithm, name)
            counts[f"{algorithm}: sites"] += 1
            counts[f"{algorithm}: kept"] += len(mapped & got)
            counts[f"{algorithm}: dropped"] += len(mapped - got)
            for cls in mapped - got:
                method = next((item for signature, item in code.methods.items() if _owner(signature) == cls
                               and _jvm_name(_method(signature)) == name), None)
                if method and method.get("abstract"):
                    why = "abstract in that class"
                elif not any(code.subtype(cls, owner) for owner in declared):
                    why = "not a subtype of the receiver's static type"
                elif algorithm != "cha" and cls not in code.instantiated and algorithm == "rta":
                    why = "never created by a reachable `new`"
                elif algorithm == "rtat":
                    why = "not created by a reachable `new` nor by the test runner"
                else:
                    why = "other"
                counts[f"{algorithm}: dropped because {why}"] += 1
            counts[f"{algorithm}: added (project)"] += len(got - mapped - declared)
            counts[f"{algorithm}: external targets"] += len({target for call in mine for target in call["targets"]
                                                            if _owner(target) not in code.classes})
            if mapped - got:
                counts[f"{algorithm}: sites with a drop"] += 1
            row[f"{algorithm}_dropped"] = sorted(mapped - got)
            row[f"{algorithm}_added"] = sorted(got - mapped - declared)
        row["dropped_never_instantiated"] = sorted(cls for cls in (row.get("rta_dropped") or ())
                                                   if cls not in code.instantiated)
        rows.append(row)
    dropped = {algorithm: dict(collections.Counter(cls for row in rows for cls in (row.get(f"{algorithm}_dropped") or ()))
                               .most_common(15)) for algorithm in ALGORITHMS}
    return {"counts": dict(counts), "dropped_classes": dropped,
            "examples_dropped": {algorithm: [row for row in rows if row.get(f"{algorithm}_dropped")][:6]
                                 for algorithm in ALGORITHMS},
            "examples_unreached": [row for row in rows if row.get("rta_dropped") is None][:3],
            "examples_without_call": dict(missing),
            "examples_kept": [row for row in rows if row.get("rtat_dropped") == [] and row["index"]][:3],
            "examples_added": [row for row in rows if row.get("rtat_added")][:3]}


def lambdas(graph: dict, code: Bytecode) -> dict:
    """invokedynamic lambdas and method references; Kotlin's lambda classes and FunctionN dispatch."""
    counts = collections.Counter()
    index_names = collections.defaultdict(set)
    for edge in graph["edges"]:
        index_names[edge["site"]].add(_symbol_name(edge["symbol"]))
    examples = collections.defaultdict(list)
    for edge in code.lambdas:
        kind = edge["kind"]
        counts[f"{kind} sites"] += 1
        for algorithm in ALGORITHMS:
            if edge["reached"].get(algorithm):
                counts[f"{kind} reached by {algorithm.upper()}"] += 1
        file, at = edge["site"].rsplit(":", 1)
        if any(_jvm_name(_method(edge["callee"])) in index_names.get(f"{file}:{int(at) + delta}", ())
               for delta in range(0, 6)):
            counts[f"{kind}: the index names the target within five lines"] += 1
        if len(examples[kind]) < 3:
            examples[kind].append({"site": edge["site"], "callee": edge["callee"], "reached": edge["reached"]})
    lambda_classes = [name for name, cls in code.classes.items() if cls.get("super") == "kotlin/jvm/internal/Lambda"]
    counts["Kotlin lambda classes (extend kotlin/jvm/internal/Lambda)"] = len(lambda_classes)
    fan = collections.defaultdict(list)
    for call in code.raw["calls"]:
        if re.match(r"kotlin/jvm/functions/Function\d+\.invoke\(", call["declared"]):
            fan[call["alg"]].append(sum(1 for target in call["targets"] if _owner(target) in code.classes))
    for algorithm, sizes in fan.items():
        if sizes:
            counts[f"FunctionN.invoke sites ({algorithm})"] = len(sizes)
            counts[f"FunctionN.invoke mean project targets ({algorithm})"] = round(sum(sizes) / len(sizes), 1)
            counts[f"FunctionN.invoke max project targets ({algorithm})"] = max(sizes)
    return {"counts": dict(counts), "examples": dict(examples), "lambda_class_examples": lambda_classes[:3]}


def _index_names(graph: dict) -> dict:
    """Names the index links at each line, with the getter and setter names of a property."""
    names = collections.defaultdict(set)
    for edge in graph["edges"]:
        name = _symbol_name(edge["symbol"])
        if name:
            names[edge["site"]].update({name, f"get{name[:1].upper()}{name[1:]}", f"set{name[:1].upper()}{name[1:]}",
                                        f"is{name[:1].upper()}{name[1:]}"})
            if name == "<init>":
                names[edge["site"]].add("<init>")
    return names


def losses(graph: dict, code: Bytecode, inline: dict) -> dict:
    """Index calls the bytecode does not hold at that line, and bytecode calls the index does not name."""
    nodes = {node["id"]: node for node in graph["nodes"]}
    counts, examples = collections.Counter(), collections.defaultdict(list)

    def note(kind: str, item):
        counts[kind] += 1
        if len(examples[kind]) < 3:
            examples[kind].append(item)

    for edge in graph["edges"]:
        if edge["kind"] != "call" or edge["chain"] or edge["end"] not in ("project-callable", "external"):
            continue
        name = _symbol_name(edge["symbol"])
        if not name:
            continue
        rel, line = edge["site"].rsplit(":", 1)
        here = {_jvm_name(_method(call["declared"])) for call in code.at.get((rel, int(line)), ())}
        here |= {_jvm_name(_method(item["callee"])) for item in code.lambdas if item["site"] == edge["site"]}
        counts["index calls"] += 1
        if name in here or (name == "<init>" and "<init>" in here):
            counts["held at the same line"] += 1
        elif f"{name}$default" in here:
            note("held as name$default", edge["site"] + " " + name)
        elif any(item.startswith("access$") and name in item for item in here):
            note("held through a synthetic accessor", edge["site"] + " " + name)
        else:
            place = _place(nodes, edge["to"])
            text = ""
            if place and edge["end"] == "project-callable":
                file, at = place.rsplit(":", 1)
                try:
                    text = (code.source / file).read_text(encoding="utf-8").split("\n")[int(at) - 1]
                except (OSError, IndexError, UnicodeError):
                    text = ""
            near = {_jvm_name(_method(call["declared"])) for delta in (-2, -1, 1, 2)
                    for call in code.at.get((rel, int(line) + delta), ())}
            if re.search(r"\binline\b", text) or inline.get((edge["site"], edge["symbol"])):
                note("lost: inline function, body copied into the caller", edge["site"] + " " + name)
            elif name in PRIMITIVE:
                note("lost: primitive operator or conversion, a JVM instruction", edge["site"] + " " + name)
            elif name in near:
                note("held two lines away or less", edge["site"] + " " + name)
            else:
                note("lost: other", edge["site"] + " " + name)
    names = _index_names(graph)
    for call in code.raw["calls"]:
        if call["alg"] != "cha":  # CHA holds every project method's call sites
            continue
        rel = code.files.get(_owner(call["caller"]))
        site, name, owner = f"{rel}:{call['line']}", _jvm_name(_method(call["declared"])), _owner(call["declared"])
        counts["bytecode calls"] += 1
        if name in names.get(site, ()):
            continue
        if call["line"] > code.lines(rel) > 0:
            note("bytecode only: line beyond the file (inlined body, SMAP)", site + " " + call["declared"])
        elif owner == "kotlin/jvm/internal/Intrinsics":
            note("bytecode only: Kotlin null checks (Intrinsics)", site + " " + call["declared"])
        elif _method(call["declared"]).endswith("$default"):
            note("bytecode only: $default", site + " " + call["declared"])
        elif _method(call["declared"]).startswith("access$"):
            note("bytecode only: synthetic accessor", site + " " + call["declared"])
        elif owner.endswith("$DefaultImpls"):
            note("bytecode only: interface DefaultImpls", site + " " + call["declared"])
        elif re.match(r"java/lang/(Integer|Long|Double|Float|Boolean|Character|Short|Byte)\.(valueOf|\w+Value)$",
                      f"{owner}.{_method(call['declared'])}"):
            note("bytecode only: boxing", site + " " + call["declared"])
        elif owner == "java/lang/StringBuilder":
            note("bytecode only: string building", site + " " + call["declared"])
        elif name in ("iterator", "hasNext", "next"):
            note("bytecode only: iteration protocol", site + " " + call["declared"])
        else:
            note("bytecode only: other", site + " " + call["declared"])
    for call in code.raw["calls"]:
        if call["alg"] != "cha":
            continue
        method, owner = _method(call["declared"]), _owner(call["declared"])
        rel = code.files.get(_owner(call["caller"]))
        if method.endswith("$default"):
            counts["all bytecode calls to a $default method"] += 1
        if method.startswith("access$"):
            counts["all bytecode calls to a synthetic accessor"] += 1
        if owner.endswith("$DefaultImpls"):
            counts["all bytecode calls to an interface DefaultImpls"] += 1
        if call["line"] > code.lines(rel) > 0:
            counts["all bytecode calls at a line beyond the file (SMAP)"] += 1
    coroutines = sum(1 for signature in code.methods if "kotlin/coroutines/Continuation" in signature)
    counts["methods taking a Continuation (coroutines)"] = coroutines
    return {"counts": dict(counts), "examples": dict(examples)}


def _where(target: dict | None) -> tuple[str, str | None]:
    """Where an answer lies: project source, a jar and its version, the JDK, the Kotlin builtins, or a project
    member (delegated, inherited) whose original lies in one of those."""
    if target is None:
        return "no answer", None
    if target.get("file"):
        return "project source", None
    jar = kotlin_analysis.external(target)
    if jar and jar.get("version"):
        return "jar with a version", f"{jar['artifact']} {jar['version']}"
    if jar and jar.get("jdk"):
        return "JDK", None
    module = target.get("module") or ""
    if "Builtins" in module:
        return "Kotlin builtins, no jar", None
    if target.get("origin") == "SAM_CONSTRUCTOR":
        return "SAM constructor, no jar", None
    for other in [target.get("original"), *(target.get("overridden") or ())]:
        if other:
            where, artifact = _where(other)
            if where in ("jar with a version", "JDK", "Kotlin builtins, no jar"):
                return f"project member ({target.get('origin')}) of {where}", artifact
    return f"no jar ({module})", None


def _verdicts(graph: dict, raw: dict) -> dict:
    """The Analysis API on klaxon: uncertain arcs, implicit holes, packageless references."""
    answers, nodes = raw["answers"], {node["id"]: node for node in graph["nodes"]}
    by_place = collections.defaultdict(list)  # (mode, file, line, symbol or None) -> sites
    for site in raw["sites"]:
        for symbol in site["symbols"] or [None]:
            by_place[(site["mode"], site["file"], site["line"], symbol)].append(site["site"])

    out = {}
    # Uncertain arcs: the overload the API names, among the graph's candidates or not.
    counts, examples = collections.Counter(), collections.defaultdict(list)
    overridden = {}  # a candidate's declaration -> the declarations it overrides
    for site in raw["sites"]:
        if site["mode"] == "overridden":
            overridden[f"{site['file']}:{site['line']}"] = {_project_place(target)
                                                             for target in answers[site["site"]]["target"]}
    for edge in graph["edges"]:
        uncertain = edge.get("uncertain")
        if not uncertain:
            continue
        rel, line = edge["site"].rsplit(":", 1)
        chosen = {_project_place(target) for site in by_place.get(("ref", rel, int(line), edge["symbol"]), ())
                  for target in answers[site]["target"]} - {None}
        candidates = {_place(nodes, key) for key in uncertain["candidates"]} - {None}
        if "implementation" in edge["chain"]:
            # the implementation is the candidate that overrides the overload the call reaches
            right = {place for place in candidates if chosen & overridden.get(place, set())}
        else:
            right = candidates & chosen
        index_place = _place(nodes, edge["to"])
        if not chosen:
            verdict = "no answer"
        elif len(right) != 1:
            verdict = "answer not among the candidates" if not right else "several candidates"
        elif index_place in right:
            verdict = "certain: the index's overload"
        else:
            verdict = "certain: another candidate"
        counts[f"{uncertain['reason']}{' (implementation)' if 'implementation' in edge['chain'] else ''}: {verdict}"] += 1
        if len(examples[verdict]) < 3:
            examples[verdict].append({"site": edge["site"], "index": index_place, "api": sorted(right or chosen)})
    out["uncertain"] = {"counts": dict(counts), "examples": dict(examples)}
    # Implicit-operator holes: a target for the role, in the project or in a jar with a version.
    counts, examples = collections.Counter(), collections.defaultdict(list)
    used = collections.Counter()
    for hole in graph["holes"]:
        if hole["class"] != "implicit-operator":
            continue
        rel, line = hole["site"].rsplit(":", 1)
        role = ROLES.get(hole["reason"])
        elements = [element for site in by_place.get(("implicit", rel, int(line), None), ())
                    for element in answers[site]["detail"]["elements"] if element["role"] == role]
        nth = used[(hole["site"], role)]
        used[(hole["site"], role)] += 1
        element = elements[nth] if nth < len(elements) else (elements[0] if elements else None)
        targets = element["targets"] if element else []
        called = [target for target in targets if target.get("callable") or target.get("class")]
        where, artifact = _where((called or targets or [None])[0])
        verdict = f"{where} ({artifact})" if artifact else where
        counts[f"{role}: {verdict}"] += 1
        key = f"{where} {role}"
        if len(examples[key]) < 3:
            examples[key].append({"site": hole["site"], "targets": [
                {k: target.get(k) for k in ("callable", "params", "module", "inline")} for target in targets[:2]]})
    out["implicit"] = {"counts": dict(counts), "examples": dict(examples)}
    # Packageless references: the jar and version the API places them in.
    counts, examples, artifacts = collections.Counter(), collections.defaultdict(list), collections.Counter()
    for edge in graph["edges"]:
        if edge["end"] != "external" or (nodes.get(edge["to"], {}).get("external") or {}).get("manager") != "unknown":
            continue
        rel, line = edge["site"].rsplit(":", 1)
        targets = [target for site in by_place.get(("ref", rel, int(line), edge["symbol"]), ())
                   for target in answers[site]["target"]]
        target = (targets or [None])[0]
        verdict, artifact = _where(target)
        if artifact:
            artifacts[artifact] += 1
        counts[verdict] += 1
        if len(examples[verdict]) < 3:
            examples[verdict].append({"site": edge["site"], "symbol": edge["symbol"].split(" ")[-1],
                                      "api": {k: (target or {}).get(k) for k in ("callable", "class", "origin", "module")}})
    out["packageless"] = {"counts": dict(counts), "artifacts": dict(artifacts.most_common()),
                          "examples": dict(examples)}
    out["engine"] = raw["engine"]
    return out


def _inline_flags(graph: dict, raw: dict | None) -> dict:
    """(site, symbol) of index edges whose packageless target the Analysis API calls inline."""
    flags = {}
    if not raw:
        return flags
    for site in raw["sites"]:
        if site["mode"] == "ref" and any(target.get("inline") for target in raw["answers"][site["site"]]["target"]):
            for symbol in site["symbols"]:
                flags[(f"{site['file']}:{site['line']}", symbol)] = True
    return flags


def hand_check(graphs: dict, codes: dict, raw_answers: dict | None) -> dict:
    """Each hand-read site scored for the index graph, the Analysis API, RTA and CHA."""
    rows = []
    for check in HAND_CHECK:
        graph, code = graphs[check["case"]], codes.get(check["case"])
        nodes = {node["id"]: node for node in graph["nodes"]}
        rel, line = check["site"].rsplit(":", 1)
        token, kind = check["token"], check["kind"]
        edges = [edge for edge in graph["edges"] if edge["site"] == check["site"]]
        direct = [edge for edge in edges if not edge["chain"] and _symbol_name(edge["symbol"]) in (token, "<init>")]
        impls = {_place(nodes, edge["to"]) for edge in edges if "implementation" in edge["chain"]
                 and _symbol_name(edge["symbol"]) == token}
        row = {"site": f"{check['site']} {token}", "kind": kind, "why": check["why"], "scores": {}, "got": {}}
        # the index graph
        if kind in ("overload", "dispatch"):
            places = sorted({_place(nodes, edge["to"]) for edge in direct} - {None})
            row["got"]["index"] = {"target": places, "implementations": sorted(impls - {None}),
                                   "uncertain": sorted({edge["uncertain"]["reason"] for edge in edges if edge.get("uncertain")})}
            target_ok = "def" not in check or check["def"] in places and len(places) == 1
            expected = impls if check.get("impls") == "all-index" else set(check.get("impls", ()))
            impls_ok = kind != "dispatch" or impls == expected
            row["scores"]["index"] = "right" if target_ok and impls_ok else "wrong"
            row["expected_implementations"] = sorted(expected - {None}) if kind == "dispatch" else None
        elif kind == "implicit":
            holes = {hole["site"] for hole in graph["holes"] if hole["class"] == "implicit-operator"}
            row["got"]["index"] = sorted({edge["symbol"].split(" ")[-1] for edge in edges
                                          if _symbol_name(edge["symbol"]) == check["role"]})
            row["scores"]["index"] = "miss (hole)" if check["site"] in holes else (
                "right" if any(re.search(check["callable"], name.replace("#", ".").rstrip("().")) for name in
                               row["got"]["index"]) else "wrong")
        else:
            names = {_symbol_name(edge["symbol"]) for edge in edges}
            row["got"]["index"] = sorted(name for name in names if name)
            row["scores"]["index"] = "right" if check["index"] in names else "miss"
        # the Analysis API
        if check["case"] == "klaxon" and raw_answers:
            answers = raw_answers["answers"]
            found = [site for site in raw_answers["sites"] if site["file"] == rel and site["line"] == int(line)
                     and "hand check" in site["why"]]
            targets = [target for site in found for target in answers[site["site"]]["target"]]
            if kind == "implicit":
                elements = [element for site in found for element in answers[site["site"]]["detail"]["elements"]
                            if element["role"] == check["role"]]
                targets = [target for element in elements for target in element["targets"]]
                ok = any(re.search(check["callable"], target.get("callable") or "") or any(
                    re.search(check["callable"], (other.get("callable") or "")) for other in target.get("overridden", ()))
                    or re.search(check["callable"], ((target.get("original") or {}).get("callable") or ""))
                    for target in targets)
                if check.get("artifact"):
                    ok = ok and any((kotlin_analysis.external(target) or {}).get("artifact") == check["artifact"]
                                    for target in targets)
            else:
                places = [_project_place(target) for target in targets if target.get("file")]
                ok = places == [check["def"]] if "def" in check else None
                if kind == "dispatch" and "def" in check:
                    over = [site for site in raw_answers["sites"] if site["mode"] == "overridden"]
                    hits = set()
                    for site in over:
                        if any(_project_place(target) == check["def"] for target in answers[site["site"]]["target"]):
                            hits.add(f"{site['file']}:{site['line']}")
                    row["got"]["api_overrides_of_target"] = sorted(hits)
                    jackson = {impl for impl in check["impls"] if "jackson" in impl}
                    ok = ok and jackson <= hits
            row["got"]["api"] = [{k: target.get(k) for k in ("callable", "params", "file", "line", "module", "inline")}
                                 for target in targets][:4]
            row["scores"]["api"] = "n/a" if ok is None else ("right" if ok else "wrong")
        else:
            row["scores"]["api"] = "n/a"
        # the bytecode call graph
        if code is None:
            rows.append(row)
            continue
        if kind == "lambda":
            for algorithm in ALGORITHMS:
                hits = [edge for edge in code.lambdas if edge["caller"].startswith(check["caller"])
                        and edge["callee"].startswith(check["impl"])]
                row["got"][algorithm] = [{"site": edge["site"], "callee": edge["callee"], "reached": edge["reached"]}
                                         for edge in hits]
                row["scores"][algorithm] = "right" if any(edge["reached"].get(algorithm) for edge in hits) else "wrong"
            rows.append(row)
            continue
        name = "<init>" if kind == "overload" and token[:1].isupper() else ("get" if token == "[" else token)
        calls = code.at.get((rel, int(line)), [])
        for algorithm in ALGORITHMS:
            mine = [call for call in calls if call["alg"] == algorithm]
            declared = sorted({call["declared"] for call in mine})
            row["got"][algorithm] = {"declared": declared[:6]}
            if not mine:
                row["scores"][algorithm] = "unreached caller"
                continue
            if kind in ("overload", "implicit") or "jvm" in check:
                if any(item.startswith(check["jvm"]) for item in declared):
                    verdict = "right"
                elif any(_method(item).endswith("$default") and _jvm_name(_method(item)) == token for item in declared):
                    verdict = "distorted ($default)"
                else:
                    verdict = "wrong"
            else:
                verdict = "right"
            if kind == "dispatch":
                if check["impls"] == "all-index":
                    expected = {code.jvm_class(edge["to"], _place(nodes, edge["to"]), token) for edge in edges
                                if "implementation" in edge["chain"] and _symbol_name(edge["symbol"]) == token}
                else:
                    expected = {code.class_at(place.rsplit(":", 1)[0], int(place.rsplit(":", 1)[1]), token)
                                for place in check["impls"]}
                got = code.targets([call for call in code.calls(rel, int(line), token) if call["alg"] == algorithm],
                                   algorithm, token)
                declared_classes = {_owner(call["declared"]) for call in code.calls(rel, int(line), token)}
                got -= declared_classes
                row["got"][algorithm].update(implementations=sorted(got), expected_classes=sorted(c for c in expected if c))
                if verdict == "right" and got != {c for c in expected if c}:
                    verdict = "wrong"
            row["scores"][algorithm] = verdict
        rows.append(row)
    totals = collections.Counter((source, verdict.split(" ")[0]) for row in rows for source, verdict in row["scores"].items())
    return {"totals": {f"{source} {verdict}": count for (source, verdict), count in sorted(totals.items())},
            "sites": rows}


def compare(raw: dict, graphs: dict, sources: dict, builds: dict) -> dict:
    """Everything the result file reports, from the raw answers of both engines and the index graphs."""
    result = {"builds": builds, "jvm": {}, "kotlin_analysis": None}
    codes = {}
    for case in ("javapoet", "klaxon"):
        data = raw.get(f"jvm-{case}")
        if not data:
            continue
        code = codes[case] = Bytecode(data, sources[case])
        graph = graphs[case]
        edges = data["edges"]
        result["jvm"][case] = {
            "engine": data["engine"],
            "edges": {"total": len(edges), **{algorithm: sum(1 for e in edges if algorithm in e["algorithms"])
                                              for algorithm in ALGORITHMS},
                      **{f"{algorithm}_external": sum(1 for e in edges if algorithm in e["algorithms"] and e["external"])
                         for algorithm in ALGORITHMS},
                      "callers": {algorithm: len({call["caller"] for call in data["calls"] if call["alg"] == algorithm})
                                  for algorithm in ALGORITHMS}},
            "instantiated_project_classes": sum(1 for name in code.instantiated if name in code.classes),
            "project_classes": len(code.classes),
            "dispatch": dispatch(graph, code),
            "lambdas": lambdas(graph, code),
            "losses": losses(graph, code, _inline_flags(graph, raw.get("kotlin-answers")) if case == "klaxon" else {}),
        }
    if raw.get("kotlin-answers"):
        result["kotlin_analysis"] = _verdicts(graphs["klaxon"], raw["kotlin-answers"])
    result["hand_check"] = hand_check(graphs, codes, raw.get("kotlin-answers"))
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "compare"))
    parser.add_argument("--raw", help="fetch: also download the raw answers here; compare: read them from here")
    parser.add_argument("--javapoet", help="compare: javapoet's checkout")
    parser.add_argument("--klaxon", help="compare: klaxon's checkout")
    parser.add_argument("--graphs", help="compare: a directory with graph-java-javapoet.json and graph.json")
    args = parser.parse_args()
    if args.command == "spawn":
        function = modal.Function.from_name("daodan-strong-jvm", "strong_case")
        print(function.spawn().object_id)
    elif args.command == "fetch":
        RESULTS.mkdir(parents=True, exist_ok=True)
        data = b"".join(volume.read_file(f"{TAG}/{RESULT}"))
        (RESULTS / RESULT).write_bytes(data.replace(b"\r\n", b"\n"))
        print("result", len(data))
        if args.raw:
            folder = Path(args.raw)
            folder.mkdir(parents=True, exist_ok=True)
            for name in RAW:
                try:
                    (folder / name).write_bytes(b"".join(volume.read_file(f"{STORE}/{name}")))
                    print(name, (folder / name).stat().st_size)
                except Exception as error:
                    print(name, "not on the volume:", type(error).__name__)
    else:
        folder = Path(args.raw)
        raw = {name[:-5]: json.loads((folder / name).read_text(encoding="utf-8")) for name in RAW
               if (folder / name).is_file() and name != "builds.json"}
        builds = json.loads((folder / "builds.json").read_text(encoding="utf-8")) if (folder / "builds.json").is_file() else {}
        graph_dir = Path(args.graphs) if args.graphs else RESULTS
        graphs = {"javapoet": json.loads((graph_dir / "graph-java-javapoet.json").read_text(encoding="utf-8")),
                  "klaxon": json.loads((graph_dir / "graph.json").read_text(encoding="utf-8"))}
        result = compare(raw, graphs, {"javapoet": Path(args.javapoet), "klaxon": Path(args.klaxon)}, builds)
        (RESULTS / RESULT).write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                                      newline="\n")
        print(RESULTS / RESULT, json.dumps(result["hand_check"]["totals"]))
