#!/usr/bin/env python3
"""Price the token usage coding-agent hosts log, at list price, per endpoint (ADR-0003).

A figure here is a comparison measure for runs, roles and tiers, never a bill:
subscriptions, credits, private offers and gateway margins are not modelled.

Three inputs, each with one owner:

- **usage**, read from the host's own local log by one reader per host (`READERS`).
  Hosts disagree on what a token count contains, and every reader maps its host to one
  row shape where `input` is uncached input, cache reads and writes have their own
  buckets and `output` excludes `reasoning`. Measured on 2026-10-24: Claude Code puts
  `thinking_tokens` inside `output_tokens` and splits cache writes into 5 minutes and
  1 hour; Codex puts `cached_input_tokens` inside `input_tokens` and
  `reasoning_output_tokens` inside `output_tokens`; OpenCode keeps `reasoning` outside
  `output` (its logged cost reproduces only that way); Pi reports one write bucket.
- **endpoint prices**, from `references/model-prices.json`, which `build_model_prices.py`
  generates from models.dev with every price dimension it publishes. A row is priced at
  the endpoint that served it, because prices belong to endpoints. An endpoint models.dev
  does not list (a private gateway) is priced from the harness's own provider config when
  one is passed, otherwise at the model creator's endpoint, marked approximate.
- **provider rules**, from `references/price-rules.json`: what an official pricing page
  states and models.dev does not carry, each rule with its source and verification date.

What is never done: a missing source or price becomes zero. An unpriced row is
`priced: false` with its reason, and every total says how many rows it lacks.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_model_catalog import norm  # noqa: E402  one owner of model-name identity

HERE = Path(__file__).resolve().parent
DEFAULT_PRICES = HERE.parent / "references" / "model-prices.json"
DEFAULT_CATALOG = HERE.parent / "references" / "model-catalog.json"
DEFAULT_RULES = HERE.parent / "references" / "price-rules.json"

BUCKETS = ("input", "cache_read", "cache_write_5m", "cache_write_1h", "output", "reasoning")
PROMPT_BUCKETS = ("input", "cache_read", "cache_write_5m", "cache_write_1h")


# --------------------------------------------------------------------------- readers
def _jsonl(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _row(host, **kw):
    row = {"host": host, "provider": None, "model": None, "session": None, "worker": None,
           "ts": None, "source_key": None, "host_cost": None, "requests": {}, "attrs": {}}
    row.update({b: 0 for b in BUCKETS})
    row.update(kw)
    for b in BUCKETS:
        row[b] = max(int(row[b] or 0), 0)
    return row


def read_claude_code(paths, endpoint=None):
    """Session transcripts; a session's workers sit in `<session>/subagents/`.

    One response is written as several lines with the same `message.id` and `requestId`
    and an identical usage (measured: 112 of 132 keys repeated, none differing), so the
    key counts once. The log names no provider: the API endpoint is `anthropic` unless
    the caller says otherwise (Bedrock, Vertex, a gateway).
    """
    files = []
    for p in map(Path, paths):
        files.append(p)
        sub = p.with_suffix("") / "subagents"
        if sub.is_dir():
            files.extend(sorted(sub.glob("agent-*.jsonl")))
    seen = set()
    for f in files:
        for line in _jsonl(f):
            m = line.get("message")
            if not isinstance(m, dict) or m.get("role") != "assistant":
                continue
            u = m.get("usage")
            if not isinstance(u, dict) or m.get("model") in (None, "<synthetic>"):
                continue
            key = (m.get("id"), line.get("requestId"))
            if key in seen:
                continue
            seen.add(key)
            cc = u.get("cache_creation") or {}
            w5, w1 = cc.get("ephemeral_5m_input_tokens"), cc.get("ephemeral_1h_input_tokens")
            if w5 is None and w1 is None:
                w5, w1 = u.get("cache_creation_input_tokens") or 0, 0
            out = u.get("output_tokens") or 0
            think = (u.get("output_tokens_details") or {}).get("thinking_tokens") or 0
            stu = u.get("server_tool_use") or {}
            yield _row("claude-code", provider=endpoint or "anthropic", model=m.get("model"),
                       session=line.get("sessionId"),
                       worker=line.get("agentId") if line.get("isSidechain") else None,
                       ts=line.get("timestamp"), source_key=f"{key[0]}:{key[1]}",
                       input=u.get("input_tokens"), cache_read=u.get("cache_read_input_tokens"),
                       cache_write_5m=w5, cache_write_1h=w1,
                       output=out - think, reasoning=think,
                       requests={"web_search": stu.get("web_search_requests") or 0},
                       attrs={k: u[k] for k in ("service_tier", "inference_geo", "speed")
                              if u.get(k) is not None})


def read_codex(paths, endpoint=None):
    """Rollout files; one `token_usage_record` per response, keyed by `response_id`.

    `cached_input_tokens` is a subset of `input_tokens` and `reasoning_output_tokens` of
    `output_tokens` (input plus output equals `total_tokens`). `cache_write_input_tokens`
    was 0 in every local rollout, so whether it is also inside `input_tokens` is
    unverified; it is treated as inside, like the cached subset. The model comes from the
    `turn_context` of the record's turn, the provider from `session_meta`.
    """
    for f in map(Path, paths):
        provider, session, models, last_model, seen = endpoint, None, {}, None, set()
        for line in _jsonl(f):
            t, p = line.get("type"), line.get("payload") or {}
            if t == "session_meta":
                provider = endpoint or p.get("model_provider")
                session = p.get("id") or p.get("session_id")
            elif t == "turn_context":
                models[p.get("turn_id")] = p.get("model")
                last_model = p.get("model")
            elif t == "token_usage_record":
                rid = p.get("response_id")
                if rid in seen:
                    continue
                seen.add(rid)
                u = p.get("usage") or {}
                cached = u.get("cached_input_tokens") or 0
                write = u.get("cache_write_input_tokens") or 0
                out = u.get("output_tokens") or 0
                rs = u.get("reasoning_output_tokens") or 0
                thread = p.get("thread_id")
                sess = p.get("session_id") or session
                yield _row("codex", provider=provider or "openai",
                           model=models.get(p.get("turn_id")) or last_model,
                           session=sess, worker=thread if thread and thread != sess else None,
                           ts=line.get("timestamp"), source_key=rid,
                           input=(u.get("input_tokens") or 0) - cached - write,
                           cache_read=cached, cache_write_5m=write,
                           output=out - rs, reasoning=rs)


def _epoch_iso(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat(timespec="seconds")
    return value


def read_opencode(paths, endpoint=None):
    """The SQLite store, opened read-only. V2 keeps assistant and compaction turns in
    `session_message`; a worker is a child session (`session_v2.parent_id`).

    Its logged cost reproduces exactly with `reasoning` priced beside `output`, so here
    `output` already excludes reasoning. One write bucket.
    """
    for path in paths:
        db = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
        try:
            tables = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
            parent = {}
            if "session_v2" in tables:
                parent = dict(db.execute("select id, parent_id from session_v2"))

            def root(sid):
                hops = 0
                while parent.get(sid) and hops < 64:
                    sid, hops = parent[sid], hops + 1
                return sid

            sources = []
            if "session_message" in tables:
                sources.append("select id, session_id, time_created, data from session_message "
                               "where type in ('assistant', 'compaction')")
            if "message" in tables:
                sources.append("select id, session_id, time_created, data from message")
            for query in sources:
                for mid, sid, created, data in db.execute(query):
                    try:
                        m = json.loads(data)
                    except (TypeError, json.JSONDecodeError):
                        continue
                    t = m.get("tokens")
                    if not isinstance(t, dict):
                        continue
                    model = m.get("model") if isinstance(m.get("model"), dict) else {}
                    cache = t.get("cache") or {}
                    yield _row("opencode",
                               provider=endpoint or model.get("providerID") or m.get("providerID"),
                               model=model.get("id") or m.get("modelID"),
                               session=root(sid), worker=sid if parent.get(sid) else None,
                               ts=_epoch_iso(created), source_key=mid, host_cost=m.get("cost"),
                               input=t.get("input"), cache_read=cache.get("read"),
                               cache_write_5m=cache.get("write"),
                               output=t.get("output"), reasoning=t.get("reasoning"))
        finally:
            db.close()


def read_pi(paths, endpoint=None):
    """Session files (or directories of them); assistant messages carry `usage`.

    `totalTokens` equals input, output and both cache buckets on every local sample, all
    with `reasoning` 0. Whether a nonzero `reasoning` sits inside `output` is decided per
    row from that identity: when the total also adds `reasoning`, it is outside.
    """
    files = []
    for p in map(Path, paths):
        files.extend(sorted(p.rglob("*.jsonl")) if p.is_dir() else [p])
    for f in files:
        session = None
        for line in _jsonl(f):
            if line.get("type") == "session":
                session = line.get("id")
            m = line.get("message")
            if not isinstance(m, dict) or m.get("role") != "assistant":
                continue
            u = m.get("usage")
            if not isinstance(u, dict):
                continue
            inp, out = u.get("input") or 0, u.get("output") or 0
            cr, cw, rs = u.get("cacheRead") or 0, u.get("cacheWrite") or 0, u.get("reasoning") or 0
            outside = rs and u.get("totalTokens") == inp + out + cr + cw + rs
            yield _row("pi", provider=endpoint or m.get("provider"), model=m.get("model"),
                       session=session, ts=line.get("timestamp"), source_key=line.get("id"),
                       host_cost=(u.get("cost") or {}).get("total"),
                       input=inp, cache_read=cr, cache_write_5m=cw,
                       output=out if outside else out - rs, reasoning=rs)


READERS = {"claude-code": read_claude_code, "codex": read_codex,
           "opencode": read_opencode, "pi": read_pi}
UNAVAILABLE = {"copilot": "no local usage source has been verified for Copilot"}


# --------------------------------------------------------------------------- prices
def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def alias_index(catalog):
    """Normalized spelling -> canonical id, for spellings that name exactly one row."""
    owners = {}
    for m in catalog.get("models") or []:
        for spelling in set(m.get("aliases") or []) | {m["id"]}:
            owners.setdefault(norm(spelling), set()).add(m["id"])
    return {k: next(iter(v)) for k, v in owners.items() if len(v) == 1}


def load_harness_prices(path):
    """Declared endpoint prices from a harness's own provider config.

    Accepts Pi's `models.json` (`providers.<id>.models[]` with camelCase `cost`) and an
    OpenCode config (`provider.<id>.models.<id>.cost`). Returns models.dev-shaped cost
    objects keyed by provider, then by normalized model id. A model with no cost, or with
    every rate 0, declares nothing.
    """
    data = load_json(path)
    out = {}

    def keep(provider, mid, cost):
        if not isinstance(cost, dict):
            return
        c = {"input": cost.get("input"), "output": cost.get("output"),
             "cache_read": cost.get("cache_read", cost.get("cacheRead")),
             "cache_write": cost.get("cache_write", cost.get("cacheWrite"))}
        if any(v for v in c.values()):
            out.setdefault(provider, {})[norm(mid)] = {k: v for k, v in c.items() if v is not None}

    for pid, prov in (data.get("providers") or {}).items():
        for m in prov.get("models") or []:
            keep(pid, m.get("id") or "", m.get("cost"))
    for pid, prov in (data.get("provider") or {}).items():
        for mid, m in (prov.get("models") or {}).items():
            keep(pid, mid, (m or {}).get("cost"))
    return out


class Pricer:
    def __init__(self, prices, catalog, rules, harness_prices=None):
        self.prices = prices.get("models") or {}
        self.revision = {"prices": prices.get("revision"),
                         "models_dev_raw_sha256": prices.get("models_dev_raw_sha256"),
                         "rules": rules.get("revision")}
        self.aliases = alias_index(catalog)
        self.creator = {m["id"]: m.get("creator") for m in catalog.get("models") or []}
        self.rules = rules.get("rules") or []
        self.harness = harness_prices or {}

    def resolve(self, provider, model):
        """(cost object, endpoint, basis, canonical id, approximations) or a reason."""
        if not model:
            return None, "the log names no model"
        canonical = self.aliases.get(norm(model))
        declared = (self.harness.get(provider) or {}).get(norm(model))
        if declared:
            return (declared, provider, "harness-config", canonical, []), None
        if not canonical:
            return None, f"model {model!r} is not in the catalog"
        endpoints = (self.prices.get(canonical) or {}).get("endpoints") or {}
        creator = self.creator.get(canonical)
        for endpoint, basis in ((provider, "endpoint"), (creator, "creator-endpoint")):
            spellings = endpoints.get(endpoint)
            if not spellings:
                continue
            approx = [] if basis == "endpoint" else [
                f"endpoint {provider!r} has no price; priced at the creator's endpoint "
                f"{endpoint!r}"]
            # One model can be sold under several names at one endpoint at different
            # prices (a `-free` variant at 0): the logged name decides, then the canonical.
            by_norm = {norm(mid): mid for mid in spellings}
            bare = canonical.split("/", 1)[-1]
            mid = by_norm.get(norm(model)) or by_norm.get(norm(bare))
            if not mid:
                mid = min(spellings, key=lambda s: (len(s), s))
                approx.append(f"{model!r} is not listed at {endpoint!r}; priced as {mid!r}")
            return (spellings[mid], endpoint, basis, canonical, approx), None
        return None, f"no price for {canonical} at {provider!r} or its creator"

    @staticmethod
    def _tier(cost, prompt):
        """The highest context tier the prompt passes; tiers replace the rates they list."""
        tiers = [t for t in cost.get("tiers") or []
                 if (t.get("tier") or {}).get("type") == "context"]
        if not tiers and isinstance(cost.get("context_over_200k"), dict):
            tiers = [dict(cost["context_over_200k"], tier={"type": "context", "size": 200_000})]
        passed = [t for t in tiers if prompt > t["tier"]["size"]]
        return max(passed, key=lambda t: t["tier"]["size"]) if passed else None

    def _matches(self, rule, endpoint, canonical, row):
        if rule.get("provider") not in (None, endpoint):
            return False
        bare = (canonical or row.get("model") or "").split("/", 1)[-1]
        models = rule.get("models")
        if models and not any(fnmatch.fnmatchcase(bare, pat) for pat in models):
            return False
        when = rule.get("when") or {}
        timed = {"utc_days", "utc_hours", "since", "until"}
        for key, want in when.items():
            if key not in timed and row.get("attrs", {}).get(key) != want:
                return False
        if timed & set(when):
            try:
                ts = datetime.fromisoformat(str(row.get("ts")).replace("Z", "+00:00"))
            except ValueError:
                return False
            ts = ts.astimezone(timezone.utc)
            day = ts.date().isoformat()
            if "since" in when and day < when["since"]:
                return False
            if "until" in when and day >= when["until"]:
                return False
            if "utc_days" in when and ts.strftime("%A").lower() not in when["utc_days"]:
                return False
            if "utc_hours" in when:
                start, end = when["utc_hours"]
                minutes = ts.hour * 60 + ts.minute
                if not (start * 60 <= minutes < end * 60):
                    return False
        return True

    def price(self, row):
        found, reason = self.resolve(row.get("provider"), row.get("model"))
        if not found:
            return dict(row, price={"priced": False, "reason": reason})
        cost, endpoint, basis, canonical, approx = found
        prompt = sum(row[b] for b in PROMPT_BUCKETS)
        tier = self._tier(cost, prompt)
        src = dict(cost, **{k: v for k, v in (tier or {}).items() if k != "tier"})
        rates = {"input": src.get("input"), "output": src.get("output"),
                 "cache_read": src.get("cache_read"), "cache_write_5m": src.get("cache_write"),
                 "cache_write_1h": None, "reasoning": src.get("reasoning")}
        applied = []
        matching = [r for r in self.rules if self._matches(r, endpoint, canonical, row)]
        for r in matching:
            if r.get("kind") == "rate":
                rates[r["bucket"]] = r["usd_per_million"]
                applied.append(r["id"])
        for r in matching:
            if r.get("kind") == "bucket_rate" and rates.get(r["of"]) is not None:
                rates[r["bucket"]] = rates[r["of"]] * r["multiplier"]
                applied.append(r["id"])
        if rates["input"] is None or rates["output"] is None:
            return dict(row, price={"priced": False, "endpoint": endpoint, "basis": basis,
                                    "reason": "the endpoint publishes no input or output rate"})
        # Reasoning without its own rate is output, as every provider bills it; the other
        # three fallbacks are assumptions, and a row that needed one says so.
        if rates["reasoning"] is None:
            rates["reasoning"] = rates["output"]
        for bucket, of, note in (
                ("cache_write_5m", "input", "cache write billed at the input rate"),
                ("cache_write_1h", "cache_write_5m", "1-hour cache write billed at the "
                                                     "5-minute rate"),
                ("cache_read", "input", "cache read billed at the input rate: an upper bound")):
            if rates[bucket] is None:
                rates[bucket] = rates[of]
                if row[bucket]:
                    approx.append(note)
        for r in matching:
            if r.get("kind") == "multiplier":
                for b in r.get("buckets") or BUCKETS:
                    rates[b] *= r["multiplier"]
                applied.append(r["id"])
        usd = {b: row[b] * rates[b] / 1e6 for b in BUCKETS}
        per_request = {}
        for r in matching:
            if r.get("kind") == "per_request":
                n = (row.get("requests") or {}).get(r["request"]) or 0
                if n:
                    per_request[r["request"]] = n * r["usd_per_request"]
                    applied.append(r["id"])
        total = sum(usd.values()) + sum(per_request.values())
        return dict(row, price={"priced": True, "endpoint": endpoint, "basis": basis,
                                "canonical": canonical,
                                "tier": tier["tier"]["size"] if tier else None,
                                "rates_usd_per_million": rates, "usd": usd,
                                "per_request_usd": per_request, "total_usd": total,
                                "rules": applied, "approximations": approx})


# --------------------------------------------------------------------------- report
def summarize(priced_rows, revision):
    groups, totals = {}, {"rows": 0, "priced": 0, "unpriced": 0, "total_usd": 0.0,
                          "tokens": {b: 0 for b in BUCKETS}, "usd": {b: 0.0 for b in BUCKETS},
                          "per_request_usd": 0.0, "host_cost_usd": 0.0, "host_cost_rows": 0,
                          "approximate_rows": 0}
    unpriced_reasons = {}
    for r in priced_rows:
        p = r["price"]
        key = f"{r['host']}|{p.get('endpoint') or r.get('provider')}|{r.get('model')}"
        g = groups.setdefault(key, {"host": r["host"], "endpoint": p.get("endpoint") or
                                    r.get("provider"), "model": r.get("model"),
                                    "canonical": p.get("canonical"), "basis": p.get("basis"),
                                    "rows": 0, "tokens": {b: 0 for b in BUCKETS},
                                    "total_usd": 0.0 if p.get("priced") else None,
                                    "host_cost_usd": None})
        for t in (g, totals):
            t["rows"] += 1
            for b in BUCKETS:
                t["tokens"][b] += r[b]
        if r.get("host_cost") is not None:
            totals["host_cost_usd"] += r["host_cost"]
            totals["host_cost_rows"] += 1
            g["host_cost_usd"] = (g["host_cost_usd"] or 0.0) + r["host_cost"]
        if p.get("priced"):
            totals["priced"] += 1
            g["total_usd"] += p["total_usd"]
            totals["total_usd"] += p["total_usd"]
            totals["per_request_usd"] += sum(p["per_request_usd"].values())
            for b in BUCKETS:
                totals["usd"][b] += p["usd"][b]
            if p["approximations"]:
                totals["approximate_rows"] += 1
        else:
            totals["unpriced"] += 1
            unpriced_reasons[p["reason"]] = unpriced_reasons.get(p["reason"], 0) + 1
    status = "complete" if totals["unpriced"] == 0 else "partial"
    if totals["rows"] == 0:
        status = "empty"
    return {"status": status, "price_sources": revision, "totals": totals,
            "unpriced_reasons": unpriced_reasons,
            "by_model": sorted(groups.values(), key=lambda g: -(g["total_usd"] or 0))}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="usage_pricing.py", description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=("summary", "rows"))
    ap.add_argument("--host", required=True, choices=sorted(READERS) + sorted(UNAVAILABLE))
    ap.add_argument("--source", action="append", default=[],
                    help="log file, session directory or database; repeatable")
    ap.add_argument("--endpoint", help="override the endpoint the log implies")
    ap.add_argument("--harness-prices", help="Pi models.json or OpenCode config declaring "
                                             "prices for endpoints models.dev does not list")
    ap.add_argument("--session", help="keep only this session id")
    ap.add_argument("--since", help="keep rows at or after this ISO timestamp")
    ap.add_argument("--prices", default=str(DEFAULT_PRICES))
    ap.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    ap.add_argument("--rules", default=str(DEFAULT_RULES))
    args = ap.parse_args(argv)

    if args.host in UNAVAILABLE:
        print(json.dumps({"status": "unavailable", "host": args.host,
                          "reason": UNAVAILABLE[args.host]}))
        return 3
    if not args.source:
        print(json.dumps({"status": "failed", "reason": "no --source given"}))
        return 2
    missing = [s for s in args.source if not Path(s).exists()]
    if missing:
        print(json.dumps({"status": "failed", "reason": "source not found", "paths": missing}))
        return 2
    pricer = Pricer(load_json(args.prices), load_json(args.catalog), load_json(args.rules),
                    load_harness_prices(args.harness_prices) if args.harness_prices else None)
    rows = []
    for row in READERS[args.host](args.source, args.endpoint):
        if args.session and args.session not in (row["session"], row["worker"]):
            continue
        if args.since and str(row.get("ts") or "") < args.since:
            continue
        rows.append(pricer.price(row))
    if args.command == "rows":
        for r in rows:
            print(json.dumps(r, sort_keys=True))
    else:
        print(json.dumps(summarize(rows, pricer.revision), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
