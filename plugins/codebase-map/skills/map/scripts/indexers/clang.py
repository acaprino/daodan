"""scip-clang for C and C++: what its index leaves to the reader.

Symbols carry no file: a function declared in a header and defined in a source file is one symbol, defined at
its body; the declaration is a reference. Two `static` functions of one name in two files are one symbol too.
scip-clang writes what a macro expands to at the expansion: the call `SQUARE(n)` references the macro and the
function its body calls, at the same range, so macros need no hop.

`prepare(index, snapshot)` fills in place what the index leaves out, before anything reads it: each
occurrence once (a file compiled by several translation units comes as several documents, which the shared
reader appends), columns in UTF-8 bytes (no position encoding is written, and the shared reader would take
UTF-16) and each function and class definition's enclosing range, the body the snapshot declares, so edges
start at the function that holds them rather than at the file. It keeps the snapshot's declarations of the
indexed files on the index (`index.declarations`) for `hops`.

`hops` states two things the index leaves implicit: a function the index defines nowhere leads to its
prototype in the project (`declaration`); in C++, a variable declared `auto` with a lambda leads to that
lambda (`lambda`, the closure type is its own). A call through a function pointer, a struct field or a
parameter ends on that value: nothing is guessed. `same_range` keeps the shared rule from reading a variable
defined where a constructor or a macro is referenced as an alias: only a using-declaration aliases at a shared
range. `classify` names namespaces and the package of an external symbol. `refine` marks an edge `uncertain`
when its symbol has bodies at several places, each place a candidate.
"""
from __future__ import annotations

import collections
from pathlib import Path

import code_graph

VERSION = "v0.4.1"  # github.com/sourcegraph/scip-clang, released 2026-10-22, LLVM 21
URL = f"https://github.com/sourcegraph/scip-clang/releases/download/{VERSION}/scip-clang-x86_64-linux"
SHA256 = "a434d26a079fd80e1996ba79276cb1ef86b2b2ad28b13e24386285db32c59046"  # the release asset's digest
C_SOURCES = {".c"}
CPP_SOURCES = {".cc", ".cpp", ".cxx", ".c++"}
CALLABLES = ("function", "method", "class")


# ---------------------------------------------------------------------------------------------------------
# What the index leaves to the reader


def dedupe(index) -> int:
    """Keep each occurrence of a document once, and rebuild the lookups; returns how many it dropped."""
    dropped = 0
    for occurrences in index.documents.values():
        unique = list(dict.fromkeys(occurrences))
        dropped += len(occurrences) - len(unique)
        occurrences[:] = unique
    index.at.clear()
    index.defs.clear()
    for rel, occurrences in index.documents.items():
        for item in occurrences:
            index.at[(rel, item.line, item.start)].append(item)
            if item.definition:
                index.defs[item.key].append((rel, item))
    return dropped


def utf8_columns(index) -> int:
    """scip-clang's columns are UTF-8 bytes, whatever the document states: every document is read so."""
    for rel in index.documents:
        index.units[rel] = "utf-8"
    return len(index.documents)


def _declarations(index, snapshot) -> dict:
    """`{checkout rel: [(kind, (l0, c0, l1, c1), payload)]}`: the snapshot's callables in the indexed files."""
    from snapshot_store import _unpack
    out = collections.defaultdict(list)
    for rel, kind, l0, c0, l1, c1, blob in snapshot.connection.execute(
            "SELECT file, kind, l0, c0, l1, c1, payload FROM sem_declarations WHERE kind IN (?,?,?) "
            "ORDER BY file, l0, c0", CALLABLES):
        checkout = snapshot.checkout.get(rel)
        if checkout in index.documents:
            out[checkout].append((kind, (l0, c0, l1, c1), _unpack(blob) or {}))
    return dict(out)


def enclose(index) -> int:
    """Give each definition of a function or class the range of the body the snapshot declares at its name.
    Returns how many it set."""
    done = 0
    for rel, declared in getattr(index, "declarations", {}).items():
        spans = {}
        for _kind, (l0, c0, l1, c1), payload in declared:
            if payload.get("contract"):  # a prototype: no body
                continue
            body = (l0, index.from_bytes(rel, l0, c0), l1, index.from_bytes(rel, l1, c1))
            for name in [payload.get("name_span"), *payload.get("signature_spans", ())]:
                if name and None not in body:
                    spans[(name[0], index.from_bytes(rel, name[0], name[1]))] = body
        occurrences = index.documents[rel]
        for i, item in enumerate(occurrences):
            span = spans.get((item.line, item.start)) if item.definition and item.enclosing is None else None
            if span:
                occurrences[i] = item._replace(enclosing=span)
                done += 1
    if done:  # the lookups hold the occurrences themselves
        dedupe(index)
    return done


def prepare(index, snapshot) -> dict:
    """Fill in what the index leaves to the reader (see the module docstring); returns what each step did."""
    deduplicated = dedupe(index)
    documents = utf8_columns(index)
    index.declarations = _declarations(index, snapshot)
    index.languages = {snapshot.checkout[rel]: language for rel, language in snapshot.languages.items()
                       if rel in snapshot.checkout and language in ("c", "cpp")}
    return {"deduplicated": deduplicated, "utf8_documents": documents, "enclosed": enclose(index)}


# ---------------------------------------------------------------------------------------------------------
# Hops


def _language(index, rel: str) -> str:
    known = getattr(index, "languages", {}).get(rel)
    return known or ("c" if Path(rel).suffix.lower() in C_SOURCES else "cpp")


def _tree(index, rel: str):
    """The file's tree as the snapshot's reader parses it without an include context; None without a grammar."""
    key = (rel, "cfamily")
    if key not in index._trees:
        from languages import cfamily
        from languages._treesitter import get_parser
        language = _language(index, rel)
        loaded = get_parser(language)
        try:
            source = (index.root / rel).read_bytes()
        except OSError:
            source = None
        index._trees[key] = loaded[0].parse(cfamily.prepare(source, language)[0]) \
            if loaded and source is not None else None
    return index._trees[key]


def _references(index, rel: str, line: int, byte_column: int, definition: bool) -> list:
    native = index.from_bytes(rel, line, byte_column)
    return [item for item in index.at.get((rel, line, native), ()) if item.definition == definition]


def declaration_hops(index) -> dict:
    """A function the index defines nowhere leads to its prototype in the project, where the snapshot declares it."""
    out = collections.defaultdict(list)
    for rel, declared in getattr(index, "declarations", {}).items():
        for _kind, (l0, c0, _l1, _c1), payload in declared:
            name = payload.get("name_span")
            if not payload.get("contract") or not name:
                continue
            for item in _references(index, rel, name[0], name[1], False):
                if item.key not in index.defs and "#local " not in item.key:
                    out[item.key].append(((rel, l0, c0), "declaration"))
    return out


def lambda_hops(index) -> dict:
    """C++: a variable declared `auto` with a lambda leads to the lambda (its closure type is its own)."""
    out = collections.defaultdict(list)
    for rel in index.documents:
        if _language(index, rel) != "cpp":
            continue
        tree = _tree(index, rel)
        stack = [tree.root_node] if tree is not None else []
        while stack:
            node = stack.pop()
            stack.extend(node.children)
            holder = node.parent
            if node.type != "lambda_expression" or holder is None or holder.type != "init_declarator" \
                    or holder.child_by_field_name("value") != node:
                continue
            declaration = holder.parent
            kind = declaration.child_by_field_name("type") if declaration is not None else None
            name = holder.child_by_field_name("declarator")
            if kind is None or kind.type != "placeholder_type_specifier" or name is None or name.type != "identifier":
                continue
            for item in _references(index, rel, name.start_point[0] + 1, name.start_point[1], True):
                out[item.key].append(((rel, node.start_point[0] + 1, node.start_point[1]), "lambda"))
    return out


def hops(index) -> dict:
    """The adapter's hops over every C and C++ document of the index (after `prepare`)."""
    out = collections.defaultdict(list)
    for found in (declaration_hops(index), lambda_hops(index)):
        for key, items in found.items():
            out[key] += items
    return {key: list(dict.fromkeys(items)) for key, items in out.items()}


# ---------------------------------------------------------------------------------------------------------
# Rules


def _last_name(key: str) -> str | None:
    parts = code_graph.split_symbol(code_graph._global(key))
    items = code_graph.descriptors(parts[4]) if parts else []
    return items[-1][0] if items else None


def same_range(index) -> dict[tuple[str, str], bool]:
    """At a shared range only a using-declaration aliases: a global definition and a reference to a symbol of the
    same name (`using geo::twice;`). Never otherwise: scip-clang writes the constructor a declaration runs at the
    variable's name (`Circle circle(2.0);`) and everything a macro expands to at the macro's name, so a variable
    defined there would read as a call of the constructor or of the macro's contents."""
    out = {}
    for rel, occurrences in index.documents.items():
        for item in occurrences:
            if not item.definition:
                continue
            for other in index.at.get((rel, item.line, item.start), ()):
                if other.definition or other.key == item.key or (other.end_line, other.end) != (item.end_line, item.end):
                    continue
                out[(item.key, other.key)] = "#local " not in item.key and _last_name(item.key) == _last_name(other.key)
    return out


def classify(index):
    """`project` for a package the index defines symbols of, `namespace` for a namespace, the stated package of
    any other symbol (`(none)` for the package scip-clang writes `.`)."""
    own = set()
    for key in index.defs:
        parts = code_graph.split_symbol(code_graph._global(key))
        if parts is not None:
            own.add((parts[2], parts[3].rstrip("$")))

    def stated(key: str):
        parts = code_graph.split_symbol(code_graph._global(key))
        if parts is None:
            return None
        items = code_graph.descriptors(parts[4])
        if items and items[-1][1] == "namespace":
            return "namespace"
        package, version = parts[2], parts[3].rstrip("$")
        if (package, version) in own:
            return "project"
        return {"manager": parts[1], "package": package, "version": version} if package != "." else \
            {"manager": parts[1], "package": "(none)", "version": "-"}
    return stated


def refine(index, graph: dict) -> None:
    """An edge to a symbol with bodies at several places is `uncertain`: each place, `rel:line`, a candidate."""
    places = {}
    for edge in graph["edges"]:
        if edge["end"] != "project-callable" or edge["chain"]:
            continue
        key = edge["to"]
        if key not in places:
            places[key] = sorted({f"{rel}:{occurrence.line}" for rel, occurrence in index.defs.get(key, ())})
        if len(places[key]) > 1:
            edge["uncertain"] = {"reason": "one symbol defined at several places", "candidates": places[key]}


def missing(index, rels: list[str], compiled: dict = (), removed: list = ()) -> dict:
    """Why a C or C++ file of the snapshot has no document."""
    reasons = {}
    for rel in rels:
        if rel in removed:
            reasons[rel] = "removed from the copy by the build's configure step"
        elif rel in compiled:
            reasons[rel] = "compiled, yet no document in the index"
        elif Path(rel).suffix.lower() in C_SOURCES | CPP_SOURCES:
            reasons[rel] = "no compile command: not built by the default configuration"
        else:
            reasons[rel] = "header no indexed translation unit includes in an active branch"
    return reasons
