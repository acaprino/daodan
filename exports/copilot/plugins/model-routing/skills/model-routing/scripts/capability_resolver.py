"""Resolve a model's capability from one authoritative source, then two declared fallbacks.

The chain is a decision, not a preference order. Measured evidence fixed each level:

1. **`benchmark` — the single authoritative source.** One pinned Arena snapshot
   (``benchmark_snapshot.py``), never several registries. Identity is **effort-stripped**:
   ``claude-opus-5-5-max`` IS ``claude-opus-5-5``. Effort is an attribute of the
   observation, so a model may own several observations in one category and that is a
   measured series, not an ambiguity (on the 2026-10-07 ``code`` board
   ``claude-sonnet-5.5`` owns ``high`` 1716, ``xhigh`` 1773 and ``max``; the high/xhigh
   gap is 57 ELO with non-overlapping CIs).
2. **`family-preauthorized` — an interval, never a scalar.** Only families named in the
   policy are eligible, and they yield the observed sibling range plus a member count.
   A scalar would be a fabrication: within ``claude-opus`` on that board
   ``claude-opus-5.5-max`` scores 1814 while ``claude-opus-5-max`` scores 1692, 122 ELO
   apart; within ``mimo``, ``mimo-v2.6-flash`` (1636) outscores ``mimo-v2.6-pro`` (1630).
   Eligibility therefore uses the interval's **lower bound**. Family never fills a price
   or a context window either: ``opus-5.5`` is 4/20 USD per 1M and ``opus-5`` is 5/25.
3. **`heuristic` — cost only, and it says so.** Price is not capability. On the same
   board ``gpt-6-astra-max`` and ``claude-fable-5.1-max`` have an identical price
   structure (10/50) and differ by 43 ELO and 3 ranks, while the cheaper
   ``claude-opus-5.5-max`` (4/20) outscores the 2.5x dearer ``claude-fable-5.1-max``
   (10/50) by 69. Spearman rho between input price and score is 0.718 inside the
   ``code`` board (n=20) but **-0.112** once boards are pooled (n=58), because each board
   has its own ELO scale. This level therefore emits ``capability: unknown`` with a
   ``very-low`` confidence prior whose own refutation travels with it, and it may order
   candidates **economically** only.
4. **`unknown`** — never a zero, never a pass, never an automatic tier3 binding.

Two rules bind every level:

- **No ordering across overlapping confidence intervals.** On the ``code`` board ranks
  1→2→3→4→5 are pairwise inseparable, and inseparability is not transitive: the
  endpoints ``claude-sonnet-5.5-xhigh`` [1758, 1788] and ``claude-fable-5.1-max``
  [1736, 1754] do not overlap. So a comparison is answered per pair, never by rank alone.
- **Nothing here binds a model.** The result informs a human's tier declaration; the
  frontier is never auto-picked.

Standard library only. Reads a snapshot captured by ``benchmark_snapshot.py`` and a policy
file; performs no network access.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA = "daodan/capability-resolution/v1"

# Kept identical to benchmark_snapshot.py on purpose: two normalisers that drift would
# silently un-match models. See tests/test_capability_resolver.py.
EFFORT_TOKENS = frozenset({
    "xhigh", "x", "high", "medium", "med", "low", "minimal", "mini", "none",
    "max", "xmax", "thinking", "fast", "ultra",
})

# Measured on the pinned 2026-10-07 snapshot; travels with every heuristic result so the
# prior is never read without its own refutation.
HEURISTIC_EVIDENCE = {
    "spearman_input_within_code_board": 0.718,
    "spearman_output_within_code_board": 0.7697,
    "n_within_code_board": 20,
    "spearman_input_pooled_boards": -0.1117,
    "spearman_output_pooled_boards": -0.1739,
    "n_pooled": 58,
    "counterexamples": [
        "gpt-6-astra-max and claude-fable-5.1-max share the price structure 10/50 and "
        "differ by 43 ELO and 3 ranks",
        "claude-opus-5.5-max (4/20) outscores claude-fable-5.1-max (10/50) by 69 ELO: the "
        "cheaper model is better",
        "pooling boards collapses rho to about -0.11 because each board has its own scale",
    ],
    "conclusion": "price may order candidates economically; it may not rank capability",
}


def norm_model_key(name):
    """Identity key with **no** effort stripping.

    Our harness ids never carry an effort token: effort lives in the separate ``variants``
    map and in the ``#effort`` suffix of ``model_param``. Stripping effort from our own
    ids would corrupt real names, so it is not done here: ``qwen3.8-max`` keeps its
    ``max`` and stays distinct from a hypothetical ``qwen3.8``.
    """
    text = (name or "").split("/", 1)[-1]
    text = re.sub(r"\(.*?\)", " ", text)
    return "".join(t for t in re.split(r"[\s._/-]+", text.lower()) if t)


def norm_effort_key(name):
    """Identity key with trailing effort stripped — **arena side only**.

    Board rows do carry effort (``claude-opus-5.5-max``, ``claude-sonnet-5.5-xhigh``,
    ``muse-spark-1.3 (xHigh)``), and one model owns one row per effort. Stripping groups
    those rows into the model's effort series. Applying this to a harness id would be
    wrong, which is why the two functions are separate. The result must stay identical to
    the key ``benchmark_snapshot.py`` writes into ``match_index``.
    """
    tokens = re.split(r"[\s._/-]+", re.sub(r"\(.*?\)", " ",
                                           (name or "").split("/", 1)[-1]).lower())
    tokens = [t for t in tokens if t]
    while tokens and tokens[-1] in EFFORT_TOKENS:
        tokens.pop()
    return "".join(tokens)


def norm_key(name):
    """Deprecated alias for ``norm_effort_key``.

    Kept so the snapshot's existing effort-stripped ``match_index`` keys and this module
    stay in step. New call sites must choose one of the two explicit functions: a single
    symmetric normaliser is what silently turned ``qwen3.8-max`` into ``qwen38``.
    """
    return norm_effort_key(name)


def effort_of(name):
    """Effort attribute of an observation, from a suffix or a parenthetical."""
    text = (name or "").lower()
    if re.search(r"x[\s._-]?high", text):
        return "xhigh"
    parens = " ".join(re.findall(r"\((.*?)\)", text))
    tokens = [t for t in re.split(r"[\s._()-]+", text + " " + parens) if t]
    found = [t for t in tokens if t in EFFORT_TOKENS]
    return found[-1] if found else None


def _result(model_id, level, **fields):
    out = {"schema": SCHEMA, "model_id": model_id, "level": level,
           "capability": None, "capability_evidence": None,
           "capability_bounds": None,
           "confidence": None, "orders_capability": False,
           # Tier membership is a property of the model, never of the (model, effort)
           # pair: a model that is tier3 stays tier3 at every effort.
           "tier_invariant": True,
           "economic_order_only": level == "heuristic"}
    out.update(fields)
    return out


def load_snapshot(path):
    """Load a captured snapshot and verify it is usable. Returns (snapshot, error)."""
    try:
        snap = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{exc.__class__.__name__}: {exc}"
    if snap.get("schema") != "daodan/benchmark-snapshot/v1":
        return None, f"unexpected schema {snap.get('schema')!r}"
    if snap.get("status") != "captured":
        return None, f"snapshot status is {snap.get('status')!r}, not 'captured'"
    if not (snap.get("authority") or {}).get("advisory_only"):
        return None, "snapshot does not declare advisory_only; refusing to consume it"
    return snap, None


def _significantly_above(a, b):
    """True only when a's lower bound clears b's upper bound. Missing bounds: no claim.

    Bounds are the model-level aggregation across every observed effort, so the answer
    does not depend on which effort either model happens to run at.
    """
    ab, bb = a.get("capability_bounds"), b.get("capability_bounds")
    if not ab or not bb:
        return None
    return ab["lower"] > bb["upper"]


def _family_of(model_id, policy):
    """Declared family for a model id, matched raw or normalized on both sides.

    The policy may key either the harness form (``provider/model``) or the bare board
    name, and the lookup may receive either; both sides are normalized so the two forms
    resolve to one declaration.
    """
    table = policy.get("family_of") or {}
    if model_id in table:
        return table[model_id]
    exact, stripped = norm_model_key(model_id), norm_effort_key(model_id)
    for declared, family in table.items():
        if norm_model_key(declared) == exact or norm_effort_key(declared) == stripped:
            return family
    return None


def _locate(index, model_id):
    """Find a model's board rows: exact name first, then the effort-stripped group.

    Two normalisers are tried in that order because they are different strengths of
    evidence. An exact name match means the board row spells the model the way the harness
    does; an effort-stripped group match means the board row carries an effort suffix the
    harness id does not. The route is returned so the result can say which happened.
    """
    exact = norm_model_key(model_id)
    for group_key, rows in index.items():
        if any(norm_model_key(r.get("arena_name")) == exact for r in rows):
            return rows, "exact-name", group_key
    stripped = norm_effort_key(model_id)
    if stripped in index:
        return index[stripped], "effort-stripped-group", stripped
    for group_key, rows in index.items():
        if any(norm_effort_key(r.get("arena_name")) == stripped for r in rows):
            return rows, "effort-stripped-group", group_key
    return [], None, None


def resolve(model_id, effort, category, snapshot, policy):
    """Walk the chain for one model on one board.

    **``effort`` never changes the level or the capability.** Tier membership is a
    property of the model: if a model is tier3, it is tier3 at every effort. The
    requested effort is used only to report which observation matches this dispatch, and
    a model measured at one effort is still measured at the model level.

    ``policy`` carries ``family_of`` (id -> family) and ``family_members`` (family ->
    arena names), both human-declared. An undeclared family is not a fallback; it is
    level 4.
    """
    index = snapshot.get("match_index") or {}
    rows, route, group_key = _locate(index, model_id)
    board = [r for r in rows if r.get("category") == category]
    scored = [r for r in board if r.get("score") is not None]
    stamp = (f"benchmark@arena/{category}@{snapshot['source']['snapshot_date']}"
             f"@{(snapshot['source']['commit'] or {}).get('sha', '')[:12]}")

    # ---- level 1: the authoritative snapshot, aggregated over every observed effort
    if scored:
        at_effort = [r for r in scored if (r.get("effort") or None) == (effort or None)]
        same_effort_dupes = len(at_effort) > 1 or any(
            r.get("identity_conflict") for r in at_effort)
        if same_effort_dupes:
            return _result(model_id, "conflict", capability_evidence="refused",
                           confidence="none",
                           rows=[{k: r.get(k) for k in ("arena_name", "effort", "vendor",
                                                         "score", "ci", "rank")}
                                 for r in at_effort],
                           reason="several board rows match this model at this effort; a "
                                  "human must resolve the identity before any tier uses it")
        bounds = [(r["score"] - r["ci"], r["score"] + r["ci"])
                  for r in scored if r.get("ci") is not None]
        best = max(scored, key=lambda r: r["score"])
        matched = at_effort[0] if at_effort else None
        return _result(
            model_id, "benchmark",
            capability=best["score"],
            capability_basis="best observed effort; tier membership is effort-invariant",
            capability_interval={"min": min(r["score"] for r in scored),
                                 "max": max(r["score"] for r in scored)},
            capability_bounds=({"lower": min(b[0] for b in bounds),
                                "upper": max(b[1] for b in bounds)} if bounds else None),
            capability_evidence=f"{stamp} over {len(scored)} observed effort(s)",
            confidence="measured",
            observations=[{k: r.get(k) for k in ("arena_name", "effort", "rank", "score",
                                                 "ci", "votes", "vendor")}
                          for r in sorted(scored, key=lambda r: -r["score"])],
            efforts_observed=sorted({r.get("effort") for r in scored if r.get("effort")}),
            requested_effort=effort,
            effort_matched=({k: matched.get(k) for k in ("arena_name", "effort", "rank",
                                                          "score", "ci", "votes")}
                             if matched else None),
            effort_match=("exact" if matched else
                          ("not-requested" if effort is None else "other-effort")),
            tier_invariant=True,
            rank=best.get("rank"), ci=(matched or best).get("ci"),
            votes=(matched or best).get("votes"), vendor=best.get("vendor"),
            identity_route=route, identity_group=group_key,
            identity="name-normalized-unverified",
            identity_conflict=any(r.get("identity_conflict") for r in scored),
            orders_capability=True)

    # ---- level 2: pre-authorized family, as an interval only.
    # Membership is human-declared in the policy (`family_members`). It is never derived
    # from a name prefix, and it is never imported from a second registry: one
    # authoritative source means the family grouping is a declaration, not a lookup.
    family = _family_of(model_id, policy)
    members = (policy.get("family_members") or {}).get(family or "") or []
    # Declared members are arena names, which do carry effort; index keys do not.
    member_keys = {norm_effort_key(m) for m in members} | set(members)
    if family and member_keys:
        siblings = []
        for other_key, other_rows in index.items():
            if other_key == group_key or other_key not in member_keys:
                continue
            siblings += [r for r in other_rows
                         if r.get("category") == category and r.get("score") is not None]
        if siblings:
            scores = sorted(r["score"] for r in siblings)
            return _result(model_id, "family-preauthorized", capability=None,
                           capability_interval={"min": scores[0], "max": scores[-1],
                                                "median": scores[len(scores) // 2]},
                           capability_evidence=f"family:{family}@arena/{category} over "
                                               f"{len(siblings)} observed sibling rows",
                           confidence="very-low", family=family,
                           siblings=sorted({r.get("arena_name") for r in siblings}),
                           eligibility_bound=scores[0],
                           note="an interval, never a scalar: siblings in one family differ "
                                "by 122 ELO (claude-opus-5.5-max 1814 vs claude-opus-5-max "
                                "1692). Eligibility must use the lower bound.",
                           orders_capability=False)
        return _result(model_id, "family-authorized-unobserved", capability=None,
                       capability_evidence=None, confidence="none", family=family,
                       reason=f"family {family} is pre-authorized but no sibling appears on "
                              f"the {category} board; nothing to inherit")

    # ---- level 3: heuristic, cost only
    return _result(model_id, "heuristic", capability="unknown",
                   capability_evidence=None, confidence="none",
                   prior=HEURISTIC_EVIDENCE,
                   reason="no authoritative observation and no pre-authorized family; the "
                          "cost model may order this model economically and may not rank "
                          "its capability")


def _at_effort(result, effort):
    """Bounds from one effort's observation, for comparing a specific dispatch."""
    for obs in result.get("observations") or []:
        if (obs.get("effort") or None) == (effort or None) and obs.get("ci") is not None:
            return {"lower": obs["score"] - obs["ci"], "upper": obs["score"] + obs["ci"],
                    "arena_name": obs.get("arena_name")}
    return None


def compare(a, b, effort=None):
    """Significant ordering between two resolved results, or an explicit refusal.

    Without ``effort`` the comparison is **effort-invariant**: it uses each model's
    bounds aggregated across every observed effort, so the answer cannot depend on which
    effort either model runs at. Passing ``effort`` narrows both sides to that one
    observation, which is the right question for a specific dispatch and the wrong one
    for tier membership.
    """
    if a.get("level") != "benchmark" or b.get("level") != "benchmark":
        return {"ordered": False, "reason": f"levels {a.get('level')} and {b.get('level')} "
                                           "carry no comparable measurement"}
    if effort is not None:
        ea, eb = _at_effort(a, effort), _at_effort(b, effort)
        if not ea or not eb:
            missing = [r["model_id"] for r, e in ((a, ea), (b, eb)) if not e]
            return {"ordered": False, "effort": effort,
                    "reason": f"no observation at effort {effort!r} for {missing}; "
                              "compare without effort for the tier-invariant answer"}
        a, b = dict(a, capability_bounds=ea), dict(b, capability_bounds=eb)
    sig = _significantly_above(a, b)
    if sig is None:
        return {"ordered": False, "reason": "a confidence interval is missing; no claim"}
    basis = ("non-overlapping 95% CI" + (f" at effort {effort}" if effort is not None
                                         else ", aggregated over observed efforts"))
    if sig:
        return {"ordered": True, "higher": a["model_id"], "basis": basis}
    if _significantly_above(b, a):
        return {"ordered": True, "higher": b["model_id"], "basis": basis}
    return {"ordered": False,
            "reason": "the 95% confidence intervals overlap; this pair is not a "
                      "significant ordering, and inseparability is not transitive"}
