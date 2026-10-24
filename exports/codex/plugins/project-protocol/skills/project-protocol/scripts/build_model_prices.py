#!/usr/bin/env python3
"""Build `model-prices.json`: every price dimension of the endpoints that serve catalog models.

`model-catalog.json` keeps one indicative price per model, because routing reads nothing
else and carrying every endpoint's price there cost ~1.9 MB. Pricing measured usage needs
the opposite (ADR-0003): the rate of the endpoint that served a response, with every
dimension the provider publishes, since a context tier, a reasoning rate or a cache rate
changes the figure. So this file sits beside the catalog, keyed by the catalog's canonical
ids, and keeps the full models.dev `cost` object (input, output, cache_read, cache_write,
reasoning, context `tiers`, `context_over_200k`, audio) for a bounded set of endpoints:

- the model creator's own endpoint, which is also the fallback for an unlisted endpoint;
- the catalog's selected endpoint;
- the resellers named by `--keep-provider` (default `KEEP`), where hosts commonly send
  requests.

Measured on the 2026-10-24 response: 5813 priced endpoints serve catalog models; this
set keeps about one in six. What models.dev does not publish (a 1-hour cache write, a
region multiplier, a time window) is not guessed here: it lives in `price-rules.json`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_model_catalog import MODELS_DEV_URL, norm  # noqa: E402

SCHEMA = "daodan/model-prices/v1"
KEEP = ("openrouter", "opencode", "amazon-bedrock", "google-vertex",
        "google-vertex-anthropic", "azure")


def build(models_dev, catalog, keep):
    rows = {m["id"]: m for m in catalog.get("models") or []}
    owners = {}
    for m in rows.values():
        for spelling in set(m.get("aliases") or []) | {m["id"]}:
            owners.setdefault(norm(spelling), set()).add(m["id"])
    by_name = {k: next(iter(v)) for k, v in owners.items() if len(v) == 1}

    candidates, attached_by_name = {}, 0
    for provider, prov in models_dev.items():
        for mid, entry in (prov.get("models") or {}).items():
            cost = entry.get("cost")
            if not isinstance(cost, dict) or cost.get("input") is None:
                continue
            canonical = entry.get("canonical_model_id")
            exact = canonical in rows
            if not exact:
                canonical = by_name.get(norm(mid))
                if not canonical:
                    continue
                attached_by_name += 1
            row = rows[canonical]
            if provider in {row.get("creator"), row.get("selected_endpoint")} | set(keep):
                candidates.setdefault((canonical, provider), {})[mid] = cost
    # Every spelling stays: one endpoint sells one model under several names at different
    # prices (measured: `deepseek-v4.1-flash-free` at 0 beside the paid spelling), and the
    # logged name is what picks the rate.
    models = {}
    for (canonical, provider), spellings in sorted(candidates.items()):
        slot = models.setdefault(canonical, {"creator": rows[canonical].get("creator"),
                                             "endpoints": {}})
        slot["endpoints"][provider] = spellings
    return models, attached_by_name


def main(argv=None):
    ap = argparse.ArgumentParser(prog="build_model_prices.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--catalog", required=True, help="the model-catalog.json to key by")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--from-response", help="an already downloaded models.dev response")
    ap.add_argument("--keep-provider", action="append",
                    help=f"reseller endpoints to keep; default {', '.join(KEEP)}")
    ap.add_argument("--revision", type=int, default=1)
    args = ap.parse_args(argv)

    if args.from_response:
        raw, retrieved = Path(args.from_response).read_bytes(), None
    elif args.fetch:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(MODELS_DEV_URL,
                                     headers={"User-Agent": "daodan-model-prices/1"})
        try:
            with opener.open(req, timeout=90) as r:
                raw = r.read(64 * 1024 * 1024)
        except Exception as exc:
            print(json.dumps({"status": "failed", "reason": f"models.dev unreachable: {exc}"}))
            return 1
        retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    else:
        print(json.dumps({"status": "failed",
                          "reason": "network egress is opt-in: pass --fetch or --from-response"}))
        return 1

    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    models, by_name = build(json.loads(raw.decode("utf-8")), catalog,
                            tuple(args.keep_provider or KEEP))
    doc = {"schema": SCHEMA, "revision": args.revision, "retrieved_at": retrieved,
           "models_dev_raw_sha256": hashlib.sha256(raw).hexdigest(),
           "catalog_revision": catalog.get("revision"),
           "kept_providers": sorted(args.keep_provider or KEEP),
           "units": "USD per million tokens, as models.dev publishes them; tiers apply "
                    "when a request's prompt exceeds their size",
           "models": models}
    body = json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_bytes(body)
    tmp.replace(out)
    endpoints = sum(len(m["endpoints"]) for m in models.values())
    print(json.dumps({"status": "written", "out": str(out), "bytes": len(body),
                      "models": len(models), "endpoints": endpoints,
                      "attached_by_name": by_name,
                      "without_creator_endpoint": sorted(
                          c for c, m in models.items() if m["creator"] not in m["endpoints"])
                      [:20]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
