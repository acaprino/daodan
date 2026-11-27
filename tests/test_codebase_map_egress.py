"""The criterion of egress: canonical hosts, the user's four answers and the file they are kept in."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import egress  # noqa: E402

PROJECT = "/work/app"


@pytest.fixture(autouse=True)
def shared(tmp_path, monkeypatch):
    monkeypatch.setenv("DAODAN_SHARED_DIR", str(tmp_path / "shared"))
    return tmp_path / "shared"


def test_the_canonical_hosts_pass_and_every_other_host_asks():
    state, session = egress.load(), egress.new_session()
    assert all(egress.decide(host, PROJECT, state, session) == "allow" for host in container.REGISTRIES)
    assert egress.decide("NodeJS.org", PROJECT, state, session) == "allow"  # a host has no case
    for host in ("example.com", "github.com", "codeload.github.com", "objects.githubusercontent.com",
                 "release-assets.githubusercontent.com", "storage.googleapis.com", "aka.ms",
                 "cache-redirector.jetbrains.com", "d2xrhe97vsfxuc.cloudfront.net", "scala.jfrog.io",
                 "dotnetcli.azureedge.net", "playwright.azureedge.net"):
        assert egress.decide(host, PROJECT, state, session) == "ask", host


def test_always_is_for_one_project_and_outlives_the_analysis(shared):
    state, session = egress.answer(egress.load(), egress.new_session(), "Git.Example.com", PROJECT, "always")
    egress.save(state)
    assert egress.decide("git.example.com", PROJECT, egress.load(), egress.new_session()) == "allow"
    assert egress.decide("git.example.com", "/work/other", egress.load(), egress.new_session()) == "ask"
    assert json.loads((shared / "egress.json").read_text(encoding="utf-8")) == {
        "whitelist": {PROJECT: ["git.example.com"]}, "blacklist": []}


def test_once_and_no_last_for_the_analysis_only(shared):
    state, session = egress.answer(egress.load(), egress.new_session(), "a.example.com", PROJECT, "once")
    state, session = egress.answer(state, session, "b.example.com", PROJECT, "no")
    assert egress.decide("a.example.com", PROJECT, state, session) == "allow"
    assert egress.decide("b.example.com", PROJECT, state, session) == "deny"
    assert state == egress.load() == {"whitelist": {}, "blacklist": []}  # nothing durable: the file is never written
    assert not (shared / "egress.json").exists()
    assert egress.decide("a.example.com", PROJECT, state, egress.new_session()) == "ask"
    assert egress.decide("b.example.com", PROJECT, state, egress.new_session()) == "ask"


def test_the_latest_answer_of_the_analysis_stands():
    state, session = egress.load(), egress.new_session()
    state, session = egress.answer(state, session, "x.example.com", PROJECT, "no")
    state, session = egress.answer(state, session, "x.example.com", PROJECT, "once")
    assert egress.decide("x.example.com", PROJECT, state, session) == "allow"
    state, session = egress.answer(state, session, "x.example.com", PROJECT, "no")
    assert egress.decide("x.example.com", PROJECT, state, session) == "deny"


def test_block_refuses_everywhere_even_a_canonical_or_an_approved_host():
    state, session = egress.answer(egress.load(), egress.new_session(), "x.example.com", PROJECT, "always")
    for host in ("x.example.com", "pypi.org"):
        state, session = egress.answer(state, session, host, PROJECT, "block")
        assert egress.decide(host, PROJECT, state, session) == "deny"
        assert egress.decide(host, "/work/other", state, egress.new_session()) == "deny"


def test_answer_changes_nothing_it_was_given_and_refuses_an_unknown_reply():
    state, session = egress.load(), egress.new_session()
    egress.answer(state, session, "x.example.com", PROJECT, "always")
    egress.answer(state, session, "x.example.com", PROJECT, "block")
    assert state == {"whitelist": {}, "blacklist": []} and session == {"allow": [], "deny": []}
    with pytest.raises(ValueError):
        egress.answer(state, session, "x.example.com", PROJECT, "maybe")


@pytest.mark.parametrize("text", ["", "not json", "[]", '{"whitelist": [], "blacklist": {}}', '{"whitelist": {}}'])
def test_an_unreadable_file_is_an_empty_state(shared, text):
    shared.mkdir(parents=True)
    (shared / "egress.json").write_text(text, encoding="utf-8")
    assert egress.load() == {"whitelist": {}, "blacklist": []}


def test_a_malformed_entry_is_dropped_and_the_rest_kept(shared):
    shared.mkdir(parents=True)
    (shared / "egress.json").write_text(json.dumps({"whitelist": {"p": ["a.example.com", 3], "q": "x"},
                                                    "blacklist": ["b.example.com", None]}), encoding="utf-8")
    assert egress.load() == {"whitelist": {"p": ["a.example.com"]}, "blacklist": ["b.example.com"]}
