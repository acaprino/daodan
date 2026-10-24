"""Harvest model FACTS from an allowlisted public catalog into a local registry file.

This script collects the layer that a harness may not expose: context window, output
limit, per-1M-token rates, modality and tool/reasoning support for models the active
harness does not list. It is the fallback fact source ``tier_router.py`` consults when a
screened model has no harness-declared value.

What it deliberately does NOT contain, and must never grow:

- **No capability, quality or tier claim.** OpenRouter and similar catalogs publish
  prices and limits, not rankings. The deliberation recorded in
  ``.tritech/local/moe/2026-10-22-tier-banding/answer.md`` established that metadata of
  this kind supports economic cost bands and eligibility gates only. Tier ordering stays
  in the human-maintained policy file, never here.
- **No authority over a harness-declared value.** Measured on 2026-10-22 against the
  active ``tri-llm-gateway`` catalog and ``https://openrouter.ai/api/v1/models``
  (468 models, 68 providers), 17 of 23 local models match an OpenRouter entry by
  normalized name, and the harvested prices disagree with what the gateway actually
  charges by 1.1x (``gemini-3.8-flash``: 0.825 vs 0.75), 1.8x on cache read
  (``deepseek-v4-pro``: 0.0796 vs 0.044), 2x on cache read (``claude-sonnet-5.5``: 0.1
  vs 0.2) and 12.5x on input (``kimi-k3``: 0.239 vs 3). Context windows agreed on 16 of
  17 and disagreed on ``kimi-k3`` (1048576 vs 1000000). A harvested number is therefore
  a *fallback for absent values*, never a correction of a present one.

Three traps in the source data this script handles explicitly rather than silently:

1. ``pricing`` values are strings in **USD per token**, not per million. They are
   converted here so the registry shares the harness convention.
2. Ids carry a ``:batch`` or ``:free`` suffix for a different service tier at a different
   price (``anthropic/claude-fable-5.1`` is 10/50 while ``...:batch`` is 5/25). These are
   kept as separate records with ``service_tier`` set, never merged into the base model.
3. Ids prefixed ``~`` are **floating aliases** (``~openai/gpt-luna-latest``), not pinned
   artifacts. They are flagged, because binding a run to a floating alias is not
   reproducible. 78 of 468 records also carry ``pricing.overrides`` (context-size
   tiering), for which the flat ``prompt`` rate is not the effective price; those are
   flagged ``price_is_tiered``.

Nothing is written into the repository. The caller chooses ``--out``, which belongs in a
run root or the harness cache, so a harvested snapshot is never committed as a vendored
copy of a third-party service and never goes stale inside the kernel.

Standard library only. Network egress is opt-in: without ``--fetch`` the script refuses
rather than reaching out.

Usage:

    python registry_fetch.py --out FILE.json --fetch
        [--source openrouter] [--timeout 45] [--max-bytes 8388608]
        [--from-response FILE.json]     # re-reduce an already downloaded response
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "daodan/model-fact-registry/v1"

# Allowlisted sources. A caller may select one by key; it may never pass a URL. Letting a
# URL in would turn the registry into an injection vector, because whatever it returns
# steers which model an agent binds.
SOURCES = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/models",
        "records_path": ["data"],
        "attribution": "Model facts from the OpenRouter public model list "
                       "(https://openrouter.ai/models). Prices and limits are the "
                       "upstream service's, re-expressed per 1M tokens; they are not "
                       "Daodan measurements and carry no capability claim.",
    },
}

DEFAULT_TIMEOUT_S = 45
DEFAULT_MAX_BYTES = 8 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects: the allowlist names one host, and a redirect leaves it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fail(reason, **extra):
    out = {"schema": SCHEMA, "status": "failed", "reason": reason}
    out.update(extra)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1


def fetch_raw(url, timeout_s, max_bytes):
    """GET one allowlisted URL. Returns (bytes, None) or (None, reason)."""
    if not url.startswith("https://"):
        return None, f"refusing non-HTTPS source: {url}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "daodan-model-fact-registry/1",
                      "Accept": "application/json"})
    # A system proxy must not silently sit between this script and the allowlisted host,
    # and a redirect must not move the request off it.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=timeout_s) as response:
            raw = response.read(max_bytes + 1)
    except Exception as exc:                      # noqa: BLE001 - reported, not guessed
        return None, f"{exc.__class__.__name__}: {exc}"
    if len(raw) > max_bytes:
        return None, f"response exceeds --max-bytes {max_bytes}; truncated read discarded"
    return raw, None


def _rate(value):
    """USD per token as a string -> USD per 1M tokens as a float, or None."""
    if value is None:
        return None
    try:
        return round(float(value) * 1_000_000, 8)
    except (TypeError, ValueError):
        return None


def _dig(payload, path):
    node = payload
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def reduce_records(records, source_key):
    """Project the upstream shape onto the registry schema, keeping provenance per row."""
    models, skipped = [], 0
    for raw in records:
        if not isinstance(raw, dict):
            skipped += 1
            continue
        mid = raw.get("id")
        if not isinstance(mid, str) or not mid:
            skipped += 1
            continue
        base, _, suffix = mid.partition(":")
        pricing = raw.get("pricing") or {}
        params = raw.get("supported_parameters") or []
        arch = raw.get("architecture") or {}
        top = raw.get("top_provider") or {}
        models.append({
            "id": mid,
            "base_id": base,
            "service_tier": suffix or "base",
            "floating_alias": base.startswith("~"),
            "canonical_slug": raw.get("canonical_slug"),
            "provider": base.lstrip("~").split("/", 1)[0] if "/" in base else None,
            "name": raw.get("name"),
            "context_window": raw.get("context_length"),
            "provider_context_window": top.get("context_length"),
            "output_limit": top.get("max_completion_tokens"),
            "cost_usd_per_million_tokens": {
                "input": _rate(pricing.get("prompt")),
                "output": _rate(pricing.get("completion")),
                "cache_read": _rate(pricing.get("input_cache_read")),
                "cache_write": _rate(pricing.get("input_cache_write")),
                "cache_write_1h": _rate(pricing.get("input_cache_write_1h")),
                "internal_reasoning": _rate(pricing.get("internal_reasoning")),
                "image": _rate(pricing.get("image")),
                "audio": _rate(pricing.get("audio")),
                "web_search": _rate(pricing.get("web_search")),
            },
            "price_is_tiered": bool(pricing.get("overrides")),
            "price_tiered_note": (
                "pricing.overrides present: the flat input rate is not the effective "
                "price at every context size" if pricing.get("overrides") else None),
            "modality": arch.get("modality"),
            "input_modalities": arch.get("input_modalities") or [],
            "output_modalities": arch.get("output_modalities") or [],
            "capabilities": {"tools": "tools" in params,
                             "reasoning": bool(raw.get("reasoning"))
                                          or "reasoning" in params
                                          or "include_reasoning" in params,
                             "structured_outputs": "response_format" in params},
            "supported_parameters": sorted(params),
            "knowledge_cutoff": raw.get("knowledge_cutoff"),
            "created": raw.get("created"),
            "expiration_date": raw.get("expiration_date"),
            "source": source_key,
            "evidence": "harvested",
        })
    models.sort(key=lambda m: (m["id"], m["service_tier"]))
    return models, skipped


def build(args):
    source = SOURCES.get(args.source)
    if source is None:
        return _fail(f"unknown --source {args.source!r}; allowlisted: "
                     f"{', '.join(sorted(SOURCES))}", allowlisted=sorted(SOURCES))

    if args.from_response:
        raw = Path(args.from_response).read_bytes()
        origin = f"local response file {args.from_response}"
    elif args.fetch:
        raw, err = fetch_raw(source["url"], args.timeout, args.max_bytes)
        if raw is None:
            # Offline is a stated gap, never a silent empty registry.
            return _fail(f"source unreachable: {err}", source=args.source,
                         url=source["url"],
                         consequence="no registry written; tier_router.py must fall back "
                                     "to harness-declared values and report `unknown`")
        origin = source["url"]
    else:
        return _fail("network egress is opt-in: pass --fetch to reach the allowlisted "
                     "source, or --from-response FILE to reduce an existing download")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _fail(f"response is not UTF-8 JSON: {exc.__class__.__name__}",
                     source=args.source, origin=origin)

    records = _dig(payload, source["records_path"])
    if not isinstance(records, list):
        return _fail(f"records not found at {'.'.join(source['records_path'])}",
                     source=args.source, origin=origin)

    models, skipped = reduce_records(records, args.source)
    body = json.dumps(models, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8")
    registry = {
        "schema": SCHEMA,
        "status": "built",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": args.source,
        "origin": origin,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_bytes": len(raw),
        "upstream_total_count": payload.get("total_count"),
        "models_sha256": hashlib.sha256(body).hexdigest(),
        "model_count": len(models),
        "records_skipped": skipped,
        "counts": {
            "providers": len({m["provider"] for m in models if m["provider"]}),
            "base_models": len({m["base_id"] for m in models}),
            "service_tiers": {t: sum(1 for m in models if m["service_tier"] == t)
                              for t in sorted({m["service_tier"] for m in models})},
            "floating_aliases": sum(1 for m in models if m["floating_alias"]),
            "price_is_tiered": sum(1 for m in models if m["price_is_tiered"]),
            "with_priced_input": sum(1 for m in models
                                     if m["cost_usd_per_million_tokens"]["input"] is not None),
            "with_context_window": sum(1 for m in models if m["context_window"]),
            "with_tools": sum(1 for m in models if m["capabilities"]["tools"]),
        },
        "semantics": {
            "prices": "USD per 1M tokens, converted from the source's per-token strings",
            "authority": "fallback only: a harness-declared value always outranks a "
                         "harvested one, and the disagreement is recorded",
            "not_included": ["capability", "quality", "tier", "frontier ordering"],
            "identity": "rows are keyed by the source's own id; matching them to a "
                        "harness model id is a separate, explicitly labelled step",
        },
        "attribution": source["attribution"],
        "models": models,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_bytes(json.dumps(registry, indent=1, ensure_ascii=False,
                               sort_keys=True).encode("utf-8"))
    tmp.replace(out)                            # atomic: never a half-written registry
    summary = {k: v for k, v in registry.items() if k != "models"}
    summary["out"] = str(out)
    summary["out_bytes"] = out.stat().st_size
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="registry_fetch.py",
                                description="Harvest model facts from an allowlisted catalog.")
    p.add_argument("--out", required=True, help="registry JSON to write (never inside the repo)")
    p.add_argument("--source", default="openrouter", choices=sorted(SOURCES))
    p.add_argument("--fetch", action="store_true", help="opt in to network egress")
    p.add_argument("--from-response", help="reduce an already downloaded response instead")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    p.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    args = p.parse_args(argv)
    return build(args)


if __name__ == "__main__":
    sys.exit(main())
