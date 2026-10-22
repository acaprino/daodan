# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Turn the campaign's result JSONs into the numbers RESULTS.md publishes.

Every figure is recomputed from the raw JSON rather than transcribed, and the
`edge-instantiation` grade is reported separately from `edge-call` because on the
Go corpus it turned out to be 267 records of one type conversion
(`attribute.Key("...")` -> `type Key string`), not a construction. Nothing is
merged silently: `confirmed_call_only` and `confirmed_call_plus_instantiation`
are both printed, and the reason-weighted extrapolation is computed for each.

Read-only over the result files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EDGE_CALL = "edge-call"
EDGE_INST = "edge-instantiation"
EDGE_BIND = "edge-variable-binding"


def weighted(verdicts_by_reason: dict, population: dict, accepted: set[str]) -> dict:
    """Reason-weighted edges over the full population, for a chosen verdict set."""
    terms = []
    for reason, pop_count in population.items():
        per = verdicts_by_reason.get(reason) or {}
        sample = sum(per.values())
        hits = sum(v for k, v in per.items() if k in accepted)
        rate = (hits / sample) if sample else 0.0
        terms.append({"reason": reason, "population": pop_count, "sample": sample,
                      "hits": hits, "rate": rate, "weighted": pop_count * rate})
    total = sum(t["population"] for t in terms)
    edges = sum(t["weighted"] for t in terms)
    return {"population": total, "weighted_edges": edges,
            "weighted_share": (edges / total) if total else None,
            "terms": sorted(terms, key=lambda t: -t["population"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, action="append", required=True)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    out = {}
    for path in args.result:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("fatal"):
            out[data.get("label") or path.name] = {
                "fatal": data["fatal"], "language": data.get("language"),
                "workspace": data.get("workspace"),
                "readiness": {k: data.get("readiness", {}).get(k)
                              for k in ("ready", "attempts", "seconds", "timeout_seconds")},
            }
            continue
        verdicts = data.get("verdicts") or {}
        positions = sum(verdicts.values())
        call = verdicts.get(EDGE_CALL, 0)
        inst = verdicts.get(EDGE_INST, 0)
        bind = verdicts.get(EDGE_BIND, 0)
        population = {k: v for k, v in (data.get("population_reason_counts") or {}).items()
                      if k != "unbound-name"}
        by_reason = data.get("verdicts_by_unresolved_reason") or {}
        w_call = weighted(by_reason, population, {EDGE_CALL})
        w_both = weighted(by_reason, population, {EDGE_CALL, EDGE_INST})
        binding_split = data.get("binding_kind_split") or {}
        nested_in_type = sum(v for k, v in binding_split.items()
                             if k.startswith("nested-inside-") and
                             k.split(":", 1)[0].split("-")[-1] in ("5", "11", "23"))
        lexical = data.get("lexical_baseline_in_workspace") or {}
        out[data.get("label") or path.name] = {
            "file": str(path),
            "language": data.get("language") or (data.get("engine") or {}).get("language"),
            "workspace": (data.get("workspace") or {}).get("project") or data.get("workspace"),
            "prefix": (data.get("workspace") or {}).get("workspace_rel_prefix"),
            "node_modules": (data.get("workspace") or {}).get("node_modules_in_project"),
            "lexical_baseline": {"resolved": lexical.get("resolved"),
                                 "total": lexical.get("total"),
                                 "share": lexical.get("lexical_resolved_share")},
            "population_measurable": sum(population.values()),
            "sample": {"files": (data.get("sample") or {}).get("files"),
                       "positions": positions},
            "verdicts": verdicts,
            "grades": {"edge-call": call, "edge-instantiation": inst,
                       "edge-variable-binding": bind},
            "share_call_only": (call / positions) if positions else None,
            "share_call_plus_instantiation": ((call + inst) / positions) if positions else None,
            "weighted_call_only": w_call,
            "weighted_call_plus_instantiation": w_both,
            "binding_kind_split": binding_split,
            "prescribed_variable_binding_only":
                data.get("variable_binding_prescribed_kinds_only"),
            "nested_inside_type_lower_bound_records": nested_in_type,
            "kind_match": data.get("kind_match_counts"),
            "probe_kind": data.get("probe_kind_counts"),
            "external_uri_schemes": data.get("external_uri_schemes"),
            "external_packages_top": (data.get("external_packages") or [])[:8],
            "outside_workspace_targets": (data.get("outside_workspace_target_dirs") or [])[:8],
            "readiness": {"ready": (data.get("readiness") or {}).get("ready"),
                          "attempts": (data.get("readiness") or {}).get("attempts"),
                          "seconds": (data.get("readiness") or {}).get("seconds"),
                          "min_required": (data.get("readiness") or {}).get("min_resolved_required")},
            "startup_seconds": data.get("server_startup_seconds"),
            "elapsed_seconds": data.get("elapsed_seconds"),
            "latency_ms": data.get("latency_ms"),
            "engine": data.get("engine"),
        }

    text = json.dumps(out, indent=2, ensure_ascii=False, default=str)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")

    for label, e in out.items():
        if e.get("fatal"):
            print(f"== {label}: FATAL - {e['fatal']}")
            print(f"   readiness {e['readiness']}")
            continue
        s = e["sample"]
        print(f"== {label} [{e['language']}] ws={e['workspace']} prefix={e['prefix']!r} "
              f"node_modules={e['node_modules']}")
        lb = e["lexical_baseline"]
        print(f"   lexical baseline {lb['resolved']}/{lb['total']} = "
              f"{(lb['share'] or 0):.2%} | population measurable {e['population_measurable']}")
        print(f"   sample {s['files']} files / {s['positions']} positions")
        print(f"   verdicts: " + ", ".join(f"{k}={v}" for k, v in sorted(
            e["verdicts"].items(), key=lambda kv: -kv[1])))
        print(f"   EDGE-CALL ONLY        {e['grades']['edge-call']:5d} = "
              f"{e['share_call_only']:.2%}   weighted {e['weighted_call_only']['weighted_share']:.2%}")
        print(f"   call + instantiation  {e['grades']['edge-call'] + e['grades']['edge-instantiation']:5d} = "
              f"{e['share_call_plus_instantiation']:.2%}   weighted "
              f"{e['weighted_call_plus_instantiation']['weighted_share']:.2%}")
        print(f"   variable-binding (candidate) {e['grades']['edge-variable-binding']:5d} = "
              f"{e['grades']['edge-variable-binding'] / s['positions']:.2%}"
              f"   prescribed-kinds-only {e['prescribed_variable_binding_only']}")
        print(f"   nested-inside-a-type (verified lower bound) {e['nested_inside_type_lower_bound_records']}")
        print(f"   binding split: {e['binding_kind_split']}")
        print(f"   kind_match: {e['kind_match']}")
        print(f"   probe_kind: {e['probe_kind']}")
        r = e["readiness"]
        print(f"   ready={r['ready']} attempts={r['attempts']} in {r['seconds']:.1f}s "
              f"(min {r['min_required']}) | startup {e['startup_seconds']:.1f}s | "
              f"elapsed {e['elapsed_seconds']:.1f}s")
        lat = e["latency_ms"] or {}
        print(f"   latency mean {lat.get('mean'):.1f} ms p95 {lat.get('p95'):.1f} ms n={lat.get('count')}")
        if e.get("external_uri_schemes"):
            print(f"   external uri schemes: {e['external_uri_schemes']}")
        print(f"   top external: {e['external_packages_top'][:5]}")
        if e.get("outside_workspace_targets"):
            print(f"   outside-workspace targets: {e['outside_workspace_targets']}")
        print(f"   weighted terms (call only): " + "; ".join(
            f"{t['reason']} pop={t['population']} n={t['sample']} rate={t['rate']:.1%}"
            for t in e["weighted_call_only"]["terms"][:6]))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
