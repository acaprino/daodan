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
import unittest
from pathlib import Path


SERVER = (Path(__file__).resolve().parents[1] /
          "plugins/codebase-map/skills/map-method/scripts/mcp_server.py")
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

    def test_real_tool_catalog_exposes_typed_tools_without_context(self):
        catalog = self.request("tools/list", {})["result"]["tools"]
        by_name = {tool["name"]: tool for tool in catalog}
        for name in ("scope", "create_run", "runs", "status", "outline", "graph", "read", "search", "index",
                     "diff", "artifact", "checkpoint", "events", "resume", "stop", "publish"):
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
        self.data(self.call('codebase_map_create_run', {'target': 'src', 'run_id': 'context-wire'}))
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
                                 {"target": "src", "run_id": "explicit-json", "format": "json"}))
        self.assertEqual(run["state"]["snapshot"]["format"], "json")
        self.assertTrue(self.call("codebase_map_create_run",
                                 {"target": "src", "run_id": "invalid", "format": "pickle"}).get("isError"))

    def test_engine_parameters_and_coverage_cross_the_real_transport(self):
        self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "engine-wire"}))
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
        prepared = self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "wire-run"}))
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
        self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "partial"}))
        publication = self.call("codebase_map_publish", {"run_id": "partial"})
        self.assertTrue(publication.get("isError"), publication)
        self.assertIn("Publication refused", publication["content"][0]["text"])
        self.assertFalse((self.project / ".codebase-map/07-final-report.md").exists())

    def test_changed_source_is_rejected_through_actual_transport(self):
        self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "changed"}))
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
        self.data(self.call("codebase_map_create_run", {"target": "src", "run_id": "stored"}))
        self.assertTrue((self.project / ".app/codebase-map/runs/stored/state.json").is_file())
        self.assertFalse((self.project / ".codebase-map").exists())
        refused = self.call("codebase_map_scope", {"target": ".app"})
        self.assertTrue(refused.get("isError"), refused)
        self.assertIn("analysis output", refused["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
