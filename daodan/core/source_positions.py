"""Where an engine says a callee is declared, and the column units an engine and the snapshot count in."""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple



class Location(NamedTuple):
    """Where an engine says a callee is declared.

    `column` is the UTF-8 byte offset of the declaration's name on its 1-based
    `line`, the snapshot's own unit. A location without `module_path` is a
    definition the engine found outside any file, which is external.
    """

    module_path: Path | None
    line: int | None
    column: int | None


def byte_to_char(line: str, column: int) -> int | None:
    """A UTF-8 byte column as a code-point column, or None inside a character."""
    try:
        return len(line.encode("utf-8")[:column].decode("utf-8"))
    except UnicodeError:
        return None


def char_to_byte(line: str, column: int) -> int:
    return len(line[:column].encode("utf-8"))


def byte_to_utf16(line: str, column: int) -> int | None:
    """A UTF-8 byte column as UTF-16 code units, LSP's default position encoding."""
    chars = byte_to_char(line, column)
    return None if chars is None else len(line[:chars].encode("utf-16-le")) // 2


def utf16_to_byte(line: str, units: int) -> int | None:
    count = 0
    for index, character in enumerate(line):
        if count == units:
            return char_to_byte(line, index)
        if count > units:
            return None
        count += 2 if ord(character) > 0xFFFF else 1
    return len(line.encode("utf-8")) if count == units else None


class SourceLines:
    """Lines of the files an engine reads, decoded once."""

    def __init__(self):
        self._lines: dict[Path, list[str]] = {}

    def get(self, path: Path, line: int) -> str | None:
        path = Path(path)
        if path not in self._lines:
            try:
                self._lines[path] = path.read_text(encoding="utf-8").split("\n")
            except (OSError, UnicodeError):
                self._lines[path] = []
        lines = self._lines[path]
        return lines[line - 1] if type(line) is int and 1 <= line <= len(lines) else None


class EngineFailure(RuntimeError):
    """The engine can no longer answer; the pass stops asking and reports why."""
