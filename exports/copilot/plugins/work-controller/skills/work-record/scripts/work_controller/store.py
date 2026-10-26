"""SQLite run state, durable attempts and append-only coordination events."""

from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .errors import StateError
from .util import canonical_json, digest_bytes, digest_value

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    definition_yaml TEXT NOT NULL,
    definition_digest TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    workspace TEXT NOT NULL,
    status TEXT NOT NULL,
    outcome TEXT,
    revision INTEGER NOT NULL,
    grants_json TEXT NOT NULL,
    deadline REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    run_id TEXT NOT NULL REFERENCES runs(id),
    id TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (run_id, id)
);
CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id),
    job_id TEXT NOT NULL,
    number INTEGER NOT NULL,
    holder TEXT NOT NULL,
    status TEXT NOT NULL,
    inputs_json TEXT NOT NULL,
    expires_at REAL NOT NULL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    error TEXT,
    commit_sha TEXT,
    UNIQUE (run_id, job_id, number),
    FOREIGN KEY (run_id, job_id) REFERENCES jobs(run_id, id)
);
CREATE TABLE IF NOT EXISTS artifacts (
    run_id TEXT NOT NULL REFERENCES runs(id),
    name TEXT NOT NULL,
    version INTEGER NOT NULL,
    type TEXT NOT NULL,
    digest TEXT NOT NULL,
    size INTEGER NOT NULL,
    producer_job TEXT,
    producer_attempt TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, name, version)
);
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(id),
    event_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    job_id TEXT,
    attempt_id TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (run_id, event_id)
);
CREATE TABLE IF NOT EXISTS interviews (
    id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS maps (
    id TEXT PRIMARY KEY,
    destination TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tickets (
    map_id TEXT NOT NULL REFERENCES maps(id),
    id TEXT NOT NULL,
    kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    status TEXT NOT NULL,
    blocked_by_json TEXT NOT NULL,
    holder TEXT,
    run_id TEXT,
    resolution TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (map_id, id)
);
CREATE INDEX IF NOT EXISTS idx_tickets_map_status ON tickets(map_id, status);
CREATE TABLE IF NOT EXISTS map_events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    map_id TEXT NOT NULL REFERENCES maps(id),
    event_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (map_id, event_id)
);
CREATE INDEX IF NOT EXISTS idx_attempts_run_status ON attempts(run_id, status);
CREATE INDEX IF NOT EXISTS idx_artifacts_run_name ON artifacts(run_id, name, version);
CREATE INDEX IF NOT EXISTS idx_events_run_seq ON events(run_id, seq);
"""

_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_INTERNAL_EVENT = "__process:"
_MAX_SQLITE_INT64 = 9_223_372_036_854_775_807


def utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def _json(value: Any) -> str:
    return canonical_json(value)


def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _validate_delivery_event(event_id: str) -> None:
    if (
        not isinstance(event_id, str)
        or not event_id.strip()
        or len(event_id) > 200
        or event_id.startswith(_INTERNAL_EVENT)
    ):
        raise StateError("delivery event id is empty, too long or reserved")


class Store:
    """One local store. Every public mutation uses an immediate transaction."""

    def __init__(self, home: Path):
        self.home = home.resolve()
        self._readonly = False
        self.home.mkdir(parents=True, exist_ok=True)
        self.path = self.home / "process.db"
        legacy_path = self.home / "brain.db"
        if not self.path.exists() and legacy_path.exists():
            self.path = legacy_path
        with self.connection() as conn:
            conn.executescript(_SCHEMA)
            conn.execute(
                "INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', '1')"
            )

    @classmethod
    def open_readonly(cls, home: Path) -> Store:
        """Open an existing store without initializing or changing its schema."""
        store = cls.__new__(cls)
        store.home = Path(home).resolve()
        store.path = store.home / "process.db"
        legacy_path = store.home / "brain.db"
        if not store.path.exists() and legacy_path.exists():
            store.path = legacy_path
        if not store.path.is_file():
            raise StateError(f"no existing process database at {store.home}")
        store._readonly = True
        return store

    def connect(self) -> sqlite3.Connection:
        if self._readonly:
            conn = sqlite3.connect(
                self.path.as_uri() + "?mode=ro", uri=True, timeout=5, isolation_level=None
            )
            conn.row_factory = sqlite3.Row
            return conn
        conn = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        if self._readonly:
            raise StateError("read-only process stores cannot start a write transaction")
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    @staticmethod
    def _run(conn: sqlite3.Connection, run_id: str) -> dict[str, Any]:
        row = _row(conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone())
        if row is None:
            raise StateError(f"unknown run: {run_id}")
        row["grants"] = json.loads(row.pop("grants_json"))
        return row

    @staticmethod
    def _job(conn: sqlite3.Connection, run_id: str, job_id: str) -> dict[str, Any]:
        row = _row(
            conn.execute(
                "SELECT * FROM jobs WHERE run_id = ? AND id = ?", (run_id, job_id)
            ).fetchone()
        )
        if row is None:
            raise StateError(f"unknown job: {job_id}")
        row["payload"] = json.loads(row.pop("payload_json"))
        return row

    def _touch(self, conn: sqlite3.Connection, run_id: str) -> None:
        conn.execute(
            "UPDATE runs SET revision = revision + 1, updated_at = ? WHERE id = ?",
            (utcnow(), run_id),
        )

    @staticmethod
    def _event(
        conn: sqlite3.Connection,
        run_id: str,
        event_id: str,
        kind: str,
        payload: dict[str, Any],
        *,
        job_id: str | None = None,
        attempt_id: str | None = None,
    ) -> None:
        if kind != "delivery.completed":
            event_id = _INTERNAL_EVENT + event_id
        conn.execute(
            """INSERT INTO events(run_id, event_id, kind, job_id, attempt_id, payload_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (run_id, event_id, kind, job_id, attempt_id, _json(payload), utcnow()),
        )

    def create_run(
        self,
        definition: Any,
        source_yaml: str,
        workspace: Path,
        grants: list[str],
        artifacts: list[dict[str, Any]],
        run_id: str | None = None,
    ) -> dict[str, Any]:
        run_id = run_id or f"{definition.data['id']}-{uuid.uuid4().hex[:8]}"
        if not _ID.fullmatch(run_id):
            raise StateError("run id must use lowercase letters, digits and hyphens")
        now = utcnow()
        with self.transaction() as conn:
            if conn.execute("SELECT 1 FROM runs WHERE id = ?", (run_id,)).fetchone():
                raise StateError(f"run already exists: {run_id}")
            budget = definition.data["budget"]
            conn.execute(
                """INSERT INTO runs(id, definition_yaml, definition_digest, source_digest,
                   workspace, status, outcome, revision, grants_json, deadline, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 'in_progress', NULL, 0, ?, ?, ?, ?)""",
                (
                    run_id,
                    source_yaml,
                    definition.digest,
                    digest_bytes(source_yaml.encode("utf-8")),
                    str(workspace.resolve()),
                    _json(sorted(grants)),
                    time.time() + budget["max_seconds"],
                    now,
                    now,
                ),
            )
            for job_id in definition.order:
                job = definition.job(job_id)
                conn.execute(
                    "INSERT INTO jobs(run_id, id, status, payload_json) VALUES (?, ?, 'pending', ?)",
                    (run_id, job_id, _json(job)),
                )
            for artifact in artifacts:
                self._insert_artifact(conn, run_id, artifact)
            self._event(
                conn,
                run_id,
                "run-created",
                "run.created",
                {"definition_digest": definition.digest, "grants": sorted(grants)},
            )
            return self._run(conn, run_id)

    @staticmethod
    def _insert_artifact(
        conn: sqlite3.Connection, run_id: str, artifact: dict[str, Any]
    ) -> None:
        conn.execute(
            """INSERT INTO artifacts(run_id, name, version, type, digest, size,
               producer_job, producer_attempt, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                artifact["name"],
                artifact.get("version", 1),
                artifact["type"],
                artifact["digest"],
                artifact["size"],
                artifact.get("producer_job"),
                artifact.get("producer_attempt"),
                artifact.get("status", "admitted"),
                utcnow(),
            ),
        )

    def run(self, run_id: str) -> dict[str, Any]:
        with self.connection() as conn:
            return self._run(conn, run_id)

    def job(self, run_id: str, job_id: str) -> dict[str, Any]:
        with self.connection() as conn:
            return self._job(conn, run_id, job_id)

    def jobs(self, run_id: str) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT id, status, attempts FROM jobs WHERE run_id = ? ORDER BY id", (run_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def attempt(self, attempt_id: str) -> dict[str, Any]:
        with self.connection() as conn:
            row = _row(conn.execute("SELECT * FROM attempts WHERE id = ?", (attempt_id,)).fetchone())
            if row is None:
                raise StateError(f"unknown attempt: {attempt_id}")
            row["inputs"] = json.loads(row.pop("inputs_json"))
            return row

    def latest_artifact(self, run_id: str, name: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            return self._latest_artifact(conn, run_id, name)

    @staticmethod
    def _latest_artifact(
        conn: sqlite3.Connection, run_id: str, name: str
    ) -> dict[str, Any] | None:
        return _row(
            conn.execute(
                """SELECT * FROM artifacts WHERE run_id = ? AND name = ? AND status = 'admitted'
                   ORDER BY version DESC LIMIT 1""",
                (run_id, name),
            ).fetchone()
        )

    def _inputs(
        self, conn: sqlite3.Connection, run_id: str, job: dict[str, Any]
    ) -> dict[str, Any] | None:
        inputs = {}
        for name in job["payload"]["consumes"]:
            artifact = self._latest_artifact(conn, run_id, name)
            if artifact is None:
                return None
            inputs[name] = {
                key: artifact[key] for key in ("name", "version", "type", "digest", "size")
            }
        return inputs

    def frontier(self, run_id: str, order: tuple[str, ...], dependencies: dict[str, set[str]]) -> list[dict[str, Any]]:
        with self.connection() as conn:
            run = self._run(conn, run_id)
            if run["status"] != "in_progress":
                return []
            active = conn.execute(
                "SELECT 1 FROM attempts WHERE run_id = ? AND status IN ('reserved', 'running', 'completing') LIMIT 1",
                (run_id,),
            ).fetchone()
            if active:
                return []
            ready = []
            statuses = {
                row["id"]: row["status"]
                for row in conn.execute("SELECT id, status FROM jobs WHERE run_id = ?", (run_id,))
            }
            for job_id in order:
                if statuses[job_id] not in ("pending", "failed"):
                    continue
                if any(statuses[dep] != "succeeded" for dep in dependencies[job_id]):
                    continue
                job = self._job(conn, run_id, job_id)
                if self._inputs(conn, run_id, job) is None:
                    continue
                ready.append({"id": job_id, "type": job["payload"]["type"], "attempts": job["attempts"]})
                if len(ready) == 10:
                    break
            return ready

    def claim(
        self,
        run_id: str,
        holder: str,
        order: tuple[str, ...],
        dependencies: dict[str, set[str]],
    ) -> dict[str, Any] | None:
        if not holder.strip():
            raise StateError("holder must be nonempty")
        with self.transaction() as conn:
            run = self._run(conn, run_id)
            if run["status"] != "in_progress":
                return None
            statuses = {
                row["id"]: row["status"]
                for row in conn.execute("SELECT id, status FROM jobs WHERE run_id = ?", (run_id,))
            }
            if statuses and all(status == "succeeded" for status in statuses.values()):
                return None
            if time.time() >= run["deadline"]:
                self._stop(conn, run_id, "BUDGET_EXHAUSTED", "deadline reached")
                return None
            if conn.execute(
                "SELECT 1 FROM attempts WHERE run_id = ? AND status IN ('reserved', 'running', 'completing') LIMIT 1",
                (run_id,),
            ).fetchone():
                return None
            used = conn.execute(
                "SELECT COALESCE(SUM(attempts), 0) AS used FROM jobs WHERE run_id = ?", (run_id,)
            ).fetchone()["used"]
            definition_budget = self._definition_budget(run)
            if used >= definition_budget["max_attempts"]:
                self._stop(conn, run_id, "BUDGET_EXHAUSTED", "attempt budget reached")
                return None
            for job_id in order:
                if statuses[job_id] not in ("pending", "failed"):
                    continue
                if any(statuses[dep] != "succeeded" for dep in dependencies[job_id]):
                    continue
                job = self._job(conn, run_id, job_id)
                inputs = self._inputs(conn, run_id, job)
                if inputs is None:
                    continue
                if job["attempts"] >= job["payload"]["max_attempts"]:
                    self._stop(conn, run_id, "ATTEMPTS_EXHAUSTED", f"no attempts left for {job_id}")
                    return None
                number = job["attempts"] + 1
                attempt_id = f"{run_id}:{job_id}:{number}"
                conn.execute(
                    """INSERT INTO attempts(id, run_id, job_id, number, holder, status,
                       inputs_json, expires_at, created_at)
                       VALUES (?, ?, ?, ?, ?, 'reserved', ?, ?, ?)""",
                    (
                        attempt_id,
                        run_id,
                        job_id,
                        number,
                        holder,
                        _json(inputs),
                        time.time() + job["payload"]["timeout_seconds"],
                        utcnow(),
                    ),
                )
                conn.execute(
                    "UPDATE jobs SET status = 'reserved', attempts = attempts + 1 WHERE run_id = ? AND id = ?",
                    (run_id, job_id),
                )
                self._touch(conn, run_id)
                self._event(
                    conn,
                    run_id,
                    attempt_id + ":reserved",
                    "attempt.reserved",
                    {"holder": holder, "inputs": inputs},
                    job_id=job_id,
                    attempt_id=attempt_id,
                )
                return self._attempt(conn, attempt_id)
            return None

    @staticmethod
    def _definition_budget(run: dict[str, Any]) -> dict[str, int]:
        import yaml

        data = yaml.safe_load(run["definition_yaml"])
        return data["budget"]

    def start(self, attempt_id: str, holder: str) -> dict[str, Any]:
        expired = False
        with self.transaction() as conn:
            attempt = self._attempt(conn, attempt_id)
            run = self._run(conn, attempt["run_id"])
            if run["status"] != "in_progress":
                raise StateError("run is not active")
            if attempt["status"] != "reserved" or attempt["holder"] != holder:
                raise StateError("attempt is not reserved to this holder")
            if time.time() >= attempt["expires_at"]:
                expired = True
                conn.execute("UPDATE attempts SET status = 'revoked' WHERE id = ?", (attempt_id,))
                conn.execute(
                    "UPDATE jobs SET status = 'pending' WHERE run_id = ? AND id = ?",
                    (attempt["run_id"], attempt["job_id"]),
                )
                self._touch(conn, attempt["run_id"])
                self._event(
                    conn,
                    attempt["run_id"],
                    attempt_id + ":expired",
                    "attempt.revoked",
                    {"reason": "lease expired"},
                    job_id=attempt["job_id"],
                    attempt_id=attempt_id,
                )
            else:
                conn.execute(
                    "UPDATE attempts SET status = 'running', started_at = ? WHERE id = ?",
                    (utcnow(), attempt_id),
                )
                conn.execute(
                    "UPDATE jobs SET status = 'running' WHERE run_id = ? AND id = ?",
                    (attempt["run_id"], attempt["job_id"]),
                )
                self._touch(conn, attempt["run_id"])
                self._event(
                    conn,
                    attempt["run_id"],
                    attempt_id + ":started",
                    "attempt.started",
                    {"holder": holder},
                    job_id=attempt["job_id"],
                    attempt_id=attempt_id,
                )
        if expired:
            raise StateError("reservation expired")
        return self.attempt(attempt_id)

    @staticmethod
    def _attempt(conn: sqlite3.Connection, attempt_id: str) -> dict[str, Any]:
        row = _row(conn.execute("SELECT * FROM attempts WHERE id = ?", (attempt_id,)).fetchone())
        if row is None:
            raise StateError(f"unknown attempt: {attempt_id}")
        row["inputs"] = json.loads(row.pop("inputs_json"))
        return row

    @staticmethod
    def _active_completion(conn, attempt_id: str) -> dict[str, Any] | None:
        started = conn.execute(
            """SELECT seq, payload_json FROM events WHERE attempt_id = ? AND kind = 'delivery.started'
               ORDER BY seq DESC LIMIT 1""",
            (attempt_id,),
        ).fetchone()
        if started is None:
            return None
        aborted = conn.execute(
            "SELECT 1 FROM events WHERE attempt_id = ? AND kind = 'delivery.aborted' AND seq > ?",
            (attempt_id, started["seq"]),
        ).fetchone()
        return None if aborted else json.loads(started["payload_json"])

    def begin_completion(
        self,
        attempt_id: str,
        holder: str,
        event_id: str,
        verdict: str,
        error: str | None,
        commit_sha: str | None,
    ) -> str:
        """Admit external completion effects exactly once for an attempt."""
        _validate_delivery_event(event_id)
        if verdict not in ("pass", "fail"):
            raise StateError("verdict must be pass or fail")
        with self.transaction() as conn:
            attempt = self._attempt(conn, attempt_id)
            run = self._run(conn, attempt["run_id"])
            previous = conn.execute(
                "SELECT * FROM events WHERE run_id = ? AND event_id = ?",
                (attempt["run_id"], event_id),
            ).fetchone()
            if previous:
                payload = json.loads(previous["payload_json"])
                if (
                    previous["attempt_id"] != attempt_id
                    or payload.get("verdict") != verdict
                    or payload.get("error") != error
                    or (commit_sha is not None and payload.get("commit_sha") != commit_sha)
                ):
                    raise StateError("event id already has a different delivery request")
                return "duplicate"
            if run["status"] != "in_progress":
                raise StateError("run is not active")
            if attempt["status"] not in ("running", "completing"):
                raise StateError("attempt is not active for completion")
            if attempt["holder"] != holder:
                raise StateError("attempt is not assigned to this holder")
            requested = self._active_completion(conn, attempt_id)
            if requested:
                if (
                    requested.get("event_id") != event_id
                    or requested.get("holder") != holder
                    or requested.get("verdict") != verdict
                    or requested.get("error") != error
                ):
                    raise StateError("a different completion is already admitted for this attempt")
                if attempt["status"] == "completing":
                    return "in_progress"
                conn.execute("UPDATE attempts SET status = 'completing' WHERE id = ?", (attempt_id,))
                self._touch(conn, attempt["run_id"])
                return "proceed"
            if attempt["status"] != "running":
                raise StateError("completion admission is missing")
            conn.execute("UPDATE attempts SET status = 'completing' WHERE id = ?", (attempt_id,))
            self._touch(conn, attempt["run_id"])
            self._event(
                conn,
                attempt["run_id"],
                f"delivery-started:{attempt_id}:{uuid.uuid4().hex}",
                "delivery.started",
                {
                    "event_id": event_id,
                    "holder": holder,
                    "verdict": verdict,
                    "error": error,
                },
                job_id=attempt["job_id"],
                attempt_id=attempt_id,
            )
            return "proceed"

    def abort_completion(self, attempt_id: str, event_id: str) -> None:
        """Close an admitted but unfinished effect phase without erasing its history."""
        with self.transaction() as conn:
            attempt = self._attempt(conn, attempt_id)
            requested = self._active_completion(conn, attempt_id)
            if requested is None or requested.get("event_id") != event_id:
                return
            if attempt["status"] == "completing" and self._run(conn, attempt["run_id"])["status"] == "in_progress":
                conn.execute("UPDATE attempts SET status = 'running' WHERE id = ?", (attempt_id,))
                self._touch(conn, attempt["run_id"])
            self._event(
                conn,
                attempt["run_id"],
                f"delivery-aborted:{attempt_id}:{uuid.uuid4().hex}",
                "delivery.aborted",
                {"event_id": event_id},
                job_id=attempt["job_id"],
                attempt_id=attempt_id,
            )

    def mark_completion_unknown(
        self,
        attempt_id: str,
        event_id: str,
        reason: str,
        *,
        commit_sha: str | None = None,
    ) -> None:
        """Block an uncertain external effect instead of making it retryable."""
        with self.transaction() as conn:
            attempt = self._attempt(conn, attempt_id)
            requested = self._active_completion(conn, attempt_id)
            if requested is None or requested.get("event_id") != event_id:
                raise StateError("uncertain completion has no matching admission")
            if attempt["commit_sha"] and commit_sha and attempt["commit_sha"] != commit_sha:
                raise StateError("attempt already has a different commit SHA")
            recorded_sha = commit_sha or attempt["commit_sha"]
            conn.execute(
                "UPDATE attempts SET status = 'unknown', error = ?, commit_sha = ? WHERE id = ?",
                (f"COMMIT_OUTCOME_UNKNOWN: {reason}", recorded_sha, attempt_id),
            )
            conn.execute(
                "UPDATE jobs SET status = 'blocked' WHERE run_id = ? AND id = ?",
                (attempt["run_id"], attempt["job_id"]),
            )
            conn.execute(
                """UPDATE runs SET status = 'blocked', outcome = 'ENVIRONMENT_BLOCKED',
                   revision = revision + 1, updated_at = ? WHERE id = ?""",
                (utcnow(), attempt["run_id"]),
            )
            self._event(
                conn,
                attempt["run_id"],
                f"delivery-unknown:{attempt_id}:{uuid.uuid4().hex}",
                "delivery.unknown",
                {"event_id": event_id, "reason": reason, "commit_sha": recorded_sha},
                job_id=attempt["job_id"],
                attempt_id=attempt_id,
            )

    def note_commit(self, attempt_id: str, holder: str, commit_sha: str) -> None:
        """Persist an external commit before delivery so a database retry cannot repeat it."""
        with self.transaction() as conn:
            attempt = self._attempt(conn, attempt_id)
            if attempt["status"] != "completing" or attempt["holder"] != holder:
                raise StateError("commit cannot be recorded for this attempt")
            run = self._run(conn, attempt["run_id"])
            if run["status"] != "in_progress":
                raise StateError("run is not active")
            if attempt["commit_sha"] and attempt["commit_sha"] != commit_sha:
                raise StateError("attempt already has a different commit SHA")
            if attempt["commit_sha"] == commit_sha:
                return
            conn.execute("UPDATE attempts SET commit_sha = ? WHERE id = ?", (commit_sha, attempt_id))
            self._touch(conn, attempt["run_id"])
            self._event(
                conn,
                attempt["run_id"],
                attempt_id + ":commit-recorded",
                "attempt.commit_recorded",
                {"commit_sha": commit_sha},
                job_id=attempt["job_id"],
                attempt_id=attempt_id,
            )

    def complete(
        self,
        attempt_id: str,
        holder: str,
        event_id: str,
        verdict: str,
        artifacts: list[dict[str, Any]],
        *,
        error: str | None = None,
        commit_sha: str | None = None,
    ) -> dict[str, Any]:
        _validate_delivery_event(event_id)
        if verdict not in ("pass", "fail"):
            raise StateError("verdict must be pass or fail")
        signature = digest_value(
            {"attempt": attempt_id, "verdict": verdict, "artifacts": artifacts, "error": error, "commit": commit_sha}
        )
        with self.transaction() as conn:
            attempt = self._attempt(conn, attempt_id)
            run_id = attempt["run_id"]
            previous = conn.execute(
                "SELECT payload_json FROM events WHERE run_id = ? AND event_id = ?",
                (run_id, event_id),
            ).fetchone()
            if previous:
                payload = json.loads(previous["payload_json"])
                if payload.get("signature") != signature:
                    raise StateError("event id already has a different payload")
                return {"duplicate": True, "attempt_id": attempt_id, "verdict": verdict}
            if attempt["status"] != "completing" or attempt["holder"] != holder:
                raise StateError("completion was not admitted for this attempt")
            requested = self._active_completion(conn, attempt_id)
            if requested is None:
                raise StateError("completion admission is missing")
            if (
                requested.get("event_id") != event_id
                or requested.get("holder") != holder
                or requested.get("verdict") != verdict
                or requested.get("error") != error
            ):
                raise StateError("completion request differs from its admission")
            run = self._run(conn, run_id)
            if run["status"] != "in_progress":
                raise StateError("run is not active")
            job = self._job(conn, run_id, attempt["job_id"])
            if verdict == "pass":
                for artifact in artifacts:
                    version = conn.execute(
                        "SELECT COALESCE(MAX(version), 0) + 1 AS version FROM artifacts WHERE run_id = ? AND name = ?",
                        (run_id, artifact["name"]),
                    ).fetchone()["version"]
                    self._insert_artifact(
                        conn,
                        run_id,
                        {
                            **artifact,
                            "version": version,
                            "producer_job": attempt["job_id"],
                            "producer_attempt": attempt_id,
                            "status": "admitted",
                        },
                    )
            conn.execute(
                """UPDATE attempts SET status = ?, ended_at = ?, error = ?, commit_sha = ? WHERE id = ?""",
                ("delivered" if verdict == "pass" else "failed", utcnow(), error, commit_sha, attempt_id),
            )
            conn.execute(
                "UPDATE jobs SET status = ? WHERE run_id = ? AND id = ?",
                ("succeeded" if verdict == "pass" else "failed", run_id, attempt["job_id"]),
            )
            self._event(
                conn,
                run_id,
                event_id,
                "delivery.completed",
                {
                    "signature": signature,
                    "verdict": verdict,
                    "artifacts": artifacts,
                    "error": error,
                    "commit_sha": commit_sha,
                },
                job_id=attempt["job_id"],
                attempt_id=attempt_id,
            )
            if verdict == "fail" and job["attempts"] >= job["payload"]["max_attempts"]:
                self._stop(conn, run_id, "JOB_FAILED", f"job exhausted: {attempt['job_id']}")
            else:
                self._touch(conn, run_id)
            return {"duplicate": False, "attempt_id": attempt_id, "verdict": verdict}

    def _stop(self, conn: sqlite3.Connection, run_id: str, outcome: str, reason: str) -> None:
        conn.execute(
            "UPDATE runs SET status = 'stopped', outcome = ?, revision = revision + 1, updated_at = ? WHERE id = ?",
            (outcome, utcnow(), run_id),
        )
        self._event(conn, run_id, f"stopped:{outcome}", "run.stopped", {"reason": reason})

    def resume(self, run_id: str) -> dict[str, Any]:
        with self.transaction() as conn:
            run = self._run(conn, run_id)
            changed = False
            if run["status"] == "in_progress":
                for attempt in conn.execute(
                    "SELECT * FROM attempts WHERE run_id = ? AND status IN ('reserved', 'running', 'completing')",
                    (run_id,),
                ).fetchall():
                    changed = True
                    if attempt["status"] == "reserved":
                        new_status, job_status = "revoked", "pending"
                    else:
                        new_status, job_status = "unknown", "blocked"
                    conn.execute("UPDATE attempts SET status = ? WHERE id = ?", (new_status, attempt["id"]))
                    conn.execute(
                        "UPDATE jobs SET status = ? WHERE run_id = ? AND id = ?",
                        (job_status, run_id, attempt["job_id"]),
                    )
                    self._event(
                        conn,
                        run_id,
                        attempt["id"] + ":resumed",
                        "attempt.reconciled",
                        {"status": new_status},
                        job_id=attempt["job_id"],
                        attempt_id=attempt["id"],
                    )
                if any(
                    row["status"] == "unknown"
                    for row in conn.execute("SELECT status FROM attempts WHERE run_id = ?", (run_id,))
                ):
                    conn.execute(
                        "UPDATE runs SET status = 'blocked', outcome = 'ENVIRONMENT_BLOCKED' WHERE id = ?",
                        (run_id,),
                    )
            if changed:
                self._touch(conn, run_id)
        return self.status(run_id)

    def resolve_unknown(
        self,
        attempt_id: str,
        *,
        confirm_stopped: bool,
        commit_sha: str | None = None,
        discard_commit_outcome: bool = False,
    ) -> dict[str, Any]:
        if not confirm_stopped:
            raise StateError("retry of an unknown attempt requires explicit confirmation that it stopped")
        if commit_sha and discard_commit_outcome:
            raise StateError("choose either a commit SHA or explicit commit-outcome discard")
        if commit_sha and not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", commit_sha):
            raise StateError("commit SHA must contain 40 or 64 hexadecimal characters")
        with self.transaction() as conn:
            attempt = self._attempt(conn, attempt_id)
            if attempt["status"] != "unknown":
                raise StateError("attempt is not unknown")
            run = self._run(conn, attempt["run_id"])
            if run["status"] != "blocked":
                raise StateError("run is not blocked")
            uncertain_commit = bool((attempt.get("error") or "").startswith("COMMIT_OUTCOME_UNKNOWN:"))
            if uncertain_commit and not commit_sha and not discard_commit_outcome:
                raise StateError("uncertain Git outcome requires --commit-sha or --discard-commit-outcome")
            if commit_sha and attempt["commit_sha"] and commit_sha != attempt["commit_sha"]:
                raise StateError("attempt already has a different commit SHA")
            if commit_sha:
                conn.execute(
                    """UPDATE attempts SET status = 'running', ended_at = NULL, error = NULL,
                       commit_sha = ? WHERE id = ?""",
                    (commit_sha, attempt_id),
                )
                new_status = "running"
            else:
                conn.execute(
                    "UPDATE attempts SET status = 'failed', ended_at = ?, error = ? WHERE id = ?",
                    (utcnow(), "unknown outcome reconciled by the user", attempt_id),
                )
                new_status = "failed"
                requested = self._active_completion(conn, attempt_id)
                if requested is not None:
                    self._event(
                        conn,
                        attempt["run_id"],
                        f"delivery-aborted:{attempt_id}:{uuid.uuid4().hex}",
                        "delivery.aborted",
                        {"event_id": requested["event_id"], "reason": "unknown attempt reconciled"},
                        job_id=attempt["job_id"],
                        attempt_id=attempt_id,
                    )
            conn.execute(
                "UPDATE jobs SET status = ? WHERE run_id = ? AND id = ?",
                (new_status, attempt["run_id"], attempt["job_id"]),
            )
            conn.execute(
                "UPDATE runs SET status = 'in_progress', outcome = NULL WHERE id = ?",
                (attempt["run_id"],),
            )
            self._touch(conn, attempt["run_id"])
            self._event(
                conn,
                attempt["run_id"],
                attempt_id + f":reconciled-{new_status}:{uuid.uuid4().hex}",
                "attempt.reconciled",
                {
                    "status": new_status,
                    "confirmation": "worker stopped",
                    "commit_sha": commit_sha,
                    "discard_commit_outcome": discard_commit_outcome,
                },
                job_id=attempt["job_id"],
                attempt_id=attempt_id,
            )
            return self._attempt(conn, attempt_id)

    def finish(self, run_id: str) -> dict[str, Any]:
        with self.transaction() as conn:
            run = self._run(conn, run_id)
            if run["status"] != "in_progress":
                raise StateError("run is not active")
            pending = conn.execute(
                "SELECT id FROM jobs WHERE run_id = ? AND status != 'succeeded'", (run_id,)
            ).fetchall()
            if pending:
                raise StateError("undelivered jobs: " + ", ".join(row["id"] for row in pending))
            conn.execute(
                "UPDATE runs SET status = 'complete', outcome = 'VERIFIED_SUCCESS', revision = revision + 1, updated_at = ? WHERE id = ?",
                (utcnow(), run_id),
            )
            self._event(conn, run_id, "run-finished", "run.completed", {"outcome": "VERIFIED_SUCCESS"})
            return self._run(conn, run_id)

    def status(self, run_id: str) -> dict[str, Any]:
        with self.connection() as conn:
            run = self._run(conn, run_id)
            counts = {
                row["status"]: row["count"]
                for row in conn.execute(
                    "SELECT status, COUNT(*) AS count FROM jobs WHERE run_id = ? GROUP BY status",
                    (run_id,),
                )
            }
            last = conn.execute(
                "SELECT seq, kind, job_id, attempt_id, created_at FROM events WHERE run_id = ? ORDER BY seq DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            return {
                "id": run_id,
                "status": run["status"],
                "outcome": run["outcome"],
                "revision": run["revision"],
                "definition_digest": run["definition_digest"],
                "jobs": counts,
                "last_event": _row(last),
            }

    def events(self, run_id: str, *, after: int = 0, limit: int = 20) -> list[dict[str, Any]]:
        if isinstance(after, bool) or not isinstance(after, int) or not 0 <= after <= _MAX_SQLITE_INT64:
            raise StateError("event cursor is outside the SQLite Int64 range")
        limit = max(1, min(limit, 100))
        with self.connection() as conn:
            self._run(conn, run_id)
            rows = conn.execute(
                """SELECT seq, event_id, kind, job_id, attempt_id, payload_json, created_at
                   FROM events WHERE run_id = ? AND seq > ? ORDER BY seq LIMIT ?""",
                (run_id, after, limit),
            ).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["payload"] = json.loads(item.pop("payload_json"))
                result.append(item)
            return result

    def event(self, run_id: str, event_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = _row(
                conn.execute(
                    "SELECT * FROM events WHERE run_id = ? AND event_id = ?",
                    (run_id, event_id),
                ).fetchone()
            )
            if row is not None:
                row["payload"] = json.loads(row.pop("payload_json"))
            return row

    def attempt_events(self, attempt_id: str, *, limit: int = 8) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 100))
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT seq, event_id, kind, job_id, attempt_id, payload_json, created_at
                   FROM events WHERE attempt_id = ? ORDER BY seq DESC LIMIT ?""",
                (attempt_id, limit),
            ).fetchall()
            result = []
            for row in reversed(rows):
                item = dict(row)
                item["payload"] = json.loads(item.pop("payload_json"))
                result.append(item)
            return result

    def save_interview(self, interview_id: str, payload: dict[str, Any], status: str) -> dict[str, Any]:
        if not _ID.fullmatch(interview_id):
            raise StateError("interview id must use lowercase letters, digits and hyphens")
        now = utcnow()
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO interviews(id, payload_json, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET payload_json = excluded.payload_json,
                   status = excluded.status, updated_at = excluded.updated_at""",
                (interview_id, _json(payload), status, now, now),
            )
            return {"id": interview_id, "status": status, "payload": payload}

    def interview(self, interview_id: str) -> dict[str, Any]:
        with self.connection() as conn:
            row = _row(conn.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,)).fetchone())
            if row is None:
                raise StateError(f"unknown interview: {interview_id}")
            row["payload"] = json.loads(row.pop("payload_json"))
            return row

    @staticmethod
    def _map_event(conn, map_id: str, event_id: str, kind: str, payload: dict[str, Any]) -> None:
        conn.execute(
            "INSERT INTO map_events(map_id, event_id, kind, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (map_id, event_id, kind, _json(payload), utcnow()),
        )

    def map_open(self, map_id: str, destination: str) -> dict[str, Any]:
        if not _ID.fullmatch(map_id) or not destination.strip():
            raise StateError("map id and destination are required")
        with self.transaction() as conn:
            existing = _row(conn.execute("SELECT * FROM maps WHERE id = ?", (map_id,)).fetchone())
            if existing:
                if existing["destination"] != destination.strip():
                    raise StateError("map id already has a different destination")
                return existing
            now = utcnow()
            conn.execute(
                "INSERT INTO maps(id, destination, status, created_at, updated_at) VALUES (?, ?, 'in_progress', ?, ?)",
                (map_id, destination.strip(), now, now),
            )
            self._map_event(conn, map_id, "map-opened", "map.opened", {"destination": destination.strip()})
            return _row(conn.execute("SELECT * FROM maps WHERE id = ?", (map_id,)).fetchone())

    @staticmethod
    def _validate_map_graph(conn, map_id: str) -> None:
        from graphlib import TopologicalSorter

        rows = conn.execute("SELECT id, blocked_by_json FROM tickets WHERE map_id = ?", (map_id,)).fetchall()
        ids = {row["id"] for row in rows}
        edges = {row["id"]: set(json.loads(row["blocked_by_json"])) & ids for row in rows}
        try:
            TopologicalSorter(edges).prepare()
        except ValueError as exc:
            raise StateError("ticket blocks must form an acyclic graph") from exc

    def ticket_add(self, map_id: str, ticket_id: str, kind: str, summary: str, *,
                   blocked_by: list[str] | None = None, run_id: str | None = None) -> dict[str, Any]:
        if not _ID.fullmatch(ticket_id) or kind not in ("decision", "research", "execution"):
            raise StateError("invalid ticket id or kind")
        if not summary.strip():
            raise StateError("ticket summary is required")
        blocked_by = sorted(set(blocked_by or []))
        if ticket_id in blocked_by or any(not _ID.fullmatch(item) for item in blocked_by):
            raise StateError("invalid ticket blocker")
        with self.transaction() as conn:
            if not conn.execute("SELECT 1 FROM maps WHERE id = ?", (map_id,)).fetchone():
                raise StateError(f"unknown map: {map_id}")
            if conn.execute("SELECT 1 FROM tickets WHERE map_id = ? AND id = ?", (map_id, ticket_id)).fetchone():
                raise StateError(f"ticket already exists: {ticket_id}")
            now = utcnow()
            conn.execute(
                """INSERT INTO tickets(map_id, id, kind, summary, status, blocked_by_json,
                   holder, run_id, resolution, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'pending', ?, NULL, ?, NULL, ?, ?)""",
                (map_id, ticket_id, kind, summary.strip(), _json(blocked_by), run_id, now, now),
            )
            self._validate_map_graph(conn, map_id)
            conn.execute("UPDATE maps SET status = 'in_progress', updated_at = ? WHERE id = ?", (utcnow(), map_id))
            self._map_event(conn, map_id, f"ticket-added:{ticket_id}", "ticket.added",
                            {"ticket": ticket_id, "kind": kind, "blocked_by": blocked_by, "run_id": run_id})
            return self._ticket(conn, map_id, ticket_id)

    @staticmethod
    def _ticket(conn, map_id: str, ticket_id: str) -> dict[str, Any]:
        row = _row(conn.execute("SELECT * FROM tickets WHERE map_id = ? AND id = ?", (map_id, ticket_id)).fetchone())
        if row is None:
            raise StateError(f"unknown ticket: {ticket_id}")
        row["blocked_by"] = json.loads(row.pop("blocked_by_json"))
        return row

    def ticket(self, map_id: str, ticket_id: str) -> dict[str, Any]:
        with self.connection() as conn:
            return self._ticket(conn, map_id, ticket_id)

    @staticmethod
    def _map_next(conn, map_id: str) -> dict[str, Any] | None:
        rows = conn.execute("SELECT id, blocked_by_json FROM tickets WHERE map_id = ? ORDER BY id", (map_id,)).fetchall()
        statuses = {row["id"]: row["status"] for row in conn.execute(
            "SELECT id, status FROM tickets WHERE map_id = ?", (map_id,))}
        for row in rows:
            if statuses[row["id"]] != "pending":
                continue
            blockers = json.loads(row["blocked_by_json"])
            if any(statuses.get(blocker, "pending") != "closed" for blocker in blockers):
                continue
            ticket = Store._ticket(conn, map_id, row["id"])
            if ticket["holder"] is None:
                return ticket
        return None

    def map_next(self, map_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            if not conn.execute("SELECT 1 FROM maps WHERE id = ?", (map_id,)).fetchone():
                raise StateError(f"unknown map: {map_id}")
            return self._map_next(conn, map_id)

    def ticket_claim(self, map_id: str, ticket_id: str, holder: str) -> dict[str, Any]:
        if not holder.strip():
            raise StateError("holder is required")
        with self.transaction() as conn:
            ticket = self._ticket(conn, map_id, ticket_id)
            if ticket["holder"] == holder and ticket["status"] == "in_progress":
                return ticket
            candidate = self._map_next(conn, map_id)
            if candidate is None or candidate["id"] != ticket_id:
                raise StateError("ticket is not at the open frontier or is already held")
            conn.execute(
                "UPDATE tickets SET status = 'in_progress', holder = ?, updated_at = ? WHERE map_id = ? AND id = ?",
                (holder, utcnow(), map_id, ticket_id),
            )
            self._map_event(conn, map_id, f"ticket-claimed:{ticket_id}", "ticket.claimed",
                            {"ticket": ticket_id, "holder": holder})
            return self._ticket(conn, map_id, ticket_id)

    def ticket_close(self, map_id: str, ticket_id: str, holder: str, *, source: str,
                     resolution: str | None = None, run_id: str | None = None) -> dict[str, Any]:
        with self.transaction() as conn:
            ticket = self._ticket(conn, map_id, ticket_id)
            if ticket["status"] != "in_progress" or ticket["holder"] != holder:
                raise StateError("ticket is not held by this session")
            kind = ticket["kind"]
            if kind == "decision" and source != "user":
                raise StateError("a decision ticket closes only with a real user answer")
            if kind == "research" and source != "evidence":
                raise StateError("a research ticket closes only with evidence")
            if kind == "execution" and source != "run":
                raise StateError("an execution ticket closes only through its completed run")
            if kind in ("decision", "research") and not (resolution or "").strip():
                raise StateError("a closing answer or evidence reference is required")
            if kind == "execution":
                if ticket["run_id"] and run_id and run_id != ticket["run_id"]:
                    raise StateError("execution ticket cannot be rebound to a different run")
                run_id = run_id or ticket["run_id"]
                if not run_id:
                    raise StateError("execution ticket is not linked to a run")
                run = self._run(conn, run_id)
                if run["status"] != "complete":
                    raise StateError("execution ticket cannot close before its run gates complete")
                resolution = f"run:{run_id}"
            conn.execute(
                """UPDATE tickets SET status = 'closed', resolution = ?, run_id = ?, updated_at = ?
                   WHERE map_id = ? AND id = ?""",
                (resolution, run_id or ticket["run_id"], utcnow(), map_id, ticket_id),
            )
            remaining = conn.execute(
                "SELECT 1 FROM tickets WHERE map_id = ? AND status != 'closed' LIMIT 1", (map_id,)).fetchone()
            conn.execute("UPDATE maps SET status = ?, updated_at = ? WHERE id = ?",
                         ("in_progress" if remaining else "complete", utcnow(), map_id))
            self._map_event(conn, map_id, f"ticket-closed:{ticket_id}", "ticket.closed",
                            {"ticket": ticket_id, "source": source, "resolution": resolution})
            return self._ticket(conn, map_id, ticket_id)

    def map_status(self, map_id: str) -> dict[str, Any]:
        with self.connection() as conn:
            row = _row(conn.execute("SELECT * FROM maps WHERE id = ?", (map_id,)).fetchone())
            if row is None:
                raise StateError(f"unknown map: {map_id}")
            counts = {item["status"]: item["count"] for item in conn.execute(
                "SELECT status, COUNT(*) AS count FROM tickets WHERE map_id = ? GROUP BY status", (map_id,))}
            return {"id": map_id, "status": row["status"], "destination": row["destination"],
                    "tickets": counts, "next": self._map_next(conn, map_id)}

    def map_events(self, map_id: str, *, after: int = 0, limit: int = 20) -> list[dict[str, Any]]:
        if isinstance(after, bool) or not isinstance(after, int) or not 0 <= after <= _MAX_SQLITE_INT64:
            raise StateError("event cursor is outside the SQLite Int64 range")
        limit = max(1, min(limit, 100))
        with self.connection() as conn:
            if not conn.execute("SELECT 1 FROM maps WHERE id = ?", (map_id,)).fetchone():
                raise StateError(f"unknown map: {map_id}")
            rows = conn.execute(
                """SELECT seq, event_id, kind, payload_json, created_at FROM map_events
                   WHERE map_id = ? AND seq > ? ORDER BY seq LIMIT ?""", (map_id, after, limit)).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["payload"] = json.loads(item.pop("payload_json"))
                result.append(item)
            return result
