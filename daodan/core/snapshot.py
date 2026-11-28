#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""
Structural snapshots and incremental change sets for the Codebase Map.

A run records the tree it analyzed as `snapshot/manifest.json`: every file with
its size, mtime and content hash, and every symbol with its line span and a hash
of its body. A later run diffs that manifest against the current worktree and
learns, without spending a model token, which files and symbols changed, which
files import them, and which claims in the earlier run's phase files cite any of
it.

Subcommands:
    scope <target>
        Count what a run would analyze and name what its perimeter leaves out. Parses nothing.
    files <manifest> --out <FILES.json>
    technologies <manifest> --out <TECHNOLOGIES.json>
        List the snapshot inventory: path, sha256 of the bytes, size, lines, language.
    write <target> --out <manifest.json> [--reuse <previous.json>]
        Write a structural snapshot; reuse parses only after checking file bytes.
        Also builds the lexical index, the module graph and the pre-map beside it
        (`--no-index` skips the first, `--no-modules` the other two; `modules.py` owns
        the graph, `premap/` the pre-map built on it), then
        starts the call-resolution engine pass in the background (`--no-engine`
        skips it; `resolve_edges.py` owns it).
    diff <parent_run> <target> --out <run_dir>
        Diff a parent run's snapshot against the worktree; write changes.json/changes.md.
    carry <parent_run> <run_dir>
        Copy the parent run's phase files forward, renumbering citations and marking stale claims.
    check <run_dir>
        Check the declared mode's delivery and whether it may publish.
    prepare <run_dir> [--phase N] [--stop-after N] [--resume-from [N] --run-name ID]
        Declare a run's artifacts, or verify and resume that same named run.
    publish <run_dir>
        Replace the phase-file mirror only after a complete delivery passes.
    register <run_dir> / unregister <run_dir>
        Update only this run's active entry under the publication registry lock.
    refresh [<project>] [--store S]
        Bring the run `working`, born from the published run, to the current source:
        snapshot, index, modules and `chiama` edges, then `refresh.json`.
    hook
        PostToolUse entry: `refresh` after an edit inside the published perimeter.

Standard library only. Parsing reuses the adapters in ./languages/. The Python
grammar is the running interpreter's, so this script declares `requires-python`
for `uv run --script` and refuses an older interpreter in main().
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from languages import SUPPORTED_EXTENSIONS, detect_language, get_adapter  # noqa: E402
from tree_scope import Perimeter  # noqa: E402
import file_inventory  # noqa: E402
from file_inventory import write as write_inventory, SCHEMA, _read_source, _temporary_beside, _text  # noqa: E402,F401
from snapshot_store import (SnapshotStore, artifact_digest, file_headers, open_snapshot, resolve_run_snapshot)  # noqa: E402
from source_files import (DOC_EXTENSIONS, git_info, hash_text, is_forbidden, iter_files,  # noqa: E402,F401
                          MANIFEST_FILES, MAX_FILE_BYTES, MAX_PARSE_BYTES, PRESENTATION_EXTENSIONS, read_text,
                          relative_to_root, repo_root, scope_record)
from parser_identity import grammar_gaps, parser_fingerprint, PARSER_PACKAGES, parser_profile  # noqa: E402,F401
from symbol_records import MAX_SIGNATURE_TEXT, signature_record, symbol_spans  # noqa: E402,F401
from symbols_at import (_entity_record, MAX_DIFF_CHARS, parse_unified_diff, _snapshot_info,  # noqa: E402,F401
                        symbols_at, SYMBOLS_AT_SCHEMA)
from import_resolution import (blast_radius, build_import_index, _by_basename, c_family_contexts,  # noqa: E402,F401
                               _C_FAMILY_SUFFIXES, context_key, iter_resolved_imports, module_targets,
                               _python_module_candidates, resolve_module, resolved_imports, _strip_jsonc_comments,
                               ts_path_config)
from run_store import (_acquire_registry_lock, _artifact_bytes, _artifact_hash, CANONICAL_STORE,  # noqa: E402,F401
                       _effective_flags, _hold, keep_local, own_store, _read_json, _read_registry, _reject_links,
                       _reject_links_below, _run_context,
                       RunControlError, STORE_MARKER, store_project, STORE_SCHEMA, update_registration, validate_store,
                       _write_json_atomic)
from change_set import (_changes_markdown, cited_symbols, cmd_carry, _legacy_check, MARKER_PREFIX,  # noqa: E402,F401
                        _match_cited_path, _path_index, PHASE_FILES, recommend, renumber_line, scan_claims)

__all__ = [
    "DOC_EXTENSIONS",
    "MANIFEST_FILES",
    "MARKER_PREFIX",
    "PHASE_FILES",
    "PRESENTATION_EXTENSIONS",
    "SCHEMA",
    "blast_radius",
    "build_import_index",
    "compare_files",
    "compare_symbols",
    "file_entry",
    "hash_text",
    "is_forbidden",
    "iter_files",
    "module_targets",
    "parser_fingerprint",
    "parser_profile",
    "read_text",
    "recommend",
    "renumber_line",
    "repo_root",
    "resolve_module",
    "resolved_imports",
    "scan_claims",
    "parse_unified_diff",
    "scope_record",
    "signature_record",
    "symbol_spans",
    "symbols_at",
    "ts_path_config",
]

_DETECT = object()  # `file_entry`'s language when none is given: detect it

# A stylesheet with a line longer than this is minified: every rule shares one
# line, so each rule symbol would hash the whole file and any edit would change
# them all. It stays a file-level entry.
MAX_STYLESHEET_LINE = 10_000


# A presentation file the product cannot read says so in its entry, never silently.
UNREAD_STYLESHEETS = {
    ".pug": "not read: no Pug reader in the product",
    ".styl": "not read: no Stylus reader in the product",
    ".stylus": "not read: no Stylus reader in the product",
}


def _record_parse(entry: dict, result, text: str, lines: list[str], profile: dict) -> dict:
    """What a parse result says about these bytes: status, imports, semantic facts and symbols."""
    entry["language"] = result.language
    entry["parser_notes"] = list(result.notes)
    if any(note.startswith("syntax error:") for note in result.notes):
        entry["status"] = "parse-error"
    else:
        entry["status"] = "parsed"
    # A loaded grammar can fail on this particular source and fall back.
    # Retain the availability profile for freshness checks, but do not cache
    # this result as a successful native parse. The reader returns it in full.
    # A component without a script gives its grammar nothing to parse: no fallback.
    if profile["backend"] == "tree-sitter" and not any(
        note.startswith(("parser=tree-sitter", "parser=sfc-no-script")) for note in result.notes
    ):
        entry["status"] = "parse-error"
    # A bare specifier can be a configured alias or workspace package. Its
    # classification becomes known only when the project graph is resolved.
    entry["imports"] = sorted({i.module for i in result.imports if i.module})
    entry["import_bindings"] = [
        {"module": item.module, "names": list(item.names), "from": item.is_from_import,
         **({"default_import": item.default_import} if getattr(item, "default_import", None) else {})}
        for item in result.imports if item.module
    ]
    if getattr(result, "default_export", None):
        entry["default_export"] = result.default_export
    if getattr(result, "tauri", None) and entry["status"] == "parsed":
        entry["tauri"] = result.tauri
    # Semantic facts belong to these exact bytes and the same parser
    # identity. A damaged parse cannot certify complete reference coverage:
    # its facts are kept only read around the error, with the lines it could
    # not read (`unread`, languages/semantic.py `_around`).
    semantic = getattr(result, "semantic", None)
    if isinstance(semantic, dict) and (entry["status"] == "parsed" or semantic.get("unread")):
        entry["semantic"] = copy.deepcopy(semantic)
    if result.language == "css" and max((len(text) for text in lines), default=0) > MAX_STYLESHEET_LINE:
        entry["status"] = "file-level"
        entry["parser_notes"].append("minified stylesheet; precise rule selection disabled")
        return entry
    entry["symbols"] = symbol_spans(result, lines)
    return entry


def file_entry(path: Path, data: bytes | None = None, mtime: float | None = None,
               *, parse_result=None, macros: dict | None = None, language=_DETECT) -> dict:
    """One manifest row, parsed from the same bytes whose identity it records.

    A given `language` (the inventory's, `None` included) is taken as is; by default it is detected.

    `macros` is a C or C++ file's include context (`c_family_contexts`): the entry records its key, because the
    same bytes read with other macros give other facts.
    """
    if mtime is None or data is None:
        stat = path.stat()
        mtime = round(stat.st_mtime, 3) if mtime is None else mtime
    data = path.read_bytes() if data is None else data
    text = _text(data)
    lines = text.split("\n")
    language = detect_language(path, text) if language is _DETECT else language
    profile = parser_profile(path, language)
    entry = {
        "size": len(data),
        "mtime": mtime,
        "hash": hash_text(text),
        "raw_hash": hashlib.sha256(data).hexdigest(),
        "language": language,
        "lines": len(lines),
        "symbols": {},
        "imports": [],
        "parser_profile": profile,
        "parser_notes": [],
        "status": "file-level",
    }
    if macros is not None and parse_result is None:
        entry["macro_context"] = context_key(macros)
    if path.suffix.lower() in UNREAD_STYLESHEETS:
        entry["parser_notes"] = [UNREAD_STYLESHEETS[path.suffix.lower()]]
    if language and len(data) > MAX_PARSE_BYTES:
        entry["status"] = "parse-skipped"
        entry["parser_notes"] = ["source exceeds parsing size limit"]
    elif language and parse_result is None and profile["backend"] == "unavailable":
        entry["status"] = "parse-skipped"
        entry["parser_notes"] = [f"grammar unavailable: {profile['grammar']}: {profile['reason']}"]
    elif language:
        try:
            data.decode("utf-8")  # Lossy decoding cannot supply precise source spans.
            adapter = get_adapter(language) if parse_result is None else None
            result = (parse_result if adapter is None else adapter.parse(text, str(path)) if macros is None
                      else adapter.parse(text, str(path), macros=macros))
        except Exception as exc:  # a parser failure degrades to a file-level entry
            entry["status"] = "parse-error"
            entry["parser_notes"] = [f"{type(exc).__name__}: {exc}"]
            return entry
        return _record_parse(entry, result, text, lines, profile)
    return entry


def _rejected(entry: dict) -> bool:
    """A Python file Daodan's interpreter could not parse: read again with the Python its project states."""
    return entry.get("language") == "python" and entry.get("status") == "parse-error" and any(
        note.startswith("syntax error:") for note in entry.get("parser_notes", ()))


def _newer_python(root: Path, rejected: list[tuple]) -> list[tuple[str, dict, bytes]]:
    """`(rel, entry, data)` of each `(path, rel, mtime, data, entry)` Daodan's interpreter rejected: parsed by the
    Python its project states where that one is newer (`languages/python_newer.py`), else its entry, whose syntax
    error says why not."""
    from languages import python_newer
    read = python_newer.reread(root, [(rel, _text(data)) for _path, rel, _mtime, data, _entry in rejected])
    out = []
    for path, rel, mtime, data, entry in rejected:
        tree, note = read.get(rel, (None, None))
        if tree is not None:
            entry = file_entry(path, data, mtime, language="python", parse_result=get_adapter("python").parse_tree(
                _text(data), str(path), tree, ["parser=stdlib-ast", note]))
        elif note:
            entry["parser_notes"] = [f"{item} ({note})" if item.startswith("syntax error:") else item
                                     for item in entry["parser_notes"]]
        out.append((rel, entry, data))
    return out


_REUSABLE_STATUSES = {"parsed", "file-level", "parse-skipped"}


def _reusable(old, path: Path, raw_hash: str, macro_key: str | None = None, *, language) -> bool:
    """A previous entry still describes these bytes: same bytes, language, include context and parser, a reusable
    status."""
    return (isinstance(old, dict) and old.get("raw_hash") == raw_hash
            and old.get("language") == language
            and (macro_key is None or old.get("macro_context") == macro_key)
            and old.get("parser_profile") == parser_profile(path, old.get("language"))
            and old.get("status") in _REUSABLE_STATUSES)


_RESERVED_METADATA = {"schema", "target", "root", "created_at", "git", "scope", "parser_fingerprint",
                      "metrics", "files", "file_count", "format", "reading", "unread", "excluded", "excluded_unknown"}


NO_PARSE_NODE = "no parse node in the plan"  # why a file is read as file-level (`_SnapshotPass.unplanned`)


class _SnapshotPass:
    """One streaming pass of the inventory's files into a snapshot writer: reuse what still holds, parse the rest.

    Each source is released once its entry is written; C and C++ files wait for their include context, and a
    Python file Daodan's interpreter rejects for the Python its project states (`newer`).
    """

    def __init__(self, format: str, previous, reusable: bool, fast_reuse: bool, metrics: dict, progress, rows: dict,
                 unplanned: frozenset | set = frozenset()):
        self.format = format
        self.previous = previous
        self.reusable = reusable
        self.fast_reuse = fast_reuse
        self.verified_headers = previous.verified_reusable_headers() if fast_reuse else {}
        self.metrics = metrics
        self.progress = progress
        self.rows = rows  # the inventory's rows by path, corrected where a file changed since
        self.unplanned = unplanned  # the files the plan puts in no parse node: read as file-level, with the cause
        self.writer = None
        self.count = 0
        self.exact_reused_paths: list[str] = []
        self.touched_reused_headers: dict[str, dict] = {}
        self.profiles: list[dict] = []
        self.rejected: list[tuple] = []  # `(path, rel, mtime, data, entry)` of the Python files `newer` reads again

    def _advance(self) -> None:
        self.count += 1
        if self.progress is not None:
            self.progress("parsing", self.count)

    def _put(self, rel: str, entry: dict, data: bytes) -> None:
        self.profiles.append(entry.get("parser_profile"))
        self.writer.put_file(rel, entry)
        if self.format == "sqlite":
            from semantic_store import observed_coverage
            from snapshot_store import _pack
            self.writer.connection.execute("INSERT INTO observed_coverage VALUES(?,?)",
                                           (rel, _pack(observed_coverage(entry, data))))

    def _fast_reused(self, rel: str, path: Path, row: dict) -> bool:
        """A header the previous SQLite snapshot verified, copied in bulk at the end instead of rewritten."""
        if not (self.fast_reuse and rel in self.verified_headers) or rel in self.unplanned:
            return False
        old_h = self.verified_headers[rel]
        if not _reusable(old_h, path, row["raw_hash"], language=row["language"]):
            return False
        self.metrics["cache_hits"] += 1
        self.profiles.append(old_h["parser_profile"])
        if old_h.get("size") == row["size"] and old_h.get("mtime") == row["mtime"]:
            self.exact_reused_paths.append(rel)
        else:
            updated_h = dict(old_h)
            updated_h["size"], updated_h["mtime"] = row["size"], row["mtime"]
            self.touched_reused_headers[rel] = updated_h
        return True

    def _entry(self, path: Path, rel: str, data: bytes, raw_digest: str | None, mtime: float, parsed,
               macros: dict | None = None) -> dict:
        """The previous entry when it still holds, otherwise a fresh parse."""
        old = self.previous.get_file(rel) if self.reusable else None
        language = None if rel in self.unplanned else self.rows[rel]["language"]
        key = None if macros is None else context_key(macros)
        if old is not None and _reusable(old, path, raw_digest or hashlib.sha256(data).hexdigest(), key, language=language):
            old["size"], old["mtime"] = len(data), mtime
            self.metrics["cache_hits"] += 1
            entry = old
        else:
            del old
            entry = (file_entry(path, data, mtime, parse_result=parsed, language=language) if macros is None
                     else file_entry(path, data, mtime, parse_result=parsed, macros=macros, language=language))
            if entry["status"] in {"parsed", "parse-error"} and parsed is None:
                self.metrics["parsed_files"] += 1
        if rel in self.unplanned:  # read as no language, so not parsed; the language stays the inventory's
            entry["language"] = self.rows[rel]["language"]
            if NO_PARSE_NODE not in entry["parser_notes"]:
                entry["parser_notes"] = [*entry["parser_notes"], NO_PARSE_NODE]
        return entry

    def sources(self, root: Path, supplied: dict) -> list[tuple]:
        """Write every inventoried file but the C and C++ ones, which are returned in reading order."""
        deferred: list[tuple[Path, str, float, bytes, object]] = []
        spent = {"files_read": 0, "source_bytes_read": 0}  # the inventory counted these reads
        for rel, row in list(self.rows.items()):
            path = root / rel
            c_family = rel.lower().endswith(_C_FAMILY_SUFFIXES)
            if not c_family:
                try:
                    st = path.stat()
                except OSError:
                    del self.rows[rel]
                    continue
                if ((st.st_size, round(st.st_mtime, 3)) == (row["size"], row["mtime"])
                        and (st.st_size <= file_inventory.MAX_FILE_BYTES or path.resolve() in supplied)
                        and self._fast_reused(rel, path, row)):
                    self._advance()
                    continue
            try:
                read = _read_source(path, supplied, spent)
            except OSError:
                read = None
            if read is None:
                del self.rows[rel]
                continue
            st, data, parsed = read
            del read
            mtime = round(st.st_mtime, 3)
            raw_digest = hashlib.sha256(data).hexdigest()
            fresh = {**row, "size": len(data), "mtime": mtime, "raw_hash": raw_digest}
            if fresh != row:
                self.rows[rel] = fresh
            if c_family:
                deferred.append((path, rel, mtime, data, parsed))
                del data
                continue
            entry = self._entry(path, rel, data, raw_digest, mtime, parsed)
            if _rejected(entry):
                self.rejected.append((path, rel, mtime, data, entry))
            else:
                self._put(rel, entry, data)
            del entry, data
            self._advance()
        return deferred

    def newer(self, root: Path) -> None:
        """The Python files Daodan's interpreter rejected, each read with the Python its project states."""
        for rel, entry, data in _newer_python(root, self.rejected) if self.rejected else ():
            self._put(rel, entry, data)
        self.rejected = []

    def c_family(self, deferred: list[tuple]) -> None:
        contexts = c_family_contexts({rel: data for _, rel, _, data, _ in deferred})
        deferred.reverse()  # popped from the end, in reading order, each source released once written
        while deferred:
            path, rel, mtime, data, parsed = deferred.pop()
            entry = self._entry(path, rel, data, None, mtime, parsed, contexts[rel])
            self._put(rel, entry, data)
            del entry, data
            self._advance()

    def close_sources(self) -> None:
        """Record the grammar gaps and bulk-copy the verified headers."""
        unavailable = grammar_gaps(self.profiles)
        if unavailable:
            self.metrics["grammars_unavailable"] = unavailable
        if self.exact_reused_paths or self.touched_reused_headers:
            self.writer.bulk_copy_from_sqlite(self.previous, self.exact_reused_paths, self.touched_reused_headers)
        if self.progress is not None:
            self.progress("validating", self.count)

    def seal(self, metadata_record: dict, perimeter: Perimeter) -> None:
        """Bind the semantic store to the finished header and seal the snapshot."""
        if self.format == "sqlite":
            from semantic_store import build_semantic_store
            reused_set = set(self.exact_reused_paths) | set(self.touched_reused_headers)
            with self.writer.reader() as current:
                current.metadata.update(metadata_record)
                build_semantic_store(
                    current,
                    writer=self.writer,
                    previous=self.previous if self.fast_reuse else None,
                    reused_files=reused_set if self.fast_reuse else None,
                    perimeter=perimeter,
                )
        self.writer.finish(metadata_record)


def _checked_options(format: str, extra_metadata: dict | None) -> dict:
    """The host metadata of a write, once its format and reserved names are checked."""
    from snapshot_store import validate_format

    validate_format(format)
    if extra_metadata is not None and (not isinstance(extra_metadata, dict)
            or any(not isinstance(key, str) or key in _RESERVED_METADATA for key in extra_metadata)):
        raise ValueError("invalid additional snapshot metadata")
    return dict(extra_metadata or {})


def read_project(target: Path, out: Path, *, format: str = "sqlite", previous=None,
                 parse_results: dict | None = None, extra_metadata: dict | None = None,
                 progress=None) -> dict:
    """Read the project into a snapshot, in two writes, the file inventory and then its reading; progress may cancel either.

    The inventory is staged beside `out` and removed at the end; only the reading publishes `out`.
    """
    from snapshot_store import _plain
    _checked_options(format, extra_metadata)
    out = Path(out)
    _plain(out)
    resolved = Path(target).resolve()
    if not (resolved.is_dir() or resolved.is_file()):
        raise ValueError(f"snapshot target does not exist: {resolved}")
    inventory = _temporary_beside(out)
    try:
        write_inventory(target, inventory, parse_results=parse_results, progress=progress)
        return write_reading(inventory, out, format=format, previous=previous, parse_results=parse_results,
                             extra_metadata=extra_metadata, progress=progress)
    finally:
        inventory.unlink(missing_ok=True)
        Path(str(inventory) + "-journal").unlink(missing_ok=True)


def write_reading(inventory: Path, out: Path, *, format: str = "sqlite", previous=None,
                  parse_results: dict | None = None, extra_metadata: dict | None = None,
                  progress=None) -> dict:
    """Read the files of an inventory (`file_inventory.write`), in its order and language, into a snapshot.

    Host metadata joins the immutable header before semantic binding. Reserved
    snapshot fields cannot be overridden by an embedding application's header.
    A file changed since the inventory is read as it now is, and its inventory row corrected.
    Its plan is the parse part only (`pipeline.plan.parse_nodes`): the inventory has no status yet, and the
    resolve and observe nodes are the plan of the read snapshot (`plan.stored`).
    """
    from datetime import datetime, timezone
    from snapshot_store import SnapshotWriter, _plain

    extra_metadata = _checked_options(format, extra_metadata)
    out = Path(out)
    _plain(out)
    with open_snapshot(inventory) as listed:
        if listed.metadata.get("reading") != "not-started":
            raise ValueError("not an inventory awaiting its reading")
        root = Path(listed.metadata["root"])
        target_key = listed.metadata["target"]
        target = (root / target_key).resolve()
        if not (target.is_dir() or target.is_file()):
            raise ValueError(f"snapshot target does not exist: {target}")
        fingerprint = parser_fingerprint()
        reusable = (previous is not None and previous.metadata.get("schema") == SCHEMA
                    and previous.metadata.get("root") == root.as_posix()
                    and previous.metadata.get("target") == target_key
                    and previous.metadata.get("parser_fingerprint") == fingerprint)
        counted = listed.metadata["metrics"]
        metrics = {"files_read": counted["files_read"], "source_bytes_read": counted["source_bytes_read"],
                   "parsed_files": 0, "cache_hits": 0}
        perimeter = Perimeter(target)
        temporary = _temporary_beside(out)
        supplied = {Path(path).resolve(): value for path, value in (parse_results or {}).items()}
        fast_reuse = (
            reusable
            and format == "sqlite"
            and getattr(previous, "format", None) == "sqlite"
            and hasattr(previous, "verified_reusable_headers")
            and previous._has_json_cache()
        )
        # The plan's `read_code` nodes (spec 8.4; no entries exist yet, so no status): a file in none of them is not
        # read by a language adapter. It keeps its inventory row and a file-level entry that says so.
        from pipeline import plan as planning
        rows = dict(listed.iter_inventory())
        parse = {node["id"] for node in planning.parse_nodes(rows.items())}
        run = _SnapshotPass(format, previous, reusable, fast_reuse, metrics, progress, rows,
                            {path for path, row in rows.items() if planning.node_of(row) not in parse})
        scope = listed.metadata["scope"]
        unread = listed.metadata.get("unread") or {}
        left_out = {key: listed.metadata[key] for key in ("excluded", "excluded_unknown") if key in listed.metadata}
    try:
        with SnapshotWriter(temporary, format) as writer:
            run.writer = writer
            if format == "sqlite":
                writer.connection.execute("CREATE TABLE observed_coverage(file TEXT PRIMARY KEY,payload BLOB)")
            run.c_family(run.sources(root, supplied))
            run.newer(root)
            run.close_sources()
            if format == "sqlite":
                for path, row in run.rows.items():
                    writer.put_inventory(path, row)
            metadata_record = {
                **extra_metadata,
                "schema": SCHEMA, "target": target_key, "root": root.as_posix(),
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "git": git_info(root), "scope": scope, "unread": unread, **left_out,
                "parser_fingerprint": fingerprint, "metrics": metrics,
            }
            run.seal(metadata_record, perimeter)
        _plain(out)
        # A caller reusing the same pathname transfers its reader to publication.
        # Windows cannot replace the file while that connection is open.
        if previous is not None and previous.path.resolve() == out.resolve():
            previous.close()
        os.replace(temporary, out)
        return {**metadata_record, "file_count": run.count, "format": format}
    finally:
        temporary.unlink(missing_ok=True)
        Path(str(temporary) + "-journal").unlink(missing_ok=True)


def compare_files(manifest: dict, target: Path, verify: bool = False,
                  raw_hashes: dict | None = None, *, source_identity=None) -> dict:
    """
    Classify every path as added, removed, modified or unchanged.

    Fast path: equal size and mtime means unchanged, with no read at all. Any
    other case is hashed, because a checkout or a `touch` moves the mtime
    without changing a byte, and the hash is what decides.

    Keep the manifest's coordinate root even when Git metadata is unavailable.
    Rediscovering it can rename surviving files from one comparison to the next.
    """
    target = target.resolve()
    recorded_root = manifest.get("root")
    root = (
        Path(recorded_root).resolve()
        if isinstance(recorded_root, str) and recorded_root
        else repo_root(target).resolve()
    )
    old = file_headers(manifest)
    structural_refresh = manifest.get("parser_fingerprint") != parser_fingerprint()
    current: dict[str, Path] = {}
    for path in iter_files(target):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        current[relative_to_root(path, root)] = path

    added, removed, modified, unchanged = [], [], [], []
    for rel, entry in old.items():
        path = current.get(rel)
        if path is None:
            removed.append(rel)
            continue
        try:
            stat = path.stat()
        except OSError:
            removed.append(rel)
            continue
        if structural_refresh or entry.get("parser_profile") != parser_profile(path, entry.get("language")):
            modified.append(rel)
            continue
        if source_identity is not None and entry.get("raw_hash"):
            try:
                identity = source_identity(path)
            except (OSError, ValueError):
                identity = None
            if identity is not None and raw_hashes is not None:
                raw_hashes[rel] = identity[0]
            (unchanged if identity and identity[0] == entry["raw_hash"] else modified).append(rel)
            continue
        if not verify and stat.st_size == entry.get("size") and round(stat.st_mtime, 3) == entry.get("mtime"):
            unchanged.append(rel)
            continue
        try:
            data = path.read_bytes()
            text = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
            same = hash_text(text) == entry.get("hash")
            if raw_hashes is not None:
                raw_hashes[rel] = hashlib.sha256(data).hexdigest()
        except OSError:
            same = False
        (unchanged if same else modified).append(rel)
    for rel in current:
        if rel not in old:
            added.append(rel)

    return {
        "root": root.as_posix(),
        "target": relative_to_root(target, root),
        "added": sorted(added),
        "removed": sorted(removed),
        "modified": sorted(modified),
        "unchanged": sorted(unchanged),
        "current": current,
    }


def compare_symbols(manifest: dict, comparison: dict, entries=None) -> dict:
    """
    Classify symbols inside added and modified files, and record how the lines
    of every surviving symbol moved.

    `fresh` carries the re-parsed structure of those files so the caller does
    not parse them a second time. `entries`, the headers of a newer snapshot,
    replaces the parse.
    """
    old_files = file_headers(manifest)
    added, removed, changed = [], [], []
    renumber: dict[str, list[dict]] = {}
    fresh: dict[str, dict] = {}

    for rel in comparison["added"] + comparison["modified"]:
        try:
            entry = entries[rel] if entries is not None else file_entry(comparison["current"][rel])
        except OSError:
            continue
        fresh[rel] = {"symbols": entry["symbols"], "imports": entry["imports"],
                      "import_bindings": entry.get("import_bindings", []),
                      "default_export": entry.get("default_export")}
        old_symbols = old_files.get(rel, {}).get("symbols", {})
        new_symbols = entry["symbols"]
        moved: list[dict] = []
        for name, spec in new_symbols.items():
            previous = old_symbols.get(name)
            if previous is None:
                added.append({"file": rel, "symbol": name, "kind": spec["kind"]})
            # A decorator sits above a Python span: its edit moves the signature
            # and leaves the body hash alone.
            elif previous["hash"] != spec["hash"] or previous.get("signatures") != spec.get("signatures"):
                changed.append({"file": rel, "symbol": name, "kind": spec["kind"]})
            else:
                moved.append({
                    "symbol": name,
                    "start_old": previous["start"],
                    "end_old": previous["end"],
                    "start_new": spec["start"],
                })
        for name, previous in old_symbols.items():
            if name not in new_symbols:
                removed.append({"file": rel, "symbol": name, "kind": previous["kind"]})
        if moved:
            renumber[rel] = sorted(moved, key=lambda m: m["start_old"])

    for rel in comparison["removed"]:
        for name, previous in old_files.get(rel, {}).get("symbols", {}).items():
            removed.append({"file": rel, "symbol": name, "kind": previous["kind"]})

    order = lambda item: (item["file"], item["symbol"])  # noqa: E731
    return {
        "added": sorted(added, key=order),
        "removed": sorted(removed, key=order),
        "changed": sorted(changed, key=order),
        "renumber": renumber,
        "fresh": fresh,
    }


def _diff_reasons(manifest, parent_state: dict, target: Path, flags: str | None) -> list[str]:
    """Why an incremental update cannot stand on the parent run: each reason forces a full run."""
    reasons: list[str] = []
    if parent_state.get("status") not in (None, "complete"):
        reasons.append(f"parent run status is {parent_state.get('status')}")
    if manifest.get("parser_fingerprint") != parser_fingerprint():
        reasons.append("parser identity changed or is missing; refresh the structural snapshot")
    target_resolved = target.resolve()
    root = repo_root(target_resolved).resolve()
    if manifest.get("root") != root.as_posix() or manifest.get("target") != relative_to_root(target_resolved, root):
        reasons.append("snapshot root or target differs from this run")
    if flags:
        try:
            requested = json.loads(flags)
        except ValueError:
            requested = {}
        parent_flags = parent_state.get("flags") or {}
        differing = sorted(k for k, v in requested.items() if parent_flags.get(k) != v)
        if differing:
            reasons.append("flags differ from the parent run: " + ", ".join(differing))
    return reasons


def _import_diagnostics(index: dict[str, list[str]], comparison: dict) -> tuple[dict, list[str], list[dict]]:
    """Static reachability beside the one-hop radius: graph metrics, the seeds and the transitive importers."""
    from dependency_graph import dependency_graph_metrics, transitive_importers

    diagnostic_graph = {rel: [] for rel in comparison["current"]}
    for dependency, importing_files in index.items():
        diagnostic_graph.setdefault(dependency, [])
        for importer in importing_files:
            diagnostic_graph.setdefault(importer, []).append(dependency)
    graph_metrics = dependency_graph_metrics(diagnostic_graph)
    diagnostic_seeds = sorted(set(comparison["added"]) | set(comparison["removed"]) | set(comparison["modified"]))
    return graph_metrics, diagnostic_seeds, transitive_importers(index, diagnostic_seeds)


def _change_record(manifest, parent_dir: Path, parent_state: dict, target: Path, comparison: dict, symbols: dict,
                   importers: list[dict], diagnostics: tuple, claims: list[dict], affected_files: list[str],
                   total: int, ratio: float, recommendation: str, reasons: list[str]) -> dict:
    from datetime import datetime, timezone
    graph_metrics, diagnostic_seeds, reachable_importers = diagnostics
    return {
        "schema": SCHEMA,
        "parent_run": parent_state.get("run_id") or parent_dir.name,
        "base_snapshot_created_at": manifest.get("created_at"),
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git": git_info(repo_root(target.resolve()).resolve()),
        "files": {
            "added": comparison["added"],
            "removed": comparison["removed"],
            "modified": comparison["modified"],
        },
        "symbols": {
            "added": symbols["added"],
            "removed": symbols["removed"],
            "changed": symbols["changed"],
        },
        "renumber": symbols["renumber"],
        "importers": importers,
        "import_cycles": graph_metrics["import_cycles"],
        "transitive_importers": reachable_importers,
        "transitive_seeds": diagnostic_seeds,
        "dependency_graph": {
            "nodes": len(graph_metrics["nodes"]),
            "edges": len(graph_metrics["edges"]),
            "pagerank": graph_metrics["pagerank"],
            **{key: value for key, value in graph_metrics.items() if key.startswith("pagerank_")},
            "interpretation": "Static import reachability and centrality; the one-hop recommendation is unchanged.",
        },
        "affected_files": affected_files,
        "claims": claims,
        "totals": {
            "files_in_snapshot": total,
            "affected_files": len(affected_files),
            "ratio": round(ratio, 4),
            "claims_affected": len(claims),
        },
        "recommendation": recommendation,
        "reasons": reasons,
    }


def cmd_diff(args: argparse.Namespace) -> int:
    with ExitStack() as stack:
        parent_dir = Path(args.parent_run)
        try:
            _reject_links_below(parent_dir)  # a parent run can come with the project
        except RunControlError as error:
            print(f"diff: {error}", file=sys.stderr)
            return 2
        target = Path(args.target)
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)

        parent_state = _read_json(parent_dir / "state.json") or {}
        present = any((parent_dir / f"snapshot/manifest.{format}").exists() for format in ("sqlite", "json"))
        manifest = stack.enter_context(open_snapshot(resolve_run_snapshot(parent_dir, parent_state))) if present else None
        missing = manifest is None
        if missing:
            manifest = {"files": {}, "target": None, "created_at": None}
        reasons = (["parent run has no snapshot manifest"] if missing else []) + _diff_reasons(
            manifest, parent_state, target, args.flags)

        comparison = compare_files(manifest, target, verify=args.verify)
        symbols = compare_symbols(manifest, comparison)
        index = build_import_index(manifest, comparison, symbols)
        importers = blast_radius(index, comparison, symbols)
        diagnostics = _import_diagnostics(index, comparison)
        claims = scan_claims(parent_dir, comparison, symbols, importers) if file_headers(manifest) else []

        affected_files = sorted(
            set(comparison["added"]) | set(comparison["removed"]) | set(comparison["modified"])
            | {entry["file"] for entry in importers}
        )
        # With no parent manifest, this falls back to the current worktree's file
        # count: the same fallback the ratio's denominator uses just below, so the
        # two always agree. A consumer that recomputes the ratio from the stored
        # totals must never divide by a files_in_snapshot of 0.
        total = len(file_headers(manifest) or {}) or len(comparison["current"]) or 1
        ratio = len(affected_files) / total
        recommendation = recommend(ratio, args.threshold, len(affected_files), reasons)
        changes = _change_record(manifest, parent_dir, parent_state, target, comparison, symbols, importers,
                                 diagnostics, claims, affected_files, total, ratio, recommendation, reasons)
        (out_dir / "changes.json").write_text(
            json.dumps(changes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (out_dir / "changes.md").write_text(_changes_markdown(changes), encoding="utf-8")
        print(
            f"change set: {recommendation}; {len(affected_files)} affected files of {total}, "
            f"{len(claims)} affected claims -> {out_dir / 'changes.json'}"
        )
        return 0


def _project_target(root: Path, value) -> Path:
    """The target a state of the store at `root` names, inside the store's project, or a refusal: a state is the
    store's, which a project can bring."""
    project = store_project(root)
    target = Path(value)
    target = (target if target.is_absolute() else project / target).resolve()
    if not target.is_relative_to(project):
        raise RunControlError("target is outside this run's project")
    return target


def _bound_manifest(run_dir: Path, root: Path, state: dict, fresh: bool = False) -> dict:
    try:
        with open_snapshot(resolve_run_snapshot(run_dir, state)) as manifest:
            validate_reuse_manifest(manifest)
            project = store_project(root)
            target = _project_target(root, state["target"])
            if not isinstance(manifest.get("root"), str) or not isinstance(manifest.get("target"), str):
                raise RunControlError("snapshot requires root and target binding")
            if (Path(manifest["root"]) / manifest["target"]).resolve() != target:
                raise RunControlError("snapshot and state target bindings differ")
            if Path(manifest["root"]).resolve() != repo_root(target).resolve():
                raise RunControlError("snapshot root differs from the target's repository binding")
            for name in file_headers(manifest):
                relative = Path(name)
                source = (Path(manifest["root"]) / relative).resolve()
                if relative.is_absolute() or ".." in relative.parts:
                    raise RunControlError("snapshot file paths must be confined relative paths")
                try:
                    source.relative_to(project)
                    if target.is_file():
                        if source != target:
                            raise ValueError("file target differs")
                    else:
                        source.relative_to(target)
                except ValueError as exc:
                    raise RunControlError("snapshot file is outside this run's target") from exc
            if fresh:
                if manifest.get("parser_fingerprint") != parser_fingerprint():
                    raise RunControlError("snapshot parser identity changed; start a new run")
                comparison = compare_files(manifest, target, verify=True)
                if comparison["added"] or comparison["removed"] or comparison["modified"]:
                    raise RunControlError("worktree changed since the run snapshot; start a new run or update")
                for name, entry in file_headers(manifest).items():
                    source = Path(manifest["root"]) / name
                    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != entry.get("raw_hash"):
                        raise RunControlError("worktree bytes changed since the run snapshot; start a new run or update")
                    if entry.get("parser_profile") != parser_profile(source, entry.get("language")):
                        raise RunControlError("effective parser changed since the run snapshot; start a new run")
            return dict(manifest.metadata)
    except ValueError as error:
        raise RunControlError(str(error)) from error


def _initial_delivery(run_dir: Path, root: Path, state: dict, stop_after: int | None,
                      classify_carry: bool = True) -> dict:
    flags = _effective_flags(state["flags"])
    mode = state["mode"]
    if mode == "team" and (flags["phase"] is not None or flags["docs_only"]):
        raise RunControlError("single-phase controls require classic mode")
    if stop_after is not None and (stop_after not in range(1, 7) or flags["phase"] or flags["docs_only"]):
        raise RunControlError("--stop-after accepts 1 through 6 and cannot combine with --phase or --docs-only")
    selected = {1, 2, 3, 4, 5, 6, 7}
    if flags["phase"] is not None:
        selected = {flags["phase"]}
    elif flags["docs_only"]:
        selected = {6}
    elif flags["depth"] == "lite":
        selected = {1, 2, 5, 7}
    if mode == "team" and flags["skip_synthesis"]:
        selected = set()
    if mode == "team" and not flags["skip_synthesis"] and not flags["skip_interconnect"]:
        selected.add(8)
    artifacts = {"knowledge/": {"phase": 0, "status": "produced"}}
    changes = _read_json(run_dir / "changes.json")
    updating = state.get("incremental") is not None
    if updating and (not isinstance(changes, dict) or not state.get("parent_run")):
        raise RunControlError("update requires changes.json and parent_run")
    record = _read_json(run_dir / "carry.json") or {}
    added = (changes or {}).get("symbols", {}).get("added", [])
    for phase, name in enumerate(PHASE_FILES, start=1):
        if phase not in selected:
            artifacts[name] = {"phase": phase, "status": "skipped", "reason": "not selected by the run's mode and flags"}
            continue
        artifact = {"phase": phase, "status": "produced"}
        data = _artifact_bytes(run_dir, name)
        if classify_carry and updating and phase != 7 and data:
            carried = record.get("artifacts", {}).get(name)
            if not isinstance(carried, dict):
                raise RunControlError(f"existing update artifact requires carry proof: {name}")
            provenance = {
                "kind": "carry", "run_id": record.get("parent_run"),
                "parent_path": record.get("parent_path"),
                "source_sha256": carried.get("source_sha256"), "sha256": carried.get("sha256"),
                "parent_manifest_sha256": record.get("parent_manifest_sha256"),
                "record_sha256": hashlib.sha256((run_dir / "carry.json").read_bytes()).hexdigest(),
            }
            if not _valid_inheritance(run_dir, root, state, name, {"provenance": provenance}):
                raise RunControlError(f"invalid carry proof for existing update artifact: {name}")
            if MARKER_PREFIX.encode() not in data and not added:
                artifact.update(status="inherited", provenance=provenance)
        artifacts[name] = artifact
    if flags["comments"] and flags["depth"] != "lite":
        if mode == "classic" and 6 in selected:
            artifacts["comment_health.md"] = {"phase": 6, "status": "produced"}
        elif mode == "team":
            partitions = state.get("partitions", [])
            if not isinstance(partitions, list):
                raise RunControlError("team partitions must be a list")
            for partition in partitions:
                name = partition.get("name") if isinstance(partition, dict) else None
                if not isinstance(name, str) or name in ("", ".", "..") or "/" in name or "\\" in name:
                    raise RunControlError("partition name must be one run-owned directory name")
                artifacts[f"partitions/{name}/06-documentation.md"] = {"phase": 6, "status": "produced"}
    if updating:
        artifacts["changes.md"] = {"phase": 7, "status": "produced"}
    return {
        "schema": 1, "mode": mode, "flags": flags,
        "binding": {"project": store_project(root).as_posix(), "target": state["target"], "parent_run": state.get("parent_run"), "parent_phases": state.get("parent_phases"), "incremental": updating},
        "stop_after": stop_after, "resume_from": None, "artifacts": artifacts,
        "run_phases": sorted({a["phase"] for a in artifacts.values() if a["status"] == "produced" and (stop_after is None or a["phase"] <= stop_after)}),
    }


def _validate_delivery(run_dir: Path, root: Path, state: dict) -> dict:
    delivery = state.get("delivery")
    if not isinstance(delivery, dict) or delivery.get("schema") != 1:
        raise RunControlError("run has no declared delivery; run prepare before dispatch")
    if delivery.get("mode") != state["mode"] or delivery.get("flags") != _effective_flags(state["flags"]):
        raise RunControlError("run mode or immutable flags changed; create a new run")
    binding = delivery.get("binding")
    expected = {"project": store_project(root).as_posix(), "target": state["target"], "parent_run": state.get("parent_run"), "parent_phases": state.get("parent_phases"), "incremental": state.get("incremental") is not None}
    if binding != expected:
        raise RunControlError("run project, target or lineage binding changed")
    artifacts = delivery.get("artifacts")
    if not isinstance(artifacts, dict):
        raise RunControlError("delivery artifacts must be an object")
    original = _initial_delivery(run_dir, root, state, delivery.get("stop_after"),
                                 classify_carry=False)["artifacts"]
    if set(original) != set(artifacts):
        raise RunControlError("delivery artifact set differs from the run's declared mode")
    for name, artifact in artifacts.items():
        if not isinstance(artifact, dict) or artifact.get("phase") != original[name]["phase"] or artifact.get("status") not in ("produced", "inherited", "skipped"):
            raise RunControlError(f"invalid artifact declaration: {name}")
        if (original[name]["status"] == "skipped") != (artifact["status"] == "skipped"):
            raise RunControlError(f"artifact skip conflicts with the run's mode: {name}")
        if artifact["status"] == "skipped" and not artifact.get("reason"):
            raise RunControlError(f"skipped artifact requires a reason: {name}")
    return delivery


def _valid_inheritance(run_dir: Path, root: Path, state: dict, name: str, artifact: dict) -> bool:
    provenance = artifact.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("sha256") != _artifact_hash(run_dir, name):
        return False
    if provenance.get("kind") == "resume":
        return (provenance.get("run_id") == state["run_id"] and provenance.get("manifest_sha256") == artifact_digest(resolve_run_snapshot(run_dir, state)))
    if provenance.get("kind") != "carry" or provenance.get("run_id") != state.get("parent_run"):
        return False
    record_path = run_dir / "carry.json"
    _reject_links(record_path)
    record = _read_json(record_path)
    if not isinstance(record, dict) or provenance.get("record_sha256") != hashlib.sha256(record_path.read_bytes()).hexdigest():
        return False
    parent = root / "runs" / str(state.get("parent_run"))
    _reject_links(parent)
    if parent.parent.resolve() != run_dir.parent or provenance.get("parent_path") != parent.as_posix() or record.get("parent_path") != parent.as_posix() or record.get("parent_run") != parent.name:
        return False
    parent_state = _read_json(parent / "state.json")
    if not isinstance(parent_state, dict) or parent_state.get("run_id") != parent.name or parent_state.get("target") != state["target"]:
        return False
    if parent_state.get("mode") != state["mode"] and not (state["mode"] == "classic" and parent_state.get("mode") == "team" and state.get("parent_phases") == [1, 2, 3, 4] and name in PHASE_FILES[:4]):
        return False
    parent_flags = _effective_flags(parent_state.get("flags") or {})
    if any(parent_flags[key] != _effective_flags(state["flags"])[key] for key in ("depth", "critical", "comments")):
        return False
    _bound_manifest(parent, root, parent_state)
    parent_manifest = artifact_digest(resolve_run_snapshot(parent, parent_state))
    if provenance.get("parent_manifest_sha256") != parent_manifest or record.get("parent_manifest_sha256") != parent_manifest:
        return False
    if not _artifact_bytes(parent, name):
        return False
    recorded = record.get("artifacts", {}).get(name)
    return (isinstance(recorded, dict) and recorded.get("sha256") == provenance.get("sha256") and recorded.get("source_sha256") == provenance.get("source_sha256") and provenance.get("source_sha256") == _artifact_hash(parent, name))


_CHANGES_SECTIONS = ("Claims confirmed", "Claims revised", "Claims retired", "Claims added", "Extra reads")


def _phase_markers(data: bytes, name: str, deferred: bool, index: dict, result: dict, documented: set) -> bool:
    """Stale markers left in a phase file, and the added symbols its citations document; True when blocking."""
    bad = False
    for number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), start=1):
        if MARKER_PREFIX in line:
            result["stale"].append({"artifact": name, "line": number, "deferred": deferred})
            bad = not deferred or bad
            continue
        if not deferred:
            for path_text, symbol in cited_symbols(line):
                resolved = _match_cited_path(path_text, index)
                if resolved:
                    documented.add((resolved, symbol))
    return bad


def _missing_sections(data: bytes, name: str, flags: dict) -> bool:
    """A changes.md without its required headings, or a documentation phase without its comment review."""
    if name == "changes.md":
        if any(f"## {heading}" not in data.decode("utf-8", errors="replace") for heading in _CHANGES_SECTIONS):
            return True
    documentation = name == "06-documentation.md" or name.endswith("/06-documentation.md")
    if documentation and flags["comments"] and flags["depth"] != "lite":
        text = data.decode("utf-8", errors="replace")
        section = re.search(r"^## Comment Quality\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
        if not section or not section.group(1).strip():
            return True
    return False


def _check_artifact(run_dir: Path, root: Path, state: dict, name: str, artifact: dict, delivery: dict,
                    index: dict, result: dict, documented: set, incomplete: list[int]) -> None:
    """One declared artifact against what the run directory holds."""
    phase = artifact["phase"]
    stop = delivery.get("stop_after")
    if artifact["status"] == "skipped":
        if (run_dir / name).exists():
            result["unexpected"].append(name)
        return
    produced = artifact["status"] == "produced"
    deferred = produced and stop is not None and phase > stop
    if deferred:
        result["not_yet_produced"].append(name)
        incomplete.append(phase)
    data = _artifact_bytes(run_dir, name)
    bad = False
    if not deferred:
        if data is None:
            result["missing"].append(name)
            bad = True
        elif not data:
            result["empty"].append(name)
            bad = True
        if artifact["status"] == "inherited" and (not data or not _valid_inheritance(run_dir, root, state, name, artifact)):
            result["invalid_inherited"].append(name)
            bad = True
    if data and name in PHASE_FILES:
        bad = _phase_markers(data, name, deferred, index, result, documented) or bad
    if data and not deferred and _missing_sections(data, name, delivery["flags"]):
        result["empty"].append(name)
        bad = True
    if bad and produced:
        incomplete.append(phase)


def _team_coverage(state: dict) -> list[dict]:
    """Partitions and agents of a team run that did not finish."""
    gaps = []
    for ledger, complete_status in (("partitions", "done"), ("agents_spawned", "delivered")):
        entries = state.get(ledger, [])
        if not isinstance(entries, list):
            raise RunControlError(f"team {ledger} must be a list")
        for number, entry in enumerate(entries):
            if not isinstance(entry, dict) or entry.get("status") != complete_status:
                gaps.append({"ledger": ledger, "index": number,
                             "name": entry.get("name") if isinstance(entry, dict) else None,
                             "status": entry.get("status") if isinstance(entry, dict) else None})
    return gaps


def check_delivery(run_dir: Path) -> dict:
    run_dir, root, state = _run_context(run_dir)
    delivery = _validate_delivery(run_dir, root, state)
    _bound_manifest(run_dir, root, state)
    result = {key: [] for key in ("missing", "empty", "unexpected", "invalid_inherited", "stale",
                                  "undocumented_added", "not_yet_produced", "coverage_gaps")}
    artifacts = delivery["artifacts"]
    flags = delivery["flags"]
    stop = delivery.get("stop_after")
    incomplete = []
    documented = set()
    changes = _read_json(run_dir / "changes.json") or {}
    added = changes.get("symbols", {}).get("added", [])
    index = _path_index({item["file"] for item in added})
    for name, artifact in artifacts.items():
        _check_artifact(run_dir, root, state, name, artifact, delivery, index, result, documented, incomplete)
    if added:
        eligible = [a["phase"] for name, a in artifacts.items() if name in PHASE_FILES[:6] and a["status"] == "produced"]
        due = [phase for phase in eligible if stop is None or phase <= stop]
        if due:
            for item in added:
                if (item["file"], item["symbol"]) not in documented:
                    result["undocumented_added"].append(f"{item['file']}::{item['symbol']}")
                    incomplete.append(min(due))
    for path in run_dir.glob("[0-9][0-9]-*.md"):
        _reject_links(path)
        if path.name not in artifacts:
            result["unexpected"].append(path.name)
    if (run_dir / "comment_health.md").exists() and "comment_health.md" not in artifacts:
        result["unexpected"].append("comment_health.md")
    if delivery["mode"] == "team":
        result["coverage_gaps"].extend(_team_coverage(state))
    for key in ("missing", "empty", "unexpected", "invalid_inherited"):
        result[key] = sorted(set(result[key]))
    result["first_incomplete_phase"] = min(incomplete) if incomplete else None
    blocking = (any(result[key] for key in ("missing", "empty", "unexpected", "invalid_inherited",
                                            "undocumented_added", "coverage_gaps"))
                or any(not marker["deferred"] for marker in result["stale"]))
    result.update(run_id=state["run_id"], mode=delivery["mode"], invocation_complete=not blocking,
                  complete=not blocking and stop is None,
                  may_publish=not blocking and stop is None and flags["phase"] is None and not flags["docs_only"]
                  and not flags["skip_synthesis"])
    return result


def cmd_prepare(args: argparse.Namespace) -> int:
    try:
        run_dir, root, state = _run_context(Path(args.run_dir))
        if args.mode is not None and args.mode != state["mode"]:
            raise RunControlError("requested mode differs; create a new run")
        if args.flags is not None and _effective_flags(json.loads(args.flags)) != _effective_flags(state["flags"]):
            raise RunControlError("requested flags differ; create a new run")
        if args.resume_from is not None:
            if args.run_name != state["run_id"]:
                raise RunControlError("resume requires --run-name naming this exact existing run")
            if args.phase is not None or args.stop_after is not None:
                raise RunControlError("resume cannot combine with phase or stop controls")
            delivery = _validate_delivery(run_dir, root, state)
            _bound_manifest(run_dir, root, state, fresh=True)
            checked = check_delivery(run_dir)
            if checked["invalid_inherited"]:
                raise RunControlError("inherited proof is invalid; restore its bound evidence or create a new run")
            start = checked["first_incomplete_phase"] if args.resume_from == "auto" else args.resume_from
            if start is None:
                raise RunControlError("run has no incomplete phase; use --resume-from 7 to regenerate its report")
            if args.resume_from != "auto" and args.resume_from not in range(1, 8):
                raise RunControlError("explicit resume accepts 1 through 7")
            if checked["unexpected"]:
                raise RunControlError("unexpected artifacts must be resolved before resume")
            invalid = set(checked["missing"] + checked["empty"])
            invalid.update(marker["artifact"] for marker in checked["stale"] if not marker["deferred"])
            if checked["undocumented_added"]:
                invalid.update(name for name, item in delivery["artifacts"].items() if item["phase"] == checked["first_incomplete_phase"])
            earlier = {name: item for name, item in delivery["artifacts"].items() if item["status"] != "skipped" and item["phase"] < start}
            if any(name in invalid or name in checked["not_yet_produced"] for name in earlier):
                print(json.dumps({"error": "earlier required artifacts are incomplete", "check": checked}))
                return 1
            manifest_hash = artifact_digest(resolve_run_snapshot(run_dir, state))
            delivery = copy.deepcopy(delivery)
            for name, item in delivery["artifacts"].items():
                if item["status"] == "skipped":
                    continue
                if item["phase"] < start and item["status"] == "produced":
                    item.update(status="inherited", provenance={"kind": "resume", "run_id": state["run_id"], "sha256": _artifact_hash(run_dir, name), "manifest_sha256": manifest_hash})
                elif item["status"] == "produced":
                    item["status"] = "produced"
                    item.pop("provenance", None)
            delivery.update(stop_after=None, resume_from=start,
                            run_phases=sorted({item["phase"] for item in delivery["artifacts"].values() if item["status"] == "produced" and item["phase"] >= start}))
            state["status"] = "in_progress"
        else:
            if state.get("delivery") is not None:
                raise RunControlError("run already has a declaration; use --resume-from")
            if args.phase is not None:
                state["flags"]["phase"] = args.phase
            _bound_manifest(run_dir, root, state)
            delivery = _initial_delivery(run_dir, root, state, args.stop_after)
        state["delivery"] = delivery
        _write_json_atomic(run_dir / "state.json", state)
        print(json.dumps(delivery, sort_keys=True))
        return 0
    except (RunControlError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


def cmd_check(args: argparse.Namespace) -> int:
    state = _read_json(Path(args.run_dir) / "state.json")
    if not isinstance(state, dict) or "delivery" not in state:
        if not args.json:
            return _legacy_check(args)
        print(json.dumps({"error": "run has no declared mode-aware delivery", "may_publish": False}))
        return 2
    try:
        result = check_delivery(Path(args.run_dir))
        print(json.dumps(result, sort_keys=True) if args.json else "check: " + json.dumps(result, sort_keys=True))
        return 0 if result["invocation_complete"] else 1
    except (RunControlError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc), "may_publish": False}))
        return 2


def cmd_registry(args: argparse.Namespace) -> int:
    try:
        result = update_registration(Path(args.run_dir), active=args.command == "register")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (RunControlError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


def publish_run(run_dir: Path) -> dict:
    run_dir, root, state = _run_context(run_dir)
    lock = _acquire_registry_lock(root)
    try:
        if state.get("status") != "in_progress":
            raise RunControlError(f"only an in-progress run can publish; status is {state.get('status')!r}; resume it first")
        checked = check_delivery(run_dir)
        if not checked["may_publish"]:
            return {"published": False, "check": checked}
        _bound_manifest(run_dir, root, state, fresh=True)
        names = (*PHASE_FILES, "state.json", "runs.json")
        before = {}
        for name in names:
            path = root / name
            _reject_links(path)
            if path.exists() and not path.is_file():
                raise RunControlError(f"mirror path is not a regular file: {name}")
            before[name] = path.read_bytes() if path.exists() else None
        registry = _read_registry(root)
        payloads = {name: (run_dir / name).read_bytes() for name in PHASE_FILES if state["delivery"]["artifacts"][name]["status"] != "skipped"}
        from datetime import datetime, timezone
        published_state = copy.deepcopy(state)
        published_state.update(status="complete", completed_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        registry["active"] = [item for item in registry["active"] if item["run_id"] != state["run_id"]]
        registry["latest_completed"] = state["run_id"]
        payloads["state.json"] = (json.dumps(published_state, indent=2, sort_keys=True) + "\n").encode()
        payloads["runs.json"] = (json.dumps(registry, indent=2, sort_keys=True) + "\n").encode()
        run_state_before = (run_dir / "state.json").read_bytes()
        with tempfile.TemporaryDirectory(prefix=".map-publish-", dir=root) as temporary:
            staged = Path(temporary)
            for name, data in payloads.items():
                (staged / name).write_bytes(data)
            # Re-check after staging; publication never trusts an earlier coordinator check.
            rechecked = check_delivery(run_dir)
            if not rechecked["may_publish"] or any((run_dir / name).read_bytes() != data for name, data in payloads.items() if name in PHASE_FILES):
                raise RunControlError("delivery changed while preparing publication")
            _bound_manifest(run_dir, root, state, fresh=True)
            try:
                for name in names:
                    destination = root / name
                    if name in payloads:
                        os.replace(staged / name, destination)
                    elif destination.exists():
                        destination.unlink()
                _write_json_atomic(run_dir / "state.json", published_state)
            except OSError:
                for name, data in before.items():
                    destination = root / name
                    if data is None:
                        if destination.exists():
                            destination.unlink()
                    else:
                        destination.write_bytes(data)
                (run_dir / "state.json").write_bytes(run_state_before)
                raise
        return {"published": True, "run_id": state["run_id"], "mirror": root.as_posix()}
    finally:
        lock.unlink()


def cmd_publish(args: argparse.Namespace) -> int:
    try:
        result = publish_run(Path(args.run_dir))
        print(json.dumps(result, sort_keys=True))
        return 0 if result["published"] else 1
    except (RunControlError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"published": False, "error": str(exc)}))
        return 2


WORKING_RUN = "working"
# Over this share of changed files a refresh rebuilds without reusing a parse.
FULL_REBUILD_SHARE = 0.4


def published_run(root: Path) -> Path | None:
    """The store's latest complete run, the one the working run follows: the registry names it, never a path."""
    own_store(root)
    run_id = _read_registry(root).get("latest_completed")
    if run_id is None or run_id == WORKING_RUN:
        return None
    run = root / "runs" / run_id
    state = _read_json(run / "state.json")
    return run if isinstance(state, dict) and state.get("status") == "complete" else None


def _refresh_action(root: Path) -> str:
    project = store_project(root)
    store = root.relative_to(project).as_posix()
    return f"snapshot.py refresh {project.as_posix()}" + ("" if store == CANONICAL_STORE else f" --store {store}")


def query_gate(manifest: Path) -> dict | None:
    """None when a query may answer from this snapshot, else why not and what to run.

    Only the working run and the published run are gated: the working run when
    its last refresh did not end fresh or left another manifest, both when the
    current source bytes differ from the snapshot. Verified byte identities are reused only
    while the filesystem identity and change clock still match.
    """
    manifest = Path(manifest).resolve()
    run = manifest.parent.parent
    if manifest.parent.name != "snapshot" or run.parent.name != "runs":
        return None
    root = run.parent.parent
    if run.name != WORKING_RUN and published_run(root) != run:
        return None

    def needs(reason: str) -> dict:
        return {"state": "needs_refresh", "run_id": run.name, "reason": reason,
                "action": _refresh_action(root) + f", then query run {WORKING_RUN!r}"}

    if run.name == WORKING_RUN:
        refresh = _read_json(run / "refresh.json") or {}
        if refresh.get("status") != "fresh":
            return needs(f"working run refresh is {refresh.get('status', 'missing')}"
                         + (f": {refresh['error']}" if refresh.get("error") else ""))
        st = manifest.stat()
        if refresh.get("manifest_stat") != [st.st_ino, st.st_size, st.st_mtime_ns]:
            return needs("the working snapshot is not the one its last refresh published")
    from store_graph import source_identity
    with open_snapshot(manifest) as store:
        comparison = compare_files(store, Path(store["root"]) / store["target"], verify=True,
                                   source_identity=source_identity)
    changed = comparison["added"] + comparison["removed"] + comparison["modified"]
    if changed:
        return needs(f"{len(changed)} files changed since the snapshot: " + ", ".join(changed[:5]))
    return None


LIVE_PULSE = "live-pulse.jsonl"


def append_live_pulse(root: Path, kind: str, **data) -> dict:
    """Append one reactive store pulse line so MCP and UI listeners observe hook/service updates without blocking."""
    from datetime import datetime, timezone
    import confinement
    entry = {"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "kind": kind, **data}
    target = Path(root) / LIVE_PULSE
    confinement.reject_link_chain(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return entry


def read_live_pulse(root: Path, after: int = 0, limit: int = 100) -> dict:
    import confinement
    target = Path(root) / LIVE_PULSE
    confinement.reject_link_chain(target)
    if not target.is_file():
        return {"events": [], "next_cursor": after, "has_more": False}
    lines = target.read_text(encoding="utf-8").split("\n")[:-1]
    chosen = lines[after:after + limit + 1]
    page = [json.loads(line) for line in chosen[:limit]]
    return {"events": page, "next_cursor": after + len(page), "has_more": len(chosen) > limit}


def refresh_working(root: Path) -> dict:
    """Bring the working run to the current source; one refresh runs, at most one waits."""
    published = published_run(root)
    if published is None:
        return {"status": "skipped", "reason": "no published run"}
    working = root / "runs" / WORKING_RUN
    for run in (published, working):  # the refresh reads, replaces and removes files of both
        _reject_links_below(run)
    keep_local(root)
    (working / "snapshot").mkdir(parents=True, exist_ok=True)
    queued = _hold(working / ".refresh-queue.lock", wait=False)
    if queued is None:
        return {"status": "queued", "reason": "a refresh is already waiting and will see this change"}
    try:
        active = _hold(working / ".refresh.lock", wait=True)
    finally:
        queued.unlink()
    try:
        # MCP readers must close their snapshots before Windows can replace one.
        from confinement import project_lock
        with project_lock(store_project(root)):
            return _refresh_locked(root, published, working)
    finally:
        active.unlink()


def _refresh_locked(root: Path, published: Path, working: Path) -> dict:
    import pipeline
    import resolve_edges
    import retrieval
    from datetime import datetime, timezone

    started = time.perf_counter()
    report_path = working / "refresh.json"
    previous = _read_json(report_path) or {}
    pstate = _read_json(published / "state.json")
    state = _read_json(working / "state.json") or {}
    born = state.get("parent_run") != published.name
    if born:
        state = {key: pstate.get(key) for key in ("mode", "target", "flags", "snapshot")}
        state.update(run_id=WORKING_RUN, status="working", parent_run=published.name,
                     engine=pstate.get("engine", True))
        for stale in (working / "snapshot").glob("manifest.*"):
            stale.unlink()
        # The stack record goes too: the fast scan keeps the signs of the sources only a full scan runs.
        for carried in ("proposals.json", "technologies.json"):
            if (published / "snapshot" / carried).is_file():
                shutil.copy2(published / "snapshot" / carried, working / "snapshot" / carried)
            else:
                (working / "snapshot" / carried).unlink(missing_ok=True)
        _write_json_atomic(working / "state.json", state)
    manifest = working / state["snapshot"]["path"]
    target = _project_target(root, state["target"])
    now = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    try:
        with ExitStack() as stack:
            base = stack.enter_context(open_snapshot(resolve_run_snapshot(published if born else working, state)))
            raw: dict = {}
            comparison = compare_files(base, target, verify=True, raw_hashes=raw)
            headers = file_headers(base)
            changed = sorted(comparison["added"] + comparison["removed"] + comparison["modified"]
                             + [name for name in comparison["unchanged"]
                                if raw.get(name) != headers[name].get("raw_hash")])
            if not born and not changed and previous.get("status") == "fresh":
                return {"status": "unchanged", "changed": 0}
            full = len(changed) > FULL_REBUILD_SHARE * max(len(headers), 1)
            _write_json_atomic(report_path, {"status": "running", "started_at": now()})
            resolve_edges.reset_pass(manifest)
            if full:
                # A full rebuild reuses nothing; Windows cannot replace the manifest this reader holds.
                base.close()
            written = read_project(target, manifest, format=state["snapshot"]["format"],
                                     previous=None if full else base)
        index = retrieval.ensure_index(manifest)
        if index["state"] != "fresh":
            raise ValueError(f"index: {index['state']}: {index.get('reason', '')}")
        piped = pipeline.run(manifest, stop=pipeline.FindEntryPoints.NAME, fast_scan=True)
        scanned = piped[pipeline.FindModules.NAME]
        if "failed" in scanned:
            raise ValueError(f"modules: {scanned['failed']}")
        stacked = piped.get(pipeline.RecognizeStack.NAME) or {}
        engine = resolve_edges.ensure_edges(manifest) if state.get("engine", True) else {"state": "off"}
        with ExitStack() as stack:
            base = stack.enter_context(open_snapshot(resolve_run_snapshot(published, pstate)))
            current = stack.enter_context(open_snapshot(manifest))
            old, new = file_headers(base), file_headers(current)
            delta = {"added": sorted(set(new) - set(old)), "removed": sorted(set(old) - set(new))}
            delta["modified"] = sorted(name for name in set(old) & set(new)
                                       if old[name].get("hash") != new[name].get("hash"))
            delta["unchanged"] = sorted(set(old) & set(new) - set(delta["modified"]))
            symbols = compare_symbols(base, delta, entries=new)
        st = manifest.stat()
        report = {
            "status": "fresh", "refreshed_at": now(), "published_run": published.name,
            "rebuild": "full" if full else "incremental", "changed_since_last": len(changed),
            "parsed_files": written["metrics"]["parsed_files"],
            "modules": scanned.get("modules", 0),
            "stack": {"state": "failed" if "failed" in stacked else "fresh", **stacked},
            "seconds": round(time.perf_counter() - started, 2),
            "engine": {"fresh": "fresh", "running": "running"}.get(engine["state"], "unavailable"),
            "manifest_stat": [st.st_ino, st.st_size, st.st_mtime_ns],
            "since_published": {"files": {key: delta[key] for key in ("added", "removed", "modified")},
                                "symbols": {key: symbols[key] for key in ("added", "removed", "changed")},
                                "claims": scan_claims(published, delta, symbols, [])},
        }
        append_live_pulse(root, "working.refreshed", run_id=WORKING_RUN, changed=len(changed),
                          modules=scanned.get("modules", 0), technologies=stacked.get("technologies", 0))
    except (OSError, ValueError, KeyError, TypeError, RunControlError) as error:
        report = {"status": "failed", "refreshed_at": now(), "error": str(error)}
    _write_json_atomic(report_path, report)
    return {key: value for key, value in report.items() if key != "since_published"}


def cmd_refresh(args: argparse.Namespace) -> int:
    try:
        project = Path(args.project).resolve()
        root = project / (validate_store(args.store) if args.store else CANONICAL_STORE)
        result = refresh_working(root)
    except (RunControlError, OSError, ValueError) as error:
        result = {"status": "failed", "error": str(error)}
    print(json.dumps(result, sort_keys=True))
    return 2 if result["status"] == "failed" else 0


def cmd_hook(args: argparse.Namespace) -> int:
    """PostToolUse: refresh after an edit inside the published run's perimeter; never fails the tool."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
        root = next((base / CANONICAL_STORE for base in (cwd, *cwd.parents)
                     if (base / CANONICAL_STORE / "runs.json").is_file()), None)
        published = published_run(root) if root is not None else None
        if published is None:
            return 0
        tool_input = payload.get("tool_input") or {}
        edited = tool_input.get("file_path") or tool_input.get("notebook_path")
        if edited:
            project = store_project(root)
            target = _project_target(root, (_read_json(published / "state.json") or {}).get("target", "."))
            path = (cwd / edited).resolve()
            if (not path.is_relative_to(target) or path.relative_to(project).parts[0] in (".daodan", ".team-review")
                    or not Perimeter(target).covers(path)):
                return 0
        print(json.dumps(refresh_working(root), sort_keys=True))
    except (RunControlError, OSError, ValueError, AttributeError, TypeError):
        pass
    return 0


def inventory_rows(manifest: Path) -> list[dict]:
    """Every snapshot file with the identity of its bytes, sorted by path: the inventory a review splits.
    `status` and `imports` (the modules as the source writes them) tell a review which libraries a file uses."""
    with open_snapshot(Path(manifest)) as store:
        rows = [{"path": path, "sha256": entry["raw_hash"], "size": entry["size"],
                 "lines": entry.get("lines"), "language": entry.get("language"),
                 "status": entry.get("status"), "imports": list(entry.get("imports") or [])}
                for path, entry in store.iter_file_headers_only()]
    return sorted(rows, key=lambda row: row["path"])


def cmd_files(args: argparse.Namespace) -> int:
    try:
        rows = inventory_rows(Path(args.manifest))
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2
    payload = {"schema": "codebase-map/files/v1", "manifest": Path(args.manifest).resolve().as_posix(), "files": rows}
    Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"files": len(rows)}))
    return 0


def cmd_technologies(args: argparse.Namespace) -> int:
    import technologies
    try:
        payload = technologies.ensure(Path(args.manifest))
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2
    Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"technologies": len(payload["technologies"]), "units": len(payload["units"])}))
    return 0


def cmd_scope(args: argparse.Namespace) -> int:
    """
    The figures a scope confirmation shows, from the same walk the manifest
    takes: a count made by hand would not apply the perimeter, and the user
    would confirm one number and get another.
    """
    target = Path(args.target).resolve()
    root = repo_root(target).resolve()
    perimeter = Perimeter(target)
    sets = {"parsed_source": 0, "configuration_and_documentation": 0, "presentation": 0}
    languages: dict[str, int] = {}
    files = 0
    for path in iter_files(target, perimeter):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        files += 1
        suffix = path.suffix.lower()
        # By extension alone: this runs before the user has confirmed anything,
        # so it reads no file. The manifest may name a language more precisely.
        language = SUPPORTED_EXTENSIONS.get(suffix)
        if language and language != "markup":  # markup is presentation, read for its style blocks
            sets["parsed_source"] += 1
            languages[language] = languages.get(language, 0) + 1
        elif suffix in DOC_EXTENSIONS:
            sets["configuration_and_documentation"] += 1
        else:
            sets["presentation"] += 1
    print(json.dumps({
        "target": relative_to_root(target, root) or ".",
        "files": files,
        "sets": sets,
        "languages": languages,
        "scope": scope_record(perimeter, root),
    }, indent=2, sort_keys=True))
    return 0


def validate_reuse_manifest(manifest: object) -> None:
    """Reject malformed stored structure before it can replace a valid output."""
    if isinstance(manifest, SnapshotStore):
        validate_reuse_manifest({**manifest.metadata, "files": {}})
        for rel, entry in manifest.iter_files(semantic=False):
            validate_reuse_manifest({**manifest.metadata, "files": {rel: entry}})
        return
    if (not isinstance(manifest, dict) or type(manifest.get("schema")) is not int or manifest["schema"] != SCHEMA
            or not isinstance(file_headers(manifest), dict)
            or not isinstance(manifest.get("root"), str)
            or not isinstance(manifest.get("target"), str)):
        raise ValueError("expected a snapshot object with schema, root, target and files")
    if "parser_fingerprint" in manifest and not isinstance(manifest["parser_fingerprint"], str):
        raise ValueError("invalid cached parser fingerprint")
    for rel, entry in file_headers(manifest).items():
        if (not isinstance(rel, str) or not isinstance(entry, dict)
                or type(entry.get("size")) is not int or entry["size"] < 0
                or type(entry.get("mtime")) not in (int, float)
                or not isinstance(entry.get("hash"), str)
                or type(entry.get("lines")) is not int or entry["lines"] < 1
                or not isinstance(entry.get("symbols"), dict)
                or not isinstance(entry.get("imports"), list)
                or any(not isinstance(value, str) for value in entry["imports"])
                or entry.get("language") is not None and not isinstance(entry["language"], str)):
            raise ValueError(f"invalid cached file metadata: {rel}")
        for name, symbol in entry["symbols"].items():
            if (not isinstance(name, str) or not isinstance(symbol, dict)
                    or not isinstance(symbol.get("kind"), str)
                    or not isinstance(symbol.get("hash"), str)
                    or type(symbol.get("start")) is not int or type(symbol.get("end")) is not int
                    or not 1 <= symbol["start"] <= symbol["end"] <= entry["lines"]
                    or "span_precision" in symbol and (
                        not isinstance(symbol["span_precision"], str)
                        or symbol["span_precision"] not in {"exact", "inferred", "merged"})):
                raise ValueError(f"invalid cached symbol metadata: {rel}:{name}")
        if "raw_hash" in entry and (not isinstance(entry["raw_hash"], str)
                                    or not re.fullmatch(r"[0-9a-f]{64}", entry["raw_hash"])):
            raise ValueError(f"invalid cached raw hash: {rel}")
        if "parser_profile" in entry and not isinstance(entry["parser_profile"], dict):
            raise ValueError(f"invalid cached parser profile: {rel}")
        if "parser_notes" in entry and (not isinstance(entry["parser_notes"], list)
                                       or any(not isinstance(note, str) for note in entry["parser_notes"])):
            raise ValueError(f"invalid cached parser notes: {rel}")
        if "status" in entry and (not isinstance(entry["status"], str)
                                 or entry["status"] not in {"parsed", "file-level", "parse-error", "parse-skipped"}):
            raise ValueError(f"invalid cached parser status: {rel}")


def cmd_resolve(args: argparse.Namespace) -> int:
    """Resolve a run's authoritative format/path and small header for shell clients."""
    try:
        run_dir, root, state = _run_context(Path(args.run_dir))
        metadata = _bound_manifest(run_dir, root, state)
        path = resolve_run_snapshot(run_dir, state)
        with open_snapshot(path) as store:
            result = {"path": path.as_posix(), "format": store.format, "storage_version": 1,
                      "metadata": metadata, "file_count": store.file_count}
        print(json.dumps(result, separators=(",", ":")))
        return 0
    except (RunControlError, OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2


def cmd_runtime(args: argparse.Namespace) -> int:
    """What the run's dynamic step observed, for the final report's runtime coverage (`pipeline.runtime`)."""
    import pipeline
    try:
        run_dir, _root, state = _run_context(Path(args.run_dir))
        print(json.dumps(pipeline.runtime(resolve_run_snapshot(run_dir, state)), separators=(",", ":")))
        return 0
    except (RunControlError, OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2


def cmd_write(args: argparse.Namespace) -> int:
    import resolve_edges
    try:
        # A pass over the manifest being replaced holds it open and is stale.
        resolve_edges.reset_pass(Path(args.out))
    except OSError as error:
        print(f"snapshot: cannot stop the engine pass of {args.out}: {error}", file=sys.stderr)
        return 2
    try:
        with ExitStack() as stack:
            previous = stack.enter_context(open_snapshot(Path(args.reuse))) if args.reuse else None
            result = read_project(Path(args.target), Path(args.out),
                                    format=getattr(args, "format", "sqlite"), previous=previous)
        print(f"snapshot: {result['file_count']} files -> {args.out}")
    except (OSError, ValueError) as error:
        print(f"snapshot: cannot write manifest: {error}", file=sys.stderr)
        return 2
    status = 0
    if not getattr(args, "no_index", False):
        import retrieval
        index = retrieval.ensure_index(Path(args.out))
        if index["state"] != "fresh":
            print(f"index: {index['state']}: {index['reason']}", file=sys.stderr)
            status = 1
        else:
            print(f"index: {index['action']} -> {index['index']} ({index['documents']} documents)")
    if not getattr(args, "no_modules", False):
        # The steps to `find_entry_points`: the stack, structure and module stack, then the entry points.
        import pipeline
        piped = pipeline.run(Path(args.out), stop=pipeline.FindEntryPoints.NAME)
        scanned = piped[pipeline.FindModules.NAME]
        if "failed" in scanned:
            print(f"modules: {scanned['failed']}", file=sys.stderr)
            status = 1
        else:
            print(f"modules: {scanned['action']} -> {scanned['graph']} ({scanned['modules']} modules)")
            print(f"premap: {scanned['units']} units, {scanned['gaps']} gaps -> {scanned['premap']}")
    if not getattr(args, "no_engine", False):
        engine = resolve_edges.ensure_edges(Path(args.out))
        if engine["state"] in ("running", "fresh"):
            print(f"engine: {engine['state']} -> {engine['edges_store']}")
        else:
            print(f"engine: {engine['state']}: {engine.get('reason', '')}", file=sys.stderr)
            if engine["state"] == "failed":
                status = 1
    return status


def _index_command(manifest: Path) -> str:
    return f"{Path(__file__).name} index {manifest}"


def cmd_index(args: argparse.Namespace) -> int:
    """Report or repair the lexical index beside a manifest; exit 0 only when it ends fresh."""
    try:
        import retrieval
        result = retrieval.ensure_index(Path(args.manifest), check=args.check, break_lock=args.break_lock)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["state"] == "fresh" else 1


def _search_anchor(value: str) -> dict:
    text = value.strip()
    if text.startswith("{"):
        anchor = json.loads(text)
        if not isinstance(anchor, dict):
            raise ValueError("an anchor must be a JSON object or an entity id")
        return anchor
    return {"entity_id": text}


def cmd_search(args: argparse.Namespace) -> int:
    """Rank the lexical index for a query; a non-fresh index is a gap, never an error."""
    try:
        import retrieval
        manifest = Path(args.manifest)
        if type(args.limit) is not int or not 1 <= args.limit <= 1000:
            raise ValueError("limit must be an integer from 1 through 1000")
        anchors = [_search_anchor(item) for item in args.anchor or []]
        if any(set(anchor) - {"entity_id", "path", "symbol", "line", "start", "end"} for anchor in anchors):
            raise ValueError("anchor keys are entity_id, path, symbol, line, start and end")
        gate = query_gate(manifest)
        if gate is not None:
            print(json.dumps(gate, indent=2, sort_keys=True))
            return 1
        state = retrieval.index_state(manifest)
        if state["state"] != "fresh":
            print(json.dumps(retrieval.gap_result(state, args.limit, _index_command(manifest)), indent=2, sort_keys=True))
            return 0
        dense = None
        if args.embedding_result:
            _reject_links(Path(args.embedding_result))
            dense = json.loads(Path(args.embedding_result).read_text(encoding="utf-8"))
        result = retrieval.search(retrieval.index_name(manifest), args.query, anchors=anchors, limit=args.limit,
                                  embedding_result=dense, verify=args.verify_tree)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2
    print(json.dumps({**retrieval.public_result(result), "index_state": "fresh"}, indent=2, sort_keys=True))
    return 0


def _cards_path(args: argparse.Namespace) -> Path:
    """`--cards`, or the card store of the analysis the snapshot belongs to."""
    from card_store import default_cards_path
    return Path(args.cards) if args.cards else default_cards_path(args.manifest)


def cmd_meta_query(args: argparse.Namespace) -> int:
    try:
        from semantic_store import query_meta_code
        with open_snapshot(Path(args.manifest)) as store:
            result = query_meta_code(
                store,
                cards_path=_cards_path(args),
                paths=args.path or None,
                symbol=args.symbol,
                freshness=args.freshness,
                include_history=not args.no_history,
                limit=args.limit,
            )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2


def cmd_edit_impact(args: argparse.Namespace) -> int:
    try:
        from semantic_store import build_edit_impact
        gate = query_gate(Path(args.manifest))
        if gate is not None:
            print(json.dumps(gate, indent=2, sort_keys=True))
            return 1
        with open_snapshot(Path(args.manifest)) as store:
            result = build_edit_impact(
                store, args.target, cards_path=_cards_path(args), neighbors=args.neighbors,
                history=args.history, include_source=not args.no_source, hops=args.hops,
                include_neighbor_source=args.neighbor_source, include_slices=args.slices,
                budget_chars=args.budget_chars, engine_store=args.engine_store,
            )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2


def cmd_symbols_at(args: argparse.Namespace) -> int:
    try:
        if args.diff is not None and args.request:
            raise ValueError("symbols-at takes either --request or --diff, not both")
        if args.diff is not None and not args.base:
            raise ValueError("symbols-at --diff requires --base")
        if args.diff is None and args.base:
            raise ValueError("symbols-at --base requires --diff")
        gate = query_gate(Path(args.manifest))
        if gate is not None:
            print(json.dumps(gate, indent=2, sort_keys=True))
            return 1
        with ExitStack() as stack:
            candidate = stack.enter_context(open_snapshot(Path(args.manifest)))
            if args.diff is not None:
                text = sys.stdin.read() if args.diff == "-" else Path(args.diff).read_text(encoding="utf-8")
                base = stack.enter_context(open_snapshot(Path(args.base)))
                result = symbols_at(candidate, base=base, diff=text)
            else:
                grouped: dict[str, list[dict]] = {}
                for value in args.request or []:
                    try:
                        path, start, end = value.rsplit(":", 2)
                        item = {"start": int(start), "end": int(end)}
                    except ValueError as error:
                        raise ValueError(f"symbols-at request must be PATH:START:END: {value}") from error
                    grouped.setdefault(path, []).append(item)
                requests = [{"path": path, "ranges": ranges} for path, ranges in grouped.items()]
                result = symbols_at(candidate, requests)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2


def cmd_stale_callers(args: argparse.Namespace) -> int:
    try:
        from semantic_store import build_stale_callers
        with ExitStack() as stack:
            candidate = stack.enter_context(open_snapshot(Path(args.manifest)))
            base = stack.enter_context(open_snapshot(Path(args.base)))
            result = build_stale_callers(base, candidate, limit=args.limit,
                                        base_engine_store=args.base_engine_store,
                                        candidate_engine_store=args.candidate_engine_store)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2


def cmd_meta_upsert(args: argparse.Namespace) -> int:
    try:
        from semantic_store import upsert_meta_cards
        text = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        cards = json.loads(text)
        if isinstance(cards, dict) and "cards" in cards:
            cards = cards["cards"]
        if not isinstance(cards, list):
            raise ValueError("cards payload must be a JSON array or {'cards': [...]}")
        with open_snapshot(Path(args.manifest)) as store:
            result = upsert_meta_cards(store, _cards_path(args), cards)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2


def cmd_context(args: argparse.Namespace) -> int:
    try:
        import context_packet
        def load(path):
            _reject_links(Path(path))
            return json.loads(Path(path).read_text(encoding='utf8'))
        result = context_packet.create_context(Path(args.manifest), load(args.request), load(args.recipient),
            authority=load(args.authority), out=Path(args.out),
            cursor=Path(args.cursor) if args.cursor else None,
            indexes=load(args.indexes) if args.indexes else None)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 1


def cmd_plan(args: argparse.Namespace) -> int:
    """The one plan of a snapshot (`pipeline.plan.current`), as JSON: the same the app and `codebase_map_status` show."""
    from pipeline import plan as planning
    try:
        print(json.dumps(planning.current(Path(args.manifest)), separators=(",", ":")))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2


def _add_tree_commands(sub) -> None:
    """Subcommands over a source tree and its snapshot: scope, files, technologies, plan, write, index, search."""
    scope_parser = sub.add_parser("scope", help="count what a run would analyze and what its perimeter leaves out")
    scope_parser.add_argument("target")
    scope_parser.set_defaults(func=cmd_scope)

    files_parser = sub.add_parser("files", help="list the snapshot inventory: path, sha256, size, lines, language")
    files_parser.add_argument("manifest")
    files_parser.add_argument("--out", required=True)
    files_parser.set_defaults(func=cmd_files)

    technologies_parser = sub.add_parser("technologies", help="copy the stack step's record: frameworks, libraries, tools and services, per build unit")
    technologies_parser.add_argument("manifest")
    technologies_parser.add_argument("--out", required=True)
    technologies_parser.set_defaults(func=cmd_technologies)

    plan_parser = sub.add_parser("plan", help="the one plan of a snapshot: steps, policy, actions and gaps, as JSON")
    plan_parser.add_argument("manifest")
    plan_parser.set_defaults(func=cmd_plan)

    write_parser = sub.add_parser("write", help="write a manifest for a target tree")
    write_parser.add_argument("target")
    write_parser.add_argument("--out", required=True)
    write_parser.add_argument("--format", choices=("sqlite", "json"), default="sqlite")
    write_parser.add_argument("--reuse", help="prior manifest; verify every file before reusing its parse")
    write_parser.add_argument("--no-index", action="store_true",
                              help="skip the lexical index that write builds beside the manifest")
    write_parser.add_argument("--no-modules", action="store_true",
                              help="skip the module graph (modules.json/.md) and the pre-map (premap.json) that write "
                                   "derives beside the manifest")
    write_parser.add_argument("--no-engine", action="store_true",
                              help="skip the call-resolution engine pass that write starts in the background")
    write_parser.set_defaults(func=cmd_write)

    index_parser = sub.add_parser("index", help="build or repair the lexical index beside a manifest")
    index_parser.add_argument("manifest")
    index_parser.add_argument("--check", action="store_true", help="report the index state and write nothing")
    index_parser.add_argument("--break-lock", action="store_true",
                              help="remove a lock and temporaries left by a crashed build before repairing")
    index_parser.set_defaults(func=cmd_index)

    search_parser = sub.add_parser("search", help="rank the lexical index of a manifest for a query")
    search_parser.add_argument("manifest")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--anchor", action="append",
                               help="an entity id or a JSON anchor object; repeatable")
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--embedding-result", help="a daodan/embedding-result/v1 JSON beside the manifest")
    search_parser.add_argument("--verify-tree", action="store_true",
                               help="reread the whole source tree before ranking (slow; the index binding is always checked)")
    search_parser.set_defaults(func=cmd_search)


def _add_run_commands(sub) -> None:
    """Subcommands over analysis runs: resolve, diff, carry, prepare, check, publish, register."""
    resolve_parser = sub.add_parser("resolve", help="resolve the declared snapshot path and small header of a bound run")
    resolve_parser.add_argument("run_dir")
    resolve_parser.set_defaults(func=cmd_resolve)

    runtime_parser = sub.add_parser("runtime", help="what the run's dynamic step observed, per language, and its gaps")
    runtime_parser.add_argument("run_dir")
    runtime_parser.set_defaults(func=cmd_runtime)

    diff_parser = sub.add_parser("diff", help="diff a parent run's snapshot against the worktree")
    diff_parser.add_argument("parent_run")
    diff_parser.add_argument("target")
    diff_parser.add_argument("--out", required=True)
    diff_parser.add_argument("--verify", action="store_true", help="hash every file, ignoring size and mtime")
    diff_parser.add_argument("--threshold", type=float, default=0.4)
    diff_parser.add_argument("--flags", default=None, help="this run's flags as JSON, compared with the parent's")
    diff_parser.set_defaults(func=cmd_diff)

    carry_parser = sub.add_parser("carry", help="copy a parent run's phase files and mark the stale claims")
    carry_parser.add_argument("parent_run")
    carry_parser.add_argument("run_dir")
    carry_parser.set_defaults(func=cmd_carry)

    prepare_parser = sub.add_parser("prepare", help="declare or resume a mode-aware run delivery")
    prepare_parser.add_argument("run_dir")
    prepare_parser.add_argument("--phase", type=int)
    prepare_parser.add_argument("--stop-after", type=int)
    prepare_parser.add_argument("--resume-from", nargs="?", const="auto", type=lambda value: int(value) if value != "auto" else value)
    prepare_parser.add_argument("--run-name")
    prepare_parser.add_argument("--mode", choices=("classic", "team"))
    prepare_parser.add_argument("--flags", help="requested immutable flags as a JSON object")
    prepare_parser.set_defaults(func=cmd_prepare)

    check_parser = sub.add_parser("check", help="verify run delivery before publishing")
    check_parser.add_argument("run_dir")
    check_parser.add_argument("--json", action="store_true", help="emit the mode-aware delivery result")
    check_parser.set_defaults(func=cmd_check)

    publish_parser = sub.add_parser("publish", help="replace the complete phase-file mirror")
    publish_parser.add_argument("run_dir")
    publish_parser.set_defaults(func=cmd_publish)

    for command in ("register", "unregister"):
        registry_parser = sub.add_parser(command, help="update this run's active registry entry")
        registry_parser.add_argument("run_dir")
        registry_parser.set_defaults(func=cmd_registry)


def _add_query_commands(sub) -> None:
    """Subcommands that read a snapshot: Meta-Code, context, edit impact, symbols at lines, stale callers."""
    meta_query_parser = sub.add_parser("meta-query", help="query Meta-Code symbols, their cards with freshness against this snapshot, and bounded changesets")
    meta_query_parser.add_argument("manifest")
    meta_query_parser.add_argument("--path", action="append", default=[])
    meta_query_parser.add_argument("--symbol")
    meta_query_parser.add_argument("--freshness")
    meta_query_parser.add_argument("--no-history", action="store_true")
    meta_query_parser.add_argument("--limit", type=int, default=100)
    meta_query_parser.add_argument("--cards", help="card store; default: cards.sqlite of the analysis root the snapshot belongs to")
    meta_query_parser.set_defaults(func=cmd_meta_query)

    context_parser = sub.add_parser('context', help='publish bounded evidence and resumable residuals; no implicit indexing or inference')
    context_parser.add_argument('manifest')
    for name in ('request', 'recipient', 'authority', 'out'):
        context_parser.add_argument('--' + name, required=True)
    context_parser.add_argument('--cursor')
    context_parser.add_argument('--indexes')
    context_parser.set_defaults(func=cmd_context)

    edit_impact_parser = sub.add_parser("edit-impact", help="what to know before editing symbols: digests, signatures, cards, one-hop callers and callees, blind spots, verified source")
    edit_impact_parser.add_argument("manifest")
    edit_impact_parser.add_argument("--target", action="append", required=True, help="symbol id (path::Name) or file path; repeatable")
    edit_impact_parser.add_argument("--neighbors", type=int, default=20)
    edit_impact_parser.add_argument("--history", type=int, default=5)
    edit_impact_parser.add_argument("--hops", type=int, default=1, help="graph hops: 1 or 2")
    edit_impact_parser.add_argument("--neighbor-source", action="store_true", help="include verified source of listed one-hop neighbours")
    edit_impact_parser.add_argument("--slices", action="store_true", help="compute lazy Python backward slices for targets")
    edit_impact_parser.add_argument("--budget-chars", type=int, default=120000, help="packet budget in JSON characters")
    edit_impact_parser.add_argument("--no-source", action="store_true")
    edit_impact_parser.add_argument("--engine-store", type=Path)
    edit_impact_parser.add_argument("--cards", help="card store; default: cards.sqlite of the analysis root the snapshot belongs to")
    edit_impact_parser.set_defaults(func=cmd_edit_impact)

    symbols_at_parser = sub.add_parser("symbols-at", help="map line ranges or a unified diff to symbols in one or two snapshots")
    symbols_at_parser.add_argument("manifest", help="candidate snapshot")
    symbols_at_parser.add_argument("--request", action="append", default=[], help="PATH:START:END in the candidate snapshot; repeatable")
    symbols_at_parser.add_argument("--base", help="base snapshot, required with --diff")
    symbols_at_parser.add_argument("--diff", help="unified diff file, or - for standard input")
    symbols_at_parser.set_defaults(func=cmd_symbols_at)

    stale_parser = sub.add_parser("stale-callers", help="compare two snapshots and classify callers of changed symbols by edit and validation impact")
    stale_parser.add_argument("manifest", help="candidate snapshot")
    stale_parser.add_argument("--base", required=True, help="base snapshot")
    stale_parser.add_argument("--limit", type=int, default=100)
    stale_parser.add_argument("--base-engine-store", type=Path)
    stale_parser.add_argument("--candidate-engine-store", type=Path)
    stale_parser.set_defaults(func=cmd_stale_callers)


def _add_upkeep_commands(sub) -> None:
    """Subcommands that keep the map current: refresh, hook, Meta-Code card writes."""
    refresh_parser = sub.add_parser("refresh", help="bring the working run to the current source")
    refresh_parser.add_argument("project", nargs="?", default=".")
    refresh_parser.add_argument("--store", help="project-relative custom analysis store")
    refresh_parser.set_defaults(func=cmd_refresh)

    hook_parser = sub.add_parser("hook", help="PostToolUse entry: refresh after an edit in the published perimeter")
    hook_parser.set_defaults(func=cmd_hook)

    meta_upsert_parser = sub.add_parser("meta-upsert", help="write Meta-Code cards, bound to the digests of this snapshot, to the card store")
    meta_upsert_parser.add_argument("manifest")
    meta_upsert_parser.add_argument("--input", required=True, help="cards JSON file, or - for standard input")
    meta_upsert_parser.add_argument("--cards", help="card store; default: cards.sqlite of the analysis root the snapshot belongs to")
    meta_upsert_parser.set_defaults(func=cmd_meta_upsert)


def main(argv: list[str] | None = None) -> int:
    from languages.python import require_minimum_interpreter
    require_minimum_interpreter("snapshot.py")
    parser = argparse.ArgumentParser(description="Codebase Map structural snapshots and change sets.")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_tree_commands(sub)
    _add_run_commands(sub)
    _add_query_commands(sub)
    _add_upkeep_commands(sub)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
