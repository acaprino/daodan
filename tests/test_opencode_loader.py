"""Run the OpenCode loader's own tests under Node, from the Python suite.

The loader is the one piece of runtime JavaScript this repository ships, so its
tests are `node --test` rather than unittest. This wrapper is what puts them in
`python -m unittest discover -s tests`, the command CI and every task gate run.
Without Node on the machine the case is skipped, never passed.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


@unittest.skipIf(NODE is None, "node is not installed")
class OpenCodeLoaderTests(unittest.TestCase):
    def node(self, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [NODE, *arguments], cwd=REPO_ROOT, capture_output=True, text=True, timeout=120
        )

    def test_loader_suite_passes(self):
        result = self.node("--test", "tests/opencode/loader.test.mjs")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_published_loader_registers_every_component_of_the_real_manifest(self):
        script = """
import { createLoader } from "./exports/opencode/index.js";
import fs from "node:fs";
const counts = { skills: 0, agents: 0, commands: 0, mcp: 0 };
const editor = (kind) => ({
  add: () => counts[kind]++, update: (id, fn) => { fn({ permissions: [] }); counts[kind]++; },
  get: () => undefined, set: () => counts[kind]++,
});
const errors = [];
console.error = (...args) => errors.push(args.join(" "));
const ctx = {
  options: {},
  skill: { transform: async (fn) => fn(editor("skills")) },
  agent: { transform: async (fn) => fn(editor("agents")) },
  command: { transform: async (fn) => fn(editor("commands")) },
  mcp: { transform: async (fn) => fn(editor("mcp")) },
  session: { prompt: async () => {} },
};
await createLoader("exports/opencode")(ctx);
const plugins = JSON.parse(fs.readFileSync("exports/opencode/package.json", "utf8")).daodan.plugins;
const expected = { skills: 0, agents: 0, commands: 0, mcp: 0 };
for (const entry of Object.values(plugins)) for (const kind of Object.keys(expected)) expected[kind] += (entry[kind] ?? []).length;
process.stdout.write(JSON.stringify({ counts, expected, errors }));
"""
        result = self.node("--input-type=module", "-e", script)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["counts"], report["expected"])
        self.assertGreater(report["counts"]["agents"], 0)


if __name__ == "__main__":
    unittest.main()
