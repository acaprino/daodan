#!/usr/bin/env python3
"""Score every recovery policy for broken files, on spans as well as on names.

run_all.py scored recovery on (qualified name, kind, start line). That is not
enough for a Code Graph: a symbol's span feeds its body hash, so a definition
with the right name and a truncated span is as wrong as an invented one. This
script re-scores the same effective mutated files on spans, and adds the stdlib
policy the first pass lacked.

Policies scored:

  ast-whole       the current adapter: the file is rejected, nothing recovered
  ast-toplevel    longest prefix ending on a TOP-LEVEL statement boundary that
                  parses (ast_worker.salvage, from run_all.py's output)
  ast-anyindent   longest prefix ending on ANY logical-line boundary that parses,
                  boundaries found with the stdlib tokenizer; recovers the
                  methods of a class broken further down
  ast-strict      ast-anyindent without the definitions left open by the cut
                  (their end is the prefix's last statement, so their span may
                  be truncated)
  ts-all          every definition tree-sitter emits
  ts-clean        tree-sitter definitions outside ERROR regions
  ts-prefix       clean tree-sitter definitions starting before the first error

For each policy and file:

  name level   matched / wrong on (q, k, l) against the reference truth
  span level   the truth is split into S, definitions whose span does not
               contain the broken line (their true span is defined), and C, the
               containers of the broken line (their true span in a broken file
               is not). An emission is
                 exact      (q, k, l, e) equals a member of S
                 span-error (q, k, l) is in S but e differs
                 partial    (q, k, l) is in C: necessarily a partial span
                 wrong      (q, k, l) matches nothing
               `unsafe` = span-error + partial + wrong: emissions that would put
               a wrong identity or a wrong body span into the graph.

Span truth uses each parser's own convention on the ORIGINAL file (stdlib ends a
definition at its last statement, tree-sitter after trailing comments), so no
parser is charged for a convention, only for recovery.

Run with the reference interpreter (the same one as ast-3.14-mut.jsonl).
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import sys
import tokenize
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ast_worker import definitions  # noqa: E402

MAX_ATTEMPTS = 60
POLICIES = ("ast-whole", "ast-toplevel", "ast-anyindent", "ast-strict", "ts-all", "ts-clean", "ts-prefix")


def load(path: Path) -> dict:
    records = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            obj = json.loads(line)
            if not obj.get("meta"):
                records[obj["f"]] = obj
    return records


def boundaries(source: str, stop_line: int) -> list[int]:
    """Lines on which a logical line ends, strictly before stop_line, newest first."""
    ends = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.NEWLINE:
                if token.end[0] >= stop_line:
                    break
                ends.append(token.end[0])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return sorted(set(ends), reverse=True)


def salvage_anyindent(source: str, error_line):
    lines = source.splitlines(keepends=True)
    stop = error_line if error_line else len(lines) + 1
    attempts = 0
    for cut in boundaries(source, stop):
        attempts += 1
        if attempts > MAX_ATTEMPTS:
            break
        try:
            tree = ast.parse("".join(lines[:cut]))
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            continue
        last = max((getattr(node, "end_lineno", 0) or 0 for node in tree.body), default=0)
        return {"cut": cut, "attempts": attempts, "defs": definitions(tree), "last": last}
    return {"cut": 0, "attempts": attempts, "defs": [], "last": 0}


def shift_of(row):
    if row["mutation"] == "merge-conflict":
        return (row["where"], 1, 4), None
    if row["mutation"] == "truncate-mid-body":
        return None, row["where"]
    return None, None


def map_line(line, shift):
    if shift is None:
        return line
    k, at, after = shift
    if line < k:
        return line
    if line == k:
        return line + at
    return line + after


def truth_sets(original_defs, row):
    """(T multiset of (q,k,l,e), S subset with defined spans, C containers)."""
    shift, limit = shift_of(row)
    where = row["where"]
    full, scored, containers = Counter(), Counter(), Counter()
    for d in original_defs:
        if limit is not None and d["l"] > limit:
            continue
        item = (d["q"], d["k"], map_line(d["l"], shift), map_line(d["e"], shift))
        full[item] += 1
        contains = d["l"] <= where <= d["e"] if limit is None else d["e"] > limit
        (containers if contains else scored)[item] += 1
    return full, scored, containers


def score(emitted, truth_qkl, scored, containers):
    E = Counter((d["q"], d["k"], d["l"], d["e"]) for d in emitted)
    E_qkl = Counter((q, k, l) for (q, k, l, _e), n in E.items() for _ in range(n))
    out = Counter()
    out["truth"] = sum(truth_qkl.values())
    out["emitted"] = sum(E.values())
    out["matched"] = sum((E_qkl & truth_qkl).values())
    out["wrong"] = sum((E_qkl - truth_qkl).values())
    out["scored_truth"] = sum(scored.values())
    exact = E & scored
    out["exact"] = sum(exact.values())
    remaining = E - exact
    scored_qkl = Counter((q, k, l) for (q, k, l, _e), n in scored.items() for _ in range(n))
    container_qkl = Counter((q, k, l) for (q, k, l, _e), n in containers.items() for _ in range(n))
    for (q, k, l, _e), n in remaining.items():
        key = (q, k, l)
        for _ in range(n):
            if container_qkl[key] > 0:
                out["partial"] += 1
                container_qkl[key] -= 1
            elif scored_qkl[key] > 0:
                out["span_error"] += 1
                scored_qkl[key] -= 1
    out["unsafe"] = out["span_error"] + out["partial"] + out["wrong"]
    return out


def pct(part, whole):
    return f"{100.0 * part / whole:6.2f}%" if whole else "   n/a"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    reference = meta["reference"]
    rows = [json.loads(line) for line in (out / "mut" / "truth.jsonl").read_text(encoding="utf-8").splitlines() if line]
    ast_mut = load(out / f"ast-{reference}-mut.jsonl")
    ts_mut = load(out / "ts-mut.jsonl")
    ast_orig = {c: load(out / f"ast-{reference}-{c}.jsonl") for c in meta["mutation_corpora"]}
    ts_orig = {c: load(out / f"ts-{c}.jsonl") for c in meta["mutation_corpora"]}

    totals = {p: Counter() for p in POLICIES}
    per_mutation = defaultdict(lambda: {p: Counter() for p in POLICIES})
    attempts = Counter()
    examples = defaultdict(list)
    effective = 0

    for row in rows:
        a, t = ast_mut.get(row["f"]), ts_mut.get(row["f"])
        if a is None or t is None or a.get("ok"):
            continue
        source_ast = ast_orig[row["corpus"]].get(row["source"])
        source_ts = ts_orig[row["corpus"]].get(row["source"])
        if not source_ast or not source_ts:
            continue
        effective += 1
        truth_qkl = Counter((d["q"], d["k"], d["l"]) for d in row["truth"])
        _, s_ast, c_ast = truth_sets(source_ast["defs"], row)
        _, s_ts, c_ts = truth_sets(source_ts["defs"], row)

        text = Path(row["f"]).read_text(encoding="utf-8")
        any_rec = salvage_anyindent(text, (a.get("err") or {}).get("line"))
        attempts[min(any_rec["attempts"], MAX_ATTEMPTS)] += 1
        strict = [d for d in any_rec["defs"] if d["e"] < any_rec["last"]]
        first_error = ((t.get("err") or {}).get("first") or [10 ** 9])[0]

        emitted = {
            "ast-whole": ([], s_ast, c_ast),
            "ast-toplevel": ((a.get("salvage") or {}).get("defs", []), s_ast, c_ast),
            "ast-anyindent": (any_rec["defs"], s_ast, c_ast),
            "ast-strict": (strict, s_ast, c_ast),
            "ts-all": (t["defs"], s_ts, c_ts),
            "ts-clean": ([d for d in t["defs"] if not d.get("x")], s_ts, c_ts),
            "ts-prefix": ([d for d in t["defs"] if not d.get("x") and d["l"] < first_error], s_ts, c_ts),
        }
        for policy, (defs, scored, containers) in emitted.items():
            result = score(defs, truth_qkl, scored, containers)
            totals[policy].update(result)
            per_mutation[row["mutation"]][policy].update(result)
            if result["unsafe"] and len(examples[policy]) < 40:
                examples[policy].append(f"{row['f']} ({row['mutation']}, where {row['where']}) "
                                        f"partial={result['partial']} span_error={result['span_error']} "
                                        f"wrong={result['wrong']}")

    print(f"effective mutated files: {effective} (reference parser rejects each one)")
    print(f"ast-anyindent attempts per file: {dict(sorted(attempts.items()))}\n")
    header = (f"  {'policy':14} {'name recall':>12} {'name prec.':>11} {'span exact':>11} "
              f"{'span-err':>9} {'partial':>8} {'wrong':>6} {'UNSAFE':>7}")
    print(header)
    for policy in POLICIES:
        c = totals[policy]
        print(f"  {policy:14} {pct(c['matched'], c['truth']):>12} {pct(c['matched'], c['emitted']):>11} "
              f"{pct(c['exact'], c['scored_truth']):>11} {c['span_error']:>9} {c['partial']:>8} "
              f"{c['wrong']:>6} {c['unsafe']:>7}")
    print("\n  name recall / unsafe emissions, per mutation:")
    print("  " + f"{'mutation':20}" + "".join(f"{p:>20}" for p in POLICIES))
    for mutation, by_policy in sorted(per_mutation.items()):
        cells = "".join(f"{pct(by_policy[p]['matched'], by_policy[p]['truth']).strip() + ' / ' + str(by_policy[p]['unsafe']):>20}"
                        for p in POLICIES)
        print(f"  {mutation:20}{cells}")

    examples_dir = out / "examples"
    examples_dir.mkdir(exist_ok=True)
    for policy, lines in examples.items():
        (examples_dir / f"S-{policy}-unsafe.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "summary-salvage.json").write_text(json.dumps({
        "effective": effective, "attempts": dict(attempts),
        "totals": {p: dict(c) for p, c in totals.items()},
        "per_mutation": {m: {p: dict(c) for p, c in v.items()} for m, v in per_mutation.items()},
    }, indent=2), encoding="utf-8")
    print(f"\nwrote {out / 'summary-salvage.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
