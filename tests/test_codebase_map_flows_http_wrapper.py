"""A function of the project that wraps the HTTP client, proved from the engine's own data, and the `rotta` rule it proposes.

`fetch` called inside `adminFetch(url, body)` hides every call made through `adminFetch` from the route join, because the
`rotta` rules are written by hand, wrapper by wrapper. The engine names the client function it resolved the call into (a
symbol of `typescript` or `@types/node`: `daodan/data/http-clients.json`) and the parameter the URL is read from (a read of
a `project-value` of kind `parameter`, the reader being the function itself): the view carries both (`external_symbols`,
`detail`). `http_wrappers.prove` proves the wrapper from them, `report` proposes the rule, and the sites it cannot prove
are gaps with their cause. Nothing here is a name, a depth or an expression.

The proof runs on a snapshot of `fixtures/http-wrapper` (a TypeScript project) with the index scip-typescript 0.6.2 wrote
for it, wherever the tree-sitter grammars of the snapshot load:

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_flows_http_wrapper.py

Record the index again after any change to the fixture's sources (`fixtures/http-wrapper/record_index.py`, on Modal):
the index states positions. Its `fetch` is TypeScript's own (`lib.dom.d.ts`); the one of `@types/node` is in the index
of `fixtures/code-graph/ts`, which the table test reads.
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent / "daodan/core"))
sys.path.insert(0, str(TESTS))
import code_graph  # noqa: E402
import edge_view  # noqa: E402
import flows  # noqa: E402
import http_wrappers  # noqa: E402
import resolve_edges  # noqa: E402
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from indexers import typescript  # noqa: E402
from languages import semantic  # noqa: E402
from snapshot_store import _unpack, open_snapshot  # noqa: E402
from test_codebase_map_flows import read_project  # noqa: E402

FIXTURE = TESTS / "fixtures/http-wrapper"
DOM = "scip-typescript npm typescript 6.0.3 lib/`lib.dom.d.ts`/fetch()."
WINDOW = "scip-typescript npm typescript 6.0.3 lib/`lib.dom.d.ts`/WindowOrWorkerGlobalScope#fetch()."
NODE = "scip-typescript npm @types/node 22.19.8 web-globals/`fetch.d.ts`/global/fetch()."
OTHER = "scip-typescript npm node-fetch 3.3.2 `index.d.ts`/fetch()."


class TableTests(unittest.TestCase):
    def test_the_table_holds_the_three_fetch_symbols_and_the_parser_reads_each(self):
        clients = http_wrappers.CLIENTS
        self.assertEqual(sorted((c["manager"], c["package"], c["descriptors"]) for c in clients),
                         sorted([("npm", "typescript", "lib/`lib.dom.d.ts`/fetch()."),
                                 ("npm", "typescript", "lib/`lib.dom.d.ts`/WindowOrWorkerGlobalScope#fetch()."),
                                 ("npm", "@types/node", "web-globals/`fetch.d.ts`/global/fetch().")]))
        for entry in clients:
            with self.subTest(entry["descriptors"]):
                self.assertEqual(code_graph.descriptors(entry["descriptors"])[-1], ("fetch", "method"))
                self.assertEqual((entry["url"], entry["method"]), (0, "arg1.method|GET"))

    def test_a_symbol_of_any_version_finds_its_entry_and_no_other_symbol_does(self):
        for symbol in (DOM, WINDOW, NODE, NODE.replace("22.19.8", "26.6.6"), DOM.replace("6.0.3", "5.9.1")):
            with self.subTest(symbol):
                self.assertIsNotNone(http_wrappers.client(symbol))
        for symbol in (OTHER, DOM.replace("typescript", "typescript-lite"),  # another package of the same descriptors
                       DOM.replace("fetch()", "fetchAll()"), "local 3", "src/a.ts#local 3", "", "not a symbol"):
            with self.subTest(symbol):
                self.assertIsNone(http_wrappers.client(symbol))

    def test_the_symbols_the_recorded_engine_wrote_for_fetch_are_in_the_table(self):
        root = TESTS / "fixtures/code-graph/ts"
        index = code_graph.Index(root)
        index.load(root / "index.scip")
        found = {occurrence.key for occurrences in index.documents.values() for occurrence in occurrences
                 if occurrence.key.endswith("/fetch().")}
        self.assertEqual(len(found), 2, found)  # TypeScript's DOM `fetch`, and Node's
        self.assertTrue(all(http_wrappers.client(symbol) for symbol in found), found)


class ViewTests(unittest.TestCase):
    """What the view carries from the store's rows, on rows written by hand for a Python snapshot."""

    SOURCES = {"app/calls.py": "def work(url, other):\n    both(url)\n    mixed(other)\n    callback()\n    return url\n"}
    PARAMETER = "scip-python python app 1 `app.calls`/work().(url)"
    OTHER_PARAMETER = "scip-python python app 1 `app.calls`/work().(other)"

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name).resolve() / "proj"
        for rel, text in cls.SOURCES.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")
        cls.manifest = root.parent / "manifest.sqlite"
        cls.edges = root.parent / "engine-edges.sqlite"
        snapshot.read_project(root, cls.manifest)
        cls.refs = {}  # (kind, line, name) -> what a row of the store repeats of the reference
        with open_snapshot(cls.manifest) as store, semantic_store.semantic_reader(store) as db:
            for identity, kind, caller, l0, c0, blob in db.execute(
                    "SELECT id, kind, caller, l0, c0, payload FROM sem_references WHERE kind IN ('call','read')"):
                cls.refs[kind, l0, ".".join(_unpack(blob)["parts"])] = (identity, caller, l0, c0)
            cls.binding = resolve_edges.store_binding(store, cls.manifest, store.metadata.get("parser_fingerprint"),
                                                      {"python": {"engine": "stub", "state": "fresh"}}, {})

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def ref(self, kind: str, line: int, name: str) -> tuple:
        return self.refs[kind, line, name]

    def row(self, kind, line, name, verdict, symbol, *, detail="", confidence="confirmed", package=None):
        identity, caller, l0, c0 = self.ref(kind, line, name)
        return {"reference_id": identity, "file": "app/calls.py", "language": "python", "kind": kind, "caller": caller,
                "l0": l0, "c0": c0, "verdict": verdict, "target_id": None, "symbol": symbol, "resolver": "stub@1",
                "confidence": confidence, "external": package, "payload": {"chain": [], "detail": detail}}

    def view(self, rows):
        resolve_edges.write_edge_store(self.edges, rows, self.binding)
        with open_snapshot(self.manifest) as store:
            view = edge_view.load_edge_view(store, engine_store=self.edges)
        by = {(kind, ref["span"][0], ".".join(ref["parts"])): ref for kind, found in
              (("call", view["references"]), ("read", view["reads"])) for ref in found}
        return by, view

    def package(self, name):
        return {"manager": "npm", "package": name, "version": "1"}

    def test_a_call_whose_sure_ends_are_all_external_lists_the_symbol_of_each_once_and_keeps_the_first_package(self):
        by, _ = self.view([self.row("call", 2, "both", "external", DOM, package=self.package("typescript")),
                           self.row("call", 2, "both", "external", NODE, package=self.package("@types/node")),
                           self.row("call", 2, "both", "external", DOM, package=self.package("typescript"))])
        record = by["call", 2, "both"]
        self.assertEqual(record["external_symbols"], sorted({DOM, NODE}))
        self.assertEqual(record["external"], self.package("typescript"))  # as it was: the first end's package
        self.assertEqual((record["resolution"], record["target_id"]), ("unresolved", None))

    def test_an_end_that_is_not_external_beside_the_external_ones_lists_no_symbols(self):
        by, _ = self.view([self.row("call", 3, "mixed", "external", DOM, package=self.package("typescript")),
                           self.row("call", 3, "mixed", "project-value", self.OTHER_PARAMETER, detail="parameter")])
        self.assertNotIn("external_symbols", by["call", 3, "mixed"])
        self.assertEqual(by["call", 3, "mixed"]["external"], self.package("typescript"))  # as it was

    def test_an_uncertain_external_end_is_no_sure_end(self):
        by, _ = self.view([self.row("call", 2, "both", "external", DOM, package=self.package("typescript")),
                           self.row("call", 2, "both", "external", NODE, package=self.package("@types/node"),
                                    confidence="uncertain")])
        self.assertNotIn("external_symbols", by["call", 2, "both"])  # the answer is a candidate, no external end

    def test_a_read_whose_ends_are_project_values_of_one_kind_exposes_the_kind_and_no_symbol(self):
        by, _ = self.view([self.row("read", 2, "url", "project-value", self.PARAMETER, detail="parameter"),
                           self.row("read", 3, "other", "project-value", self.OTHER_PARAMETER, detail="variable")])
        self.assertEqual((by["read", 2, "url"]["detail"], by["read", 3, "other"]["detail"]), ("parameter", "variable"))
        self.assertEqual(by["read", 2, "url"]["reason"], "project-value")  # as it was
        for record in (by["read", 2, "url"], by["read", 3, "other"]):
            self.assertNotIn("symbol", record)  # the kind is all a consumer needs, and the record travels in packets

    def test_a_read_with_ends_of_two_kinds_or_an_end_that_is_no_value_exposes_no_kind(self):
        by, _ = self.view([self.row("read", 2, "url", "project-value", self.PARAMETER, detail="parameter"),
                           self.row("read", 2, "url", "project-value", self.OTHER_PARAMETER, detail="variable"),
                           self.row("read", 3, "other", "project-value", self.OTHER_PARAMETER, detail="parameter"),
                           self.row("read", 3, "other", "external", DOM, package=self.package("typescript"))])
        for record in (by["read", 2, "url"], by["read", 3, "other"]):
            self.assertNotIn("detail", record)

    def test_a_call_whose_end_is_a_value_exposes_no_kind(self):
        by, _ = self.view([self.row("call", 4, "callback", "project-value", self.PARAMETER, detail="parameter")])
        self.assertNotIn("detail", by["call", 4, "callback"])


RULES = [{"written": f"router.{verb}", "link": "offre", "handler": "arg1",
          "route": {"service": "api", "method": verb.upper(), "path": "arg0"}}
         for verb in ("get", "post", "put", "patch", "delete")]
PROVED = {  # every proof the fixture gives (callee -> {(position of the URL, method)}): an unexpected one fails
    "src/client.ts::plain": {(0, "POST")}, "src/client.ts::generic": {(0, "PUT")}, "src/client.ts::arrow": {(0, "GET")},
    "src/client.ts::Api.remove": {(0, "DELETE")}, "src/client.ts::second": {(1, "PATCH")},
    "src/client.ts::viaWindow": {(0, "GET")}, "src/client.ts::remote": {(0, "GET")},
    "src/client.ts::agreeing": {(0, "POST")}, "src/client.ts::overloadedFunction": {(0, "GET")},
    "src/client.ts::Overloaded.get": {(0, "GET")},  # overloads, as a function's: the implementation's parameters
    "src/client.ts::genericDefault": {(0, "PUT")},  # generic, with a scope of its own for the default value
    "src/client.ts::quotedKey": {(0, "POST")},  # a string key is a key like another
    "src/client.ts::indirectEval": {(0, "PUT")},  # an indirect eval runs in the global scope: it cannot write the parameter
    "src/view.tsx::jsxClean": {(0, "PUT")},  # elements and attributes that write nothing refuse nothing
    "src/client.ts::adminFetch": {(0, "POST")},  # a real project's shape: generic, five parameters, `try`, nested arrow
    "src/refused.ts::conflicting": {(0, "POST"), (1, "PUT")}}  # each call alone; `report` refuses the pair
# The cause of each refusal has a text of its own: a gap that holds its text and no other's is that cause's.
CAUSES = {
    "several": "several ends", "again": "declared or assigned again inside the function",
    "shadowed": "the engine reads another variable there", "template": "built from the parameter path by template_string",
    "concatenation": "built from the parameter path by binary_expression", "call": "built from the parameter path by call_expression",
    "method": "method arg1.method|GET: not a literal", "differently": "read the route differently",
    "unresolved": "holds a scope the reader cannot close", "unread": "holds lines the reader could not read",
    "arguments": "reads `arguments`",
    "ambiguous": "another declaration of the file", "no-declaration": "declares no parameter",
    "destructured": "is destructured", "rest": "is a rest parameter"}
REFUSED = {  # function -> its cause, and how many gaps it has (one per call of the client that is refused)
    **{f"src/refused.ts::{name}": ("again", 1) for name in (
        "reassigned", "augmented", "counted", "destructured", "iterated", "objectPattern", "closure")},
    # a write the snapshot cannot declare: its scope stays unresolved; generic functions are no exception
    **{f"src/refused.ts::{name}": ("unresolved", 1) for name in (
        "parenthesized", "nonNull", "arrayParen", "forParen", "pairParen", "arrayNonNull", "evaluated", "nestedGeneric",
        "genericArrayParen", "genericEval", "genericDefaultArrayParen", "genericBlock",
        # a direct eval whose callee is wrapped in what only wraps it (parentheses, `as`, `!`): the same eval
        "parenEval", "asEval", "nonNullEval", "genericParenEval")},
    # the reader leaves a function with a `this` parameter unresolved, so it is refused as any other: `this` takes no
    # place in the count, and the reader reading it would turn this test red before a place went wrong
    "src/client.ts::withThis": ("unresolved", 1),
    "src/refused.ts::unreadBlock": ("unread", 1),  # a syntax error the grammar makes of the statement: lines unread
    "src/refused.ts::argsAlias": ("arguments", 1), "src/legacy.js::argsAliasJs": ("arguments", 1),
    "src/legacy.js::withSloppy": ("unresolved", 1), "src/legacy.js::parenEvalJs": ("unresolved", 1),  # a sloppy script
    # a write in an element that is an attribute's value or a fragment's: declared now, so it is the write's cause
    **{f"src/view.tsx::{name}": ("again", 1) for name in ("jsxAttr", "jsxAttrPlain", "jsxFragment", "jsxChild")},
    "src/refused.ts::shadowed": ("shadowed", 1), "src/refused.ts::templated": ("template", 1),
    "src/refused.ts::concatenated": ("concatenation", 1), "src/refused.ts::called": ("call", 1),
    **{f"src/refused.ts::{name}": ("method", 1) for name in (
        "methodParameter", "optionsPassed", "spreadOptions", "computedMethod",
        # a computed key, or `__proto__`, may set any member: the options hold no `method` that can be read
        "computedKey", "computedOther", "protoMethod")},
    "src/refused.ts::conflicting": ("differently", 1),
    "src/refused.ts::destructuredParameter": ("destructured", 1), "src/refused.ts::restParameter": ("rest", 1),
    "src/refused.ts::outer.inner": ("no-declaration", 1),  # the parameter is the outer function's
    # the callee form `file::name` is the name of two declarations of the file
    "src/ambiguous.ts::post": ("ambiguous", 1), "src/ambiguous.ts::send": ("ambiguous", 2),
    "src/ambiguous.ts::relay": ("ambiguous", 2)}
SILENT = ("src/own.ts::useOwn", "src/own.ts::injected", "src/refused.ts::fixed", "src/refused.ts::noArgument")  # no gap
HAND = [  # what a model writes by hand for the wrappers of the fixture: the candidates are these rules
    {"callee": f"src/client.ts::{name}", "link": "rotta", "route": {"service": "api", "method": method, "path": path}}
    for name, method, path in (
        ("Api.remove", "DELETE", "arg0"), ("Overloaded.get", "GET", "arg0"), ("adminFetch", "POST", "arg0"),
        ("agreeing", "POST", "arg0"),
        ("arrow", "GET", "arg0"), ("generic", "PUT", "arg0"), ("genericDefault", "PUT", "arg0"),
        ("indirectEval", "PUT", "arg0"), ("overloadedFunction", "GET", "arg0"), ("plain", "POST", "arg0"),
        ("quotedKey", "POST", "arg0"), ("remote", "GET", "arg0"), ("second", "PATCH", "arg1"),
        ("viaWindow", "GET", "arg0"))] + [
    {"callee": "src/view.tsx::jsxClean", "link": "rotta", "route": {"service": "api", "method": "PUT", "path": "arg0"}}]


def sources() -> dict:
    """The fixture's sources: its two manifests and `src/`, never a bytecode or the index."""
    paths = [FIXTURE / "package.json", FIXTURE / "tsconfig.json", *sorted((FIXTURE / "src").rglob("*"))]
    return {path.relative_to(FIXTURE).as_posix(): path.read_text(encoding="utf-8") for path in paths if path.is_file()}


class WrapperTests(unittest.TestCase):
    """The proof on the snapshot of the fixture, with the engine's own index."""

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="http-wrapper-")).resolve()
        cls.manifest = read_project(cls.work, sources())
        with code_graph.Snapshot(cls.manifest) as snap:
            index = code_graph.Index(snap.root)
            index.load(FIXTURE / "index.scip")
            hops, traversal, _ = code_graph.adapter_traversal(typescript, index, snap)
            built = {language: code_graph.build(index, snap, language, hops,
                                                {"name": "scip-typescript", "version": typescript.VERSION}, None,
                                                traversal) for language in ("javascript", "typescript")}
            code_graph.write_store(snap, resolve_edges.default_edge_store(cls.manifest), built,
                                   f"scip-typescript@{typescript.VERSION}")
        cls.stack = contextlib.ExitStack()
        store = cls.stack.enter_context(open_snapshot(cls.manifest))
        cls.db = cls.stack.enter_context(semantic_store.semantic_reader(store))
        cls.view = edge_view.load_edge_view(store)
        cls.facts = flows.Facts(store, cls.db, cls.view)
        cls.report = http_wrappers.report(cls.facts, cls.view, RULES)
        cls.proofs, cls.gaps = http_wrappers.prove(cls.facts, cls.view)

    @classmethod
    def tearDownClass(cls):
        cls.stack.close()
        shutil.rmtree(cls.work, True)

    def candidate(self, callee: str, report=None) -> dict | None:
        return next((c for c in (report or self.report)["candidates"] if c["callee"] == callee), None)

    def gaps_of(self, symbol: str, report=None) -> list[dict]:
        return [gap for gap in (report or self.report)["gaps"] if gap["symbol"] == symbol]

    def line_of(self, file: str, within: str, needle: str) -> int:
        """The line of the first `needle` after the line that holds `within`."""
        lines = sources()[file].split("\n")
        start = next(n for n, text in enumerate(lines) if within in text)
        return next(n for n in range(start, len(lines)) if needle in lines[n]) + 1

    def unresolved_inside(self, callee: str) -> list:
        """The reasons of the scopes inside a function that the reader left unresolved."""
        [function] = [d for d in self.facts.declarations.values()
                      if d["kind"] in ("function", "method") and self.facts.named(d["id"]) == callee]
        scopes = {identity: _unpack(blob) for identity, blob in self.db.execute(
            "SELECT id, payload FROM sem_scopes WHERE file=?", (function["file"],))}
        own = {identity for identity, scope in scopes.items()
               if scope.get("caller") is not None and f"{function['file']}::{scope['caller']}" == function["id"]}

        def within(identity):
            while identity is not None:
                if identity in own:
                    return True
                identity = scopes[identity].get("parent")
            return False
        return [scope.get("reason") for identity, scope in scopes.items() if within(identity) and scope.get("unresolved")]

    def test_the_view_names_the_client_function_and_the_parameter_the_engine_resolved(self):
        fetches = {(ref["file"], ref["span"][0]): ref for ref in self.view["references"] if ref["parts"][-1:] == ["fetch"]}
        plain = fetches["src/client.ts", self.line_of("src/client.ts", "function plain", "fetch(")]
        self.assertEqual(plain["external_symbols"], [DOM])
        window = fetches["src/client.ts", self.line_of("src/client.ts", "function viaWindow", "fetch(")]
        self.assertEqual(window["external_symbols"], sorted([DOM, WINDOW]))  # two ends of one call
        own = fetches["src/own.ts", self.line_of("src/own.ts", "function useOwn", "fetch(")]  # the project's own `fetch`
        self.assertNotIn("external_symbols", own)
        injected = fetches["src/own.ts", self.line_of("src/own.ts", "function injected", "fetch(")]  # a parameter
        self.assertNotIn("external_symbols", injected)
        reads = {(ref["file"], ref["span"][0]): ref for ref in self.view["reads"] if ref["parts"] == ["url"]}
        generic = reads["src/client.ts", self.line_of("src/client.ts", "function generic<", "fetch(")]
        self.assertEqual(generic["detail"], "parameter")
        self.assertIsNone(generic.get("binding_id"))  # the snapshot's scope of a generic function stays open: the engine says
        arrow = reads["src/client.ts", self.line_of("src/client.ts", "const arrow", "fetch(")]  # a local symbol of the engine
        self.assertEqual(arrow["detail"], "parameter")
        shadowed = reads["src/refused.ts", self.line_of("src/refused.ts", "function shadowed", "fetch(")]
        self.assertEqual(shadowed["detail"], "variable")
        self.assertNotIn("symbol", shadowed)

    def test_a_wrapper_is_proved_with_the_argument_its_url_is_and_the_method_it_calls_with(self):
        proved = {}
        for proof in self.proofs:
            proved.setdefault(proof["callee"], set()).add((proof["index"], proof["method"]))
        self.assertEqual(proved, PROVED)  # no other proof: a false one fails here
        for proof in self.proofs:
            self.assertTrue(proof["site"].startswith(proof["callee"].split("::")[0] + ":"), proof)
            self.assertEqual(proof["symbol"], self.facts.declarations[proof["symbol"]]["id"])
        plain = next(proof for proof in self.proofs if proof["callee"] == "src/client.ts::plain")
        self.assertEqual(plain["site"], f"src/client.ts:{self.line_of('src/client.ts', 'function plain', 'fetch(')}")

    def test_the_four_shapes_a_wrapper_is_written_in_are_proved(self):
        """A plain function, a generic one (the snapshot cannot close its scope: the engine is the source), an arrow
        assigned to a constant (the engine names its parameter with a local symbol) and a method."""
        for name in ("plain", "generic", "arrow", "Api.remove"):
            with self.subTest(name):
                self.assertIsNotNone(self.candidate(f"src/client.ts::{name}"))

    def test_the_position_of_the_url_is_the_one_in_the_functions_own_parameter_list(self):
        """From the tree of the function, not from a record looked up by name: the second parameter is 1; overloads
        change nothing, for a method as for a function (the implementation's parameters are the call's)."""
        positions = {callee: {index for index, _ in found} for callee, found in PROVED.items()}
        self.assertEqual({name: positions[f"src/client.ts::{name}"] for name in (
            "second", "Overloaded.get", "overloadedFunction")},
            {"second": {1}, "Overloaded.get": {0}, "overloadedFunction": {0}})
        self.assertEqual(self.candidate("src/client.ts::second")["rule"]["route"]["path"], "arg1")
        self.assertEqual(self.candidate("src/client.ts::Overloaded.get")["rule"]["route"]["path"], "arg0")

    def test_what_the_url_is_not_a_parameter_of_is_no_wrapper_and_no_gap(self):
        for symbol in SILENT:
            with self.subTest(symbol):
                self.assertEqual(self.gaps_of(symbol), [])
                self.assertIsNone(self.candidate(symbol))
                self.assertNotIn(symbol, {proof["callee"] for proof in self.proofs})

    def test_each_refusal_is_a_gap_with_its_own_cause_and_its_site_and_no_candidate(self):
        for callee, (cause, count) in REFUSED.items():
            with self.subTest(callee):
                gaps = self.gaps_of(callee)
                self.assertEqual(len(gaps), count, gaps)
                for gap in gaps:
                    self.assertIn(CAUSES[cause], gap["reason"])
                    self.assertEqual([other for other, text in CAUSES.items() if other != cause and text in gap["reason"]],
                                     [], gap)  # no other cause's text: one text covers one check
                    file, _, line = gap["site"].rpartition(":")
                    self.assertEqual((file, line.isdecimal()), (callee.split("::")[0], True), gap)
                self.assertIsNone(self.candidate(callee))
        reassigned = self.gaps_of("src/refused.ts::reassigned")
        self.assertEqual([gap["site"] for gap in reassigned],
                         [f"src/refused.ts:{self.line_of('src/refused.ts', 'function reassigned', 'fetch(')}"])
        self.assertEqual(sorted(gap["symbol"] for gap in self.report["gaps"] if gap["symbol"] not in REFUSED),
                         [])  # a gap no refusal above names fails here

    def test_a_name_that_two_declarations_of_a_file_share_is_a_gap_and_links_nothing(self):
        """The rule names a function as `file::name`, and the reader gives that name to an object literal's method, a
        block's function and a namespace's member too: `queue.post(...)` was linked as the wrapper `post`."""
        calls = [ref for ref in self.view["references"] if ref["file"] == "src/ambiguous.ts" and ref["parts"] == ["queue", "post"]]
        self.assertEqual([self.facts.named(ref["target_id"]) for ref in calls], ["src/ambiguous.ts::post"])  # the premise
        for name in ("post", "send", "relay"):
            self.assertIsNone(self.candidate(f"src/ambiguous.ts::{name}"))
        links = flows.link_facts(self.manifest, flows.validate_rules(
            [*RULES, *(candidate["rule"] for candidate in self.report["candidates"])]))
        self.assertEqual([edge for edge in links["edges"] if edge.get("route") and edge["from"] == "src/ambiguous.ts::useQueue"], [])
        # the overload signature of a function is no second declaration of its name
        self.assertIsNotNone(self.candidate("src/client.ts::overloadedFunction"))

    def test_the_generic_exemption_is_exactly_the_readers_one_reason_and_nothing_hides_behind_it(self):
        generic = semantic.GENERIC_SCOPE_REASON
        self.assertEqual(self.unresolved_inside("src/client.ts::generic"), [generic])
        self.assertEqual(self.unresolved_inside("src/client.ts::genericDefault"), [generic])  # on its parameter scope
        self.assertIsNotNone(self.candidate("src/client.ts::generic"))
        self.assertIsNotNone(self.candidate("src/client.ts::genericDefault"))
        # a later reason takes the place of the generic one on the same scope, or sits on another scope of the function
        for name in ("genericArrayParen", "genericEval", "genericBlock", "genericDefaultArrayParen", "nestedGeneric"):
            with self.subTest(name):
                reasons = self.unresolved_inside(f"src/refused.ts::{name}")
                self.assertTrue([reason for reason in reasons if reason != generic], reasons)
                self.assertIsNone(self.candidate(f"src/refused.ts::{name}"))
        self.assertNotIn(generic, self.unresolved_inside("src/refused.ts::genericArrayParen"))  # overwritten
        self.assertIn(generic, self.unresolved_inside("src/refused.ts::genericDefaultArrayParen"))  # beside the other

    def test_a_function_the_engine_ends_in_a_symbol_outside_the_table_is_no_proof_and_no_gap(self):
        view = copy.deepcopy(self.view)
        for ref in view["references"]:
            if any(http_wrappers.client(symbol) for symbol in ref.get("external_symbols") or ()):
                ref["external_symbols"] = [OTHER]
        proofs, gaps = http_wrappers.prove(self.facts, view)
        self.assertEqual((proofs, gaps), ([], []))

    def test_ends_outside_the_table_mixed_with_the_table_ends_are_a_gap_with_several_ends(self):
        view = copy.deepcopy(self.view)
        plain = self.line_of("src/client.ts", "function plain", "fetch(")
        for ref in view["references"]:
            if (ref["file"], ref["span"][0], ref["parts"]) == ("src/client.ts", plain, ["fetch"]):
                ref["external_symbols"] = sorted([DOM, OTHER])
        proofs, gaps = http_wrappers.prove(self.facts, view)
        self.assertNotIn("src/client.ts::plain", {proof["callee"] for proof in proofs})
        [gap] = [gap for gap in gaps if gap["symbol"] == "src/client.ts::plain"]
        self.assertIn(CAUSES["several"], gap["reason"])
        self.assertEqual(gap["site"], f"src/client.ts:{plain}")
        report = http_wrappers.report(self.facts, view, RULES)
        self.assertIsNone(self.candidate("src/client.ts::plain", report))

    def test_the_candidate_is_the_rotta_rule_with_the_proof_and_the_call_sites_it_covers(self):
        plain = self.candidate("src/client.ts::plain")
        self.assertEqual(plain["rule"], {"callee": "src/client.ts::plain", "link": "rotta",
                                         "route": {"service": "api", "method": "POST", "path": "arg0"}})
        self.assertEqual(plain["proof"], f"src/client.ts:{self.line_of('src/client.ts', 'function plain', 'fetch(')}")
        # four calls resolve to it; three have a URL the rules read (one has a `${...}`, one a host); one is computed
        self.assertEqual((plain["calls"], plain["literal"]), (4, 3))
        self.assertNotIn("absolute", plain)  # `_rest_key` drops a base URL by design: no rule depends on a host
        second = self.candidate("src/client.ts::second")
        self.assertEqual(second["rule"]["route"], {"service": "api", "method": "PATCH", "path": "arg1"})
        self.assertEqual((second["calls"], second["literal"]), (1, 1))
        generic = self.candidate("src/client.ts::generic")
        self.assertEqual(generic["rule"]["route"], {"service": "api", "method": "PUT", "path": "arg0"})
        arrow = self.candidate("src/client.ts::arrow")
        self.assertEqual(arrow["rule"]["route"]["method"], "GET")  # no options: fetch's default
        remove = self.candidate("src/client.ts::Api.remove")
        self.assertEqual((remove["rule"]["route"]["method"], remove["calls"]), ("DELETE", 1))
        agreeing = self.candidate("src/client.ts::agreeing")  # two calls of fetch that read the route alike
        self.assertEqual((agreeing["rule"]["route"]["method"], agreeing["calls"]), ("POST", 0))
        self.assertEqual(agreeing["proof"], f"src/client.ts:{self.line_of('src/client.ts', 'function agreeing', 'fetch(')}")
        remote = self.candidate("src/client.ts::remote")  # a host in every URL it is called with changes nothing
        self.assertEqual((remote["calls"], remote["literal"]), (2, 2))
        self.assertNotIn("others", self.report)

    def test_the_service_is_the_one_the_offered_routes_name_else_the_candidate_has_none(self):
        self.assertEqual(self.candidate("src/client.ts::plain")["rule"]["route"]["service"], "api")
        self.assertNotIn("services", self.candidate("src/client.ts::plain"))
        two = http_wrappers.report(self.facts, self.view, [*RULES, {
            "written": "other.get", "link": "offre", "route": {"service": "web", "method": "GET", "path": "arg0"},
            "handler": "arg1"}])
        plain = self.candidate("src/client.ts::plain", two)
        self.assertEqual(plain["rule"]["route"], {"method": "POST", "path": "arg0"})  # no service: the model chooses
        self.assertEqual(plain["services"], ["api", "web"])
        none = http_wrappers.report(self.facts, self.view, [])
        plain = self.candidate("src/client.ts::plain", none)
        self.assertEqual((plain["rule"]["route"], plain["services"]), ({"method": "POST", "path": "arg0"}, []))
        self.assertIn("any service", plain["note"])
        # a service a rule reads from the call is no name
        read = http_wrappers.report(self.facts, self.view, [{
            "written": "other.get", "link": "offre", "route": {"service": "arg0", "method": "GET", "path": "arg1"},
            "handler": "arg2"}])
        self.assertEqual(self.candidate("src/client.ts::plain", read)["services"], [])

    def test_a_service_only_a_rotta_rule_names_is_a_service_of_others_and_no_candidate_takes_it(self):
        external = {"written": "stripe.charge", "link": "rotta",
                    "route": {"service": "stripe", "method": "POST", "path": "arg0"}}
        with_offered = http_wrappers.report(self.facts, self.view, [*RULES, external])
        self.assertEqual(self.candidate("src/client.ts::plain", with_offered)["rule"]["route"]["service"], "api")
        alone = http_wrappers.report(self.facts, self.view, [external])
        plain = self.candidate("src/client.ts::plain", alone)
        self.assertEqual((plain["rule"]["route"], plain["services"]), ({"method": "POST", "path": "arg0"}, []))

    def test_a_candidate_is_a_rule_once_it_has_a_service(self):
        without = http_wrappers.report(self.facts, self.view, [])
        rule = self.candidate("src/client.ts::plain", without)["rule"]
        with self.assertRaises(ValueError):
            flows.validate_rules([rule])  # the service is the model's to name
        self.assertEqual(flows.validate_rules([{**rule, "route": {**rule["route"], "service": "api"}}])[0]["link"], "rotta")
        for candidate in self.report["candidates"]:  # no `*`, ever
            flows.validate_rules([candidate["rule"]])

    def test_the_proposed_rules_are_the_hand_written_ones_and_link_the_calls_they_do(self):
        proposed = [candidate["rule"] for candidate in self.report["candidates"]]
        self.assertEqual(sorted(proposed, key=lambda rule: rule["callee"]), HAND)
        before = flows.link_facts(self.manifest, flows.validate_rules(RULES))
        after = flows.link_facts(self.manifest, flows.validate_rules([*RULES, *proposed]))
        # `link_facts` applies the proposed rules with no model: writing them changes nothing
        self.assertEqual(before["routes"], after["routes"])
        self.assertEqual([edge for edge in before["edges"] if edge.get("route")],
                         [edge for edge in after["edges"] if edge.get("route")])
        # ten literal URLs reach a wrapper (two with a host, which the route key drops); six meet a route
        linked = {(edge["from"], edge["to"]) for edge in after["edges"]
                  if edge.get("route") and not edge["from"].startswith("src/static.ts::")}  # the direct calls of the client
        self.assertIn(("src/callers.ts::useAll", "src/server.ts::createOrder"), linked)
        self.assertEqual(len(linked), 6)

    def test_a_wrapper_a_recorded_rule_already_names_is_no_candidate(self):
        route = {"service": "api", "method": "POST", "path": "arg0"}
        by_callee = http_wrappers.report(self.facts, self.view, [
            *RULES, {"callee": "src/client.ts::plain", "link": "rotta", "route": route}])
        by_written = http_wrappers.report(self.facts, self.view, [
            *RULES, {"written": "second", "link": "rotta", "route": {**route, "method": "PATCH", "path": "arg1"}}])
        for report, named in ((by_callee, "src/client.ts::plain"), (by_written, "src/client.ts::second")):
            with self.subTest(named):
                self.assertIsNone(self.candidate(named, report))
                self.assertEqual(self.gaps_of(named, report), [])
                self.assertIsNotNone(self.candidate("src/client.ts::generic", report))  # the others stay

    def test_the_subcommand_prints_the_candidates_and_the_gaps_as_json(self):
        rules = self.work / "flow-rules.json"
        rules.write_text(json.dumps({"schema": flows.RULES_SCHEMA, "rules": RULES}), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = flows.main(["wrappers", str(self.manifest), "--rules", str(rules)])
        printed = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(printed, json.loads(json.dumps(self.report)))
        self.assertEqual(sorted(printed), ["candidates", "coverage", "gaps"])

    def test_without_the_engine_nothing_is_proved_and_the_report_says_why(self):
        work = Path(tempfile.mkdtemp(prefix="http-wrapper-lexical-")).resolve()
        self.addCleanup(shutil.rmtree, work, True)
        manifest = read_project(work, sources())
        report = http_wrappers.wrappers(manifest, RULES)
        self.assertEqual((report["candidates"], report["gaps"]), ([], []))
        self.assertEqual(report["coverage"], "missing_store")

    def test_a_store_the_snapshot_rejects_gives_no_candidate_and_its_reason(self):
        """A measure that read nothing from the engine looked like a project with no wrapper: the report names the cause."""
        work = Path(tempfile.mkdtemp(prefix="http-wrapper-rejected-")).resolve()
        self.addCleanup(shutil.rmtree, work, True)
        manifest = read_project(work, sources())
        resolve_edges.default_edge_store(manifest).write_bytes(b"corrupted")
        report = http_wrappers.wrappers(manifest, RULES)
        self.assertEqual((report["candidates"], report["gaps"], report["coverage"]), ([], [], "rejected_store"))
        self.assertTrue(any("edge store" in reason for reason in report["why"]), report["why"])
        self.assertNotIn("why", self.report)  # an engine that answered has nothing to explain


if __name__ == "__main__":
    unittest.main()
