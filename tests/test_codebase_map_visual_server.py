"""The explorer's local server: 127.0.0.1 only, a fixed list of files, no listing, no other origin.

Live, over a MapService: the runs, a run's events after a cursor and a run's envelope; a refused request answers 400.
"""

import http.client
import json
import os
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


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix="visual-live-")).resolve()
        self.addCleanup(shutil.rmtree, self.project, True)
        (self.project / "src").mkdir()
        (self.project / "src/module.py").write_text("LIMIT = 7\n\ndef selected():\n    return LIMIT\n", encoding="utf-8")
        self.service = mcp_service.MapService(self.project)
        self.service.create_run("src", "example", engine=False)
        self.server = visual.make_server(None, self.project / "no-assets", routes=visual.live_routes(self.service))
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

    def test_a_refused_request_answers_400_with_the_reason(self):
        for path in ("/api/events", "/api/events?run=example&after=x", "/api/events?run=missing",
                     "/data/visual.json?run=..%2F..", "/data/visual.json"):
            with self.subTest(path=path):
                status, value = self.get(path)
                self.assertEqual(status, 400)
                self.assertTrue(value["error"])


if __name__ == "__main__":
    unittest.main()
