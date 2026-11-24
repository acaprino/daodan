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

import stack_recognition  # noqa: E402
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
        monkeypatch.setattr(stack_recognition, "run", lambda *args, **kwargs: recognized)
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
    scan(1, answer([entry("fastapi", sign("api/requirements.txt", "fastapi"),
                          sign("api/requirements.txt", "fastapi", "requirements@1"))],
                   ran=["requirements", "stack-analyser"]))
    failed = {"checker": "stack-analyser", "state": "failed", "reason": "no Node"}
    cause = {"kind": "checker_failed", "checker": "stack-analyser", "detail": "no Node"}
    record = scan(2, answer(ran=["registry_hosts"], gaps=[cause], checkers=[failed]))
    assert sorted(signs_of(record, "fastapi")) == [("requirements@1", "api/requirements.txt", 1, "scan-1"),
                                                   ("stack-analyser", "api/requirements.txt", 1, "scan-1")]
    assert cause in record["gaps"] and failed in record["checkers"]
    assert {"kind": "signs_kept", "sources": ["requirements", "stack-analyser"], "scans": ["scan-1"]} in record["gaps"]


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


def test_a_source_that_ran_since_makes_the_record_stale(scan, manifest):
    """A full scan whose source states differ from the last scan's derives again, even with the same facts: the
    signs that source kept from before are replaced by what it says now."""
    scan(1, answer([entry("fastapi", sign("web/package.json", "fastapi", "renovate@41"))], ran=["renovate"]))
    facts = {"packages": [], "excluded": [{"path": "skipped-1/", "why": "test"}], "inputs_digest": "scan-1"}
    assert technologies.state(manifest, facts=facts) == "fresh"
    assert technologies.state(manifest, facts={**facts, "sources": [
        {"source": "renovate@41", "state": "ran"}]}) == "stale"


def test_a_record_the_tool_failed_for_is_stale_once_this_process_remembers_no_failure(scan, manifest, monkeypatch):
    """Node installed or the network back since: a later process runs the tool again. The process that remembers the
    failure (`stack_analyser._failed`) does not."""
    failed = {"checker": "stack-analyser", "state": "failed", "reason": "no Node"}
    cause = {"kind": "checker_failed", "checker": "stack-analyser", "detail": "no Node"}
    scan(1, answer(ran=["registry_hosts"], gaps=[cause], checkers=[failed]))
    facts = {"packages": [], "excluded": [{"path": "skipped-1/", "why": "test"}], "inputs_digest": "scan-1"}
    monkeypatch.setattr(technologies, "_derived", set())  # a later process
    monkeypatch.setattr(stack_analyser, "_failed", {})
    assert technologies.state(manifest, facts=facts) == "stale"
    monkeypatch.setattr(stack_analyser, "_failed", {"cli": RuntimeError("no network")})
    assert technologies.state(manifest, facts=facts) == "fresh"


def test_a_failure_that_is_not_an_install_is_derived_once_per_process(scan, manifest, monkeypatch):
    """A timeout or an exit with an error is not remembered as an install is: the record this process derived for the
    same inputs stays fresh in it, and a later process derives it once again."""
    failed = {"checker": "stack-analyser", "state": "failed", "reason": "no answer within 300 s"}
    cause = {"kind": "checker_failed", "checker": "stack-analyser", "detail": "no answer within 300 s"}
    monkeypatch.setattr(stack_analyser, "_failed", {})
    scan(1, answer(ran=["registry_hosts"], gaps=[cause], checkers=[failed]))
    facts = {"packages": [], "excluded": [{"path": "skipped-1/", "why": "test"}], "inputs_digest": "scan-1"}
    assert technologies.state(manifest, facts=facts) == "fresh"
    runs = []
    monkeypatch.setattr(stack_recognition, "run", lambda *args, **kwargs: runs.append(1) or answer())
    technologies.ensure(manifest, facts=facts)
    assert runs == []
    monkeypatch.setattr(technologies, "_derived", set())  # a later process
    assert technologies.state(manifest, facts=facts) == "stale"


def test_a_kept_sign_leaves_when_the_premap_leaves_its_file_out(scan, manifest, monkeypatch):
    scan(1, answer([entry("redis", sign("api/requirements.txt", "redis", "renovate@41"))], ran=["renovate"]))
    monkeypatch.setattr(stack_recognition, "run", lambda *args, **kwargs: answer(ran=["stack-analyser"]))
    record = technologies.ensure(manifest, facts={"packages": [], "inputs_digest": "scan-2",
                                                  "excluded": [{"path": "api/", "why": "generated"}]})
    assert record["technologies"] == [] and not any(g["kind"] == "signs_kept" for g in record["gaps"])


def test_a_kept_sign_this_scan_made_again_is_there_once(scan):
    """A sign of a source outside `ran` that this scan made too is the sign of now, once."""
    redis = entry("redis", sign("web/package.json", "redis", "renovate@41"))
    scan(1, answer([redis], ran=["renovate"]))
    scan(2, answer([redis], ran=["stack-analyser"]))
    record = scan(3, answer([redis], ran=["stack-analyser"]))
    assert signs_of(record, "redis") == [("renovate@41", "web/package.json", 1, "scan-3")]


def test_reading_the_state_writes_no_premap(scan, manifest):
    """`state` is a read: with a pre-map that is not fresh (here one a pass is writing, unreadable) the record is stale,
    and the pre-map is left to the pass that writes it, never rewritten by a reader-only scan."""
    scan(1, answer(ran=["stack-analyser"]))
    written = technologies.premap.path(manifest)
    written.write_text("{}", encoding="utf-8")
    assert technologies.state(manifest) == "stale"
    assert written.read_text(encoding="utf-8") == "{}"


def test_a_site_is_a_line_of_a_file_and_the_tool_s_reading_of_a_declared_file_is_not_another():
    """The release reads a file by itself (no line, the name as written) and is given the pre-map's declaration of it
    (its line, the name as the pre-map keeps it): one site, whatever the spelling (`Sentry_SDK`, `sentry-sdk`; an image
    with or without its registry). Two packages of a technology in one file are two sites, by their lines, or, when
    only the release read the file, by their names."""
    def values(*signs):
        return [(s["path"], s["line"], s["value"]) for s in technologies.sites(list(signs))]

    assert values(sign("requirements.txt", "Sentry_SDK", line=None),
                  sign("requirements.txt", "sentry-sdk", "requirements@1", line=2)) == [
        ("requirements.txt", 2, "sentry-sdk")]
    assert values(sign("compose.yaml", "docker.io/library/postgres", line=None),
                  sign("compose.yaml", "postgres", "modules.py@1", line=3)) == [("compose.yaml", 3, "postgres")]
    assert values(sign("package.json", "@sentry/node", line=None), sign("package.json", "@sentry/react", line=None)) == [
        ("package.json", None, "@sentry/node"), ("package.json", None, "@sentry/react")]
    assert values(sign("package.json", "@sentry/node", line=None), sign("package.json", "@sentry/node", "npm@1", line=4),
                  sign("package.json", "@sentry/react", "npm@1", line=5)) == [
        ("package.json", 4, "@sentry/node"), ("package.json", 5, "@sentry/react")]


def test_a_grammar_placed_later_makes_the_record_stale(tmp_path, monkeypatch):
    """A record written while the host check had no grammar for a source (`source_grammar_unavailable`) is derived
    again once the grammar is there."""
    import registry_hosts
    manifest = snapshot_of(tmp_path, {"api/client.py": 'URL = "https://api.telegram.org/bot"\n'})
    facts = {"packages": [], "inputs_digest": "scan-1"}
    monkeypatch.setattr(registry_hosts.ts, "get_parser", lambda _grammar: None)
    monkeypatch.setattr(technologies, "get_parser", lambda _grammar: None)
    record = technologies.ensure(manifest, facts=facts)
    assert {"python"} == {g["language"] for g in record["gaps"] if g["kind"] == "source_grammar_unavailable"}
    assert technologies.state(manifest, facts=facts) == "fresh"
    monkeypatch.undo()  # the grammar is placed
    assert technologies.state(manifest, facts=facts) == "stale"
