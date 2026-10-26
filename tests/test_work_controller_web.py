"""Real HTTP behavior of the local read-only web console."""

from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.definition import dump_definition
from work_controller.engine import Engine
from work_controller.web import create_server


class WebConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.workspace = root / "workspace"
        self.workspace.mkdir()
        self.home = root / "home"
        self.engine = Engine(self.home, self.workspace)
        command = (
            "from pathlib import Path; import sys; "
            "print('x' * 70000); print('console stdout'); "
            "print('console stderr', file=sys.stderr); "
            "Path('result.txt').write_text('artifact body', encoding='utf-8')"
        )
        definition = self.workspace / "process.yaml"
        definition.write_text(dump_definition({
            "schema": "work-controller/process/v1",
            "kind": "graph",
            "id": "web-fixture",
            "objective": "exercise the read-only console",
            "jobs": [{
                "id": "emit",
                "type": "command",
                "summary": "emit bounded logs and one artifact",
                "command": {"argv": [sys.executable, "-c", command]},
                "produces": [{"name": "result", "type": "text", "path": "result.txt"}],
                "write_set": ["result.txt"],
                "max_attempts": 1,
                "timeout_seconds": 30,
            }],
            "budget": {"max_attempts": 2, "max_seconds": 60},
        }), encoding="utf-8")
        self.run_id = self.engine.start(definition, grants=["shell"])["id"]
        self.assertEqual(self.engine.drive(self.run_id, "local-holder")["status"], "complete")
        self.attempt_id = f"{self.run_id}:emit:1"
        self.engine.store.map_open("migration", "Inspect the migration safely")
        self.engine.store.ticket_add(
            "migration", "execute", "execution", "Execute the inspected run", run_id=self.run_id
        )
        self.server = create_server(self.home, self.workspace, port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._stop_server)

    def _stop_server(self):
        self.server.shutdown_event.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive(), "HTTP server thread did not stop")

    def request(self, method, path, *, auth=True, headers=None):
        request_headers = dict(headers or {})
        if auth:
            request_headers.setdefault("X-Process-Controller-Token", self.server.token)
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
        try:
            connection.request(method, path, headers=request_headers)
            response = connection.getresponse()
            body = response.read()
            return response.status, response.headers, body
        finally:
            connection.close()

    def json_request(self, path, *, expected=200, auth=True, headers=None):
        status, response_headers, body = self.request(
            "GET", path, auth=auth, headers=headers
        )
        self.assertEqual(status, expected, body)
        self.assertIn("application/json", response_headers.get("Content-Type", ""))
        return json.loads(body)

    def open_stream(self, path, *, auth=True):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
        headers = {"X-Process-Controller-Token": self.server.token} if auth else {}
        try:
            connection.request("GET", path, headers=headers)
            response = connection.getresponse()
            return connection, response
        except Exception:
            connection.close()
            raise

    def read_sse_event(self, response):
        lines = []
        for _ in range(100):
            line = response.fp.readline()
            if not line:
                self.fail("event stream closed before a complete event")
            if line in (b"\n", b"\r\n"):
                if lines:
                    return lines
                continue
            lines.append(line.decode("utf-8").rstrip("\r\n"))
        self.fail("event stream event exceeded the bounded test frame")

    @staticmethod
    def sse_data(lines):
        for line in lines:
            if line.startswith("data: "):
                return json.loads(line[6:])
        return None

    def latest_seq(self, run_id=None):
        events = self.engine.events(run_id or self.run_id, limit=100)
        return max(event["seq"] for event in events)

    def run_snapshot(self):
        return {
            "run": self.engine.store.run(self.run_id),
            "jobs": self.engine.store.jobs(self.run_id),
            "attempt": self.engine.store.attempt(self.attempt_id),
            "artifact": self.engine.store.latest_artifact(self.run_id, "result"),
            "events": self.engine.events(self.run_id, limit=100),
            "map": self.engine.store.map_status("migration"),
        }

    def test_overview_and_map_expose_bounded_metadata(self):
        overview = self.json_request("/api/overview")
        run = next(item for item in overview["runs"] if item["id"] == self.run_id)
        self.assertEqual(run["total_jobs"], 1)
        self.assertEqual(run["succeeded_jobs"], 1)
        self.assertNotIn("definition_yaml", run)
        self.assertNotIn("workspace", run)
        self.assertIn("migration", [item["id"] for item in overview["maps"]])

        decision_map = self.json_request("/api/map/migration")
        self.assertEqual(decision_map["status"]["destination"], "Inspect the migration safely")
        self.assertEqual(decision_map["status"]["next"]["id"], "execute")
        self.assertEqual(decision_map["tickets"][0]["blocked_by"], [])
        self.assertEqual(decision_map["tickets"][0]["run_id"], self.run_id)
        self.json_request("/api/map/missing", expected=404)

    def test_run_and_frontier_expose_execution_and_artifact_metadata(self):
        run = self.json_request(f"/api/run/{self.run_id}")
        self.assertEqual(run["status"]["outcome"], "VERIFIED_SUCCESS")
        self.assertEqual(run["jobs"][0]["status"], "succeeded")
        self.assertEqual(run["attempts"][0]["holder"], "local-holder")
        self.assertEqual(run["attempts"][0]["id"], self.attempt_id)
        self.assertEqual(run["artifacts"][0]["name"], "result")
        self.assertRegex(run["artifacts"][0]["digest"], r"^[0-9a-f]{64}$")
        self.assertEqual(run["frontier"], [])
        self.assertNotIn("definition_yaml", run["status"])
        self.assertNotIn("artifact body", json.dumps(run))
        self.assertEqual(
            self.json_request(f"/api/run/{self.run_id}/frontier"), {"frontier": []}
        )
        self.json_request("/api/run/missing", expected=404)

    def test_events_support_cursor_limits_and_validation(self):
        first = self.json_request(f"/api/run/{self.run_id}/events?after=0&limit=2")
        self.assertEqual(len(first["events"]), 2)
        self.assertEqual(first["events"][0]["kind"], "run.created")
        sequences = [event["seq"] for event in first["events"]]
        self.assertEqual(sequences, sorted(sequences))
        following = self.json_request(
            f"/api/run/{self.run_id}/events?after={sequences[-1]}&limit=100"
        )["events"]
        self.assertTrue(following)
        self.assertTrue(all(event["seq"] > sequences[-1] for event in following))
        self.assertNotIn(sequences[0], [event["seq"] for event in following])
        self.json_request(f"/api/run/{self.run_id}/events?after=-1", expected=400)
        self.json_request(f"/api/run/{self.run_id}/events?limit=0", expected=400)

    def test_attempt_logs_return_both_streams_and_bounded_tails(self):
        encoded_attempt = self.attempt_id.replace(":", "%3A")
        stdout = self.json_request(f"/api/attempt/{encoded_attempt}/log?stream=stdout")
        self.assertTrue(stdout["available"])
        self.assertTrue(stdout["truncated"])
        self.assertGreater(stdout["size"], 65536)
        self.assertLessEqual(len(stdout["text"].encode("utf-8")), 32768)
        self.assertEqual(stdout["text"].splitlines()[-1], "console stdout")

        stderr = self.json_request(f"/api/attempt/{encoded_attempt}/log?stream=stderr")
        self.assertFalse(stderr["truncated"])
        self.assertEqual(stderr["text"].splitlines(), ["console stderr"])

        tail = self.json_request(
            f"/api/attempt/{encoded_attempt}/log?stream=stdout&max_bytes=65537"
        )
        self.assertLessEqual(len(tail["text"].encode("utf-8")), 65536)
        self.assertEqual(tail["text"].splitlines()[-1], "console stdout")
        small = self.json_request(
            f"/api/attempt/{encoded_attempt}/log?stream=stdout&max_bytes=5"
        )
        log_path = self.home / "runs" / self.run_id / "attempts" / "emit-1" / "stdout.log"
        self.assertEqual(
            small["text"], log_path.read_bytes()[-5:].decode("utf-8", errors="replace")
        )
        self.json_request(f"/api/attempt/{encoded_attempt}/log?stream=stdin", expected=400)
        self.json_request("/api/attempt/missing/log?stream=stdout", expected=404)

    def test_assets_head_and_security_headers(self):
        assets = {
            "/": "text/html",
            "/console.css": "text/css",
            "/console.js": "text/javascript",
        }
        for path, content_type in assets.items():
            with self.subTest(path=path):
                status, headers, body = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertIn(content_type, headers.get("Content-Type", ""))
                self.assertGreater(len(body), 100)
                self.assertEqual(int(headers.get("Content-Length")), len(body))
                self.assertEqual(headers.get("Cache-Control"), "no-store")
                self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
                self.assertEqual(headers.get("Referrer-Policy"), "no-referrer")
                self.assertIn("script-src 'self'", headers.get("Content-Security-Policy"))
                self.assertNotIn("unsafe-inline", headers.get("Content-Security-Policy"))
                head_status, head_headers, head_body = self.request("HEAD", path)
                self.assertEqual(head_status, 200)
                self.assertEqual(head_body, b"")
                self.assertEqual(head_headers.get("Content-Length"), str(len(body)))
        _, _, html = self.request("GET", "/")
        self.assertIn(b'src="/console.js"', html)
        self.assertIn(b'href="/console.css"', html)
        self.assertNotIn(b'src="http', html)
        _, _, javascript = self.request("GET", "/console.js")
        self.assertIn(b"EventSource", javascript)
        self.assertNotIn(b"https://", javascript)

    def test_bootstrap_session_token_and_authentication_rejections(self):
        status, headers, _ = self.request("GET", "/api/overview", auth=False)
        self.assertEqual(status, 401)
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        self.assertIsNone(headers.get("Access-Control-Allow-Origin"))
        self.assertEqual(self.request(
            "GET", "/api/overview", auth=False,
            headers={"X-Process-Controller-Token": "wrong"},
        )[0], 401)
        self.assertEqual(self.request(
            "GET", f"/api/overview?token={self.server.token}", auth=False
        )[0], 401)
        self.assertEqual(self.request(
            "GET", "/api/overview", auth=False,
            headers={"Cookie": f"process_controller_token={self.server.token}"},
        )[0], 401)

        status, headers, body = self.request(
            "GET", f"/?token={self.server.token}", auth=False
        )
        self.assertEqual(status, 200)
        self.assertIn(b"Work Controller", body)
        self.assertIsNone(headers.get("Set-Cookie"))
        _, _, javascript = self.request("GET", "/console.js", auth=False)
        self.assertIn(b"sessionStorage", javascript)
        self.assertIn(b"replaceState", javascript)
        self.assertIn(b"X-Process-Controller-Token", javascript)
        self.assertIn(b"params.set(\"token\", token)", javascript)
        self.assertIn("runs", self.json_request("/api/overview"))

    def test_host_validation_and_read_only_methods(self):
        status, headers, _ = self.request(
            "GET", "/api/overview", headers={"Host": "evil.example"}
        )
        self.assertEqual(status, 403)
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        self.assertEqual(self.request(
            "GET", "/api/overview", headers={"Host": f"127.0.0.1:{self.port + 1}"}
        )[0], 403)
        self.assertEqual(self.request(
            "GET", "/api/overview", headers={"Host": f"localhost:{self.port}"}
        )[0], 200)
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"):
            with self.subTest(method=method):
                status, headers, _ = self.request(method, "/api/overview")
                self.assertEqual(status, 405)
                self.assertEqual(headers.get("Allow"), "GET, HEAD")
                self.assertIsNone(headers.get("Access-Control-Allow-Origin"))

    def test_sse_ready_backlog_query_token_and_heartbeat(self):
        self.server.sse_heartbeat = 0.1
        after = self.latest_seq()
        path = f"/api/events/stream?run_id={self.run_id}&after=0&token={self.server.token}"
        connection, response = self.open_stream(path, auth=False)
        try:
            self.assertEqual(response.status, 200)
            self.assertIn("text/event-stream", response.getheader("Content-Type", ""))
            ready = self.read_sse_event(response)
            self.assertIn("event: ready", ready)
            self.assertEqual(self.sse_data(ready)["run_id"], self.run_id)
            update = self.read_sse_event(response)
            self.assertIn("event: update", update)
            self.assertEqual(self.sse_data(update)["kind"], "run.created")
        finally:
            response.close()
            connection.close()

        connection, response = self.open_stream(
            f"/api/events/stream?run_id={self.run_id}&after={after}"
        )
        try:
            self.read_sse_event(response)
            heartbeat = self.read_sse_event(response)
            self.assertIn(": heartbeat", heartbeat)
        finally:
            response.close()
            connection.close()

    def test_sse_delivers_an_event_added_after_connection(self):
        definition = self.workspace / "agent.yaml"
        definition.write_text(dump_definition({
            "schema": "work-controller/process/v1",
            "kind": "graph",
            "id": "web-agent",
            "objective": "observe incremental events",
            "jobs": [{"id": "agent", "type": "agent", "summary": "wait for a host"}],
        }), encoding="utf-8")
        run_id = self.engine.start(definition)["id"]
        after = self.latest_seq(run_id)
        connection, response = self.open_stream(
            f"/api/events/stream?run_id={run_id}&after={after}"
        )
        try:
            self.assertEqual(response.status, 200)
            self.read_sse_event(response)
            packet = self.engine.claim(run_id, "external-holder")
            self.assertIsNotNone(packet)
            update = self.read_sse_event(response)
            self.assertIn("event: update", update)
            event = self.sse_data(update)
            self.assertEqual(event["kind"], "attempt.reserved")
            self.assertGreater(event["seq"], after)
            self.assertEqual(event["payload"]["holder"], "external-holder")
        finally:
            response.close()
            connection.close()

    def test_sse_rejects_a_fifth_concurrent_client(self):
        after = self.latest_seq()
        clients = []
        try:
            for _ in range(4):
                connection, response = self.open_stream(
                    f"/api/events/stream?run_id={self.run_id}&after={after}"
                )
                clients.append((connection, response))
                self.assertEqual(response.status, 200)
                self.read_sse_event(response)
            connection, response = self.open_stream(
                f"/api/events/stream?run_id={self.run_id}&after={after}"
            )
            clients.append((connection, response))
            self.assertEqual(response.status, 429)
            self.assertEqual(response.getheader("Retry-After"), "2")
            self.assertIn("too many", json.loads(response.read())["error"])
        finally:
            for connection, response in clients:
                response.close()
                connection.close()

    def test_http_views_and_rejected_writes_do_not_modify_run_state(self):
        before = self.run_snapshot()
        paths = [
            "/api/overview",
            f"/api/run/{self.run_id}",
            f"/api/run/{self.run_id}/events?after=0&limit=100",
            f"/api/run/{self.run_id}/frontier",
            "/api/map/migration",
            f"/api/attempt/{self.attempt_id}/log?stream=stdout&max_bytes=65536",
        ]
        for path in paths:
            self.assertEqual(self.request("GET", path)[0], 200)
        self.assertEqual(self.request("POST", f"/api/run/{self.run_id}")[0], 405)
        self.assertEqual(self.run_snapshot(), before)

    def test_create_server_is_loopback_only_and_uses_random_tokens(self):
        for host in ("0.0.0.0", "::1", "example.com", "192.168.1.10"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                create_server(self.home, self.workspace, host=host, port=0)
        local = create_server(self.home, self.workspace, host="localhost", port=0)
        other = create_server(self.home, self.workspace, port=0)
        try:
            self.assertIsInstance(local, ThreadingHTTPServer)
            self.assertGreater(local.server_address[1], 0)
            self.assertGreaterEqual(len(local.token), 32)
            self.assertNotEqual(local.token, other.token)
        finally:
            local.server_close()
            other.server_close()


if __name__ == "__main__":
    unittest.main()
