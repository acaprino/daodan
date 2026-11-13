"""The shared module's mechanisms, on SCIP indexes written in memory and a stand-in snapshot.

    python -m pytest benchmarks/inference-audit/test_scip_graph.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scip_graph  # noqa: E402

P = "scip-x mgr pkg 1.0 "  # a project symbol's prefix


# A few SCIP messages, encoded.

def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte, value = value & 0x7F, value >> 7
        out.append(byte | 0x80 if value else byte)
        if not value:
            return bytes(out)


def _field(number: int, payload) -> bytes:
    if isinstance(payload, int):
        return _varint(number << 3) + _varint(payload)
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    return _varint(number << 3 | 2) + _varint(len(data)) + data


def occurrence(line: int, start: int, end: int, symbol: str, definition: bool = False) -> bytes:
    """A one-line occurrence, `line` 1-based, columns in the document's unit."""
    return _field(1, b"".join(_varint(n) for n in (line - 1, start, end))) + _field(2, symbol) \
        + _field(3, 1 if definition else 0)


def information(symbol: str, implements: str | None = None, signature: str | None = None) -> bytes:
    out = _field(1, symbol)
    if implements:
        out += _field(4, _field(1, implements) + _field(3, 1))
    if signature:
        out += _field(7, _field(5, signature))
    return out


def document(rel: str, occurrences: list[bytes], informations: list[bytes] = (), unit: int = 1) -> bytes:
    return _field(2, _field(1, rel) + _field(6, unit) + b"".join(_field(2, o) for o in occurrences)
                  + b"".join(_field(3, i) for i in informations))


def load(tmp_path: Path, *documents: bytes) -> scip_graph.Index:
    path = tmp_path / "index.scip"
    path.write_bytes(b"".join(documents))
    index = scip_graph.Index(tmp_path)
    index.load(path)
    return index


class Snapshot:
    """What `Traversal` and `build` ask of a snapshot: declarations by position, references, languages."""

    def __init__(self, declared: dict, references: list = (), language: str = "x"):
        self.declared = declared  # (rel, line, byte column) -> declaration id
        self._references = list(references)  # (id, rel, kind, line, byte column)
        self.rel, self.checkout = {}, {}
        rels = {rel for rel, *_ in declared} | {row[1] for row in self._references}
        self.languages = {rel: language for rel in rels}
        self.inventory = sorted(rels)

    def grade(self, rel, line, column):
        if column is None:
            return "outside", None
        target = self.declared.get((rel, line, column))
        return ("callable", target) if target else ("value", "variable")

    def function_at(self, rel, line, column):
        return self.declared.get((rel, line, column))

    def references(self, language):
        for identity, rel, kind, line, column in self._references:
            yield identity, rel, kind, "unresolved", None, (line, column, line, column + 1), ["name"], "-"

    def callee(self, rel, span, parts):
        return span[0], span[1]


def ends(index, snapshot, key, **options):
    return scip_graph.Traversal(index, snapshot, {}, **options).ends(key)


# 1. Same-range aliasing: a definition and a reference are aliases, two definitions never; the adapter decides.

def _shared_range(tmp_path):
    """`a.x` line 1: Q and G both defined at 0-1, with references to each other there; C defined at 2-3 with a
    reference to D, a function declared at line 2."""
    q, g, c, d = P + "A#q.", P + "A#getQ().", P + "c.", P + "d()."
    (tmp_path / "a.x").write_text("q c\nd\n", encoding="utf-8")
    index = load(tmp_path, document("a.x", [
        occurrence(1, 0, 1, q, True), occurrence(1, 0, 1, g, True), occurrence(1, 0, 1, q), occurrence(1, 0, 1, g),
        occurrence(1, 2, 3, c, True), occurrence(1, 2, 3, d), occurrence(2, 0, 1, d, True)]))
    return index, Snapshot({("a.x", 2, 0): "a.x::function@2:0"}), (q, g, c, d)


def test_two_definitions_at_one_range_are_no_alias(tmp_path):
    index, snapshot, (q, g, _c, _d) = _shared_range(tmp_path)
    for key in (q, g):
        assert [(end.cls, end.chain) for end in ends(index, snapshot, key)] == [("project-value", ())]


def test_definition_and_reference_at_one_range_are_an_alias(tmp_path):
    index, snapshot, (_q, _g, c, _d) = _shared_range(tmp_path)
    assert [(end.cls, end.target, end.chain) for end in ends(index, snapshot, c)] == \
        [("project-callable", "a.x::function@2:0", ("same-range",))]


def test_adapter_vetoes_and_adds_same_range_pairs(tmp_path):
    index, snapshot, (q, g, c, d) = _shared_range(tmp_path)
    vetoed = ends(index, snapshot, c, same_range={(c, d): False})
    assert [(end.cls, end.chain) for end in vetoed] == [("project-value", ())]
    added = ends(index, snapshot, q, same_range={(q, g): True})
    assert [(end.cls, end.key, end.chain) for end in added] == [("project-value", g, ("same-range",))]


# 2. The adapter's classification of a symbol key, before the default rule.

def _placeholder(tmp_path):
    own, string, namespace = "scip-java maven . . pkg/Own#", "scip-java maven . . kotlin/String#", \
        "scip-java maven . . pkg/"
    (tmp_path / "a.x").write_text("Own\nString\npkg\n", encoding="utf-8")
    index = load(tmp_path, document("a.x", [occurrence(1, 0, 3, own, True), occurrence(2, 0, 6, string),
                                            occurrence(3, 0, 3, namespace)]))
    return index, own, string, namespace


def test_placeholder_package_is_undefined_project_symbol_by_default(tmp_path):
    index, _own, string, namespace = _placeholder(tmp_path)
    for key in (string, namespace):
        assert [(end.cls, end.detail) for end in ends(index, Snapshot({}), key)] == \
            [("dead-end", "undefined-project-symbol")]


def test_adapter_classifies_external_namespace_and_project(tmp_path):
    index, own, string, namespace = _placeholder(tmp_path)
    stdlib = {"manager": "maven", "package": "kotlin-stdlib", "version": "unknown"}
    table = {string: stdlib, namespace: "namespace", own: "project"}
    traversal = scip_graph.Traversal(index, Snapshot({}), {}, classify=table.get)
    assert [(end.cls, end.detail) for end in traversal.ends(string)] == [("external", "maven kotlin-stdlib@unknown")]
    assert [end.cls for end in traversal.ends(namespace)] == ["namespace"]
    assert [end.cls for end in traversal.ends(own)] == ["project-value"]
    project = scip_graph.Traversal(index, Snapshot({}), {}, classify=lambda key: "project")
    assert [end.detail for end in project.ends("scip-java maven lib 2.0 lib/Other#")] == ["undefined-project-symbol"]
    graph, _ = scip_graph.build(index, Snapshot({}, [(1, "a.x", "read", 2, 0), (2, "a.x", "read", 3, 0)]), "x", {},
                                {}, traversal=traversal)
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert nodes[string]["external"] == stdlib and nodes[namespace]["external"] is None
    assert graph["holes"] == []


# 3. Every edge carries the symbol referenced at its site; `uncertain` only when an adapter writes it.

def test_edges_carry_symbol(tmp_path):
    index, snapshot, (_q, _g, c, d) = _shared_range(tmp_path)
    graph, _ = scip_graph.build(index, snapshot, "x", {}, {})
    assert graph["edges"] and all(edge["symbol"] in (_q, _g, d) for edge in graph["edges"])
    assert all("uncertain" not in edge for edge in graph["edges"])
    assert graph["removed"] == []


# 4. The adapter's refine step: its holes, uncertain edges and removed edges are told apart.

def test_refine_changes_are_tagged(tmp_path):
    index, snapshot, _keys = _shared_range(tmp_path)

    def refine(seen, graph):
        assert seen is index
        graph["edges"][0]["uncertain"] = {"reason": "overload", "candidates": ["x", "y"]}
        graph["edges"][1]["removed"] = "not a call"
        graph["holes"].append({"site": "a.x:9", "name": "get", "kind": "call", "class": "implicit-operator",
                               "reason": "indexed read"})

    plain, _ = scip_graph.build(index, snapshot, "x", {}, {})
    graph, _ = scip_graph.build(index, snapshot, "x", {}, {}, refine=refine)
    assert len(graph["edges"]) == len(plain["edges"]) - 1
    assert [edge["removed"] for edge in graph["removed"]] == ["not a call"]
    assert graph["edges"][0]["uncertain"]["reason"] == "overload"
    assert [hole.get("by") for hole in graph["holes"]] == ["refine"]
    counts = scip_graph.report(graph)
    assert counts["edges_uncertain"] == {"overload": 1} and counts["edges_removed"] == {"not a call": 1}


def test_refine_cannot_drop_untagged(tmp_path):
    index, snapshot, _keys = _shared_range(tmp_path)
    with pytest.raises(ValueError, match="removed"):
        scip_graph.build(index, snapshot, "x", {}, {}, refine=lambda seen, graph: graph["edges"].pop())


# 5. Statically dispatched sites take no implementation edges.

def test_static_sites_take_no_implementation(tmp_path):
    base, sub = P + "Base#m().", P + "Sub#m()."
    # UTF-16 columns: the `é` before the second call is two bytes, one unit.
    (tmp_path / "a.x").write_text("m\nm\nx.m()\né.m()\n", encoding="utf-8")
    index = load(tmp_path, document("a.x", [occurrence(1, 0, 1, base, True), occurrence(2, 0, 1, sub, True),
                                            occurrence(3, 2, 3, base), occurrence(4, 2, 3, base)],
                                    [information(sub, implements=base)], unit=2))
    snapshot = Snapshot({("a.x", 1, 0): "base", ("a.x", 2, 0): "sub"},
                        [(1, "a.x", "call", 3, 2), (2, "a.x", "call", 4, 3)])
    graph, references = scip_graph.build(index, snapshot, "x", {}, {}, static={("a.x", 4, 3)})
    by_site = {}
    for edge in graph["edges"]:
        by_site.setdefault(edge["site"], []).append((edge["to"], edge["chain"]))
    assert by_site["a.x:3"] == [(base, []), (sub, ["implementation"])]
    assert by_site["a.x:4"] == [(base, [])]
    assert [end.target for end in references[2]["ends"]] == ["base"]
    assert [end.target for end in references[1]["ends"]] == ["base", "sub"]


# 6. SymbolInformation.signature_documentation is kept.

def test_signature_documentation_is_kept(tmp_path):
    key = P + "A#m()."
    index = load(tmp_path, document("a.x", [occurrence(1, 0, 1, key, True)],
                                    [information(key, signature="void m(int a)")]))
    assert index.info[key]["signature"] == "void m(int a)"


# 7. The map's scripts are found from any depth, or the Modal mount is assumed.

def test_scripts_lookup_from_a_shallow_folder(tmp_path):
    (tmp_path / "scip_graph.py").write_bytes((HERE / "scip_graph.py").read_bytes())
    code = "import sys; sys.path.insert(0, '.'); import scip_graph; print(scip_graph._SCRIPTS.as_posix())"
    found = subprocess.run([sys.executable, "-I", "-c", code],
                           cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert found.returncode == 0, found.stderr
    assert found.stdout.strip() in ("/daodan/map/scripts",
                                    *(str(parent / "plugins/codebase-map/skills/map/scripts").replace("\\", "/")
                                      for parent in tmp_path.parents))
