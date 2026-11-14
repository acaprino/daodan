"""Shared pieces of the `lang` adapters: the file walk, Linguist's names and types, a subprocess wrapper.

Linguist's spelling is the one the corpus uses, so every adapter maps its tool's names onto it. The name and type
table is `languages.json`, converted from the gem's `languages.yml` when the Modal image is built.
Standard library only.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

DATA = Path(os.environ.get("LINGUIST_DATA", "/opt/linguist-data"))
_TABLE: dict | None = None
_BY_LOWER: dict | None = None


def files(root: str | Path) -> list[str]:
    """Every regular file below `root` as a POSIX path, `.git` left out, links to directories not followed."""
    root = Path(root)
    found = []
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for name in sorted(names):
            path = Path(folder) / name
            if path.is_file() or path.is_symlink():
                found.append(path.relative_to(root).as_posix())
    return found


def table() -> dict:
    global _TABLE
    if _TABLE is None:
        _TABLE = json.loads((DATA / "languages.json").read_text(encoding="utf-8"))
    return _TABLE


def _by_lower() -> dict:
    global _BY_LOWER
    if _BY_LOWER is None:
        _BY_LOWER = {}
        for name, entry in table().items():
            _BY_LOWER[name.lower()] = name
        for name, entry in table().items():
            for alias in entry.get("aliases") or []:
                _BY_LOWER.setdefault(str(alias).lower(), name)
    return _BY_LOWER


def canon(name: str | None, overrides: dict | None = None) -> str | None:
    """Linguist's spelling of a tool's language name: the tool's own table first, then Linguist's names and
    aliases; a name Linguist does not know comes back as the tool wrote it."""
    if not name:
        return None
    if overrides and name in overrides:
        return overrides[name]
    return _by_lower().get(name.lower(), name)


def known(name: str) -> bool:
    return name.lower() in _by_lower()


def type_of(name: str) -> str | None:
    """Linguist's type of a language (programming, markup, data, prose), None when Linguist has no such name."""
    entry = table().get(canon(name) or "")
    return entry.get("type") if entry else None


def sh(command: list[str], cwd: str | Path | None = None, timeout: int = 600, env: dict | None = None):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env,
                          encoding="utf-8", errors="replace")


def read_text(root: str | Path, relative: str, limit: int = 200_000) -> str | None:
    """The start of a file as text; None for a file with a NUL byte or one that cannot be read."""
    try:
        data = (Path(root) / relative).read_bytes()[:limit]
    except OSError:
        return None
    if b"\0" in data[:8000]:
        return None
    return data.decode("utf-8", errors="replace")
