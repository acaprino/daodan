"""What each host package must say, checked on the real kernels.

These tests render `codebase-xray` and `senior-review` for every host and read
the result the way the host's agent would. They exist because the first
cross-host review of `codebase-xray` found four things the compiler got wrong
for Codex and Copilot while Claude looked fine: a harness header that said
"once each" over a workflow that fans out per partition, a Copilot coordinator
that could not write, `${CLAUDE_PLUGIN_ROOT}` passed through to hosts that do
not define it, and Claude command frontmatter copied into Codex skills.
"""

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
from host_binding_assertions import canonical_markdown, without_host_binding

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
        # The synthesizer consolidates 01..07 and leaves 08 to the mapper, which reads
        # that consolidated output: synthesis must close before interconnect starts.
        for host in HOSTS:
            with self.subTest(host=host):
                text = self.harness(host, "codebase-xray", "team-analyze")
                plan = text[text.index("Dispatch plan") : text.index("## Method")]
                order = [
                    match.group(1)
                    for match in re.finditer(r"^\d+\. `([a-z-]+)`:", plan, flags=re.MULTILINE)
                ]
                self.assertEqual(
                    order,
                    ["partition-selection", "structure", "behavior", "quality", "synthesis", "interconnect"],
                )
                lines = {name: next(line for line in plan.splitlines() if line.split(". ", 1)[-1].startswith(f"`{name}`:"))
                         for name in order}
                self.assertIn("`structure`: one `partition-structure-worker`", plan)
                self.assertIn("needs `structure`", plan)
                self.assertIn("barrier `all-delivered`", plan)
                self.assertIn("`synthesis`: one `partition-synthesizer`", lines["synthesis"])
                self.assertIn("needs `behavior`, `quality`;", lines["synthesis"])
                self.assertNotIn("interconnect", lines["synthesis"])
                self.assertIn("`interconnect`: one `semantic-interconnect-mapper`", lines["interconnect"])
                self.assertIn("needs `synthesis`", lines["interconnect"])
                self.assertIn("consumes `artifact:xray-report`", lines["interconnect"])
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

    def test_claude_flat_workflow_preserves_kernel_under_execution_binding(self):
        rendered = _read(self.package("claude", "codebase-xray") / "commands/analyze.md")
        kernel = _read(XRAY / "workflows/analyze.md").replace("\r\n", "\n")
        body = without_host_binding(self, rendered, "claude")
        self.assertEqual(body, canonical_markdown(kernel))

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


class ReportRenderingHostContracts(unittest.TestCase):
    """Read consumer methods and resources from fresh source renderings."""

    CONSUMERS = ("digital-marketing", "codebase-xray", "senior-review")
    PROVIDER = "report-rendering"
    SKILL = "skills/report-renderer/SKILL.md"
    RESOURCES = ("skills/report-renderer/scripts/render_report.py",
                 "skills/report-renderer/assets/report.css",
                 "skills/report-renderer/assets/report.js")
    HOOKS = {
        "digital-marketing": {
            "skills/brand-naming-method/SKILL.md": "--profile naming",
            "skills/brand-naming-method/references/report-template.md": "naming",
        },
        "codebase-xray": {
            "skills/xray-method/references/human-view.md": "--profile report",
        },
        "senior-review": {
            "skills/review-consolidation/SKILL.md": "--profile review",
            "skills/review-quality-gates/references/code-review-output.md": "--profile review",
            "skills/review-consolidation/references/team-review.md": "--profile review",
            "skills/review-consolidation/references/pr-review.md": "--profile review",
        },
    }

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="daodan-report-hosts-")
        cls.addClassCleanup(cls.temp.cleanup)
        registry = {path.parent.name: load_plugin(path.parent)
                    for path in (REPO_ROOT / "plugins").glob("*/plugin.toml")}
        cls.plugins = [registry[name] for name in (*cls.CONSUMERS, cls.PROVIDER)]
        cls.packages, cls.catalogs = {}, {}
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            packages = {}
            for plugin in cls.plugins:
                target = Path(cls.temp.name) / host / plugin.name
                render_plugin(plugin, adapter, target, adapters_root=ADAPTERS,
                              plugin_registry=registry)
                packages[plugin.name] = target
                cls.packages[(host, plugin.name)] = target
            cls.catalogs[host] = json.loads(render_catalog(
                host, cls.plugins, "1.0.0", packages, layout=adapter.layout))

    def package(self, host, plugin):
        return self.packages[(host, plugin)]

    def test_provider_is_an_actual_registered_skill_with_the_same_shipped_runtime(self):
        kernel = REPO_ROOT / "plugins" / self.PROVIDER

        for host in HOSTS:
            with self.subTest(host=host):
                package = self.package(host, self.PROVIDER)
                skill = _read(package / self.SKILL)
                self.assertEqual(_frontmatter(skill)["name"], "report-renderer")
                self.assertIn("render_report.py", skill)
                self.assertIn("--input", skill)
                self.assertIn("--output", skill)
                self.assertIn("--root", skill)
                root_reference = load_adapter(ADAPTERS, host).layout["plugin_root_reference"]
                self.assertIn(f'{root_reference}/skills/report-renderer/scripts/render_report.py', skill)
                for resource in self.RESOURCES:
                    self.assertEqual((package / resource).read_bytes(), (kernel / resource).read_bytes(),
                                     f"{host}: runtime resource did not ship intact: {resource}")
                catalog = self.catalogs[host]
                if host == "opencode":
                    registered = catalog["daodan"]["plugins"][self.PROVIDER]["skills"]
                    self.assertTrue(any(entry["id"] == "report-rendering:report-renderer"
                                        and entry["file"] == self.SKILL for entry in registered))
                elif host == "pi":
                    self.assertIn("./exports/pi/plugins/*/skills", catalog["pi"]["skills"])
                    self.assertIn("exact registered names", " ".join(skill.split()))
                else:
                    registered = next(entry for entry in catalog["plugins"]
                                      if entry["name"] == self.PROVIDER)
                    self.assertIn("./skills/report-renderer", registered["skills"])

    def test_consumers_require_the_provider_in_each_native_catalog(self):
        for host in HOSTS:
            for consumer in self.CONSUMERS:
                with self.subTest(host=host, consumer=consumer):
                    plugin = next(plugin for plugin in self.plugins if plugin.name == consumer)
                    self.assertIn(self.PROVIDER, plugin.required_dependencies)
                    catalog = self.catalogs[host]
                    if host == "opencode":
                        registered = catalog["daodan"]["plugins"][consumer]
                        self.assertIn(self.PROVIDER, registered["dependencies"])
                    elif host != "pi":
                        registered = next(entry for entry in catalog["plugins"]
                                          if entry["name"] == consumer)
                        self.assertIn(self.PROVIDER, registered["dependencies"])
                    # Pi filters the whole package; its binding must preserve
                    # local closure even though its catalog names no dependency.
                    text = _read(self.package(host, consumer) / next(iter(self.HOOKS[consumer])))
                    if host == "pi":
                        self.assertIn("full local dependency closure", text)
                    self.assertNotRegex(text, r"(?i)if report-rendering (?:is )?installed")

    def test_required_renderer_execution_cannot_fall_back_when_host_shell_is_unavailable(self):
        provider = next(plugin for plugin in self.plugins if plugin.name == self.PROVIDER)

        for host in HOSTS:
            with self.subTest(host=host):
                adapter = load_adapter(ADAPTERS, host)
                supported = resolve_support(provider, adapter)
                bindings = dict(adapter.bindings)
                bindings["shell.execute"] = replace(bindings["shell.execute"], state="unsupported")

                unavailable = resolve_support(provider, replace(adapter, bindings=bindings))

                self.assertIn(supported.state, {"native", "adapted"})
                self.assertEqual(unavailable.state, "unsupported")
                self.assertEqual(unavailable.missing_capabilities, ("shell.execute",))

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

    def test_provider_verification_does_not_add_browser_runtime_to_static_xray(self):
        for host in HOSTS:
            with self.subTest(host=host):
                skill = _read(self.package(host, self.PROVIDER) / self.SKILL)
                prose = " ".join(skill.split())

                self.assertIn("structural verification and needs no browser", prose)
                self.assertIn("a browser is optional for this renderer", prose)
                self.assertIn("An X-ray caller stays static", prose)
                self.assertIn("Never add a browser exercise or product runtime step to its workflow", prose)

    def test_final_method_and_nested_reference_hooks_load_the_registered_provider(self):
        for host in HOSTS:
            for consumer, hooks in self.HOOKS.items():
                for resource, profile in hooks.items():
                    with self.subTest(host=host, consumer=consumer, resource=resource):
                        text = _read(self.package(host, consumer) / resource)
                        self.assertIn("report-rendering:report-renderer", text)
                        self.assertIn(profile, text)
                        self.assertNotIn("plugins/report-rendering/", text,
                                         "Consumers must resolve the installed provider, not a checkout")
                        self.assertNotRegex(text, r"(?i)report-rendering[^\n]*(?:optional dependency|fallback)")

    def test_xray_coordinator_owns_the_view_and_preserves_static_coverage(self):
        entrypoints = {
            "claude": "commands/team-analyze.md",
            "copilot": "agents/team-analyze-coordinator.agent.md",
            "codex": "skills/team-analyze-workflow/SKILL.md",
            "pi": "prompts/codebase-xray-team-analyze.md",
            "opencode": "commands/team-analyze.md",
        }

        for host in HOSTS:
            with self.subTest(host=host):
                package = self.package(host, "codebase-xray")
                coordinator = _read(package / entrypoints[host])
                phase = _read(package / "skills/xray-method/references/phase-7.md")
                view = _read(package / "skills/xray-method/references/human-view.md")
                coordinator_prose = " ".join(coordinator.split())
                phase_prose = " ".join(phase.split())
                view_prose = " ".join(view.split())
                self.assertIn("references/human-view.md", coordinator)
                self.assertIn("references/human-view.md", phase)
                self.assertIn("only the coordinator loads", coordinator_prose)
                self.assertIn("Workers never load presentation instructions", coordinator_prose)
                self.assertIn("only the run owner loads", phase_prose)
                self.assertIn("Workers never load presentation instructions", phase_prose)
                self.assertIn("Exercised at runtime: none. This is static analysis", phase)
                self.assertIn("Files read in depth:", phase)
                self.assertIn("report-rendering:report-renderer", view)
                self.assertIn("workers and the synthesizer do not load this reference or generate a separate UI",
                              view_prose)
                self.assertIn("Do not add browser exercise to the X-ray", view_prose)
                self.assertIn("07-final-report.md", view)
                self.assertIn("07-final-report.html", view)
                self.assertIn("--root $RUN_DIR", view)
                self.assertIn("Classic owner: set `$RUN_DIR/state.json`", phase_prose)
                self.assertIn("status to `complete` only after native Markdown and every requested view are delivered", phase_prose)
                self.assertIn("explicitly requested HTML deliverable remains open", view_prose)


if __name__ == "__main__":
    unittest.main()
