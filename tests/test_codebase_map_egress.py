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
    egress.PENDING.clear()
    egress.SESSIONS.clear()
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


def test_the_refusals_of_a_proxy_log_are_read_in_order_and_once():
    log = "\n".join(["ready 3128", '@@daodan-refused {"host": "A.example.com", "port": "443"}', "noise",
                     '@@daodan-refused {"host": "a.example.com", "port": "443"}', "@@daodan-refused not json",
                     '@@daodan-refused {"host": 3, "port": "1"}', '@@daodan-refused {"host": "", "port": "1"}',
                     '@@daodan-refused {"host": "10.0.0.1", "port": "8080"}', "@@daodan-refused []"])
    assert egress.refused(log) == [{"host": "a.example.com", "port": "443"}, {"host": "10.0.0.1", "port": "8080"}]


@pytest.mark.parametrize("address, expected", [
    ("10.1.2.3", True), ("192.168.0.9", True), ("127.0.0.1", True), ("169.254.169.254", True), ("::1", True),
    ("fe80::1", True), ("fd00::1", True), ("::ffff:10.0.0.1", True), ("93.184.216.34", False),
    ("2606:2800:220:1::1", False), ("not an address", False)])
def test_the_users_own_network_is_private_loopback_and_link_local(address, expected):
    assert egress.private(address) is expected


def test_resolve_reads_literals_and_looks_each_name_up_once_up_to_the_cap(monkeypatch):
    asked = []

    def lookup(host, *_, **__):
        asked.append(host)
        if host == "gone.example.com":
            raise OSError("no such host")
        return [(0, 0, 0, "", ("192.168.1.5" if host == "nas.example.com" else "93.184.216.34", 0))]

    monkeypatch.setattr(egress.socket, "getaddrinfo", lookup)
    requests = [{"host": "10.0.0.1", "port": "443"}, {"host": "[::1]", "port": "443"},
                {"host": "nas.example.com", "port": "443"}, {"host": "nas.example.com", "port": "8080"},
                {"host": "gone.example.com", "port": "443"}, {"host": "late.example.com", "port": "443"}]
    out = egress.resolve(requests, lookups=2)
    assert asked == ["nas.example.com", "gone.example.com"]  # literals cost no lookup, a name one, the cap holds
    assert [(r["host"], r["address"], r["network"]) for r in out] == [
        ("10.0.0.1", "10.0.0.1", True), ("[::1]", "::1", True), ("nas.example.com", "192.168.1.5", True),
        ("nas.example.com", "192.168.1.5", True), ("gone.example.com", None, False), ("late.example.com", None, False)]


def test_requests_split_the_refusals_into_requests_and_host_denied_gaps(monkeypatch):
    monkeypatch.setattr(egress.socket, "getaddrinfo", lambda host, *_, **__: [(0, 0, 0, "", ("93.184.216.34", 0))])
    state, session = egress.answer(egress.load(), egress.new_session(), "blocked.example.com", PROJECT, "block")
    state, session = egress.answer(state, session, "no.example.com", PROJECT, "no")
    refused = [{"host": host, "port": "443"} for host in
               ("blocked.example.com", "no.example.com", "ask.example.com", "pypi.org")]
    refused.append({"host": "10.0.0.5", "port": "8080"})
    asked, gaps = egress.requests(refused, PROJECT, state, session, {"ask.example.com": ["pom.xml"]})
    assert [(g["kind"], g["host"], g["port"]) for g in gaps] == [("host_denied", "blocked.example.com", "443"),
                                                                 ("host_denied", "no.example.com", "443")]
    assert [(r["host"], r["port"], r["address"], r["network"], r["declared_in"]) for r in asked] == [
        ("ask.example.com", "443", "93.184.216.34", False, ["pom.xml"]), ("10.0.0.5", "8080", "10.0.0.5", True, [])]
    # a canonical host refused (another port) is neither a request nor a gap


def test_collect_registers_the_requests_once_and_returns_them_with_the_gaps(monkeypatch):
    monkeypatch.setattr(egress.socket, "getaddrinfo", lambda host, *_, **__: [(0, 0, 0, "", ("93.184.216.34", 0))])
    egress.save({"whitelist": {}, "blacklist": ["blocked.example.com"]})
    refused = [{"host": "ask.example.com", "port": "443"}, {"host": "blocked.example.com", "port": "443"}]
    asked, gaps = egress.collect(PROJECT, refused)
    assert [r["host"] for r in asked] == ["ask.example.com"] and [g["host"] for g in gaps] == ["blocked.example.com"]
    egress.collect(PROJECT, refused)  # the second run: no duplicate
    assert [r["host"] for r in egress.pending(PROJECT)] == ["ask.example.com"]
    assert egress.pending("/work/other") == []
    egress.SESSIONS[PROJECT] = egress.answer(egress.load(), egress.session(PROJECT), "ask.example.com", PROJECT, "no")[1]
    assert egress.collect(PROJECT, refused)[0] == []
    assert [g["host"] for g in egress.collect(PROJECT, refused)[1]] == ["ask.example.com", "blocked.example.com"]


def test_an_approval_gap_names_the_hosts_and_the_files_that_declare_them():
    assert egress.approval_gap([]) == []
    [gap] = egress.approval_gap([{"host": "a.example.com", "port": "443", "declared_in": ["pom.xml"]},
                                 {"host": "b.example.com", "port": "80", "declared_in": []}])
    assert gap["kind"] == "approval_required" and gap["hosts"] == ["a.example.com", "b.example.com"]
    assert "a.example.com:443 (declared in pom.xml)" in gap["detail"] and "b.example.com:80" in gap["detail"]


def test_an_apt_archive_is_approved_as_its_host_is():
    state, session = egress.answer(egress.load(), egress.new_session(), "deb.example.com", PROJECT, "always")
    assert egress.decide("http://deb.example.com", PROJECT, state, session) == "allow"
    assert egress.decide("http://other.example.com", PROJECT, state, session) == "ask"
    assert egress.decide("http://archive.ubuntu.com", PROJECT, state, session) == "allow"  # a canonical archive
    state, session = egress.answer(state, session, "deb.example.com", PROJECT, "block")
    assert egress.decide("http://deb.example.com", PROJECT, state, session) == "deny"


def test_resolve_reaches_no_network_for_literals_and_localhost():
    out = egress.resolve([{"host": "127.0.0.1", "port": "80"}, {"host": "localhost", "port": "80"}])
    assert out[0]["network"] is True and out[1]["network"] is True
