"""Notes on disk: one directory per user, one UTF-8 file per note."""
import os
import re
from pathlib import Path

NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")


class StorageError(Exception):
    """A note name, size or lookup the store refuses."""


class NoteStore:
    def __init__(self, root: Path, max_bytes: int):
        self.root = root.resolve()
        self.max_bytes = max_bytes

    def _path(self, user: str, name: str) -> Path:
        if not user.isalnum() or not NAME.fullmatch(name):
            raise StorageError("invalid note name")
        return self.root / user / f"{name}.txt"

    def read(self, user: str, name: str) -> str:
        path = self._path(user, name)
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise StorageError("no such note") from None

    def write(self, user: str, name: str, text: str) -> None:
        data = text.encode("utf-8")
        if len(data) > self.max_bytes:
            raise StorageError("note too large")
        path = self._path(user, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, path)

    def names(self, user: str) -> list[str]:
        if not user.isalnum():
            raise StorageError("invalid user")
        folder = self.root / user
        if not folder.is_dir():
            return []
        return sorted(entry.stem for entry in folder.glob("*.txt"))
