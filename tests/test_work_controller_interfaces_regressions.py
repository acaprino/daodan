"""Regressions for console and MCP findings from the final interface review."""

from __future__ import annotations

import contextlib
import http.client
import io
import json
import tempfile
import unittest
from pathlib import Path

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.cli import main
from work_controller.definition import dump_definition
from work_controller.engine import Engine
from work_controller.errors import DefinitionError, StateError
from work_controller.mcp import MODERN_VERSION, _MCPService
from work_controller.views import Views
from work_controller.web import create_server


class InterfaceRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.workspace = root / "workspace"
        self.workspace.mkdir()
        self.home = root / "home"
        self.engine = Engine(self.home, self.workspace)
        definition = self.workspace / "process.yaml"
        definition.write_text(dump_definition({
            "schema": "work-controller/process/v1", "kind": "graph", "id": "interfaces",
            "objective": "exercise interface regressions",
            "jobs": [{"id": "agent", "type": "agent", "summary": "wait"}],
        }), encoding="utf-8")
        self.run_id = self.engine.start(definition, run_id="interface-run")["id"]

    def start_server(self):
        server = create_server(self.home, self.workspace, port=0)
        import threading

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.stop_server, server, thread)
        return server

    @staticmethod
    def stop_server(server, thread):
        server.shutdown_event.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    def request(self, server, path):
        connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=4)
        try:
            connection.request(
                "GET", path, headers={"X-Process-Controller-Token": server.token}
            )
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def test_shared_home_inventory_and_status_stay_on_the_selected_workspace(self):
        other_workspace = Path(self.temp.name) / "other"
        other_workspace.mkdir()
        other = Views(Engine(self.home, other_workspace))
        self.assertEqual(other.overview()["runs"], [])
        with self.assertRaisesRegex(StateError, "workspace mismatch"):
            other.status(self.run_id)
        service = _MCPService(self.home, other_workspace)
        result = service._call_tool(
            {"name": "process_run_status", "arguments": {"run_id": self.run_id}}, modern=False
        )
        self.assertTrue(result["isError"])
        self.assertEqual(service._execute_tool("process_runs", {})["runs"], [])

    def test_overflow_cursor_is_rejected_before_sqlite(self):
        after = 9223372036854775808
        with self.assertRaises(DefinitionError):
            Views(self.engine).events(self.run_id, after=after)
        server = self.start_server()
        status, payload = self.request(server, f"/api/run/{self.run_id}/events?after={after}")
        self.assertEqual(status, 400)
        self.assertIn("Int64", payload["error"])
        service = _MCPService(self.home, self.workspace)
        service.legacy_phase = "ready"
        legacy = service.handle({
            "jsonrpc": "2.0", "id": "legacy-overflow", "method": "tools/call",
            "params": {"name": "process_events", "arguments": {"run_id": self.run_id, "after": after}},
        })
        self.assertEqual(legacy["error"]["code"], -32602)
        modern = service.handle({
            "jsonrpc": "2.0", "id": "modern-overflow", "method": "tools/call",
            "params": {
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": MODERN_VERSION,
                    "io.modelcontextprotocol/clientInfo": {"name": "test", "version": "1"},
                    "io.modelcontextprotocol/clientCapabilities": {},
                },
                "name": "process_events", "arguments": {"run_id": self.run_id, "after": after},
            },
        })
        self.assertEqual(modern["error"]["code"], -32602)

    def test_too_many_query_fields_is_a_controlled_bad_request(self):
        server = self.start_server()
        query = "&".join(f"field{index}=x" for index in range(17))
        status, payload = self.request(server, f"/api/overview?{query}")
        self.assertEqual(status, 400)
        self.assertIn("too many query fields", payload["error"])

    def test_port_range_is_validated_before_binding_and_by_the_cli(self):
        for port in (-1, 65536, True):
            with self.subTest(port=port), self.assertRaises(ValueError):
                create_server(self.home, self.workspace, port=port)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main([
                "--workspace", str(self.workspace), "--home", str(self.home),
                "console", "--port", "65536",
            ])
        self.assertEqual(result, 1)
        self.assertIn("port", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_bootstrap_uses_no_cookie_and_static_assets_are_data_free(self):
        server = self.start_server()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=4)
        try:
            connection.request("GET", f"/?token={server.token}")
            response = connection.getresponse()
            body = response.read()
            self.assertEqual(response.status, 200)
            self.assertIsNone(response.getheader("Set-Cookie"))
            self.assertIn(b"Work Controller", body)
        finally:
            connection.close()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=4)
        try:
            connection.request(
                "GET", "/api/overview",
                headers={"Cookie": f"process_controller_token={server.token}"},
            )
            response = connection.getresponse()
            response.read()
            self.assertEqual(response.status, 401)
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
