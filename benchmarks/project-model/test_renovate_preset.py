"""Il preset di Renovate chiesto nell'app (T0.C.10), riletto dai risultati committati di `modal_pipeline.py --cases
real-bank-of-anthos`: `results/pipeline/2026-11-28-t0c10-renovate-undecided.json` (nessuna risposta) e
`...-approved.json` (`--approve api.github.com`, l'host approvato «sempre» nello stato di `egress` della corsa).

- Senza risposta: Renovate ha `model_failed` (il repository chiuso) e `approval_required` per `api.github.com`, la
  richiesta di `renovate` attende in `egress`, l'azione del piano è `awaiting_approval`; le funzioni del Cancello T1
  (`test_gate_t1`) non vi trovano un piano rotto, una perdita senza causa né una voce persa senza una lacuna.
- Approvato: l'estrazione è girata di nuovo con l'host (`premap-runs/renovate-hosts`), le toolchain sono voce per voce
  (strumento, versione, file) quelle della pre-mappa di riferimento (`results/daodan_premap_corpus.json`), Renovate non ha
  lacune oltre a `file_withheld` e nessuna richiesta attende.

Su Modal: python tests/modal_pytest.py benchmarks/project-model/test_renovate_preset.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "daodan/core")]

import test_gate_t1 as gate  # noqa: E402

CASE, HOST = "real-bank-of-anthos", "api.github.com"
RUNS = HERE / "results" / "pipeline"


def case(answer: str) -> dict:
    found = json.loads((RUNS / f"2026-11-28-t0c10-renovate-{answer}.json").read_text(encoding="utf-8"))
    assert "error" not in found[CASE], found[CASE].get("error")
    return found[CASE]


def renovate(found: dict) -> tuple[list[dict], list[dict]]:
    """Le lacune di Renovate (oltre ai file che Daodan non legge) e le azioni del piano della sua sorgente."""
    gaps = [gap for gap in found["gaps"] if str(gap.get("source", "")).startswith("renovate@")
            and gap["kind"] != "file_withheld"]
    return gaps, [action for action in found["plan"]["actions"] if action["id"].startswith("find_modules:renovate@")]


def toolchains(items) -> list[tuple]:
    return sorted((item["tool"], item.get("version"), item["declared_in"]) for item in items)


REFERENCE = json.loads((HERE / "results" / "daodan_premap_corpus.json").read_text(encoding="utf-8"))[CASE]


def test_without_an_answer_the_preset_host_is_a_request_and_the_gate_finds_every_loss_explained():
    import pipeline
    found = case("undecided")
    gaps, [action] = renovate(found)
    assert sorted(gap["kind"] for gap in gaps) == ["approval_required", "model_failed"]
    assert [gap["hosts"] for gap in gaps if gap["kind"] == "approval_required"] == [[HOST]]
    assert (action["state"], action["hosts"]) == ("awaiting_approval", [HOST])
    assert [(group["tool"], [row["host"] for row in group["requests"]]) for group in found["egress"]["requests"]] == [
        ("renovate", [HOST])]
    assert len(found["toolchains"]) < len(REFERENCE["output"]["toolchains"])  # what the preset keeps from the pre-map
    assert gate.plan_problems(found["plan"], pipeline.IDS) == []
    assert gate.unexplained(found) == []
    lost = gate.lost(found["premap"], REFERENCE["premap"])
    assert lost and gate.unexplained_losses(lost, found["gaps"], REFERENCE["output"]) == []


def test_approved_the_extraction_runs_again_with_the_host_and_finds_the_toolchains_of_the_reference():
    found = case("approved")
    gaps, [action] = renovate(found)
    assert found["egress"] == {"approved": [HOST], "requests": []}
    assert gaps == [] and action["state"] == "done"
    assert any(path.startswith("premap-runs/renovate-hosts/") for path in found["logs"])
    assert toolchains(found["toolchains"]) == toolchains(REFERENCE["output"]["toolchains"])
