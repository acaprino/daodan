"""Run kouhxp/gutsy (gutsy-0.8b-v04 Q8_0) across all three Daodan Choicer benchmark suites with incremental checkpointing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

from probe_gutsy import SNAP, Calibration, Engine, TorchGutsyBackend, decide_fast
import metrics
import probe_static_router

HERE = Path(__file__).resolve().parent
OUT_PATH = HERE / "runs/20261020T100258Z/gutsy-comparison.json"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_saved() -> dict:
    if OUT_PATH.exists():
        return json.loads(OUT_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(data: dict) -> None:
    OUT_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_suite_1_fresh_controls(engine: Engine) -> dict:
    fc = json.loads((HERE / "runs/20261020T-diagnostic/fresh-controls.json").read_text(encoding="utf-8"))
    choice_q = {
        "family": {
            "type": "choice",
            "instructions": "Which category best describes this source code snippet?",
            "criteria": {
                "react": "React UI component using JSX or React hooks such as useState or useMemo",
                "persistence": "Database, SQL, or Redis cache storage read/write code",
                "computation": "In-memory calculation, math, sorting, or data counting without UI or storage I/O",
            },
        },
    }
    noul_q = {
        "has_react": {
            "type": "noul",
            "instructions": "Does this code define or render a React component or use React hooks?",
            "criteria": {
                "true": "Uses React imports, hooks (useState, useMemo, useEffect), or JSX elements",
                "false": "Backend, database, CLI, or plain computation code without React or JSX",
            },
        },
        "has_persistence": {
            "type": "noul",
            "instructions": "Does this code read from or write to a database or cache store?",
            "criteria": {
                "true": "Executes SQL queries, opens database connections, or reads/writes Redis or cache keys",
                "false": "UI component or pure in-memory calculation with no database or cache I/O",
            },
        },
    }

    rows = []
    fam_ok = react_tp = react_fp = pers_tp = pers_fp = 0

    for item in fc["cases"]:
        t0 = time.perf_counter()
        r_c = decide_fast(engine, {"state": item["state"], "questions": choice_q}, batch_size=4)
        r_n = decide_fast(engine, {"state": item["state"], "questions": noul_q}, batch_size=4)
        pred_fam = r_c["answers"]["family"]["choice"]
        p_react = r_n["answers"]["has_react"]["noul"]
        p_pers = r_n["answers"]["has_persistence"]["noul"]
        if pred_fam == item["expected_family"]:
            fam_ok += 1
        if item["expected_has_react"]:
            if p_react >= 0.5:
                react_tp += 1
        else:
            if p_react >= 0.5:
                react_fp += 1
        if item["expected_has_persistence"]:
            if p_pers >= 0.5:
                pers_tp += 1
        else:
            if p_pers >= 0.5:
                pers_fp += 1
        rows.append(
            {
                "id": item["id"],
                "expected_family": item["expected_family"],
                "pred_family": pred_fam,
                "family_conf": r_c["answers"]["family"]["confidence"],
                "p_react": p_react,
                "p_persistence": p_pers,
                "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            }
        )

    c01 = json.loads((HERE / "runs/20261020T100258Z/dataset.json").read_text(encoding="utf-8"))["cases"][0]
    h1 = c01["hunks"][0]
    numbered_h1 = f"[{h1['id']}]\n" + "\n".join(
        f"{h1['path']}:{h1['start_line'] + i} {line}" for i, line in enumerate(h1["text"].splitlines())
    )
    c01_c = decide_fast(engine, {"state": numbered_h1, "questions": choice_q}, batch_size=4)
    c01_n = decide_fast(engine, {"state": numbered_h1, "questions": noul_q}, batch_size=4)

    return {
        "family_correct": f"{fam_ok}/8",
        "react_tp": f"{react_tp}/2",
        "react_fp": f"{react_fp}/6",
        "persistence_tp": f"{pers_tp}/2",
        "persistence_fp": f"{pers_fp}/6",
        "c01_h1_numbered_python_cache": {
            "pred_family": c01_c["answers"]["family"]["choice"],
            "family_probs": c01_c["answers"]["family"]["probabilities"],
            "p_react": c01_n["answers"]["has_react"]["noul"],
            "p_persistence": c01_n["answers"]["has_persistence"]["noul"],
        },
        "rows": rows,
    }


def score_team_probs(teams: list[dict], raw_probs: dict[str, dict[str, float]]) -> dict:
    by_thresh = {}
    for th in (0.45, 0.50, 0.55, 0.60, 0.65):
        req_found = req_total = out_of_scope = total_sel = acceptable = 0
        per_team = []
        for t in teams:
            tid = t["id"]
            req = set(t["required_roles"])
            allow = set(t["allowed_roles"])
            probs = raw_probs[tid]
            sel = {rid for rid, p in probs.items() if p >= th}
            req_hit = len(sel & req)
            req_found += req_hit
            req_total += len(req)
            forb = sel - (req | allow)
            out_of_scope += len(forb)
            total_sel += len(sel)
            is_acc = (req_hit == len(req)) and (len(forb) == 0)
            if is_acc:
                acceptable += 1
            per_team.append(
                {
                    "id": tid,
                    "required_found": f"{req_hit}/{len(req)}",
                    "missing": sorted(req - sel),
                    "out_of_scope": sorted(forb),
                    "selected": sorted(sel),
                    "acceptable": is_acc,
                }
            )
        by_thresh[f"{th:.2f}"] = {
            "acceptable_teams": f"{acceptable}/{len(teams)}",
            "mandatory_found": f"{req_found}/{req_total} ({req_found/req_total*100:.1f}%)",
            "out_of_scope_selections": out_of_scope,
            "mean_out_of_scope_per_team": round(out_of_scope / len(teams), 2),
            "total_selected": total_sel,
            "per_team": per_team,
        }
    return by_thresh


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    t0 = time.perf_counter()
    gguf_file = SNAP / "gutsy-0.8b-v04-q8_0.gguf"
    cal_file = SNAP / "gutsy-0.8b-v04.calibration.json"
    backend = TorchGutsyBackend(gguf_file, n_ctx=8192, n_threads=4)
    engine = Engine(
        backend,
        calibration=Calibration.load(cal_file),
        name="gutsy-0.8b-v04",
        reject_slot=True,
        shortlist=True,
    )
    load_sec = round(time.perf_counter() - t0, 2)
    print(f"Loaded gutsy-0.8b-v04 in {load_sec}s")

    state = load_saved()
    state.setdefault("model", "kouhxp/gutsy (gutsy-0.8b-v04-q8_0.gguf)")
    state.setdefault("revision", "f9995fe26a337f1a4ea3f1a5ed38c9799e5a8f63")
    state.setdefault("gguf_bytes", gguf_file.stat().st_size)

    if mode in ("all", "suite1"):
        s1 = run_suite_1_fresh_controls(engine)
        state["suite1_fresh_controls"] = s1
        save_state(state)
        print("Suite 1 saved:", s1["family_correct"], "react TP/FP:", s1["react_tp"], s1["react_fp"], "pers TP/FP:", s1["persistence_tp"], s1["persistence_fp"])
        print("C01-H1 numbered Python cache:", str(s1["c01_h1_numbered_python_cache"]).replace("{", "(").replace("}", ")"))

    if mode in ("all", "suite2"):
        suite = json.loads((HERE / "runs/20261020T-all-reviewers/suite.json").read_text(encoding="utf-8"))
        roles = suite["roles"]
        teams = suite["teams"]
        grounded_qs = {
            r["role_id"]: {
                "type": "noul",
                "instructions": r["question"],
                "criteria": {"true": r["criteria"]["true"], "false": r["criteria"]["false"]},
            }
            for r in roles
        }
        s2_raw = state.get("suite2_raw_probs", {})
        for t in teams:
            tid = t["id"]
            if tid in s2_raw:
                continue
            ts = time.perf_counter()
            res = decide_fast(engine, {"state": t["state"], "questions": grounded_qs}, batch_size=22)
            s2_raw[tid] = {rid: res["answers"][rid]["noul"] for rid in grounded_qs}
            state["suite2_raw_probs"] = s2_raw
            save_state(state)
            print(f"Suite 2 {tid} done in {time.perf_counter() - ts:.2f}s")
        if len(s2_raw) == len(teams):
            state["suite2_grounded_noul"] = score_team_probs(teams, s2_raw)
            save_state(state)
            print("Suite 2 scored.")

    if mode in ("all", "suite3"):
        run_dir = HERE / "runs/20261020T100258Z"
        dataset = json.loads((run_dir / "dataset.json").read_text(encoding="utf-8"))
        catalog = json.loads((run_dir / "catalog.json").read_text(encoding="utf-8"))
        roles = [r for r in catalog["roles"] if r["is_reviewer"]]
        reviewer_ids = [r["id"] for r in roles]
        exact_questions = {
            r["id"]: {
                "type": "noul",
                "instructions": f"Does this code diff hunk satisfy {r['id']}'s TRIGGER WHEN?",
                "criteria": {
                    "true": r["trigger_when"],
                    "false": r["do_not_trigger_when"] or "Not applicable to this hunk.",
                },
            }
            for r in roles
        }
        s3_raw = state.get("suite3_raw_probs", {})
        for case in dataset["cases"]:
            cid = case["id"]
            if cid in s3_raw:
                continue
            ts = time.perf_counter()
            parts = []
            per_hunk_budget = max(250, 3600 // max(1, len(case["hunks"])))
            for h in case["hunks"]:
                snippet = h["text"][:per_hunk_budget]
                parts.append(f"# {h['path']}:{h['start_line']}\n{snippet}")
            state_text = "\n\n".join(parts)[:3800]
            res = decide_fast(engine, {"state": state_text, "questions": exact_questions}, batch_size=18)
            s3_raw[cid] = {rid: res["answers"][rid]["noul"] for rid in reviewer_ids}
            state["suite3_raw_probs"] = s3_raw
            save_state(state)
            print(f"Suite 3 {cid} done in {time.perf_counter() - ts:.2f}s")

        if len(s3_raw) == len(dataset["cases"]):
            static_eval = probe_static_router.evaluate_static_variants()
            ast_by_case = {
                cid: set(static_eval["per_case_details"][cid]["ast_domain_router"])
                for cid in s3_raw
            }
            hybrid_pool_by_case = {
                cid: set(static_eval["per_case_details"][cid]["hybrid_union_candidates"])
                for cid in s3_raw
            }
            results_by_mode = {}
            for th in (0.40, 0.50, 0.60, 0.70):
                pure_rows, hybrid_rows, inter_rows = [], [], []
                for case in dataset["cases"]:
                    cid = case["id"]
                    probs = s3_raw[cid]
                    sel_pure = sorted(rid for rid, p in probs.items() if p >= th)
                    semantic_lenses = {
                        "senior-review:security-auditor",
                        "senior-review:data-integrity-auditor",
                        "senior-review:logic-integrity-auditor",
                        "senior-review:temporal-resilience-auditor",
                        "senior-review:resource-lifecycle-auditor",
                        "senior-review:distributed-flow-auditor",
                        "senior-review:ui-race-auditor",
                    }
                    sel_hybrid = sorted(
                        ast_by_case[cid] | {rid for rid in semantic_lenses if probs.get(rid, 0.0) >= th}
                    )
                    sel_inter = sorted(
                        rid for rid in hybrid_pool_by_case[cid] if probs.get(rid, 0.0) >= th
                    )
                    for rows, sel in ((pure_rows, sel_pure), (hybrid_rows, sel_hybrid), (inter_rows, sel_inter)):
                        rows.append(
                            {
                                "case_id": cid,
                                "label_status": case["label_status"],
                                "expected_roles": case["expected_roles"],
                                "selected": sel,
                            }
                        )
                for mode_name, rows in (
                    (f"gutsy_exact_catalog_th_{th:.2f}", pure_rows),
                    (f"ast_plus_gutsy_th_{th:.2f}", hybrid_rows),
                    (f"hybrid_pool_filtered_by_gutsy_th_{th:.2f}", inter_rows),
                ):
                    sc = metrics._role_metrics(rows)
                    results_by_mode[mode_name] = {
                        "complete_cases": "11/11",
                        "labeled_cases": sc["labeled_cases"],
                        "expected_role_recall": f"{sc['matched_expected_roles']}/{sc['expected_role_activations']} ({sc['expected_role_recall']*100:.1f}%)",
                        "critical_recall": f"{sc['critical_overall']['true_positives']}/{sc['critical_overall']['support']} ({sc['critical_overall']['recall']*100:.1f}%)",
                        "excess_activations_per_case": round(sc["benchmark_excess_per_case"], 3),
                        "per_case_selected": {r["case_id"]: r["selected"] for r in rows},
                    }
            state["suite3_c01_c11"] = results_by_mode
            save_state(state)
            print("Suite 3 scored.")
