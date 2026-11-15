"""The analysis's events, from the first step to the complete graph: one bus, its listeners, and a journal.

An event is a dict: `step`, `analyzer` (None outside an analyzer), `kind`, `level`, `message` (to read), `data`
and `at`. A `warning` or an `error` carries `cause` and `remedy` in its data. The journal (`JOURNAL`, beside
the snapshot) keeps every event as a line, so a listener in another process, or one that comes later, reads
them with `read` from a cursor. A listener that fails stops nothing: its error becomes an event.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

JOURNAL = "pipeline-events.jsonl"
KINDS = frozenset({"step.started", "step.finished", "step.failed", "step.skipped", "analyzer.started",
                   "analyzer.finished", "analyzer.unavailable", "progress", "gap", "log", "graph.ready"})
LEVELS = ("debug", "info", "warning", "error")


class Bus:
    def __init__(self, journal: Path | None = None):
        self.journal = Path(journal) if journal else None
        self._listeners: list = []

    def subscribe(self, listener) -> callable:
        """`listener(event)` for every event from now on; the call returned unsubscribes it."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener) if listener in self._listeners else None

    def emit(self, kind: str, message: str, *, step: str, analyzer: str | None = None, level: str = "info",
             **data) -> dict:
        if kind not in KINDS:
            raise ValueError(f"no event kind {kind!r}")
        if level not in LEVELS:
            raise ValueError(f"no level {level!r}")
        if level in ("warning", "error") and not (data.get("cause") and data.get("remedy")):
            raise ValueError(f"a {level} says its cause and its remedy")
        event = {"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "step": step,
                 "analyzer": analyzer, "kind": kind, "level": level, "message": message, "data": data}
        if self.journal is not None:
            self.journal.parent.mkdir(parents=True, exist_ok=True)
            with self.journal.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        failed = []
        for listener in list(self._listeners):  # every listener gets the event before any failure is told
            try:
                listener(event)
            except Exception as error:  # noqa: BLE001 - a listener's failure is an event, never the analysis's end
                failed.append((listener, error))
        if "listener" not in data:  # a failure on a failure's own event is not told again
            for listener, error in failed:
                self.emit("log", f"a listener failed on {kind}: {error}", step=step, analyzer=analyzer,
                          level="error", cause=f"{type(error).__name__}: {error}",
                          remedy="fix or remove the listener; the analysis went on", listener=repr(listener))
        return event

    def progress(self, step: str, done: int, total: int, *, analyzer: str | None = None, phase: str | None = None,
                 message: str = "") -> dict:
        data = {"done": done, "total": total, **({"phase": phase} if phase else {})}
        return self.emit("progress", message or f"{done} of {total}", step=step, analyzer=analyzer, **data)


def read(journal: Path, after: int = 0, limit: int | None = None) -> tuple[list[dict], int]:
    """The events after the cursor `after` (a count of lines), and the cursor to read from next."""
    path = Path(journal)
    if not path.is_file():
        return [], after
    lines = path.read_text(encoding="utf-8").splitlines()
    chosen = lines[after:] if limit is None else lines[after:after + limit]
    return [json.loads(line) for line in chosen], after + len(chosen)
