#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["mcp>=2.0.0,<3", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "keyring>=25", "PyYAML>=6", "protobuf==7.36.2", "pip-requirements-parser==32.0.1"]
# ///
"""The standalone app: one local server, from the address of a public repository to its graph.

    uv run --no-project --script app.py [--work DIR] [--port N] [--desktop]

The launcher composes what exists and owns its end: `repository` gives the checkout, `MapService` the run (snapshot,
pre-map, stack, and the pass that builds the graph beside it), `visual.make_server` the transport on 127.0.0.1 with
its token, `engines` the model a question is given to, `app_view` the run in the shapes the page draws (the
pre-map, the graph with its groups open in place), and `service_registry` the mark of an external node. It prints the page's
address, which carries the token.

One repository and branch is active at a time. Selecting it is work off the request: the page asks, observes
`/api/stream` (the app's state whenever it changes, the run's events as they are written), and opens the explorer of
the graph (`/`, the compiled viewer) on the run.
The explorer's routes are the service's own (`visual.live_routes`), bound to the active checkout; before one is
selected they answer that none is.

A question to the engine is the same: asked, then read. The engine reads the project only through Daodan's
operations (functions of this process for an API, the MCP server for a command line): nothing of the analysed
project runs on this machine. The chosen engine is kept in the work folder for the next start and its key in the
system's deposit of secrets (`engines.kept`); the key is said `set` or `missing`, never itself.
Finding the links between modules is a task of the engine too: it writes the project's link rules through the flows
tool and corrects them on what stays unlinked; what they link is the service's answer, never the engine's words.
When the selected run's pass ends fresh, the app finds the links and then maps the system by itself, once.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import app_view  # noqa: E402
import confinement  # noqa: E402
import egress  # noqa: E402
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
         "Known entry forms are already classified. Classify remaining forms with shape_offset and shape_answers; "
         "keep project route and store rules with rules. First numbered shapes: {shapes}\n\n"
         "The technologies of each build unit:\n{technologies}\n\nThe rule format:\n{format}")
MAP = ("Map the system of run `{run}`: the machine checks every proposal against the code's links and records what "
       "holds, and your final words are not a result. Read the code only with the tools given. Begin with "
       "`codebase_map_flows` with `brief` true. While it answers `needs_rules`, write the link rules in the format it "
       "gives, record them with `rules` and ask again. Then follow «Sequence» in the map format it returns, for the "
       "whole system.")
LINKED = {"routes": "routes", "stores": "store_count", "gaps": "gap_count"}  # what the state says of the links
DRAWN = {"nodes": "nodes", "flows": "flows", "left": "coverage"}  # what the state says of the system map
WRITING = "the engine is writing the link rules or the system map: wait for it"  # `link` and `map`: one at a time
FINAL = ("fresh", "unavailable", "failed", "off")  # the pass's states that change no more by themselves
LEVELS = 64  # answers of the graph kept for the run's data (open sets, files' symbols), least recently asked dropped first
TURN, RECHECK = 0.5, 1.5  # seconds between two reads of the stream, and between two reads of a running pass's state


def _listed(query: dict, name: str, why: str) -> list | None:
    """The JSON list of the query's `name`, None when absent; anything else is refused with `why`."""
    if query.get(name) is None:
        return None
    try:
        found = json.loads(query[name])
    except ValueError:
        raise ValueError(why) from None
    if not isinstance(found, list):
        raise ValueError(why)
    return found


def _cause(error: Exception) -> str:
    """Why a piece of work failed, as the page reads it."""
    return str(error) if isinstance(error, ValueError) else f"{type(error).__name__}: {error}"


def _refusals(kept: list):
    """What an engine says, kept when it is the flows tool refusing a call: the service's reason, for an engine that
    passes the tool's answer on."""
    def said(kind, name=None, answer=None, **data):
        if kind == "tool" and str(name).endswith("codebase_map_flows") and str(answer).startswith('{"error"'):
            kept.append(answer)
    return said


def _why(outcome: dict, refused: list, recorded: str) -> str:
    """Why an engine's work recorded nothing: the service's last refusal, or how the engine ended."""
    return (f"the service refused the last call: {refused[-1]}" if refused else outcome["cause"]
            or ("the engine was stopped" if outcome["state"] == "cancelled"
                else f"the engine ended and recorded no {recorded}"))


class App:
    """The active repository, the work that prepares it and the question asked of the engine."""

    def __init__(self, work: Path, environment=os.environ):
        self.work = Path(work).resolve()
        self.work.mkdir(parents=True, exist_ok=True)
        self.service: MapService | None = None
        self.context: dict | None = None
        self.job = {"state": "idle", "step": None, "detail": ""}
        self.mcp_ready = "not prepared"  # whether the MCP server starts: said in the state
        self.environment = environment  # what `setting` reads again when a key is forgotten
        self.engine = engines.recalled(self.work, environment)
        self._saving = threading.Lock()  # one `configure` at a time: the folder, the deposit and `engine` agree
        self.asked = {"state": "idle", "question": "", "text": "", "events": [], "cause": None}
        self.linked = {"state": "idle", "cause": None}  # the links between modules: see `link`
        self.mapped = {"state": "idle", "cause": None}  # the system map: see `map`
        self._following = None  # the selection whose pass's end is followed: see `_follow`
        self.marks = service_registry.Marks()  # the logos the two pages ask for
        self._lock, self._stop = threading.Lock(), threading.Event()
        self._levels, self._graphing = {}, threading.Lock()  # the graph's answers kept for the run's data: see `_kept`

    # -- the repository -------------------------------------------------------------------------------------------

    def check(self, body: dict) -> dict:
        return repository.branches(body["url"], self.work)

    def select(self, body: dict) -> dict:
        """Start preparing `branch` of the repository at `url`; the state says how it goes."""
        found, branch = repository.parse(body["url"]), body["branch"]
        if not isinstance(branch, str):
            raise ValueError("the branch is a name")
        with self._lock:
            if "running" in (self.asked["state"], self.linked["state"], self.mapped["state"]) \
                    or self.job["state"] == "preparing":
                raise ValueError("work is in progress: wait for it, or stop the app")
            self.job = {"state": "preparing", "step": "checkout", "detail": f"{found['url']} at {branch}"}
            self.service = self.context = None
            self.linked = {"state": "idle", "cause": None}
            self.mapped = {"state": "idle", "cause": None}
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
        self._follow()

    def retry(self, body: dict) -> dict:
        """Start again the selected run's pass where it failed; one that is fresh, running or unavailable stays."""
        service, run_id = self._active()
        service.index(run_id)
        threading.Thread(target=self._follow, daemon=True).start()
        return self.state({})

    def _follow(self) -> None:
        """When the selected run's pass ends `fresh`, find the links and then map the system (`link`, `map`): once for
        a selection, however often it is followed again. A pass that ends otherwise starts nothing, and `retry` follows
        it again; another selection or the app's end stops the wait. Links that are not found leave the map not started,
        with their cause; a failure of the chain is the map's cause."""
        with self._lock:
            service, context = self.service, self.context
            if context is None or self._following is context:
                return
            self._following = context
        try:
            if self._pass_end(service, context) != "fresh":
                with self._lock:
                    if self._following is context:
                        self._following = None
                return
            for held in ("linked", "mapped"):
                self._settled(held)  # what the person asked meanwhile ends first: what it records is not asked again
            self.link({})
            linked = self._settled("linked")
            if linked["state"] == "done":
                self.map({})
                return
            ended = {"state": linked["state"], "cause": f"the links are not found: {linked['cause']}"}
        except Exception as error:  # noqa: BLE001 - the page reads why the chain stopped
            ended = {"state": "failed", "cause": _cause(error)}
        with self._lock:
            if self.context is context and self.mapped["state"] != "running" and not self._stop.is_set():
                self.mapped = ended

    def _pass_end(self, service: MapService, context: dict) -> str | None:
        """How the selected run's pass ends, read every RECHECK seconds while it runs; None when another selection or
        the app's end comes first."""
        while self.context is context and not self._stop.is_set():
            try:
                engine = service.status(context["run_id"]).get("engine") or {}
                if engine.get("state") != "running":
                    return engine.get("state")
            except confinement.ProjectBusy:
                pass  # another helper holds the project now: the next turn reads again
            self._stop.wait(RECHECK)
        return None

    def _settled(self, held: str) -> dict:
        """The work kept in `held` once it does not run, read every TURN seconds; as it is when the app ends."""
        while getattr(self, held)["state"] == "running" and not self._stop.wait(TURN):
            pass
        return getattr(self, held)

    def _warm(self) -> None:
        """Try the MCP server now, so that the state says whether a command-line engine will find it."""
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
        return {"command": sys.executable, "args": [(SCRIPT_DIR / "mcp_server.py").as_posix(), "--project",
                                                    Path(self.context["path"]).parent.as_posix()]}

    def _held(self) -> dict:
        """The part of the state this process holds, cheap to read: the run's states are read from its store."""
        return {"job": self.job, "context": self.context, "engine": engines.described(self.engine), "mcp": self.mcp(),
                "mcp_ready": self.mcp_ready, "asked": {key: self.asked[key] for key in ("state", "question", "cause")},
                "links": self.linked, "mapped": self.mapped,
                "egress": egress.groups([self._project()]) if self.context is not None else []}

    def _project(self) -> str:
        """The name `egress` knows the selected checkout by: its folder, the snapshot's root."""
        if self.context is None:
            raise ValueError("no repository is selected")
        return str(Path(self.context["path"]).resolve())

    def hosts(self, body: dict) -> dict:
        """The person's answer to a group of the host requests the state shows: `{"hosts": [...], "reply": "always"
        | "once" | "no" | "block"}` (`egress.reply`). Only this action answers: MCP and the command line only read."""
        egress.reply(self._project(), body.get("hosts"), body.get("reply"))
        return self.state({})

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

    def paths(self, query: dict) -> dict:
        """A page of entries or the directed evidence for the selected entry in this run."""
        service, run = self._active()
        if query.get("effects") == "1":
            return service.flows(run, effect_offset=int(query.get("offset", 0)), limit=int(query.get("limit", 20)))
        return service.flows(run, trace_id=query.get("id"), trace_offset=int(query.get("offset", 0)),
                             limit=int(query.get("limit", 20)))

    def premap(self, query: dict) -> dict:
        """The pre-map as the page draws it: the stack's units and libraries beside the snapshot's files."""
        service, run = self._active()
        return app_view.premap(service.stack(run), service.modules(run), app_view.headers(service.root / "runs" / run))

    def graph(self, query: dict) -> dict:
        """The run's graph at the system map's `levels` (a JSON list; `app_view.levels`: the app builds codice and
        infrastruttura) with the groups of `open` (a JSON list of node ids) open in place (`app_view.view`); the
        explorer (`/`) shows it whole."""
        shown = app_view.levels(_listed(query, "levels", "levels is a JSON list of levels"))
        groups = _listed(query, "open", "open is a JSON list of node ids") or []
        if not all(isinstance(item, str) for item in groups):
            raise ValueError("open is a JSON list of node ids")
        groups = tuple(sorted(set(groups)))
        return self._kept(("graph", shown, groups), lambda envelope, run_dir: app_view.view(
            envelope, groups, shown, self._file_symbols(run_dir)))

    def symbols(self, query: dict) -> dict:
        """The inspector's data of the run's `file` (a node id), open or not: its symbols and their calls, with lines
        (`app_view.symbols`), read for that file only."""
        file = query.get("file")
        return self._kept(("symbols", file), lambda envelope, run_dir: app_view.symbols(
            envelope, file, self._file_symbols(run_dir)))

    def _file_symbols(self, run_dir: Path):
        """`visual.file_symbols`, read once per file and per state of the run's data, for an open file and for the
        inspector alike; asked while `_kept` holds its lock."""
        answers = self._levels["answers"]

        def read(path: str) -> dict:
            if ("file", path) not in answers:
                answers[("file", path)] = visual.file_symbols(run_dir, path)
            return answers[("file", path)]
        return read

    def _kept(self, key: tuple, compute):
        """What `compute(envelope, run_dir)` answers for `key`, kept: the run's envelope without the files' symbols is
        built once per state of the data it reads (`visual.inputs_stamp`), and each answer once on it; a change of
        that data throws all away, and at most LEVELS answers stay. One is computed at a time: who asks meanwhile
        waits, and finds it kept."""
        service, run = self._active()
        run_dir = service.root / "runs" / run
        import store_graph
        with self._graphing:
            stamp = (run_dir, visual.inputs_stamp(run_dir))
            if self._levels.get("stamp") != stamp or not store_graph.sources_unchanged(self._levels["sources"]):
                visual.settle(run_dir)  # the build writes what it derives: the stamp is of what it leaves
                stamp = (run_dir, visual.inputs_stamp(run_dir))
                with store_graph.capture_verified_sources() as sources:
                    envelope = visual.build_envelope(run_dir, symbols=False)
                self._levels = {"stamp": stamp, "envelope": envelope, "sources": sources, "answers": OrderedDict()}
            answers = self._levels["answers"]
            if key not in answers:
                answers[key] = compute(self._levels["envelope"], run_dir)
                while len(answers) > LEVELS:
                    answers.popitem(last=False)
            answers.move_to_end(key)
            return answers[key]

    def mark(self, query: dict) -> Path | None:
        """The mark of the registry entry `id` (`service_registry.Marks`); an id of no entry is refused."""
        if query["id"] not in self.marks.entries:
            raise ValueError("the registry has no entry with this id")
        return self.marks.file(query["id"])

    # -- the engine -----------------------------------------------------------------------------------------------

    def _chosen(self, body: dict) -> dict:
        """The setting `body` asks for over the one in use: the engine and, for an endpoint, its address, model and
        key. A key left out stays as it is; an empty one leaves the key a start would find without it."""
        chosen = {**self.engine, **{key: body[key] for key in ("engine", "base_url", "model") if key in body}}
        if "api_key" in body:
            chosen["api_key"] = body["api_key"] or engines.setting(self.environment)["api_key"]
        if any(not isinstance(chosen[key], str) for key in ("base_url", "model", "api_key")) \
                or chosen["engine"] not in (None, *engines.ENGINES):
            raise ValueError(f"the engine is one of {', '.join(engines.ENGINES)}, with text for its settings")
        return chosen

    def configure(self, body: dict) -> dict:
        """Use the setting `body` asks for and keep it for the next start: the choice in the work folder, a key
        given here in the system's deposit, an empty one forgotten there."""
        with self._saving:
            chosen = self._chosen(body)
            cause = engines.kept(chosen, self.work, (body["api_key"] or "") if "api_key" in body else None)
            chosen["unread"] = None  # the folder holds this setting now
            if "api_key" in body:
                chosen["unkept"] = cause
            self.engine = chosen
        return engines.described(chosen)

    def probe(self, body: dict) -> dict:
        """Whether the engine of the setting `body` asks for answers; nothing of it is used or kept."""
        folder = self.work / "engine"
        folder.mkdir(exist_ok=True)
        return engines.probe(engines.configured(self._chosen(body)), folder)

    def _tools(self) -> list[dict]:
        """The service's operations on the active run, as the tools of an engine asked over an API: they read, and
        the flows tool records the project's link rules and its system map."""
        service, run = self.service, self.context["run_id"]
        text, names = {"type": "string"}, {"type": "array", "items": {"type": "string"}}

        def tool(name, description, properties, required, call):
            def checked(arguments):
                import secret_mask
                try:
                    result = call(arguments)
                except Exception as error:
                    result = {"error": str(error)}
                return secret_mask.tool_result(result)

            return {"name": name, "description": description, "call": checked,
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
            tool("codebase_map_flows", "The project's link rules and its system map. `rules` records the rules, and the "
                                       "answer is what they link (routes, stores, gaps) or why a rule is refused; with "
                                       "nothing, what the recorded rules link or the rule format. `brief` gives the "
                                       "system brief and the map format; `map` records a proposal and reports it; "
                                       "`about` answers for an area, a flow or a node. shape_offset pages unknown "
                                       "forms and shape_answers classifies them. trace_offset lists cards; trace_id "
                                       "reads numbered steps. effect_offset pages writes without a proven entry. "
                                       "next_question gives one card to review. trace_decision "
                                       "records a proved path by its step numbers or an unresolved/excluded reason.",
                 {"rules": {"type": "array", "items": {"type": "object"}}, "brief": {"type": "boolean"},
                  "map": {"type": "object"}, "about": text, "entry_offset": {"type": "integer", "minimum": 0},
                  "shape_offset": {"type": "integer", "minimum": 0}, "shape_answers": {"type": "object"},
                  "trace_offset": {"type": "integer", "minimum": 0}, "trace_id": text,
                  "trace_decision": {"type": "object"}, "next_question": {"type": "boolean"},
                  "effect_offset": {"type": "integer", "minimum": 0},
                  "limit": {"type": "integer", "minimum": 1}}, [],
                 lambda a: service.flows(run, **{key: a[key] for key in
                                                  ("rules", "brief", "map", "about", "entry_offset", "limit", "shape_answers",
                                                   "shape_offset", "trace_id", "trace_offset", "trace_decision",
                                                   "next_question", "effect_offset") if key in a})),
        ]

    def _engage(self, held: str, busy: str, running: dict, start, beside: tuple = (), next_prompt=None, before_engine=None) -> None:
        """The engine's work kept in `held` (asked, linked, mapped), one at a time: it is `running` until it ends, and
        another asked meanwhile, or while a work `beside` names runs, is refused with `busy`. `start()` gives its end at
        once, or its task, what is said while the engine runs and what the engine's outcome ends as; the engine runs in
        a thread of its own. Without an engine the end is `no_engine` and nothing is written; a failure anywhere is an
        end with its cause."""
        with self._lock:
            if any(getattr(self, name)["state"] == "running" for name in (held, *beside)):
                raise ValueError(busy)
            setattr(self, held, running)

        def failed(error: Exception) -> dict:
            return {**running, "state": "failed", "cause": _cause(error)}

        try:
            begun = start()
            if isinstance(begun, dict):  # ended before an engine was needed
                setattr(self, held, begun)
                return
            try:
                engine = engines.configured(self.engine)
            except ValueError as error:  # no engine is chosen, or it lacks what it needs: the engine screen says
                setattr(self, held, {**running, "state": "no_engine",
                                     "cause": f"{error}; set the engine on its screen, then ask again"})
                return
            task, said, ended = begun
            import secret_mask
            prompt = secret_mask.tool_result({"prompt": task["prompt"]})
            if "prompt" not in prompt:
                setattr(self, held, {**running, "state": "failed", "cause": secret_mask.UNAVAILABLE})
                return
            task = {**task, "prompt": prompt["prompt"]}
            folder = self.work / "engine"
            folder.mkdir(exist_ok=True)
            task = {**task, "tools": self._tools(), "mcp": self.mcp(), "cwd": str(folder)}
        except Exception as error:  # noqa: BLE001 - the page reads why the work failed
            setattr(self, held, failed(error))
            return

        def work():
            try:
                current = task
                while True:
                    if before_engine:
                        before_engine()
                    outcome = engine.run(current, said, self._stop.is_set)
                    if outcome["state"] != "done" or not next_prompt or self._stop.is_set():
                        break
                    following = next_prompt(outcome)
                    if not following:
                        break
                    scanned = secret_mask.tool_result({"prompt": following})
                    if "prompt" not in scanned:
                        raise ValueError(secret_mask.UNAVAILABLE)
                    current = {**task, "prompt": scanned["prompt"]}
            except Exception as error:  # noqa: BLE001 - the page reads why the engine failed
                outcome = {"state": "failed", "text": "", "session": None, "cause": f"{type(error).__name__}: {error}"}
            try:
                setattr(self, held, ended(outcome))
            except Exception as error:  # noqa: BLE001 - the page reads why the work failed
                setattr(self, held, failed(error))

        threading.Thread(target=work, daemon=True).start()

    def ask(self, body: dict) -> dict:
        """Give the engine a question about the active run; `answer` reads how it goes."""
        question = body["question"]
        if not isinstance(question, str) or not question.strip():
            raise ValueError("the question is text")
        engines.configured(self.engine)  # without an engine the question is refused, before anything starts
        _, run = self._active()
        asked = {"state": "running", "question": question, "text": "", "events": [], "cause": None}

        def said(kind, **data):
            asked["events"].append({"kind": kind, **data})
            if kind == "text":
                asked["text"] += data["text"]

        def ended(outcome):
            return {**asked, "state": outcome["state"], "cause": outcome["cause"],
                    "text": outcome["text"] or asked["text"]}

        self._engage("asked", "the engine is answering: wait for it", asked, lambda: (
            {"system": SYSTEM, "prompt": f"The run is `{run}`.\n\n{question}"}, said, ended))
        return {"state": self.asked["state"]}

    def answer(self, query: dict) -> dict:
        after = int(query.get("after", 0))
        return {**{key: self.asked[key] for key in ("state", "question", "text", "cause")},
                "events": self.asked["events"][after:], "next": len(self.asked["events"])}

    def link(self, body: dict) -> dict:
        """Find the links between the active run's modules. Without recorded rules the engine is given the rule format
        the service answers and writes the rules through the flows tool; at its end the service says what they link.
        Rules recorded before are the service's already: no engine is asked again."""
        service, run = self._active()
        refused = []

        def start():
            needs = service.flows(run)
            if needs.get("status") != "needs_rules":
                return self._counted(needs)
            technologies = needs.get("technologies") or needs.get("technologies_unavailable")
            if "technologies_remaining" in needs:
                technologies = {"units": needs["technologies"], "remaining": needs["technologies_remaining"],
                                "lookup": needs["technologies_lookup"]}
            task = {"prompt": LINKS.format(run=run, rounds=ROUNDS, format=needs["format"],
                                           technologies=json.dumps(technologies, ensure_ascii=False),
                                           shapes=json.dumps(needs.get("shapes", {}), ensure_ascii=False))}
            return task, _refusals(refused), lambda outcome: self._counted(
                service.flows(run), _why(outcome, refused, "rules"))

        self._engage("linked", WRITING, {"state": "running", "cause": None}, start, beside=("mapped",))
        return self.state({})

    def map(self, body: dict) -> dict:
        """Map the active run's system: the engine follows the sequence of the map format the service gives, writing
        the link rules first when the run has none; at its end the service says the recorded map's nodes and flows
        and what its coverage leaves out. Reuse fresh maps and revisit stale or incomplete records once per call."""
        service, run = self._active()
        refused = []
        running = {"state": "running", "cause": None}

        from flow_questions import Review
        review = Review(service, run)
        budget = body.get("question_budget")
        if budget is not None and (type(budget) is not int or budget < 0):
            raise ValueError("question_budget must be a nonnegative number of model questions per run")

        def needs_structure(recorded):
            if recorded.get("needs_structure"):
                return True
            return (recorded.get("status") == "no_map" and review.counts.get("count", 0) > 0
                    and not review.counts["remaining"] and not review.counts["reviewed"]["unresolved"])

        def start():
            recorded = service.system_map(run)
            needs_review = recorded.get("needs_review")
            prompt = review.prompt()
            if review.counts.get("count") or "effect_coverage" in review.counts or review.counts.get("remaining_shapes"):
                running["discovery"] = review.counts
            if prompt:
                return {"prompt": prompt}, _refusals(refused), finish
            if (not needs_review and not needs_structure(recorded)
                    and (review.counts.get("count") or recorded.get("status") == "ok")):
                return finish({"state": "done", "cause": None}, recorded)
            return {"prompt": structural_prompt(recorded)}, _refusals(refused), finish

        def structural_prompt(recorded):
            needs_review = recorded.get("needs_review")
            prompt = MAP.format(run=run)
            if needs_review:
                running["needs_review"] = needs_review
                prompt = (f"Review the stale or incomplete records in the recorded map of run `{run}`. "
                          "Read their current evidence through codebase_map_flows, then submit corrected records. "
                          "Keep unresolved steps and report what still needs project confirmation. "
                          f"Counts and record ids: {json.dumps(needs_review, ensure_ascii=False)}")
            if needs_structure(recorded):
                prompt += (" Complete the whole-system structure: record the product node and its parts. "
                           "Reuse the event paths and decisions already recorded for this snapshot.")
            return prompt

        def advance(outcome):
            if review.current is None:
                return None
            following = review.advance(outcome)
            if following:
                return following
            recorded = service.system_map(run)
            if needs_structure(recorded) or recorded.get("needs_review"):
                return structural_prompt(recorded)
            return None

        def finish(outcome, recorded=None):
            if recorded is None:
                recorded = service.system_map(run)
            result = self._counted(recorded, _why(outcome, refused, "map"), DRAWN)
            if outcome["state"] != "done" and result["state"] == "done":
                result.update(state="incomplete", cause=outcome.get("cause") or "mapping interrupted")
            if review.counts.get("remaining_shapes"):
                result.update(state="incomplete", cause=outcome.get("cause") or "entry forms still pending",
                              discovery=review.counts)
            if review.counts.get("count") or "effect_coverage" in review.counts:
                counts = review.counts
                result["discovery"] = counts
                orphans = counts.get("effect_coverage", {}).get("without_entry", 0)
                if orphans:
                    result.update(state="incomplete", cause=outcome.get("cause") or
                                  f"{orphans} writes without an evidenced entry")
                if counts["remaining"] or counts["reviewed"].get("unresolved"):
                    result.update(state="incomplete", cause=outcome.get("cause") or
                                  f'{counts["remaining"]} entries pending; {counts["reviewed"]["unresolved"]} unresolved')
            if pending := recorded.get("needs_review"):
                result.update(state="incomplete", needs_review=pending,
                              cause=outcome.get("cause") or "the recorded map still has stale or incomplete records")
            if needs_structure(recorded):
                result.update(state="incomplete", needs_structure=True,
                              cause=outcome.get("cause") or "the product node still needs to be recorded")
            return result

        def reserve():
            if review.current is not None:
                service.reserve_question(run, review.current, budget)
                running["discovery"] = review.counts
            else:
                service.reserve_question(run, "system-map", budget)

        self._engage("mapped", WRITING, running, start, beside=("linked",), next_prompt=advance,
                     before_engine=reserve)
        return self.state({})

    @staticmethod
    def _counted(answer: dict, cause: str | None = None, kept: dict = LINKED) -> dict:
        """What the service says was recorded, its fields `kept` (the state's name: the answer's), or why it says
        nothing."""
        if answer.get("status") != "ok":
            return {"state": "failed", "cause": cause or answer.get("reason") or f"the service answered {answer}"[:600]}
        return {"state": "done", "cause": None, **{name: answer[field] for name, field in kept.items()}}

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
                  "/api/app/paths": self.paths, "/api/app/premap": self.premap, "/api/app/graph": self.graph, "/api/app/symbols": self.symbols}
        actions = {**visual.live_actions(active), "/api/app/check": self.check, "/api/app/select": self.select,
                   "/api/app/retry": self.retry, "/api/app/egress": self.hosts,
                   "/api/app/engine": self.configure, "/api/app/probe": self.probe, "/api/app/ask": self.ask,
                   "/api/app/link": self.link, "/api/app/map": self.map}
        stream = {"/api/stream": self.stream(visual.live_stream(active)["/api/stream"])}
        return visual.make_server(None, VIEWER, port, routes=routes, actions=actions, token=token, stream=stream,
                                  mounts={"app": PAGE},
                                  files={**visual.mark_files(self.marks), "/api/app/mark": self.mark})

    def close(self) -> None:
        self._stop.set()
        self.marks.close()


def _held_input() -> int:
    """The standard input of a server in a window, kept for this process alone: the others it starts get an empty one.
    While a read of a pipe waits, Windows makes any other process that holds the same end wait too, when it starts."""
    held = os.dup(0)
    empty = os.open(os.devnull, os.O_RDONLY)
    os.dup2(empty, 0)
    os.close(empty)
    return held


def _when_ended(held: int, stop) -> None:
    """Call `stop` when the input `held` ends, or cannot be read."""
    try:
        while os.read(held, 4096):
            pass
    except OSError:
        pass
    stop()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--work", type=Path, default=Path.home() / ".daodan" / "app",
                        help="where checkouts and their analysis live; default: .daodan/app in the home folder")
    parser.add_argument("--port", type=int, default=0, help="the port on 127.0.0.1; default: a free one")
    parser.add_argument("--desktop", action="store_true",
                        help="for Daodan's window: end when the standard input ends, print the address and nothing "
                             "else, and take a free port when the one asked for cannot be had")
    args = parser.parse_args(argv)
    held = _held_input() if args.desktop else None
    app, token = App(args.work), secrets.token_urlsafe(24)
    try:
        server = app.serve(args.port, token)
    except OSError:
        if not args.desktop or not args.port:
            raise
        server = app.serve(0, token)
    print(f"http://127.0.0.1:{server.server_address[1]}/app/?token={token}", flush=True)
    if held is not None:
        os.dup2(2, 1)  # what this process or one it starts prints from now on goes where the errors go
        threading.Thread(target=_when_ended, args=(held, server.shutdown), daemon=True).start()
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
