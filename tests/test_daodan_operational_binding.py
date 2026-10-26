"""Execution bindings, isolated phase dispatch and Copilot permission parity.

Rendered writes are captured in memory: these tests do not create candidate trees
or duplicate source checkouts.
"""
import re
import sys
import unittest
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter
from scripts.daodan.load import load_plugin
from scripts.daodan.role_bodies import resolve_role
from scripts.daodan.render import (
    MCP_REGISTRATION_STRATEGY, RenderError, _copilot_tools, _frontmatter, _host_text,
    _inline_role_scope, _mcp_registration_notes, _operational_binding, render_plugin,
)
from scripts.daodan.validate import MCP_CAPABILITY

from host_binding_assertions import canonical_markdown, without_host_binding

ADAPTERS = REPO_ROOT / "adapters"
MARKER = '<daodan_host_binding host="'
# Since 38.0.0 every command is a workflow of the `daodan` entry plugin, and each
# one dispatches roles that other plugins own.
ENTRY = "daodan"


@lru_cache(maxsize=None)
def plugin_registry():
    """Every kernel, as the build passes it, so cross-plugin roles resolve."""
    return {path.parent.name: load_plugin(path.parent)
            for path in sorted((REPO_ROOT / "plugins").glob("*/plugin.toml"))}


def entry_paths(workflow):
    """Where each host registers a daodan workflow's executable body."""
    return {
        "claude": f"commands/{workflow}.md",
        "copilot": f"agents/{workflow}-coordinator.agent.md",
        "codex": f"skills/{workflow}-workflow/SKILL.md",
        "pi": f"prompts/{ENTRY}-{workflow}.md",
        "opencode": f"commands/{workflow}.md",
    }


class OperationalBindingTests(unittest.TestCase):
    def render_in_memory(self, name, host, mutate=None):
        registry = plugin_registry()
        plugin = registry[name]
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
            render_plugin(plugin, adapter, destination, adapters_root=ADAPTERS,
                          plugin_registry=registry)
        self.assertFalse(destination.exists(), "No rendered paths should be persisted")
        return captured

    def render_in_memory_fixture(self, host):
        """The fixture plugin: one workflow, no dependency and no MCP server."""
        plugin = load_plugin(REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example")
        captured = {}
        destination = REPO_ROOT / ".daodan-in-memory-render"
        with (
            patch("scripts.daodan.render._write_text",
                  side_effect=lambda p, c: captured.__setitem__(Path(p).relative_to(destination).as_posix(), c)),
            patch("scripts.daodan.render._copy"),
            patch("scripts.daodan.render.write_provenance"),
            patch("pathlib.Path.mkdir"),
        ):
            render_plugin(plugin, load_adapter(ADAPTERS, host), destination, adapters_root=ADAPTERS)
        return captured

    def test_single_isolated_phase_role_receives_harness_on_every_host(self):
        # The single isolated phase role is daodan onboard-project's `explore`
        # phase, a role of another plugin; review-react was retired and
        # humanize-text moved to Shinatama.
        paths = entry_paths("onboard-project")
        for host in HOSTS:
            with self.subTest(host=host):
                rendered = self.render_in_memory(ENTRY, host)
                text = rendered[paths[host]]
                self.assertIn("## Execution harness", text)
                self.assertIn("Coordinator completion ownership", text)
                self.assertIn("each expected worker, attempt, report path and required check evidence", text)
                self.assertIn("Validate report artifacts before recording delivered", text)
                self.assertIn("ledger schema", text)
                self.assertIn("never converted into a successful delivery", text)
                self.assertIn("**required**", text)
                self.assertIn("one `project-knowledge:codebase-explorer` in an isolated context", text)
                self.assertIn("artifact:context-brief", text)
                self.assertIn("delivered", text)
                self.assertIn("failed", text)
                if host in ("claude", "copilot", "opencode"):
                    self.assertIn("dispatch the installed `project-knowledge:codebase-explorer` agent "
                                  "by its qualified identity", text)
                else:
                    self.assertIn("read `contracts/dispatch/project-knowledge/codebase-explorer.md` inside "
                                  "this package and pass its complete role body verbatim", text)
                    self.assertIn("contracts/dispatch/project-knowledge/codebase-explorer.md", rendered)

    def test_copilot_dispatched_prompt_hands_off_once_to_the_coordinator(self):
        # Since 38.0.0 the three dispatch shapes are daodan entries: a single
        # isolated phase role (onboard-project), the map that replaced team-analyze
        # (map-code) and the method-bound review that replaced code-review
        # (review-changes).
        plugin = ENTRY
        rendered = self.render_in_memory(plugin, "copilot")
        for workflow in ("onboard-project", "map-code", "review-changes"):
            with self.subTest(workflow=workflow):
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
                    # The role writes its assigned report on inline hosts too.
                    self.assertIn("create or overwrite files;", text)
        for host in ("codex", "pi"):
            with self.subTest(host=host, resource=True):
                # Since 38.0.0 senior-review registers no workflow, so the inline
                # dispatch resources ship with the daodan entries that dispatch them.
                rendered = self.render_in_memory(ENTRY, host)
                resources = {name: text for name, text in rendered.items()
                             if name.startswith("contracts/dispatch/")}
                self.assertTrue(resources)
                for name, text in resources.items():
                    self.assertNotRegex(text, r"(?m)^model:", name)
                    self.assertNotRegex(text, r"(?m)^tools:", name)
                    owner, role = Path(name).relative_to("contracts/dispatch").with_suffix("").parts
                    source_meta = resolve_role(plugin_registry(), owner, role)["metadata"]
                    # A role without a source restriction keeps the session's
                    # permissions rather than becoming a read-only worker.
                    if "tools" in source_meta:
                        self.assertIn("Declared role operation allowlist", text, name)
                    else:
                        self.assertIn("declares no additional tool restriction", text, name)
                        self.assertNotIn("Declared role operation allowlist", text, name)
                    self.assertIn("source-sha256", text, name)
                self.assertTrue(any("Declared role operation allowlist" in text
                                    for text in resources.values()))

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
        # The single phase role is daodan onboard-project's `explore` phase.
        def undeclared(plugin):
            workflow = next(w for w in plugin.workflows if w.name == "onboard-project")
            phases = tuple(replace(p, role="missing-provider/worker") if p.id == "explore" else p
                           for p in workflow.phases)
            self.assertNotEqual(phases, workflow.phases)
            return replace(plugin, workflows=(replace(workflow, phases=phases),))
        for host in HOSTS:
            with self.subTest(host=host), self.assertRaisesRegex(RenderError, "undeclared role provider"):
                self.render_in_memory(ENTRY, host, undeclared)

    def test_all_markdown_receives_binding_including_references_and_dispatch_resources(self):
        # Since 38.0.0 the workflow entries and the inline dispatch resources ship
        # in the daodan package, while senior-review keeps its skills,
        # references and roles; both packages are checked.
        for host in HOSTS:
            with self.subTest(host=host):
                rendered = self.render_in_memory("senior-review", host)
                entries = self.render_in_memory(ENTRY, host)
                markdown = {name: text for name, text in rendered.items() if name.endswith(".md")}
                self.assertTrue(any("/references/" in name for name in markdown))
                self.assertTrue(any("SKILL.md" in name for name in markdown))
                self.assertTrue(any("agents/" in name or "roles/" in name or "-auditor/" in name
                                    for name in markdown))
                entry_markdown = {f"{ENTRY}/{name}": text for name, text in entries.items()
                                  if name.endswith(".md")}
                self.assertIn(f"{ENTRY}/{entry_paths('review-branch')[host]}", entry_markdown)
                if host in ("codex", "pi"):
                    self.assertTrue(any(name.startswith(f"{ENTRY}/contracts/dispatch/")
                                        for name in entry_markdown))
                markdown.update(entry_markdown)
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

    def test_generated_inventory_reference_also_has_execution_binding(self):
        for host in HOSTS:
            with self.subTest(host=host):
                text = self.render_in_memory("skill-catalog", host)["skills/skill-catalog/references/host-inventory.md"]
                self.assertEqual(text.count(MARKER), 1)
                self.assertIn("actual", text)
                self.assertIn("inventory", text)

    def test_host_subject_and_domain_examples_are_preserved(self):
        examples = (
            ("marketplace-ops", "skills/kernel-marketplace/SKILL.md"),
            ("ai-tooling", "skills/agent-sdk-builder/SKILL.md"),
        )
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            binding = adapter.bindings.get(MCP_CAPABILITY)
            registers = binding is not None and binding.strategy == MCP_REGISTRATION_STRATEGY
            for plugin, relative in examples:
                with self.subTest(host=host, plugin=plugin):
                    source = (REPO_ROOT / "plugins" / plugin / relative).read_text(encoding="utf-8")
                    text = self.render_in_memory(plugin, host)[relative]
                    # Since 38.0.0 a skill entry of a plugin that declares an MCP
                    # server carries the registration note where the host needs one.
                    spec = plugin_registry()[plugin]
                    notes = _mcp_registration_notes(spec, adapter) if registers else ()
                    if spec.mcp_servers and registers:
                        self.assertTrue(notes)
                        for note in notes:
                            self.assertEqual(text.count(note), 1)
                    self.assertEqual(without_host_binding(self, text, host),
                                     canonical_markdown(_host_text(source, adapter, extra_notes=notes)))
            sample = "---\nname: sample\n---\n\n```bash\necho Bash\n```\nAgent SDK role = 'sonnet'\n"
            bound = _host_text(sample, adapter, operational_binding=_operational_binding(adapter, ADAPTERS))
            self.assertEqual(without_host_binding(self, bound, host), _host_text(sample, adapter))

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
        text = self.render_in_memory_fixture("copilot")["agents/inspector.agent.md"]
        meta, _ = _frontmatter(text)
        self.assertNotIn("tools", meta)
        self.assertNotIn("tools: ['search']", text)
        self.assertIsNone(_copilot_tools(None))

    def test_copilot_coordinator_allowlist_retains_declared_mcp_servers(self):
        # Since 38.0.0 the coordinator that loads a server-declaring provider's
        # method is a daodan entry: map-code loads codebase-map's map-method, and
        # get-second-opinion loads peer-review's review protocol (which calls
        # `mcp__peer-review__peer_ask`) and moe's deliberation (which calls
        # moe_ask). An explicit Copilot tools list filters MCP, so each entry keeps
        # its providers' servers and no server outside its local dependency closure.
        registry = plugin_registry()
        closure, pending = set(), list(registry[ENTRY].required_dependencies)
        while pending:
            name = pending.pop()
            if name in registry and name not in closure:
                closure.add(name)
                pending.extend(registry[name].required_dependencies)
        declared = {server.name for name in closure for server in registry[name].mcp_servers}
        rendered = self.render_in_memory(ENTRY, "copilot")
        for workflow, servers in (("map-code", {"codebase-map"}),
                                  ("get-second-opinion", {"peer-review", "moe"})):
            with self.subTest(workflow=workflow):
                meta, _ = _frontmatter(rendered[f"agents/{workflow}-coordinator.agent.md"])
                for server in servers:
                    self.assertIn(f"'{server}/*'", meta["tools"])
                self.assertNotIn("'*'", meta["tools"])
                self.assertNotIn("unrelated-server", meta["tools"])
        for name, text in rendered.items():
            if name.endswith("-coordinator.agent.md"):
                with self.subTest(coordinator=name):
                    meta, _ = _frontmatter(text)
                    self.assertLessEqual(set(re.findall(r"'([^'/]+)/\*'", meta["tools"])), declared)
        plain = self.render_in_memory_fixture("copilot")
        meta, _ = _frontmatter(plain["agents/review-coordinator.agent.md"])
        self.assertNotIn("/*", meta["tools"])
        binding = _operational_binding(load_adapter(ADAPTERS, "copilot"), ADAPTERS)
        self.assertIn("agent allowlist alias", binding)
        self.assertIn("task", binding)
        self.assertIn("actually registered", binding)

    def test_pi_dispatch_skill_bindings_distinguish_logical_and_registry_identity(self):
        # Since 38.0.0 the inline dispatch resource ships with daodan's entries.
        rendered = self.render_in_memory(ENTRY, "pi")
        text = rendered["contracts/dispatch/testing/test-suite-auditor.md"]
        self.assertIn("`testing:test-hygiene` -> compiled registry name `test-hygiene`", text)
        self.assertIn("at `skills/test-hygiene/SKILL.md` inside the owner's package", text)
        self.assertIn("declared logical skill identities", text)
        self.assertIn("provider paths in the active inventory", text)
        self.assertNotIn("registered skills are `testing:", text)
        self.assertNotIn("qualify it with that owner's namespace", text)

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
        self.assertIn("'edit'", meta["tools"])
        # API review persists its assigned report, so it must retain write access.
        api = self.render_in_memory("senior-review", "copilot")["agents/api-contract-auditor.agent.md"]
        api_meta, _ = _frontmatter(api)
        self.assertIn("'edit'", api_meta["tools"])
        readonly_tools = _copilot_tools("Read, Glob, Grep, Bash")
        self.assertIn("'runCommands'", readonly_tools)
        self.assertNotIn("'edit'", readonly_tools)


if __name__ == "__main__":
    unittest.main()
