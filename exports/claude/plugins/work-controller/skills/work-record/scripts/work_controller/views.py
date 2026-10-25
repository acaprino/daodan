"""Read-only, bounded projections shared by the web console and MCP."""

from __future__ import annotations

import json
from typing import Any

from .engine import Engine
from .errors import DefinitionError, StateError

MAX_SQLITE_INT64 = 9_223_372_036_854_775_807


def _bounded_limit(value: int, default: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DefinitionError("limit must be an integer")
    return max(1, min(value or default, maximum))


class Views:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.store = engine.store

    def overview(self, *, limit: int = 20) -> dict[str, Any]:
        limit = _bounded_limit(limit, 20, 100)
        with self.store.connection() as conn:
            runs = [dict(row) for row in conn.execute(
                """SELECT r.id, r.status, r.outcome, r.revision, r.updated_at,
                   (SELECT COUNT(*) FROM jobs j WHERE j.run_id = r.id) AS total_jobs,
                   (SELECT COUNT(*) FROM jobs j WHERE j.run_id = r.id AND j.status = 'succeeded') AS succeeded_jobs
                   FROM runs r WHERE r.workspace = ? ORDER BY r.updated_at DESC LIMIT ?""",
                (str(self.engine.workspace), limit),
            )]
            maps = [dict(row) for row in conn.execute(
                """SELECT m.id, m.destination, m.status, m.updated_at,
                   (SELECT COUNT(*) FROM tickets t WHERE t.map_id = m.id) AS total_tickets,
                   (SELECT COUNT(*) FROM tickets t WHERE t.map_id = m.id AND t.status = 'closed') AS closed_tickets
                   FROM maps m ORDER BY m.updated_at DESC LIMIT ?""",
                (limit,),
            )]
        return {"runs": runs, "maps": maps}

    def status(self, run_id: str) -> dict[str, Any]:
        self.engine._bind_workspace(run_id)
        return self.store.status(run_id)

    def run(self, run_id: str) -> dict[str, Any]:
        self.engine._bind_workspace(run_id)
        status = self.store.status(run_id)
        jobs = []
        with self.store.connection() as conn:
            rows = conn.execute(
                "SELECT id, status, payload_json, attempts FROM jobs WHERE run_id = ? ORDER BY id",
                (run_id,),
            ).fetchall()
            for row in rows:
                payload = json.loads(row["payload_json"])
                jobs.append({
                    "id": row["id"],
                    "type": payload["type"],
                    "summary": payload["summary"],
                    "status": row["status"],
                    "attempts": row["attempts"],
                    "max_attempts": payload["max_attempts"],
                })
            attempts = [dict(row) for row in conn.execute(
                """SELECT id, job_id, number, holder, status, expires_at, started_at,
                   ended_at, error, commit_sha FROM attempts WHERE run_id = ?
                   ORDER BY created_at DESC LIMIT 100""",
                (run_id,),
            )]
            artifacts = [dict(row) for row in conn.execute(
                """SELECT a.name, a.version, a.type, a.digest, a.size, a.producer_job,
                   a.producer_attempt, a.status, a.created_at FROM artifacts a
                   JOIN (SELECT name, MAX(version) AS version FROM artifacts
                   WHERE run_id = ? GROUP BY name) latest
                   ON latest.name = a.name AND latest.version = a.version
                   WHERE a.run_id = ? ORDER BY a.name LIMIT 100""",
                (run_id, run_id),
            )]
            event_rows = conn.execute(
                """SELECT seq, event_id, kind, job_id, attempt_id, payload_json, created_at
                   FROM events WHERE run_id = ? ORDER BY seq DESC LIMIT 20""",
                (run_id,),
            ).fetchall()
        events = []
        for row in reversed(event_rows):
            event = dict(row)
            event["payload"] = json.loads(event.pop("payload_json"))
            events.append(event)
        return {
            "status": status,
            "jobs": jobs,
            "attempts": attempts,
            "artifacts": artifacts,
            "events": events,
            "frontier": self.engine.frontier(run_id),
        }

    def events(self, run_id: str, *, after: int = 0, limit: int = 20) -> dict[str, Any]:
        self.engine._bind_workspace(run_id)
        if isinstance(after, bool) or not isinstance(after, int) or after < 0:
            raise DefinitionError("after must be a nonnegative integer")
        if after > MAX_SQLITE_INT64:
            raise DefinitionError("after exceeds the SQLite Int64 cursor range")
        limit = _bounded_limit(limit, 20, 100)
        return {"events": self.store.events(run_id, after=after, limit=limit)}

    def map(self, map_id: str) -> dict[str, Any]:
        with self.store.connection() as conn:
            if not conn.execute("SELECT 1 FROM maps WHERE id = ?", (map_id,)).fetchone():
                raise StateError(f"unknown map: {map_id}")
            tickets = []
            for row in conn.execute(
                "SELECT * FROM tickets WHERE map_id = ? ORDER BY id LIMIT 200", (map_id,)
            ):
                ticket = dict(row)
                ticket["blocked_by"] = json.loads(ticket.pop("blocked_by_json"))
                tickets.append(ticket)
        return {"status": self.store.map_status(map_id), "tickets": tickets}

    def attempt_log(self, attempt_id: str, stream: str, *, max_bytes: int = 32768) -> dict[str, Any]:
        if stream not in ("stdout", "stderr"):
            raise DefinitionError("stream must be stdout or stderr")
        max_bytes = _bounded_limit(max_bytes, 32768, 65536)
        attempt = self.store.attempt(attempt_id)
        self.engine._bind_workspace(attempt["run_id"])
        path = (
            self.engine.home / "runs" / attempt["run_id"] / "attempts"
            / f"{attempt['job_id']}-{attempt['number']}" / f"{stream}.log"
        )
        attempts_root = (self.engine.home / "runs" / attempt["run_id"] / "attempts").resolve()
        resolved = path.resolve()
        if attempts_root not in resolved.parents:
            raise StateError("attempt log escapes its owned directory")
        if not resolved.is_file() or resolved.is_symlink():
            return {"attempt_id": attempt_id, "stream": stream, "available": False, "text": ""}
        path = resolved
        size = path.stat().st_size
        with path.open("rb") as source:
            source.seek(max(0, size - max_bytes))
            data = source.read(max_bytes)
        return {
            "attempt_id": attempt_id,
            "stream": stream,
            "available": True,
            "size": size,
            "truncated": size > max_bytes,
            "text": data.decode("utf-8", errors="replace"),
        }
