"""The code graph's mechanisms, on SCIP indexes written in memory and a stand-in snapshot; then the chain
ends of eight small projects in `fixtures/code-graph/`, each with the index its engine wrote, read with its
indexer module, and the invariant that every call and read of their snapshots ends somewhere.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_code_graph.py

Rebuild a fixture's index after changing its sources (the snapshot is written by the test):
- `ts`: `scip-typescript index --cwd . --output index.scip --no-progress-bar` (0.5.2, with `node_modules` beside
  `ts`, removed afterwards) in `fixtures/code-graph/ts`;
- `rust`: `rust-analyzer scip . --output index.scip` in `fixtures/code-graph/rust`;
- `go`, `python`, `java`, `kotlin`, `c`, `cpp`: on Modal with the pinned indexers, since Java, Kotlin, C and C++
  need their build, from the checkout's root, with the proxy variables empty:

      export HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= PYTHONIOENCODING=utf-8
      modal deploy benchmarks/inference-audit/fixture_indexes.py
      python benchmarks/inference-audit/fixture_indexes.py spawn --languages go,python,java,kotlin,c,cpp
      python benchmarks/inference-audit/fixture_indexes.py fetch --languages go,python,java,kotlin,c,cpp

  `fetch`, once the calls end, writes `index.scip` (and Kotlin's `kotlin-configs/`) into each fixture.
"""
from __future__ import annotations

import collections
import json
import re
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
from indexers import typescript  # noqa: E402

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


# A `rebinding` hop takes the place of the definition, and its edge says so in its chain.

def test_rebinding_takes_the_place_of_the_definition(tmp_path):
    f, g = P + "f().", P + "g()."
    (tmp_path / "a.x").write_text("f\ng\nf\nf()\n", encoding="utf-8")
    index = load(tmp_path, document("a.x", [occurrence(1, 0, 1, f, True), occurrence(2, 0, 1, g, True),
                                            occurrence(3, 0, 1, f), occurrence(4, 0, 1, f)]))
    snapshot = Snapshot({("a.x", 1, 0): "first", ("a.x", 2, 0): "other", ("a.x", 3, 0): "bound"},
                        [(1, "a.x", "call", 4, 0)])
    hops = {f: [(("a.x", 3, 0), "rebinding"), (g, "alias")]}
    graph, references = code_graph.build(index, snapshot, "x", hops, {})
    assert [(end.cls, end.target, end.chain) for end in references[1]["ends"]] == \
        [("project-callable", "bound", ("rebinding",))]
    assert [(edge["site"], edge["target"], edge["chain"]) for edge in graph["edges"] if edge["symbol"] == f] == \
        [("a.x:3", "bound", ["rebinding"]), ("a.x:4", "bound", ["rebinding"])]
    nowhere = code_graph.Traversal(index, snapshot, {f: [(("a.x", 2, 2), "rebinding"), (g, "alias")]}).ends(f)
    assert [(end.cls, end.target, end.chain) for end in nowhere] == \
        [("project-value", None, ("rebinding",)), ("project-callable", "other", ("alias",))]


# 6. SymbolInformation.signature_documentation is kept.

def test_signature_documentation_is_kept(tmp_path):
    key = P + "A#m()."
    index = load(tmp_path, document("a.x", [occurrence(1, 0, 1, key, True)],
                                    [information(key, signature="void m(int a)")]))
    assert index.info[key]["signature"] == "void m(int a)"


# A file the snapshot holds without declarations (lexical coverage) is the project's, not outside it.

def test_adapter_traversal_runs_prepare_first_and_passes_only_what_the_module_defines(tmp_path):
    import types
    index, snapshot, (q, g, _c, _d) = _shared_range(tmp_path)
    calls = []
    full = types.SimpleNamespace(
        prepare=lambda read, snap: calls.append("prepare") or {"filled": 1},
        hops=lambda read: calls.append("hops") or {},
        same_range=lambda read: calls.append("same_range") or {(q, g): True},
        classify=lambda read: calls.append("classify") or (lambda key: None))
    hops, traversal, prepared = code_graph.adapter_traversal(full, index, snapshot)
    assert calls[:2] == ["prepare", "hops"] and set(calls[2:]) == {"same_range", "classify"}
    assert prepared == {"filled": 1} and traversal.same_range == {(q, g): True} and traversal.classify is not None
    bare = types.SimpleNamespace(hops=lambda read: {})
    _hops, traversal, prepared = code_graph.adapter_traversal(bare, index, snapshot)
    assert prepared is None and traversal.same_range == {} and traversal.classify is None


HOOKS = ("prepare", "same_range", "classify", "unanswered", "static", "refine", "missing", "tasks")  # the optional ones


def test_an_indexer_takes_the_folders_it_runs_in_from_the_pre_map():
    """The structure of a project is the pre-map's: an indexer that runs once per module, crate or package says
    which units it wants (`structure`) and is handed their folders (`roots`); none walks the tree for a
    manifest, and the common part offers no way to."""
    import inspect
    from indexers import go, java, kotlin, rust, typescript
    assert not hasattr(code_graph, "manifest_dirs")
    import importlib
    import resolve_edges
    for spec in resolve_edges.ENGINES:
        module = importlib.import_module(f"indexers.{spec.indexer}")
        if not hasattr(module, "engine"):  # every indexer of the pass takes its structure from the pre-map
            assert callable(getattr(module, "structure", None)), spec.name
    record = {"units": [{"kind": "go-module", "root": "."}, {"kind": "cargo-crate", "root": "crates/a"},
                        {"kind": "npm-package", "root": "web"}],
              "workspace": [{"tool": "cargo", "root": "."}]}
    assert go.structure(record) == {"roots": {""}}
    assert rust.structure(record) == {"roots": {"", "crates/a"}}
    assert typescript.structure(record) == {"roots": {"web"}}
    assert java.structure(record) == kotlin.structure(record) == {  # Maven's modules, the builds not run
        "roots": set(), "tools": {}, "toolchains": [], "modules": [], "other_builds": []}
    for module in (go, rust, typescript, java, kotlin):
        source = inspect.getsource(module)
        assert "roots" in inspect.signature(module.index).parameters
        assert not re.search(r"rglob[(][^)]*(go[.]mod|Cargo[.]toml|package[.]json)", source), module.__name__


def test_every_hook_an_indexer_defines_is_reached():
    """A hook an indexer module defines and nothing calls is a silent difference between the measured graph and
    the product's: each is reached through `adapter_traversal`, which the driver calls, or by the driver itself."""
    import importlib
    import inspect
    import pkgutil
    import resolve_edges
    driver = inspect.getsource(resolve_edges.index_stage)
    reached = set(re.findall(r'hasattr\(module, "(\w+)"\)', driver))
    if "code_graph.adapter_traversal(module" in driver:
        reached |= set(code_graph.TRAVERSAL_HOOKS)
    unreached = {}
    for item in pkgutil.iter_modules([str(SCRIPTS / "indexers")]):
        module = importlib.import_module(f"indexers.{item.name}")
        if not hasattr(module, "hops"):  # a helper the adapters share, no adapter
            continue
        defined = {name for name in HOOKS if callable(getattr(module, name, None))}
        if defined - reached:
            unreached[item.name] = sorted(defined - reached)
    assert not unreached, unreached


def test_file_without_declarations_is_inside_the_snapshot(tmp_path):
    snapshot = code_graph.Snapshot.__new__(code_graph.Snapshot)
    snapshot.paths, snapshot.inventory = {"a.kt": tmp_path / "a.kt"}, set()
    assert snapshot.grade("a.kt", 1, 0) == ("value", "file without declarations in the snapshot")
    assert snapshot.grade("b.kt", 1, 0) == ("outside", None)

# 5. A constructor names its class (requirement 14 of the engine specification): javapoet's 25 calls where the lexical
# resolver gives the class and scip-java the constructor.

def test_a_constructor_end_names_its_class(tmp_path):
    import snapshot
    project = tmp_path / "proj"
    (project / "fx").mkdir(parents=True)
    (project / "fx/Box.java").write_text("package fx;\n\nclass Box {\n    final int size;\n\n"
                                         "    Box(int size) { this.size = size; }\n\n"
                                         "    static Box make() {\n        return new Box(3);\n    }\n}\n",
                                         encoding="utf-8")
    manifest = tmp_path / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    box, init = "scip-java maven . . fx/Box#", "scip-java maven . . fx/Box#`<init>`()."
    (tmp_path / "index.scip").write_bytes(document("fx/Box.java", [
        occurrence(3, 6, 9, box, True), occurrence(6, 4, 7, init, True), occurrence(9, 19, 22, init)]))
    with code_graph.Snapshot(manifest) as snap:
        index = code_graph.Index(snap.root)
        index.load(tmp_path / "index.scip")
        _graph, references = code_graph.build(index, snap, "java", {}, {})
    calls = [row for row in references.values() if row["kind"] == "call"]
    assert [(end.cls, end.target) for row in calls for end in row["ends"]] == \
        [("project-callable", "fx/Box.java::class@3:0")]


CALLED = {
    # chi's shapes: a literal called where it is written, a call's result called, an element called.
    "app.go": "package app\n\nfunc Deprecation(x int) func(int) int {\n\treturn func(y int) int { return x + y }\n}\n\n"
              "func Run(handlers []func()) {\n\tfunc() {}()\n\tdefer func() {}()\n\tgo func(i int) {}(1)\n"
              "\t_ = Deprecation(1)(2)\n\thandlers[len(handlers)-1]()\n}\n",
    # tududi's: an IIFE, an arrow called in place, a call's result, an element, a conditional.
    "app.js": "(function () { return 1; })();\n(() => 2)();\nconst f = () => () => 3;\nf()();\n"
              "const table = [() => 4];\ntable[0]();\n(f || table[0])();\n"
              "class A {}\nclass B extends A {\n  constructor() {\n    super();\n  }\n}\nconst lazy = () => import('./x');\n"}


def test_a_call_with_no_callee_name_is_answered_by_its_literal_or_named_by_its_callee(tmp_path):
    """A call whose callee has no name: a function literal called where it is written reaches that literal, a
    certain static edge from the snapshot's own declaration; a call of a call's result (`Deprecation(x)(y)`), of an
    element (`handlers[i]()`) or of another computed value is a hole of that class, the dynamic step's to answer:
    a declared type says a signature, never which function a value is. `super(x)` is answered where the index
    names the keyword's constructor, else a `super-call` hole; `import(x)` loads a module: `dynamic-import`."""
    import snapshot
    project = tmp_path / "proj"
    project.mkdir()
    for rel, text in CALLED.items():
        (project / rel).write_text(text, encoding="utf-8")
    manifest = tmp_path / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    found = {}
    with code_graph.Snapshot(manifest) as snap:
        for language in ("go", "javascript"):
            _graph, references = code_graph.build(code_graph.Index(snap.root), snap, language, {}, {})
            found.update({row["site"]: (row["hole"], [(end.cls, end.target) for end in row["ends"]])
                          for row in references.values() if row["kind"] == "call" and not row["name"]})
    literal = lambda rel, at: [("project-callable", f"{rel}::function@{at}")]  # noqa: E731
    assert found == {"app.go:8": ("", literal("app.go", "8:1")), "app.go:9": ("", literal("app.go", "9:7")),
                     "app.go:10": ("", literal("app.go", "10:4")), "app.go:11": ("call-result", []),
                     "app.go:12": ("element", []),
                     "app.js:1": ("", literal("app.js", "1:1")), "app.js:2": ("", literal("app.js", "2:1")),
                     "app.js:4": ("call-result", []), "app.js:6": ("element", []), "app.js:7": ("computed-callee", []),
                     "app.js:11": ("super-call", []), "app.js:14": ("dynamic-import", [])}


# The fixtures: one small project per indexer in `fixtures/code-graph/<name>/`, with the index its engine wrote.
# `ts-ends.json` and `RUST_ENDS` hold the ends of `ts` and `rust`; each other fixture has `expected.json`, ends
# written from its sources before any index existed: `"FILE:LINE NAME"` (the snapshot reference whose name ends
# with NAME there) to `kind`, then
# - `ends`: `decl FILE:LINE` (exactly the project declarations reached), `external TEXT` (an external end whose
#   package holds TEXT), `value KIND PATTERN` (a project value of that kind, `*` for any, whose symbol matches the
#   regular expression); `via TAG+TAG` is the chain reaching it, `via -` none;
# - `none`: no project declaration (a hole, a value or an external, never a guess);
# - `uncertain`: every edge there is uncertain for that reason with exactly those candidates (without it, none is);
# - `operator`: no snapshot reference, a graph hole of that class for an implicit call;
# - `rule`: the adapter rule the case covers.

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
LANGUAGES = {"ts": ("javascript", "typescript"), "rust": ("rust",), "go": ("go",), "python": ("python",),
             "java": ("java",), "kotlin": ("kotlin",), "c": ("c",), "cpp": ("cpp",)}
ADAPTERS = {"ts": "typescript", "c": "clang", "cpp": "clang"}
CASES = {name: json.loads((FIXTURES / name / "expected.json").read_text(encoding="utf-8"))
         for name in ("go", "python", "java", "kotlin", "c", "cpp")}
KNOWN = {}  # (fixture, case) -> why the graph is wrong there, one line, until it is fixed


def _built(name: str, source: Path, manifest: Path) -> dict:
    """The fixture's graph per language, with what its driver passes from the adapter, and its snapshot rows."""
    import importlib
    adapter = importlib.import_module(f"indexers.{ADAPTERS.get(name, name)}")
    with code_graph.Snapshot(manifest) as snapshot:
        index = code_graph.Index(snapshot.root)
        index.load(source / "index.scip")
        hops, traversal, prepared = code_graph.adapter_traversal(adapter, index, snapshot)
        build_options = {}
        if hasattr(adapter, "static"):
            build_options["static"] = adapter.static(index)
        if hasattr(adapter, "refine"):
            extra = (adapter.tasks([[source / "kotlin-configs", ""]]),) if hasattr(adapter, "tasks") else ()
            build_options["refine"] = lambda read, graph: adapter.refine(read, graph, *extra)
        graphs, references = {}, {}
        for language in LANGUAGES[name]:
            graphs[language], found = code_graph.build(index, snapshot, language, hops, {}, None, traversal,
                                                       **build_options)
            references.update(found)
        rows = snapshot.connection.execute(
            "SELECT r.id, r.file, r.kind, c.language FROM sem_references r LEFT JOIN sem_coverage c ON c.file = r.file "
            "WHERE r.kind IN ('call','read') ORDER BY r.file, r.l0, r.c0").fetchall()
        declarations = {identity: f"{snapshot.checkout.get(rel, rel)}:{line}" for identity, rel, line in
                        snapshot.connection.execute("SELECT id, file, l0 FROM sem_declarations")}
    return {"index": index, "graphs": graphs, "references": references, "rows": rows, "declarations": declarations,
            "prepared": prepared}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """`{fixture: built}`, each fixture copied out of the checkout and snapshotted."""
    out = {}
    for name in LANGUAGES:
        source = tmp_path_factory.mktemp(name) / name
        shutil.copytree(FIXTURES / name, source)
        manifest = source.parent / "manifest.sqlite"
        done = subprocess.run([sys.executable, "-I", "snapshot.py", "write", str(source), "--out", str(manifest),
                               "--no-engine", "--no-index", "--no-modules"], cwd=SCRIPTS,
                              capture_output=True, text=True, timeout=300)
        assert done.returncode == 0, done.stderr
        out[name] = _built(name, source, manifest)
    return out


@pytest.fixture(scope="module")
def fixture_rows(built):
    """`{fixture: {"kind site name": reference}}`."""
    return {name: {f"{row['kind']} {row['site']} {row['name']}": row for row in data["references"].values()}
            for name, data in built.items()}


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
    elif want["end"] in (*code_graph.HOLES, typescript.MEMBER):  # a hole, with its class
        assert row["hole"] == want["end"]
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


def _name(key: str) -> str | None:
    parts = code_graph.split_symbol(code_graph._global(key))
    items = code_graph.descriptors(parts[4]) if parts else []
    return items[-1][0] if items else None


def _spec(text: str) -> tuple[str, str, tuple | None]:
    """`(kind, what, chain)` of an expected end: `decl a.go:3 via initializer` -> `decl`, `a.go:3`, the chain."""
    kind, _, rest = text.partition(" ")
    what, via, chain = rest.partition(" via ")
    return kind, what, (() if chain == "-" else tuple(chain.split("+"))) if via else None


def _case_params():
    for name, cases in CASES.items():
        for case in sorted(cases):
            reason = KNOWN.get((name, case))
            yield pytest.param(name, case, id=f"{name} {case}",
                               marks=[pytest.mark.xfail(reason=reason, strict=True)] if reason else [])


@pytest.mark.parametrize("name, case", list(_case_params()))
def test_fixture_case(built, name, case):
    want, data = CASES[name][case], built[name]
    site, called = case.rsplit(" ", 1)
    edges = [edge for graph in data["graphs"].values() for edge in graph["edges"]
             if edge["site"] == site and _name(edge["symbol"]) == called]
    if "operator" in want:
        holes = [hole["class"] for graph in data["graphs"].values() for hole in graph["holes"]
                 if hole["site"] == site and hole["name"] == called]
        assert holes == [want["operator"]]
        return
    rows = [row for row in data["references"].values()
            if row["site"] == site and row["kind"] == want["kind"] and row["name"].split(".")[-1] == called]
    assert len(rows) == 1, f"{len(rows)} snapshot references"
    row = rows[0]
    seen = [(end.cls, data["declarations"].get(end.target, end.key), "+".join(end.chain) or "-", end.detail)
            for end in row["ends"]]
    declared = collections.defaultdict(set)
    for end in row["ends"]:
        if end.cls == "project-callable":
            declared[data["declarations"].get(end.target, end.target)].add(end.chain)
    wanted = [_spec(text) for text in want.get("ends", ())]
    if "uncertain" not in want:
        assert set(declared) == {what for kind, what, _chain in wanted if kind == "decl"}, seen
    for kind, what, chain in wanted:
        if kind == "decl":
            assert chain is None or chain in declared[what], seen
        elif kind == "external":
            assert any(end.cls == "external" and what in end.detail and chain in (None, end.chain)
                       for end in row["ends"]), seen
        else:
            node, pattern = what.split(" ", 1)
            assert any(end.cls == "project-value" and node in ("*", end.detail) and re.search(pattern, end.key, re.I)
                       for end in row["ends"]), seen
    if want.get("none"):
        assert not declared, seen
    if "hole" in want:
        assert row["hole"] == want["hole"], seen
    marked = [edge["uncertain"] for edge in edges if edge.get("uncertain")]
    if "uncertain" not in want:
        assert not marked, marked
        return
    assert edges and len(marked) == len(edges), edges
    assert {item["reason"] for item in marked} == {want["uncertain"]["reason"]}, marked
    candidates = set()
    for key in {key for item in marked for key in item["candidates"]}:
        if key not in data["index"].defs:  # a place, `rel:line`, as C and C++ name a symbol's several bodies
            candidates.add(key)
            continue
        rel, occurrence = data["index"].defs[key][0]
        candidates.add(f"{rel}:{occurrence.line}")
    assert candidates == {_spec(text)[1] for text in want["uncertain"]["candidates"]}, marked


# The invariant: every call and read of a snapshot ends in graph ends or in a hole with a class.

def test_every_reference_ends_or_is_a_hole(built):
    from indexers import clang, rust
    inactive = [cause.split("{}") for cause in (clang.INACTIVE, rust.INACTIVE)]  # code the configuration leaves out
    classes = set(code_graph.HOLES) | {"implicit-operator", typescript.MEMBER}  # the TS adapter's cause of a member
    classes |= {hole["class"] for data in built.values() for graph in data["graphs"].values() for hole in graph["holes"]
                if any(hole["class"].startswith(head) and hole["class"].endswith(tail) for head, tail in inactive)}
    violations = collections.defaultdict(list)
    for name, data in sorted(built.items()):
        graphs = data["graphs"].values()
        edges = {(edge["site"], edge["to"]) for graph in graphs for edge in graph["edges"]}
        holes = {(hole["site"], hole["name"], hole["class"]) for graph in graphs for hole in graph["holes"]}
        for identity, rel, kind, language in data["rows"]:
            row = data["references"].get(identity)
            if row is None:
                violations["not in a graph"].append(f"{name} {kind} {rel} ({language or 'no language'})")
                continue
            label = f"{name} {kind} {row['site']} {row['name']}"
            if row["hole"]:
                if row["hole"] not in classes:
                    violations["hole of no known class"].append(f"{label}: {row['hole']}")
                if (row["site"], row["name"], row["hole"]) not in holes:
                    violations["hole missing from the graph"].append(label)
            elif not any(end.cls != "dead-end" for end in row["ends"]):
                violations["neither end nor hole"].append(label)
            else:
                absent = [end.key for end in row["ends"] if end.cls != "dead-end" and (row["site"], end.key) not in edges]
                if absent:
                    violations["end missing from the graph"].append(f"{label}: {absent[0]}")
        for graph in graphs:
            violations["graph hole of no known class"] += [f"{name} {hole['site']} {hole['name']}: {hole['class']}"
                                                           for hole in graph["holes"] if hole["class"] not in classes]
    found = {category: items for category, items in violations.items() if items}
    assert not found, "\n".join(f"{category} ({len(items)}): " + "; ".join(items[:10])
                                for category, items in sorted(found.items()))


# C and C++: what the clang adapter's `prepare` fills in, and what the snapshot cannot read.

def test_clang_prepare_keeps_each_occurrence_once_and_encloses_definitions(built):
    """util.c is compiled by two libraries: the index holds it twice, the graph once. A call's edge starts at
    the function holding it (`enclose`), not at its file."""
    data = built["c"]
    assert data["prepared"]["deduplicated"] > 0
    occurrences = data["index"].documents["util.c"]
    assert len(occurrences) == len(set(occurrences))
    edges = [edge for edge in data["graphs"]["c"]["edges"] if edge["site"] == "main.c:9" and _name(edge["symbol"]) == "add"]
    assert edges and {data["index"].defs[edge["from"]][0][1].line for edge in edges} == {6}, edges


def test_clang_a_file_the_snapshot_cannot_read_is_a_declared_gap_and_its_occurrences_are_kept(built):
    """split.c has a statement split by `#ifdef`: the snapshot reads it lexically, without references. The graph
    names it among the files it could not measure, with the cause, and keeps the index's references there as
    edges of kind `unknown`."""
    graph = built["c"]["graphs"]["c"]
    unread = {item["path"]: item for item in graph["files"]["unread"]}
    assert set(unread) == {"split.c"}
    assert unread["split.c"]["reason"] == "syntax error: line 5"
    kinds = {edge["kind"] for edge in graph["edges"] if edge["site"].startswith("split.c:")}
    assert kinds == {"unknown"} and unread["split.c"]["references"] >= 2


MACRO_C = ("#define CHECK(x) do { if (!(x)) abort(); } while (0)\n"
           "struct pair { int first; };\n"
           "int twice(int v) { return v * 2; }\n"
           "int run(struct pair *p, int n) {\n"
           "    CHECK(p->first == twice(n));\n"
           "#if defined(_MSC_VER)\n"
           "    return _msc_only(n);\n"
           "#elif defined(__APPLE__)\n"
           "    return _apple_only(n);\n"
           "#else\n"
           "    return n;\n"
           "#endif\n"
           "}\n")


def test_clang_a_macros_arguments_take_the_symbols_the_index_writes_at_the_macro(tmp_path):
    """tinyxml2's `TIXMLASSERT( other->_flags == 0 )`: scip-clang writes every reference at its expansion location
    (Indexer.cc, `saveReference`), so what a macro's argument names sits at the macro's name. `prepare` places each
    symbol of the argument's name there back at the argument (the macro keeps its body's own); a name two symbols
    there could be stays a hole. `p` of `p->first` has no reference of its own in the snapshot, its local still
    moves to it. A
    branch of `#if` with no occurrence at all is one the build does not compile: the hole says so."""
    import snapshot
    from indexers import clang
    project = tmp_path / "proj"
    project.mkdir()
    (project / "run.c").write_text(MACRO_C, encoding="utf-8")
    manifest = tmp_path / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    macro, pair, first, twice, run = ("cxx . . $ `run.c:1:9`!", "cxx . project 0$ pair#", "cxx . project 0$ pair#first.",
                                      "cxx . project 0$ twice(1a).", "cxx . project 0$ run(2b).")
    (tmp_path / "index.scip").write_bytes(document("run.c", [
        occurrence(1, 8, 13, macro, True), occurrence(2, 7, 11, pair, True), occurrence(2, 18, 23, first, True),
        occurrence(3, 4, 9, twice, True), occurrence(3, 14, 15, "local 0", True), occurrence(3, 26, 27, "local 0"),
        occurrence(4, 4, 7, run, True), occurrence(4, 21, 22, "local 1", True), occurrence(4, 28, 29, "local 2", True),
        *(occurrence(5, 4, 9, key) for key in (macro, "local 1", first, twice, "local 2")),
        occurrence(11, 11, 12, "local 2")]))
    with code_graph.Snapshot(manifest) as snap:
        index = code_graph.Index(snap.root)
        index.load(tmp_path / "index.scip")
        hops, traversal, prepared = code_graph.adapter_traversal(clang, index, snap)
        _graph, references = code_graph.build(index, snap, "c", hops, {}, None, traversal)
    assert prepared["macro_arguments"] == 4
    found = {(row["site"], row["name"]): (row["hole"], sorted(end.key for end in row["ends"]))
             for row in references.values() if row["site"].split(":")[1] in ("5", "7", "9")}
    assert found == {("run.c:5", "p.first"): ("", [first]),
                     ("run.c:5", "twice"): ("", [twice]), ("run.c:5", "n"): ("", ["run.c#local 2"]),
                     ("run.c:5", "CHECK"): ("", [macro]),
                     ("run.c:7", "_msc_only"): (clang.INACTIVE.format("#if defined(_MSC_VER)"), []),
                     ("run.c:7", "n"): (clang.INACTIVE.format("#if defined(_MSC_VER)"), []),
                     **{("run.c:9", name): (clang.INACTIVE.format("#elif defined(__APPLE__)` of `#if defined(_MSC_VER)"),
                                            []) for name in ("_apple_only", "n")}}


def test_clang_an_operator_call_is_an_edge_of_kind_unknown(built):
    """`a + b` is no call the snapshot lists; the index names `Vec::operator+` there."""
    data = built["cpp"]
    edges = [edge for edge in data["graphs"]["cpp"]["edges"] if edge["site"] == "main.cpp:12"
             and _name(edge["symbol"]) == "operator+"]
    assert {(edge["kind"], data["declarations"].get(edge["target"])) for edge in edges} ==         {("unknown", "shapes.cpp:13")}, edges
