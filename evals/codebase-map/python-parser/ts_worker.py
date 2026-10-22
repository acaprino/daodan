#!/usr/bin/env python3
"""Parse files with tree-sitter-python and emit the facts ast_worker.py emits.

Same output shape, field for field, so a disagreement between the two files is
a disagreement between the parsers or a defect in one of the two extractors,
never a difference in what was asked. Two fields exist only here:

    x  1 when the definition is inside an ERROR node or contains an ERROR or
       MISSING node, i.e. when tree-sitter itself marks it as uncertain
    err  per file: count of ERROR and MISSING nodes and the first position

Requires tree-sitter and tree-sitter-python.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import tree_sitter_python
from tree_sitter import Language, Parser

LANGUAGE = Language(tree_sitter_python.language())
PARSER = Parser(LANGUAGE)

CONTAINER_TYPES = {"function_definition", "class_definition"}


def text(node) -> str:
    if node is None:
        return "?"
    return node.text.decode("utf-8", "replace")


def compact(node) -> str:
    return "".join(text(node).split())


def tainted(node) -> int:
    if node.has_error:
        return 1
    parent = node.parent
    while parent is not None:
        if parent.type == "ERROR":
            return 1
        parent = parent.parent
    return 0


def in_block(node) -> int:
    host = node.parent if node.parent is not None and node.parent.type == "decorated_definition" else node
    parent = host.parent
    if parent is None or parent.type == "module":
        return 0
    if parent.type == "block" and parent.parent is not None and parent.parent.type in CONTAINER_TYPES:
        return 0
    return 1


def decorator_count(node) -> int:
    parent = node.parent
    if parent is None or parent.type != "decorated_definition":
        return 0
    return sum(1 for child in parent.named_children if child.type == "decorator")


def first_identifier(node):
    stack = [node]
    while stack:
        current = stack.pop(0)
        if current.type == "identifier":
            return text(current)
        stack.extend(current.named_children)
    return "?"


def definitions(root) -> list:
    """Iterative pre-order walk in source order: deep expressions must not crash."""
    out = []
    stack = [(child, [], []) for child in reversed(root.named_children)]
    while stack:
        node, chain, kinds = stack.pop()
        node_type = node.type
        if node_type in CONTAINER_TYPES:
            name = text(node.child_by_field_name("name"))
            if node_type == "class_definition":
                kind, tag = "class", "c"
            else:
                is_async = node.child_count > 0 and node.children[0].type == "async"
                kind, tag = ("async def" if is_async else "def"), "d"
            names = chain + [name]
            out.append({"q": ".".join(names), "k": kind,
                        "l": node.start_point[0] + 1, "e": node.end_point[0] + 1,
                        "c": node.start_point[1], "d": decorator_count(node),
                        "b": in_block(node), "a": ".".join(kinds), "x": tainted(node)})
            children = [(c, names, kinds + [tag]) for c in node.named_children]
        elif node_type == "type_alias_statement":
            left = node.child_by_field_name("left")
            out.append({"q": ".".join(chain + [first_identifier(left) if left else "?"]),
                        "k": "type", "l": node.start_point[0] + 1,
                        "e": node.end_point[0] + 1, "c": node.start_point[1], "d": 0,
                        "b": in_block(node), "a": ".".join(kinds), "x": tainted(node)})
            children = []
        else:
            children = [(c, chain, kinds) for c in node.named_children]
        stack.extend(reversed(children))
    return out


def imports(root) -> list:
    out = []
    stack = [root]
    while stack:
        node = stack.pop()
        kind = node.type
        line = node.start_point[0] + 1
        if kind == "import_statement":
            for name in node.children_by_field_name("name"):
                if name.type == "aliased_import":
                    out.append(["import", compact(name.child_by_field_name("name")),
                                text(name.child_by_field_name("alias")), line])
                else:
                    out.append(["import", compact(name), "", line])
            continue
        if kind in ("import_from_statement", "future_import_statement"):
            if kind == "future_import_statement":
                module = "__future__"
            else:
                module = compact(node.child_by_field_name("module_name"))
            if any(child.type == "wildcard_import" for child in node.named_children):
                out.append(["from", module, "*", "", line])
            for name in node.children_by_field_name("name"):
                if name.type == "aliased_import":
                    out.append(["from", module, compact(name.child_by_field_name("name")),
                                text(name.child_by_field_name("alias")), line])
                else:
                    out.append(["from", module, compact(name), "", line])
            continue
        stack.extend(node.children)
    return out


def error_info(root):
    if not root.has_error:
        return None
    errors = missing = 0
    first = None
    stack = [root]
    while stack:
        node = stack.pop()
        if node.type == "ERROR" or node.is_missing:
            if node.is_missing:
                missing += 1
            else:
                errors += 1
            position = [node.start_point[0] + 1, node.start_point[1]]
            if first is None or position < first:
                first = position
            if node.type == "ERROR":
                continue
        stack.extend(node.children)
    return {"errors": errors, "missing": missing, "first": first}


def parse_one(data: bytes) -> dict:
    started = time.perf_counter()
    tree = PARSER.parse(data)
    elapsed = time.perf_counter() - started
    root = tree.root_node
    return {"ok": not root.has_error, "t": elapsed, "defs": definitions(root),
            "imps": imports(root), "err": error_info(root)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", type=Path)
    ap.add_argument("--features", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    with args.out.open("w", encoding="utf-8") as sink:
        sink.write(json.dumps({"meta": True, "engine": "tree-sitter-python",
                               "python": sys.version.split()[0],
                               "abi": LANGUAGE.abi_version}) + "\n")
        if args.features:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from features import FEATURES
            for case in FEATURES:
                record = parse_one(case["source"].encode(case.get("enc", "utf-8")))
                record["f"] = case["id"]
                sink.write(json.dumps(record) + "\n")
            return 0
        for line in args.list.read_text(encoding="utf-8").splitlines():
            path = line.strip()
            if not path:
                continue
            try:
                data = Path(path).read_bytes()
            except OSError as error:
                record = {"ok": False, "t": 0.0, "defs": [], "imps": [],
                          "err": {"io": str(error)[:160]}}
            else:
                record = parse_one(data)
                record["h"] = hashlib.sha256(data).hexdigest()[:16]
            record["f"] = path
            sink.write(json.dumps(record) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
