"""The explorer's local server: 127.0.0.1 only, a fixed list of files, no listing, no other origin.

Live, over a MapService: the runs, a run's events after a cursor and a run's envelope; a refused request answers 400.
The page's requests wait for the host, which takes and closes them; a closed request shows its findings. A POST
from another origin, a bad length or a missing token is refused. A stopped session's taken request can be
released; only the most recent done requests are kept; a malformed request file answers 400.
"""

import http.client
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import mcp_service  # noqa: E402
import visual  # noqa: E402


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="visual-server-")).resolve()
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.export = self.temp / "export"
        self.export.mkdir()
        (self.export / "visual.json").write_text('{"schema": "daodan/visual@1"}', encoding="utf-8")
        (self.export / "state.json").write_text("{}", encoding="utf-8")
        self.assets = self.temp / "assets"
        (self.assets / "assets").mkdir(parents=True)
        (self.assets / "index.html").write_text("<!doctype html><title>Explorer</title>", encoding="utf-8")
        (self.assets / "assets/app.js").write_text("console.log(1)", encoding="utf-8")
        (self.temp / "secret.txt").write_text("secret", encoding="utf-8")
        try:
            os.symlink(self.temp / "secret.txt", self.assets / "assets/link.js")
            self.linked = True
        except OSError:
            self.linked = False
        self.server = visual.make_server(self.export, self.assets)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.port = self.server.server_address[1]

    def get(self, path, host=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        connection.putrequest("GET", path, skip_host=True)
        connection.putheader("Host", host or f"127.0.0.1:{self.port}")
        connection.endheaders()
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response, body

    def test_the_page_assets_and_envelope_are_served_with_a_strict_policy(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        response, body = self.get("/")
        self.assertEqual((response.status, response.getheader("Content-Type")), (200, "text/html; charset=utf-8"))
        self.assertIn(b"Explorer", body)
        response, body = self.get("/data/visual.json")
        self.assertEqual((response.status, body), (200, (self.export / "visual.json").read_bytes()))
        response, _ = self.get("/assets/app.js")
        self.assertEqual(response.getheader("Content-Type"), "text/javascript; charset=utf-8")
        self.assertIn("default-src 'self'", response.getheader("Content-Security-Policy"))
        self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))

    def test_listings_traversals_links_and_other_hosts_are_refused(self):
        for path in ("/assets/", "/../visual.py", "/%2e%2e/visual.py", "/data/../../state.json", "/data/state.json"):
            with self.subTest(path=path):
                self.assertEqual(self.get(path)[0].status, 404)
        self.assertEqual(self.get("/", host="evil.example")[0].status, 421)
        if self.linked:
            self.assertEqual(self.get("/assets/link.js")[0].status, 404)

    def test_a_port_in_use_is_refused(self):
        try:
            second = visual.make_server(self.export, self.assets, self.port)
        except OSError:
            return
        second.server_close()
        self.fail("a second server bound a port already in use")


class CommittedViewerTests(unittest.TestCase):
    """The compiled viewer the plugin ships: served by default, with its notices, loading nothing remote."""

    ASSETS = SCRIPTS.parents[2] / "assets" / "viewer"
    # A namespace or an error link inside the bundle is text; loading code or styles from elsewhere is not allowed.
    REMOTE = re.compile(r"""(?:\bimport\s*\(|\bfrom\s*|new\s+Worker\s*\(|url\(|\bsrc=|\bhref=)\s*['"`]?https?://""")

    def test_the_shipped_viewer_is_served_and_loads_nothing_remote(self):
        self.assertTrue((self.ASSETS / "index.html").is_file())
        self.assertTrue((self.ASSETS / "LICENSES.txt").is_file())
        for path in self.ASSETS.rglob("*"):
            if path.suffix in (".html", ".css", ".js"):
                with self.subTest(path=path.name):
                    self.assertIsNone(self.REMOTE.search(path.read_text(encoding="utf-8", errors="replace")))
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "visual.json").write_text('{"schema": "daodan/visual@1"}', encoding="utf-8")
            server = visual.make_server(Path(temp), self.ASSETS)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                port = server.server_address[1]
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                connection.request("GET", "/", headers={"Host": f"127.0.0.1:{port}"})
                response = connection.getresponse()
                page = response.read().decode("utf-8")
                connection.close()
                self.assertEqual(response.status, 200)
                for script in re.findall(r'src="\./(assets/[^"]+)"', page):
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                    connection.request("GET", "/" + script, headers={"Host": f"127.0.0.1:{port}"})
                    self.assertEqual(connection.getresponse().status, 200, script)
                    connection.close()
            finally:
                server.shutdown()
                server.server_close()


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix="visual-live-")).resolve()
        self.addCleanup(shutil.rmtree, self.project, True)
        (self.project / "src").mkdir()
        (self.project / "src/module.py").write_text("LIMIT = 7\n\ndef selected():\n    return LIMIT\n", encoding="utf-8")
        self.service = mcp_service.MapService(self.project)
        self.service.create_run("src", "example", engine=False)
        self.server = visual.make_server(None, self.project / "no-assets", routes=visual.live_routes(self.service),
                                         actions=visual.live_actions(self.service))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def get(self, path):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=30)
        connection.request("GET", path)
        response = connection.getresponse()
        value = json.loads(response.read())
        connection.close()
        return response.status, value

    def test_runs_events_and_envelope_come_from_the_service(self):
        status, runs = self.get("/api/runs")
        self.assertEqual((status, [run["run_id"] for run in runs["runs"]]), (200, ["example"]))
        status, events = self.get("/api/events?run=example")
        self.assertEqual((status, events["next_cursor"]), (200, len(events["events"])))
        self.service.checkpoint("example", 1, "phase_started", message="reading")
        status, later = self.get(f"/api/events?run=example&after={events['next_cursor']}")
        self.assertEqual([(item["event"], item["message"]) for item in later["events"]], [("phase_started", "reading")])
        status, envelope = self.get("/data/visual.json?run=example")
        self.assertEqual((status, envelope["schema"]), (200, visual.SCHEMA))
        self.assertIn("file:module.py", [entity["ref"] for entity in envelope["entities"]])

    def post(self, path, body, origin=None):
        port = self.server.server_address[1]
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
        connection.request("POST", path, json.dumps(body), {"Content-Type": "application/json",
                                                            "Origin": origin or f"http://127.0.0.1:{port}"})
        response = connection.getresponse()
        value = json.loads(response.read())
        connection.close()
        return response.status, value

    def test_a_request_waits_for_the_host_and_shows_its_findings_when_closed(self):
        status, item = self.post("/api/requests", {"kind": "review", "scope": "prompt", "text": "check payments"})
        self.assertEqual((status, item["state"], item["id"]), (200, "pending", 1))
        self.assertEqual(self.service.ui_requests(take=True)["taken"], [1])
        self.assertEqual(self.service.ui_requests(take=True)["taken"], [])
        (self.project / "result.json").write_text(json.dumps(
            {"findings": [{"file": "src/module.py", "line": 3, "severity": "High"}], "gaps": ["g"]}), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.service.ui_done(1, results=["../outside.json"])
        self.service.ui_done(1, results=["result.json"], message="one finding")
        self.assertEqual(self.get("/api/requests")[1]["requests"][0]["state"], "done")
        status, shown = self.get("/api/findings")
        self.assertEqual((shown["findings"][0]["line"], shown["findings"][0]["request"], shown["gaps"]), (3, 1, ["g"]))
        (self.project / "result.json").unlink()
        self.assertIn("result.json", self.get("/api/findings")[1]["gaps"][0])

    def test_a_taken_request_can_be_released_and_done_ones_are_pruned(self):
        self.service.ui_request("review", "global")
        self.assertEqual(self.service.ui_requests(take=True)["taken"], [1])
        with self.assertRaises(ValueError):
            self.service.ui_requests(release=[2])
        again = self.service.ui_requests(release=[1], take=True)
        self.assertEqual((again["released"], again["taken"]), ([1], [1]))
        for _ in range(mcp_service.MAX_UI_DONE + 5):
            item = self.service.ui_request("map", "global")
            self.service.ui_requests(take=True)
            self.service.ui_done(item["id"])
        self.service.ui_request("map", "global")
        ids = [item["id"] for item in self.service.ui_requests()["requests"]]
        self.assertEqual(len(ids), mcp_service.MAX_UI_DONE + 2)
        self.assertEqual(ids[-1], mcp_service.MAX_UI_DONE + 7)

    def test_a_malformed_request_file_answers_400(self):
        (self.project / ".daodan/map/ui-requests.json").write_text('{"schema": 1, "requests": ["x"]}', encoding="utf-8")
        for path in ("/api/requests", "/api/findings"):
            with self.subTest(path=path):
                self.assertEqual(self.get(path)[0], 400)

    def test_a_token_guards_routes_and_actions(self):
        server = visual.make_server(None, self.project / "no-assets", routes=visual.live_routes(self.service),
                                    actions=visual.live_actions(self.service), token="secret-token")
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        port = server.server_address[1]

        def call(method, path, headers):
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
            body = json.dumps({"kind": "review", "scope": "global"}) if method == "POST" else None
            connection.request(method, path, body, {"Origin": f"http://127.0.0.1:{port}",
                                                    "Content-Type": "application/json", **headers})
            status = connection.getresponse().status
            connection.close()
            return status

        for method, path in (("GET", "/api/runs"), ("GET", "/data/visual.json?run=example"), ("POST", "/api/requests")):
            with self.subTest(method=method, path=path):
                self.assertEqual(call(method, path, {}), 403)
                self.assertEqual(call(method, path, {"X-Daodan-Token": "wrong"}), 403)
                self.assertEqual(call(method, path, {"X-Daodan-Token": "secret-token"}), 200)

    def test_a_bad_content_length_is_refused(self):
        port = self.server.server_address[1]
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
        connection.putrequest("POST", "/api/requests")
        for name, value in (("Origin", f"http://127.0.0.1:{port}"), ("Content-Type", "application/json"),
                            ("Content-Length", "abc")):
            connection.putheader(name, value)
        connection.endheaders()
        self.assertEqual(connection.getresponse().status, 403)
        connection.close()

    def test_refused_posts_change_nothing(self):
        good = {"kind": "review", "scope": "global"}
        self.assertEqual(self.post("/api/requests", good, origin="http://evil.example")[0], 403)
        self.assertEqual(self.post("/api/events", good)[0], 403)
        for body in ({"kind": "deploy", "scope": "global"}, {"kind": "review", "scope": "feature"}, []):
            with self.subTest(body=body):
                self.assertEqual(self.post("/api/requests", body)[0], 400)
        self.assertEqual(self.service.ui_requests()["requests"], [])

    def test_a_refused_request_answers_400_with_the_reason(self):
        for path in ("/api/events", "/api/events?run=example&after=x", "/api/events?run=missing",
                     "/data/visual.json?run=..%2F..", "/data/visual.json"):
            with self.subTest(path=path):
                status, value = self.get(path)
                self.assertEqual(status, 400)
                self.assertTrue(value["error"])


if __name__ == "__main__":
    unittest.main()
