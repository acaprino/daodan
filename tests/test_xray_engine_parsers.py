"""Real parser regressions for structural detail, call ownership and caches."""

import ast
import sys
import threading
import tomllib
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import snapshot
from languages import javascript, typescript, java, rust, sql, plsql, python
from languages import _treesitter as ts
from languages.base import SIGNATURE_FIELDS


class SqlMaskTests(unittest.TestCase):
    def test_comments_unicode_and_literal_ddl_do_not_create_symbols(self):
        source = (
            "-- città CREATE TABLE ghost (id INT);\n"
            "/* CREATE VIEW absent AS SELECT 1; */\n"
            "CREATE TABLE \"real orders\" (note TEXT DEFAULT 'it''s CREATE TABLE phantom (id INT)');\n"
            "SELECT $$CREATE TABLE dollar_ghost (id INT)$$;\n"
        )
        result = sql.adapter.parse(source, "schema.sql")
        self.assertEqual([(c.name, c.line_number) for c in result.classes], [("real orders", 3)])

    def test_plsql_dynamic_ddl_and_comment_markers_in_strings_are_ignored(self):
        source = (
            "-- CREATE PACKAGE fake AS END;\n"
            "CREATE OR REPLACE PACKAGE BODY billing AS\n"
            "  PROCEDURE run IS BEGIN\n"
            "    EXECUTE IMMEDIATE q'[CREATE TABLE pretend (name VARCHAR2(10))]';\n"
            "    x := 'a--b /* CREATE PACKAGE phantom AS END; */';\n"
            "  END;\nEND;\n"
        )
        result = plsql.adapter.parse(source, "billing.pkb")
        self.assertEqual([c.name for c in result.classes], ["billing"])
        self.assertEqual([f.name for f in result.functions], ["run"])


class ParserCacheTests(unittest.TestCase):
    def test_language_is_shared_and_cache_clear_refreshes_live_threads(self):
        if ts.get_parser("javascript") is None:
            self.skipTest("JavaScript grammar unavailable")
        barrier = threading.Barrier(3)
        observations = [[], []]

        def worker(index):
            observations[index].append(ts.get_parser("javascript"))
            barrier.wait(timeout=10)
            barrier.wait(timeout=10)
            observations[index].append(ts.get_parser("javascript"))

        workers = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
        for worker_thread in workers:
            worker_thread.start()
        barrier.wait(timeout=10)
        ts.get_parser.cache_clear()
        barrier.wait(timeout=10)
        for worker_thread in workers:
            worker_thread.join(timeout=10)
            self.assertFalse(worker_thread.is_alive())
        self.assertIs(observations[0][0][1], observations[1][0][1])
        self.assertIsNot(observations[0][0][0], observations[1][0][0])
        for old, new in observations:
            self.assertIsNot(old[0], new[0])
            self.assertEqual(new[0].parse(b"function ok() {}").root_node.has_error, False)


class AstParserTests(unittest.TestCase):
    def require(self, language):
        if ts.get_parser(language) is None:
            self.skipTest(f"{language} grammar unavailable")

    def assert_reexport_binding(self, module, suffix, provenance):
        result = module.adapter.parse(
            "export { default as PublicEngine, Other as Renamed } from './core.js';\n",
            f"barrel.{suffix}")
        self.assertTrue(result.notes[0].startswith(provenance), result.notes)
        self.assertEqual([(i.module, i.names, i.is_from_import, i.is_internal, i.default_import)
                          for i in result.imports],
                         [("./core.js", ["default", "Other"], True, True, None)])
        self.assertEqual(result.exported_symbols, ["PublicEngine", "Renamed"])
        self.assertIsNone(result.default_export)

    def test_reexport_bindings_are_preserved_without_a_native_grammar(self):
        for module, suffix in ((javascript, "js"), (typescript, "ts")):
            with self.subTest(language=module.adapter.language):
                with mock.patch.object(module, "_ts_parse", return_value=None):
                    self.assert_reexport_binding(module, suffix, "parser=regex-fallback")

    def test_reexport_bindings_match_the_native_parser(self):
        for module, suffix in ((javascript, "js"), (typescript, "ts")):
            with self.subTest(language=module.adapter.language):
                self.require(module.adapter.language)
                self.assert_reexport_binding(module, suffix, "parser=tree-sitter")

    def test_js_wrappers_are_callables_but_map_results_are_values(self):
        self.require("javascript")
        result = javascript.adapter.parse(
            "const rows = items.map(x => transform(x));\n"
            "export const View = React.memo(React.forwardRef((p, ref) => render(p, ref)));\n"
            "const Handler = memo(function inner() { handle(); });\n", "view.js")
        self.assertEqual([f.name for f in result.functions], ["View", "Handler"])
        self.assertEqual(result.functions[0].calls_made, ["render"])
        self.assertEqual(result.functions[1].calls_made, ["handle"])

    def test_js_calls_exclude_strings_comments_and_nested_callable_bodies(self):
        self.require("javascript")
        source = (
            "function run() {\n"
            "  const hint = 'fetch(fake); fs.readFile(fake)'; // axios.get(fake)\n"
            "  function nested() { hidden(); }\n"
            "  const later = () => deferred();\n"
            "  const Thing = class { method() { secret(); } };\n"
            "  db.query('SELECT 1');\n"
            "  fetch('/ok');\n"
            "  new Client();\n"
            "  db.query('SELECT 2');\n"
            "}\n")
        result = javascript.adapter.parse(source, "calls.js")
        self.assertEqual(result.functions[0].calls_made, ["db.query", "fetch", "Client"])
        self.assertEqual([(c.call_type, c.line_number) for c in result.external_calls],
                         [("database", 6), ("network", 7), ("database", 9)])

    def test_chained_callee_names_do_not_reintroduce_literal_or_comment_text(self):
        self.require("javascript")
        result = javascript.adapter.parse(
            "function run() { build('fetch(fake)').finish(); api /* fs.readFile(fake) */.send(); }",
            "chain.js")
        self.assertEqual(result.functions[0].calls_made, ["build().finish", "build", "api.send"])
        self.assertEqual(result.external_calls, [])

    def test_expression_bodied_arrows_and_method_calls_are_attributed(self):
        self.require("typescript")
        result = typescript.adapter.parse(
            "type Callback = (x: string) => void;\n"
            "const load = (x: string) => fetch(x);\n"
            "class Store { read() { return db.query('x'); } save = () => persist(); }\n", "calls.ts")
        self.assertEqual(result.functions[0].calls_made, ["fetch"])
        store = next(c for c in result.classes if c.name == "Store")
        self.assertEqual({m.name: m.calls_made for m in store.methods},
                         {"read": ["db.query"], "save": ["persist"]})

    def test_typescript_members_namespaces_and_heritage_use_existing_models(self):
        self.require("typescript")
        result = typescript.adapter.parse(
            "export interface Repo<T> extends Base<T> { readonly id: string; get(x: T): T; }\n"
            "export enum Mode { Fast = 'f', Safe }\n"
            "export namespace Tools { export function go() { execute(); } export interface Config { enabled: boolean; } }\n"
            "export abstract class Cache<T> extends Parent<T> implements Repo<T> { abstract get(x: T): T; public id: string; }\n",
            "shape.ts")
        classes = {c.name: c for c in result.classes}
        self.assertEqual(classes["Repo"].class_variables, ["id"])
        self.assertEqual([m.name for m in classes["Repo"].methods], ["get"])
        self.assertEqual(classes["Repo"].bases, ["Base<T>"])
        self.assertEqual(classes["Mode"].class_variables, ["Fast", "Safe"])
        self.assertEqual(classes["Cache"].bases, ["Parent<T>", "Repo<T>"])
        self.assertEqual([m.name for m in classes["Cache"].methods], ["get"])
        self.assertIn("Tools", classes)
        self.assertIn("Tools.Config", classes)
        self.assertEqual([(f.name, f.calls_made) for f in result.functions], [("Tools.go", ["execute"])])

    def test_java_calls_and_constructors_ignore_literal_and_lambda_bodies(self):
        self.require("java")
        result = java.adapter.parse(
            "class Service { void run() {\n"
            " String fake = \"new Socket(); Files.readString(path)\";\n"
            " Runnable task = () -> hidden();\n"
            " class Inner { void go() { secret(); } }\n"
            " client.send(); new Socket(); Files.readString(path);\n"
            "} }", "Service.java")
        method = next(c for c in result.classes if c.name == "Service").methods[0]
        self.assertEqual(method.calls_made, ["client.send", "Socket", "Files.readString"])
        self.assertEqual([(c.call_type, c.line_number) for c in result.external_calls],
                         [("network", 5), ("filesystem", 5)])

    def test_java_generic_construction_keeps_the_constructor_call(self):
        self.require("java")
        result = java.adapter.parse(
            "class Factory { void run() { new Holder<String, Integer>(); } }", "Factory.java")
        self.assertEqual(result.classes[0].methods[0].calls_made, ["Holder"])

    def test_rust_calls_macros_impl_heritage_and_macro_symbols(self):
        self.require("rust")
        result = rust.adapter.parse(
            "macro_rules! build { () => { generated() }; }\n"
            "pub struct Store { pub id: u64 }\n"
            "impl Repo for Store { fn get(&self) {\n"
            " let fake = r#\"reqwest::get(fake)\"#;\n"
            " let later = || hidden(); fn nested() { secret(); }\n"
            " std::fs::read(\"x\"); println!(\"ok\"); self.finish();\n"
            "} }", "lib.rs")
        impl = next(c for c in result.classes if c.kind == "impl")
        self.assertEqual(impl.bases, ["Repo"])
        self.assertEqual(impl.methods[0].calls_made, ["std::fs::read", "println!", "self.finish"])
        self.assertIn("build", result.constants)
        self.assertEqual([(c.call_type, c.line_number) for c in result.external_calls], [("filesystem", 6)])

    def test_query_path_and_structural_recovery_produce_same_owned_calls(self):
        self.require("javascript")
        source = b"function f() { function nested() { hidden(); } new Client(); api.send(); }"
        root = ts.get_parser("javascript")[0].parse(source).root_node
        body = root.children[0].child_by_field_name("body")
        self.assertEqual(ts.extract_ast_calls(body, source, "javascript"), ["Client", "api.send"])
        with mock.patch.object(ts, "get_query", return_value=None):
            self.assertEqual(ts.extract_ast_calls(body, source, "javascript"), ["Client", "api.send"])

    def test_typescript_nested_namespaces_keep_qualified_members_and_calls(self):
        self.require("typescript")
        result = typescript.adapter.parse(
            "namespace Outer.Inner { export interface Input extends Pair<string, number>, Other { "
            "readonly name?: string; run(value: number): Promise<void>; } "
            "export const launch = (value: number) => execute(value); }\n",
            "namespace.ts")
        classes = {c.name: c for c in result.classes}
        self.assertEqual(classes["Outer.Inner.Input"].bases, ["Pair<string, number>", "Other"])
        self.assertEqual(classes["Outer.Inner.Input"].class_variables, ["name"])
        method = classes["Outer.Inner.Input"].methods[0]
        self.assertEqual((method.name, method.return_annotation), ("run", "Promise<void>"))
        self.assertEqual([(f.name, f.calls_made) for f in result.functions],
                         [("Outer.Inner.launch", ["execute"])])

    def test_private_typescript_types_do_not_take_exported_symbol_slots(self):
        self.require("typescript")
        source = (
            "interface Private {}\nenum Hidden { Item }\ntype Local = string;\n"
            "export interface Public {}\nexport enum Visible { Item }\nexport type Shared = string;\n"
            "export namespace Tools { interface Secret {} class Detail {} function hidden() {} "
            "export interface Input {} export function run() {} }\n")
        result = typescript.adapter.parse(source, "visibility.ts")
        self.assertEqual(result.exported_symbols,
                         ["Public", "Visible", "Shared", "Tools", "Tools.Input", "Tools.run"])
        js_result = javascript.adapter.parse("class Internal {}\nfunction helper() {}", "legacy.js")
        self.assertEqual(js_result.exported_symbols, ["Internal", "helper"])

    def test_default_import_and_export_identity_survives_native_and_regex_parsers(self):
        cases = [
            ("export default class Engine {}\nexport class Other {}", "Engine"),
            ("export default function build() {}\nexport function Other() {}", "build"),
            ("const Engine = () => {};\nexport default Engine;", "Engine"),
            ("class Engine {}\nexport { Engine as default };", "Engine"),
            ("export default class {}", None),
            ("export default () => work();", None),
        ]
        for module, suffix in ((javascript, "js"), (typescript, "ts")):
            self.require(module.adapter.language)
            for fallback in (False, True):
                with self.subTest(language=module.adapter.language, fallback=fallback):
                    context = mock.patch.object(module, "_ts_parse", return_value=None) if fallback else nullcontext()
                    with context:
                        imported = module.adapter.parse(
                            "import Renamed, { Other as Local } from './core.js';\n"
                            "import { default as Alias, Helper } from './more.js';\n"
                            "import Primary, { default as Second } from './same.js';\n"
                            "import { default as Other, Other as Named } from './collision.js';", f"main.{suffix}")
                        expected_parser = "parser=regex-fallback" if fallback else "parser=tree-sitter"
                        self.assertTrue(imported.notes[0].startswith(expected_parser), imported.notes)
                        self.assertEqual([(i.module, i.default_import, i.names) for i in imported.imports],
                                         [("./core.js", "Renamed", ["Renamed", "Other"]),
                                          ("./more.js", None, ["default", "Helper"]),
                                          ("./same.js", "Primary", ["Primary", "default"]),
                                          ("./collision.js", None, ["default", "Other"])])
                        for source, expected in cases:
                            with self.subTest(source=source):
                                self.assertEqual(module.adapter.parse(source, f"core.{suffix}").default_export, expected)

    def test_rust_chained_call_order_skips_macro_and_closure_bodies(self):
        self.require("rust")
        source = b"fn run() { macro_rules! inner { () => { hidden() }; } let next = || deferred(); new_client().send(); }"
        root = ts.get_parser("rust")[0].parse(source).root_node
        body = root.children[0].child_by_field_name("body")
        self.assertEqual(ts.extract_ast_calls(body, source, "rust"), ["new_client().send", "new_client"])

    def test_python_relative_levels_and_lambda_call_ownership(self):
        result = python.adapter.parse(
            "from ..helpers import work\nfrom . import local\n"
            "def run():\n    deferred = lambda: hidden()\n    return work()\n", "pkg/sub/main.py")
        self.assertEqual([(i.module, i.names, i.is_internal) for i in result.imports],
                         [("..helpers", ["work"], True), (".", ["local"], True)])
        self.assertEqual(result.functions[0].calls_made, ["work"])

    def test_python_signature_holds_every_parameter_kind_flag_and_decorator(self):
        result = python.adapter.parse(
            "import functools\n"
            "@functools.cache\n"
            "async def run(a, b=1, /, c: int = 2, *rest: str, d, e=None, **extra) -> 'Out':\n"
            "    yield a\n"
            "def plain():\n"
            "    def inner():\n"
            "        yield 1\n"
            "    return inner\n"
            "@dataclass(frozen=True)\n"
            "class Point(Base, metaclass=Meta):\n"
            "    x: int = 0\n"
            "    LIMIT = 3\n", "mod.py")
        run, plain = result.functions
        self.assertEqual([(p.name, p.kind, p.annotation, p.default) for p in run.parameters], [
            ("a", "positional_only", None, None),
            ("b", "positional_only", None, "1"),
            ("c", None, "int", "2"),
            ("rest", "var_positional", "str", None),
            ("d", "keyword_only", None, None),
            ("e", "keyword_only", None, "None"),
            ("extra", "var_keyword", None, None),
        ])
        self.assertEqual((run.return_annotation, run.is_async, run.is_generator), ("'Out'", True, True))
        self.assertEqual(run.decorators, ["functools.cache"])
        self.assertFalse(plain.is_generator, "a yield of a nested function is not the outer one's")
        point = result.classes[0]
        self.assertEqual(point.bases, ["Base", "metaclass=Meta"])
        self.assertEqual(point.decorators, ["dataclass(frozen=True)"])
        self.assertEqual([(a.name, a.annotation, a.default) for a in point.attributes],
                         [("x", "int", "0"), ("LIMIT", None, "3")])
        self.assertEqual(point.class_variables, ["x", "LIMIT"])
        for declared in (run.signature_fields, point.signature_fields):
            self.assertTrue(declared and set(declared) <= SIGNATURE_FIELDS, declared)

    def test_typescript_optional_parameters_have_their_own_kind(self):
        self.require("typescript")
        function = typescript.adapter.parse("function f(a: number, b?: string) {}\n", "f.ts").functions[0]
        self.assertEqual([(p.name, p.annotation, p.kind) for p in function.parameters],
                         [("a", "number", None), ("b", "string", "optional")])

    def test_java_varargs_and_annotations_enter_the_signature(self):
        self.require("java")
        method = java.adapter.parse(
            "class A {\n  @Override @Deprecated\n  public int run(final String name, int... rest) { return 1; }\n}\n",
            "A.java").classes[0].methods[0]
        self.assertEqual([(p.name, p.annotation, p.kind) for p in method.parameters],
                         [("name", "String", None), ("rest", "int...", "var_positional")])
        self.assertEqual(method.decorators, ["@Override", "@Deprecated"])

    def test_missing_grammar_still_returns_explicit_regex_provenance(self):
        with mock.patch.object(javascript, "get_parser", return_value=None):
            result = javascript.adapter.parse("function run() { fetch('/ok'); }", "fallback.js")
        self.assertIn("parser=regex-fallback", result.notes)
        self.assertEqual([f.name for f in result.functions], ["run"])


class PythonExtractionTests(unittest.TestCase):
    """The widened Python extraction convention and broken-file recovery.

    Both are measured, not designed: evals/codebase-map/python-parser/RESULTS.md
    records what the top-level-only convention dropped (4.8% to 7.2% of the
    projects' definitions, 8.8% to 9.7% of the libraries') and which recovery
    policy is safe on spans as well as names (50.16% of names at 100% precision
    with zero unsafe emissions over 1,892 broken real files, against 58.14% with
    2,218 unsafe emissions when definitions the cut leaves open are kept).
    """

    NESTED = (
        "import sys\n"
        "\n"
        "if sys.platform == 'win32':\n"
        "    def windows_only():\n"
        "        return helper()\n"
        "\n"
        "def outer(value):\n"
        "    def inner(x):\n"
        "        return x + value\n"
        "\n"
        "    class Local:\n"
        "        def method(self):\n"
        "            return inner(1)\n"
        "\n"
        "class Top:\n"
        "    def visible(self):\n"
        "        def shadow():\n"
        "            return 1\n"
        "        return shadow()\n"
        "\n"
        "    if True:\n"
        "        def conditional(self):\n"
        "            return 2\n"
    )

    BROKEN = (
        "def first():\n"
        "    return 1\n"
        "\n"
        "class Second:\n"
        "    def ok(self):\n"
        "        return first()\n"
        "\n"
        "    def broken(self\n"
        "        return 2\n"
        "\n"
        "def after():\n"
        "    return 3\n"
    )

    def test_nested_and_conditional_definitions_are_qualified_graph_nodes(self):
        result = python.adapter.parse(self.NESTED, "nested.py")
        # The two documented lists keep their meaning, so no consumer of the file
        # outline sees a new entry.
        self.assertEqual([f.name for f in result.functions], ["outer"])
        self.assertEqual([(c.name, [m.name for m in c.methods]) for c in result.classes],
                         [("Top", ["visible"])])
        self.assertEqual([(item.qualified_name, item.kind) for item in result.nested],
                         [("windows_only", "function"), ("outer.inner", "function"),
                          ("outer.Local", "class"), ("outer.Local.method", "method"),
                          ("Top.visible.shadow", "function"), ("Top.conditional", "method")])

    def test_symbol_spans_records_nested_symbols_once_with_exact_spans(self):
        result = python.adapter.parse(self.NESTED, "nested.py")
        spans = snapshot.symbol_spans(result, self.NESTED.split("\n"))
        for name in ("windows_only", "outer.inner", "outer.Local", "outer.Local.method",
                     "Top.visible.shadow", "Top.conditional"):
            self.assertEqual(spans[name]["span_precision"], "exact", name)
        self.assertEqual((spans["outer.inner"]["start"], spans["outer.inner"]["end"]), (8, 9))
        self.assertEqual((spans["Top.conditional"]["start"], spans["Top.conditional"]["end"]),
                         (22, 23))
        # A nested symbol sits inside its enclosing one, so an edit moves both hashes.
        self.assertEqual((spans["outer"]["start"], spans["outer"]["end"]), (7, 13))
        # A direct method of a top-level class is recorded by the class pass only;
        # "merged" would mean the nested pass recorded it a second time.
        self.assertEqual(spans["Top.visible"]["span_precision"], "exact")
        self.assertEqual(len(spans["Top.visible"]["signatures"]), 1)

    def test_pep695_type_alias_is_a_symbol(self):
        if getattr(ast, "TypeAlias", None) is None:
            self.skipTest("PEP 695 aliases need Python 3.12")
        source = ("type CellKey = tuple[str, str]\n"
                  "\n"
                  "class Holder:\n"
                  "    type Inner = int\n"
                  "\n"
                  "    def method(self):\n"
                  "        return 1\n")
        result = python.adapter.parse(source, "alias.py")
        self.assertEqual([(item.qualified_name, item.kind, item.info.line_number)
                          for item in result.nested],
                         [("CellKey", "type-alias", 1), ("Holder.Inner", "type-alias", 4)])
        self.assertEqual([c.name for c in result.classes], ["Holder"])

    def test_direct_nested_class_is_a_graph_node_with_exact_span(self):
        source = "class Outer:\n    class Inner:\n        def run(self):\n            return 1\n"
        result = python.adapter.parse(source, "nested.py")
        self.assertEqual([(item.qualified_name, item.kind) for item in result.nested],
                         [("Outer.Inner", "class"), ("Outer.Inner.run", "method")])
        spans = snapshot.symbol_spans(result, source.split("\n"))
        self.assertEqual((spans["Outer.Inner"]["start"], spans["Outer.Inner"]["end"],
                          spans["Outer.Inner"]["span_precision"]), (2, 4, "exact"))

    def test_conditional_top_level_class_keeps_its_direct_methods(self):
        source = "if flag:\n    class Conditional:\n        def run(self):\n            return 1\n"
        result = python.adapter.parse(source, "conditional.py")
        self.assertEqual([(item.qualified_name, item.kind) for item in result.nested],
                         [("Conditional", "class"), ("Conditional.run", "method")])
        spans = snapshot.symbol_spans(result, source.split("\n"))
        self.assertEqual((spans["Conditional.run"]["start"], spans["Conditional.run"]["end"]), (3, 4))

    def test_broken_file_keeps_only_the_definitions_its_prefix_closes(self):
        result = python.adapter.parse(self.BROKEN, "broken.py")
        self.assertTrue(result.notes[1].startswith("syntax error:"), result.notes)
        self.assertIn("recovered prefix: line 6, 1 closed definitions", result.notes)
        self.assertEqual([f.name for f in result.functions], ["first"])
        self.assertEqual([f.end_line for f in result.functions], [2])
        # `Second` and `Second.ok` end at the prefix's last statement, so their span
        # may be truncated. The safe policy drops them rather than record a body
        # hash an edit outside them would move. `after` is past the damage.
        self.assertEqual([c.name for c in result.classes], [])
        self.assertEqual(result.nested, [])
        # A prefix of a broken file cannot certify reference coverage.
        self.assertIsNone(result.semantic)

    def test_damage_before_any_complete_statement_recovers_nothing_and_says_so(self):
        result = python.adapter.parse("def broken(:\n    return 1\n", "broken.py")
        self.assertIn("recovered prefix: none", result.notes)
        self.assertEqual((result.functions, result.classes, result.nested), ([], [], []))
        self.assertTrue(any(note.startswith("syntax error:") for note in result.notes))

    def test_minimum_interpreter_is_declared_and_enforced(self):
        self.assertEqual(python.MINIMUM_PYTHON, (3, 12))
        python.require_minimum_interpreter("test")
        above = (sys.version_info[0], sys.version_info[1] + 1)
        with mock.patch.object(python, "MINIMUM_PYTHON", above):
            with self.assertRaises(SystemExit) as caught:
                python.require_minimum_interpreter("test")
        message = str(caught.exception)
        self.assertIn("requires-python", message)
        self.assertIn(f"{above[0]}.{above[1]}", message)

    def test_entry_scripts_request_a_compatible_managed_interpreter(self):
        for name in ("snapshot.py", "analyze_file.py", "doc_review.py",
                     "mcp_server.py", "resolve_edges.py"):
            with self.subTest(entry=name):
                source = (SCRIPTS / name).read_text(encoding="utf-8")
                metadata = source.split("# /// script\n", 1)[1].split("# ///", 1)[0]
                config = tomllib.loads("\n".join(line.removeprefix("# ")
                                               for line in metadata.splitlines()))
                self.assertEqual(config["requires-python"], ">=3.12")


if __name__ == "__main__":
    unittest.main()
