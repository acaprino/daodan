"""The helpers of the three runs (`modal_runs.py`), on synthetic edges, records and events. Run: python tests/modal_pytest.py
benchmarks/project-model/test_modal_runs.py (Modal's client is there)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "daodan/core")]

import modal_runs  # noqa: E402

BUY = {"from": "react-app/src/App.tsx::App", "to": "react-app/src/checkout.ts::startCheckout", "type": "chiama"}
RECEIPT = {"from": "react-app/src/App.tsx::App.onClick", "to": "react-app/src/checkout.ts::saveReceipt", "type": "chiama"}
NATIVE = {"from": "react-app/src/checkout.ts::saveReceipt", "to": "react-app/src-tauri/src/lib.rs::save_receipt",
          "type": "invoca"}


def test_an_expected_link_is_found_by_an_edge_between_its_two_places_whatever_its_type():
    found = modal_runs.expected_links([BUY, RECEIPT, NATIVE])
    assert (found["found"], found["of"]) == (3, 4)
    assert found["missing"] == ["the checkout handler calls the Python backend"]


def test_an_edge_to_another_name_or_another_file_is_no_link_found():
    wrong_name = {**BUY, "to": "react-app/src/checkout.ts::watchOrders"}
    wrong_file = {**NATIVE, "to": "react-app/src-tauri/src/main.rs::save_receipt"}
    found = modal_runs.expected_links([wrong_name, wrong_file])
    assert found["found"] == 0 and len(found["missing"]) == 4


def test_a_method_of_a_class_is_the_name_it_is_called_by():
    method = {"from": "react-app/src/checkout.ts::Api.saveReceipt", "to": "react-app/src-tauri/src/lib.rs::save_receipt"}
    assert modal_runs.expected_links([method])["found"] == 1


def test_the_lines_a_run_adds_to_the_records_are_those_after_what_was_there():
    files = {"a/container-runs.jsonl": ['{"phase": "prepare"}', '{"phase": "execute"}'],
             "b/container-runs.jsonl": ['{"phase": "node-restore"}']}
    assert modal_runs.new_lines({"a/container-runs.jsonl": 1}, files) == ['{"phase": "execute"}',
                                                                          '{"phase": "node-restore"}']
    assert modal_runs.new_lines(dict.fromkeys(files, 99), files) == []


def test_the_seconds_of_a_step_run_from_its_start_to_its_end():
    event = lambda kind, step, at: {"kind": kind, "step": step, "at": f"2026-11-24T10:{at}Z"}  # noqa: E731
    events = [event("step.started", "find_modules", "00:00.000000"), event("step.finished", "find_modules", "00:12.500000"),
              event("step.started", "link_calls", "00:12.500000"), event("step.failed", "link_calls", "01:00.000000")]
    assert modal_runs.step_seconds(events) == {"find_modules": 12.5, "link_calls": 47.5}


def test_a_run_is_written_as_score_reads_it_and_unreadable_links_leave_no_file(tmp_path):
    run = {"seconds": 12.5, "step_seconds": {"find_modules": 3.0}, "steps": {}, "links": {"found": 2, "of": 4, "missing": []},
           "events": '{"at": "x"}\n', "containers": '{"phase": "prepare"}'}
    modal_runs.write_run(tmp_path / "a", run)
    assert sorted(path.name for path in (tmp_path / "a").iterdir()) == [
        "container-runs.jsonl", "links.json", "pipeline-events.jsonl", "run.json"]
    assert json.loads((tmp_path / "a" / "run.json").read_text(encoding="utf-8")) == {
        "seconds": 12.5, "step_seconds": {"find_modules": 3.0}, "steps": {}, "links": {"found": 2, "of": 4, "missing": []}}
    modal_runs.write_run(tmp_path / "b", {**run, "links": {"error": "ValueError: boom"}})
    assert not (tmp_path / "b" / "links.json").exists()
