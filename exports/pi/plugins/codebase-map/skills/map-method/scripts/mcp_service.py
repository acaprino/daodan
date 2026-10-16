"""Project-bound Codebase Map operations, independent of an MCP runtime.

The caller owns agent execution, authorization and stopping workers. This service
prepares and observes canonical runs; it never starts or cancels an agent. Events
record service operations, while state and delivery checks remain authoritative.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import migrate_root
import snapshot
import source_reader


__all__ = ["MapService"]
EVENT_FILE = "mcp-events.json"
MAX_LIMIT = 1000
MAX_MESSAGE = 10000
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
    migrate_root._reject_link_chain(path)
    if not path.is_file():
        raise ValueError(f"required regular file is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _write(path: Path, value: dict) -> None:
    migrate_root._reject_link_chain(path)
    snapshot._write_json_atomic(path, value)


class MapService:
    """Reuse canonical helpers within one explicit, existing project directory."""

    def __init__(self, project_root):
        self.project_root = migrate_root._project(project_root)
        self.root = self.project_root / ".codebase-map"

    @contextmanager
    def _operation(self, *, write=False):
        # Share the existing OS project lock with migration. Calling its locked
        # implementation avoids reacquiring a POSIX lock on another descriptor.
        migrate_root._reject_link_chain(self.project_root)
        with migrate_root._migration_lock(self.project_root):
            migration = migrate_root._migrate_locked(self.project_root, check=not write)
            if migration["status"] in {"migration_required", "recovery_required"}:
                raise ValueError("analysis-root migration is required; run migrate_root.py --project for this bound project before querying")
            migrate_root._reject_link_chain(self.root)
            yield

    def _target(self, value, *, require_exists=True):
        relative = _relative(value, root=True)
        if relative.split("/")[0].casefold() in {".codebase-map", ".codebase-xray"}:
            raise ValueError("analysis output cannot be the source target")
        target = self.project_root / relative
        migrate_root._reject_link_chain(target)
        resolved = target.resolve()
        if any(resolved.is_relative_to((self.project_root / name).resolve())
               for name in (".codebase-map", ".codebase-xray")):
            raise ValueError("analysis output cannot be the source target")
        if (require_exists or target.exists()) and not (target.is_dir() or target.is_file()):
            raise ValueError("target must be an existing project-relative file or directory")
        if not resolved.is_relative_to(self.project_root):
            raise ValueError("target is outside the bound project")
        if target.is_file() and snapshot.is_forbidden(target.name):
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
        migrate_root._reject_link_chain(root)
        if (root / relative_target).resolve() != target:
            raise ValueError("snapshot and state target bindings differ")
        for relative in manifest["files"]:
            source = root / _relative(relative)
            migrate_root._reject_link_chain(source)
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
        file_target = relative_target in manifest["files"]
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
            migrate_root._reject_link_chain(path)

    def _run_path(self, run_id):
        path = self.root / "runs" / _run_id(run_id)
        migrate_root._reject_link_chain(path)
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
            migrate_root._reject_link_chain(run / name)
        manifest = _json(run / "snapshot/manifest.json")
        self._manifest_binding(run, state, manifest, target)
        self._validate_artifact_paths(run, state)
        if state.get("delivery") is not None:
            snapshot._validate_delivery(run, self.root, state)
        return run, state, manifest, target

    def _validate_artifact_paths(self, run, state):
        # Helpers read these fixed inputs before validating their declaration.
        # Include optional inputs and possible unexpected phase files as well.
        names = {*snapshot.PHASE_FILES, "knowledge/navigation.md", "knowledge/documentation-leads.md",
                 "comment_health.md", "changes.md"}
        for path in run.glob("[0-9][0-9]-*.md"):
            migrate_root._reject_link_chain(path)
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
            migrate_root._reject_link_chain(run / name)

    def _status(self, run_id):
        run, state, _, target = self._bound_run(run_id)
        if not target.exists():
            return {"run_id": run_id, "state": state, "check": None, "source_available": False,
                    "check_unavailable": "source target is missing; canonical delivery/freshness check is unavailable"}
        checked = snapshot.check_delivery(run) if state.get("delivery") is not None else None
        return {"run_id": run_id, "state": state, "check": checked, "source_available": True}

    def _journal(self, run):
        path = run / EVENT_FILE
        migrate_root._reject_link_chain(path)
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
        try:
            result = subprocess.run(
                [sys.executable, "-B", str(Path(snapshot.__file__)), command, *map(str, args)],
                cwd=self.project_root, capture_output=True, text=True, timeout=120,
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
            return self._command("scope", bound)

    def create_run(self, target, run_id, depth="full", critical=False, comments=False,
                   docs_only=False, phase=None, stop_after=None):
        _run_id(run_id)
        flags = {"depth": depth, "critical": critical, "comments": comments,
                 "docs_only": docs_only, "phase": phase}
        snapshot._effective_flags(flags)
        if stop_after is not None and (type(stop_after) is not int or stop_after not in range(1, 7)
                                       or phase is not None or docs_only):
            raise ValueError("stop_after accepts 1 through 6 without phase or docs_only")
        # Validate before migration or creating any output directory.
        self._target(target)
        with self._operation(write=True):
            bound = self._target(target)
            run = self._run_path(run_id)
            if run.exists():
                raise ValueError("run already exists; resume the exact run or choose another run_id")
            self._source_paths(bound)
            manifest = snapshot.build_manifest(bound)
            state = {"run_id": run_id, "target": bound.relative_to(self.project_root).as_posix(),
                     "mode": "classic", "status": "in_progress", "flags": flags,
                     "started_at": _now(), "updated_at": _now(), "parent_run": None,
                     "incremental": None, "current_phase": 0, "completed_phases": [],
                     "files_created": [], "git": manifest.get("git")}
            run.mkdir(parents=True)
            (run / "snapshot").mkdir()
            _write(run / "snapshot/manifest.json", manifest)
            _write(run / "state.json", state)
            arguments = [run]
            if stop_after is not None:
                arguments.extend(["--stop-after", stop_after])
            self._command("prepare", *arguments)
            snapshot.update_registration(run, active=True)
            self._event(run, "run_created")
            return self._status(run_id)

    def status(self, run_id):
        with self._operation():
            return self._status(run_id)

    def runs(self):
        with self._operation():
            directory = self.root / "runs"
            migrate_root._reject_link_chain(directory)
            values = []
            if directory.exists():
                if not directory.is_dir():
                    raise ValueError("analysis runs root must be a directory")
                for path in sorted(directory.iterdir()):
                    migrate_root._reject_link_chain(path)
                    if path.is_dir():
                        values.append(self._status(path.name))
            registry = self.root / "runs.json"
            migrate_root._reject_link_chain(registry)
            return {"runs": values, "registry": snapshot._read_registry(self.root) if registry.exists() else None}

    def outline(self, run_id, path=None, pattern=None, limit=100):
        _limit(limit)
        if path is not None:
            _relative(path)
        if pattern is not None and (not isinstance(pattern, str) or len(pattern) > 1000):
            raise ValueError("pattern must be text of at most 1000 characters")
        with self._operation():
            _, _, manifest, _ = self._bound_run(run_id)
            return dict(source_reader.outline_manifest(manifest, path, pattern, limit), run_id=run_id)

    def graph(self, run_id, paths=None, hops=2, limit=100):
        _limit(limit)
        if paths is not None:
            if not isinstance(paths, list) or not paths:
                raise ValueError("paths must be a nonempty list or null")
            for path in paths:
                _relative(path)
        with self._operation():
            _, _, manifest, _ = self._bound_run(run_id)
            return dict(source_reader.graph_packet(manifest, paths, hops, limit), run_id=run_id)

    def read(self, run_id, requests):
        if not isinstance(requests, list) or not 1 <= len(requests) <= MAX_LIMIT:
            raise ValueError(f"requests must be a list containing 1 through {MAX_LIMIT} selections")
        with self._operation():
            _, _, manifest, _ = self._bound_run(run_id)
            return dict(source_reader.read_packet(manifest, requests), run_id=run_id)

    def diff(self, run_id):
        with self._operation():
            _, _, manifest, target = self._bound_run(run_id)
            available = target.exists()
            if available:
                self._source_paths(target)
                comparison = snapshot.compare_files(manifest, target, verify=True)
            else:
                comparison = {"added": [], "removed": sorted(manifest["files"]),
                              "modified": [], "unchanged": [], "current": {}}
            symbols = snapshot.compare_symbols(manifest, comparison)
            files = {key: comparison[key] for key in ("added", "removed", "modified")}
            # Normalized hashes intentionally ignore CRLF. Byte freshness still
            # matters to verified readers and resume, so expose it separately.
            raw_changed = sorted(name for name in comparison["unchanged"]
                                 if hashlib.sha256(comparison["current"][name].read_bytes()).hexdigest()
                                 != manifest["files"][name].get("raw_hash"))
            parser_changed = manifest.get("parser_fingerprint") != snapshot.parser_fingerprint()
            return {"run_id": run_id, "files": files,
                    "symbols": {key: symbols[key] for key in ("added", "removed", "changed")},
                    "raw_changed": raw_changed, "parser_changed": parser_changed,
                    "source_available": available,
                    "unchanged": available and not any(files.values()) and not raw_changed and not parser_changed}

    def artifact(self, run_id, name):
        _relative(name)
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
            migrate_root._reject_link_chain(path)
            if not path.is_file():
                raise ValueError("declared artifact has not been delivered")
            data = path.read_bytes()
            return {"run_id": run_id, "name": name, "content": data.decode("utf-8-sig"),
                    "sha256": hashlib.sha256(data).hexdigest()}

    def checkpoint(self, run_id, phase, event, message=""):
        if type(phase) is not int or phase not in range(9):
            raise ValueError("phase must be an integer from 0 through 8")
        if event not in ("phase_started", "phase_completed", "blocked"):
            raise ValueError("event must be phase_started, phase_completed or blocked")
        _message(message)
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
                completed = state.get("completed_phases", [])
                if not isinstance(completed, list) or any(type(value) is not int for value in completed):
                    raise ValueError("invalid completed_phases state")
                state["completed_phases"] = sorted(set(completed) | {phase})
            state["current_phase"] = phase
            state["updated_at"] = _now()
            if event == "blocked":
                state["blocker"] = message
            else:
                state.pop("blocker", None)
            _write(run / "state.json", state)
            self._event(run, event, phase=phase, message=message)
            return self._status(run_id)

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
        with self._operation(write=True):
            run, state, _, target = self._bound_run(run_id)
            if not target.exists():
                raise ValueError("source target is missing; restore it before resuming")
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
            state = _json(run / "state.json")
            start = delivery["resume_from"]
            state.update(current_phase=start, updated_at=_now(),
                         completed_phases=sorted({value for value in completed if value < start}))
            state.pop("blocker", None)
            _write(run / "state.json", state)
            snapshot.update_registration(run, active=True)
            self._event(run, "run_resumed", phase=start)
            return self._status(run_id)

    def stop(self, run_id, reason):
        _message(reason)
        if not reason.strip():
            raise ValueError("stop requires a reason after the host has stopped its workers")
        with self._operation(write=True):
            run, state, _, _ = self._bound_run(run_id)
            if state.get("status") == "complete":
                raise ValueError("published run cannot be stopped")
            state.update(status="partial", blocker=reason, updated_at=_now())
            _write(run / "state.json", state)
            snapshot.update_registration(run, active=False)
            self._event(run, "run_stopped", message=reason)
            return self._status(run_id)

    def publish(self, run_id):
        with self._operation(write=True):
            run, _, _, target = self._bound_run(run_id)
            if not target.exists():
                raise ValueError("source target is missing; restore it before publishing")
            self._source_paths(target)
            result = snapshot.publish_run(run)
            if result.get("published"):
                self._event(run, "run_published")
            return result
