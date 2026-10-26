"""What each host package must say, checked on the real kernels.

These tests render `codebase-map`, `senior-review` and the `daodan` entry plugin
for every host and read the result the way the host's agent would. Since
marketplace 38.0.0 every command is a `daodan` workflow: the harness tests read
those entries, and the order a method owns (the team map's waves) is read from
the method unit the entry loads. They exist because the first
cross-host review of `codebase-map` found four things the compiler got wrong
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
from host_binding_assertions import canonical_markdown, without_host_binding, loaded_instruction_text

ADAPTERS = REPO_ROOT / "adapters"
MAP = REPO_ROOT / "plugins/codebase-map"
REVIEW = REPO_ROOT / "plugins/senior-review"
ENTRY = REPO_ROOT / "plugins/daodan"
LOOP = tuple(REPO_ROOT / "plugins" / name for name in ("peer-review", "moe", "project-delivery", "project-lifecycle"))
MARKETING = REPO_ROOT / "plugins/digital-marketing"
RESEARCH = REPO_ROOT / "plugins/research"
FIXTURE = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"

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
        registry = {path.parent.name: load_plugin(path.parent)
                    for path in (REPO_ROOT / "plugins").glob("*/plugin.toml")}
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            for plugin_root in (MAP, REVIEW, ENTRY, *LOOP, MARKETING, RESEARCH):
                plugin = registry[plugin_root.name]
                staging = cls.temp / host / plugin.name
                render_plugin(plugin, adapter, staging, adapters_root=ADAPTERS, plugin_registry=registry)
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

    # -- dispatch plan -----------------------------------------------------

    def test_the_map_entry_binds_every_isolated_map_worker_on_every_host(self):
        # The map's procedure belongs to its entry units; the command binds the
        # workers they dispatch, in isolated contexts, behind the delivery rules.
        for host in HOSTS:
            with self.subTest(host=host):
                text = self.harness(host, "daodan", "map-code")
                plan = text[text.index("Dispatch plan:"):text.index("## Method")]
                phases = re.findall(r"^\d+\. `([a-z-]+)`:", plan, re.MULTILINE)
                self.assertEqual(phases, ["prepare", "execute"])
                self.assertIn("required", text.split("Dispatch plan:", 1)[0])
                for role in ("map-analyst", "partition-structure-worker", "partition-behavior-worker",
                             "partition-quality-worker", "partition-synthesizer",
                             "semantic-interconnect-mapper"):
                    self.assertIn(f"codebase-map:{role}", text)
                for unit in ("references/entry-analyze.md", "references/entry-team-analyze.md",
                             "references/deepen.md"):
                    self.assertIn(unit, text)
                self.assertIn("An empty final message or", text)
                self.assertIn("worker stop remains missing delivery", text)

    def test_the_team_map_order_and_barriers_are_owned_by_its_entry_unit(self):
        # Before 38.0.0 the team command's phase graph rendered this order; the
        # entry unit that the map command loads states it on every host.
        for host in HOSTS:
            with self.subTest(host=host):
                unit = _read(self.package(host, "codebase-map")
                             / "skills/map-method/references/entry-team-analyze.md")
                prose = " ".join(unit.split())
                self.assertIn("every partition worker runs in its own context and owns exactly one partition directory", prose)
                self.assertIn("Wave 2 starts only after every Wave 1 worker has been recorded delivered or failed", prose)
                self.assertIn("synthesis runs only after every partition has been accounted for", prose)
                self.assertIn("**Execute phases in order.**", prose)
                headings = [line for line in unit.splitlines() if line.startswith("## Phase ")]
                self.assertEqual([heading.split(":")[0] for heading in headings],
                                 ["## Phase 0", "## Phase 1", "## Phase 2", "## Phase 3", "## Phase 4"])
                self.assertIn("Interconnect", headings[3])
                self.assertIn("Synthesis", headings[2])

    def test_composed_classic_analyst_binding_uses_the_canonical_owner_on_every_host(self):
        for host in HOSTS:
            with self.subTest(host=host):
                package = self.package(host, "daodan")
                text = self.harness(host, "daodan", "review-branch")
                self.assertNotIn("codebase-xray:map-analyst", text)
                resource = package / "contracts/dispatch/codebase-map/map-analyst.md"

                if host in {"codex", "pi"}:
                    self.assertIn("read `contracts/dispatch/codebase-map/map-analyst.md`", text)
                    role = _read(resource)
                    self.assertIn("Owner: codebase-map:map-analyst", role)
                    self.assertIn("# Classic analysis owner", role)
                    self.assertIn("Ask no questions.", role)
                    self.assertIn("Never publish", role)
                    self.assertIn("<codebase-map-plugin-root>/skills/map-method/", role)
                    self.assertNotIn("<codebase-xray-plugin-root>", role)
                    source = _read(MAP / "roles/map-analyst.md")
                    expected = source.split("\n---\n", 1)[1].lstrip("\n").replace(
                        CLAUDE_ROOT, "<codebase-map-plugin-root>"
                    )
                    self.assertEqual(role[role.index("# Classic analysis owner"):],
                                     canonical_markdown(expected))
                else:
                    self.assertIn("dispatch the installed `codebase-map:map-analyst` agent", text)
                    self.assertFalse(resource.exists())

    def test_classic_entries_reject_hosts_without_isolated_dispatch(self):
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            shared_only = replace(adapter, strategies=tuple(
                replace(strategy, isolated=False) for strategy in adapter.strategies
            ))
            for root in (ENTRY,):
                plugin = load_plugin(root)
                classic = replace(plugin, workflows=tuple(
                    workflow for workflow in plugin.workflows if workflow.name == "map-code"
                ))
                with self.subTest(host=host, plugin=plugin.name):
                    self.assertIn(resolve_support(classic, adapter).state, {"native", "adapted"})
                    unavailable = resolve_support(classic, shared_only)
                    self.assertEqual(unavailable.state, "unsupported")
                    self.assertEqual(unavailable.workflow_strategies, (("map-code", "none"),))
                    self.assertEqual(unavailable.missing_capabilities, ())

                    for capability in ("contexts.isolate", "roles.dispatch"):
                        bindings = dict(adapter.bindings)
                        bindings[capability] = replace(bindings[capability], state="unsupported")
                        unavailable = resolve_support(classic, replace(adapter, bindings=bindings))
                        self.assertEqual(unavailable.state, "unsupported")
                        self.assertEqual(unavailable.missing_capabilities, (capability,))

    def test_fanout_per_selection_is_rendered_per_item_on_every_host(self):
        for host in HOSTS:
            with self.subTest(host=host):
                text = self.harness(host, "daodan", "check-health")
                self.assertIn(
                    "one `senior-review:cleanup-auditor` per item of `selection:cleanup`", text
                )
                self.assertIn(
                    "one `testing:test-suite-auditor` per item of `selection:tests`", text
                )
                self.assertNotIn("once each: `testing:test-suite-auditor`", text)

    def test_dispatch_plan_keeps_phase_order_and_barriers(self):
        # The plan consolidates every audit: it may start only when each audit
        # phase has recorded all its workers delivered or failed.
        audits = ["audit-cleanup", "audit-tests", "audit-structure", "audit-instructions", "audit-workspace"]
        for host in HOSTS:
            with self.subTest(host=host):
                text = self.harness(host, "daodan", "check-health")
                plan = text[text.index("Dispatch plan") : text.index("## Method")]
                order = [
                    match.group(1)
                    for match in re.finditer(r"^\d+\. `([a-z-]+)`:", plan, flags=re.MULTILINE)
                ]
                self.assertEqual(order, ["prepare", *audits, "plan"])
                lines = {name: next(line for line in plan.splitlines() if line.split(". ", 1)[-1].startswith(f"`{name}`:"))
                         for name in order}
                for audit in audits:
                    self.assertIn("barrier `all-delivered`", lines[audit])
                    self.assertIn("needs `prepare`", lines[audit])
                self.assertIn("needs " + ", ".join(f"`{audit}`" for audit in audits) + ";", lines["plan"])
                self.assertIn("`plan`: runs in the orchestrating context", lines["plan"])
                self.assertIn("`prepare`: runs in the orchestrating context", plan)

    def test_graph_mapping_obligations_survive_in_loaded_roles_and_nested_methods_on_every_host(self):
        for host in HOSTS:
            with self.subTest(host=host):
                package = self.package(host, "codebase-map")
                role_layout = load_adapter(ADAPTERS, host).layout["roles"]
                roles = {}
                for role in ("map-analyst", "semantic-interconnect-mapper",
                             "partition-structure-worker", "partition-behavior-worker"):
                    relative = role_layout.replace("${plugin}", "codebase-map").replace("${role}", role)
                    roles[role] = loaded_instruction_text(self, package / relative, host)
                    self.assertIn("references/evidence.md", roles[role])
                    self.assertIn("before: Maintained documentation", roles[role])

                # These are the actual resources reached through the rendered
                # roles, rather than matching hashes or inspecting kernel prose.
                evidence = _read(package / "skills/map-method/references/evidence.md")
                core = " ".join(evidence.split("## Maintained documentation", 1)[0].split())
                self.assertIn("Before mapping structure, calls or flows, run:", core)
                self.assertRegex(evidence, r'python "[^"\n]+/scripts/source_reader\.py" graph')
                self.assertIn("question-relevant candidate `requests`", core)
                self.assertIn("read them with `source_reader.py read` before claims", core)
                self.assertIn("AST metadata is not deep reading", core)
                self.assertIn("static resolution does not cover dynamic dispatch or arbitrary receiver types", core)
                self.assertIn("Cycles, transitive importers and PageRank guide reading, not criticality or incremental invalidation", core)
                self.assertIn("checks source identity and parser fingerprint", core)
                self.assertIn("neither reparses nor writes a snapshot", core)
                self.assertIn("`truncated`", core)

                mapper = " ".join(roles["semantic-interconnect-mapper"].split())
                self.assertIn("First query `source_reader.py graph source_manifest`", mapper)
                self.assertIn("`--hops 2` or `--hops 3`", mapper)
                self.assertIn("Keep unresolved targets explicit", mapper)
                self.assertIn("a resolved edge does not verify its contract", mapper)
                self.assertIn("through source blocks before contract claims", mapper)
                self.assertIn("Static resolution and evidence status are separate", mapper)
                for role in ("partition-structure-worker", "partition-behavior-worker"):
                    worker = " ".join(roles[role].split())
                    self.assertIn("`source_reader.py graph` on `source_manifest`", worker)
                    self.assertIn("requests through `source_reader.py read`", worker)
                    self.assertIn("unresolved/AST coverage gaps", worker)
                analyst = roles["map-analyst"]
                self.assertIn("references/phases-1-2.md", analyst)
                self.assertIn("references/phases-3-4.md", analyst)
                for phase in ("phases-1-2.md", "phases-3-4.md"):
                    text = _read(package / "skills/map-method/references" / phase)
                    self.assertIn("## Source reading", text)

    def test_static_fanout_still_dispatches_once_each(self):
        # No shipped kernel declares a static fan-out since the review's roster
        # became computed; the compiler path stays pinned on the valid fixture.
        with tempfile.TemporaryDirectory() as temporary:
            staging = Path(temporary) / "example"
            render_plugin(load_plugin(FIXTURE), load_adapter(ADAPTERS, "claude"), staging,
                          adapters_root=ADAPTERS)
            text = _read(staging / "commands/review.md")
        self.assertIn("`inspect`: `inspector`, once each", text)

    # -- copilot coordinator -----------------------------------------------

    def test_copilot_coordinator_gets_the_tools_its_capabilities_need(self):
        meta = _frontmatter(self.harness("copilot", "daodan", "map-code"))
        tools = meta["tools"]
        for tool in ("'agent'", "'search'", "'edit'", "'runCommands'"):
            self.assertIn(tool, tools)

    # -- plugin root -------------------------------------------------------

    def test_claude_keeps_its_own_plugin_root_variable(self):
        texts = self.markdown("claude", "codebase-map")
        self.assertTrue(any(CLAUDE_ROOT in text for text in texts.values()))

    def test_other_hosts_never_see_the_claude_plugin_root_variable(self):
        for host in ("copilot", "codex"):
            with self.subTest(host=host):
                for name, text in self.markdown(host, "codebase-map").items():
                    self.assertNotIn("CLAUDE_PLUGIN_ROOT", text, name)

    def test_other_hosts_explain_their_plugin_root_where_they_use_it(self):
        expectations = {
            "copilot": ("${PLUGIN_ROOT}", "plugin.json"),
            "codex": ("<plugin-root>", ".codex-plugin/plugin.json"),
        }
        for host, (reference, manifest) in expectations.items():
            with self.subTest(host=host):
                texts = self.markdown(host, "codebase-map")
                using = {name: text for name, text in texts.items() if reference in text}
                self.assertTrue(using, f"{host}: nothing references {reference}")
                for name, text in using.items():
                    self.assertIn(manifest, text, name)
                skill = texts["skills/map-method/SKILL.md"]
                self.assertIn(f"{reference}/skills/map-method/scripts/", skill)

    # -- workflow frontmatter and arguments --------------------------------

    def test_claude_classic_workflow_preserves_kernel_method_under_execution_binding(self):
        rendered = _read(self.package("claude", "daodan") / "commands/map-code.md")
        kernel = _read(ENTRY / "workflows/map-code.md").replace("\r\n", "\n")
        body = without_host_binding(self, rendered, "claude")
        kernel_body = kernel.split("\n---\n", 1)[1].lstrip("\n")
        self.assertEqual(body.split("## Method\n\n", 1)[1], canonical_markdown(kernel_body))

    def test_codex_flat_workflow_has_skill_frontmatter(self):
        text = _read(self.package("codex", "daodan") / "skills/record-decision-workflow/SKILL.md")
        meta = _frontmatter(text)
        # Codex registers skills by frontmatter name, so the name carries the
        # directory suffix: a plugin with a skill and a workflow of one name
        # (digital-marketing's brand-naming before marketplace 29.0.0) would
        # otherwise register two skills under it.
        self.assertEqual(meta["name"], "record-decision-workflow")
        self.assertIn("description", meta)
        self.assertNotIn("argument-hint", meta)
        self.assertIn("Arguments: `<decision>`", text)

    def test_copilot_flat_workflow_keeps_the_argument_hint(self):
        text = _read(self.package("copilot", "daodan") / "prompts/record-decision.prompt.md")
        meta = _frontmatter(text)
        self.assertEqual(meta["name"], "record-decision")
        self.assertIn("argument-hint", meta)
        self.assertIn("<decision>", meta["argument-hint"])

    def test_other_hosts_never_see_the_claude_arguments_variable(self):
        for host in ("copilot", "codex"):
            with self.subTest(host=host):
                for name, text in self.markdown(host, "daodan").items():
                    self.assertNotRegex(text, r"\$ARGUMENTS\b", name)
                harness = self.harness(host, "daodan", "map-code")
                self.assertIn("<arguments>", harness)
                self.assertIn("Wherever `<arguments>` appears", harness)

    # -- opencode ----------------------------------------------------------

    def test_independent_derivation_cannot_consume_either_analysis_store(self):
        for host in HOSTS:
            with self.subTest(host=host):
                layout = load_adapter(ADAPTERS, host).layout["roles"]
                relative = layout.replace("${plugin}", "senior-review").replace("${role}", "premise-auditor")
                body = _read(self.package(host, "senior-review") / relative)
                mode = body.split("## Mode 1:", 1)[1].split("## Mode 2:", 1)[0]
                self.assertIn("`.codebase-map/` in any form", mode)
                self.assertIn("`.codebase-xray/` in any form", mode)
                self.assertIn("stop and report the contamination", mode)
                self.assertNotIn("references/migration.md", body)

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
        text = self.harness("opencode", "daodan", "review-branch")
        self.assertIn("`subagent` tool", text)
        self.assertIn('agent: "daodan:<role>"', text)
        self.assertIn("external roles use their owner's prefix", " ".join(text.split()))
        self.assertIn("`senior-review:code-auditor`: dispatch the installed `senior-review:code-auditor` agent", text)
        self.assertIn("background: true", text)
        self.assertNotIn("pi install", text)
        self.assertRegex(text, r"\$ARGUMENTS\b")

    def test_opencode_never_sees_the_claude_plugin_root_variable(self):
        texts = self.markdown("opencode", "codebase-map")
        for name, text in texts.items():
            self.assertNotIn("CLAUDE_PLUGIN_ROOT", text, name)
        self.assertIn(
            "<plugin-root>/skills/map-method/scripts/", texts["skills/map-method/SKILL.md"]
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
        for plugin in ("daodan", "codebase-map", "senior-review", "peer-review", "moe", "project-delivery", "project-lifecycle", "digital-marketing", "research"):
            for path in self.package("opencode", plugin).glob("commands/*.md"):
                self.assertIsNone(re.search(r"(?m)^!`", _read(path)), path)


class ReportRenderingHostContracts(unittest.TestCase):
    """Read consumer methods and resources from fresh source renderings."""

    CONSUMERS = ("digital-marketing", "codebase-map", "senior-review")
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
        "codebase-map": {
            "skills/map-method/references/human-view.md": "--profile report",
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
                host, cls.plugins, "1.0.0", packages, layout=adapter.layout,
                plugin_registry=registry))

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
                self.assertIn("A Codebase Map caller stays static", prose)
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
        # The map command's coordinator runs the entry units of `map-method`:
        # those units, not the command, own the view and its completion gate.
        for host in HOSTS:
            with self.subTest(host=host):
                package = self.package(host, "codebase-map")
                references = package / "skills/map-method/references"
                coordinator = _read(references / "entry-team-analyze.md")
                phase = _read(references / "phase-7.md")
                view = _read(references / "human-view.md")
                classic = _read(references / "entry-analyze.md")
                coordinator_prose = " ".join(coordinator.split())
                phase_prose = " ".join(phase.split())
                classic_prose = " ".join(classic.split())
                view_prose = " ".join(view.split())
                self.assertIn("references/human-view.md", coordinator)
                self.assertIn("references/human-view.md", phase)
                self.assertIn("only the coordinator loads", coordinator_prose)
                self.assertIn("Workers never load presentation instructions", coordinator_prose)
                self.assertIn("only the entry coordinator loads", phase_prose)
                self.assertIn("Workers never load presentation instructions", phase_prose)
                self.assertIn("Exercised at runtime: none. This is static analysis", phase)
                self.assertIn("Files read in depth:", phase)
                self.assertIn("report-rendering:report-renderer", view)
                self.assertIn("workers and the synthesizer do not load this reference or generate a separate UI",
                              view_prose)
                self.assertIn("Do not add browser exercise to the Codebase Map", view_prose)
                self.assertIn("07-final-report.md", view)
                self.assertIn("07-final-report.html", view)
                self.assertIn("--root $RUN_DIR", view)
                self.assertIn("The entry coordinator marks the run complete only after native delivery and every requested view pass their gates",
                              phase_prose)
                self.assertIn("only this coordinator loads `human-view.md`", classic_prose)
                self.assertIn("Verify native output and every requested view before completion", classic_prose)
                self.assertIn("requested view failure keeps the run open", classic_prose)
                self.assertIn("explicitly requested HTML deliverable remains open", view_prose)


if __name__ == "__main__":
    unittest.main()
