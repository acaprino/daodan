"""The analysis's events, from the first step to the complete graph: one bus, its listeners, and a journal.

An event is a dict: `step`, `analyzer` (the analyzer of the analysis or the observer of the dynamic step it comes
from, None outside one), `kind`, `level`, `message` (to read), `data` and `at`. A `warning` or an `error` carries
`cause` and `remedy` in its data. The journal (`JOURNAL`, beside the snapshot) keeps every event as a line, so a
listener in another process, or one that comes later, reads them with `read` from a cursor. A listener that fails
stops nothing: its error becomes an event. Nor does a journal that cannot be written: the listeners are told once,
and the events go on to them. Each event is one write, so the lines of two processes that append do not mix; a
line a stopped writer left broken is skipped by `read`. An analysis that ends without a word (stopped, killed)
leaves a step started and never ended: who knows it is over says that end (`close_open`). A journal written before the
steps had their ids reads with them (`LEGACY`).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

JOURNAL = "pipeline-events.jsonl"
KINDS = frozenset({"step.started", "step.finished", "step.failed", "step.skipped", "analyzer.started",
                   "analyzer.finished", "analyzer.unavailable", "progress", "gap", "log", "graph.ready"})
LEVELS = ("debug", "info", "warning", "error")
# The steps' old names, as a journal written before the eight ids keeps them: `read` gives the id. `parse` said the plan
# on a store `read_code` had read.
LEGACY = {"stack": "recognize_stack", "scan": "find_modules", "parse": "read_code", "analyze": "link_calls",
          "dynamic": "run_and_observe", "union": "assemble_graph"}


class Bus:
    def __init__(self, journal: Path | None = None):
        self.journal = Path(journal) if journal else None
        self._listeners: list = []
        self._unwritten = False  # a failed write of the journal has been told

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
        unwritten = None if self.journal is None else self._write(event)
        failed = []
        for listener in list(self._listeners):  # every listener gets the event before any failure is told
            try:
                listener(event)
            except Exception as error:  # noqa: BLE001 - a listener's failure is an event, never the analysis's end
                failed.append((listener, error))
        if unwritten and not self._unwritten:  # told once: every later event would say the same
            self._unwritten = True
            self.emit("log", f"the journal cannot be written: {unwritten}", step=step, analyzer=analyzer,
                      level="error", cause=unwritten, journal=str(self.journal),
                      remedy="free the disk or fix the folder's permissions; the analysis goes on, and a listener "
                             "that reads the journal misses the events from here")
        if "listener" not in data:  # a failure on a failure's own event is not told again
            for listener, error in failed:
                self.emit("log", f"a listener failed on {kind}: {error}", step=step, analyzer=analyzer,
                          level="error", cause=f"{type(error).__name__}: {error}",
                          remedy="fix or remove the listener; the analysis went on", listener=repr(listener))
        return event

    def _write(self, event: dict) -> str | None:
        """The event as one line of the journal, in one write; the cause when it could not be written."""
        line = (json.dumps(event, ensure_ascii=False, default=str) + "\n").encode("utf-8")
        try:
            self.journal.parent.mkdir(parents=True, exist_ok=True)
            with self.journal.open("ab", buffering=0) as stream:
                if stream.write(line) != len(line):
                    raise OSError("the line was written in part")
        except OSError as error:
            return f"{type(error).__name__}: {error}"
        return None

    def progress(self, step: str, done: int, total: int, *, analyzer: str | None = None, phase: str | None = None,
                 message: str = "") -> dict:
        data = {"done": done, "total": total, **({"phase": phase} if phase else {})}
        return self.emit("progress", message or f"{done} of {total}", step=step, analyzer=analyzer, **data)


def read(journal: Path, after: int = 0, limit: int | None = None) -> tuple[list[dict], int]:
    """The events after the cursor `after` (a count of lines), and the cursor to read from next, each with its step's id
    (`LEGACY`). A line that is no event (a writer stopped in its middle) counts and is skipped: one broken line never hides
    the ones after it."""
    path = Path(journal)
    if not path.is_file():
        return [], after
    found, cursor = [], after
    with path.open("rb") as stream:
        for number, line in enumerate(stream):
            # A last line without its newline is still being written: read it next time.
            if not line.endswith(b"\n") or (limit is not None and cursor - after >= limit):
                break
            if number < after:
                continue
            cursor += 1
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                if event.get("step") in LEGACY:
                    event["step"] = LEGACY[event["step"]]
                found.append(event)
    return found, cursor


def close_open(journal: Path, cause: str, remedy: str) -> list[str]:
    """Say the end of every step and analyzer the journal shows started and never ended: an analyzer as
    `analyzer.finished` and a step as `step.failed`, both errors with `cause` and `remedy`, the analyzers first.
    Returns their names. For the caller that knows the analysis that wrote them is over (it stopped it, or found
    its process gone): a step of an analysis still running beside it would be closed too."""
    last: dict = {}
    for event in read(journal)[0]:
        family = str(event.get("kind")).partition(".")[0]
        if family in ("step", "analyzer"):
            last[family, event.get("step"), event.get("analyzer") if family == "analyzer" else None] = event["kind"]
    left = sorted((key for key, kind in last.items() if kind.endswith(".started")), key=lambda key: key[0] == "step")
    bus = Bus(journal)
    for family, step, analyzer in left:
        if family == "analyzer":
            bus.emit("analyzer.finished", f"{analyzer} did not end: {cause}", step=step, analyzer=analyzer,
                     level="error", cause=cause, remedy=remedy)
        else:
            bus.emit("step.failed", cause, step=step, level="error", cause=cause, remedy=remedy)
    return [analyzer or step for _family, step, analyzer in left]
