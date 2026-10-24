"""Protect catalog identity and evidence before the router intersects a harness.

Fixtures model independent upstream facts: reseller endpoints share an identity,
aliases can be contested, and Arena boards measure different populations.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from datetime import datetime, timezone

SCRIPTS = (Path(__file__).resolve().parents[1] / "plugins" / "model-routing"
           / "skills" / "model-routing" / "scripts")
sys.path.insert(0, str(SCRIPTS))

import build_model_catalog as catalog  # noqa: E402


def _entry(canonical=None, *, input_price=2.0, output_price=8.0,
           family="fixture-family", **extra):
    row = {"family": family, "type": "chat", "status": "active",
           "cost": {"input": input_price, "output": output_price},
           "limit": {"context": 200_000, "output": 32_000},
           "modalities": {"input": ["text"], "output": ["text"]},
           "tool_call": True, "release_date": "2026-10-01"}
    if canonical is not None:
        row["canonical_model_id"] = canonical
    row.update(extra)
    return row


def _provider(models):
    return {"name": "Fixture provider", "models": models}


def _harness(*ids):
    return {"provider": {"gateway": {"models": {mid: {} for mid in ids}}}}


def _observation(category, name, *, score=None, rank=1, effort=None, votes=3000):
    return {"category": category, "arena_name": name, "effort": effort,
            "rank": rank, "score": score, "ci": 12 if score is not None else None,
            "votes": votes}


def _benchmark(index, board_sizes=None):
    observations = [o for rows in index.values() for o in rows]
    board_sizes = board_sizes or {o["category"]: 5 for o in observations}
    return {"source": {"snapshot_date": "2026-10-07", "commit": {"sha": "a" * 40}},
            "boards": {board: {"meta": {"last_updated": "Oct 7, 2026"},
                               "rows_verbatim": [{} for _ in range(count)]}
                       for board, count in board_sizes.items()},
            "match_index": index}


class CatalogCase(unittest.TestCase):
    def build(self, models, benchmark=None, harness=None, **options):
        args = SimpleNamespace(limit=500, per_family=6, revision=3,
                               retrieved_at="2026-10-22T00:00:00+00:00")
        for key, value in options.items():
            setattr(args, key, value)
        return catalog.build(models, benchmark, harness, args)


class TestCanonicalIdentity(CatalogCase):
    def test_non_chat_models_are_excluded_even_when_priced_measured_or_harness_named(self):
        doc = self.build({"lab": _provider({
            "chat": _entry("lab/chat"),
            "priced": _entry("lab/priced", type="embedding"),
            "measured": _entry("lab/measured", type="image"),
            "harness": _entry("lab/harness", type="embedding"),
        })}, _benchmark({"measured": [_observation("vision", "measured", score=1700)]}),
            _harness("harness"))
        self.assertEqual([m["id"] for m in doc["models"]], ["lab/chat"])

    def test_a_non_chat_endpoint_cannot_supply_a_chat_models_indicative_price(self):
        doc = self.build({
            "opencode": _provider({"orbit": _entry("lab/orbit", type="embedding", input_price=0.1)}),
            "lab": _provider({"orbit": _entry("lab/orbit", input_price=2.0)}),
        })
        self.assertEqual(doc["model_count"], 1)
        self.assertEqual(doc["models"][0]["selected_endpoint"], "lab")
        self.assertEqual(doc["models"][0]["cost_usd_per_million"]["input"], 2.0)

    def test_resellers_collapse_to_the_lab_identity_without_losing_price_spread(self):
        identity = "moonshotai/kimi-k3"
        doc = self.build({
            "moonshotai": _provider({"kimi-k3": _entry(identity, input_price=None)}),
            "opencode": _provider({"kimi-k3": _entry(identity, input_price=1.5)}),
            "a-free": _provider({"kimi-k3": _entry(identity, input_price=0)}),
            "reseller": _provider({"moonshotai/kimi-k3": _entry(identity, input_price=3.0)}),
        })
        self.assertEqual(doc["model_count"], 1)
        row = doc["models"][0]
        self.assertEqual((row["id"], row["creator"]), (identity, "moonshotai"))
        self.assertEqual(row["selected_endpoint"], "opencode")
        self.assertEqual(row["cost_usd_per_million"]["input"], 1.5)
        self.assertEqual(row["endpoints"]["count"], 4)
        self.assertEqual(row["endpoints"]["price_spread_usd_per_million"]["input"],
                         {"min": 0, "max": 3.0})
        self.assertTrue(row["cost_is_indicative"])

    def test_a_shared_basename_does_not_merge_different_labs(self):
        doc = self.build({"reseller": _provider({
            "lab-a/orbit": _entry("lab-a/orbit"),
            "lab-b/orbit": _entry("lab-b/orbit"),
        })})
        self.assertEqual({m["id"] for m in doc["models"]}, {"lab-a/orbit", "lab-b/orbit"})
        self.assertEqual(doc["creator_count"], 2)

    def test_an_unattributed_endpoint_joins_only_a_unique_canonical_name(self):
        doc = self.build({
            "lab": _provider({"orbit": _entry("lab/orbit")}),
            "reseller": _provider({"orbit": _entry(), "unknown": _entry()}),
        })
        self.assertEqual(doc["model_count"], 1)
        self.assertEqual(doc["models"][0]["endpoints"]["count"], 2)
        self.assertTrue(any("1 matched one canonical model by name" in n for n in doc["notes"]))
        self.assertTrue(any("1 left unattached" in n for n in doc["notes"]))

    def test_an_unattributed_endpoint_with_two_canonical_claimants_stays_unattached(self):
        doc = self.build({"reseller": _provider({
            "lab-a/orbit": _entry("lab-a/orbit"),
            "lab-b/orbit": _entry("lab-b/orbit"),
            "orbit": _entry(),
        })})
        self.assertEqual([m["endpoints"]["count"] for m in doc["models"]], [1, 1])
        self.assertTrue(any("1 left unattached" in n for n in doc["notes"]))

    def test_a_contested_reseller_alias_is_owned_by_neither_model(self):
        doc = self.build({
            "reseller-a": _provider({"shared-latest": _entry("lab/alpha")}),
            "reseller-b": _provider({"shared-latest": _entry("lab/beta")}),
        })
        self.assertEqual(doc["model_count"], 2)
        for row in doc["models"]:
            self.assertNotIn("shared-latest", row["aliases"])
        self.assertTrue(any("1 have no exact-name owner" in n for n in doc["notes"]))

    def test_the_exact_canonical_name_wins_over_another_models_reseller_alias(self):
        doc = self.build({
            "reseller-a": _provider({"alpha": _entry("lab/alpha")}),
            "reseller-b": _provider({"alpha": _entry("lab/beta")}),
        })
        aliases = {m["id"]: m["aliases"] for m in doc["models"]}
        self.assertIn("alpha", aliases["lab/alpha"])
        self.assertNotIn("alpha", aliases["lab/beta"])

    def test_an_observed_harness_alias_survives_the_limit_on_extra_spellings(self):
        identity = "zhipuai/glm-5.3-flash"
        providers = {f"reseller-{i}": _provider({f"alias-{i}": _entry(identity)})
                     for i in range(15)}
        providers["gateway-mirror"] = _provider({"glm-flash-latest": _entry(identity)})
        doc = self.build(providers, harness=_harness("glm-flash-latest"))
        self.assertIn("glm-flash-latest", doc["models"][0]["aliases"])

    def test_a_harness_local_identity_keeps_the_missing_creator_explicit(self):
        doc = self.build({"reseller": _provider({"local-engine": _entry()})},
                         harness=_harness("local-engine", "not-published"))
        self.assertEqual(doc["model_count"], 1)
        row = doc["models"][0]
        self.assertEqual(row["id"], "local-engine")
        self.assertIsNone(row["creator"])
        self.assertEqual(row["identity"], "harness-declared-provider-local")
        self.assertEqual(row["provenance"]["taxonomy"]["method"], "declared")
        self.assertTrue(any("not-published" in n and "stay outside" in n for n in doc["notes"]))

    def test_catalog_ids_keep_real_suffixes_while_arena_observations_strip_effort(self):
        self.assertEqual(catalog.norm("qwen/qwen3.8-max"), "qwen38max")
        self.assertNotEqual(catalog.norm("qwen3.8-max"), catalog.norm("qwen3.8"))
        self.assertEqual(catalog.norm_arena("claude-opus-5.5-max"),
                         catalog.norm("anthropic/claude-opus-5-5"))

    def test_effort_options_follow_the_published_list_shape_and_unknown_stays_unknown(self):
        doc = self.build({"lab": _provider({
            "a": _entry("lab/a", reasoning_options=[
                {"type": "effort", "values": ["high", "low", "high"]},
                {"type": "other", "values": ["unsupported"]}]),
            "b": _entry("lab/b", reasoning_options={"efforts": ["high"]}),
        })})
        rows = {m["id"]: m for m in doc["models"]}
        self.assertEqual(rows["lab/a"]["capabilities"]["effort_levels"], ["high", "low"])
        self.assertIsNone(rows["lab/b"]["capabilities"]["effort_levels"])


class TestBoardEvidence(CatalogCase):
    def test_board_priority_never_compares_the_larger_score_from_another_population(self):
        benchmark = _benchmark({"claudeopus55": [
            _observation("text", "claude-opus-5.5-max", score=2200, rank=1),
            _observation("code", "claude-opus-5.5-high", score=1700, rank=3, effort="high"),
            _observation("code", "claude-opus-5.5-max", score=1750, rank=2, effort="max"),
        ]})
        row = self.build({"lab": _provider({"opus": _entry("anthropic/claude-opus-5-5")})},
                         benchmark)["models"][0]
        self.assertEqual(row["tier"], 3)
        self.assertTrue(row["tier_invariant_to_effort"])
        self.assertEqual(row["tier_evidence"]["benchmark"]["board"], "code")
        self.assertEqual(row["tier_evidence"]["benchmark"]["score"], 1750)
        self.assertEqual(row["aptitudes"]["analysis"]["score"], 2200)
        self.assertEqual(row["aptitudes"]["coding"]["effort"], "max")

    def test_a_rank_only_board_preserves_rank_and_never_fabricates_a_score(self):
        benchmark = _benchmark({"kimik3": [
            _observation("agent", "kimi-k3-high", rank=4, effort="high"),
            _observation("agent", "kimi-k3-max", rank=2, effort="max"),
        ]}, {"agent": 5})
        row = self.build({"lab": _provider({"kimi": _entry("moonshotai/kimi-k3")})},
                         benchmark)["models"][0]
        aptitude = row["aptitudes"]["agent_tool_use"]
        self.assertEqual((aptitude["rank"], aptitude["of"], aptitude["level"]), (2, 5, 0.75))
        self.assertIsNone(aptitude["score"])
        self.assertIsNone(aptitude["ci"])
        self.assertEqual(aptitude["method"], "measured-rank-only")
        self.assertEqual(row["tier_evidence"]["method"], "measured-rank-only")
        self.assertNotIn("coding", row["aptitudes"])
        self.assertNotIn("media_generation", row["aptitudes"])

    def test_file_order_is_evidence_order_and_does_not_depend_on_provider_order(self):
        models = {"lab": _provider({
            "alpha": _entry("lab/alpha"), "zeta": _entry("lab/zeta"),
            "beta": _entry("lab/beta"), "none": _entry("lab/none"),
        })}
        benchmark = _benchmark({
            "alpha": [_observation("text", "alpha", score=3000)],
            "zeta": [_observation("code", "zeta", score=1700)],
            "beta": [_observation("code", "beta", score=1600)],
        })
        expected = ["lab/zeta", "lab/beta", "lab/alpha", "lab/none"]
        self.assertEqual([m["id"] for m in self.build(models, benchmark)["models"]], expected)
        reversed_models = {"lab": _provider(dict(reversed(list(models["lab"]["models"].items()))))}
        self.assertEqual([m["id"] for m in self.build(reversed_models, benchmark)["models"]], expected)

    def test_rank_only_observations_order_the_catalog_by_rank_within_the_board(self):
        models = {"lab": _provider({
            "alpha": _entry("lab/alpha"), "zeta": _entry("lab/zeta"),
        })}
        benchmark = _benchmark({"alpha": [_observation("agent", "alpha", rank=4)],
                                "zeta": [_observation("agent", "zeta", rank=1)]})
        self.assertEqual([m["id"] for m in self.build(models, benchmark)["models"]],
                         ["lab/zeta", "lab/alpha"])

    def test_harness_and_measured_rows_survive_a_limit_that_excludes_other_rows(self):
        doc = self.build({"lab": _provider({
            "harness": _entry("lab/harness", release_date="2020-01-01"),
            "measured": _entry("lab/measured", release_date="2020-01-01"),
            "newest": _entry("lab/newest", release_date="2026-10-22"),
        })}, _benchmark({"measured": [_observation("code", "measured", score=1700)]}),
            _harness("harness"), limit=1)
        self.assertEqual({m["id"] for m in doc["models"]}, {"lab/harness", "lab/measured"})


class TestProvidedData(CatalogCase):
    def test_direct_build_keeps_the_supplied_retrieval_time_and_names_its_input_mode(self):
        source = self.build({"lab": _provider({"orbit": _entry("lab/orbit")})})["sources"][0]
        self.assertEqual(source["retrieved_at"], "2026-10-22T00:00:00+00:00")
        self.assertEqual(source["input_mode"], "provided-data")


class TestCatalogArtifact(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="model-catalog-")
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)

    def run_cli(self, *args):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = catalog.main(["--out", str(self.tmp / "catalog.json"), *args])
        return code, json.loads(stdout.getvalue())

    def test_egress_requires_opt_in_and_does_not_replace_an_existing_catalog(self):
        out = self.tmp / "catalog.json"
        out.write_text("existing catalog", encoding="utf-8")
        with mock.patch.object(catalog.urllib.request, "build_opener") as opener:
            code, summary = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("opt-in", summary["reason"])
        opener.assert_not_called()
        self.assertEqual(out.read_text(encoding="utf-8"), "existing catalog")

    def test_local_response_writes_a_reproducible_digest_and_preserves_provenance(self):
        raw = json.dumps({"lab": _provider({"orbit": _entry("lab/orbit")})}).encode("utf-8")
        response = self.tmp / "response.json"
        response.write_bytes(raw)
        with mock.patch.object(catalog.urllib.request, "build_opener") as opener:
            code, summary = self.run_cli("--from-response", str(response), "--revision", "7")
        self.assertEqual(code, 0, summary)
        opener.assert_not_called()
        body = (self.tmp / "catalog.json").read_bytes()
        doc = json.loads(body)
        self.assertEqual(doc["models_dev_raw_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(summary["catalog_sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(summary["out_bytes"], len(body))
        self.assertEqual(doc["schema"], "daodan/model-catalog/v1")
        self.assertEqual(doc["revision"], 7)
        self.assertFalse((self.tmp / "catalog.json.tmp").exists())
        self.assertIsNone(doc["sources"][0]["retrieved_at"])
        self.assertEqual(doc["sources"][0]["input_mode"], "cached-response")

    def test_a_network_fetch_records_the_actual_retrieval_time_and_input_mode(self):
        raw = json.dumps({"lab": _provider({"orbit": _entry("lab/orbit")})}).encode("utf-8")
        retrieved = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
        with (mock.patch.object(catalog.urllib.request, "build_opener") as opener,
              mock.patch.object(catalog, "datetime") as clock):
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = raw
            clock.now.return_value = retrieved
            code, summary = self.run_cli("--fetch")
        self.assertEqual(code, 0, summary)
        doc = json.loads((self.tmp / "catalog.json").read_bytes())
        self.assertEqual(doc["sources"][0]["retrieved_at"], "2026-10-23T12:00:00+00:00")
        self.assertEqual(doc["sources"][0]["input_mode"], "network-fetch")

    def test_invalid_local_json_fails_without_writing_a_catalog(self):
        response = self.tmp / "response.json"
        response.write_bytes(b"not JSON")
        code, summary = self.run_cli("--from-response", str(response))
        self.assertEqual(code, 1)
        self.assertIn("not UTF-8 JSON", summary["reason"])
        self.assertFalse((self.tmp / "catalog.json").exists())


if __name__ == "__main__":
    unittest.main()
