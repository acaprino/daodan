"""Protocol and read-only integration tests for the stdio MCP interface."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.definition import dump_definition
from work_controller.engine import Engine
from work_controller.mcp import (
    LEGACY_VERSION,
    MAX_MESSAGE_BYTES,
    MODERN_VERSION,
    run_stdio,
)

CLIENT_INFO = {"name": "mcp-test-client", "version": "1.0.0"}


def request(request_id, method, params=None):
    message = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    return message


def modern_params(**extra):
    params = {
        "_meta": {
            "io.modelcontextprotocol/protocolVersion": MODERN_VERSION,
            "io.modelcontextprotocol/clientInfo": CLIENT_INFO,
            "io.modelcontextprotocol/clientCapabilities": {},
        }
    }
    params.update(extra)
    return params


def tool_call(request_id, name, arguments=None, *, modern=False):
    params = {"name": name, "arguments": arguments or {}}
    if modern:
        params = modern_params(**params)
    return request(request_id, "tools/call", params)


def compact(value):
    return json.dumps(value, allow_nan=False, separators=(",", ":"))


class MCPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.workspace = root / "workspace"
        self.workspace.mkdir()
        self.home = root / "home"
        self.engine = Engine(self.home, self.workspace)
        definition = {
            "schema": "work-controller/process/v1",
            "kind": "graph",
            "id": "mcp-test",
            "objective": "exercise read-only MCP projections",
            "jobs": [
                {
                    "id": "inspect",
                    "type": "agent",
                    "summary": "inspect the fixture",
                    "max_attempts": 2,
                    "timeout_seconds": 30,
                }
            ],
            "budget": {"max_attempts": 4, "max_seconds": 300},
        }
        definition_path = self.workspace / "process.yaml"
        definition_path.write_text(dump_definition(definition), encoding="utf-8")
        self.run_id = self.engine.start(definition_path, run_id="mcp-run")["id"]
        packet = self.engine.claim(self.run_id, "mcp-test")
        self.assertIsNotNone(packet)
        self.attempt_id = packet["attempt_id"]
        self.engine.store.map_open("mcp-map", "Exercise the map projection")
        self.engine.store.ticket_add(
            "mcp-map", "inspect-map", "research", "Inspect the map fixture"
        )

    def exchange(self, messages):
        source = "".join(compact(message) + "\n" for message in messages)
        stdout = io.StringIO()
        run_stdio(
            self.home,
            self.workspace,
            stdin=io.StringIO(source),
            stdout=stdout,
        )
        return [json.loads(line) for line in stdout.getvalue().splitlines()]

    def legacy_exchange(self, messages, *, requested_version=LEGACY_VERSION):
        initialize = request(
            "initialize",
            "initialize",
            {
                "protocolVersion": requested_version,
                "capabilities": {},
                "clientInfo": CLIENT_INFO,
            },
        )
        initialized = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        return self.exchange([initialize, initialized, *messages])

    def assert_tool_success(self, response):
        self.assertNotIn("error", response)
        result = response["result"]
        self.assertFalse(result["isError"])
        self.assertEqual(result["content"], [{"type": "text", "text": compact(result["structuredContent"])}])
        return result["structuredContent"]

    def test_legacy_handshake_lists_and_calls_every_read_only_tool_without_mutation(self):
        before_run = self.engine.store.run(self.run_id)
        before_events = self.engine.store.events(self.run_id, limit=100)
        before_attempt = self.engine.store.attempt(self.attempt_id)
        calls = [
            request("tool-list", "tools/list", {}),
            tool_call("runs", "process_runs", {"limit": 1}),
            tool_call("status", "process_run_status", {"run_id": self.run_id}),
            tool_call("detail", "process_run_detail", {"run_id": self.run_id}),
            tool_call("frontier", "process_frontier", {"run_id": self.run_id}),
            tool_call("events", "process_events", {"run_id": self.run_id, "after": 0, "limit": 1}),
            tool_call("map", "process_map_status", {"map_id": "mcp-map"}),
            tool_call("supervise", "process_supervise", {"attempt_id": self.attempt_id}),
        ]
        responses = self.legacy_exchange(calls)
        self.assertEqual(len(responses), len(calls) + 1)
        initialized = responses[0]["result"]
        self.assertEqual(initialized["protocolVersion"], LEGACY_VERSION)
        self.assertEqual(initialized["capabilities"], {"tools": {}})
        self.assertEqual(initialized["serverInfo"]["name"], "work-controller")

        tools = responses[1]["result"]["tools"]
        self.assertEqual(
            [tool["name"] for tool in tools],
            [
                "process_runs",
                "process_run_status",
                "process_run_detail",
                "process_frontier",
                "process_events",
                "process_map_status",
                "process_supervise",
            ],
        )
        for tool in tools:
            self.assertEqual(tool["inputSchema"]["type"], "object")
            self.assertFalse(tool["inputSchema"]["additionalProperties"])
            self.assertTrue(tool["annotations"]["readOnlyHint"])

        by_id = {response["id"]: response for response in responses}
        runs = self.assert_tool_success(by_id["runs"])
        self.assertEqual(set(runs), {"runs"})
        self.assertEqual(runs["runs"][0]["id"], self.run_id)
        self.assertNotIn("maps", runs)
        self.assertEqual(self.assert_tool_success(by_id["status"])["id"], self.run_id)
        detail = self.assert_tool_success(by_id["detail"])
        self.assertEqual(detail["status"]["id"], self.run_id)
        self.assertNotIn("definition_yaml", detail)
        self.assertEqual(self.assert_tool_success(by_id["frontier"]), {"frontier": []})
        self.assertEqual(len(self.assert_tool_success(by_id["events"])["events"]), 1)
        self.assertEqual(self.assert_tool_success(by_id["map"])["status"]["id"], "mcp-map")
        supervision = self.assert_tool_success(by_id["supervise"])
        self.assertFalse(supervision["authoritative"])
        self.assertEqual(supervision["observation"]["attempt_id"], self.attempt_id)

        self.assertEqual(self.engine.store.run(self.run_id), before_run)
        self.assertEqual(self.engine.store.events(self.run_id, limit=100), before_events)
        self.assertEqual(self.engine.store.attempt(self.attempt_id), before_attempt)

    def test_legacy_negotiation_lifecycle_ping_and_notification_silence(self):
        initialize = request(
            "initialize",
            "initialize",
            {
                "protocolVersion": "2099-01-01",
                "capabilities": {},
                "clientInfo": CLIENT_INFO,
            },
        )
        messages = [
            initialize,
            request("too-early", "tools/list", {}),
            request("ping", "ping"),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            request("after", "tools/list", {}),
            {"jsonrpc": "2.0", "method": "notifications/unknown"},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
        ]
        responses = self.exchange(messages)
        self.assertEqual(
            [response["id"] for response in responses],
            ["initialize", "too-early", "ping", "after"],
        )
        self.assertEqual(responses[0]["result"]["protocolVersion"], LEGACY_VERSION)
        self.assertEqual(responses[1]["error"]["code"], -32602)
        self.assertIn("not initialized", responses[1]["error"]["data"]["detail"])
        self.assertEqual(responses[2]["result"], {})
        self.assertIn("tools", responses[3]["result"])

    def test_modern_discover_tools_and_required_meta(self):
        messages = [
            request("discover", "server/discover", modern_params()),
            request("list", "tools/list", modern_params()),
            tool_call("call", "process_runs", {"limit": 1}, modern=True),
            request("missing", "server/discover", {}),
            request("missing-tools", "tools/list", {}),
            request(
                "unsupported",
                "server/discover",
                {
                    "_meta": {
                        "io.modelcontextprotocol/protocolVersion": "1900-01-01",
                        "io.modelcontextprotocol/clientInfo": CLIENT_INFO,
                        "io.modelcontextprotocol/clientCapabilities": {},
                    }
                },
            ),
        ]
        responses = self.exchange(messages)
        by_id = {response["id"]: response for response in responses}
        discovery = by_id["discover"]["result"]
        self.assertEqual(discovery["resultType"], "complete")
        self.assertEqual(discovery["supportedVersions"], [MODERN_VERSION, LEGACY_VERSION])
        self.assertEqual(discovery["capabilities"], {"tools": {}})
        self.assertEqual(
            discovery["_meta"]["io.modelcontextprotocol/serverInfo"]["name"],
            "work-controller",
        )
        self.assertIn("Read-only", discovery["instructions"])
        self.assertGreater(discovery["ttlMs"], 0)
        self.assertEqual(discovery["cacheScope"], "private")
        self.assertEqual(by_id["list"]["result"]["resultType"], "complete")
        self.assertEqual(by_id["list"]["result"]["cacheScope"], "private")
        self.assertEqual(self.assert_tool_success(by_id["call"])["runs"][0]["id"], self.run_id)
        self.assertEqual(by_id["call"]["result"]["resultType"], "complete")
        for request_id in ("missing", "missing-tools"):
            self.assertEqual(by_id[request_id]["error"]["code"], -32602)
            self.assertIn("_meta", by_id[request_id]["error"]["data"]["detail"])
        self.assertEqual(by_id["unsupported"]["error"]["code"], -32022)
        self.assertEqual(
            by_id["unsupported"]["error"]["data"]["requested"], "1900-01-01"
        )

    def test_closed_invalid_params_unknown_tool_and_actionable_business_error(self):
        calls = [
            tool_call("required", "process_run_status"),
            tool_call("extra", "process_runs", {"unexpected": True}),
            tool_call("bool", "process_runs", {"limit": True}),
            tool_call("zero", "process_runs", {"limit": 0}),
            tool_call("large", "process_runs", {"limit": 101}),
            tool_call("after", "process_events", {"run_id": self.run_id, "after": -1}),
            tool_call("after-type", "process_events", {"run_id": self.run_id, "after": "0"}),
            request("arguments", "tools/call", {"name": "process_runs", "arguments": []}),
            request("name", "tools/call", {"name": 7, "arguments": {}}),
            tool_call("unknown", "process_delete_run", {"run_id": self.run_id}),
            tool_call("business", "process_run_status", {"run_id": "missing-run"}),
            request("params", "tools/call", []),
        ]
        responses = self.legacy_exchange(calls)
        by_id = {response["id"]: response for response in responses}
        for request_id in (
            "required",
            "extra",
            "bool",
            "zero",
            "large",
            "after",
            "after-type",
            "arguments",
            "name",
            "unknown",
            "params",
        ):
            self.assertEqual(by_id[request_id]["error"]["code"], -32602, request_id)
        self.assertIn("Unknown tool", compact(by_id["unknown"]["error"]))
        business = by_id["business"]["result"]
        self.assertTrue(business["isError"])
        self.assertIn("unknown run", business["content"][0]["text"])
        self.assertIn("check the identifier", business["content"][0]["text"])
        self.assertEqual(json.loads(business["content"][0]["text"]), business["structuredContent"])

    def test_parse_utf8_size_and_invalid_request_errors_recover_on_next_line(self):
        valid_ping = compact(request("ping", "ping")).encode("utf-8") + b"\n"
        notification = compact({"jsonrpc": "2.0", "method": "tools/list"}).encode("utf-8") + b"\n"
        source = (
            b"not-json\n"
            + b"\xff\n"
            + (b" " * (MAX_MESSAGE_BYTES + 1))
            + b"\n"
            + valid_ping
            + notification
            + b"[]\n"
        )
        stdout = io.BytesIO()
        run_stdio(
            self.home,
            self.workspace,
            stdin=io.BytesIO(source),
            stdout=stdout,
        )
        responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual(len(responses), 5)
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertEqual(responses[1]["error"]["code"], -32700)
        self.assertEqual(responses[2]["error"]["code"], -32600)
        self.assertIn("byte limit", responses[2]["error"]["data"]["detail"])
        self.assertEqual(responses[3], {"jsonrpc": "2.0", "id": "ping", "result": {}})
        self.assertEqual(responses[4]["error"]["code"], -32600)

    def test_rate_limit_uses_a_patchable_threshold_without_sleeping(self):
        messages = [request(index, "ping") for index in range(3)]
        with mock.patch("work_controller.mcp._RATE_LIMIT", 2):
            responses = self.exchange(messages)
        self.assertEqual([response.get("result") for response in responses[:2]], [{}, {}])
        self.assertEqual(responses[2]["id"], 2)
        self.assertEqual(responses[2]["error"]["message"], "Rate limit exceeded")
        self.assertGreater(responses[2]["error"]["data"]["retryAfterMs"], 0)

    def test_debug_is_opt_in_and_never_logs_params(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        message = request("discover", "server/discover", modern_params())
        with (
            mock.patch.dict(os.environ, {"PROCESS_CONTROLLER_MCP_DEBUG": "1"}),
            contextlib.redirect_stderr(stderr),
        ):
            run_stdio(
                self.home,
                self.workspace,
                stdin=io.StringIO(compact(message) + "\n"),
                stdout=stdout,
            )
        self.assertIn("server/discover", stderr.getvalue())
        self.assertNotIn(CLIENT_INFO["name"], stderr.getvalue())
        self.assertEqual(json.loads(stdout.getvalue())["id"], "discover")

    def test_real_subprocess_stdio_exits_when_stdin_closes(self):
        script = (
            "import sys; from pathlib import Path; "
            "from work_controller.mcp import run_stdio; "
            "run_stdio(Path(sys.argv[1]), Path(sys.argv[2]))"
        )
        env = os.environ.copy()
        env["PYTHONPATH"] = str(work_controller_test_support.CONTROLLER_SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        env["PROCESS_CONTROLLER_MCP_DEBUG"] = "0"
        process = subprocess.Popen(
            [sys.executable, "-B", "-c", script, str(self.home), str(self.workspace)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=env,
        )
        try:
            source = compact(request("discover", "server/discover", modern_params())) + "\n"
            output, errors = process.communicate(source, timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)
            self.fail("MCP subprocess did not exit after stdin closed")
        self.assertEqual(process.returncode, 0, errors)
        self.assertEqual(errors, "")
        lines = output.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["result"]["resultType"], "complete")


if __name__ == "__main__":
    unittest.main()
