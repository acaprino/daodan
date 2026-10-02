"""Validation tests for the neutral Daodan control plane."""

import dataclasses
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.trust import scan_trust  # noqa: E402
from scripts.daodan.model import ComponentIndex  # noqa: E402
from scripts.daodan.validate import (  # noqa: E402
    CAPABILITY_REGISTRY,
    validate_component_kinds,
    validate_plugins,
)

INVALID = REPO_ROOT / "tests/fixtures/daodan/invalid"
VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


def plugin_with(**components):
    """The valid fixture plugin with its component index replaced."""
    plugin = load_plugin(VALID)
    return dataclasses.replace(plugin, components=ComponentIndex(**components))


def validate_fixture(name: str):
    plugin = load_plugin(INVALID / name / "plugins/example")
    return validate_plugins([plugin], CAPABILITY_REGISTRY)


class ValidationTests(unittest.TestCase):
    def test_valid_plugin_has_no_issues(self):
        plugin = load_plugin(VALID)
        self.assertEqual(validate_plugins([plugin], CAPABILITY_REGISTRY), [])

    def test_rejects_cycle_and_path_escape(self):
        issues = validate_fixture("cyclic-workflow") + validate_fixture("path-escape")
        self.assertIn("workflow-cycle", {issue.code for issue in issues})
        self.assertIn("path-outside-plugin", {issue.code for issue in issues})

    def test_rejects_incomplete_independent_fanout_contract(self):
        issues = validate_fixture("fanout-without-join") + validate_fixture(
            "fanout-without-isolation"
        )
        self.assertIn("fanout-needs-join", {issue.code for issue in issues})
        self.assertIn("independent-fanout-needs-isolation", {issue.code for issue in issues})

    def test_rejects_capability_outside_the_closed_registry(self):
        issues = validate_fixture("unknown-capability")
        self.assertIn("unknown-capability", {issue.code for issue in issues})

    def test_rejects_secret_paths_outside_explicit_test_allowlist(self):
        issues = scan_trust(INVALID / "forbidden-secret", frozenset())
        self.assertEqual([issue.code for issue in issues], ["forbidden-secret-path"])

    def test_allowlisted_fixture_secret_is_accepted(self):
        root = INVALID / "forbidden-secret"
        allowlisted = frozenset({Path("plugins/example/.env")})
        self.assertEqual(scan_trust(root, allowlisted), [])

    def test_trust_scan_never_prints_matched_content(self):
        issues = scan_trust(INVALID / "forbidden-secret", frozenset())
        secret = (INVALID / "forbidden-secret/plugins/example/.env").read_text(encoding="utf-8")
        for issue in issues:
            self.assertNotIn(secret.strip(), issue.message)

    def test_issue_order_is_deterministic(self):
        first = [issue.code for issue in validate_fixture("cyclic-workflow")]
        second = [issue.code for issue in validate_fixture("cyclic-workflow")]
        self.assertEqual(first, second)



class ComponentKindTests(unittest.TestCase):
    """One name, one kind, inside a plugin.

    OpenCode lists skills and agents in one `@` menu, so a skill and a role of
    the same name become two identical entries there. The rule is general
    because a name that means two things in one plugin is ambiguous on every
    host, whichever menu happens to collide first.
    """

    def test_skill_and_role_sharing_a_name_fail(self):
        issues = validate_component_kinds(plugin_with(skills=("x",), roles=("x",)))
        self.assertEqual([i.code for i in issues], ["component-name-shared-across-kinds"])
        self.assertEqual(issues[0].message, "x: skills, roles")

    def test_skill_and_workflow_sharing_a_name_fail(self):
        issues = validate_component_kinds(plugin_with(skills=("x",), workflows=("x",)))
        self.assertEqual([i.message for i in issues], ["x: skills, workflows"])

    def test_role_and_workflow_sharing_a_name_fail(self):
        issues = validate_component_kinds(plugin_with(roles=("x",), workflows=("x",)))
        self.assertEqual([i.message for i in issues], ["x: roles, workflows"])

    def test_distinct_names_pass(self):
        plugin = plugin_with(skills=("x-method",), roles=("x-agent",), workflows=("x",))
        self.assertEqual(validate_component_kinds(plugin), [])

    def test_real_kernels_have_no_cross_kind_homonym(self):
        kernels = sorted((REPO_ROOT / "plugins").glob("*/plugin.toml"))
        found = [
            issue.message
            for kernel in kernels
            for issue in validate_component_kinds(load_plugin(kernel.parent))
        ]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
