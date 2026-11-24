"""The rule of the sources in `technologies.derive`: a scan replaces the signs of the sources it ran and keeps the others,
each with the scan it comes from, while its file exists (`technologies.merge`).

The recogniser is replaced by a function that answers `found`, `checkers`, `gaps` and `ran` written by hand.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_stack_sources.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))
sys.path.insert(0, str(ROOT / "tests"))

import service_registry  # noqa: E402
import stack_analyser  # noqa: E402
import technologies  # noqa: E402
from test_codebase_map_stack_recognition import snapshot_of  # noqa: E402

FILES = {"api/requirements.txt": "fastapi\nredis\n", "web/package.json": '{"name": "web"}\n'}


def sign(path, value="x", source="stack-analyser", line=1, kind="package", strength="declared"):
    return {"sign": kind, "value": value, "path": path, "line": line, "strength": strength, "source": source}


def entry(ident, *signs):
    return {"id": ident, "name": ident, "kind": "project", "category": "framework", "type": "altro", "site": None,
            "mark": None, "source": "registry", "signs": list(signs)}


def answer(found=(), ran=(), gaps=(), checkers=({"checker": "stack-analyser", "state": "ran"},)):
    return {"found": list(found), "checkers": list(checkers), "gaps": list(gaps), "ran": list(ran)}


@pytest.fixture
def manifest(tmp_path):
    return snapshot_of(tmp_path, FILES)


@pytest.fixture
def scan(manifest, monkeypatch):
    """`scan(number, answer)`: the stack step of the pre-map `scan-<number>`, the recogniser answering `answer`."""
    def run(number, recognized):
        monkeypatch.setattr(service_registry, "run", lambda *args, **kwargs: recognized)
        facts = {"packages": [], "excluded": [{"path": f"skipped-{number}/", "why": "test"}],
                 "inputs_digest": f"scan-{number}"}
        return technologies.ensure(manifest, facts=facts)
    return run


def signs_of(record, ident):
    return [(s["source"], s["path"], s["line"], s["scan"]) for e in record["technologies"] if e["id"] == ident
            for s in e["signs"]]


def test_a_fast_scan_keeps_the_signs_of_the_sources_it_did_not_run(scan):
    scan(1, answer([entry("fastapi", sign("web/package.json", "fastapi", "renovate@41"),
                          sign("api/requirements.txt", "fastapi", line=1))], ran=["renovate", "stack-analyser"]))
    record = scan(2, answer([entry("fastapi", sign("api/requirements.txt", "fastapi", line=2))],
                            ran=["requirements", "stack-analyser"]))
    assert sorted(signs_of(record, "fastapi")) == [("renovate@41", "web/package.json", 1, "scan-1"),
                                                   ("stack-analyser", "api/requirements.txt", 2, "scan-2")]
    assert {"kind": "signs_kept", "sources": ["renovate"], "scans": ["scan-1"]} in record["gaps"]


def test_a_source_that_ran_replaces_its_signs(scan):
    scan(1, answer([entry("fastapi", sign("api/requirements.txt", "fastapi")),
                    entry("redis", sign("api/requirements.txt", "redis", line=2))], ran=["stack-analyser"]))
    record = scan(2, answer([entry("fastapi", sign("api/requirements.txt", "fastapi"))], ran=["stack-analyser"]))
    assert [e["id"] for e in record["technologies"]] == ["fastapi"]
    assert signs_of(record, "fastapi") == [("stack-analyser", "api/requirements.txt", 1, "scan-2")]
    assert not any(g["kind"] == "signs_kept" for g in record["gaps"])


def test_a_technology_stays_while_it_has_a_sign(scan):
    scan(1, answer([entry("redis", sign("web/package.json", "redis", "renovate@41"),
                          sign("api/requirements.txt", "redis"))], ran=["renovate", "stack-analyser"]))
    record = scan(2, answer(ran=["stack-analyser"]))
    assert signs_of(record, "redis") == [("renovate@41", "web/package.json", 1, "scan-1")]
    assert [e["name"] for e in record["technologies"]] == ["Redis"]  # the registry of now gives the name, not the record


def test_a_kept_sign_leaves_with_its_file(scan, manifest):
    scan(1, answer([entry("redis", sign("web/package.json", "redis", "renovate@41"))], ran=["renovate"]))
    assert signs_of(scan(2, answer(ran=["stack-analyser"])), "redis") == [("renovate@41", "web/package.json", 1, "scan-1")]
    (manifest.parents[1] / "app/web/package.json").unlink()
    record = scan(3, answer(ran=["stack-analyser"]))
    assert record["technologies"] == [] and not any(g["kind"] == "signs_kept" for g in record["gaps"])


def test_without_the_tool_the_previous_signs_stay_and_a_gap_says_why(scan):
    scan(1, answer([entry("fastapi", sign("api/requirements.txt", "fastapi"))], ran=["stack-analyser"]))
    failed = {"checker": "stack-analyser", "state": "failed", "reason": "no Node"}
    cause = {"kind": "checker_failed", "checker": "stack-analyser", "detail": "no Node"}
    record = scan(2, answer(ran=["registry_hosts"], gaps=[cause], checkers=[failed]))
    assert signs_of(record, "fastapi") == [("stack-analyser", "api/requirements.txt", 1, "scan-1")]
    assert cause in record["gaps"] and failed in record["checkers"]
    assert {"kind": "signs_kept", "sources": ["stack-analyser"], "scans": ["scan-1"]} in record["gaps"]


def test_a_record_of_the_old_shape_keeps_nothing(scan, manifest):
    old = {"sign": "package", "value": "redis", "path": "api/requirements.txt", "line": 1, "strength": "declared"}
    manifest.with_name(technologies.FILE).write_text(json.dumps({
        "schema": technologies.SCHEMA, "technologies": [{"id": "redis", "name": "Redis", "signs": [old]}],
        "mentioned": [{"id": "stripe", "name": "Stripe", "signs": [{**old, "strength": "mentioned"}]}]}), encoding="utf-8")
    record = scan(1, answer(ran=["stack-analyser"]))
    assert record["technologies"] == [] and record["mentioned"] == []
    assert not any(g["kind"] == "signs_kept" for g in record["gaps"])


def test_a_new_release_makes_the_record_stale(scan, manifest, monkeypatch):
    scan(1, answer([entry("fastapi", sign("api/requirements.txt", "fastapi"))], ran=["stack-analyser"]))
    facts = {"packages": [], "excluded": [{"path": "skipped-1/", "why": "test"}], "inputs_digest": "scan-1"}
    assert technologies.state(manifest, facts=facts) == "fresh"
    monkeypatch.setattr(stack_analyser, "VERSION", "9.9.9-daodan.1")
    assert technologies.state(manifest, facts=facts) == "stale"
    monkeypatch.undo()
    monkeypatch.setattr(stack_analyser, "SHA256", "0" * 64)
    assert technologies.state(manifest, facts=facts) == "stale"
