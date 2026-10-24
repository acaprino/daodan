"""Pins usage_pricing.py: one reader per host, prices per endpoint, rules with sources.

Fixture numbers are trimmed from real local logs of 2026-10-24, so each reader is held
to what its host actually writes, and the official-rate cases price against the shipped
`model-prices.json` and `price-rules.json`.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "plugins/project-protocol/skills/project-protocol"
SCRIPT = SKILL / "scripts/usage_pricing.py"
sys.path.insert(0, str(SCRIPT.parent))

import build_model_prices as bmp  # noqa: E402
import usage_pricing as up  # noqa: E402

CATALOG = {"models": [
    {"id": "acme/coder-1", "creator": "acme", "selected_endpoint": "acme",
     "aliases": ["acme/coder-1", "coder-1", "coder-1-free"]},
    {"id": "anthropic/claude-opus-5-5", "creator": "anthropic", "selected_endpoint": "opencode",
     "aliases": ["anthropic/claude-opus-5-5", "claude-opus-5-5"]},
]}
PRICES = {"revision": 7, "models": {
    "acme/coder-1": {"creator": "acme", "endpoints": {
        "acme": {"coder-1": {"input": 1, "output": 4, "cache_read": 0.1},
                 "coder-1-free": {"input": 0, "output": 0}},
        "resell": {"coder-1": {"input": 2, "output": 8, "cache_read": 0.2, "cache_write": 2.5,
                               "tiers": [{"input": 3, "output": 12, "cache_read": 0.3,
                                          "tier": {"type": "context", "size": 1000}}]}}}},
    "anthropic/claude-opus-5-5": {"creator": "anthropic", "endpoints": {
        "anthropic": {"claude-opus-5-5": {"input": 4, "output": 20, "cache_read": 0.2,
                                          "cache_write": 5}}}},
}}
RULES = json.loads((SKILL / "references/price-rules.json").read_text(encoding="utf-8"))
RULES = dict(RULES, rules=RULES["rules"] + [{
    "id": "acme.peak", "provider": "acme", "kind": "multiplier", "multiplier": 2.0,
    "when": {"utc_days": ["monday"], "utc_hours": [1, 4]}, "source": "test", "verified": "test"}])


def pricer(harness=None):
    return up.Pricer(PRICES, CATALOG, RULES, harness)


def write_jsonl(path, lines):
    path.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
    return path


class Readers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_claude_code_counts_a_response_once_and_splits_thinking_and_ttl(self):
        usage = {"input_tokens": 4, "cache_read_input_tokens": 110474,
                 "cache_creation_input_tokens": 67171,
                 "cache_creation": {"ephemeral_5m_input_tokens": 67171,
                                    "ephemeral_1h_input_tokens": 0},
                 "output_tokens": 1025, "output_tokens_details": {"thinking_tokens": 803},
                 "server_tool_use": {"web_search_requests": 2}, "inference_geo": "global",
                 "speed": "standard", "service_tier": "standard"}
        line = {"sessionId": "s1", "requestId": "r1", "timestamp": "2026-10-24T09:00:00Z",
                "message": {"id": "m1", "role": "assistant", "model": "claude-opus-5-5",
                            "usage": usage}}
        session = write_jsonl(self.dir / "s1.jsonl", [line, line, {
            "message": {"role": "assistant", "model": "<synthetic>", "usage": usage}}])
        sub = self.dir / "s1" / "subagents"
        sub.mkdir(parents=True)
        worker = dict(line, isSidechain=True, agentId="a7", requestId="r2",
                      message=dict(line["message"], id="m2"))
        write_jsonl(sub / "agent-a7.jsonl", [worker])
        rows = list(up.read_claude_code([session]))
        self.assertEqual(len(rows), 2)
        main, sidechain = rows
        self.assertEqual((main["output"], main["reasoning"]), (222, 803))
        self.assertEqual((main["cache_write_5m"], main["cache_write_1h"]), (67171, 0))
        self.assertEqual(main["provider"], "anthropic")
        self.assertEqual(main["requests"], {"web_search": 2})
        self.assertEqual((main["worker"], sidechain["worker"]), (None, "a7"))

    def test_codex_subtracts_the_cached_subset_and_takes_the_turn_model(self):
        rec = {"type": "token_usage_record", "timestamp": "2026-10-23T19:06:12Z", "payload": {
            "thread_id": "t1", "session_id": "t1", "turn_id": "u1", "response_id": "resp1",
            "usage": {"input_tokens": 175458, "cached_input_tokens": 23808,
                      "cache_write_input_tokens": 0, "output_tokens": 125,
                      "reasoning_output_tokens": 52, "total_tokens": 175583}}}
        f = write_jsonl(self.dir / "rollout.jsonl", [
            {"type": "session_meta", "payload": {"id": "t1", "model_provider": "openai"}},
            {"type": "turn_context", "payload": {"turn_id": "u1", "model": "gpt-6.1-sol"}},
            rec, rec])
        rows = list(up.read_codex([f]))
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["input"], r["cache_read"]), (151650, 23808))
        self.assertEqual((r["output"], r["reasoning"]), (73, 52))
        self.assertEqual((r["provider"], r["model"], r["worker"]), ("openai", "gpt-6.1-sol", None))

    def test_opencode_reproduces_its_logged_cost_with_reasoning_beside_output(self):
        db = self.dir / "opencode.db"
        con = sqlite3.connect(db)
        con.execute("create table session_v2 (id text, parent_id text)")
        con.execute("create table session_message (id text, session_id text, type text, "
                    "seq int, time_created int, data text)")
        con.executemany("insert into session_v2 values (?, ?)", [("root", None), ("kid", "root")])
        data = {"cost": 0.1789946, "model": {"id": "claude-opus-5-5",
                                             "providerID": "tri-llm-gateway"},
                "tokens": {"input": 4, "output": 321, "reasoning": 42,
                           "cache": {"read": 707273, "write": 3783}}}
        con.execute("insert into session_message values ('m1', 'kid', 'assistant', 1, "
                    "1761300000000, ?)", (json.dumps(data),))
        con.execute("insert into session_message values ('m2', 'kid', 'user', 2, 0, '{}')")
        con.commit()
        con.close()
        rows = list(up.read_opencode([db]))
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["session"], r["worker"]), ("root", "kid"))
        gateway = {"tri-llm-gateway": {up.norm("claude-opus-5-5"): {
            "input": 4, "output": 20, "cache_read": 0.2, "cache_write": 8}}}
        p = pricer(gateway).price(r)["price"]
        self.assertEqual(p["basis"], "harness-config")
        self.assertAlmostEqual(p["total_usd"], 0.1789946, places=9)

    def test_pi_reproduces_its_logged_cost_and_detects_reasoning_outside_output(self):
        msg = {"role": "assistant", "provider": "tri-llm-gateway", "model": "claude-opus-5-5",
               "usage": {"input": 4, "output": 140, "cacheRead": 12556, "cacheWrite": 61913,
                         "reasoning": 0, "totalTokens": 74613, "cost": {"total": 0.5006312}}}
        outside = dict(msg, usage=dict(msg["usage"], reasoning=10, totalTokens=74623))
        sessions = self.dir / "sessions" / "proj"
        sessions.mkdir(parents=True)
        write_jsonl(sessions / "x.jsonl", [{"type": "session", "id": "p1"},
                                           {"id": "e1", "message": msg},
                                           {"id": "e2", "message": outside}])
        rows = list(up.read_pi([self.dir / "sessions"]))
        self.assertEqual([r["session"] for r in rows], ["p1", "p1"])
        self.assertEqual((rows[1]["output"], rows[1]["reasoning"]), (140, 10))
        gateway = {"tri-llm-gateway": {up.norm("claude-opus-5-5"): {
            "input": 4, "output": 20, "cache_read": 0.2, "cache_write": 8}}}
        p = pricer(gateway).price(rows[0])["price"]
        self.assertAlmostEqual(p["total_usd"], rows[0]["host_cost"], places=9)


class Pricing(unittest.TestCase):
    def row(self, **kw):
        return up._row("test", **kw)

    def test_official_anthropic_rates_price_the_one_hour_write_at_twice_input(self):
        real = up.Pricer(up.load_json(up.DEFAULT_PRICES), up.load_json(up.DEFAULT_CATALOG),
                         up.load_json(up.DEFAULT_RULES))
        p = real.price(self.row(provider="anthropic", model="claude-opus-5-5",
                                cache_write_1h=488681))["price"]
        self.assertEqual(p["rates_usd_per_million"]["cache_write_1h"], 8.0)
        self.assertAlmostEqual(p["total_usd"], 3.909448, places=6)
        self.assertIn("anthropic.cache-write-1h", p["rules"])

    def test_official_haiku_tier_applies_above_100k_prompt_tokens_including_cache(self):
        real = up.Pricer(up.load_json(up.DEFAULT_PRICES), up.load_json(up.DEFAULT_CATALOG),
                         up.load_json(up.DEFAULT_RULES))
        below = real.price(self.row(provider="anthropic", model="claude-haiku-5-5",
                                    input=50_000, cache_read=50_000))["price"]
        above = real.price(self.row(provider="anthropic", model="claude-haiku-5-5",
                                    input=50_000, cache_read=100_000))["price"]
        self.assertEqual(below["rates_usd_per_million"]["input"], 0.1)
        self.assertEqual((above["tier"], above["rates_usd_per_million"]["input"]), (100000, 0.5))

    def test_attribute_rules_multiply_and_web_search_is_per_request(self):
        base = dict(provider="anthropic", model="claude-opus-5-5", input=1_000_000)
        plain = pricer().price(self.row(**base))["price"]["total_usd"]
        us = pricer().price(self.row(**base, attrs={"inference_geo": "us"}))["price"]
        fast = pricer().price(self.row(**base, attrs={"speed": "fast"}))["price"]
        search = pricer().price(self.row(**base, requests={"web_search": 3}))["price"]
        self.assertAlmostEqual(plain, 4.0)
        self.assertAlmostEqual(us["total_usd"], 4.4)
        self.assertAlmostEqual(fast["total_usd"], 8.0)
        self.assertAlmostEqual(search["total_usd"], 4.03)

    def test_time_window_rule_holds_only_inside_its_utc_hours(self):
        inside = pricer().price(self.row(provider="acme", model="coder-1", input=1_000_000,
                                         ts="2026-10-19T02:30:00Z"))["price"]
        outside = pricer().price(self.row(provider="acme", model="coder-1", input=1_000_000,
                                          ts="2026-10-19T04:00:00Z"))["price"]
        self.assertEqual((inside["total_usd"], outside["total_usd"]), (2.0, 1.0))

    def test_dated_and_peak_rules_from_the_shipped_file_hold_only_in_their_window(self):
        real = up.Pricer({"revision": 0, "models": {
            "google/gemini-4-argon": {"creator": "google", "endpoints": {"google": {
                "gemini-4-argon": {"input": 2, "output": 10, "cache_read": 0.1}}}},
            "deepseek/deepseek-flash": {"creator": "deepseek", "endpoints": {"deepseek": {
                "deepseek-flash": {"input": 0.15, "output": 0.6, "cache_read": 0.003}}}}}},
            {"models": [{"id": "google/gemini-4-argon", "creator": "google",
                         "aliases": ["gemini-4-argon"]},
                        {"id": "deepseek/deepseek-flash", "creator": "deepseek",
                         "aliases": ["deepseek-flash"]}]},
            up.load_json(up.DEFAULT_RULES))
        argon = lambda ts: real.price(self.row(provider="google", model="gemini-4-argon",  # noqa: E731
                                               input=1_000_000, ts=ts))["price"]["total_usd"]
        self.assertEqual((argon("2026-11-30T23:59:00Z"), argon("2026-12-01T00:00:00Z")), (2.0, 4.0))
        flash = lambda ts: real.price(self.row(provider="deepseek", model="deepseek-flash",  # noqa: E731
                                               input=1_000_000, ts=ts))["price"]
        peak, off, weekend = flash("2026-10-26T07:30:00Z"), flash("2026-10-26T05:00:00Z"), \
            flash("2026-10-25T07:30:00Z")
        self.assertEqual((peak["total_usd"], off["total_usd"], weekend["total_usd"]), (0.3, 0.15, 0.15))
        self.assertIn("deepseek.peak-late", peak["rules"])

    def test_the_logged_spelling_picks_its_own_price_at_the_endpoint(self):
        free = pricer().price(self.row(provider="acme", model="coder-1-free",
                                       input=1000, output=1000))["price"]
        self.assertEqual((free["priced"], free["total_usd"]), (True, 0.0))

    def test_context_tier_and_missing_write_rate_fall_back_with_a_note(self):
        p = pricer().price(self.row(provider="resell", model="coder-1", input=800,
                                    cache_write_5m=400))["price"]
        self.assertEqual(p["tier"], 1000)
        self.assertEqual(p["rates_usd_per_million"]["input"], 3)
        self.assertEqual(p["rates_usd_per_million"]["cache_write_5m"], 2.5)
        q = pricer().price(self.row(provider="acme", model="coder-1", cache_write_5m=10))["price"]
        self.assertIn("cache write billed at the input rate", q["approximations"])

    def test_unlisted_endpoint_falls_back_to_the_creator_and_says_so(self):
        p = pricer().price(self.row(provider="gateway", model="coder-1", input=10))["price"]
        self.assertEqual((p["endpoint"], p["basis"]), ("acme", "creator-endpoint"))
        self.assertTrue(p["approximations"])

    def test_an_unknown_model_is_unpriced_never_zero_and_the_total_is_partial(self):
        rows = [pricer().price(self.row(provider="acme", model="mystery", input=51531)),
                pricer().price(self.row(provider="acme", model="coder-1", input=1000))]
        self.assertEqual(rows[0]["price"]["priced"], False)
        s = up.summarize(rows, {})
        self.assertEqual((s["status"], s["totals"]["unpriced"]), ("partial", 1))
        self.assertIsNone(next(g for g in s["by_model"] if g["model"] == "mystery")["total_usd"])


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *args],
                              capture_output=True, text=True, encoding="utf-8")

    def test_copilot_is_unavailable_with_its_reason(self):
        r = self.run_cli("summary", "--host", "copilot")
        self.assertEqual(r.returncode, 3)
        self.assertEqual(json.loads(r.stdout)["status"], "unavailable")

    def test_summary_is_byte_identical_across_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            line = {"sessionId": "s", "requestId": "r", "timestamp": "2026-10-24T09:00:00Z",
                    "message": {"id": "m", "role": "assistant", "model": "claude-opus-5-5",
                                "usage": {"input_tokens": 10, "output_tokens": 20}}}
            f = write_jsonl(Path(tmp) / "s.jsonl", [line])
            a = self.run_cli("summary", "--host", "claude-code", "--source", str(f))
            b = self.run_cli("summary", "--host", "claude-code", "--source", str(f))
        self.assertEqual(a.returncode, 0, a.stderr)
        self.assertEqual(a.stdout, b.stdout)
        self.assertEqual(json.loads(a.stdout)["status"], "complete")


class PriceFile(unittest.TestCase):
    def test_keeps_every_spelling_at_kept_endpoints_only(self):
        models_dev = {
            "acme": {"models": {"coder-1": {"canonical_model_id": "acme/coder-1",
                                            "cost": {"input": 1, "output": 4}},
                                "coder-1-free": {"cost": {"input": 0, "output": 0}}}},
            "elsewhere": {"models": {"coder-1": {"canonical_model_id": "acme/coder-1",
                                                 "cost": {"input": 9, "output": 9}}}},
            "openrouter": {"models": {"acme/coder-1": {"canonical_model_id": "acme/coder-1",
                                                       "cost": {"input": 1.1, "output": 4.4,
                                                                "tiers": []}}}}}
        models, by_name = bmp.build(models_dev, CATALOG, bmp.KEEP)
        eps = models["acme/coder-1"]["endpoints"]
        self.assertEqual(sorted(eps), ["acme", "openrouter"])
        self.assertEqual(sorted(eps["acme"]), ["coder-1", "coder-1-free"])
        self.assertIn("tiers", eps["openrouter"]["acme/coder-1"])
        self.assertEqual(by_name, 1)


if __name__ == "__main__":
    unittest.main()
