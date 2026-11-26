"""The snapshot as module derivation reads it: files and directories, source text
verified against the snapshot hash, and the path and digest helpers every module
step shares."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re

import confinement
import snapshot
import source_files
from tree_scope import DEPENDENCY_DIRS, Perimeter, workspace_glob

EMPTY_DIRECTORY = "directory holds no inventoried file"


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).casefold()).strip("-")


def _posix(value: str) -> str:
    return str(value).replace("\\", "/").strip().strip("/")


def _dirname(rel: str) -> str:
    return rel.rsplit("/", 1)[0] if "/" in rel else "."


def _inside(path: str, prefix: str) -> bool:
    return prefix == "." or path == prefix or path.startswith(prefix + "/")


def _join(base: str, relative: str) -> str:
    joined = os.path.normpath(os.path.join("" if base == "." else base, relative)).replace(os.sep, "/")
    return "." if joined in ("", ".") else joined.strip("/")


def _line_of(text: str, needle: str) -> int | None:
    for number, line in enumerate(text.split("\n"), 1):
        if needle and needle in line:
            return number
    return None


class StaleSource(ValueError):
    """A file on disk no longer matches the snapshot; nothing derived from it is evidence."""


class _Inventory:
    """Snapshot files and directories, with source text verified against the snapshot hash."""

    def __init__(self, store):
        self.store = store
        self.root = Path(store["root"])
        self.target = store.get("target") or "."
        self.headers = dict(store.iter_listed())  # the inventory's rows: `scan` and `stack` run before `parse`
        self.files = sorted(self.headers)
        self.directories: set[str] = {"."}
        for rel in self.files:
            parts = rel.split("/")
            for depth in range(1, len(parts)):
                self.directories.add("/".join(parts[:depth]))
        self._text: dict[str, str] = {}
        self._perimeter = None

    def exists(self, path: str) -> bool:
        return path in self.headers or path in self.directories

    def hash(self, rel: str) -> str | None:
        header = self.headers.get(rel)
        return header.get("raw_hash") if header else None

    def text(self, rel: str) -> str:
        if rel not in self._text:
            path = self.root / rel
            confinement.reject_link_chain(path)
            try:
                data = path.read_bytes()
            except OSError as error:
                raise ValueError(f"cannot read {rel}; refresh the manifest") from error
            if hashlib.sha256(data).hexdigest() != self.hash(rel):
                raise StaleSource(f"source changed since the snapshot: {rel}; refresh the manifest")
            self._text[rel] = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
        return self._text[rel]

    def files_under(self, paths: list[str], excluded: list[str] = ()) -> list[str]:
        return [rel for rel in self.files if any(_inside(rel, p) for p in paths)
                and not any(_inside(rel, p) for p in excluded)]

    def glob_directories(self, base: str, pattern: str) -> list[str]:
        """Directories matching a workspace pattern: `*` stays inside one segment, `**` crosses segments."""
        relative = _join(base, pattern.rstrip("/"))
        matcher = workspace_glob(relative)
        return sorted(d for d in self.directories if d != "." and matcher.fullmatch(d))

    def absence(self, rel: str) -> str:
        """Why a cited path is not in the snapshot."""
        rel = _posix(rel)
        parts = PurePosixPath(rel).parts
        if not parts or ".." in parts or PurePosixPath(rel).is_absolute() or ":" in parts[0]:
            return "not a project-relative path"
        if snapshot.is_forbidden(parts[-1], self.root / rel):
            return "credential or secret file, never inventoried"
        if any(part.startswith(".") for part in parts[:-1]):
            return "inside a dot directory, outside the map perimeter"
        if any(part in DEPENDENCY_DIRS for part in parts):
            return "inside a dependency or build directory, outside the map perimeter"
        path = self.root / rel
        try:
            exists, is_dir = path.exists(), path.is_dir()
        except OSError:
            exists, is_dir = False, False
        if not exists:
            return "absent from the tree"
        if is_dir and parts[-1].startswith("."):
            return "inside a dot directory, outside the map perimeter"
        if self._perimeter is None:
            target = (self.root / self.target).resolve()
            self._perimeter = Perimeter(target) if target.is_dir() else False
        probe = path / "probe" if is_dir else path
        if self._perimeter and self._perimeter.git_ignore == "applied" and not self._perimeter.covers(probe):
            return "ignored by Git, outside the map perimeter"
        if is_dir:
            return EMPTY_DIRECTORY
        suffix = path.suffix.lower()
        if (suffix not in snapshot.SUPPORTED_EXTENSIONS and suffix not in snapshot.DOC_EXTENSIONS
                and suffix not in snapshot.PRESENTATION_EXTENSIONS
                and not source_files.is_build_file(path.name)):
            return "file type the map does not inventory"
        return "present on disk but not in this snapshot; refresh the snapshot"


def _plain(path: Path) -> None:
    confinement.reject_link_chain(path)
    if path.exists() and not path.is_file():
        raise ValueError(f"artifact must be a regular file: {path}")
