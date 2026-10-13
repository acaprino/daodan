"""Validation tests for the neutral Daodan control plane."""

import dataclasses
import shutil
import sys
import tempfile
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

    def test_identical_version_duplicate_identity_names_both_roots(self):
        with tempfile.TemporaryDirectory(prefix="daodan-duplicate-identity-") as holder:
            roots = [Path(holder) / origin / "example" for origin in ("first", "second")]
            for root in roots:
                shutil.copytree(VALID, root)
            plugins = [load_plugin(root) for root in roots]

            first = validate_plugins(plugins, CAPABILITY_REGISTRY)
            repeated = validate_plugins(plugins, CAPABILITY_REGISTRY)

            self.assertEqual(first, repeated)
            duplicates = [issue for issue in first if "duplicate" in issue.code.lower()]
            self.assertTrue(duplicates, "Identical versions do not make a plugin name unique")
            diagnosis = "\n".join(f"{issue.path}: {issue.message}" for issue in duplicates)
            self.assertIn("example", diagnosis)
            for root in roots:
                self.assertIn(str(root), diagnosis)

    def test_rejects_cycle_and_path_escape(self):
        issues = validate_fixture("cyclic-workflow") + validate_fixture("path-escape")
        self.assertIn("workflow-cycle", {issue.code for issue in issues})
        self.assertIn("path-outside-plugin", {issue.code for issue in issues})

    def test_rejects_duplicate_phase_ids_including_an_overwritten_cycle(self):
        plugin = load_plugin(VALID)
        workflow = plugin.workflows[0]
        original = workflow.phases[0]
        cyclic = dataclasses.replace(original, needs=("inspect",))
        for first in (original, cyclic):
            with self.subTest(overwritten_cycle=bool(first.needs)):
                changed = dataclasses.replace(
                    workflow, phases=(first, original)
                )
                candidate = dataclasses.replace(plugin, workflows=(changed,))

                issues = validate_plugins([candidate], CAPABILITY_REGISTRY)

                duplicates = [
                    issue for issue in issues
                    if "duplicate" in issue.code.lower()
                ]
                self.assertTrue(duplicates, "Phase IDs must identify one phase")
                self.assertIn("inspect", duplicates[0].message)
                self.assertEqual(duplicates[0].path, workflow.entrypoint)

    def test_rejects_a_prerequisite_declared_after_its_dependent(self):
        plugin = load_plugin(VALID)
        workflow = plugin.workflows[0]
        inspect = workflow.phases[0]
        dependent = dataclasses.replace(
            inspect, id="prepare", needs=("inspect",), produces=()
        )
        changed = dataclasses.replace(workflow, phases=(dependent, inspect))
        candidate = dataclasses.replace(plugin, workflows=(changed,))

        issues = validate_plugins([candidate], CAPABILITY_REGISTRY)

        self.assertTrue(issues, "Declared order cannot run a future prerequisite")
        diagnosis = "\n".join(issue.message for issue in issues)
        self.assertIn("prepare", diagnosis)
        self.assertIn("inspect", diagnosis)

    def test_missing_prerequisite_keeps_its_unknown_phase_diagnosis(self):
        plugin = load_plugin(VALID)
        workflow = plugin.workflows[0]
        inspect = dataclasses.replace(workflow.phases[0], needs=("missing",))
        changed = dataclasses.replace(workflow, phases=(inspect,))
        candidate = dataclasses.replace(plugin, workflows=(changed,))

        issues = validate_plugins([candidate], CAPABILITY_REGISTRY)

        self.assertIn("unknown-phase", {issue.code for issue in issues})

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
