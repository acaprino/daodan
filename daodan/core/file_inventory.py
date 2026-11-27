"""The file inventory, the first write of a snapshot (spec 8.6): every file of the perimeter, once, as read.

One row per file, `{size, mtime, raw_hash, language}`, in walk order, in a SQLite store with no file entries.
`snapshot.write_reading` reads the files it lists, in this order and language. The header counts, by Linguist's name
and type, the files of the perimeter no reader reads (`unread`), from their names alone.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from languages import detect_language
from languages.detect import linguist_name, linguist_type
from snapshot_store import SnapshotWriter, _plain
from source_files import git_info, is_inventory_path, iter_walked, MAX_FILE_BYTES, relative_to_root, repo_root, scope_record
from tree_scope import Perimeter

SCHEMA = 1  # the only header schema `SnapshotWriter.finish` accepts


def _text(data: bytes) -> str:
    """The text a parser reads: decoded, its line ends `\\n`."""
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def _read_source(path: Path, supplied: dict, metrics: dict):
    """The stat, bytes and supplied parse of one walked file; None for a file above the size limit."""
    st = path.stat()
    observed = supplied.get(path.resolve())
    if observed is None and st.st_size > MAX_FILE_BYTES:
        return None
    if observed is not None:
        content, parsed = observed
        data = content.encode("utf-8")
    else:
        data = path.read_bytes()
        parsed = None
        metrics["files_read"] += 1
        metrics["source_bytes_read"] += len(data)
    if len(data) > MAX_FILE_BYTES:
        return None
    return st, data, parsed


def _temporary_beside(out: Path) -> Path:
    """A fresh, absent path beside `out` to write into before replacing it."""
    out.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{out.name}.", dir=out.parent)
    os.close(descriptor)
    temporary = Path(name)
    temporary.unlink()
    return temporary


def _unread(counts: dict[str, list]) -> dict:
    """`{name: {"type", "files"}}` of the files counted by `_count`: a suffix several languages list stays under the
    suffix with its `candidates`, of their type if they share one (`.md` is Markdown, prose, and GCC Machine
    Description, programming: no type, so no gap); a name Linguist does not give is `Unknown`."""
    found = {}
    for key, (names, files) in sorted(counts.items()):
        types = {linguist_type(name) for name in names}
        kind = types.pop() if len(types) == 1 else "Unknown"  # candidates of two types: no type is guessed
        found[key] = {"type": kind, "files": files, **({"candidates": names} if len(names) > 1 else {})}
    return found


def _count(counts: dict[str, list], path: Path) -> None:
    """Count one file by the name Linguist gives it: its own name, the suffix when several, `Unknown` when none."""
    names = linguist_name(path)
    key = names[0] if len(names) == 1 else path.suffix.lower() or path.name if names else "Unknown"
    counts.setdefault(key, [names, 0])[1] += 1


def write(target: Path, out: Path, *, parse_results: dict | None = None, progress=None) -> dict:
    """Walk the perimeter of `target` once and publish its inventory at `out`; returns the header."""
    target = Path(target).resolve()
    out = Path(out)
    _plain(out)
    if not (target.is_dir() or target.is_file()):
        raise ValueError(f"snapshot target does not exist: {target}")
    root = repo_root(target).resolve()
    perimeter = Perimeter(target)
    supplied = {Path(path).resolve(): value for path, value in (parse_results or {}).items()}
    metrics = {"files_read": 0, "source_bytes_read": 0}
    temporary = _temporary_beside(out)
    try:
        with SnapshotWriter(temporary, "sqlite") as writer:
            count = 0
            counts: dict[str, list] = {}
            for path in iter_walked(target, perimeter):
                if not is_inventory_path(path):
                    _count(counts, path)  # nothing of it is read
                    continue
                try:
                    read = _read_source(path, supplied, metrics)
                except OSError:
                    continue
                if read is None:
                    continue
                st, data, _parsed = read
                del read
                count += 1
                if progress is not None:
                    progress("reading", count)
                writer.put_inventory(relative_to_root(path, root), {
                    "size": len(data), "mtime": round(st.st_mtime, 3),
                    "raw_hash": hashlib.sha256(data).hexdigest(), "language": (
                        language := detect_language(path, _text(data)))})
                if language is None:
                    _count(counts, path)
                del data
            header = {"schema": SCHEMA, "target": relative_to_root(target, root) or ".", "root": root.as_posix(),
                      "scope": scope_record(perimeter, root), "git": git_info(root), "metrics": metrics,
                      "unread": _unread(counts), "reading": "not-started"}
            writer.finish(header)
        os.replace(temporary, out)
        return header
    finally:
        temporary.unlink(missing_ok=True)
        Path(str(temporary) + "-journal").unlink(missing_ok=True)
