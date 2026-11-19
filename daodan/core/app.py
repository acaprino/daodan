#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30"]
# ///
"""The standalone app: one local server, from the address of a public repository to its graph.

    uv run --no-project --script app.py [--work DIR] [--port N]

The launcher composes what exists and owns its end: `repository` gives the checkout, `MapService` the run (snapshot,
pre-map, stack, and the pass that builds the graph beside it), `visual.make_server` the transport on 127.0.0.1 with
its token, `engines` the model a question is given to, `app_view` the run in the shapes the page draws (the
pre-map, the graph in groups), and `service_registry` the mark of an external node. It prints the page's address,
which carries the token.

One repository and branch is active at a time. Selecting it is work off the request: the page asks, observes
`/api/stream` (the app's state whenever it changes, the run's events as they are written), and opens the explorer of
the graph (`/`, the compiled viewer) on the run.
The explorer's routes are the service's own (`visual.live_routes`), bound to the active checkout; before one is
selected they answer that none is.

A question to the engine is the same: asked, then read. The engine reads the project only through Daodan's
operations (functions of this process for an API, the MCP server for a command line): nothing of the analysed
project runs on this machine. The engine's key stays in this process's memory, said `set` or `missing`.
Finding the links between modules is a task of the engine too: it writes the project's link rules through the flows
tool and corrects them on what stays unlinked; what they link is the service's answer, never the engine's words.
"""
from __future__ import annotations

import argparse
import json
import secrets
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import app_view  # noqa: E402
import confinement  # noqa: E402
import engines  # noqa: E402
import repository  # noqa: E402
import service_registry  # noqa: E402
import visual  # noqa: E402
from mcp_service import MapService  # noqa: E402

PACKAGE = SCRIPT_DIR.parent
VIEWER, PAGE = PACKAGE / "assets" / "viewer", PACKAGE / "assets" / "app"
SYSTEM = ("You answer questions about one codebase that Daodan has mapped. Read it only with the tools given: "
          "search first, then read what you need. Say what you could not establish instead of guessing.")
ROUNDS = 3  # the times the engine corrects its link rules on what the machine left unlinked
LINKS = ("Write the link rules of the project of run `{run}`: the machine applies them and decides every link, and "
         "your final words are not a result. Read the code only with the tools given: read the few files that decide "
         "how the project reads and writes its state, calls and declares its routes, reaches its stores and binds "
         "user actions, then pass rules to `codebase_map_flows` to record them. Its answer is what they link: "
         "`routes` counts the calls of a route, the routes offered and the calls linked to one; `stores`; `gaps`, "
         "each call or value no rule links, with its reason. A rule it refuses comes back with why. Correct your "
         "rules on those leftovers and record them again, at most {rounds} times, then stop.\n\n"
         "The technologies of each build unit:\n{technologies}\n\nThe rule format:\n{format}")
FINAL = ("fresh", "unavailable", "failed", "off")  # the pass's states that change no more by themselves
TURN, RECHECK = 0.5, 1.5  # seconds between two reads of the stream, and between two reads of a running pass's state


def _cause(error: Exception) -> str:
    """Why a piece of work failed, as the page reads it."""
    return str(error) if isinstance(error, ValueError) else f"{type(error).__name__}: {error}"


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
        self.linked = {"state": "idle", "cause": None}  # the links between modules: see `link`
        self.registry = {entry["id"]: entry for entry in service_registry.load()["entries"]}  # whose marks `mark` serves
        self._marks, self._fetch = {}, ThreadPoolExecutor(max_workers=1)  # the marks fetched on first use, one at a time
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
            if "running" in (self.asked["state"], self.linked["state"]) or self.job["state"] == "preparing":
                raise ValueError("work is in progress: wait for it, or stop the app")
            self.job = {"state": "preparing", "step": "checkout", "detail": f"{found['url']} at {branch}"}
            self.service = self.context = None
            self.linked = {"state": "idle", "cause": None}
            self.mcp_ready = "not prepared"
        threading.Thread(target=self._prepare, args=(found["url"], branch), daemon=True).start()
        return self.state({})

    def _prepare(self, url: str, branch: str) -> None:
        try:
            checked = repository.checkout(url, branch, self.work)
            self.job = {"state": "preparing", "step": "snapshot", "detail": f"commit {checked['commit'][:12]}"}
            checkout = Path(checked["path"])
            service = MapService(checkout.parent)  # the analysis beside the checkout, never inside the project
            run_id = f"app-{checked['commit'][:12]}"
            if run_id not in [run["run_id"] for run in service.runs()["runs"]]:
                service.create_run(checkout.name, run_id)
            else:
                service.index(run_id)  # a run already there: a pass that failed starts again
            with self._lock:
                self.service, self.context = service, {**checked, "run_id": run_id}
                self.job = {"state": "ready", "step": None, "detail": ""}
        except Exception as error:  # noqa: BLE001 - the page reads why the preparation failed
            self.job = {"state": "failed", "step": self.job["step"], "detail": _cause(error)[:600]}
            return
        self._warm()

    def retry(self, body: dict) -> dict:
        """Start again the selected run's pass where it failed; one that is fresh, running or unavailable stays."""
        service, run_id = self._active()
        service.index(run_id)
        return self.state({})

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
        return {"command": "uv", "args": ["--directory", PACKAGE.as_posix(), "run", "--no-config", "--no-project",
                                          "--script", (SCRIPT_DIR / "mcp_server.py").as_posix(), "--project",
                                          Path(self.context["path"]).parent.as_posix()]}

    def _held(self) -> dict:
        """The part of the state this process holds, cheap to read: the run's states are read from its store."""
        return {"job": self.job, "context": self.context, "engine": engines.described(self.engine), "mcp": self.mcp(),
                "mcp_ready": self.mcp_ready, "asked": {key: self.asked[key] for key in ("state", "question", "cause")},
                "links": self.linked}

    def state(self, query: dict) -> dict:
        service, context = self.service, self.context
        status = service.status(context["run_id"]) if service is not None else {}
        engine = status.get("engine") or {}
        return {**self._held(),
                "run": {"pipeline": status.get("pipeline"), "progress": status.get("progress"),
                        "pass": {key: engine.get(key) for key in ("state", "reason")}} if status else None}

    def stream(self, explorer):
        """`/api/stream` of the app, for a page that observes: the explorer's frames on the active run (`explorer`
        is `visual.live_stream`'s, read once a turn from the cursors so far), and an `app` frame with the app's state
        first and whenever it changes. Before a selection the state alone; after one, the new run from its start.
        The run's states are read again after its events, and every RECHECK seconds while its pass runs. A failure
        ends the stream with a `failure` frame; a project another helper holds is busy, not failed: that turn gives
        nothing and the next reads again. The stream ends after `max_seconds` (15, at most 60), and the page opens it
        again from its cursors."""
        def frames(query: dict, should_stop):
            deadline = time.monotonic() + min(float(query.get("max_seconds", 15)), 60.0)
            run, kind = query.get("run"), "snapshot"
            cursors = {key: int(query.get(key, 0)) for key in ("after", "pipeline_after", "pulse_after")}
            held = shown = None
            checked = 0.0
            while not should_stop():
                try:
                    found, context, moved = None, self.context, cursors
                    if context is not None and self.service is not None:
                        if context["run_id"] != run:
                            run, kind, cursors = context["run_id"], "snapshot", dict.fromkeys(cursors, 0)
                        [(_, found)] = explorer({"run": run, "once": "1", **cursors}, should_stop)
                        events, pulse = found["run_events"], found["pulse"]
                        moved = {"after": events["next_cursor"], "pipeline_after": events["pipeline"]["next_cursor"],
                                 "pulse_after": pulse["next_cursor"]}
                    news = bool(found) and bool(events["events"] or events["pipeline"]["events"] or pulse["events"])
                    now = self._held()
                    running = not shown or not shown["run"] or shown["run"]["pass"]["state"] not in FINAL
                    if now != held or news or (running and time.monotonic() - checked >= RECHECK):
                        state = self.state({})
                        held, checked = now, time.monotonic()
                        if state != shown:  # before the events it follows, so that the page knows their run
                            shown = state
                            yield "app", state
                    if news or (found and kind == "snapshot"):
                        yield kind, found
                        kind = "update"
                    cursors = moved  # the turn is over: what it read is given
                except confinement.ProjectBusy:
                    pass  # another helper holds the project now: the turn is skipped, the next one reads it again
                except (ValueError, KeyError, TypeError, OSError) as error:
                    yield "failure", {"error": str(error)}
                    return
                if time.monotonic() >= deadline:
                    return
                time.sleep(TURN)

        return frames

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

    def mark(self, query: dict) -> Path | None:
        """The mark of the registry entry `id` (`service_registry.mark_file`), or None: the page draws the icon of the
        node's type. A mark taken out of its owner's package on first use is fetched off the request: until it is
        there, and after it failed, the answer is None, so that no page or graph waits on a download."""
        entry = self.registry.get(query["id"])
        if entry is None:
            raise ValueError("the registry has no entry with this id")
        if entry.get("mark") or not entry.get("mark_source"):
            return service_registry.mark_file(entry)
        with self._lock:
            if entry["id"] not in self._marks:
                self._marks[entry["id"]] = self._fetch.submit(service_registry.mark_file, entry)
            fetched = self._marks[entry["id"]]
        return fetched.result() if fetched.done() else None

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
        """The service's operations on the active run, as the tools of an engine asked over an API: they read, and
        the flows tool records the project's link rules."""
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
            tool("codebase_map_flows", "The project's link rules: `rules` records them, and the answer is what they "
                                       "link (routes, stores, gaps) or why a rule is refused; without them, what the "
                                       "recorded rules link or the rule format.",
                 {"rules": {"type": "array", "items": {"type": "object"}}}, [],
                 lambda a: service.flows(run, rules=a.get("rules"))),
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

    def link(self, body: dict) -> dict:
        """Find the links between the active run's modules. Without recorded rules the engine is given the rule format
        the service answers and writes the rules through the flows tool; at its end the service says what they link.
        Rules recorded before are the service's already: no engine is asked again."""
        service, run = self._active()
        with self._lock:
            if self.linked["state"] == "running":
                raise ValueError("the engine is finding the links: wait for it")
            self.linked = {"state": "running", "cause": None}
        try:
            needs = service.flows(run)
        except Exception as error:  # noqa: BLE001 - the page reads why the links were not found
            self.linked = {"state": "failed", "cause": _cause(error)}
            return self.state({})
        if needs.get("status") != "needs_rules":
            self.linked = self._counted(needs)
            return self.state({})
        try:
            engine = engines.configured(self.engine)
        except ValueError as error:  # no engine is chosen, or it lacks what it needs: the engine screen says
            self.linked = {"state": "no_engine", "cause": str(error)}
            return self.state({})
        folder = self.work / "engine"
        folder.mkdir(exist_ok=True)
        technologies = needs.get("technologies") or needs.get("technologies_unavailable")
        task = {"prompt": LINKS.format(run=run, rounds=ROUNDS, format=needs["format"],
                                       technologies=json.dumps(technologies, ensure_ascii=False)),
                "tools": self._tools(), "mcp": self.mcp(), "cwd": str(folder)}
        refused = []

        def said(kind, name=None, answer=None, **data):  # a rule the service refused: its reason, if the engine says it
            if kind == "tool" and str(name).endswith("codebase_map_flows") and str(answer).startswith('{"error"'):
                refused.append(answer)

        def work():
            try:
                outcome = engine.run(task, said, self._stop.is_set)
                why = (f"the last rules were refused: {refused[-1]}" if refused else outcome["cause"]
                       or ("the engine was stopped" if outcome["state"] == "cancelled"
                           else "the engine ended and recorded no rules"))
                self.linked = self._counted(service.flows(run), why)
            except Exception as error:  # noqa: BLE001 - the page reads why the links were not found
                self.linked = {"state": "failed", "cause": _cause(error)}

        threading.Thread(target=work, daemon=True).start()
        return self.state({})

    @staticmethod
    def _counted(answer: dict, cause: str | None = None) -> dict:
        """What the service says the recorded rules link, or why it says nothing."""
        if answer.get("status") != "ok":
            return {"state": "failed", "cause": cause or answer.get("reason") or f"the service answered {answer}"[:600]}
        return {"state": "done", "cause": None, "routes": answer["routes"], "stores": answer["store_count"],
                "gaps": answer["gap_count"]}

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
                   "/api/app/retry": self.retry,
                   "/api/app/engine": self.configure, "/api/app/probe": self.probe, "/api/app/ask": self.ask,
                   "/api/app/link": self.link}
        stream = {"/api/stream": self.stream(visual.live_stream(active)["/api/stream"])}
        return visual.make_server(None, VIEWER, port, routes=routes, actions=actions, token=token, stream=stream,
                                  mounts={"app": PAGE}, files={"/api/app/mark": self.mark})

    def close(self) -> None:
        self._stop.set()
        self._fetch.shutdown(wait=False, cancel_futures=True)


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
