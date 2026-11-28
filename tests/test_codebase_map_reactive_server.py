"""Task 4: Non-blocking reactive server — `create_run`, `PostToolUse` hook (`refresh_working`), MCP `codebase_map_stack`, and UI HTTP `/api/modules`, `/api/stack`, `/api/events`, `/api/stream` (SSE)."""
from __future__ import annotations

import asyncio
import http.client
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import types
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import mcp_service  # noqa: E402
import pipeline  # noqa: E402
import snapshot  # noqa: E402
import visual  # noqa: E402


def _load_mcp_server():
    if importlib.util.find_spec("mcp") is not None:
        import mcp_server
        return mcp_server
    fake_anyio = types.ModuleType("anyio")
    fake_to_thread = types.ModuleType("anyio.to_thread")
    async def run_sync(fn):
        return fn()
    fake_to_thread.run_sync = run_sync
    fake_anyio.to_thread = fake_to_thread

    class FakeMCPServer:
        def __init__(self, name):
            self.name = name
            self._tools = {}
            self._resources = {}
        def tool(self, **_kw):
            def reg(fn):
                self._tools[fn.__name__] = fn
                return fn
            return reg
        def resource(self, uri, **_kw):
            def reg(fn):
                self._resources[uri] = fn
                return fn
            return reg
        async def list_tools(self):
            return [types.SimpleNamespace(name=k) for k in self._tools]
        async def call_tool(self, name, args):
            class Ctx:
                session = None
                async def report_progress(self, *_a, **_kw):
                    return None
            return await self._tools[name](Ctx(), **args)

    fake_mcp = types.ModuleType("mcp")
    fake_srv_pkg = types.ModuleType("mcp.server")
    fake_srv_pkg.MCPServer = FakeMCPServer
    fake_mcpsrv = types.ModuleType("mcp.server.mcpserver")
    fake_mcpsrv.Context = object
    fake_exc = types.ModuleType("mcp.server.mcpserver.exceptions")
    fake_exc.ToolError = RuntimeError
    fake_types = types.ModuleType("mcp.types")
    fake_types.ToolAnnotations = lambda **kw: kw
    with mock.patch.dict(sys.modules, {
        "anyio": fake_anyio, "anyio.to_thread": fake_to_thread,
        "mcp": fake_mcp, "mcp.server": fake_srv_pkg,
        "mcp.server.mcpserver": fake_mcpsrv,
        "mcp.server.mcpserver.exceptions": fake_exc,
        "mcp.types": fake_types,
    }):
        sys.modules.pop("mcp_server", None)
        import mcp_server
        return mcp_server


def _modelling(plan: dict) -> bool:
    """A source of `find_modules` still waits for the pass to run its model commands (`pending` with `model_not_run`)."""
    return any(action["step"] == "find_modules" and action["state"] == "pending" and action.get("gap") == "model_not_run"
               for action in plan["actions"])


def _modelled(plan: dict) -> bool:
    """The step `find_modules` of the plan is done, or up to date."""
    return {step["id"]: step["state"] for step in plan["steps"]}["find_modules"] in ("done", "skipped")


def _make_project(root: Path) -> Path:
    files = {
        "api/pom.xml": (
            '<project xmlns="http://maven.apache.org/POM/4.0.0">'
            "<parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId></parent>"
            "<groupId>com.acme</groupId><artifactId>api</artifactId>"
            "<dependencies><dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId></dependency>"
            "<dependency><groupId>com.acme.lib</groupId><artifactId>billing-sdk</artifactId></dependency></dependencies>"
            "</project>\n"
        ),
        "api/src/main/java/com/acme/Main.java": "package com.acme;\npublic class Main {}\n",
        "scripts/cron.py": "def tick():\n    return 1\n",
    }
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def _run_mcp_check(check):
    if importlib.util.find_spec("mcp") is not None:
        return asyncio.run(check)
    # The in-process MCP stub runs all awaitables inline, including its worker.
    try:
        check.send(None)
    except StopIteration as completed:
        return completed.value
    finally:
        check.close()
    raise AssertionError("the in-process MCP stub unexpectedly suspended")


def test_manifest_only_run_drives_model_scan_and_keeps_the_cause_without_a_container(tmp_path):
    import engine_pass
    import pipeline
    import premap
    import resolve_edges
    from unittest.mock import Mock, patch

    project = tmp_path / "workspace"
    project.mkdir()
    (project / "package.json").write_text('{"name":"umbrella","workspaces":["packages/*"]}', encoding="utf-8")
    service = mcp_service.MapService(project)
    child = Mock(pid=os.getpid())
    with patch("engine_tools.shared_cache_dir", return_value=tmp_path / "cache"), \
            patch.object(engine_pass, "_spawn_detached", return_value=child) as spawn:
        created = service.create_run(".", "config", engine=True)
        assert created["engine"]["state"] == "running" and _modelling(created["plan"])
        spawn.assert_called_once()
        manifest = project / ".daodan/map/runs/config/snapshot/manifest.sqlite"
        engine_pass.running_record(manifest).unlink()
        with patch.object(container, "find_engine", side_effect=container.Gap("engine offline", "start engine")):
            assert resolve_edges.main([str(manifest), "--pass"]) == 0
        assert any(gap.get("kind") == "model_not_run" and "engine offline" in gap["detail"]
                   for gap in premap.ensure(manifest)["gaps"])
        status = service.status("config")
        assert _modelled(status["plan"]) and not _modelling(status["plan"])  # current with the recorded container gaps
        assert pipeline.runtime(manifest)["state"] == "none"
        assert service.index("config")["engine"]["action"] == "started"
        assert spawn.call_count == 2


def test_create_run_and_hook_refresh_never_probe_containers_under_lock_and_expose_stack(real_stack, tmp_path):
    project = _make_project(tmp_path / "proj")
    with mock.patch.dict(os.environ, {"XDG_CACHE_HOME": str(tmp_path / ".shared"),
                                      "LOCALAPPDATA": str(tmp_path / ".shared")}):
        service = mcp_service.MapService(project)
        with mock.patch.object(container, "find_engine", side_effect=AssertionError("must not probe container under lock")):
            created = service.create_run(".", "r1", engine=False)
        states = {step["id"]: step["state"] for step in created["plan"]["steps"]}
        assert _modelled(created["plan"]) and states["recognize_stack"] in ("done", "skipped")

        mods = service.modules("r1")
        by_id = {m["id"]: m for m in mods["modules"]}
        assert by_id["api"]["nature"] == "concrete"
        assert "java" in by_id["api"]["languages"]
        assert any(m["nature"] == "virtual" for m in mods["modules"])

        stack_all = service.stack("r1")
        api_stack = service.stack("r1", module="api")
        assert len(stack_all["modules"]) >= 2
        assert "spring-boot" in api_stack["module"]["frameworks"]
        assert "postgresql" in api_stack["module"]["services"]
        assert any(lib["name"] == "com.acme.lib:billing-sdk" for lib in api_stack["module"]["libraries"])

        # Publish r1 and trigger PostToolUse hook refresh: must stay fast & container-free under lock
        state_file = project / ".daodan/map/runs/r1/state.json"
        st = json.loads(state_file.read_text(encoding="utf-8"))
        st["status"] = "complete"
        state_file.write_text(json.dumps(st), encoding="utf-8")
        (project / ".daodan/map/runs.json").write_text(
            json.dumps({"schema": 2, "active": [], "latest_completed": "r1"}), encoding="utf-8"
        )
        (project / "scripts/cron.py").write_text("import fastapi\ndef tick():\n    return 2\n", encoding="utf-8")
        (project / "requirements.txt").write_text("fastapi>=0.115\n", encoding="utf-8")
        stamp = time.time() + 2
        for p in (project / "scripts/cron.py", project / "requirements.txt"):
            os.utime(p, (stamp, stamp))

        with mock.patch.object(container, "find_engine", side_effect=AssertionError("hook must not probe container")):
            refreshed = snapshot.refresh_working(project / ".daodan/map")
        assert refreshed["status"] == "fresh"
        assert refreshed["stack"]["state"] == "fresh"
        working_stack = service.stack("working")
        virt = next(m for m in working_stack["modules"] if m["nature"] == "virtual")
        assert "fastapi" in virt["frameworks"]
        pulse = service.live_pulse(after=0)
        assert any(item["kind"] == "working.refreshed" for item in pulse["events"])


def test_mcp_server_exposes_stack_tool_and_live_resource(tmp_path, monkeypatch):
    import secret_mask
    monkeypatch.setattr(secret_mask, "masked", lambda text, name: {"text": text, "found": 0, "kinds": []})
    project = _make_project(tmp_path / "proj")
    mcp_srv_mod = _load_mcp_server()
    with mock.patch.dict(os.environ, {"XDG_CACHE_HOME": str(tmp_path / ".shared"),
                                      "LOCALAPPDATA": str(tmp_path / ".shared")}):
        srv = mcp_srv_mod.create_server(project)
        service = mcp_service.MapService(project)
        service.create_run(".", "r1", engine=False)

        async def check():
            args = {"run_id": "r1", "module": "api"}
            if importlib.util.find_spec("mcp") is not None:
                from mcp import Client
                async with Client(srv) as client:
                    assert "codebase_map_stack" in {t.name for t in (await client.list_tools()).tools}
                    result = await client.call_tool("codebase_map_stack", args)
                    assert not result.is_error and "spring-boot" in result.content[0].text
                    pulse = await client.read_resource("daodan://project/live")
                    assert "events" in json.loads(pulse.contents[0].text)
            else:
                assert "codebase_map_stack" in {t.name for t in await srv.list_tools()}
                assert "spring-boot" in json.dumps(await srv.call_tool("codebase_map_stack", args))

        _run_mcp_check(check())


def test_mcp_redacts_errors_and_nested_results(monkeypatch):
    import secret_mask
    server = _load_mcp_server()
    needle = "FAKE_PRIVATE"
    monkeypatch.setattr(secret_mask, "masked", lambda text, name: {
        "text": text.replace(needle, "*" * len(needle)), "found": text.count(needle)})
    class Context:
        async def report_progress(self, *args, **kwargs):
            pass
    def failed():
        raise ValueError("failed " + needle)
    async def check():
        answer = await server._invoke(Context(), lambda: {"rows": [needle]})
        assert answer["rows"] == ["*" * len(needle)] and answer["masked_secrets"] == 1
        try:
            await server._invoke(Context(), failed)
        except server.ToolError as error:
            assert "*" * len(needle) in str(error) and needle not in str(error)
        else:
            raise AssertionError("the tool should have failed")
    _run_mcp_check(check())


def test_ui_http_routes_pipeline_events_stack_envelope_and_sse_stream_with_clean_shutdown(real_stack, tmp_path):
    project = _make_project(tmp_path / "proj")
    with mock.patch.dict(os.environ, {"XDG_CACHE_HOME": str(tmp_path / ".shared"),
                                      "LOCALAPPDATA": str(tmp_path / ".shared")}):
        service = mcp_service.MapService(project)
        service.create_run(".", "r1", engine=False)
        manifest = project / ".daodan/map/runs/r1/snapshot/manifest.sqlite"
        bus = pipeline.events.Bus(manifest.with_name(pipeline.events.JOURNAL))
        bus.emit("log", "first-line", step="find_modules")
        bus.emit("log", "second-line", step="recognize_stack")

        assets = tmp_path / "assets"
        assets.mkdir()
        (assets / "index.html").write_text("<!doctype html><title>UI</title>", encoding="utf-8")
        server = visual.make_server(None, assets, routes=visual.live_routes(service),
                                    actions=visual.live_actions(service), token="tok-1",
                                    stream=visual.live_stream(service))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]

        def get(path: str, *, token: str | None = "tok-1"):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            headers = {"Host": f"127.0.0.1:{port}"}
            if token:
                headers["X-Daodan-Token"] = token
            conn.request("GET", path, headers=headers)
            resp = conn.getresponse()
            body = resp.read()
            conn.close()
            return resp.status, resp.getheader("Content-Type"), body

        try:
            # pipeline_after forwarded properly on /api/events
            code, _, raw = get("/api/events?run=r1&pipeline_after=0")
            first = json.loads(raw)
            assert code == 200 and first["pipeline"]["next_cursor"] >= 2
            code2, _, raw2 = get(f"/api/events?run=r1&pipeline_after={first['pipeline']['next_cursor']}")
            assert code2 == 200 and json.loads(raw2)["pipeline"]["events"] == []

            # /api/modules and /api/stack and /data/visual.json expose Step 1 + Step 2 fields without container runs
            m_code, _, m_raw = get("/api/modules?run=r1")
            assert m_code == 200 and any(m["nature"] == "concrete" for m in json.loads(m_raw)["modules"])
            s_code, _, s_raw = get("/api/stack?run=r1&module=api")
            assert s_code == 200 and "spring-boot" in json.loads(s_raw)["module"]["frameworks"]
            v_code, _, v_raw = get("/data/visual.json?run=r1")
            env = json.loads(v_raw)
            api_entity = next(e for e in env["entities"] if e["ref"] == "build:api")
            assert (api_entity["species"], api_entity["concrete"]) == ("modulo", True)
            assert "spring-boot" in api_entity["frameworks"]
            assert all("species" in e and "nature" not in e for e in env["entities"])

            # SSE /api/stream refuses missing token and streams live events with token
            unauth, _, _ = get("/api/stream?run=r1&once=1", token=None)
            assert unauth == 403
            sse_code, ctype, sse_body = get("/api/stream?run=r1&once=1")
            assert sse_code == 200 and "text/event-stream" in (ctype or "")
            assert b"event: snapshot" in sse_body or b"data:" in sse_body
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
        assert not thread.is_alive()
