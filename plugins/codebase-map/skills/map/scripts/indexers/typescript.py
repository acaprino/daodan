"""scip-typescript, for JavaScript and TypeScript: the aliases its index states its own way.

`hops` reads the statement that defines a name: `a = b`, `k: b.c`, `exports.f = g` and `{ k: name } = …` lead
to the symbol the index references at the value or the key (CommonJS `module.exports = { f }` needs none: the
index states it as a shared range); a function value leads to the function the snapshot declares there. A
library function whose documented contract returns its argument is a declared hop, tagged
`declared:<package>.<function>`.
"""
from __future__ import annotations

import collections
from pathlib import Path

import code_graph

GRAMMARS = {".ts": "typescript", ".mts": "typescript", ".cts": "typescript", ".tsx": "tsx", ".js": "javascript",
            ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript"}
PATTERNS = {"object_pattern", "array_pattern", "pair_pattern", "shorthand_property_identifier_pattern",
            "assignment_pattern", "object_assignment_pattern", "rest_pattern"}
PARAMETERS = {"formal_parameters", "required_parameter", "optional_parameter", "catch_clause"}
WRAPPERS = {"parenthesized_expression", "as_expression", "satisfies_expression", "non_null_expression",
            "type_assertion"}
FUNCTIONS = {"arrow_function", "function_expression", "function", "generator_function", "class"}
# Library functions whose documented contract returns their argument (`argument`) or what their argument, a
# function without a block body, returns (`result`); matched by the package and descriptors of the index.
DECLARED = {("@types/react", "/React/useCallback()."): "argument",
            ("@types/react", "/React/useMemo()."): "result"}


def _unwrap(node):
    while node is not None and node.type in WRAPPERS:
        node = node.named_children[0] if node.named_children else None
    return node


def _defining_value(node) -> tuple[str, object]:
    """(form, node) of the statement that defines the name at `node`: `pattern-key` with the key, `value` or
    `field` with the value, `parameter`, `destructured` (another element of a pattern) or `none`."""
    child, parent = node, node.parent
    if parent is not None and parent.type == "assignment_pattern" and parent.child_by_field_name("left") == node:
        child, parent = parent, parent.parent
    if parent is not None and parent.type == "pair_pattern" and parent.child_by_field_name("value") == child:
        return "pattern-key", parent.child_by_field_name("key")
    child, parent, destructured = node, node.parent, False
    while parent is not None and parent.type in PATTERNS:
        child, parent, destructured = parent, parent.parent, True
    if parent is None:
        return "none", None
    kind, field = parent.type, parent.child_by_field_name
    if kind in PARAMETERS or (kind == "arrow_function" and field("parameter") == child):
        return "parameter", None
    if kind == "variable_declarator" and field("name") == child:
        return ("destructured" if destructured else "value"), field("value")
    if kind == "pair" and field("key") == child:
        return "value", field("value")
    if kind in ("public_field_definition", "field_definition"):
        return "field", field("value")
    if kind == "member_expression" and field("property") == child and parent.parent is not None \
            and parent.parent.type == "assignment_expression" and parent.parent.child_by_field_name("left") == parent:
        return "value", parent.parent.child_by_field_name("right")
    return "none", None


def _value(index, rel: str, value, tag: str, function_tag: str = "value") -> list:
    """Where a value leads: a function's start, or the symbols the index references at a name."""
    value = _unwrap(value)
    if value is None:
        return []
    if value.type in FUNCTIONS:
        return [((rel, value.start_point[0] + 1, value.start_point[1]), function_tag)]
    if value.type in ("identifier", "member_expression"):
        name = value if value.type == "identifier" else value.child_by_field_name("property")
        return [(key, tag) for key in index.stated(rel, name)] if name is not None else []
    if value.type == "call_expression":
        return _declared(index, rel, value)
    return []


def _declared(index, rel: str, call) -> list:
    callee = _unwrap(call.child_by_field_name("function"))
    if callee is None:
        return []
    name = callee if callee.type == "identifier" else callee.child_by_field_name("property") \
        if callee.type == "member_expression" else None
    arguments = call.child_by_field_name("arguments")
    first = arguments.named_children[0] if arguments is not None and arguments.named_children else None
    if name is None or first is None:
        return []
    for key in index.stated(rel, name):
        parts = code_graph.split_symbol(key)
        for (package, suffix), contract in DECLARED.items():
            if not parts or parts[2] != package or not parts[4].endswith(suffix):
                continue
            tag = f"declared:{package}.{suffix.rsplit('/', 1)[-1][:-3]}"
            if contract == "argument":
                return _value(index, rel, first, tag, tag)
            first = _unwrap(first)
            body = first.child_by_field_name("body") if first is not None and first.type == "arrow_function" else None
            return _value(index, rel, body, tag, tag) if body is not None and body.type != "statement_block" else []
    return []


def hops(index) -> dict:
    """Alias edges from the statements that define the names of JS/TS documents."""
    out = collections.defaultdict(list)
    for rel, occurrences in index.documents.items():
        grammar = GRAMMARS.get(Path(rel).suffix.lower())
        if grammar is None:
            continue
        for occurrence in occurrences:
            # Types, methods, modules and parameters are declarations, never aliases.
            if not occurrence.definition or occurrence.key.endswith(("#", ").", "/", ")")):
                continue
            node = index.node(rel, occurrence, grammar)
            if node is None:
                continue
            form, value = _defining_value(node)
            if form == "pattern-key" and value is not None:
                found = [(key, "pattern-key") for key in index.stated(rel, value)]
            elif form in ("value", "field") and value is not None:
                found = _value(index, rel, value, "initializer")
            else:
                found = []
            out[occurrence.key] += [item for item in found if item[0] != occurrence.key]
    return {key: list(dict.fromkeys(items)) for key, items in out.items() if items}
