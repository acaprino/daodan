"""Execution bindings, isolated phase dispatch and Copilot permission parity.

Rendered writes are captured in memory: these tests do not create candidate trees
or duplicate source checkouts.
"""
import re
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter
from scripts.daodan.load import load_plugin
from scripts.daodan.render import (
    RenderError, _copilot_tools, _frontmatter, _host_text, _inline_role_scope,
    _operational_binding, render_plugin,
)

from host_binding_assertions import canonical_markdown, without_host_binding

ADAPTERS = REPO_ROOT / "adapters"
MARKER = '<daodan_host_binding host="'


class OperationalBindingTests(unittest.TestCase):
    def render_in_memory(self, name, host, mutate=None, root=None):
        plugin = load_plugin(root or REPO_ROOT / "plugins" / name)
        if mutate:
            plugin = mutate(plugin)
        adapter = load_adapter(ADAPTERS, host)
        captured = {}
        destination = REPO_ROOT / ".daodan-in-memory-render"
        self.assertFalse(destination.exists())
        def remember(path, content):
            captured[Path(path).relative_to(destination).as_posix()] = content
        def copy(source, target, source_root=None):
            raw = Path(source).read_bytes()
            try:
                content = raw.decode("utf-8").replace("\r\n", "\n")
            except UnicodeError:
                content = raw
            remember(target, content)
        with (
            patch("scripts.daodan.render._write_text", side_effect=remember),
            patch("scripts.daodan.render._copy", side_effect=copy),
            patch("scripts.daodan.render.write_provenance"),
            patch("pathlib.Path.mkdir"),
        ):
            render_plugin(plugin, adapter, destination, adapters_root=ADAPTERS)
        self.assertFalse(destination.exists(), "No rendered paths should be persisted")
        return captured

    def test_single_isolated_phase_role_receives_harness_on_every_host(self):
        paths = {
            "claude": "commands/audit-webhooks.md",
            "copilot": "agents/audit-webhooks-coordinator.agent.md",
            "codex": "skills/audit-webhooks-workflow/SKILL.md",
            "pi": "prompts/stripe-audit-webhooks.md",
            "opencode": "commands/audit-webhooks.md",
        }
        for host in HOSTS:
            with self.subTest(host=host):
                rendered = self.render_in_memory("stripe", host)
                text = rendered[paths[host]]
                self.assertIn("## Execution harness", text)
                self.assertIn("Coordinator completion ownership", text)
                self.assertIn("each expected worker, attempt, report path and required check evidence", text)
                self.assertIn("Validate report artifacts before recording delivered", text)
                self.assertIn("ledger schema", text)
                self.assertIn("never converted into a successful delivery", text)
                self.assertIn("**required**", text)
                self.assertIn("one `stripe-webhooks-auditor` in an isolated context", text)
                self.assertIn("artifact:audit-webhooks-report", text)
                self.assertIn("delivered", text)
                self.assertIn("failed", text)
                if host in ("claude", "copilot", "opencode"):
                    self.assertIn("stripe:stripe-webhooks-auditor", text)
                else:
                    self.assertIn("complete body verbatim", text)

    def test_copilot_dispatched_prompt_hands_off_once_to_the_coordinator(self):
        for plugin, workflow in (("stripe", "audit-webhooks"),
                                 ("digital-marketing", "content-strategy"),
                                 ("libgdx-development", "libgdx-audit")):
            with self.subTest(plugin=plugin):
                rendered = self.render_in_memory(plugin, "copilot")
                prompt = rendered[f"prompts/{workflow}.prompt.md"]
                coordinator = rendered[f"agents/{workflow}-coordinator.agent.md"]
                meta, _ = _frontmatter(prompt)
                source_meta, _ = _frontmatter((REPO_ROOT / "plugins" / plugin /
                                              "workflows" / f"{workflow}.md").read_text(encoding="utf-8"))
                self.assertEqual(meta["name"], workflow)
                if "argument-hint" in source_meta:
                    self.assertIn("argument-hint", meta)
                self.assertIn(f"{plugin}:{workflow}-coordinator", prompt)
                self.assertIn("complete original user request", prompt)
                self.assertIn("scope, authorization and budget", prompt)
                self.assertIn("Workflow arguments: <arguments>", prompt)
                self.assertIn("exclusive final report owner", prompt)
                self.assertIn("required coordinator", prompt)
                self.assertIn("nested worker capability", prompt)
                self.assertNotIn("## Execution harness", prompt)
                self.assertNotIn("## Method", prompt)
                self.assertIn("## Execution harness", coordinator)
                self.assertIn("## Method", coordinator)

    def test_nonclaude_roles_inherit_model_and_keep_declared_operation_scope(self):
        for host in ("copilot", "codex", "pi", "opencode"):
            with self.subTest(host=host):
                rendered = self.render_in_memory("research", host)
                adapter = load_adapter(ADAPTERS, host)
                from scripts.daodan.templates import render_path
                relative = render_path(adapter.layout["roles"],
                                       {"plugin": "research", "role": "quick-searcher"})
                text = rendered[relative.as_posix()]
                meta, _ = _frontmatter(text)
                self.assertNotIn("model", meta)
                self.assertIn("Inherit the active session's model and default variant", text)
                self.assertIn("explicit adapter mapping", text)
                if host in ("codex", "pi"):
                    self.assertIn("Declared role operation allowlist", text)
                    self.assertIn("execute shell commands", text)
                    self.assertNotIn("create or overwrite files;", text)

    def test_inline_scope_omitted_empty_unknown_and_restricted_are_distinct(self):
        self.assertIn("no additional tool restriction", _inline_role_scope({}))
        self.assertIn("no file, shell, web or worker operations", _inline_role_scope({"tools": "[]"}))
        text = _inline_role_scope({"tools": "Read, Grep, Bash, Read"})
        self.assertIn("read files; search file contents; execute shell commands", text)
        self.assertNotIn("edit existing files", text)
        self.assertIn("does not grant tools", text)
        with self.assertRaisesRegex(RenderError, "unbound tool"):
            _inline_role_scope({"tools": "Read, InventedTool"})

    def test_single_phase_role_is_validated_against_owner_registry(self):
        def undeclared(plugin):
            workflow = plugin.workflows[0]
            phases = tuple(replace(p, role="missing-provider/worker") if p.role else p
                           for p in workflow.phases)
            return replace(plugin, workflows=(replace(workflow, phases=phases),))
        for host in HOSTS:
            with self.subTest(host=host), self.assertRaisesRegex(RenderError, "undeclared role provider"):
                self.render_in_memory("stripe", host, undeclared)

    def test_all_markdown_receives_binding_including_references_and_dispatch_resources(self):
        for host in HOSTS:
            with self.subTest(host=host):
                rendered = self.render_in_memory("digital-marketing", host)
                markdown = {name: text for name, text in rendered.items() if name.endswith(".md")}
                self.assertTrue(any("/references/" in name for name in markdown))
                self.assertTrue(any("SKILL.md" in name for name in markdown))
                self.assertTrue(any("agents/" in name or "roles/" in name or "-marketer" in name
                                    for name in markdown))
                for name, text in markdown.items():
                    self.assertEqual(text.count(MARKER), 1, name)
                    self.assertIn(f'{MARKER}{host}">', text, name)
                    self.assertIn("An empty worker result is missing delivery", text, name)
                    self.assertIn("Continue working within the current authorization", text, name)
                    self.assertIn("The executing agent and its coordinator own continuation", text, name)
                    self.assertIn("Skills supply knowledge and method instructions", text, name)
                    self.assertIn("After a tool error, inspect its cause", text, name)
                    self.assertIn("never repeat a", text, name)
                    self.assertIn("Stop only for a documented real impediment", text, name)
                    self.assertIn("concrete prerequisite for continuation", text, name)
                    self.assertIn("Shell execution alone does not establish interactive stdin", text, name)

    def test_host_subject_and_domain_examples_are_preserved(self):
        examples = (
            ("marketplace-ops", "skills/kernel-marketplace/SKILL.md"),
            ("ai-tooling", "skills/agent-sdk-builder/SKILL.md"),
        )
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            for plugin, relative in examples:
                with self.subTest(host=host, plugin=plugin):
                    source = (REPO_ROOT / "plugins" / plugin / relative).read_text(encoding="utf-8")
                    text = self.render_in_memory(plugin, host)[relative]
                    self.assertEqual(without_host_binding(self, text, host), canonical_markdown(_host_text(source, adapter)))
            sample = "---\nname: sample\n---\n\n```bash\necho Bash\n```\nAgent SDK role = 'sonnet'\n"
            bound = _host_text(sample, adapter, operational_binding=_operational_binding(adapter, ADAPTERS))
            self.assertEqual(without_host_binding(self, bound, host), _host_text(sample, adapter))

    def test_optional_foreign_providers_do_not_become_required_in_loaded_bodies(self):
        for host in HOSTS:
            with self.subTest(host=host):
                rendered = self.render_in_memory("office", host)
                for name, body in rendered.items():
                    if not name.endswith(".md"):
                        continue
                    text = " ".join(body.split())
                    self.assertNotIn("Named foreign providers remain mandatory", text, name)
                    self.assertIn("Declared required foreign providers remain mandatory", text, name)
                    self.assertIn("stop its dependent phase and report the missing capability", text, name)
                    self.assertIn("Optional external providers follow the method's declared selection and absence behavior", text, name)
                    self.assertIn("their absence alone does not block the base workflow", text, name)
                    self.assertIn("explicitly requested but unavailable provider contribution as unfulfilled", text, name)

    def test_active_host_schema_and_dependency_provisioning_are_explicit(self):
        expectations = {
            "claude": ("Bash", "claude plugin install", "qualified ID"),
            "copilot": ("runCommands", "copilot plugin install", "agents allowlist"),
            "codex": ("apply_patch", "codex plugin add", "inline delivery"),
            "pi": ("pi-subagents", "pi-mcp-adapter", "body resources"),
            "opencode": ("timeout", "sessionID", 'id: "<plugin>:<skill>"'),
        }
        for host, needles in expectations.items():
            with self.subTest(host=host):
                text = _operational_binding(load_adapter(ADAPTERS, host), ADAPTERS)
                for needle in needles:
                    self.assertIn(needle, text)
                self.assertIn("actual input schema", text)
                self.assertIn("a worker stop or an idle session is not the deliverable", text)
                if host != "claude":
                    self.assertNotIn("claude plugin install", text)

    def test_omitted_copilot_tools_preserve_host_defaults(self):
        for plugin, role in (("app-analyzer", "app-analyzer"),):
            with self.subTest(plugin=plugin):
                text = self.render_in_memory(plugin, "copilot")[f"agents/{role}.agent.md"]
                meta, _ = _frontmatter(text)
                self.assertNotIn("tools", meta)
                self.assertNotIn("tools: ['search']", text)
        self.assertIsNone(_copilot_tools(None))

    def test_copilot_coordinator_allowlist_retains_declared_mcp_servers(self):
        fixture = REPO_ROOT / "tests/fixtures/daodan/valid-mcp/plugins/example"
        rendered = self.render_in_memory("example", "copilot", root=fixture)
        meta, _ = _frontmatter(rendered["agents/review-coordinator.agent.md"])
        self.assertIn("'example-tools/*'", meta["tools"])
        self.assertNotIn("'*'", meta["tools"])
        self.assertNotIn("unrelated-server", meta["tools"])
        plain = self.render_in_memory("stripe", "copilot")
        meta, _ = _frontmatter(plain["agents/audit-webhooks-coordinator.agent.md"])
        self.assertNotIn("/*", meta["tools"])
        binding = _operational_binding(load_adapter(ADAPTERS, "copilot"), ADAPTERS)
        self.assertIn("agent allowlist alias", binding)
        self.assertIn("task", binding)
        self.assertIn("actually registered", binding)

    def test_explicit_copilot_tools_are_mapped_or_rejected_without_fallback(self):
        self.assertEqual(_copilot_tools("Read, Edit, Bash, Agent, Read"),
                         "'search', 'edit', 'runCommands', 'agent'")
        self.assertEqual(_copilot_tools("[]"), "")
        self.assertEqual(_copilot_tools("[Read, 'Bash']"), "'search', 'runCommands'")
        with self.assertRaisesRegex(RenderError, "unbound role tool"):
            _copilot_tools("InventedTool")
        with self.assertRaisesRegex(RenderError, "unbound role tool"):
            _copilot_tools("Read, InventedTool")
        text = self.render_in_memory("research", "copilot")["agents/deep-researcher.agent.md"]
        meta, _ = _frontmatter(text)
        self.assertIn("'runCommands'", meta["tools"])
        self.assertNotIn("'edit'", meta["tools"])


if __name__ == "__main__":
    unittest.main()
