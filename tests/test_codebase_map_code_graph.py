"""The code graph's mechanisms, on SCIP indexes written in memory and a stand-in snapshot; then the chain
ends of two small projects in `fixtures/code-graph/`, each with the index its engine wrote, read with its
indexer module.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_code_graph.py

Rebuild a fixture's index after changing its sources (the snapshot is written by the test):
`scip-typescript index --cwd . --output index.scip --no-progress-bar` (0.5.2, with `node_modules` beside
`ts`, removed afterwards) in `fixtures/code-graph/ts`; `rust-analyzer scip . --output index.scip` in
`fixtures/code-graph/rust`.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import code_graph  # noqa: E402

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


def load(tmp_path: Path, *documents: bytes) -> code_graph.Index:
    path = tmp_path / "index.scip"
    path.write_bytes(b"".join(documents))
    index = code_graph.Index(tmp_path)
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
    return code_graph.Traversal(index, snapshot, {}, **options).ends(key)


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
    traversal = code_graph.Traversal(index, Snapshot({}), {}, classify=table.get)
    assert [(end.cls, end.detail) for end in traversal.ends(string)] == [("external", "maven kotlin-stdlib@unknown")]
    assert [end.cls for end in traversal.ends(namespace)] == ["namespace"]
    assert [end.cls for end in traversal.ends(own)] == ["project-value"]
    project = code_graph.Traversal(index, Snapshot({}), {}, classify=lambda key: "project")
    assert [end.detail for end in project.ends("scip-java maven lib 2.0 lib/Other#")] == ["undefined-project-symbol"]
    graph, _ = code_graph.build(index, Snapshot({}, [(1, "a.x", "read", 2, 0), (2, "a.x", "read", 3, 0)]), "x", {},
                                {}, traversal=traversal)
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert nodes[string]["external"] == stdlib and nodes[namespace]["external"] is None
    assert graph["holes"] == []


# 3. Every edge carries the symbol referenced at its site; `uncertain` only when an adapter writes it.

def test_edges_carry_symbol(tmp_path):
    index, snapshot, (_q, _g, c, d) = _shared_range(tmp_path)
    graph, _ = code_graph.build(index, snapshot, "x", {}, {})
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

    plain, _ = code_graph.build(index, snapshot, "x", {}, {})
    graph, _ = code_graph.build(index, snapshot, "x", {}, {}, refine=refine)
    assert len(graph["edges"]) == len(plain["edges"]) - 1
    assert [edge["removed"] for edge in graph["removed"]] == ["not a call"]
    assert graph["edges"][0]["uncertain"]["reason"] == "overload"
    assert [hole.get("by") for hole in graph["holes"]] == ["refine"]
    counts = code_graph.report(graph)
    assert counts["edges_uncertain"] == {"overload": 1} and counts["edges_removed"] == {"not a call": 1}


def test_refine_cannot_drop_untagged(tmp_path):
    index, snapshot, _keys = _shared_range(tmp_path)
    with pytest.raises(ValueError, match="removed"):
        code_graph.build(index, snapshot, "x", {}, {}, refine=lambda seen, graph: graph["edges"].pop())


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
    graph, references = code_graph.build(index, snapshot, "x", {}, {}, static={("a.x", 4, 3)})
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


# A file the snapshot holds without declarations (lexical coverage) is the project's, not outside it.

def test_file_without_declarations_is_inside_the_snapshot(tmp_path):
    snapshot = code_graph.Snapshot.__new__(code_graph.Snapshot)
    snapshot.paths, snapshot.inventory = {"a.kt": tmp_path / "a.kt"}, set()
    assert snapshot.grade("a.kt", 1, 0) == ("value", "file without declarations in the snapshot")
    assert snapshot.grade("b.kt", 1, 0) == ("outside", None)

# The fixtures: 30 ends in a JS/TS project (`ts-ends.json`), 6 in two Rust test crates sharing one module file.

FIXTURES = HERE / "fixtures/code-graph"
TS_ENDS = json.loads((FIXTURES / "ts-ends.json").read_text(encoding="utf-8"))
RUST_ENDS = {  # site -> the snapshot declaration, or `external`, and the chain that reaches it
    "call tests/test_a.rs:7 assert_len": ("tests/util/mod.rs::function@5:0", []),
    "call tests/test_a.rs:8 util.version": ("tests/util/mod.rs::function@1:0", []),
    "call tests/test_b.rs:5 util.assert_len": ("tests/util/mod.rs::function@5:0", ["rust:module-file"]),
    "call tests/test_b.rs:6 util.version": ("tests/util/mod.rs::function@1:0", ["rust:module-file"]),
    "call tests/util/mod.rs:2 fxrs.parse": ("src/lib.rs::function@1:0", []),
    "call src/lib.rs:2 text.len": ("external", []),
}


@pytest.fixture(scope="module")
def fixture_rows(tmp_path_factory):
    """`{fixture: {"kind site name": reference}}`, each fixture copied out of the checkout and snapshotted."""
    from indexers import rust, typescript
    rows = {}
    for name, adapter in (("ts", typescript), ("rust", rust)):
        source = tmp_path_factory.mktemp(name) / name
        shutil.copytree(FIXTURES / name, source)
        manifest = source.parent / "manifest.sqlite"
        done = subprocess.run([sys.executable, "-I", "snapshot.py", "write", str(source), "--out", str(manifest),
                               "--no-engine", "--no-index", "--no-modules"], cwd=SCRIPTS,
                              capture_output=True, text=True, timeout=300)
        assert done.returncode == 0, done.stderr
        found = rows[name] = {}
        with code_graph.Snapshot(manifest) as snapshot:
            index = code_graph.Index(snapshot.root)
            index.load(source / "index.scip")
            hops = adapter.hops(index)
            traversal = code_graph.Traversal(index, snapshot, hops)
            for language in sorted(set(snapshot.languages.values()) & {"javascript", "typescript", "rust"}):
                _graph, references = code_graph.build(index, snapshot, language, hops, {}, {}, traversal)
                found.update({f"{row['kind']} {row['site']} {row['name']}": row for row in references.values()})
    return rows


@pytest.mark.parametrize("site", sorted(TS_ENDS))
def test_ts_fixture_end(fixture_rows, site):
    row, want = fixture_rows["ts"][site], TS_ENDS[site]
    targets = sorted({end.target for end in row["ends"] if end.cls == "project-callable"})
    if isinstance(want["end"], list):
        best = min((len(end.chain) for end in row["ends"] if end.cls == "project-callable"), default=None)
        assert (targets, best) == (sorted(want["end"]), want.get("hops", best))
    elif want["end"].startswith("external"):
        assert not targets and any(end.cls == "external" and want["end"].split(" ", 1)[1] in end.detail
                                   for end in row["ends"])
    elif want["end"] == "dangling-local":
        assert row["hole"] == "dangling-local"
    else:
        assert not targets and any(end.cls == want["end"] for end in row["ends"])


@pytest.mark.parametrize("site", sorted(RUST_ENDS))
def test_rust_fixture_end(fixture_rows, site):
    target, chain = RUST_ENDS[site]
    ends = fixture_rows["rust"][site]["ends"]
    if target == "external":
        assert any(end.cls == "external" for end in ends)
    else:
        assert any(end.target == target and list(end.chain) == chain for end in ends)

