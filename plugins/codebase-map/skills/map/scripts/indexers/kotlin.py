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

def tasks(configs) -> dict[str, str]:
    """Checkout-relative path -> the compile task whose dump lists it; `configs` the dumps' folders, each with
    the folder of the build it came from. Two builds are two compilations: a task is named with its build."""
    out = {}
    for folder, build in configs or ():
        for config in sorted(Path(folder).glob("*.txt")) if Path(folder).is_dir() else ():
            rows = config.read_text(encoding="utf-8").splitlines()
            root = next((row.split(" ", 1)[1] for row in rows if row.startswith("sourceroot ")), "")
            task = f"{build}/{config.stem}" if build else config.stem
            for row in rows:
                if row.startswith("source ") and root and row.split(" ", 1)[1].startswith(root):
                    rel = Path(row.split(" ", 1)[1]).relative_to(root).as_posix()
                    out[f"{build}/{rel}" if build else rel] = task
    return out


def missing(index, rels: list[str], compiled: dict[str, str] | None = None) -> dict:
    """Why a Kotlin file has no document: no compile task the indexer reads lists it."""
    reasons = {}
    for rel in rels:
        if compiled and rel in compiled:
            continue
        if rel.endswith(".kts"):
            reasons[rel] = "Gradle script: no KotlinCompile task compiles it"
        elif build_logic(rel):
            reasons[rel] = "buildSrc: compiled by its own build, where scip-java's tasks do not run"
        else:
            reasons[rel] = "no Kotlin compile task of the build lists it"
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

# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
ENTRY, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-kotlin", ("kotlin",), frozenset({"gradle-project", "maven-module"}), True
MIN_FREE = 5 * 2**30  # the container's memory: 4,688 MB for all its processes on klaxon (13 November 2026)
# Under Maven scip-java indexes Java only: `jvm.MAVEN_KOTLIN` indexes the modules' Kotlin after its build, and the
# targetroot is aggregated again into the index. scip-java runs the build tool it is told (`jvm.tool_line`), else
# the folder's. A Gradle build that gives no index and states a Java under 17 is built once more with
# `jvm.RAISE_LEVELS`: its Java compile task loads scip-java's compiler plugin on JDK 17 or newer only.
PREPARE = r'''if [ "${DAODAN_TOOL:-}" = maven ] || { [ -z "${DAODAN_TOOL:-}" ] && [ -f pom.xml ] \
    && ! ls build.gradle build.gradle.kts settings.gradle settings.gradle.kts >/dev/null 2>&1; }; then
  step index "$SCIP_JAVA" index --output "$OUT/index.scip" ${DAODAN_TOOL:+--build-tool=$DAODAN_TOOL}
  maven_kotlin "$OUT/kotlin-configs" \
    && step aggregate "$SCIP_JAVA" aggregate --output "$OUT/index.scip" "$WORK/target/scip-targetroot"
else
  step index "$SCIP_JAVA" index --output "$OUT/index.scip" ${DAODAN_TOOL:+--build-tool=$DAODAN_TOOL}
  if [ ! -f "$OUT/index.scip" ] && [ -n "${DAODAN_RAISE:-}" ]; then  # `jvm.RAISE_LEVELS`
    raise_levels
    step index "$SCIP_JAVA" index --output "$OUT/index.scip" ${DAODAN_TOOL:+--build-tool=$DAODAN_TOOL}
  fi
fi
[ -f "$OUT/index.scip" ]
'''
EXECUTE = r'''if [ -d build/scip-targetroot/kotlin-configs ]; then
  step configs cp -r build/scip-targetroot/kotlin-configs "$OUT/kotlin-configs"
fi
exit 0
'''


def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: the folder of each build with its tools, the JDKs it states and, for
    Maven, each module with the source folders Maven's own model gives it."""
    from indexers import jvm
    return {"roots": jvm.build_roots(record), "tools": jvm.build_tools(record), "toolchains": jvm.toolchains(record),
            "modules": jvm.modules(record), "other_builds": jvm.other_builds(record)}


READS = (".kt", ".kts")  # the stage hands `index` the checkout's Kotlin files


def build_logic(rel: str) -> bool:
    """A file of the build's own Kotlin: a Gradle script, or buildSrc, the build of the build's logic."""
    return rel.endswith(".kts") or "buildSrc" in rel.split("/")[:-1]


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, *, roots, tools=None, toolchains=(),
          modules=(), other_builds=(), engine=None, memory: int = MIN_FREE, declared=None) -> dict:
    """The forward-only index of each build in `roots` (the pre-map's build folders, built by their `tools`), each
    in a container of its own, its runs, the indexer's time and memory, `configs` (the compile tasks `refine`
    reads, with the build each came from) and `written` (the index as scip-java wrote it). The preparation also
    reaches the hosts the project declares (`declared`, `preparation.declared`). Without a container,
    `unavailable`; without an index, `failed`. When the Kotlin `files` are all the build's own (`build_logic`),
    which the pre-map reads through Gradle and no Kotlin compile task compiles, nothing is built: `unavailable`."""
    from indexers import jvm
    if files is not None and all(build_logic(rel) for rel in files):
        return jvm.unavailable(f"the build's own Kotlin only ({len(files)} Gradle scripts and buildSrc files): the "
                               "pre-map reads them through Gradle, and no Kotlin compile task compiles them",
                               "nothing to do: they are the build's definition, not the program's code")
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    def one(folder: Path, work: Path, tool: str | None) -> dict:
        root = jvm.build_root(project_dir, folder)
        prepare = (jvm.modules_line(modules, root) + jvm.tool_line(tool)
                   + jvm.raise_line(toolchains, root, jvm.JDK, "all") + PREPARE)
        result, runs, out = jvm.run(folder, work, prepare, EXECUTE, memory=memory, engine=engine,
                                    toolchains=toolchains, hosts=(declared or {}).get("hosts", ()))
        part = finish(work, result, runs, out)
        said = jvm.edited(runs, root) if part.get("indexes") else []
        return jvm.with_gaps(jvm.with_gaps(part, result), {"gaps": said})

    parts = jvm.builds(project_dir, work_dir, roots, one, tools)
    done = [(root, part) for root, part in parts if part.get("indexes")]
    return jvm.combined(parts, other_builds,
                        configs=[[part["configs"], root] for root, part in done if part.get("configs")],
                        written=[[part["written"], root] for root, part in done])


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
    # An index a failed step left is read, and the failure is said: what it did not compile is not in it.
    gaps = [{"kind": "build_failed", "detail": f"{item['step']} exited with code {item['returncode']}: "
             + " ".join((item.get("stderr_tail") or "").split())[-400:]}
            for item in runs if item["step"] in ("index", "kotlin", "aggregate") and item.get("returncode")
            and (item["step"] != "index" or item is run)]  # the build as declared: `jvm.edited` says it
    return {"indexes": [[str(forward), ""]], "runs": runs,
            "indexer": code_graph.indexer("scip-java", jvm.VERSION, runs),
            "configs": str(configs) if configs else None, "written": str(written),
            **({"gaps": gaps} if gaps else {})}


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
