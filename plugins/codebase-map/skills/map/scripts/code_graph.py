"""A whole-project SCIP index read completely as one code graph: the part that knows no language.

What is specific to an indexer lives in its adapter, `indexers/<language>.py`:

    hops(index) -> {symbol key: [(target, tag), ...]}

A hop's target is another symbol key, or `(rel, line, byte column)` where a function the snapshot declares
starts; its tag names the engine quirk it reads. A hop tagged `rebinding`, to `(rel, line, byte column)`, takes
the place of the symbol's definition: the adapter states that the symbol is bound there at run time, not where
the index defines it. An adapter may add, each passed by its driver to `Traversal` or `build`:

    missing(index, rels) -> {rel: reason}       snapshot files the index holds no document for
    same_range(index) -> {(definition key, other key): bool}   at a shared range: True alias, False never
    classify(key) -> "project" | "namespace" | {"manager", "package", "version"} | None (the default rule)
    static(index) -> {(rel, line, byte column)}  member references dispatched statically
    refine(index, graph) -> None                 holes added, edges marked `uncertain` or `removed`

An indexer run gives `{"indexes": [[path, prefix], ...], "indexer": {...}, "runs": [...]}`: `prefix` is the
checkout-relative directory a run names its documents from, `indexer` is `{"name", "version", "seconds",
"peak_mb"}`; `measured`, `module_runs` and `indexer` build it.

Everything else is here: every document, occurrence and SymbolInformation decoded (`Index`); the Daodan
snapshot a graph is measured against (`Snapshot`); from each referenced symbol every chain the index states,
followed with cycle protection and no step limit (`Traversal`); the graph every language emits (`build`) and
its counts (`report`); the edge store it is saved in (`write_store`). A chain follows only a definition
sharing its range with a reference to a symbol not also defined there (two definitions at one range are
facets of one declaration, never aliases), an adapter hop, and the implementations a member's
SymbolInformation states (`is_implementation`). It ends on a function, method or class the snapshot declares
(a constructor names its class), an external symbol, a namespace the adapter names, a project value with no
stated alias, or a dead end: a `local` or project symbol the index defines nowhere, a cycle.
"""
from __future__ import annotations

import collections
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

UNITS = {1: "utf-8", 2: "utf-16", 3: "utf-32"}
# SymbolInformation.Kind numbers, grouped into the kinds a graph reports.
KINDS = {
    "function": {17},
    "method": {9, 18, 26, 27, 45, 66, 67, 68, 69, 70, 71, 72, 73, 74, 76, 80},
    "class": {7, 11, 33, 49, 59, 75, 84, 85},
    "type": {3, 10, 21, 42, 53, 54, 55, 56, 57, 86},
    "variable": {8, 60, 61, 77, 82},
    "parameter": {37, 38, 44, 52, 58},
    "property": {12, 13, 15, 22, 41, 78, 79, 81},
    "module": {16, 29, 30, 35, 36, 64},
    "macro": {25},
}
KIND_OF = {number: name for name, numbers in KINDS.items() for number in numbers}
SUFFIXES = {"/": "namespace", "#": "type", ".": "term", ":": "meta", "!": "macro"}
CALLABLE = ("project-callable",)


# Protocol Buffers, the few wire types SCIP uses.

def _varint(data: bytes, at: int) -> tuple[int, int]:
    value = shift = 0
    while True:
        byte = data[at]
        at += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, at
        shift += 7


def _fields(data: bytes):
    at, size = 0, len(data)
    while at < size:
        tag, at = _varint(data, at)
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value, at = _varint(data, at)
        elif wire == 2:
            length, at = _varint(data, at)
            value, at = data[at:at + length], at + length
        elif wire in (1, 5):
            width = 8 if wire == 1 else 4
            value, at = data[at:at + width], at + width
        else:
            raise ValueError(f"unsupported wire type {wire}")
        yield number, wire, value


def _ints(value, wire: int) -> list[int]:
    if wire == 0:
        return [value]
    out, at = [], 0
    while at < len(value):
        item, at = _varint(value, at)
        out.append(item)
    return out


def _range(values: list[int]) -> tuple | None:
    """`(line, start, end line, end)`, lines 1-based, from SCIP's three or four 0-based numbers."""
    if len(values) == 3:
        return values[0] + 1, values[1], values[0] + 1, values[2]
    if len(values) == 4:
        return values[0] + 1, values[1], values[2] + 1, values[3]
    return None


def _typed(value: bytes, multi: bool) -> tuple | None:
    fields = {number: item for number, wire, item in _fields(value) if wire == 0}
    if multi:
        return _range([fields.get(1, 0), fields.get(2, 0), fields.get(3, 0), fields.get(4, 0)])
    return _range([fields.get(1, 0), fields.get(2, 0), fields.get(3, 0)])


# Symbols.

def split_symbol(symbol: str) -> tuple | None:
    """`(scheme, manager, package, version, descriptors)` of a global symbol, None for a `local`."""
    if symbol.startswith("local "):
        return None
    parts, current, at = [], [], 0
    while at < len(symbol) and len(parts) < 4:
        char = symbol[at]
        if char == " " and symbol[at + 1:at + 2] == " ":
            current.append(" ")
            at += 2
        elif char == " ":
            parts.append("".join(current))
            current = []
            at += 1
        else:
            current.append(char)
            at += 1
    return (*parts, symbol[at:]) if len(parts) == 4 else None


def _name(text: str, at: int) -> tuple[str, int]:
    if text[at:at + 1] == "`":
        out, at = [], at + 1
        while at < len(text):
            if text[at] == "`" and text[at + 1:at + 2] == "`":
                out.append("`")
                at += 2
            elif text[at] == "`":
                return "".join(out), at + 1
            else:
                out.append(text[at])
                at += 1
        return "".join(out), at
    end = at
    while end < len(text) and (text[end].isalnum() or text[end] in "_+-$"):
        end += 1
    return text[at:end], end


def descriptors(text: str) -> list[tuple[str, str]]:
    """`(name, suffix)` of each descriptor: namespace, type, term, meta, macro, method, parameter, type-parameter."""
    out, at = [], 0
    while at < len(text):
        if text[at] in "([":
            kind = "parameter" if text[at] == "(" else "type-parameter"
            name, at = _name(text, at + 1)
            out.append((name, kind))
            at += 1  # the closing bracket
            continue
        name, at = _name(text, at)
        if at >= len(text):
            out.append((name, "?"))
            break
        if text[at] == "(":
            close = text.find(")", at)
            at = len(text) if close < 0 else close + 2
            out.append((name, "method"))
        else:
            out.append((name, SUFFIXES.get(text[at], "?")))
            at += 1
    return out


def _global(key: str) -> str:
    """The symbol of a key, without the document a `local` is prefixed with."""
    return key.split("#", 1)[1] if "#local " in key else key


def package(symbol: str) -> dict | None:
    parts = split_symbol(_global(symbol))
    return {"manager": parts[1], "package": parts[2], "version": parts[3]} if parts else None


def package_name(symbol: str | dict) -> str:
    """`manager package@version` of a symbol, or of a package an adapter states."""
    stated = symbol if isinstance(symbol, dict) else package(symbol)
    return f"{stated['manager']} {stated['package']}@{stated['version']}" if stated else "local"


def node_kind(key: str, info: dict | None) -> str:
    """The index's own kind of a symbol: its SymbolInformation kind, else its last descriptor's suffix."""
    kind = KIND_OF.get((info or {}).get("kind", 0))
    if kind:
        return kind
    parts = split_symbol(_global(key))
    if parts is None:
        return "variable"
    items = descriptors(parts[4])
    if not items:
        return "module"
    last = items[-1][1]
    parent = items[-2][1] if len(items) > 1 else "namespace"
    if last == "method":
        return "method" if parent == "type" else "function"
    if last == "term":
        return "property" if parent == "type" else "variable"
    return {"namespace": "module", "type": "class", "parameter": "parameter", "type-parameter": "parameter",
            "macro": "macro"}.get(last, "other")


class Occurrence(NamedTuple):
    line: int  # 1-based
    start: int  # columns in the document's position unit
    end_line: int
    end: int
    key: str  # the symbol, a `local` prefixed with its document
    definition: bool
    enclosing: tuple | None  # a definition's enclosing range, when the indexer writes one


class Index:
    """Every document, occurrence and SymbolInformation of one or more SCIP files, by checkout-relative path."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.tools: list[tuple[str, str]] = []
        self.documents: dict[str, list[Occurrence]] = {}
        self.units: dict[str, str] = {}
        self.at: dict[tuple, list[Occurrence]] = collections.defaultdict(list)
        self.defs: dict[str, list[tuple[str, Occurrence]]] = collections.defaultdict(list)
        self.info: dict[str, dict] = {}
        self.implementers: dict[str, set] = collections.defaultdict(set)
        self.repeated = collections.Counter()
        self.unknown = collections.Counter()
        self._lines: dict[str, list[str]] = {}
        self._trees: dict = {}

    @staticmethod
    def key(symbol: str, rel: str | None) -> str:
        return f"{rel}#{symbol}" if rel is not None and symbol.startswith("local ") else symbol

    def load(self, path: Path, prefix: str = "") -> None:
        for number, wire, value in _fields(Path(path).read_bytes()):
            if number == 1 and wire == 2:
                tool = ["", ""]
                for field, kind, item in _fields(value):
                    if field == 2 and kind == 2:
                        for part, part_kind, text in _fields(item):
                            if part in (1, 2) and part_kind == 2:
                                tool[part - 1] = text.decode("utf-8", errors="replace")
                self.tools.append((tool[0], tool[1]))
            elif number == 2 and wire == 2:
                self._document(value, prefix)
            elif number == 3 and wire == 2:
                self._information(value, None)
            else:
                self.unknown[f"index field {number}"] += 1

    def _document(self, data: bytes, prefix: str) -> None:
        rel, unit, raw, informations = "", 0, [], []
        for number, wire, value in _fields(data):
            if number == 1 and wire == 2:
                rel = value.decode("utf-8", errors="replace").replace("\\", "/")
            elif number == 6 and wire == 0:
                unit = int(value)
            elif number == 2 and wire == 2:
                raw.append(value)
            elif number == 3 and wire == 2:
                informations.append(value)
            elif number not in (4, 5):
                self.unknown[f"document field {number}"] += 1
        if not rel:
            return
        # A run in a module directory may name its documents from that directory or from the checkout.
        if prefix and not (self.root / rel).is_file():
            rel = f"{prefix}/{rel}"
        self.repeated[rel] += 1
        self.units[rel] = UNITS.get(unit, "utf-16")
        occurrences = self.documents.setdefault(rel, [])
        for item in raw:
            occurrence = self._occurrence(item, rel)
            if occurrence is None:
                continue
            occurrences.append(occurrence)
            self.at[(rel, occurrence.line, occurrence.start)].append(occurrence)
            if occurrence.definition:
                self.defs[occurrence.key].append((rel, occurrence))
        for item in informations:
            self._information(item, rel)

    def _occurrence(self, data: bytes, rel: str) -> Occurrence | None:
        place = enclosing = None
        symbol, roles = "", 0
        for number, wire, value in _fields(data):
            if number == 1:
                place = place or _range(_ints(value, wire))
            elif number == 2 and wire == 2:
                symbol = value.decode("utf-8", errors="replace")
            elif number == 3 and wire == 0:
                roles = int(value)
            elif number in (8, 9) and wire == 2:
                place = _typed(value, number == 9)  # the typed range wins over the deprecated one
            elif number == 7:
                enclosing = enclosing or _range(_ints(value, wire))
            elif number in (10, 11) and wire == 2:
                enclosing = _typed(value, number == 11)
            elif number not in (4, 5, 6):
                self.unknown[f"occurrence field {number}"] += 1
        if place is None or not symbol:
            return None
        return Occurrence(*place, self.key(symbol, rel), bool(roles & 1), enclosing)

    def _information(self, data: bytes, rel: str | None) -> None:
        entry = {"kind": 0, "display": "", "enclosing": "", "documentation": "", "signature": ""}
        symbol = ""
        for number, wire, value in _fields(data):
            if number == 1 and wire == 2:
                symbol = value.decode("utf-8", errors="replace")
            elif number == 5 and wire == 0:
                entry["kind"] = int(value)
            elif number == 6 and wire == 2:
                entry["display"] = value.decode("utf-8", errors="replace")
            elif number == 8 and wire == 2:
                entry["enclosing"] = value.decode("utf-8", errors="replace")
            elif number == 3 and wire == 2 and not entry["documentation"]:
                entry["documentation"] = value.decode("utf-8", errors="replace")[:200]
            elif number == 7 and wire == 2:  # signature_documentation, a Document whose text is the signature
                entry["signature"] = next((text.decode("utf-8", errors="replace") for field, kind, text in
                                           _fields(value) if field == 5 and kind == 2), "")
            elif number == 4 and wire == 2:
                target, implementation = "", False
                for field, kind, item in _fields(value):
                    if field == 1 and kind == 2:
                        target = item.decode("utf-8", errors="replace")
                    elif field == 3 and kind == 0:
                        implementation = bool(item)
                if implementation and target:
                    entry.setdefault("implements", []).append(self.key(target, rel))
        if not symbol:
            return
        key = self.key(symbol, rel)
        self.info[key] = entry
        for target in entry.get("implements", ()):
            self.implementers[target].add(key)

    # Source text, for position units and syntax.

    def line(self, rel: str, line: int) -> str | None:
        if rel not in self._lines:
            try:
                self._lines[rel] = (self.root / rel).read_text(encoding="utf-8").split("\n")
            except (OSError, UnicodeError):
                self._lines[rel] = []
        lines = self._lines[rel]
        return lines[line - 1] if 1 <= line <= len(lines) else None

    def to_bytes(self, rel: str, line: int, column: int) -> int | None:
        text, unit = self.line(rel, line), self.units.get(rel, "utf-16")
        if text is None:
            return None
        if unit == "utf-8" or text.isascii():
            return column
        if unit == "utf-32":
            return len(text[:column].encode("utf-8"))
        units = 0
        for at, char in enumerate(text):
            if units >= column:
                return len(text[:at].encode("utf-8"))
            units += 2 if ord(char) > 0xFFFF else 1
        return len(text.encode("utf-8"))

    def from_bytes(self, rel: str, line: int, column: int) -> int | None:
        text, unit = self.line(rel, line), self.units.get(rel, "utf-16")
        if text is None:
            return None
        if unit == "utf-8" or text.isascii():
            return column
        head = text.encode("utf-8")[:column].decode("utf-8", errors="ignore")
        return len(head) if unit == "utf-32" else len(head.encode("utf-16-le")) // 2

    def tree(self, rel: str, grammar: str):
        """The tree-sitter tree of a document, with the snapshot's grammars; None without one."""
        if (rel, grammar) not in self._trees:
            from languages._treesitter import get_parser
            loaded = get_parser(grammar)
            try:
                source = (self.root / rel).read_bytes()
            except OSError:
                source = None
            self._trees[(rel, grammar)] = loaded[0].parse(source) if loaded and source is not None else None
        return self._trees[(rel, grammar)]

    def node(self, rel: str, occurrence: Occurrence, grammar: str):
        """The smallest syntax node spanning an occurrence's range."""
        tree = self.tree(rel, grammar)
        begin = self.to_bytes(rel, occurrence.line, occurrence.start)
        if tree is None or begin is None:
            return None
        stop = self.to_bytes(rel, occurrence.line, occurrence.end) if occurrence.end_line == occurrence.line else None
        row = occurrence.line - 1
        return tree.root_node.descendant_for_point_range((row, begin), (row, stop if stop and stop > begin else begin + 1))

    def stated(self, rel: str, node) -> list[str]:
        """The symbols the index references where a syntax node starts."""
        row = node.start_point[0] + 1
        native = self.from_bytes(rel, row, node.start_point[1])
        return sorted({item.key for item in self.at.get((rel, row, native), ()) if not item.definition})


class Snapshot:
    """The Daodan snapshot a graph is measured against: files, languages, references, declarations."""

    def __init__(self, manifest: Path):
        self.manifest = Path(manifest)

    def __enter__(self):
        import resolve_edges as rx
        from snapshot_store import _unpack, open_snapshot
        self._rx, self._unpack = rx, _unpack
        self._context = open_snapshot(self.manifest)
        self.store = store = self._context.__enter__()
        self.connection = store.connection
        root = (Path(store["root"]) / store["target"]).resolve()
        self.root = root.parent if root.is_file() else root
        self.store_root, self.paths, _ = rx.verify_sources(store)
        self.inventory = rx.inventory_files(self.connection)
        self.languages = dict(self.connection.execute("SELECT file, language FROM sem_coverage"))
        # The snapshot's file key of a checkout-relative path, which the index uses.
        self.rel, self.checkout = {}, {}
        for rel, path in self.paths.items():
            try:
                checkout = path.resolve().relative_to(self.root).as_posix()
            except ValueError:
                continue
            self.rel[checkout], self.checkout[rel] = rel, checkout
        self._lines: dict = {}
        self.functions = collections.defaultdict(dict)
        declarations = self.connection.execute(
            "SELECT id, file, name, kind, l0, c0, payload FROM sem_declarations "
            "WHERE kind IN ('function','method','class')").fetchall()
        for identity, rel, _name, _kind, line, column, _blob in declarations:
            self.functions[rel][(line, column)] = identity
        # A constructor names its class (requirement 14 of the engine specification): a function a class
        # declares under the class's own name. JavaScript's `constructor` is marked by the snapshot itself.
        classes = {identity: name for identity, _rel, name, kind, *_rest in declarations if kind == "class"}
        self.constructs = {}
        for identity, rel, name, kind, _line, _column, blob in declarations:
            owner = f"{rel}::{str((_unpack(blob) or {}).get('scope') or '').removeprefix('scope-')}"
            if kind != "class" and classes.get(owner) == name:
                self.constructs[identity] = owner
        self._tables: dict = {}
        return self

    def __exit__(self, *error):
        return self._context.__exit__(*error)

    def references(self, language: str):
        """`(id, file, kind, resolution, lexical target, span, name parts, reason)` of its calls and reads."""
        for identity, rel, kind, resolution, target, l0, c0, l1, c1, blob in self.connection.execute(
                "SELECT r.id, r.file, r.kind, r.resolution, r.target_id, r.l0, r.c0, r.l1, r.c1, r.payload "
                "FROM sem_references r JOIN sem_coverage c ON c.file = r.file "
                "WHERE r.kind IN ('call','read') AND c.language = ? ORDER BY r.file, r.l0, r.c0, r.id", (language,)):
            payload = self._unpack(blob) or {}
            yield identity, rel, kind, resolution, target, (l0, c0, l1, c1), payload.get("parts") or [], \
                payload.get("reason") or "-"

    def callee(self, rel: str, span: tuple, parts: list) -> tuple[int, int] | None:
        """`(line, byte column)` of a reference's last name, as the engine pass asks for it."""
        l0, _c0, l1, _c1 = span
        if rel not in self._lines:
            try:
                self._lines[rel] = self.paths[rel].read_text(encoding="utf-8").split("\n")
            except (KeyError, OSError, UnicodeError):
                self._lines[rel] = None
        text = self._lines[rel]
        if not parts or text is None or not 1 <= l0 <= l1 <= len(text):
            return None
        column = self._rx.callee_column(text[l1 - 1], list(span), parts[-1])
        return None if column is None else (l1, column)

    def grade(self, rel: str, line: int, column: int | None) -> tuple[str, str | None]:
        """`callable` with the declaration the snapshot names there, `outside` the snapshot, or `value`."""
        if column is None or rel not in self.paths:
            return "outside", None
        if rel not in self.inventory:  # a project file the snapshot reads lexically: no declaration to name
            return "value", "file without declarations in the snapshot"
        location = self._rx.Location(self.paths[rel], line, column)
        verdict, target = self._rx.grade(location, self.inventory, self._tables, self.store_root, self._table)
        if verdict.startswith("edge-") and target:
            return "callable", self.constructs.get(target["id"], target["id"])
        return ("outside", None) if verdict == "external-definition" else ("value", verdict)

    def _table(self, rel: str):
        return self._rx.symbol_table(self.connection, rel, self.paths[rel].read_text(encoding="utf-8"))

    def function_at(self, rel: str, line: int, column: int) -> str | None:
        return self.functions.get(rel, {}).get((line, column))


class End(NamedTuple):
    cls: str  # project-callable, project-value, external, namespace, dead-end
    key: str  # the symbol the chain ends at
    target: str | None  # the snapshot's declaration, for a project-callable end
    detail: str  # a value's kind, an external's package, a dead end's reason
    chain: tuple = ()  # hop kinds, in order


class Traversal:
    """Every end the index states for a symbol, memoized; a symbol met again on its own chain is a cycle.

    `same_range` and `classify` are the adapter's (see the module docstring): a pair it names overrides the
    same-range rule; a key it classifies `namespace` or external ends there, `project` is a project symbol
    whatever its package, None keeps the default (a project symbol is of a package the index defines).
    """

    def __init__(self, index: Index, snapshot: Snapshot, hops: dict, same_range: dict | None = None,
                 classify=None):
        self.index, self.snapshot, self.hops = index, snapshot, hops
        self.same_range, self.classify = same_range or {}, classify
        self.own = {tuple(parts[1:4]) for parts in map(split_symbol, map(_global, index.defs)) if parts}
        self.memo: dict[str, list[End]] = {}
        self.active: set = set()
        self._stated: dict = {}

    def stated(self, key: str):
        """The adapter's classification of a key, None without one."""
        if key not in self._stated:
            self._stated[key] = self.classify(key) if self.classify else None
        return self._stated[key]

    def package(self, key: str) -> dict | None:
        stated = self.stated(key)
        return stated if isinstance(stated, dict) else package(key)

    def ends(self, key: str) -> list[End]:
        if key in self.memo:
            return self.memo[key]
        if key in self.active:
            return [End("dead-end", key, None, "cycle")]
        self.active.add(key)
        index, found, aliased, stated = self.index, [], False, self.stated(key)
        places = index.defs.get(key, ()) if stated in (None, "project") else ()
        rebound = [target for target, tag in self.hops.get(key, ()) if tag == "rebinding"]
        if rebound:  # where the symbol is bound at run time, in place of where the index defines it
            places, aliased = (), True
        for rel, line, column in rebound:
            verdict, target = self.snapshot.grade(self.snapshot.rel.get(rel, rel), line, column)
            found.append(End("project-callable", key, target, "", ("rebinding",)) if verdict == "callable" else
                         End("project-value", key, None, "function the snapshot does not declare", ("rebinding",)))
        for rel, occurrence in places:
            verdict, target = self.snapshot.grade(
                self.snapshot.rel.get(rel, rel), occurrence.line, index.to_bytes(rel, occurrence.line, occurrence.start))
            if verdict == "callable":
                found.append(End("project-callable", key, target, ""))
                aliased = True
                continue
            if verdict == "outside":
                found.append(End("external", key, None, f"{package_name(key)} (outside the snapshot)"))
                aliased = True
                continue
            here = [item for item in index.at.get((rel, occurrence.line, occurrence.start), ())
                    if item.key != key and (item.end_line, item.end) == (occurrence.end_line, occurrence.end)]
            defined = {item.key for item in here if item.definition}
            same = sorted({item.key for item in here if self.same_range.get((key, item.key), item.key not in defined)})
            for other in same:
                found += [end._replace(chain=("same-range",) + end.chain) for end in self.ends(other)]
            aliased = aliased or bool(same)
        if not any(end.cls in CALLABLE and end.chain in ((), ("rebinding",)) for end in found):
            for target, tag in self.hops.get(key, ()):
                if tag == "rebinding":
                    continue
                aliased = True
                if isinstance(target, str):
                    found += [end._replace(chain=(tag,) + end.chain) for end in self.ends(target)]
                else:
                    rel, line, column = target
                    identity = self.snapshot.function_at(self.snapshot.rel.get(rel, rel), line, column)
                    found.append(End("project-callable", key, identity, "", (tag,)) if identity else
                                 End("project-value", key, None, "function the snapshot does not declare", (tag,)))
        if not places and not aliased:
            found.append(self._undefined(key, stated))
        elif not aliased:
            found.append(End("project-value", key, None, node_kind(key, index.info.get(key))))
        # A member's implementations are where a call through it can run; a type's subtypes (SCIP's type
        # suffix `#`) are never the target of a reference to the type itself.
        if not key.endswith("#"):
            for other in sorted(index.implementers.get(key, ())):
                found += [end._replace(chain=("implementation",) + end.chain) for end in self.ends(other)
                          if end.cls in CALLABLE]
        self.active.discard(key)
        self.memo[key] = found = list(dict.fromkeys(found))
        return found

    def _undefined(self, key: str, stated=None) -> End:
        if stated == "namespace":
            return End("namespace", key, None, "")
        if isinstance(stated, dict):
            return End("external", key, None, package_name(stated))
        parts = split_symbol(_global(key))
        if parts is None:
            return End("dead-end", key, None, "dangling-local")
        if stated == "project" or tuple(parts[1:4]) in self.own:
            return End("dead-end", key, None, "undefined-project-symbol")
        return End("external", key, None, package_name(key))


def _enclosing(occurrences: list[Occurrence]) -> dict[int, str]:
    """For each reference (by position in the list), the innermost definition whose enclosing range holds it."""
    # Outer before inner at the same start, so the innermost holder is the last one opened.
    spans = sorted((((o.enclosing[0], o.enclosing[1]), (o.enclosing[2], o.enclosing[3]), o.key)
                    for o in occurrences if o.definition and o.enclosing),
                   key=lambda span: (span[0], (-span[1][0], -span[1][1])))
    order = sorted((i for i, o in enumerate(occurrences) if not o.definition),
                   key=lambda i: (occurrences[i].line, occurrences[i].start))
    out, stack, cursor = {}, [], 0
    for i in order:
        here = (occurrences[i].line, occurrences[i].start)
        while cursor < len(spans) and spans[cursor][0] <= here:
            stack.append(spans[cursor])
            cursor += 1
        while stack and stack[-1][1] <= here:
            stack.pop()
        holders = [span for span in stack if span[0] <= here < span[1]]
        if holders:
            out[i] = holders[-1][2]
    return out


HOLES = ("no-position", "no-document", "no-occurrence", "dangling-local", "undefined-project-symbol", "cycle")


def build(index: Index, snapshot: Snapshot, language: str, hops: dict, indexer: dict,
          missing_reasons: dict | None = None, traversal: Traversal | None = None, static=None,
          refine=None) -> tuple[dict, dict]:
    """The graph of one language's documents, and the ends at each snapshot reference (for comparisons).

    Edges run from every non-definition occurrence's innermost enclosing definition (its document when none
    holds it) to each end of its symbol (`symbol`, the key referenced there), with the snapshot reference's
    kind at that position; at a `static` site `(rel, line, byte column)` to no end reached through an
    implementation. Holes are the snapshot references the index answers nothing at, or only with a dead end.
    `refine(index, graph)` runs last: an edge it gives `uncertain` (`{reason, candidates}`) stays, one it gives
    `removed` (a reason) moves to `graph["removed"]`, a hole or edge it adds carries `"by": "refine"`; it
    drops nothing otherwise.
    """
    traversal = traversal or Traversal(index, snapshot, hops)
    static = {(rel, line, index.from_bytes(rel, line, column)) for rel, line, column in static or ()}

    def ends(position: tuple | None, keys) -> list[End]:
        found = list(dict.fromkeys(end for key in dict.fromkeys(keys) for end in traversal.ends(key)))
        return [end for end in found if "implementation" not in end.chain] if position in static else found
    documents = {rel for rel in index.documents if snapshot.languages.get(snapshot.rel.get(rel, rel)) == language}
    references, holes, by_position = {}, [], collections.defaultdict(list)
    for identity, rel, kind, resolution, lexical, span, parts, reason in snapshot.references(language):
        checkout = snapshot.checkout.get(rel, rel)
        site = snapshot.callee(rel, span, parts)
        entries, position = [], None
        if site is not None:
            position = (checkout, site[0], index.from_bytes(checkout, site[0], site[1]))
            entries = index.at.get(position, [])
            by_position[position].append(kind)
        keys = [item.key for item in entries if not item.definition] or [item.key for item in entries]
        found = ends(position, keys)
        if site is None:
            cls = "no-position"
        elif not entries:
            cls = "no-occurrence" if checkout in index.documents else "no-document"
        elif all(end.cls == "dead-end" for end in found):
            cls = found[0].detail if found else "no-occurrence"
        else:
            cls = ""
        references[identity] = {"site": f"{rel}:{site[0] if site else span[2]}", "name": ".".join(parts),
                                "kind": kind, "reason": reason, "resolution": resolution, "lexical": lexical,
                                "ends": found, "hole": cls}
        if cls:
            holes.append({"site": references[identity]["site"], "name": ".".join(parts), "kind": kind, "class": cls,
                          "reason": reason})
    nodes, edges = {}, []
    for rel in sorted(documents):
        occurrences = index.documents[rel]
        holder = _enclosing(occurrences)
        for i, occurrence in enumerate(occurrences):
            if occurrence.definition:
                nodes.setdefault(occurrence.key, {"id": occurrence.key, "kind": node_kind(occurrence.key,
                                                  index.info.get(occurrence.key)),
                                                  "file": rel, "line": occurrence.line, "external": None})
                continue
            position = (rel, occurrence.line, occurrence.start)
            kinds = by_position.get(position, ())
            kind = kinds[0] if len(set(kinds)) == 1 else "unknown"
            source = holder.get(i, rel)
            for end in ends(position, [occurrence.key]):
                edges.append({"from": source, "to": end.key, "symbol": occurrence.key,
                              "site": f"{rel}:{occurrence.line}", "kind": kind, "chain": list(end.chain),
                              "end": end.cls, "target": end.target})
    for rel in documents:
        nodes.setdefault(rel, {"id": rel, "kind": "module", "file": rel, "line": 1, "external": None})
    for edge in edges:
        key = edge["to"]
        if key in nodes:
            continue
        places = index.defs.get(key)
        if places:
            rel, occurrence = places[0]
            nodes[key] = {"id": key, "kind": node_kind(key, index.info.get(key)), "file": rel, "line": occurrence.line,
                          "external": traversal.package(key) if edge["end"] == "external" else None}
        else:
            nodes[key] = {"id": key, "kind": node_kind(key, index.info.get(key)), "file": None, "line": None,
                          "external": traversal.package(key) if edge["end"] == "external" else None}
    inventory = sorted(snapshot.checkout[rel] for rel in snapshot.inventory
                       if snapshot.languages.get(rel) == language and rel in snapshot.checkout)
    missing = [{"path": rel, "reason": (missing_reasons or {}).get(rel) or "no document in the index"}
               for rel in inventory if rel not in index.documents]
    missing += [{"path": rel, "reason": "document without occurrences"} for rel in inventory
                if rel in index.documents and not index.documents[rel]]
    graph = {"language": language, "indexer": indexer,
             "files": {"snapshot": len(inventory), "indexed": sum(1 for rel in inventory if index.documents.get(rel)),
                       "missing": missing},
             "nodes": list(nodes.values()), "edges": edges, "holes": holes, "removed": []}
    if refine is not None:
        _refined(index, graph, refine)
    return graph, references


def _refined(index: Index, graph: dict, refine) -> None:
    """Run an adapter's refine step and tag what it changed (see `build`)."""
    before = {name: list(graph[name]) for name in ("edges", "holes")}
    refine(index, graph)
    for name, items in before.items():
        now = {id(item) for item in graph[name]}
        if any(id(item) not in now for item in items):
            raise ValueError(f"refine dropped {name}: give an edge `removed` (a reason) instead")
        seen = {id(item) for item in items}
        for item in graph[name]:
            if id(item) not in seen:
                item["by"] = "refine"
    graph["removed"] += [edge for edge in graph["edges"] if edge.get("removed")]
    graph["edges"] = [edge for edge in graph["edges"] if not edge.get("removed")]


def write_store(snapshot: Snapshot, out: Path, built: dict, resolver: str) -> Path:
    """Save `build`'s graphs, `{language: (graph, references)}`, as the snapshot's edge store, beside what it
    already holds for other languages (`resolve_edges.kept_languages`).

    A snapshot reference's ends are its rows, `uncertain` where `refine` marked the edge of that end at its
    site; an end `refine` removed is counted in `edges_removed` and not saved. A reference the index answers
    nothing at, or only with removed ends, is a hole, like an implicit call an adapter adds. An occurrence the
    snapshot lists no reference for is a row of kind `unknown`, which no consumer reads. `symbol` is the key
    the end is at; an external end's package goes to `externals`.
    """
    import resolve_edges as rx
    known = {identity: (caller, l0, c0) for identity, caller, l0, c0 in snapshot.connection.execute(
        "SELECT id, caller, l0, c0 FROM sem_references")}
    edges, holes, entries = [], [], {}
    for language, (graph, references) in sorted(built.items()):
        packages = {node["id"]: node["external"] for node in graph["nodes"]}
        kept = {(edge["site"], edge["to"], tuple(edge["chain"])) for edge in graph["edges"]}
        doubts = {(edge["site"], edge["to"], tuple(edge["chain"])): edge["uncertain"]
                  for edge in graph["edges"] if edge.get("uncertain")}
        removed = {(edge["site"], edge["to"], tuple(edge["chain"])): edge["removed"] for edge in graph["removed"]}

        def row(place: dict, end_class: str, key: str, target, chain, detail: str, doubt=None, **payload) -> dict:
            external = (packages.get(key) or package(key)) if end_class == "external" else None
            return {**place, "language": language, "verdict": end_class, "target_id": target, "symbol": key,
                    "resolver": resolver, "confidence": "uncertain" if doubt else "confirmed",
                    "external": external, "payload": {**payload, "chain": list(chain), "detail": detail,
                                                      **({"uncertain": doubt} if doubt else {})}}

        for identity, reference in references.items():
            rel, line = reference["site"].rsplit(":", 1)
            site = f"{snapshot.checkout.get(rel, rel)}:{line}"
            caller, l0, c0 = known[identity]
            place = {"reference_id": identity, "file": rel, "kind": reference["kind"], "caller": caller,
                     "l0": l0, "c0": c0}
            ends = [end for end in reference["ends"] if (site, end.key, end.chain) in kept
                    or (site, end.key, end.chain) not in removed]
            hole = reference["hole"] or ("" if ends else "removed")
            if hole:
                reason = reference["reason"] if reference["hole"] else removed[(site, reference["ends"][0].key,
                                                                                reference["ends"][0].chain)]
                holes.append({**place, "language": language, "class": hole, "reason": reason, "resolver": resolver})
                continue
            edges += [row(place, end.cls, end.key, end.target, end.chain, end.detail,
                          doubts.get((site, end.key, end.chain))) for end in ends]
        for edge in graph["edges"]:
            if edge["kind"] == "unknown":
                rel, line = edge["site"].rsplit(":", 1)
                place = {"reference_id": None, "file": snapshot.rel.get(rel, rel), "kind": "unknown", "caller": None,
                         "l0": int(line), "c0": None}
                edges.append(row(place, edge["end"], edge["to"], edge.get("target"), edge["chain"], "",
                                 edge.get("uncertain"), **{"from": edge["from"]}))
        for hole in graph["holes"]:
            if hole.get("by") == "refine":
                rel, line = hole["site"].rsplit(":", 1)
                holes.append({"reference_id": None, "file": snapshot.rel.get(rel, rel), "language": language,
                              "kind": hole["kind"], "l0": int(line), "c0": None, "class": hole["class"],
                              "reason": hole["reason"], "resolver": resolver})
        entries[language] = {"engine": resolver, "state": "fresh", "indexer": graph["indexer"],
                             "files": graph["files"],
                             "edges_removed": dict(collections.Counter(edge["removed"] for edge in graph["removed"]))}
    kept_entries, kept_edges, kept_holes, kept_reports = rx.kept_languages(out, snapshot.store, built)
    binding = rx.store_binding(snapshot.store, snapshot.manifest, snapshot.store.metadata.get("parser_fingerprint"),
                               {**kept_entries, **entries}, kept_reports)
    return rx.write_edge_store(out, kept_edges + edges, binding, kept_holes + holes)


def _examples(items: list, size: int = 3) -> list:
    if len(items) <= size:
        return items
    step = len(items) / size
    return [items[int(i * step)] for i in range(size)]


def report(graph: dict) -> dict:
    """The counts a reader checks a graph by."""
    nodes = {node["id"]: node for node in graph["nodes"]}
    kinds = collections.Counter(("external" if node["external"] else "project" if node["file"] else "undefined",
                                 node["kind"]) for node in graph["nodes"])
    ends = collections.Counter((edge["end"], edge["kind"]) for edge in graph["edges"])
    callable_chains = collections.Counter(min(len(edge["chain"]), 3) for edge in graph["edges"]
                                          if edge["end"] == "project-callable")
    tags = collections.Counter(tag for edge in graph["edges"] for tag in edge["chain"])
    packages = collections.Counter()
    for edge in graph["edges"]:
        external = nodes[edge["to"]]["external"]
        if edge["end"] == "external" and external:
            packages[f"{external['manager']} {external['package']}@{external['version']}"] += 1
    holes = collections.defaultdict(list)
    for hole in graph["holes"]:
        holes[(hole["class"], hole["kind"], hole["reason"])].append(f"{hole['site']} {hole['name']}")
    by_class = collections.Counter()
    for (cls, kind, _reason), items in holes.items():
        by_class[(cls, kind)] += len(items)
    return {
        "language": graph["language"], "indexer": graph["indexer"],
        "files": {"snapshot": graph["files"]["snapshot"], "indexed": graph["files"]["indexed"],
                  "missing": graph["files"]["missing"][:60], "missing_count": len(graph["files"]["missing"])},
        "nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
        "symbols_by_kind": {f"{origin} {kind}": count for (origin, kind), count in sorted(kinds.items())},
        "edges_by_end": {f"{end} {kind}": count for (end, kind), count in sorted(ends.items())},
        "callable_chain_hops": {("3+" if hops == 3 else str(hops)): count for hops, count in sorted(callable_chains.items())},
        "hop_tags": dict(tags.most_common()),
        "edges_uncertain": dict(collections.Counter(edge["uncertain"]["reason"] for edge in graph["edges"]
                                                    if edge.get("uncertain")).most_common()),
        "edges_removed": dict(collections.Counter(edge["removed"] for edge in graph.get("removed", ())).most_common()),
        "holes_by_class": {f"{cls} {kind}": count for (cls, kind), count in sorted(by_class.items())},
        "holes": [{"class": cls, "kind": kind, "reason": reason, "count": len(items), "examples": _examples(items)}
                  for (cls, kind, reason), items in sorted(holes.items(), key=lambda pair: -len(pair[1]))][:40],
        "external_packages": dict(packages.most_common(20)),
    }


def measured(command: list[str], cwd: str, env: dict | None, timeout: int) -> dict:
    """An indexer run: return code, wall seconds, the peak memory of its largest process, the output's tail."""
    import re
    probe = ("import resource,subprocess,sys;r=subprocess.run(sys.argv[1:]);"
             "print('DAODAN_MAXRSS_KB=%d' % resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss, file=sys.stderr);"
             "sys.exit(r.returncode)")
    begun = time.time()
    wrapped = [sys.executable, "-c", probe, *command] if sys.platform != "win32" else command
    try:
        done = subprocess.run(wrapped, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)
        code, out, err = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as error:
        code, out, err = "timeout", str(error.stdout or "")[-2000:], str(error.stderr or "")[-2000:]
    peak = re.findall(r"DAODAN_MAXRSS_KB=(\d+)", err or "")
    errors = [line[line.find(" ERROR ") + 7:][:200] for line in (err or "").splitlines() if " ERROR " in line]
    return {"command": command, "returncode": code, "seconds": round(time.time() - begun, 1),
            "peak_mb": round(int(peak[-1]) / 1024) if peak else None,
            "stdout_tail": (out or "")[-1500:], "stderr_tail": (err or "")[-2500:],
            # An indexer's own errors, such as a definition it knows but leaves out of every document.
            "stderr_errors": len(errors), "stderr_error_examples": list(dict.fromkeys(errors))[:5]}


def manifest_dirs(mirror: Path, manifest: str) -> set[str]:
    """The checkout-relative directories holding a build manifest (`go.mod`, `Cargo.toml`), '' for the root."""
    roots = set()
    for path in Path(mirror).rglob(manifest):
        relative = path.parent.relative_to(mirror)
        if not {".git", "target", "node_modules"} & set(relative.parts):
            roots.add("" if relative == Path(".") else relative.as_posix())
    return roots


def owner(rel: str, roots: set[str]) -> str | None:
    """The nearest directory holding a manifest above a file, '' for the checkout's root."""
    parts = rel.split("/")[:-1]
    for size in range(len(parts), -1, -1):
        if "/".join(parts[:size]) in roots:
            return "/".join(parts[:size])
    return None


def module_runs(tool: str, roots: set[str], command, files: list[str], mirror: Path, work_dir: Path, env: dict,
                fallback=None) -> list[dict]:
    """Indexer runs: the checkout's root, then each manifest directory holding files the earlier runs left out.

    `command(prefix, output)` is the run in a directory; `fallback(prefix, output)` the run once more when the
    first one fails (an option the release does not take: the indexer's defaults rather than no index).
    """
    pending, covered, runs = [""], set(), []
    while pending:
        prefix = pending.pop(0)
        output = Path(work_dir) / f"{tool}-{len(runs)}.scip"
        run = {"prefix": prefix, **measured(command(prefix, output), str(Path(mirror) / prefix), env, 3 * 3600)}
        if run["returncode"] != 0 and fallback is not None:
            run = {"prefix": prefix, "fallback": True,
                   **measured(fallback(prefix, output), str(Path(mirror) / prefix), env, 3 * 3600)}
        run["index"] = str(output) if output.is_file() else None
        run["index_bytes"] = output.stat().st_size if output.is_file() else 0
        runs.append(run)
        if run["index"]:
            probe = Index(mirror)
            probe.load(output, prefix)
            covered |= set(probe.documents)
        if prefix == "" and roots:
            missing = [rel for rel in files if rel not in covered]
            pending += sorted({owner(rel, roots) for rel in missing} - {None, ""})
    return runs


def indexer(name: str, version: str, runs: list[dict]) -> dict:
    return {"name": name, "version": version, "seconds": round(sum(run["seconds"] for run in runs), 1),
            # None when no run's peak was measured (Windows), never 0.
            "peak_mb": max((run["peak_mb"] for run in runs if run.get("peak_mb") is not None), default=None)}
