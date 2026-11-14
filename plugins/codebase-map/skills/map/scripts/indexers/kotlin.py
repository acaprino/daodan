"""scip-java for Kotlin: what its index leaves to the reader.

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
