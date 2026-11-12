"""The explorer's local server: 127.0.0.1 only, a fixed list of files, no listing, no other origin."""

import http.client
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


if __name__ == "__main__":
    unittest.main()
