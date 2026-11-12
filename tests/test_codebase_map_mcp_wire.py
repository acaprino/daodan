"""Exercise the real SDK stdio transport when its runtime dependency is available.

Run with the server's SDK environment; the default stdlib suite records a skip
when MCP is absent. These are protocol tests, not installed-host probes.
"""

import importlib.util
import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path


SERVER = (Path(__file__).resolve().parents[1] /
          "plugins/codebase-map/skills/map/scripts/mcp_server.py")
HAS_SDK = importlib.util.find_spec("mcp") is not None


@unittest.skipUnless(HAS_SDK, "requires the actual MCP SDK runtime")
class CodebaseMapWireTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-mcp-wire-")
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        (self.project / "src").mkdir()
        self.source = self.project / "src/service.py"
        self.source.write_text("def greet(name):\n    return 'Hello ' + name\n", encoding="utf-8")
        self.notifications = []
        self.sequence = 0
        self.start()

    def start(self, *options):
        self.messages = queue.Queue()
        self.diagnostics = []
        self.process = subprocess.Popen(
            [sys.executable, "-u", str(SERVER), "--project", str(self.project), *options],
            cwd=self.project, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
        )
        self.addCleanup(self.close)
        stream = self.process.stdout

        def collect():
            for line in stream:
                try:
                    self.messages.put(json.loads(line))
                except ValueError:
                    self.messages.put({"invalid_stdout": line})
            self.messages.put({"eof": True})

        self.reader = threading.Thread(target=collect, daemon=True)
        self.reader.start()
        errors = self.process.stderr
        diagnostics = self.diagnostics
        self.error_reader = threading.Thread(
            target=lambda: diagnostics.extend(iter(errors.readline, "")), daemon=True,
        )
        self.error_reader.start()
        initialized = self.request("initialize", {
            "protocolVersion": "2025-11-25", "capabilities": {},
            "clientInfo": {"name": "daodan-wire-test", "version": "1.0"},
        })
        self.assertEqual(initialized["result"]["serverInfo"]["name"], "codebase-map")
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def close(self):
        process = getattr(self, "process", None)
        if process is None:
            return
        self.process = None
        if process.poll() is None:
            process.stdin.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream and not stream.closed:
                stream.close()
        self.reader.join(timeout=2)
        self.error_reader.join(timeout=2)

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method, params):
        self.sequence += 1
        identity = self.sequence
        self.send({"jsonrpc": "2.0", "id": identity, "method": method, "params": params})
        while True:
            try:
                message = self.messages.get(timeout=30)
            except queue.Empty:
                self.fail(f"No MCP reply for {method}; process status {self.process.poll()}")
            self.assertNotIn("invalid_stdout", message, message)
            if message.get("eof"):
                diagnostic = "".join(self.diagnostics)
                self.fail(f"Server closed before {method}: {diagnostic}")
            if message.get("id") == identity:
                return message
            self.notifications.append(message)

    def call(self, name, arguments, token=None):
        params = {"name": name, "arguments": arguments}
        if token is not None:
            params["_meta"] = {"progressToken": token}
        reply = self.request("tools/call", params)
        self.assertNotIn("error", reply, reply)
        return reply["result"]

    def data(self, result):
        self.assertFalse(result.get("isError", False),
                         f"{result}; server diagnostics: {''.join(self.diagnostics)[-5000:]}")
        if "structuredContent" in result:
            return result["structuredContent"]
        return json.loads(result["content"][0]["text"])

    def test_stdin_eof_stops_server_cleanly(self):
        self.process.stdin.close()
        self.assertEqual(self.process.wait(timeout=10), 0)

    def test_ui_tool_starts_one_explorer_that_answers_with_the_runs(self):
        import http.client
        from urllib.parse import urlsplit
        first = self.data(self.call("codebase_map_ui", {}))
        self.assertEqual(self.data(self.call("codebase_map_ui", {})), first)
        address = urlsplit(first["url"])
        self.assertEqual(address.hostname, "127.0.0.1")
        token = address.query.removeprefix("token=")
        self.assertGreater(len(token), 20)
        for header, status in (({}, 403), ({"X-Daodan-Token": token}, 200)):
            connection = http.client.HTTPConnection(address.hostname, address.port, timeout=10)
            connection.request("GET", "/api/runs", headers=header)
            response = connection.getresponse()
            self.assertEqual(response.status, status)
            if status == 200:
                self.assertIn("runs", json.loads(response.read()))
            connection.close()

    def test_real_tool_catalog_exposes_typed_tools_without_context(self):
        catalog = self.request("tools/list", {})["result"]["tools"]
        by_name = {tool["name"]: tool for tool in catalog}
        for name in ("scope", "create_run", "runs", "status", "outline", "graph", "read", "search", "index",
                     "diff", "artifact", "checkpoint", "events", "resume", "stop", "publish", "ui"):
            self.assertIn("codebase_map_" + name, by_name)
        search = by_name["codebase_map_search"]
        self.assertTrue(search["annotations"]["readOnlyHint"])
        self.assertEqual(set(search["inputSchema"]["required"]), {"run_id", "query"})
        self.assertNotIn("embedding_result", search["inputSchema"]["properties"])
        self.assertEqual(search["inputSchema"]["properties"]["limit"]["default"], 20)
        self.assertFalse(by_name["codebase_map_index"]["annotations"]["readOnlyHint"])
        for tool in catalog:
            properties = tool["inputSchema"].get("properties", {})
            self.assertNotIn("ctx", properties)
            self.assertNotIn("project_root", properties)
        self.assertIn("run_id", by_name["codebase_map_status"]["inputSchema"]["required"])
        format = by_name["codebase_map_create_run"]["inputSchema"]["properties"]["format"]
        self.assertEqual(format["default"], "sqlite")
        self.assertEqual(set(format["enum"]), {"sqlite", "json"})
        context = by_name['codebase_map_context']
        self.assertFalse(context['annotations']['readOnlyHint'])
        self.assertTrue({'run_id', 'request', 'recipient'} <= set(context['inputSchema']['required']))

    def test_context_writes_bounded_packet_over_real_transport(self):
        self.data(self.call('codebase_map_create_run', {'target': 'src', 'run_id': 'context-wire', 'engine': False}))
        request = {'schema': 'daodan/context-request/v1', 'task_id': 'wire-context',
            'intent': 'analysis', 'query': '', 'read_boundary': ['.'], 'write_boundary': [],
            'anchors': [{'entity_id': 'service.py::greet'}], 'base': None, 'candidate': None,
            'diff': [], 'proposed_edits': [], 'mandatory_requirements': [], 'required_gates': [],
            'budget': {'max_candidates': 100, 'max_edges': 1000, 'max_rounds': 100,
                'max_seconds': 120, 'max_input_tokens': 100000, 'max_output_tokens': 100000},
            'policy_version': 'scope-v1'}
        result = self.data(self.call('codebase_map_context', {'run_id': 'context-wire', 'request': request,
            'recipient': {'id': 'wire-host', 'available_tokens': 100000, 'reserve_tokens': 1000,
                          'max_chars': 100000, 'max_evaluations': 100}}))
        self.assertEqual(result['status'], 'ready')
        self.assertNotIn('input', result)
        packet = json.loads(Path(result['path']).read_text(encoding='utf8'))
        self.assertIn("return 'Hello ' + name", packet['input'])
        self.assertFalse(packet['budget']['dispatch_verified'])

    def test_json_requires_explicit_format_and_invalid_format_is_a_tool_error(self):
        run = self.data(self.call("codebase_map_create_run",
                                 {"target": "src", "run_id": "explicit-json", "format": "json", "engine": False}))
        self.assertEqual(run["state"]["snapshot"]["format"], "json")
        self.assertTrue(self.call("codebase_map_create_run",
                                 {"target": "src", "run_id": "invalid", "format": "pickle"}).get("isError"))

    def test_engine_parameters_and_coverage_cross_the_real_transport(self):
        self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "engine-wire", "engine": False}))
        graph = self.data(self.call("codebase_map_graph", {
            "run_id": "engine-wire", "engine_store": "snapshot/engine-edges.sqlite"}))
        self.assertEqual(graph["edge_view"]["coverage"]["status"], "missing_store")
        impact = self.data(self.call("codebase_map_edit_impact", {
            "run_id": "engine-wire", "targets": ["src/service.py::greet"],
            "engine_store": "snapshot/engine-edges.sqlite"}))
        self.assertEqual(impact["freshness_basis"], "lexical")
        drift = self.data(self.call("codebase_map_stale_callers", {
            "run_id": "engine-wire", "base_run_id": "engine-wire",
            "base_engine_store": "snapshot/engine-edges.sqlite",
            "candidate_engine_store": "snapshot/engine-edges.sqlite"}))
        self.assertEqual(drift["engine_callee_drift"]["status"], "unavailable")
        self.assertTrue(self.call("codebase_map_graph", {
            "run_id": "engine-wire", "engine_store": "../escape.sqlite"}).get("isError"))

    def test_run_creation_starts_the_engine_pass_through_actual_transport(self):
        created = self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "engine-live"}))
        state = created["engine"]
        self.assertIn(state["state"], {"running", "unavailable", "fresh"}, state)
        # Wait for the pass so no child still holds the run when the test cleans up.
        deadline = time.monotonic() + 120
        while state["state"] == "running" and time.monotonic() < deadline:
            time.sleep(1)
            state = self.data(self.call("codebase_map_status", {"run_id": "engine-live"}))["engine"]
        self.assertIn(state["state"], {"fresh", "unavailable"}, state)
        self.assertIn("resolved_ratio", state["resolution"])

    def test_a_typescript_pass_resolves_what_the_lexical_resolver_cannot(self):
        (self.project / "web").mkdir()
        (self.project / "web/tool.ts").write_text(
            "export class Tool {\n  run(): number { return 1; }\n}\n", encoding="utf-8")
        (self.project / "web/use.ts").write_text(
            "import { Tool } from './tool';\nexport function go(tool: Tool) {\n  return tool.run();\n}\n",
            encoding="utf-8")
        state = self.data(self.call("codebase_map_create_run", {"target": "web", "run_id": "ts-live"}))["engine"]
        # The first pass on a machine installs typescript-language-server.
        deadline = time.monotonic() + 300
        while state["state"] == "running" and time.monotonic() < deadline:
            time.sleep(1)
            state = self.data(self.call("codebase_map_status", {"run_id": "ts-live"}))["engine"]
        language = state["languages"]["typescript"]
        if language["state"] == "unavailable":
            self.skipTest(language.get("install"))
        self.assertEqual(language["state"], "fresh", state)
        self.assertTrue(language["engine"].startswith("typescript-language-server@"), language)
        typescript = state["resolution"]["by_language"]["typescript"]
        self.assertEqual((typescript["resolved"], typescript["resolvable"]), (1, 1), typescript)

    def test_a_java_pass_resolves_a_method_on_a_typed_receiver(self):
        package = self.project / "jvm/src/main/java/demo"
        package.mkdir(parents=True)
        (package / "Tool.java").write_text(
            "package demo;\n\npublic class Tool {\n  public int run() { return 1; }\n}\n", encoding="utf-8")
        (package / "Use.java").write_text(
            "package demo;\n\npublic class Use {\n  int go(Tool tool) { return tool.run(); }\n}\n", encoding="utf-8")
        state = self.data(self.call("codebase_map_create_run", {"target": "jvm", "run_id": "java-live"}))["engine"]
        # The first pass on a machine installs Eclipse JDT LS with its Java runtime.
        deadline = time.monotonic() + 420
        while state["state"] == "running" and time.monotonic() < deadline:
            time.sleep(1)
            state = self.data(self.call("codebase_map_status", {"run_id": "java-live"}))["engine"]
        language = state["languages"]["java"]
        if language["state"] == "unavailable":
            self.skipTest(language.get("install"))
        self.assertEqual(language["state"], "fresh", state)
        self.assertTrue(language["engine"].startswith("eclipse-jdtls@"), language)
        java = state["resolution"]["by_language"]["java"]
        self.assertEqual((java["resolved"], java["resolvable"]), (1, 1), java)

    def pass_state(self, run_id, language, seconds):
        state = self.data(self.call("codebase_map_status", {"run_id": run_id}))["engine"]
        deadline = time.monotonic() + seconds
        while state["state"] == "running" and time.monotonic() < deadline:
            time.sleep(1)
            state = self.data(self.call("codebase_map_status", {"run_id": run_id}))["engine"]
        entry = state["languages"][language]
        if entry["state"] == "unavailable":
            self.skipTest(entry.get("install"))
        self.assertEqual(entry["state"], "fresh", state)
        return entry, state["resolution"]["by_language"][language]

    def test_a_go_pass_resolves_a_method_on_a_typed_receiver(self):
        (self.project / "mod").mkdir()
        (self.project / "mod/go.mod").write_text("module demo\n\ngo 1.22\n", encoding="utf-8")
        (self.project / "mod/tool.go").write_text(
            "package demo\n\ntype Tool struct{}\n\nfunc (t Tool) Run() int { return 1 }\n\ntype Other struct{}\n\n"
            "func (o Other) Run() int { return 2 }\n", encoding="utf-8")
        (self.project / "mod/use.go").write_text(
            "package demo\n\nfunc Make() Tool { return Tool{} }\n\nfunc Go() int {\n\treturn Make().Run()\n}\n",
            encoding="utf-8")
        self.call("codebase_map_create_run", {"target": "mod", "run_id": "go-live"})
        # The first pass on a machine installs Go and builds gopls.
        entry, go = self.pass_state("go-live", "go", 420)
        self.assertTrue(entry["engine"].startswith("gopls@"), entry)
        # `Make()` is lexical; `Make().Run()` is the engine's, and `Other.Run` shares its name.
        self.assertEqual((go["resolved"], go["resolvable"]), (2, 2), go)

    def test_a_rust_pass_resolves_a_method_on_a_typed_receiver(self):
        (self.project / "crate/src").mkdir(parents=True)
        (self.project / "crate/Cargo.toml").write_text(
            '[package]\nname = "demo"\nversion = "0.1.0"\nedition = "2021"\n', encoding="utf-8")
        (self.project / "crate/src/lib.rs").write_text(
            "pub struct Tool;\n\nimpl Tool {\n    pub fn run(&self) -> u32 { 1 }\n}\n\n"
            "pub fn go(tool: &Tool) -> u32 {\n    tool.run()\n}\n", encoding="utf-8")
        self.call("codebase_map_create_run", {"target": "crate", "run_id": "rust-live"})
        # The first pass on a machine installs rust-analyzer and, without one on PATH, a Rust toolchain.
        entry, rust = self.pass_state("rust-live", "rust", 480)
        self.assertTrue(entry["engine"].startswith("rust-analyzer@"), entry)
        self.assertEqual((rust["resolved"], rust["resolvable"]), (1, 1), rust)

    def test_scope_streams_monotonic_request_progress_and_structured_result(self):
        result = self.data(self.call("codebase_map_scope", {"target": "src"}, token="scope-1"))
        self.assertEqual(result["files"], 1)
        progress = [message["params"] for message in self.notifications
                    if message.get("method") == "notifications/progress"]
        self.assertGreaterEqual(len(progress), 2)
        self.assertTrue(all(item["progressToken"] == "scope-1" for item in progress))
        values = [item["progress"] for item in progress]
        self.assertTrue(all(left < right for left, right in zip(values, values[1:])), values)

    def test_run_queries_checkpoint_and_event_replay_survive_server_restart(self):
        prepared = self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "wire-run", "engine": False}))
        self.assertEqual(prepared["run_id"], "wire-run")
        outline = self.data(self.call("codebase_map_outline", {"run_id": "wire-run"}))
        path = outline["items"][0]["path"]
        reading = self.data(self.call("codebase_map_read", {
            "run_id": "wire-run", "requests": [{"path": path, "symbols": ["greet"]}],
        }))
        self.assertIn("def greet", reading["files"][0]["blocks"][0]["source"])
        self.data(self.call("codebase_map_checkpoint", {
            "run_id": "wire-run", "phase": 0, "event": "phase_started",
        }))
        events = self.data(self.call("codebase_map_events", {"run_id": "wire-run"}))
        self.assertIn("phase_started", [item["event"] for item in events["events"]])
        cursor = events["next_cursor"]
        self.close()
        self.start()
        replay = self.data(self.call("codebase_map_events", {"run_id": "wire-run", "after": cursor}))
        self.assertEqual(replay["events"], [])
        state = self.data(self.call("codebase_map_status", {"run_id": "wire-run"}))
        self.assertFalse(state["check"]["complete"])

    def test_invalid_arguments_and_incomplete_publication_are_tool_errors(self):
        escaped = self.call("codebase_map_scope", {"target": "../"})
        self.assertTrue(escaped.get("isError"), escaped)
        self.assertIn("repository-relative", escaped["content"][0]["text"])
        malformed = self.call("codebase_map_status", {"run_id": "../foreign"})
        self.assertTrue(malformed.get("isError"), malformed)
        self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "partial", "engine": False}))
        publication = self.call("codebase_map_publish", {"run_id": "partial"})
        self.assertTrue(publication.get("isError"), publication)
        self.assertIn("Publication refused", publication["content"][0]["text"])
        self.assertFalse((self.project / ".daodan/map/07-final-report.md").exists())

    def test_changed_source_is_rejected_through_actual_transport(self):
        self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "changed", "engine": False}))
        outline = self.data(self.call("codebase_map_outline", {"run_id": "changed"}))
        path = outline["items"][0]["path"]
        self.data(self.call("codebase_map_read", {
            "run_id": "changed", "requests": [{"path": path, "full_file": True}],
        }))
        self.source.write_text("def greet(name):\n    return name.upper()\n", encoding="utf-8")
        result = self.call("codebase_map_read", {
            "run_id": "changed", "requests": [{"path": path, "full_file": True}],
        })
        self.assertTrue(result.get("isError"), result)
        self.assertIn("source changed", result["content"][0]["text"])

    def test_store_option_binds_the_custom_store_through_actual_transport(self):
        self.close()
        self.start("--store", ".app/codebase-map")
        self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "stored", "engine": False}))
        self.assertTrue((self.project / ".app/codebase-map/runs/stored/state.json").is_file())
        self.assertFalse((self.project / ".daodan/map").exists())
        refused = self.call("codebase_map_scope", {"target": ".app"})
        self.assertTrue(refused.get("isError"), refused)
        self.assertIn("analysis output", refused["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
