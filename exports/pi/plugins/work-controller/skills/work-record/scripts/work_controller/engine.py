"""Durable graph coordinator for local commands and host-driven agent jobs."""

from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore
from .definition import Definition, parse_definition
from .errors import (
    AuthorizationError,
    DefinitionError,
    ExecutionError,
    OutcomeUnknownError,
    ProcessError,
    StateError,
)
from .git_support import GitSupport
from .store import Store
from .util import confined_path

_GRANTS = {"shell", "commit"}


class Engine:
    def __init__(self, home: Path, workspace: Path):
        self.home = home.resolve()
        self.workspace = workspace.resolve()
        if not self.workspace.is_dir():
            raise StateError(f"workspace is not a directory: {workspace}")
        self.store = Store(self.home)
        self.artifacts = ArtifactStore(self.home / "artifacts")

    def _bind_workspace(self, run_id: str) -> None:
        recorded = Path(self.store.run(run_id)["workspace"]).resolve()
        if recorded != self.workspace:
            raise StateError(
                f"run workspace mismatch: recorded {recorded}, requested {self.workspace}"
            )

    def definition(self, run_id: str) -> Definition:
        self._bind_workspace(run_id)
        return parse_definition(self.store.run(run_id)["definition_yaml"])

    def start(
        self,
        definition_path: Path,
        *,
        grants: list[str] | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        with definition_path.open("rb") as stream:
            source_bytes = stream.read(1024 * 1024 + 1)
        if len(source_bytes) > 1024 * 1024:
            raise DefinitionError("definition YAML exceeds the 1 MiB limit")
        try:
            source = source_bytes.decode("utf-8")
        except UnicodeError as exc:
            raise DefinitionError("definition source is not valid UTF-8") from exc
        definition = parse_definition(source)
        grants = sorted(set(grants or []))
        unknown = set(grants) - _GRANTS
        if unknown:
            raise AuthorizationError("unknown grants: " + ", ".join(sorted(unknown)))
        jobs = definition.data["jobs"]
        if any(job["type"] == "command" for job in jobs) and "shell" not in grants:
            raise AuthorizationError("command jobs require the explicit 'shell' grant")
        if any("commit" in job for job in jobs) and "commit" not in grants:
            raise AuthorizationError("partial commits require the explicit 'commit' grant")
        if any("commit" in job for job in jobs):
            GitSupport(self.workspace).ensure_clean()
        external = []
        for item in definition.data["inputs"]:
            source_path = confined_path(self.workspace, item["path"], field="input path")
            stored = self.artifacts.put_file(source_path)
            external.append({"name": item["name"], "type": item["type"], **stored})
        run = self.store.create_run(
            definition,
            source,
            self.workspace,
            grants,
            [
                {key: value for key, value in artifact.items() if key != "path"}
                for artifact in external
            ],
            run_id=run_id,
        )
        return {
            "id": run["id"],
            "status": run["status"],
            "revision": run["revision"],
            "definition_digest": run["definition_digest"],
            "jobs": len(definition.order),
        }

    def frontier(self, run_id: str) -> list[dict[str, Any]]:
        definition = self.definition(run_id)
        return self.store.frontier(run_id, definition.order, definition.dependencies)

    def claim(self, run_id: str, holder: str) -> dict[str, Any] | None:
        definition = self.definition(run_id)
        attempt = self.store.claim(run_id, holder, definition.order, definition.dependencies)
        return self.packet(attempt["id"], holder) if attempt else None

    def packet(self, attempt_id: str, holder: str) -> dict[str, Any]:
        attempt = self.store.attempt(attempt_id)
        self._bind_workspace(attempt["run_id"])
        if attempt["holder"] != holder or attempt["status"] not in ("reserved", "running"):
            raise StateError("attempt is not available to this holder")
        job = self.store.job(attempt["run_id"], attempt["job_id"])
        inputs = []
        for artifact in attempt["inputs"].values():
            inputs.append({**artifact, "content_path": str(self.artifacts.path_for(artifact["digest"]))})
        return {
            "run_id": attempt["run_id"],
            "attempt_id": attempt_id,
            "job_id": attempt["job_id"],
            "attempt": attempt["number"],
            "type": job["payload"]["type"],
            "objective": self.definition(attempt["run_id"]).data["objective"],
            "summary": job["payload"]["summary"],
            "workspace": str(self.workspace),
            "inputs": inputs,
            "produces": job["payload"]["produces"],
            "write_set": job["payload"]["write_set"],
            "timeout_seconds": job["payload"]["timeout_seconds"],
        }

    def start_attempt(self, attempt_id: str, holder: str) -> dict[str, Any]:
        self._bind_workspace(self.store.attempt(attempt_id)["run_id"])
        self.store.start(attempt_id, holder)
        return self.packet(attempt_id, holder)

    def _check_duplicate(
        self,
        attempt: dict[str, Any],
        event_id: str,
        verdict: str,
        error: str | None,
        commit_sha: str | None,
    ) -> dict[str, Any] | None:
        previous = self.store.event(attempt["run_id"], event_id)
        if previous is None:
            return None
        payload = previous["payload"]
        if (
            previous.get("attempt_id") != attempt["id"]
            or payload.get("verdict") != verdict
            or payload.get("error") != error
            or (commit_sha is not None and payload.get("commit_sha") != commit_sha)
        ):
            raise StateError("event id already has a different delivery request")
        return {"duplicate": True, "attempt_id": attempt["id"], "verdict": verdict}

    def complete(
        self,
        attempt_id: str,
        holder: str,
        event_id: str,
        verdict: str,
        *,
        error: str | None = None,
        commit_sha: str | None = None,
    ) -> dict[str, Any]:
        if verdict == "fail" and not error:
            error = "job failed without an error summary"
        attempt = self.store.attempt(attempt_id)
        self._bind_workspace(attempt["run_id"])
        job = self.store.job(attempt["run_id"], attempt["job_id"])
        duplicate = self._check_duplicate(attempt, event_id, verdict, error, commit_sha)
        if duplicate:
            return duplicate
        run = self.store.run(attempt["run_id"])
        if "commit" in job["payload"] and "commit" not in run["grants"]:
            raise AuthorizationError("job commit lacks the run 'commit' grant")
        recorded_commit = attempt.get("commit_sha")
        if commit_sha and recorded_commit and commit_sha != recorded_commit:
            raise StateError("attempt already has a different commit SHA")
        commit_sha = commit_sha or recorded_commit
        admission = self.store.begin_completion(
            attempt_id, holder, event_id, verdict, error, commit_sha
        )
        if admission == "duplicate":
            return {"duplicate": True, "attempt_id": attempt_id, "verdict": verdict}
        if admission == "in_progress":
            return {"in_progress": True, "attempt_id": attempt_id, "verdict": verdict}
        produced = []
        try:
            if verdict == "pass":
                for spec in job["payload"]["produces"]:
                    path = confined_path(self.workspace, spec["path"], field="artifact path")
                    stored = self.artifacts.put_file(path)
                    produced.append(
                        {
                            "name": spec["name"],
                            "type": spec["type"],
                            "digest": stored["digest"],
                            "size": stored["size"],
                        }
                    )
                if "commit" in job["payload"] and commit_sha is None:
                    commit_sha = GitSupport(self.workspace).commit_paths(
                        job["payload"]["write_set"], job["payload"]["commit"]["message"]
                    )
                    try:
                        self.store.note_commit(attempt_id, holder, commit_sha)
                    except (ProcessError, OSError, sqlite3.Error) as exc:
                        raise OutcomeUnknownError(
                            f"commit {commit_sha} was created but its SHA could not be recorded: {exc}"
                        ) from exc
            result = self.store.complete(
                attempt_id,
                holder,
                event_id,
                verdict,
                produced,
                error=error,
                commit_sha=commit_sha,
            )
        except OutcomeUnknownError as exc:
            try:
                self.store.mark_completion_unknown(
                    attempt_id, event_id, str(exc), commit_sha=commit_sha
                )
            except (ProcessError, OSError, sqlite3.Error) as recovery_error:
                raise StateError(
                    f"{exc}; uncertain completion could not be recorded: {recovery_error}"
                ) from exc
            raise
        except (ProcessError, OSError, ValueError, sqlite3.Error) as exc:
            try:
                self.store.abort_completion(attempt_id, event_id)
            except (ProcessError, OSError, sqlite3.Error) as abort_error:
                raise StateError(f"{exc}; completion recovery also failed: {abort_error}") from exc
            raise
        result["artifacts"] = produced
        result["commit_sha"] = commit_sha
        return result

    def _execute_command(self, attempt_id: str, holder: str) -> dict[str, Any]:
        attempt = self.store.start(attempt_id, holder)
        run = self.store.run(attempt["run_id"])
        if "shell" not in run["grants"]:
            raise AuthorizationError("command execution lacks the run 'shell' grant")
        job = self.store.job(attempt["run_id"], attempt["job_id"])
        command = job["payload"]["command"]["argv"]
        directory = self.home / "runs" / attempt["run_id"] / "attempts" / f"{attempt['job_id']}-{attempt['number']}"
        directory.mkdir(parents=True, exist_ok=False)
        stdout_path = directory / "stdout.log"
        stderr_path = directory / "stderr.log"
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                completed = subprocess.run(
                    command,
                    cwd=self.workspace,
                    env=os.environ.copy(),
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    shell=False,
                    timeout=job["payload"]["timeout_seconds"],
                    check=False,
                )
            if completed.returncode == 0:
                result = self.complete(attempt_id, holder, attempt_id + ":completed", "pass")
            else:
                result = self.complete(
                    attempt_id,
                    holder,
                    attempt_id + ":completed",
                    "fail",
                    error=f"exit code {completed.returncode}; log: {stderr_path}",
                )
        except subprocess.TimeoutExpired:
            result = self.complete(
                attempt_id,
                holder,
                attempt_id + ":completed",
                "fail",
                error=f"timeout after {job['payload']['timeout_seconds']} seconds; log: {stderr_path}",
            )
        except OSError as exc:
            result = self.complete(
                attempt_id,
                holder,
                attempt_id + ":completed",
                "fail",
                error=f"command could not start: {exc}",
            )
        result["log_dir"] = str(directory)
        return result

    def drive(self, run_id: str, holder: str, *, max_steps: int = 100) -> dict[str, Any]:
        self._bind_workspace(run_id)
        steps = 0
        while steps < max_steps:
            status = self.store.status(run_id)
            if status["status"] != "in_progress":
                return {"status": "stopped", "run": status, "steps": steps}
            jobs = self.store.jobs(run_id)
            if jobs and all(job["status"] == "succeeded" for job in jobs):
                self.store.finish(run_id)
                return {"status": "complete", "run": self.store.status(run_id), "steps": steps}
            packet = self.claim(run_id, holder)
            if packet is None:
                status = self.store.status(run_id)
                if status["status"] == "in_progress":
                    jobs = self.store.jobs(run_id)
                    if all(job["status"] == "succeeded" for job in jobs):
                        self.store.finish(run_id)
                        return {"status": "complete", "run": self.store.status(run_id), "steps": steps}
                    if any(job["status"] in ("reserved", "running") for job in jobs):
                        return {"status": "active", "run": status, "steps": steps}
                    raise StateError("no runnable job and the run is not complete")
                return {"status": "stopped", "run": status, "steps": steps}
            steps += 1
            if packet["type"] == "agent":
                return {"status": "waiting_for_agent", "packet": packet, "steps": steps}
            result = self._execute_command(packet["attempt_id"], holder)
            if result["verdict"] == "fail" and self.store.status(run_id)["status"] != "in_progress":
                return {"status": "stopped", "run": self.store.status(run_id), "result": result, "steps": steps}
        raise ExecutionError(f"drive exceeded its bounded step count: {max_steps}")

    def supervise(self, attempt_id: str) -> dict[str, Any]:
        from .supervision import supervise

        return supervise(self, attempt_id)

    def resume(self, run_id: str) -> dict[str, Any]:
        self._bind_workspace(run_id)
        return self.store.resume(run_id)

    def resolve_unknown(
        self,
        attempt_id: str,
        *,
        confirm_stopped: bool,
        commit_sha: str | None = None,
        discard_commit_outcome: bool = False,
    ) -> dict[str, Any]:
        self._bind_workspace(self.store.attempt(attempt_id)["run_id"])
        attempt = self.store.resolve_unknown(
            attempt_id,
            confirm_stopped=confirm_stopped,
            commit_sha=commit_sha,
            discard_commit_outcome=discard_commit_outcome,
        )
        return {"attempt_id": attempt_id, "status": attempt["status"], "run_id": attempt["run_id"]}

    def finish(self, run_id: str) -> dict[str, Any]:
        self._bind_workspace(run_id)
        run = self.store.finish(run_id)
        return {"id": run["id"], "status": run["status"], "outcome": run["outcome"]}

    def status(self, run_id: str) -> dict[str, Any]:
        return self.store.status(run_id)

    def events(self, run_id: str, *, after: int = 0, limit: int = 20) -> list[dict[str, Any]]:
        return self.store.events(run_id, after=after, limit=limit)
