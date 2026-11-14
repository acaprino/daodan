"""The call graph of compiled JVM classes, Java and Kotlin together: WALA's CHA and RTA.

WALA 1.9.0 over the classes a build already wrote: CHA (`CHACallGraph`, project targets only) and RTA
(`Util.makeRTABuilder`, which walks the JDK and the jars too). Both model `invokedynamic` lambdas and method
references with WALA's lambda summaries. Every concrete project method is an entry point and allocates
nothing, so RTA's instantiated classes are those some reachable `new` creates (`JvmCallGraph.java`); a second
RTA, `rtat`, also lets the test runner create each concrete class with a `@Test` annotation (JUnit, TestNG).
SootUp 3.0.1, the other candidate, gives `invokedynamic` no target in its released CHA and RTA.

`analyze` returns one edge per caller, callee and call site, with the algorithms that hold it; a call site is
`file:line` from the class's source file attribute, its package and the source roots given for its class
directory. `lambda` and `method-reference` edges go from the `invokedynamic` site to the implementation
method its bootstrap names; `reached` says whether RTA's lambda summary calls it.
"""
from __future__ import annotations

import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph as scip_graph  # noqa: E402

VERSION = "1.9.0"  # com.ibm.wala:com.ibm.wala.core on Maven Central, released 2026-10-30
SOURCE = Path(__file__).with_name("JvmCallGraph.java")
JDK = "/opt/jdk"  # the JDK of adapters/kotlin.py: WALA reads its standard library from the jmods
CLASSPATH = "/opt/wala/classpath.txt"
HEAP = "-Xmx6g"
# The JDK outside what these projects call: kept out of the hierarchy, as WALA's own regression exclusions do.
EXCLUSIONS = ["java/awt/.*", "javax/swing/.*", "javax/sound/.*", "javax/imageio/.*", "javax/print/.*",
              "javax/management/.*", "javax/naming/.*", "javax/xml/.*", "javax/crypto/.*", "javax/net/.*",
              "javax/security/.*", "javax/sql/.*", "javax/accessibility/.*", "java/sql/.*", "java/rmi/.*",
              "java/applet/.*", "java/beans/.*", "java/net/http/.*", "sun/.*", "com/sun/.*", "jdk/.*", "apple/.*",
              "org/w3c/.*", "org/xml/.*", "org/ietf/.*", "org/omg/.*"]
DISPATCH = {"VIRTUAL": "virtual", "INTERFACE": "interface", "SPECIAL": "special", "STATIC": "static"}


def install_commands(coursier: str = "/opt/coursier.jar") -> list[str]:
    """WALA's classpath, fetched by coursier."""
    return ["mkdir -p /opt/wala",
            f"{JDK}/bin/java -jar {coursier} fetch --classpath com.ibm.wala:com.ibm.wala.core:{VERSION} > {CLASSPATH}"]


def build(work_dir: Path) -> Path:
    """JvmCallGraph.java compiled against WALA, cached by the source's digest."""
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()[:12]
    out = Path(work_dir) / f"jvm-callgraph-{VERSION}-{digest}"
    if (out / "JvmCallGraph.class").is_file():
        return out
    out.mkdir(parents=True, exist_ok=True)
    done = subprocess.run([f"{JDK}/bin/javac", "-nowarn", "-d", str(out), "-cp", Path(CLASSPATH).read_text().strip(),
                           str(SOURCE)], capture_output=True, text=True, timeout=600)
    if done.returncode != 0:
        raise RuntimeError("JvmCallGraph.java did not compile: " + done.stderr[-1500:])
    return out


def _owner(signature: str) -> str:
    return signature.split(".", 1)[0] if "(" in signature else signature


def _name(signature: str) -> str:
    return signature.split("(", 1)[0].rsplit(".", 1)[-1]


def analyze(class_dirs: list, classpath: list, work_dir: Path, project_dir: Path | None = None,
            roots: dict | None = None) -> dict:
    """`{"edges", "engine", "classes", "methods", "instantiated", "files", "calls", "trampolines"}`.

    `roots` maps a class directory to the checkout-relative source roots its classes come from; a call site's
    file is the first root holding the class's package path and source file under `project_dir`.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    classes_dir = build(work_dir)
    exclusions, settings, output = work_dir / "exclusions.txt", work_dir / "jvm-callgraph.txt", work_dir / "jvm-callgraph.jsonl"
    exclusions.write_text("\n".join(EXCLUSIONS) + "\n", encoding="utf-8")
    settings.write_text("".join(f"dir {path}\n" for path in class_dirs) + "".join(f"jar {path}\n" for path in classpath)
                        + f"exclusions {exclusions}\nout {output}\n", encoding="utf-8")
    command = [f"{JDK}/bin/java", HEAP, "-cp", f"{classes_dir}:{Path(CLASSPATH).read_text().strip()}", "JvmCallGraph",
               str(settings)]
    run = scip_graph.measured(command, str(work_dir), None, 3000)
    records = collections.defaultdict(list)
    if output.is_file():
        for row in output.read_text(encoding="utf-8").splitlines():
            item = json.loads(row)
            records[item.pop("t")].append(item)
    classes = {item["name"]: item for item in records["class"]}
    methods = {item["sig"]: item for item in records["method"]}
    sources = {}

    def site_file(caller: str) -> str | None:
        owner = classes.get(_owner(caller))
        if owner is None or not owner.get("source"):
            return None
        if owner["name"] not in sources:
            package = owner["name"].rsplit("/", 1)[0] + "/" if "/" in owner["name"] else ""
            found = None
            for root in (roots or {}).get(owner.get("dir"), ()):
                candidate = f"{root}/{package}{owner['source']}" if root else f"{package}{owner['source']}"
                if project_dir is None or (Path(project_dir) / candidate).is_file():
                    found = candidate
                    break
            sources[owner["name"]] = found or f"{package}{owner['source']}"
        return sources[owner["name"]]

    reached = collections.defaultdict(set)
    for item in records["trampoline"]:
        reached[(item["alg"], item["class"])].update(item["targets"])
    edges = {}
    for call in records["call"]:
        rel = site_file(call["caller"])
        site = f"{rel}:{call['line']}"
        lambda_ = call.get("lambda") or {}
        if lambda_.get("impl"):
            impl = lambda_["impl"]
            impl = impl[1:] if impl.startswith("L") else impl
            # javac names a lambda body `lambda$m$0`, kotlinc `m$lambda-0`; any other handle is a method reference
            kind = "lambda" if _name(impl).startswith("lambda$") or "$lambda-" in _name(impl) else "method-reference"
            key = (call["caller"], impl, site, kind)
            edge = edges.setdefault(key, {"caller": call["caller"], "callee": impl, "site": site, "kind": kind,
                                          "external": _owner(impl) not in classes, "algorithms": [],
                                          "pc": call["pc"], "reached": {}})
            edge["algorithms"] = sorted(set(edge["algorithms"]) | {call["alg"]})
            edge["reached"][call["alg"]] = impl in reached.get((call["alg"], lambda_["summary"]), ())
            continue
        kind = DISPATCH.get(call["invoke"], call["invoke"].lower())
        targets = call["targets"] or [call["declared"]]
        for target in targets:
            key = (call["caller"], target, site, call["pc"])
            edge = edges.setdefault(key, {"caller": call["caller"], "callee": target, "site": site, "kind": kind,
                                          "external": _owner(target) not in classes, "algorithms": [],
                                          "pc": call["pc"], "declared": call["declared"],
                                          "resolved": bool(call["targets"])})
            edge["algorithms"] = sorted(set(edge["algorithms"]) | {call["alg"]})
    for name in classes:  # every project class's source file, for callers and callees alike
        site_file(f"{name}.?()")
    engine = (records["engine"] or [{}])[0]
    engine.update({"name": "wala", "version": VERSION, "seconds": run["seconds"], "peak_mb": run["peak_mb"],
                   "returncode": run["returncode"], "stderr_tail": run["stderr_tail"][-800:]})
    return {"edges": list(edges.values()), "engine": engine, "classes": classes, "methods": methods,
            "instantiated": (records["instantiated"] or [{"classes": []}])[0]["classes"],
            "files": dict(sources), "calls": records["call"], "trampolines": records["trampoline"]}
