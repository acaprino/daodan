"""stack-analyser as one more source: run from Daodan's cache, kept to the snapshot's files, never fatal."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import stack_analyser  # noqa: E402

RESULT = {"name": "main", "path": ["/", "/docker-compose.yml", "/api"], "tech": None, "techs": ["docker"], "childs": [
    {"name": "web", "path": ["/web/package.json"], "tech": None, "techs": ["react", "stripe"], "childs": [
        {"name": "Stripe", "path": ["/web/package.json"], "tech": "stripe", "techs": [], "childs": []}]},
    {"name": "db", "path": ["/elsewhere/docker-compose.yml"], "tech": "postgresql", "techs": [], "childs": []}]}


class RunTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix="stack-analyser-"))
        self.addCleanup(shutil.rmtree, self.work, True)
        self.cache = self.work / "cache"
        cli = self.cache / f"stack-analyser-{stack_analyser.VERSION}/node_modules/@specfy/stack-analyser/dist/cli.js"
        cli.parent.mkdir(parents=True)
        cli.write_text("// installed\n")
        self.bin = self.work / "bin"
        self.bin.mkdir()
        path = os.environ["PATH"]
        self.addCleanup(os.environ.__setitem__, "PATH", path)

    def fake_node(self, body: str) -> None:
        node = self.bin / "node"
        node.write_text(f"#!{sys.executable}\nimport json, sys\n{body}\n")
        node.chmod(0o755)
        os.environ["PATH"] = str(self.bin)

    def run_it(self):
        return stack_analyser.run(self.work, self.cache, {"web/package.json", "docker-compose.yml", "api/Dockerfile"})

    def test_ok_keeps_the_findings_inside_the_snapshot(self):
        self.fake_node("out = next(a.split('=', 1)[1] for a in sys.argv if a.startswith('--output='))\n"
                       f"open(out, 'w').write({json.dumps(json.dumps(RESULT))})")
        result = self.run_it()
        self.assertEqual((result["status"], result["version"]), ("ok", stack_analyser.VERSION))
        found = {f["tech"]: f["paths"] for f in result["found"]}
        self.assertEqual(found["stripe"], ["web/package.json"])
        self.assertEqual(found["docker"], ["docker-compose.yml"])
        self.assertNotIn("postgresql", found)  # its only path is outside the snapshot's files
        self.assertGreaterEqual(result["seconds"], 0)

    def test_without_node_it_is_unavailable(self):
        os.environ["PATH"] = str(self.bin)
        result = self.run_it()
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("node", result["reason"])

    def test_a_failing_node_is_unavailable_and_raises_nothing(self):
        self.fake_node("sys.stderr.write('boom'); sys.exit(3)")
        result = self.run_it()
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("boom", result["reason"])


if __name__ == "__main__":
    unittest.main()
