"""The file inventory, the first write of a snapshot (spec 8.6): every file of the perimeter, once, as read.

One row per file, `{size, mtime, raw_hash, language}`, in walk order, in a SQLite store with no file entries.
`snapshot.write_reading` reads the files it lists, in this order and language. The header counts, by Linguist's name
and type, the files of the perimeter no reader reads (`unread`), from their names alone, and names the files of the
perimeter that are not the project's own code (`excluded`, `{path, why}`): vendored or documentation by Linguist's
expressions on the path (`vendor`, `documentation` of `linguist-catalog.json`), or as `.gitattributes` says
(`linguist-vendored`, `linguist-generated`, `linguist-documentation`, read by `git check-attr`). A generated file is
known only from `.gitattributes`: Linguist's `generated.rb` is code, not data. Where Git cannot read the attributes
the project declares, `excluded_unknown` says why.
"""
from __future__ import annotations

import collections
import functools
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from languages import detect_language
from languages.detect import linguist_name, linguist_type
from snapshot_store import SnapshotWriter, _plain
import format_catalog
from source_files import (git_attributes, git_info, is_inventory_path, iter_walked, MAX_FILE_BYTES, relative_to_root,
                          repo_root, scope_record)
from tree_scope import READ_DOT_DIRECTORIES, Perimeter

SCHEMA = 1  # the only header schema `SnapshotWriter.finish` accepts
WHY = ("vendored", "generated", "documentation")  # the first that holds is the file's reason
ATTRIBUTES = {"vendored": "linguist-vendored", "generated": "linguist-generated",
              "documentation": "linguist-documentation"}
EXPRESSIONS = {"vendored": "vendor", "documentation": "documentation"}  # the catalogue's table of each reason


@functools.cache
def _expressions() -> dict[str, re.Pattern]:
    """Linguist's expressions of each reason, joined as Linguist joins them (`Regexp.union`). A path is text with no
    grammar, so an expression is allowed on it (`AGENTS.md`); `format_catalog.check` proves each compiles with `re`.
    An expression that holds for a dot directory the perimeter enters (`READ_DOT_DIRECTORIES`) is left out: Linguist's
    `(^|/)\\.github/` keeps CI configuration out of its language statistics, and that configuration is the project's own,
    the stack tool's evidence (`.gitattributes` still decides)."""
    catalogue = json.loads(format_catalog.PATH.read_text(encoding="utf-8"))
    return {why: re.compile("|".join(expression for expression in catalogue[table]
                                     if not any(re.search(expression, name + "/") for name in READ_DOT_DIRECTORIES)))
            for why, table in EXPRESSIONS.items()}


def _holds(why: str, rel: str, value: str | None) -> bool:
    """Whether `rel` is `why`: as `.gitattributes` says when it sets or unsets the attribute, else by Linguist's
    expressions (a generated file has none)."""
    if value in ("set", "true"):
        return True
    if value in ("unset", "false"):
        return False
    return why in EXPRESSIONS and _expressions()[why].search(rel) is not None


def grouped(reasons: dict[str, str | None]) -> list[dict]:
    """`[{path, why}]` of the files with a reason: a folder whose every file has one reason is one entry, `folder/`;
    the files of a mixed folder stay apart."""
    under: dict[str, set] = collections.defaultdict(set)
    for path, why in reasons.items():
        parts = path.split("/")
        for depth in range(1, len(parts)):
            under["/".join(parts[:depth])].add(why)
    excluded = {}
    for path, why in sorted(reasons.items()):
        if why is None:
            continue
        parts, entry = path.split("/"), path
        for depth in range(1, len(parts)):
            if under["/".join(parts[:depth])] == {why}:
                entry = "/".join(parts[:depth]) + "/"
                break
        excluded[entry] = why
    return [{"path": path, "why": why} for path, why in excluded.items()]


def excluded(root: Path, paths: list[str]) -> tuple[list[dict], str | None]:
    """The files of `paths` (relative to `root`) that are not the project's own code, grouped by folder, and why the
    attributes the project declares were not read, if they were not."""
    said, unknown = git_attributes(root, paths, ATTRIBUTES.values())
    reasons = {rel: next((why for why in WHY if _holds(why, rel, said.get(rel, {}).get(ATTRIBUTES[why]))), None)
               for rel in paths}
    return grouped(reasons), unknown


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
            walked: list[str] = []
            for path in iter_walked(target, perimeter):
                walked.append(relative_to_root(path, root))
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
            left_out, unknown = excluded(root, walked)
            header = {"schema": SCHEMA, "target": relative_to_root(target, root) or ".", "root": root.as_posix(),
                      "scope": scope_record(perimeter, root), "git": git_info(root), "metrics": metrics,
                      "unread": _unread(counts), "excluded": left_out,
                      **({"excluded_unknown": unknown} if unknown else {}), "reading": "not-started"}
            writer.finish(header)
        os.replace(temporary, out)
        return header
    finally:
        temporary.unlink(missing_ok=True)
        Path(str(temporary) + "-journal").unlink(missing_ok=True)
