"""What each host package must say, checked on the real Shinatama kernels."""

import json
import re
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support  # noqa: E402
from scripts.daodan.catalogs import render_catalog  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import opencode_permissions, render_plugin  # noqa: E402
from host_binding_assertions import canonical_markdown, without_host_binding, loaded_instruction_text

ADAPTERS = REPO_ROOT / "adapters"
MARKETING = REPO_ROOT / "plugins/digital-marketing"
RESEARCH = REPO_ROOT / "plugins/research"

CLAUDE_ROOT = "${CLAUDE_PLUGIN_ROOT}"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    assert text.startswith("---\n"), text[:40]
    block = text[4 : text.index("\n---\n", 4)]
    meta = {}
    for line in block.split("\n"):
        if line[:1] not in {" ", "\t"} and ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta


class HostRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = Path(tempfile.mkdtemp())
        cls.packages = {}
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            for plugin_root in (MARKETING, RESEARCH):
                plugin = load_plugin(plugin_root)
                staging = cls.temp / host / plugin.name
                render_plugin(plugin, adapter, staging, adapters_root=ADAPTERS)
                cls.packages[(host, plugin.name)] = staging

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp, ignore_errors=True)

    def package(self, host: str, plugin: str) -> Path:
        return self.packages[(host, plugin)]

    def harness(self, host: str, plugin: str, workflow: str) -> str:
        layout = {
            "claude": f"commands/{workflow}.md",
            "copilot": f"agents/{workflow}-coordinator.agent.md",
            "codex": f"skills/{workflow}-workflow/SKILL.md",
            "pi": f"prompts/{plugin}-{workflow}.md",
            "opencode": f"commands/{workflow}.md",
        }
        return loaded_instruction_text(self, self.package(host, plugin) / layout[host], host)

    def markdown(self, host: str, plugin: str):
        root = self.package(host, plugin)
        return {path.relative_to(root).as_posix(): _read(path) for path in root.rglob("*.md")}

    def test_fanout_per_selection_is_rendered_per_item_on_every_host(self):
        for host in HOSTS:
            with self.subTest(host=host):
                text = self.harness(host, "digital-marketing", "content-strategy")
                self.assertIn(
                    "one `content-marketer` per item of `selection:audits`", text
                )
                self.assertIn("barrier `all-delivered`", text)

    def test_dispatched_entries_reject_hosts_without_isolated_dispatch(self):
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            shared_only = replace(adapter, strategies=tuple(
                replace(strategy, isolated=False) for strategy in adapter.strategies
            ))
            plugin = load_plugin(MARKETING)
            dispatched = replace(plugin, workflows=tuple(
                workflow for workflow in plugin.workflows if workflow.name == "content-strategy"
            ))
            with self.subTest(host=host):
                self.assertIn(resolve_support(dispatched, adapter).state, {"native", "adapted"})
                unavailable = resolve_support(dispatched, shared_only)
                self.assertEqual(unavailable.state, "unsupported")
                self.assertEqual(unavailable.workflow_strategies, (("content-strategy", "none"),))

    def test_copilot_coordinator_gets_the_tools_its_capabilities_need(self):
        meta = _frontmatter(self.harness("copilot", "digital-marketing", "content-strategy"))
        tools = meta["tools"]
        for tool in ("'agent'", "'search'", "'edit'", "'runCommands'", "'fetch'"):
            self.assertIn(tool, tools)

    def test_claude_keeps_its_own_plugin_root_variable(self):
        texts = self.markdown("claude", "research")
        self.assertTrue(any(CLAUDE_ROOT in text for text in texts.values()))

    def test_other_hosts_never_see_the_claude_plugin_root_variable(self):
        for host in ("copilot", "codex", "opencode", "pi"):
            with self.subTest(host=host):
                for name, text in self.markdown(host, "research").items():
                    self.assertNotIn("CLAUDE_PLUGIN_ROOT", text, name)

    def test_codex_flat_workflow_has_skill_frontmatter(self):
        text = _read(self.package("codex", "digital-marketing") / "skills/seo-audit-workflow/SKILL.md")
        meta = _frontmatter(text)
        self.assertEqual(meta["name"], "seo-audit-workflow")
        self.assertIn("description", meta)
        self.assertNotIn("argument-hint", meta)

    def test_copilot_flat_workflow_keeps_the_argument_hint(self):
        text = _read(self.package("copilot", "digital-marketing") / "prompts/seo-audit.prompt.md")
        meta = _frontmatter(text)
        self.assertEqual(meta["name"], "seo-audit")
        self.assertIn("argument-hint", meta)

    def test_opencode_agent_is_a_v2_subagent(self):
        text = _read(self.package("opencode", "research") / "agents/quick-searcher.md")
        head = text.split("\n---\n", 1)[0]
        meta = _frontmatter(text)
        self.assertEqual(meta["mode"], "subagent")
        self.assertIn("permissions:", head)
        self.assertNotIn("\ntools:", head)
        self.assertNotIn("\nmodel:", head)
        self.assertNotIn("\ncolor:", head)

    def test_opencode_permissions_deny_first_and_scope_the_package(self):
        rules = opencode_permissions("Read, Grep, Bash, Grep")
        self.assertEqual(rules[0], {"action": "*", "resource": "*", "effect": "deny"})
        self.assertEqual([rule["action"] for rule in rules[1:4]], ["read", "grep", "shell"])
        self.assertIn({"action": "skill", "resource": "*", "effect": "allow"}, rules)
        self.assertEqual(
            rules[-1],
            {"action": "external_directory", "resource": "<package-root>/**", "effect": "allow"},
        )

    def test_opencode_role_without_tools_gets_only_the_package_allowance(self):
        self.assertEqual(
            opencode_permissions(""),
            [{"action": "external_directory", "resource": "<package-root>/**", "effect": "allow"}],
        )

    def test_kernel_script_invocations_quote_the_plugin_root(self):
        unquoted = re.compile(
            r"(?:python3?|uv run(?: --script)?(?: python)?|bash|node|sh) \$\{CLAUDE_PLUGIN_ROOT\}/"
        )
        offenders = []
        for path in sorted((REPO_ROOT / "plugins").rglob("*.md")):
            for number, line in enumerate(_read(path).splitlines(), 1):
                if unquoted.search(line):
                    offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{number}")
        self.assertEqual(offenders, [])

    def test_opencode_command_bodies_use_no_shell_template_syntax(self):
        for plugin in ("digital-marketing", "research"):
            for path in self.package("opencode", plugin).glob("commands/*.md"):
                self.assertIsNone(re.search(r"(?m)^!`", _read(path)), path)

    def test_naming_default_and_root_selected_paths_keep_the_html_in_an_owned_directory(self):
        for host in HOSTS:
            with self.subTest(host=host):
                method = _read(self.package(host, "digital-marketing") /
                               "skills/brand-naming-method/SKILL.md")
                prose = " ".join(method.split())
                self.assertIn("dedicated `.brand-naming/` directory inside the current workspace", prose)
                self.assertIn("same dedicated owned output directory", prose)
                self.assertIn("report path in the repository root or a shared directory", prose)
                self.assertIn("place its HTML in a dedicated `.brand-naming/` subdirectory", prose)
                self.assertIn("subdirectory as `--root`", prose)
                self.assertIn("report-rendering:report-renderer", method)


if __name__ == "__main__":
    unittest.main()
