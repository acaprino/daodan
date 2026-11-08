"""Append-only trail of note changes, one JSON line per event."""
import json
import threading
import time
from pathlib import Path


class AuditLog:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def record(self, user: str, action: str, name: str, now: float | None = None) -> None:
        entry = {"at": int(time.time() if now is None else now), "user": user, "action": action, "note": name}
        line = json.dumps(entry, ensure_ascii=True) + "\n"
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(line)

    def entries(self, user: str) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream if line.strip()]
        return [row for row in rows if row.get("user") == user]
