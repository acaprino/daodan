"""`daodan app --desktop`, as Daodan's window starts it: the server's life and what its policy lets a page do, over the
real process, and the MCP server a command-line engine gets, with nothing but this Python. Standard library alone, so
`desktop.yml` runs it with the private Python of the window's folder, on the packages installed there.

    python tests/modal_pytest.py -q tests/test_daodan_desktop.py
    runtime/python.exe -I tests/test_daodan_desktop.py
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[1]
INSTALLED = bool(sys.flags.isolated)  # `-I`: the wheel beside this Python, not the checkout
DAODAN = [sys.executable, *(["-I"] if INSTALLED else []), "-m", "daodan"]
CORE = (Path(importlib.util.find_spec("daodan").origin).parent if INSTALLED else REPO / "daodan") / "core"
HAS_SDK = importlib.util.find_spec("mcp") is not None
NEITHER_PYTHON_NOR_UV = {**os.environ, "PATH": os.path.join(os.environ.get("SYSTEMROOT", "/usr"), "System32")}
HELD = """
import subprocess, sys, threading
sys.path.insert(0, sys.argv[1])
import app
ended = threading.Event()
threading.Thread(target=app._when_ended, args=(app._held_input(), ended.set), daemon=True).start()
child = subprocess.run([sys.executable, "-c", "import sys; print(len(sys.stdin.read()))"], timeout=60,
                       capture_output=True, text=True)
print(child.stdout.strip(), ended.is_set(), flush=True)
raise SystemExit(0 if ended.wait(60) else 1)
"""
LAUNCH = """
import json, sys
sys.path.insert(0, sys.argv[1])
import app
daodan = app.App(sys.argv[2], environment={})
daodan.context = {"path": sys.argv[3]}
print(json.dumps(daodan.mcp()))
"""


class DesktopTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="daodan-desktop-", ignore_cleanup_errors=True)
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)

    def run_held(self, command: list[str]):
        """A process with its input held open and its errors in the file `log`."""
        with (self.folder / "log").open("wb") as log:
            process = subprocess.Popen(command, cwd=REPO, env=NEITHER_PYTHON_NOR_UV, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=log)
        for end in (process.stdout.close, process.stdin.close, process.wait, process.kill):
            self.addCleanup(end)
        return process

    def start(self, *words):
        return self.run_held([*DAODAN, "app", "--desktop", "--work", str(self.folder / "work"), *words])

    def address(self, process):
        line = process.stdout.readline().decode("utf-8").strip()
        address = urlsplit(line)
        log = (self.folder / "log").read_text(encoding="utf-8", errors="replace")
        self.assertEqual((address.scheme, address.hostname, address.path), ("http", "127.0.0.1", "/app/"), log)
        self.assertTrue(address.query.startswith("token="), log)
        return address

    def ended(self, process) -> float:
        """How long the process takes to end once its input has ended."""
        before = time.monotonic()
        process.stdin.close()
        self.assertEqual(process.wait(timeout=30), 0)
        return time.monotonic() - before

    def ask(self, address, method: str, path: str, body: str | None = None, **headers):
        connection = http.client.HTTPConnection("127.0.0.1", address.port, timeout=30)
        try:
            connection.request(method, path, body, headers)
            answer = connection.getresponse()
            return answer.status, answer.read(), answer.headers
        finally:
            connection.close()

    def test_it_prints_its_address_and_ends_with_its_input(self):
        process = self.start()
        address = self.address(process)
        self.assertEqual(self.ask(address, "GET", "/app/")[0], 200)
        self.assertLess(self.ended(process), 5)
        self.assertEqual(process.stdout.read(), b"", "the address is the whole of the output")
        again = self.start("--port", str(address.port))  # the port is free again: the same origin at the next start
        self.assertEqual(self.address(again).port, address.port)
        self.ended(again)

    def test_it_ends_with_its_input_while_a_page_observes(self):
        process = self.start()
        address = self.address(process)
        with socket.create_connection(("127.0.0.1", address.port)) as page:
            page.sendall(f"GET /api/stream?{address.query}&max_seconds=60 HTTP/1.1\r\n"
                         f"Host: 127.0.0.1:{address.port}\r\n\r\n".encode())
            self.assertIn(b"200", page.recv(64))
            self.assertLess(self.ended(process), 5)

    def test_a_port_that_is_taken_gives_a_free_one(self):
        first = self.start()
        taken = self.address(first).port
        second = self.start("--port", str(taken))
        self.assertNotEqual(self.address(second).port, taken)
        alone = subprocess.run([*DAODAN, "app", "--work", str(self.folder / "other"), "--port", str(taken)], cwd=REPO,
                               stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
        self.assertNotEqual(alone.returncode, 0, "without a window the port asked for is the port or nothing")
        self.ended(first)
        self.ended(second)

    def test_the_pages_may_speak_to_the_window_and_the_protections_hold(self):
        process = self.start()
        address = self.address(process)
        own, token = f"http://127.0.0.1:{address.port}", address.query.removeprefix("token=")
        for path in ("/app/", "/"):
            status, _, headers = self.ask(address, "GET", path)
            policy = [part.strip() for part in headers["Content-Security-Policy"].split(";")]
            self.assertEqual(status, 200)
            self.assertIn("default-src 'self'", policy)
            self.assertIn("connect-src 'self' http://ipc.localhost", policy)
            self.assertIsNone(headers["Access-Control-Allow-Origin"])
        given = {"Content-Type": "application/json", "Origin": own, "X-Daodan-Token": token}

        def check(**changed):
            return self.ask(address, "POST", "/api/app/check", json.dumps({"url": "x"}), **{**given, **changed})[0]

        self.assertNotEqual(check(), 403)
        self.assertEqual(check(**{"X-Daodan-Token": "x"}), 403)
        self.assertEqual(check(Origin="http://tauri.localhost"), 403)
        self.assertEqual(self.ask(address, "GET", "/api/app/state")[0], 403)
        self.assertEqual(self.ask(address, "GET", "/app/", Host="evil.test")[0], 421)
        self.ended(process)

    def test_a_program_it_starts_does_not_hold_the_input(self):
        """A child that inherits the pipe a read waits on hangs as it starts, on Windows."""
        process = self.run_held([sys.executable, "-c", HELD, str(CORE)])
        self.assertEqual(process.stdout.readline().split(), [b"0", b"False"],
                         (self.folder / "log").read_text(encoding="utf-8", errors="replace"))
        self.ended(process)

    @unittest.skipUnless(HAS_SDK, "requires the MCP SDK, which the installed application holds")
    def test_a_command_line_engine_reaches_the_tools_with_this_python_alone(self):
        project = self.folder / "checkout" / "project"
        project.mkdir(parents=True)
        launch = json.loads(subprocess.run(
            [sys.executable, "-c", LAUNCH, str(CORE), str(self.folder / "work"), str(project / "tree")],
            capture_output=True, text=True, timeout=60, check=True).stdout)
        self.assertEqual(launch["command"], sys.executable)
        self.assertNotIn("uv", launch["args"])
        self.assertEqual(launch["args"][-2:], ["--project", project.as_posix()])
        server = self.run_held([launch["command"], *launch["args"]])

        def said(message: dict) -> None:
            server.stdin.write(json.dumps({"jsonrpc": "2.0", **message}).encode() + b"\n")
            server.stdin.flush()

        def answer(identity: int) -> dict:
            while True:
                line = server.stdout.readline()
                self.assertTrue(line, (self.folder / "log").read_text(encoding="utf-8", errors="replace"))
                message = json.loads(line)
                if message.get("id") == identity:
                    return message["result"]

        said({"id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}})
        self.assertEqual(answer(1)["serverInfo"]["name"], "codebase-map")
        said({"method": "notifications/initialized"})
        said({"id": 2, "method": "tools/list", "params": {}})
        self.assertIn("codebase_map_flows", [tool["name"] for tool in answer(2)["tools"]])
        self.ended(server)


if __name__ == "__main__":
    unittest.main(verbosity=2)
