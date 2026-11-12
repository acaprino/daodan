"""The explorer's local server: 127.0.0.1 only, a fixed list of files, no listing, no other origin."""

import http.client
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


if __name__ == "__main__":
    unittest.main()
