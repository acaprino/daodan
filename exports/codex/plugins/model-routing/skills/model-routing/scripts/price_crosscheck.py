#!/usr/bin/env python3
"""Compare `model-prices.json` with LiteLLM and OpenRouter, to say what to verify by hand.

Neither aggregator is a price source here: models.dev is, and an official pricing page
settles a disagreement. They are a second and a third reading of the same public facts,
and on 2026-10-24 both carried dimensions models.dev lacks: LiteLLM a 1-hour cache write,
priority, flex, batch and context-tier rates; OpenRouter a 1-hour cache write and
`overrides` by UTC day and hour (DeepSeek's peak and off-peak prices). So a refresh runs
this, and every line it prints is either a models.dev error to report or a rule that
`price-rules.json` still lacks. Nothing here writes into the repository.

Matching is by endpoint and normalized model name only: LiteLLM's first-party rows
against the creator's endpoint, OpenRouter against models.dev's `openrouter` endpoint.
An unmatched model is counted, never guessed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_model_catalog import norm  # noqa: E402

# models.dev creator endpoint -> LiteLLM `litellm_provider` of the same first-party API.
LITELLM_PROVIDER = {"anthropic": "anthropic", "openai": "openai", "xai": "xai",
                    "deepseek": "deepseek", "google": "gemini", "moonshotai": "moonshot",
                    "mistral": "mistral", "alibaba": "dashscope", "zhipuai": "zai",
                    "minimax": "minimax", "xiaomi": "xiaomi_mimo"}
FIELDS = {"input": "input_cost_per_token", "output": "output_cost_per_token",
          "cache_read": "cache_read_input_token_cost",
          "cache_write": "cache_creation_input_token_cost"}
OPENROUTER = {"input": "prompt", "output": "completion", "cache_read": "input_cache_read",
              "cache_write": "input_cache_write"}
EXTRA_SUFFIXES = ("_above_1hr", "_priority", "_flex", "_batches", "_cache_hit")


def close(a, b):
    return a is not None and b is not None and abs(a - b) <= max(abs(a), abs(b)) * 0.01 + 1e-12


def crosscheck(prices, litellm, openrouter):
    lite = {}
    for key, v in (litellm or {}).items():
        if isinstance(v, dict) and v.get("litellm_provider"):
            lite.setdefault((v["litellm_provider"], norm(key)), (key, v))
    orouter = {}
    for m in (openrouter or {}).get("data") or []:
        ns, _, rest = m.get("id", "").partition("/")
        orouter.setdefault((ns, norm(rest)), m)

    findings, matched = [], {"litellm": 0, "openrouter": 0}
    for canonical, m in sorted((prices.get("models") or {}).items()):
        creator = m.get("creator")
        spellings = (m.get("endpoints") or {}).get(creator) or {}
        bare = canonical.split("/", 1)[-1]
        ours = spellings.get(bare) or (next(iter(spellings.values())) if spellings else None)
        if not ours:
            continue
        hit = lite.get((LITELLM_PROVIDER.get(creator), norm(bare)))
        if hit:
            matched["litellm"] += 1
            key, v = hit
            for ours_k, their_k in FIELDS.items():
                theirs = v.get(their_k)
                theirs = theirs * 1e6 if isinstance(theirs, (int, float)) else None
                if ours.get(ours_k) is not None and theirs is not None \
                        and not close(ours[ours_k], theirs):
                    findings.append({"model": canonical, "source": "litellm", "key": key,
                                     "field": ours_k, "models_dev": ours[ours_k],
                                     "other": round(theirs, 6)})
            extra = sorted(k for k in v if "cost" in k and k.endswith(EXTRA_SUFFIXES))
            tiers = sorted(k for k in v if "_above_" in k and k.endswith("_tokens"))
            if extra or tiers:
                findings.append({"model": canonical, "source": "litellm", "key": key,
                                 "field": "dimensions-only-there", "other": extra + tiers})
        # OpenRouter is its own endpoint: it is compared with models.dev's `openrouter`
        # entry, never with the creator's price, which it resells at its own rate.
        o = orouter.get((creator, norm(bare)))
        if o:
            matched["openrouter"] += 1
            p = o.get("pricing") or {}
            resale = (m.get("endpoints") or {}).get("openrouter") or {}
            listed = next((c for k, c in resale.items() if norm(k) == norm(o["id"])), None)
            for ours_k, their_k in OPENROUTER.items():
                try:
                    theirs = float(p[their_k]) * 1e6 if their_k in p else None
                except (TypeError, ValueError):
                    theirs = None
                if listed and listed.get(ours_k) is not None and theirs is not None \
                        and not close(listed[ours_k], theirs):
                    findings.append({"model": canonical, "source": "openrouter", "key": o["id"],
                                     "field": ours_k, "models_dev": listed[ours_k],
                                     "other": round(theirs, 6)})
            only = sorted(k for k in ("input_cache_write_1h", "internal_reasoning", "overrides")
                          if p.get(k) not in (None, "0", 0, []))
            if only:
                findings.append({"model": canonical, "source": "openrouter", "key": o["id"],
                                 "field": "dimensions-only-there", "other": only})
    return {"matched": matched, "findings": findings}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="price_crosscheck.py")
    ap.add_argument("--prices", required=True)
    ap.add_argument("--litellm", help="model_prices_and_context_window.json from BerriAI/litellm")
    ap.add_argument("--openrouter", help="the response of https://openrouter.ai/api/v1/models")
    ap.add_argument("--out", help="write the report here instead of stdout")
    args = ap.parse_args(argv)
    load = lambda p: json.loads(Path(p).read_text(encoding="utf-8")) if p else None  # noqa: E731
    report = crosscheck(load(args.prices), load(args.litellm), load(args.openrouter))
    body = json.dumps(report, indent=1, sort_keys=True)
    if args.out:
        Path(args.out).write_text(body + "\n", encoding="utf-8")
        print(json.dumps({"status": "written", "out": args.out, "matched": report["matched"],
                          "findings": len(report["findings"])}))
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
