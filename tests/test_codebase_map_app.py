"""The standalone app: a public repository's checkout, the engines' contract and the launcher's routes.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_app.py

No network, no model and no login: the repository is a local one Git serves from a folder, the endpoint is a
server of this test, and a command-line engine is a script that prints the events its real one prints.
"""
from __future__ import annotations

import http.client
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
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
    assert path.name == commit == git(origin, "rev-parse", "HEAD") and (path / "a.py").read_text() == "x = 1\n"
    assert repository._clone(origin.as_uri(), "main", work / "r", work, transports=("file",))[0] == path  # reused
    assert [item.name for item in (work / "r").iterdir()] == [commit]
    with pytest.raises(ValueError):
        repository._clone(origin.as_uri(), "--upload-pack=x", work / "r", work, transports=("file",))


class Endpoint(BaseHTTPRequestHandler):
    """Chat Completions, streamed: a call of the first tool offered, then the tool's answer as the text."""
    seen: list = []

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Endpoint.seen.append((self.path, self.headers.get("Authorization"), body))
        last = body["messages"][-1]
        if last["role"] == "tool":
            chunks = [{"delta": {"content": last["content"][:5]}}, {"delta": {"content": last["content"][5:]}}]
        else:
            name = body["tools"][0]["function"]["name"]
            chunks = [{"delta": {"tool_calls": [{"index": 0, "id": "c1", "function": {"name": name, "arguments": '{"val'}}]}},
                      {"delta": {"tool_calls": [{"index": 0, "function": {"arguments": 'ue": "w"}'}}]}}]
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
                "gaps": [], "meta": {}}
    found = app_view.graph(envelope)
    assert (found["level"], found["files"], found["symbols"]) == ("modules", 3, 1)
    assert {node["id"]: node["files"] for node in found["nodes"]} == {"build:app": ["app/main.py"],
                                                                      "build:lib": ["app/lib/util.py"]}
    assert [(edge["id"], edge["counts"]) for edge in found["edges"]] == [("build:app->build:lib", {"imports": 1, "calls": 3})]
    assert found["unassigned"] == {"count": 1, "areas": [("docs", 1)]}
    alone = app_view.graph({**envelope, "entities": [item for item in envelope["entities"] if item["ref"] != "build:lib"]})
    assert alone["level"] == "directories" and alone["unassigned"]["count"] == 0
    assert {node["id"]: node["files"] for node in alone["nodes"]} == {
        "directory:app": ["app/main.py"], "directory:app/lib": ["app/lib/util.py"], "directory:docs": ["docs/a.md"]}
    assert [(edge["id"], edge["counts"]) for edge in alone["edges"]] == [("directory:app->directory:app/lib", {"imports": 1})]


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
        assert request(port, "/api/app/select", {"url": "https://example.com/o/n", "branch": "main"})[0] == 400
        status, state = request(port, "/api/app/select", {"url": found["url"], "branch": "main"})
        assert status == 200 and state["job"]["state"] in ("preparing", "ready")
        deadline = time.monotonic() + 120
        while state["job"]["state"] == "preparing" and time.monotonic() < deadline:
            time.sleep(0.2)
            state = request(port, "/api/app/state")[1]
        assert state["job"] == {"state": "ready", "step": None, "detail": ""}
        assert state["context"]["run_id"] == "app-aaaaaaaaaaaa" and state["run"]["pipeline"]["scan"] == "fresh"
        assert state["mcp"]["args"][-2:] == ["--project", project.as_posix()]
        assert [run["run_id"] for run in request(port, "/api/runs")[1]["runs"]] == ["app-aaaaaaaaaaaa"]
        premap = request(port, "/api/app/premap")[1]
        assert premap["files"] == ["a.py"] and premap["languages"] == [{"name": "Python", "files": 1}]
        drawn = request(port, "/api/app/graph")[1]
        assert drawn["files"] == 1 and sum(len(node["files"]) for node in drawn["nodes"]) == 1
        described = request(port, "/api/app/engine", {"engine": "openai", "model": "m", "api_key": "sk-secret"})[1]
        assert described["api_key"] == "set" and "sk-secret" not in json.dumps(request(port, "/api/app/state")[1])
        assert request(port, "/api/app/engine", {"engine": "other"})[0] == 400
        assert request(port, "/api/app/ask", {"question": " "})[0] == 400
    finally:
        app.close()
        server.shutdown()
        server.server_close()
