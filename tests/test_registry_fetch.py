"""Pins registry_fetch.py: opt-in egress, the allowlist, and the source-shape traps.

The traps matter more than the happy path. OpenRouter prices are strings in USD per
token, ids carry ``:batch``/``:free`` service tiers at different prices, ``~``-prefixed
ids are floating aliases, and ``pricing.overrides`` means the flat rate is not the
effective price. Each of those, handled silently, would corrupt a model binding.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "project-protocol" / "skills" / "project-protocol" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import registry_fetch  # noqa: E402


def _row(rid, prompt="0.000002", completion="0.00001", cache_read=None,
         cache_write=None, overrides=None, ctx=1_000_000, max_out=64_000,
         params=None, reasoning=False):
    pricing = {"prompt": prompt, "completion": completion}
    if cache_read is not None:
        pricing["input_cache_read"] = cache_read
    if cache_write is not None:
        pricing["input_cache_write"] = cache_write
    if overrides is not None:
        pricing["overrides"] = overrides
    return {"id": rid, "canonical_slug": rid, "name": rid.upper(),
            "context_length": ctx,
            "architecture": {"modality": "text->text", "input_modalities": ["text"],
                             "output_modalities": ["text"]},
            "pricing": pricing,
            "top_provider": {"context_length": ctx, "max_completion_tokens": max_out},
            "supported_parameters": params if params is not None else ["tools", "max_tokens"],
            "reasoning": reasoning}


class RegistryFetchCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="registry-fetch-"))
        self.addCleanup(lambda: None)

    def run_cli(self, *argv):
        out = self.tmp / "registry.json"
        buf = []
        with mock.patch.object(sys, "stdout", new=_Capture(buf)):
            code = registry_fetch.main(["--out", str(out), *argv])
        payload = json.loads("".join(buf)) if buf else None
        return code, payload, out


class _Capture:
    def __init__(self, sink):
        self.sink = sink

    def write(self, text):
        self.sink.append(text)

    def flush(self):
        pass


class TestEgressIsOptIn(RegistryFetchCase):
    def test_without_fetch_or_a_local_response_it_refuses_and_reaches_no_network(self):
        with mock.patch.object(registry_fetch.urllib.request, "urlopen") as opener:
            code, payload, out = self.run_cli()
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("opt-in", payload["reason"])
        opener.assert_not_called()
        self.assertFalse(out.exists())

    def test_an_unreachable_source_is_a_stated_gap_not_an_empty_registry(self):
        with mock.patch.object(registry_fetch, "fetch_raw",
                               return_value=(None, "TimeoutError: timed out")):
            code, payload, out = self.run_cli("--fetch")
        self.assertEqual(code, 1)
        self.assertIn("source unreachable", payload["reason"])
        self.assertIn("TimeoutError", payload["reason"])
        self.assertIn("fall back", payload["consequence"])
        self.assertFalse(out.exists())

    def test_a_non_https_url_is_refused_before_any_request(self):
        raw, err = registry_fetch.fetch_raw("http://openrouter.ai/api/v1/models", 5, 1024)
        self.assertIsNone(raw)
        self.assertIn("non-HTTPS", err)

    def test_an_unknown_source_is_refused_and_the_allowlist_is_named(self):
        # argparse owns the allowlist: a source outside it never reaches a request.
        with self.assertRaises(SystemExit) as ctx:
            registry_fetch.main(["--out", str(self.tmp / "r.json"),
                                 "--from-response", "x.json", "--source", "evil"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(sorted(registry_fetch.SOURCES), ["openrouter"])
        for source in registry_fetch.SOURCES.values():
            self.assertTrue(source["url"].startswith("https://"))

    def test_an_oversized_response_is_discarded_rather_than_truncated(self):
        with mock.patch.object(registry_fetch.urllib.request, "build_opener") as opener:
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = b"x" * 11
            raw, err = registry_fetch.fetch_raw("https://openrouter.ai/api/v1/models", 5, 10)
        self.assertIsNone(raw)
        self.assertIn("--max-bytes", err)


class TestSourceShapeTraps(RegistryFetchCase):
    def reduce(self, rows):
        response = self.tmp / "response.json"
        response.write_text(json.dumps({"data": rows, "total_count": len(rows)}),
                            encoding="utf-8")
        code, payload, out = self.run_cli("--from-response", str(response))
        self.assertEqual(code, 0, payload)
        return json.loads(out.read_text(encoding="utf-8")), payload

    def test_per_token_string_prices_become_usd_per_million_tokens(self):
        reg, _ = self.reduce([_row("anthropic/claude-x", prompt="0.000002",
                                   completion="0.00001", cache_read="0.0000001",
                                   cache_write="0.0000025")])
        cost = reg["models"][0]["cost_usd_per_million_tokens"]
        self.assertEqual(cost["input"], 2.0)
        self.assertEqual(cost["output"], 10.0)
        self.assertEqual(cost["cache_read"], 0.1)
        self.assertEqual(cost["cache_write"], 2.5)

    def test_service_tiers_stay_separate_records_and_are_never_merged(self):
        reg, _ = self.reduce([_row("anthropic/claude-x", prompt="0.000010"),
                              _row("anthropic/claude-x:batch", prompt="0.000005"),
                              _row("anthropic/claude-x:free", prompt="0")])
        by_tier = {(m["base_id"], m["service_tier"]): m for m in reg["models"]}
        self.assertEqual(by_tier[("anthropic/claude-x", "base")]
                         ["cost_usd_per_million_tokens"]["input"], 10.0)
        self.assertEqual(by_tier[("anthropic/claude-x", "batch")]
                         ["cost_usd_per_million_tokens"]["input"], 5.0)
        self.assertEqual(reg["counts"]["service_tiers"], {"base": 1, "batch": 1, "free": 1})

    def test_a_floating_alias_is_flagged_because_it_is_not_a_pinned_artifact(self):
        reg, _ = self.reduce([_row("~openai/gpt-x-latest")])
        self.assertTrue(reg["models"][0]["floating_alias"])
        self.assertEqual(reg["counts"]["floating_aliases"], 1)

    def test_context_tiered_pricing_is_flagged_so_the_flat_rate_is_not_trusted(self):
        reg, _ = self.reduce([_row("moonshotai/kimi-x", overrides=[{"price": "1"}])])
        self.assertTrue(reg["models"][0]["price_is_tiered"])
        self.assertIn("not the effective price",
                      reg["models"][0]["price_tiered_note"])
        self.assertEqual(reg["counts"]["price_is_tiered"], 1)

    def test_capability_flags_come_from_declared_parameters_not_from_the_name(self):
        reg, _ = self.reduce([
            _row("a/with-tools", params=["tools", "response_format"]),
            _row("a/no-tools", params=["max_tokens"]),
            _row("a/reasoning-param", params=["include_reasoning"]),
            _row("a/reasoning-flag", params=["max_tokens"], reasoning=True),
        ])
        caps = {m["id"]: m["capabilities"] for m in reg["models"]}
        self.assertTrue(caps["a/with-tools"]["tools"])
        self.assertTrue(caps["a/with-tools"]["structured_outputs"])
        self.assertFalse(caps["a/no-tools"]["tools"])
        self.assertTrue(caps["a/reasoning-param"]["reasoning"])
        self.assertTrue(caps["a/reasoning-flag"]["reasoning"])

    def test_the_artifact_carries_its_own_provenance_and_attribution(self):
        reg, summary = self.reduce([_row("a/b")])
        for key in ("raw_sha256", "models_sha256", "generated_at", "source", "origin",
                    "upstream_total_count", "model_count", "attribution"):
            self.assertIn(key, reg, key)
        self.assertEqual(reg["schema"], "daodan/model-fact-registry/v1")
        self.assertEqual(reg["semantics"]["not_included"],
                         ["capability", "quality", "tier", "frontier ordering"])
        self.assertIn("OpenRouter", reg["attribution"])
        self.assertEqual(summary["model_count"], 1)
        self.assertEqual(len(reg["raw_sha256"]), 64)

    def test_a_malformed_record_is_skipped_and_counted_not_crashed_on(self):
        reg, summary = self.reduce([_row("a/b"), {"no_id": True}, "not-a-dict"])
        self.assertEqual(summary["model_count"], 1)
        self.assertEqual(summary["records_skipped"], 2)


if __name__ == "__main__":
    unittest.main()
