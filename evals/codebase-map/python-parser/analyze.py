#!/usr/bin/env python3
"""Turn the raw measurements of run_all.py into the comparison and its evidence.

Every disagreement counted here is also written, with file and line, to
examples/*.txt under --out, because a count that nobody checked against source
is not evidence of which parser is right.

Sections:
  A  parse status per corpus and interpreter
  B  reference-parser failures, and failures that depend on the interpreter
  C  structural agreement on files both parsers accept
  D  tree-sitter errors on files the reference parser accepts
  E  files only tree-sitter accepts
  F  syntax-feature matrix
  G  work-in-progress corpus: what each parser recovers, and whether it is right
  H  parse time
  I  what the current adapter's extraction convention drops (parser-independent)
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from features import FEATURES  # noqa: E402


def load(path: Path):
    meta, records = None, {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            obj = json.loads(line)
            if obj.get("meta"):
                meta = obj
            else:
                records[obj["f"]] = obj
    return meta, records


def vkey(version: str):
    return tuple(int(part) for part in version.split("."))


def defkey(d):
    return (d["q"], d["k"], d["l"])


def pct(part, whole):
    return f"{100.0 * part / whole:.2f}%" if whole else "n/a"


class Examples:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.buckets = defaultdict(list)

    def add(self, bucket: str, line: str, cap: int = 200):
        if len(self.buckets[bucket]) < cap:
            self.buckets[bucket].append(line)

    def flush(self):
        for bucket, lines in self.buckets.items():
            (self.root / f"{bucket}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def classify_unmatched(item, other_items):
    """Why is a definition present on one side only."""
    q, k, line = item
    same_q_k = [o for o in other_items if o[0] == q and o[1] == k]
    if same_q_k:
        return "line-differs"
    last = q.rsplit(".", 1)[-1]
    same_name_line = [o for o in other_items if o[2] == line and o[0].rsplit(".", 1)[-1] == last]
    if same_name_line:
        if any(o[1] != k for o in same_name_line):
            return "kind-differs"
        return "nesting-differs"
    return "absent"


def section_structural(corpus, files, ref, ts, examples, summary):
    stats = Counter()
    unmatched = Counter()
    for path in files:
        a, t = ref.get(path), ts.get(path)
        if not a or not t or not a.get("ok") or not t.get("ok"):
            continue
        stats["files"] += 1
        A = Counter(defkey(d) for d in a["defs"])
        T = Counter(defkey(d) for d in t["defs"])
        both = A & T
        stats["ast_defs"] += sum(A.values())
        stats["ts_defs"] += sum(T.values())
        stats["matched"] += sum(both.values())
        a_only, t_only = A - T, T - A
        for item in a_only.elements():
            why = classify_unmatched(item, list(t_only))
            unmatched[f"ast-only:{why}"] += 1
            examples.add(f"C-{corpus}-ast-only", f"{path}:{item[2]} {item[1]} {item[0]} [{why}]")
        for item in t_only.elements():
            why = classify_unmatched(item, list(a_only))
            unmatched[f"ts-only:{why}"] += 1
            examples.add(f"C-{corpus}-ts-only", f"{path}:{item[2]} {item[1]} {item[0]} [{why}]")
        by_key_a = {defkey(d): d for d in a["defs"]}
        by_key_t = {defkey(d): d for d in t["defs"]}
        for key in both:
            da, dt = by_key_a[key], by_key_t[key]
            if da["c"] != dt["c"]:
                stats["column_differs"] += 1
                examples.add(f"C-{corpus}-column", f"{path}:{key[2]} {key[0]} ast={da['c']} ts={dt['c']}")
            if da["e"] != dt["e"]:
                stats["end_line_differs"] += 1
                examples.add(f"C-{corpus}-end-line", f"{path}:{key[2]} {key[0]} ast={da['e']} ts={dt['e']}", cap=60)
            if da["d"] != dt["d"]:
                stats["decorators_differ"] += 1
                examples.add(f"C-{corpus}-decorators", f"{path}:{key[2]} {key[0]} ast={da['d']} ts={dt['d']}")
            if da["b"] != dt["b"]:
                stats["block_flag_differs"] += 1
                examples.add(f"C-{corpus}-block-flag", f"{path}:{key[2]} {key[0]} ast={da['b']} ts={dt['b']}")
        IA = Counter(tuple(i) for i in a["imps"])
        IT = Counter(tuple(i) for i in t["imps"])
        stats["ast_imports"] += sum(IA.values())
        stats["ts_imports"] += sum(IT.values())
        stats["imports_matched"] += sum((IA & IT).values())
        for item in (IA - IT).elements():
            examples.add(f"C-{corpus}-imports-ast-only", f"{path}: {list(item)}")
        for item in (IT - IA).elements():
            examples.add(f"C-{corpus}-imports-ts-only", f"{path}: {list(item)}")
    summary["C"][corpus] = {**stats, "unmatched": dict(unmatched)}
    print(f"\n  {corpus}: {stats['files']} files accepted by both")
    print(f"    definitions  ast={stats['ast_defs']}  ts={stats['ts_defs']}  "
          f"matched={stats['matched']}  ({pct(stats['matched'], stats['ast_defs'])} of ast)")
    for reason, count in sorted(unmatched.items()):
        print(f"      {reason:28} {count}")
    print(f"    imports      ast={stats['ast_imports']}  ts={stats['ts_imports']}  "
          f"matched={stats['imports_matched']}  ({pct(stats['imports_matched'], stats['ast_imports'])})")
    print(f"    on matched definitions: column differs {stats['column_differs']}, "
          f"end line differs {stats['end_line_differs']}, decorators differ "
          f"{stats['decorators_differ']}, block flag differs {stats['block_flag_differs']}")


def section_ts_errors_on_valid(corpus, files, ref, ts, examples, summary):
    count = recovered = expected = emitted = 0
    for path in files:
        a, t = ref.get(path), ts.get(path)
        if not a or not t or not a.get("ok") or t.get("ok"):
            continue
        count += 1
        err = t.get("err") or {}
        first = err.get("first")
        examples.add(f"D-{corpus}-ts-error-on-valid",
                     f"{path}:{first[0] if first else '?'}:{first[1] if first else '?'} "
                     f"errors={err.get('errors')} missing={err.get('missing')}")
        A = Counter(defkey(d) for d in a["defs"])
        T = Counter(defkey(d) for d in t["defs"])
        recovered += sum((A & T).values())
        expected += sum(A.values())
        emitted += sum(T.values())
    summary["D"][corpus] = {"files": count, "ast_defs": expected, "ts_defs": emitted,
                            "ts_correct": recovered}
    print(f"  {corpus}: {count} files valid for the reference parser that tree-sitter "
          f"marks with ERROR/MISSING; on them it still emits {recovered}/{expected} "
          f"definitions correctly ({emitted} emitted)")


def section_features(versions, out, summary):
    ts_meta, ts_records = load(out / "ts-features.jsonl")
    ast_runs = {v: load(out / f"ast-{v}-features.jsonl")[1] for v in versions}
    header = "  " + f"{'feature':38}" + "".join(f"{('ast ' + v):>11}" for v in versions) + f"{'ts':>8}"
    print(header)
    rows = {}
    for case in FEATURES:
        cid = case["id"]
        expect = Counter(case["expect"])
        cells = {}
        line = f"  {cid:38}"
        for v in versions:
            rec = ast_runs[v][cid]
            valid_here = case.get("valid", True) and case["min"] is not None and vkey(v) >= vkey(case["min"])
            if rec["ok"]:
                got = Counter(d["q"] for d in rec["defs"])
                cell = "ok" if got == expect else "ok-diff"
                if not valid_here:
                    cell = "ACCEPTS"
            else:
                cell = "rejects" if not valid_here else "FAILS"
            cells[f"ast {v}"] = cell
            line += f"{cell:>11}"
        rec = ts_records[cid]
        got = Counter(d["q"] for d in rec["defs"])
        if rec["ok"]:
            cell = "ok" if got == expect else "ok-diff"
        else:
            cell = "err+ok" if got == expect else "err"
        cells["ts"] = cell
        cells["ts_defs"] = [d["q"] for d in rec["defs"]]
        line += f"{cell:>8}"
        rows[cid] = cells
        print(line)
    summary["F"] = rows
    print("\n  legend: ok = accepted, definitions as expected; ok-diff = accepted, definitions differ;")
    print("          rejects = correctly rejected below its version or invalid; FAILS = wrongly rejected;")
    print("          ACCEPTS = accepted although invalid here; err = ERROR nodes and wrong definitions;")
    print("          err+ok = ERROR nodes but the expected definitions still emitted")


def section_mutations(out, reference, examples, summary):
    truth_rows = [json.loads(line) for line in (out / "mut" / "truth.jsonl").read_text(encoding="utf-8").splitlines() if line]
    _, ast_mut = load(out / f"ast-{reference}-mut.jsonl")
    _, ts_mut = load(out / "ts-mut.jsonl")
    per_type = defaultdict(Counter)
    totals = Counter()
    for row in truth_rows:
        path, mutation = row["f"], row["mutation"]
        a = ast_mut.get(path)
        t = ts_mut.get(path)
        if a is None or t is None:
            continue
        if a.get("ok"):
            per_type[mutation]["ineffective"] += 1
            totals["ineffective"] += 1
            continue
        per_type[mutation]["files"] += 1
        totals["files"] += 1
        truth = Counter((d["q"], d["k"], d["l"]) for d in row["truth"])
        truth_items = list(truth.elements())
        n_truth = len(truth_items)
        first_error = ((t.get("err") or {}).get("first") or [10 ** 9])[0]
        subsets = (
            ("all", t["defs"]),
            ("clean", [d for d in t["defs"] if not d.get("x")]),
            ("prefix", [d for d in t["defs"] if not d.get("x") and d["l"] < first_error]),
        )
        for subset, defs in subsets:
            emitted = Counter(defkey(d) for d in defs)
            matched = sum((emitted & truth).values())
            invented = misplaced = 0
            for item in (emitted - truth).elements():
                last = item[0].rsplit(".", 1)[-1]
                if any(tq.rsplit(".", 1)[-1] == last and tk == item[1] and tl == item[2]
                       for tq, tk, tl in truth_items):
                    misplaced += 1
                    if subset == "all":
                        examples.add("G-misplaced", f"{path}:{item[2]} {item[0]} ({mutation}, source {row['source']})")
                else:
                    invented += 1
                    if subset == "all":
                        examples.add("G-invented", f"{path}:{item[2]} {item[1]} {item[0]} ({mutation}, source {row['source']})")
            for key, value in (("truth", n_truth), ("emitted", sum(emitted.values())),
                               ("matched", matched), ("misplaced", misplaced), ("invented", invented)):
                per_type[mutation][f"{subset}_{key}"] += value
                totals[f"{subset}_{key}"] += value
    # stdlib salvage: the longest prefix ending on a top-level statement that
    # still parses (ast_worker.salvage). Measured on the same effective files.
    salvage = Counter()
    salvage_per_type = defaultdict(Counter)
    for row in truth_rows:
        a = ast_mut.get(row["f"])
        if a is None or a.get("ok"):
            continue
        truth = Counter((d["q"], d["k"], d["l"]) for d in row["truth"])
        rec = a.get("salvage") or {}
        emitted = Counter(defkey(d) for d in rec.get("defs", []))
        matched = sum((emitted & truth).values())
        wrong = sum((emitted - truth).values())
        for target in (salvage, salvage_per_type[row["mutation"]]):
            target["truth"] += sum(truth.values())
            target["emitted"] += sum(emitted.values())
            target["matched"] += matched
            target["wrong"] += wrong
        for item in (emitted - truth).elements():
            examples.add("G-salvage-wrong", f"{row['f']}:{item[2]} {item[1]} {item[0]} ({row['mutation']})")

    summary["G"] = {"totals": dict(totals), "per_mutation": {k: dict(v) for k, v in per_type.items()},
                    "ast_salvage": dict(salvage),
                    "ast_salvage_per_mutation": {k: dict(v) for k, v in salvage_per_type.items()}}
    print(f"  effective mutated files: {totals['files']}   ineffective (reference still parses): "
          f"{totals['ineffective']}")
    print(f"  stdlib ast, whole file: rejects every effective file, recovers 0 of "
          f"{totals['all_truth']} definitions, emits nothing wrong")
    print(f"  stdlib ast, prefix salvage (longest top-level prefix that parses):")
    print(f"    recall {pct(salvage['matched'], salvage['truth'])} ({salvage['matched']}/{salvage['truth']})"
          f"   precision {pct(salvage['matched'], salvage['emitted'])} ({salvage['matched']}/{salvage['emitted']})"
          f"   wrong {salvage['wrong']}")
    for mutation, c in sorted(salvage_per_type.items()):
        print(f"      {mutation:20} recall {pct(c['matched'], c['truth']):>8}  precision "
              f"{pct(c['matched'], c['emitted']):>8}  wrong {c['wrong']}")
    for subset, label in (("all", "tree-sitter, every definition"),
                          ("clean", "tree-sitter, only definitions outside ERROR regions"),
                          ("prefix", "tree-sitter, only clean definitions before the first error")):
        truth = totals[f"{subset}_truth"]
        emitted = totals[f"{subset}_emitted"]
        matched = totals[f"{subset}_matched"]
        print(f"  {label}:")
        print(f"    recall {pct(matched, truth)} ({matched}/{truth})   precision {pct(matched, emitted)} "
              f"({matched}/{emitted})   misplaced {totals[f'{subset}_misplaced']}   invented "
              f"{totals[f'{subset}_invented']}")
    print("  per mutation (tree-sitter: every definition / outside ERROR regions / before first error):")
    for mutation, c in sorted(per_type.items()):
        print(f"    {mutation:20} files={c['files']:4} ineffective={c['ineffective']:3}  "
              f"recall {pct(c['all_matched'], c['all_truth']):>8} / {pct(c['clean_matched'], c['clean_truth']):>8}"
              f" / {pct(c['prefix_matched'], c['prefix_truth']):>8}  "
              f"precision {pct(c['all_matched'], c['all_emitted']):>8} / {pct(c['clean_matched'], c['clean_emitted']):>8}"
              f" / {pct(c['prefix_matched'], c['prefix_emitted']):>8}  "
              f"wrong {c['all_misplaced'] + c['all_invented']:4} / {c['clean_misplaced'] + c['clean_invented']:4}"
              f" / {c['prefix_misplaced'] + c['prefix_invented']:4}")


def section_convention(corpus, files, ref, summary):
    total = recorded = 0
    reasons = Counter()
    for path in files:
        a = ref.get(path)
        if not a or not a.get("ok"):
            continue
        defs = a["defs"]
        first_by_q = {}
        for d in defs:
            first_by_q.setdefault(d["q"], d)
        for d in defs:
            total += 1
            depth = d["q"].count(".")
            if d["k"] == "type":
                reasons["type alias"] += 1
                continue
            if depth == 0 and d["b"] == 0:
                recorded += 1
                continue
            if depth == 0:
                reasons["module level, inside if/try/with/for"] += 1
                continue
            if "d" in d["a"].split("."):
                reasons["nested inside a function"] += 1
                continue
            if d["a"] == "c" and d["k"] != "class":
                parent = first_by_q.get(d["q"].rsplit(".", 1)[0])
                if parent and parent["b"] == 0 and d["b"] == 0:
                    recorded += 1
                elif d["b"] == 1:
                    reasons["method inside if/try in a class body"] += 1
                else:
                    reasons["method of a class inside if/try"] += 1
                continue
            reasons["nested class, or member of one"] += 1
    summary["I"][corpus] = {"definitions": total, "recorded": recorded, "dropped": dict(reasons)}
    print(f"  {corpus}: {total} definitions, the adapter records {recorded} ({pct(recorded, total)}), "
          f"drops {total - recorded}")
    for reason, count in reasons.most_common():
        print(f"      {reason:42} {count}")


def section_time(corpus, versions, runs, ts, summary):
    out = {}
    for label, records in [(f"ast {v}", runs[v]) for v in versions] + [("tree-sitter", ts)]:
        times = [r["t"] for r in records.values() if "t" in r]
        if not times:
            continue
        times.sort()
        out[label] = {"total_s": sum(times), "median_ms": 1000 * statistics.median(times),
                      "p95_ms": 1000 * times[int(len(times) * 0.95) - 1] if len(times) > 1 else 1000 * times[0]}
    summary["H"][corpus] = out
    cells = "  ".join(f"{k}: {v['total_s']:.2f}s (med {v['median_ms']:.2f} ms)" for k, v in out.items())
    print(f"  {corpus}: {cells}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--meta", type=Path, default=None,
                    help="meta.json to use instead of <out>/meta.json, for a phase that has not finished")
    ap.add_argument("--skip", default="", help="comma list of sections to skip, e.g. G")
    args = ap.parse_args()
    out = args.out
    meta = json.loads((args.meta or (out / "meta.json")).read_text(encoding="utf-8"))
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    versions = sorted(meta["interpreters"], key=vkey)
    reference = meta["reference"]
    examples = Examples(out / "examples")
    summary = {k: {} for k in "ABCDEHIJ"}
    ts_meta, _ = load(out / f"ts-{next(iter(meta['corpora']))}.jsonl")
    print(f"engines: stdlib ast under {', '.join(versions)} (reference {reference}); "
          f"tree-sitter-python ABI {ts_meta.get('abi')} on CPython {ts_meta.get('python')}")

    loaded = {}
    print("\n== A. parse status (files accepted)")
    for corpus, info in meta["corpora"].items():
        files = [line for line in Path(info["list"]).read_text(encoding="utf-8").splitlines() if line]
        runs = {v: load(out / f"ast-{v}-{corpus}.jsonl")[1] for v in versions}
        _, ts = load(out / f"ts-{corpus}.jsonl")
        loaded[corpus] = (files, runs, ts)
        n = len(files)
        row = {v: sum(1 for f in files if runs[v].get(f, {}).get("ok")) for v in versions}
        ts_clean = sum(1 for f in files if ts.get(f, {}).get("ok"))
        ref = runs[reference]
        cross = Counter((bool(ref.get(f, {}).get("ok")), bool(ts.get(f, {}).get("ok"))) for f in files)
        summary["A"][corpus] = {"files": n, "ast_ok": row, "ts_clean": ts_clean,
                                "both_ok": cross[(True, True)], "ast_only": cross[(True, False)],
                                "ts_only": cross[(False, True)], "neither": cross[(False, False)]}
        cells = "  ".join(f"ast {v} {row[v]} ({pct(row[v], n)})" for v in versions)
        print(f"  {corpus} ({n}): {cells}  tree-sitter clean {ts_clean} ({pct(ts_clean, n)})")
        print(f"      vs reference {reference}: both {cross[(True, True)]}, only ast {cross[(True, False)]}, "
              f"only tree-sitter {cross[(False, True)]}, neither {cross[(False, False)]}")

    print("\n== B. reference-parser failures, and interpreter-dependent failures")
    for corpus, (files, runs, ts) in loaded.items():
        ref = runs[reference]
        messages = Counter()
        for f in files:
            r = ref.get(f, {})
            if not r.get("ok"):
                err = r.get("err", {})
                messages[f"{err.get('type')}: {err.get('msg')}"] += 1
                examples.add(f"B-{corpus}-reference-fails", f"{f}:{err.get('line')} {err.get('type')}: {err.get('msg')}")
        dependent = {}
        for v in versions:
            if v == reference:
                continue
            fails_here = [f for f in files if ref.get(f, {}).get("ok") and not runs[v].get(f, {}).get("ok")]
            dependent[v] = len(fails_here)
            for f in fails_here:
                err = runs[v][f].get("err", {})
                examples.add(f"B-{corpus}-fails-only-on-{v}", f"{f}:{err.get('line')} {err.get('msg')}")
        summary["B"][corpus] = {"reference_failures": dict(messages), "fails_only_on": dependent}
        print(f"  {corpus}: reference failures {sum(messages.values())}; valid on {reference} but "
              f"rejected on: " + ", ".join(f"{v} {n}" for v, n in dependent.items()))
        for message, count in messages.most_common(6):
            print(f"      {count:5}  {message}")

    print("\n== C. structural agreement on files both parsers accept (reference = ast "
          f"{reference})")
    for corpus, (files, runs, ts) in loaded.items():
        section_structural(corpus, files, runs[reference], ts, examples, summary)

    print("\n== D. tree-sitter ERROR on files the reference parser accepts")
    for corpus, (files, runs, ts) in loaded.items():
        section_ts_errors_on_valid(corpus, files, runs[reference], ts, examples, summary)

    print("\n== E. files only tree-sitter accepts")
    for corpus, (files, runs, ts) in loaded.items():
        ref = runs[reference]
        only = [f for f in files if not ref.get(f, {}).get("ok") and ts.get(f, {}).get("ok")]
        summary["E"][corpus] = len(only)
        for f in only:
            err = ref.get(f, {}).get("err", {})
            examples.add(f"E-{corpus}-ts-only-accepts", f"{f}:{err.get('line')} reference says {err.get('msg')}")
        print(f"  {corpus}: {len(only)}")

    print("\n== F. syntax-feature matrix")
    section_features(versions, out, summary)

    print("\n== G. work-in-progress corpus")
    if "G" in skip:
        print("  skipped on request")
    else:
        section_mutations(out, reference, examples, summary)

    print("\n== H. parse time (parser call only)")
    for corpus, (files, runs, ts) in loaded.items():
        section_time(corpus, versions, runs, ts, summary)

    print("\n== I. definitions the current adapter's convention drops (parser-independent, "
          f"ast {reference})")
    for corpus, (files, runs, ts) in loaded.items():
        section_convention(corpus, files, runs[reference], summary)

    print("\n== J. grammar-version selection: what each interpreter would have to do")
    print("  For every file rejected by at least one interpreter: the oldest interpreter that")
    print("  accepts it, and whether an older one silently returns a different tree.")
    summary["J"] = {}
    for corpus, (files, runs, ts) in loaded.items():
        accept_profile = Counter()
        tree_differs = []
        for f in files:
            status = tuple(bool(runs[v].get(f, {}).get("ok")) for v in versions)
            if all(status):
                defs_by_version = {v: Counter(defkey(d) for d in runs[v][f]["defs"]) for v in versions}
                first = defs_by_version[versions[0]]
                if any(defs_by_version[v] != first for v in versions[1:]):
                    tree_differs.append(f)
                    examples.add(f"J-{corpus}-tree-differs-across-versions", f)
                continue
            label = "".join("A" if ok else "-" for ok in status)
            accept_profile[label] += 1
            examples.add(f"J-{corpus}-profile-{label}", f)
        summary["J"][corpus] = {"profiles": dict(accept_profile), "accepted_by_all_but_tree_differs": len(tree_differs)}
        legend = "".join(v[-2:] + " " for v in versions)
        print(f"  {corpus}: acceptance profile over [{legend.strip()}] (A = accepts): "
              f"{dict(accept_profile) or 'every file accepted by every version'}; accepted by all "
              f"but definitions differ: {len(tree_differs)}")

    examples.flush()
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {out / 'summary.json'} and {out / 'examples'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
