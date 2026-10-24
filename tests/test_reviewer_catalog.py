"""The compiled reviewer catalog shipped inside the senior-review package.

The oracle is provenance: every entry names a registered role of a loaded
provider, carries the trigger text of that role's own frontmatter and a digest
of its body, and no entry invents a role for a method-only provider.
"""
import json
import runpy
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_work_record import ProtocolCase

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class ReviewerCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.daodan_build import discover_plugins
        from scripts.daodan.reviewer_catalog import reviewer_catalog

        cls.registry = {p.name: p for p in discover_plugins(ROOT)}
        cls.catalog = reviewer_catalog(cls.registry, "claude", "agents/{role}.md")

    def test_schema_and_host_are_declared(self):
        self.assertEqual(self.catalog["schema"], "daodan/reviewer-catalog/v1")
        self.assertEqual(self.catalog["host"], "claude")

    def test_python_method_binds_semantics_and_reachability_without_losing_audit_methods(self):
        entry = next(row for row in self.catalog["entries"] if row["id"] == "senior-review:python-method")
        self.assertEqual(entry["members"], ["python-development:python-semantics-auditor",
                                            "senior-review:application-reachability-auditor"])
        self.assertEqual(entry["skills"], ["python-development:python-refactor-method",
                                           "python-development:python-dead-code"])

    def test_every_role_entry_is_a_registered_role_with_its_own_triggers(self):
        from scripts.daodan.reviewer_catalog import REVIEWER_ROLES

        entries = {entry["id"]: entry for entry in self.catalog["entries"] if entry["kind"] == "role"}
        self.assertEqual(set(entries), {f"{p}:{r}" for p, r in REVIEWER_ROLES})
        for entry in entries.values():
            provider = self.registry[entry["provider"]]
            self.assertIn(entry["role"], provider.components.roles)
            self.assertEqual(entry["provider_version"], provider.version)
            self.assertTrue(entry["body_sha256"].startswith("sha256:"))
            self.assertEqual(entry["host_binding"]["id"], entry["id"])
            self.assertTrue(entry["host_binding"]["file"].endswith(".md"))

    def test_security_and_logic_triggers_carry_the_wave_3_contract(self):
        entries = {entry["id"]: entry for entry in self.catalog["entries"]}
        security = entries["senior-review:security-auditor"]
        if "members" in security:
            required = {"senior-review:authorization-auditor",
                        "senior-review:session-delegation-auditor",
                        "senior-review:capacity-quota-auditor"}
            self.assertLessEqual(required, set(security["members"]))
            for member in security["members"]:
                self.assertIn(entries[member]["trigger_when"], security["trigger_when"])
        else:
            for phrase in ("caller-supplied ID", "permissions, roles", "logins and sessions"):
                self.assertIn(phrase, security["trigger_when"])
        logic = entries["senior-review:logic-integrity-auditor"]
        self.assertIn("scoped semantic context", logic["trigger_when"])
        self.assertNotIn("when no interconnect map exists yet", logic["do_not_trigger_when"])
        self.assertTrue(any("scoped-semantic-context" in item for item in logic["prerequisites"]))

    def test_method_only_providers_are_bindings_not_invented_roles(self):
        entries = {entry["id"]: entry for entry in self.catalog["entries"]}
        for binding in ("senior-review:python-method", "senior-review:dependencies-method"):
            self.assertEqual(entries[binding]["kind"], "method-binding")
            self.assertEqual(entries[binding]["role"], "work-controller:isolated-worker")
        self.assertNotIn("python-development:python-engineer",
                         {entry["id"] for entry in self.catalog["entries"] if entry["kind"] == "role"})

    def test_specialist_bindings_preserve_required_preparation(self):
        entries = {entry["id"]: entry for entry in self.catalog["entries"]}
        for role in ("concept-ownership-auditor", "abstraction-fit-auditor"):
            self.assertIn("candidate-bound-codebase-map", entries[
                f"abstraction-architect:{role}"]["prerequisites"])
        for role in ("test-suite-structure-auditor", "test-reliability-auditor"):
            self.assertIn("prepared-test-suite-context", entries[
                f"testing:{role}"]["prerequisites"])
        self.assertTrue(any("3-claim-check" in value for value in entries[
            "senior-review:premise-auditor"]["prerequisites"]))

    def test_specialists_reuse_registered_identities_and_host_bindings_on_all_hosts(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.reviewer_catalog import reviewer_catalog

        for host in HOSTS:
            adapter = load_adapter(ROOT / "adapters", host)
            entries = {entry["id"]: entry for entry in reviewer_catalog(
                self.registry, host, adapter.layout.get("roles"))["entries"]}
            for role in ("accessibility-auditor", "performance-auditor", "operability-auditor"):
                with self.subTest(host=host, role=role):
                    entry = entries[f"senior-review:{role}"]
                    self.assertEqual(entry["kind"], "role")
                    self.assertEqual(entry["file"], f"roles/{role}.md")
                    self.assertTrue(entry["trigger_when"])
                    self.assertTrue(entry["do_not_trigger_when"])
                    self.assertEqual(entry["host_binding"]["host"], host)
                    self.assertEqual(entry["host_binding"]["id"], entry["id"])
                    self.assertIn(role, entry["host_binding"]["file"])

    def test_focused_specialists_are_registered_and_bound_on_every_host(self):
        # A missing registration or host binding must prevent a specialist dispatch.
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.reviewer_catalog import reviewer_catalog

        required = {
            "senior-review": "authorization-auditor session-delegation-auditor secret-exposure-auditor input-validation-auditor untrusted-resource-auditor browser-security-auditor callback-authenticity-auditor ai-boundary-auditor audit-trail-auditor transaction-integrity-auditor schema-coherence-auditor cache-consistency-auditor data-representation-auditor data-retention-auditor message-delivery-auditor remote-effect-auditor service-resilience-auditor sql-efficiency-auditor algorithmic-cost-auditor asset-delivery-auditor capacity-quota-auditor runtime-cost-auditor observability-auditor service-health-auditor release-compatibility-auditor environment-binding-auditor feature-flag-auditor recovery-auditor accessible-navigation-auditor accessible-perception-auditor local-correctness-auditor local-concurrency-auditor application-reachability-auditor dependency-usage-auditor artifact-lifecycle-auditor",
            "testing": "test-suite-structure-auditor test-oracle-auditor test-reliability-auditor journey-protection-auditor contract-test-auditor capacity-test-auditor ai-evaluation-auditor",
            "react-development": "react-effects-auditor react-render-cost-auditor react-bundle-auditor react-dataflow-auditor",
            "typescript-development": "type-soundness-auditor typed-boundary-auditor",
            "platform-engineering": "browser-compatibility-auditor offline-lifecycle-auditor native-lifecycle-auditor desktop-bridge-auditor app-distribution-auditor",
            "abstraction-architect": "concept-ownership-auditor abstraction-fit-auditor",
            "python-development": "python-semantics-auditor",
        }
        for host in HOSTS:
            adapter = load_adapter(ROOT / "adapters", host)
            entries = {entry["id"]: entry for entry in reviewer_catalog(
                self.registry, host, adapter.layout.get("roles"))["entries"]}
            for owner, roles in required.items():
                for role in roles.split():
                    with self.subTest(host=host, role=role):
                        identity = f"{owner}:{role}"
                        self.assertIn(identity, entries)
                        entry = entries[identity]
                        self.assertEqual(entry["kind"], "role")
                        self.assertIn(role, self.registry[owner].components.roles)
                        self.assertEqual(entry["host_binding"]["id"], identity)
                        self.assertEqual(entry["host_binding"]["host"], host)
                        self.assertTrue(entry["trigger_when"])
                        self.assertTrue(entry["body_sha256"].startswith("sha256:"))

    def test_unregistered_canonical_leaf_cannot_publish_on_any_host(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.render import publish_plugin
        from scripts.daodan.reviewer_catalog import ReviewerCatalogError, reviewer_catalog
        from scripts.daodan.validate import validate_dependencies

        provider = self.registry["senior-review"]
        role = "api-contract-auditor"
        self.assertTrue((provider.root / "roles" / f"{role}.md").is_file())
        unregistered = replace(provider, components=replace(
            provider.components, roles=tuple(r for r in provider.components.roles if r != role)))
        registry = {**self.registry, provider.name: unregistered}
        issues = validate_dependencies(registry["daodan"], registry)
        self.assertTrue(any(issue.code == "unknown-role" and role in issue.message for issue in issues))

        with tempfile.TemporaryDirectory() as directory:
            for host in HOSTS:
                with self.subTest(host=host):
                    adapter = load_adapter(ROOT / "adapters", host)
                    with self.assertRaises(ReviewerCatalogError):
                        reviewer_catalog(registry, host, adapter.layout.get("roles"))
                    live = Path(directory) / host
                    live.mkdir()
                    (live / "previous-package").write_bytes(b"keep published package")
                    with self.assertRaises(ReviewerCatalogError):
                        publish_plugin(unregistered, adapter, live,
                                       adapters_root=ROOT / "adapters", plugin_registry=registry)
                    self.assertEqual([path.name for path in live.iterdir()], ["previous-package"])
                    self.assertEqual((live / "previous-package").read_bytes(), b"keep published package")


class ReviewerInputDeliveryTests(ProtocolCase):
    """Exercise knowledge coverage and persisted delivery gates, not prompt quality.

    The coordinator records the failed assignment in the work ledger. The ledger
    does not infer arbitrary missing inputs from the reviewer's prose or report.
    """

    def setUp(self):
        super().setUp()
        helper = ROOT / "plugins/skill-catalog/skills/skill-catalog/scripts/catalog.py"
        self.knowledge = runpy.run_path(str(helper))
        self.body = self.temp / "knowledge/skills/contracts/SKILL.md"
        self.body.parent.mkdir(parents=True)
        self.body.write_text("# Contract knowledge\nCheck the wire representation.\n", encoding="utf-8")
        metadata = {
            "schema": "daodan/skill-metadata/v1", "kind": "knowledge",
            "operations": ["review"], "languages": ["python"],
            "dimensions": ["api-contract"],
        }
        self.body.with_suffix(".toml").write_text(
            "\n".join(f"{key} = {json.dumps(value)}" for key, value in metadata.items()), encoding="utf-8")
        inventory = [{"id": "fixture:contracts", "provider": "fixture", "version": "1.0.0",
                      "root": str(self.temp / "knowledge"), "file": "skills/contracts/SKILL.md",
                      "origin": "project"}]
        self.catalog = self.knowledge["index_inventory"](
            {"schema": "daodan/skill-catalog/v1", "entries": []}, inventory)
        self.request = {
            "run_id": "test-run", "project_id": "project-fixture", "snapshot_id": "candidate-1",
            "operation": "review", "scopes": [{
                "id": "api", "paths": ["app.py"], "languages": ["python"],
                "frameworks": [], "topics": [], "evidence": ["Inspected app.py contract boundary"],
                "workers": {"api-contract": ["senior-review:api-contract-auditor"]},
            }],
        }
        self.selection = self.knowledge["prepare"](self.catalog, self.request)
        loaded = self.knowledge["load_skill"](self.selection, "fixture:contracts")
        self.usage = {key: loaded[key] for key in ("id", "status", "sha256", "selection_sha256")}
        self.usage.update(scope_id="api", worker="senior-review:api-contract-auditor",
                          application="Compared producer and consumer wire representations.", references=[])

    def reviewer_report(self, *, status, gaps, usage):
        envelope = {
            "dimension": "api-contract", "reviewer": "senior-review:api-contract-auditor",
            "status": status, "findings": [], "gaps": gaps,
            "output_path": "reviewer.json", "knowledge_usage": usage,
        }
        path = self.project / ".daodan/runs/test-run/reviewer.json"
        path.write_text(json.dumps(envelope), encoding="utf-8")
        return path

    def test_missing_assigned_input_fails_coverage_and_prevents_completion(self):
        self.init()
        self.body.unlink()
        prepared = self.knowledge["prepare"](self.catalog, self.request)
        self.assertEqual(prepared["status"], "failed")
        # A receipt from before deletion must not make a missing input current.
        coverage = self.knowledge["validate_usage"](self.selection, [self.usage])
        self.assertFalse(coverage["complete"])
        self.assertEqual(coverage["failures"][0]["reason"], "knowledge-load-failed")
        report = self.reviewer_report(status="failed", gaps=coverage["failures"], usage=[])
        self.invoke("update", {"deliveries": {"audit": {
            "status": "failed", "output": report.name, "reason": "Required contract knowledge is missing",
        }}}, ("--expected-revision", "0"))
        failure = self.invoke("update", {
            "status": "complete", "phases": {"audit": {"status": "complete"}},
        }, ("--expected-revision", "1"), ok=False)
        self.assertIn("Completion requires every expected delivery", failure.stderr)
        work = self.invoke("show")
        self.assertEqual(work["revision"], 1)
        self.assertEqual(work["deliveries"]["audit"]["status"], "failed")
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["findings"], [])

    def test_no_findings_with_valid_inputs_can_complete(self):
        self.init()
        coverage = self.knowledge["validate_usage"](self.selection, [self.usage])
        self.assertTrue(coverage["complete"])
        report = self.reviewer_report(status="delivered", gaps=[], usage=[self.usage])
        work = self.invoke("update", {
            "status": "complete", "phases": {"audit": {"status": "complete"}},
            "deliveries": {"audit": {"status": "delivered", "output": report.name}},
        }, ("--expected-revision", "0"))
        self.assertEqual(work["status"], "complete")
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["findings"], [])


if __name__ == "__main__":
    unittest.main()
