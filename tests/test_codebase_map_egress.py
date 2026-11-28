"""The criterion of egress: canonical hosts, the user's four answers and where they are kept: the project's lists in
its project file, the analysis's answers in the shared folder.

    modal run tests/modal_pytest.py --args "tests/test_codebase_map_egress.py -q"
"""
from __future__ import annotations

import json
import sys
from contextlib import closing
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import egress  # noqa: E402
import project_file  # noqa: E402
import repository  # noqa: E402

PROJECT = "/work/app"  # no checkout of the app: the answers of an analysis only
EMPTY = {"always": [], "block": []}


@pytest.fixture(autouse=True)
def shared(tmp_path, monkeypatch):
    monkeypatch.setenv("DAODAN_SHARED_DIR", str(tmp_path / "shared"))
    egress.PENDING.clear()
    return tmp_path / "shared"


def _checkout(tmp_path: Path, name: str = "app") -> str:
    """A project laid out as the app's checkout (`repository.checkout`), whose project file keeps its lists."""
    folder = tmp_path / "repositories" / "owner" / name / "commit" / repository.CHECKOUT
    folder.mkdir(parents=True)
    return str(folder.resolve())


@pytest.fixture
def checkout(tmp_path) -> str:
    return _checkout(tmp_path)


def _rows(project: str) -> tuple[list[dict], list[dict]]:
    with closing(project_file.open_project(egress.project_file_of(project))) as db:
        return project_file.answers(db, egress.person())


def test_the_canonical_hosts_pass_and_every_other_host_asks():
    state, session = egress.load(PROJECT), egress.new_session()
    assert all(egress.decide(host, PROJECT, state, session) == "allow" for host in container.REGISTRIES)
    assert egress.decide("NodeJS.org", PROJECT, state, session) == "allow"  # a host has no case
    for host in ("example.com", "github.com", "codeload.github.com", "objects.githubusercontent.com",
                 "release-assets.githubusercontent.com", "storage.googleapis.com", "aka.ms",
                 "cache-redirector.jetbrains.com", "d2xrhe97vsfxuc.cloudfront.net", "scala.jfrog.io",
                 "dotnetcli.azureedge.net", "playwright.azureedge.net"):
        assert egress.decide(host, PROJECT, state, session) == "ask", host


def test_always_is_for_one_project_kept_in_its_project_file_with_author_and_instant(tmp_path, checkout):
    other = _checkout(tmp_path, "other")
    egress.respond("Git.Example.com", checkout, "always")
    assert egress.decide("git.example.com", checkout, egress.load(checkout), egress.new_session()) == "allow"
    assert egress.decide("git.example.com", other, egress.load(other), egress.new_session()) == "ask"
    path = egress.project_file_of(checkout)
    assert path == repository.project_path(checkout) == tmp_path / "repositories/owner/app/project.daodan"
    [row], others = _rows(checkout)
    assert others == []
    assert (row["host"], row["answer"], row["author"]) == ("git.example.com", "always", egress.person())
    assert row["answered_at"].endswith("+00:00")
    assert not project_file.started(path)  # the schema and the answer: the first analysis writes the project into it
    egress.end(checkout)  # it outlives the analysis
    assert egress.load(checkout) == {"always": ["git.example.com"], "block": []}


def test_once_and_no_last_for_the_analysis_only_and_write_no_project_file(checkout):
    egress.respond("a.example.com", checkout, "once")
    egress.respond("b.example.com", checkout, "no")
    state, session = egress.load(checkout), egress.session(checkout)
    assert egress.decide("a.example.com", checkout, state, session) == "allow"
    assert egress.decide("b.example.com", checkout, state, session) == "deny"
    assert state == EMPTY and not egress.project_file_of(checkout).exists()  # nothing durable
    egress.end(checkout)
    assert egress.decide("a.example.com", checkout, state, egress.session(checkout)) == "ask"
    assert egress.decide("b.example.com", checkout, state, egress.session(checkout)) == "ask"


def test_a_folder_that_is_no_checkout_of_the_app_has_no_lists_and_keeps_no_answer(tmp_path):
    folder = tmp_path / "work" / "app"
    (tmp_path / "project.daodan").write_bytes(b"")  # where `repository.project_path` would look: never read
    assert egress.project_file_of(str(folder)) is None and egress.project_file_of(None) is None
    assert egress.load(str(folder)) == egress.load(None) == EMPTY
    for reply in ("always", "block"):
        with pytest.raises(ValueError, match="no checkout of the app"):
            egress.respond("x.example.com", str(folder), reply)
    egress.respond("x.example.com", str(folder), "once")  # the analysis's answers need no project file
    assert egress.session(str(folder))["allow"] == ["x.example.com"]


def test_only_the_persons_own_answers_apply_and_a_confirmed_one_becomes_theirs(checkout):
    """A file received from someone: their answers wait (`project_file.adopt`, the app's confirmation); MCP and the
    command line read `load`, so they never apply them."""
    path = egress.project_file_of(checkout)
    project_file.create(path)
    with closing(project_file.open_project(path, write=True)) as db:
        for host, said in (("a.example.com", "always"), ("b.example.com", "block"), ("c.example.com", "always")):
            project_file.keep_answer(db, host, said, f"not-{egress.person()}")
    assert egress.load(checkout) == EMPTY
    assert egress.decide("b.example.com", checkout, egress.load(checkout), egress.new_session()) == "ask"
    with closing(project_file.open_project(path, write=True)) as db:
        project_file.adopt(db, ["b.example.com", "A.example.com"], egress.person())
    assert egress.load(checkout) == {"always": ["a.example.com"], "block": ["b.example.com"]}
    own, others = _rows(checkout)
    assert others == [] and {row["author"] for row in own} == {egress.person()}  # c asks again


def test_the_latest_answer_of_the_analysis_stands():
    state, session = egress.load(PROJECT), egress.new_session()
    state, session = egress.answer(state, session, "x.example.com", PROJECT, "no")
    state, session = egress.answer(state, session, "x.example.com", PROJECT, "once")
    assert egress.decide("x.example.com", PROJECT, state, session) == "allow"
    state, session = egress.answer(state, session, "x.example.com", PROJECT, "no")
    assert egress.decide("x.example.com", PROJECT, state, session) == "deny"


def test_block_refuses_in_its_project_even_a_canonical_or_an_approved_host():
    state, session = egress.answer(EMPTY, egress.new_session(), "x.example.com", PROJECT, "always")
    for host in ("x.example.com", "pypi.org"):
        state, session = egress.answer(state, session, host, PROJECT, "block")
        assert egress.decide(host, PROJECT, state, session) == "deny"
    assert egress.decide("pypi.org", "/work/other", EMPTY, egress.new_session()) == "allow"  # another project's lists
    assert egress.decide("x.example.com", "/work/other", EMPTY, egress.new_session()) == "ask"


def test_a_host_is_in_one_list_the_latest_answer_and_block_takes_it_out_of_the_allowed_hosts():
    state, session = egress.answer(EMPTY, egress.new_session(), "x.example.com", PROJECT, "always")
    state, session = egress.answer(state, session, "x.example.com", PROJECT, "once")
    state, session = egress.answer(state, session, "x.example.com", PROJECT, "block")
    assert state == {"always": [], "block": ["x.example.com"]} and session["allow"] == []
    state, session = egress.answer(state, session, "x.example.com", PROJECT, "always")
    assert state == {"always": ["x.example.com"], "block": []}


def test_answer_changes_nothing_it_was_given_and_refuses_an_unknown_reply():
    state, session = egress.load(PROJECT), egress.new_session()
    egress.answer(state, session, "x.example.com", PROJECT, "always")
    egress.answer(state, session, "x.example.com", PROJECT, "block")
    assert state == EMPTY and session == {"allow": [], "deny": []}
    with pytest.raises(ValueError):
        egress.answer(state, session, "x.example.com", PROJECT, "maybe")


@pytest.mark.parametrize("content", [b"not a database, only some bytes" * 4, b""])
def test_a_project_file_that_cannot_be_read_has_no_lists_and_no_answer_is_kept_over_it(checkout, content):
    path = egress.project_file_of(checkout)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    assert egress.load(checkout) == EMPTY
    with pytest.raises(ValueError, match="non è un file di progetto"):
        egress.respond("x.example.com", checkout, "always")
    assert path.read_bytes() == content


def test_the_shared_files_are_written_through_a_temporary_file_of_their_own_and_leave_none(shared):
    shared.mkdir(parents=True)
    (shared / f"{egress.SESSION_FILE}.partial").mkdir()  # a fixed temporary name another writer holds
    egress.respond("a.example.com", PROJECT, "once")
    assert egress.session(PROJECT)["allow"] == ["a.example.com"]
    assert sorted(path.name for path in shared.iterdir()) == [
        egress.PENDING_FILE, egress.SESSION_FILE, f"{egress.SESSION_FILE}.partial", egress.LOCK]


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
    assert sorted(asked) == ["gone.example.com", "nas.example.com"]  # literals cost no lookup, a name one, the cap
    assert [(r["host"], r["address"], r["network"]) for r in out] == [
        ("10.0.0.1", "10.0.0.1", True), ("[::1]", "::1", True), ("nas.example.com", "192.168.1.5", True),
        ("nas.example.com", "192.168.1.5", True), ("gone.example.com", None, False), ("late.example.com", None, False)]


def test_a_name_that_is_no_valid_name_or_does_not_answer_in_time_has_no_address(monkeypatch):
    """The real lookup raises ValueError for a label of 64 characters and for an empty one; a lookup past the time
    is left behind."""
    out = egress.resolve([{"host": "a" * 64 + ".x", "port": "443"}, {"host": "a..b", "port": "443"}])
    assert [r["address"] for r in out] == [None, None]
    import threading
    release = threading.Event()
    monkeypatch.setattr(egress.socket, "getaddrinfo", lambda *_, **__: release.wait(5) and [])
    try:
        assert egress.resolve([{"host": "slow.example.com", "port": "443"}], seconds=0.1)[0]["address"] is None
    finally:
        release.set()


def test_one_analysis_looks_up_lookups_names_in_all_and_a_pending_request_not_again(monkeypatch):
    asked = []
    monkeypatch.setattr(egress, "LOOKUPS", 3)
    monkeypatch.setattr(egress.socket, "getaddrinfo",
                        lambda host, *_, **__: asked.append(host) or [(0, 0, 0, "", ("93.184.216.34", 0))])
    egress.collect(PROJECT, [{"host": "a.example.com", "port": "443"}, {"host": "b.example.com", "port": "443"}])
    egress.collect(PROJECT, [{"host": "a.example.com", "port": "443"}, {"host": "10.0.0.9", "port": "443"}])
    assert sorted(asked) == ["a.example.com", "b.example.com"]  # pending, a is not looked up again
    [*_, late] = egress.collect(PROJECT, [{"host": "c.example.com", "port": "443"},
                                          {"host": "d.example.com", "port": "443"}])[0]
    assert len(asked) == 3 and late["address"] is None  # the third name of the analysis, then no more
    egress.respond("c.example.com", PROJECT, "no")  # an answer keeps the count
    egress.collect(PROJECT, [{"host": "e.example.com", "port": "443"}])
    assert len(asked) == 3
    egress.end(PROJECT)  # the next analysis looks up again
    egress.begin(PROJECT)
    egress.collect(PROJECT, [{"host": "e.example.com", "port": "443"}])
    assert asked[-1] == "e.example.com" and len(asked) == 4


def test_the_requests_are_grouped_by_the_tool_that_asked_and_the_command_line_only_lists_them(tmp_path, capsys):
    project = tmp_path / "app"
    key = str(project.resolve())
    with egress.asking("dotnet"):
        egress.collect(key, [{"host": "10.0.0.1", "port": "443"}])
        egress.preflight(key, ("10.0.0.2",))
    egress.collect(key, [{"host": "10.0.0.1", "port": "443"}, {"host": "10.0.0.3", "port": "443"}])
    assert [(g["tool"], [r["host"] for r in g["requests"]]) for g in egress.groups([key])] == [
        ("dotnet", ["10.0.0.1", "10.0.0.2"]), ("", ["10.0.0.3"])]  # a request keeps the tool that first asked
    assert egress.main([str(project)]) == 0
    assert json.loads(capsys.readouterr().out) == egress.groups([key])
    with pytest.raises(ValueError, match="no request waits"):
        egress.reply(key, ["10.0.0.9"], "once")
    with pytest.raises(ValueError, match="must be one of"):
        egress.reply(key, ["10.0.0.1"], "yes")
    egress.reply(key, ["10.0.0.1", "10.0.0.2"], "no")
    assert [g["tool"] for g in egress.groups([key])] == [""] and egress.session(key)["deny"] == ["10.0.0.1",
                                                                                               "10.0.0.2"]


def test_requests_split_the_refusals_into_requests_and_host_denied_gaps(monkeypatch):
    monkeypatch.setattr(egress.socket, "getaddrinfo", lambda host, *_, **__: [(0, 0, 0, "", ("93.184.216.34", 0))])
    state, session = egress.answer(EMPTY, egress.new_session(), "blocked.example.com", PROJECT, "block")
    state, session = egress.answer(state, session, "no.example.com", PROJECT, "no")
    refused = [{"host": host, "port": "443"} for host in
               ("blocked.example.com", "no.example.com", "ask.example.com", "pypi.org")]
    refused.append({"host": "10.0.0.5", "port": "8080"})
    asked, gaps = egress.requests(refused, PROJECT, state, session, {"ask.example.com": ["pom.xml"]})
    assert [(g["kind"], g["host"], g["port"]) for g in gaps] == [("host_denied", "blocked.example.com", "443"),
                                                                 ("host_denied", "no.example.com", "443")]
    assert [(r["host"], r["port"], r["address"], r["network"], r["declared_in"]) for r in asked] == [
        ("ask.example.com", "443", "93.184.216.34", False, ["pom.xml"]), ("10.0.0.5", "8080", "10.0.0.5", True, [])]
    # a canonical host refused at 443 (the run did not list it) is neither a request nor a gap
    [gap] = egress.requests([{"host": "pypi.org", "port": "8443"}], PROJECT, state, session)[1]
    assert (gap["kind"], gap["port"]) == ("host_denied", "8443") and "port 443 only" in gap["detail"]


def test_collect_registers_the_requests_once_and_returns_them_with_the_gaps(monkeypatch, checkout):
    monkeypatch.setattr(egress.socket, "getaddrinfo", lambda host, *_, **__: [(0, 0, 0, "", ("93.184.216.34", 0))])
    monkeypatch.setattr(sys.modules[__name__], "PROJECT", checkout)  # a checkout of the app: its lists are kept
    egress.respond("blocked.example.com", PROJECT, "block")
    refused = [{"host": "ask.example.com", "port": "443"}, {"host": "blocked.example.com", "port": "443"}]
    asked, gaps = egress.collect(PROJECT, refused)
    assert [r["host"] for r in asked] == ["ask.example.com"] and [g["host"] for g in gaps] == ["blocked.example.com"]
    egress.collect(PROJECT, refused)  # the second run: no duplicate
    assert [r["host"] for r in egress.pending(PROJECT)] == ["ask.example.com"]
    assert egress.pending("/work/other") == []
    egress.respond("ask.example.com", PROJECT, "no")
    assert egress.collect(PROJECT, refused)[0] == []
    assert [g["host"] for g in egress.collect(PROJECT, refused)[1]] == ["ask.example.com", "blocked.example.com"]


def test_an_approval_gap_names_the_hosts_and_the_files_that_declare_them():
    assert egress.approval_gap([]) == []
    [gap] = egress.approval_gap([{"host": "a.example.com", "port": "443", "declared_in": ["pom.xml"]},
                                 {"host": "b.example.com", "port": "80", "declared_in": []}])
    assert gap["kind"] == "approval_required" and gap["hosts"] == ["a.example.com", "b.example.com"]
    assert "a.example.com:443 (declared in pom.xml)" in gap["detail"] and "b.example.com:80" in gap["detail"]


def test_preflight_asks_for_the_hosts_nobody_decided_and_names_the_files_that_declare_them(monkeypatch, checkout):
    monkeypatch.setattr(egress.socket, "getaddrinfo", lambda host, *_, **__: [(0, 0, 0, "", ("93.184.216.34", 0))])
    monkeypatch.setattr(sys.modules[__name__], "PROJECT", checkout)  # a checkout of the app: its lists are kept
    egress.respond("ok.example.com", PROJECT, "always")
    egress.respond("blocked.example.com", PROJECT, "block")
    egress.declare(PROJECT, {"10.1.1.1": ["pom.xml", "build.gradle"]})
    hosts = ("pypi.org", "ok.example.com", "blocked.example.com", "10.1.1.1", "Github.com", "10.1.1.1",
             "http://deb.example.com", "http://archive.ubuntu.com")
    asked, gaps = egress.preflight(PROJECT, hosts)
    assert [(r["host"], r["port"], r["declared_in"]) for r in asked] == [
        ("10.1.1.1", "443", ["pom.xml", "build.gradle"]), ("github.com", "443", []), ("deb.example.com", "80", [])]
    assert asked[0]["network"] is True  # a private address is the user's own network
    [gap] = gaps
    assert gap["kind"] == "approval_required" and gap["hosts"] == ["10.1.1.1", "github.com", "deb.example.com"]
    assert gap["detail"].startswith("the step did not start: it needs hosts the user has not approved: ")
    assert "10.1.1.1:443 (declared in pom.xml, build.gradle)" in gap["detail"]
    assert [r["host"] for r in egress.pending(PROJECT)] == ["10.1.1.1", "github.com", "deb.example.com"]
    assert egress.preflight(PROJECT, ("pypi.org", "ok.example.com", "blocked.example.com")) == ([], [])  # none stops it
    egress.respond("github.com", PROJECT, "once")
    assert [r["host"] for r in egress.preflight(PROJECT, ("github.com", "10.1.1.1"))[0]] == ["10.1.1.1"]
    assert egress.preflight("/work/other", ("github.com",))[0][0]["declared_in"] == []  # declared for another project


def test_only_the_app_s_processes_answer_and_there_preflight_waits_for_the_person(monkeypatch):
    """`T1.F.3`: as a PC's firewall, where a person answers (`DAODAN_ANSWERS=app`, set by the app for the analyses it
    starts) a run does not start without its tool's hosts and does not stop either: it waits, with no time limit,
    until the user has answered, and then starts; the requests it waits on are `held`. Elsewhere it stops at once."""
    import threading
    monkeypatch.setattr(egress, "resolve", lambda rows, *_: [{**row, "address": None, "network": False} for row in rows])
    monkeypatch.setattr(egress, "POLL", 0.05)
    monkeypatch.delenv(egress.ANSWERS, raising=False)
    assert not egress.answerable()
    assert egress.preflight(PROJECT, ("github.com",))[1][0]["kind"] == "approval_required"  # MCP, the command line
    egress.begin(PROJECT)
    monkeypatch.setenv(egress.ANSWERS, "app")
    assert egress.answerable()
    seen = []

    def person():  # the app's page, once the request is there
        while not egress.pending(PROJECT):
            threading.Event().wait(0.02)
        seen.append([(row["host"], row.get("held")) for row in egress.pending(PROJECT)])
        egress.reply(PROJECT, ["github.com"], "once")
    answering = threading.Thread(target=person)
    answering.start()
    assert egress.preflight(PROJECT, ("github.com",)) == ([], [])  # it waited, then nothing stops it
    answering.join(10)
    assert seen == [[("github.com", True)]] and egress.pending(PROJECT) == []


def test_wait_ends_with_the_answers_and_with_its_stop():
    import threading
    stop = threading.Event()
    stop.set()
    egress.wait(PROJECT, ["github.com"], stop)  # it returns: stopped
    egress.wait(PROJECT, ["pypi.org"])  # canonical: nothing to wait for
    egress.respond("github.com", PROJECT, "no")
    egress.wait(PROJECT, ["github.com"])  # answered


def test_the_held_and_the_gone_lines_of_a_proxy_log_are_read_as_its_refusals():
    log = ('@@daodan-asked {"host": "Git.Example.com", "port": "443"}\nnoise\n'
           '@@daodan-asked {"host": "git.example.com", "port": "443"}\n'
           '@@daodan-gone {"host": "git.example.com", "port": "443"}\n'
           '@@daodan-refused {"host": "other.example.com", "port": "443"}\n')
    assert egress.refused(log, egress.ASKED) == [{"host": "git.example.com", "port": "443"}]
    assert egress.refused(log, egress.GONE) == [{"host": "git.example.com", "port": "443"}]
    assert egress.refused(log) == [{"host": "other.example.com", "port": "443"}]


def test_an_approval_gap_says_whether_the_step_failed_did_not_start_or_ran():
    row = [{"host": "a.example.com", "port": "443", "declared_in": []}]
    assert egress.approval_gap(row)[0]["detail"].startswith("the step failed and asked for hosts")
    assert egress.approval_gap(row, "before")[0]["detail"].startswith("the step did not start: it needs hosts")
    assert egress.approval_gap(row, "ran")[0]["detail"].startswith("the step ran without hosts the user")


def test_an_apt_archive_is_approved_as_its_host_is():
    state, session = egress.answer(EMPTY, egress.new_session(), "deb.example.com", PROJECT, "always")
    assert egress.decide("http://deb.example.com", PROJECT, state, session) == "allow"
    assert egress.decide("http://other.example.com", PROJECT, state, session) == "ask"
    assert egress.decide("http://archive.ubuntu.com", PROJECT, state, session) == "allow"  # a canonical archive
    state, session = egress.answer(state, session, "deb.example.com", PROJECT, "block")
    assert egress.decide("http://deb.example.com", PROJECT, state, session) == "deny"


def test_resolve_reaches_no_network_for_literals_and_localhost():
    out = egress.resolve([{"host": "127.0.0.1", "port": "80"}, {"host": "localhost", "port": "80"}])
    assert out[0]["network"] is True and out[1]["network"] is True


CHILD = """
import sys
sys.path.insert(0, {scripts!r})
import egress
{body}
"""


def _process(body: str, shared) -> str:
    """A process of its own over the same shared folder: its stdout."""
    import os
    import subprocess
    done = subprocess.run([sys.executable, "-c", CHILD.format(scripts=str(SCRIPTS), body=body)], capture_output=True,
                          text=True, env={**os.environ, "DAODAN_SHARED_DIR": str(shared)}, timeout=60)
    assert done.returncode == 0, done.stderr
    return done.stdout


def test_a_request_one_process_makes_another_sees_and_answers_and_the_first_sees_the_answer(shared):
    refused = [{"host": "93.184.216.34", "port": "443"}, {"host": "10.0.0.5", "port": "8080"}]
    _process(f"egress.collect({PROJECT!r}, {refused!r}, {{'10.0.0.5': ['pom.xml']}})", shared)
    seen = json.loads(_process(f"import json; print(json.dumps([r['host'] for r in egress.pending({PROJECT!r})]))",
                               shared))
    assert seen == ["93.184.216.34", "10.0.0.5"]
    assert [r["host"] for r in egress.pending(PROJECT)] == seen  # this process reads what a child wrote
    _process(f"egress.respond('10.0.0.5', {PROJECT!r}, 'once'); egress.respond('93.184.216.34', {PROJECT!r}, 'no')",
             shared)
    assert egress.pending(PROJECT) == []
    answered = egress.session(PROJECT)
    assert answered == {"allow": ["10.0.0.5"], "deny": ["93.184.216.34"]}
    assert egress.decide("10.0.0.5", PROJECT, egress.load(PROJECT), answered) == "allow"
    again = _process(f"import json; print(json.dumps(egress.session({PROJECT!r})))", shared)
    assert json.loads(again) == answered  # a child of the pass finds it


def test_always_and_block_answered_elsewhere_reach_this_process_for_their_project_only(shared, checkout):
    _process(f"egress.respond('git.example.com', {checkout!r}, 'always'); "
             f"egress.respond('bad.example.com', {checkout!r}, 'block')", shared)
    state = egress.load(checkout)
    assert egress.decide("git.example.com", checkout, state, egress.session(checkout)) == "allow"
    assert egress.decide("bad.example.com", checkout, state, egress.session(checkout)) == "deny"
    assert egress.decide("bad.example.com", PROJECT, egress.load(PROJECT), egress.session(PROJECT)) == "ask"


def test_a_pass_empties_its_requests_when_it_starts_and_its_answers_when_it_ends(shared):
    egress.collect(PROJECT, [{"host": "10.0.0.1", "port": "443"}])
    egress.collect("/work/other", [{"host": "10.0.0.2", "port": "443"}])
    egress.respond("10.0.0.1", PROJECT, "once")
    egress.collect(PROJECT, [{"host": "10.0.0.3", "port": "443"}])
    egress.begin(PROJECT)
    assert egress.pending(PROJECT) == [] and [r["host"] for r in egress.pending("/work/other")] == ["10.0.0.2"]
    assert egress.session(PROJECT)["allow"] == ["10.0.0.1"]  # the answer given between two passes serves the next
    egress.end(PROJECT)
    assert egress.session(PROJECT) == egress.new_session()
    assert json.loads(_process(f"import json; print(json.dumps(egress.session({PROJECT!r})))", shared)) == \
        egress.new_session()


def test_an_analysis_ended_in_another_process_leaves_no_answer_here_and_the_next_reply_does_not_bring_it_back(shared):
    egress.respond("10.0.0.1", PROJECT, "once")  # the app's process answers for one analysis
    assert egress.session(PROJECT)["allow"] == ["10.0.0.1"]
    _process(f"egress.end({PROJECT!r})", shared)  # the analysis ends in its own process
    assert egress.session(PROJECT) == egress.new_session()
    egress.respond("10.0.0.2", PROJECT, "no")  # the app answers for the next analysis
    assert json.loads((shared / egress.SESSION_FILE).read_text(encoding="utf-8"))[PROJECT] == {
        "allow": [], "deny": ["10.0.0.2"]}


@pytest.mark.parametrize("fails", [False, True])
def test_the_whole_analysis_begins_and_ends_the_egress_of_its_project(shared, monkeypatch, fails):
    """The boundary is the analysis, all its steps (`pipeline.run`), not one of them: the pre-map's requests made in
    it are not emptied by a later step, "once" serves the dynamic step too, and the answers end with it, even when it
    fails."""
    import pipeline
    egress.collect(PROJECT, [{"host": "10.0.0.1", "port": "443"}])  # a request of the analysis before
    egress.respond("10.0.0.2", PROJECT, "once")  # answered between two analyses
    seen = {}

    def steps(manifest, listeners, **options):
        seen.update(before=egress.pending(PROJECT), named=egress.name("/work/app/sub"))
        egress.collect(egress.name("/work/app/sub"), [{"host": "10.0.0.3", "port": "443"}])  # the pre-map asks
        seen.update(premap=[row["host"] for row in egress.pending(PROJECT)],
                    allow=egress.session(PROJECT)["allow"])  # what the dynamic step finds, after the analyze one
        if fails:
            raise RuntimeError("a step that nobody foresaw")
        return {"ran": True}

    monkeypatch.setattr(egress, "project_of", lambda manifest: PROJECT)
    monkeypatch.setattr(pipeline, "_run", steps)
    if fails:
        with pytest.raises(RuntimeError):
            pipeline.run(Path("m.sqlite"))
    else:
        assert pipeline.run(Path("m.sqlite")) == {"ran": True}
    assert seen == {"before": [], "named": PROJECT, "premap": ["10.0.0.3"], "allow": ["10.0.0.2"]}
    assert egress.session(PROJECT) == egress.new_session()  # forgotten when the analysis ends, however it ends
    assert [row["host"] for row in egress.pending(PROJECT)] == ["10.0.0.3"]  # the pre-map's request stays visible
    assert egress.name("/work/app/sub") == "/work/app/sub"  # outside the analysis, a run names its own folder


def test_a_missing_or_corrupt_shared_file_is_an_empty_one(shared):
    shared.mkdir(parents=True)
    for name in (egress.PENDING_FILE, egress.SESSION_FILE):
        (shared / name).write_text("{not json", encoding="utf-8")
    assert egress.pending(PROJECT) == [] and egress.session(PROJECT) == egress.new_session()
    egress.respond("x.example.com", PROJECT, "once")  # and it is written whole again
    assert json.loads((shared / egress.SESSION_FILE).read_text(encoding="utf-8")) == {
        PROJECT: {"allow": ["x.example.com"], "deny": []}}
    (shared / egress.PENDING_FILE).write_text(json.dumps({PROJECT: "no"}), encoding="utf-8")
    assert egress.pending(PROJECT) == []
