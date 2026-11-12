"""Project-bound Codebase Map operations, independent of an MCP runtime.

The caller owns agent execution, authorization and stopping workers. This service
prepares and observes canonical runs; it never starts or cancels an agent. Events
record service operations, while state and delivery checks remain authoritative.
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import hashlib
import json
import os
import tempfile
from pathlib import Path
import re
import shutil
import subprocess
import sys

import card_store
import confinement
import modules as module_graph
import resolve_edges
import retrieval
import semantic_store
import snapshot
import source_reader
from snapshot_store import file_headers, open_snapshot, resolve_run_snapshot, validate_format

_SNAPSHOTS = ContextVar("map_operation_snapshots", default=None)


__all__ = ["MapService"]
EVENT_FILE = "mcp-events.json"
UI_FILE = "ui-requests.json"
UI_KINDS = ("map", "review")
UI_SCOPES = ("global", "changeset", "feature", "prompt")
MAX_UI_REQUESTS = 200  # open requests; done ones beyond MAX_UI_DONE are dropped, oldest first
MAX_UI_DONE = 50
UI_STATES = ("pending", "taken", "done")
MAX_UI_TEXT = 2000
MAX_LIMIT = 1000
MAX_MESSAGE = 10000
MAX_EVENTS = 10000
MAX_ARTIFACT_BYTES = 2_000_000
MAX_READ_CHARS = 4_000_000
COMMAND_TIMEOUT_SECONDS = 600
SCRIPT_DIR = Path(__file__).resolve().parent
RUN_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
            *(f"lpt{i}" for i in range(1, 10))}
FLAGS = {"depth", "critical", "comments", "docs_only", "phase", "skip_synthesis", "skip_interconnect"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id(value: str) -> str:
    if (not isinstance(value, str) or len(value) > 128 or not RUN_ID.fullmatch(value)
            or value in RESERVED):
        raise ValueError("run_id must be an exact lowercase alphanumeric/hyphen name, excluding device names")
    return value


def _relative(value: str, *, root: bool = False) -> str:
    return source_reader._relative(value, allow_root=root)


def _message(value: str) -> str:
    if not isinstance(value, str) or len(value) > MAX_MESSAGE or "\0" in value:
        raise ValueError(f"message must be text of at most {MAX_MESSAGE} characters without NUL")
    return value


def _limit(value: int) -> int:
    if type(value) is not int or not 1 <= value <= MAX_LIMIT:
        raise ValueError(f"limit must be an integer from 1 through {MAX_LIMIT}")
    return value


def _json(path: Path) -> dict:
    confinement.reject_link_chain(path)
    if not path.is_file():
        raise ValueError(f"required regular file is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _evidence_run(run_id: str) -> str:
    """A run that documents, reviews or progresses is never the working run."""
    if run_id == snapshot.WORKING_RUN:
        raise ValueError("the working run has no analysis documents and serves no review or phase; "
                         "use the published run, or a run created for the review")
    return run_id


def _write(path: Path, value: dict) -> None:
    confinement.reject_link_chain(path)
    snapshot._write_json_atomic(path, value)


class MapService:
    """Reuse canonical helpers within one explicit, existing project directory."""

    def __init__(self, project_root, store=None):
        self.project_root = confinement.bind_project(project_root)
        self.store = None if store is None else snapshot.validate_store(store)
        self.root = self.project_root / (self.store or snapshot.CANONICAL_STORE)
        self._outputs = {snapshot.CANONICAL_STORE.split("/")[0]}
        if self.store is not None:
            self._outputs.add(self.store.split("/")[0])

    @contextmanager
    def _operation(self, *, write=False):
        with ExitStack() as snapshots:
            token = _SNAPSHOTS.set(snapshots)
            try:
                confinement.reject_link_chain(self.project_root)
                with confinement.project_lock(self.project_root):
                    confinement.reject_link_chain(self.root)
                    if self.store is not None:
                        self._bind_store(write=write)
                    yield
            finally:
                _SNAPSHOTS.reset(token)

    def _bind_store(self, *, write):
        # A custom store names itself, so standalone CLI commands bind the
        # same project. An existing directory without the matching marker
        # belongs to something else and is never adopted.
        marker = self.root / snapshot.STORE_MARKER
        confinement.reject_link_chain(marker)
        expected = {"schema": snapshot.STORE_SCHEMA, "store": self.store}
        if marker.exists():
            if _json(marker) != expected:
                raise ValueError("analysis store marker names another store")
            return
        if self.root.exists() and (not self.root.is_dir() or any(self.root.iterdir())):
            raise ValueError("analysis store exists without its marker; choose an empty or new directory")
        if write:
            self.root.mkdir(parents=True, exist_ok=True)
            confinement.reject_link_chain(self.root)
            _write(marker, expected)

    def _target(self, value, *, require_exists=True):
        relative = _relative(value, root=True)
        if relative.split("/")[0].casefold() in {name.casefold() for name in self._outputs}:
            raise ValueError("analysis output cannot be the source target")
        target = self.project_root / relative
        confinement.reject_link_chain(target)
        resolved = target.resolve()
        if any(resolved.is_relative_to((self.project_root / name).resolve())
               for name in self._outputs):
            raise ValueError("analysis output cannot be the source target")
        if (require_exists or target.exists()) and not (target.is_dir() or target.is_file()):
            raise ValueError("target must be an existing project-relative file or directory")
        if not resolved.is_relative_to(self.project_root):
            raise ValueError("target is outside the bound project")
        if target.is_file() and (snapshot.is_forbidden(target.name, resolved) or snapshot.is_forbidden(resolved.name, resolved)):
            raise ValueError("forbidden source target")
        return resolved

    def _stored_target(self, value):
        # Canonical shell workflows may persist an absolute target. Client
        # arguments stay relative; stored absolutes must remain project-bound.
        if not isinstance(value, str) or not value or "\0" in value:
            raise ValueError("stored target must be a confined path")
        path = Path(value)
        if path.is_absolute():
            if ".." in value.replace("\\", "/").split("/"):
                raise ValueError("stored target cannot contain traversal")
            try:
                value = path.relative_to(self.project_root).as_posix()
            except ValueError as exc:
                raise ValueError("stored target is outside the bound project") from exc
        return self._target(value, require_exists=False)

    def _manifest_binding(self, run, state, manifest, target):
        snapshot.validate_reuse_manifest(manifest)
        root = Path(manifest["root"])
        if not root.is_absolute() or ".." in root.parts:
            raise ValueError("manifest root must be a canonical absolute path")
        relative_target = _relative(manifest["target"], root=True)
        confinement.reject_link_chain(root)
        if (root / relative_target).resolve() != target:
            raise ValueError("snapshot and state target bindings differ")
        for relative in file_headers(manifest):
            source = root / _relative(relative)
            confinement.reject_link_chain(source)
            if not source.resolve().is_relative_to(self.project_root):
                raise ValueError("manifest source escapes the bound project")
            if source.resolve() != target and not source.resolve().is_relative_to(target):
                raise ValueError("manifest source is outside the bound target")
        if target.exists():
            snapshot._bound_manifest(run, self.root, state)
            return
        # A deleted standalone target changes repo_root()'s answer. History is
        # still readable when the recorded root is its standalone base or the
        # repository of its nearest existing ancestor. Execution stays blocked.
        file_target = relative_target in file_headers(manifest)
        base = target.parent if file_target else target
        ancestor = base
        while not ancestor.exists():
            ancestor = ancestor.parent
        expected = {base, snapshot.repo_root(ancestor).resolve()}
        if root.resolve() not in expected:
            raise ValueError("missing target has an inconsistent recorded repository binding")

    def _source_paths(self, target):
        # Snapshot helpers read source files after walking the canonical
        # perimeter. Reject links on those candidates before invoking parsers.
        for path in snapshot.iter_files(target):
            confinement.reject_link_chain(path)

    def _run_path(self, run_id):
        path = self.root / "runs" / _run_id(run_id)
        confinement.reject_link_chain(path)
        return path

    def _bound_run(self, run_id):
        run = self._run_path(run_id)
        if not run.is_dir():
            raise ValueError(f"run does not exist in the bound project: {run_id}")
        state = _json(run / "state.json")
        if state.get("run_id") != run_id or state.get("mode") not in ("classic", "team"):
            raise ValueError("run state identity or mode is invalid")
        target = self._stored_target(state.get("target"))
        flags = state.get("flags")
        if not isinstance(flags, dict) or set(flags) - FLAGS:
            raise ValueError("state contains unsupported mode flags")
        snapshot._effective_flags(flags)
        if state.get("parent_run") is not None:
            self._run_path(state["parent_run"])
        for name in ("changes.json", "carry.json", EVENT_FILE):
            confinement.reject_link_chain(run / name)
        manifest = open_snapshot(resolve_run_snapshot(run, state))
        snapshots = _SNAPSHOTS.get()
        if snapshots is None:
            manifest.close()
            raise ValueError("bound run requires an operation context")
        snapshots.enter_context(manifest)
        self._manifest_binding(run, state, manifest, target)
        self._validate_artifact_paths(run, state)
        if state.get("delivery") is not None:
            snapshot._validate_delivery(run, self.root, state)
        return run, state, manifest, target

    def _validate_artifact_paths(self, run, state):
        # Helpers read these fixed inputs before validating their declaration.
        # Include optional inputs and possible unexpected phase files as well.
        names = {*snapshot.PHASE_FILES, "knowledge/navigation.md", "knowledge/documentation-leads.md",
                 "comment_health.md", "changes.md", "snapshot/engine-edges.sqlite", "snapshot/retrieval.sqlite",
                 "snapshot/engine-report.json", "snapshot/engine-pass.running", "snapshot/engine-pass.log",
                 "snapshot/modules.json", "snapshot/modules.md", "snapshot/proposals.json", "snapshot/context",
                 "cards.sqlite"}
        for path in run.glob("[0-9][0-9]-*.md"):
            confinement.reject_link_chain(path)
        delivery = state.get("delivery")
        if delivery is not None:
            artifacts = delivery.get("artifacts") if isinstance(delivery, dict) else None
            if not isinstance(artifacts, dict):
                raise ValueError("invalid delivery artifact declaration")
            for name in artifacts:
                if name != "knowledge/":
                    _relative(name)
                    names.add(name)
        for name in names:
            confinement.reject_link_chain(run / name)

    def _status(self, run_id, *, engine=False):
        run, state, manifest, target = self._bound_run(run_id)
        project = self.project_root.as_posix()
        if not target.exists():
            return {"run_id": run_id, "project_root": project, "state": state, "check": None,
                    "source_available": False,
                    "check_unavailable": "source target is missing; canonical delivery/freshness check is unavailable"}
        checked = snapshot.check_delivery(run) if state.get("delivery") is not None else None
        result = {"run_id": run_id, "project_root": project, "state": state, "check": checked,
                  "source_available": True}
        if engine:
            result["engine"] = self._engine(state, manifest.path, repair=False)
        return result

    def _engine(self, state, manifest, *, repair, environment=None):
        """The run's engine store, repaired when asked, unless the run declined the pass.

        `environment` is the project's Python environment for a pass that starts now:
        a path, `none`, or nothing for the one Daodan finds or builds."""
        if state.get("engine", True) is False:
            return {"state": "off", "action": "none", "reason": "the run was created with engine=false",
                    "resolution": resolve_edges.edge_state(manifest).get("resolution")}
        if not repair:
            return resolve_edges.edge_state(manifest)
        offered = None if environment in (None, "auto") else [Path(environment)]
        return resolve_edges.ensure_edges(manifest, environments=offered)

    def _update_state(self, run, updates, *, remove=()):
        # Workers write state.json outside the service lock. Re-read just
        # before writing and change only the keys this operation owns.
        state = _json(run / "state.json")
        state.update(updates)
        for key in remove:
            state.pop(key, None)
        _write(run / "state.json", state)
        return state

    def _journal(self, run):
        path = run / EVENT_FILE
        confinement.reject_link_chain(path)
        if not path.exists():
            return []
        value = _json(path)
        events = value.get("events")
        if value.get("schema") != 1 or not isinstance(events, list):
            raise ValueError("invalid MCP event journal")
        for cursor, event in enumerate(events, 1):
            if (not isinstance(event, dict) or type(event.get("cursor")) is not int
                    or event["cursor"] != cursor or event.get("run_id") != run.name):
                raise ValueError("invalid MCP event ordering or run binding")
        return events

    def _event(self, run, event, *, phase=None, message=""):
        events = self._journal(run)
        if len(events) >= MAX_EVENTS:
            raise ValueError(f"event journal reached {MAX_EVENTS} events; canonical state remains authoritative")
        item = {"cursor": len(events) + 1, "run_id": run.name, "timestamp": _now(),
                "event": event, "message": message}
        if phase is not None:
            item["phase"] = phase
        events.append(item)
        _write(run / EVENT_FILE, {"schema": 1, "events": events})
        return item

    def _command(self, command, *args):
        # Existing CLI commands own mode selection and resume provenance. A
        # child process captures their output without redirecting global stdout.
        # Its working directory is the helper directory, never the analyzed
        # project, whose own executables Windows would otherwise search first.
        try:
            result = subprocess.run(
                [sys.executable, "-B", str(Path(snapshot.__file__)), command, *map(str, args)],
                cwd=SCRIPT_DIR, capture_output=True, text=True, timeout=COMMAND_TIMEOUT_SECONDS,
            )
        except subprocess.SubprocessError as exc:
            raise ValueError(f"canonical {command} command did not finish: {exc}") from exc
        try:
            value = json.loads(result.stdout)
        except ValueError as exc:
            raise ValueError(f"canonical {command} returned invalid output: {result.stderr.strip()}") from exc
        if result.returncode or not isinstance(value, dict):
            raise ValueError(f"canonical {command} failed: {value}")
        return value

    def scope(self, target="."):
        with self._operation():
            bound = self._target(target)
            self._source_paths(bound)
            return dict(self._command("scope", bound), project_root=self.project_root.as_posix())

    def create_run(self, target, run_id, depth="full", critical=False, comments=False,
                   docs_only=False, phase=None, stop_after=None, format="sqlite", engine=True):
        _evidence_run(_run_id(run_id))
        validate_format(format)
        if type(engine) is not bool:
            raise ValueError("engine must be a boolean")
        flags = {"depth": depth, "critical": critical, "comments": comments,
                 "docs_only": docs_only, "phase": phase}
        snapshot._effective_flags(flags)
        if stop_after is not None and (type(stop_after) is not int or stop_after not in range(1, 7)
                                       or phase is not None or docs_only):
            raise ValueError("stop_after accepts 1 through 6 without phase or docs_only")
        bound = self._target(target)
        self._source_paths(bound)
        with self._operation(write=True):
            run = self._run_path(run_id)
            if run.exists():
                raise ValueError("run already exists; resume the exact run or choose another run_id")
            self.root.mkdir(parents=True, exist_ok=True)
            confinement.reject_link_chain(self.root)
            descriptor, name = tempfile.mkstemp(prefix=f".{run_id}-snapshot-", dir=self.root)
            os.close(descriptor)
            temporary = Path(name)
            temporary.unlink()
        try:
            metadata = snapshot.write_snapshot(bound, temporary, format=format)
            with self._operation(write=True):
                if self._target(target) != bound:
                    raise ValueError("target binding changed while building the snapshot")
                run = self._run_path(run_id)
                if run.exists():
                    raise ValueError("run already exists; resume the exact run or choose another run_id")
                state = {"run_id": run_id, "target": bound.relative_to(self.project_root).as_posix(),
                         "mode": "classic", "status": "in_progress", "flags": flags,
                         "started_at": _now(), "updated_at": _now(), "parent_run": None,
                         "incremental": None, "current_phase": 0, "completed_phases": [],
                         "files_created": [], "git": metadata.get("git"), "engine": engine,
                         "snapshot": {"format": format, "path": f"snapshot/manifest.{format}",
                                      "storage_version": 1}}
                run.mkdir(parents=True)
                try:
                    (run / "snapshot").mkdir()
                    os.replace(temporary, run / state["snapshot"]["path"])
                    _write(run / "state.json", state)
                    index = retrieval.ensure_index(run / state["snapshot"]["path"])
                    arguments = [run]
                    if stop_after is not None:
                        arguments.extend(["--stop-after", stop_after])
                    self._command("prepare", *arguments)
                    snapshot.update_registration(run, active=True)
                except BaseException:
                    shutil.rmtree(run, ignore_errors=True)
                    raise
                self._event(run, "run_created")
                if index["state"] != "fresh":
                    # The run stays usable without its index: searches report the gap
                    # and codebase_map_index repairs it.
                    self._event(run, "index_failed", message=f"{index['state']}: {index['reason']}")
                graph = module_graph.ensure_graph(run / state["snapshot"]["path"])
                if graph["state"] != "fresh":
                    # Likewise without its module graph: module queries report the
                    # gap and codebase_map_modules(refresh=true) rebuilds it.
                    self._event(run, "modules_failed", message=f"{graph['state']}: {graph.get('reason', '')}")
                # The call-resolution pass runs beside the run, never inside it:
                # consumers read its store as soon as it lands.
                self._engine_event(run, self._engine(state, run / state["snapshot"]["path"], repair=True))
                return self._status(run_id, engine=True)
        finally:
            temporary.unlink(missing_ok=True)

    def status(self, run_id):
        with self._operation():
            return self._status(run_id, engine=True)

    def _engine_event(self, run, result):
        if result.get("action") == "started":
            self._event(run, "engine_started", message=f"pid {result.get('pid')}")
        elif result.get("state") in ("unavailable", "failed"):
            self._event(run, f"engine_{result['state']}", message=str(result.get("reason") or "")[:MAX_MESSAGE])

    def runs(self):
        with self._operation():
            directory = self.root / "runs"
            confinement.reject_link_chain(directory)
            values = []
            if directory.exists():
                if not directory.is_dir():
                    raise ValueError("analysis runs root must be a directory")
                for path in sorted(directory.iterdir()):
                    try:
                        confinement.reject_link_chain(path)
                        if path.is_dir():
                            values.append(dict(self._status(path.name), readable=True))
                    except (ValueError, OSError, TypeError, KeyError) as exc:
                        # One damaged or foreign run must not hide the others.
                        values.append({"run_id": path.name, "readable": False, "error": str(exc)})
            registry = self.root / "runs.json"
            confinement.reject_link_chain(registry)
            return {"runs": values, "registry": snapshot._read_registry(self.root) if registry.exists() else None}

    def search(self, run_id, query, anchors=None, limit=20):
        """Rank the run's lexical index for `query`; a non-fresh index is a gap, never an error."""
        if not isinstance(query, str) or len(query) > 16_384:
            raise ValueError("query must be text of at most 16384 characters")
        if anchors is None:
            anchors = []
        if not isinstance(anchors, list) or len(anchors) > 100:
            raise ValueError("anchors must be a list of at most 100 anchors")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 through 100")
        with self._operation():
            _, _, manifest, _ = self._bound_run(run_id)
            if gate := snapshot.query_gate(manifest.path):
                return gate
            state = retrieval.index_state(manifest.path)
            if state["state"] != "fresh":
                return {**retrieval.gap_result(state, limit, f"codebase_map_index(run_id={run_id!r})"), "run_id": run_id}
            result = retrieval.search(retrieval.index_name(manifest.path), query, anchors=anchors, limit=limit,
                                      verify=False)
            return {**retrieval.public_result(result), "run_id": run_id, "index_state": "fresh"}

    def index(self, run_id, check=False, break_lock=False, environment=None):
        """Report or repair the run's lexical index beside its snapshot."""
        if not isinstance(check, bool) or not isinstance(break_lock, bool):
            raise ValueError("check and break_lock must be booleans")
        if environment is not None and (not isinstance(environment, str) or not environment.strip()
                                        or len(environment) > 1000):
            raise ValueError("environment must be auto, none or the path of a Python environment")
        with self._operation(write=not check):
            run, state, manifest, _ = self._bound_run(run_id)
            result = retrieval.ensure_index(manifest.path, check=check, break_lock=break_lock)
            if not check and result.get("action") in ("rebuilt", "refreshed"):
                self._event(run, "index_refreshed", message=result["action"])
            engine = self._engine(state, manifest.path, repair=not check, environment=environment)
            if not check:
                self._engine_event(run, engine)
            return {**result, "engine": engine, "run_id": run_id}

    def modules(self, run_id, query=None, refresh=False, brief=False, limit=10, proposals=None, replace_proposals=False):
        """Modules of the bound run: summary, the candidates for a name, the brief for a model, or proposals.

        `refresh` rebuilds a missing or stale graph from the bound snapshot.
        `proposals` records a model's module proposals beside the snapshot and
        rebuilds; every member is verified, nothing is promoted.
        """
        for name, value in (("refresh", refresh), ("brief", brief), ("replace_proposals", replace_proposals)):
            if type(value) is not bool:
                raise ValueError(f"{name} must be a boolean")
        if query is not None and (not isinstance(query, str) or not query.strip() or len(query) > 1000):
            raise ValueError("query must be text of at most 1000 characters")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 through 100")
        if proposals is not None and not isinstance(proposals, list):
            raise ValueError("proposals must be a list of module records")
        with self._operation(write=refresh or proposals is not None):
            run, _, manifest, _ = self._bound_run(run_id)
            if proposals is not None:
                report = module_graph.propose(manifest.path, proposals, replace=replace_proposals)
                self._event(run, "modules_proposed", message=f"{report['accepted']} proposals")
                if query is None and not brief:
                    return dict(report, run_id=run_id)
            elif refresh:
                result = module_graph.ensure_graph(manifest.path)
                if result.get("action") in ("rebuilt", "refreshed"):
                    self._event(run, "modules_refreshed", message=result["action"])
            if gate := snapshot.query_gate(manifest.path):
                return gate
            if query is not None:
                return dict(module_graph.query_manifest(manifest.path, query, limit=limit), run_id=run_id)
            if brief:
                return dict(module_graph.brief(manifest.path), run_id=run_id)
            state = module_graph.graph_state(manifest.path)
            summary = {"run_id": run_id, "graph_state": state["state"], "state": state}
            if state["state"] in ("fresh", "stale"):
                graph = module_graph.load_graph(Path(state["graph"]))
                summary.update(
                    binding=graph["binding"], coverage=graph["coverage"], changes=graph.get("changes"),
                    modules=[{key: m[key] for key in ("id", "name", "aliases", "provenance", "kind", "description",
                                                      "responsibility", "status", "paths", "excluded", "coverage")}
                             | {"members": [x["id"] for x in m["members"]],
                                "conflicts": len(m["conflicts"]), "gaps": len(m["gaps"])}
                             for m in graph["modules"]],
                    edges=[{key: e[key] for key in ("kind", "source", "target", "status", "evidence_total")}
                           for e in graph["edges"]],
                    gaps=graph["gaps"], notes=graph["notes"])
            return summary

    def outline(self, run_id, path=None, pattern=None, limit=100):
        _limit(limit)
        if path is not None:
            _relative(path)
        if pattern is not None and (not isinstance(pattern, str) or len(pattern) > 1000):
            raise ValueError("pattern must be text of at most 1000 characters")
        with self._operation():
            _, _, manifest, _ = self._bound_run(run_id)
            if gate := snapshot.query_gate(manifest.path):
                return gate
            return dict(source_reader.outline_manifest(manifest, path, pattern, limit), run_id=run_id)

    def flows(self, run_id, rules=None, start=None, direction="from", level="fisico", limit=100, card=None,
              brief=False, map=None, about=None, levels=None):
        """Flows of the bound run from its link rules: the summary, or one flow at a level.

        `rules` records the project's link rules beside the snapshot. Without recorded
        rules the answer is the rule format, for a model to write them. `card` records
        the model's card of the flow at `start`; a flow answer carries its card, stale
        when a file of the flow changed since. The system map: `brief` gives the system
        brief, its format and the areas; `map` records a proposal and reports it; `about`
        answers for an area, a flow or a node, and with `levels` shows a flow at those levels.
        """
        import flows as flow_model
        import system_levels
        asked = [name for name, value in (("brief", brief), ("map", map is not None), ("about", about is not None),
                                          ("start", start is not None)) if value]
        if len(asked) > 1:
            raise ValueError("ask one of brief, map, about or start")
        if levels is not None and (about is None or not isinstance(levels, list)
                                   or not levels or any(lv not in system_levels.LEVELS for lv in levels)):
            raise ValueError("levels go with about and are one or more of " + ", ".join(system_levels.LEVELS))
        if about is not None and (not isinstance(about, str) or not about.strip() or len(about) > 200):
            raise ValueError("about must be a name of at most 200 characters")
        if direction not in ("from", "to", "through") or level not in flow_model.LEVELS:
            raise ValueError("direction is from, to or through; level is " + ", ".join(flow_model.LEVELS))
        if start is not None and (not isinstance(start, str) or not start.strip() or len(start) > 1000):
            raise ValueError("start must be a node of at most 1000 characters")
        _limit(limit)
        if rules is not None:
            if not isinstance(rules, list) or not rules:
                raise ValueError("rules must be a nonempty list")
            flow_model.validate_rules(rules)
        if card is not None and (start is None or direction == "through"):
            raise ValueError("a card belongs to one flow: give start and direction from or to")
        with self._operation(write=rules is not None or card is not None or map is not None):
            _, _, manifest, _ = self._bound_run(run_id)
            if gate := snapshot.query_gate(manifest.path):
                return gate
            recorded = manifest.path.with_name("flow-rules.json")
            if rules is not None:
                _write(recorded, {"schema": flow_model.RULES_SCHEMA, "rules": rules})
            if not recorded.is_file():
                return {"status": "needs_rules", "run_id": run_id,
                        "format": flow_model.__doc__.split("    python flows.py")[0].strip()}
            if brief or map is not None or about is not None:
                return {"status": "ok", "run_id": run_id,
                        **self._system_map(manifest.path, flow_model.load_rules(recorded), brief, map, about, levels)}
            links = flow_model.cached_links(manifest.path, flow_model.load_rules(recorded))
            if start is None:
                return {"status": "ok", "run_id": run_id, "entries": links["entries"][:limit],
                        "entry_count": len(links["entries"]), "routes": links["routes"],
                        "stores": {name: {key: len(value) for key, value in store.items()}
                                   for name, store in list(links["stores"].items())[:limit]},
                        "store_count": len(links["stores"]), "gaps": links["gaps"][:limit],
                        "gap_count": len(links["gaps"]), "external": links["external"]}
            flow = flow_model.trace(links, start, direction)
            if direction != "through":
                cards_path = manifest.path.with_name("flow-cards.json")
                cards = _json(cards_path) if cards_path.is_file() else {"schema": "daodan/flow-cards/v1", "cards": {}}
                key = f"{direction}:{start}"
                with snapshot.open_snapshot(manifest.path) as store:
                    hashes = {rel: entry.get("hash") for rel, entry in snapshot.file_headers(store).items()}
                if card is not None:
                    flow_model.check_card(card, flow)
                    cards["cards"][key] = {**card, "files": {rel: hashes.get(rel) for rel in flow_model.card_files(flow)}}
                    _write(cards_path, cards)
                kept = cards["cards"].get(key)
                if kept is not None:
                    changed = sorted(rel for rel, digest in kept["files"].items() if hashes.get(rel) != digest)
                    flow["card"] = {**{name: kept[name] for name in ("name", "type", "text")},
                                    "fresh": not changed, "changed_files": changed[:limit]}
                flow = flow_model.at_level(
                    flow, level, flow_model.file_modules(manifest.path) if level == "logico" else {})
                flow["edge_count"] = len(flow["edges"])
                flow["edges"] = flow["edges"][:limit]
            return {"status": "ok", "run_id": run_id, **flow}

    @staticmethod
    def _system_map(manifest, rules, brief, proposal, about, levels):
        import system_brief
        import system_levels
        import system_map
        if brief:
            value = system_brief.brief(manifest, rules)
            reference = Path(__file__).resolve().parent.parent / "references" / "system-map.md"
            return {"brief": value["text"], "truncated": value["truncated"], "steps": value["steps"],
                    "format": reference.read_text(encoding="utf-8"), "areas": list(system_map.AREAS)}
        if proposal is not None:
            return system_map.record(manifest, rules, proposal)
        system = system_map.load(manifest, rules)
        if system is None:
            return {"status": "no_map", "reason": "no system map is recorded: propose one with map"}
        if levels:
            import flows as flow_model
            links = flow_model.cached_links(manifest, rules) if "codice" in levels else None
            return system_levels.view(system, about, levels, links)
        return system_map.about(system, about)

    def _engine_store(self, run, value):
        name = "snapshot/engine-edges.sqlite" if value is None else value
        _relative(name)
        path = run / name
        if path.suffix != ".sqlite" or path.name in {"manifest.sqlite", "cards.sqlite", "retrieval.sqlite", "engine-answers.sqlite"}:
            raise ValueError("engine_store must name an engine SQLite artifact within its run")
        confinement.reject_link_chain(path)
        if not path.resolve().is_relative_to(run.resolve()):
            raise ValueError("engine_store is outside its run")
        return path

    def graph(self, run_id, paths=None, hops=2, limit=100, engine_store=None):
        _limit(limit)
        if paths is not None:
            if not isinstance(paths, list) or not paths:
                raise ValueError("paths must be a nonempty list or null")
            for path in paths:
                _relative(path)
        with self._operation():
            run, _, manifest, _ = self._bound_run(run_id)
            if gate := snapshot.query_gate(manifest.path):
                return gate
            return dict(source_reader.graph_packet(manifest, paths, hops, limit,
                        engine_store=self._engine_store(run, engine_store)), run_id=run_id)

    def read(self, run_id, requests):
        if not isinstance(requests, list) or not 1 <= len(requests) <= MAX_LIMIT:
            raise ValueError(f"requests must be a list containing 1 through {MAX_LIMIT} selections")
        with self._operation():
            _, _, manifest, _ = self._bound_run(run_id)
            if gate := snapshot.query_gate(manifest.path):
                return gate
            packet = dict(source_reader.read_packet(manifest, requests), run_id=run_id)
        if len(json.dumps(packet)) > MAX_READ_CHARS:
            raise ValueError(f"read result exceeds {MAX_READ_CHARS} characters; request fewer files, symbols or ranges")
        return packet

    def edit_impact(self, run_id, targets, neighbors=20, history=5, include_source=True,
                    hops=1, include_neighbor_source=False, include_slices=False,
                    budget_chars=semantic_store.DEFAULT_IMPACT_BUDGET_CHARS, engine_store=None):
        for name, value in (("include_source", include_source),
                            ("include_neighbor_source", include_neighbor_source),
                            ("include_slices", include_slices)):
            if type(value) is not bool:
                raise ValueError(f"{name} must be a boolean")
        with self._operation():
            run, _, manifest, _ = self._bound_run(run_id)
            if gate := snapshot.query_gate(manifest.path):
                return gate
            packet = dict(semantic_store.build_edit_impact(
                manifest, targets, cards_path=self.root / card_store.CARD_STORE_NAME,
                neighbors=neighbors, history=history, include_source=include_source, hops=hops,
                include_neighbor_source=include_neighbor_source, include_slices=include_slices,
                budget_chars=budget_chars, engine_store=self._engine_store(run, engine_store)), run_id=run_id)
        if len(json.dumps(packet)) > MAX_READ_CHARS:
            raise ValueError(f"edit impact exceeds {MAX_READ_CHARS} characters; request fewer targets or neighbors")
        return packet

    def context(self, run_id, request, recipient, out='context', cursor=None, base_run_id=None, embedding_result=None):
        """Create a bounded evidence packet within an already bound analysis run."""
        import context_packet
        _evidence_run(run_id)
        with self._operation(write=True):
            run, _, manifest, _ = self._bound_run(run_id)
            out = _relative(out)
            output = manifest.path.parent / out
            confinement.reject_link_chain(output)
            checkpoint = None
            if cursor is not None:
                checkpoint = run / _relative(cursor)
                confinement.reject_link_chain(checkpoint)
            request = dict(request)
            base_engine = None
            if base_run_id is not None:
                base_run, _, base, _ = self._bound_run(base_run_id)
                expected_base = {'manifest': str(base.path)}
                if request.get('base') not in (None, expected_base):
                    raise ValueError('context base differs from the independently bound base run')
                request['base'] = expected_base
                base_engine = str(base.path.parent / 'engine-edges.sqlite')
            elif request.get('base') is not None:
                raise ValueError('context base requires a bound base_run_id')
            authority = {'root': str(self.project_root), 'source_root': str(Path(manifest['root'])),
                         'read_boundary': [manifest['target']], 'write_boundary': []}
            indexes = {'cards': str(self.root / card_store.CARD_STORE_NAME)}
            # Name the lexical index only when it is on disk: an absent index is the
            # planner's `retrieval_missing` gap, not an unreadable database.
            if retrieval.index_name(manifest.path).is_file():
                indexes['retrieval'] = str(retrieval.index_name(manifest.path))
            if embedding_result is not None:
                dense = run / _relative(embedding_result)
                confinement.reject_link_chain(dense)
                if not dense.is_relative_to(manifest.path.parent) or dense.suffix != '.json':
                    raise ValueError('embedding receipt must be a JSON inside the bound snapshot directory')
                indexes['embedding_result'] = str(dense)
            if base_engine is not None:
                indexes['base_engine'] = base_engine
            result = context_packet.create_context(manifest.path, request, recipient,
                authority=authority, out=output, cursor=checkpoint, indexes=indexes)
            return dict(result, run_id=run_id, cursor=Path(result['cursor_path']).relative_to(run).as_posix())

    def symbols_at(self, run_id, requests=None, base_run_id=None, diff=None):
        if diff is not None:
            if requests is not None:
                raise ValueError("symbols-at takes either requests or a diff, not both")
            if not isinstance(base_run_id, str) or not base_run_id:
                raise ValueError("symbols-at diff mode requires base_run_id")
            if not isinstance(diff, str) or len(diff) > snapshot.MAX_DIFF_CHARS:
                raise ValueError(f"diff must be text of at most {snapshot.MAX_DIFF_CHARS} characters")
        elif base_run_id is not None:
            raise ValueError("base_run_id requires a diff")
        with self._operation():
            _, _, candidate, _ = self._bound_run(run_id)
            if gate := snapshot.query_gate(candidate.path):
                return gate
            if diff is not None:
                _, _, base, _ = self._bound_run(base_run_id)
                packet = snapshot.symbols_at(candidate, base=base, diff=diff)
            else:
                packet = snapshot.symbols_at(candidate, requests)
            return dict(packet, run_id=run_id)

    def stale_callers(self, run_id, base_run_id, limit=100,
                      base_engine_store=None, candidate_engine_store=None):
        _limit(limit)
        if not isinstance(base_run_id, str) or not base_run_id:
            raise ValueError("stale-callers requires base_run_id")
        with self._operation():
            candidate_run, _, candidate, _ = self._bound_run(run_id)
            base_run, _, base, _ = self._bound_run(base_run_id)
            return dict(semantic_store.build_stale_callers(base, candidate, limit=limit,
                        base_engine_store=self._engine_store(base_run, base_engine_store),
                        candidate_engine_store=self._engine_store(candidate_run, candidate_engine_store)),
                        run_id=run_id, base_run_id=base_run_id)

    def meta_query(self, run_id, paths=None, symbol=None, freshness=None, include_history=True, limit=100):
        _limit(limit)
        if paths is not None:
            if not isinstance(paths, list) or not paths:
                raise ValueError("paths must be a nonempty list or null")
            for path in paths:
                _relative(path)
        if symbol is not None and (not isinstance(symbol, str) or len(symbol) > 1000):
            raise ValueError("symbol must be text of at most 1000 characters")
        if freshness is not None and not isinstance(freshness, str):
            raise ValueError("freshness must be text")
        with self._operation():
            _, _, manifest, _ = self._bound_run(run_id)
            return dict(semantic_store.query_meta_code(
                manifest, cards_path=self.root / card_store.CARD_STORE_NAME,
                paths=paths, symbol=symbol, freshness=freshness,
                include_history=bool(include_history), limit=limit), run_id=run_id)

    def diff(self, run_id):
        with self._operation():
            _, _, manifest, target = self._bound_run(run_id)
            available = target.exists()
            raw_hashes = {}
            if available:
                self._source_paths(target)
                comparison = snapshot.compare_files(manifest, target, verify=True, raw_hashes=raw_hashes)
            else:
                comparison = {"added": [], "removed": sorted(file_headers(manifest)),
                              "modified": [], "unchanged": [], "current": {}}
            symbols = snapshot.compare_symbols(manifest, comparison)
            files = {key: comparison[key] for key in ("added", "removed", "modified")}
            # Normalized hashes intentionally ignore CRLF. Byte freshness still
            # matters to verified readers and resume, so expose it separately.
            raw_changed = sorted(name for name in comparison["unchanged"]
                                 if raw_hashes.get(name) != file_headers(manifest)[name].get("raw_hash"))
            parser_changed = manifest.get("parser_fingerprint") != snapshot.parser_fingerprint()
            return {"run_id": run_id, "files": files,
                    "symbols": {key: symbols[key] for key in ("added", "removed", "changed")},
                    "raw_changed": raw_changed, "parser_changed": parser_changed,
                    "source_available": available,
                    "unchanged": available and not any(files.values()) and not raw_changed and not parser_changed}

    def artifact(self, run_id, name):
        _relative(name)
        _evidence_run(run_id)
        with self._operation():
            run, state, _, _ = self._bound_run(run_id)
            delivery = snapshot._validate_delivery(run, self.root, state)
            allowed = {key for key, item in delivery["artifacts"].items()
                       if item["status"] != "skipped" and key != "knowledge/"}
            if delivery["artifacts"].get("knowledge/", {}).get("status") != "skipped":
                allowed.update({"knowledge/navigation.md", "knowledge/documentation-leads.md"})
            if name not in allowed:
                raise ValueError("artifact is not declared by this run")
            path = run / name
            confinement.reject_link_chain(path)
            if not path.is_file():
                raise ValueError("declared artifact has not been delivered")
            digest = hashlib.sha256()
            size = 0
            head = b""
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1 << 20), b""):
                    digest.update(chunk)
                    if size < MAX_ARTIFACT_BYTES:
                        head += chunk[:MAX_ARTIFACT_BYTES - size]
                    size += len(chunk)
            truncated = size > MAX_ARTIFACT_BYTES
            content = head.decode("utf-8-sig", errors="replace" if truncated else "strict")
            return {"run_id": run_id, "name": name, "content": content, "bytes": size,
                    "truncated": truncated, "sha256": digest.hexdigest()}

    def checkpoint(self, run_id, phase, event, message=""):
        if type(phase) is not int or phase not in range(9):
            raise ValueError("phase must be an integer from 0 through 8")
        if event not in ("phase_started", "phase_completed", "blocked"):
            raise ValueError("event must be phase_started, phase_completed or blocked")
        _message(message)
        _evidence_run(run_id)
        with self._operation(write=True):
            run, state, _, target = self._bound_run(run_id)
            if state.get("status") != "in_progress":
                raise ValueError("checkpoint requires an in-progress run; resume first")
            if not target.exists() and event != "blocked":
                raise ValueError("source target is missing; restore it before executing phases")
            delivery = snapshot._validate_delivery(run, self.root, state)
            if phase not in delivery.get("run_phases", []):
                raise ValueError("phase is not selected for this invocation")
            if event == "phase_completed":
                checked = snapshot.check_delivery(run)
                names = {name for name, item in delivery["artifacts"].items()
                         if item["phase"] == phase and item["status"] == "produced"}
                bad = set(checked["missing"] + checked["empty"] + checked["invalid_inherited"])
                bad.update(marker["artifact"] for marker in checked["stale"])
                if (not names or names & bad or names & set(checked["not_yet_produced"])
                        or (checked["undocumented_added"] and phase in range(1, 7))):
                    raise ValueError("phase has missing, empty, stale or otherwise invalid declared outputs")
            current = _json(run / "state.json")
            updates = {"updated_at": _now()}
            if event == "phase_completed":
                completed = current.get("completed_phases", [])
                if not isinstance(completed, list) or any(type(value) is not int for value in completed):
                    raise ValueError("invalid completed_phases state")
                updates["completed_phases"] = sorted(set(completed) | {phase})
            # Progress only advances; resume is what moves it back.
            recorded = current.get("current_phase")
            updates["current_phase"] = max(phase, recorded) if type(recorded) is int else phase
            if event == "blocked":
                updates["blocker"] = message
            self._update_state(run, updates, remove=() if event == "blocked" else ("blocker",))
            self._event(run, event, phase=phase, message=message)
            return self._status(run_id)

    def _ui(self):
        path = self.root / UI_FILE
        confinement.reject_link_chain(path)
        if not path.exists():
            return []
        requests = _json(path).get("requests")
        if not isinstance(requests, list) or not all(
                isinstance(item, dict) and type(item.get("id")) is int and item.get("state") in UI_STATES
                and isinstance(item.get("results", []), list) for item in requests):
            raise ValueError("invalid explorer request file")
        return requests

    def _ui_write(self, requests):
        self.root.mkdir(parents=True, exist_ok=True)
        _write(self.root / UI_FILE, {"schema": 1, "requests": requests})

    def _ui_result(self, relative):
        """A result's findings and gaps, parsed again only when the file changed."""
        path = self.project_root / relative
        confinement.reject_link_chain(path)
        info = path.stat()
        key = (info.st_mtime_ns, info.st_size)
        cache = self.__dict__.setdefault("_ui_cache", {})
        if cache.get(relative, (None,))[0] != key:
            record = _json(path)
            findings = record.get("retained_findings", record.get("findings"))
            if not isinstance(findings, list):
                raise ValueError(f"{relative}: no retained_findings or findings list")
            gaps = record.get("gaps")
            gaps = [] if gaps in (None, "", []) else gaps if isinstance(gaps, list) else [gaps]
            cache[relative] = (key, [item for item in findings if isinstance(item, dict)], gaps)
        return cache[relative][1], cache[relative][2]

    def ui_request(self, kind, scope, text=""):
        """Record what the person asked in the explorer; the host session takes it with `ui_requests`."""
        if kind not in UI_KINDS or scope not in UI_SCOPES:
            raise ValueError(f"kind is one of {UI_KINDS} and scope one of {UI_SCOPES}")
        if not isinstance(text, str) or len(text) > MAX_UI_TEXT or "\0" in text:
            raise ValueError(f"text must be at most {MAX_UI_TEXT} characters without NUL")
        if scope in ("feature", "prompt") and not text.strip():
            raise ValueError(f"a {scope} request needs its text")
        with self._operation(write=True):
            requests = self._ui()
            done = [item["id"] for item in requests if item["state"] == "done"][-MAX_UI_DONE:]
            requests = [item for item in requests if item["state"] != "done" or item["id"] in done]
            if len(requests) - len(done) >= MAX_UI_REQUESTS:
                raise ValueError(f"the explorer already holds {MAX_UI_REQUESTS} open requests")
            item = {"id": max((item["id"] for item in requests), default=0) + 1, "kind": kind, "scope": scope, "text": text.strip(),
                    "state": "pending", "created_at": _now()}
            self._ui_write([*requests, item])
            return item

    def ui_requests(self, take=False, release=()):
        """The explorer's requests; `release` moves the named taken ones back to pending, then `take`
        moves the pending ones to `taken` and names them."""
        release = list(release)
        if not all(type(item) is int for item in release):
            raise ValueError("release names request ids")
        with self._operation(write=take or bool(release)):
            requests = self._ui()
            released = [item["id"] for item in requests if item["id"] in release and item["state"] == "taken"]
            if len(released) != len(set(release)):
                raise ValueError("only a taken request can be released")
            for item in requests:
                if item["id"] in released:
                    item["state"] = "pending"
            taken = [item["id"] for item in requests if item["state"] == "pending"] if take else []
            for item in requests:
                if item["id"] in taken:
                    item["state"] = "taken"
            if taken or released:
                self._ui_write(requests)
            return {"requests": requests, "taken": taken, "released": released}

    def ui_done(self, request_id, results=(), message=""):
        """Close a taken request with the project-relative JSON results whose findings the explorer shows."""
        paths = [_relative(path) for path in results]
        _message(message)
        with self._operation(write=True):
            requests = self._ui()
            item = next((item for item in requests if item["id"] == request_id), None)
            if item is None or item["state"] != "taken":
                raise ValueError("only a taken request can be closed")
            for path in paths:
                self._ui_result(path)
            item.update(state="done", results=paths, message=message, done_at=_now())
            self._ui_write(requests)
            return item

    def ui_findings(self):
        """Findings and gaps of the closed requests, read from their results now; an unreadable result is a gap."""
        with self._operation():
            findings, gaps = [], []
            for item in self._ui():
                for path in item.get("results", ()):
                    try:
                        found, declared = self._ui_result(path)
                    except (ValueError, OSError) as exc:
                        gaps.append(f"{path}: {exc}")
                        continue
                    findings.extend({**finding, "request": item["id"]} for finding in found)
                    gaps.extend(declared)
            return {"findings": findings, "gaps": gaps}

    def events(self, run_id, after=0, limit=100):
        if type(after) is not int or after < 0:
            raise ValueError("after must be a nonnegative integer cursor")
        _limit(limit)
        with self._operation():
            run, _, _, _ = self._bound_run(run_id)
            journal = self._journal(run)
            if after > len(journal):
                raise ValueError("cursor is ahead of the persisted journal")
            selected = journal[after:after + limit]
            cursor = selected[-1]["cursor"] if selected else after
            return {"run_id": run_id, "events": selected, "next_cursor": cursor,
                    "has_more": cursor < len(journal)}

    def resume(self, run_id, phase=None):
        if phase is not None and (type(phase) is not int or phase not in range(1, 8)):
            raise ValueError("resume phase must be an integer from 1 through 7 or null")
        _evidence_run(run_id)
        with self._operation(write=True):
            run, state, _, target = self._bound_run(run_id)
            if not target.exists():
                raise ValueError("source target is missing; restore it before resuming")
            if state.get("status") == "complete":
                raise ValueError("published run cannot be resumed; create a new run")
            completed = state.get("completed_phases", [])
            if (not isinstance(completed, list)
                    or any(type(value) is not int or value not in range(9) for value in completed)):
                raise ValueError("invalid completed_phases state")
            self._source_paths(target)
            args = [run, "--resume-from"]
            if phase is not None:
                args.append(phase)
            args.extend(["--run-name", run_id])
            delivery = self._command("prepare", *args)
            start = delivery["resume_from"]
            # Phases whose outputs prepare just bound as inherited proof are
            # completed, whether or not a host recorded a checkpoint for them.
            inherited = {item["phase"] for item in delivery["artifacts"].values()
                         if item.get("status") == "inherited" and type(item.get("phase")) is int}
            self._update_state(run, {
                "current_phase": start, "updated_at": _now(),
                "completed_phases": sorted({value for value in completed if value < start} | inherited),
            }, remove=("blocker",))
            snapshot.update_registration(run, active=True)
            self._event(run, "run_resumed", phase=start)
            return self._status(run_id)

    def stop(self, run_id, reason):
        _message(reason)
        if not reason.strip():
            raise ValueError("stop requires a reason after the host has stopped its workers")
        _evidence_run(run_id)
        with self._operation(write=True):
            run, state, _, _ = self._bound_run(run_id)
            if state.get("status") == "complete":
                raise ValueError("published run cannot be stopped")
            self._update_state(run, {"status": "partial", "blocker": reason, "updated_at": _now()})
            snapshot.update_registration(run, active=False)
            self._event(run, "run_stopped", message=reason)
            engine = resolve_edges.stop_pass(run / state["snapshot"]["path"], reason)
            if engine["stopped"]:
                self._event(run, "engine_stopped", message=f"pid {engine['pid']}")
            return self._status(run_id, engine=True)

    def publish(self, run_id):
        _evidence_run(run_id)
        with self._operation(write=True):
            run, _, _, target = self._bound_run(run_id)
            if not target.exists():
                raise ValueError("source target is missing; restore it before publishing")
            self._source_paths(target)
            result = snapshot.publish_run(run)
            if result.get("published"):
                self._event(run, "run_published")
            return result
