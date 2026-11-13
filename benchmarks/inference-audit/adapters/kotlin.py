"""scip-java for Kotlin: how this engine builds its index and what its index leaves to the reader.

`index` runs `scip-java index` (0.14: the Gradle build with scip-java's init script, then its standalone
Kotlin Analysis API indexer over the sources and classpath each KotlinCompile task dumps to
`kotlin-configs/`) on a copy of the checkout. What the index states its own way, and how it is read here:
- relationships: the indexer writes `is_implementation` on the overriding member, pointing to the member it
  overrides; the aggregator adds the reverse one on the overridden member (`is_implementation` and
  `is_reference`, ScipAggregator.java), which `forward_only` drops so the shared reader sees one direction;
- a property reference is written as the property plus its getter (and setter) at the same range, a
  companion member through its class symbol, an extension function as its own symbol: no hop is needed;
- the overload number `(+N)` follows source order for a declaration with source and compiled member order
  for one on another task's classpath, so a reference across compile tasks to an overloaded project function,
  and an override relation across tasks, can name the wrong overload: `refine` marks those edges uncertain
  with every overload of the name in the target class as candidates;
- calls the index never writes (`x[k]`, `x[k] = v`, the `for` iterator, `by` delegates, `componentN`) are
  found with tree-sitter and become holes of class `implicit-operator`.
"""
from __future__ import annotations

import collections
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scip_graph  # noqa: E402

VERSION = "0.14.2"  # org.scip-code:scip-java on Maven Central, Kotlin through scip-kotlin-analysis 0.14.2
JDK = "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse"
JAVA = "/opt/jdk/bin/java"
CLASSPATH = "/opt/scip-java/classpath.txt"  # strings: the image is defined on any host
OVERLOAD = re.compile(r"^(.*[#/])([^#/().]+|`[^`]+`)\((?:\+\d+)?\)\.$")  # owner, name of a method symbol
OPERATORS = {"indexed read": "get", "indexed assignment": "set", "for loop": "iterator",
             "property delegate": "getValue", "destructuring entry": "componentN"}


def install_commands() -> list[str]:
    """A JDK 17 and scip-java's classpath, fetched by coursier at the pin of the map's engines."""
    import resolve_edges
    coursier = resolve_edges.COURSIER
    return [f"curl -fsSL '{JDK}' -o /tmp/jdk.tgz && mkdir -p /opt/jdk && "
            "tar -xzf /tmp/jdk.tgz -C /opt/jdk --strip-components=1 && rm /tmp/jdk.tgz",
            f"mkdir -p /opt/scip-java && curl -fsSL {coursier['url']} -o /opt/scip-java/coursier.jar",
            f"echo '{coursier['sha256']}  /opt/scip-java/coursier.jar' | sha256sum -c -",
            f"{JAVA} -jar /opt/scip-java/coursier.jar fetch --classpath org.scip-code:scip-java:{VERSION} "
            f"> {CLASSPATH}"]


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    """One `scip-java index` run at the checkout's root; the forward-only copy is the index to read."""
    work_dir = Path(work_dir)
    mirror = work_dir / "mirror-scip-java"
    if not mirror.exists():
        shutil.copytree(project_dir, mirror, symlinks=True)
    env = dict(os.environ, JAVA_HOME=str(Path(JAVA).parents[1]), GRADLE_USER_HOME=str(work_dir / "gradle-home"),
               TERM="dumb")
    env["PATH"] = f"{Path(JAVA).parent}{os.pathsep}{env.get('PATH', '')}"
    output = work_dir / "scip-java-0.scip"
    command = [JAVA, "-Xmx4g", "-cp", Path(CLASSPATH).read_text().strip(), "org.scip_code.scip_java.ScipJava", "index",
               "--output", str(output)]
    run = {"prefix": "", **scip_graph.measured(command, str(mirror), env, 3600)}
    run["index_bytes"] = output.stat().st_size if output.is_file() else 0
    configs = mirror / "build/scip-targetroot/kotlin-configs"
    if configs.is_dir():
        shutil.copytree(configs, work_dir / "kotlin-configs", dirs_exist_ok=True)
    forward = work_dir / "index-forward.scip"
    run["index"] = str(forward) if output.is_file() else None
    if output.is_file():
        run["reverse_relationships_dropped"] = forward_only(output, forward)
    return {"indexes": [[run["index"], ""]] if run["index"] else [], "runs": [run],
            "indexer": scip_graph.indexer("scip-java", VERSION, [run]), "configs": str(work_dir / "kotlin-configs")}


# The aggregator's reverse relationships, dropped from a copy of the index.

def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte, value = value & 0x7F, value >> 7
        out.append(byte | 0x80 if value else byte)
        if not value:
            return bytes(out)


def _spans(data: bytes):
    """`(number, wire, value, start, end)` of each field, `start:end` its raw bytes."""
    at = 0
    while at < len(data):
        start = at
        tag, at = scip_graph._varint(data, at)
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value, at = scip_graph._varint(data, at)
        elif wire == 2:
            length, at = scip_graph._varint(data, at)
            value, at = data[at:at + length], at + length
        elif wire in (1, 5):
            value, at = data[at:at + (8 if wire == 1 else 4)], at + (8 if wire == 1 else 4)
        else:
            raise ValueError(f"unsupported wire type {wire}")
        yield number, wire, value, start, at


def _rebuilt(data: bytes, keep) -> tuple[bytes, int]:
    """`data` without the fields `keep(number, wire, value)` refuses, and how many it refused."""
    out, dropped = bytearray(), 0
    for number, wire, value, start, end in _spans(data):
        if keep(number, wire, value):
            out += data[start:end]
        else:
            dropped += 1
    return bytes(out), dropped


def _information(data: bytes) -> tuple[bytes, int]:
    def keep(number, wire, value):
        if number != 4 or wire != 2:
            return True
        flags = {field: item for field, kind, item in scip_graph._fields(value) if kind == 0}
        return not (flags.get(2) and flags.get(3))  # is_reference and is_implementation: the reverse one
    return _rebuilt(data, keep)


def forward_only(source: Path, out: Path) -> int:
    """Write `source` without the aggregator's reverse relationships; returns how many were dropped."""
    data, total, result = Path(source).read_bytes(), 0, bytearray()
    for number, wire, value, start, end in _spans(data):
        if wire == 2 and number in (2, 3):
            if number == 2:  # Document: its SymbolInformation entries are field 3
                parts, count = bytearray(), 0
                for field, kind, item, begin, stop in _spans(value):
                    if field == 3 and kind == 2:
                        item, dropped = _information(item)
                        count += dropped
                        parts += _varint(field << 3 | 2) + _varint(len(item)) + item
                    else:
                        parts += value[begin:stop]
                value = bytes(parts)
            else:  # external SymbolInformation
                value, count = _information(value)
            total += count
            result += _varint(number << 3 | 2) + _varint(len(value)) + value
        else:
            result += data[start:end]
    Path(out).write_bytes(bytes(result))
    return total


def hops(index) -> dict:
    """None: the index states its aliases at the reference itself (see the module docstring)."""
    return {}


# Compile tasks, from the sources each KotlinCompile task listed for the indexer.

def tasks(configs_dir: Path | None) -> dict[str, str]:
    """Checkout-relative path -> the compile task whose dump lists it."""
    out = {}
    for config in sorted(Path(configs_dir).glob("*.txt")) if configs_dir and Path(configs_dir).is_dir() else ():
        rows = config.read_text(encoding="utf-8").splitlines()
        root = next((row.split(" ", 1)[1] for row in rows if row.startswith("sourceroot ")), "")
        for row in rows:
            if row.startswith("source ") and root and row.split(" ", 1)[1].startswith(root):
                out[Path(row.split(" ", 1)[1]).relative_to(root).as_posix()] = config.stem
    return out


def missing(index, rels: list[str], compiled: dict[str, str] | None = None) -> dict:
    """Why a Kotlin file has no document: no compile task the indexer reads lists it."""
    reasons = {}
    for rel in rels:
        if compiled and rel in compiled:
            continue
        if rel.endswith(".kts"):
            reasons[rel] = "Gradle script: no KotlinCompile task compiles it"
        elif rel.startswith("buildSrc/"):
            reasons[rel] = "buildSrc: compiled by its own build, where scip-java's tasks do not run"
        else:
            reasons[rel] = "in no Gradle source set: no KotlinCompile task lists it"
    return reasons


# Edges and holes only this engine's reader can judge.

def _overloads(index) -> dict[tuple[str, str], list[str]]:
    groups = collections.defaultdict(list)
    for key in index.defs:
        match = OVERLOAD.match(key) if "#local " not in key and not key.startswith("local ") else None
        if match:
            groups[match.groups()].append(key)
    return {name: sorted(keys) for name, keys in groups.items() if len(keys) > 1}


def _task(index, compiled: dict, key: str) -> str | None:
    places = index.defs.get(key)
    return compiled.get(places[0][0]) if places else None


def _implicit(index) -> list[dict]:
    """Implicit calls the index holds no occurrence for where they are written."""
    holes = []
    for rel in sorted(index.documents):
        if not rel.endswith(".kt"):
            continue
        tree = index.tree(rel, "kotlin")
        if tree is None:
            continue
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            stack.extend(node.children)
            places = []
            if node.type == "indexing_suffix":
                parent = node.parent
                role = ("indexed assignment" if parent is not None and parent.type == "directly_assignable_expression"
                        else "indexed read")
                places.append((role, node, OPERATORS[role]))
            elif node.type == "for_statement":
                token = next((child for child in node.children if child.type == "in"), None)
                if token is not None:
                    places.append(("for loop", token, "iterator"))
            elif node.type == "property_delegate":
                places.append(("property delegate", node, "getValue"))
            elif node.type == "multi_variable_declaration":
                entries = [child for child in node.children if child.type == "variable_declaration"]
                places += [("destructuring entry", entry, f"component{number}")
                           for number, entry in enumerate(entries, 1)]
            for role, place, name in places:
                line = place.start_point[0] + 1
                native = index.from_bytes(rel, line, place.start_point[1])
                written = [item for item in index.at.get((rel, line, native), ())
                           if not item.definition and "#local " not in item.key]
                if not written:
                    holes.append({"site": f"{rel}:{line}", "name": name, "kind": "call", "class": "implicit-operator",
                                  "reason": role})
    return holes


def refine(index, graph: dict, compiled: dict[str, str]) -> None:
    """Mark the edges an overload number can make wrong, and add the implicit-call holes."""
    overloads = _overloads(index)

    def candidates(key: str) -> list[str] | None:
        match = OVERLOAD.match(key)
        return overloads.get(match.groups()) if match else None

    if graph["edges"] and "symbol" not in graph["edges"][0]:
        raise ValueError("scip_graph edges carry no `symbol` (the key referenced at the site): overloads unjudged")
    for edge in graph["edges"]:
        edge.setdefault("uncertain", None)
        symbol, target = edge["symbol"], edge["to"]
        site = compiled.get(edge["site"].rsplit(":", 1)[0])
        if candidates(symbol) and site and _task(index, compiled, symbol) not in (None, site):
            edge["uncertain"] = {"reason": "overload-across-tasks", "candidates": candidates(target) or [target]}
        elif ("implementation" in edge["chain"] and (candidates(symbol) or candidates(target))
              and None not in (_task(index, compiled, target), _task(index, compiled, symbol))
              and _task(index, compiled, target) != _task(index, compiled, symbol)):
            edge["uncertain"] = {"reason": "override-across-tasks", "candidates": candidates(target) or [target]}
    graph["holes"] += _implicit(index)
