# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Precision hand-check helper for the resolver measurement campaign.

Selects the edges to audit from one `lsp_edges.py` result and prints the source
at BOTH ends of each, so a verdict is reached by reading code and never by
trusting the LSP response. Selection order, per the campaign protocol:

1. every result whose unresolved reason is `dynamic-callee`,
2. every `edge-variable-binding`,
3. a spread of `edge-call` across as many distinct files as possible,

up to `--limit` in total. When categories 1 and 2 alone exceed the limit the tool
prints more than the limit and says so; the cap is a target, not a truncation of
mandatory evidence.

Read-only: opens source files, writes only `--out`.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as error:
        return [f"<unreadable: {type(error).__name__}>"]


def spread(records: list[dict], limit: int) -> list[dict]:
    """Round-robin across distinct call-site files so a spread is a real spread."""
    if limit <= 0:
        return []
    if len(records) <= limit:
        return records
    by_file: dict[str, list[dict]] = collections.OrderedDict()
    for record in records:
        by_file.setdefault(record["call_site"]["file"], []).append(record)
    picked: list[dict] = []
    index = 0
    while len(picked) < limit:
        added = False
        for bucket in by_file.values():
            if index < len(bucket):
                picked.append(bucket[index])
                added = True
                if len(picked) >= limit:
                    break
        if not added:
            break
        index += 1
    return picked


def spread_by_target(records: list[dict], limit: int) -> list[dict]:
    """Round-robin across distinct TARGET files, so no target file goes unaudited.

    Used when the mandatory categories alone exceed the cap: the protocol wants
    every binding candidate and every dynamic callee looked at, and when that is
    more than the budget the honest reduction is to keep one claim per target
    file first and only then take a second claim from any file.
    """
    if limit <= 0:
        return []
    if len(records) <= limit:
        return records
    by_target: dict[str, list[dict]] = collections.OrderedDict()
    for record in records:
        key = (record.get("target") or {}).get("path") or "<none>"
        by_target.setdefault(key, []).append(record)
    picked: list[dict] = []
    index = 0
    while len(picked) < limit:
        added = False
        for bucket in by_target.values():
            if index < len(bucket):
                picked.append(bucket[index])
                added = True
                if len(picked) >= limit:
                    break
        if not added:
            break
        index += 1
    return picked


def target_identity(record: dict) -> tuple:
    """What makes two records the same claim about the program.

    Precision is a property of an edge, not of a call site: fifty test files
    calling `store.getState().setInitialPositions` produce fifty records and one
    claim, that this position resolves to that declaration. Auditing the same
    claim fifty times buys nothing and crowds out the claims that differ, so the
    audit set is deduplicated on (verdict, target file, target line, symbol).
    """
    target = record.get("target") or {}
    return (record.get("verdict"), target.get("path"), target.get("line1"),
            target.get("character"), target.get("symbol"), target.get("kind"))


def dedupe(records: list[dict]) -> tuple[list[dict], dict[tuple, int]]:
    """One representative per distinct claim, plus how many records each stands for."""
    representatives: list[dict] = []
    counts: dict[tuple, int] = collections.Counter()
    for record in records:
        key = target_identity(record)
        counts[key] += 1
        if counts[key] == 1:
            representatives.append(record)
    return representatives, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--context", type=int, default=2)
    parser.add_argument("--grades", default="edge-call,edge-instantiation,edge-variable-binding",
                        help="comma-separated verdicts that count as an engine-produced edge")
    parser.add_argument("--compact", action="store_true",
                        help="one line per claim: call-site source and target source side by side, "
                             "instead of the full context block")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.result.read_text(encoding="utf-8"))
    records = data.get("records") or []
    grades = {g.strip() for g in args.grades.split(",") if g.strip()}

    dynamic = [r for r in records
               if r.get("reason") == "dynamic-callee" and r.get("verdict") in grades]
    # `--grades` narrows the whole audit, the mandatory binding category included,
    # so a confirmed-grade-only audit is expressible; without this the binding
    # claims crowd out every edge-call and the confirmed edges go unaudited.
    binding = [r for r in records if r.get("verdict") == "edge-variable-binding"
               and "edge-variable-binding" in grades]
    confirmed = [r for r in records
                 if r.get("verdict") in grades and r.get("verdict") != "edge-variable-binding"]

    dynamic_d, dynamic_counts = dedupe(dynamic)
    binding_d, binding_counts = dedupe(binding)
    confirmed_d, confirmed_counts = dedupe(confirmed)
    all_counts = collections.Counter()
    for counts in (dynamic_counts, binding_counts, confirmed_counts):
        all_counts.update(counts)

    seen: set[int] = set()
    mandatory: list[dict] = []
    for record in dynamic_d + binding_d:
        if id(record) not in seen:
            seen.add(id(record))
            mandatory.append(record)
    remaining_budget = max(0, args.limit - len(mandatory))
    fill = [r for r in confirmed_d if id(r) not in seen]
    chosen = mandatory + spread(fill, remaining_budget)
    if len(mandatory) > args.limit:
        # The mandatory categories alone exceed the budget. Keep one claim per
        # distinct target file first, then a second pass, and publish what the
        # reduction dropped rather than letting it disappear.
        chosen = spread_by_target(mandatory, args.limit)
        chosen_ids = {id(r) for r in chosen}
        fill_budget = max(0, args.limit - len(chosen))
        chosen = chosen + spread([r for r in confirmed_d if id(r) not in chosen_ids],
                                 fill_budget)
    chosen_ids = {id(r) for r in chosen}
    unaudited = [r for r in (dynamic_d + binding_d + confirmed_d) if id(r) not in chosen_ids]

    lines_out: list[str] = []
    lines_out.append(f"# hand-check: {data.get('label')} ({args.result.name})")
    lines_out.append(f"workspace: {data.get('workspace', {}).get('project')}")
    lines_out.append(f"source_root: {data.get('workspace', {}).get('source_root')}")
    lines_out.append(f"records available: {len(records)}")
    lines_out.append(f"dynamic-callee edges: {len(dynamic)} records / {len(dynamic_d)} distinct claims")
    lines_out.append(f"edge-variable-binding: {len(binding)} records / {len(binding_d)} distinct claims")
    lines_out.append(f"confirmed grade (edge-call + edge-instantiation): "
                     f"{len(confirmed)} records / {len(confirmed_d)} distinct claims")
    lines_out.append(f"selected for audit: {len(chosen)} distinct claims (limit {args.limit}"
                     f"{' EXCEEDED by mandatory evidence' if len(mandatory) > args.limit else ''})")
    audited_records = sum(all_counts[target_identity(r)] for r in chosen)
    edge_records = len(dynamic) + len(binding) + len(confirmed) - len(
        [r for r in binding if r.get("reason") == "dynamic-callee"])
    lines_out.append(f"records covered by the audited claims: {audited_records} "
                     f"of {edge_records} engine-produced edge records")
    lines_out.append("")

    tally = collections.Counter()
    for n, record in enumerate(chosen, 1):
        call = record["call_site"]
        target = record.get("target") or {}
        call_path = Path(call["abs"])
        call_lines = read_lines(call_path)
        cl = call["l0_1based"]
        if args.compact:
            call_src = call_lines[cl - 1].strip()[:110] if 0 < cl <= len(call_lines) else "?"
            target_path = target.get("path")
            target_src = ""
            tname = ""
            if target_path and target.get("line1"):
                tl = read_lines(Path(target_path))
                t1 = target["line1"]
                target_src = (tl[t1 - 1].strip()[:110] if 0 < t1 <= len(tl) else "?")
                tname = Path(target_path).name
            lines_out.append(
                f"{n:3d}. [{record['verdict']}] reason={record['reason']} "
                f"match={target.get('kind_match')} kind={target.get('kind')}"
                f"({target.get('kind_name')}) sym={target.get('symbol')} "
                f"x{all_counts[target_identity(record)]}")
            lines_out.append(f"     CALL {call['file']}:{cl}:{call['lsp_character0']}  {call_src}")
            lines_out.append(f"     TGT  {tname}:{target.get('line1')}:{target.get('character')}  {target_src}")
            lines_out.append("     VERDICT: <tp|fp|undecidable>  REASON: <one sentence>")
            tally[record["verdict"]] += 1
            continue
        lo = max(0, cl - 1 - args.context)
        hi = min(len(call_lines), cl + args.context)
        lines_out.append(f"## {n}. {record['verdict']}  reason={record['reason']}  "
                         f"probe={record['probe_kind']}  latency={record.get('latency_ms')}ms")
        lines_out.append(f"stands for {all_counts[target_identity(record)]} record(s) "
                         f"making this same claim")
        lines_out.append(f"callee recorded by our resolver: {record.get('callee') or '<none, dynamic>'}")
        if record.get("callee_text"):
            lines_out.append(f"callee expression text from span: {record['callee_text'][:160]}")
        lines_out.append(f"CALL SITE {call['file']}:{cl} (lsp {call['lsp_line0']}:{call['lsp_character0']})")
        for i in range(lo, hi):
            marker = ">>" if i == cl - 1 else "  "
            lines_out.append(f"  {marker}{i + 1:5d}|{call_lines[i][:220]}")
        if cl - 1 < len(call_lines):
            raw = call_lines[cl - 1]
            col = call["lsp_character0"]
            if 0 <= col < len(raw):
                lines_out.append(f"       caret at char {col}: "
                                 f"'{raw[max(0, col - 3):col]}'[{raw[col:col + 40]}]")
        target_path = target.get("path")
        if target_path:
            tp = Path(target_path)
            target_lines = read_lines(tp)
            tl1 = target.get("line1")
            lines_out.append(f"TARGET {tp.name}:{tl1} char {target.get('character')} "
                             f"kind={target.get('kind')}({target.get('kind_name')}) "
                             f"match={target.get('kind_match')} symbol={target.get('symbol')}")
            lines_out.append(f"       server-relative: {target.get('server_relative')}")
            if tl1:
                lo2 = max(0, tl1 - 1 - args.context)
                hi2 = min(len(target_lines), tl1 + args.context)
                for i in range(lo2, hi2):
                    marker = ">>" if i == tl1 - 1 else "  "
                    lines_out.append(f"  {marker}{i + 1:5d}|{target_lines[i][:220]}")
        else:
            lines_out.append(f"TARGET <none> verdict={record['verdict']}")
        lines_out.append("VERDICT: <true-positive | false-positive | undecidable>  "
                         "REASON: <one sentence>")
        lines_out.append("")
        tally[record["verdict"]] += 1

    lines_out.append("## selection composition")
    for key, value in sorted(tally.items()):
        lines_out.append(f"  {key}: {value}")
    lines_out.append("")
    lines_out.append(f"## claims NOT audited ({len(unaudited)} distinct, "
                     f"{sum(all_counts[target_identity(r)] for r in unaudited)} records)")
    lines_out.append("Published so the reduction is visible instead of silent. "
                     "Grouped by verdict and target.")
    grouped: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for record in unaudited:
        target = record.get("target") or {}
        grouped[record.get("verdict") or "?"][
            f"{target.get('path')}:{target.get('line1')} {target.get('symbol')} "
            f"(kind={target.get('kind')}, match={target.get('kind_match')})"
        ] += all_counts[target_identity(record)]
    for verdict in sorted(grouped):
        lines_out.append(f"### {verdict}")
        for claim, count in grouped[verdict].most_common():
            lines_out.append(f"  {count:4d} record(s)  {claim}")

    text = "\n".join(lines_out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
