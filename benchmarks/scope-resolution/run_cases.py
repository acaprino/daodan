"""Runner: resolver deterministico sui casi di ground_truth.json.

Tre misure separate per caso: file indispensabili mancanti (required), inclusioni vietate
(forbidden) e violazioni di protocollo (tracecheck). Report in results/run-<ts>/. Exit non-zero
se un caso fallisce; i casi di giudizio in cui il resolver non può riuscire sono xfail nei test.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from resolver import POLICY, ensure_run, resolve  # noqa: E402
from tracecheck import validate_trace  # noqa: E402

# Regole di tracecheck che sono convenzioni del benchmark, non della spec.
PROTOCOL_LAYERS = {
    "exclusion-needs-read": "reference_policy", "resolved-residual-empty": "reference_policy",
    "resolved-empty-perimeter": "reference_policy", "budget-cap": "reference_policy",
    "budget-accounting": "reference_policy", "unknown-op": "reference_policy",
    "modules-index-before-lexical": "reference_policy", "module-fallback-order": "reference_policy",
    "error-is-not-empty": "reference_policy", "invalid-is-not-empty": "reference_policy",
}


def measure(case, trace):
    required, perimeter = set(case["required"]), set(trace["perimeter"])
    extra = sorted(perimeter - required)
    seen = {node for step in trace["steps"] if step["op"] in ("read", "outline") for node in step["nodes"]}
    return {"perimeter": len(perimeter), "required": len(required), "extra": extra,
            "no_evidence": sorted(perimeter - seen),
            "precision": round(len(perimeter & required) / len(perimeter), 2) if perimeter else None,
            "recall": round(len(perimeter & required) / len(required), 2) if required else None,
            "queries": trace["budget"]["queries"], "reads": trace["budget"]["reads"]}


def check_case(case, trace):
    """[(assert, livello, dettaglio)] per ogni mismatch: esito, required, forbidden, candidati, protocollo."""
    failures = []
    perimeter = set(trace["perimeter"])
    allowed = case["outcome"] if isinstance(case["outcome"], list) else [case["outcome"]]
    if trace["outcome"] not in allowed:
        failures.append(("outcome", "spec", f"atteso {case['outcome']}, ottenuto {trace['outcome']} ({trace['stop_reason']})"))
    for f in case["required"]:
        if f not in perimeter:
            failures.append(("required", "fixture", f"manca {f}"))
    for f in case.get("forbidden", []):
        if f in perimeter:
            failures.append(("forbidden", "fixture", f"presente {f}"))
    if case.get("candidates"):
        got = {c["target"] for c in trace["candidates"] or []}
        if got != set(case["candidates"]):
            failures.append(("candidates", "fixture", f"atteso {sorted(case['candidates'])}, ottenuto {sorted(got)}"))
    for violation in validate_trace(trace, POLICY):
        failures.append(("protocol", PROTOCOL_LAYERS.get(violation.split(":", 1)[0], "spec"), violation))
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="bench-1")
    parser.add_argument("--case", action="append", default=None)
    parser.add_argument("--label", default="")
    args = parser.parse_args(argv)
    if not args.run_id.startswith("bench-"):
        parser.error("--run-id deve iniziare con 'bench-': ensure_run ricostruisce il run esistente")
    ground_truth = json.loads((HERE / "ground_truth.json").read_text(encoding="utf-8"))
    service, run_id = ensure_run(HERE, args.run_id)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = HERE / "results" / f"run-{stamp}{'-' + args.label if args.label else ''}"
    out_dir.mkdir(parents=True, exist_ok=True)
    traces, rows, failed = {}, [], 0
    lines = [f"# Run {stamp} (run_id={run_id}, resolver policy v{POLICY['version']})", ""]
    for cid in args.case or list(ground_truth):
        case = ground_truth[cid]
        trace = resolve(service, run_id, case, POLICY)
        traces[cid] = trace
        failures = check_case(case, trace)
        m = measure(case, trace)
        status = "PASS" if not failures else "FAIL"
        failed += bool(failures)
        lines += [f"## {cid}: {status} — {trace['outcome']} / {trace['stop_reason']}",
                  f"- perimetro {m['perimeter']} (required {m['required']}, precision {m['precision']}, recall {m['recall']}); "
                  f"extra: {[e.split('app/', 1)[-1] for e in m['extra']]}; budget {m['queries']}q/{m['reads']}r"]
        lines += [f"- **FAIL** [{layer}] {name}: {detail}" for name, layer, detail in failures]
        lines.append("")
        rows.append(f"| {cid} | {status} | {m['perimeter']}/{m['required']} | {m['precision']} | {m['recall']} | {m['queries']}/{m['reads']} |")
    lines += ["## Sintesi", "", "| Caso | Esito | Perimetro/required | Precision | Recall | Query/letture |", "|---|---|---|---|---|---|"] + rows
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "traces.json").write_text(json.dumps(traces, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n".join(lines))
    print(f"report: {out_dir / 'report.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
