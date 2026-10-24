"""The review roster is computed from measured signals, never chosen by the model.

Pinned on the probe of 2026-10-19: a fix inside one function of python-humanize
got seven reviewers, 40 minutes and 30.90 USD. The same diff must now compute
`small` for a branch review and one reviewer for the light review, and a
dispatch that adds a security auditor must be refused.
"""

import difflib
import copy
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

MAP_SCRIPTS = REPO_ROOT / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(MAP_SCRIPTS))
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

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


def source_diff(path, removed="", added="", deleted=False):
    destination = "/dev/null" if deleted else f"b/{path}"
    lines = [f"diff --git a/{path} b/{path}", f"--- a/{path}", f"+++ {destination}", "@@ -1 +1 @@"]
    lines += ["-" + line for line in removed.splitlines()]
    lines += ["+" + line for line in added.splitlines()]
    return "\n".join(lines) + "\n"


class UnifiedDiffParsingTests(unittest.TestCase):
    def test_concatenated_unified_diffs_preserve_paths_and_specialist_selection(self):
        diff = "".join(difflib.unified_diff(
            ["value = 1\n"], ["value = 2\n"],
            fromfile="a/src/value.py", tofile="b/src/value.py"))
        diff += "".join(difflib.unified_diff(
            [".dialog {\n", "  position: fixed;\n", "}\n"],
            [".dialog {\n", "  position: absolute;\n", "}\n"],
            fromfile="a/src/dialog.css", tofile="b/src/dialog.css"))
        self.assertEqual(review_roster.numstat_from_diff(diff), [
            {"path": "src/value.py", "added": 1, "removed": 1},
            {"path": "src/dialog.css", "added": 1, "removed": 1},
        ])
        roster = review_roster.compute("branch", diff, None, None, False)
        self.assertIn("senior-review:accessibility-auditor", roster["roster"])
        self.assertEqual(roster["signals"]["files"], 2)

    def test_deleted_and_added_files_keep_paths_across_zero_length_hunks(self):
        diff = "".join(difflib.unified_diff(
            [".dialog { overflow-y: auto; }\n"], [],
            fromfile="a/src/dialog.css", tofile="/dev/null"))
        diff += "".join(difflib.unified_diff(
            [], ["FROM python:3.13-slim\n"],
            fromfile="/dev/null", tofile="b/Dockerfile"))
        self.assertEqual(review_roster.numstat_from_diff(diff), [
            {"path": "src/dialog.css", "added": 0, "removed": 1},
            {"path": "Dockerfile", "added": 1, "removed": 0},
        ])
        roster = review_roster.compute("branch", diff, None, None, False)
        self.assertIn("senior-review:accessibility-auditor", roster["roster"])
        self.assertIn("senior-review:operability-auditor", roster["roster"])

    def test_header_like_source_lines_are_counted_inside_their_hunk(self):
        diff = "".join(difflib.unified_diff(
            ["-- a/src/ghost.css\n", "tail\n"],
            ["++ b/src/ghost.css\n", "tail\n"],
            fromfile="a/docs/example.txt", tofile="b/docs/example.txt"))
        diff += "".join(difflib.unified_diff(
            ["value = 1\n"], ["value = 2\n"],
            fromfile="a/src/value.py", tofile="b/src/value.py"))
        self.assertEqual(review_roster.numstat_from_diff(diff), [
            {"path": "docs/example.txt", "added": 1, "removed": 1},
            {"path": "src/value.py", "added": 1, "removed": 1},
        ])
        roster = review_roster.compute("branch", diff, None, None, False)
        self.assertNotIn("senior-review:accessibility-auditor", roster["roster"])

    def test_rename_keeps_both_paths_and_untracked_source_keeps_its_controls(self):
        diff = ("diff --git a/app/auth/check.py b/app/check.py\n"
                "similarity index 100%\nrename from app/auth/check.py\nrename to app/check.py\n")
        context = {"sources": [{"path": "web/consent.css", "status": "untracked",
                                 "text": ":root { overflow: hidden; }"}]}
        result = review_roster.compute("branch", diff, None, None, False, context=context)
        self.assertEqual(result["grounding"]["conclusion_paths"],
                         ["app/auth/check.py", "app/check.py", "web/consent.css"])
        self.assertIn("app/auth/check.py", result["signals"]["sensitive_paths"])
        self.assertTrue(result["signals"]["content"]["accessibility"])
        self.assertEqual(result["signals"]["lines"], 1)
        self.assertEqual(result["grounding"]["changes"][0]["old_path"], "app/auth/check.py")


class RosterComputationTests(unittest.TestCase):
    def test_static_presentation_changes_reach_accessibility_without_an_async_signal(self):
        for path, content in (
            ("src/consent.css", ":root { overflow: hidden; position: fixed; }"),
            ("src/consent.html", '<button aria-label="Accept">OK</button>'),
            ("src/consent.vue", '<template><div class="consent" /></template>'),
            ("src/render.py", "return '<button>Accept</button>'"),
        ):
            with self.subTest(path=path):
                roster = review_roster.compute("branch", source_diff(path, added=content), None, None, False)
                self.assertIn("senior-review:accessibility-auditor", roster["roster"])
                self.assertNotIn("senior-review:ui-race-auditor", roster["roster"])
                self.assertNotIn("platform-engineering:platform-reviewer", roster["roster"])
                self.assertEqual(roster["roster"].count("senior-review:accessibility-auditor"), 1)

    def test_removed_controls_and_deleted_files_keep_their_specialist_signals(self):
        for path, removed, role, deleted in (
            ("src/keyboard.ts", "if (event.key !== 'Escape') return;", "senior-review:accessibility-auditor", False),
            ("src/dialog.css", ".dialog { overflow-y: auto; }", "senior-review:accessibility-auditor", True),
            ("src/service.py", "rate_limit = 10", "senior-review:performance-auditor", False),
            ("src/queries.sql", "-- unbounded query\nSELECT id FROM orders", "senior-review:performance-auditor", True),
            ("src/service.py", "restore_backup(snapshot)", "senior-review:operability-auditor", True),
            ("src/client.ts", "localStorage.removeItem('token');", "platform-engineering:platform-reviewer", False),
        ):
            with self.subTest(path=path, role=role):
                diff = source_diff(path, removed=removed, deleted=deleted)
                roster = review_roster.compute("branch", diff, None, None, False)
                self.assertIn(role, roster["roster"])
                self.assertEqual(roster["signals"]["files"], 1)
                self.assertEqual(roster["signals"]["lines"], len(removed.splitlines()))
                self.assertIn(path, {row["path"] for row in review_roster.numstat_from_diff(diff)})

    def test_performance_operations_and_platform_have_distinct_activation_evidence(self):
        specialists = {"senior-review:performance-auditor", "senior-review:operability-auditor",
                       "platform-engineering:platform-reviewer"}
        for path, content, expected in (
            ("src/queries.sql", "SELECT id FROM orders", "senior-review:performance-auditor"),
            ("src/report.py", "items = sorted(records)", "senior-review:performance-auditor"),
            ("src/cache.py", "cache_ttl = 60", "senior-review:performance-auditor"),
            ("Dockerfile", "FROM python:3.13-slim", "senior-review:operability-auditor"),
            (".github/workflows/release.yml", "name: release", "senior-review:operability-auditor"),
            ("src/service.py", "logger.error('request failed')", "senior-review:operability-auditor"),
            ("src/service.py", "feature_flag = 'new_checkout'", "senior-review:operability-auditor"),
            ("src/service-worker.ts", "const version = 2;", "platform-engineering:platform-reviewer"),
            ("src/desktop.ts", "const window = new BrowserWindow();", "platform-engineering:platform-reviewer"),
        ):
            with self.subTest(path=path, content=content):
                roster = review_roster.compute("branch", source_diff(path, added=content), None, None, False)
                self.assertEqual(set(roster["roster"]) & specialists, {expected})

    def test_empty_diff_and_generic_words_do_not_activate_specialists(self):
        specialists = {"senior-review:accessibility-auditor", "senior-review:performance-auditor",
                       "senior-review:operability-auditor", "platform-engineering:platform-reviewer"}
        for diff in ("", source_diff("src/empty.css"),
                     source_diff("src/value.py", added="message = 'error retry timeout cache'"),
                     source_diff("docs/styles.md", added="value = 2")):
            with self.subTest(diff=diff):
                roster = review_roster.compute("branch", diff, None, None, False)
                self.assertFalse(set(roster["roster"]) & specialists)

    def test_specialist_signals_do_not_widen_the_light_review_or_change_the_floor(self):
        diff = source_diff("src/page.tsx", added="const items = sorted(records); localStorage.clear(); logger.error('x');")
        light = review_roster.compute("light", diff, None, None, False)
        self.assertEqual(light["roster"], ["senior-review:code-auditor"])
        branch = review_roster.compute("branch", diff, None, None, False)
        self.assertEqual(branch["tier"], "small")
        self.assertEqual(branch["roster"][:2], review_roster.SMALL_ROSTER)
        self.assertEqual(branch["support"], review_roster.SUPPORT)
        self.assertFalse(branch["blind_derivation"])
        self.assertFalse(branch["critic"])
        for role in ("accessibility-auditor", "performance-auditor", "operability-auditor"):
            self.assertIn(f"senior-review:{role}", branch["roster"])

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

    def test_a_record_a_plan_or_a_document_gets_the_claim_check_when_light(self):
        spec = "diff --git a/docs/adr/0004-x.md b/docs/adr/0004-x.md\n+++ b/docs/adr/0004-x.md\n+Tokens expire after authentication.\n"
        for kind in ("plan", "spec", "doc"):
            with self.subTest(kind=kind):
                roster = review_roster.compute("light", spec, None, None, False, kind)
                self.assertEqual(roster["roster"], ["senior-review:premise-auditor"])
                self.assertEqual(roster["kind"], kind)
        branch = review_roster.compute("branch", spec, None, None, False, "spec")
        self.assertEqual(branch["roster"][:4], review_roster.KIND_ROSTER["spec"])
        self.assertIn("senior-review:security-auditor", branch["roster"])
        code = review_roster.compute("branch", PROBE_DIFF.replace("negative = False", "token = None"), None, None, False)
        self.assertNotIn("senior-review:security-auditor", code["roster"])
        deeper = review_roster.compute("branch", spec, None, None, True, "spec")
        self.assertEqual(deeper["roster"], branch["roster"])
        self.assertIn("fixed set", deeper["advice"][0])
        with self.assertRaises(ValueError):
            review_roster.compute("light", spec, None, None, False, "poem")

    def test_support_roles_are_the_verification_lenses_and_the_maps_at_large(self):
        small = review_roster.compute("branch", PROBE_DIFF, None, None, False)
        self.assertEqual(small["support"], review_roster.SUPPORT)
        large = review_roster.compute("branch", INTERFACE_DIFF, None, None, False)
        self.assertIn("codebase-map:semantic-interconnect-mapper", large["support"])
        self.assertIn("review-branch", review_roster.compute("light", PROBE_DIFF, None, None, True)["advice"][0])

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

    def test_deeper_raises_one_tier_and_nothing_lowers(self):
        self.assertEqual(review_roster.compute("branch", PROBE_DIFF, None, None, True)["tier"], "medium")
        self.assertEqual(review_roster.compute("branch", WIDE_DIFF, None, None, True)["tier"], "large")
        self.assertEqual(review_roster.compute("branch", INTERFACE_DIFF, None, None, True)["tier"], "large")

    def test_private_signatures_and_new_functions_are_not_interface_changes(self):
        private = INTERFACE_DIFF.replace("validate_order", "_validate_order")
        self.assertEqual(review_roster.compute("branch", private, None, None, False)["tier"], "small")
        new = "diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1,0 +2,2 @@\n+def brand_new(x):\n+    return x\n"
        self.assertEqual(review_roster.compute("branch", new, None, None, False)["signals"]["interface_changed"], [])


class CandidateGroundingTests(unittest.TestCase):
    """Real producer packets, with the review's independently retained snapshots."""

    def setUp(self):
        # A visible owned fixture avoids the map's dot-directory exclusion even
        # when the test runner's TEMP is inside its .daodan run directory.
        temporary = tempfile.TemporaryDirectory(prefix="roster-map-", dir=REPO_ROOT)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True, capture_output=True)
        self.write("pkg/__init__.py", "")
        self.before = "def helper(value):\n    return value + 1\n\ndef extra():\n    return 10\n"
        self.write("pkg/leaf.py", self.before)
        self.write("pkg/caller.py", "from .leaf import helper\n\ndef run(value):\n    return helper(value)\n")
        self.write("pkg/top.py", "from .caller import run\n\ndef top(value):\n    return run(value)\n")
        self.base = self.root / ".codebase-map/base.sqlite"

    def write(self, path, text):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")

    def packets(self, after, *, neighbors=20, targets=None, stale_source=False):
        if not self.base.exists():
            snapshot.write_snapshot(self.root, self.base)
        self.write("pkg/leaf.py", after)
        candidate_path = self.base.with_name("candidate.sqlite")
        with open_snapshot(self.base) as base:
            snapshot.write_snapshot(self.root, candidate_path, previous=base)
            with open_snapshot(candidate_path) as candidate:
                context = {
                    "scope_id": "candidate", "review_basis": "changeset",
                    "base": snapshot._snapshot_info(base),
                    "candidate": snapshot._snapshot_info(candidate),
                    "stale_callers": semantic_store.build_stale_callers(base, candidate),
                    "conclusion_paths": ["pkg/leaf.py"],
                }
                if stale_source:
                    self.write("pkg/leaf.py", after + "\n# edited after snapshot\n")
                impact = semantic_store.build_edit_impact(
                    candidate, targets or ["pkg/leaf.py::helper"], neighbors=neighbors)
        diff = "".join(difflib.unified_diff(self.before.splitlines(True), after.splitlines(True),
                                         fromfile="a/pkg/leaf.py", tofile="b/pkg/leaf.py"))
        return diff, impact, context

    def compute(self, diff, impact, context, shape="branch"):
        return review_roster.compute(shape, diff, None, impact, False, context=context)

    def test_composed_code_floor_survives_opaque_calls_and_missing_graph(self):
        identities = ["code-auditor", "local-correctness-auditor", "local-concurrency-auditor",
                      "input-validation-auditor", "resource-lifecycle-auditor", "algorithmic-cost-auditor",
                      "security-auditor", "data-integrity-auditor", "chicken-egg-detector",
                      "temporal-resilience-auditor", "distributed-flow-auditor", "api-contract-auditor"]
        catalog = {"entries": [{"id": "senior-review:" + name} for name in identities]
                              + [{"id": "testing:test-reliability-auditor"}]}
        catalog["entries"][0]["members"] = ["senior-review:local-correctness-auditor",
                                            "senior-review:local-concurrency-auditor"]
        context = {"catalog": catalog, "candidate": {"digest": "now"}, "scope_id": "opaque"}
        diff = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-return a(x)\n+return b(x)\n"
        result = self.compute(diff, None, context, shape="light")
        required = {row["specialist_id"] for row in result["required_specialists"]}
        for name in ("input-validation-auditor", "resource-lifecycle-auditor", "data-integrity-auditor"):
            self.assertIn("senior-review:" + name, required)
        self.assertEqual(result["roster"], ["senior-review:code-auditor"])
        self.assertEqual(result["jobs"], [])

    def test_floor_exclusion_needs_evidence_bound_to_the_same_candidate_and_scope(self):
        catalog = {"entries": [{"id": "senior-review:code-auditor", "members": ["senior-review:local-correctness-auditor"]},
                               {"id": "senior-review:local-correctness-auditor"},
                               {"id": "senior-review:resource-lifecycle-auditor"}]}
        context = {"catalog": catalog, "candidate": {"digest": "now"}, "scope_id": "one"}
        exclusion = {"specialist_id": "senior-review:resource-lifecycle-auditor", "scope_id": "one",
                     "candidate": context["candidate"], "status": "not-applicable",
                     "evidence": [{"path": "a.py", "reason": "Complete target and callers are pure arithmetic; no acquisition or ownership."}]}
        for change in ({"candidate": {"digest": "old"}}, {"scope_id": "elsewhere"}, {"evidence": []}, {"status": "unknown"}):
            with self.subTest(change=change):
                context["applicability"] = [{**exclusion, **change}]
                result = self.compute(PROBE_DIFF, None, context, shape="light")
                self.assertIn("senior-review:resource-lifecycle-auditor",
                              [row["specialist_id"] for row in result["required_specialists"]])
        context["applicability"] = [exclusion]
        result = self.compute(PROBE_DIFF, None, context, shape="light")
        self.assertNotIn("senior-review:resource-lifecycle-auditor",
                         [row["specialist_id"] for row in result["required_specialists"]])
        self.assertEqual(result["grounding"]["applicability"], [exclusion])
        context["required_specialists"] = [{"specialist_id": exclusion["specialist_id"],
            "scope_id": "one", "evidence": ["explicit caller requirement"]}]
        result = self.compute(PROBE_DIFF, None, context, shape="light")
        self.assertIn(exclusion["specialist_id"], [row["specialist_id"] for row in result["required_specialists"]])

    def test_real_effect_delta_selects_required_specialist(self):
        diff, impact, context = self.packets(self.before.replace("value + 1", "value + extra()"))
        result = self.compute(diff, impact, context)
        self.assertEqual(result["tier"], "medium")
        self.assertEqual(result["signals"]["effects_changed"], ["pkg/leaf.py::helper"])
        required = [item for item in result["required_specialists"]
                    if item["specialist_id"] == "senior-review:api-contract-auditor"]
        self.assertEqual(len(required), 1)
        self.assertEqual(required[0]["scope_id"], "candidate")
        self.assertIn("effects_changed", json.dumps(required[0]["evidence"]))
        self.assertIn("pkg/caller.py", result["grounding"]["read_scope"])
        self.assertIn("pkg/top.py", result["grounding"]["read_scope"])

    def test_cross_provider_handoffs_survive_missing_foreign_or_stale_graphs(self):
        # The provider identifies a boundary; preparation records the receiving
        # obligation. Graph silence cannot cancel that source-backed handoff.
        handoffs = (
            ("server-action", "sources", "senior-review:authorization-auditor",
             "Guarded page loader does not guard independently callable action."),
            ("client-authority", "requirements", "senior-review:authorization-auditor",
             "Tenant and export authority must come from the authenticated server principal."),
            ("offline-merge", "configurations", "senior-review:transaction-integrity-auditor",
             "Required concurrent edits must survive replay and offline reconciliation."),
        )
        for graph in (None, {"schema": "foreign/packet/v1"},
                      {"schema": "edit-impact/v2", "source": {"error": "stale snapshot"}}):
            for name, source_kind, receiver, reason in handoffs:
                with self.subTest(graph=graph, handoff=name):
                    path = f"pkg/{name}.py"
                    context = {"candidate": {"digest": "actual-candidate"},
                               "scope_id": "provider-boundary", "review_basis": "content",
                               "inventory": [{"path": path}], source_kind: [{
                                   "path": path, "reason": reason,
                                   "specialist_ids": [receiver]}]}
                    result = self.compute("", graph, context, shape="light")
                    required = [row for row in result["required_specialists"]
                                if row["specialist_id"] == receiver]
                    self.assertEqual(len(required), 1)
                    self.assertEqual(required[0]["scope_id"], "provider-boundary")
                    self.assertIn(reason, json.dumps(required[0]["evidence"]))
                    self.assertIn({"source": source_kind, **context[source_kind][0]},
                                  required[0]["evidence"])

    def test_old_history_is_not_candidate_delta(self):
        self.write("pkg/leaf.py", self.before.replace("helper(value)", "helper(value, obsolete=None)"))
        initial = self.base.with_name("initial.sqlite")
        snapshot.write_snapshot(self.root, initial)
        self.write("pkg/leaf.py", self.before)
        with open_snapshot(initial) as previous:
            snapshot.write_snapshot(self.root, self.base, previous=previous)
        diff, impact, context = self.packets(self.before.replace("value + 1", "value + 2"))
        self.assertIn("interface_changed", [row["change_kind"] for row in impact["targets"][0]["recent_changes"]])
        result = self.compute(diff, impact, context)
        self.assertEqual(result["tier"], "small")
        self.assertEqual(result["signals"]["interface_changed"], [])
        self.assertEqual(result["signals"]["effects_changed"], [])
        self.assertIn("interface_changed", json.dumps(result["grounding"]["graph"]["history"]))

    def test_real_caller_totals_raise_tier_without_losing_omissions(self):
        for count, tier in ((7, "medium"), (25, "large")):
            with self.subTest(count=count):
                self.write("pkg/caller.py", "from .leaf import helper\n" + "".join(
                    f"\ndef caller_{n}(value):\n    return helper(value)\n" for n in range(count)))
                self.write("pkg/leaf.py", self.before)
                snapshot.write_snapshot(self.root, self.base)
                diff, impact, context = self.packets(self.before.replace("value + 1", "value + 2"), neighbors=1)
                result = self.compute(diff, impact, context)
                self.assertEqual(result["tier"], tier)
                self.assertEqual(result["signals"]["max_callers"], count)
                self.assertTrue(any("omitted" in gap for gap in result["gaps"]))

    def test_stale_or_truncated_graph_keeps_gaps(self):
        self.write("pkg/caller.py", "from .leaf import helper\n\ndef run(x):\n    return helper(x)\n\ndef again(x):\n    return helper(x)\n")
        diff, impact, context = self.packets(self.before.replace("value + 1", "value + missing()"),
                                             neighbors=1, targets=["pkg/leaf.py", "unknown.py"], stale_source=True)
        # Producer truncation is exercised by selecting more than its target cap.
        self.write("many.py", "\n".join(f"def f{n}():\n    return {n}" for n in range(30)))
        many = self.base.with_name("many.sqlite")
        snapshot.write_snapshot(self.root, many)
        with open_snapshot(many) as store:
            truncated = semantic_store.build_edit_impact(store, ["many.py"], include_source=False)
        result = self.compute(diff, impact, context)
        gaps = "\n".join(result["gaps"])
        self.assertIn("unknown.py", gaps)
        self.assertIn("omitted", gaps)
        self.assertIn(impact["source"]["error"], gaps)
        self.assertIn("unavailable_edge_kinds", gaps)
        self.assertTrue(result["grounding"]["graph"]["freshness_basis"])
        self.assertTrue(any("truncated_targets" in gap for gap in self.compute("", truncated, context)["gaps"]))

    def test_parser_failure_and_unknown_applicability_cannot_become_a_skip(self):
        self.write("broken.py", "def broken(:\n")
        snapshot.write_snapshot(self.root, self.base)
        with open_snapshot(self.base) as store:
            entry = store.get_file("broken.py", semantic=False)
        context = {"review_basis": "content", "scope_id": "broken",
                   "inventory": [{"path": "broken.py", "status": entry["status"]}],
                   "requirements": [{"id": "R1", "applicability": "unknown",
                                     "specialist_ids": ["senior-review:authorization-auditor"]}]}
        result = self.compute("", None, context)
        gaps = "\n".join(result["gaps"])
        self.assertIn("parse-error", gaps)
        self.assertIn("applicability: unknown", gaps)
        self.assertIn("senior-review:authorization-auditor",
                      {row["specialist_id"] for row in result["required_specialists"]})

    def test_wrong_snapshot_schema_or_symbol_digest_is_not_authoritative(self):
        diff, impact, context = self.packets(self.before.replace("value + 1", "value + extra()"))
        for corrupt in ("snapshot", "schema", "digest"):
            changed_context, changed_impact = copy.deepcopy(context), copy.deepcopy(impact)
            if corrupt == "snapshot":
                changed_context["stale_callers"]["candidate"]["root"] = "/different/project"
            elif corrupt == "schema":
                changed_context["stale_callers"]["schema"] = "foreign/packet/v1"
            else:
                changed_context["stale_callers"]["changed"][0]["new"]["effects_hash"] = "unrelated"
            with self.subTest(corrupt=corrupt):
                result = self.compute(diff, changed_impact, changed_context)
                self.assertEqual(result["signals"]["effects_changed"], [])
                self.assertTrue(result["gaps"])

    def test_unbound_legacy_graph_is_a_gap_not_coverage(self):
        impact = {"targets": [{"id": "x", "callers": {"total": 25},
                               "history": [{"kind": "interface_changed"}]}]}
        result = review_roster.compute("branch", PROBE_DIFF, None, impact, False)
        self.assertEqual(result["tier"], "small")
        self.assertFalse(result["signals"]["map_available"])
        self.assertTrue(result["gaps"])

    def test_unmatched_detection_leaves_applicability_unknown(self):
        result = self.compute("", None, {"review_basis": "content", "inventory": [{"path": "service.py"}]})
        self.assertEqual(result["signals"].get("applicability", {}).get("persistence"), "unknown")
        self.assertTrue(any("applicability" in gap for gap in result["gaps"]))

    def test_content_audit_keeps_unchanged_requirements(self):
        context = {"review_basis": "content", "scope_id": "package",
                   "inventory": [{"path": "pkg/service.py", "status": "parsed"}],
                   "requirements": [{"id": "R1", "text": "Every transaction is atomic.",
                                     "specialist_ids": ["senior-review:transaction-integrity-auditor"]}]}
        result = self.compute("", None, context)
        self.assertEqual(result["review_basis"], "content")
        self.assertEqual(result["signals"]["files"], 1)
        self.assertEqual(result["signals"]["lines"], 0)
        self.assertEqual(result["signals"]["effects_changed"], [])
        self.assertEqual(result["grounding"]["requirements"], context["requirements"])
        self.assertIn(("senior-review:transaction-integrity-auditor", "package"),
                      {(row["specialist_id"], row["scope_id"]) for row in result["required_specialists"]})

    def test_hidden_config_and_static_css_remain_reviewable(self):
        context = {"review_basis": "content", "scope_id": "entry",
                   "conclusion_paths": [".github/workflows/release.yml", "src/consent.css"],
                   "inventory": [], "sources": [{"path": "src/consent.css", "text": ":root { overflow:hidden; }"}],
                   "configurations": [{"path": ".github/workflows/release.yml", "status": "unavailable"}],
                   "required_specialists": [
                       {"specialist_id": "senior-review:accessible-perception-auditor", "scope_id": "entry",
                        "evidence": [{"path": "src/consent.css", "reason": "entry cascade"}]}]}
        result = self.compute("", None, context)
        self.assertIn("src/consent.css", result["grounding"]["read_scope"])
        self.assertIn(".github/workflows/release.yml", result["grounding"]["conclusion_paths"])
        self.assertTrue(result["signals"]["content"]["accessibility"])
        self.assertTrue(result["signals"]["content"]["operability"])
        self.assertTrue(any("unavailable" in gap for gap in result["gaps"]))

    def test_catalog_expansion_is_scoped_and_light_keeps_one_discovery(self):
        context = {"scope_id": "entry", "catalog": {"entries": [
            {"id": "senior-review:code-auditor", "members": ["senior-review:local-correctness-auditor"]},
            {"id": "senior-review:local-correctness-auditor", "kind": "role"}]},
            "required_specialists": [{"specialist_id": "senior-review:local-correctness-auditor",
                                       "scope_id": "other", "evidence": ["second scope"]}]}
        result = self.compute(PROBE_DIFF, None, context, shape="light")
        self.assertEqual(result["roster"], ["senior-review:code-auditor"])
        self.assertEqual([(row["specialist_id"], row["scope_id"]) for row in result["required_specialists"]
                          if row["specialist_id"] == "senior-review:local-correctness-auditor"],
                         [("senior-review:local-correctness-auditor", "entry"),
                          ("senior-review:local-correctness-auditor", "other")])
        self.assertTrue(any("floor missing" in gap for gap in result["gaps"]))

    def test_malformed_specialist_evidence_cannot_be_accepted_as_coverage(self):
        for evidence in (None, [], "unsupported", [""]):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                self.compute("", None, {"required_specialists": [
                    {"specialist_id": "senior-review:api-contract-auditor", "scope_id": "api",
                     "evidence": evidence}]})


class RosterCheckTests(unittest.TestCase):
    def test_cli_context_preserves_content_requirements(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "diff.patch").write_text("", encoding="utf-8")
            requirement = {"id": "R1", "text": "Transactions are atomic.",
                           "specialist_ids": ["senior-review:transaction-integrity-auditor"]}
            (root / "context.json").write_text(json.dumps({
                "review_basis": "content", "scope_id": "service", "requirements": [requirement],
                "inventory": [{"path": "service.py", "status": "parsed"}]}), encoding="utf-8")
            process = subprocess.run(
                [sys.executable, "-I", str(HELPER), "compute", "--shape", "branch",
                 "--diff", str(root / "diff.patch"), "--context", str(root / "context.json"),
                 "--out", str(root / "roster.json")], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads((root / "roster.json").read_text(encoding="utf-8"))
            self.assertEqual(result["review_basis"], "content")
            self.assertEqual(result["grounding"]["requirements"], [requirement])

    def test_a_dispatch_outside_the_roster_is_refused(self):
        roster = review_roster.compute("branch", PROBE_DIFF, None, None, False)
        ok = {"roles": roster["roster"][:2] + ["project-protocol:isolated-worker"], "blind_derivation": False, "critic": False}
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
                [sys.executable, "-I", str(HELPER), "compute", "--shape", "branch", "--id", "R4",
                 "--stage", "candidate", "--diff", str(root / "diff.patch"), "--out", str(root / "roster.json")],
                capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(compute.returncode, 0, compute.stderr)
            self.assertEqual(json.loads(compute.stdout)["tier"], "small")
            roster = json.loads((root / "roster.json").read_text(encoding="utf-8"))
            self.assertEqual(roster["schema"], review_roster.SCHEMA)
            self.assertEqual((roster["id"], roster["stage"], roster["kind"]), ("R4", "candidate", "changeset"))
            (root / "dispatch.json").write_text(json.dumps({"roles": ["senior-review:security-auditor"]}), encoding="utf-8")
            check = subprocess.run(
                [sys.executable, "-I", str(HELPER), "check", "--roster", str(root / "roster.json"),
                 "--dispatch", str(root / "dispatch.json")], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(check.returncode, 1)
            self.assertFalse(json.loads(check.stdout)["conforms"])


if __name__ == "__main__":
    unittest.main()
