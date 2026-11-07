"""model_eval.py — valuta una sessione del modello contro ground truth e protocollo.

  python model_eval.py SESSION CASE_ID [--intent-index N]

Legge results/model-runs/SESSION/{trace.jsonl,final.json}, ricostruisce la traccia nel
formato del resolver, applica check_case (assert per livello), measure e validate_trace.
Gli assert sono quelli del resolver: i fallimenti di un modello sono misurazioni, non bocciature.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from resolver import POLICY, PREFIX, _Trace  # noqa: E402
from run_cases import check_case, measure  # noqa: E402

OUTCOMES = {"incomplete": "partial", "needs_clarification": "clarify"}


def build_trace(session):
    base = HERE / "results" / "model-runs" / session
    lines = (base / "trace.jsonl").read_text(encoding="utf-8").splitlines() if (base / "trace.jsonl").exists() else []
    final = json.loads((base / "final.json").read_text(encoding="utf-8"))
    t = _Trace(POLICY)
    for raw in lines:
        e = json.loads(raw)
        t.add(e["op"], e["args"], e.get("lineage"), e["result_kind"], e.get("motivation") or "", e.get("nodes") or [],
              truncated=bool(e.get("truncated")))

    def full(p):
        return p if p.startswith(PREFIX) else PREFIX + p

    perimeter = [full(x["path"] if isinstance(x, dict) else x) for x in final.get("perimeter", [])]
    exclusions = [{"path": full(x["path"]), "motivation": x.get("why") or x.get("motivation", "")}
                  for x in final.get("exclusions", [])]
    unresolved = [{"caller": u.get("caller", "?"), "callee": u.get("callee", "?"),
                   "resolution": u.get("resolution", "unresolved")} for u in final.get("unresolved_calls", [])]
    candidates = final.get("candidates")
    if candidates:
        candidates = [{"target": full(c["target"]), "motivation": c.get("why") or c.get("motivation", "")} for c in candidates]
    return {"steps": t.steps, "budget": t.budget(), "outcome": OUTCOMES.get(final.get("outcome"), final.get("outcome")),
            "stop_reason": final.get("stop_reason"), "perimeter": sorted(set(perimeter)),
            "unresolved_calls": unresolved, "candidates": candidates or None,
            "residual": [full(r) if "/" in r else r for r in final.get("residual", [])],
            "exclusions": exclusions, "question": final.get("question"),
            "terminal_index": len(t.steps) - 1}


def main(argv=None):
    session, cid = (argv or sys.argv[1:])[:2]
    ground_truth = json.loads((HERE / "ground_truth.json").read_text(encoding="utf-8"))
    case = ground_truth[cid]
    trace = build_trace(session)
    failures = check_case(case, trace)
    metrics = measure(case, trace)
    out = {"session": session, "case": cid, "outcome": trace["outcome"], "stop_reason": trace["stop_reason"],
           "metrics": metrics, "failures": [{"assert": a, "layer": l, "detail": d} for a, l, d in failures]}
    (HERE / "results" / "model-runs" / session / "eval.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
