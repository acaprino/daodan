#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30"]
# ///
"""The standalone app: one local server, from the address of a public repository to its graph.

    uv run --no-project --script app.py [--work DIR] [--port N]

The launcher composes what exists and owns its end: `repository` gives the checkout, `MapService` the run (snapshot,
pre-map, stack, and the pass that builds the graph beside it), `visual.make_server` the transport on 127.0.0.1 with
its token, `engines` the model a question is given to, and `app_view` the run in the shapes the page draws (the
pre-map, the graph in groups). It prints the page's address, which carries the token.

One repository and branch is active at a time. Selecting it is work off the request: the page asks, reads
`/api/app/state` and the run's events, and opens the explorer of the graph (`/`, the compiled viewer) on the run.
The explorer's routes are the service's own (`visual.live_routes`), bound to the active checkout; before one is
selected they answer that none is.

A question to the engine is the same: asked, then read. The engine reads the project only through Daodan's
operations (functions of this process for an API, the MCP server for a command line): nothing of the analysed
project runs on this machine. The engine's key stays in this process's memory, said `set` or `missing`.
"""
from __future__ import annotations

import argparse
import secrets
import subprocess
import sys
import threading
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import app_view  # noqa: E402
import engines  # noqa: E402
import repository  # noqa: E402
import visual  # noqa: E402
from mcp_service import MapService  # noqa: E402

PLUGIN = SCRIPT_DIR.parents[2]
VIEWER, PAGE = PLUGIN / "assets" / "viewer", PLUGIN / "assets" / "app"
SYSTEM = ("You answer questions about one codebase that Daodan has mapped. Read it only with the tools given: "
          "search first, then read what you need. Say what you could not establish instead of guessing.")


class App:
    """The active repository, the work that prepares it and the question asked of the engine."""

    def __init__(self, work: Path, environment=None):
        self.work = Path(work).resolve()
        self.work.mkdir(parents=True, exist_ok=True)
        self.service: MapService | None = None
        self.context: dict | None = None
        self.job = {"state": "idle", "step": None, "detail": ""}
        self.mcp_ready = "not prepared"  # whether the MCP server's own packages are fetched: said in the state
        self.engine = engines.setting(environment) if environment is not None else engines.setting()
        self.asked = {"state": "idle", "question": "", "text": "", "events": [], "cause": None}
        self._lock, self._stop = threading.Lock(), threading.Event()

    # -- the repository -------------------------------------------------------------------------------------------

    def check(self, body: dict) -> dict:
        return repository.branches(body["url"], self.work)

    def select(self, body: dict) -> dict:
        """Start preparing `branch` of the repository at `url`; the state says how it goes."""
        found, branch = repository.parse(body["url"]), body["branch"]
        if not isinstance(branch, str):
            raise ValueError("the branch is a name")
        with self._lock:
            if self.job["state"] == "preparing" or self.asked["state"] == "running":
                raise ValueError("work is in progress: wait for it, or stop the app")
            self.job = {"state": "preparing", "step": "checkout", "detail": f"{found['url']} at {branch}"}
            self.service = self.context = None
            self.mcp_ready = "not prepared"
        threading.Thread(target=self._prepare, args=(found["url"], branch), daemon=True).start()
        return self.state({})

    def _prepare(self, url: str, branch: str) -> None:
        try:
            checked = repository.checkout(url, branch, self.work)
            self.job = {"state": "preparing", "step": "snapshot", "detail": f"commit {checked['commit'][:12]}"}
            service = MapService(checked["path"])
            run_id = f"app-{checked['commit'][:12]}"
            if run_id not in [run["run_id"] for run in service.runs()["runs"]]:
                service.create_run(".", run_id)
            with self._lock:
                self.service, self.context = service, {**checked, "run_id": run_id}
                self.job = {"state": "ready", "step": None, "detail": ""}
        except Exception as error:  # noqa: BLE001 - the page reads why the preparation failed
            cause = str(error) if isinstance(error, ValueError) else f"{type(error).__name__}: {error}"
            self.job = {"state": "failed", "step": self.job["step"], "detail": cause[:600]}
            return
        self._warm()

    def _warm(self) -> None:
        """Fetch the MCP server's own packages now, so that a command-line engine finds it ready when it starts."""
        launch = self.mcp()
        try:
            done = subprocess.run([launch["command"], *launch["args"][:-2], "--help"], capture_output=True, text=True,
                                  timeout=300, stdin=subprocess.DEVNULL, check=False)
            self.mcp_ready = "ready" if done.returncode == 0 else f"not ready: {done.stderr.strip()[-300:]}"
        except (OSError, subprocess.TimeoutExpired) as error:
            self.mcp_ready = f"not ready: {type(error).__name__}: {error}"

    def mcp(self) -> dict | None:
        """How a command-line engine, or a session of the person's, starts Daodan's MCP server on the checkout."""
        if self.context is None:
            return None
        return {"command": "uv", "args": ["--directory", PLUGIN.as_posix(), "run", "--no-config", "--no-project",
                                          "--script", (SCRIPT_DIR / "mcp_server.py").as_posix(), "--project",
                                          Path(self.context["path"]).as_posix()]}

    def state(self, query: dict) -> dict:
        service, context = self.service, self.context
        status = service.status(context["run_id"]) if service is not None else {}
        engine = status.get("engine") or {}
        return {"job": self.job, "context": context, "engine": engines.described(self.engine), "mcp": self.mcp(),
                "mcp_ready": self.mcp_ready,
                "run": {"pipeline": status.get("pipeline"), "progress": status.get("progress"),
                        "pass": {key: engine.get(key) for key in ("state", "reason")}} if status else None,
                "asked": {key: self.asked[key] for key in ("state", "question", "cause")}}

    # -- the views of the page -------------------------------------------------------------------------------------

    def _active(self) -> tuple[MapService, str]:
        service, context = self.service, self.context
        if service is None or context is None:
            raise ValueError("no repository is selected")
        return service, context["run_id"]

    def premap(self, query: dict) -> dict:
        """The pre-map as the page draws it: the stack's units and libraries beside the snapshot's files."""
        service, run = self._active()
        return app_view.premap(service.stack(run), service.modules(run), app_view.headers(service.root / "runs" / run))

    def graph(self, query: dict) -> dict:
        """The run's graph in groups, as the page draws it while it grows; the explorer (`/`) shows it whole."""
        service, run = self._active()
        return app_view.graph(visual.build_envelope(service.root / "runs" / run))

    # -- the engine -----------------------------------------------------------------------------------------------

    def configure(self, body: dict) -> dict:
        """Choose the engine and, for an endpoint, its address, model and key; a key left out stays as it is."""
        chosen = {**self.engine, **{key: body[key] for key in ("engine", "base_url", "model") if key in body}}
        if body.get("api_key"):
            chosen["api_key"] = body["api_key"]
        if any(not isinstance(chosen[key], str) for key in ("base_url", "model", "api_key")) \
                or chosen["engine"] not in (None, *engines.ENGINES):
            raise ValueError(f"the engine is one of {', '.join(engines.ENGINES)}, with text for its settings")
        self.engine = chosen
        return engines.described(chosen)

    def probe(self, body: dict) -> dict:
        folder = self.work / "engine"
        folder.mkdir(exist_ok=True)
        return engines.probe(engines.configured(self.engine), folder)

    def _tools(self) -> list[dict]:
        """The service's reading operations on the active run, as the tools of an engine asked over an API."""
        service, run = self.service, self.context["run_id"]
        text, names = {"type": "string"}, {"type": "array", "items": {"type": "string"}}

        def tool(name, description, properties, required, call):
            return {"name": name, "description": description, "call": call,
                    "parameters": {"type": "object", "properties": properties, "required": required}}

        return [
            tool("codebase_map_modules", "The project's modules, or the candidates for a name.", {"query": text}, [],
                 lambda a: service.modules(run, query=a.get("query"), brief=not a.get("query"))),
            tool("codebase_map_stack", "Frameworks, libraries, services and tools of every module, or of one.",
                 {"module": text}, [], lambda a: service.stack(run, module=a.get("module"))),
            tool("codebase_map_search", "Rank symbols and files for a query; returns ids, paths and spans, no source.",
                 {"query": text}, ["query"], lambda a: service.search(run, a["query"], limit=12)),
            tool("codebase_map_graph", "Verified static links around the given paths.", {"paths": names}, ["paths"],
                 lambda a: service.graph(run, paths=a["paths"], hops=1, limit=60)),
            tool("codebase_map_read", "Read source by path: requests are objects with `path` and, where wanted, "
                                      "`symbols` or `ranges`.",
                 {"requests": {"type": "array", "items": {"type": "object"}}}, ["requests"],
                 lambda a: service.read(run, a["requests"])),
        ]

    def ask(self, body: dict) -> dict:
        """Give the engine a question about the active run; `answer` reads how it goes."""
        question = body["question"]
        if not isinstance(question, str) or not question.strip():
            raise ValueError("the question is text")
        engine = engines.configured(self.engine)
        with self._lock:
            if self.service is None:
                raise ValueError("no repository is selected")
            if self.asked["state"] == "running":
                raise ValueError("the engine is answering: wait for it")
            self.asked = asked = {"state": "running", "question": question, "text": "", "events": [], "cause": None}
        folder = self.work / "engine"
        folder.mkdir(exist_ok=True)
        task = {"system": SYSTEM, "prompt": f"The run is `{self.context['run_id']}`.\n\n{question}",
                "tools": self._tools(), "mcp": self.mcp(), "cwd": str(folder)}

        def said(kind, **data):
            asked["events"].append({"kind": kind, **data})
            if kind == "text":
                asked["text"] += data["text"]

        def work():
            try:
                outcome = engine.run(task, said, self._stop.is_set)
            except Exception as error:  # noqa: BLE001 - the page reads why the engine failed
                outcome = {"state": "failed", "text": "", "cause": f"{type(error).__name__}: {error}"}
            asked.update(state=outcome["state"], cause=outcome["cause"], text=outcome["text"] or asked["text"])

        threading.Thread(target=work, daemon=True).start()
        return {"state": "running"}

    def answer(self, query: dict) -> dict:
        after = int(query.get("after", 0))
        return {**{key: self.asked[key] for key in ("state", "question", "text", "cause")},
                "events": self.asked["events"][after:], "next": len(self.asked["events"])}

    # -- the transport --------------------------------------------------------------------------------------------

    def serve(self, port: int = 0, token: str | None = None):
        """The server over this app: the explorer's routes on the active service, and the app's own."""
        app = self

        class Active:  # the service of the checkout selected now, for routes built once
            def __getattr__(self, name):
                if app.service is None:
                    raise ValueError("no repository is selected")
                return getattr(app.service, name)

        active = Active()
        routes = {**visual.live_routes(active), "/api/app/state": self.state, "/api/app/answer": self.answer,
                  "/api/app/premap": self.premap, "/api/app/graph": self.graph}
        actions = {**visual.live_actions(active), "/api/app/check": self.check, "/api/app/select": self.select,
                   "/api/app/engine": self.configure, "/api/app/probe": self.probe, "/api/app/ask": self.ask}
        return visual.make_server(None, VIEWER, port, routes=routes, actions=actions, token=token,
                                  stream=visual.live_stream(active), mounts={"app": PAGE})

    def close(self) -> None:
        self._stop.set()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--work", type=Path, default=Path.home() / ".daodan" / "app",
                        help="where checkouts and their analysis live; default: .daodan/app in the home folder")
    parser.add_argument("--port", type=int, default=0, help="the port on 127.0.0.1; default: a free one")
    args = parser.parse_args(argv)
    app, token = App(args.work), secrets.token_urlsafe(24)
    server = app.serve(args.port, token)
    print(f"http://127.0.0.1:{server.server_address[1]}/app/?token={token}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.close()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
