"""Pins the capability resolution chain: one authoritative source, then two declared fallbacks.

The numeric assertions are the measured counterexamples from the pinned 2026-10-07 Arena
snapshot. They exist so a later edit cannot silently reintroduce a price-to-capability
inference or a scalar family guess.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "plugins" / "project-protocol" / "skills" / "project-protocol" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import capability_resolver as cr  # noqa: E402

SNAPSHOT = {
    "schema": "daodan/benchmark-snapshot/v1",
    "status": "captured",
    "authority": {"advisory_only": True},
    "source": {"snapshot_date": "2026-10-07",
               "commit": {"sha": "b6ab43b16f8cb4fd60d79a2a199ee590e9548bc0"}},
    "boards": {"code": {"rows_verbatim": []}},
    "match_index": {
        "claudeopus55": [
            {"category": "code", "arena_name": "claude-opus-5.5-max", "effort": "max",
             "vendor": "Anthropic", "rank": 1, "score": 1814.0, "ci": 16.0, "votes": 2229,
             "observations_in_category": 1, "identity_conflict": False}],
        "claudeopus5": [
            {"category": "code", "arena_name": "claude-opus-5-max", "effort": "max",
             "vendor": "Anthropic", "rank": 7, "score": 1692.0, "ci": 10.0, "votes": 100,
             "observations_in_category": 1, "identity_conflict": False}],
        "claudesonnet55": [
            {"category": "code", "arena_name": "claude-sonnet-5.5-xhigh", "effort": "xhigh",
             "vendor": "Anthropic", "rank": 3, "score": 1773.0, "ci": 15.0, "votes": 2150,
             "observations_in_category": 2, "identity_conflict": False},
            {"category": "code", "arena_name": "claude-sonnet-5.5-high", "effort": "high",
             "vendor": "Anthropic", "rank": 6, "score": 1716.0, "ci": 11.0, "votes": 3787,
             "observations_in_category": 2, "identity_conflict": False}],
        "gpt6astra": [
            {"category": "code", "arena_name": "gpt-6-astra-max", "effort": "max",
             "vendor": "OpenAI", "rank": 2, "score": 1788.0, "ci": 11.0, "votes": 5057,
             "observations_in_category": 2, "identity_conflict": False},
            {"category": "code", "arena_name": "gpt-6-astra-high", "effort": "high",
             "vendor": "OpenAI", "rank": 6, "score": 1740.0, "ci": 10.0, "votes": 900,
             "observations_in_category": 2, "identity_conflict": False}],
        "claudefable51": [
            {"category": "code", "arena_name": "claude-fable-5.1-max", "effort": "max",
             "vendor": "Anthropic", "rank": 5, "score": 1745.0, "ci": 9.0, "votes": 6521,
             "observations_in_category": 1, "identity_conflict": False}],
        "gpt61sol": [
            {"category": "code", "arena_name": "gpt-6.1-sol-max", "effort": "max",
             "vendor": "OpenAI", "rank": 4, "score": 1757.0, "ci": 15.0, "votes": 1965,
             "observations_in_category": 1, "identity_conflict": False}],
        "qwen38": [
            {"category": "code", "arena_name": "qwen3.8-max", "effort": None,
             "vendor": "Alibaba", "rank": 10, "score": 1672.0, "ci": 12.0, "votes": 3450,
             "observations_in_category": 1, "identity_conflict": False}],
        "qwen38flashnext": [
            {"category": "code", "arena_name": "qwen3.8-flash-next", "effort": None,
             "vendor": "Alibaba", "rank": 17, "score": 1632.0, "ci": 12.0, "votes": 50,
             "observations_in_category": 1, "identity_conflict": False}],
        "clashmodel": [
            {"category": "code", "arena_name": "clash-model-max", "effort": "max",
             "vendor": "A", "rank": 1, "score": 1500.0, "ci": 5.0, "votes": 1,
             "observations_in_category": 2, "identity_conflict": True},
            {"category": "code", "arena_name": "clash-model-max", "effort": "max",
             "vendor": "B", "rank": 2, "score": 1400.0, "ci": 5.0, "votes": 1,
             "observations_in_category": 2, "identity_conflict": True}],
    },
}

POLICY = {
    "family_of": {"tri-llm-gateway/claude-opus-5-5": "claude-opus",
                  "qwen3.8-max-prime": "qwen",
                  "glm-flash-latest": "glm"},
    "family_members": {
        "claude-opus": ["claude-opus-5.5-max", "claude-opus-5-max"],
        "qwen": ["qwen3.8-max", "qwen3.8-flash-next"],
        "glm": ["glm-4.7", "glm-5"],
    },
}


class TestIdentity(unittest.TestCase):
    def test_the_effort_level_is_not_part_of_the_model_identity(self):
        # The user's rule: opus-5-5-max IS opus-5-5.
        for a, b in [("claude-opus-5-5-max", "claude-opus-5-5"),
                     ("claude-opus-5.5-max", "tri-llm-gateway/claude-opus-5-5"),
                     ("claude-sonnet-5.5-xhigh", "claude-sonnet-5-5"),
                     ("muse-spark-1.3 (xHigh)", "muse-spark-1.3")]:
            self.assertEqual(cr.norm_key(a), cr.norm_key(b), f"{a} vs {b}")

    def test_the_provider_prefix_is_stripped_so_a_harness_id_matches_a_board_name(self):
        self.assertEqual(cr.norm_key("tri-llm-gateway/claude-opus-5-5"),
                         cr.norm_key("claude-opus-5.5-max"))

    def test_our_own_ids_are_never_effort_stripped_because_they_carry_no_effort(self):
        # `qwen3.8-max` is a real model name, not `qwen3.8` at effort `max`. Stripping it
        # would collide with a future bare `qwen3.8`.
        self.assertEqual(cr.norm_model_key("qwen3.8-max"), "qwen38max")
        self.assertEqual(cr.norm_model_key("tri-llm-gateway/qwen3.8-max"), "qwen38max")
        self.assertNotEqual(cr.norm_model_key("qwen3.8-max"), cr.norm_model_key("qwen3.8"))
        # The arena side does strip, which is what groups an effort series.
        self.assertEqual(cr.norm_effort_key("claude-opus-5.5-max"), "claudeopus55")
        self.assertEqual(cr.norm_effort_key("muse-spark-1.3 (xHigh)"), "musespark13")

    def test_an_exact_name_match_is_preferred_over_an_effort_stripped_group(self):
        snap = json.loads(json.dumps(SNAPSHOT))
        snap["match_index"]["qwen38max"] = [
            {"category": "code", "arena_name": "qwen3.8-max", "effort": None,
             "vendor": "Alibaba", "rank": 10, "score": 1672.0, "ci": 12.0, "votes": 3450,
             "observations_in_category": 1, "identity_conflict": False}]
        r = cr.resolve("tri-llm-gateway/qwen3.8-max", None, "code", snap, POLICY)
        self.assertEqual(r["level"], "benchmark")
        self.assertEqual(r["identity_route"], "exact-name")
        self.assertEqual(r["capability"], 1672.0)

    def test_a_harness_id_reaches_its_group_when_the_board_name_carries_an_effort(self):
        r = cr.resolve("tri-llm-gateway/claude-opus-5-5", "max", "code", SNAPSHOT, POLICY)
        self.assertEqual(r["level"], "benchmark")
        self.assertEqual(r["identity_route"], "effort-stripped-group")
        self.assertEqual(r["identity_group"], "claudeopus55")

    def test_effort_is_read_from_a_suffix_and_from_a_parenthetical(self):
        self.assertEqual(cr.effort_of("claude-sonnet-5.5-xhigh"), "xhigh")
        self.assertEqual(cr.effort_of("muse-spark-1.3 (xHigh)"), "xhigh")
        self.assertEqual(cr.effort_of("gpt-6-astra-max"), "max")
        self.assertIsNone(cr.effort_of("qwen3.8-flash-next"))


class TestLevel1AuthoritativeSource(unittest.TestCase):
    def resolve(self, mid, effort, cat="code", policy=None, snap=None):
        return cr.resolve(mid, effort, cat, snap or SNAPSHOT, policy if policy is not None else POLICY)

    def test_an_exact_effort_match_is_measured_and_orders_capability(self):
        r = self.resolve("tri-llm-gateway/claude-opus-5-5", "max")
        self.assertEqual(r["level"], "benchmark")
        self.assertEqual(r["capability"], 1814.0)
        self.assertEqual(r["confidence"], "measured")
        self.assertTrue(r["orders_capability"])
        self.assertIn("benchmark@arena/code@2026-10-07@b6ab43b16f8c", r["capability_evidence"])
        self.assertEqual(r["identity"], "name-normalized-unverified")

    def test_the_level_and_capability_do_not_depend_on_the_requested_effort(self):
        # "se opus è tier3, resta tier3 a qualsiasi effort": one model, one tier, whatever
        # effort the dispatch will use. The requested effort only annotates the result.
        results = [self.resolve("claude-sonnet-5.5", e) for e in ("low", "high", "xhigh", "max", None)]
        self.assertEqual({r["level"] for r in results}, {"benchmark"})
        self.assertEqual({r["capability"] for r in results}, {1773.0})
        self.assertTrue(all(r["tier_invariant"] for r in results))
        by_effort = {r["requested_effort"]: r for r in results}
        self.assertEqual(by_effort["high"]["effort_match"], "exact")
        self.assertEqual(by_effort["high"]["effort_matched"]["score"], 1716.0)
        self.assertEqual(by_effort["xhigh"]["effort_match"], "exact")
        self.assertEqual(by_effort["xhigh"]["effort_matched"]["score"], 1773.0)
        self.assertEqual(by_effort["low"]["effort_match"], "other-effort")
        self.assertIsNone(by_effort["low"]["effort_matched"])
        self.assertEqual(by_effort[None]["effort_match"], "not-requested")
        for r in results:
            self.assertEqual(r["capability_interval"], {"min": 1716.0, "max": 1773.0})
            self.assertEqual(r["capability_bounds"], {"lower": 1705.0, "upper": 1788.0})
            self.assertEqual(sorted(r["efforts_observed"]), ["high", "xhigh"])

    def test_two_rows_at_one_effort_are_an_identity_conflict_and_are_refused(self):
        r = self.resolve("clash-model", "max")
        self.assertEqual(r["level"], "conflict")
        self.assertEqual(r["confidence"], "none")
        self.assertEqual(r["capability_evidence"], "refused")
        self.assertEqual([x["vendor"] for x in r["rows"]], ["A", "B"])
        self.assertIn("a human must resolve", r["reason"])

    def test_a_snapshot_that_is_not_advisory_only_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = dict(SNAPSHOT, authority={"advisory_only": False})
            p = Path(tmp) / "bad.json"
            p.write_text(json.dumps(bad), encoding="utf-8")
            snap, err = cr.load_snapshot(p)
        self.assertIsNone(snap)
        self.assertIn("advisory_only", err)


class TestLevel2PreauthorizedFamily(unittest.TestCase):
    def resolve(self, mid, effort="max", policy=None):
        return cr.resolve(mid, effort, "code", SNAPSHOT, policy if policy is not None else POLICY)

    def test_an_authorized_family_yields_an_interval_and_a_lower_bound_for_eligibility(self):
        r = self.resolve("qwen3.8-max-prime")
        self.assertEqual(r["level"], "family-preauthorized")
        self.assertIsNone(r["capability"])
        self.assertEqual(r["capability_interval"]["min"], 1632.0)
        self.assertEqual(r["capability_interval"]["max"], 1672.0)
        self.assertEqual(r["eligibility_bound"], 1632.0)
        self.assertEqual(r["confidence"], "very-low")
        self.assertFalse(r["orders_capability"])

    def test_family_never_collapses_to_one_sibling_score(self):
        # opus-5.5 (1814) and opus-5 (1692) are 122 ELO apart inside one family, so a
        # scalar inherited from a sibling would be a fabrication.
        r = cr.resolve("claude-opus-5-1", "max", "code", SNAPSHOT,
                       {"family_of": {"claude-opus-5-1": "claude-opus"},
                        "family_members": POLICY["family_members"]})
        self.assertEqual(r["level"], "family-preauthorized")
        self.assertEqual(r["capability_interval"]["min"], 1692.0)
        self.assertEqual(r["capability_interval"]["max"], 1814.0)
        self.assertEqual(r["capability_interval"]["max"] - r["capability_interval"]["min"], 122.0)

    def test_a_family_that_is_not_preauthorized_is_not_a_fallback(self):
        r = self.resolve("muse-wonder", policy={"family_of": {}, "family_members": {}})
        self.assertEqual(r["level"], "heuristic")
        self.assertEqual(r["capability"], "unknown")

    def test_an_authorized_family_with_no_observed_sibling_inherits_nothing(self):
        r = self.resolve("glm-flash-latest", effort="low")
        self.assertEqual(r["level"], "family-authorized-unobserved")
        self.assertIsNone(r["capability"])
        self.assertIn("no sibling appears", r["reason"])


class TestLevel3Heuristic(unittest.TestCase):
    def test_the_heuristic_never_ranks_capability_and_carries_its_own_refutation(self):
        r = cr.resolve("venice-uncensored-1-2", None, "code", SNAPSHOT, POLICY)
        self.assertEqual(r["level"], "heuristic")
        self.assertEqual(r["capability"], "unknown")
        self.assertIsNone(r["capability_evidence"])
        self.assertEqual(r["confidence"], "none")
        self.assertFalse(r["orders_capability"])
        self.assertTrue(r["economic_order_only"])
        prior = r["prior"]
        self.assertEqual(prior["spearman_input_within_code_board"], 0.718)
        self.assertLess(prior["spearman_input_pooled_boards"], 0)
        self.assertIn("may not rank capability", prior["conclusion"])
        self.assertTrue(any("10/50" in c for c in prior["counterexamples"]))

    def test_no_level_synthesizes_a_capability_number_where_none_was_measured(self):
        for mid, eff in [("venice-uncensored-1-2", None), ("glm-flash-latest", "low"),
                         ("muse-wonder", "max")]:
            r = cr.resolve(mid, eff, "code", SNAPSHOT, POLICY)
            self.assertNotIsInstance(r["capability"], float, mid)


class TestSignificanceRule(unittest.TestCase):
    def r(self, mid, eff):
        return cr.resolve(mid, eff, "code", SNAPSHOT, POLICY)

    def test_overlapping_intervals_are_not_an_ordering(self):
        # opus-5.5-max 1814+/-16 = [1798,1830] against astra-max 1788+/-11 = [1777,1799].
        out = cr.compare(self.r("claude-opus-5.5", "max"), self.r("gpt-6-astra", "max"))
        self.assertFalse(out["ordered"])
        self.assertIn("overlap", out["reason"])
        self.assertIn("not transitive", out["reason"])

    def test_disjoint_intervals_are_an_ordering(self):
        out = cr.compare(self.r("claude-opus-5.5", "max"), self.r("claude-fable-5.1", "max"))
        self.assertTrue(out["ordered"])
        self.assertEqual(out["higher"], "claude-opus-5.5")
        self.assertEqual(out["basis"], "non-overlapping 95% CI, aggregated over observed efforts")

    def test_identical_price_does_not_imply_identical_capability(self):
        # gpt-6-astra-max and claude-fable-5.1-max both list 10/50 USD per 1M and differ
        # by 43 ELO and three ranks. This is the counterexample that forbids a
        # price-to-capability heuristic.
        astra, fable = self.r("gpt-6-astra", "max"), self.r("claude-fable-5.1", "max")
        self.assertEqual(astra["effort_matched"]["score"] - fable["capability"], 43.0)
        self.assertEqual(astra["effort_matched"]["rank"] - fable["rank"], -3)
        # Compared at the effort both were measured at, the gap is significant; compared
        # effort-invariantly it is not, because astra's own high/max spread overlaps
        # fable. Both answers are correct and they answer different questions.
        self.assertTrue(cr.compare(astra, fable, effort="max")["ordered"])
        self.assertFalse(cr.compare(astra, fable)["ordered"])

    def test_a_missing_confidence_interval_makes_no_claim(self):
        a = {"model_id": "x", "level": "benchmark", "capability": 1800.0,
             "capability_bounds": None}
        b = {"model_id": "y", "level": "benchmark", "capability": 1700.0,
             "capability_bounds": {"lower": 1695.0, "upper": 1705.0}}
        out = cr.compare(a, b)
        self.assertFalse(out["ordered"])
        self.assertIn("missing", out["reason"])

    def test_passing_an_effort_narrows_the_comparison_to_that_observation(self):
        astra = self.r("gpt-6-astra", "max")
        fable = self.r("claude-fable-5.1", "max")
        # Aggregated over efforts astra spans [1730,1799] (max 1788+/-11, high 1740+/-10)
        # and fable spans [1736,1754], so the pair is not separable and no tier order
        # follows. Narrowed to the effort a dispatch would actually use, max, astra is
        # [1777,1799] against fable [1736,1754] and the ordering becomes significant.
        self.assertEqual(astra["capability_bounds"], {"lower": 1730.0, "upper": 1799.0})
        self.assertFalse(cr.compare(astra, fable)["ordered"])
        out = cr.compare(astra, fable, effort="max")
        self.assertTrue(out["ordered"])
        self.assertEqual(out["higher"], "gpt-6-astra")
        self.assertIn("at effort max", out["basis"])

    def test_an_unobserved_effort_refuses_the_narrowed_comparison(self):
        out = cr.compare(self.r("claude-sonnet-5.5", "low"),
                         self.r("claude-fable-5.1", "max"), effort="low")
        self.assertFalse(out["ordered"])
        self.assertIn("no observation at effort", out["reason"])
        self.assertIn("tier-invariant", out["reason"])

    def test_a_non_benchmark_level_is_never_ordered(self):
        out = cr.compare(self.r("claude-opus-5.5", "max"),
                         self.r("venice-uncensored-1-2", None))
        self.assertFalse(out["ordered"])
        self.assertIn("no comparable measurement", out["reason"])


if __name__ == "__main__":
    unittest.main()
