# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Quantify how often the probed LSP character really lands on the callee name.

`lsp_edges.py` located the callee by `line_text.find(parts[-1], c0)`. Two ways
that can miss, both found by hand-checking Rust edges:

* prefix match - `max` matches inside `max_attempts`, so the probe lands on an
  unrelated identifier that merely starts with the method name;
* span start - for a callee whose span crosses lines, `c0` is on the first line
  and the name is on a later one, so the forward search finds a same-named local
  declaration before it ever reaches the call.

This reads each result JSON, re-reads the source line at the recorded probe
position, and classifies it. Read-only.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

IDENT = re.compile(r"[A-Za-z0-9_$]")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, action="append", required=True)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--examples", type=int, default=6)
    args = parser.parse_args()

    report = {}
    for path in args.result:
        data = json.loads(path.read_text(encoding="utf-8"))
        source_root = Path(data["workspace"]["source_root"])
        cache: dict[str, list[str]] = {}
        tally = collections.Counter()
        by_verdict = collections.defaultdict(collections.Counter)
        samples = collections.defaultdict(list)
        for record in data.get("records") or []:
            call = record["call_site"]
            callee = record.get("callee") or ""
            method = callee.split(".")[-1] if callee else ""
            if not method:
                tally["no-named-callee(dynamic)"] += 1
                continue
            file = call["file"]
            if file not in cache:
                try:
                    cache[file] = (source_root / file).read_text(
                        encoding="utf-8", errors="replace").splitlines()
                except OSError:
                    cache[file] = []
            lines = cache[file]
            lsp_line = call["lsp_line0"]
            char = call["lsp_character0"]
            if lsp_line >= len(lines):
                tally["line-out-of-range"] += 1
                continue
            text = lines[lsp_line]
            at = text[char:char + len(method)]
            after = text[char + len(method):char + len(method) + 1]
            if at == method and not (after and IDENT.match(after)):
                kind = "exact-callee"
            elif at == method:
                kind = "prefix-of-longer-identifier"
            elif method in text:
                kind = "name-on-line-but-not-at-probe"
            else:
                kind = "name-not-on-probed-line"

            # Second defect: the probe takes the FIRST boundary-matched
            # occurrence at or after c0, but the callee name is the LAST one in
            # the recorded span. When the span covers `let x = a.b.x(...)` the
            # first occurrence is the local binding being declared, not the call.
            span_occurrences = None
            probe_is_last_in_span = None
            record_span = record.get("span")
            if record_span and len(record_span) == 4:
                sl0, sc0, sl1, sc1 = record_span
                if None not in record_span and 0 < sl0 <= len(lines) and 0 < sl1 <= len(lines):
                    if sl0 == sl1:
                        span_text = lines[sl0 - 1][sc0:sc1 if isinstance(sc1, int) else None]
                        base_line, base_off = sl0 - 1, sc0
                    else:
                        pieces = [lines[sl0 - 1][sc0:]]
                        pieces.extend(lines[i] for i in range(sl0, sl1 - 1))
                        tail = lines[sl1 - 1]
                        pieces.append(tail[:sc1] if isinstance(sc1, int) and sc1 <= len(tail) else tail)
                        span_text = "\n".join(pieces)
                        base_line, base_off = None, None
                    matches = [m for m in re.finditer(
                        r"(?<![A-Za-z0-9_$])" + re.escape(method) + r"(?![A-Za-z0-9_$])", span_text)]
                    span_occurrences = len(matches)
                    if sl0 == l0 and base_line is not None and matches:
                        probe_is_last_in_span = (base_off + matches[-1].start()) == char
                    elif matches:
                        probe_is_last_in_span = None
            if span_occurrences is not None:
                tally[f"span-occurrences:{min(span_occurrences, 3)}"] += 1
                if span_occurrences > 1:
                    tally["ambiguous-method-name-in-span"] += 1
                    by_verdict[record["verdict"]]["ambiguous-method-name-in-span"] += 1
                    if len(samples["ambiguous-method-name-in-span"]) < args.examples:
                        samples["ambiguous-method-name-in-span"].append({
                            "verdict": record["verdict"], "reason": record["reason"],
                            "probe_kind": record["probe_kind"], "callee": callee,
                            "site": f"{file}:{call['l0_1based']}:{char}",
                            "line": text.strip()[:160],
                            "occurrences_in_span": span_occurrences,
                            "probe_is_last": probe_is_last_in_span,
                        })
                if probe_is_last_in_span is False:
                    tally["probe-not-last-occurrence-in-span"] += 1
                    by_verdict[record["verdict"]]["probe-not-last-occurrence-in-span"] += 1
                    if len(samples["probe-not-last-occurrence-in-span"]) < args.examples:
                        samples["probe-not-last-occurrence-in-span"].append({
                            "verdict": record["verdict"], "reason": record["reason"],
                            "probe_kind": record["probe_kind"], "callee": callee,
                            "site": f"{file}:{call['l0_1based']}:{char}",
                            "line": text.strip()[:160],
                            "occurrences_in_span": span_occurrences,
                        })
            tally[kind] += 1
            by_verdict[record["verdict"]][kind] += 1
            if kind != "exact-callee" and len(samples[kind]) < args.examples:
                samples[kind].append({
                    "verdict": record["verdict"], "reason": record["reason"],
                    "probe_kind": record["probe_kind"], "callee": callee,
                    "site": f"{file}:{call['l0_1based']}:{char}",
                    "line": text.strip()[:160],
                    "text_at_probe": text[char:char + 40],
                })
        total = sum(tally.values())
        named = total - tally["no-named-callee(dynamic)"]
        report[data.get("label") or path.name] = {
            "file": str(path),
            "records": total,
            "named_callee_records": named,
            "probe_accuracy": dict(tally),
            "exact_callee_share_of_named": (tally["exact-callee"] / named) if named else None,
            "misprobe_share_of_named": ((named - tally["exact-callee"]) / named) if named else None,
            "by_verdict": {k: dict(v) for k, v in sorted(by_verdict.items())},
            "examples": dict(samples),
        }

    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    for label, entry in report.items():
        print(f"== {label}: {entry['records']} records, {entry['named_callee_records']} with a named callee")
        for key, value in entry["probe_accuracy"].items():
            print(f"     {key}: {value}")
        print(f"     exact-callee share of named: {entry['exact_callee_share_of_named']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
