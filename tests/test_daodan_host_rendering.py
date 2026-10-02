"""What each host package must say, checked on the real kernels.

These tests render `codebase-xray` and `senior-review` for every host and read
the result the way the host's agent would. They exist because the first
cross-host review of `codebase-xray` found four things the compiler got wrong
for Codex and Copilot while Claude looked fine: a harness header that said
"once each" over a workflow that fans out per partition, a Copilot coordinator
that could not write, `${CLAUDE_PLUGIN_ROOT}` passed through to hosts that do
not define it, and Claude command frontmatter copied into Codex skills.
"""

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import opencode_permissions, render_plugin  # noqa: E402

ADAPTERS = REPO_ROOT / "adapters"
XRAY = REPO_ROOT / "plugins/codebase-xray"
REVIEW = REPO_ROOT / "plugins/senior-review"

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
            for plugin_root in (XRAY, REVIEW):
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
        return _read(self.package(host, plugin) / layout[host])

    def markdown(self, host: str, plugin: str):
        root = self.package(host, plugin)
        return {path.relative_to(root).as_posix(): _read(path) for path in root.rglob("*.md")}

    # -- dispatch plan -----------------------------------------------------

    def test_fanout_per_selection_is_rendered_per_item_on_every_host(self):
        for host in HOSTS:
            with self.subTest(host=host):
                text = self.harness(host, "codebase-xray", "team-analyze")
                self.assertIn(
                    "one `partition-structure-worker` per item of `selection:partitions`", text
                )
                self.assertIn(
                    "one `partition-behavior-worker` per item of `selection:partitions`", text
                )
                self.assertNotIn("once each: `partition-behavior-worker`", text)

    def test_dispatch_plan_keeps_phase_order_and_barriers(self):
        text = self.harness("codex", "codebase-xray", "team-analyze")
        plan = text[text.index("Dispatch plan") : text.index("## Method")]
        order = [
            match.group(1)
            for match in re.finditer(r"^\d+\. `([a-z-]+)`:", plan, flags=re.MULTILINE)
        ]
        self.assertEqual(
            order,
            ["partition-selection", "structure", "behavior", "quality", "interconnect", "synthesis"],
        )
        self.assertIn("`structure`: one `partition-structure-worker`", plan)
        self.assertIn("needs `structure`", plan)
        self.assertIn("barrier `all-delivered`", plan)
        self.assertIn("`synthesis`: one `partition-synthesizer`", plan)
        self.assertIn("needs `behavior`, `quality`, `interconnect`", plan)
        self.assertIn("`partition-selection`: runs in the orchestrating context", plan)

    def test_static_fanout_still_dispatches_once_each(self):
        text = self.harness("claude", "senior-review", "team-review")
        self.assertIn(
            "`cross-examination`: `logic-integrity-auditor` and `premise-auditor`, once each",
            text,
        )
        self.assertIn(
            "`independent-review`: one worker per item of `selection:reviewers`", text
        )
        self.assertIn("`consolidation`: one `code-auditor`", text)

    # -- copilot coordinator -----------------------------------------------

    def test_copilot_coordinator_gets_the_tools_its_capabilities_need(self):
        meta = _frontmatter(self.harness("copilot", "codebase-xray", "team-analyze"))
        tools = meta["tools"]
        for tool in ("'agent'", "'search'", "'edit'", "'runCommands'"):
            self.assertIn(tool, tools)

    # -- plugin root -------------------------------------------------------

    def test_claude_keeps_its_own_plugin_root_variable(self):
        texts = self.markdown("claude", "codebase-xray")
        self.assertTrue(any(CLAUDE_ROOT in text for text in texts.values()))

    def test_other_hosts_never_see_the_claude_plugin_root_variable(self):
        for host in ("copilot", "codex"):
            with self.subTest(host=host):
                for name, text in self.markdown(host, "codebase-xray").items():
                    self.assertNotIn("CLAUDE_PLUGIN_ROOT", text, name)

    def test_other_hosts_explain_their_plugin_root_where_they_use_it(self):
        expectations = {
            "copilot": ("${PLUGIN_ROOT}", "plugin.json"),
            "codex": ("<plugin-root>", ".codex-plugin/plugin.json"),
        }
        for host, (reference, manifest) in expectations.items():
            with self.subTest(host=host):
                texts = self.markdown(host, "codebase-xray")
                using = {name: text for name, text in texts.items() if reference in text}
                self.assertTrue(using, f"{host}: nothing references {reference}")
                for name, text in using.items():
                    self.assertIn(manifest, text, name)
                skill = texts["skills/xray-method/SKILL.md"]
                self.assertIn(f"{reference}/skills/xray-method/scripts/", skill)

    # -- workflow frontmatter and arguments --------------------------------

    def test_claude_flat_workflow_is_the_kernel_verbatim(self):
        rendered = _read(self.package("claude", "codebase-xray") / "commands/analyze.md")
        kernel = _read(XRAY / "workflows/analyze.md").replace("\r\n", "\n")
        self.assertEqual(rendered, kernel)

    def test_codex_flat_workflow_has_skill_frontmatter(self):
        text = _read(self.package("codex", "codebase-xray") / "skills/analyze-workflow/SKILL.md")
        meta = _frontmatter(text)
        # Codex registers skills by frontmatter name, so the name carries the
        # directory suffix: `codebase-xray` also ships a skill, and a plugin
        # with a skill and a workflow of one name (digital-marketing's
        # brand-naming before marketplace 29.0.0) would otherwise register two skills under it.
        self.assertEqual(meta["name"], "analyze-workflow")
        self.assertIn("description", meta)
        self.assertNotIn("argument-hint", meta)
        self.assertIn("Arguments: `<target path>", text)

    def test_copilot_flat_workflow_keeps_the_argument_hint(self):
        text = _read(self.package("copilot", "codebase-xray") / "prompts/analyze.prompt.md")
        meta = _frontmatter(text)
        self.assertEqual(meta["name"], "analyze")
        self.assertIn("argument-hint", meta)
        self.assertIn("<target path>", meta["argument-hint"])

    def test_other_hosts_never_see_the_claude_arguments_variable(self):
        for host in ("copilot", "codex"):
            with self.subTest(host=host):
                for name, text in self.markdown(host, "codebase-xray").items():
                    self.assertNotRegex(text, r"\$ARGUMENTS\b", name)
                harness = self.harness(host, "codebase-xray", "team-analyze")
                self.assertIn("<arguments>", harness)
                self.assertIn("Wherever `<arguments>` appears", harness)

    # -- opencode ----------------------------------------------------------

    def test_opencode_agent_is_a_v2_subagent(self):
        text = _read(self.package("opencode", "senior-review") / "agents/code-auditor.md")
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
        self.assertNotIn(
            {"action": "external_directory", "resource": "*", "effect": "allow"}, rules
        )

    def test_opencode_role_without_tools_gets_only_the_package_allowance(self):
        # No deny-all: the loader appends this to V2's defaults rather than
        # replacing them, so an unrestricted role keeps ordinary tool access.
        self.assertEqual(
            opencode_permissions(""),
            [{"action": "external_directory", "resource": "<package-root>/**", "effect": "allow"}],
        )

    def test_opencode_team_command_dispatches_with_the_subagent_tool(self):
        text = self.harness("opencode", "senior-review", "team-review")
        self.assertIn("`subagent` tool", text)
        self.assertIn('agent: "senior-review:', text)
        self.assertIn("background: true", text)
        self.assertNotIn("pi install", text)
        self.assertRegex(text, r"\$ARGUMENTS\b")

    def test_opencode_never_sees_the_claude_plugin_root_variable(self):
        texts = self.markdown("opencode", "codebase-xray")
        for name, text in texts.items():
            self.assertNotIn("CLAUDE_PLUGIN_ROOT", text, name)
        self.assertIn(
            "<plugin-root>/skills/xray-method/scripts/", texts["skills/xray-method/SKILL.md"]
        )

    def test_kernel_script_invocations_quote_the_plugin_root(self):
        # On OpenCode the loader substitutes the absolute install path, and on
        # every host that path may contain a space (C:/Users/John Doe/...). An
        # unquoted script operand then splits and the command runs the wrong
        # file, so every interpreter invocation of a shipped script quotes it.
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
        for plugin in ("codebase-xray", "senior-review"):
            for path in self.package("opencode", plugin).glob("commands/*.md"):
                self.assertIsNone(re.search(r"(?m)^!`", _read(path)), path)


if __name__ == "__main__":
    unittest.main()
