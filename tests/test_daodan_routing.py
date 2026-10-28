"""Loader and validation contract for the declarative `[routing]` table.

Routing lines are derived at build time from kernel metadata, so the loader
owns their shape: closed keys, bounded terms and component-form targets.
Validation owns capability agreement, target existence and the refusal of a
routing that produces no line. Tests use owned temporary copies of the
example fixture; no network, no subprocess.
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

from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.model import ModelError, RoutingKeyword, RoutingSpec  # noqa: E402
from scripts.daodan.validate import CAPABILITY_REGISTRY, validate_plugins  # noqa: E402

FIXTURE = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"
WORKFLOWS_ONLY = "\n[routing]\nworkflows = true\n"


def keyword_row(words, target="review", **extra):
    row = {"words": words, "target": target, **extra}
    return "\n[[routing.keywords]]\n" + "".join(
        f"{key} = {json.dumps(value, ensure_ascii=True)}\n" for key, value in row.items()
    )


class RoutingKernelCase(unittest.TestCase):
    """Owned temporary copy of the example kernel, rewritten per case."""

    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="daodan routing "))
        self.addCleanup(self.remove_owned_temp)
        self.kernel = self.temp / "kernel" / "example"
        shutil.copytree(FIXTURE, self.kernel)
        self.base = (self.kernel / "plugin.toml").read_text(encoding="utf-8")

    def remove_owned_temp(self):
        root = self.temp.resolve()
        self.assertTrue(root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        shutil.rmtree(root)

    def load(self, routing, prefix=""):
        (self.kernel / "plugin.toml").write_text(prefix + self.base + routing, encoding="utf-8")
        return load_plugin(self.kernel)


class RoutingLoadTests(RoutingKernelCase):
    def test_declared_routing_loads_into_spec(self):
        plugin = self.load(
            "\n[routing]\nworkflows = true\n"
            + keyword_row(["audit", "inspect"], "inspector")
            + keyword_row(["IBKR"], "review")
        )

        self.assertEqual(
            plugin.routing,
            RoutingSpec(
                workflows=True,
                keywords=(
                    RoutingKeyword(words=("audit", "inspect"), target="inspector"),
                    RoutingKeyword(words=("IBKR",), target="review"),
                ),
            ),
        )

    def test_absent_routing_contributes_nothing(self):
        self.assertIsNone(self.load("").routing)

    def test_term_bounds_are_inclusive(self):
        words = ["a" * 64] + [f"term-{index}" for index in range(7)]

        plugin = self.load("\n[routing]\n" + keyword_row(words))

        self.assertEqual(plugin.routing, RoutingSpec(
            keywords=(RoutingKeyword(words=tuple(words), target="review"),)))

    def test_malformed_routing_is_rejected_naming_the_field(self):
        table = "\n[routing]\n"
        cases = {
            "not a table": ("", "routing", "routing = true\n"),
            "unknown routing key": (table + 'workflows = true\nprompt = "x"\n', "prompt", ""),
            "unknown keyword key": (table + keyword_row(["audit"], prompt="x"), "prompt", ""),
            "workflows not bool": (table + 'workflows = "yes"\n', "workflows", ""),
            "keywords not tables": (table + 'keywords = ["audit"]\n', "keywords", ""),
            "zero words": (table + keyword_row([]), "words", ""),
            "nine words": (table + keyword_row([f"t{i}" for i in range(9)]), "words", ""),
            "empty word": (table + keyword_row(["audit", ""]), "words", ""),
            "blank word": (table + keyword_row(["   "]), "words", ""),
            "65-character word": (table + keyword_row(["a" * 65]), "words", ""),
            "control character": (table + keyword_row(["a\tb"]), "words", ""),
            "duplicate word": (table + keyword_row(["audit", "audit"]), "words", ""),
            "non-string word": (table + keyword_row([1]), "words", ""),
            "missing target": (table + '[[routing.keywords]]\nwords = ["audit"]\n', "target", ""),
            "uppercase target": (table + keyword_row(["audit"], "Review"), "target", ""),
            "qualified target": (table + keyword_row(["audit"], "daodan:review"), "target", ""),
        }
        for label, (routing, field, prefix) in cases.items():
            with self.subTest(label):
                with self.assertRaises(ModelError) as caught:
                    self.load(routing, prefix)
                self.assertIn("routing", caught.exception.message)
                self.assertIn(field, caught.exception.message)


class RoutingValidationTests(RoutingKernelCase):
    def setUp(self):
        super().setUp()
        skill = self.kernel / "skills/guide"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: guide\ndescription: Routing fixture\n---\n\n# Guide\n",
            encoding="utf-8",
        )
        self.base = self.base.replace('skills = []', 'skills = ["guide"]')

    def issues(self, routing, capability="optional"):
        base = self.base
        if capability == "optional":
            base = base.replace('optional = ["execution.parallel"]',
                                'optional = ["execution.parallel", "hooks.lifecycle"]')
        elif capability == "required":
            base = base.replace('"roles.dispatch"]', '"roles.dispatch", "hooks.lifecycle"]')
        (self.kernel / "plugin.toml").write_text(base + routing, encoding="utf-8")
        return validate_plugins([load_plugin(self.kernel)], CAPABILITY_REGISTRY)

    def codes(self, routing, capability="optional"):
        return [issue.code for issue in self.issues(routing, capability)]

    def remove_workflows(self):
        shutil.rmtree(self.kernel / "workflows")
        self.base = self.base.replace('workflows = ["review"]', 'workflows = []')

    def test_routing_with_capability_and_no_hooks_is_valid(self):
        for capability in ("optional", "required"):
            with self.subTest(capability=capability):
                self.assertEqual(self.codes(WORKFLOWS_ONLY, capability), [])

    def test_routing_without_capability_is_rejected(self):
        self.assertEqual(self.codes(WORKFLOWS_ONLY, capability=None),
                         ["routing-capability-undeclared"])

    def test_unknown_target_is_rejected(self):
        issues = self.issues("\n[routing]\n" + keyword_row(["audit"], "missing"))

        self.assertEqual([issue.code for issue in issues], ["routing-target-unknown"])
        self.assertIn("missing", issues[0].message)

    def test_skill_role_and_workflow_targets_are_accepted(self):
        for target in ("guide", "inspector", "review"):
            with self.subTest(target=target):
                self.assertEqual(self.codes("\n[routing]\n" + keyword_row(["audit"], target)), [])

    def test_workflows_flag_without_workflows_or_keywords_is_empty(self):
        self.remove_workflows()

        self.assertEqual(self.codes(WORKFLOWS_ONLY), ["routing-empty"])
        self.assertEqual(self.codes(WORKFLOWS_ONLY + keyword_row(["audit"], "inspector")), [])

    def test_routing_without_workflows_or_keywords_is_empty(self):
        for routing in ("\n[routing]\n", "\n[routing]\nworkflows = false\n"):
            with self.subTest(routing=routing):
                self.assertEqual(self.codes(routing), ["routing-empty"])


if __name__ == "__main__":
    unittest.main()
