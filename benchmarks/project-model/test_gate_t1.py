"""Il Cancello T1 sul campione di `T0.B.4`, Bank of Anthos, riletto dal risultato committato di `modal_pipeline.py` (T1.E.7).

Il risultato è il più recente `results/pipeline/*-t1-gate*.json` per nome (la data in testa; non i `.report.json` di
`pipeline_report.py`), scritto da `modal_pipeline.py --cases real-bank-of-anthos` con i container e nessun LLM. Del caso:

- un solo piano (`plan.current`): gli otto step nell'ordine di `pipeline.IDS`, ogni azione `failed` o `not_possible` con la
  sua `cause`, ogni lacuna del piano con `kind` e `detail`;
- i moduli: il punteggio di `score.score` contro `fixtures/real-bank-of-anthos/expected.json`, che il driver calcola come
  oggi, non perde una voce che la pre-mappa di oggi trova (`results/daodan_premap_corpus.json`, di `modal_premap.py`): una
  voce persa è mancata o sbagliata ora e non lì, e una faccia data lì e non ora le perde tutte;
- gli ingressi: `entries_vs_reference.compare(system.json, {"static_sites": entry_sites, "observed_spans": []})` copre almeno
  `STATIC` controlli iniziali dei flussi del riferimento;
- nessuna perdita senza causa: ha una causa uno step con `cause`, un'azione con `cause`, una lacuna (`gap`) o gli host che
  attende (`hosts`), una sorgente della pre-mappa con la sua `reason` o una lacuna di suo nome. Uno step che non è `done` né
  `skipped` ne ha una, o segue uno step fallito che ferma i successivi (`stops`); un'azione che non lo è, sotto uno step
  `done` o `skipped`, ne ha una; una sorgente che non è `ran` né `not_needed` ne ha una; le lacune della pre-mappa e del passo
  dinamico hanno `kind` e `detail`; una voce dei moduli persa sta in ACCEPTED con la causa.

Il calcolo sta in funzioni pure, provate anche su righe scritte qui.

Su Modal: python tests/modal_pytest.py benchmarks/project-model/test_gate_t1.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "daodan/core")]

import entries_vs_reference  # noqa: E402

CASE = "real-bank-of-anthos"
RESULTS, FIXTURE = HERE / "results", HERE / "fixtures" / CASE
# le facce dei moduli nel punteggio di `score.score`
MODULES = ("units", "units.depends_on", "units.source_roots", "units.config", "workspace", "workspace.members")
# `T1.C.11` ha misurato i fatti della pipeline sui flussi persi, non `entries_vs_reference`: nessun suo numero si confronta.
# La soglia è quella della corsa di prova, `results/pipeline/2026-11-28-t1-gate-prova.json`: 0 dei 27 controlli citati, perché
# stanno in template, manifesti di Kubernetes e Skaffold, CI, Terraform e Makefile, e i 44 siti delle rotte in `.py`, `.java`,
# `pom.xml` e in un Ingress.
STATIC = 0
ACCEPTED: dict[tuple[str, str], str] = {}  # (faccia, voce) dei moduli persa: la causa; oggi nessuna
ENDED = ("done", "skipped")


def latest(folder: Path) -> Path | None:
    """Il risultato del Cancello più recente in `folder`, per nome."""
    found = sorted(p for p in folder.glob("*-t1-gate*.json") if not p.name.endswith(".report.json"))
    return found[-1] if found else None


def plan_problems(plan: dict, ids) -> list[str]:
    """Che cosa manca al piano per essere uno solo, con gli step `ids`."""
    steps = [step.get("id") for step in plan.get("steps") or ()]
    problems = [] if steps == list(ids) else [f"gli step sono {steps}, non {list(ids)}"]
    problems += [f"l'azione {action['id']} è {action['state']} senza causa" for action in plan.get("actions") or ()
                 if action.get("state") in ("failed", "not_possible") and not action.get("cause")]
    problems += [f"una lacuna del piano senza kind o detail: {gap}" for gap in plan.get("gaps") or ()
                 if not (gap.get("kind") and gap.get("detail"))]
    return problems


def unexplained(case: dict) -> list[str]:
    """Le perdite del caso che non dicono la loro causa."""
    plan = case.get("plan") or {}
    out, stopped = [], None
    for step in plan.get("steps") or ():
        if step["state"] not in ENDED and not step.get("cause") and stopped is None:
            out.append(f"lo step {step['id']} è {step['state']} senza causa")
        if step["state"] == "failed" and step.get("stops") and stopped is None:
            stopped = step["id"]
    states = {step["id"]: step["state"] for step in plan.get("steps") or ()}
    out += [f"l'azione {action['id']} è {action['state']} senza causa" for action in plan.get("actions") or ()
            if action["state"] not in ENDED and states.get(action["step"]) in ENDED
            and not any(action.get(key) for key in ("cause", "gap", "hosts"))]
    said = {gap.get("source") for gap in case.get("gaps") or ()}
    out += [f"la sorgente {source['source']} è {source['state']} senza causa" for source in case.get("sources") or ()
            if source["state"] not in ("ran", "not_needed") and not source.get("reason") and source["source"] not in said]
    out += [f"una lacuna senza kind o detail: {gap}" for gap in (*(case.get("gaps") or ()), *(case.get("dynamic_gaps") or ()))
            if not (gap.get("kind") and gap.get("detail"))]
    return out


def lost(now: dict, before: dict, facets=MODULES) -> list[tuple[str, str]]:
    """Le voci delle `facets` che il punteggio `before` trova e `now` no; `(faccia, "*")` per una faccia data prima e non ora."""
    def missing(result: dict) -> set[str]:
        return set(result.get("missed") or ()) | {wrong["item"] for wrong in result.get("wrong") or ()}

    out = []
    for facet in facets:
        old, new = before.get(facet) or {}, now.get(facet) or {}
        if not old.get("given"):
            continue
        out += [(facet, "*")] if not new.get("given") else [(facet, item) for item in sorted(missing(new) - missing(old))]
    return out


def entries(case: dict) -> dict:
    """Il confronto degli ingressi del caso con i controlli iniziali dei flussi di `system.json`, il riferimento del campione."""
    reference = json.loads((FIXTURE / "system.json").read_text(encoding="utf-8"))
    return entries_vs_reference.compare(reference, {"static_sites": case.get("entry_sites") or [], "observed_spans": []})


# ---------------------------------------------------------------- il risultato committato

@pytest.fixture(scope="module")
def case() -> dict:
    path = latest(RESULTS / "pipeline")
    assert path is not None, "nessun risultato del Cancello T1: results/pipeline/*-t1-gate*.json"
    found = json.loads(path.read_text(encoding="utf-8"))
    assert CASE in found, f"{path.name} non ha il caso {CASE}"
    print(f"{path.name}, codice {found['code']['commit']}", "errore: " + found[CASE]["error"] if "error" in found[CASE] else "")
    return found[CASE]


def test_the_caller_gets_one_plan_with_the_eight_steps_in_order(case):
    import pipeline
    print(json.dumps([[step["id"], step["state"]] for step in (case.get("plan") or {}).get("steps") or ()]))
    problems = plan_problems(case.get("plan") or {}, pipeline.IDS)
    assert not problems, problems


def test_the_modules_lose_nothing_the_pre_map_of_today_finds(case):
    before = json.loads((RESULTS / "daodan_premap_corpus.json").read_text(encoding="utf-8"))[CASE]["premap"]
    now = case.get("premap") or {}
    print(json.dumps({facet: {key: (now.get(facet) or {}).get(key) for key in ("given", "expected", "found")}
                      for facet in MODULES}))
    losses = [item for item in lost(now, before) if item not in ACCEPTED]
    assert not losses, losses


def test_the_entries_cover_at_least_the_cites_of_the_trial(case):
    seen = entries(case)
    print(json.dumps({**seen, "entry_sites": len(case.get("entry_sites") or ()),
                      "cause": case.get("entry_sites_cause")}))
    assert seen["static"] >= STATIC, seen


def test_no_loss_without_a_cause(case):
    problems = unexplained(case)
    assert not problems, problems


# ---------------------------------------------------------------- il calcolo, su righe scritte qui

IDS = ("a", "b", "c")


def _step(ident: str, state: str = "done", **more) -> dict:
    return {"id": ident, "state": state, "stops": True, **more}


def _action(ident: str, step: str, state: str = "done", **more) -> dict:
    return {"id": ident, "step": step, "state": state, **more}


def test_a_plan_with_its_steps_in_order_and_every_failure_said_is_one_plan():
    plan = {"steps": [_step("a"), _step("b"), _step("c")],
            "actions": [_action("a:x", "a", "failed", cause="exit 1"), _action("b:y", "b", "not_possible", cause="no tool")],
            "gaps": [{"kind": "no-analyzer", "detail": "Ruby: no analyzer"}]}
    assert plan_problems(plan, IDS) == []


def test_steps_out_of_order_a_failure_with_no_cause_and_a_gap_with_no_detail_are_named():
    plan = {"steps": [_step("b"), _step("a")], "actions": [_action("a:x", "a", "not_possible")],
            "gaps": [{"kind": "download_size_unknown"}]}
    problems = plan_problems(plan, IDS)
    assert len(problems) == 3 and "['b', 'a']" in problems[0] and "a:x" in problems[1] and "download" in problems[2]


def test_a_step_left_pending_says_why_unless_a_step_before_it_failed_and_stops_the_ones_after():
    stopped = {"plan": {"steps": [_step("a"), _step("b", "failed", cause="no store"), _step("c", "pending")]}}
    assert unexplained(stopped) == []
    silent = {"plan": {"steps": [_step("a"), _step("b", "pending"), _step("c", "failed", cause="no store")]}}
    assert unexplained(silent) == ["lo step b è pending senza causa"]


def test_an_action_left_pending_under_an_ended_step_says_why():
    plan = {"steps": [_step("a"), _step("b", "failed", cause="x"), _step("c", "skipped")],
            "actions": [_action("a:x", "a", "pending"), _action("a:y", "a", "pending", gap="model_not_run"),
                        _action("a:z", "a", "awaiting_approval", hosts=["github.com"]),
                        _action("b:x", "b", "pending"), _action("c:x", "c", "skipped")]}
    assert unexplained({"plan": plan}) == ["l'azione a:x è pending senza causa"]


def test_a_source_that_did_not_run_says_why_and_every_gap_says_what():
    case = {"sources": [{"source": "maven", "state": "failed", "reason": "exit 1"}, {"source": "uv", "state": "not_run"},
                        {"source": "make", "state": "unavailable"}, {"source": "noir", "state": "ran"}],
            "gaps": [{"kind": "model_not_run", "source": "uv", "detail": "8 model commands not run"}],
            "dynamic_gaps": [{"kind": "no_tests"}]}
    assert unexplained(case) == ["la sorgente make è unavailable senza causa",
                                 "una lacuna senza kind o detail: {'kind': 'no_tests'}"]


def test_a_module_found_before_and_missed_or_wrong_now_is_lost_and_one_missed_in_both_is_not():
    before = {"units": {"given": True, "missed": ["u@a"], "wrong": []},
              "workspace": {"given": True, "missed": [], "wrong": []}, "units.config": {"given": False}}
    now = {"units": {"given": True, "missed": ["u@a", "u@b"], "wrong": [{"item": "u@c"}]}, "workspace": {"given": False}}
    assert lost(now, before) == [("units", "u@b"), ("units", "u@c"), ("workspace", "*")]


def test_the_latest_result_is_the_last_by_name_and_no_report_is_one(tmp_path):
    for name in ("2026-11-28-t1-gate-prova.json", "2026-11-28-t1-gate-prova.report.json", "2026-11-28-t1-gate.json",
                 "2026-11-30-other.json"):
        (tmp_path / name).write_text("{}", encoding="utf-8")
    assert latest(tmp_path).name == "2026-11-28-t1-gate.json"
    (tmp_path / "2026-11-28-t1-gate.json").unlink()
    assert latest(tmp_path).name == "2026-11-28-t1-gate-prova.json"
    assert latest(tmp_path / "none") is None
