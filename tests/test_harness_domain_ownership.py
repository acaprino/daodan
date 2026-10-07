"""Ownership contracts for the universal harness and its specialist extension."""
from pathlib import Path
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXTENSION_ROLES = {"react-development/react-performance-optimizer", "typescript-development/type-safety-auditor", "platform-engineering/platform-reviewer"}
CORE_ROLES = {
    "code-review": {f"senior-review/{name}" for name in ("code-auditor", "security-auditor", "ui-race-auditor", "temporal-resilience-auditor", "data-integrity-auditor", "resource-lifecycle-auditor", "premise-auditor")} | {"testing/test-suite-auditor", "abstraction-architect/abstraction-architect-agent"},
    "team-review": {f"senior-review/{name}" for name in ("api-contract-auditor", "chicken-egg-detector", "cleanup-auditor", "code-auditor", "data-integrity-auditor", "distributed-flow-auditor", "logic-integrity-auditor", "premise-auditor", "resource-lifecycle-auditor", "security-auditor", "temporal-resilience-auditor", "ui-race-auditor")} | {"repo-hygiene/workspace-auditor", "testing/test-suite-auditor", "abstraction-architect/abstraction-architect-agent", "codebase-xray/semantic-interconnect-mapper"},
    "pr-review": {f"senior-review/{name}" for name in ("code-auditor", "security-auditor", "premise-auditor")},
}


def manifest(name):
    return tomllib.loads((ROOT / "plugins" / name / "plugin.toml").read_text(encoding="utf-8"))


def wrapper_path(host, plugin, entry):
    return {
        "claude": f"commands/{entry}.md",
        "copilot": f"agents/{entry}-coordinator.agent.md",
        "codex": f"skills/{entry}-workflow/SKILL.md",
        "pi": f"prompts/{plugin}-{entry}.md",
        "opencode": f"commands/{entry}.md",
    }[host]


class HarnessDomainOwnershipTests(unittest.TestCase):
    def test_review_wrapper_bindings_and_owner_resources_ship_on_every_host(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.load import load_plugin
        from scripts.daodan.render import render_plugin

        registry = {p.parent.name: load_plugin(p.parent) for p in (ROOT / "plugins").glob("*/plugin.toml")}
        with tempfile.TemporaryDirectory() as temporary:
            for host in HOSTS:
                for plugin in ("review-plus", "senior-review"):
                    with self.subTest(host=host, plugin=plugin):
                        root = Path(temporary) / host / plugin
                        render_plugin(registry[plugin], load_adapter(ROOT / "adapters", host), root,
                                      adapters_root=ROOT / "adapters", plugin_registry=registry)
                        extras = EXTENSION_ROLES if plugin == "review-plus" else set()
                        for entry, core in CORE_ROLES.items():
                            body = (root / wrapper_path(host, plugin, entry)).read_text(encoding="utf-8")
                            if plugin == "review-plus":
                                for selection in ("react", "typescript", "platform"):
                                    self.assertIn(f"selection:{selection}", body)
                            for binding in core | extras:
                                owner, role = binding.split("/")
                                identity = role if owner == plugin else f"{owner}:{role}"
                                self.assertIn(f"`{identity}`", body)
                            self.assertIn("project-protocol:isolated-worker", body)
                            self.assertIn("senior-review:review-method", body)
                            self.assertNotIn("subagent_type", body)
                        if host in {"codex", "pi"}:
                            for binding in CORE_ROLES["team-review"] | extras | {"project-protocol/isolated-worker"}:
                                owner, role = binding.split("/")
                                if owner == plugin:
                                    continue
                                resource = root / "contracts/dispatch" / owner / f"{role}.md"
                                text = resource.read_text(encoding="utf-8")
                                self.assertIn(f"Owner: {owner}:{role}", text)
                                self.assertIn(f"<{owner}-plugin-root>", text)
                                for skill in registry[owner].components.skills:
                                    self.assertIn(f"{owner}:{skill}", text)
                                self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)

    def test_lifecycle_and_guide_wrappers_bind_their_composed_methods_on_every_host(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.load import load_plugin
        from scripts.daodan.render import render_plugin

        registry = {p.parent.name: load_plugin(p.parent) for p in (ROOT / "plugins").glob("*/plugin.toml")}
        cases = {
            ("project-lifecycle", "change"): {"testing/test-writer", "senior-review/code-auditor", "project-knowledge/instructions-auditor"},
            ("project-lifecycle", "assess"): {"project-knowledge/documentation-engineer", "project-knowledge/guide-reviewer"},
            ("project-knowledge", "guide"): {"codebase-xray/semantic-interconnect-mapper", "text-humanizer/text-humanizer"} | {f"project-knowledge/{role}" for role in ("codebase-explorer", "overview-writer", "tech-writer", "flow-writer", "ops-writer", "onboarding-writer")},
        }
        with tempfile.TemporaryDirectory() as temporary:
            for host in HOSTS:
                for plugin in {plugin for plugin, _ in cases}:
                    root = Path(temporary) / host / plugin
                    render_plugin(registry[plugin], load_adapter(ROOT / "adapters", host), root,
                                  adapters_root=ROOT / "adapters", plugin_registry=registry)
                    for (case_plugin, entry), roles in cases.items():
                        if plugin != case_plugin:
                            continue
                        with self.subTest(host=host, plugin=plugin, entry=entry):
                            body = (root / wrapper_path(host, plugin, entry)).read_text(encoding="utf-8")
                            for binding in roles:
                                owner, role = binding.split("/")
                                identity = role if owner == plugin else f"{owner}:{role}"
                                self.assertIn(f"`{identity}`", body)
                                if host in {"codex", "pi"} and owner != plugin:
                                    resource = root / "contracts/dispatch" / owner / f"{role}.md"
                                    text = resource.read_text(encoding="utf-8")
                                    self.assertIn(f"Owner: {owner}:{role}", text)
                                    self.assertIn(f"<{owner}-plugin-root>", text)
                                    for skill in registry[owner].components.skills:
                                        self.assertIn(f"{owner}:{skill}", text)

    def test_composed_inventory_binds_methods_without_copying_their_schedule(self):
        for owner in ("senior-review", "review-plus"):
            for entry, core in CORE_ROLES.items():
                with self.subTest(owner=owner, entry=entry):
                    sidecar = tomllib.loads((ROOT / "plugins" / owner / "workflows" / f"{entry}.toml").read_text())
                    dispatch = sidecar["dispatch"]
                    expected = core | EXTENSION_ROLES if owner == "review-plus" else core
                    self.assertEqual(set(dispatch["roles"]), expected)
                    self.assertTrue(dispatch["isolated"])
                    self.assertIs(dispatch["inline_workers"], True)
                    self.assertIn("project-protocol", manifest(owner)["dependencies"]["required"])
                    if owner == "review-plus":
                        # Composition exposes core bindings; it does not duplicate
                        # the canonical review phase graph in the outer wrapper.
                        self.assertEqual([p["id"] for p in sidecar["phases"]], ["prepare", "react", "typescript", "platform", "universal-review"])

    def test_specialist_review_is_a_separate_mandatory_closure(self):
        core = manifest("senior-review")
        extras = {"react-development", "typescript-development", "platform-engineering"}
        self.assertTrue(extras.isdisjoint(core["dependencies"]["required"]))
        extended = manifest("review-plus")
        self.assertTrue((extras | {"senior-review"}).issubset(extended["dependencies"]["required"]))
        self.assertEqual(extended["components"]["roles"], [])
        for entry in ("code-review", "team-review", "pr-review"):
            sidecar = tomllib.loads((ROOT / "plugins/review-plus/workflows" / f"{entry}.toml").read_text())
            roles = {p.get("role") for p in sidecar["phases"] if p.get("role")}
            self.assertEqual(roles, {"react-development/react-performance-optimizer", "typescript-development/type-safety-auditor", "platform-engineering/platform-reviewer"})
            self.assertTrue(all(p.get("join") == "all-delivered" for p in sidecar["phases"] if p.get("fanout_from")))

    def test_native_review_contracts_survive_the_envelope_migration(self):
        contracts = ROOT / "plugins/senior-review/contracts"
        self.assertEqual({p.stem for p in contracts.glob("*.toml")}, {"review-brief", "reviewer-binding", "reviewer-selection", "evidenced-finding", "reviewer-result", "delivery-ledger", "final-report"})
        for method in ("review-method", "review-preparation", "review-consolidation", "application-cleanup-method"):
            self.assertIn(method, manifest("senior-review")["components"]["skills"])
            self.assertTrue((ROOT / "plugins/senior-review/skills" / method / "SKILL.md").is_file())

    def test_python_uses_the_canonical_test_writer_without_a_cycle(self):
        python = manifest("python-development")
        self.assertIn("testing", python["dependencies"]["required"])
        self.assertIn("pytest-patterns", python["components"]["skills"])
        self.assertNotIn("python-tdd", python["components"]["skills"])
        self.assertNotIn("python-test-engineer", python["components"]["roles"])
        self.assertFalse((ROOT / "plugins/python-development/roles/python-test-engineer.md").exists())
        self.assertNotIn("python-development", manifest("testing")["dependencies"]["required"])
        for body in (ROOT / "plugins/testing").rglob("*.md"):
            self.assertNotIn("python-development:python-tdd", body.read_text(encoding="utf-8"))

    def test_mutation_owners_have_the_operational_protocol(self):
        for owner, method in (("senior-review", "application-cleanup-method"), ("testing", "test-remediation-method"), ("clean-code", "readability-method"), ("python-development", "python-refactor-method")):
            with self.subTest(owner=owner):
                self.assertIn("project-protocol", manifest(owner)["dependencies"]["required"])
                body = (ROOT / "plugins" / owner / "skills" / method / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("project-protocol:project-protocol", body)


if __name__ == "__main__":
    unittest.main()
