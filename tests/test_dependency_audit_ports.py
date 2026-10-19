"""Cross-host package parity for the first real compiled plugin.

`dependency-audit` is the simple canary: one skill, one context. It proves the
compiler produces one installable package per host with the same identity and
the same observable contract before anything harder is attempted. Since
marketplace 38.0.0 it registers no workflow: its audit is the skill's
`references/audit.md`, and the command that reaches it on every host is
`daodan:check-health`, whose assessment loads that unit when manifests exist.
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

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402
from host_binding_assertions import canonical_markdown, without_host_binding

PLUGIN = "dependency-audit"
KERNEL = REPO_ROOT / "plugins" / PLUGIN

#: Pi and OpenCode are absent on purpose: neither has a per-plugin manifest, so the identity it
#: can be held to is the one its package records in `.daodan-provenance.json`.
MANIFEST = {
    "claude": ".claude-plugin/plugin.json",
    "copilot": "plugin.json",
    "codex": ".codex-plugin/plugin.json",
}

#: The entry that reaches the audit on each host. Copilot splits it in two: the
#: prompt hands off to a coordinator agent, which carries the harness and method.
ENTRY = REPO_ROOT / "plugins" / "daodan"
ENTRY_WORKFLOW = "check-health"
WORKFLOW_ENTRYPOINT = {
    "claude": "commands/check-health.md",
    "copilot": "prompts/check-health.prompt.md",
    "codex": "skills/check-health-workflow/SKILL.md",
    "pi": "prompts/daodan-check-health.md",
    "opencode": "commands/check-health.md",
}
METHOD_CARRIER = {**WORKFLOW_ENTRYPOINT, "copilot": "agents/check-health-coordinator.agent.md"}

PROVENANCE = ".daodan-provenance.json"

#: What each host's workflow frontmatter opens with. Pi and OpenCode carry no
#: `name`: on Pi the command is the filename, on OpenCode the loader names it.
FRONTMATTER_PREFIX = {
    "claude": "---\ndescription:",
    "copilot": "---\nname: check-health\n",
    "codex": "---\nname: check-health-workflow\n",
    "pi": "---\ndescription:",
    "opencode": "---\ndescription:",
}

SKILL_RESOURCES = (
    "skills/dependency-audit/SKILL.md",
    "skills/dependency-audit/references/audit.md",
    "skills/dependency-audit/references/ecosystems.md",
    "skills/dependency-audit/references/license-analysis.md",
    "skills/dependency-audit/references/supply-chain.md",
)

#: Each outcome the retired `deps-audit` sidecar declared, with the sentence of
#: the audit unit that now carries it. Since 38.0.0 the unit is the contract.
CONTRACT_OUTCOMES = {
    "dependencies-discovered": "List what was found and what will be audited.",
    "direct-and-transitive-classified": "whether the package is a direct or transitive dependency",
    "licenses-analyzed": "apply the obligations analysis in the `dependency-audit:dependency-audit` skill, "
                         "file `references/license-analysis.md`",
    "supply-chain-findings-evidenced": "Every supply-chain finding is a pointer requiring human verification",
    "remediation-is-non-destructive": "**Non-destructive, always.** Never run `npm audit fix --force` or any forced fix.",
}


def normalized(path: Path) -> str:
    """Compare content, not line endings: generated text is always LF."""
    return path.read_text(encoding="utf-8").replace(chr(13) + chr(10), chr(10))


def package(host: str) -> Path:
    return REPO_ROOT / "exports" / host / "plugins" / PLUGIN


class DependencyAuditPortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The entry's roles and the assessment that loads the audit belong to
        # other plugins, so the entry renders against the whole registry.
        cls.temp = Path(tempfile.mkdtemp())
        cls.rendered = {}
        registry = {path.parent.name: load_plugin(path.parent)
                    for path in (REPO_ROOT / "plugins").glob("*/plugin.toml")}
        for host in HOSTS:
            adapter = load_adapter(REPO_ROOT / "adapters", host)
            for name in ("daodan", "project-lifecycle"):
                staging = cls.temp / host / name
                render_plugin(registry[name], adapter, staging,
                              adapters_root=REPO_ROOT / "adapters", plugin_registry=registry)
                cls.rendered[(host, name)] = staging

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp, ignore_errors=True)

    def test_every_host_reports_the_same_identity(self):
        kernel = load_plugin(KERNEL)
        for host in HOSTS:
            with self.subTest(host=host):
                manifest = MANIFEST.get(host)
                if manifest is None:
                    recorded = json.loads(
                        (package(host) / PROVENANCE).read_text(encoding="utf-8")
                    )
                    self.assertEqual(recorded["plugin"], kernel.name)
                    self.assertEqual(recorded["version"], kernel.version)
                    continue
                declared = json.loads(
                    (package(host) / manifest).read_text(encoding="utf-8")
                )
                self.assertEqual(declared["name"], kernel.name)
                self.assertEqual(declared["version"], kernel.version)

    def test_every_host_preserves_skill_resources_under_its_exact_execution_binding(self):
        for host in HOSTS:
            for resource in SKILL_RESOURCES:
                with self.subTest(host=host, resource=resource):
                    exported = package(host) / resource
                    self.assertTrue(exported.is_file(), f"missing: {exported}")
                    rendered = normalized(exported)
                    self.assertEqual(rendered, canonical_markdown(rendered), "Generated EOF must be canonical")
                    self.assertEqual(
                        without_host_binding(self, rendered, host),
                        canonical_markdown(normalized(KERNEL / resource)),
                    )

    def test_every_host_exposes_one_invocable_entry_that_reaches_the_audit(self):
        """The entry body reaches every host whole; only the frontmatter is the host's.

        Since 38.0.0 the audit is invoked through `daodan:check-health`. Each
        host gets its exact verified execution binding and its own frontmatter
        (`name` on Codex and Copilot, `argument-hint` on Copilot); the method
        under the harness is the kernel body with the two Claude placeholders
        rewritten as the adapter layout says. The body loads the assessment,
        and the assessment, rendered on the same host, names the audit unit.
        """
        kernel = normalized(ENTRY / f"workflows/{ENTRY_WORKFLOW}.md")
        kernel_body = kernel[kernel.index("\n---\n", 4) + 5:].lstrip("\n")
        self.assertIn("project-lifecycle:lifecycle-method", kernel_body)
        self.assertIn("`references/assess.md`", kernel_body)
        for host, entrypoint in WORKFLOW_ENTRYPOINT.items():
            with self.subTest(host=host):
                target = self.rendered[(host, "daodan")] / entrypoint
                self.assertTrue(target.is_file(), f"missing: {target}")
                exported = normalized(target)
                self.assertEqual(exported, canonical_markdown(exported), "Generated EOF must be canonical")
                rendered = without_host_binding(self, exported, host)
                self.assertTrue(rendered.startswith(FRONTMATTER_PREFIX[host]), rendered[:60])
                layout = load_adapter(REPO_ROOT / "adapters", host).layout
                if host == "copilot":
                    self.assertIn("argument-hint", rendered.split("\n---\n", 1)[0])
                    self.assertIn(f"`daodan:{ENTRY_WORKFLOW}-coordinator`", rendered)
                carrier = normalized(self.rendered[(host, "daodan")] / METHOD_CARRIER[host])
                method = without_host_binding(self, carrier, host).split("## Method\n\n", 1)[1]
                expected = kernel_body.replace(
                    "${CLAUDE_PLUGIN_ROOT}", layout["plugin_root_reference"]
                ).replace("$ARGUMENTS", layout["arguments_reference"])
                self.assertEqual(method, canonical_markdown(expected))
                assess = normalized(self.rendered[(host, "project-lifecycle")]
                                    / "skills/lifecycle-method/references/assess.md")
                self.assertIn("`dependency-audit:dependency-audit` when manifests exist", assess)
        self.assertIn("project-lifecycle", load_plugin(ENTRY).required_dependencies)
        self.assertIn("dependency-audit", load_plugin(REPO_ROOT / "plugins/project-lifecycle").required_dependencies)

    def test_the_audit_method_states_the_audit_contract(self):
        # Until 38.0.0 the `deps-audit` sidecar declared these outcomes and the
        # report artifact. No kernel declares that workflow any more; the audit
        # unit the entry loads owns each obligation, and its report is the
        # caller's, written outside the project tree.
        plugin = load_plugin(KERNEL)
        self.assertEqual(plugin.workflows, ())
        self.assertEqual(plugin.components.skills, ("dependency-audit",))
        unit = normalized(KERNEL / "skills/dependency-audit/references/audit.md")
        prose = " ".join(unit.split())
        for outcome, sentence in CONTRACT_OUTCOMES.items():
            with self.subTest(outcome=outcome):
                self.assertIn(sentence, prose)
        steps = [line.split(":")[0] for line in unit.splitlines() if line.startswith("### Step ")]
        self.assertEqual(steps, [f"### Step {number}" for number in range(1, 8)])
        self.assertIn("## Output Format", unit)
        self.assertIn("# Dependency Audit: <path>", unit)
        self.assertIn("goes in the run directory, never in the project tree", prose)

    def test_the_kernel_needs_no_semantic_override(self):
        for host in MANIFEST:
            with self.subTest(host=host):
                provenance = json.loads(
                    (package(host) / ".daodan-provenance.json").read_text(encoding="utf-8")
                )
                self.assertEqual(provenance["overrides"], [])


if __name__ == "__main__":
    unittest.main()
