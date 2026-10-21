"""The compiled reviewer catalog shipped inside the senior-review package.

The oracle is provenance: every entry names a registered role of a loaded
provider, carries the trigger text of that role's own frontmatter and a digest
of its body, and no entry invents a role for a method-only provider.
"""
import sys
import unittest
from pathlib import Path

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
        security = entries["senior-review:security-auditor"]["trigger_when"]
        for phrase in ("caller-supplied ID", "permissions, roles", "logins and sessions"):
            self.assertIn(phrase, security)
        logic = entries["senior-review:logic-integrity-auditor"]
        self.assertIn("scoped semantic context", logic["trigger_when"])
        self.assertNotIn("when no interconnect map exists yet", logic["do_not_trigger_when"])
        self.assertTrue(any("scoped-semantic-context" in item for item in logic["prerequisites"]))

    def test_method_only_providers_are_bindings_not_invented_roles(self):
        entries = {entry["id"]: entry for entry in self.catalog["entries"]}
        for binding in ("senior-review:python-method", "senior-review:dependencies-method"):
            self.assertEqual(entries[binding]["kind"], "method-binding")
            self.assertEqual(entries[binding]["role"], "project-protocol:isolated-worker")
        self.assertNotIn("python-development:python-engineer",
                         {entry["id"] for entry in self.catalog["entries"] if entry["kind"] == "role"})

    def test_an_unregistered_reviewer_role_fails_the_build(self):
        from scripts.daodan.reviewer_catalog import ReviewerCatalogError, reviewer_catalog
        import scripts.daodan.reviewer_catalog as module

        original = module.REVIEWER_ROLES
        module.REVIEWER_ROLES = original + (("senior-review", "missing-auditor"),)
        try:
            with self.assertRaises(ReviewerCatalogError):
                reviewer_catalog(self.registry, "claude", None)
        finally:
            module.REVIEWER_ROLES = original


if __name__ == "__main__":
    unittest.main()
