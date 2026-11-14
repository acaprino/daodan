"""scip-go: the aliases its index states its own way.

Interface implementations need no hop: scip-go states them in `SymbolInformation` (`is_implementation`), which
the shared traversal follows for members. `hops` reads the statement that defines a name: `x := y.z`,
`var x = y` lead to the symbol the index references at the value, position by position; a function literal
leads to the function the snapshot declares there.
"""
from __future__ import annotations

import collections

PARAMETERS = {"parameter_declaration", "variadic_parameter_declaration"}


def _positional(names: list, node, values) -> tuple[str, object]:
    """Go binds by position: the value at the name's index, or the one call that returns them all."""
    items = values.named_children if values is not None else []
    at = next((i for i, name in enumerate(names) if name == node), None)
    if at is not None and len(items) == len(names):
        return "value", items[at]
    return ("destructured", items[0]) if len(items) == 1 else ("none", None)


def _defining_value(node) -> tuple[str, object]:
    parent = node.parent
    if parent is None:
        return "none", None
    if parent.type == "expression_list" and parent.parent is not None \
            and parent.parent.type == "short_var_declaration" and parent.parent.child_by_field_name("left") == parent:
        return _positional(parent.named_children, node, parent.parent.child_by_field_name("right"))
    if parent.type in ("var_spec", "const_spec"):
        return _positional(parent.children_by_field_name("name"), node, parent.child_by_field_name("value"))
    if parent.type in PARAMETERS:
        return "parameter", None
    return "none", None


def _value(index, rel: str, value) -> list:
    while value is not None and value.type == "parenthesized_expression":
        value = value.named_children[0] if value.named_children else None
    if value is None:
        return []
    if value.type == "func_literal":
        return [((rel, value.start_point[0] + 1, value.start_point[1]), "value")]
    name = value if value.type == "identifier" else value.child_by_field_name("field") \
        if value.type == "selector_expression" else None
    return [(key, "initializer") for key in index.stated(rel, name)] if name is not None else []


def hops(index) -> dict:
    """Alias edges from the statements that define the names of Go documents."""
    out = collections.defaultdict(list)
    for rel, occurrences in index.documents.items():
        if not rel.endswith(".go"):
            continue
        for occurrence in occurrences:
            if not occurrence.definition or occurrence.key.endswith(("#", ").", "/", ")")):
                continue
            node = index.node(rel, occurrence, "go")
            if node is None:
                continue
            form, value = _defining_value(node)
            if form == "value" and value is not None:
                out[occurrence.key] += [item for item in _value(index, rel, value) if item[0] != occurrence.key]
    return {key: list(dict.fromkeys(items)) for key, items in out.items() if items}


def missing(index, rels: list[str]) -> dict:
    """Why a Go file has no document: a build constraint the indexer's default build leaves out."""
    reasons = {}
    for rel in rels:
        try:
            head = (index.root / rel).read_text(encoding="utf-8", errors="replace").split("\n")[:20]
        except OSError:
            continue
        constraint = next((line.strip() for line in head if line.startswith("//go:build")), None)
        if constraint:
            reasons[rel] = f"build constraint `{constraint}`"
    return reasons
