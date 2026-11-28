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


def _modelling(plan: dict) -> bool:
    """A source of `find_modules` still waits for the pass to run its model commands (`pending` with `model_not_run`)."""
    return any(action["step"] == "find_modules" and action["state"] == "pending" and action.get("gap") == "model_not_run"
               for action in plan["actions"])


def _modelled(plan: dict) -> bool:
    """The step `find_modules` of the plan is done, or up to date."""
    return {step["id"]: step["state"] for step in plan["steps"]}["find_modules"] in ("done", "skipped")


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
def deposit(monkeypatch):
    import secret_mask
    monkeypatch.setattr(secret_mask, "masked", lambda text, name: {"text": text, "found": 0, "kinds": []})
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


def test_mapping_tool_checks_source_and_errors_before_the_api_turn(monkeypatch):
    import io
    import secret_mask
    from unittest.mock import Mock

    secret = "DEMO_ONLY_PRIVATE"
    def scan(text, _name):
        return {"text": text.replace(secret, "*" * len(secret)), "found": text.count(secret), "kinds": []}

    monkeypatch.setattr(secret_mask, "masked", scan)
    app = object.__new__(launcher.App)
    app.service, app.context = Mock(), {"run_id": "demo"}
    app.service.read.return_value = {"excerpt": ["😀\n" + secret + "\nend", {"field": "kept"}]}
    tools = app._tools()
    read = next(tool["call"] for tool in tools if tool["name"] == "codebase_map_read")
    checked = read({"requests": []})
    assert checked["excerpt"] == ["😀\n" + "*" * len(secret) + "\nend", {"field": "kept"}]
    assert checked["masked_secrets"] == 1
    app.service.read.side_effect = ValueError("refused " + secret)
    requests = []
    def transport(request, timeout):
        requests.append(json.loads(request.data))
        delta = {"tool_calls": [{"id": "read", "function": {"name": "codebase_map_read", "arguments": '{"requests":[]}'}}]} \
            if len(requests) == 1 else {"content": "done"}
        return io.BytesIO(("data: " + json.dumps({"choices": [{"delta": delta}]}) + "\n").encode("utf-8"))
    monkeypatch.setattr(engines.urllib.request, "urlopen", transport)
    client = engines.OpenAICompatible("https://demo.invalid/v1", "demo")
    result = client.run({"prompt": "read", "tools": tools})
    assert result["state"] == "done"
    message = json.loads(requests[-1]["messages"][-1]["content"])
    assert message["error"] == "refused " + "*" * len(secret)
    def broken(*args):
        raise ValueError(secret)
    monkeypatch.setattr(secret_mask, "masked", broken)
    assert read({"requests": []}) == {"status": "withheld", "error": secret_mask.UNAVAILABLE}


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


def test_the_pre_map_shows_uncatalogued_services_with_their_actual_owner():
    mail = {"name": "mailpit", "path": "api/compose.yml", "declared_in": "api/compose.yml#L3",
            "image": "axllent/mailpit"}
    worker = {"name": "worker", "path": "ci/compose.yml", "declared_in": "ci/compose.yml#L5"}
    stack = {"technologies": [], "configured_services": [mail, worker],
             "modules": [{"id": "api", "name": "api", "paths": ["api"], "configured_services": [mail]}]}
    assert app_view.premap(stack, {}, {})["technologies"] == [
        {"name": "mailpit", "category": "servizio configurato", "source": mail["declared_in"], "unit": "api",
         "state": "configured", "image": "axllent/mailpit"},
        {"name": "worker", "category": "servizio configurato", "source": worker["declared_in"], "unit": "",
         "state": "configured"},
    ]


def test_the_pre_map_lists_the_units_with_their_declared_libraries_and_the_unit_that_holds_each():
    stack = {"technologies": [{"id": "pytest", "name": "pytest", "category": "framework",
                               "signs": [{"path": "other/pyproject.toml", "line": 3, "sign": "package", "strength": "declared"},
                                         {"path": "pkg/a.py", "line": 1, "sign": "env", "strength": "mentioned"},
                                         {"path": "pkg/pyproject.toml", "line": 9, "sign": "package", "strength": "declared"}]}],
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
    # a recognized technology names the mark of its registry entry, as the envelope does; a toolchain has no entry
    assert [(item["name"], item["source"], item["state"], item.get("mark")) for item in found["technologies"]] == [
        ("pytest", "pkg/pyproject.toml:9", "recognized", "pytest"), ("python", "pkg/pyproject.toml", "declared", None)]
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
def levels(real_stack, tmp_path_factory):
    """A run with three build units, a service the stack recognises, declared and mentioned by a host in a URL, a
    framework two of them declare, a service only mentioned by a host, a library the registry knows, a tool and a library it does not know, a deduced link between two units and a module with a
    directory whose files call each other, one holding a class with two methods."""
    import mcp_service
    pets = HERE.parent / "benchmarks/connection-points/fixtures/pets"
    project = tmp_path_factory.mktemp("levels") / "project"
    shutil.copytree(pets / "app", project)
    files = {"web/package.json": json.dumps({"name": "web", "version": "1.0.0", "dependencies": {
                 "stripe": "^14.0.0", "express": "^4.19.0", "@acme/widgets": "^1.0.0", "zod": "^3.23.0",
                 "jest": "^29.7.0", "lemonsqueezy.ts": "^0.1.0"}}, indent=2),
             # express: line 6, zod (a library) 8, jest (a tool) 9
             "web/lib/pay.js": 'module.exports = "https://api.lemonsqueezy.com/v1/checkouts";\n',
             "web/lib/trace.js": 'module.exports = "https://api.pushbullet.com/v2";\n',
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
    # no node is in an open group; an external service is a node of the nature fisico, a group of codice
    assert [{**node, "group": None, "level": "fisico" if node["location"] == "external" else "codice"}
            for node in whole["nodes"]] == top["nodes"]
    assert (top["levels"], top["grouping"], top["open"]) == (["codice", "fisico"], "modules", [])
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
    assert two[(f"{web}#web/lib", "external:lemonsqueezy", "uncertain")]["counts"] == {"uses": 1}
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


def test_a_technology_a_module_declares_is_a_node_under_technologies_and_a_tile_of_its_stack_and_a_mention_is_not(
        levels, tmp_path):
    import technologies
    from snapshot_store import resolve_run_snapshot
    run = levels.root / "runs" / "levels"
    stack = technologies.ensure(resolve_run_snapshot(run, json.loads((run / "state.json").read_text(encoding="utf-8"))))
    assert "pushbullet" in {item["id"] for item in stack["mentioned"]}  # a service only mentioned
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
    # Open, the frame of the module keeps its stack.
    one, two = opened(app, web), opened(app, web, admin, f"{web}#web/lib")
    assert next(item for item in one["open"] if item["id"] == web)["projects"] == shown[web]["projects"]
    assert next(item for item in two["open"] if item["id"] == admin)["projects"] == shown[admin]["projects"]
    # Frameworks, libraries and tools are nodes under «Tecnologie», a group beside the modules that does not choose the
    # grouping; a mention and a service are not among them. Closed, a module's uses go to the group.
    group = "group:technologies"
    built = {f"technology:{item['id']}" for item in stack["technologies"]
             if item["category"] in ("framework", "library", "tool")}
    assert {"technology:express", "technology:zod", "technology:jest", "technology:nodejs", "technology:nextjs"} <= built
    assert not built & {"technology:pushbullet", "technology:stripe"}
    assert (shown[group]["name"], shown[group]["group"], sorted(shown[group]["members"])) == ("Tecnologie", None, sorted(built))
    assert not any(node["id"].startswith("technology:") for node in top["nodes"])
    closed = arrows(top)
    assert closed[(web, group, "confirmed")]["counts"]["uses"] >= 3  # express, zod, jest at least
    assert closed[(admin, group, "confirmed")]["counts"]["uses"] >= 2  # express, nextjs
    # Open, each module uses each technology it declares, at the declaring site.
    techs = opened(app, group)
    assert {node["id"] for node in techs["nodes"] if node["group"] == group} == built
    assert {node["level"] for node in techs["nodes"] if node["group"] == group} == {"codice"}
    express_node = next(node for node in techs["nodes"] if node["id"] == "technology:express")
    assert (express_node["location"], express_node["mark"]) == ("external", "express")
    uses = arrows(techs)
    assert uses[(web, "technology:express", "confirmed")]["evidence"] == [
        {"kind": "uses", "path": "web/package.json", "line": 6}]
    assert uses[(admin, "technology:express", "confirmed")]["evidence"] == [
        {"kind": "uses", "path": "admin/package.json", "line": 5}]
    assert uses[(web, "technology:jest", "confirmed")]["evidence"] == [
        {"kind": "uses", "path": "web/package.json", "line": 9}]
    assert (web, "technology:zod", "confirmed") in uses and (admin, "technology:nextjs", "confirmed") in uses
    assert not any(target == group for _source, target, _status in uses)
    for found in (top, one, two, techs):
        ends = {node["id"] for node in found["nodes"]} | {
            end for edge in found["edges"] for end in (edge["source"], edge["target"])}
        assert not ends & {"external:express", "external:zod", "external:jest", "external:nodejs",
                           "external:pushbullet", "technology:pushbullet"}
    assert opened(app) == top
    # codice alone keeps the stack, the module's own, and «Tecnologie», and drops the services
    code = {node["id"]: node for node in app.graph({"levels": json.dumps(["codice"])})["nodes"]}
    assert code[web]["projects"] == shown[web]["projects"] and "external:stripe" not in code and group in code


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
    # the graph is the natures codice and fisico (the old name infrastruttura still taken); codice alone has no
    # external node nor its arrows;
    # a level the app does not build is refused, never served as the code's
    both = app.graph({"levels": json.dumps(["fisico", "codice"])})
    assert both == app.graph({}) and both["levels"] == ["codice", "fisico"]
    assert app.graph({"levels": json.dumps(["infrastruttura", "codice"])}) == both
    code = app.graph({"levels": json.dumps(["codice"])})
    assert code["levels"] == ["codice"] and {node["level"] for node in code["nodes"]} == {"codice"}
    assert not any(end.startswith("external:") for edge in code["edges"] for end in (edge["source"], edge["target"]))
    assert {node["id"] for node in code["nodes"]} == {node["id"] for node in both["nodes"]} - {
        "external:stripe", "external:lemonsqueezy"}
    for asked, why in ((["logico"], "'logico' is not built in the app yet"), (["funzioni"], "'logico' is not built"),
                       (["Funzionale"], "no level 'Funzionale'"), (["fisico"], "only beside 'codice'"), ([], "a JSON list of levels"),
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


def test_the_state_shows_the_host_requests_by_tool_and_only_its_guarded_action_answers_them(tmp_path):
    """The requests of the selected checkout's analysis, one group a tool, with what the popup shows; the action
    answers a group, under the server's guard, and only for hosts that wait for an answer."""
    import egress
    project = tmp_path / "checkout"
    project.mkdir()
    key = str(project.resolve())
    with egress.asking("mise"):
        egress.collect(key, [{"host": "10.0.0.1", "port": "443"}, {"host": "10.0.0.2", "port": "443"}])
    egress.collect(key, [{"host": "10.0.0.3", "port": "8443"}], {"10.0.0.3": ["pom.xml"]})
    app = launcher.App(tmp_path / "work", environment={})
    server = app.serve(token="t")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        port = server.server_address[1]
        assert request(port, "/api/app/state")[1]["egress"] == []  # no checkout selected
        app.context = {"path": str(project), "run_id": "app-aaaaaaaaaaaa"}
        assert request(port, "/api/app/state")[1]["egress"] == [
            {"tool": "mise", "project": key, "requests": [
                {"host": "10.0.0.1", "port": "443", "address": "10.0.0.1", "network": True, "declared_in": []},
                {"host": "10.0.0.2", "port": "443", "address": "10.0.0.2", "network": True, "declared_in": []}]},
            {"tool": "", "project": key, "requests": [
                {"host": "10.0.0.3", "port": "8443", "address": "10.0.0.3", "network": True,
                 "declared_in": ["pom.xml"]}]}]
        group = {"hosts": ["10.0.0.1", "10.0.0.2"], "reply": "once"}
        assert request(port, "/api/app/egress", group, token=None)[0] == 403  # the guard: no token, no answer
        assert request(port, "/api/app/egress", {"hosts": ["10.0.0.9"], "reply": "once"})[0] == 400  # not asked
        assert request(port, "/api/app/egress", {"hosts": ["10.0.0.3"], "reply": "maybe"})[0] == 400
        assert egress.pending(key) and egress.session(key) == egress.new_session()
        status, told = request(port, "/api/app/egress", group)
        assert status == 200 and [g["tool"] for g in told["egress"]] == [""]
        assert egress.session(key)["allow"] == ["10.0.0.1", "10.0.0.2"]
        status, told = request(port, "/api/app/egress", {"hosts": ["10.0.0.3"], "reply": "block"})
        assert status == 200 and told["egress"] == [] and egress.load()["blacklist"] == ["10.0.0.3"]
    finally:
        app.close()
        server.shutdown()
        server.server_close()


def test_the_app_goes_from_an_address_to_a_run_and_says_its_state(tmp_path, monkeypatch):
    project = tmp_path / "checkout"
    project.mkdir()
    (project / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    found = {"host": "github.com", "owner": "o", "name": "n", "url": "https://github.com/o/n"}
    monkeypatch.setattr(repository, "checkout", lambda address, branch, work: {
        "repository": found, "branch": branch, "commit": "a" * 40, "path": str(project)})
    monkeypatch.setattr(launcher.App, "_warm", lambda self: setattr(self, "mcp_ready", "ready"))  # no download
    monkeypatch.setattr(launcher.App, "_follow", lambda self: None)  # the chain at the pass's end: its own tests
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
        # Selection prepares the run; the detached pass then attempts the scan's container commands.
        while time.monotonic() < deadline and (state["job"]["state"] == "preparing" or
                (state["job"]["state"] == "ready" and _modelling(state["run"]["plan"])
                 and state["run"]["pass"]["state"] == "running")):
            time.sleep(0.2)
            state = request(port, "/api/app/state")[1]
        assert state["job"] == {"state": "ready", "step": None, "detail": ""}
        assert state["context"]["run_id"] == "app-aaaaaaaaaaaa" and _modelled(state["run"]["plan"])
        # the run's one plan, as `codebase_map_status` gives it: the steps to the entry points are done
        import pipeline
        plan = state["run"]["plan"]
        assert [step["id"] for step in plan["steps"]] == list(pipeline.IDS)
        assert {step["id"]: step["state"] for step in plan["steps"]}["find_entry_points"] in ("done", "skipped")
        assert state["mcp"]["args"][-2:] == ["--project", project.parent.as_posix()]
        assert state["mcp"]["command"] == sys.executable  # its packages are the app's: no `uv` on the PATH
        # what Daodan writes about the checkout is beside it: a container's output may not be inside the project
        assert (project.parent / ".daodan").is_dir() and not (project / ".daodan").exists()
        # The page observes: the run's events from its start and the app's state, then again from the cursors.
        seen = stream(port, "run=app-000000000000&after=3&max_seconds=1")
        first = next(data for name, data in seen if name == "snapshot")["run_events"]
        assert first["run_id"] == "app-aaaaaaaaaaaa" and first["pipeline"]["events"][0]["kind"] == "step.started"
        told = [data for name, data in seen if name == "app"][-1]
        assert told["context"]["run_id"] == "app-aaaaaaaaaaaa" and _modelled(told["run"]["plan"])
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
        status, told = request(port, "/api/app/map", {})  # no engine is chosen: nothing is asked of the service
        assert status == 200 and told["mapped"]["state"] == "no_engine"
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


PROPOSAL = {"nodes": [{"name": "Prodotto", "type": "altro", "members": ["."]}], "flows": []}


class Flows:
    """The service's flows as the app reads them: the rule format until rules are recorded, then what they link, the
    system brief, and a map proposal recorded and reported; a rule without its link and a proposal without nodes are
    refused with the service's reason."""

    def __init__(self):
        self.rules, self.map, self.asked = None, None, []
        self.model_requests = []

    def reserve_question(self, run_id, question, budget=None):
        self.model_requests.append(question)

    def status(self, run_id):
        return {}

    def flows(self, run_id, rules=None, brief=False, map=None, next_question=False, shape_offset=None, limit=100):
        if shape_offset is not None:
            return {"questions": [], "count": 0}
        if next_question:
            return {"status": "complete", "count": 0, "remaining": 0, "reviewed": {}, "question": None}
        self.asked.append(("map", map) if map is not None else "brief" if brief else rules)
        if rules is not None:
            if any("link" not in rule for rule in rules):
                raise ValueError("rule 0: link must be one of scrive, legge, rotta, offre, attiva, ingresso")
            self.rules = rules
        if self.rules is None:
            return {"status": "needs_rules", "run_id": run_id, "format": "the rule format v1",
                    "technologies": [{"unit": "app/server", "technologies": ["flask"]}]}
        if brief:
            return {"status": "ok", "run_id": run_id, "brief": "the brief", "format": "the map format v1", "areas": []}
        if map is not None:
            if not map.get("nodes"):
                raise ValueError("a proposal names its nodes")
            self.map = map
            return {"status": "ok", "run_id": run_id, "nodes": [{"name": node["name"], "status": "accepted"}
                                                                for node in map["nodes"]], "flows": []}
        return {"status": "ok", "run_id": run_id, "entries": [], "entry_count": 0,
                "routes": {"offered": 2, "called": 2, "linked": 2}, "stores": {}, "store_count": 0, "gaps": [],
                "gap_count": 0, "external": []}

    def system_map(self, run_id):
        self.asked.append("system_map")
        if self.map is None:
            return {"status": "no_map", "run_id": run_id, "reason": "no system map is recorded: propose one with map"}
        return {"status": "ok", "run_id": run_id, "nodes": {"accepted": len(self.map["nodes"])}, "flows": {},
                "coverage": LEFT}


LEFT = {"entries": {"in": 0, "of": 1, "left": ["app/client.py::main"]}, "stores": {"in": 0, "of": 0, "left": []},
        "routes": {"in": 0, "of": 0, "left": []}}


def linking(tmp_path, environment=None):
    """An app on a selected run whose service is `Flows`."""
    app = launcher.App(tmp_path / "work", environment=environment or {})
    app.service, app.context = Flows(), {"run_id": "app-r", "path": str(tmp_path / "commit" / "source")}
    return app


def settled(app, held: str = "linked") -> dict:
    deadline = time.monotonic() + 60
    while getattr(app, held)["state"] == "running" and time.monotonic() < deadline:
        time.sleep(0.05)
    return getattr(app, held)


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


@pytest.mark.parametrize("action, held, shown", [("link", "linked", "links"), ("map", "mapped", "mapped")])
def test_the_links_and_the_map_run_once_at_a_time_and_stop_with_the_app(tmp_path, monkeypatch, action, held, shown):
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
    assert getattr(app, action)({})[shown]["state"] == "running"
    with pytest.raises(ValueError, match="wait"):
        getattr(app, action)({})
    with pytest.raises(ValueError, match="wait"):  # both write the link rules: the other waits too
        getattr(app, "map" if action == "link" else "link")({})
    with pytest.raises(ValueError, match="in progress"):
        app.select({"url": "https://github.com/o/n", "branch": "main"})
    app.close()
    engine.go.set()
    told = settled(app, held)
    assert len(engine.started) == 1 and told["state"] == "failed" and "stopped" in told["cause"]


def test_mapping_without_an_engine_says_what_to_do_and_writes_nothing(tmp_path):
    app = linking(tmp_path)
    told = app.map({})["mapped"]
    assert told["state"] == "no_engine" and "engine" in told["cause"]
    assert app.service.asked == ["system_map"] and not (tmp_path / "work" / "engine").exists()  # read, nothing written or run


def test_the_engine_records_a_map_through_the_flows_tool_and_the_service_says_its_nodes_flows_and_remainder(
        tmp_path, endpoint, monkeypatch):
    monkeypatch.setattr(Endpoint, "call", ("codebase_map_flows", json.dumps({"map": PROPOSAL})))
    app = linking(tmp_path, openai(endpoint))
    app.service.rules = [RULE]
    assert app.map({})["mapped"]["state"] == "running"
    assert settled(app, "mapped") == {"state": "done", "cause": None, "nodes": {"accepted": 1}, "flows": {},
                                      "left": LEFT}
    assert app.service.asked == ["system_map", ("map", PROPOSAL), "system_map"]  # none recorded, the proposal, the map
    first = Endpoint.seen[0][2]
    tool = next(tool["function"] for tool in first["tools"] if tool["function"]["name"] == "codebase_map_flows")
    assert set(tool["parameters"]["properties"]) == {"rules", "brief", "map", "about", "entry_offset", "limit",
                                                  "trace_id", "trace_offset", "trace_decision",
                                                  "shape_offset", "shape_answers", "next_question", "effect_offset"}
    task = first["messages"][-1]["content"]
    assert "app-r" in task and "`brief` true" in task and "needs_rules" in task and "«Sequence»" in task
    assert app.state({})["mapped"]["state"] == "done" and "sk-secret" not in json.dumps(app.state({}))


def test_the_service_says_the_recorded_map_in_counts_with_its_remainder_or_that_there_is_none(levels):
    import system_map
    assert levels.system_map("levels") == {"status": "no_map", "run_id": "levels",
                                           "reason": "no system map is recorded: propose one with map"}
    proposal = {"scope": ["funzioni principali"],
                "nodes": [{"name": "Cliente", "type": "attore", "position": "external", "evidence": ["web/api.ts"]},
                          {"name": "Web", "type": "applicazione", "members": ["web"]}],
                "flows": [{"name": "Ricerca di un cane", "area": "funzioni principali", "types": ["funzionale"],
                           "nodes": ["Cliente", "Web"], "arrows": [{"from": "Cliente", "to": "Web", "data": "a page",
                                                                     "kind": "attiva", "cite": "web/api.ts:4"}]}]}
    report = levels.flows("levels", map=proposal)
    written = levels.root / "runs" / "levels" / "snapshot" / system_map.FILE
    try:
        found = levels.system_map("levels")
        assert (found["status"], found["nodes"], found["flows"]) == ("ok", {"accepted": 2}, {"accepted": 1})
        assert found["reachability"] == {"not_declared": 1}
        assert found["coverage"] == report["coverage"] and found["coverage"]["entries"]["left"]  # what is left out
        assert "needs_review" not in found
        # A refused second step survives the write and the service reports the flow that needs another look.
        flow = proposal["flows"][0]
        flow["arrows"].append({**flow["arrows"][0], "cite": "web/api.ts:99999"})
        levels.flows("levels", map=proposal)
        assert levels.system_map("levels")["needs_review"] == {"flows": {"count": 1, "ids": ["ricerca-di-un-cane"]}}
        # A changed citation can also make an otherwise accepted node stale.
        stored = json.loads(written.read_text(encoding="utf-8"))
        next(n for n in stored["nodes"] if n["id"] == "cliente")["digests"]["web/api.ts"] = "previous-digest"
        written.write_text(json.dumps(stored), encoding="utf-8")
        assert levels.system_map("levels")["needs_review"]["nodes"] == {"count": 1, "ids": ["cliente"]}
    finally:
        written.unlink()  # the run is the module's: it goes on without a map


def test_a_question_runs_as_the_links_do_and_without_an_engine_is_refused(tmp_path, endpoint, monkeypatch):
    with pytest.raises(ValueError, match="no engine"):
        linking(tmp_path).ask({"question": "where?"})
    monkeypatch.setattr(Endpoint, "call", ("codebase_map_flows", "{}"))
    app = linking(tmp_path, openai(endpoint))
    assert app.ask({"question": "where?"}) == {"state": "running"}
    settled(app, "asked")
    found = app.answer({})
    assert (found["state"], found["question"], [event["kind"] for event in found["events"]]) == (
        "done", "where?", ["tool", "text", "text"])
    assert "needs_rules" in found["text"] and Endpoint.seen[0][2]["messages"][0]["content"] == launcher.SYSTEM


def test_a_refused_proposal_ends_the_map_with_the_service_s_cause(tmp_path, endpoint, monkeypatch):
    monkeypatch.setattr(Endpoint, "call", ("codebase_map_flows", json.dumps({"map": {"flows": []}})))
    app = linking(tmp_path, openai(endpoint))
    app.service.rules = [RULE]
    app.map({})
    told = settled(app, "mapped")
    assert told["state"] == "failed" and "a proposal names its nodes" in told["cause"]  # the service's own reason
    assert app.service.map is None


class Passing(Flows):
    """`Flows` with the selected run's pass: each `index` starts the next of `passes`, whose states are read in turn,
    the last one staying; with none left the pass stays as it is, as a fresh one does."""

    def __init__(self, *passes):
        super().__init__()
        self.passes, self.states = list(passes), ["missing"]

    def runs(self):
        return {"runs": [{"run_id": "app-aaaaaaaaaaaa"}]}

    def index(self, run_id):
        if self.passes:
            self.states = list(self.passes.pop(0))

    def status(self, run_id):
        return {"engine": {"state": self.states.pop(0) if len(self.states) > 1 else self.states[0], "reason": None}}


class Doing:
    """An engine that records through the flows tool what its task asks, rules for the links and a proposal for the
    map, or ends with `cause`; it keeps each task's first word and the links' state when the task began."""

    def __init__(self, app, cause=None):
        self.app, self.cause, self.started = app, cause, []

    def run(self, task, say, cancelled):
        word = task["prompt"].split()[0]
        self.started.append((word, self.app.linked["state"]))
        if self.cause:
            return {"state": "failed", "text": "", "session": None, "cause": self.cause}
        flows = next(tool["call"] for tool in task["tools"] if tool["name"] == "codebase_map_flows")
        flows({"rules": [RULE]} if word == "Write" else {"map": PROPOSAL})
        return {"state": "done", "text": "", "session": None, "cause": None}


def selecting(tmp_path, monkeypatch, service):
    """An app that selects a commit whose run's service is `service`, reading the pass and the work at short turns."""
    monkeypatch.setattr(launcher, "MapService", lambda root: service)
    monkeypatch.setattr(repository, "checkout", lambda address, branch, work: {
        "repository": {}, "branch": branch, "commit": "a" * 40, "path": str(tmp_path / "commit" / "source")})
    monkeypatch.setattr(launcher.App, "_warm", lambda self: None)
    monkeypatch.setattr(launcher, "RECHECK", 0.01)
    monkeypatch.setattr(launcher, "TURN", 0.01)
    return launcher.App(tmp_path / "work", environment={})


def ended(app, held: str) -> dict:
    """The work kept in `held` once it has started and ended."""
    deadline = time.monotonic() + 20
    while getattr(app, held)["state"] in ("idle", "running") and time.monotonic() < deadline:
        time.sleep(0.02)
    return getattr(app, held)


def quiet(query, should_stop):
    """The explorer's frame of a run without events."""
    return [("snapshot", {"run_events": {"events": [], "next_cursor": 0, "pipeline": {"events": [], "next_cursor": 0}},
                          "pulse": {"events": [], "next_cursor": 0}})]


def test_when_the_pass_ends_fresh_the_links_and_then_the_map_start_by_themselves_once(tmp_path, monkeypatch):
    service = Passing(("running", "running", "failed"), ("running", "fresh"))
    app = selecting(tmp_path, monkeypatch, service)
    engine = Doing(app)
    monkeypatch.setattr(engines, "configured", lambda chosen: engine)
    app._prepare("https://github.com/o/n", "main")  # the pass ends failed: nothing starts
    assert (engine.started, app.linked["state"], app.mapped["state"]) == ([], "idle", "idle")
    app.retry({})  # the pass starts again and ends fresh
    assert ended(app, "mapped") == {"state": "done", "cause": None, "nodes": {"accepted": 1}, "flows": {}, "left": LEFT}
    assert engine.started == [("Write", "running"), ("Map", "done")]  # the map once the links are found
    assert app.linked == {"state": "done", "cause": None, "routes": {"offered": 2, "called": 2, "linked": 2},
                          "stores": 0, "gaps": 0}
    read = list(service.asked)
    # reads of the state, a page that observes, the pass asked again and a second follower start nothing
    for _ in range(3):
        app.state({})
    assert [name for name, _ in app.stream(quiet)({"run": "app-aaaaaaaaaaaa", "max_seconds": "0.3"}, lambda: False)]
    app.retry({})
    app._follow()
    assert len(engine.started) == 2 and service.asked == read


def test_with_the_rules_and_a_map_recorded_for_the_snapshot_no_engine_is_asked_again(tmp_path, monkeypatch):
    service = Passing(("fresh",))
    service.rules, service.map = [RULE], PROPOSAL
    app = selecting(tmp_path, monkeypatch, service)
    engine = Doing(app)
    monkeypatch.setattr(engines, "configured", lambda chosen: engine)
    app._prepare("https://github.com/o/n", "main")
    assert ended(app, "mapped") == {"state": "done", "cause": None, "nodes": {"accepted": 1}, "flows": {}, "left": LEFT}
    assert app.linked["state"] == "done" and engine.started == []
    assert service.asked == [None, "system_map"]  # what is recorded is read, nothing is written


@pytest.mark.parametrize("unresolved", [False, True])
def test_a_stale_record_gets_one_automatic_recheck_and_the_result_is_visible(tmp_path, monkeypatch, unresolved):
    service = Passing(("fresh",))
    service.rules, service.map = [RULE], PROPOSAL
    app = selecting(tmp_path, monkeypatch, service)
    engine = Doing(app)
    monkeypatch.setattr(engines, "configured", lambda chosen: engine)
    original = service.system_map
    pending = {"flows": {"count": 1, "ids": ["payment"]}}

    def recorded(run_id):
        answer = original(run_id)
        if not engine.started or unresolved:
            answer["needs_review"] = pending
        return answer

    monkeypatch.setattr(service, "system_map", recorded)
    app._prepare("https://github.com/o/n", "main")
    result = ended(app, "mapped")
    if unresolved:
        assert result["state"] == "incomplete" and result["needs_review"] == pending and result["cause"]
    else:
        assert result["state"] == "done" and "needs_review" not in result
    app._follow()
    assert engine.started == [("Review", "done")]


def test_an_existing_partial_map_keeps_its_review_counts_without_an_engine(tmp_path, monkeypatch):
    service = Passing(("fresh",))
    service.rules, service.map = [RULE], PROPOSAL
    app = selecting(tmp_path, monkeypatch, service)
    original = service.system_map
    pending = {"flows": {"count": 1, "ids": ["payment"]}}
    monkeypatch.setattr(service, "system_map", lambda run: {**original(run), "needs_review": pending})
    app._prepare("https://github.com/o/n", "main")
    result = ended(app, "mapped")
    assert result["state"] == "no_engine" and result["needs_review"] == pending
    assert "set the engine" in result["cause"]


def test_without_an_engine_the_state_says_the_part_left_uncovered_its_cause_and_the_remedy(tmp_path, monkeypatch):
    app = selecting(tmp_path, monkeypatch, Passing(("running", "fresh")))
    app._prepare("https://github.com/o/n", "main")
    told = app.state({})
    assert told["links"]["state"] == told["mapped"]["state"] == "no_engine"
    cause = told["mapped"]["cause"]
    assert "the links are not found" in cause and "no engine is chosen" in cause and "set the engine" in cause
    assert app.service.asked == [None] and not (tmp_path / "work" / "engine").exists()  # the map is not started


def test_links_that_are_not_found_leave_the_map_not_started_with_their_cause(tmp_path, monkeypatch):
    service = Passing(("fresh",))
    app = selecting(tmp_path, monkeypatch, service)
    engine = Doing(app, cause="the model is not reached")
    monkeypatch.setattr(engines, "configured", lambda chosen: engine)
    app._prepare("https://github.com/o/n", "main")
    assert ended(app, "mapped") == {"state": "failed", "cause": "the links are not found: the model is not reached"}
    assert app.linked == {"state": "failed", "cause": "the model is not reached"}
    assert engine.started == [("Write", "running")] and "system_map" not in service.asked


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
    app.marks.entries["packaged.example"] = {"id": "packaged.example", "mark": None,
                                             "mark_source": {"url": "https://owner.example/icons.zip"}}
    server = app.serve(token="t")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        port = server.server_address[1]
        stripe = (service_registry.REGISTRY.parent / "marks/stripe.svg").read_bytes()
        assert raw(port, "/api/app/mark?id=stripe&token=t") == (200, "image/svg+xml", stripe)
        assert raw(port, "/api/mark?id=stripe&token=t") == (200, "image/svg+xml", stripe)  # the map's page, on the same server
        assert raw(port, "/api/app/mark?id=stripe")[0] == 403
        for wrong in ("nope", "marks/stripe.svg", "../data/marks/stripe.svg", ""):
            assert raw(port, f"/api/app/mark?id={wrong}&token=t")[0] == 400, wrong
        assert raw(port, "/api/app/mark?token=t")[0] == 400
        assert raw(port, "/api/mark?id=nope&token=t")[0] == 404 and raw(port, "/api/mark?id=stripe")[0] == 403
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
            return {"plan": {"steps": [{"id": "find_modules", "state": "done"}]}, "progress": None,
                    "engine": {"state": "fresh", "reason": None}}

    monkeypatch.setattr(launcher, "TURN", 0.01)
    app = launcher.App(tmp_path / "work", environment={})
    app.service, app.context = Service(), {"run_id": "r", "path": str(tmp_path / "checkout")}
    frames = list(app.stream(quiet)({"run": "r", "max_seconds": "1"}, lambda: False))
    assert [name for name, _ in frames] == ["app", "snapshot"] and Service.asked == 2
    assert frames[0][1]["run"]["plan"] == {"steps": [{"id": "find_modules", "state": "done"}]}
    assert "pipeline" not in frames[0][1]["run"]

    def refused(query):
        raise busy()

    server = visual.make_server(None, tmp_path, routes={"/api/app/graph": refused}, token="t")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        assert request(server.server_address[1], "/api/app/graph") == (503, {"error": str(busy())})
    finally:
        server.shutdown()
        server.server_close()


def test_entry_questions_resume_after_the_run_budget_with_one_context_per_event(tmp_path, monkeypatch):
    import mcp_service
    import secret_mask
    project = tmp_path / "shop"
    project.mkdir()
    (project / "View.tsx").write_text(
        'function save() {}\nfunction close() {}\n'
        'export function View() { return <main>\n'
        '<button onClick={save}>SecretFixture Salva</button>\n'
        '<button onClick={close}>SecretFixture Chiudi</button>\n</main> }\n', encoding="utf-8")
    git(project, "init", "-q")
    service = mcp_service.MapService(project)
    service.create_run(".", "events", engine=False)
    service.flows("events", rules=[])
    app = launcher.App(tmp_path / "work", environment={})
    app.service, app.context = service, {"run_id": "events", "path": str(project)}
    prompts = []

    class Engine:
        def run(self, task, say, cancelled):
            prompts.append(task["prompt"])
            return {"state": "done", "cause": None,
                    "text": json.dumps({"disposition": "unresolved", "reason": "no evidence after the handler"})}

    monkeypatch.setattr(engines, "configured", lambda _: Engine())
    monkeypatch.setattr(secret_mask, "masked", lambda text, name: {
        "text": text.replace("SecretFixture", "*************"), "found": text.count("SecretFixture"), "kinds": []})
    try:
        app.map({"question_budget": 1})
        first = settled(app, "mapped")
        assert first["state"] == "incomplete" and "budget" in first["cause"]
        assert first["discovery"]["remaining"] == 1 and first["discovery"]["reviewed"]["unresolved"] == 1
        app.service = mcp_service.MapService(project)
        app.map({})
        assert "budget" in settled(app, "mapped")["cause"] and len(prompts) == 1
        app.map({"question_budget": 2})
        last = settled(app, "mapped")["discovery"]
        assert last["remaining"] == 0 and last["reviewed"]["unresolved"] == 2
        assert len(prompts) == 2 and prompts[0] != prompts[1]
        assert all("SecretFixture" not in prompt and "*************" in prompt for prompt in prompts)
    finally:
        app.close()


def test_last_accepted_event_still_requests_the_system_structure_once(tmp_path, monkeypatch):
    app = linking(tmp_path)
    tasks = []

    class Service(Flows):
        answered = structured = False

        def system_map(self, run_id):
            return {"status": "ok", "nodes": {}, "flows": {"accepted": 1}, "coverage": LEFT,
                    "needs_structure": self.answered and not self.structured}

        def flows(self, run_id, **options):
            if "shape_offset" in options:
                return {"count": 0, "questions": []}
            if "trace_id" in options:
                return {"steps": []}
            if "trace_decision" in options:
                self.answered = True
                return {"status": "accepted"}
            assert options == {"next_question": True}
            return {"status": "complete" if self.answered else "pending", "count": 1,
                    "remaining": int(not self.answered), "reviewed": {"unresolved": 0},
                    "question": None if self.answered else {"card_id": "button"}}

        def reserve_question(self, run, question, budget):
            assert question == ("system-map" if self.answered else "button")

    class Engine:
        def run(self, task, say, cancelled):
            tasks.append(task["prompt"])
            if len(tasks) == 2:
                assert "whole-system structure" in task["prompt"]
                app.service.structured = True
            return {"state": "done", "text": "{}", "cause": None}

    app.service = Service()
    monkeypatch.setattr(engines, "configured", lambda _: Engine())
    try:
        app.map({})
        assert settled(app, "mapped")["state"] == "done"
        app.map({})
        assert settled(app, "mapped")["state"] == "done" and len(tasks) == 2
    finally:
        app.close()


def test_the_app_classifies_one_form_once_for_two_callbacks_and_keeps_the_rule(tmp_path, monkeypatch):
    import mcp_service
    project = tmp_path / "panel"
    project.mkdir()
    (project / "panel.py").write_text(
        "def subscribe(callback): pass\ndef save(): pass\ndef cancel(): pass\nsubscribe(save)\nsubscribe(cancel)\n",
        encoding="utf-8")
    git(project, "init", "-q")
    service = mcp_service.MapService(project)
    service.create_run(".", "panel", engine=False)
    service.flows("panel", rules=[])
    form = service.flows("panel", shape_offset=0)
    assert len(form["questions"]) == 1 and form["questions"][0]["count"] == 2
    app = launcher.App(tmp_path / "work", environment={})
    app.service, app.context = service, {"run_id": "panel", "path": str(project)}
    decisions = []

    class Engine:
        def run(self, task, say, cancelled):
            if "Classify this code shape" in task["prompt"]:
                decision = {"kind": "controllo dell'interfaccia"}
            else:
                decision = {"disposition": "unresolved", "reason": "handler has no outgoing evidence"}
            decisions.append(decision)
            return {"state": "done", "cause": None, "text": json.dumps(decision)}

    monkeypatch.setattr(engines, "configured", lambda _: Engine())
    try:
        app.map({})
        state = settled(app, "mapped")
        assert state["discovery"]["reviewed"]["unresolved"] == 2
        assert [list(item)[0] for item in decisions] == ["kind", "disposition", "disposition"]
        service.flows("panel", rules=[])
        restored = mcp_service.MapService(project)
        assert restored.flows("panel", shape_offset=0)["count"] == 0
        assert restored.flows("panel", next_question=True)["remaining"] == 0
    finally:
        app.close()


def test_zero_budget_also_stops_the_first_structural_question_after_reopening(tmp_path, monkeypatch):
    import mcp_service
    project = tmp_path / "repo"
    project.mkdir()
    (project / "lib.py").write_text("def utility(): pass\n", encoding="utf-8")
    git(project, "init", "-q")
    app = launcher.App(tmp_path / "work", environment={})
    app.service, app.context = mcp_service.MapService(project), {"run_id": "empty", "path": str(project)}
    app.service.create_run(".", "empty", engine=False)
    app.service.flows("empty", rules=[])
    asked = []

    class Engine:
        def run(self, task, say, cancelled):
            asked.append(task["prompt"])
            return {"state": "done", "cause": None, "text": ""}

    monkeypatch.setattr(engines, "configured", lambda _: Engine())
    try:
        for options in ({"question_budget": 0}, {}):
            app.service = mcp_service.MapService(project)
            app.map(options)
            assert "budget exhausted" in settled(app, "mapped")["cause"]
        assert asked == []
    finally:
        app.close()


def test_existing_map_reports_an_orphan_write_without_any_classified_entry(tmp_path):
    import mcp_service
    project = tmp_path / "repo"
    project.mkdir()
    (project / "lib.py").write_text("def write(key): pass\ndef worker(): write('orders')\n", encoding="utf-8")
    git(project, "init", "-q")
    service = mcp_service.MapService(project)
    service.create_run(".", "orphan", engine=False)
    service.flows("orphan", rules=[{"callee": "lib.py::write", "link": "scrive", "store": "db", "key": "arg0"}])
    service.flows("orphan", map={**PROPOSAL, "scope": ["funzioni principali"]})
    app = launcher.App(tmp_path / "work", environment={})
    app.service, app.context = mcp_service.MapService(project), {"run_id": "orphan", "path": str(project)}
    try:
        state = app.map({})["mapped"]
        assert state["state"] == "incomplete", state
        assert state["discovery"]["count"] == 0
        assert state["discovery"]["effect_coverage"] == {"without_entry": 1, "writes": 1, "reached": 0}
    finally:
        app.close()


def test_review_accepts_tool_then_text_once_per_question(tmp_path):
    import flow_questions
    import mcp_service
    project = tmp_path / "repo"
    project.mkdir()
    (project / "panel.py").write_text("def subscribe(callback): pass\ndef save(): pass\nsubscribe(save)\n")
    git(project, "init", "-q")
    service = mcp_service.MapService(project)
    service.create_run(".", "queue", engine=False)
    service.flows("queue", rules=[])
    review = flow_questions.Review(service, "queue")
    assert "Classify" in review.prompt()
    question_id, row = review.shape
    service.flows("queue", shape_offset=0, limit=1,
                  shape_answers={"id": question_id, "answers": {row: "controllo dell'interfaccia"}})
    assert "numbered step" in review.advance({"text": '{"kind":"controllo dell\'interfaccia"}'})
    decision = {"card_id": review.current, "disposition": "unresolved", "reason": "no write proved"}
    assert service.flows("queue", trace_decision=decision)["status"] == "unresolved"
    assert review.advance({"text": '{"disposition":"excluded","reason":"late text"}'}) is None
    assert review.counts["reviewed"] == {"accepted": 0, "excluded": 0, "unresolved": 1}


def test_graph_keeps_a_conflicting_call_at_the_twenty_first_site():
    relations = {}
    for line in range(1, 22):
        call = {"confidence": "observed", "file": "a.py", "span": [line],
                **({"conflict": True} if line == 21 else {})}
        visual._call(relations, "file:a.py", "file:b.py", call)
    owners = {"file:a.py": "source", "file:b.py": "target"}
    grouped = app_view._edges(list(relations.values()), set(owners.values()), owners)
    certain, disputed = sorted(grouped, key=lambda e: bool(e.get("conflict")))
    assert certain["counts"]["calls"] == len(certain["evidence"]) == 20
    assert disputed["status"] == "observed" and disputed["counts"]["calls"] == 1
    assert disputed["conflict"] and disputed["evidence"][0]["line"] == 21


def payments(linked: bool) -> dict:
    """The spec's case («Seguire un flusso attraverso i gruppi»): the frontend calls A, B writes the ledger; A and B
    are «Pagamenti»; with `linked`, A calls B."""
    def entity(ref, kind, **fields):
        return {"ref": ref, "type": kind, "name": ref.split(":", 1)[1], **fields}

    def step(source, target, kind, site):
        return {"source": source, "target": target, "type": kind, "origin": "statico", "site": site}

    submit, charge, record = "symbol:web/app.ts::submit", "symbol:pay/a.py::charge", "symbol:pay/b.py::record"
    first = [step(submit, charge, "chiama", "web/app.ts:3")]
    writes = [step(record, "store:ledger", "scrive", "pay/b.py:5")]
    flows = [{"ref": "flow:submit", "entry": submit, "complete": True, "gaps": [],
              "steps": first + ([step(charge, record, "chiama", "pay/a.py:2")] + writes if linked else [])},
             {"ref": "flow:record", "entry": record, "complete": True, "gaps": [], "steps": writes}]
    return {"entities": [entity("build:web", "build"), {**entity("build:pay", "build"), "name": "Pagamenti"},
                         *[entity(f"file:{path}", "file", path=path) for path in ("web/app.ts", "pay/a.py", "pay/b.py")],
                         entity(submit, "symbol"), entity(charge, "symbol"), entity(record, "symbol"),
                         entity("store:ledger", "store")],
            "relations": [{"ref": "calls:file:web/app.ts->file:pay/a.py", "kind": "calls", "source": "file:web/app.ts",
                           "target": "file:pay/a.py", "status": "confirmed", "counts": {"calls": 1},
                           "evidence": [{"path": "web/app.ts", "line": 3}]},
                          *([{"ref": "calls:file:pay/a.py->file:pay/b.py", "kind": "calls", "source": "file:pay/a.py",
                              "target": "file:pay/b.py", "status": "confirmed", "counts": {"calls": 1},
                              "evidence": [{"path": "pay/a.py", "line": 2}]}] if linked else [])],
            "memberships": [{"member": "file:web/app.ts", "group": "build:web", "view": "physical"},
                            {"member": "file:pay/a.py", "group": "build:pay", "view": "physical"},
                            {"member": "file:pay/b.py", "group": "build:pay", "view": "physical"}],
            "gaps": [], "meta": {}, "technologies": [], "flows": flows}


def test_a_flow_through_a_closed_group_shows_its_two_dependencies_and_the_path_left_to_prove():
    envelope = payments(linked=False)
    arrow, = app_view.view(envelope)["edges"]
    assert (arrow["id"], arrow["relations"]) == ("build:web->build:pay", ["calls:file:web/app.ts->file:pay/a.py"])
    found = app_view.flow(envelope, "flow:submit")
    step, = found["steps"]
    assert (step["n"], step["parent"], step["source"], step["target"]) == (1, None, "build:web", "build:pay")
    assert step["relation"]["target"] == "symbol:pay/a.py::charge" and step["proof"] == [{"path": "web/app.ts", "line": 3}]
    assert "condition" not in step and "profile" not in step  # no source gives them
    web = {"id": "build:web", "name": "web", "entries": [], "exits": [{"step": 1, "end": "symbol:web/app.ts::submit"}]}
    assert found["groups"] == [{"id": "build:pay", "name": "Pagamenti",
                                "entries": [{"step": 1, "end": "symbol:pay/a.py::charge"}], "exits": []}, web]
    # «Pagamenti» closed: in from the frontend, out to the ledger, and nothing inside joins A to B
    path, = found["to_prove"]
    assert (path["group"], path["from"], path["to"], path["enters"], path["leaves"]) == (
        "build:pay", "build:web", "store:ledger", ["symbol:pay/a.py::charge"], ["symbol:pay/b.py::record"])
    # open, each step shows its files, and no closed group is left to cross
    opened = app_view.flow(envelope, "flow:submit", ("build:pay",))
    assert [(item["source"], item["target"]) for item in opened["steps"]] == [("build:web", "file:pay/a.py")]
    assert opened["to_prove"] == []
    with pytest.raises(ValueError, match="flow:nothing"):
        app_view.flow(envelope, "flow:nothing")


def test_with_the_arc_inside_the_group_the_flow_through_it_is_proved_step_by_step():
    found = app_view.flow(payments(linked=True), "flow:submit")
    assert [(item["n"], item["parent"], item["source"], item["target"]) for item in found["steps"]] == [
        (1, None, "build:web", "build:pay"), (2, 1, "build:pay", "build:pay"), (3, 2, "build:pay", "store:ledger")]
    assert found["groups"] == [{"id": "build:pay", "name": "Pagamenti",
                                "entries": [{"step": 1, "end": "symbol:pay/a.py::charge"}],
                                "exits": [{"step": 3, "end": "symbol:pay/b.py::record"}]},
                               {"id": "build:web", "name": "web", "entries": [],
                                "exits": [{"step": 1, "end": "symbol:web/app.ts::submit"}]}]
    assert found["to_prove"] == []
    opened = app_view.view(payments(linked=True), ("build:pay",))
    inside, = [edge for edge in opened["edges"] if edge["source"] == "file:pay/a.py"]
    assert inside["relations"] == ["calls:file:pay/a.py->file:pay/b.py"]


def natured() -> dict:
    """Two modules, a gateway that calls one, the service it uses, and «Tecnologie» holding what the other uses."""
    def entity(ref, kind, **fields):
        return {"ref": ref, "type": kind, "name": ref.split(":", 1)[1], **fields}

    def relation(kind, source, target, line):
        return {"ref": f"{kind}:{source}->{target}", "kind": kind, "source": source, "target": target,
                "status": "confirmed", "counts": {kind: 1}, "evidence": [{"path": "api/main.py", "line": line}]}

    return {"entities": [entity("build:api", "build"), entity("build:web", "build"),
                         *[entity(f"file:{path}", "file", path=path) for path in ("api/main.py", "web/app.ts")],
                         entity("external:gateway", "external", location="external", node_type="gateway"),
                         entity("external:stripe", "external", location="external", node_type="servizio o API"),
                         entity("technology:react", "technology", location="external"),
                         {**entity("group:technologies", "group"), "name": "Tecnologie"}],
            "relations": [relation("calls", "external:gateway", "build:api", 1),
                          relation("uses", "file:api/main.py", "external:stripe", 2),
                          relation("imports", "file:web/app.ts", "file:api/main.py", 3),
                          relation("uses", "build:web", "technology:react", 4)],
            "memberships": [{"member": "file:api/main.py", "group": "build:api", "view": "physical"},
                            {"member": "file:web/app.ts", "group": "build:web", "view": "physical"},
                            {"member": "technology:react", "group": "group:technologies", "view": "logical"}],
            "gaps": [], "meta": {}, "technologies": []}


def test_opening_closing_and_filtering_in_any_order_give_the_same_view():
    envelope = natured()
    for mode in app_view.MODES:
        first = app_view.view(envelope, ("build:api", "group:technologies"), natures=["fisico", "codice"], mode=mode)
        second = app_view.view(envelope, ("group:technologies", "build:api", "build:api"), natures=["codice", "fisico"],
                               mode=mode)
        assert first == second and first["natures"] == ["codice", "fisico"]
        # closing a group is the view without it, whatever was opened or filtered before
        assert app_view.view(envelope, ("build:api",), natures=["codice"], mode=mode) == app_view.view(
            envelope, ("build:api",), natures=["codice"], mode=mode)
    with pytest.raises(ValueError, match="mode"):
        app_view.view(envelope, mode="fade")


def test_hiding_keeps_the_nodes_of_the_natures_and_an_arrow_through_a_hidden_one_keeps_its_steps():
    envelope = natured()
    found = app_view.view(envelope, natures=["logico"], mode="hide")
    assert [node["id"] for node in found["nodes"]] == ["external:gateway", "external:stripe"]
    arrow, = found["edges"]
    assert (arrow["id"], arrow["source"], arrow["target"], arrow["status"], arrow["through"]) == (
        "external:gateway->external:stripe via", "external:gateway", "external:stripe", "confirmed", ["build:api"])
    assert [step["id"] for step in arrow["steps"]] == ["external:gateway->build:api", "build:api->external:stripe"]
    assert arrow["relations"] == ["calls:external:gateway->build:api", "uses:file:api/main.py->external:stripe"]
    assert [site["line"] for site in arrow["evidence"]] == [1, 2] and arrow["counts"] == {"calls": 1, "uses": 1}
    # the filter never opens a group, and an open one shows only the children it admits
    opened = app_view.view(envelope, ("build:api",), natures=["logico"], mode="hide")
    assert [group["id"] for group in opened["open"]] == ["build:api"]
    assert [node["id"] for node in opened["nodes"]] == ["external:gateway", "external:stripe"]
    code = app_view.view(envelope, ("build:api",), natures=["codice"], mode="hide")
    assert {node["id"] for node in code["nodes"]} == {"build:web", "file:api/main.py", "group:technologies"}
    assert app_view.view(envelope, natures=["persone", "logico"], mode="hide")["absent"] == ["persone"]


def test_highlighting_dims_the_others_and_lights_a_closed_group_with_how_many_it_holds():
    envelope = natured()
    whole = app_view.view(envelope)
    found = app_view.view(envelope, natures=["logico"])
    assert [node["id"] for node in found["nodes"]] == [node["id"] for node in whole["nodes"]]
    assert found["edges"] == whole["edges"] and found["absent"] == []
    assert {node["id"] for node in found["nodes"] if node.get("dim")} == {"build:api", "build:web", "group:technologies"}
    code = {node["id"]: node for node in app_view.view(envelope, natures=["codice"])["nodes"]}
    assert {ref: node.get("lit") for ref, node in code.items() if node.get("lit")} == {
        "build:api": 1, "build:web": 1, "group:technologies": 1}
    assert {ref for ref, node in code.items() if node.get("dim")} == {"external:gateway", "external:stripe"}


def test_a_large_group_opens_in_blocks_with_a_node_for_the_others_and_loses_no_child():
    paths = [f"big/f{index:03}.py" for index in range(700)]
    envelope = {"entities": [{"ref": "build:big", "type": "build", "name": "big"},
                             {"ref": "build:small", "type": "build", "name": "small"},
                             *({"ref": f"file:{path}", "type": "file", "name": path.split("/")[-1], "path": path}
                               for path in [*paths, "small/s.py"])],
                "relations": [{"ref": "imports:file:small/s.py->file:big/f650.py", "kind": "imports",
                               "source": "file:small/s.py", "target": "file:big/f650.py", "status": "confirmed",
                               "evidence": []}],
                "memberships": [*({"member": f"file:{path}", "group": "build:big", "view": "physical"} for path in paths),
                                {"member": "file:small/s.py", "group": "build:small", "view": "physical"}],
                "gaps": [], "meta": {}, "technologies": []}
    blocks = ("build:big", "more:build:big#1", "more:build:big#2")
    for opened, count, left, target in ((1, 300, 400, "more:build:big#1"), (2, 600, 100, "more:build:big#2"),
                                        (3, 700, 0, "file:big/f650.py")):
        found = app_view.view(envelope, blocks[:opened])
        shown = [node for node in found["nodes"] if node["kind"] == "file"]
        assert [node["name"] for node in shown] == [path.split("/")[-1] for path in paths[:count]]
        assert {node["group"] for node in shown} == {"build:big"} and [item["id"] for item in found["open"]] == ["build:big"]
        more = [node for node in found["nodes"] if node["kind"] == "more"]
        assert [(node["name"], len(node["files"])) for node in more] == ([(f"altri {left}", left)] if left else [])
        assert len(shown) + sum(len(node["files"]) for node in more) == 700
        assert [edge["target"] for edge in found["edges"]] == [target]
    # the filter and the blocks together: the node for the others holds files of the code, and no physical node
    lit = {node["id"]: node for node in app_view.view(envelope, ("build:big",), natures=["codice"])["nodes"]}
    assert lit["more:build:big#1"]["lit"] == 400 and "dim" not in lit["more:build:big#1"]
    hidden = app_view.view(envelope, ("build:big",), natures=["fisico"], mode="hide")
    assert (hidden["nodes"], hidden["absent"]) == ([], ["fisico"])
    with pytest.raises(ValueError, match="more:build:big#2"):
        app_view.view(envelope, ("build:big", "more:build:big#2"))
