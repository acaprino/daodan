"""The tier proposal is screened from what a harness actually exposes, never invented.

Pinned on the harness evidence measured on 2026-10-21: OpenCode's config file carries
price, context window and capability flags, while its tool projection carries status and
no window; Pi carries capabilities and no price; Claude Code carries three aliases;
Codex carries one model and one effort; Copilot carried no file at all. A uniform
economic tiering across those five is not constructible, so every field records its
evidence level, an unevaluable gate stays ``unknown``, each host is proposed through the
route it actually supports, and the output stays a proposal until a human confirms it.

Invariants these tests exist to protect:

- no capability is inferred from a model name;
- a missing value never becomes a pass, and a missing rate never becomes zero;
- no credential read from a harness configuration reaches the output;
- an empty or unpriced catalog collapses the scheme instead of inventing three bands.
"""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = REPO_ROOT / "plugins/project-protocol/skills/project-protocol/scripts/tier_router.py"
sys.path.insert(0, str(HELPER.parent))
import tier_router  # noqa: E402

SECRET_A = "SUPER-SECRET-VALUE"
SECRET_B = "ANOTHER-SECRET"

FULL_VARIANTS = {name: {"reasoningEffort": name}
                 for name in ("none", "minimal", "low", "medium", "high", "xhigh", "max")}


def _model(name, cost=None, context=1_048_576, output_limit=0, tool_call=True,
           reasoning=True, variants=None):
    entry = {
        "name": name,
        "tool_call": tool_call,
        "attachment": True,
        "modalities": {"input": ["text", "image"], "output": ["text"]},
        "reasoning": reasoning,
        "variants": FULL_VARIANTS if variants is None else variants,
        "limit": {"context": context, "output": output_limit},
    }
    if cost is not None:
        entry["cost"] = cost
    return entry


def _config(models, provider="gw"):
    return {"$schema": "https://opencode.ai/config.json",
            "provider": {provider: {"name": "Gateway",
                                    "env": {"API_KEY": SECRET_A},
                                    "options": {"baseURL": "https://gw.example/v1",
                                                "apiKey": SECRET_B},
                                    "models": models}}}


# Five priced candidates spanning two orders of magnitude, one model without tool
# calling, one meta-router with no price, one narrow-window model and one model whose
# cache rates are absent. Prices are USD per 1M tokens; the shapes mirror the observed
# OpenCode config and tool projection.
OPENCODE_CONFIG = _config({
    "cheap-lite": _model("cheap-lite", {"input": 0.1, "output": 0.5,
                                        "cache_read": 0.01, "cache_write": 0.2}),
    "tiny-window": _model("tiny-window", {"input": 0.5, "output": 2.0,
                                          "cache_read": 0.05, "cache_write": 0.5},
                          context=16_384),
    "work-mid": _model("work-mid", {"input": 2.0, "output": 10.0,
                                    "cache_read": 0.2, "cache_write": 4.0}),
    "no-cache-rates": _model("no-cache-rates", {"input": 3.0, "output": 15.0}),
    "deep-high": _model("deep-high", {"input": 10.0, "output": 50.0,
                                      "cache_read": 1.0, "cache_write": 12.5},
                        context=200_000),
    "no-tools": _model("no-tools", {"input": 1.0, "output": 5.0}, tool_call=False),
    "meta-auto": _model("meta-auto", context=1_000_000),
})

OPENCODE_CATALOG = {
    "total": 3,
    "next": None,
    "providers": [{
        "id": "gw",
        "name": "Gateway",
        "models": [
            {"id": "gw/cheap-lite", "name": "cheap-lite", "released": 0,
             "variants": sorted(FULL_VARIANTS), "status": "active",
             "cost": [{"input": 0.1, "output": 0.5, "cache": {"read": 0.01, "write": 0.2}}]},
            {"id": "gw/retired", "name": "retired", "released": 0,
             "variants": sorted(FULL_VARIANTS), "status": "deprecated",
             "cost": [{"input": 1.0, "output": 5.0, "cache": {"read": 0.1, "write": 1.0}}]},
            {"id": "gw/meta-auto", "name": "meta-auto", "released": 0,
             "variants": sorted(FULL_VARIANTS), "status": "active", "cost": []},
        ],
    }],
}

PI_MODELS = {
    "providers": {
        "gw": {
            "name": "Gateway",
            "apiKey": SECRET_B,
            "baseUrl": "https://gw.example/v1",
            "api": "openai-completions",
            "compat": {"maxTokensField": "max_completion_tokens"},
            "models": [
                {"id": "cheap-lite", "name": "cheap-lite", "input": ["text"],
                 "reasoning": True,
                 "thinkingLevelMap": {"minimal": None, "low": "low", "medium": "medium",
                                      "high": "high", "xhigh": "max", "max": "max"}},
                {"id": "work-mid", "name": "work-mid", "input": ["text"],
                 "reasoning": True, "thinkingLevelMap": {"low": "low", "high": "high"}},
            ],
        }
    }
}

CODEX_CONFIG = 'model = "gpt-example"\nmodel_reasoning_effort = "medium"\nservice_tier = "auto"\n'


class TierRouterCase(unittest.TestCase):
    """Writes the fixtures into a temp home and drives the helper through main()."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.home / ".config/opencode").mkdir(parents=True)
        (self.home / ".pi/agent").mkdir(parents=True)
        (self.home / ".claude").mkdir(parents=True)
        (self.home / ".codex").mkdir(parents=True)
        self.oc_config = self.home / ".config/opencode/opencode.json"
        self.oc_config.write_text(json.dumps(OPENCODE_CONFIG), encoding="utf-8")
        self.catalog = self.home / "catalog.json"
        self.catalog.write_text(json.dumps(OPENCODE_CATALOG), encoding="utf-8")
        self.pi_models = self.home / ".pi/agent/models.json"
        self.pi_models.write_text(json.dumps(PI_MODELS), encoding="utf-8")
        self.codex_config = self.home / ".codex/config.toml"
        self.codex_config.write_text(CODEX_CONFIG, encoding="utf-8")
        patch = mock.patch.dict(os.environ, {"TIER_ROUTER_HOME": str(self.home)}, clear=False)
        patch.start()
        self.addCleanup(patch.stop)

    def discover(self, *extra):
        """Run the CLI and read back the artifact it wrote."""
        out = self.home / "TIERS_PROPOSAL.json"
        code = tier_router.main(["discover", "--out", str(out), *extra])
        return code, json.loads(out.read_text(encoding="utf-8"))

    def discover_config(self, models, *extra, provider="gw"):
        path = self.home / "custom-config.json"
        path.write_text(json.dumps(_config(models, provider)), encoding="utf-8")
        return self.discover("--host", "opencode", "--opencode-config", str(path), *extra)

    def screened(self, payload, suffix):
        for m in payload["screened"]:
            if m["id"].endswith(suffix):
                return m
        raise AssertionError(f"{suffix} not screened: {[m['id'] for m in payload['screened']]}")

    def gate(self, model, name):
        for g in model["gates"]:
            if g["gate"] == name:
                return g
        raise AssertionError(f"gate {name} missing from {[g['gate'] for g in model['gates']]}")

    def tiers(self, payload):
        return payload["proposal"]["tiers"]


class TestOpenCodeScreening(TierRouterCase):
    def test_price_window_and_capabilities_are_read_from_the_config(self):
        code, payload = self.discover("--host", "opencode")
        self.assertEqual(code, 0)
        mid = self.screened(payload, "work-mid")
        self.assertEqual(mid["cost_usd_per_million_tokens"]["input"], 2.0)
        self.assertEqual(mid["context_window"]["value"], 1_048_576)
        self.assertIs(mid["capabilities"]["tool_call"], True)
        self.assertIn("opencode config", mid["cost_evidence"])
        self.assertIn("opencode config", mid["context_window"]["evidence"])

    def test_cost_per_call_uses_every_token_category_of_the_profile(self):
        _, payload = self.discover("--host", "opencode")
        mid = self.screened(payload, "work-mid")
        # 10k fresh * 2.0 + 30k cache read * 0.2 + 3k output * 10.0, per million.
        self.assertAlmostEqual(mid["cost_per_call_usd"], 0.056, places=6)
        self.assertEqual(payload["workload"]["status"], "assumed")
        self.assertIn("modelled USD per invocation", payload["cost_semantics"]["meaning"])

    def test_a_declared_workload_replaces_the_assumed_profile(self):
        workload = {"fresh_input_tokens": 40_000, "cache_read_tokens": 0,
                    "cache_write_tokens": 0, "output_tokens": 1_000, "status": "declared"}
        path = self.home / "workload.json"
        path.write_text(json.dumps(workload), encoding="utf-8")
        _, payload = self.discover("--host", "opencode", "--workload", str(path))
        self.assertEqual(payload["workload"]["status"], "declared")
        # 40k * 2.0 + 1k * 10.0 per million.
        self.assertAlmostEqual(self.screened(payload, "work-mid")["cost_per_call_usd"],
                               0.09, places=6)

    def test_a_zero_output_limit_is_a_marker_not_a_limit(self):
        _, payload = self.discover("--host", "opencode")
        mid = self.screened(payload, "work-mid")
        self.assertIsNone(mid["output_limit"]["value"])
        self.assertIn("marker", mid["output_limit"]["evidence"])

    def test_a_missing_cache_rate_falls_back_and_is_reported_not_zeroed(self):
        _, payload = self.discover("--host", "opencode")
        bare = self.screened(payload, "no-cache-rates")
        # 10k * 3.0 + 30k * 3.0 (fallback to the input rate) + 3k * 15.0.
        self.assertAlmostEqual(bare["cost_per_call_usd"], 0.165, places=6)
        self.assertTrue(bare["cost_fallbacks"])
        self.assertIn("cache_read", bare["cost_fallbacks"][0])

    def test_a_model_without_tool_calling_is_rejected_by_a_gate(self):
        _, payload = self.discover("--host", "opencode")
        rejected = {r["id"]: r for r in payload["rejected"]}
        self.assertIn("gw/no-tools", rejected)
        self.assertIn("tool_call", rejected["gw/no-tools"]["failed_gates"])
        self.assertNotIn("gw/no-tools", payload["ordered_candidates"])

    def test_a_meta_router_without_a_price_is_unpriced_not_free(self):
        _, payload = self.discover("--host", "opencode")
        meta = self.screened(payload, "meta-auto")
        self.assertIsNone(meta["cost_per_call_usd"])
        self.assertEqual(self.gate(meta, "priced")["result"], "fail")

    def test_the_tool_projection_adds_status_and_exposes_no_window(self):
        _, payload = self.discover("--host", "opencode", "--catalog", str(self.catalog))
        self.assertEqual(self.screened(payload, "cheap-lite")["status"], "active")
        rejected = {r["id"]: r for r in payload["rejected"]}
        self.assertIn("gw/retired", rejected)
        self.assertIn("status_active", rejected["gw/retired"]["failed_gates"])
        self.assertTrue(any("exposes no context window" in n for n in payload["notes"]))

    def test_a_context_size_pricing_tier_is_reported_as_a_limit_of_the_estimate(self):
        catalog = json.loads(json.dumps(OPENCODE_CATALOG))
        catalog["providers"][0]["models"][0]["cost"] = [
            {"tier": {"type": "context", "size": 200_000}, "input": 0.1, "output": 0.5,
             "cache": {"read": 0.01, "write": 0.2}},
            {"tier": {"type": "context", "size": 1_000_000}, "input": 0.4, "output": 2.0,
             "cache": {"read": 0.04, "write": 0.8}}]
        path = self.home / "tiered.json"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        _, payload = self.discover("--host", "opencode", "--catalog", str(path))
        self.assertTrue(any("context-size pricing tier" in n for n in payload["notes"]))

    def test_no_capability_is_inferred_from_a_model_name(self):
        _, payload = self.discover("--host", "opencode")
        for m in payload["screened"]:
            for gate in m["gates"]:
                self.assertNotIn("name", gate["reason"].lower())
        self.assertEqual(self.screened(payload, "deep-high")["cost_usd_per_million_tokens"]["input"], 10.0)

    def test_an_explicit_exclusion_is_labelled_policy(self):
        _, payload = self.discover("--host", "opencode", "--exclude", "deep-high")
        excluded = self.screened(payload, "deep-high")
        self.assertIn("policy", excluded["excluded_by_policy"][0])
        self.assertNotIn("gw/deep-high", payload["ordered_candidates"])

    def test_the_session_provider_scopes_the_screening_unless_widened(self):
        config = _config({
            "cheap-lite": _model("cheap-lite", {"input": 0.1, "output": 0.5,
                                                "cache_read": 0.01, "cache_write": 0.2}),
            "work-mid": _model("work-mid", {"input": 2.0, "output": 10.0,
                                            "cache_read": 0.2, "cache_write": 4.0}),
            "deep-high": _model("deep-high", {"input": 10.0, "output": 50.0,
                                              "cache_read": 1.0, "cache_write": 12.5}),
        }, provider="aaa")
        config["provider"]["gw"] = config["provider"].pop("aaa")
        config["provider"]["zzz"] = {"name": "Other", "models": {
            "other-cheap": _model("other-cheap", {"input": 0.01, "output": 0.05,
                                                  "cache_read": 0.001, "cache_write": 0.01})}}
        path = self.home / "two-providers.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        _, scoped = self.discover("--host", "opencode", "--opencode-config", str(path))
        self.assertNotIn("zzz/other-cheap", scoped["ordered_candidates"])
        self.assertIn("spec §2.1 rule 2",
                      self.screened(scoped, "other-cheap")["excluded_by_policy"][0])
        _, widened = self.discover("--host", "opencode", "--opencode-config", str(path),
                                   "--all-providers")
        self.assertEqual(widened["ordered_candidates"][0], "zzz/other-cheap")

    def test_secrets_from_the_harness_config_never_reach_the_output(self):
        _, payload = self.discover("--host", "opencode", "--catalog", str(self.catalog))
        text = json.dumps(payload)
        for needle in (SECRET_A, SECRET_B, "apiKey", "API_KEY", "baseURL"):
            self.assertNotIn(needle, text)


class TestBanding(TierRouterCase):
    def test_relative_bands_order_by_cost_and_pick_the_cheapest_eligible(self):
        _, payload = self.discover("--host", "opencode")
        tiers = self.tiers(payload)
        self.assertEqual(payload["proposal"]["route"], "economic-bands")
        self.assertEqual(payload["proposal"]["band"]["policy"], "relative")
        self.assertEqual(tiers["tier1"]["chosen"], "gw/cheap-lite")
        # The fixture's dearest model is alone in the top cluster: 0.165 -> 0.28 is a
        # 1.7x step, but 0.056 -> 0.165 already crossed the 3x bound one cluster earlier.
        self.assertEqual(tiers["tier3"]["chosen"], "gw/deep-high")
        self.assertEqual(tiers["tier3"]["cost_per_call_usd"], 0.28)
        self.assertEqual(tiers["tier1"]["selection_rule"],
                         "cheapest eligible in band, tie-break by canonical id")

    def test_a_cost_gap_wider_than_the_ratio_bound_never_shares_a_band(self):
        # The defect this pins: the old rank-based cut made tier3 an open-ended
        # "above the 66th percentile" bucket, so a $0.056 model and a $0.2575 one
        # (4.6x apart) landed in one cluster. The bound is now the ratio to a band's
        # own floor, independent of its position in the list.
        _, payload = self.discover("--host", "opencode")
        band_info = payload["proposal"]["band"]
        self.assertEqual(band_info["rule"],
                         "ratio-bounded clusters mapped onto the three tiers")
        self.assertEqual(band_info["max_band_ratio"], 3.0)
        for tier in tier_router.TIERS:
            span = band_info["tiers"][tier]["span_ratio"]
            if span is not None and tier != "tier2":
                self.assertLessEqual(span, 3.0, f"{tier} spans {span}x")
        tiers = self.tiers(payload)
        self.assertNotIn("gw/no-cache-rates", tiers["tier3"]["candidates"])
        self.assertIn("gw/no-cache-rates", tiers["tier2"]["candidates"])
        self.assertNotIn("gw/deep-high", tiers["tier2"]["candidates"])

    def test_a_surplus_of_clusters_merges_into_tier2_and_says_so(self):
        _, payload = self.discover("--host", "opencode")
        band_info = payload["proposal"]["band"]
        self.assertEqual(band_info["clusters_found"], 4)
        # tier2 keeps the two interior clusters (tiny-window; work-mid + no-cache-rates),
        # three models from two clusters.
        self.assertEqual(band_info["tiers"]["tier2"]["clusters_merged"], 2)
        self.assertTrue(any("more than the three tiers" in n for n in payload["notes"]))
        self.assertTrue(any("tier2 spans" in n for n in payload["notes"]))

    def test_a_ratio_below_one_is_refused_rather_than_making_every_model_its_own_band(self):
        code, payload = self.discover("--host", "opencode", "--max-band-ratio", "0.5")
        self.assertEqual(code, 0)
        self.assertEqual(payload["proposal"]["route"], "none")
        self.assertIsNone(payload["proposal"]["tiers"])
        self.assertEqual(payload["proposal"]["band"]["status"], "refused")
        self.assertIn("below 1", payload["proposal"]["band"]["reason"])

    def test_disabling_the_ratio_bound_restores_one_cluster_per_tier_edge(self):
        _, payload = self.discover("--host", "opencode", "--max-band-ratio", "0")
        self.assertEqual(payload["proposal"]["band"]["clusters_found"], 1)
        tiers = self.tiers(payload)
        self.assertEqual(tiers["tier1"]["chosen"], "gw/cheap-lite")
        self.assertIsNone(tiers["tier2"]["chosen"])
        self.assertIsNone(tiers["tier3"]["chosen"])

    def test_the_window_gate_is_per_tier_and_demotes_only_that_tier(self):
        _, payload = self.discover("--host", "opencode")
        tiers = self.tiers(payload)
        # tiny-window is the cheapest of the middle band but cannot hold a tier2 packet.
        self.assertEqual(tiers["tier2"]["chosen"], "gw/work-mid")
        self.assertIn("gw/tiny-window", [b["id"] for b in tiers["tier2"]["blocked_by_context"]])
        # It was not rejected outright: it stays a screened, ordered candidate.
        self.assertIn("gw/tiny-window", payload["ordered_candidates"])

    def test_a_band_whose_candidates_all_fail_the_window_is_left_empty(self):
        models = {
            "cheap-lite": _model("cheap-lite", {"input": 0.1, "output": 0.5,
                                                "cache_read": 0.01, "cache_write": 0.2}),
            "work-mid": _model("work-mid", {"input": 2.0, "output": 10.0,
                                            "cache_read": 0.2, "cache_write": 4.0}),
            "deep-high": _model("deep-high", {"input": 10.0, "output": 50.0,
                                              "cache_read": 1.0, "cache_write": 12.5},
                                context=40_000),
        }
        _, payload = self.discover_config(models)
        top = self.tiers(payload)["tier3"]
        self.assertIsNone(top["model_param"])
        self.assertIn("window requirement", top["reason"])
        self.assertEqual([b["id"] for b in top["blocked_by_context"]], ["gw/deep-high"])

    def test_equal_costs_are_never_split_across_two_bands(self):
        same = {"input": 1.0, "output": 5.0, "cache_read": 0.1, "cache_write": 1.0}
        models = dict(OPENCODE_CONFIG["provider"]["gw"]["models"])
        for name in ("twin-a", "twin-b"):
            models[name] = _model(name, dict(same))
        _, payload = self.discover_config(models)
        for tier in self.tiers(payload).values():
            twins = [c for c in tier.get("candidates", []) if c.startswith("gw/twin-")]
            self.assertIn(len(twins), (0, 2), f"twins split: {tier.get('candidates')}")

    def test_absolute_bands_require_two_approved_cutpoints(self):
        code, payload = self.discover("--host", "opencode", "--band-policy", "absolute")
        self.assertEqual(code, 0)
        self.assertEqual(payload["proposal"]["band"]["status"], "refused")
        self.assertIsNone(payload["proposal"]["tiers"])
        self.assertEqual(payload["mode"], "thinking-only")

    def test_absolute_bands_apply_the_declared_budget(self):
        _, payload = self.discover("--host", "opencode", "--band-policy", "absolute",
                                   "--band-cut", "0.01", "--band-cut", "0.1")
        self.assertEqual(payload["proposal"]["band"]["status"], "applied")
        self.assertEqual(payload["proposal"]["band"]["cutpoints_usd_per_call"], [0.01, 0.1])

    def test_too_few_priced_models_collapse_instead_of_inventing_bands(self):
        models = {"only-one": _model("only-one", {"input": 1.0, "output": 5.0,
                                                  "cache_read": 0.1, "cache_write": 1.0})}
        _, payload = self.discover_config(models)
        self.assertEqual(payload["proposal"]["band"]["status"], "collapsed")
        self.assertIsNone(payload["proposal"]["tiers"])
        self.assertEqual(payload["mode"], "thinking-only")
        self.assertIn("thinking-only", payload["proposal"]["consequence"])

    def test_a_declared_minimum_context_applies_to_every_tier(self):
        _, payload = self.discover("--host", "opencode", "--min-context", "4096")
        self.assertEqual(payload["context_minimum_tokens"],
                         {t: 4096 for t in tier_router.TIERS})
        self.assertEqual(payload["context_minimum_provenance"], "declared by --min-context")


    def test_the_workload_model_disagrees_with_the_spec_formula_and_the_reason_is_recorded(self):
        # Spec §2.1 rule 4 orders by ``input + 3 * output``, which ignores both cache
        # rates. On this gateway's real catalog the two metrics invert 10 of 231 pairwise
        # orderings, so the deviation is load-bearing and must not be reverted silently.
        F, R, W, O = 10_000, 30_000, 0, 3_000
        rates = {"role-play": {"input": 0.5, "output": 2.0, "cache_read": 0.5, "cache_write": 0.5},
                 "flash-lite": {"input": 0.3, "output": 2.5, "cache_read": 0.03, "cache_write": 0.3}}
        spec_score = {k: v["input"] + 3 * v["output"] for k, v in rates.items()}
        workload = {k: tier_router.cost_per_call(v, {"fresh_input_tokens": F,
                                                     "cache_read_tokens": R,
                                                     "cache_write_tokens": W,
                                                     "output_tokens": O})[0]
                    for k, v in rates.items()}
        self.assertLess(spec_score["role-play"], spec_score["flash-lite"])
        self.assertGreater(workload["role-play"], workload["flash-lite"])
        self.assertIn("superseded", tier_router.__doc__)
        self.assertIn("cache_read", tier_router.__doc__)


def _registry(models, status="built", sha="abc12345def"):
    return {"schema": "daodan/model-fact-registry/v1", "status": status,
            "source": "test-source", "models_sha256": sha,
            "generated_at": "2026-10-22T00:00:00+00:00", "model_count": len(models),
            "models": models}


def _row(rid, ctx=1_000_000, out=64_000, inp=1.0, outp=5.0, cr=0.1, cw=1.0,
         tier="base", floating=False, tiered=False):
    return {"id": rid, "base_id": rid.split(":")[0], "service_tier": tier,
            "floating_alias": floating or rid.startswith("~"),
            "provider": rid.split("/")[0], "context_window": ctx, "output_limit": out,
            "price_is_tiered": tiered,
            "cost_usd_per_million_tokens": {"input": inp, "output": outp,
                                            "cache_read": cr, "cache_write": cw}}


class TestRegistryFallback(TierRouterCase):
    """The harvested registry is a fallback for absent values, never a correction."""

    def write_registry(self, rows, **kw):
        path = self.home / "registry.json"
        path.write_text(json.dumps(_registry(rows, **kw)), encoding="utf-8")
        return str(path)

    def test_no_registry_flag_leaves_the_run_deterministic_and_offline(self):
        _, payload = self.discover("--host", "opencode")
        self.assertFalse(payload["registry"]["used"])
        self.assertIsNone(payload["registry"]["path"])
        self.assertEqual(payload["registry"]["filled"], {})

    def test_a_harness_declared_value_is_never_overwritten_by_a_harvested_one(self):
        reg = self.write_registry([_row("up/cheap-lite", ctx=999, out=111, inp=99.0)])
        _, payload = self.discover("--host", "opencode", "--registry", reg)
        rec = payload["registry"]
        self.assertTrue(rec["used"])
        # cheap-lite declares a window and a price, so neither is filled. Its
        # limit.output is 0, which is a marker and not a limit, so that one is absent and
        # legitimately filled: one model exercises both behaviours.
        self.assertEqual(rec["filled"]["gw/cheap-lite"]["fields"], ["output_limit"])
        self.assertEqual(self.screened(payload, "cheap-lite")["context_window"]["value"],
                         1_048_576)
        self.assertEqual(self.screened(payload, "cheap-lite")["cost_usd_per_million_tokens"],
                         {"input": 0.1, "output": 0.5, "cache_read": 0.01, "cache_write": 0.2})
        d = [x for x in rec["disagreements"] if x["id"] == "gw/cheap-lite"]
        self.assertTrue(all(x["used"] == "harness" for x in d))
        seen = {x["field"]: (x["harness"], x["registry"]) for x in d}
        self.assertEqual(seen["context_window"], (1_048_576, 999))
        self.assertEqual(seen["cost.input"], (0.1, 99.0))

    def test_an_absent_output_limit_is_filled_and_labelled_as_harvested(self):
        # The fixture marks limit.output = 0, which is a marker and not a limit.
        reg = self.write_registry([_row("up/work-mid", out=32_000)])
        _, payload = self.discover("--host", "opencode", "--registry", reg)
        self.assertEqual(payload["registry"]["filled"]["gw/work-mid"]["fields"],
                         ["output_limit"])
        filled = self.screened(payload, "work-mid")["output_limit"]
        self.assertEqual(filled["value"], 32_000)
        self.assertIn("registry:abc12345", filled["evidence"])
        self.assertIn("harvested", filled["evidence"])

    def test_batch_free_and_floating_alias_rows_never_back_a_match(self):
        reg = self.write_registry([
            _row("up/work-mid:batch", tier="batch", out=1),
            _row("up/work-mid:free", tier="free", out=2),
            _row("~up/work-mid-latest", floating=True, out=3),
        ])
        _, payload = self.discover("--host", "opencode", "--registry", reg)
        rec = payload["registry"]
        self.assertEqual(rec["filled"], {})
        self.assertEqual(rec["rows_excluded"], {"batch": 1, "free": 1, "floating_alias": 1})
        self.assertIn("gw/work-mid", rec["unmatched"])

    def test_an_ambiguous_name_match_is_reported_and_not_guessed(self):
        reg = self.write_registry([_row("a/work-mid", out=1), _row("b/work-mid", out=2)])
        _, payload = self.discover("--host", "opencode", "--registry", reg)
        rec = payload["registry"]
        self.assertEqual(rec["filled"], {})
        self.assertEqual([a["id"] for a in rec["ambiguous"]], ["gw/work-mid"])
        self.assertEqual(sorted(rec["ambiguous"][0]["candidates"]),
                         ["a/work-mid", "b/work-mid"])

    def test_a_registry_that_is_not_built_is_ignored_with_a_note(self):
        reg = self.write_registry([_row("up/work-mid")], status="failed")
        _, payload = self.discover("--host", "opencode", "--registry", reg)
        self.assertFalse(payload["registry"]["used"] and payload["registry"]["filled"])
        self.assertIn("status 'failed'", payload["registry"]["error"])
        self.assertTrue(any("not 'built'" in n for n in payload["notes"]))

    def test_identity_is_recorded_as_a_name_claim_never_as_a_proof(self):
        reg = self.write_registry([_row("up/work-mid", out=32_000)])
        _, payload = self.discover("--host", "opencode", "--registry", reg)
        self.assertEqual(payload["registry"]["identity"], "name-normalized-unverified")
        self.assertEqual(payload["registry"]["filled"]["gw/work-mid"]["identity"],
                         "name-normalized-unverified")
        self.assertEqual(payload["registry"]["precedence"],
                         "harness-declared > registry-harvested > unknown")


class TestBindings(TierRouterCase):
    def test_opencode_binds_provider_model_and_a_variant_that_exists(self):
        _, payload = self.discover("--host", "opencode")
        tiers = self.tiers(payload)
        self.assertEqual(tiers["tier1"]["model_param"], "gw/cheap-lite#low")
        self.assertEqual(tiers["tier1"]["effort_applied"], "low")
        self.assertEqual(tiers["tier3"]["model_param"], "gw/deep-high#xhigh")

    def test_a_model_without_the_requested_step_falls_back_to_what_it_exposes(self):
        models = {
            "cheap-lite": _model("cheap-lite", {"input": 0.1, "output": 0.5,
                                                "cache_read": 0.01, "cache_write": 0.2}),
            "work-mid": _model("work-mid", {"input": 2.0, "output": 10.0,
                                            "cache_read": 0.2, "cache_write": 4.0}),
            "only-high": _model("only-high", {"input": 10.0, "output": 50.0,
                                              "cache_read": 1.0, "cache_write": 12.5},
                                variants={"low": {"reasoningEffort": "low"},
                                          "high": {"reasoningEffort": "high"}}),
        }
        _, payload = self.discover_config(models)
        top = self.tiers(payload)["tier3"]
        self.assertEqual(top["chosen"], "gw/only-high")
        self.assertEqual(top["effort_applied"], "high")
        self.assertEqual(top["model_param"], "gw/only-high#high")

    def test_a_model_with_no_variants_omits_the_effort_suffix(self):
        models = {
            "cheap-lite": _model("cheap-lite", {"input": 0.1, "output": 0.5,
                                                "cache_read": 0.01, "cache_write": 0.2}),
            "work-mid": _model("work-mid", {"input": 2.0, "output": 10.0,
                                            "cache_read": 0.2, "cache_write": 4.0}),
            "plain": _model("plain", {"input": 10.0, "output": 50.0,
                                      "cache_read": 1.0, "cache_write": 12.5}, variants={}),
        }
        _, payload = self.discover_config(models)
        top = self.tiers(payload)["tier3"]
        self.assertEqual(top["model_param"], "gw/plain")
        self.assertIsNone(top["effort_applied"])

    def test_the_packet_policy_is_the_same_obligation_on_every_host(self):
        for host in tier_router.HOSTS:
            with self.subTest(host):
                _, payload = self.discover("--host", host)
                for tier in self.tiers(payload).values():
                    self.assertEqual(tier["packet_policy_provenance"],
                                     tier_router.PACKET_POLICY_PROVENANCE)
                self.assertEqual(self.tiers(payload)["tier3"]["packet_policy"],
                                 {"hop_depth": 2, "direct_output": False,
                                  "invariant_table": True})
                self.assertEqual(self.tiers(payload)["tier1"]["packet_policy"],
                                 {"hop_depth": 1, "direct_output": True,
                                  "invariant_table": False})

    def test_claude_uses_the_harness_ladder_and_never_an_effort_suffix(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            _, payload = self.discover("--host", "claude")
        self.assertEqual(payload["proposal"]["route"], "host-alias-ladder")
        tiers = self.tiers(payload)
        self.assertEqual([tiers[t]["model_param"] for t in tier_router.TIERS],
                         ["haiku", "sonnet", "opus"])
        for tier in tiers.values():
            self.assertIsNone(tier["effort_applied"])
            self.assertNotIn("#", tier["model_param"])
        self.assertEqual(payload["mode"], "hybrid")

    def test_an_aliased_claude_model_is_recorded_without_leaking_the_alias_target(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_DEFAULT_HAIKU_MODEL": "custom-small"},
                             clear=False):
            _, payload = self.discover("--host", "claude")
        self.assertEqual(payload["host_facts"]["aliases"]["haiku"], "custom-small")
        self.assertEqual(self.tiers(payload)["tier1"]["model_param"], "haiku")

    def test_a_forced_subagent_model_degrades_the_mode_and_is_recorded(self):
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_SUBAGENT_MODEL": "forced-model"},
                             clear=False):
            _, payload = self.discover("--host", "claude")
        self.assertEqual(payload["proposal"]["route"], "forced-single-model")
        self.assertEqual(payload["mode"], "thinking-only")
        self.assertTrue(any("forces a single model" in n for n in payload["notes"]))
        for tier in self.tiers(payload).values():
            self.assertIsNone(tier["model_param"])

    def test_codex_inherits_unless_the_caller_declares_a_supported_override(self):
        _, payload = self.discover("--host", "codex")
        self.assertEqual(payload["proposal"]["route"], "inherit-packet-policy")
        self.assertIsNone(payload["screened"][0]["binding"]["model_param"])
        self.assertIn("no evidence", payload["screened"][0]["binding"]["reason"])
        self.assertTrue(any("model=gpt-example" in n for n in payload["notes"]))
        self.assertEqual(payload["mode"], "thinking-only")
        _, declared = self.discover("--host", "codex", "--codex-override-supported")
        self.assertEqual(declared["proposal"]["route"], "override-single-model")
        self.assertEqual(self.tiers(declared)["tier2"]["model_param"], "gpt-example")

    def test_copilot_reports_no_evidence_and_binds_nothing(self):
        code, payload = self.discover("--host", "copilot")
        self.assertEqual(code, 0)
        self.assertEqual(payload["screened"], [])
        self.assertEqual(payload["proposal"]["route"], "inherit-packet-policy")
        for tier in self.tiers(payload).values():
            self.assertIsNone(tier["model_param"])
        self.assertTrue(any("no evidence found" in n for n in payload["notes"]))
        self.assertTrue(any("packet_policy alone" in n for n in payload["notes"]))

    def test_pi_exposes_no_price_so_no_economic_band_is_invented(self):
        _, payload = self.discover("--host", "pi")
        self.assertEqual(len(payload["screened"]), 2)
        for m in payload["screened"]:
            self.assertIsNone(m["cost_per_call_usd"])
            # The harness exposes no price at all, which is a property of the harness
            # and not a defect of the model: the gate stays unknown, never fail.
            self.assertEqual(self.gate(m, "priced")["result"], "unknown")
            self.assertIsNone(m["context_window"]["value"])
            self.assertIn("unknown", m["context_window"]["evidence"])
        self.assertEqual([r["id"] for r in payload["rejected"]], [])
        self.assertEqual(payload["proposal"]["route"], "inherit-packet-policy")
        self.assertEqual(payload["mode"], "thinking-only")
        self.assertTrue(any("price exposed for 0" in n for n in payload["notes"]))

    def test_pi_reads_camel_case_cost_context_window_and_cache_format_when_present(self):
        rich_pi = {
            "providers": {
                "gw": {
                    "name": "Gateway",
                    "apiKey": SECRET_B,
                    "compat": {"maxTokensField": "max_tokens", "sendSessionAffinityHeaders": True},
                    "models": [
                        {"id": "auto", "name": "auto", "input": ["text"], "reasoning": True,
                         "thinkingLevelMap": {"low": "low", "high": "high"}},
                        {"id": "cheap", "name": "cheap", "input": ["text"], "reasoning": True,
                         "contextWindow": 200_000, "maxTokens": 32_000,
                         "cost": {"input": 0.1, "output": 0.5, "cacheRead": 0.01, "cacheWrite": 0.2},
                         "thinkingLevelMap": {"low": "low", "medium": "medium", "high": "high"}},
                        {"id": "mid", "name": "mid", "input": ["text"], "reasoning": True,
                         "contextWindow": 500_000, "maxTokens": 64_000,
                         "cost": {"input": 2.0, "output": 10.0, "cacheRead": 0.2, "cacheWrite": 4.0},
                         "compat": {"cacheControlFormat": "anthropic"},
                         "thinkingLevelMap": {"low": "low", "medium": "medium", "high": "high"}},
                        {"id": "high", "name": "high", "input": ["text"], "reasoning": True,
                         "contextWindow": 1_000_000, "maxTokens": 100_000,
                         "cost": {"input": 10.0, "output": 50.0, "cacheRead": 0.25, "cacheWrite": 20.0},
                         "compat": {"cacheControlFormat": "anthropic"},
                         "thinkingLevelMap": {"low": "low", "medium": "medium", "high": "high", "xhigh": "max"}},
                    ],
                }
            }
        }
        path = self.home / "pi-rich.json"
        path.write_text(json.dumps(rich_pi), encoding="utf-8")
        _, payload = self.discover("--host", "pi", "--pi-models", str(path))
        self.assertTrue(payload["host_facts"]["price_exposed"])
        self.assertTrue(payload["host_facts"]["window_exposed"])
        self.assertEqual(payload["proposal"]["route"], "economic-bands")
        mid = self.screened(payload, "mid")
        self.assertEqual(mid["context_window"]["value"], 500_000)
        self.assertEqual(mid["output_limit"]["value"], 64_000)
        self.assertAlmostEqual(mid["cost_per_call_usd"], 0.056, places=6)
        self.assertEqual(mid["pricing_semantics"]["cache_control_format"], "anthropic")
        # Even with economic bands, Pi's subagent model_param format is not evidenced.
        for tier in self.tiers(payload).values():
            self.assertIsNone(tier["model_param"])
        self.assertEqual(self.tiers(payload)["tier1"]["chosen"], "gw/cheap")
        self.assertEqual(self.tiers(payload)["tier3"]["chosen"], "gw/high")
        self.assertEqual(payload["mode"], "thinking-only")

    def test_pi_thinking_levels_drop_null_targets_and_become_the_ladder(self):
        _, payload = self.discover("--host", "pi")
        ladder = self.screened(payload, "cheap-lite")["variants"]
        self.assertEqual(ladder["shape"], "thinkingLevelMap")
        self.assertNotIn("minimal", ladder["available"])
        self.assertIn("xhigh", ladder["available"])

    def test_pi_never_invents_a_subagent_model_format(self):
        _, payload = self.discover("--host", "pi")
        self.assertEqual(payload["host_facts"]["subagent_model_param_format"], "not evidenced")
        for tier in self.tiers(payload).values():
            self.assertIsNone(tier["model_param"])
            # models.json lists what is reachable, not what the session runs.
            self.assertIsNone(tier["chosen"])

    def test_a_host_that_exposes_no_price_leaves_the_priced_gate_unknown(self):
        for host in ("pi", "codex"):
            with self.subTest(host):
                _, payload = self.discover("--host", host)
                for m in payload["screened"]:
                    self.assertEqual(self.gate(m, "priced")["result"], "unknown")

    def test_a_missing_price_in_a_catalog_that_exposes_prices_still_fails(self):
        _, payload = self.discover("--host", "opencode")
        self.assertTrue(payload["host_facts"]["price_exposed"])
        self.assertEqual(self.gate(self.screened(payload, "meta-auto"), "priced")["result"],
                         "fail")

    def test_screening_without_the_tool_projection_warns_that_membership_may_be_partial(self):
        _, payload = self.discover("--host", "opencode")
        self.assertTrue(any("can be a subset" in n for n in payload["notes"]))
        _, with_catalog = self.discover("--host", "opencode", "--catalog", str(self.catalog))
        self.assertFalse(any("can be a subset" in n for n in with_catalog["notes"]))


class TestHostDetection(TierRouterCase):
    def test_auto_detection_uses_the_session_environment_only(self):
        self.assertEqual(tier_router.detect_host({"MOE_BRIDGE_URL": "http://x"}),
                         ("opencode", "MOE_BRIDGE_URL set"))
        self.assertEqual(tier_router.detect_host({"OPENCODE_SESSION": "1"})[0], "opencode")
        self.assertEqual(tier_router.detect_host({"CLAUDECODE": "1"})[0], "claude")
        self.assertEqual(tier_router.detect_host({"CODEX_HOME": "/x"})[0], "codex")
        self.assertEqual(tier_router.detect_host({"PI_AGENT_DIR": "/x"})[0], "pi")

    def test_a_configuration_file_on_disk_does_not_prove_the_active_harness(self):
        out = self.home / "auto.json"
        with mock.patch.dict(os.environ, {"TIER_ROUTER_HOME": str(self.home)}, clear=True):
            code = tier_router.main(["discover", "--host", "auto", "--out", str(out)])
        payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "host-unresolved")
        self.assertIn("does not prove", payload["required"])

    def test_the_tri_tech_session_environment_resolves_to_opencode(self):
        # Measured on 2026-10-22: Tri-Tech Code exports TRITECH_CODE=1,
        # TRITECH_SESSION_ID and OPENCHAMBER_OPENCODE_* instead of OPENCODE_*.
        self.assertEqual(
            tier_router.detect_host({"TRITECH_CODE": "1"}),
            ("opencode", "TRITECH_CODE set (Tri-Tech Code OpenCode consumer)"),
        )
        self.assertEqual(
            tier_router.detect_host({"OPENCHAMBER_OPENCODE_CWD": "C:\\x"})[0],
            "opencode",
        )

    def test_tri_tech_code_resolves_its_bundled_opencode_config_instead_of_user_home(self):
        app_data = self.home / "tritech" / "data"
        oc_dir = app_data / "openchamber"
        cfg_dir = app_data / "config" / "opencode"
        oc_dir.mkdir(parents=True)
        cfg_dir.mkdir(parents=True)
        cfg_file = cfg_dir / "opencode.json"
        cfg_file.write_text(json.dumps({"provider": {}}), encoding="utf-8")
        path, source = tier_router._opencode_default_config(
            {"OPENCHAMBER_DATA_DIR": str(oc_dir)}
        )
        self.assertEqual(path, cfg_file)
        self.assertIn("Tri-Tech Code data root", source)


class TestOutputContract(TierRouterCase):
    def test_the_output_is_deterministic_for_the_same_input(self):
        _, first = self.discover("--host", "opencode")
        _, second = self.discover("--host", "opencode")
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_the_proposal_is_never_applied_automatically(self):
        _, payload = self.discover("--host", "opencode")
        self.assertTrue(payload["confirmation"]["required"])
        self.assertEqual(payload["confirmation"]["writes_to"], "environment.models in work.json")
        self.assertIn("never auto-picked", payload["confirmation"]["rule"])

    def test_a_refusal_is_written_with_an_explicit_status_and_never_an_empty_success(self):
        out = self.home / "RESOLVED_DISPATCH.json"
        code = tier_router.main(["resolve", "--out", str(out)])
        payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "choice-missing")
        self.assertIn("never", payload["reason"])
        # A preparation refusal leaves no prompt file behind: a .md path must never hold
        # something that is not a prompt.
        prompt = self.home / "CHOICE_PROMPT.md"
        with contextlib.redirect_stdout(io.StringIO()):
            code = tier_router.main(["prepare-choice", "--out", str(prompt)])
        self.assertEqual(code, 2)
        self.assertFalse(prompt.exists())
        refusal = json.loads(
            (self.home / "CHOICE_PROMPT.request.json").read_text(encoding="utf-8"))
        self.assertEqual(refusal["status"], "evidence-missing")
        self.assertIs(refusal["prompt_written"], False)

    def test_the_cli_writes_the_artifact_and_exits_zero(self):
        out = self.home / "nested" / "TIERS_PROPOSAL.json"
        self.assertEqual(tier_router.main(["discover", "--host", "opencode",
                                           "--out", str(out)]), 0)
        written = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(written["schema"], tier_router.SCHEMA)
        self.assertEqual(written["host"], "opencode")

    def test_the_helper_runs_under_a_plain_interpreter_with_no_third_party_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "TIERS_PROPOSAL.json"
            proc = subprocess.run(
                [sys.executable, "-B", str(HELPER), "discover", "--host", "opencode",
                 "--opencode-config", str(self.oc_config), "--out", str(out)],
                capture_output=True, text=True,
                env={**dict(os.environ), "TIER_ROUTER_HOME": str(self.home)},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(out.exists())


ROSTER = {
    "schema": "daodan/review-roster/v1", "shape": "branch", "kind": "changeset",
    "tier": "medium", "reasons": ["3 modules touched"],
    "roster": ["senior-review:code-auditor", "testing:test-suite-auditor"],
    "support": ["senior-review:premise-auditor"],
    "verification": "all-above-floor", "blind_derivation": True, "critic": False,
    "signals": {}, "gaps": [], "advice": [],
}

CHOICE_DIFF = """--- a/api/invoices.py
+++ b/api/invoices.py
@@ -30,6 +30,8 @@ def get_invoice(invoice_id):
+@router.get('/invoices/{invoice_id}')
+    if discount >= 0:
--- a/tests/test_invoices.py
+++ b/tests/test_invoices.py
@@ -18,0 +19,2 @@
+def test_get_invoice():
"""

REVIEWER_CATALOG = [
    {"role": "senior-review:code-auditor", "trigger_when": "every changeset",
     "do_not_trigger_when": None, "digest": "aaa1"},
    {"role": "senior-review:security-auditor", "trigger_when": "routes, authz, data by id",
     "do_not_trigger_when": "no user boundary touched", "digest": "bbb2"},
    {"role": "senior-review:premise-auditor", "trigger_when": "boundaries and defaults",
     "digest": "ccc3"},
    {"role": "testing:test-suite-auditor", "trigger_when": "tests changed", "digest": "ddd4"},
]

REVIEWER_EVIDENCE = {
    "schema": "daodan/choice-evidence/v1", "snodo": "reviewer", "mode": "lite",
    "candidate_digest": "cand-123",
    "intent_and_docs": "ADR-7: invoice routes are owner-scoped",
    "code_graph_facts": {"symbols_at": ["api/invoices.py:get_invoice"],
                         "callers": ["api/router.py"]},
    "tool_results": "pytest: 12 passed; ruff: clean",
    "diff": CHOICE_DIFF,
    "interface_hash_changed": True, "external_callers": True,
    "catalog": REVIEWER_CATALOG,
}

TASK_EVIDENCE = {
    "schema": "daodan/choice-evidence/v1", "snodo": "task", "plan_digest": "plan-abc",
    "objective": "Route every dispatch through the frozen decision contract",
    "workflow_dag_facts": "wave 1: T1; wave 2: T2, T3",
    "code_graph_facts": "callers(tier_router.main) = 3; module is public",
    "nodes": [
        {"id": "T1", "op": "SPEC_ADR", "text": "Write the ADR for the routing contract",
         "facts": {"downstream": 3, "fanin": 2}},
        {"id": "T2", "op": "CODE_WRITE", "text": "Implement prepare-choice and resolve",
         "facts": {"downstream": 1, "fanin": 1, "callers": 6, "public": True,
                   "write_set": ["scripts/tier_router.py"]}},
        {"id": "T3", "op": "MAP_SLICE", "text": "Refresh the slice", "facts": {"fanin": 1}},
    ],
}

RETRY_EVIDENCE = {
    "schema": "daodan/choice-evidence/v1", "snodo": "retry", "plan_digest": "plan-abc",
    "task_summary": "T2, write_set: scripts/tier_router.py",
    "attempt_diff": "--- a/scripts/tier_router.py\n+++ b/scripts/tier_router.py\n@@ -1 +1 @@\n-old\n+new",
    "error_output": "AssertionError: 0.056 != 0.028 at tests/test_tier_router.py:192",
    "node": {"id": "T2", "op": "CODE_WRITE", "text": "Implement prepare-choice and resolve",
             "facts": {"downstream": 1, "fanin": 1, "callers": 6, "public": True,
                       "write_set": ["scripts/tier_router.py"]}},
    "escalation": {"current_tier": "tier2", "attempt": 1},
}

CONFIRMED_MODELS = {
    "host": "opencode", "mode": "hybrid", "model_override_supported": True,
    "effort_override_supported": True, "session_tier": "tier2",
    "tiers": {
        "tier1": {"model_param": "gw/cheap-lite#low", "hop_depth": 1,
                  "direct_output": True, "invariant_table": False},
        "tier2": {"model_param": "gw/work-mid#medium",
                  "model_param_high": "gw/work-mid#high"},
        "tier3": {"model_param": "gw/deep-high#xhigh"},
    },
}


class ChoiceCase(TierRouterCase):
    """Drives prepare-choice and resolve over the frozen contract of spec §3.6."""

    def prepare(self, evidence, roster=ROSTER, mode=None, snodo=None,
                name="CHOICE_PROMPT.md"):
        evidence_path = self.home / "EVIDENCE.json"
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        argv = ["prepare-choice", "--evidence", str(evidence_path),
                "--out", str(self.home / name)]
        if roster is not None:
            roster_path = self.home / "REVIEWERS.json"
            roster_path.write_text(json.dumps(roster), encoding="utf-8")
            argv += ["--reviewers", str(roster_path)]
        if mode:
            argv += ["--mode", mode]
        if snodo:
            argv += ["--snodo", snodo]
        with contextlib.redirect_stdout(io.StringIO()):
            code = tier_router.main(argv)
        out = self.home / name
        request_path = out.with_name(out.stem + ".request.json")
        envelope = (json.loads(request_path.read_text(encoding="utf-8"))
                    if request_path.exists() else None)
        return code, (out.read_text(encoding="utf-8") if out.exists() else None), envelope

    def answer(self, envelope, decisions, status="ok", digest="unset", raw=None,
               **extra):
        payload = {
            "schema": envelope["answer_schema"],
            "implementation": {"name": tier_router.BACKEND,
                               "version": tier_router.BACKEND_VERSION},
            "input_digest": envelope["request_sha256"] if digest == "unset" else digest,
            "status": status, "gaps": [], "decision_id": "D-1", "decisions": decisions,
        }
        if raw is not None:
            payload["raw"] = raw
        payload.update(extra)
        return payload

    def resolve(self, envelope, answer, *extra, name="RESOLVED_DISPATCH.json"):
        request_path = self.home / "CHOICE_REQUEST.json"
        request_path.write_text(json.dumps(envelope), encoding="utf-8")
        choice_path = self.home / "CHOICE.json"
        choice_path.write_text(json.dumps(answer), encoding="utf-8")
        out = self.home / name
        with contextlib.redirect_stdout(io.StringIO()):
            code = tier_router.main(["resolve", "--request", str(request_path),
                                     "--choice", str(choice_path), "--out", str(out),
                                     *extra])
        return code, json.loads(out.read_text(encoding="utf-8"))

    def confirmed_project(self, run_id="RUN-1", models=CONFIRMED_MODELS):
        run_dir = self.home / "project" / ".daodan" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "work.json").write_text(json.dumps({"environment": {"models": models}}),
                                           encoding="utf-8")
        return str(self.home / "project"), run_id


class TestPrepareChoice(ChoiceCase):
    def test_the_reviewer_prompt_is_the_frozen_text_with_only_the_evidence_substituted(self):
        code, prompt, envelope = self.prepare(REVIEWER_EVIDENCE, mode="lite")
        self.assertEqual(code, 0)
        self.assertIn("You are Daodan's reviewer Choicer. Reply ONLY with a valid JSON "
                      "object.", prompt)
        self.assertIn('4. Requested mode: "lite".', prompt)
        self.assertIn("senior-review:security-auditor", prompt)
        self.assertIn("ADR-7: invoice routes are owner-scoped", prompt)
        self.assertIn("pytest: 12 passed; ruff: clean", prompt)
        self.assertIn("[H1] candidate api/invoices.py", prompt)
        self.assertNotRegex(prompt, r"\$[A-Za-z_]")
        self.assertEqual(envelope["snodo"], "reviewer")
        self.assertEqual(envelope["answer_schema"], "daodan/selection/v1")
        self.assertEqual(envelope["implementation"]["name"], "llm-tier1")

    def test_the_frozen_rules_are_never_reworded_by_the_rendering(self):
        _, prompt, _ = self.prepare(REVIEWER_EVIDENCE, mode="full")
        for line in tier_router.REVIEWER_CHOICER_PROMPT.splitlines():
            if "$" not in line and line.strip():
                self.assertIn(line, prompt, f"frozen line altered: {line[:60]}")
        self.assertIn('4. Requested mode: "full".', prompt)

    def test_the_request_digest_is_recomputed_identically_for_the_same_evidence(self):
        _, _, first = self.prepare(REVIEWER_EVIDENCE, name="A.md")
        _, _, second = self.prepare(REVIEWER_EVIDENCE, name="B.md")
        self.assertEqual(first["request_sha256"], second["request_sha256"])
        self.assertEqual(first["prompt_sha256"], second["prompt_sha256"])
        self.assertEqual(first["request_sha256"],
                         tier_router.canonical_digest(first["request"]))
        self.assertEqual(first["evidence"]["sha256"],
                         tier_router.canonical_digest(REVIEWER_EVIDENCE))

    def test_a_diff_is_enumerated_into_the_hunks_a_citation_must_point_at(self):
        _, _, envelope = self.prepare(REVIEWER_EVIDENCE)
        hunks = envelope["request"]["hunks"]
        self.assertEqual([h["id"] for h in hunks], ["H1", "H2"])
        self.assertEqual(hunks[0]["path"], "api/invoices.py")
        self.assertEqual(hunks[0]["side"], "candidate")
        self.assertIn("@router.get", hunks[0]["text"])
        self.assertEqual(hunks[1]["path"], "tests/test_invoices.py")
        self.assertEqual(envelope["options"]["roles"],
                         sorted(c["role"] for c in REVIEWER_CATALOG))
        self.assertEqual(envelope["options"]["roster_floor"], sorted(ROSTER["roster"]))

    def test_the_reviewer_snodo_refuses_without_the_roster_floor(self):
        code, prompt, envelope = self.prepare(REVIEWER_EVIDENCE, roster=None, snodo="reviewer")
        self.assertEqual(code, 2)
        self.assertIsNone(prompt)
        self.assertEqual(envelope["status"], "reviewers-missing")

    def test_a_roster_of_another_schema_is_refused_rather_than_trusted(self):
        code, _, envelope = self.prepare(REVIEWER_EVIDENCE,
                                         roster=dict(ROSTER, schema="daodan/review-roster/v2"))
        self.assertEqual(code, 2)
        self.assertEqual(envelope["status"], "reviewers-schema-unknown")

    def test_an_unknown_evidence_version_is_refused(self):
        code, _, envelope = self.prepare(
            dict(REVIEWER_EVIDENCE, schema="daodan/choice-evidence/v2"))
        self.assertEqual(code, 2)
        self.assertEqual(envelope["status"], "evidence-schema-unknown")

    def test_the_task_prompt_separates_the_dag_facts_from_the_code_graph_facts(self):
        code, prompt, envelope = self.prepare(TASK_EVIDENCE, roster=None)
        self.assertEqual(code, 0)
        self.assertIn("You are Daodan's task-tier Choicer.", prompt)
        self.assertIn("- T2 op=CODE_WRITE", prompt)
        self.assertIn('"downstream": 1', prompt)
        self.assertIn("callers(tier_router.main) = 3", prompt)
        self.assertEqual(envelope["answer_schema"], "daodan/routing/v1")
        self.assertEqual([n["id"] for n in envelope["request"]["nodes"]], ["T1", "T2", "T3"])
        self.assertEqual(envelope["request"]["plan_digest"], "plan-abc")
        self.assertEqual(envelope["options"]["tiers"], ["tier1", "tier2", "tier3"])

    def test_the_retry_prompt_carries_the_deterministic_failure_output(self):
        code, prompt, envelope = self.prepare(RETRY_EVIDENCE, roster=None)
        self.assertEqual(code, 0)
        self.assertIn("You are Daodan's retry diagnostic Choicer.", prompt)
        self.assertIn("AssertionError: 0.056 != 0.028", prompt)
        self.assertEqual(envelope["request"]["escalation"]["current_tier"], "tier2")
        self.assertEqual(envelope["options"]["actions"],
                         ["retry_same_tier", "escalate_tier", "needs_replan"])

    def test_evidence_text_that_looks_like_a_placeholder_is_data_not_a_template(self):
        evidence = dict(REVIEWER_EVIDENCE,
                        tool_results="the diff adds a line reading $mode and $objective")
        code, prompt, _ = self.prepare(evidence)
        self.assertEqual(code, 0)
        self.assertIn("the diff adds a line reading $mode and $objective", prompt)
        self.assertIn('4. Requested mode: "lite".', prompt)

    def test_a_prompt_that_cannot_be_fully_rendered_is_refused_not_partially_emitted(self):
        prompt, err = tier_router._render_prompt("task", {"objective": "one field only"})
        self.assertIsNone(prompt)
        self.assertIn("workflow_dag_facts", err)

    def test_the_answer_contract_tells_the_backend_what_binds_it(self):
        _, _, envelope = self.prepare(REVIEWER_EVIDENCE)
        contract = envelope["answer_contract"]
        self.assertEqual(contract["input_digest"], envelope["request_sha256"])
        self.assertEqual(contract["status_options"], ["ok", "abstain", "unavailable"])
        self.assertTrue(any("input_digest" in rule for rule in contract["rules"]))
        self.assertTrue(any("never reassigned" in rule for rule in contract["rules"]))


class TestResolveReviewer(ChoiceCase):
    def setUp(self):
        super().setUp()
        _, _, self.envelope = self.prepare(REVIEWER_EVIDENCE)
        self.floor = set(ROSTER["roster"])

    def roles(self, payload):
        return set(payload["reviewers"]["applied"])

    def test_the_roster_floor_is_applied_whatever_the_answer_says(self):
        code, payload = self.resolve(self.envelope, self.answer(self.envelope, []))
        self.assertEqual(code, 0)
        self.assertTrue(self.floor <= self.roles(payload))
        for role in self.floor:
            self.assertEqual(payload["reviewers"]["applied"][role]["source"], "roster-floor")

    def test_a_cited_selection_is_applied_with_its_evidence_locator(self):
        answer = self.answer(self.envelope, [
            {"role": "senior-review:security-auditor", "selected": True,
             "probability": 0.9, "citation": "H1"}])
        _, payload = self.resolve(self.envelope, answer)
        entry = payload["reviewers"]["applied"]["senior-review:security-auditor"]
        self.assertEqual(entry["source"], "choicer")
        self.assertEqual(entry["citation"], "H1")
        self.assertEqual(entry["evidence"]["path"], "api/invoices.py")
        self.assertEqual(entry["probability"], 0.9)
        self.assertNotIn("text", entry["evidence"])

    def test_an_uncited_selection_is_ignored_and_recorded_never_reassigned(self):
        answer = self.answer(self.envelope, [
            {"role": "senior-review:security-auditor", "selected": True,
             "probability": None, "citation": None}])
        _, payload = self.resolve(self.envelope, answer)
        self.assertNotIn("senior-review:security-auditor", self.roles(payload))
        self.assertEqual(self.roles(payload), self.floor)
        ignored = payload["reviewers"]["ignored_uncited"]
        self.assertEqual([i["role"] for i in ignored], ["senior-review:security-auditor"])
        self.assertIn("never reassigned", ignored[0]["reason"])

    def test_a_citation_outside_the_request_makes_the_whole_answer_non_conformant(self):
        answer = self.answer(self.envelope, [
            {"role": "senior-review:security-auditor", "selected": True,
             "probability": None, "citation": "H9"},
            {"role": "testing:test-suite-auditor", "selected": True,
             "probability": None, "citation": "H2"}])
        _, payload = self.resolve(self.envelope, answer)
        self.assertEqual(payload["answer"]["classification"], "non-conformant")
        self.assertTrue(any("citation outside the request" in r
                            for r in payload["answer"]["reasons"]))
        # The conformant half of a non-conformant answer is not salvaged.
        self.assertEqual(self.roles(payload), self.floor)

    def test_an_answer_bound_to_another_request_is_not_a_decision(self):
        answer = self.answer(self.envelope, [], digest="0" * 64, status="ok")
        _, payload = self.resolve(self.envelope, answer)
        self.assertEqual(payload["answer"]["classification"], "non-conformant")
        self.assertTrue(any("bound to another request" in r
                            for r in payload["answer"]["reasons"]))

    def test_abstention_applies_the_floor_and_invents_no_reviewer(self):
        answer = self.answer(self.envelope, [], status="abstain")
        code, payload = self.resolve(self.envelope, answer)
        self.assertEqual(code, 0)
        self.assertEqual(payload["answer"]["classification"], "abstain")
        self.assertEqual(self.roles(payload), self.floor)

    def test_a_status_that_is_not_ok_carrying_decisions_is_non_conformant(self):
        answer = self.answer(self.envelope, [
            {"role": "senior-review:security-auditor", "selected": True,
             "probability": None, "citation": "H1"}], status="abstain")
        _, payload = self.resolve(self.envelope, answer)
        self.assertEqual(payload["answer"]["classification"], "non-conformant")
        self.assertEqual(self.roles(payload), self.floor)

    def test_a_floor_role_is_never_removed_by_a_choice(self):
        answer = self.answer(self.envelope, [
            {"role": "senior-review:code-auditor", "selected": False,
             "probability": 0.0, "citation": None}])
        _, payload = self.resolve(self.envelope, answer)
        self.assertIn("senior-review:code-auditor", self.roles(payload))
        self.assertEqual([k["role"] for k in payload["reviewers"]["floor_kept"]],
                         ["senior-review:code-auditor"])

    def test_no_reviewer_runs_below_tier2_and_the_critical_lenses_carry_effort_high(self):
        answer = self.answer(self.envelope, [
            {"role": "senior-review:security-auditor", "selected": True,
             "probability": None, "citation": "H1", "tier": "tier1", "effort": "low"}])
        _, payload = self.resolve(self.envelope, answer)
        entry = payload["reviewers"]["applied"]["senior-review:security-auditor"]
        self.assertEqual(entry["tier"], "tier2")
        self.assertEqual(entry["floor"], "tier2")
        self.assertEqual(entry["proposed_tier"], "tier1")
        self.assertEqual(entry["effort_requested"], "high")
        self.assertIs(entry["effort_forced_high"], True)
        self.assertEqual(entry["packet_policy"], tier_router.TIER_PACKET_POLICY["tier2"])
        # A changed public interface with external callers raises every lens.
        self.assertIs(payload["reviewers"]["interface_risk_effort_high"], True)

    def test_the_llm_answer_shape_is_adapted_without_inventing_a_citation(self):
        raw = {"mode": "lite",
               "selected": [
                   {"trigger_line": "[H1] candidate api/invoices.py:34 @router.get",
                    "reason": "Exposed invoice route needs an ownership check",
                    "role": "senior-review:security-auditor", "tier": "tier2",
                    "effort": "high"},
                   {"trigger_line": "somewhere in the diff", "reason": "no enumerated id",
                    "role": "senior-review:premise-auditor", "tier": "tier2",
                    "effort": "medium"}],
               "recommend_full_review": True, "recommend_full_reason": "four risk axes"}
        _, payload = self.resolve(self.envelope, self.answer(self.envelope, None, raw=raw))
        self.assertIs(payload["answer"]["adapted_from_backend_shape"], True)
        applied = payload["reviewers"]["applied"]
        self.assertEqual(applied["senior-review:security-auditor"]["citation"], "H1")
        self.assertIn("@router.get", applied["senior-review:security-auditor"]["trigger_line"])
        self.assertEqual([i["role"] for i in payload["reviewers"]["ignored_uncited"]],
                         ["senior-review:premise-auditor"])

    def test_a_full_review_recommendation_is_recorded_and_never_applied(self):
        raw = {"mode": "lite", "selected": [], "recommend_full_review": True,
               "recommend_full_reason": "four distinct risk axes have trigger lines"}
        _, payload = self.resolve(self.envelope, self.answer(self.envelope, None, raw=raw))
        recommendation = payload["reviewers"]["recommend_full_review"]
        self.assertIs(recommendation["value"], True)
        self.assertIs(recommendation["applied"], False)
        self.assertEqual(recommendation["reason"],
                         "four distinct risk axes have trigger lines")

    def test_a_ceiling_below_the_reviewer_floor_blocks_before_anything_is_applied(self):
        code, payload = self.resolve(self.envelope, self.answer(self.envelope, []),
                                     "--ceiling", "tier1")
        self.assertEqual(code, 2)
        self.assertEqual(payload["outcome"], "POLICY_BLOCKED")
        self.assertIn("never runs below tier2", payload["reason"])
        self.assertEqual(payload["reviewers"]["applied"], {})
        self.assertEqual(payload["reviewers"]["floor"], sorted(ROSTER["roster"]))

    def test_the_audit_record_carries_implementation_input_options_and_both_choices(self):
        decisions = [{"role": "senior-review:security-auditor", "selected": True,
                      "probability": None, "citation": "H1"}]
        _, payload = self.resolve(self.envelope, self.answer(self.envelope, decisions))
        audit = payload["audit"][0]
        self.assertEqual(audit["decision_id"], "D-1")
        self.assertEqual(audit["snodo"], "reviewer")
        self.assertEqual(audit["implementation"]["name"], "llm-tier1")
        self.assertEqual(audit["policy_version"], tier_router.POLICY_VERSION)
        self.assertEqual(audit["state_digest"], self.envelope["request_sha256"])
        self.assertEqual(audit["candidate_digest"], "cand-123")
        self.assertEqual(audit["option_set"]["roles"],
                         self.envelope["request"]["catalog"]["roles"])
        self.assertEqual(audit["option_set"]["citations"], ["H1", "H2"])
        self.assertEqual(audit["proposed_choice"], decisions)
        self.assertIn("senior-review:security-auditor", audit["applied_choice"])
        self.assertEqual(audit["evidence_refs"], ["H1"])
        self.assertEqual(audit["usage"], "unknown")
        self.assertIsNone(audit["downstream_outcome"])
        self.assertIn("host", audit["runtime_identity"])

    def test_a_confirmed_binding_renders_the_host_triple(self):
        project, run_id = self.confirmed_project()
        answer = self.answer(self.envelope, [
            {"role": "senior-review:security-auditor", "selected": True,
             "probability": None, "citation": "H1", "tier": "tier2", "effort": "high"}])
        _, payload = self.resolve(self.envelope, answer,
                                  "--project", project, "--run-id", run_id)
        binding = payload["host_binding"]
        self.assertEqual(binding["source"], "work.json environment.models")
        self.assertIs(binding["confirmed"], True)
        entry = payload["reviewers"]["applied"]["senior-review:security-auditor"]
        self.assertEqual(entry["model_param"], "gw/work-mid#high")
        self.assertEqual(entry["effort_applied"], "high")
        self.assertIs(entry["inherit"], False)
        self.assertEqual(entry["cost"], tier_router.TIER_COST["tier2"])

    def test_an_unconfirmed_proposal_never_binds_a_model(self):
        proposal = self.home / "TIERS_PROPOSAL.json"
        tier_router.main(["discover", "--host", "opencode", "--out", str(proposal)])
        answer = self.answer(self.envelope, [
            {"role": "senior-review:security-auditor", "selected": True,
             "probability": None, "citation": "H1"}])
        _, payload = self.resolve(self.envelope, answer, "--tiers", str(proposal))
        binding = payload["host_binding"]
        self.assertEqual(binding["source"], "TIERS_PROPOSAL.json (unconfirmed)")
        self.assertIs(binding["confirmed"], False)
        entry = payload["reviewers"]["applied"]["senior-review:security-auditor"]
        self.assertIsNone(entry["model_param"])
        self.assertIsNotNone(entry["proposed_model_param"])
        self.assertIs(entry["inherit"], True)
        # An inherited model is charged at the dearest tier when the session tier is unknown.
        self.assertEqual(entry["cost"], tier_router.TIER_COST["tier3"])
        self.assertTrue(any("unconfirmed" in n for n in payload["notes"]))


class TestResolveTask(ChoiceCase):
    def setUp(self):
        super().setUp()
        _, _, self.envelope = self.prepare(TASK_EVIDENCE, roster=None)
        self.project, self.run_id = self.confirmed_project()

    def resolve_confirmed(self, decisions, *extra, **kw):
        return self.resolve(self.envelope, self.answer(self.envelope, decisions, **kw),
                            "--project", self.project, "--run-id", self.run_id, *extra)

    def test_the_operator_floor_survives_a_cheaper_choice(self):
        _, payload = self.resolve_confirmed([
            {"node": "T1", "tier": "tier1", "effort": "low"}])
        node = payload["nodes"]["T1"]
        self.assertEqual(node["floor"], "tier2")
        self.assertEqual(node["proposed"], "tier1")
        self.assertEqual(node["tier"], "tier2")
        # Only a confirmed binding is rendered: the requested "low" is recorded, the
        # confirmed "#medium" is applied, and the gap between them is not hidden.
        self.assertEqual(node["model_param"], "gw/work-mid#medium")
        self.assertEqual(node["effort_requested"], "low")
        self.assertEqual(node["effort_applied"], "medium")
        self.assertIs(node["effort_gap"], True)

    def test_abstention_applies_the_declared_default_and_says_so(self):
        _, payload = self.resolve_confirmed([], status="abstain")
        self.assertEqual(payload["answer"]["classification"], "abstain")
        node = payload["nodes"]["T2"]
        self.assertEqual(node["tier"], "tier2")
        self.assertIn("never a guessed tier", node["default_applied"])

    def test_a_deterministic_operator_takes_no_model_and_no_tier(self):
        _, payload = self.resolve_confirmed([])
        node = payload["nodes"]["T3"]
        self.assertIsNone(node["tier"])
        self.assertIsNone(node["model_param"])
        self.assertIsNone(node["packet_policy"])
        self.assertIn("deterministic", node["reason"])

    def test_every_node_entry_carries_the_host_triple_and_its_cost(self):
        # A consumer reads any node entry the same way, routed or deterministic.
        _, payload = self.resolve_confirmed([{"node": "T2", "tier": "tier3"}])
        required = {"node", "op", "tier", "model_param", "effort_requested",
                    "effort_applied", "packet_policy", "cost", "charged_at", "floor",
                    "judge", "proposed", "inherit"}
        for nid, entry in payload["nodes"].items():
            self.assertTrue(required <= set(entry),
                            f"{nid} misses {sorted(required - set(entry))}")

    def test_a_choice_above_the_authorized_ceiling_is_clamped_not_refused(self):
        _, payload = self.resolve_confirmed([{"node": "T2", "tier": "tier3",
                                              "effort": "high"}], "--ceiling", "tier2")
        self.assertEqual(payload["nodes"]["T2"]["tier"], "tier2")
        self.assertEqual(payload["ceiling"], "tier2")

    def test_a_ceiling_below_a_floor_blocks_before_spending(self):
        code, payload = self.resolve_confirmed([], "--ceiling", "tier1")
        self.assertEqual(code, 2)
        self.assertEqual(payload["outcome"], "POLICY_BLOCKED")
        self.assertIn("needs tier2", payload["reason"])

    def test_the_budget_descends_toward_the_floor_and_never_below_it(self):
        _, payload = self.resolve_confirmed([{"node": "T2", "tier": "tier2",
                                              "effort": "high"}], "--budget", "9")
        self.assertEqual(payload["downgraded"], ["T2"])
        self.assertEqual(payload["nodes"]["T2"]["tier"], "tier1")
        self.assertIn("budget", payload["nodes"]["T2"]["downgrade_reason"])
        self.assertLessEqual(payload["expected_cost_units"], 9)
        # SPEC_ADR sits on its floor and is never the node that gives way.
        self.assertEqual(payload["nodes"]["T1"]["tier"], "tier2")

    def test_an_uncovered_floor_reports_budget_exhausted_before_starting(self):
        code, payload = self.resolve_confirmed([], "--budget", "5")
        self.assertEqual(code, 2)
        self.assertEqual(payload["outcome"], "BUDGET_EXHAUSTED")
        self.assertIn("floors need", payload["reason"])

    def test_the_expected_cost_counts_dispatch_verification_and_the_router_call(self):
        _, payload = self.resolve_confirmed([])
        expected = (sum(e["cost"] for e in payload["nodes"].values())
                    + len(payload["nodes"]) * tier_router.VERIFICATION_COST_PER_NODE
                    + tier_router.ROUTER_CALL_COST)
        self.assertEqual(payload["expected_cost_units"], expected)
        self.assertEqual(payload["cost_policy"]["tier_cost"],
                         {"tier1": 1, "tier2": 3, "tier3": 8})

    def test_a_node_outside_the_request_makes_the_answer_non_conformant(self):
        _, payload = self.resolve_confirmed([{"node": "T9", "tier": "tier3"}])
        self.assertEqual(payload["answer"]["classification"], "non-conformant")
        self.assertTrue(any("node outside the request" in r
                            for r in payload["answer"]["reasons"]))
        self.assertEqual(payload["nodes"]["T1"]["tier"], "tier2")

    def test_a_judge_node_is_routed_once_and_marked_as_never_escalatable(self):
        evidence = dict(TASK_EVIDENCE, nodes=[
            {"id": "J1", "op": "VERIFY_FINDING", "text": "Judge the finding",
             "role": "senior-review:premise-auditor", "facts": {"fanin": 1}}])
        _, _, envelope = self.prepare(evidence, roster=None)
        _, payload = self.resolve(envelope, self.answer(envelope, [
            {"node": "J1", "tier": "tier3", "effort": "high"}]),
            "--project", self.project, "--run-id", self.run_id)
        node = payload["nodes"]["J1"]
        self.assertIs(node["judge"], True)
        self.assertEqual(node["floor"], "tier2")
        self.assertEqual(node["proposed"], "tier3")


class TestResolveRetry(ChoiceCase):
    def setUp(self):
        super().setUp()
        _, _, self.envelope = self.prepare(RETRY_EVIDENCE, roster=None)
        self.project, self.run_id = self.confirmed_project()

    def resolve_retry(self, decisions, *extra, **kw):
        return self.resolve(self.envelope, self.answer(self.envelope, decisions, **kw),
                            "--project", self.project, "--run-id", self.run_id, *extra)

    def test_a_conformant_escalation_raises_the_tier_and_carries_the_diagnostic(self):
        raw = {"diagnostic": "The assertion compared the modelled cost with the spec formula",
               "missing_file_or_contract": None, "action": "escalate_tier",
               "target_tier": "tier3", "effort": "high"}
        code, payload = self.resolve_retry(None, raw=raw)
        self.assertEqual(code, 0)
        node = payload["node"]
        self.assertEqual(node["action"], "escalate_tier")
        self.assertEqual(node["tier"], "tier3")
        self.assertEqual(node["current_tier"], "tier2")
        self.assertIs(node["fresh_escalation"], True)
        self.assertIs(node["without_failed_trace"], True)
        self.assertIn("modelled cost", node["diagnostic"])
        self.assertEqual(node["packet_policy"], tier_router.TIER_PACKET_POLICY["tier3"])
        self.assertEqual(node["model_param"], "gw/deep-high#xhigh")

    def test_a_malformed_action_defaults_to_escalation_and_never_to_a_cheaper_retry(self):
        code, payload = self.resolve_retry([{"node": "T2", "action": "give_up"}])
        self.assertEqual(code, 0)
        self.assertEqual(payload["answer"]["classification"], "non-conformant")
        self.assertEqual(payload["node"]["action"], "escalate_tier")
        self.assertEqual(payload["node"]["tier"], "tier3")
        self.assertIn("declared default", payload["node"]["default_applied"])

    def test_abstention_escalates_rather_than_repeating_the_failed_tier(self):
        _, payload = self.resolve_retry([], status="abstain")
        self.assertEqual(payload["answer"]["classification"], "abstain")
        self.assertEqual(payload["node"]["action"], "escalate_tier")

    def test_a_judge_is_never_escalated(self):
        evidence = dict(RETRY_EVIDENCE,
                        node=dict(RETRY_EVIDENCE["node"], id="J1", op="VERIFY_FINDING"))
        _, _, envelope = self.prepare(evidence, roster=None)
        code, payload = self.resolve(envelope, self.answer(envelope, [
            {"node": "J1", "action": "escalate_tier", "tier": "tier3"}]),
            "--project", self.project, "--run-id", self.run_id)
        self.assertEqual(code, 2)
        self.assertEqual(payload["outcome"], "POLICY_BLOCKED")
        self.assertIn("never escalated", payload["reason"])

    def test_an_escalation_is_refused_when_the_ceiling_is_already_reached(self):
        code, payload = self.resolve_retry(
            [{"node": "T2", "action": "escalate_tier", "tier": "tier3"}],
            "--ceiling", "tier2")
        self.assertEqual(code, 2)
        self.assertEqual(payload["outcome"], "POLICY_BLOCKED")
        self.assertIn("no escalation above tier2", payload["reason"])

    def test_needs_replan_returns_to_the_planner_on_the_top_tier(self):
        code, payload = self.resolve_retry([{"node": "T2", "action": "needs_replan"}])
        self.assertEqual(code, 0)
        self.assertEqual(payload["node"]["action"], "needs_replan")
        self.assertEqual(payload["node"]["tier"], "tier3")
        self.assertEqual(payload["node"]["packet_policy"]["hop_depth"], 2)

    def test_retry_same_tier_keeps_the_tier_of_the_failed_attempt(self):
        _, payload = self.resolve_retry([{"node": "T2", "action": "retry_same_tier"}])
        self.assertEqual(payload["node"]["tier"], "tier2")
        self.assertEqual(payload["node"]["current_tier"], "tier2")
        self.assertIsNone(payload["node"]["fresh_escalation"])

    def test_a_request_edited_after_preparation_binds_no_answer(self):
        envelope = json.loads(json.dumps(self.envelope))
        envelope["request"]["plan_digest"] = "plan-tampered"
        code, payload = self.resolve(envelope, self.answer(self.envelope, []))
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "request-digest-mismatch")
        self.assertIn("edited after preparation", payload["reason"])

    def test_resolve_without_the_frozen_request_refuses_instead_of_trusting_the_answer(self):
        choice = self.home / "CHOICE.json"
        choice.write_text(json.dumps(self.answer(self.envelope, [])), encoding="utf-8")
        out = self.home / "RESOLVED_DISPATCH.json"
        code = tier_router.main(["resolve", "--choice", str(choice), "--out", str(out)])
        payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "request-missing")

    def test_a_snodo_that_contradicts_the_request_is_refused_not_crashed(self):
        _, _, task_envelope = self.prepare(TASK_EVIDENCE, roster=None, name="TASK.md")
        code, payload = self.resolve(task_envelope,
                                     self.answer(task_envelope, []), "--snodo", "reviewer")
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "snodo-request-mismatch")
        self.assertIn("different preparations", payload["reason"])
        code, payload = self.resolve(self.envelope, self.answer(self.envelope, []),
                                     "--snodo", "task")
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "snodo-request-mismatch")

    def test_a_retry_request_without_a_node_refuses_instead_of_escalating_nothing(self):
        request = {"schema": "daodan/routing/v1", "plan_digest": "p", "nodes": [],
                   "escalation": {"current_tier": "tier2", "attempt": 1}}
        envelope = {"schema": tier_router.REQUEST_SCHEMA, "status": "prepared",
                    "snodo": "retry", "answer_schema": "daodan/routing/v1",
                    "request": request,
                    "request_sha256": tier_router.canonical_digest(request)}
        code, payload = self.resolve(envelope, self.answer(envelope, []))
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "node-missing")


if __name__ == "__main__":
    unittest.main()
