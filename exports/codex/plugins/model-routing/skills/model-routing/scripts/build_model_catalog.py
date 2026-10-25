"""Build `model-catalog.json`: the routing plugin's PRIMARY source of model knowledge.

The router agent must not reconstruct model knowledge at runtime. It reads this catalog
for identity, taxonomy, indicative prices, input/output windows, input/output
capabilities, per-work-type aptitudes and **tier**, then intersects it with what the
active harness actually exposes and assigns per tier. This script is the generator; the
catalog is the artifact.

Four separations this file exists to keep, because flattening them loses information that
was measured to differ:

- **canonical model identity** — one row per model, effort-free. models.dev publishes one
  entry per provider endpoint (109 for `moonshotai/kimi-k3`, 48 for
  `anthropic/claude-opus-5-5`), and `canonical_model_id` collapses them to one identity:
  it is `<lab>/<model>` and it agrees across every aggregator. A row built from the
  endpoint instead of the identity produced 500 rows over 282 identities, named an
  aggregator as the `creator`, and attached one benchmark 21 times. Our harness ids never
  carry a thinking level; Arena board names do (`claude-opus-5.5-max`). ``opus-5-5-max``
  IS ``opus-5-5``, and the tier is invariant to effort.
- **endpoint** — prices are endpoint-specific, not model properties. `gemini-3.8-flash`
  was measured at 0.75 (this gateway), 1.5 (models.dev) and 0.825 (OpenRouter) USD per 1M
  input tokens; Anthropic `cache_write` is exactly 1.6x on this gateway against models.dev
  and OpenRouter, which agree with each other. So the row carries a selected indicative
  price plus every known endpoint, and the harness always wins at runtime.
- **benchmark** — a score belongs to a board, a date and a configuration, not to a model.
  Boards are separate populations: taking the maximum score across them compares numbers
  that are not on one scale, so the tier evidence is chosen by an explicit board priority
  and the per-board observations live under `aptitudes`.
- **work type** — an ELO on `code` does not rank a model for a vision task. Measured on
  the pinned 2026-10-07 snapshot: `code` rank 1 is `claude-opus-5.5-max` with
  `claude-fable-5.1-max` 5th, while `agent` rank 1 is Claude Fable 5.1 (Max). `aptitudes`
  records one observation per board per model, so the router can rank inside the intent
  the classifier emitted.

Tier is **declared here**, not derived. Verified across models.dev (9146 entries), LiteLLM
(4245) and OpenRouter (468): none carries a quality, score, rank or tier field. Price does
not rank capability either — `gpt-6-astra-max` and `claude-fable-5.1-max` share the price
structure 10/50 and sit 43 ELO and 3 ranks apart on the same board, while the cheaper
`claude-opus-5.5-max` (4/20) outscores the 2.5x dearer `claude-fable-5.1-max` by 69.
Spearman rho(price, score) is 0.718 inside one board (n=20) and -0.11 pooled (n=58). So
every tier here carries `tier_evidence` with method, confidence and reasoning, and a tier
is never inferred from a name alone.

Standard library only. Network egress is opt-in (`--fetch`).

Usage:
    python build_model_catalog.py --out FILE.json --fetch [--limit 500]
        [--models-dev-url URL] [--benchmark FILE.json] [--harness-config FILE.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_capabilities import normalize  # noqa: E402  one reader of capabilities

SCHEMA = "daodan/model-catalog/v1"
MODELS_DEV_URL = "https://models.dev/api.json"

# --------------------------------------------------------------------------- tiers
# Declared from knowledge of each lab's product segmentation, checked against the pinned
# Arena `code` board where it covers the model. Order matters: first match wins.
TIER3_IDS = {
    "claude-opus-5-5", "claude-opus-5.5", "claude-fable-5-1", "claude-fable-5.1",
    "claude-fable-5", "gpt-6-astra", "gpt-6.1-sol", "gpt-5.5-pro", "gpt-5.5",
    "gpt-5.4-pro", "gemini-4-argon", "gemini-3.1-pro", "gemini-3-pro", "grok-4.7",
    "qwen3.8-max-prime", "claude-opus-4-8", "claude-opus-4.8", "o4-pro",
}
TIER2_IDS = {
    "claude-sonnet-5-5", "claude-sonnet-5.5", "claude-sonnet-5", "claude-opus-5",
    "gpt-6-sol", "gpt-6.1-sol-lite", "gpt-5.2", "gpt-5.1", "gpt-5", "gemini-3.8-flash",
    "gemini-3.7-flash", "gemini-3.6-flash", "grok-4.6", "grok-4.5", "grok-code",
    "kimi-k3", "kimi-k2.7-code", "kimi-k2.6", "kimi-k2.5", "qwen3.8-max", "qwen3-coder",
    "deepseek-v4-pro", "deepseek-r1", "mistral-large-4", "mistral-medium-3",
    "minimax-m3", "minimax-m2.7", "minimax-m2.5", "glm-5.3", "glm-5.2", "glm-5.1",
    "glm-5", "glm-4.7", "muse-wonder", "muse-spark-1.3", "mimo-v2.6-pro",
    "abliteration-abliterated-model-large-v2", "hy4-preview",
}
TIER1_IDS = {
    "claude-haiku-5-5", "claude-haiku-5.5", "claude-haiku-4-5", "gpt-6-luna",
    "glm-flash-latest", "glm-5.3-flash", "glm-4.7-flash", "glm-4.7-flashx",
    "glm-4.5-air", "deepseek-v4.1-flash", "deepseek-v4-flash", "gemini-3.5-flash-lite",
    "venice-uncensored-1-2", "venice-uncensored-role-play", "qwen3.8-flash-next",
    "olafangensan-glm-4.7-flash-heretic", "mimo-v2.6-flash",
}
# Family-level rules, applied after exact ids. Longest prefix wins.
FAMILY_TIER = [
    ("claude-opus", 3), ("claude-fable", 3), ("gpt-astra", 3), ("gpt-sol", 2),
    ("claude-sonnet", 2), ("claude-haiku", 1), ("gemini-flash", 2), ("gemini", 2),
    ("gpt", 2), ("grok", 2), ("kimi-k3", 2), ("kimi", 2), ("qwen", 2), ("glm", 2),
    ("deepseek-flash", 1), ("deepseek", 2), ("minimax", 2), ("muse", 2), ("mimo", 1),
    ("mistral", 2), ("llama", 2), ("nemotron", 1), ("longcat", 1), ("ling", 1),
]
# Name-pattern rules. A `-flash`/`-lite`/`-mini`/`-nano` suffix is an economy class in
# every lab's naming, so it is evidence, not a guess — but it never overrides an exact id
# or a declared family, and it is recorded as `derived` with low confidence.
ECONOMY_PATTERN = re.compile(
    r"(?:^|[\s._/-])(haiku|flash|lite|mini|nano|tiny|air|fast|small|free)(?:$|[\s._/-])")
FRONTIER_PATTERN = re.compile(r"(?:^|[\s._/-])(opus|fable|astra|ultra|pro|max)(?:$|[\s._/-])")

# --------------------------------------------------------------------------- evidence
# WORK TYPE -> the Arena board whose rank may order candidates for that intent. This is
# the catalog's own declaration and the router reads it (falling back to its built-in
# default only when a catalog does not declare one), so the mapping cannot drift between
# the artifact that holds the evidence and the code that consumes it. `media_generation`
# has no board: the catalog excludes non-chat models, so no image/video generator is in
# its inventory to be ranked.
WORK_TYPE_BOARDS = {"coding": "code", "agent_tool_use": "agent", "analysis": "text",
                    "writing": "text", "vision": "vision", "document": "document",
                    "media_generation": None}
# Board priority for the single benchmark attached to `tier_evidence`. Never the maximum
# score across boards: `code` (1814 -> 1626, n=20) and `text` (1505 -> ..., n=20) are
# separate populations, and a maximum taken across them credits a model with a number
# measured against different competitors.
BOARD_PRIORITY = ["code", "text", "vision", "agent"]


def assign_tier(model_id, family, cost):
    """Declare the tier and say how. Returns (tier, evidence)."""
    base = model_id.split("/", 1)[-1].lower()
    if base in {x.lower() for x in TIER3_IDS}:
        return 3, {"method": "declared", "confidence": "high",
                   "reasoning": "current-generation flagship of its lab's range"}
    if base in {x.lower() for x in TIER2_IDS}:
        return 2, {"method": "declared", "confidence": "high",
                   "reasoning": "workhorse class: previous-generation flagship or "
                                "current mid-tier"}
    if base in {x.lower() for x in TIER1_IDS}:
        return 1, {"method": "declared", "confidence": "high",
                   "reasoning": "economy class: small, cheap, high-volume"}
    fam = (family or "").lower()
    for prefix, tier in FAMILY_TIER:
        if fam.startswith(prefix) or base.startswith(prefix):
            return tier, {"method": "declared", "confidence": "medium",
                          "reasoning": f"family `{fam}` positioned by its lab as "
                                       f"{'frontier' if tier == 3 else 'workhorse' if tier == 2 else 'economy'}"}
    if ECONOMY_PATTERN.search(base):
        return 1, {"method": "derived", "confidence": "low",
                   "reasoning": "economy naming class (haiku/flash/lite/mini/nano/air/fast)"}
    if FRONTIER_PATTERN.search(base):
        return 2, {"method": "derived", "confidence": "low",
                   "reasoning": "flagship naming class, but no measured evidence; held at "
                                "tier2 rather than promoted to tier3"}
    if cost and cost.get("input") is not None:
        # Price is a last-resort signal and is explicitly labelled as one. It may not rank
        # capability across families; here it only separates an unclassified model into a
        # plausible band, at low confidence.
        inp = cost["input"]
        tier = 1 if inp < 0.5 else (2 if inp < 4 else 3)
        return tier, {"method": "derived", "confidence": "very-low",
                      "reasoning": f"no identity, family or naming evidence; banded on "
                                   f"input price {inp} USD/1M. Price does not rank "
                                   f"capability and this must be reviewed."}
    return 1, {"method": "derived", "confidence": "very-low",
               "reasoning": "no evidence of any kind; defaulted to the cheapest tier so a "
                            "mis-tiering costs money, never quality"}


def cost_band(cost):
    """Indicative price band, stable even when the exact price is not."""
    if not cost or cost.get("input") is None or cost.get("output") is None:
        return "unknown"
    blended = cost["input"] + 3 * cost["output"]
    if blended < 3:
        return "economy"
    if blended < 20:
        return "mid"
    if blended < 60:
        return "high"
    return "frontier-price"


def norm(s):
    """Identity key for a model name. Effort is NOT stripped here.

    Our ids never carry a thinking level, so stripping one would corrupt real names
    (`qwen3.8-max` would collapse onto a hypothetical `qwen3.8`).
    """
    text = re.sub(r"\(.*?\)", " ", (s or "").split("/", 1)[-1])
    return "".join(t for t in re.split(r"[\s._/-]+", text.lower()) if t)


def norm_ns(s):
    """Identity key that KEEPS the namespace: `anthropic/claude-opus-5.5` -> `anthropic/claudeopus55`."""
    ns, _, rest = (s or "").partition("/")
    return f"{norm(ns)}/{norm(rest)}" if rest else norm(ns)


EFFORT_TOKENS = frozenset({"xhigh", "x", "high", "medium", "med", "low", "minimal", "mini",
                           "none", "max", "xmax", "thinking", "fast", "ultra"})


def norm_arena(s):
    """Identity key for a benchmark row. Effort IS stripped, arena side only.

    Arena spells one model as several rows (`claude-opus-5.5-max`, `-high`), and the
    catalog holds one identity. Without this asymmetry the benchmark never attaches to
    any model whose arena name carries an effort suffix, and `rule: best` silently loses
    the evidence it is supposed to maximise.
    """
    text = re.sub(r"\(.*?\)", " ", (s or "").split("/", 1)[-1])
    tokens = [t for t in re.split(r"[\s._/-]+", text.lower()) if t]
    while tokens and tokens[-1] in EFFORT_TOKENS:
        tokens.pop()
    return "".join(tokens)


def split_version(model_id, family):
    """Split `claude-opus-5.5` into model `claude-opus` and version `5.5`."""
    base = model_id.split("/", 1)[-1]
    m = re.search(r"(\d[\w.-]*)$", base)
    if m:
        return base[: m.start()].rstrip("-._ ") or base, m.group(1)
    return base, None


def effort_levels(entry):
    """Thinking levels a model declares, or None when it declares nothing.

    models.dev publishes `reasoning_options` as a LIST of option objects
    (`[{"type": "effort", "values": ["low", "medium", "high", "xhigh", "max"]}]`), not as a
    dict with an `efforts` key. Reading the wrong shape reported zero level sets for all
    500 rows and made `#effort` resolution look unsupported everywhere.
    """
    options = entry.get("reasoning_options")
    if options is None:
        return None
    if not isinstance(options, list):
        return None
    values = set()
    for option in options:
        if isinstance(option, dict) and option.get("type") == "effort":
            values.update(str(v) for v in option.get("values") or [])
    return sorted(values)


def endpoint_record(provider, mid, entry):
    cost = entry.get("cost") or {}
    limit = entry.get("limit") or {}
    return {"provider": provider, "provider_model_id": mid, "entry": entry,
            "cost": {"input": cost.get("input"), "output": cost.get("output"),
                     "cache_read": cost.get("cache_read"),
                     "cache_write": cost.get("cache_write")},
            "window": {"input": limit.get("context"), "output": limit.get("output")},
            "type": entry.get("type") or "chat",
            "status": entry.get("status") or "active"}


def endpoint_rank(rec, harness_norms, namespace):
    """Deterministic endpoint priority. Returns a sort tuple, lower wins.

    1. an endpoint whose id is the harness's own id for this model, when the harness names
    2. an endpoint that carries an input price at all: the row's purpose is an indicative
       price, so an unpriced lab endpoint never outranks a priced aggregator endpoint
    3. the published mirror closest to the harness gateway (`opencode`), so the indicative
       price is the one a gateway consumer is most likely to see
    4. the lab's own endpoint, when the lab publishes one
    5. a complete price over a partial one, then cache rates present over absent
    6. provider slug, so the choice never depends on dict order
    """
    cost = rec["cost"]
    harness_hit = bool(harness_norms) and norm(rec["provider_model_id"]) in harness_norms
    # A zero input price is a fact about that endpoint (a free tier), never the indicative
    # price of a paid model: ranking `0.0 is not None` as "priced" let an alphabetical
    # free endpoint supply `qwen3.8-flash-next`'s row price in the first build.
    priced = cost["input"] is not None and cost["input"] > 0
    return (0 if harness_hit else 1,
            0 if priced else 1,
            0 if rec["provider"] == "opencode" else 1,
            0 if rec["provider"] == namespace else 1,
            0 if (priced and cost["output"] is not None) else 1,
            0 if (cost["cache_read"] is not None and cost["cache_write"] is not None) else 1,
            str(rec["provider"]))


def endpoint_summary(recs):
    """The endpoint set, compacted: identity plus the measured spread of its prices.

    Carrying every endpoint's full price record cost ~1.9 MB for 8105 endpoints and no
    routing decision reads it: the row's indicative price is the selected endpoint's, and
    the harness always wins at runtime. What matters is that the divergence stays visible,
    so the spread is recorded rather than the individual prices.
    """
    priced_in = [r["cost"]["input"] for r in recs if r["cost"]["input"] is not None]
    priced_out = [r["cost"]["output"] for r in recs if r["cost"]["output"] is not None]
    spread = None
    if len(priced_in) > 1 or len(priced_out) > 1:
        spread = {}
        for name, values in (("input", priced_in), ("output", priced_out)):
            if values:
                spread[name] = {"min": min(values), "max": max(values)}
        spread["note"] = "list prices differ per endpoint; the row's price is the " \
                         "selected endpoint's and the harness always wins at runtime"
    return {"count": len(recs), "priced": len(priced_in),
            "providers": sorted({r["provider"] for r in recs}),
            "price_spread_usd_per_million": spread}


def aptitudes_for(observations, board_rows):
    """One measured observation per work type, from the boards that cover it.

    `level` is the rank percentile inside that board (`1 - (rank-1)/(rows-1)`), recorded
    with `of` so the percentile is reproducible; it is a convenience for readers, while the
    router orders on `score` inside one board. A work type with no board, or a board with no
    observation for this model, is absent rather than null: an absent aptitude is a stated
    absence, and three nulls per row would only add noise.
    """
    out = {}
    for work_type, board in WORK_TYPE_BOARDS.items():
        if not board:
            continue
        rows = [o for o in observations if o.get("board") == board]
        if not rows:
            continue
        scored = [o for o in rows if o.get("score") is not None]
        if scored:
            best = max(scored, key=lambda o: (o["score"], o.get("votes") or 0))
        else:
            best = min(rows, key=lambda o: (o.get("rank") or 10 ** 6, str(o.get("arena_name"))))
        of = board_rows.get(board)
        level = None
        if best.get("rank") and of and of > 1:
            level = round(1 - (best["rank"] - 1) / (of - 1), 4)
        out[work_type] = {
            "board": board, "arena_name": best.get("arena_name"),
            "effort": best.get("effort"), "rank": best.get("rank"), "of": of,
            "level": level, "score": best.get("score"), "ci": best.get("ci"),
            "votes": best.get("votes"), "as_of": best.get("as_of"),
            "method": "measured" if best.get("score") is not None else "measured-rank-only"}
    return out


def tier_benchmark(aptitudes, observations):
    """The single observation that evidences the tier, chosen by BOARD_PRIORITY.

    Never `max(score)` across boards. A model measured 1504 on `text` and 1655 on `code`
    must not be credited with 1655 as a text score, and a board that publishes dimensions
    instead of ELO (`agent`) evidences a rank, not a capability number.
    """
    for board in BOARD_PRIORITY:
        rows = [o for o in observations if o.get("board") == board]
        if not rows:
            continue
        scored = [o for o in rows if o.get("score") is not None]
        best = (max(scored, key=lambda o: (o["score"], o.get("votes") or 0)) if scored
                else min(rows, key=lambda o: (o.get("rank") or 10 ** 6,
                                              str(o.get("arena_name")))))
        return {"board": board, "arena_name": best.get("arena_name"),
                "effort": best.get("effort"), "rank": best.get("rank"),
                "score": best.get("score"), "ci": best.get("ci"),
                "votes": best.get("votes"), "as_of": best.get("as_of"),
                "note": (None if best.get("score") is not None else
                         "rank only, no score or CI on this board"),
                "selection": f"board priority {BOARD_PRIORITY}; never the maximum score "
                             f"across boards"}
    return None


def aliases_for(canonical, spellings, owners, harness_norms):
    """Every spelling this row OWNS, harness ids first.

    A canonical id is not the only name a model answers to: `zhipuai/glm-5.3-flash` is
    published by two endpoints as `glm-flash-latest`, and that is the id our harness
    exposes, so without the observed spellings the router cannot recognise its own model.
    Resellers create ambiguity though: measured on the first build of this catalog, 28
    spellings were claimed by more than one row (`deepseek-chat` by two, `qwen3.8-max` by
    its own preview). So a row takes a spelling only when it is the exact name match or the
    sole claimant; an ambiguous spelling resolves to nothing, and the router reports the
    unmatched harness id instead of silently placing the model inside another model's row.
    """
    here = norm(canonical.split("/", 1)[-1])
    mine = []
    for key, spelling in spellings.items():
        who = owners.get(key) or set()
        if who == {canonical} or (key == here and canonical in who):
            mine.append(spelling)
    harness_aliases = sorted(s for s in mine if norm(s) in harness_norms)
    rest = sorted((s for s in mine if norm(s) not in harness_norms), key=lambda s: (len(s), s))
    return sorted({canonical, canonical.split("/", 1)[-1]} | set(harness_aliases)
                  | set(rest[:12]))


def build(models_dev, benchmark, harness, args):
    notes = []
    harness_norms, harness_entries = set(), {}
    if harness:
        for prov in (harness.get("provider") or {}).values():
            for mid, e in (prov.get("models") or {}).items():
                harness_norms.add(norm(mid))
                harness_entries.setdefault(norm(mid), (mid, e))

    # ---- endpoints, grouped by canonical identity ---------------------------- identity
    groups = {}
    unattached = []
    for provider, prov in models_dev.items():
        for mid, e in (prov.get("models") or {}).items():
            rec = endpoint_record(provider, mid, e)
            canonical = e.get("canonical_model_id")
            key = norm_ns(canonical) if canonical else None
            if not key:
                unattached.append(rec)
                continue
            groups.setdefault(key, []).append(rec)

    # An entry with no canonical id (1363 of 9146) is still a real endpoint. Attach it when
    # its model name matches exactly one canonical model; leave it out, and say so, when the
    # name is ambiguous. Never guess a namespace.
    names = {}
    for key, recs in groups.items():
        names.setdefault(norm(recs[0]["entry"].get("canonical_model_id") or
                              recs[0]["provider_model_id"]), set()).add(key)
    matched_unattached = 0
    for rec in unattached:
        hits = names.get(norm(rec["provider_model_id"])) or set()
        if len(hits) == 1:
            groups[next(iter(hits))].append(rec)
            matched_unattached += 1
    notes.append(f"endpoints: {sum(len(v) for v in groups.values())} grouped into "
                 f"{len(groups)} canonical models; {len(unattached)} entries carry no "
                 f"canonical_model_id, {matched_unattached} matched one canonical model by "
                 f"name, {len(unattached) - matched_unattached} left unattached (ambiguous "
                 f"or unknown)")

    # Which rows publish which spelling. Cleaned up here, before rows are built, because
    # ownership is a property of the whole catalog and not of one row.
    row_spellings, owners = {}, {}
    for key, recs in groups.items():
        canonical = recs[0]["entry"].get("canonical_model_id") or recs[0]["provider_model_id"]
        spell = {}
        for r in recs:
            k = norm(r["provider_model_id"])
            if k and (k not in spell or len(r["provider_model_id"]) < len(spell[k])):
                spell[k] = r["provider_model_id"]
        k = norm(canonical)
        if k and (k not in spell or len(canonical) < len(spell[k])):
            spell[k] = canonical
        row_spellings[canonical] = spell
    for canonical, spell in row_spellings.items():
        for k in spell:
            owners.setdefault(k, set()).add(canonical)
    ambiguous_spellings = sorted(k for k, who in owners.items() if len(who) > 1)
    contested_unowned = sorted(
        k for k in ambiguous_spellings
        if not any(norm(c.split("/", 1)[-1]) == k for c in owners[k]))
    notes.append(f"spellings: {len(owners)} normalized names over {len(row_spellings)} rows; "
                 f"{len(ambiguous_spellings)} are claimed by more than one row, of which "
                 f"{len(contested_unowned)} have no exact-name owner and therefore resolve "
                 f"to none ({', '.join(contested_unowned[:8])}"
                 f"{', ...' if len(contested_unowned) > 8 else ''})")

    # ---- benchmark observations, keyed by the effort-free arena identity -------- evidence
    arena_index = {}
    board_rows = {}
    if benchmark:
        boards = benchmark.get("boards") or {}
        board_rows = {cat: len(b.get("rows_verbatim") or []) for cat, b in boards.items()}
        for key, obs_list in (benchmark.get("match_index") or {}).items():
            for o in obs_list:
                cat = o.get("category")
                arena_index.setdefault(key, []).append({
                    "board": cat, "arena_name": o.get("arena_name"),
                    "effort": o.get("effort"), "rank": o.get("rank"), "score": o.get("score"),
                    "ci": o.get("ci"), "votes": o.get("votes"),
                    "as_of": ((boards.get(cat) or {}).get("meta") or {}).get("last_updated")})

    # ---- selection: harness models, then benchmark-covered, then newest per family
    def make_row(canonical, namespace, recs, obs, harness_named, identity, spellings=None):
        chat = [r for r in recs if r["type"] in ("", None, "chat")]
        chosen = min(chat or recs, key=lambda r: endpoint_rank(r, harness_norms, namespace))
        e = chosen["entry"]
        statuses = {(r["status"] or "active") for r in recs}
        status = "active" if statuses - {"deprecated"} else "deprecated"
        cost, limit = chosen["cost"], chosen["window"]
        family = e.get("family") or (harness_entries.get(norm(canonical), (None, {}))[1]
                                     or {}).get("family")
        tier, tier_ev = assign_tier(canonical, family, cost)
        apts = aptitudes_for(obs, board_rows)
        bench = tier_benchmark(apts, obs)
        if bench:
            tier_ev = dict(tier_ev)
            tier_ev["benchmark"] = bench
            tier_ev["method"] = ("measured" if bench.get("score") is not None
                                 else "measured-rank-only")
            tier_ev["confidence"] = ("high" if (bench.get("votes") or 0) >= 2000
                                     else "medium")
        model, version = split_version(canonical, family)
        tagged = any((r["cost"]["input"] or 0) > 0 for r in recs)
        return {
            "id": canonical,
            "creator": namespace,
            "creator_display": (((models_dev.get(namespace) or {}).get("name")
                                 or namespace.replace("-", " ").title()) if namespace else None),
            "identity": identity,
            "family": family,
            "model": model,
            "version": version,
            "aliases": aliases_for(canonical, spellings or {}, owners, harness_norms),
            "release_date": e.get("release_date"),
            "status": status,
            "selected_endpoint": chosen["provider"],
            "endpoints": endpoint_summary(recs),
            "cost_usd_per_million": cost,
            "cost_band": cost_band(cost),
            "cost_is_indicative": True,
            "window": limit,
            "capabilities": {
                **normalize(e),
                "reasoning_options": e.get("reasoning_options"),
                "effort_levels": effort_levels(e),
            },
            "aptitudes": apts,
            "tier": tier,
            "tier_invariant_to_effort": True,
            "tier_evidence": tier_ev,
            "open_weights": e.get("open_weights"),
            "knowledge_cutoff": e.get("knowledge"),
            "provenance": {
                "taxonomy": {"source": ["models.dev", namespace] if namespace else
                             ["harness-config", "declared-by-catalog-author"],
                             "method": "harvested" if namespace else "declared",
                             "confidence": "medium" if namespace else "low"},
                "cost": {"source": ["models.dev", chosen["provider"]], "method": "harvested",
                         "confidence": "medium"},
                "window": {"source": ["models.dev", chosen["provider"]],
                           "method": "harvested", "confidence": "high"},
                "capabilities": {"source": ["models.dev", chosen["provider"]],
                                 "method": "harvested", "confidence": "high"},
                "aptitudes": {"source": sorted({f"arena/{o['board']}" for o in obs}),
                              "method": "measured", "confidence": "medium"} if obs else
                             {"source": [], "method": "none", "confidence": "none"},
                "tier": {"source": (["arena/" + o["board"] for o in obs] if obs else [])
                                  + ["declared-by-catalog-author"],
                         "method": tier_ev["method"], "confidence": tier_ev["confidence"]},
            },
            "_priority": (9 if not chat else
                          0 if harness_named else
                          1 if obs else
                          2 if status != "deprecated" and tagged else 9),
        }

    models = []
    for key, recs in groups.items():
        canonical = recs[0]["entry"].get("canonical_model_id") or recs[0]["provider_model_id"]
        namespace = canonical.split("/", 1)[0]
        base = norm(canonical.split("/", 1)[-1])
        e = recs[0]["entry"]
        name_key = norm(e.get("canonical_model_id") or recs[0]["provider_model_id"])
        obs = arena_index.get(name_key) or arena_index.get(base) or []
        harness_named = base in harness_norms or any(
            norm(r["provider_model_id"]) in harness_norms for r in recs)
        models.append(make_row(canonical, namespace, recs, obs, harness_named,
                               "canonical-model-id", row_spellings.get(canonical)))

    # A harness model models.dev publishes only under a provider-local id (no canonical
    # id) still has to be in the catalog: the harness exposes it, and the classifier is
    # chosen from this catalog. It enters as its own row, keyed by the id the harness
    # uses, with the attribution gap declared rather than a namespace invented.
    covered = set()
    for key, recs in groups.items():
        canonical = recs[0]["entry"].get("canonical_model_id") or recs[0]["provider_model_id"]
        covered.add(norm(canonical.split("/", 1)[-1]))
        covered |= {norm(r["provider_model_id"]) for r in recs}
    local_rows, uncovered_harness = [], []
    for hnorm, (hmid, hentry) in sorted(harness_entries.items()):
        if hnorm in covered:
            continue
        extra = [r for r in unattached if norm(r["provider_model_id"]) == hnorm]
        if not extra:
            uncovered_harness.append(hmid)
            continue
        obs = arena_index.get(hnorm) or []
        spell = {hnorm: hmid}
        for r in extra:
            k = norm(r["provider_model_id"])
            if k and k not in owners:
                spell.setdefault(k, r["provider_model_id"])
        row = make_row(hmid, None, extra, obs, True, "harness-declared-provider-local", spell)
        local_rows.append(row)
        covered.add(hnorm)
    models += local_rows
    notes.append(f"harness-declared rows: {len(local_rows)} models the harness exposes and "
                 f"models.dev publishes without a canonical id "
                 f"({', '.join(r['id'] for r in local_rows) or 'none'}); "
                 f"{len(uncovered_harness)} harness ids appear in no models.dev entry at all "
                 f"({', '.join(uncovered_harness) or 'none'}) and stay outside the catalog, so "
                 f"the router places them by family inference. A harness id that models.dev "
                 f"does publish is matched through the aliases of its canonical row, which is "
                 f"how `<lab>/glm-5.3-flash` answers to the harness id `glm-flash-latest`")

    # ---- priority first (harness, benchmark-covered), then newest per family up to --limit
    ordered = sorted(models, key=lambda m: (str(m.get("release_date") or ""), m["id"]),
                     reverse=True)
    ordered.sort(key=lambda m: m["_priority"])
    per_family, selected = {}, []
    prio_count = sum(1 for m in models if m["_priority"] < 9)
    for m in ordered:
        if m["_priority"] == 9:
            continue
        if len(selected) >= args.limit and m["_priority"] > 1:
            break
        if m["_priority"] == 2:
            fam = m["family"] or m["model"]
            if per_family.get(fam, 0) >= args.per_family:
                continue
            per_family[fam] = per_family.get(fam, 0) + 1
        selected.append(m)
    for m in selected:
        m.pop("_priority", None)
    # Rows are ordered by tier, then by the declared evidence order, then by id. The router
    # reads `declared_order` as the row index, so this file order IS the last-resort ranking.
    selected.sort(key=lambda m: (m["tier"], evidence_order(m), m["id"]))
    notes.append(f"selected {len(selected)} of {len(models)} canonical models; {prio_count} "
                 f"usable (chat, priced or harness-exposed), the rest non-chat, unpriced or "
                 f"deprecated; harness + benchmark-covered first, then newest-per-family up to "
                 f"--per-family {args.per_family} within --limit {args.limit}")
    models = selected

    dist = {}
    for m in models:
        dist[m["tier"]] = dist.get(m["tier"], 0) + 1
    ev = {}
    for m in models:
        k = m["tier_evidence"]["method"]
        ev[k] = ev.get(k, 0) + 1
    return {
        "schema": SCHEMA,
        "revision": args.revision,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "role": "primary source of model knowledge for the routing plugin; the router "
                "intersects this catalog with what the active harness exposes, then "
                "assigns per tier",
        "model_count": len(models),
        "identity": {
            "key": "canonical_model_id from models.dev (`<lab>/<model>`, one row per model)",
            "endpoints": "every provider endpoint that publishes this model, with its own "
                         "prices; `selected_endpoint` names the one whose price the row "
                         "carries, and the harness always wins at runtime",
            "aliases": "the spellings the catalog matched: our harness ids never carry an "
                       "effort token and Arena names do, so normalization is asymmetric",
        },
        "creator_count": len({m["creator"] for m in models}),
        "tier_distribution": {str(k): dist.get(k, 0) for k in (1, 2, 3)},
        "tier_evidence_distribution": ev,
        "work_type_boards": dict(WORK_TYPE_BOARDS),
        "board_coverage": {cat: {"rows": len((b.get("rows_verbatim") or [])),
                                 "scored": sum(1 for r in (b.get("rows_verbatim") or [])
                                               if r.get("score") is not None),
                                 "as_of": (b.get("meta") or {}).get("last_updated")}
                           for cat, b in ((benchmark or {}).get("boards") or {}).items()},
        "row_order": {
            "rule": "tier ascending, then the declared evidence order (board priority "
                    f"{BOARD_PRIORITY}, score descending inside a board, rank ascending for "
                    "a rank-only board), then the model id",
            "why": "`declared_order` in the router is the row index, and `best` falls back to "
                   "it when the governing board has evidence for none of the candidates. An "
                   "alphabetical file made that fallback depend on the first letter of a "
                   "model id",
        },
        "aptitudes_semantics": {
            "shape": "per model, per work type: {board, arena_name, effort, rank, of, "
                     "level, score, ci, votes, as_of, method}",
            "level": "rank percentile inside the named board: 1 - (rank-1)/(of-1). A "
                     "convenience for readers; the router orders on `score` inside one "
                     "board, and a board that publishes dimensions instead of ELO has "
                     "`score: null` and `method: measured-rank-only`",
            "absent": "a work type with no board, or no observation for this model, is "
                      "ABSENT from `aptitudes`, never null",
            "board_coverage": "boards the pinned snapshot carries, with the rows each one "
                              "publishes. A work type mapped to a board that is not listed "
                              "here, or listed with neither scored nor ranked rows, has no "
                              "evidence in this catalog. A rank-only board supplies measured "
                              "ordering; missing evidence is reported as degraded ordering",
            "measured_disagreement": "the boards disagree on the frontier: on the pinned "
                                     "2026-10-07 snapshot `code` rank 1 is "
                                     "claude-opus-5.5-max with claude-fable-5.1-max 5th, "
                                     "while `agent` rank 1 is Claude Fable 5.1 (Max)",
        },
        "tier_definition": {
            "tier1": "economy: small, cheap, high-volume, low-risk work. hop_depth 1, "
                     "direct output, no invariant table.",
            "tier2": "workhorse: standard development and analysis work. hop_depth 1, no "
                     "direct output.",
            "tier3": "frontier: deep work, multi-hop reasoning, adversarial review. "
                     "hop_depth 2, invariant table required.",
            "invariance_rule": "tier is a property of the model, never of the "
                               "(model, effort) pair: a tier3 model stays tier3 at every "
                               "thinking level",
            "assignment": "declared by the catalog author from lab product positioning and "
                          "checked against the pinned Arena board where it covers the "
                          "model. Never derived from price alone, and never from a name "
                          "without recorded reasoning.",
        },
        "semantics": {
            "cost_is_indicative": "list prices, not what any given gateway charges. "
                                  "Measured divergences: Anthropic cache_write is 1.6x on "
                                  "the reference gateway; gemini-3.8-flash input is 0.75 "
                                  "there against 1.5 in models.dev and 0.825 in OpenRouter. "
                                  "At runtime a harness-declared value always wins.",
            "window": "input = context window in tokens, output = max completion tokens. "
                      "A zero or null output limit is a marker, not a limit.",
            "null_policy": "a missing value is null, never 0 and never a silent default",
            "price_does_not_rank_capability": "measured: gpt-6-astra-max and "
                                              "claude-fable-5.1-max share the price "
                                              "structure 10/50 and sit 43 ELO and 3 ranks "
                                              "apart; Spearman rho(price,score) is 0.718 "
                                              "within one board and -0.11 pooled.",
            "benchmark_selection": f"the benchmark on `tier_evidence` is chosen by board "
                                   f"priority {BOARD_PRIORITY} and by score inside that "
                                   f"board. Taking the maximum score across boards would "
                                   f"compare separate populations.",
        },
        "sources": [
            {"name": "models.dev", "url": MODELS_DEV_URL, "retrieved_at": args.retrieved_at,
             "input_mode": getattr(args, "input_mode", "provided-data"),
             "supplies": ["identity (canonical_model_id)", "creator", "family", "version",
                          "cost", "limit.context", "limit.output", "modalities", "tool_call",
                          "reasoning", "reasoning_options", "structured_output", "status",
                          "type", "open_weights", "knowledge", "release_date", "endpoints"],
             "licence": "open database; attribution retained"},
        ] + ([{"name": "arena-ai-leaderboards (mirror of arena.ai)",
               "snapshot_date": (benchmark.get("source") or {}).get("snapshot_date"),
               "commit": ((benchmark.get("source") or {}).get("commit") or {}).get("sha"),
               "supplies": ["aptitudes and tier evidence: rank, ELO score, 95% CI, votes, "
                            "per board"],
               "licence": "MIT on the mirror's files; the underlying ELO data belongs to "
                          "arena.ai with no stated redistribution term, so it is used as "
                          "evidence for a declared tier and not republished",
               "stale_after": (benchmark.get("source") or {}).get("snapshot_date")}]
             if benchmark else []),
        "excluded": {"deprecated": "every endpoint declares models.dev status=deprecated",
                     "non_chat": "no endpoint of the model is a chat model",
                     "unpriced": "no endpoint carries cost.input, so no indicative price "
                                 "could be recorded",
                     "not_selected": "a priced chat model the selection left out: harness "
                                     "and benchmark-covered models come first, then the "
                                     "newest per family up to --per-family, then --limit"},
        "notes": notes,
        "models": models,
    }


def evidence_order(model):
    """Last-resort ordering for a row: board priority, then the observation inside it.

    `best` falls back to this order only when the governing board has no evidence for the
    whole pool, and it used to be the order the rows happened to sit in the file, which was
    alphabetical: the deepest tier was then decided by the first letter of a model id. The
    order below is declared policy instead, applied to the file itself so the router keeps
    reading one number (`declared_order` = the row index) with no second implementation.
    """
    for i, board in enumerate(BOARD_PRIORITY):
        scores = [apt.get("score") for apt in (model.get("aptitudes") or {}).values()
                  if apt.get("board") == board and apt.get("score") is not None]
        if scores:
            return (i, -max(scores))
        ranks = [apt.get("rank") for apt in (model.get("aptitudes") or {}).values()
                 if apt.get("board") == board and apt.get("score") is None
                 and apt.get("rank") is not None]
        if ranks:
            return (i, min(ranks))
    bench = (model.get("tier_evidence") or {}).get("benchmark") or {}
    if bench.get("board") in BOARD_PRIORITY:
        i = BOARD_PRIORITY.index(bench["board"])
        if bench.get("score") is not None:
            return (i, -bench["score"])
        if bench.get("rank") is not None:
            return (i, bench["rank"])
    return (len(BOARD_PRIORITY), 0)


def main(argv=None):
    p = argparse.ArgumentParser(prog="build_model_catalog.py")
    p.add_argument("--out", required=True)
    p.add_argument("--fetch", action="store_true")
    p.add_argument("--from-response", help="use an already downloaded models.dev response")
    p.add_argument("--models-dev-url", default=MODELS_DEV_URL)
    p.add_argument("--benchmark", help="pinned Arena snapshot from benchmark_snapshot.py")
    p.add_argument("--harness-config", help="the active harness opencode.json, for priority")
    p.add_argument("--limit", type=int, default=500)
    p.add_argument("--per-family", type=int, default=6)
    p.add_argument("--revision", type=int, default=1)
    args = p.parse_args(argv)

    if args.from_response:
        raw = Path(args.from_response).read_bytes()
        args.input_mode = "cached-response"
        args.retrieved_at = None
    elif args.fetch:
        if not args.models_dev_url.startswith("https://"):
            print(json.dumps({"status": "failed", "reason": "non-HTTPS url refused"}))
            return 1
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(args.models_dev_url,
                                     headers={"User-Agent": "daodan-model-catalog/1"})
        try:
            with opener.open(req, timeout=90) as r:
                raw = r.read(64 * 1024 * 1024)
            args.input_mode = "network-fetch"
            args.retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        except Exception as exc:
            print(json.dumps({"status": "failed",
                              "reason": f"models.dev unreachable: {exc.__class__.__name__}: {exc}",
                              "consequence": "no catalog written; the router must not "
                                             "fall back to inventing model knowledge"}))
            return 1
    else:
        print(json.dumps({"status": "failed",
                          "reason": "network egress is opt-in: pass --fetch, or "
                                    "--from-response FILE"}))
        return 1

    try:
        models_dev = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "reason": f"not UTF-8 JSON: {exc}"}))
        return 1

    benchmark = json.loads(Path(args.benchmark).read_text(encoding="utf-8")) if args.benchmark else None
    harness = (json.loads(Path(args.harness_config).read_text(encoding="utf-8"))
               if args.harness_config else None)

    catalog = build(models_dev, benchmark, harness, args)
    catalog["models_dev_raw_sha256"] = hashlib.sha256(raw).hexdigest()
    body = json.dumps(catalog, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_bytes(body)
    tmp.replace(out)
    summary = {k: v for k, v in catalog.items() if k != "models"}
    summary["out"] = str(out)
    summary["out_bytes"] = len(body)
    summary["catalog_sha256"] = hashlib.sha256(body).hexdigest()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
