"""Offline tests for external corpus parsing and candidate rules."""
import unittest

import external_corpus as corpus


class DiffParsingTests(unittest.TestCase):
    def test_old_side_keeps_context_and_removed_lines_only(self):
        patch = """diff --git a/pkg/a.py b/pkg/a.py
--- a/pkg/a.py
+++ b/pkg/a.py
@@ -10,3 +10,3 @@
 keep
-old value
+new value
 tail
"""
        hunks = corpus.parse_old_side(patch)
        self.assertEqual(len(hunks), 1)
        self.assertEqual(hunks[0]["path"], "pkg/a.py")
        self.assertEqual(hunks[0]["start_line"], 10)
        self.assertEqual(hunks[0]["text"], "keep\nold value\ntail\n")

    def test_new_file_has_no_old_side_hunk(self):
        patch = """diff --git a/pkg/new.py b/pkg/new.py
--- /dev/null
+++ b/pkg/new.py
@@ -0,0 +1 @@
+created
"""
        self.assertEqual(corpus.parse_old_side(patch), [])


class CandidateRuleTests(unittest.TestCase):
    def test_signal_roles_are_ranked_and_limited(self):
        roles = corpus.signal_roles("Retry after timeout; the cache returns stale database rows and leaks a socket")
        self.assertIn("temporal-resilience-auditor", roles)
        self.assertIn("data-integrity-auditor", roles)
        self.assertLessEqual(len(roles), 4)
        scores = corpus.signal_scores("Retry after timeout; the cache returns stale database rows and leaks a socket")
        self.assertGreaterEqual(scores["temporal-resilience-auditor"], 1)
        self.assertGreaterEqual(scores["data-integrity-auditor"], 1)

    def test_devign_labels_only_security_as_gold(self):
        cand = {"source": "devign", "candidate_positive_roles": ["security-auditor"],
                "candidate_negative_roles": [], "candidate_signal_scores": {"security-auditor": 1}}
        self.assertEqual(corpus.lens_decision(cand, "security-auditor")["status"], "gold_positive")
        self.assertEqual(corpus.lens_decision(cand, "logic-integrity-auditor")["status"], "unknown")

    def test_absence_is_not_a_frozen_negative(self):
        cand = {"source": "swe-bench-verified", "candidate_positive_roles": [],
                "candidate_negative_roles": [], "candidate_signal_scores": {}}
        decision = corpus.lens_decision(cand, "cleanup-auditor")
        self.assertEqual(decision["status"], "candidate_negative_from_absence")

    def test_adjudication_uses_evidence_not_patch_keywords(self):
        cand = {"id": "X", "source": "swe-bench-verified", "candidate_positive_roles": ["temporal-resilience-auditor"],
                "candidate_negative_roles": [], "candidate_signal_scores": {"temporal-resilience-auditor": 9},
                "label_evidence": {"problem_statement_excerpt": "The result is incorrect for nested models"},
                "input": {"chars": 100}}
        result = corpus.adjudicate_candidate(cand)
        self.assertEqual(result["label_status"], "needs_manual_adjudication")
        self.assertEqual(result["positive_roles"], [])

    def test_adjudication_accepts_strong_external_evidence(self):
        cand = {"id": "X", "source": "swe-bench-verified", "candidate_positive_roles": ["temporal-resilience-auditor"],
                "candidate_negative_roles": [], "candidate_signal_scores": {},
                "label_evidence": {"problem_statement_excerpt": "The worker hangs after a timeout and keeps retrying forever"},
                "input": {"chars": 100}}
        result = corpus.adjudicate_candidate(cand)
        self.assertEqual(result["label_status"], "adjudicated_silver")
        self.assertIn("temporal-resilience-auditor", result["positive_roles"])
        self.assertIn("cleanup-auditor", result["negative_roles"])

    def test_strong_roles_require_two_evidence_terms(self):
        scores = {"temporal-resilience-auditor": 2, "cleanup-auditor": 1, "ui-race-auditor": 3}
        self.assertEqual(corpus.strong_roles(scores, corpus.TARGET_FILL_ROLES),
                         ["temporal-resilience-auditor", "ui-race-auditor"])

    def test_strong_resource_phrase_can_accept_resource(self):
        cand = {"id": "X", "source": "swe-bench-verified", "candidate_positive_roles": ["resource-lifecycle-auditor"],
                "candidate_negative_roles": [], "candidate_signal_scores": {},
                "label_evidence": {"problem_statement_excerpt": "The worker hits too many open files after each run"},
                "input": {"chars": 100}}
        result = corpus.adjudicate_candidate(cand)
        self.assertIn("resource-lifecycle-auditor", result["positive_roles"])

    def test_freeze_selection_preserves_split_quotas(self):
        candidates, adjudicated = [], []
        index = 0
        for split, quota in (("development", 4), ("verification", 2)):
            for role in corpus.ROLES:
                for _ in range(quota):
                    index += 1
                    cid = f"X{index:03}"
                    candidates.append({"id": cid, "repo": f"r{index}", "split_proposal": split})
                    adjudicated.append({"id": cid, "label_status": "adjudicated_silver",
                                        "positive_roles": [role], "negative_roles": []})
        selected = corpus.select_freeze(candidates, adjudicated)
        self.assertEqual(len(selected), 48)
        for role in corpus.ROLES:
            self.assertEqual(sum(role in item["positive_roles"] for item in adjudicated if item["id"] in selected), 6)

    def test_visibility_category_uses_shown_code_only(self):
        self.assertEqual(corpus.visibility_category("temporal-resilience-auditor", "retry after timeout"), "visible_signal_in_code")
        self.assertEqual(corpus.visibility_category("temporal-resilience-auditor", "use a timeout value"), "weak_signal_in_code")
        self.assertEqual(corpus.visibility_category("security-auditor", "return value + 1"), "no_signal_in_code_external_only")

    def test_rubric_covers_all_eight_lenses(self):
        self.assertEqual(set(corpus.RUBRIC), set(corpus.ROLES))
        for rule in corpus.RUBRIC.values():
            self.assertTrue(rule["applies"])
            self.assertTrue(rule["excludes"])

    def test_resolve_slot_classifies_two_reader_agreement(self):
        a = {"judgment": "applicable", "confidence": "high", "code_anchor_or_exclusion": "line 1"}
        n = {"judgment": "not_applicable", "confidence": "high", "code_anchor_or_exclusion": "excluded"}
        u = {"judgment": "insufficient_evidence", "confidence": "low", "code_anchor_or_exclusion": "fragment"}
        self.assertEqual(corpus.resolve_slot(a, a)["visibility_status"], "code_supported")
        self.assertEqual(corpus.resolve_slot(n, n)["visibility_status"], "code_not_applicable")
        self.assertEqual(corpus.resolve_slot(a, u)["visibility_status"], "disputed_applicable")
        self.assertEqual(corpus.resolve_slot(u, n)["visibility_status"], "insufficient_or_external_only")

    def test_split_assignment_is_deterministic(self):
        dev, ver = {"a/one"}, {"b/two"}
        self.assertEqual(corpus.split_for_repo("a/one", dev, ver), "development")
        self.assertEqual(corpus.split_for_repo("b/two", dev, ver), "verification")
        self.assertIn(corpus.split_for_repo("c/three", dev, ver), ("development", "verification"))


if __name__ == "__main__":
    unittest.main()
