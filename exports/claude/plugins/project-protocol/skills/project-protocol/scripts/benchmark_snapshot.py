"""Snapshot and pin a third-party benchmark mirror, so a routing decision can cite it.

The Arena AI leaderboards are the only reachable source of measured capability ranks for
the models this harness can bind: ``arena.ai`` returns **403** to non-browser clients on
``/leaderboard/*`` and serves a Cloudflare challenge to reader proxies, and it publishes
no API (``/api/leaderboard`` and ``/api/v1/leaderboard`` both 403; ``llms.txt`` returns
the app shell). Its ``robots.txt`` does explicitly ``Allow: /leaderboard`` and every
subpath, so the block is a client-fingerprint gate, not a policy one. Until a browser
job exists, this script captures the MIT-licensed community mirror
``oolong-tea-2026/arena-ai-leaderboards`` at a pinned commit instead.

Two defects of that mirror are the reason this script exists rather than a plain
download:

1. **It dies silently.** Its upstream started returning 403, and from 2026-10-08 the
   daily workflow kept committing snapshots with ``leaderboards: {}`` and ``errors: []``,
   while ``data/latest.json`` kept pointing at the newest, empty one. A consumer that
   trusts ``latest.json`` therefore gets zero models and no error. This script refuses an
   empty snapshot and walks back to the newest one that actually carries categories.
2. **Freshness is per category, not per snapshot.** Measured on the 2026-10-07 snapshot:
   ``code`` was updated Oct 7, ``text``/``vision``/``agent`` Oct 2, ``document`` Sep 13,
   ``search`` Aug 24. One date for the whole snapshot would hide a six-week-old board.

What the output is, and is not:

- It is **advisory**. Arena ELO measures human preference in chat/agent arenas, not this
  harness's workload. It informs a human's tier declaration; it never binds a model. The
  frontier is never auto-picked.
- It carries **no authority over a harness-declared value**, and no capability claim is
  derived from a model name: ranks come from the board, and matching a board row to a
  harness model id stays a ``name-normalized-unverified`` claim.
- Rows are stored **verbatim**. The ``match_index`` beside them is derived and says so.
- Ranks whose 95% confidence intervals overlap are **not** a significant ordering. On the
  2026-10-07 ``code`` board ``claude-opus-5.5-max`` (1814 +/-16) and ``gpt-6-astra-max``
  (1788 +/-11) overlap, while ``claude-sonnet-5.5-xhigh`` (1773 +/-15) and
  ``claude-fable-5.1-max`` (1745 +/-9) do not. ``ci`` and ``votes`` are kept for exactly
  this reason and must be read together with ``rank``.

Nothing is written into the repository. ``--out-dir`` belongs in local ignored storage
(``.tritech/local/`` is gitignored) or a harness cache.

Standard library only. Network egress is opt-in: without ``--fetch`` the script refuses.

Usage:

    python benchmark_snapshot.py --out-dir DIR --fetch
        [--repo OWNER/NAME] [--ref main]
        [--categories code,agent,text,vision]
        [--date YYYY-MM-DD]        # pin a snapshot explicitly instead of resolving it
        [--max-staleness-days 45]  # per-category freshness gate, reported not enforced
        [--timeout 45] [--max-bytes 8388608]
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

SCHEMA = "daodan/benchmark-snapshot/v1"
DEFAULT_REPO = "oolong-tea-2026/arena-ai-leaderboards"
DEFAULT_CATEGORIES = ("code", "agent", "text", "vision")
DEFAULT_MAX_STALENESS_DAYS = 45
DEFAULT_TIMEOUT_S = 45
DEFAULT_MAX_BYTES = 8 * 1024 * 1024

# Effort/variant suffixes arena.ai appends to a model name. Stripping them is what makes
# `claude-sonnet-5.5-xhigh` and `claude-sonnet-5-5` comparable, and it is also what makes
# a board row ambiguous: one harness model can own several rows at different efforts.
EFFORT_TOKENS = frozenset({
    "xhigh", "x", "high", "medium", "med", "low", "minimal", "mini", "none",
    "max", "xmax", "thinking", "fast", "ultra",
})

LICENCE = "MIT (the mirror's own files). The underlying Arena ELO data belongs to arena.ai; the mirror's README states no redistribution term for it, so this snapshot is used locally as advisory input and is not republished."


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects: the allowlist names fixed hosts, and a redirect leaves them."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())


def _get_json(url, timeout, max_bytes):
    """GET one URL from an allowlisted host. Returns (payload, raw_bytes, None) or (None, None, reason)."""
    if not url.startswith("https://"):
        return None, None, f"refusing non-HTTPS url: {url}"
    allowed = ("api.github.com", "raw.githubusercontent.com")
    if not any(url.startswith(f"https://{h}/") for h in allowed):
        return None, None, f"host not allowlisted: {url}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "daodan-benchmark-snapshot/1",
                      "Accept": "application/vnd.github+json, application/json"})
    try:
        with OPENER.open(request, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
    except Exception as exc:                      # noqa: BLE001 - reported, not guessed
        return None, None, f"{exc.__class__.__name__}: {exc}"
    if len(raw) > max_bytes:
        return None, None, f"response exceeds --max-bytes {max_bytes}"
    try:
        return json.loads(raw.decode("utf-8")), raw, None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, None, f"not UTF-8 JSON: {exc.__class__.__name__}"


def _fail(reason, **extra):
    out = {"schema": SCHEMA, "status": "failed", "reason": reason}
    out.update(extra)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1


def resolve_commit(repo, ref, timeout, max_bytes):
    """Pin the mirror at an exact commit, so the captured bytes cannot move later."""
    payload, _, err = _get_json(f"https://api.github.com/repos/{repo}/commits/{ref}",
                                timeout, max_bytes)
    if payload is None:
        return None, None, err
    sha = payload.get("sha")
    if not isinstance(sha, str) or len(sha) < 7:
        return None, None, f"commit response carries no usable sha: {str(payload)[:200]}"
    commit = (payload.get("commit") or {})
    return sha, {"sha": sha,
                 "author_date": commit.get("author", {}).get("date"),
                 "committer_date": commit.get("committer", {}).get("date"),
                 "message": (commit.get("message") or "").split("\n", 1)[0][:200]}, None


def list_snapshot_dates(repo, sha, timeout, max_bytes):
    payload, _, err = _get_json(f"https://api.github.com/repos/{repo}/contents/data?ref={sha}",
                                timeout, max_bytes)
    if payload is None:
        return [], err
    if not isinstance(payload, list):
        return [], "contents/data is not a list"
    dates = sorted(e["name"] for e in payload
                   if e.get("type") == "dir" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", e.get("name") or ""))
    return dates, None


def raw_url(repo, sha, *parts):
    return "https://raw.githubusercontent.com/" + "/".join([repo, sha, *parts])


def resolve_snapshot(repo, sha, requested_date, dates, timeout, max_bytes, notes):
    """Pick the newest snapshot that actually carries leaderboards.

    Walking back is the whole point: ``latest.json`` on this mirror points at an empty
    snapshot, and an empty snapshot reports no error.
    """
    if requested_date:
        if requested_date not in dates:
            return None, f"--date {requested_date} is not among the {len(dates)} snapshots"
        return requested_date, None
    latest, _, err = _get_json(raw_url(repo, sha, "data", "latest.json"), timeout, max_bytes)
    ordered = list(reversed(dates))
    if isinstance(latest, dict) and latest.get("date"):
        pointer = str(latest["date"])
        ordered = [pointer] + [d for d in ordered if d != pointer]
        notes.append(f"latest.json points at {pointer}; its content is verified before use")
    if err:
        notes.append(f"latest.json unreadable ({err}); walking the snapshot list instead")
    for day in ordered:
        index, _, ierr = _get_json(raw_url(repo, sha, "data", day, "_index.json"),
                                   timeout, max_bytes)
        if index is None:
            continue
        boards = index.get("leaderboards")
        if isinstance(boards, dict) and boards:
            if day != ordered[0]:
                notes.append(f"walked back from {ordered[0]} to {day}: the newer snapshots "
                             f"carry no leaderboards (the mirror's fetch is failing silently)")
            return day, None
    return None, ("no snapshot in this mirror carries any leaderboard; the upstream is "
                  "unreachable to it and there is nothing to capture")


def parse_board_date(value):
    """`Oct 7, 2026` -> date, or None. An unparsable date stays unknown, never today."""
    if not isinstance(value, str):
        return None
    for fmt in ("%b %d, %Y", "%Y-%m-%d", "%d %b %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def norm_key(name):
    """Normalised model key with effort/variant suffixes and display punctuation removed.

    Verified against the 2026-10-07 snapshot: this raises coverage of the active gateway
    catalog from 1/23 to 10/23. It is a **name** match and stays unverified; two board
    rows that normalise to one key are reported ambiguous rather than merged, because
    they are different effort levels and the difference is measurable (57 ELO between
    ``claude-sonnet-5.5-xhigh`` and ``claude-sonnet-5.5-high`` on the code board).
    """
    text = re.sub(r"\(.*?\)", " ", name or "")
    text = text.replace(".", " ").replace("-", " ").replace("_", " ").lower()
    tokens = [t for t in re.split(r"\s+", text) if t]
    while tokens and tokens[-1] in EFFORT_TOKENS:
        tokens.pop()
    return "".join(tokens)


def effort_of(name):
    """The effort/variant token of a board row, or None.

    Arena spells it two ways: a trailing suffix (``claude-sonnet-5.5-xhigh``) and a
    parenthetical (``muse-spark-1.3 (xHigh)``). Both are read. Effort is an attribute of
    the **observation**, never part of the model's identity: ``claude-opus-5-5-max`` is
    ``claude-opus-5-5``, and one model may own several observations at different efforts.
    """
    text = (name or "").lower()
    if re.search(r"x[\s._-]?high", text):
        return "xhigh"
    parens = " ".join(re.findall(r"\((.*?)\)", text))
    tokens = [t for t in re.split(r"[\s._()-]+", text + " " + parens) if t]
    found = [t for t in tokens if t in EFFORT_TOKENS]
    return found[-1] if found else None


def capture(args):
    notes = []
    if not args.fetch:
        return _fail("network egress is opt-in: pass --fetch to capture a snapshot")
    repo = args.repo.strip("/")
    sha, commit, err = resolve_commit(repo, args.ref, args.timeout, args.max_bytes)
    if sha is None:
        return _fail(f"cannot pin the mirror commit: {err}", repo=repo, ref=args.ref,
                     consequence="no snapshot captured; a benchmark source must be pinned "
                                 "or it is not reproducible")
    dates, err = list_snapshot_dates(repo, sha, args.timeout, args.max_bytes)
    if err:
        return _fail(f"cannot list snapshots: {err}", repo=repo, commit=sha)
    if not dates:
        return _fail("the mirror carries no snapshot directories; nothing to capture",
                     repo=repo, commit=sha, snapshots=0)
    notes.append(f"mirror pinned at {repo}@{sha[:12]} ({len(dates)} snapshots, "
                 f"{dates[0]} to {dates[-1]})")
    day, err = resolve_snapshot(repo, sha, args.date, dates, args.timeout, args.max_bytes, notes)
    if day is None:
        return _fail(err, repo=repo, commit=sha, snapshots=len(dates))

    categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    today = datetime.now(timezone.utc).date()
    boards, gaps = {}, []
    for cat in categories:
        payload, raw, cerr = _get_json(raw_url(repo, sha, "data", day, f"{cat}.json"),
                                       args.timeout, args.max_bytes)
        if payload is None:
            gaps.append({"category": cat, "reason": cerr, "status": "unreachable"})
            continue
        rows = payload.get("models")
        if not isinstance(rows, list) or not rows:
            gaps.append({"category": cat, "reason": "no models in the captured file",
                         "status": "empty"})
            continue
        meta = payload.get("meta") or {}
        board_date = parse_board_date(meta.get("last_updated"))
        boards[cat] = {
            "meta": {"leaderboard": meta.get("leaderboard"),
                     "source_url": meta.get("source_url"),
                     "fetched_at": meta.get("fetched_at"),
                     "last_updated": meta.get("last_updated"),
                     "model_count": meta.get("model_count"),
                     "dimensions": meta.get("dimensions")},
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "raw_bytes": len(raw),
            "rows_verbatim": rows,
            "staleness_days": (today - board_date).days if board_date else None,
            "staleness_status": ("unknown" if board_date is None else
                                 "stale" if (today - board_date).days > args.max_staleness_days
                                 else "fresh"),
        }
    if not boards:
        return _fail("every requested category came back empty or unreachable; nothing "
                     "captured", repo=repo, commit=sha, snapshot_date=day, gaps=gaps,
                     consequence="the mirror has no usable data for these categories; a "
                                 "browser-based capture from arena.ai is the remaining path")

    match_index, conflicts = {}, []
    for cat, board in boards.items():
        for row in board["rows_verbatim"]:
            name = row.get("model")
            key = norm_key(name)
            if not key:
                continue
            effort = effort_of(name)
            entry = {"category": cat, "arena_name": name, "effort": effort,
                     "vendor": row.get("vendor"), "license": row.get("license"),
                     "rank": row.get("rank"), "score": row.get("score"),
                     "ci": row.get("ci"), "votes": row.get("votes")}
            bucket = match_index.setdefault(key, [])
            # Two rows in one category AT ONE EFFORT are a genuine identity collision and
            # must be reported. Two rows at different efforts are one model's effort
            # series, which is a measurement, not an ambiguity: on the 2026-10-07 code
            # board the gap inside `claude-sonnet-5.5` is 57 ELO with non-overlapping CIs.
            clash = [e for e in bucket if e["category"] == cat and e["effort"] == effort]
            if clash:
                conflicts.append({"key": key, "category": cat, "effort": effort,
                                  "arena_names": [clash[0]["arena_name"], name],
                                  "vendors": [clash[0]["vendor"], row.get("vendor")],
                                  "reason": "two rows normalise to one model at one effort; "
                                            "they are different artifacts or the normaliser "
                                            "collapsed a distinction it must keep"})
            bucket.append(entry)
    for key, entries in match_index.items():
        for entry in entries:
            peers = [e for e in entries if e["category"] == entry["category"]]
            entry["observations_in_category"] = len(peers)
            entry["efforts_in_category"] = sorted({e["effort"] for e in peers
                                                   if e["effort"] is not None})
            entry["identity_conflict"] = any(
                c["key"] == key and c["category"] == entry["category"] for c in conflicts)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "schema": SCHEMA,
        "status": "captured",
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "kind": "third-party mirror of arena.ai leaderboards",
            "repo": repo,
            "ref": args.ref,
            "commit": commit,
            "snapshot_date": day,
            "snapshot_age_days": (today - parse_board_date(day)).days if parse_board_date(day) else None,
            "raw_base_url": raw_url(repo, sha, "data", day),
        },
        "categories_captured": sorted(boards),
        "categories_requested": categories,
        "gaps": gaps,
        "staleness_gate_days": args.max_staleness_days,
        "boards": boards,
        "match_index": match_index,
        "match_index_semantics": {
            "method": "derived",
            "source": ["arena_name"],
            "confidence": "low",
            "identity": "name-normalized-unverified",
            "identity_rule": "the key is effort-stripped: `claude-opus-5-5-max` IS "
                             "`claude-opus-5-5`. Effort is an attribute of the observation, "
                             "so one model may own several observations in one category, "
                             "and that is a measured effort series, not an ambiguity.",
            "note": "effort/variant suffixes and parentheticals are stripped to make board "
                    "rows comparable to harness model ids; this is a name match, never an "
                    "identity proof",
        },
        "authority": {
            "advisory_only": True,
            "never": ["binds a model", "overrides a harness-declared value",
                      "establishes a tier without a human policy declaration"],
            "preference_rule": "informs a human's tier declaration; the frontier is never "
                               "auto-picked",
            "significance_rule": "ranks whose 95% confidence intervals overlap are not a "
                                 "significant ordering; read rank with ci and votes",
        },
        "measurement_caveat": "Arena ELO measures human preference in chat/agent arenas, "
                              "not this harness's workload; `code` and `agent` are the "
                              "relevant boards for coding work",
        "licence": LICENCE,
        "notes": notes,
    }
    body = json.dumps(snapshot, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8")
    out_path = out_dir / f"arena-{day}.json"
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_bytes(body)
    tmp.replace(out_path)                       # atomic: never a half-written snapshot

    summary = {k: v for k, v in snapshot.items()
               if k not in ("boards", "match_index")}
    summary["out"] = str(out_path)
    summary["out_bytes"] = len(body)
    summary["snapshot_sha256"] = hashlib.sha256(body).hexdigest()
    summary["per_category"] = {
        c: {"rows": len(b["rows_verbatim"]), "raw_sha256": b["raw_sha256"][:16],
            "last_updated": b["meta"]["last_updated"],
            "staleness_days": b["staleness_days"], "staleness_status": b["staleness_status"],
            "raw_bytes": b["raw_bytes"]}
        for c, b in sorted(boards.items())}
    summary["match_keys"] = len(match_index)
    summary["identity_conflicts"] = len(conflicts)
    summary["conflict_rows"] = conflicts[:20]
    summary["models_with_effort_series"] = {
        k: sorted({e["effort"] for e in v if e["effort"]})
        for k, v in sorted(match_index.items())
        if len({(e["category"], e["effort"]) for e in v}) > len({e["category"] for e in v})}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="benchmark_snapshot.py",
        description="Capture and pin a third-party benchmark mirror as advisory evidence.")
    p.add_argument("--out-dir", required=True,
                   help="local ignored storage for the snapshot; never inside the repository")
    p.add_argument("--fetch", action="store_true", help="opt in to network egress")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--ref", default="main")
    p.add_argument("--categories", default=",".join(DEFAULT_CATEGORIES))
    p.add_argument("--date", help="pin a snapshot date instead of resolving the newest non-empty one")
    p.add_argument("--max-staleness-days", type=int, default=DEFAULT_MAX_STALENESS_DAYS)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    p.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    return capture(p.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
