"""Exercise Code Mode through the actual MCP stdio transport and map service."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_codebase_map_mcp_wire import CodebaseMapWireFixture, HAS_SDK, SERVER


DENO = os.environ.get("DAODAN_TEST_DENO") or shutil.which("deno")


@unittest.skipUnless(HAS_SDK and DENO, "requires actual MCP SDK and Deno")
class CodeModeStartupTests(unittest.TestCase):
    def test_invalid_write_grants_fail_at_startup(self):
        with tempfile.TemporaryDirectory() as project:
            for name in ("*", "missing_operation", "codebase_map_scope"):
                with self.subTest(name=name):
                    result = subprocess.run(
                        [sys.executable, str(SERVER), "--project", project,
                         "--code-mode", "--deno", DENO, "--code-mode-allow-write", name],
                        input="", capture_output=True, text=True, timeout=10)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("exact native mutation names", result.stderr)

    def test_grants_cannot_silently_change_native_mode(self):
        result = subprocess.run(
            [sys.executable, str(SERVER), "--code-mode-allow-write", "codebase_map_create_run"],
            input="", capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("require --code-mode", result.stderr)


@unittest.skipUnless(HAS_SDK and DENO, "requires actual MCP SDK and Deno")
class CodeModeWireTests(CodebaseMapWireFixture):
    def start(self, *options):
        return super().start("--code-mode", "--deno", DENO, *options)

    def execute(self, code, *names):
        return self.call("execute", {"code": code, "tools": list(names)})

    def test_two_tool_surface_and_progressive_discovery(self):
        catalog = self.request("tools/list", {})["result"]["tools"]
        self.assertEqual({tool["name"] for tool in catalog}, {"search", "execute"})
        self.assertTrue(all(tool["annotations"]["readOnlyHint"] for tool in catalog))
        result = self.data(self.call("search", {"code":
            'async () => catalog.filter(t => t.name === "codebase_map_read")'}))
        self.assertEqual(len(result["value"]), 1)
        self.assertEqual(result["value"][0]["name"], "codebase_map_read")
        self.assertIn("run_id", result["value"][0]["inputSchema"]["required"])
        self.assertEqual(result["calls"], [])

    def test_composition_returns_selected_value_and_receipts(self):
        result = self.data(self.execute('''async () => {
            const scope = await tools.codebase_map_scope({target: "src"});
            const runs = await tools.codebase_map_runs({});
            return {files: scope.files, root: scope.project_root};
        }''', "codebase_map_scope", "codebase_map_runs"))
        self.assertEqual(result["value"]["files"], 1)
        self.assertEqual(Path(result["value"]["root"]), self.project)
        self.assertEqual(len(result["calls"]), 2)
        self.assertNotIn("items", result)

    def test_read_only_default_denies_mutation_before_dispatch(self):
        denied = self.execute('''async () => await tools.codebase_map_create_run({
            target: "src", run_id: "unauthorized"})''', "codebase_map_create_run")
        self.assertTrue(denied.get("isError"), denied)
        self.assertFalse((self.project / ".codebase-map/runs/unauthorized").exists())
        descriptors = self.data(self.call("search", {"code":
            'async () => catalog.map(t => t.name)'}))["value"]
        self.assertNotIn("codebase_map_create_run", descriptors)

    def test_granted_creation_reuses_validation_and_verified_source_reading(self):
        self.close()
        self.start("--code-mode-allow-write", "codebase_map_create_run")
        catalog = self.request("tools/list", {})["result"]["tools"]
        execute = next(item for item in catalog if item["name"] == "execute")
        self.assertFalse(execute["annotations"]["readOnlyHint"])
        invalid = self.execute('''async () => await tools.codebase_map_create_run({
            target: "src", run_id: "bad-format", format: "pickle"})''', "codebase_map_create_run")
        self.assertTrue(invalid.get("isError"))
        self.assertFalse((self.project / ".codebase-map/runs/bad-format").exists())
        result = self.data(self.execute('''async () => {
            const run = await tools.codebase_map_create_run({target: "src", run_id: "composed"});
            const outline = await tools.codebase_map_outline({run_id: run.run_id});
            const source = await tools.codebase_map_read({run_id: run.run_id,
                requests: [{path: outline.items[0].path, symbols: ["greet"]}]});
            return source.files[0].blocks.map(block => block.source);
        }''', "codebase_map_create_run", "codebase_map_outline", "codebase_map_read"))
        self.assertTrue(any("def greet" in item for item in result["value"]))
        self.assertEqual(len(result["calls"]), 3)

    def test_path_confinement_and_failed_publication_keep_native_behavior(self):
        escaped = self.execute('async () => await tools.codebase_map_scope({target: "../"})',
                               "codebase_map_scope")
        self.assertTrue(escaped.get("isError"))
        self.assertIn("repository-relative", escaped["content"][0]["text"])
        self.close()
        self.start("--code-mode-allow-write", "codebase_map_create_run",
                   "--code-mode-allow-write", "codebase_map_publish")
        publication = self.execute('''async () => {
            await tools.codebase_map_create_run({target: "src", run_id: "incomplete"});
            return await tools.codebase_map_publish({run_id: "incomplete"});
        }''', "codebase_map_create_run", "codebase_map_publish")
        self.assertTrue(publication.get("isError"))
        self.assertIn("Publication refused", publication["content"][0]["text"])
        self.assertIn("admitted calls", publication["content"][0]["text"])
        self.assertFalse((self.project / ".codebase-map/07-final-report.md").exists())

    def test_caught_validation_error_is_visible_in_receipts(self):
        result = self.data(self.execute('''async () => {
            try { await tools.codebase_map_status({}); } catch (_) {}
            return "handled";
        }''', "codebase_map_status"))
        self.assertFalse(result["calls"][0]["ok"])

    def test_invalid_unicode_keeps_completed_mutation_visible_on_the_wire(self):
        self.close()
        self.start("--code-mode-allow-write", "codebase_map_create_run")
        result = self.execute(r'''async () => {
            await tools.codebase_map_create_run({target: "src", run_id: "unicode-result"});
            return "\ud800";
        }''', "codebase_map_create_run")
        self.assertTrue(result.get("isError"))
        self.assertIn("invalid JSON value", result["content"][0]["text"])
        self.assertIn('"ok": true', result["content"][0]["text"])
        self.assertTrue((self.project / ".codebase-map/runs/unicode-result/state.json").is_file())

    def test_discovery_has_no_operation_access(self):
        result = self.call("search", {"code":
            'async () => await tools.codebase_map_scope({})'})
        self.assertTrue(result.get("isError"))


if __name__ == "__main__":
    unittest.main()
