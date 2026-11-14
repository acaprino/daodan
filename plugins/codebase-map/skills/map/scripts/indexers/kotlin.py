"""scip-java for Kotlin: how it runs, and what its index leaves to the reader.

`index` runs scip-java's Gradle build in a container (`indexers.jvm`; see "How it runs" below). The indexer
writes `is_implementation` on the overriding member, pointing to the member it overrides; the aggregator adds
the reverse one on the overridden member (`is_implementation` and `is_reference`, ScipAggregator.java), which
`forward_only` drops so the shared reader sees one direction.

- a property reference is written as the property plus its getter (and setter) at the same range, a
  companion member through its class symbol, an extension function as its own symbol: no hop is needed;
- the overload number `(+N)` follows source order for a declaration with source and compiled member order
  for one on another task's classpath, so a reference across compile tasks to an overloaded project function,
  and an override relation across tasks, can name the wrong overload: `refine` marks those edges uncertain
  with every overload of the name in the target class as candidates;
- calls the index never writes (`x[k]`, `x[k] = v`, the `for` iterator, `by` delegates, `componentN`) are
  found with tree-sitter and become holes of class `implicit-operator`;
- the package placeholder `. .` names both project symbols (the test tasks) and every Kotlin builtin or stdlib
  symbol: `classify` keeps it a project symbol only under a package path where the index defines `. .`
  symbols, else an external with manager `unknown` and the Kotlin package path; a namespace symbol (`package`
  and `import` lines, never defined) is a namespace.
"""
from __future__ import annotations

import collections
import re
from pathlib import Path

import code_graph

OVERLOAD = re.compile(r"^(.*[#/])([^#/().]+|`[^`]+`)\((?:\+\d+)?\)\.$")  # owner, name of a method symbol
OPERATORS = {"indexed read": "get", "indexed assignment": "set", "for loop": "iterator",
             "property delegate": "getValue", "destructuring entry": "componentN"}


def hops(index) -> dict:
    """None: the index states its aliases at the reference itself (see the module docstring)."""
    return {}


def _package_path(descriptors: str) -> str:
    return "/".join(name for name, kind in code_graph.descriptors(descriptors) if kind == "namespace")


def classify(index):
    """The classification of a symbol key for the shared traversal (see the module docstring)."""
    own = {_package_path(parts[4]) for parts in map(code_graph.split_symbol, map(code_graph._global, index.defs))
           if parts and parts[2] == "."}

    def classified(key: str):
        if key.endswith("/"):
            return "namespace"
        parts = code_graph.split_symbol(code_graph._global(key))
        if parts is None or parts[2] != "." or key in index.defs:
            return None
        path = _package_path(parts[4])
        return "project" if path in own else {"manager": "unknown", "package": path, "version": "unknown"}
    return classified


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

    for edge in graph["edges"]:
        symbol, target = edge["symbol"], edge["to"]
        site = compiled.get(edge["site"].rsplit(":", 1)[0])
        if candidates(symbol) and site and _task(index, compiled, symbol) not in (None, site):
            edge["uncertain"] = {"reason": "overload-across-tasks", "candidates": candidates(target) or [target]}
        elif ("implementation" in edge["chain"] and (candidates(symbol) or candidates(target))
              and None not in (_task(index, compiled, target), _task(index, compiled, symbol))
              and _task(index, compiled, target) != _task(index, compiled, symbol)):
            edge["uncertain"] = {"reason": "override-across-tasks", "candidates": candidates(target) or [target]}
    graph["holes"] += _implicit(index)


# How it runs: `indexers.jvm`. scip-java's Gradle build in the preparation writes the index and, per KotlinCompile
# task, the sources and classpath its Kotlin Analysis API indexer read (`kotlin-configs/`); the execution copies
# those out. The index is read even when the build exits with an error, as long as scip-java wrote it.

MIN_FREE = 5 * 2**30  # the container's memory: 4,688 MB for all its processes on klaxon (13 November 2026)
PREPARE = r'''step index "$SCIP_JAVA" index --output "$OUT/index.scip"
[ -f "$OUT/index.scip" ]
'''
EXECUTE = r'''if [ -d build/scip-targetroot/kotlin-configs ]; then
  step configs cp -r build/scip-targetroot/kotlin-configs "$OUT/kotlin-configs"
fi
exit 0
'''


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, *, engine=None,
          memory: int = MIN_FREE) -> dict:
    """The forward-only index of the whole build, its runs, the indexer's time and memory and `configs`, the
    compile tasks `refine` reads (`files` is not used: the build compiles every task). Without a container,
    `unavailable`; without an index, `failed`."""
    from indexers import jvm
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    result, runs, out = jvm.run(project_dir, work_dir, PREPARE, EXECUTE, memory=memory, engine=engine)
    return finish(work_dir, result, runs, out)


def finish(work_dir: Path, result: dict, runs: list[dict], out: Path) -> dict:
    """The contract from what came back into `out`: the index as scip-java wrote it (`scip-java-0.scip`), its
    forward-only copy (`index-forward.scip`) and `kotlin-configs/`, placed in `work_dir`."""
    from indexers import jvm
    if result["state"] == "gap":
        return jvm.unavailable(result["cause"], result["remedy"])
    written = jvm.place(out / "index.scip", Path(work_dir) / "scip-java-0.scip")
    if result["state"] != "done" or written is None:
        return jvm.failed(result, runs)
    configs = jvm.place(out / "kotlin-configs", Path(work_dir) / "kotlin-configs")
    forward = Path(work_dir) / "index-forward.scip"
    run = next((run for run in reversed(runs) if run["step"] == "index"), {})
    run.update(prefix="", index=str(forward), index_bytes=written.stat().st_size,
               reverse_relationships_dropped=forward_only(written, forward))
    return {"indexes": [[str(forward), ""]], "runs": runs,
            "indexer": code_graph.indexer("scip-java", jvm.VERSION, runs),
            "configs": str(configs) if configs else None, "written": str(written)}


# The aggregator's reverse relationships, dropped from a copy of the index.

def _encode_varint(value: int) -> bytes:
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
        tag, at = code_graph._varint(data, at)
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value, at = code_graph._varint(data, at)
        elif wire == 2:
            length, at = code_graph._varint(data, at)
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
        flags = {field: item for field, kind, item in code_graph._fields(value) if kind == 0}
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
                        parts += _encode_varint(field << 3 | 2) + _encode_varint(len(item)) + item
                    else:
                        parts += value[begin:stop]
                value = bytes(parts)
            else:  # external SymbolInformation
                value, count = _information(value)
            total += count
            result += _encode_varint(number << 3 | 2) + _encode_varint(len(value)) + value
        else:
            result += data[start:end]
    Path(out).write_bytes(bytes(result))
    return total
