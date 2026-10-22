#!/usr/bin/env python3
"""Compare LibCST against the reference stdlib ast on the corpora run_all.py listed.

Reads ast-<reference>-<corpus>.jsonl and cst-<corpus>.jsonl from --out. Column is
not compared (LibCST exposes no position for the `def` keyword, see
libcst_worker.py). Line is compared, and every disagreement is written to
examples/K-*.txt with file and line.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path


def load(path: Path):
    records = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            obj = json.loads(line)
            if not obj.get("meta"):
                records[obj["f"]] = obj
    return records


def key(d):
    return (d["q"], d["k"], d["l"])


def pct(part, whole):
    return f"{100.0 * part / whole:.2f}%" if whole else "n/a"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    reference = meta["reference"]
    examples_dir = out / "examples"
    examples_dir.mkdir(exist_ok=True)
    summary = {}
    print(f"== K. LibCST versus stdlib ast {reference}")
    for corpus, info in meta["corpora"].items():
        cst_path = out / f"cst-{corpus}.jsonl"
        if not cst_path.exists():
            print(f"  {corpus}: no LibCST run")
            continue
        files = [line for line in Path(info["list"]).read_text(encoding="utf-8").splitlines() if line]
        ref = load(out / f"ast-{reference}-{corpus}.jsonl")
        cst = load(cst_path)
        stats = Counter()
        lines = {"ast-only": [], "cst-only": [], "status": [], "imports": []}
        times = []
        for path in files:
            a, c = ref.get(path, {}), cst.get(path, {})
            if "t" in c:
                times.append(c["t"])
            a_ok, c_ok = bool(a.get("ok")), bool(c.get("ok"))
            stats[f"status:{'ast' if a_ok else '-'}/{'cst' if c_ok else '-'}"] += 1
            if a_ok != c_ok:
                err = (c.get("err") or a.get("err") or {})
                lines["status"].append(f"{path} ast_ok={a_ok} cst_ok={c_ok} {err.get('type')}: {err.get('msg')}")
            if not (a_ok and c_ok):
                continue
            A = Counter(key(d) for d in a["defs"])
            C = Counter(key(d) for d in c["defs"])
            stats["ast_defs"] += sum(A.values())
            stats["cst_defs"] += sum(C.values())
            stats["matched"] += sum((A & C).values())
            for item in (A - C).elements():
                lines["ast-only"].append(f"{path}:{item[2]} {item[1]} {item[0]}")
            for item in (C - A).elements():
                lines["cst-only"].append(f"{path}:{item[2]} {item[1]} {item[0]}")
            ka = {key(d): d for d in a["defs"]}
            kc = {key(d): d for d in c["defs"]}
            for k in A & C:
                if ka[k]["d"] != kc[k]["d"]:
                    stats["decorators_differ"] += 1
                if ka[k]["b"] != kc[k]["b"]:
                    stats["block_flag_differs"] += 1
                if ka[k]["e"] != kc[k]["e"]:
                    stats["end_line_differs"] += 1
            IA = Counter(tuple(i) for i in a["imps"])
            IC = Counter(tuple(i) for i in c["imps"])
            stats["ast_imports"] += sum(IA.values())
            stats["imports_matched"] += sum((IA & IC).values())
            for item in (IA - IC).elements():
                lines["imports"].append(f"{path}: ast-only {list(item)}")
            for item in (IC - IA).elements():
                lines["imports"].append(f"{path}: cst-only {list(item)}")
        for bucket, rows in lines.items():
            if rows:
                (examples_dir / f"K-{corpus}-{bucket}.txt").write_text("\n".join(rows[:300]) + "\n",
                                                                      encoding="utf-8")
        times.sort()
        timing = {"total_s": sum(times), "median_ms": 1000 * statistics.median(times) if times else None}
        summary[corpus] = {**stats, "timing": timing}
        status = {k[7:]: v for k, v in stats.items() if k.startswith("status:")}
        print(f"\n  {corpus} ({len(files)} files)  status ast/cst: {status}")
        print(f"    definitions ast={stats['ast_defs']} cst={stats['cst_defs']} matched={stats['matched']} "
              f"({pct(stats['matched'], stats['ast_defs'])})  ast-only {len(lines['ast-only'])}  "
              f"cst-only {len(lines['cst-only'])}")
        print(f"    imports matched {stats['imports_matched']}/{stats['ast_imports']} "
              f"({pct(stats['imports_matched'], stats['ast_imports'])})")
        print(f"    on matched: decorators differ {stats['decorators_differ']}, block flag differs "
              f"{stats['block_flag_differs']}, end line differs {stats['end_line_differs']}")
        print(f"    time: {timing['total_s']:.2f}s total, median {timing['median_ms']:.2f} ms")
    (out / "summary-cst.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
