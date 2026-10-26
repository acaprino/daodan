"""Small deterministic helpers shared by the engine."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

from .errors import DefinitionError


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def relative_path(value: str, *, field: str = "path") -> Path:
    if not isinstance(value, str) or not value.strip():
        raise DefinitionError(f"{field} must be a nonempty relative path")
    path = Path(value)
    if path.is_absolute() or path.drive or ".." in path.parts or value.startswith(("~", "/")):
        raise DefinitionError(f"{field} must stay inside the workspace: {value}")
    return path


def confined_path(root: Path, value: str, *, field: str = "path") -> Path:
    relative = relative_path(value, field=field)
    root = root.resolve()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise DefinitionError(f"{field} escapes the workspace: {value}")
    return candidate


def atomic_write_text(path: Path, text: str) -> None:
    """Replace a text file atomically without sharing a predictable temp file."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as output:
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
