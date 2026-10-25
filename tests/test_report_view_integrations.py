"""Final-report view contracts for knowledge, lifecycle and testing consumers.

The existing test_daodan_host_rendering.py owns provider registration/assets and
the earlier naming, X-ray and review consumers. This justified contract-layer
split owns the newly composed final-report paths, run boundaries and delivery
authority. It renders real consumer packages and reads the instructions workers
and coordinators receive; it does not claim that prose is a runtime scheduler.
"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter
from scripts.daodan.catalogs import render_catalog
from scripts.daodan.load import load_plugin
from scripts.daodan.render import render_plugin
from host_binding_assertions import without_host_binding


CONSUMERS = {
    "project-knowledge": {
        "view": "skills/project-knowledge/references/human-view.md",
        "profile": "review",
        "hooks": (
            "skills/project-knowledge/SKILL.md",
            "skills/instructions-method/SKILL.md",
            "skills/readme-craft/SKILL.md",
        ),
    },
    "project-delivery": {
        "view_owner": "report-rendering",
        "view": "skills/report-renderer/references/project-run-view.md",
        "reference": "references/project-run-view.md",
        "profile": "report",
        "hooks": ("skills/delivery-method/SKILL.md",),
    },
    "project-lifecycle": {
        "view_owner": "report-rendering",
        "view": "skills/report-renderer/references/project-run-view.md",
        "reference": "references/project-run-view.md",
        "profile": "report",
        "hooks": (
            "skills/assess-method/SKILL.md",
            "skills/maintainer-method/references/campaign.md",
            "skills/handover-method/SKILL.md",
        ),
    },
    "testing": {
        "view": "skills/test-remediation-method/references/human-view.md",
        "profile": "review",
        "hooks": (
            "skills/test-remediation-method/references/audit.md",
            "skills/test-remediation-method/references/consolidate.md",
        ),
    },
}


def normalized(text):
    return " ".join(text.split())


def markdown_section(text, heading):
    match = re.search(rf"(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text)
    if match is None:
        raise AssertionError(f"Missing native method checkpoint: {heading}")
    return normalized(match.group(1))


def assert_requested_view_blocks_closure(case, text):
    """Require the missing-delivery rule in the paragraph that owns failure."""
    paragraphs = [normalized(part) for part in text.split("\n\n")]
    failure = next((part for part in paragraphs
                    if re.search(r"(?i)requested[^.]*HTML[^.]*missing|"
                                 r"requested[^.]*missing[^.]*HTML", part)), None)
    case.assertIsNotNone(failure, "Requested missing HTML needs explicit accounting")
    case.assertRegex(failure, r"(?i)(?:deliverable|delivery|run)[^.]*open")
    case.assertRegex(failure, r"(?i)native (?:source|output|report)")


class ReportViewIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="daodan-report-consumers-")
        cls.addClassCleanup(cls.temp.cleanup)
        registry = {path.parent.name: load_plugin(path.parent)
                    for path in (REPO_ROOT / "plugins").glob("*/plugin.toml")}
        cls.plugins = [registry[name] for name in CONSUMERS]
        rendered = [*cls.plugins, registry["report-rendering"]]
        cls.packages, cls.catalogs = {}, {}
        adapters = REPO_ROOT / "adapters"
        for host in HOSTS:
            adapter = load_adapter(adapters, host)
            packages = {}
            for plugin in rendered:
                package = Path(cls.temp.name) / host / plugin.name
                render_plugin(plugin, adapter, package, adapters_root=adapters,
                              plugin_registry=registry)
                packages[plugin.name] = package
                cls.packages[(host, plugin.name)] = package
            cls.catalogs[host] = json.loads(render_catalog(
                host, rendered, "1.0.0", packages, layout=adapter.layout))

    def body(self, host, consumer, resource):
        path = self.packages[(host, consumer)] / resource
        return without_host_binding(self, path.read_text(encoding="utf-8"), host)

    def view(self, host, consumer):
        contract = CONSUMERS[consumer]
        return self.body(host, contract.get("view_owner", consumer), contract["view"])

    def test_each_consumer_requires_the_registered_provider_on_every_host(self):
        for host in HOSTS:
            for plugin in self.plugins:
                with self.subTest(host=host, consumer=plugin.name):
                    self.assertIn("report-rendering", plugin.required_dependencies)
                    catalog = self.catalogs[host]

                    if host == "opencode":
                        entry = catalog["daodan"]["plugins"][plugin.name]
                        self.assertIn("report-rendering", entry["dependencies"])
                    elif host == "pi":
                        self.assertIn("./exports/pi/plugins/*/skills", catalog["pi"]["skills"])
                        text = (self.packages[(host, plugin.name)] /
                                CONSUMERS[plugin.name]["hooks"][0]).read_text(encoding="utf-8")
                        self.assertIn("full local dependency closure", text)
                    else:
                        entry = next(item for item in catalog["plugins"]
                                     if item["name"] == plugin.name)
                        self.assertIn("report-rendering", entry["dependencies"])

                    view = self.view(host, plugin.name)
                    self.assertIn("report-rendering:report-renderer", view)
                    self.assertNotRegex(view, r"(?i)if[^.]*report-rendering[^.]*installed")
                    self.assertNotIn("plugins/report-rendering/", view)

    def test_final_owner_hooks_reach_shipped_on_demand_references(self):
        for host in HOSTS:
            for consumer, contract in CONSUMERS.items():
                with self.subTest(host=host, consumer=consumer):
                    view = normalized(self.view(host, consumer))
                    self.assertRegex(view, r"(?i)coordinator[^.]*loads this reference")
                    self.assertRegex(view, r"(?i)workers[^.]*native")
                    self.assertRegex(view, r"(?i)(?:requests? HTML|HTML is requested)")
                    for hook in contract["hooks"]:
                        with self.subTest(hook=hook):
                            text = normalized(self.body(host, consumer, hook))
                            self.assertIn(contract.get("reference", "references/human-view.md"), text)
                            self.assertIn("coordinator", text)
                            self.assertRegex(text, r"(?i)before[^.]*clos")

    def test_commands_bind_input_output_profile_and_exact_owned_root(self):
        for host in HOSTS:
            for consumer, contract in CONSUMERS.items():
                with self.subTest(host=host, consumer=consumer):
                    text = self.view(host, consumer)
                    commands = re.findall(r"(?m)^python [^\n]+$", text)
                    self.assertEqual(len(commands), 1)
                    command = commands[0]
                    for argument in ("--input", "--output", "--root"):
                        self.assertIn(argument + " ", command)
                    self.assertIn("--profile " + contract["profile"], command)
                    self.assertNotRegex(command, r"(?:work|result)\.json|AGENTS\.md|CLAUDE\.md")
                    prose = normalized(text)
                    self.assertRegex(prose, r"(?i)dedicated[^.]*owned|dedicated[^.]*run directory")
                    self.assertRegex(prose, r"(?i)(?:repository root|shared[^.]*directory|shared artifact)")
                    self.assertIn("--root", prose)

    def test_requested_missing_or_failed_views_cannot_close_any_consumer(self):
        for host in HOSTS:
            for consumer in CONSUMERS:
                with self.subTest(host=host, consumer=consumer):
                    assert_requested_view_blocks_closure(self, self.view(host, consumer))

    def test_a_missing_view_rule_that_closes_the_run_is_rejected(self):
        unsafe = ("If explicitly requested HTML remains missing or failed, close the run. "
                  "Keep the native report available.")

        with self.assertRaises(AssertionError):
            assert_requested_view_blocks_closure(self, unsafe)

    def test_views_preserve_gate_authority_without_browser_or_savings_claims(self):
        for host in HOSTS:
            for consumer in CONSUMERS:
                with self.subTest(host=host, consumer=consumer):
                    prose = normalized(self.view(host, consumer))
                    self.assertRegex(prose, r"(?i)(?:structural checks|structural verification)")
                    self.assertRegex(prose, r"(?i)(?:no browser|browser is optional|needs no browser)")
                    self.assertRegex(prose, r"(?i)(?:claim token savings without|no[^.]*token-saving claim|no[^.]*measured token saving)")
                    self.assertRegex(prose, r"(?i)(?:checkboxes[^.]*view|view[^.]*checkboxes)")
                    self.assertRegex(prose, r"(?i)(?:approve no|neither approve|never accept)")
                    self.assertRegex(prose, r"(?i)(?:complete no workflow check|nor change[^.]*gate results|never[^.]*satisfy gates)")

    def test_instruction_views_use_a_run_report_and_retain_unverified_loading(self):
        for host in HOSTS:
            with self.subTest(host=host):
                prose = normalized(self.view(host, "project-knowledge"))
                self.assertRegex(prose, r"(?i)final run-owned Markdown audit or change summary")
                self.assertIn("AGENTS.md", prose)
                self.assertIn("CLAUDE.md", prose)
                self.assertIn("`work.json`", prose)
                self.assertIn("`result.json`", prose)
                self.assertRegex(prose, r"(?i)coordinator's report.*rather than.*durable document")
                self.assertRegex(prose, r"(?i)canonical/generated destinations")
                self.assertRegex(prose, r"(?i)unperformed reload[^.]*activation or enforcement")
                self.assertRegex(prose, r"(?i)cannot[^.]*satisfy an unavailable gate")
                self.assertRegex(prose, r"(?i)durable files untouched")

    def test_lifecycle_views_preserve_native_dossiers_and_historical_campaign_stages(self):
        for host in HOSTS:
            with self.subTest(host=host):
                view = normalized(self.view(host, "project-lifecycle"))
                self.assertIn("`handover.md`", view)
                self.assertIn("`campaign-final.md`", view)
                self.assertIn("`run-summary.md`", view)
                self.assertRegex(view, r"(?i)never pass JSON to the Markdown renderer")
                self.assertRegex(view, r"(?i)earlier stage checks historical")
                self.assertRegex(view, r"(?i)final current verification")
                self.assertRegex(view, r"(?i)dry-run and stopped outcomes retain[^.]*status")
                self.assertRegex(view, r"(?i)absence of maintenance authorization")
                self.assertRegex(view, r"(?i)earlier stage's closed run are not output roots")

                campaign = self.body(host, "project-lifecycle",
                                     "skills/maintainer-method/references/campaign.md")
                handoff = normalized(campaign[campaign.index("FINAL BINDING AND HANDOFF"):])
                self.assertRegex(handoff, r"(?i)renders campaign-final\.md before closing")
                self.assertRegex(handoff, r"(?i)earlier stage records remain historical evidence")

    def test_audit_only_and_fix_hooks_render_at_their_final_native_checkpoints(self):
        for host in HOSTS:
            with self.subTest(host=host):
                audit = self.body(host, "testing", "skills/test-remediation-method/references/audit.md")
                report = markdown_section(audit, "Step 4: Write TEST_AUDIT.md")
                refresh = markdown_section(audit, "Step 5: Quarantine (only with `--fix`)")
                self.assertRegex(report, r"(?i)without `--fix`[^.]*print the report")
                self.assertIn("references/human-view.md", report)
                self.assertRegex(report, r"(?i)do not proceed to quarantine")
                self.assertRegex(refresh, r"(?i)include the per-batch table[^.]*native section")
                self.assertRegex(refresh, r"(?i)finalize owned audit/ledger edits before[^.]*gating")
                self.assertRegex(refresh, r"(?i)after the refreshed native audit and required gates are final")
                self.assertRegex(refresh, r"(?i)render no intermediate audit")

    def test_consolidation_dry_run_renders_inventory_without_entering_mutation(self):
        for host in HOSTS:
            with self.subTest(host=host):
                consolidation = self.body(host, "testing",
                                          "skills/test-remediation-method/references/consolidate.md")
                inventory = markdown_section(consolidation, "Step 2: Behavior inventory (always, before any code)")
                dry_run = inventory[inventory.index("Under `--dry-run`"):]
                self.assertIn("<output-root>/consolidation.md", dry_run)
                self.assertIn("test-consolidate-report", dry_run)
                self.assertIn("references/human-view.md", dry_run)
                self.assertRegex(dry_run, r"(?i)explicit dry-run status")
                self.assertRegex(dry_run, r"(?i)acceptance, rewrites, removals and mutation gates were not executed")
                self.assertRegex(dry_run, r"(?i)stop here without entering Steps 3 through 7")
                self.assertRegex(dry_run, r"(?i)without[^.]*applying any quarantine change")
                final = markdown_section(consolidation, "Step 8: Report")
                self.assertIn("<output-root>/consolidation.md", final)
                self.assertRegex(final, r"(?i)already-declared final Markdown path")
                self.assertRegex(final, r"(?i)operational JSON remains state, not report content")

    def test_testing_views_keep_native_audit_paths_and_disposition_authority(self):
        for host in HOSTS:
            with self.subTest(host=host):
                prose = normalized(self.view(host, "testing"))
                self.assertIn("TEST_AUDIT.md", prose)
                self.assertIn("findings.md", prose)
                self.assertRegex(prose, r"(?i)shared target directory(?:`[^`]*`|[^.`])*does not become owned")
                self.assertRegex(prose, r"(?i)rebases relative evidence links")
                self.assertIn("--no-run", prose)
                self.assertRegex(prose, r"(?i)stale, unavailable and unknown measurements")
                self.assertRegex(prose, r"(?i)never accept categories, retire tests, change dispositions or satisfy gates")
                for evidence in ("oracle/bugfix provenance", "quarantine ledger references",
                                 "protected behaviors", "failure modes"):
                    self.assertIn(evidence, prose)


if __name__ == "__main__":
    unittest.main()
