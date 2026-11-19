"""The standalone app: a public repository's checkout, the engines' contract and the launcher's routes.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_app.py

No network, no model and no login: the repository is a local one Git serves from a folder, the endpoint is a
server of this test, and a command-line engine is a script that prints the events its real one prints.
"""
from __future__ import annotations

import http.client
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

import keyring
import keyring.backend
import keyring.backends.fail
import keyring.errors
import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import app as launcher  # noqa: E402
import app_view  # noqa: E402
import engines  # noqa: E402
import repository  # noqa: E402
import visual  # noqa: E402

CLEAN = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
         "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(folder: Path, *arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=folder, env={**os.environ, **CLEAN}, check=True,
                          capture_output=True, text=True).stdout.strip()


class Deposit(keyring.backend.KeyringBackend):
    """The system's deposit of secrets, held by the test: no test writes in the person's own."""
    priority = 1

    def __init__(self):
        super().__init__()
        self.held = {}

    def get_password(self, service, username):
        return self.held.get((service, username))

    def set_password(self, service, username, password):
        if (service, username) in self.held:  # as the Windows one does: a replaced secret stays under a second name
            self.held[(service, f"{username}@{service}")] = self.held[(service, username)]
        self.held[(service, username)] = password

    def delete_password(self, service, username):
        found = [name for name in ((service, username), (service, f"{username}@{service}")) if name in self.held]
        if not found:
            raise keyring.errors.PasswordDeleteError(service)
        for name in found:
            del self.held[name]


@pytest.fixture(autouse=True)
def deposit():
    previous, held = keyring.get_keyring(), Deposit()
    keyring.set_keyring(held)
    yield held
    keyring.set_keyring(previous)


@pytest.fixture
def origin(tmp_path):
    """A repository whose `.gitattributes` asks for a filter, with a second branch."""
    folder = tmp_path / "origin"
    folder.mkdir()
    git(folder, "init", "-q", "-b", "main")
    (folder / ".gitattributes").write_text("* filter=mark\n", encoding="utf-8")
    (folder / "a.py").write_text("x = 1\n", encoding="utf-8")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "one")
    git(folder, "branch", "stable")
    return folder


@pytest.mark.parametrize("address, owner, name", [
    ("https://github.com/pallets/itsdangerous", "pallets", "itsdangerous"),
    ("github.com/pallets/itsdangerous.git/", "pallets", "itsdangerous"),
    ("  https://github.com/a-b/c.d_e  ", "a-b", "c.d_e"),
])
def test_an_address_of_a_github_repository_is_read(address, owner, name):
    found = repository.parse(address)
    assert (found["owner"], found["name"], found["url"]) == (owner, name, f"https://github.com/{owner}/{name}")


@pytest.mark.parametrize("address", ["https://gitlab.com/a/b", "https://github.com/a", "file:///etc", "../x",
                                     "https://github.com/a/b/c", "https://github.com/-a/b", "https://github.com/a/..",
                                     "https://user:secret@github.com/a/b", "git@github.com:a/b.git", 7])
def test_any_other_address_is_refused(address):
    with pytest.raises(ValueError):
        repository.parse(address)


def test_the_branches_are_listed_with_the_one_to_offer_first(origin, tmp_path):
    listed = repository._listed(origin.as_uri(), tmp_path / "work", transports=("file",))
    assert listed["state"] == "accessible" and listed["default"] == "main"
    assert [branch["name"] for branch in listed["branches"]] == ["main", "stable"]
    assert repository._listed((tmp_path / "none").as_uri(), tmp_path / "work", ("file",))["state"] == "not_accessible"


def test_a_checkout_runs_nothing_the_user_s_configuration_or_the_repository_names(origin, tmp_path, monkeypatch):
    """The user's Git configuration defines the filter the repository's `.gitattributes` asks for and a hook folder:
    either, if it ran, would leave a mark. The checkout reads neither."""
    home, mark = tmp_path / "home", tmp_path / "MARK"
    (home / "hooks").mkdir(parents=True)
    hook = home / "hooks" / "post-checkout"
    hook.write_text(f"#!/bin/sh\ntouch '{mark.as_posix()}'\n", encoding="utf-8")
    hook.chmod(0o755)
    (home / ".gitconfig").write_text(
        f"[filter \"mark\"]\n\tsmudge = sh -c \"touch '{mark.as_posix()}'; cat\"\n\trequired = true\n"
        f"[core]\n\thooksPath = {(home / 'hooks').as_posix()}\n", encoding="utf-8")
    for name in ("HOME", "USERPROFILE", "XDG_CONFIG_HOME"):
        monkeypatch.setenv(name, str(home))
    monkeypatch.delenv("GIT_CONFIG_GLOBAL", raising=False)
    work = tmp_path / "work"
    path, commit = repository._clone(origin.as_uri(), "main", work / "r", work, transports=("file",))
    assert not mark.exists()
    assert path.parent.name == commit == git(origin, "rev-parse", "HEAD") and path.name == repository.CHECKOUT
    assert (path / "a.py").read_text() == "x = 1\n"
    assert repository._clone(origin.as_uri(), "main", work / "r", work, transports=("file",))[0] == path  # reused
    assert [item.name for item in (work / "r").iterdir()] == [commit]
    with pytest.raises(ValueError):
        repository._clone(origin.as_uri(), "--upload-pack=x", work / "r", work, transports=("file",))


class Endpoint(BaseHTTPRequestHandler):
    """Chat Completions, streamed: a call of the first tool offered (or `call`, a name and its arguments), then the
    tool's answer as the text."""
    seen: list = []
    call = None

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Endpoint.seen.append((self.path, self.headers.get("Authorization"), body))
        last = body["messages"][-1]
        if last["role"] == "tool":
            chunks = [{"delta": {"content": last["content"][:5]}}, {"delta": {"content": last["content"][5:]}}]
        else:
            name, arguments = Endpoint.call or (body["tools"][0]["function"]["name"], '{"value": "w"}')
            chunks = [{"delta": {"tool_calls": [{"index": 0, "id": "c1", "function": {"name": name, "arguments": arguments[:5]}}]}},
                      {"delta": {"tool_calls": [{"index": 0, "function": {"arguments": arguments[5:]}}]}}]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for chunk in chunks:
            self.wfile.write(f"data: {json.dumps({'choices': [chunk]})}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")

    def log_message(self, *args):
        return


@pytest.fixture
def endpoint():
    Endpoint.seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), Endpoint)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    server.shutdown()
    server.server_close()


def test_an_endpoint_is_asked_with_tools_and_its_calls_are_run_and_answered(endpoint):
    asked, said = [], []
    tool = {"name": "echo", "description": "d", "parameters": {"type": "object"},
            "call": lambda arguments: asked.append(arguments) or {"value": arguments["value"]}}
    engine = engines.configured({"engine": "openai", "base_url": endpoint, "model": "m", "api_key": "sk-secret"})
    outcome = engine.run({"prompt": "p", "system": "s", "tools": [tool]}, lambda kind, **data: said.append(kind))
    assert outcome == {"state": "done", "text": '{"value": "w"}', "session": None, "cause": None}
    assert asked == [{"value": "w"}] and said == ["tool", "text", "text"]
    path, key, first = Endpoint.seen[0]
    assert (path, key) == ("/v1/chat/completions", "Bearer sk-secret") and first["stream"] is True
    assert [message["role"] for message in Endpoint.seen[1][2]["messages"]] == ["system", "user", "assistant", "tool"]
    assert "sk-secret" not in json.dumps(engines.described({"engine": "openai", "api_key": "sk-secret"}))


def test_an_endpoint_that_is_not_reached_fails_with_its_cause():
    outcome = engines.OpenAICompatible("http://127.0.0.1:9/v1", "m", seconds=3).run({"prompt": "p"})
    assert outcome["state"] == "failed" and "not reached" in outcome["cause"]
    with pytest.raises(ValueError):
        engines.configured({"engine": None})
    with pytest.raises(ValueError):
        engines.configured({"engine": "openai", "base_url": "ftp://x", "model": "m"})


def test_a_saved_engine_comes_back_at_the_next_start_and_its_key_is_only_in_the_deposit(tmp_path, deposit):
    work, saved = tmp_path / "work", {"engine": "openai", "base_url": "https://e.example/v1", "model": "m"}
    described = launcher.App(work, environment={}).configure({**saved, "api_key": "sk-secret"})
    assert described["api_key"] == "set" and described["unkept"] is None
    again = launcher.App(work, environment={"OPENAI_API_KEY": "sk-general"}).engine  # the general key is the last resort
    assert {name: again[name] for name in (*saved, "api_key")} == {**saved, "api_key": "sk-secret"}
    assert engines.described(again)["unkept"] is None and list(deposit.held.values()) == ["sk-secret"]
    assert not [path for path in work.rglob("*") if path.is_file() and b"sk-secret" in path.read_bytes()]


def test_what_daodan_s_variables_of_the_environment_name_wins_over_what_was_saved(tmp_path):
    work = tmp_path / "work"
    launcher.App(work, environment={}).configure(
        {"engine": "openai", "base_url": "https://e.example/v1", "model": "m", "api_key": "sk-secret"})
    again = launcher.App(work, environment={"DAODAN_OPENAI_MODEL": "other", "DAODAN_OPENAI_API_KEY": "sk-asked"}).engine
    assert [again[name] for name in ("engine", "base_url", "model", "api_key")] == [
        "openai", "https://e.example/v1", "other", "sk-asked"]


def test_a_key_of_the_environment_is_not_copied_in_the_deposit(tmp_path, deposit):
    app = launcher.App(tmp_path / "work", environment={"OPENAI_API_KEY": "sk-environment"})
    assert app.configure({"engine": "openai", "model": "m"})["api_key"] == "set"
    assert deposit.held == {}


def test_a_replaced_key_does_not_stay_in_the_deposit_and_an_empty_one_forgets_it(tmp_path, deposit):
    work = tmp_path / "work"
    app = launcher.App(work, environment={"OPENAI_API_KEY": "sk-general"})
    app.configure({"engine": "openai", "model": "m", "api_key": "sk-old"})
    app.configure({"api_key": "sk-new"})
    assert list(deposit.held.values()) == ["sk-new"]
    described = app.configure({"api_key": ""})
    assert deposit.held == {} and described["unkept"] is None
    assert app.engine["api_key"] == "sk-general"  # what a start would find now
    assert launcher.App(work, environment={}).engine["api_key"] == ""


def test_without_a_deposit_the_key_stays_in_memory_and_the_setting_says_why(tmp_path):
    keyring.set_keyring(keyring.backends.fail.Keyring())
    work = tmp_path / "work"
    app = launcher.App(work, environment={})
    described = app.configure({"engine": "openai", "model": "m", "api_key": "sk-secret"})
    assert described["api_key"] == "set" and "did not take the key" in described["unkept"]
    assert app.engine["api_key"] == "sk-secret"
    assert "did not take the key" in app.configure({"model": "n"})["unkept"]  # still so: the key was not given again
    again = launcher.App(work, environment={}).engine
    assert (again["engine"], again["model"], again["api_key"]) == ("openai", "n", "")
    assert "deposit of secrets is not read" in engines.described(again)["unkept"]
    assert not [path for path in work.rglob("*") if path.is_file() and b"sk-secret" in path.read_bytes()]


def test_a_deposit_that_fails_in_its_own_way_is_a_cause_and_never_a_failure_of_the_app(tmp_path):
    class Broken(Deposit):
        def get_password(self, service, username):
            raise RuntimeError("the deposit is locked")

        set_password = delete_password = get_password

    keyring.set_keyring(Broken())
    app = launcher.App(tmp_path / "work", environment={})
    assert "RuntimeError" in engines.described(app.engine)["unkept"]
    described = app.configure({"engine": "openai", "model": "m", "api_key": "sk-secret"})
    assert "RuntimeError" in described["unkept"] and app.engine["api_key"] == "sk-secret"
    keyring.set_keyring(Deposit())
    assert app.configure({"api_key": "sk-secret"})["unkept"] is None  # given again, and taken


def _another_schema(path: Path) -> None:
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE setting (other TEXT)")
    db.close()


@pytest.mark.parametrize("spoil", [lambda path: path.write_bytes(b"not a database, and longer than its header" * 4),
                                   lambda path: path.write_bytes(b""), _another_schema])
def test_a_saved_engine_that_cannot_be_read_does_not_stop_the_start_and_the_next_save_replaces_it(tmp_path, spoil):
    work = tmp_path / "work"
    work.mkdir()
    spoil(work / engines.STORE)
    app = launcher.App(work, environment={})
    assert app.engine["engine"] is None and "saved engine is not read" in engines.described(app.engine)["unkept"]
    assert app.configure({"engine": "claude"})["unkept"] is None
    again = launcher.App(work, environment={}).engine
    assert again["engine"] == "claude" and engines.described(again)["unkept"] is None


def test_a_setting_that_cannot_be_written_is_refused_and_changes_nothing(tmp_path, deposit):
    work = tmp_path / "work"
    app = launcher.App(work, environment={})
    (work / f"{engines.STORE}.new").mkdir()  # where a setting is written before it replaces the one kept
    with pytest.raises(OSError):
        app.configure({"engine": "openai", "model": "m", "api_key": "sk-secret"})
    assert app.engine["engine"] is None and app.engine["api_key"] == "" and deposit.held == {}


def test_a_probe_tries_the_setting_it_is_given_and_keeps_nothing(tmp_path, endpoint, deposit):
    work = tmp_path / "work"
    app = launcher.App(work, environment={})
    found = app.probe({"engine": "openai", "base_url": endpoint, "model": "m", "api_key": "sk-secret"})
    assert found["engine"] == "openai" and Endpoint.seen[0][1] == "Bearer sk-secret"
    assert app.engine["engine"] is None and deposit.held == {} and not (work / engines.STORE).exists()


def test_a_command_line_engine_starts_without_the_tools_that_run_commands(tmp_path):
    mcp = {"command": "uv", "args": ["run", "x.py"]}
    claude = engines.ClaudeCode().arguments({"mcp": mcp}, tmp_path)
    assert claude[claude.index("--tools") + 1] == "" and "--strict-mcp-config" in claude
    assert claude[claude.index("--allowedTools") + 1] == f"mcp__{engines.SERVER}"
    config = json.loads(Path(claude[claude.index("--mcp-config") + 1]).read_text(encoding="utf-8"))
    assert config == {"mcpServers": {engines.SERVER: mcp}}
    codex = engines.Codex().arguments({"mcp": mcp}, tmp_path)
    assert [codex[index + 1] for index, word in enumerate(codex) if word == "--disable"] == ["shell_tool", "unified_exec"]
    assert codex[codex.index("--sandbox") + 1] == "read-only" and codex[-1] == "-"
    assert f'mcp_servers.{engines.SERVER}.args=["run", "x.py"]' in codex


class Scripted(engines.ClaudeCode):
    """Claude Code's reader over a script that prints given events, and waits when told to."""

    def __init__(self, script: Path):
        super().__init__(command=sys.executable, seconds=30)
        self.script = script

    def arguments(self, task: dict, folder: Path) -> list[str]:
        return ["-B", str(self.script)]


def scripted(tmp_path, events: list[dict], wait: bool = False) -> Scripted:
    script = tmp_path / "engine.py"
    script.write_text("import sys, time\nsys.stdin.read()\n"
                      + "".join(f"print({json.dumps(json.dumps(event))}, flush=True)\n" for event in events)
                      + ("time.sleep(60)\n" if wait else ""), encoding="utf-8")
    return Scripted(script)


def test_a_command_line_engine_s_events_become_its_outcome(tmp_path):
    connected = {"type": "system", "subtype": "init", "session_id": "s1",
                 "mcp_servers": [{"name": engines.SERVER, "status": "connected"}]}
    answered = {"type": "result", "result": "the answer", "is_error": False, "session_id": "s1"}
    said = []
    outcome = scripted(tmp_path, [connected, {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "t", "input": {}}, {"type": "text", "text": "the answer"}]}}, answered]).run(
        {"prompt": "p", "cwd": str(tmp_path)}, lambda kind, **data: said.append(kind))
    assert outcome == {"state": "done", "text": "the answer", "session": "s1", "cause": None}
    assert said == ["tool", "text"]
    pending = {**connected, "mcp_servers": [{"name": engines.SERVER, "status": "pending"}]}
    outcome = scripted(tmp_path, [pending, answered]).run({"prompt": "p", "cwd": str(tmp_path)})
    assert outcome["state"] == "failed" and "did not connect" in outcome["cause"]  # never an answer without its tools


def test_a_cancelled_run_ends_its_process(tmp_path):
    started = time.monotonic()
    outcome = scripted(tmp_path, [{"type": "system", "subtype": "init"}, {"type": "assistant", "message": {}}],
                       wait=True).run({"prompt": "p", "cwd": str(tmp_path)}, cancelled=lambda: True)
    assert outcome["state"] == "cancelled" and time.monotonic() - started < 20


def request(port: int, path: str, body=None, token: str | None = "t"):
    headers = {"X-Daodan-Token": token} if token else {}
    if body is not None:
        headers.update({"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{port}"})
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=60)
    try:
        connection.request("GET" if body is None else "POST", path, None if body is None else json.dumps(body), headers)
        answer = connection.getresponse()
        content = answer.read()
        return answer.status, json.loads(content) if path.startswith("/api/") else content
    finally:
        connection.close()


def stream(port: int, query: str) -> list[tuple[str, dict]]:
    """The frames of one `/api/stream`, read to its end."""
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=60)
    try:
        connection.request("GET", "/api/stream?token=t&" + query)
        answer = connection.getresponse()
        assert answer.status == 200 and answer.getheader("Content-Type").startswith("text/event-stream")
        blocks = [block.split("\n") for block in answer.read().decode("utf-8").split("\n\n") if block]
    finally:
        connection.close()
    return [(name.removeprefix("event: "), json.loads(data.removeprefix("data: "))) for name, data in blocks]


def test_a_further_folder_is_served_under_its_name(tmp_path):
    (tmp_path / "viewer").mkdir()
    (tmp_path / "viewer" / "index.html").write_text("viewer", encoding="utf-8")
    (tmp_path / "page").mkdir()
    (tmp_path / "page" / "index.html").write_text("page", encoding="utf-8")
    server = visual.make_server(None, tmp_path / "viewer", mounts={"app": tmp_path / "page"})
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        port = server.server_address[1]
        assert [request(port, path)[1] for path in ("/", "/app/", "/app/index.html")] == [b"viewer", b"page", b"page"]
        assert request(port, "/app")[0] == 404 and request(port, "/page/index.html")[0] == 404
    finally:
        server.shutdown()
        server.server_close()


def test_the_pre_map_lists_the_units_with_their_declared_libraries_and_the_unit_that_holds_each():
    stack = {"technologies": [{"id": "pytest", "name": "pytest", "category": "framework",
                               "signs": [{"path": "other/pyproject.toml", "line": 3}, {"path": "pkg/pyproject.toml", "line": 9}]}],
             "modules": [{"id": "root", "name": "root", "kind": "python-package", "paths": ["."], "technologies": [],
                          "toolchains": [], "libraries": []},
                         {"id": "pkg", "name": "pkg", "kind": "python-package", "paths": ["pkg"], "technologies": ["pytest"],
                          "toolchains": [{"declared_in": "pkg/pyproject.toml", "tool": "python", "version": ">=3.12"}],
                          "libraries": [{"ecosystem": "pypi", "name": "pytest", "path": "pkg/pyproject.toml", "line": 9}]}]}
    found = app_view.premap(stack, {"modules": [{"id": "pkg", "status": "confirmed", "description": "a package"}]},
                            {"pkg/a.py": {"language": "python"}, "README.md": {"language": None}})
    assert found["files"] == ["README.md", "pkg/a.py"] and found["languages"] == [{"name": "Python", "files": 1}]
    assert [(unit["id"], unit["parent"], unit["manifest"], unit["status"]) for unit in found["units"]] == [
        ("root", None, None, None), ("pkg", "root", "pkg/pyproject.toml", "confirmed")]
    assert found["units"][1]["dependencies"] == [{"name": "pytest", "scope": "pypi", "state": "declared",
                                                  "source": "pkg/pyproject.toml:9"}]
    assert [(item["name"], item["source"], item["state"]) for item in found["technologies"]] == [
        ("pytest", "pkg/pyproject.toml:9", "recognized"), ("python", "pkg/pyproject.toml", "declared")]
    with pytest.raises(ValueError, match="stale"):
        app_view.premap({"state": "needs_refresh", "reason": "stale"}, {}, {})


def test_a_declared_library_passes_its_version_on_and_one_without_has_none():
    stack = {"technologies": [], "modules": [{"id": "pkg", "name": "pkg", "paths": ["pkg"], "technologies": [],
                                              "toolchains": [], "libraries": [
        {"ecosystem": "pypi", "name": "pytest", "path": "pkg/pyproject.toml", "line": 9, "version": ">=8,<9"},
        {"ecosystem": "pypi", "name": "rich", "path": "pkg/pyproject.toml", "line": 10}]}]}
    found = app_view.premap(stack, {}, {})
    assert [dep.get("version", "absent") for dep in found["units"][0]["dependencies"]] == [">=8,<9", "absent"]


def test_the_graph_groups_files_by_their_smallest_module_or_else_by_their_directory():
    def entity(ref, kind, **fields):
        return {"ref": ref, "type": kind, "name": ref.split(":", 1)[1], **fields}

    def relation(kind, source, target, **fields):
        return {"kind": kind, "source": source, "target": target, "status": "confirmed", "evidence": [], **fields}

    envelope = {"entities": [entity("build:app", "build", description="the app"), entity("build:lib", "build"),
                             *[entity(f"file:{path}", "file", path=path)
                               for path in ("app/main.py", "app/lib/util.py", "docs/a.md")],
                             entity("symbol:app/main.py::run", "symbol", path="app/main.py")],
                "relations": [relation("imports", "file:app/main.py", "file:app/lib/util.py"),
                              relation("calls", "build:app", "build:lib", counts={"calls": 3},
                                       evidence=[{"path": "app/main.py", "line": 4}]),
                              relation("defines", "file:app/main.py", "symbol:app/main.py::run")],
                "memberships": [{"member": "file:app/main.py", "group": "build:app", "view": "physical"},
                                {"member": "file:app/lib/util.py", "group": "build:app", "view": "physical"},
                                {"member": "file:app/lib/util.py", "group": "build:lib", "view": "physical"}],
                "gaps": [], "meta": {}, "technologies": []}
    found = app_view.graph(envelope)
    assert (found["grouping"], found["files"], found["symbols"]) == ("modules", 3, 1)
    assert {node["id"]: node["files"] for node in found["nodes"]} == {"build:app": ["app/main.py"],
                                                                      "build:lib": ["app/lib/util.py"]}
    assert [(edge["id"], edge["counts"]) for edge in found["edges"]] == [("build:app->build:lib", {"imports": 1, "calls": 3})]
    assert found["unassigned"] == {"count": 1, "areas": [("docs", 1)]}
    alone = app_view.graph({**envelope, "entities": [item for item in envelope["entities"] if item["ref"] != "build:lib"]})
    assert alone["grouping"] == "directories" and alone["unassigned"]["count"] == 0
    assert {node["id"]: node["files"] for node in alone["nodes"]} == {
        "directory:app": ["app/main.py"], "directory:app/lib": ["app/lib/util.py"], "directory:docs": ["docs/a.md"]}
    assert [(edge["id"], edge["counts"]) for edge in alone["edges"]] == [("directory:app->directory:app/lib", {"imports": 1})]
    # the tree no build names is not a module: with it, the files still show by their directories
    tree = app_view.graph({**envelope, "entities": [*(item for item in envelope["entities"] if item["ref"] != "build:lib"),
                                                    entity("virtual:tree", "virtual")],
                           "memberships": [*envelope["memberships"], *(
                               {"member": f"file:{path}", "group": "virtual:tree", "view": "physical"}
                               for path in ("app/main.py", "app/lib/util.py", "docs/a.md"))]})
    assert (tree["grouping"], tree["nodes"], tree["edges"]) == ("directories", alone["nodes"], alone["edges"])


@pytest.fixture(scope="module")
def levels(tmp_path_factory):
    """A run with three build units, a service the stack recognises, a framework two of them declare, a framework
    only mentioned, a library the registry knows, a tool and a library it does not know, a deduced link between two units and a module with a
    directory whose files call each other, one holding a class with two methods."""
    import mcp_service
    pets = HERE.parent / "benchmarks/connection-points/fixtures/pets"
    project = tmp_path_factory.mktemp("levels") / "project"
    shutil.copytree(pets / "app", project)
    files = {"web/package.json": json.dumps({"name": "web", "version": "1.0.0", "dependencies": {
                 "stripe": "^14.0.0", "express": "^4.19.0", "@acme/widgets": "^1.0.0", "zod": "^3.23.0",
                 "jest": "^29.7.0"}}, indent=2),  # express: line 6, zod (a library) 8, jest (a tool) 9
             "web/lib/pay.js": 'const stripe = require("stripe")(process.env.STRIPE_SECRET_KEY);\nmodule.exports = stripe;\n',
             "web/lib/trace.js": "module.exports = process.env.OTEL_SERVICE_NAME;\n",
             "admin/package.json": json.dumps({"name": "admin", "version": "1.0.0", "dependencies": {
                 "express": "^4.19.0"}}, indent=2),  # express: line 5
             "admin/index.js": "module.exports = 1;\n",
             "admin/next.config.js": "module.exports = {};\n",  # Next.js by its file alone: no `next` package
             "server/store/outbox.py": "from .db import save\n\n\nclass Outbox:\n    def push(self, item):\n"
                                       "        return save(item)\n\n    def size(self):\n        return 0\n\n\n"
                                       "def drain():\n    return []\n",
             "server/pyproject.toml": '[project]\nname = "server"\nversion = "0.1.0"\n',
             "server/__init__.py": "",
             "server/jobs.py": "from .store.db import load\n\n\ndef nightly():\n    return load()\n",
             "server/store/__init__.py": "",
             "server/store/db.py": "def save(item):\n    return [item]\n\n\ndef load():\n    return save(1)\n",
             "server/store/cache.py": "from .db import save\n\n\ndef remember(item):\n    return save(item)\n"}
    for rel, text in files.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    git(project, "init", "-q")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "levels")
    service = mcp_service.MapService(project)
    service.create_run(".", "levels", engine=False)
    service.flows("levels", rules=json.loads((pets / "rules.json").read_text(encoding="utf-8"))["rules"])
    return service


def leveled(service, folder: Path):
    """An app on the run of `levels`, with nothing kept yet."""
    app = launcher.App(folder / "work", environment={})
    app.service, app.context = service, {"run_id": "levels", "path": str(service.project_root)}
    return app


def group_of(found: dict, path: str) -> str:
    return next(node["id"] for node in found["nodes"] if path in node["files"])


def test_the_first_level_is_the_graph_in_groups_and_reads_no_outline(levels, tmp_path, monkeypatch):
    run = levels.root / "runs" / "levels"
    whole = app_view.graph(visual.build_envelope(run))

    def refused(*args, **kwargs):
        raise AssertionError("the first level read the symbols of a file")
    monkeypatch.setattr(visual.source_reader, "outline_manifest", refused)
    monkeypatch.setattr(visual.semantic_store, "query_meta_code", refused)
    top = leveled(levels, tmp_path).graph({})
    shown = ("grouping", "edges", "files", "unassigned")
    assert {key: top[key] for key in shown} == {key: whole[key] for key in shown}
    # no node is in an open group; an external service is a node of the level infrastruttura, a group of codice
    assert [{**node, "group": None, "level": "infrastruttura" if node["location"] == "external" else "codice"}
            for node in whole["nodes"]] == top["nodes"]
    assert (top["levels"], top["grouping"], top["open"]) == (["codice", "infrastruttura"], "modules", [])
    web, server = group_of(top, "web/api.ts"), group_of(top, "server/app.py")
    edges = {(edge["source"], edge["target"], edge["status"]): edge for edge in top["edges"]}
    assert edges[(web, server, "uncertain")]["counts"] == {"calls": 1}  # the deduced link, uncertain apart
    assert "uses" in edges[(web, "external:stripe", "confirmed")]["counts"]


def opened(app, *groups: str) -> dict:
    return app.graph({"open": json.dumps(list(groups))})


def arrows(found: dict) -> dict:
    assert len({node["id"] for node in found["nodes"]}) == len(found["nodes"])  # a node reached twice is one node
    return {(edge["source"], edge["target"], edge["status"]): edge for edge in found["edges"]}


def test_a_group_opens_in_place_and_its_summary_arrows_become_the_arrows_of_what_it_holds(levels, tmp_path):
    app = leveled(levels, tmp_path)
    top = app.graph({})
    web, server = group_of(top, "web/api.ts"), group_of(top, "server/app.py")
    store = f"{server}#server/store"
    # A module open: its files and directory carry it as their group, every other first-level node is still there.
    one = opened(app, server)
    held = {node["id"]: node for node in one["nodes"] if node["group"] == server}
    assert [(group["id"], group["parent"]) for group in one["open"]] == [(server, None)]
    assert set(held) == {"file:server/pyproject.toml", "file:server/__init__.py", "file:server/app.py",
                         "file:server/jobs.py", store}
    assert held[store]["files"] == ["server/store/__init__.py", "server/store/cache.py", "server/store/db.py",
                                    "server/store/outbox.py"]
    assert {node["id"] for node in one["nodes"] if node["group"] is None} == {node["id"] for node in top["nodes"]} - {server}
    # the summary arrow from the other module becomes the arrow to the file that holds both its ends' sites,
    # with the same counts, status and evidence: the uncertain one stays apart and uncertain
    before, after = arrows(top), arrows(one)
    for status in ("confirmed", "uncertain"):
        assert {key: after[(web, "file:server/app.py", status)][key] for key in ("counts", "status", "evidence")} == \
            {key: before[(web, server, status)][key] for key in ("counts", "status", "evidence")}
    assert after[("file:server/jobs.py", store, "confirmed")]["counts"] == {"imports": 1, "calls": 1}
    # Two groups open: the arrows run between what they hold; a service used by two of them is one node.
    two = arrows(opened(app, web, server))
    assert two[("file:web/api.ts", "file:server/app.py", "confirmed")]["counts"] == {"calls": 2}
    assert two[("file:web/api.ts", "file:server/app.py", "uncertain")]["counts"] == {"calls": 1}
    assert two[("file:web/package.json", "external:stripe", "confirmed")]["counts"] == {"uses": 1}
    assert two[(f"{web}#web/lib", "external:stripe", "uncertain")]["counts"] == {"uses": 1}
    # An inner directory open inside the open module, whatever the order asked.
    inner = opened(app, store, server)
    assert [(group["id"], group["parent"]) for group in inner["open"]] == [(server, None), (store, server)]
    assert {node["id"] for node in inner["nodes"] if node["group"] == store} == {
        "file:server/store/__init__.py", "file:server/store/cache.py", "file:server/store/db.py",
        "file:server/store/outbox.py"}
    deep = arrows(inner)
    assert deep[("file:server/jobs.py", "file:server/store/db.py", "confirmed")]["counts"] == {"imports": 1, "calls": 1}
    assert deep[("file:server/store/cache.py", "file:server/store/db.py", "confirmed")]["counts"] == {"imports": 1, "calls": 1}
    # A file open inside the open directory inside the open module: its symbols, the calls among them, and the calls of
    # closed files lifted to what shows them now; its import has no symbol at its end and stays on the open file.
    db, cache = "file:server/store/db.py", "file:server/store/cache.py"
    save, load = "symbol:server/store/db.py::save", "symbol:server/store/db.py::load"
    three = opened(app, server, store, db)
    assert [(group["id"], group["parent"]) for group in three["open"]] == [(server, None), (store, server), (db, store)]
    assert {node["id"] for node in three["nodes"] if node["group"] == db} == {save, load}
    split = arrows(three)
    assert (split[(load, save, "confirmed")]["counts"], split[(load, save, "confirmed")]["evidence"]) == (
        {"calls": 1}, [{"kind": "calls", "path": "server/store/db.py", "line": 6}])
    assert split[(cache, save, "confirmed")]["evidence"] == [{"kind": "calls", "path": "server/store/cache.py", "line": 5}]
    assert split[("file:server/jobs.py", load, "confirmed")]["counts"] == {"calls": 1}
    assert split[(cache, db, "confirmed")]["counts"] == {"imports": 1}
    # a call out of an open file to a closed one goes to the closed file
    assert arrows(opened(app, server, store, cache))[("symbol:server/store/cache.py::remember", db, "confirmed")][
        "counts"] == {"calls": 1}
    # closing the file gives the summary arrow back, with the same evidence
    assert arrows(opened(app, server, store))[(cache, db, "confirmed")] == deep[(cache, db, "confirmed")]
    assert deep[(cache, db, "confirmed")]["counts"] == {"imports": 1, "calls": 1}
    # The gaps survive opening, and closing gives the first level back.
    assert inner["gaps"] == top["gaps"] and top["gaps"]
    assert opened(app) == top


def test_a_framework_a_module_declares_is_in_its_stack_open_or_closed_and_never_a_node_and_a_tool_or_a_mention_is_not(
        levels, tmp_path):
    import technologies
    from snapshot_store import resolve_run_snapshot
    run = levels.root / "runs" / "levels"
    stack = technologies.ensure(resolve_run_snapshot(run, json.loads((run / "state.json").read_text(encoding="utf-8"))))
    assert "opentelemetry" in {item["id"] for item in stack["mentioned"]}  # a framework only mentioned
    assert {"jest", "nodejs"} == {item["id"] for item in stack["technologies"] if item["category"] == "tool"}
    assert next(unit for unit in stack["units"] if unit["paths"] == ["web"])["frameworks"] == ["express"]  # zod is no framework
    # The first level: each module carries the frameworks and libraries it declares, each with its category, the
    # declaring file and line, and the count of its other declared packages (@acme/widgets: the registry does not
    # know it; jest: a tool, no tile; zod: a tile, not counted again; stripe is a node of its own).
    app = leveled(levels, tmp_path)
    top = app.graph({})
    web, admin, server = (group_of(top, path) for path in ("web/api.ts", "admin/index.js", "server/app.py"))
    express = {"id": "express", "name": "Express", "kind": "project", "category": "framework", "mark": "express"}
    zod = {"id": "zod", "name": "Zod", "kind": "project", "category": "library", "mark": "zod"}
    shown = {node["id"]: node for node in top["nodes"]}
    assert (shown[web]["projects"], shown[web]["other_dependencies"]) == (
        [{**express, "evidence": [{"path": "web/package.json", "line": 6}]},
         {**zod, "evidence": [{"path": "web/package.json", "line": 8}]}], 2)
    # The stack is one: a framework the step recognises by a file's name is in it as one a package declares, with
    # that file as its evidence (the page's «Tecnologie e framework» lists it: the card must not say less).
    assert "nextjs" in {item["id"] for item in stack["technologies"] if item["category"] == "framework"}
    assert shown[admin]["projects"][0] == {**express, "evidence": [{"path": "admin/package.json", "line": 5}]}
    assert [(item["id"], item["name"], item["kind"], [site["path"] for site in item["evidence"]])
            for item in shown[admin]["projects"][1:]] == [("nextjs", "Next.js", "project", ["admin/next.config.js"])]
    assert (shown[server]["projects"], shown[server]["other_dependencies"]) == ([], 0)
    assert {project["id"] for node in top["nodes"] for project in node.get("projects", ())} == {"express", "nextjs", "zod"}
    # Open, the frame of the module keeps its stack; at no detail is a framework, a tool or a mention a node or an end.
    one, two = opened(app, web), opened(app, web, admin, f"{web}#web/lib")
    assert next(item for item in one["open"] if item["id"] == web)["projects"] == shown[web]["projects"]
    assert next(item for item in two["open"] if item["id"] == admin)["projects"] == shown[admin]["projects"]
    for found in (top, one, two):
        ends = {node["id"] for node in found["nodes"]} | {
            end for edge in found["edges"] for end in (edge["source"], edge["target"])}
        assert not ends & {"external:express", "external:zod", "external:jest", "external:nodejs",
                           "external:opentelemetry"}
    assert opened(app) == top
    # codice alone keeps the stack, the module's own, and drops the services
    code = {node["id"]: node for node in app.graph({"levels": json.dumps(["codice"])})["nodes"]}
    assert code[web]["projects"] == shown[web]["projects"] and "external:stripe" not in code


def test_a_symbol_holding_others_opens_into_them_and_a_closed_class_keeps_its_calls_counts_and_lines(levels, tmp_path):
    app = leveled(levels, tmp_path)
    server = group_of(app.graph({}), "server/app.py")
    store, outbox, db = f"{server}#server/store", "file:server/store/outbox.py", "file:server/store/db.py"
    klass, drain = "symbol:server/store/outbox.py::Outbox", "symbol:server/store/outbox.py::drain"
    push, size = "symbol:server/store/outbox.py::Outbox.push", "symbol:server/store/outbox.py::Outbox.size"
    call = {"calls": 1}, [{"kind": "calls", "path": "server/store/outbox.py", "line": 6}]
    # The file open: its outermost symbols, the class holding its methods; the method's call to the closed file is
    # lifted to the class with its count and line.
    file = opened(app, server, store, outbox)
    shown = {node["id"]: node for node in file["nodes"] if node["group"] == outbox}
    assert set(shown) == {klass, drain} and sorted(shown[klass]["members"]) == [push, size]
    closed = arrows(file)[(klass, db, "confirmed")]
    assert (closed["counts"], closed["evidence"]) == call
    # The class open: its methods, the call from the method itself.
    method = opened(app, server, store, outbox, klass)
    assert [(item["id"], item["parent"]) for item in method["open"]][-1] == (klass, outbox)
    assert {node["id"] for node in method["nodes"] if node["group"] == klass} == {push, size}
    open_call = arrows(method)[(push, db, "confirmed")]
    assert (open_call["counts"], open_call["evidence"]) == call
    assert not any(klass == key[0] for key in arrows(method))
    # Closing the class gives its arrow back; closing the file gives the summary between the files.
    assert arrows(opened(app, server, store, outbox))[(klass, db, "confirmed")] == closed
    assert arrows(opened(app, server, store))[(outbox, db, "confirmed")]["counts"] == {"imports": 1, "calls": 1}


def test_a_file_a_symbol_a_node_the_run_does_not_show_or_a_path_is_refused_as_a_group(levels, tmp_path):
    app = leveled(levels, tmp_path)
    server = group_of(app.graph({}), "server/app.py")
    for asked in (["component:nowhere"], ["file:server/missing.py"], ["../../etc/passwd"], ["file:../server/app.py"],
                  ["file:/etc/passwd"], [f"{server}#.."], [f"{server}#server/../web"], [f"{server}#server/store/"],
                  ["#server/store"], ["symbol:server/store/db.py::save"], ["external:stripe"],
                  [f"{server}#server/store"], ["file:server/app.py"], ["external:express"],
                  [server, f"{server}#server/store", "file:server/store/db.py", "symbol:server/store/db.py::save"]):
        with pytest.raises(ValueError, match="to open: "):
            opened(app, *asked)
    with pytest.raises(ValueError, match='to open: "symbol:server/store/db.py::save"'):  # the id, as the page drops it
        opened(app, server, "symbol:server/store/db.py::save")
    for value in ("not json", "{}", "[1]", '"build:web"'):
        with pytest.raises(ValueError, match="list of node ids"):
            app.graph({"open": value})
    for file in ("../server/app.py", "server/app.py", "symbol:server/store/db.py::save", server, "file:nowhere.py"):
        with pytest.raises(ValueError):
            app.symbols({"file": file})
    # the graph is the system map's levels codice and infrastruttura; codice alone has no external node nor its arrows;
    # a level the app does not build is refused, never served as the code's
    both = app.graph({"levels": json.dumps(["infrastruttura", "codice"])})
    assert both == app.graph({}) and both["levels"] == ["codice", "infrastruttura"]
    code = app.graph({"levels": json.dumps(["codice"])})
    assert code["levels"] == ["codice"] and {node["level"] for node in code["nodes"]} == {"codice"}
    assert not any(end.startswith("external:") for edge in code["edges"] for end in (edge["source"], edge["target"]))
    assert {node["id"] for node in code["nodes"]} == {node["id"] for node in both["nodes"]} - {"external:stripe"}
    for asked, why in ((["funzioni"], "'funzioni' is not built in the app yet"), (["Funzionale"], "no level 'Funzionale'"),
                       (["infrastruttura"], "only beside 'codice'"), ([], "a JSON list of levels"),
                       ("codice", "a JSON list of levels")):
        with pytest.raises(ValueError, match=why):
            app.graph({"levels": json.dumps(asked) if isinstance(asked, list) else asked})


def test_the_inspector_of_a_file_has_its_symbols_and_calls_with_lines_read_for_that_file_only(levels, tmp_path,
                                                                                              monkeypatch):
    app, asked = leveled(levels, tmp_path), []

    def counted(run_dir, path, _original=visual.file_symbols):
        asked.append(path)
        return _original(run_dir, path)
    monkeypatch.setattr(visual, "file_symbols", counted)
    server = group_of(app.graph({}), "server/app.py")
    store = f"{server}#server/store"
    opened(app, server, store)
    assert asked == []  # opening a module or a directory reads no symbol
    found = app.symbols({"file": "file:server/store/db.py"})  # the file closed: its inspector
    assert asked == ["server/store/db.py"]
    save, load = "symbol:server/store/db.py::save", "symbol:server/store/db.py::load"
    assert [(symbol["id"], symbol["lines"]) for symbol in found["symbols"]] == [(save, [1, 2]), (load, [5, 6])]
    calls = {(call["source"], call["target"]): call for call in found["calls"]}
    assert (calls[(load, save)]["counts"], calls[(load, save)]["evidence"]) == (
        {"calls": 1}, [{"kind": "calls", "path": "server/store/db.py", "line": 6}])
    assert calls[("file:server/store/cache.py", save)]["evidence"] == [
        {"kind": "calls", "path": "server/store/cache.py", "line": 5}]
    assert calls[("file:server/jobs.py", load)]["counts"] == {"calls": 1}
    # opening the file reads what the inspector read, once; opening another reads that one only
    opened(app, server, store, "file:server/store/db.py")
    assert asked == ["server/store/db.py"]
    opened(app, server, store, "file:server/store/cache.py")
    assert asked == ["server/store/db.py", "server/store/cache.py"]


def test_a_level_is_computed_once_per_state_of_the_run_and_again_when_the_run_changes(levels, tmp_path, monkeypatch):
    import card_store
    import semantic_store
    from snapshot_store import open_snapshot, resolve_run_snapshot
    import confinement
    app, computed = leveled(levels, tmp_path), Counter()

    def busy(*args, **kwargs):
        raise confinement.ProjectBusy("project lock is held by another helper; retry after that invocation finishes")
    with monkeypatch.context() as patch:  # a busy project answers busy (the route's 503) and keeps nothing
        patch.setattr(visual, "build_envelope", busy)
        with pytest.raises(confinement.ProjectBusy):
            app.graph({})
    for name in ("build_envelope", "file_symbols"):
        def counted(*args, _original=getattr(visual, name), _name=name, **kwargs):
            computed[_name] += 1
            return _original(*args, **kwargs)
        monkeypatch.setattr(visual, name, counted)
    file = "file:server/store/db.py"
    top = app.graph({})
    server = group_of(top, "server/app.py")
    first = [top, opened(app, server), opened(app, server, f"{server}#server/store"), app.symbols({"file": file})]
    assert computed == {"build_envelope": 1, "file_symbols": 1}

    def refused(*args, **kwargs):
        raise AssertionError("a kept level read the run again")
    with monkeypatch.context() as patch:
        for owner, name in ((visual.source_reader, "graph_packet"), (visual.source_reader, "outline_manifest"),
                            (visual, "build_envelope"), (visual, "file_symbols")):
            patch.setattr(owner, name, refused)
        assert [app.graph({}), opened(app, server), opened(app, f"{server}#server/store", server),
                app.symbols({"file": file})] == first
    # a card written on a symbol changes the run's data: what was kept is computed again, and shows it
    run = levels.root / "runs" / "levels"
    manifest = resolve_run_snapshot(run, json.loads((run / "state.json").read_text(encoding="utf-8")))
    with open_snapshot(manifest) as store:
        semantic_store.upsert_meta_cards(store, card_store.default_cards_path(manifest),
                                         [{"file": "server/store/db.py", "symbol": "save", "purpose": "Saves an item."}])
    after = app.symbols({"file": file})
    assert computed == {"build_envelope": 2, "file_symbols": 2}
    assert next(symbol for symbol in after["symbols"] if symbol["name"] == "save")["responsibility"] == "Saves an item."


def test_the_first_level_and_an_opening_ask_the_readers_as_often_however_many_symbols_the_files_hold(tmp_path,
                                                                                                    monkeypatch):
    """A guard that does not depend on the machine: two runs of 240 files, one function each or eight, ask the
    readers the same number of times for the first level and for opening a group, and never for a file's outline or
    cards."""
    import mcp_service
    import semantic_store
    import snapshot_store
    asked = []
    for functions in (1, 8):
        project = tmp_path / f"functions-{functions}"
        for number in range(240):
            path = project / f"pkg{number % 12}" / f"m{number}.py"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(f"def f{k}():\n    return {k}\n\n\n" for k in range(functions)), encoding="utf-8")
        git(project, "init", "-q")
        git(project, "add", "-A")
        git(project, "commit", "-q", "-m", "many")
        service = mcp_service.MapService(project)
        service.create_run(".", "levels", engine=False)
        calls = Counter()
        with monkeypatch.context() as patch:
            for owner, name in ((visual.source_reader, "outline_manifest"), (visual.source_reader, "graph_packet"),
                                (semantic_store, "query_meta_code"), (snapshot_store.SnapshotStore, "get_file")):
                def counted(*args, _original=getattr(owner, name), _name=name, **kwargs):
                    calls[_name] += 1
                    return _original(*args, **kwargs)
                patch.setattr(owner, name, counted)
            app = leveled(service, tmp_path / f"app-{functions}")
            top = app.graph({})
            inside = opened(app, "directory:pkg0")
        assert top["files"] == 240
        assert len([node for node in inside["nodes"] if node["group"] == "directory:pkg0"]) == 20
        asked.append(calls)
    assert asked[0] == asked[1]
    assert (asked[0]["outline_manifest"], asked[0]["query_meta_code"], asked[0]["graph_packet"]) == (0, 0, 1)


def test_the_app_goes_from_an_address_to_a_run_and_says_its_state(tmp_path, monkeypatch):
    project = tmp_path / "checkout"
    project.mkdir()
    (project / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    found = {"host": "github.com", "owner": "o", "name": "n", "url": "https://github.com/o/n"}
    monkeypatch.setattr(repository, "checkout", lambda address, branch, work: {
        "repository": found, "branch": branch, "commit": "a" * 40, "path": str(project)})
    monkeypatch.setattr(launcher.App, "_warm", lambda self: setattr(self, "mcp_ready", "ready"))  # no download
    app = launcher.App(tmp_path / "work", environment={})
    server = app.serve(token="t")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        port = server.server_address[1]
        assert request(port, "/app/")[0] == 200 and request(port, "/api/app/state", token=None)[0] == 403
        for path in ("/api/runs", "/api/app/premap", "/api/app/graph"):
            assert request(port, path) == (400, {"error": "no repository is selected"})
        alone = stream(port, "run=app-000000000000&after=3&max_seconds=1")  # before a selection: the state alone
        assert [(name, data["job"]["state"], data["context"]) for name, data in alone] == [("app", "idle", None)]
        assert request(port, "/api/stream?once=1", token=None)[0] == 403
        assert request(port, "/api/app/select", {"url": "https://example.com/o/n", "branch": "main"})[0] == 400
        status, state = request(port, "/api/app/select", {"url": found["url"], "branch": "main"})
        assert status == 200 and state["job"]["state"] in ("preparing", "ready")
        deadline = time.monotonic() + 120
        while state["job"]["state"] == "preparing" and time.monotonic() < deadline:
            time.sleep(0.2)
            state = request(port, "/api/app/state")[1]
        assert state["job"] == {"state": "ready", "step": None, "detail": ""}
        assert state["context"]["run_id"] == "app-aaaaaaaaaaaa" and state["run"]["pipeline"]["scan"] == "fresh"
        assert state["mcp"]["args"][-2:] == ["--project", project.parent.as_posix()]
        # what Daodan writes about the checkout is beside it: a container's output may not be inside the project
        assert (project.parent / ".daodan").is_dir() and not (project / ".daodan").exists()
        # The page observes: the run's events from its start and the app's state, then again from the cursors.
        seen = stream(port, "run=app-000000000000&after=3&max_seconds=1")
        first = next(data for name, data in seen if name == "snapshot")["run_events"]
        assert first["run_id"] == "app-aaaaaaaaaaaa" and first["pipeline"]["events"][0]["kind"] == "step.started"
        told = [data for name, data in seen if name == "app"][-1]
        assert told["context"]["run_id"] == "app-aaaaaaaaaaaa" and told["run"]["pipeline"]["scan"] == "fresh"
        last = [data for name, data in seen if name in ("snapshot", "update")][-1]
        cursors = (last["run_events"]["next_cursor"], last["run_events"]["pipeline"]["next_cursor"],
                   last["pulse"]["next_cursor"])
        again = stream(port, "run=app-aaaaaaaaaaaa&after=%d&pipeline_after=%d&pulse_after=%d&max_seconds=1" % cursors)

        def delivered(frames):
            return {json.dumps(item) for _, data in frames if "run_events" in data
                    for item in (*data["run_events"]["events"], *data["run_events"]["pipeline"]["events"])}
        assert [name for name, _ in again][:2] == ["app", "snapshot"] and not delivered(again) & delivered(seen)
        assert [run["run_id"] for run in request(port, "/api/runs")[1]["runs"]] == ["app-aaaaaaaaaaaa"]
        premap = request(port, "/api/app/premap")[1]
        assert premap["files"] == ["a.py"] and premap["languages"] == [{"name": "Python", "files": 1}]
        drawn = request(port, "/api/app/graph")[1]
        assert drawn["files"] == 1 and sum(len(node["files"]) for node in drawn["nodes"]) == 1
        assert drawn["open"] == []
        shown = request(port, "/api/app/graph?open=" + quote(json.dumps(["directory:."])))[1]  # opened in place
        assert [(node["id"], node["group"]) for node in shown["nodes"]] == [("file:a.py", "directory:.")]
        assert request(port, "/api/app/graph?open=" + quote(json.dumps(["../a.py"])))[0] == 400
        assert [symbol["name"] for symbol in request(port, "/api/app/symbols?file=file%3Aa.py")[1]["symbols"]] == ["f"]
        status, told = request(port, "/api/app/link", {})  # the service gives the rule format; no engine is chosen
        assert status == 200 and told["links"]["state"] == "no_engine"
        described = request(port, "/api/app/engine", {"engine": "openai", "model": "m", "api_key": "sk-secret"})[1]
        assert described["api_key"] == "set" and "sk-secret" not in json.dumps(request(port, "/api/app/state")[1])
        assert request(port, "/api/app/engine", {"engine": "other"})[0] == 400
        assert request(port, "/api/app/ask", {"question": " "})[0] == 400
    finally:
        app.close()
        server.shutdown()
        server.server_close()


def test_a_pass_that_failed_starts_again_when_asked_and_when_its_commit_is_selected_again(tmp_path, monkeypatch):
    """A pass that did not start (no memory free, say) is not the run's last word: asking again, or selecting the
    same commit again, has the service repair it; a run already there is never created twice."""
    asked = []

    class Service:
        def __init__(self, root):
            asked.append(("root", Path(root).name))

        def runs(self):
            return {"runs": [{"run_id": "app-aaaaaaaaaaaa"}]}

        def create_run(self, *given):
            asked.append(("create", *given))

        def index(self, run_id):
            asked.append(("index", run_id))

        def status(self, run_id):
            return {}

    monkeypatch.setattr(launcher, "MapService", Service)
    monkeypatch.setattr(repository, "checkout", lambda address, branch, work: {
        "repository": {}, "branch": branch, "commit": "a" * 40, "path": str(tmp_path / "commit" / "source")})
    monkeypatch.setattr(launcher.App, "_warm", lambda self: None)
    app = launcher.App(tmp_path / "work", environment={})
    with pytest.raises(ValueError, match="no repository is selected"):
        app.retry({})
    app._prepare("https://github.com/o/n", "main")
    assert app.job["state"] == "ready" and asked == [("root", "commit"), ("index", "app-aaaaaaaaaaaa")]
    assert app.retry({})["context"]["run_id"] == "app-aaaaaaaaaaaa"
    assert asked[2:] == [("index", "app-aaaaaaaaaaaa")]


RULE = {"written": "fetch", "in": ["app/client"], "link": "rotta", "route": {"service": "api", "method": "GET", "path": "arg0"}}


class Flows:
    """The service's flows as the app reads them: the rule format until rules are recorded, then what they link; a
    rule without its link is refused with the service's reason."""

    def __init__(self):
        self.rules, self.asked = None, []

    def status(self, run_id):
        return {}

    def flows(self, run_id, rules=None):
        self.asked.append(rules)
        if rules is not None:
            if any("link" not in rule for rule in rules):
                raise ValueError("rule 0: link must be one of scrive, legge, rotta, offre, attiva, ingresso")
            self.rules = rules
        if self.rules is None:
            return {"status": "needs_rules", "run_id": run_id, "format": "the rule format v1",
                    "technologies": [{"unit": "app/server", "technologies": ["flask"]}]}
        return {"status": "ok", "run_id": run_id, "entries": [], "entry_count": 0,
                "routes": {"offered": 2, "called": 2, "linked": 2}, "stores": {}, "store_count": 0, "gaps": [],
                "gap_count": 0, "external": []}


def linking(tmp_path, environment=None):
    """An app on a selected run whose service is `Flows`."""
    app = launcher.App(tmp_path / "work", environment=environment or {})
    app.service, app.context = Flows(), {"run_id": "app-r", "path": str(tmp_path / "commit" / "source")}
    return app


def settled(app) -> dict:
    deadline = time.monotonic() + 60
    while app.linked["state"] == "running" and time.monotonic() < deadline:
        time.sleep(0.05)
    return app.linked


def openai(endpoint) -> dict:
    return {"DAODAN_ENGINE": "openai", "DAODAN_OPENAI_BASE_URL": endpoint, "DAODAN_OPENAI_MODEL": "m",
            "DAODAN_OPENAI_API_KEY": "sk-secret"}


def test_finding_the_links_without_an_engine_says_what_to_do_and_starts_nothing(tmp_path):
    app = linking(tmp_path)
    told = app.link({})["links"]
    assert told["state"] == "no_engine" and "engine" in told["cause"]
    assert app.service.asked == [None] and not (tmp_path / "work" / "engine").exists()  # read, nothing written or run


def test_the_engine_records_the_rules_through_the_flows_tool_and_the_service_says_what_they_link(
        tmp_path, endpoint, monkeypatch):
    monkeypatch.setattr(Endpoint, "call", ("codebase_map_flows", json.dumps({"rules": [RULE]})))
    app = linking(tmp_path, openai(endpoint))
    assert app.link({})["links"]["state"] == "running"
    assert settled(app) == {"state": "done", "cause": None, "routes": {"offered": 2, "called": 2, "linked": 2},
                            "stores": 0, "gaps": 0}
    assert app.service.asked == [None, [RULE], None]  # the format, the rules through the tool, then the outcome
    first = Endpoint.seen[0][2]
    assert "codebase_map_flows" in [tool["function"]["name"] for tool in first["tools"]]
    task = first["messages"][-1]["content"]
    assert "the rule format v1" in task and "flask" in task and "app-r" in task and "at most 3 times" in task
    assert "sk-secret" not in task and app.state({})["links"]["state"] == "done"
    assert "sk-secret" not in json.dumps(app.state({}))


def test_an_engine_that_records_no_valid_rules_fails_with_the_cause(tmp_path, endpoint, monkeypatch):
    monkeypatch.setattr(Endpoint, "call", ("codebase_map_flows", json.dumps({"rules": [{"written": "fetch"}]})))
    app = linking(tmp_path, openai(endpoint))
    app.link({})
    told = settled(app)
    assert told["state"] == "failed" and "link must be one of" in told["cause"]  # the service's own reason
    answered = {"type": "result", "result": "all linked", "is_error": False, "session_id": "s1"}
    monkeypatch.setattr(engines, "configured", lambda chosen: scripted(tmp_path, [answered]))
    app.link({})
    told = settled(app)
    assert told["state"] == "failed" and "no rules" in told["cause"]  # its words are no result


def test_finding_the_links_runs_once_at_a_time_and_stops_with_the_app(tmp_path, monkeypatch):
    class Waiting:
        def __init__(self):
            self.started, self.go = [], threading.Event()

        def run(self, task, say, cancelled):
            self.started.append(task["prompt"])
            self.go.wait(30)
            return {"state": "cancelled" if cancelled() else "done", "text": "", "session": None, "cause": None}

    engine = Waiting()
    monkeypatch.setattr(engines, "configured", lambda chosen: engine)
    app = linking(tmp_path)
    app.link({})
    with pytest.raises(ValueError, match="wait"):
        app.link({})
    with pytest.raises(ValueError, match="in progress"):
        app.select({"url": "https://github.com/o/n", "branch": "main"})
    app.close()
    engine.go.set()
    told = settled(app)
    assert len(engine.started) == 1 and told["state"] == "failed" and "stopped" in told["cause"]


def raw(port: int, path: str) -> tuple[int, str, bytes]:
    """Status, type and body of a GET, as an image asks it: no header, the token in the address."""
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=60)
    try:
        connection.request("GET", path)
        answer = connection.getresponse()
        return answer.status, answer.getheader("Content-Type"), answer.read()
    finally:
        connection.close()


def test_the_mark_of_a_registry_entry_is_served_by_its_id_and_nothing_else_is(tmp_path, monkeypatch):
    """The page asks a node's mark by its registry id; a mark taken out of its owner's package on first use is fetched
    off the request, so the answer is no mark until it is there, never a wait."""
    import service_registry
    shipped, held, asked = service_registry.mark_file, threading.Event(), []

    def mark_file(entry):
        if not entry.get("mark_source"):
            return shipped(entry)
        asked.append(entry["id"])
        held.wait(30)
        return shipped({"mark": "marks/stripe.svg"})

    monkeypatch.setattr(service_registry, "mark_file", mark_file)
    app = launcher.App(tmp_path / "work", environment={})
    # an entry whose mark is in its owner's package: the test's own, the distributed registry ships every mark it has
    app.registry["packaged.example"] = {"id": "packaged.example", "mark": None,
                                        "mark_source": {"url": "https://owner.example/icons.zip"}}
    server = app.serve(token="t")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        port = server.server_address[1]
        stripe = (service_registry.REGISTRY.parent / "marks/stripe.svg").read_bytes()
        assert raw(port, "/api/app/mark?id=stripe&token=t") == (200, "image/svg+xml", stripe)
        assert raw(port, "/api/app/mark?id=stripe")[0] == 403
        for wrong in ("nope", "marks/stripe.svg", "../data/marks/stripe.svg", ""):
            assert raw(port, f"/api/app/mark?id={wrong}&token=t")[0] == 400, wrong
        assert raw(port, "/api/app/mark?token=t")[0] == 400
        assert raw(port, "/api/app/mark?id=adobe.analytics&token=t")[0] == 404  # an entry without a mark: no image
        started = time.monotonic()
        assert raw(port, "/api/app/mark?id=packaged.example&token=t")[0] == 404
        assert time.monotonic() - started < 5 and asked == ["packaged.example"]
        held.set()
        deadline = time.monotonic() + 30
        while (found := raw(port, "/api/app/mark?id=packaged.example&token=t"))[0] != 200 and time.monotonic() < deadline:
            time.sleep(0.05)
        assert found == (200, "image/svg+xml", stripe) and asked == ["packaged.example"]  # fetched once
    finally:
        held.set()
        app.close()
        server.shutdown()
        server.server_close()


def test_a_busy_project_is_no_failure_the_stream_skips_a_turn_and_a_read_answers_busy(tmp_path, monkeypatch):
    """Another helper holding the project's lock is busy now: the stream reads again at its next turn and a route
    answers 503, which the page reads as «Daodan è occupato»."""
    import confinement

    def busy():
        return confinement.ProjectBusy("project lock is held by another helper; retry after that invocation finishes")

    class Service:
        asked = 0

        def status(self, run_id):
            Service.asked += 1
            if Service.asked == 1:
                raise busy()
            return {"pipeline": {"scan": "fresh"}, "progress": None, "engine": {"state": "fresh", "reason": None}}

    def explorer(query, should_stop):
        return [("snapshot", {"run_events": {"events": [], "next_cursor": 0, "pipeline": {"events": [], "next_cursor": 0}},
                              "pulse": {"events": [], "next_cursor": 0}})]

    monkeypatch.setattr(launcher, "TURN", 0.01)
    app = launcher.App(tmp_path / "work", environment={})
    app.service, app.context = Service(), {"run_id": "r", "path": str(tmp_path / "checkout")}
    frames = list(app.stream(explorer)({"run": "r", "max_seconds": "1"}, lambda: False))
    assert [name for name, _ in frames] == ["app", "snapshot"] and Service.asked == 2
    assert frames[0][1]["run"]["pipeline"] == {"scan": "fresh"}

    def refused(query):
        raise busy()

    server = visual.make_server(None, tmp_path, routes={"/api/app/graph": refused}, token="t")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        assert request(server.server_address[1], "/api/app/graph") == (503, {"error": str(busy())})
    finally:
        server.shutdown()
        server.server_close()
