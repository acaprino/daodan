"""The review roster is computed from measured signals, never chosen by the model.

Pinned on the probe of 2026-10-19: a fix inside one function of python-humanize
got seven reviewers, 40 minutes and 30.90 USD. The same diff must now compute
`small` for a branch review and one reviewer for the light review, and a
dispatch that adds a security auditor must be refused.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = REPO_ROOT / "plugins/project-protocol/skills/project-protocol/scripts/review_roster.py"
sys.path.insert(0, str(HELPER.parent))
import review_roster  # noqa: E402

PROBE_DIFF = """\
diff --git a/src/humanize/time.py b/src/humanize/time.py
--- a/src/humanize/time.py
+++ b/src/humanize/time.py
@@ -620,6 +620,8 @@ def precisedelta(
     value: dt.timedelta | int | float,
     minimum_unit: str = "seconds",
 ) -> str:
+    now = _now()
+    negative = False
     date, delta = _date_and_delta(value, now=now)
@@ -660,3 +662,5 @@ def precisedelta(
-    return _format(texts)
+    rendered = _format(texts)
+    return "-" + rendered if negative and nonzero else rendered
diff --git a/tests/test_time.py b/tests/test_time.py
--- a/tests/test_time.py
+++ b/tests/test_time.py
@@ -800,0 +801,12 @@ def test_precisedelta_multiple_units
+@pytest.mark.parametrize("value, expected", [(-3661, "-1 hour, 1 minute and 1 second")])
+def test_precisedelta_negative(value, expected):
+    assert humanize.precisedelta(dt.timedelta(seconds=value)) == expected
"""

INTERFACE_DIFF = """\
diff --git a/src/orders/validator.py b/src/orders/validator.py
--- a/src/orders/validator.py
+++ b/src/orders/validator.py
@@ -10,3 +10,3 @@ class OrderValidator
-def validate_order(order):
+def validate_order(order, strict=False):
     return order.total > 0
"""

SENSITIVE_DIFF = """\
diff --git a/app/auth/session.py b/app/auth/session.py
--- a/app/auth/session.py
+++ b/app/auth/session.py
@@ -1,2 +1,3 @@
 import time
+TTL = 3600
"""

MANIFEST_DIFF = """\
diff --git a/pyproject.toml b/pyproject.toml
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -20,2 +20,3 @@
 dependencies = [
+  "httpx>=0.27",
"""

WIDE_DIFF = "".join(
    f"diff --git a/pkg{m}/mod.py b/pkg{m}/mod.py\n--- a/pkg{m}/mod.py\n+++ b/pkg{m}/mod.py\n@@ -1,1 +1,2 @@\n x = 1\n+y = {m}\n"
    for m in range(3)
)


class RosterComputationTests(unittest.TestCase):
    def test_the_probe_change_is_small_for_a_branch_review(self):
        roster = review_roster.compute("branch", PROBE_DIFF, None, None, False)
        self.assertEqual(roster["tier"], "small")
        self.assertEqual(roster["roster"][:2], ["senior-review:code-auditor", "testing:test-suite-auditor"])
        self.assertIn("project-protocol:isolated-worker#python", roster["roster"])
        self.assertNotIn("senior-review:security-auditor", roster["roster"])
        self.assertFalse(roster["blind_derivation"])
        self.assertFalse(roster["critic"])
        self.assertEqual(roster["signals"]["production_files"], 1)
        self.assertEqual(roster["signals"]["interface_changed"], [])
        self.assertIn("no Codebase Map impact packet", roster["gaps"][0])

    def test_the_light_review_has_one_reviewer_and_no_signal_widens_it(self):
        for diff in (PROBE_DIFF, INTERFACE_DIFF, SENSITIVE_DIFF, MANIFEST_DIFF):
            with self.subTest(diff=diff[:30]):
                roster = review_roster.compute("light", diff, None, None, False)
                self.assertEqual(roster["tier"], "light")
                self.assertEqual(roster["roster"], ["senior-review:code-auditor"])
                self.assertEqual(roster["verification"], "critical-high")
        advice = review_roster.compute("light", INTERFACE_DIFF, None, None, False)["advice"]
        self.assertTrue(advice and "review-branch" in advice[0])
        self.assertEqual(review_roster.compute("light", PROBE_DIFF, None, None, False)["advice"], [])

    def test_public_interface_sensitive_path_and_manifest_force_large(self):
        for diff, reason in ((INTERFACE_DIFF, "public interface changed: validate_order"),
                             (SENSITIVE_DIFF, "sensitive paths: app/auth/session.py"),
                             (MANIFEST_DIFF, "manifest or contract changed: pyproject.toml")):
            with self.subTest(reason=reason):
                roster = review_roster.compute("branch", diff, None, None, False)
                self.assertEqual(roster["tier"], "large")
                self.assertIn(reason, roster["reasons"])
                self.assertIn("senior-review:security-auditor", roster["roster"])
                self.assertTrue(roster["blind_derivation"] and roster["critic"])
        self.assertIn("project-protocol:isolated-worker#dependencies",
                      review_roster.compute("branch", MANIFEST_DIFF, None, None, False)["roster"])

    def test_several_modules_or_many_callers_raise_to_medium(self):
        wide = review_roster.compute("branch", WIDE_DIFF, None, None, False)
        self.assertEqual(wide["tier"], "medium")
        self.assertIn("3 modules touched", wide["reasons"])
        impact = {"targets": [{"id": "src/humanize/time.py::precisedelta", "callers": {"total": 7, "listed": []}}]}
        callers = review_roster.compute("branch", PROBE_DIFF, None, impact, False)
        self.assertEqual(callers["tier"], "medium")
        self.assertIn("7 callers of a changed symbol", callers["reasons"])
        self.assertEqual(callers["gaps"], [])
        many = {"targets": [{"id": "x", "callers": {"total": 25}}]}
        self.assertEqual(review_roster.compute("branch", PROBE_DIFF, None, many, False)["tier"], "large")

    def test_deeper_raises_one_tier_and_nothing_lowers(self):
        self.assertEqual(review_roster.compute("branch", PROBE_DIFF, None, None, True)["tier"], "medium")
        self.assertEqual(review_roster.compute("branch", WIDE_DIFF, None, None, True)["tier"], "large")
        self.assertEqual(review_roster.compute("branch", INTERFACE_DIFF, None, None, True)["tier"], "large")

    def test_private_signatures_and_new_functions_are_not_interface_changes(self):
        private = INTERFACE_DIFF.replace("validate_order", "_validate_order")
        self.assertEqual(review_roster.compute("branch", private, None, None, False)["tier"], "small")
        new = "diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1,0 +2,2 @@\n+def brand_new(x):\n+    return x\n"
        self.assertEqual(review_roster.compute("branch", new, None, None, False)["signals"]["interface_changed"], [])


class RosterCheckTests(unittest.TestCase):
    def test_a_dispatch_outside_the_roster_is_refused(self):
        roster = review_roster.compute("branch", PROBE_DIFF, None, None, False)
        ok = {"roles": roster["roster"][:2], "blind_derivation": False, "critic": False}
        self.assertEqual(review_roster.check(roster, ok), [])
        wide = {"roles": roster["roster"] + ["senior-review:security-auditor"], "blind_derivation": True, "critic": True}
        problems = review_roster.check(roster, wide)
        self.assertEqual(len(problems), 3)
        self.assertIn("senior-review:security-auditor", problems[0])

    def test_the_cli_writes_the_roster_and_refuses_an_oversized_dispatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "diff.patch").write_text(PROBE_DIFF, encoding="utf-8")
            compute = subprocess.run(
                [sys.executable, "-I", str(HELPER), "compute", "--shape", "branch",
                 "--diff", str(root / "diff.patch"), "--out", str(root / "roster.json")],
                capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(compute.returncode, 0, compute.stderr)
            self.assertEqual(json.loads(compute.stdout)["tier"], "small")
            roster = json.loads((root / "roster.json").read_text(encoding="utf-8"))
            self.assertEqual(roster["schema"], review_roster.SCHEMA)
            (root / "dispatch.json").write_text(json.dumps({"roles": ["senior-review:security-auditor"]}), encoding="utf-8")
            check = subprocess.run(
                [sys.executable, "-I", str(HELPER), "check", "--roster", str(root / "roster.json"),
                 "--dispatch", str(root / "dispatch.json")], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(check.returncode, 1)
            self.assertFalse(json.loads(check.stdout)["conforms"])


if __name__ == "__main__":
    unittest.main()
