"""Routing text generation: one host's entry lines from a kernel's `[routing]` table.

The text is a pure function of the kernel declarations, the workflow
frontmatter and the host adapter. The real kernels gain `[routing]` in a later
wave, so tests load owned temporary copies with the table appended; no network,
no subprocess.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.routing import routing_text  # noqa: E402

FIXTURE = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"
WORKFLOWS = "\n[routing]\nworkflows = true\n"
ROUTING = {
    "daodan": WORKFLOWS,
    "system-utils": WORKFLOWS,
    "csp": '\n[routing]\n\n[[routing.keywords]]\nwords = ["csp", "cp-sat"]\ntarget = "or-tools-expert"\n',
}
LIMIT = 9000


def keyword_rows(rows):
    return "\n[routing]\n" + "".join(
        f"\n[[routing.keywords]]\nwords = {json.dumps(words)}\ntarget = {json.dumps(target)}\n"
        for words, target in rows
    )


def line_with(text, marker):
    lines = [line for line in text.split("\n") if marker in line]
    if len(lines) != 1:
        raise AssertionError(f"expected one line with {marker!r}, found {lines!r}")
    return lines[0]


class RoutingTextCase(unittest.TestCase):
    """Owned temporary kernel copies with `[routing]` appended, shared by the class."""

    @classmethod
    def setUpClass(cls):
        cls.temp = Path(tempfile.mkdtemp(prefix="daodan routing text "))
        cls.plugins = {}
        for name, routing in ROUTING.items():
            kernel = cls.temp / "kernel" / name
            shutil.copytree(REPO_ROOT / "plugins" / name, kernel)
            manifest = kernel / "plugin.toml"
            manifest.write_text(manifest.read_text(encoding="utf-8") + routing, encoding="utf-8")
            cls.plugins[name] = load_plugin(kernel)
        cls.adapters = {host: load_adapter(REPO_ROOT / "adapters", host)
                        for host in ("claude", "codex", "opencode", "copilot", "pi")}

    @classmethod
    def tearDownClass(cls):
        root = cls.temp.resolve()
        if not root.is_relative_to(Path(tempfile.gettempdir()).resolve()):
            raise AssertionError(f"refusing to remove {root}")
        shutil.rmtree(root)

    def text(self, name, host):
        return routing_text(self.plugins[name], self.adapters[host], self.plugins)

    def synthetic(self, routing, name="oversized-example"):
        kernel = self.temp / "synthetic" / f"{name}-{len(list(self.temp.glob('synthetic/*')))}"
        shutil.copytree(FIXTURE, kernel)
        manifest = kernel / "plugin.toml"
        base = manifest.read_text(encoding="utf-8").replace('name = "example"', f'name = "{name}"')
        manifest.write_text(base + routing, encoding="utf-8")
        return load_plugin(kernel)


class RoutingTextTests(RoutingTextCase):
    def test_role_keyword_is_an_agent_on_claude_and_absent_on_codex(self):
        line = line_with(self.text("csp", "claude"), "csp:or-tools-expert")

        self.assertIn("csp, cp-sat", line)
        self.assertIn("agent to dispatch", line)
        self.assertIsNone(self.text("csp", "codex"))

    def test_required_pointer_is_kept_with_host_identity(self):
        cases = {
            "claude": ("`/daodan:fix-bug`", "(use /daodan:investigate-problem)"),
            "opencode": ("`/daodan:fix-bug`", "(use /daodan:investigate-problem)"),
            "codex": ("`fix-bug-workflow`", "(use investigate-problem-workflow)"),
        }
        for host, (identity, pointer) in cases.items():
            with self.subTest(host=host):
                line = line_with(self.text("daodan", host), identity)
                self.assertIn("the user reports a bug to fix", line)
                self.assertIn(f"the user only wants to understand a problem {pointer}", line)

    def test_pointer_to_unrequired_plugin_drops_the_clause(self):
        self.assertNotIn("daodan", self.plugins["system-utils"].required_dependencies)
        for host, identity in (("claude", "`/system-utils:organize-files`"),
                               ("codex", "`organize-files-workflow`")):
            with self.subTest(host=host):
                line = line_with(self.text("system-utils", host), identity)
                self.assertIn("organizing messy folders", line)
                self.assertNotIn("refactor-code", line)
                self.assertNotIn("DO NOT TRIGGER", line)

    def test_hosts_without_routing_delivery_get_nothing(self):
        for host in ("copilot", "pi"):
            for name in ROUTING:
                with self.subTest(host=host, plugin=name):
                    self.assertIsNone(self.text(name, host))

    def test_plugin_without_routing_gets_nothing(self):
        plugin = load_plugin(REPO_ROOT / "plugins/csp")

        self.assertIsNone(plugin.routing)
        self.assertIsNone(routing_text(plugin, self.adapters["claude"], self.plugins))

    def test_text_over_the_limit_fails_naming_the_plugin(self):
        rows = [([f"{index:02d}{letter}" + "x" * 61 for letter in "abcdefgh"], "review")
                for index in range(20)]
        plugin = self.synthetic(keyword_rows(rows))

        with self.assertRaises(ValueError) as caught:
            routing_text(plugin, self.adapters["claude"], {plugin.name: plugin})
        self.assertIn("oversized-example", str(caught.exception))

    def test_term_with_format_or_separator_character_is_rejected(self):
        for character in (" ", " ", "​"):
            with self.subTest(character=hex(ord(character))):
                plugin = self.synthetic(keyword_rows([([f"line{character}break"], "review")]),
                                        name="unsafe-terms")
                with self.assertRaises(ValueError) as caught:
                    routing_text(plugin, self.adapters["claude"], {plugin.name: plugin})
                self.assertIn("unsafe-terms", str(caught.exception))
                self.assertIn(repr(f"line{character}break"), str(caught.exception))

    def test_text_is_deterministic_with_lf_and_trailing_newline(self):
        for host in ("claude", "codex", "opencode"):
            with self.subTest(host=host):
                first = self.text("daodan", host)
                self.assertEqual(first, self.text("daodan", host))
                self.assertTrue(first.endswith("\n"))
                self.assertNotIn("\r", first)

    def test_daodan_text_fits_and_names_its_entries_in_order(self):
        text = self.text("daodan", "claude")

        self.assertLess(len(text), LIMIT)
        self.assertIn("`/daodan:fix-bug`", text)
        self.assertIn("primary entry points", text)
        self.assertNotIn("primary entry points", self.text("system-utils", "claude"))
        names = [line.split("`")[1] for line in text.split("\n") if line.startswith("- `/daodan:")]
        self.assertEqual(names, sorted(f"/daodan:{w.name}" for w in self.plugins["daodan"].workflows))

    def test_workflow_without_trigger_uses_its_first_sentence(self):
        line = line_with(self.text("daodan", "claude"), "`/daodan:start`")

        self.assertTrue(line.endswith("methods with shared content/design."), line)


if __name__ == "__main__":
    unittest.main()
