"""TDD tests for Kotlin, C#, Vue/Svelte SFC, Tauri cross-language bridge, SQL AST semantics, and SCIP engine."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import import_resolution  # noqa: E402
import resolve_edges  # noqa: E402
import semantic_index  # noqa: E402
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from languages import (  # noqa: E402
    SUPPORTED_EXTENSIONS,
    SUPPORTED_LANGUAGES,
    _treesitter,
    detect_language,
    get_adapter,
)
from snapshot_store import open_snapshot  # noqa: E402
from read_manifest import read_manifest  # noqa: E402


def _encode_varint(value: int) -> bytes:
    out = bytearray()
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value & 0x7F)
    return bytes(out)


def _pb_field_varint(field_no: int, value: int) -> bytes:
    return _encode_varint((field_no << 3) | 0) + _encode_varint(value)


def _pb_field_bytes(field_no: int, payload: bytes) -> bytes:
    return _encode_varint((field_no << 3) | 2) + _encode_varint(len(payload)) + payload


def _pb_scip_occurrence(rng: list[int], symbol: str, roles: int) -> bytes:
    packed_range = b"".join(_encode_varint(x) for x in rng)
    return (
        _pb_field_bytes(1, packed_range)
        + _pb_field_bytes(2, symbol.encode("utf-8"))
        + (_pb_field_varint(3, roles) if roles else b"")
    )


def _pb_scip_document(relative_path: str, language: str, occurrences: list[bytes]) -> bytes:
    body = _pb_field_bytes(1, relative_path.encode("utf-8"))
    for occ in occurrences:
        body += _pb_field_bytes(2, occ)
    body += _pb_field_bytes(4, language.encode("utf-8"))
    return body


def _pb_scip_index(tool_name: str, tool_version: str, documents: list[bytes]) -> bytes:
    tool_info = _pb_field_bytes(1, tool_name.encode("utf-8")) + _pb_field_bytes(2, tool_version.encode("utf-8"))
    metadata = _pb_field_varint(1, 0) + _pb_field_bytes(2, tool_info)
    out = _pb_field_bytes(1, metadata)
    for doc in documents:
        out += _pb_field_bytes(2, doc)
    return out


class KotlinLanguageTests(unittest.TestCase):
    SOURCE = (
        "package demo.billing\n\n"
        "import demo.core.Ledger\n\n"
        "interface Payable {\n"
        "    fun pay(amount: Int): Boolean\n"
        "}\n\n"
        "class Invoice(val id: String) : Payable {\n"
        "    override fun pay(amount: Int): Boolean {\n"
        "        Ledger.record(amount)\n"
        "        return true\n"
        "    }\n"
        "}\n\n"
        "suspend fun processAll(items: List<Int>): Int {\n"
        "    return helper(items.size)\n"
        "}\n\n"
        "private fun helper(n: Int): Int = n + 1\n"
    )

    def test_kotlin_registration_and_tree_sitter_extraction(self):
        self.assertEqual(SUPPORTED_EXTENSIONS.get(".kt"), "kotlin")
        self.assertEqual(SUPPORTED_EXTENSIONS.get(".kts"), "kotlin")
        self.assertIn("kotlin", SUPPORTED_LANGUAGES)
        self.assertEqual(detect_language(Path("Invoice.kt")), "kotlin")
        self.assertEqual(snapshot.parser_profile(Path("Invoice.kt"))["language"], "kotlin")

        adapter = get_adapter("kotlin")
        result = adapter.parse(self.SOURCE, "src/Invoice.kt")
        self.assertEqual(result.language, "kotlin")
        classes = {c.name: c for c in result.classes}
        self.assertIn("Payable", classes)
        self.assertEqual(classes["Payable"].kind, "interface")
        self.assertIn("Invoice", classes)
        self.assertEqual(classes["Invoice"].bases, ["Payable"])
        self.assertIn("id", classes["Invoice"].class_variables)
        self.assertEqual([m.name for m in classes["Invoice"].methods], ["pay"])

        funcs = {f.name: f for f in result.functions}
        self.assertIn("processAll", funcs)
        self.assertTrue(funcs["processAll"].is_async)
        self.assertEqual(funcs["processAll"].visibility, "public")
        self.assertIn("helper", funcs)
        self.assertEqual(funcs["helper"].visibility, "private")
        self.assertIn("Invoice", result.exported_symbols)
        self.assertIn("processAll", result.exported_symbols)
        self.assertNotIn("helper", result.exported_symbols)
        self.assertIsNotNone(result.semantic)

    def test_kotlin_cross_file_semantic_resolution_and_no_grammar(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ktproj"
            (root / "src").mkdir(parents=True)
            (root / "src/Ledger.kt").write_text(
                "package demo.core\n\nfun record(amount: Int): Boolean {\n    return true\n}\n",
                encoding="utf-8",
            )
            (root / "src/Invoice.kt").write_text(
                "package demo.billing\n\nimport demo.core.record\n\nfun run(): Boolean {\n    return record(10)\n}\n",
                encoding="utf-8",
            )
            manifest = read_manifest(root)
            index = semantic_index.build_semantic_index(manifest)
            self.assertEqual(index["coverage"]["src/Invoice.kt"]["status"], "ast")
            calls = [r for r in index["references"] if r["file"] == "src/Invoice.kt" and r["kind"] == "call"]
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["resolution"], "resolved")
            self.assertTrue(calls[0]["target_id"].startswith("src/Ledger.kt::function@"))

        with mock.patch.object(_treesitter, "get_parser", return_value=None):
            unread = get_adapter("kotlin").parse(self.SOURCE, "src/Invoice.kt")
            self.assertEqual(unread.notes[0], "parser=none")
            self.assertEqual((unread.classes, unread.functions, unread.imports), ([], [], []))


class CSharpLanguageTests(unittest.TestCase):
    SOURCE = (
        "using System;\n"
        "using Demo.Core;\n\n"
        "namespace Demo.Billing\n"
        "{\n"
        "    public interface IPayable\n"
        "    {\n"
        "        bool Pay(int amount);\n"
        "    }\n\n"
        "    public class Invoice : IPayable\n"
        "    {\n"
        "        public const int MaxRetry = 3;\n"
        "        public string Id { get; set; }\n\n"
        "        public Invoice(string id) { Id = id; }\n\n"
        "        public async Task<bool> PayAsync(int amount)\n"
        "        {\n"
        "            return Ledger.Record(amount);\n"
        "        }\n\n"
        "        private int Helper(int x) => x + 1;\n"
        "    }\n"
        "}\n"
    )

    def test_csharp_registration_and_tree_sitter_extraction(self):
        self.assertEqual(SUPPORTED_EXTENSIONS.get(".cs"), "csharp")
        self.assertIn("csharp", SUPPORTED_LANGUAGES)
        self.assertEqual(detect_language(Path("Invoice.cs")), "csharp")
        self.assertEqual(snapshot.parser_profile(Path("Invoice.cs"))["language"], "csharp")

        adapter = get_adapter("csharp")
        result = adapter.parse(self.SOURCE, "src/Invoice.cs")
        self.assertEqual(result.language, "csharp")
        classes = {c.name: c for c in result.classes}
        self.assertIn("IPayable", classes)
        self.assertEqual(classes["IPayable"].kind, "interface")
        self.assertIn("Invoice", classes)
        self.assertEqual(classes["Invoice"].bases, ["IPayable"])
        self.assertIn("MaxRetry", classes["Invoice"].class_variables)
        self.assertIn("Id", classes["Invoice"].class_variables)
        methods = {m.name: m for m in classes["Invoice"].methods}
        self.assertIn("Invoice", methods)
        self.assertIn("PayAsync", methods)
        self.assertTrue(methods["PayAsync"].is_async)
        self.assertEqual(methods["PayAsync"].visibility, "public")
        self.assertEqual(methods["Helper"].visibility, "private")
        self.assertIsNotNone(result.semantic)

    def test_csharp_semantics_resolve_internal_methods_and_no_grammar(self):
        code = (
            "namespace Demo {\n"
            "  public class Service {\n"
            "    public int Execute(int v) { return Normalize(v); }\n"
            "    private int Normalize(int v) { return v + 1; }\n"
            "  }\n"
            "}\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "csproj"
            root.mkdir(parents=True)
            (root / "Service.cs").write_text(code, encoding="utf-8")
            manifest = read_manifest(root)
            index = semantic_index.build_semantic_index(manifest)
            self.assertEqual(index["coverage"]["Service.cs"]["status"], "ast")
            calls = [r for r in index["references"] if r["file"] == "Service.cs" and r["kind"] == "call"]
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["resolution"], "resolved")

        with mock.patch.object(_treesitter, "get_parser", return_value=None):
            unread = get_adapter("csharp").parse(self.SOURCE, "src/Invoice.cs")
            self.assertEqual(unread.notes[0], "parser=none")
            self.assertEqual((unread.classes, unread.functions, unread.imports), ([], [], []))


class SingleFileComponentTests(unittest.TestCase):
    VUE_SOURCE = (
        '<template>\n'
        '  <button @click="submit">{{ label }}</button>\n'
        '</template>\n'
        '<script setup lang="ts">\n'
        'import { formatLabel } from "./util";\n'
        'export function submit(value: string): string {\n'
        '  return formatLabel(value);\n'
        '}\n'
        '</script>\n'
        '<style scoped>\n'
        '.btn { color: red; }\n'
        '</style>\n'
    )

    SVELTE_SOURCE = (
        '<script lang="ts">\n'
        '  import { formatLabel } from "./util";\n'
        '  export function runSvelte(x: string): string {\n'
        '    return formatLabel(x);\n'
        '  }\n'
        '</script>\n'
        '<main><p>Hello</p></main>\n'
    )

    def test_vue_and_svelte_extract_exact_script_spans_and_resolve_imports(self):
        self.assertEqual(SUPPORTED_EXTENSIONS.get(".vue"), "vue")
        self.assertEqual(SUPPORTED_EXTENSIONS.get(".svelte"), "svelte")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "web"
            root.mkdir(parents=True)
            (root / "util.ts").write_text(
                "export function formatLabel(s: string): string { return s.trim(); }\n",
                encoding="utf-8",
            )
            (root / "Button.vue").write_text(self.VUE_SOURCE, encoding="utf-8")
            (root / "Panel.svelte").write_text(self.SVELTE_SOURCE, encoding="utf-8")

            manifest = read_manifest(root)
            self.assertEqual(manifest["files"]["Button.vue"]["status"], "parsed")
            self.assertEqual(manifest["files"]["Panel.svelte"]["status"], "parsed")
            self.assertIn("submit", manifest["files"]["Button.vue"]["symbols"])
            self.assertEqual(manifest["files"]["Button.vue"]["symbols"]["submit"]["start"], 6)

            index = semantic_index.build_semantic_index(manifest)
            self.assertEqual(index["coverage"]["Button.vue"]["status"], "ast")
            self.assertEqual(index["coverage"]["Panel.svelte"]["status"], "ast")

            # The script's call, then the template's handler, which Vue calls on the event.
            vue_calls = sorted((r for r in index["references"] if r["file"] == "Button.vue" and r["kind"] == "call"),
                               key=lambda r: r["span"][0], reverse=True)
            self.assertEqual([r["parts"] for r in vue_calls], [["formatLabel"], ["submit"]])
            self.assertEqual({r["resolution"] for r in vue_calls}, {"resolved"})
            self.assertTrue(vue_calls[0]["target_id"].startswith("util.ts::function@"))
            self.assertTrue(vue_calls[1]["target_id"].startswith("Button.vue::function@6:"))

            svelte_calls = [r for r in index["references"] if r["file"] == "Panel.svelte" and r["kind"] == "call"]
            self.assertEqual(len(svelte_calls), 1)
            self.assertEqual(svelte_calls[0]["resolution"], "resolved")
            self.assertTrue(svelte_calls[0]["target_id"].startswith("util.ts::function@"))

    # The frontmatter (TypeScript) imports a component and a module, the `<script>` (TypeScript too) another module.
    ASTRO_SOURCE = (
        '---\n'
        'import Header from "./Header.astro";\n'
        'import { formatLabel } from "./util";\n'
        'const title: string = formatLabel("Home");\n'
        '---\n'
        '<Header title={title} />\n'
        '<script>\n'
        '  import { track } from "./track";\n'
        '  track("home");\n'
        '</script>\n'
        '<style>\n'
        '.hero { color: red; }\n'
        '</style>\n'
    )

    def test_astro_frontmatter_and_script_are_read_at_their_own_positions(self):
        self.assertEqual(SUPPORTED_EXTENSIONS.get(".astro"), "astro")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir(parents=True)
            (root / "util.ts").write_text("export function formatLabel(s: string): string { return s; }\n",
                                          encoding="utf-8")
            (root / "track.ts").write_text("export function track(event: string): void {}\n", encoding="utf-8")
            (root / "Header.astro").write_text("---\nconst { title } = Astro.props;\n---\n<h1>{title}</h1>\n",
                                               encoding="utf-8")
            (root / "Page.astro").write_text(self.ASTRO_SOURCE, encoding="utf-8")
            lines = self.ASTRO_SOURCE.split("\n")

            manifest = read_manifest(root)
            page = manifest["files"]["Page.astro"]
            self.assertEqual(page["language"], "astro")
            self.assertEqual(page["status"], "parsed")
            self.assertEqual(page["imports"], ["./Header.astro", "./track", "./util"])
            self.assertEqual(manifest["files"]["Header.astro"]["status"], "parsed")
            # The style block's rule is still a symbol at its line.
            self.assertEqual(page["symbols"][".hero"]["start"], 12)

            # Each import where the file writes it.
            imports = {item["local"]: item["span"] for item in page["semantic"]["imports"]}
            self.assertEqual({name: span[0] for name, span in imports.items()},
                             {"Header": 2, "formatLabel": 3, "track": 8})

            # The import of a component names its file, the one of a module its `.ts`.
            resolved = import_resolution.resolved_imports(manifest)["Page.astro"]
            self.assertEqual(resolved["./Header.astro"], ["Header.astro"])
            self.assertEqual(resolved["./util"], ["util.ts"])
            self.assertEqual(resolved["./track"], ["track.ts"])

            index = semantic_index.build_semantic_index(manifest)
            self.assertEqual(index["coverage"]["Page.astro"]["status"], "ast")
            calls = {r["parts"][0]: r for r in index["references"] if r["file"] == "Page.astro" and r["kind"] == "call"}
            self.assertEqual(set(calls), {"formatLabel", "track"})
            self.assertTrue(calls["formatLabel"]["target_id"].startswith("util.ts::function@"))
            self.assertTrue(calls["track"]["target_id"].startswith("track.ts::function@"))
            for name, ref in calls.items():  # the span is the file's own, line and column
                line, column = ref["span"][0], ref["span"][1]
                self.assertEqual(lines[line - 1][column:column + len(name)], name)

    def test_astro_without_frontmatter_keeps_its_styles_and_has_no_code(self):
        source = '<div class="x">hi</div>\n<style>\n.x { color: blue; }\n</style>\n'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir(parents=True)
            (root / "Plain.astro").write_text(source, encoding="utf-8")
            entry = read_manifest(root)["files"]["Plain.astro"]
            self.assertEqual(entry["status"], "parsed")
            self.assertEqual(entry["imports"], [])
            self.assertEqual(entry["symbols"][".x"]["start"], 3)

    def test_an_astro_fence_after_an_element_is_not_frontmatter(self):
        """The compiler opens the frontmatter at a `---` before any element (withastro/compiler
        internal/token.go: "If we see an element before "---", ignore any future "---""): after one it is text."""
        source = '<div>first</div>\n---\nimport Header from "./Header.astro";\n---\n'
        result = get_adapter("astro").parse(source, "Late.astro")
        self.assertEqual(result.imports, [])


class TauriCrossLanguageBridgeTests(unittest.TestCase):
    def test_reopened_button_card_stops_at_the_rust_command_without_an_effect(self):
        import flow_paths

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "app"
            (root / "src").mkdir(parents=True)
            (root / "src-tauri/src").mkdir(parents=True)
            (root / "src/view.tsx").write_text(
                'import {invoke} from "@tauri-apps/api/core";\n'
                'function save() { return invoke("persist"); }\n'
                'export function View() { return <button onClick={save}>Salva profilo</button>; }\n')
            (root / "src-tauri/src/main.rs").write_text(
                '#[tauri::command]\nfn persist() {}\n'
                'fn main() { tauri::Builder::default().invoke_handler(tauri::generate_handler![persist]).run(tauri::generate_context!()); }\n')
            manifest = Path(tmp) / "manifest.sqlite"
            snapshot.read_project(root, manifest)
            button = next(c for c in flow_paths.page(manifest, [])["cards"] if c.get("label") == "Salva profilo")
            self.assertEqual((button["event"], button["handler"], button["site"]),
                             ("click", "src/view.tsx::save", "src/view.tsx:3"))
            path = flow_paths.page(manifest, [], card_id=button["card_id"])
            command, stop = path["steps"]
            self.assertEqual((command["from"], command["to"], command["resolver"], command["site"]),
                             (button["handler"], "src-tauri/src/main.rs::persist", "tauri-invoke", "src/view.tsx:2"))
            self.assertEqual((stop["from"], stop["site"], stop["end"], stop["parent"]),
                             (command["to"], "src-tauri/src/main.rs:2", "lacuna", command["n"]))
            decision = {"card_id": button["card_id"], "disposition": "unresolved", "reason": stop["reason"]}
            self.assertEqual(flow_paths.record(manifest, [], decision)["status"], "unresolved")
            with mock.patch.object(flow_paths, "_steps", side_effect=AssertionError("path walked twice")):
                reopened = flow_paths.page(manifest, [], card_id=button["card_id"])
            self.assertEqual(reopened["steps"], path["steps"])
            self.assertEqual(reopened["review"]["reason"], stop["reason"])

    def test_flow_links_keep_the_registered_command_and_locate_each_missing_proof(self):
        import edge_store
        import flows

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "app"
            (root / "src").mkdir(parents=True)
            (root / "src-tauri/src").mkdir(parents=True)
            (root / "src/view.ts").write_text(
                'import {invoke as native} from "@tauri-apps/api/core";\n'
                'export function save() { return native("persist"); }\n'
                'export function expired() { return native("retired"); }\n'
                'export function choose(name: string) { return native(name); }\n'
                'export function other(native: any) { return native("persist"); }\n')
            (root / "src-tauri/src/main.rs").write_text(
                "#[tauri::command]\nfn persist() {}\n"
                "#[tauri::command]\nfn retired() {}\n"
                "fn main() { tauri::Builder::default().invoke_handler(tauri::generate_handler![persist]).run(tauri::generate_context!()); }\n")
            manifest = Path(tmp) / "manifest.sqlite"
            snapshot.read_project(root, manifest)
            # SCIP identifies the TypeScript SDK function. The exact registration identifies the next hop.
            with open_snapshot(manifest) as store:
                row = store.connection.execute(
                    "SELECT id,caller,c0 FROM sem_references WHERE file='src/view.ts' AND kind='call' AND l0=2"
                ).fetchone()
                binding = edge_store.store_binding(store, manifest, store.metadata["parser_fingerprint"], {}, {})
            edge_store.write_edge_store(edge_store.default_edge_store(manifest), [
                {"reference_id": row[0], "caller": row[1], "l0": 2, "c0": row[2], "file": "src/view.ts",
                 "language": "typescript", "kind": "call", "verdict": "external", "confidence": "confirmed",
                 "resolver": "scip-typescript", "symbol": "tauri-api-invoke",
                 "external": {"manager": "npm", "package": "@tauri-apps/api", "version": "2"},
                 "payload": {}}], binding)
            with mock.patch.object(flows, "link_facts", wraps=flows.link_facts) as build:
                links = flows.cached_links(manifest, [])
                self.assertEqual(build.call_count, 1)
                self.assertEqual(flows.cached_links(manifest, []), links)
                self.assertEqual(build.call_count, 1)
            command_edges = [e for e in links["edges"] if e["to"].startswith("src-tauri/")]
            self.assertEqual([(e["from"], e["to"], e["site"]) for e in command_edges],
                             [("src/view.ts::save", "src-tauri/src/main.rs::persist", "src/view.ts:2")])
            self.assertEqual((command_edges[0]["origin"], command_edges[0]["resolver"]), ("dedotto", "tauri-invoke"))
            self.assertEqual([(g["site"], g["symbol"]) for g in links["gaps"]], [
                ("src/view.ts:3", "src/view.ts::expired"), ("src/view.ts:4", "src/view.ts::choose")])
            self.assertIn("retired", links["gaps"][0]["reason"])
            self.assertIn("literal", links["gaps"][1]["reason"])
            self.assertFalse(flows.trace(links, "src/view.ts::choose", "from")["complete"])

    def test_ts_invoke_resolves_to_rust_tauri_command_across_languages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tauri-app"
            (root / "src").mkdir(parents=True)
            (root / "src-tauri/src").mkdir(parents=True)

            (root / "src/App.tsx").write_text(
                'import { invoke } from "@tauri-apps/api/core";\n\n'
                'function other(invoke: (x: string) => unknown) { return invoke("load_user_profile"); }\n'
                'export async function refreshUser(id: number) {\n'
                '  return await invoke("load_user_profile", { id });\n'
                '}\n',
                encoding="utf-8",
            )
            (root / "src-tauri/src/commands.rs").write_text(
                '#[tauri::command]\n'
                'async fn load_user_profile(id: i64) -> String {\n'
                '    format!("user:{}", id)\n'
                '}\n',
                encoding="utf-8",
            )
            (root / "src-tauri/src/main.rs").write_text(
                "mod commands; fn main() { tauri::Builder::default().invoke_handler("
                "tauri::generate_handler![commands::load_user_profile]).run(tauri::generate_context!()); }\n", encoding="utf-8")

            manifest = read_manifest(root)
            index = semantic_index.build_semantic_index(manifest)
            app_calls = [
                r for r in index["references"]
                if r["file"] == "src/App.tsx" and r["kind"] == "call" and r["resolution"] == "resolved"
            ]
            self.assertEqual(len(app_calls), 1)
            self.assertTrue(
                app_calls[0]["target_id"].startswith("src-tauri/src/commands.rs::function@"),
                app_calls[0],
            )
            self.assertEqual(app_calls[0]["span"][0], 5)

            db_path = root / "manifest.sqlite"
            snapshot.read_project(root, db_path)
            with open_snapshot(db_path) as store:
                impact = semantic_store.build_edit_impact(store, ["src-tauri/src/commands.rs::load_user_profile"])
                callers = impact["targets"][0]["callers"]["listed"]
                self.assertEqual([c["file"] for c in callers], ["src/App.tsx"])

    def test_invoke_requires_an_attributed_registered_command_in_the_calling_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "checkout"
            def write(file, source):
                path = root / file
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")
            register = "fn main() { tauri::Builder::default().invoke_handler(tauri::generate_handler![save]).run(tauri::generate_context!()); }\n"
            for app, rust in {"one": "#[tauri::command]\nfn save() {}\n",
                              "two": "#[tauri::command]\nfn save() {}\n" + register,
                              "three": "pub fn save() {}\n" + register}.items():
                write(f"{app}/src/ui.ts", 'import {invoke} from "@tauri-apps/api/core";\n'
                                        'export function ui() { return invoke("save"); }\n')
                write(f"{app}/src-tauri/src/main.rs", rust)
            write("tools/helper.rs", "pub fn save() {}\n")
            old, new = Path(tmp) / "before.sqlite", Path(tmp) / "after.sqlite"
            snapshot.read_project(root, old)
            def targets(path):
                with open_snapshot(path) as store:
                    return {file: target for file, target in store.connection.execute(
                        "SELECT file,target_id FROM sem_references WHERE kind='call' AND file LIKE '%.ts'")}
            self.assertEqual(targets(old), {"one/src/ui.ts": None, "two/src/ui.ts": "two/src-tauri/src/main.rs::function@2:0",
                                            "three/src/ui.ts": None})
            write("one/src-tauri/src/main.rs", "#[tauri::command]\nfn save() {}\n" + register)
            write("two/src-tauri/src/main.rs", "#[tauri::command]\nfn save() {}\n")
            with open_snapshot(old) as previous:
                snapshot.read_project(root, new, previous=previous)
            self.assertEqual(targets(new), {"one/src/ui.ts": "one/src-tauri/src/main.rs::function@2:0",
                                            "two/src/ui.ts": None, "three/src/ui.ts": None})


class SqlAstAndScipEngineTests(unittest.TestCase):
    def test_sql_adapter_populates_semantic_declarations_and_table_references(self):
        sql_code = (
            "CREATE TABLE orders (id INT PRIMARY KEY, user_id INT);\n"
            "CREATE TABLE users (id INT PRIMARY KEY, email TEXT);\n"
            "CREATE VIEW active_orders AS\n"
            "  SELECT o.id, u.email FROM orders o JOIN users u ON o.user_id = u.id;\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sqlproj"
            root.mkdir(parents=True)
            (root / "schema.sql").write_text(sql_code, encoding="utf-8")
            manifest = read_manifest(root)
            index = semantic_index.build_semantic_index(manifest)
            self.assertEqual(index["coverage"]["schema.sql"]["status"], "ast")
            view_Symbols = [c for c in get_adapter("sql").parse(sql_code, "schema.sql").classes if c.name == "active_orders"]
            self.assertEqual(len(view_Symbols), 1)
            refs = [
                r for r in index["references"]
                if r["file"] == "schema.sql" and r["resolution"] == "resolved"
            ]
            resolved_targets = {index["declarations"][r["target_id"]]["name"] for r in refs}
            self.assertEqual(resolved_targets, {"orders", "users"})

    def test_sql_optional_sqlglot_backend_extracts_cte_and_dml_dependencies(self):
        fake_sqlglot = mock.MagicMock()

        class FakeTable:
            def __init__(self, name):
                self.name = name
                self.db = ""

        class FakeCTE:
            def __init__(self, alias):
                self.alias = alias

        class FakeAst:
            def find_all(self, cls):
                if cls is FakeTable:
                    return [FakeTable("orders"), FakeTable("recent_cte")]
                if cls is FakeCTE:
                    return [FakeCTE("recent_cte")]
                return []

        fake_exp = mock.MagicMock()
        fake_exp.Table = FakeTable
        fake_exp.CTE = FakeCTE
        fake_sqlglot.exp = fake_exp
        fake_sqlglot.parse.return_value = [FakeAst()]

        with mock.patch.dict(sys.modules, {"sqlglot": fake_sqlglot, "sqlglot.exp": fake_exp}):
            result = get_adapter("sql").parse(
                "CREATE VIEW v AS WITH recent_cte AS (SELECT * FROM orders) SELECT * FROM recent_cte;\n",
                "view.sql",
            )
            self.assertTrue(any("sqlglot" in n for n in result.notes))

    def test_resolve_edges_scip_engine_resolves_multi_language_calls_from_protobuf_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tsproj"
            root.mkdir(parents=True)
            # `service.execute()` on an unannotated parameter is unresolved lexically ("unknown-receiver")
            (root / "caller.ts").write_text(
                "export function run(service: any) {\n"
                "  return service.execute();\n"
                "}\n",
                encoding="utf-8",
            )
            (root / "worker.ts").write_text(
                "export class Worker {\n"
                "  execute() {\n"
                "    return 42;\n"
                "  }\n"
                "}\n",
                encoding="utf-8",
            )
            manifest = root.parent / "manifest.sqlite"
            snapshot.read_project(root, manifest)

            sym = "scip-typescript npm pkg 1.0.0 worker.ts/Worker#execute()."
            doc_worker = _pb_scip_document(
                "worker.ts",
                "typescript",
                # line 1 (0-based) = line 2 (`  execute() {`), char 2..9
                [_pb_scip_occurrence([1, 2, 1, 9], sym, 1)],
            )
            doc_caller = _pb_scip_document(
                "caller.ts",
                "typescript",
                # line 1 (0-based) = line 2 (`  return service.execute();`), char 17..24 (`execute`)
                [_pb_scip_occurrence([1, 17, 1, 24], sym, 0)],
            )
            scip_bytes = _pb_scip_index("scip-typescript", "0.3.14", [doc_worker, doc_caller])
            scip_path = root / "index.scip"
            scip_path.write_bytes(scip_bytes)

            edges_out = root.parent / "engine-edges.sqlite"
            engine = resolve_edges.ScipEngine(root, [scip_path])
            report = resolve_edges.resolve_edges(
                manifest,
                engine=engine,
                limit=None,
                stride=1,
                out=edges_out,
            )
            self.assertTrue(report["available"], report)
            self.assertEqual(report["confirmed_edges"], 1)
            with open_snapshot(manifest) as store:
                edges, binding, reason = resolve_edges.read_edge_store(edges_out, store)
            self.assertIsNone(reason)
            self.assertEqual(len(edges), 1)
            self.assertEqual(edges[0]["resolver"], "scip:scip-typescript@0.3.14")
            self.assertEqual(edges[0]["payload"]["detail"], "edge-call")
            self.assertTrue(
                edges[0]["target_id"].startswith(("worker.ts::method@", "worker.ts::function@")),
                edges[0]["target_id"],
            )


if __name__ == "__main__":
    unittest.main()
