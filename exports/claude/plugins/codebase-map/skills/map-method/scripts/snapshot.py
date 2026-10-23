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
    write <target> --out <manifest.json> [--reuse <previous.json>]
        Write a structural snapshot; reuse parses only after checking file bytes.
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

Standard library only. Parsing reuses the adapters in ./languages/. The Python
grammar is the running interpreter's, so this script declares `requires-python`
for `uv run --script` and refuses an older interpreter in main().
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor
import copy
import fnmatch
import hashlib
from importlib import metadata
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterator

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from languages import SUPPORTED_EXTENSIONS, detect_language, get_adapter  # noqa: E402
from tree_scope import Perimeter, git_executable, work_tree  # noqa: E402
from snapshot_store import (SnapshotStore, artifact_digest, file_headers, header_metadata,
                            open_snapshot, resolve_run_snapshot)  # noqa: E402

__all__ = [
    "DOC_EXTENSIONS",
    "MARKER_PREFIX",
    "PHASE_FILES",
    "PRESENTATION_EXTENSIONS",
    "SCHEMA",
    "blast_radius",
    "build_import_index",
    "build_manifest",
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

SCHEMA = 1

# Hashed but never parsed above this size; recorded with no symbols.
MAX_PARSE_BYTES = 2_000_000
# Not recorded at all above this size: a file this large is not what a claim cites.
MAX_FILE_BYTES = 20_000_000
# A stylesheet with a line longer than this is minified: every rule shares one
# line, so each rule symbol would hash the whole file and any edit would change
# them all. It stays a file-level entry.
MAX_STYLESHEET_LINE = 10_000
# A signature value (an annotation, a default, a decorator) longer than this
# keeps its head and a digest of the whole: a long literal cannot bloat every
# packet that carries the signature, and an edit to it still changes the value.
MAX_SIGNATURE_TEXT = 200
SYMBOLS_AT_SCHEMA = "daodan/symbols-at/v1"
MAX_SYMBOLS_AT_REQUESTS = 100
MAX_SYMBOLS_AT_RANGES = 100
MAX_DIFF_CHARS = 4_000_000
MAX_DIFF_HUNKS = 2_000

# Non-source files a phase file legitimately cites. API contracts (protobuf,
# GraphQL, Prisma, XML schemas and WSDL), build files (Gradle, CMake, make,
# .NET project files) and infrastructure as code (Terraform) are inventoried
# as file-level entries: a claim can cite them and a diff notices their edits,
# with no symbols invented for them. `.properties`, `.config` and `.tfvars` stay
# out on purpose: they routinely hold passwords, and the forbidden list below
# filters by name, never by content.
DOC_EXTENSIONS = frozenset({
    ".bat", ".cfg", ".cmake", ".cmd", ".csproj", ".fsproj", ".gql", ".gradle",
    ".graphql", ".hcl", ".ini", ".json", ".json5", ".jsonc", ".md", ".mk",
    ".plist", ".props", ".proto", ".prisma", ".ps1", ".rst", ".sh", ".sln",
    ".targets", ".tf", ".toml", ".txt", ".vbproj", ".wsdl", ".xml", ".xsd",
    ".xsl", ".xslt", ".yaml", ".yml",
})

# Presentation files no adapter parses: markup, single-file components and
# indented Sass. They carry no symbols, but they decide whether a screen
# renders, scrolls and can be completed, so they enter the manifest as
# file-level entries: a phase file can cite them and an incremental run notices
# when one changes. The set exists because a run once held not one `.css` path
# while a global dark-theme rule was overriding a consent modal's positioning
# and locking users out. CSS, SCSS and LESS left it for their own adapter,
# which records every rule as a symbol.
PRESENTATION_EXTENSIONS = frozenset({
    ".astro", ".cshtml", ".ejs", ".ftl", ".hbs", ".htm", ".html", ".jsp",
    ".jspx", ".liquid", ".mustache", ".pug", ".razor", ".sass", ".svelte",
    ".twig", ".vm", ".vue", ".xhtml",
})

# The Codebase Map's forbidden list. These never enter the manifest, not even as a hash.
FORBIDDEN_GLOBS = (
    ".env", ".env.*", "credentials.*", "secrets.*", "*secret*", "*credential*",
    "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_ed25519*",
    ".npmrc", ".pypirc", ".netrc",
    "*service-account*.json", "*kubeconfig*", "*.tfstate", "*.tfstate.*", "*.keystore", "*.jks",
)


def is_forbidden(name: str) -> bool:
    """True for a file the Codebase Map must never read. Case-insensitive."""
    lowered = name.lower()
    return any(fnmatch.fnmatchcase(lowered, glob) for glob in FORBIDDEN_GLOBS)


def iter_files(target: Path, perimeter: Perimeter | None = None) -> Iterator[Path]:
    """
    Every file in the target the snapshot records, in a stable order.

    Which directories are descended into is the perimeter's rule, in
    tree_scope.py, and not this function's: nothing Git ignores, no directory
    whose name starts with a dot, no dependency or build output. Pass a
    perimeter to read back afterwards what the walk left out.
    """
    perimeter = perimeter or Perimeter(target)
    for directory, filenames in perimeter.walk():
        for name in filenames:
            if is_forbidden(name):
                continue
            path = directory / name
            if target.is_file() and path != target:
                continue
            suffix = path.suffix.lower()
            if (
                suffix not in SUPPORTED_EXTENSIONS
                and suffix not in DOC_EXTENSIONS
                and suffix not in PRESENTATION_EXTENSIONS
            ):
                continue
            yield path


def read_text(path: Path) -> str:
    """File content with newlines normalized, so a line-ending change is not an edit."""
    data = path.read_bytes()
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def hash_text(text: str) -> str:
    """Short content hash. 16 hex characters: readable in a manifest, ample here."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def repo_root(target: Path) -> Path:
    """
    The base every manifest path is relative to: the top level of the work
    tree that holds the target, otherwise the target itself. A work tree that
    ignores the target does not hold it.
    """
    base = target.parent if target.is_file() else target
    return work_tree(base) or base


def parser_fingerprint() -> str:
    """Identity of the structural helpers and installed parser versions.

    Compute once per snapshot or read batch. Start a fresh process after updating
    helper code; this fingerprint does not reload already imported Python modules.
    Grammar availability is checked separately by parser_profile.
    """
    digest = hashlib.sha256()
    helpers = [SCRIPT_DIR / name for name in
               ("snapshot.py", "ast_parser.py", "tree_scope.py", "source_reader.py",
                "semantic_index.py", "dependency_graph.py", "snapshot_store.py", "json_snapshot.py",
                "semantic_store.py", "resolution.py", "store_graph.py", "store_graph_metrics.py",
                "store_consumers.py")]
    helpers += sorted((SCRIPT_DIR / "languages").rglob("*.py"))
    for helper in helpers:
        if helper.is_file():
            digest.update(helper.relative_to(SCRIPT_DIR).as_posix().encode("utf-8") + b"\0")
            digest.update(helper.read_bytes())
            digest.update(b"\0")
    packages = ("tree-sitter", "tree-sitter-language-pack", "tree-sitter-java",
                "tree-sitter-javascript", "tree-sitter-typescript", "tree-sitter-rust",
                "tree-sitter-go")
    versions = {}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = None
    # Only the stdlib `ast` grammar varies with Python, and only by minor
    # version. A patch release or a separate runtime environment of the same
    # minor (the MCP server's) parses identically.
    digest.update(json.dumps({"python": list(sys.version_info[:2]), "packages": versions},
                             sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def parser_profile(path: Path, language: str | None = None) -> dict:
    """Effective backend for this file, without reading its source bytes."""
    language = language or SUPPORTED_EXTENSIONS.get(path.suffix.lower())
    if language in {"java", "javascript", "typescript", "rust", "go"}:
        from languages._treesitter import get_parser
        grammar = "tsx" if path.suffix.lower() == ".tsx" else language
        loaded = get_parser(grammar)
        profile = {"language": language, "backend": "tree-sitter" if loaded else "regex-fallback",
                   "grammar": grammar}
        if loaded:
            lang = loaded[1]
            for attribute in ("abi_version", "semantic_version"):
                value = getattr(lang, attribute, None)
                if value is not None:
                    profile[attribute] = list(value) if isinstance(value, tuple) else value
        return profile
    return {"language": language, "backend": {
        "python": "stdlib-ast", "css": "stylesheet", "sql": "regex", "plsql": "regex",
    }.get(language, "file-level")}


def git_info(root: Path) -> dict | None:
    """
    Commit, branch and dirtiness, as metadata, of the work tree that holds the
    root: none for a root no work tree holds. Nothing in the diff depends on it.
    """
    git = git_executable()
    if git is None or work_tree(root) is None:
        return None

    def run(*args: str) -> str | None:
        try:
            proc = subprocess.run(
                [git, "-C", str(root), *args], capture_output=True, text=True, timeout=10
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return proc.stdout.strip() if proc.returncode == 0 else None

    commit = run("rev-parse", "HEAD")
    if not commit:
        return None
    return {
        "commit": commit[:12],
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(run("status", "--porcelain")),
    }


def _signature_text(value: object) -> str:
    text = " ".join(str(value).split())
    if len(text) <= MAX_SIGNATURE_TEXT:
        return text
    return text[:160] + "..." + hash_text(text)


def signature_record(info) -> dict | None:
    """The declared signature of a function or class, in one comparable shape.

    A key appears only with a value. `fields` lists the signature fields the
    adapter extracts exhaustively (languages.base.SIGNATURE_FIELDS): a listed
    field whose key is absent is absent from the source, while an unlisted one
    may only be missing from the extraction. No position enters the record, so
    a symbol that only moves keeps its signature.
    """
    record: dict = {}

    def keep(key: str, value) -> None:
        if value:
            record[key] = value

    def described(items) -> list[dict]:
        out = []
        for item in items:
            entry = {"name": _signature_text(item.name)}
            for key in ("kind", "annotation", "default"):
                value = getattr(item, key, None)
                if value is not None:
                    entry[key] = _signature_text(value)
            out.append(entry)
        return out

    if hasattr(info, "parameters"):
        keep("params", described(info.parameters))
        if info.return_annotation is not None:
            keep("returns", _signature_text(info.return_annotation))
        keep("async", bool(info.is_async))
        keep("generator", bool(getattr(info, "is_generator", False)))
        keep("static", bool(getattr(info, "is_staticmethod", False)))
    else:
        keep("bases", [_signature_text(base) for base in info.bases])
        attributes = getattr(info, "attributes", None)
        keep("attributes", described(attributes) if attributes
             else [{"name": _signature_text(name)} for name in info.class_variables])
    keep("decorators", [_signature_text(text) for text in getattr(info, "decorators", None) or ()])
    keep("visibility", getattr(info, "visibility", None))
    keep("fields", sorted(getattr(info, "signature_fields", ()) or ()))
    return record or None


def symbol_spans(result, lines: list[str]) -> dict[str, dict]:
    """
    Every symbol in a parse result, qualified, with its line span and body hash.

    Top-level symbols (classes and free functions) are spanned first: an exact
    end line where the adapter has one, otherwise the line before the next
    top-level symbol. Methods are spanned inside their class, so a class span
    always encloses its methods and editing a method moves both hashes.
    Definitions the adapter reports in `nested` (a nested function or class, a
    definition inside a compound statement, a PEP 695 alias) are spanned last,
    inside the symbol that encloses them, under the name the adapter qualified.

    A symbol the adapter describes also carries `signatures`, one
    signature_record per declaration in source order: several when overloads
    or redefinitions share the name.
    """
    total = len(lines)
    top: list[dict] = []
    for cls in result.classes:
        if cls.line_number > 0:
            top.append({
                "name": cls.name, "kind": cls.kind, "start": cls.line_number,
                "end": getattr(cls, "end_line", None), "methods": list(cls.methods), "info": cls,
            })
    for func in result.functions:
        if func.line_number > 0:
            top.append({
                "name": func.name, "kind": "function", "start": func.line_number,
                "end": getattr(func, "end_line", None), "methods": [], "info": func,
            })
    top.sort(key=lambda item: (item["start"], item["name"]))

    for index, item in enumerate(top):
        item["precision"] = "exact" if item["end"] else "inferred"
        if not item["end"]:
            following = top[index + 1]["start"] - 1 if index + 1 < len(top) else total
            item["end"] = following
        item["end"] = max(item["end"], item["start"])

    spans: dict[str, dict] = {}

    hashes: dict[tuple[int, int], str] = {}

    def span_hash(start: int, end: int) -> str:
        # Many symbols can share one span (a minified line, a class and its one
        # method); each distinct span is hashed once.
        key = (start, end)
        if key not in hashes:
            hashes[key] = hash_text("\n".join(lines[start - 1:end]))
        return hashes[key]

    def record(name: str, kind: str, start: int, end: int, precision: str, info) -> None:
        if not (1 <= start <= end <= total):
            precision = "inferred"
        start = max(1, min(start, total))
        end = max(start, min(end, total))
        # A class carrying two methods of the same name (an overload) would
        # otherwise have the second `record()` call overwrite the first,
        # losing the earlier span entirely: an edit inside the lost overload
        # then changes no hash, and compare_symbols never reports it. Widen
        # the span to cover every occurrence instead, so any edit to any of
        # them moves the hash. That over-marks rather than under-marks: it
        # costs one extra re-derivation instead of a missed claim.
        existing = spans.get(name)
        signatures = list(existing.get("signatures", ())) if existing is not None else []
        if existing is not None:
            start = min(start, existing["start"])
            end = max(end, existing["end"])
            precision = "merged"
        signature = signature_record(info)
        if signature is not None:
            signatures.append(signature)
        spans[name] = {
            "kind": kind,
            "start": start,
            "end": end,
            "hash": span_hash(start, end),
            "span_precision": precision,
        }
        if signatures:
            spans[name]["signatures"] = signatures

    for item in top:
        record(item["name"], item["kind"], item["start"], item["end"], item["precision"], item["info"])
        methods = sorted(
            (m for m in item["methods"] if m.line_number > 0),
            key=lambda m: m.line_number,
        )
        for index, method in enumerate(methods):
            end = getattr(method, "end_line", None)
            precision = "exact" if end else "inferred"
            if not end:
                end = methods[index + 1].line_number - 1 if index + 1 < len(methods) else item["end"]
            record(f"{item['name']}.{method.name}", "method", method.line_number, end, precision, method)

    # Definitions the adapter reports outside the two top-level lists: nested
    # functions and classes, definitions inside a compound statement, and PEP 695
    # type aliases. Their name is already qualified by the adapter, and their end
    # line is exact, so nothing is inferred here. Recorded after the top-level
    # symbols: a name both lists carry is a redefinition, and `record` widens the
    # span to cover every occurrence rather than losing one.
    nested = sorted(
        (item for item in getattr(result, "nested", ()) or () if item.info.line_number > 0),
        key=lambda item: (item.info.line_number, item.qualified_name),
    )
    for item in nested:
        info = item.info
        end = getattr(info, "end_line", None)
        record(item.qualified_name, item.kind, info.line_number, end or total,
               "exact" if end else "inferred", info)
    return spans


def file_entry(path: Path, data: bytes | None = None, mtime: float | None = None,
               *, parse_result=None) -> dict:
    """One manifest row, parsed from the same bytes whose identity it records."""
    if mtime is None or data is None:
        stat = path.stat()
        mtime = round(stat.st_mtime, 3) if mtime is None else mtime
    data = path.read_bytes() if data is None else data
    text = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    language = detect_language(path, text)
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
    if language and len(data) > MAX_PARSE_BYTES:
        entry["status"] = "parse-skipped"
        entry["parser_notes"] = ["source exceeds parsing size limit"]
    elif language:
        try:
            data.decode("utf-8")  # Lossy decoding cannot supply precise source spans.
            result = parse_result if parse_result is not None else get_adapter(language).parse(text, str(path))
        except Exception as exc:  # a parser failure degrades to a file-level entry
            entry["status"] = "parse-error"
            entry["parser_notes"] = [f"{type(exc).__name__}: {exc}"]
            return entry
        entry["language"] = result.language
        entry["parser_notes"] = list(result.notes)
        if any(note.startswith("syntax error:") for note in result.notes):
            entry["status"] = "parse-error"
        else:
            entry["status"] = "parsed"
        # A loaded grammar can fail on this particular source and fall back.
        # Retain the availability profile for freshness checks, but do not cache
        # this result as a successful native parse. The reader returns it in full.
        if profile["backend"] == "tree-sitter" and not any(
            note.startswith("parser=tree-sitter") for note in result.notes
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
        # Semantic facts belong to these exact bytes and the same parser
        # identity. A damaged parse cannot certify complete reference coverage.
        semantic = getattr(result, "semantic", None)
        if entry["status"] == "parsed" and isinstance(semantic, dict):
            entry["semantic"] = copy.deepcopy(semantic)
        if result.language == "css" and max((len(text) for text in lines), default=0) > MAX_STYLESHEET_LINE:
            entry["status"] = "file-level"
            entry["parser_notes"].append("minified stylesheet; precise rule selection disabled")
            return entry
        entry["symbols"] = symbol_spans(result, lines)
    return entry


def relative_to_root(path: Path, root: Path) -> str:
    """POSIX path relative to the manifest root, or absolute when outside it."""
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def scope_record(perimeter: Perimeter, root: Path) -> dict:
    """
    What a perimeter left out, in the one shape the manifest and the scope
    command share. `git_ignore` is `unavailable` when no work tree holds the
    target or git did not answer: no ignore rule was applied then, and a reader
    must be able to tell.
    """
    return {
        "git_ignore": perimeter.git_ignore,
        "skipped": {
            "dot_directories": [relative_to_root(path, root) for path in perimeter.dot_directories],
            "git_ignored": perimeter.git_ignored,
        },
    }


def build_manifest(target: Path, previous: dict | None = None, *, parse_results: dict | None = None,
                   source_observations: dict | None = None) -> dict:
    """Snapshot the current perimeter; reuse structure only for verified bytes.

    A reuse candidate saves parsing, not inventory traversal or hashing. Legacy
    manifests and a different helper identity/root/target cause a fresh parse.
    An optional output dictionary receives the already-read bytes by relative
    path, for consumers that verify semantic evidence without reading again.
    """
    if previous is not None:
        validate_reuse_manifest(previous)
    if source_observations is not None:
        source_observations.clear()
    target = target.resolve()
    if not (target.is_dir() or target.is_file()):
        raise ValueError(f"snapshot target does not exist: {target}")
    root = repo_root(target).resolve()
    files: dict[str, dict] = {}
    fingerprint = parser_fingerprint()
    target_key = relative_to_root(target, root) or "."
    reusable = (
        isinstance(previous, dict) and previous.get("schema") == SCHEMA
        and previous.get("root") == root.as_posix() and previous.get("target") == target_key
        and previous.get("parser_fingerprint") == fingerprint
    )
    old_files = previous.get("files", {}) if reusable else {}
    metrics = {"files_read": 0, "source_bytes_read": 0, "parsed_files": 0, "cache_hits": 0}
    perimeter = Perimeter(target)
    supplied = {Path(path).resolve(): value for path, value in (parse_results or {}).items()}
    pending: list[tuple[str, Path, bytes, float, object]] = []
    ordered_rels: list[str] = []
    reused_entries: dict[str, dict] = {}
    for path in iter_files(target, perimeter):
        try:
            st = path.stat()
            observed = supplied.get(path.resolve())
            if observed is None and st.st_size > MAX_FILE_BYTES:
                continue
            if observed is not None:
                content, parsed = observed
                data = content.encode("utf-8")
            else:
                data = path.read_bytes()
                parsed = None
                metrics["files_read"] += 1
                metrics["source_bytes_read"] += len(data)
            if len(data) > MAX_FILE_BYTES:
                continue
            rel = relative_to_root(path, root)
            if source_observations is not None:
                source_observations[rel] = data
            mtime = round(st.st_mtime, 3)
            old = old_files.get(rel)
            raw_hash = hashlib.sha256(data).hexdigest()
            if (isinstance(old, dict) and old.get("raw_hash") == raw_hash
                    and old.get("parser_profile") == parser_profile(path, old.get("language"))
                    and old.get("status") in {"parsed", "file-level", "parse-skipped"}):
                entry = copy.deepcopy(old)
                entry["size"] = len(data)
                entry["mtime"] = mtime
                metrics["cache_hits"] += 1
                reused_entries[rel] = entry
            else:
                pending.append((rel, path, data, mtime, parsed))
            ordered_rels.append(rel)
        except OSError:
            continue

    parsed_entries: dict[str, dict] = {}
    if len(pending) >= 8:
        workers = min(8, (os.cpu_count() or 2))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                (rel, parsed is None, pool.submit(file_entry, path, data, mtime, parse_result=parsed))
                for rel, path, data, mtime, parsed in pending
            ]
            for rel, needs_parse, fut in futures:
                try:
                    entry = fut.result()
                except OSError:
                    continue
                if entry["status"] in {"parsed", "parse-error"} and needs_parse:
                    metrics["parsed_files"] += 1
                parsed_entries[rel] = entry
    else:
        for rel, path, data, mtime, parsed in pending:
            try:
                entry = file_entry(path, data, mtime, parse_result=parsed)
            except OSError:
                continue
            if entry["status"] in {"parsed", "parse-error"} and parsed is None:
                metrics["parsed_files"] += 1
            parsed_entries[rel] = entry

    for rel in ordered_rels:
        if rel in reused_entries:
            files[rel] = reused_entries[rel]
        elif rel in parsed_entries:
            files[rel] = parsed_entries[rel]
    from datetime import datetime, timezone
    return {
        "schema": SCHEMA,
        "target": target_key,
        "root": root.as_posix(),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git": git_info(root),
        "scope": scope_record(perimeter, root),
        "parser_fingerprint": fingerprint,
        "metrics": metrics,
        "files": files,
    }


def write_snapshot(target: Path, out: Path, *, format: str = "sqlite", previous=None,
                   parse_results: dict | None = None, extra_metadata: dict | None = None,
                   progress=None) -> dict:
    """Write bounded records; optional progress observes work and may cancel it.

    Host metadata joins the immutable header before semantic binding. Reserved
    snapshot fields cannot be overridden by an embedding application's header.
    """
    from datetime import datetime, timezone
    from snapshot_store import SnapshotWriter, validate_format, _plain

    validate_format(format)
    reserved = {"schema", "target", "root", "created_at", "git", "scope", "parser_fingerprint",
                "metrics", "files", "file_count", "format"}
    if extra_metadata is not None and (not isinstance(extra_metadata, dict)
            or any(not isinstance(key, str) or key in reserved for key in extra_metadata)):
        raise ValueError("invalid additional snapshot metadata")
    extra_metadata = dict(extra_metadata or {})
    target = Path(target).resolve()
    out = Path(out)
    _plain(out)
    if not (target.is_dir() or target.is_file()):
        raise ValueError(f"snapshot target does not exist: {target}")
    root = repo_root(target).resolve()
    target_key = relative_to_root(target, root) or "."
    fingerprint = parser_fingerprint()
    reusable = (previous is not None and previous.metadata.get("schema") == SCHEMA
                and previous.metadata.get("root") == root.as_posix()
                and previous.metadata.get("target") == target_key
                and previous.metadata.get("parser_fingerprint") == fingerprint)
    metrics = {"files_read": 0, "source_bytes_read": 0, "parsed_files": 0, "cache_hits": 0}
    perimeter = Perimeter(target)
    out.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{out.name}.", dir=out.parent)
    os.close(descriptor)
    temporary = Path(name)
    temporary.unlink()
    count = 0
    supplied = {Path(path).resolve(): value for path, value in (parse_results or {}).items()}
    sqlite_fast_reuse = (
        reusable
        and format == "sqlite"
        and getattr(previous, "format", None) == "sqlite"
        and hasattr(previous, "verified_reusable_headers")
        and previous._has_json_cache()
    )
    verified_headers = previous.verified_reusable_headers() if sqlite_fast_reuse else {}
    exact_reused_paths: list[str] = []
    touched_reused_headers: dict[str, dict] = {}
    try:
        with SnapshotWriter(temporary, format) as writer:
            if format == "sqlite":
                writer.connection.execute("CREATE TABLE observed_coverage(file TEXT PRIMARY KEY,payload BLOB)")
            for path in iter_files(target, perimeter):
                try:
                    st = path.stat()
                    observed = supplied.get(path.resolve())
                    if observed is None and st.st_size > MAX_FILE_BYTES:
                        continue
                    if observed is None:
                        data, parsed = path.read_bytes(), None
                        metrics["files_read"] += 1
                        metrics["source_bytes_read"] += len(data)
                    else:
                        content, parsed = observed
                        data = content.encode("utf-8")
                except OSError:
                    continue
                if len(data) > MAX_FILE_BYTES:
                    continue
                if progress is not None:
                    progress("reading", count + 1)
                rel = relative_to_root(path, root)
                mtime = round(st.st_mtime, 3)
                raw_digest = hashlib.sha256(data).hexdigest()
                if sqlite_fast_reuse and rel in verified_headers:
                    old_h = verified_headers[rel]
                    if (old_h.get("raw_hash") == raw_digest
                            and old_h.get("parser_profile") == parser_profile(path, old_h.get("language"))
                            and old_h.get("status") in {"parsed", "file-level", "parse-skipped"}):
                        metrics["cache_hits"] += 1
                        if old_h.get("size") == len(data) and old_h.get("mtime") == mtime:
                            exact_reused_paths.append(rel)
                        else:
                            updated_h = dict(old_h)
                            updated_h["size"], updated_h["mtime"] = len(data), mtime
                            touched_reused_headers[rel] = updated_h
                        del data
                        count += 1
                        if progress is not None:
                            progress("parsing", count)
                        continue
                old = previous.get_file(rel) if reusable else None
                if (old is not None and old.get("raw_hash") == raw_digest
                        and old.get("parser_profile") == parser_profile(path, old.get("language"))
                        and old.get("status") in {"parsed", "file-level", "parse-skipped"}):
                    old["size"], old["mtime"] = len(data), mtime
                    entry = old
                    metrics["cache_hits"] += 1
                else:
                    del old
                    entry = file_entry(path, data, mtime, parse_result=parsed)
                    if entry["status"] in {"parsed", "parse-error"} and parsed is None:
                        metrics["parsed_files"] += 1
                writer.put_file(rel, entry)
                if format == "sqlite":
                    from semantic_store import observed_coverage
                    from snapshot_store import _pack
                    writer.connection.execute("INSERT INTO observed_coverage VALUES(?,?)",
                                              (rel, _pack(observed_coverage(entry, data))))
                del entry, data
                count += 1
                if progress is not None:
                    progress("parsing", count)
            if exact_reused_paths or touched_reused_headers:
                writer.bulk_copy_from_sqlite(previous, exact_reused_paths, touched_reused_headers)
            if progress is not None:
                progress("validating", count)
            metadata_record = {
                **extra_metadata,
                "schema": SCHEMA, "target": target_key, "root": root.as_posix(),
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "git": git_info(root), "scope": scope_record(perimeter, root),
                "parser_fingerprint": fingerprint, "metrics": metrics,
            }
            if format == "sqlite":
                from semantic_store import build_semantic_store
                reused_set = set(exact_reused_paths) | set(touched_reused_headers)
                with writer.reader() as current:
                    current.metadata.update(metadata_record)
                    build_semantic_store(
                        current,
                        writer=writer,
                        previous=previous if sqlite_fast_reuse else None,
                        reused_files=reused_set if sqlite_fast_reuse else None,
                        perimeter=perimeter,
                    )
            writer.finish(metadata_record)
        _plain(out)
        # A caller reusing the same pathname transfers its reader to publication.
        # Windows cannot replace the file while that connection is open.
        if previous is not None and previous.path.resolve() == out.resolve():
            previous.close()
        os.replace(temporary, out)
        return {**metadata_record, "file_count": count, "format": format}
    finally:
        temporary.unlink(missing_ok=True)
        Path(str(temporary) + "-journal").unlink(missing_ok=True)


def compare_files(manifest: dict, target: Path, verify: bool = False,
                  raw_hashes: dict | None = None) -> dict:
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


def compare_symbols(manifest: dict, comparison: dict) -> dict:
    """
    Classify symbols inside added and modified files, and record how the lines
    of every surviving symbol moved.

    `fresh` carries the re-parsed structure of those files so the caller does
    not parse them a second time.
    """
    old_files = file_headers(manifest)
    added, removed, changed = [], [], []
    renumber: dict[str, list[dict]] = {}
    fresh: dict[str, dict] = {}

    for rel in comparison["added"] + comparison["modified"]:
        path = comparison["current"][rel]
        try:
            entry = file_entry(path)
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


def _snapshot_metadata(manifest) -> dict:
    return manifest.metadata if isinstance(manifest, SnapshotStore) else manifest


def _snapshot_info(manifest) -> dict:
    metadata = _snapshot_metadata(manifest)
    git = metadata.get("git") if isinstance(metadata.get("git"), dict) else {}
    return {
        "root": metadata.get("root"),
        "target": metadata.get("target"),
        "created_at": metadata.get("created_at"),
        "repo_revision": git.get("commit"),
        "parser_fingerprint": metadata.get("parser_fingerprint"),
    }


def _snapshot_entry(manifest, path: str) -> dict | None:
    if isinstance(manifest, SnapshotStore):
        return manifest.get_file(path, semantic=False)
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict):
        raise ValueError("snapshot has no file inventory")
    entry = files.get(path)
    if entry is not None and not isinstance(entry, dict):
        raise ValueError(f"invalid snapshot file entry: {path}")
    return entry


def _entity_record(manifest, path: str, entry: dict, name: str, spec: dict) -> dict:
    metadata = _snapshot_metadata(manifest)
    git = metadata.get("git") if isinstance(metadata.get("git"), dict) else {}
    parts = name.split(".")
    signatures = spec.get("signatures") or []
    return {
        "entity_id": f"{path}::{name}",
        "entity_key": {
            "repo": metadata.get("root"),
            "language": entry.get("language"),
            "chain": [path, *parts[:-1]],
            "kind": spec.get("kind"),
            "name": parts[-1],
            "overload": "merged" if spec.get("span_precision") == "merged" or len(signatures) > 1 else None,
        },
        "anchor": {
            "repo_revision": git.get("commit"),
            "file": path,
            "start_line": spec.get("start"),
            "end_line": spec.get("end"),
            "start_byte": None,
            "end_byte": None,
            "byte_precision": "unavailable",
            "ast_anchor": {
                "kind": spec.get("kind"),
                "start": spec.get("start"),
                "end": spec.get("end"),
                "span_precision": spec.get("span_precision"),
            },
        },
        "body_hash": spec.get("hash"),
        "signatures": signatures,
    }


def _map_ranges(manifest, path: str, ranges: list[dict]) -> dict:
    entry = _snapshot_entry(manifest, path)
    if entry is None:
        return {"path": path, "ranges": [], "gaps": [{"range": item, "reason": "not-inventoried"} for item in ranges]}
    total = entry.get("lines")
    if type(total) is not int or total < 1:
        raise ValueError(f"invalid line count in snapshot entry: {path}")
    symbols = entry.get("symbols") or {}
    if not isinstance(symbols, dict):
        raise ValueError(f"invalid symbols in snapshot entry: {path}")
    mapped_ranges = []
    gaps = []
    status = entry.get("status")
    for item in ranges:
        start, end = item["start"], item["end"]
        if type(start) is not int or type(end) is not int or not 1 <= start <= end <= total:
            raise ValueError(f"range {start}:{end} is outside {path} (1:{total})")
        if status != "parsed":
            gaps.append({"range": item, "reason": "no-ast", "status": status,
                         "parser_notes": list(entry.get("parser_notes") or [])})
            mapped_ranges.append({"start": start, "end": end, "symbols": []})
            continue
        found = []
        for name, spec in symbols.items():
            if not isinstance(spec, dict):
                raise ValueError(f"invalid symbol metadata: {path}:{name}")
            if spec["start"] <= end and start <= spec["end"]:
                found.append((spec["end"] - spec["start"], spec["start"], name,
                              _entity_record(manifest, path, entry, name, spec)))
        found.sort(key=lambda value: (value[0], value[1], value[2]))
        records = [value[3] for value in found]
        if not records:
            gaps.append({"range": item, "reason": "outside-symbols" if symbols else "no-symbols"})
        mapped_ranges.append({"start": start, "end": end, "symbols": records})
    return {"path": path, "language": entry.get("language"), "status": status,
            "ranges": mapped_ranges, "gaps": gaps}


def _validate_symbols_at_requests(requests) -> list[dict]:
    if not isinstance(requests, list) or not 1 <= len(requests) <= MAX_SYMBOLS_AT_REQUESTS:
        raise ValueError(f"requests must be a list of 1 to {MAX_SYMBOLS_AT_REQUESTS} items")
    validated = []
    range_count = 0
    for request in requests:
        if not isinstance(request, dict) or set(request) != {"path", "ranges"}:
            raise ValueError("each symbols-at request must contain only path and ranges")
        path, ranges = request["path"], request["ranges"]
        if not isinstance(path, str) or not path or "\\" in path or path.startswith("/"):
            raise ValueError("symbols-at path must be a snapshot-relative POSIX path")
        if not isinstance(ranges, list) or not ranges:
            raise ValueError("symbols-at ranges must be a nonempty list")
        clean_ranges = []
        for item in ranges:
            if not isinstance(item, dict) or set(item) != {"start", "end"}:
                raise ValueError("each symbols-at range must contain only start and end")
            clean_ranges.append({"start": item["start"], "end": item["end"]})
            range_count += 1
        validated.append({"path": path, "ranges": clean_ranges})
    if range_count > MAX_SYMBOLS_AT_RANGES:
        raise ValueError(f"symbols-at accepts at most {MAX_SYMBOLS_AT_RANGES} ranges")
    return validated


_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _diff_path(value: str) -> str | None:
    value = value.strip()
    if value == "/dev/null":
        return None
    if value.startswith('"') and value.endswith('"'):
        try:
            value = json.loads(value)
        except ValueError:
            pass
    for prefix in ("a/", "b/"):
        if value.startswith(prefix):
            return value[2:]
    return value


def _coalesce_lines(lines: list[int]) -> list[dict]:
    ranges = []
    for line in lines:
        if ranges and line == ranges[-1]["end"] + 1:
            ranges[-1]["end"] = line
        else:
            ranges.append({"start": line, "end": line})
    return ranges


def parse_unified_diff(text: str) -> list[dict]:
    """File sections and hunks of a unified diff, with changed line numbers.

    Only headers and hunk line positions are retained. Removed lines belong to
    the old side and added lines to the new side; context lines belong to both
    and are not changes.
    """
    if not isinstance(text, str) or len(text) > MAX_DIFF_CHARS:
        raise ValueError(f"diff must be text of at most {MAX_DIFF_CHARS} characters")
    sections = []
    section = None
    hunk = None
    old_line = new_line = old_left = new_left = 0

    def close_hunk():
        nonlocal hunk
        if section is not None and hunk is not None:
            hunk["removed_ranges"] = _coalesce_lines(hunk.pop("removed_lines"))
            hunk["added_ranges"] = _coalesce_lines(hunk.pop("added_lines"))
            section["hunks"].append(hunk)
        hunk = None

    def close_section():
        nonlocal section
        close_hunk()
        if section is not None:
            sections.append(section)
        section = None

    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            close_section()
            section = {"old_path": None, "new_path": None, "hunks": []}
            continue
        if section is None:
            if raw.startswith("--- "):
                section = {"old_path": _diff_path(raw[4:]), "new_path": None, "hunks": []}
            continue
        header_open = hunk is None or (old_left <= 0 and new_left <= 0)
        if header_open and raw.startswith("rename from "):
            section["old_path"] = _diff_path(raw[len("rename from "):])
            continue
        if header_open and raw.startswith("rename to "):
            section["new_path"] = _diff_path(raw[len("rename to "):])
            continue
        if header_open and raw.startswith("copy from "):
            section["old_path"] = _diff_path(raw[len("copy from "):])
            continue
        if header_open and raw.startswith("copy to "):
            section["new_path"] = _diff_path(raw[len("copy to "):])
            continue
        if header_open and raw.startswith("--- "):
            if section["hunks"] or section["new_path"] is not None:
                close_section()
                section = {"old_path": None, "new_path": None, "hunks": []}
            section["old_path"] = _diff_path(raw[4:])
            continue
        if header_open and raw.startswith("+++ "):
            section["new_path"] = _diff_path(raw[4:])
            continue
        match = _HUNK_HEADER.match(raw) if header_open else None
        if match:
            close_hunk()
            if sum(len(item["hunks"]) for item in sections) + sum(len(item["hunks"]) for item in ([section] if section else [])) >= MAX_DIFF_HUNKS:
                raise ValueError(f"diff has more than {MAX_DIFF_HUNKS} hunks")
            old_line = int(match.group(1))
            old_left = int(match.group(2) or "1")
            new_line = int(match.group(3))
            new_left = int(match.group(4) or "1")
            hunk = {"old_start": old_line, "old_count": old_left,
                    "new_start": new_line, "new_count": new_left,
                    "removed_lines": [], "added_lines": []}
            continue
        if hunk is None or (old_left <= 0 and new_left <= 0):
            continue
        prefix = raw[:1] or " "
        if prefix == "\\":
            continue
        if prefix == "-":
            hunk["removed_lines"].append(old_line)
            old_line += 1
            old_left -= 1
        elif prefix == "+":
            hunk["added_lines"].append(new_line)
            new_line += 1
            new_left -= 1
        else:
            old_line += 1
            new_line += 1
            old_left -= 1
            new_left -= 1
    close_section()
    return sections


def symbols_at(candidate, requests=None, *, base=None, diff: str | None = None) -> dict:
    """Map line ranges, or a unified diff, to symbols in one or two snapshots.

    In diff mode removed lines are read in the base snapshot and added lines in
    the candidate snapshot. A file or range the snapshots cannot place is a
    declared gap in the result, never an invented symbol.
    """
    if diff is None:
        validated = _validate_symbols_at_requests(requests)
        results = [_map_ranges(candidate, item["path"], item["ranges"]) for item in validated]
        return {
            "schema": SYMBOLS_AT_SCHEMA,
            "mode": "ranges",
            "candidate": _snapshot_info(candidate),
            "results": results,
            "summary": {
                "requests": len(results),
                "symbols": sum(len(item["symbols"]) for result in results for item in result["ranges"]),
                "gaps": sum(len(result["gaps"]) for result in results),
            },
        }
    if requests is not None:
        raise ValueError("symbols-at takes either ranges or a diff, not both")
    if base is None:
        raise ValueError("diff mode requires a base snapshot")
    hunks = []
    symbol_count = gap_count = 0
    for section in parse_unified_diff(diff):
        old_path, new_path = section["old_path"], section["new_path"]
        for item in section["hunks"]:
            if old_path is None:
                base_side = {"path": None, "ranges": [], "gaps": [{"reason": "file-added"}]}
            else:
                base_side = _map_ranges(base, old_path, item["removed_ranges"])
            if new_path is None:
                candidate_side = {"path": None, "ranges": [], "gaps": [{"reason": "file-removed"}]}
            else:
                candidate_side = _map_ranges(candidate, new_path, item["added_ranges"])
            symbol_count += sum(len(value["symbols"]) for side in (base_side, candidate_side)
                                for value in side["ranges"])
            gap_count += len(base_side["gaps"]) + len(candidate_side["gaps"])
            hunks.append({
                "old_path": old_path,
                "new_path": new_path,
                "renamed": old_path is not None and new_path is not None and old_path != new_path,
                "old_start": item["old_start"], "old_count": item["old_count"],
                "new_start": item["new_start"], "new_count": item["new_count"],
                "base": base_side,
                "candidate": candidate_side,
            })
    return {
        "schema": SYMBOLS_AT_SCHEMA,
        "mode": "diff",
        "base": _snapshot_info(base),
        "candidate": _snapshot_info(candidate),
        "hunks": hunks,
        "summary": {"hunks": len(hunks), "symbols": symbol_count, "gaps": gap_count},
    }

# Extensions an import specifier may resolve to, in preference order.
_MODULE_EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".java", ".rs")
# Directory imports: `orders` resolving to the package's entry file.
_PACKAGE_FILES = ("__init__.py", "index.ts", "index.tsx", "index.js", "index.jsx", "mod.rs")
# A stylesheet resolves stylesheets only, and only these ways: a TypeScript
# `import "./theme"` never means `theme.css`, and a Python `import app` never
# means `app/static/app.css`, so none of this is tried for any other importer.
_STYLESHEET_SUFFIXES = (".css", ".scss", ".less")


def _by_basename(paths) -> dict[str, list[str]]:
    """
    Group paths by their final segment, each group sorted.

    Sorted rather than insertion order because the caller usually passes a
    set, whose iteration order depends on Python's per-process hash
    randomization: left unsorted, an ambiguous bare-basename citation with
    several candidates could resolve to a different one on every run of the
    identical tree. The ambiguity itself is not resolved here, only made to
    pick the same candidate consistently.
    """
    index: dict[str, list[str]] = {}
    for path in paths:
        index.setdefault(path.rsplit("/", 1)[-1], []).append(path)
    for candidates in index.values():
        candidates.sort()
    return index


def _lookup(candidate: str, known: dict[str, list[str]], importer: str) -> str | None:
    """
    Resolve one candidate path against the known set.

    A candidate matches a known path when it equals it or is a suffix of it at a
    segment boundary, because an import specifier names a module, not a path
    from the repository root. When several match, the one in the importer's own
    directory wins; a tie with no local winner resolves to nothing, since
    inflating the radius on a guess costs a re-read of the wrong file.
    """
    while candidate.startswith("./"):
        candidate = candidate[2:]
    if not candidate:
        return None
    hits = [p for p in known.get(candidate.rsplit("/", 1)[-1], [])
            if p == candidate or p.endswith("/" + candidate)]
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]
    home = importer.rsplit("/", 1)[0] if "/" in importer else ""
    local = [p for p in hits if p.rsplit("/", 1)[0] == home]
    return local[0] if len(local) == 1 else None


def _resolve_stylesheet(module: str, importer: str, known: dict[str, list[str]]) -> str | None:
    """
    A stylesheet import is a URL relative to the importing file, and each tool
    tries its own forms in its own order. Sass tries `.sass` and `.scss`, plain
    or partial, then `.css`, then the directory's index files; LESS appends
    `.less`; a plain CSS `@import` loads exactly what it names, or that name
    plus `.css`. A candidate must match a known path exactly: the specifier is
    already joined to the importer's directory, and a suffix match would bind
    it to a same-named file somewhere else.
    """
    if not module.startswith("."):
        return None
    base = importer.rsplit("/", 1)[0] if "/" in importer else ""
    joined = os.path.normpath(os.path.join(base, module)).replace(os.sep, "/")
    head, _, tail = joined.rpartition("/")
    partial = f"{head}/_{tail}" if head else f"_{tail}"
    lowered = importer.lower()
    candidates = [joined]
    if lowered.endswith(".scss"):
        for ext in (".sass", ".scss", ".css"):
            candidates += [joined + ext, partial + ext]
        candidates += [f"{joined}/{name}" for name in
                       ("_index.sass", "index.sass", "_index.scss", "index.scss", "_index.css", "index.css")]
    elif lowered.endswith(".less"):
        candidates.append(joined + ".less")
    else:
        candidates.append(joined + ".css")
    for candidate in candidates:
        if candidate in known.get(candidate.rsplit("/", 1)[-1], []):
            return candidate
    return None


def _strip_jsonc_comments(raw: str) -> str:
    """Strip // and /* */ comments and trailing commas from tsconfig-style JSONC."""
    out: list[str] = []
    i = 0
    n = len(raw)
    in_string = False
    while i < n:
        ch = raw[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(raw[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and raw[i + 1] == "/":
            i += 2
            while i < n and raw[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and raw[i + 1] == "*":
            i += 2
            while i + 1 < n and not (raw[i] == "*" and raw[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    cleaned = "".join(out)
    return re.sub(r'("(?:\\.|[^"\\])*")|,\s*(?=[}\]])',
                  lambda match: match.group(1) or "", cleaned)


def ts_path_config(root: Path, *, source_observations: dict[Path, bytes] | None = None) -> dict:
    """Read project module configuration only inside the target's perimeter.

    Each option retains the directory in which it was declared, including an
    inherited baseUrl or paths map. Package configs apply to their descendants.
    Relative extends are supported; package-manager config lookup is outside
    the analyzed tree's dependency perimeter and is deliberately not guessed.
    Supplied observations use absolute Path keys and replace live discovery and
    content reads, so snapshot consumers cannot acquire unrecorded configuration.
    """
    root = Path(root).resolve()
    config = {"root": root.as_posix(), "configs": {}, "packages": {}}
    if not root.is_dir():
        return config
    perimeter = Perimeter(root)

    def allowed(path: Path) -> bool:
        try:
            path.resolve().relative_to(root)
        except ValueError:
            return False
        return perimeter.covers(path) and not is_forbidden(path.name)

    documents: dict[Path, dict] = {}

    def read(path: Path) -> dict:
        path = path.resolve()
        if path in documents:
            return documents[path]
        data = {}
        if allowed(path):
            try:
                if source_observations is None:
                    text = path.read_text(encoding="utf-8") if path.stat().st_size <= MAX_PARSE_BYTES else None
                else:
                    captured = source_observations.get(path)
                    text = captured.decode("utf-8") if isinstance(captured, bytes) and len(captured) <= MAX_PARSE_BYTES else None
                if text is not None:
                    value = json.loads(_strip_jsonc_comments(text))
                    if isinstance(value, dict):
                        data = value
            except (OSError, UnicodeError, ValueError, RecursionError):
                pass
        documents[path] = data
        return data

    loaded: dict[Path, dict] = {}

    def options(path: Path, visiting: set[Path]) -> dict:
        path = path.resolve()
        # A cycle guard alone does not bound a long, acyclic inheritance chain.
        if path in visiting or len(visiting) >= 32:
            return {}
        if path in loaded:
            return loaded[path]
        document = read(path)
        merged = {}
        parent = document.get("extends")
        parents = parent if isinstance(parent, list) else [parent]
        for name in parents:
            if isinstance(name, str) and name.startswith("."):
                candidate = path.parent / name
                if allowed(candidate) and candidate.suffix != ".json":
                    is_file = (candidate.resolve() in source_observations if source_observations is not None
                               else candidate.is_file())
                    if not is_file:
                        candidate = Path(str(candidate) + ".json")
                if allowed(candidate):
                    merged.update(options(candidate, visiting | {path}))
        own = document.get("compilerOptions", {})
        if isinstance(own, dict):
            base = own.get("baseUrl")
            if isinstance(base, str):
                merged["baseUrl"] = (path.parent / base).resolve().as_posix()
            paths = own.get("paths")
            if isinstance(paths, dict):
                base_path = Path(merged.get("baseUrl", path.parent))
                merged["paths"] = {
                    pattern: [(base_path / target).as_posix() for target in targets
                              if isinstance(target, str)]
                    for pattern, targets in paths.items()
                    if isinstance(pattern, str) and isinstance(targets, list)
                }
        loaded[path] = merged
        return merged

    package_paths = []
    if source_observations is None:
        directories = perimeter.walk()
    else:
        observed_directories: dict[Path, set[str]] = {}
        for path in source_observations:
            if not isinstance(path, Path) or not path.is_absolute():
                raise ValueError("configuration observations require absolute Path keys")
            if allowed(path):
                observed_directories.setdefault(path.parent, set()).add(path.name)
        directories = sorted(observed_directories.items())
    for directory, names in directories:
        if "tsconfig.json" in names:
            path = directory / "tsconfig.json"
            config["configs"][directory.as_posix()] = options(path, set())
        elif "jsconfig.json" in names:
            path = directory / "jsconfig.json"
            config["configs"][directory.as_posix()] = options(path, set())
        if "package.json" in names:
            package_paths.append(directory / "package.json")

    project = read(root / "package.json")
    workspaces = project.get("workspaces", [])
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages", [])
    patterns = [item for item in workspaces if isinstance(item, str)] if isinstance(workspaces, list) else []
    for path in package_paths:
        directory = path.parent.relative_to(root).as_posix()
        if directory != "." and not any(fnmatch.fnmatchcase(directory, pattern.rstrip("/")) for pattern in patterns):
            continue
        package = read(path)
        name = package.get("name")
        if isinstance(name, str) and name:
            # Duplicate package identities are ambiguous, so neither wins.
            if name in config["packages"]:
                config["packages"][name] = None
            else:
                config["packages"][name] = {**package, "directory": path.parent.as_posix()}
    return config


def _expand_alias(module: str, aliases: dict[str, list[str]] | None) -> list[str]:
    """Expand the most specific configured path pattern, without inventing aliases."""
    expanded: list[str] = []
    if aliases:
        if module in aliases:
            return list(aliases[module])
        for pat, targets in sorted(aliases.items(), key=lambda item: (-len(item[0].split("*")[0]), -len(item[0]))):
            if pat.count("*") == 1:
                prefix, suffix = pat.split("*", 1)
                if module.startswith(prefix) and module.endswith(suffix):
                    mid = module[len(prefix): len(module) - len(suffix) if suffix else len(module)]
                    for t in targets:
                        expanded.append(t.replace("*", mid))
                    break
    return expanded


def _module_candidates(candidate: str, importer: str) -> list[str]:
    """Ordered file forms for this importer's language."""
    suffix = Path(importer).suffix.lower()
    if suffix == ".py":
        return [candidate + ".py", candidate + "/__init__.py"]
    if suffix in {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}:
        extensions = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
        paths = [candidate]
        # TS source commonly imports the JavaScript path emitted by its build.
        if suffix in {".ts", ".tsx"}:
            for emitted, source in ((".js", ".ts"), (".jsx", ".tsx"), (".mjs", ".mts"), (".cjs", ".cts")):
                if candidate.endswith(emitted):
                    paths.insert(0, candidate[:-len(emitted)] + source)
        if Path(candidate).suffix.lower() not in extensions:
            paths += [candidate + ext for ext in extensions]
            paths += [candidate + "/index" + ext for ext in extensions]
        return paths
    return [candidate] + [candidate + ext for ext in _MODULE_EXTENSIONS] + [candidate + "/" + name for name in _PACKAGE_FILES]


def _package_candidates(module: str, packages: dict) -> list[str]:
    for name in sorted(packages, key=len, reverse=True):
        if module != name and not module.startswith(name + "/"):
            continue
        package = packages[name]
        if not isinstance(package, dict):
            return []
        subpath = "." if module == name else "./" + module[len(name) + 1:]

        def targets(value) -> list[str]:
            if isinstance(value, str):
                return [value]
            if isinstance(value, list):
                return [target for item in value for target in targets(item)]
            if isinstance(value, dict):
                for condition in ("types", "import", "require", "default"):
                    if condition in value:
                        return targets(value[condition])
            return []

        exports = package.get("exports")
        if "exports" in package:
            if isinstance(exports, dict) and any(key.startswith(".") for key in exports):
                matches = _expand_alias(subpath, {key: targets(value) for key, value in exports.items()})
            else:
                matches = targets(exports) if subpath == "." else []
        elif subpath == ".":
            matches = [package[key] for key in ("types", "module", "main") if isinstance(package.get(key), str)] or ["./index"]
        else:
            matches = [subpath]
        directory = Path(package["directory"])
        return [(directory / value).as_posix() for value in matches
                if value.startswith("./") or (exports is None and not Path(value).is_absolute())]
    return []


def _python_module_candidates(module: str, home: Path, target: Path) -> list[str]:
    """Module bases shared by graph resolution and imported-module bindings."""
    if module.startswith("."):
        level = len(module) - len(module.lstrip("."))
        base = home
        for _ in range(level - 1):
            base = base.parent
        return [(base / module[level:].replace(".", "/")).as_posix()]
    base = target if target.is_dir() else target.parent
    return [(directory / module.replace(".", "/")).as_posix()
            for directory in (base, base / "src")]


def resolved_imports(manifest: dict, config: dict | None = None, *,
                     include_self: bool = False) -> dict[str, dict[str, list[str]]]:
    return dict(iter_resolved_imports(manifest, config, include_self=include_self))


def iter_resolved_imports(manifest: dict, config: dict | None = None, *,
                     include_self: bool = False,
                     only_importers: set[str] | None = None,
                     perimeter: Perimeter | None = None) -> dict[str, dict[str, list[str]]]:
    """Resolve each manifest specifier once, keeping its binding provenance.

    JS/TS paths match only explicit relative, configured or workspace targets.
    Python absolute modules use the analyzed root and its conventional src
    directory; relative Python modules start at the importing package.
    """
    root = Path(manifest.get("root") or ".").resolve()
    target = (root / (manifest.get("target") or ".")).resolve()
    config = ts_path_config(target) if config is None else config
    files = file_headers(manifest)
    if perimeter is None:
        perimeter = Perimeter(target)
    by_absolute: dict[Path, str] = {}
    by_norm: dict[str, str] = {}
    allowed_importers: set[str] = set()
    for rel in files:
        if is_forbidden(Path(rel).name):
            continue
        full_path = root / rel
        resolved_rel = full_path.resolve()
        if (resolved_rel.is_relative_to(target) or resolved_rel == target) and perimeter.covers(resolved_rel):
            by_absolute[resolved_rel] = rel
            allowed_importers.add(rel)
            norm_rel = os.path.normcase(os.path.abspath(str(full_path)))
            if os.path.normcase(str(resolved_rel)) == norm_rel:
                by_norm[norm_rel] = rel
    known = _by_basename(by_absolute.values())

    def lookup(candidate: str, importer: str) -> str | None:
        for path in _module_candidates(candidate, importer):
            norm_path = os.path.normcase(os.path.abspath(path))
            hit = by_norm.get(norm_path)
            if hit is not None and not os.path.islink(path):
                return hit
            if os.path.exists(path):
                match = by_absolute.get(Path(path).resolve())
                if match:
                    return match
        return None

    header_iter = (
        manifest.iter_file_headers_only()
        if hasattr(manifest, "iter_file_headers_only")
        else files.items()
    )
    for importer, entry in header_iter:
        if only_importers is not None and importer not in only_importers:
            continue
        if importer not in allowed_importers:
            yield importer, {}
            continue
        imports = entry.get("imports", [])
        bindings = entry.get("import_bindings", [])
        home = (root / importer).parent
        suffix = Path(importer).suffix.lower()
        settings = {}
        applicable = [(Path(directory), value) for directory, value in config.get("configs", {}).items()
                      if home.is_relative_to(Path(directory))]
        if applicable:
            settings = max(applicable, key=lambda item: len(item[0].parts))[1]
        modules = {}
        for module in imports:
            resolved = set()
            candidates = []
            if suffix == ".py":
                candidates = _python_module_candidates(module, home, target)
            elif suffix in {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}:
                if module.startswith("."):
                    candidates = [(home / module).as_posix()]
                else:
                    candidates = _expand_alias(module, settings.get("paths"))
                    if "baseUrl" in settings:
                        candidates.append((Path(settings["baseUrl"]) / module).as_posix())
                    candidates += _package_candidates(module, config.get("packages", {}))
            else:
                hit = resolve_module(module, importer, known)
                if hit and (include_self or hit != importer):
                    resolved.add(hit)
                if suffix in {".java", ".rs"}:
                    sep = "." if suffix == ".java" else "::"
                    for binding in bindings:
                        if binding.get("module") == module and binding.get("from"):
                            for name in binding.get("names", []):
                                if name == "*":
                                    continue
                                member = name.split(" as ", 1)[0].strip()
                                qualified = f"{module}{sep}{member}"
                                mhit = resolve_module(qualified, importer, known)
                                if mhit and (include_self or mhit != importer):
                                    resolved.add(mhit)
                                    modules[qualified] = [mhit]
                                elif hit and (include_self or hit != importer):
                                    modules[qualified] = [hit]
            if suffix == ".rs" and " as " in module:
                clean_mod = module.split(" as ", 1)[0].strip()
                if clean_mod and resolved:
                    modules[clean_mod] = sorted(resolved)
            for candidate in candidates:
                hit = lookup(candidate, importer)
                if hit and (include_self or hit != importer):
                    resolved.add(hit)
                    # Paths entries are ordered fallbacks, not multiple edges.
                    break
            if suffix == ".py":
                for binding in bindings:
                    if binding.get("module") == module and binding.get("from"):
                        for name in binding.get("names", []):
                            if name == "*":
                                continue
                            for candidate in candidates:
                                hit = lookup(candidate.rstrip("/") + "/" + name, importer)
                                if hit and (include_self or hit != importer):
                                    resolved.add(hit)
                                    break
            modules[module] = sorted(resolved)
        yield importer, modules


def module_targets(manifest: dict, config: dict | None = None, *,
                   include_self: bool = False) -> dict[str, list[str]]:
    """The distinct internal targets of every importer, in a stable order."""
    return {importer: sorted({target for targets in modules.values() for target in targets})
            for importer, modules in resolved_imports(manifest, config, include_self=include_self).items()}


def resolve_module(
    module: str,
    importer: str,
    known: dict[str, list[str]],
    aliases: dict[str, list[str]] | None = None,
) -> str | None:
    """Map an import specifier to a path in the snapshot, or None."""
    if not module:
        return None
    if importer.lower().endswith(_STYLESHEET_SUFFIXES):
        return _resolve_stylesheet(module, importer, known)
    candidates: list[str] = []
    if module.startswith("."):
        base = importer.rsplit("/", 1)[0] if "/" in importer else ""
        joined = os.path.normpath(os.path.join(base, module)).replace(os.sep, "/")
        candidates.append(joined)
        candidates += [joined + ext for ext in _MODULE_EXTENSIONS]
        candidates += [f"{joined}/{name}" for name in _PACKAGE_FILES]
    elif importer.lower().endswith(".rs"):
        raw = module.split(" as ", 1)[0].strip()
        if not raw.startswith(("crate::", "self::", "super::")):
            return None
        base = importer.rsplit("/", 1)[0] if "/" in importer else ""
        stem = importer.rsplit("/", 1)[-1][:-3]
        if raw.startswith("crate::"):
            rel_mod = raw[len("crate::"):].replace("::", "/")
            parts = importer.split("/")
            src_idx = max((idx for idx, seg in enumerate(parts[:-1]) if seg == "src"), default=-1)
            crate_root = "/".join(parts[:src_idx + 1]) if src_idx >= 0 else base
            prefixes = [f"{crate_root}/{rel_mod}" if crate_root else rel_mod]
            if crate_root:
                prefixes.append(rel_mod)
        elif raw.startswith("self::"):
            rel_mod = raw[len("self::"):].replace("::", "/")
            mod_dir = base if stem in {"mod", "lib", "main"} else (f"{base}/{stem}" if base else stem)
            prefixes = [f"{mod_dir}/{rel_mod}" if mod_dir else rel_mod]
        else:
            prefixes = []
            for start_dir in (
                [base]
                if stem in {"mod", "lib", "main"}
                else [f"{base}/{stem}" if base else stem, base]
            ):
                parent = start_dir
                rest = raw
                underflow = False
                while rest.startswith("super::"):
                    rest = rest[len("super::"):]
                    if not parent:
                        underflow = True
                        break
                    parent = parent.rsplit("/", 1)[0] if "/" in parent else ""
                if not underflow:
                    rel_mod = rest.replace("::", "/")
                    cand = f"{parent}/{rel_mod}" if parent else rel_mod
                    if cand not in prefixes:
                        prefixes.append(cand)
        for pref in prefixes:
            candidates += [pref + ".rs", f"{pref}/mod.rs"]
            if "/" in pref:
                mod_parent = pref.rsplit("/", 1)[0]
                candidates += [mod_parent + ".rs", f"{mod_parent}/mod.rs"]
        for candidate in candidates:
            if candidate in known.get(candidate.rsplit("/", 1)[-1], []):
                return candidate
        return None
    else:
        specifiers = _expand_alias(module, aliases) + [module]
        for spec in specifiers:
            if "/" in spec:
                candidates += [spec] + [spec + ext for ext in _MODULE_EXTENSIONS]
                candidates += [f"{spec}/{name}" for name in _PACKAGE_FILES]
            dotted = spec.replace(".", "/")
            candidates += [dotted + ext for ext in _MODULE_EXTENSIONS]
            candidates += [f"{dotted}/{name}" for name in _PACKAGE_FILES]
    for candidate in candidates:
        hit = (candidate if candidate in known.get(candidate.rsplit("/", 1)[-1], []) else None)
        if not module.startswith(".") and not importer.lower().endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")):
            hit = _lookup(candidate, known, importer)
        if hit:
            return hit
    return None


def build_import_index(manifest: dict, comparison: dict, symbols: dict) -> dict[str, list[str]]:
    """
    Reverse import edges over the CURRENT view of the tree: the manifest's
    imports for unchanged files, the fresh parse for added and modified ones.
    Removed files contribute no outgoing edges of their own, since a deleted
    file no longer imports anything.

    They still have to be resolvable AS TARGETS, though: a surviving,
    unchanged importer's own import list still names the module that used to
    point at the removed file, and that edge is exactly what a removed file's
    blast radius depends on. So the known set for resolution is the current
    tree plus every removed file's last-known path, while the set actually
    walked for outgoing edges stays the current tree only.
    """
    old_files = file_headers(manifest)
    fresh = symbols.get("fresh", {})
    current_imports: dict[str, list[str]] = {}
    for rel in comparison["unchanged"]:
        current_imports[rel] = list(old_files.get(rel, {}).get("imports", []))
    for rel, entry in fresh.items():
        current_imports[rel] = list(entry.get("imports", []))

    resolvable = list(current_imports) + [rel for rel in comparison["removed"] if rel not in current_imports]
    graph_manifest = {**header_metadata(manifest), "root": comparison.get("root") or manifest.get("root"),
                      "target": comparison.get("target") or manifest.get("target") or ".", "files": {
        rel: {**old_files.get(rel, {}), **fresh.get(rel, {}), "imports": current_imports.get(rel, [])}
        for rel in resolvable
    }}
    graph = module_targets(graph_manifest, include_self=True)
    index: dict[str, list[str]] = {}
    for importer in current_imports:
        for imported in graph[importer]:
            index.setdefault(imported, []).append(importer)
    return {key: sorted(value) for key, value in index.items()}


def blast_radius(index: dict[str, list[str]], comparison: dict, symbols: dict) -> list[dict]:
    """
    Files importing something that changed. One hop, never the transitive
    closure: on most codebases the closure is the whole tree, which is a full
    run wearing a different name.

    A modified file whose symbols all survived unchanged (lines shifted, a
    comment rewritten) puts nobody in the radius: an importer depends on what a
    module offers, not on where its lines sit. A removed file, and a modified
    file with no symbols at all, always do.
    """
    moved: set[str] = set()
    for state in ("added", "removed", "changed"):
        moved.update(item["file"] for item in symbols[state])
    structureless = {
        rel for rel in comparison["modified"]
        if not symbols.get("fresh", {}).get(rel, {}).get("symbols")
    }
    touched = (set(comparison["modified"]) & (moved | structureless)) | set(comparison["removed"])
    reverse: dict[str, list[str]] = {}
    for imported in touched:
        for importer in index.get(imported, []):
            if importer in touched:
                continue
            reverse.setdefault(importer, []).append(imported)
    return [{"file": key, "imports": sorted(value)} for key, value in sorted(reverse.items())]


def _cell(text: str) -> str:
    """A markdown table cell: a pipe splits a row even inside a code span, so it is escaped."""
    return str(text).replace("|", "\\|")


PHASE_FILES = (
    "01-structure.md", "02-interfaces.md", "03-flows.md", "04-semantics.md",
    "05-risks.md", "06-documentation.md", "07-final-report.md",
    "08-interconnect-map.md",
)

# `src/app/service.py::Class.method`
CITE_SYMBOL = re.compile(r"([\w./\\-]+\.[A-Za-z0-9_]+)::([A-Za-z_][\w.]*)")
# `theme.css::.dark #root > div:first-child`: a stylesheet symbol carries spaces
# and punctuation the bare form cannot, so it is cited inside backticks and
# matched whole.
CITE_SYMBOL_QUOTED = re.compile(r"`([\w./\\-]+\.[A-Za-z0-9_]+)::([^`\n]+)`")
# `src/app/service.py:42`
CITE_LINE = re.compile(r"([\w./\\-]+\.[A-Za-z0-9_]+):(\d+)\b")
# A bare path inside backticks or a table cell.
CITE_PATH = re.compile(r"[`|\s(\[]([\w./\\-]+\.[A-Za-z0-9_]+)[`|\s),\]]")


def cited_symbols(line: str) -> list[tuple[str, str]]:
    """Every `path::symbol` citation on a line, bare or quoted, without repeats."""
    quoted = CITE_SYMBOL_QUOTED.findall(line)
    # A quoted stylesheet selector is matched whole and never also by its leading
    # word: `theme.css::body > div` names `body > div`, not `body`. Its span is
    # blanked before the bare pattern runs.
    bare = CITE_SYMBOL_QUOTED.sub(
        lambda m: " " * len(m.group(0)) if m.group(1).lower().endswith(_STYLESHEET_SUFFIXES) else m.group(0),
        line,
    )
    return list(dict.fromkeys(CITE_SYMBOL.findall(bare) + quoted))


def _path_index(paths) -> dict[str, list[str]]:
    return _by_basename(paths)


def _match_cited_path(cited: str, index: dict[str, list[str]]) -> str | None:
    """A phase file cites a path as the model wrote it; match at a segment boundary."""
    normalized = cited.replace("\\", "/").lstrip("./")
    if not normalized:
        return None
    for candidate in index.get(normalized.rsplit("/", 1)[-1], []):
        if candidate == normalized or candidate.endswith("/" + normalized) or normalized.endswith("/" + candidate):
            return candidate
    return None


def _symbol_verdict(path: str, symbol: str, changed: set, removed: set, added_files: set,
                    removed_files: set) -> str | None:
    """
    A claim about a symbol is affected by what happened to THAT symbol, matched
    exactly. Never by what happened to its enclosing class: a class span
    encloses its methods, so editing any one method moves the class hash, and
    walking up to the class would mark every claim about every sibling method.
    A claim about the class as a whole cites the class, and is caught by the
    exact match on it.
    """
    if path in removed_files:
        return "file-removed"
    if path in added_files:
        return "file-added"
    if (path, symbol) in removed:
        return "symbol-removed"
    if (path, symbol) in changed:
        return "symbol-changed"
    return None


def scan_claims(parent_dir: Path, comparison: dict, symbols: dict, importers: list[dict]) -> list[dict]:
    """
    Every line in the parent's phase files that cites something the change set
    touched, with the reason it is affected. Excludes 07-final-report.md:
    Phase 7 is regenerated on every run, never carried, so a claim living only
    there is not a work item, and counting it would inflate claims_affected
    and the per-phase breakdown the checkpoint prints.
    """
    modified = set(comparison["modified"])
    added_files = set(comparison["added"])
    removed_files = set(comparison["removed"])
    importer_files = {entry["file"] for entry in importers}
    changed = {(item["file"], item["symbol"]) for item in symbols["changed"]}
    removed = {(item["file"], item["symbol"]) for item in symbols["removed"]}
    spans = {
        rel: {entry["symbol"]: entry for entry in entries}
        for rel, entries in symbols["renumber"].items()
    }
    index = _path_index(
        set(comparison["unchanged"]) | modified | added_files | removed_files | importer_files
    )

    claims: list[dict] = []
    for name in PHASE_FILES:
        if name == "07-final-report.md":
            continue  # Phase 7 is regenerated, never carried; see docstring.
        phase_path = parent_dir / name
        if not phase_path.exists():
            continue
        section = ""
        for number, line in enumerate(read_text(phase_path).split("\n"), start=1):
            if line.startswith("#"):
                section = line.strip()
                continue
            cites: list[str] = []
            reason: str | None = None

            for path_text, symbol in cited_symbols(line):
                path = _match_cited_path(path_text, index)
                if not path:
                    continue
                cites.append(f"{path}::{symbol}")
                verdict = _symbol_verdict(path, symbol, changed, removed, added_files, removed_files)
                reason = reason or verdict
                if verdict is None and path in modified and not symbols.get("fresh", {}).get(path, {}).get("symbols"):
                    # A file kept file-level (a minified stylesheet) has no symbol to
                    # judge by, so a symbol citation into it is judged by the file.
                    reason = reason or "file-modified"
                if verdict is None and path in importer_files:
                    reason = reason or "importer"

            for path_text, line_text in CITE_LINE.findall(line):
                path = _match_cited_path(path_text, index)
                if not path:
                    continue
                cites.append(f"{path}:{line_text}")
                if path in removed_files:
                    reason = reason or "file-removed"
                elif path in added_files:
                    reason = reason or "file-added"
                elif path in modified:
                    inside = any(
                        entry["start_old"] <= int(line_text) <= entry["end_old"]
                        for entry in spans.get(path, {}).values()
                    )
                    if not inside:
                        reason = reason or "line-outside-known-symbol"
                elif path in importer_files:
                    reason = reason or "importer"

            # The bare-path fallback runs ONLY when the line carried no precise
            # citation. A line that named a symbol or a line number has already
            # been judged at that precision, and re-judging it by its file would
            # mark every claim about every unchanged symbol in a modified file:
            # the symbol-level granularity, thrown away at the last step.
            if reason is None and not cites:
                for path_text in CITE_PATH.findall(line):
                    path = _match_cited_path(path_text, index)
                    if not path:
                        continue
                    if path in removed_files:
                        reason = "file-removed"
                    elif path in added_files:
                        reason = "file-added"
                    elif path in modified:
                        reason = "file-modified"
                    elif path in importer_files:
                        reason = "importer"
                    if reason:
                        cites.append(path)
                        break

            if reason:
                claims.append({
                    "phase_file": name,
                    "line": number,
                    "section": section,
                    "cites": sorted(set(cites)),
                    "reason": reason,
                })
    return claims


def recommend(ratio: float, threshold: float, affected: int, reasons: list[str]) -> str:
    if reasons:
        return "full"
    if affected == 0:
        return "none"
    if ratio > threshold:
        reasons.append(f"ratio {ratio:.2f} over threshold {threshold:.2f}")
        return "full"
    return "incremental"


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _changes_markdown(changes: dict) -> str:
    files = changes["files"]
    lines = ["# Codebase Map Change Set", ""]
    parent = changes.get("parent_run") or "none"
    git = changes.get("git") or {}
    head = f"Parent run: {parent}."
    if git.get("commit"):
        head += f" Worktree at {git['commit']}" + (" (dirty)." if git.get("dirty") else ".")
    lines += [head, "", "## Code changes", ""]
    lines.append(
        f"{len(files['modified'])} modified, {len(files['added'])} added, "
        f"{len(files['removed'])} removed, of {changes['totals']['files_in_snapshot']} in the snapshot."
    )
    lines.append("")
    for label, key in (("Modified", "modified"), ("Added", "added"), ("Removed", "removed")):
        if files[key]:
            lines.append(f"**{label}:**")
            lines += [f"- `{path}`" for path in files[key]]
            lines.append("")
    if any(changes["symbols"].values()):
        lines += ["| Symbol | File | Kind | Change |", "|---|---|---|---|"]
        for state in ("changed", "added", "removed"):
            for item in changes["symbols"][state]:
                lines.append(f"| `{_cell(item['symbol'])}` | `{_cell(item['file'])}` | {item['kind']} | {state} |")
        lines.append("")
    lines += ["## Blast radius", ""]
    if changes["importers"]:
        lines += ["| Importer | Imports |", "|---|---|"]
        lines += [
            f"| `{_cell(entry['file'])}` | {', '.join('`' + _cell(i) + '`' for i in entry['imports'])} |"
            for entry in changes["importers"]
        ]
    else:
        lines.append("No file imports anything that changed.")
    if "transitive_importers" in changes:
        reachable = changes["transitive_importers"]
        cycles = changes.get("import_cycles", [])
        lines += ["", "## Transitive import diagnostics", "",
                  "Static reachability is separate from the one-hop blast radius and update recommendation.",
                  f"Reachable importing files: {len(reachable)}. Cycle components: {len(cycles)}.", ""]
        if reachable:
            lines += ["| File | Shortest hops | Via | Seed |", "|---|---:|---|---|"]
            lines += [f"| `{_cell(item['file'])}` | {item['depth']} | `{_cell(item['via'])}` | `{_cell(item['seed'])}` |"
                      for item in reachable[:50]]
            if len(reachable) > 50:
                lines += ["", f"Showing 50 of {len(reachable)} importers; changes.json contains every record."]
            lines.append("")
        for component in cycles[:20]:
            lines.append("- Cycle component: " + ", ".join(f"`{_cell(path)}`" for path in component))
        if len(cycles) > 20:
            lines.append(f"Showing 20 of {len(cycles)} components; changes.json contains every component.")
    lines += ["", "## Affected claims", ""]
    if changes["claims"]:
        lines += ["| Phase file | Line | Section | Cites | Reason |", "|---|---|---|---|---|"]
        lines += [
            f"| {c['phase_file']} | {c['line']} | {_cell(c['section'])} | "
            f"{', '.join('`' + _cell(x) + '`' for x in c['cites'])} | {c['reason']} |"
            for c in changes["claims"]
        ]
    else:
        lines.append("No claim in the parent run cites anything that changed.")
    lines.append("")
    return "\n".join(lines)


def cmd_diff(args: argparse.Namespace) -> int:
    with ExitStack() as stack:
        parent_dir = Path(args.parent_run)
        target = Path(args.target)
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)

        reasons: list[str] = []
        parent_state = _read_json(parent_dir / "state.json") or {}
        present = any((parent_dir / f"snapshot/manifest.{format}").exists() for format in ("sqlite", "json"))
        manifest = stack.enter_context(open_snapshot(resolve_run_snapshot(parent_dir, parent_state))) if present else None
        if manifest is None:
            reasons.append("parent run has no snapshot manifest")
            manifest = {"files": {}, "target": None, "created_at": None}
        if parent_state.get("status") not in (None, "complete"):
            reasons.append(f"parent run status is {parent_state.get('status')}")
        if manifest.get("parser_fingerprint") != parser_fingerprint():
            reasons.append("parser identity changed or is missing; refresh the structural snapshot")
        target_resolved = target.resolve()
        root = repo_root(target_resolved).resolve()
        if manifest.get("root") != root.as_posix() or manifest.get("target") != relative_to_root(target_resolved, root):
            reasons.append("snapshot root or target differs from this run")
        if args.flags:
            try:
                requested = json.loads(args.flags)
            except ValueError:
                requested = {}
            parent_flags = parent_state.get("flags") or {}
            differing = sorted(k for k, v in requested.items() if parent_flags.get(k) != v)
            if differing:
                reasons.append("flags differ from the parent run: " + ", ".join(differing))

        comparison = compare_files(manifest, target, verify=args.verify)
        symbols = compare_symbols(manifest, comparison)
        index = build_import_index(manifest, comparison, symbols)
        importers = blast_radius(index, comparison, symbols)
        from dependency_graph import dependency_graph_metrics, transitive_importers

        diagnostic_graph = {rel: [] for rel in comparison["current"]}
        for dependency, importing_files in index.items():
            diagnostic_graph.setdefault(dependency, [])
            for importer in importing_files:
                diagnostic_graph.setdefault(importer, []).append(dependency)
        graph_metrics = dependency_graph_metrics(diagnostic_graph)
        diagnostic_seeds = sorted(set(comparison["added"]) | set(comparison["removed"]) | set(comparison["modified"]))
        reachable_importers = transitive_importers(index, diagnostic_seeds)
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

        from datetime import datetime, timezone
        changes = {
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
        (out_dir / "changes.json").write_text(
            json.dumps(changes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (out_dir / "changes.md").write_text(_changes_markdown(changes), encoding="utf-8")
        print(
            f"change set: {recommendation}; {len(affected_files)} affected files of {total}, "
            f"{len(claims)} affected claims -> {out_dir / 'changes.json'}"
        )
        return 0


MARKER_PREFIX = "<!-- xray:stale"


def renumber_line(text: str, renumber: dict, index: dict) -> str:
    """
    Move every `path:line` citation of a modified file onto its new line, when
    the old line falls inside a symbol that survived the edit. A citation
    outside every surviving span is left alone: the diff already marked its
    claim affected, so the model rewrites it rather than trusting the number.
    """
    def replace(match: "re.Match[str]") -> str:
        cited, number = match.group(1), int(match.group(2))
        path = _match_cited_path(cited, index)
        entries = renumber.get(path or "", [])
        for entry in entries:
            if entry["start_old"] <= number <= entry["end_old"]:
                return f"{cited}:{entry['start_new'] + (number - entry['start_old'])}"
        return match.group(0)

    return CITE_LINE.sub(replace, text)


def cmd_carry(args: argparse.Namespace) -> int:
    parent_dir = Path(args.parent_run)
    run_dir = Path(args.run_dir)
    changes = _read_json(run_dir / "changes.json")
    if changes is None:
        print("carry: no changes.json in the run directory; run `diff` first", file=sys.stderr)
        return 2

    knowledge = parent_dir / "knowledge"
    if knowledge.is_dir():
        shutil.copytree(knowledge, run_dir / "knowledge", dirs_exist_ok=True)

    renumber = changes.get("renumber", {})
    child_state = _read_json(run_dir / "state.json") or {}
    parent_phases = child_state.get("parent_phases")
    if parent_phases is not None and parent_phases != [1, 2, 3, 4]:
        print("carry: bound parent_phases must be [1, 2, 3, 4]", file=sys.stderr)
        return 2
    index = _path_index(
        set(renumber)
        | set(changes["files"]["modified"])
        | set(changes["files"]["added"])
        | set(changes["files"]["removed"])
    )
    by_file: dict[str, dict[int, dict]] = {}
    for claim in changes.get("claims", []):
        by_file.setdefault(claim["phase_file"], {})[claim["line"]] = claim

    copied = 0
    marked = 0
    carried = {}
    for name in PHASE_FILES:
        phase = PHASE_FILES.index(name) + 1
        source = parent_dir / name
        if not source.exists() or name == "07-final-report.md":
            continue  # Phase 7 is regenerated, never carried.
        if child_state.get("mode") == "classic" and phase == 8:
            continue
        if parent_phases is not None and phase not in parent_phases:
            continue
        marks = by_file.get(name, {})
        out_lines: list[str] = []
        # A carried claim must survive byte for byte, so the source is read
        # raw here rather than through read_text: that helper deliberately
        # normalizes CRLF and CR to LF for the hashing and diff paths it was
        # written for, which would silently rewrite a CRLF parent phase file
        # to LF. Splitting and joining on "\n" alone, with no newline style
        # detected or re-normalized, keeps each line's own trailing "\r" (if
        # it has one) attached to it, so mixed line endings survive too.
        raw = source.read_bytes().decode("utf-8", errors="replace")
        for number, line in enumerate(raw.split("\n"), start=1):
            claim = marks.get(number)
            if claim:
                cites = " ".join(claim["cites"])
                # The inserted marker takes the same line ending as the claim
                # line it sits above, so it does not break that file's style.
                ending = "\r" if line.endswith("\r") else ""
                out_lines.append(f"{MARKER_PREFIX} reason={claim['reason']} cites={cites} -->{ending}")
                out_lines.append(line)
                marked += 1
            else:
                out_lines.append(renumber_line(line, renumber, index))
        # newline="" so Python writes "\n" literally instead of translating
        # it to the platform's line separator, the other half of preserving
        # whatever ending style each line already carries.
        with (run_dir / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write("\n".join(out_lines))
        carried[name] = {
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "sha256": hashlib.sha256((run_dir / name).read_bytes()).hexdigest(),
        }
        copied += 1

    parent_state = _read_json(parent_dir / "state.json") or {}
    record = {
        "schema": 1, "parent_run": parent_state.get("run_id") or parent_dir.name,
        "parent_path": parent_dir.resolve().as_posix(), "artifacts": carried,
        "parent_manifest_sha256": artifact_digest(resolve_run_snapshot(parent_dir, _read_json(parent_dir / "state.json") or {}))
        if any((parent_dir / f"snapshot/manifest.{format}").is_file() for format in ("sqlite", "json")) else None,
    }
    (run_dir / "carry.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    added = changes.get("symbols", {}).get("added", [])
    if added:
        with (run_dir / "changes.md").open("a", encoding="utf-8") as handle:
            handle.write("\n## Added symbols\n\n")
            handle.write("No claim cites these yet. Phases 01 and 02 always; 03 to 06 at full depth.\n\n")
            handle.write("| Symbol | File | Kind |\n|---|---|---|\n")
            for item in added:
                handle.write(f"| `{_cell(item['symbol'])}` | `{_cell(item['file'])}` | {item['kind']} |\n")

    print(f"carry: {copied} phase files copied, {marked} claims marked stale, {len(added)} symbols added")
    return 0


def _legacy_check(args: argparse.Namespace) -> int:
    """
    The publication gate for an incremental run: no claim may still be marked
    stale, and every symbol the change set added must be cited somewhere.

    "Cited" means a phase file names it through the same `path::symbol` form
    every other citation in this file is matched by, on a line that is not
    itself a stale marker: a marker's own `cites=` field is written in that
    same shape, so it must be excluded before matching, or a claim's own
    unresolved marker would count as the documentation that resolves it. The
    citation must also resolve to the SAME file the symbol was added in, not
    merely carry the same bare name: two files can each define a `handler`,
    and a citation of one must never document an addition to the other. The
    path index is built from the added symbols' own files only, so a
    citation of an unrelated file never even attempts to resolve.
    """
    run_dir = Path(args.run_dir)
    changes = _read_json(run_dir / "changes.json")
    if changes is None:
        print("check: no changes.json in the run directory; run `diff` first", file=sys.stderr)
        return 2

    added = changes.get("symbols", {}).get("added", [])
    index = _path_index({item["file"] for item in added})

    problems: list[str] = []
    documented: set[tuple[str, str]] = set()
    for name in PHASE_FILES:
        path = run_dir / name
        if not path.exists():
            continue
        for number, line in enumerate(read_text(path).split("\n"), start=1):
            if line.startswith(MARKER_PREFIX):
                problems.append(f"{name}:{number}: claim still marked stale: {line.strip()}")
                continue
            for path_text, symbol in cited_symbols(line):
                resolved = _match_cited_path(path_text, index)
                if resolved:
                    documented.add((resolved, symbol))

    for item in added:
        if (item["file"], item["symbol"]) not in documented:
            problems.append(
                f"added symbol never documented: {item['file']}::{item['symbol']}"
            )

    if problems:
        print("check: FAILED")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print("check: clean")
    return 0


class RunControlError(ValueError):
    """A malformed or unsafe run binding; no state may be written."""


def _reject_links(path: Path) -> None:
    for part in (path, *path.parents):
        try:
            metadata = part.lstat()
        except FileNotFoundError:
            metadata = None
        if part.is_symlink() or (metadata is not None and getattr(metadata, "st_file_attributes", 0) & 0x400):
            raise RunControlError(f"linked path is not a run-owned regular path: {part}")


CANONICAL_STORE = ".codebase-map"
STORE_MARKER = ".codebase-map-store.json"
STORE_SCHEMA = "daodan/codebase-map-store/v1"
_STORE_RESERVED = {CANONICAL_STORE, ".codebase-xray", ".git"}
_DEVICE_NAMES = frozenset({"con", "prn", "aux", "nul", "conin$", "conout$",
                           *(f"{port}{i}" for port in ("com", "lpt")
                             for i in (*range(1, 10), "\u00b9", "\u00b2", "\u00b3"))})
_STORE_FORBIDDEN = re.compile(r'[\x00-\x1f<>:"|?*\\]')


def validate_store(value) -> str:
    """Return a project-relative custom store path, or raise RunControlError.

    A custom store starts with a dot directory, so every perimeter already
    leaves it out of the analyzed sources, and never reuses a canonical or
    legacy store name, which identify their project by position alone.
    """
    if (not isinstance(value, str) or not value or len(value) > 255 or value.startswith("/")
            or _STORE_FORBIDDEN.search(value)):
        raise RunControlError("analysis store must be an exact project-relative POSIX path")
    parts = value.split("/")
    if any(part in ("", ".", "..") or part != part.strip() or part.endswith(".") for part in parts):
        raise RunControlError("analysis store must be an exact project-relative POSIX path")
    if not parts[0].startswith("."):
        raise RunControlError("analysis store must begin with a dot directory outside the analyzed sources")
    if any(part.casefold() in _STORE_RESERVED or part.casefold().lstrip(".").split(".")[0] in _DEVICE_NAMES
           for part in parts):
        raise RunControlError("analysis store must not reuse a canonical, legacy, git or device name")
    return value


def store_project(root: Path) -> Path:
    """Project bound by an analysis store.

    The canonical store is the project's `.codebase-map`. A custom store
    records its own project-relative path in a marker; the project is the
    ancestor that path names, and the marker must resolve back to the store.
    """
    if root.name == CANONICAL_STORE:
        return root.parent
    marker = root / STORE_MARKER
    _reject_links(marker)
    if not marker.is_file():
        raise RunControlError(f"run must be inside a project's {CANONICAL_STORE}/runs/<run-id> "
                              f"or a custom store carrying {STORE_MARKER}")
    try:
        value = json.loads(marker.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        value = None
    if not isinstance(value, dict) or value.get("schema") != STORE_SCHEMA:
        raise RunControlError(f"custom store marker {STORE_MARKER} is unreadable or has another schema")
    store = validate_store(value.get("store"))
    project = root
    for _ in store.split("/"):
        project = project.parent
    if (project / store).resolve() != root.resolve():
        raise RunControlError("custom store marker does not name this store")
    return project


def _run_context(run_dir: Path) -> tuple[Path, Path, dict]:
    _reject_links(run_dir)
    run_dir = run_dir.resolve()
    if run_dir.parent.name != "runs":
        raise RunControlError(f"run must be inside a project's {CANONICAL_STORE}/runs/<run-id> "
                              f"or a custom store carrying {STORE_MARKER}")
    root = run_dir.parent.parent
    store_project(root)
    _reject_links(run_dir / "state.json")
    state = _read_json(run_dir / "state.json")
    if not isinstance(state, dict) or state.get("run_id") != run_dir.name:
        raise RunControlError("state.run_id must equal the exact run directory name")
    if state.get("mode") not in ("classic", "team"):
        raise RunControlError("state.mode must be classic or team")
    if not isinstance(state.get("flags"), dict) or not isinstance(state.get("target"), str):
        raise RunControlError("state requires flags and target")
    return run_dir, root, state


def _effective_flags(flags: dict) -> dict:
    effective = {"critical": False, "comments": False, "docs_only": False,
                 "phase": None, "depth": "full", "skip_synthesis": False,
                 "skip_interconnect": False}
    effective.update(flags)
    if effective["depth"] not in ("full", "lite"):
        raise RunControlError("depth must be full or lite")
    for key in ("critical", "comments", "docs_only", "skip_synthesis", "skip_interconnect"):
        if not isinstance(effective[key], bool):
            raise RunControlError(f"{key} must be a boolean")
    phase = effective["phase"]
    if phase is not None and (type(phase) is not int or phase not in range(1, 7)):
        raise RunControlError("--phase accepts 1 through 6; phase 7 summarizes a complete run")
    if effective["docs_only"] and phase is not None:
        raise RunControlError("--docs-only and --phase cannot be combined")
    if "stop_after" in effective or "resume_from" in effective:
        raise RunControlError("stop and resume are invocation controls, not immutable flags")
    return effective


def _artifact_bytes(run_dir: Path, name: str) -> bytes | None:
    paths = [run_dir / name]
    if name == "knowledge/":
        paths = [run_dir / "knowledge/navigation.md", run_dir / "knowledge/documentation-leads.md"]
    chunks = []
    for path in paths:
        _reject_links(path)
        if not path.is_file():
            return None
        data = path.read_bytes()
        if not data.strip():
            return b""
        chunks.append(path.name.encode() + b"\0" + data)
    return b"\0".join(chunks) if name == "knowledge/" else paths[0].read_bytes()


def _artifact_hash(run_dir: Path, name: str) -> str:
    data = _artifact_bytes(run_dir, name)
    if not data:
        raise RunControlError(f"missing or empty artifact: {name}")
    return hashlib.sha256(data).hexdigest()


def _bound_manifest(run_dir: Path, root: Path, state: dict, fresh: bool = False) -> dict:
    try:
        with open_snapshot(resolve_run_snapshot(run_dir, state)) as manifest:
            validate_reuse_manifest(manifest)
            project = store_project(root)
            target = Path(state["target"])
            if not target.is_absolute():
                target = project / target
            target = target.resolve()
            try:
                target.relative_to(project)
            except ValueError as exc:
                raise RunControlError("target is outside this run's project") from exc
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


def _write_json_atomic(path: Path, value: dict) -> None:
    _reject_links(path)
    fd, temporary = tempfile.mkstemp(prefix=".map-write-", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


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


def check_delivery(run_dir: Path) -> dict:
    run_dir, root, state = _run_context(run_dir)
    delivery = _validate_delivery(run_dir, root, state)
    _bound_manifest(run_dir, root, state)
    result = {key: [] for key in ("missing", "empty", "unexpected", "invalid_inherited", "stale", "undocumented_added", "not_yet_produced", "coverage_gaps")}
    artifacts = delivery["artifacts"]
    flags = delivery["flags"]
    stop = delivery.get("stop_after")
    incomplete = []
    documented = set()
    changes = _read_json(run_dir / "changes.json") or {}
    added = changes.get("symbols", {}).get("added", [])
    index = _path_index({item["file"] for item in added})
    for name, artifact in artifacts.items():
        phase = artifact["phase"]
        if artifact["status"] == "skipped":
            if (run_dir / name).exists():
                result["unexpected"].append(name)
            continue
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
        if data and name == "changes.md" and not deferred:
            required = ("Claims confirmed", "Claims revised", "Claims retired", "Claims added", "Extra reads")
            if any(f"## {heading}" not in data.decode("utf-8", errors="replace") for heading in required):
                result["empty"].append(name)
                bad = True
        documentation = name == "06-documentation.md" or name.endswith("/06-documentation.md")
        if data and documentation and flags["comments"] and flags["depth"] != "lite" and not deferred:
            text = data.decode("utf-8", errors="replace")
            section = re.search(r"^## Comment Quality\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
            if not section or not section.group(1).strip():
                result["empty"].append(name)
                bad = True
        if bad and produced:
            incomplete.append(phase)
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
        for ledger, complete_status in (("partitions", "done"), ("agents_spawned", "delivered")):
            entries = state.get(ledger, [])
            if not isinstance(entries, list):
                raise RunControlError(f"team {ledger} must be a list")
            for number, entry in enumerate(entries):
                if not isinstance(entry, dict) or entry.get("status") != complete_status:
                    result["coverage_gaps"].append({"ledger": ledger, "index": number,
                        "name": entry.get("name") if isinstance(entry, dict) else None,
                        "status": entry.get("status") if isinstance(entry, dict) else None})
    for key in ("missing", "empty", "unexpected", "invalid_inherited"):
        result[key] = sorted(set(result[key]))
    result["first_incomplete_phase"] = min(incomplete) if incomplete else None
    blocking = any(result[key] for key in ("missing", "empty", "unexpected", "invalid_inherited", "undocumented_added", "coverage_gaps")) or any(not marker["deferred"] for marker in result["stale"])
    result.update(run_id=state["run_id"], mode=delivery["mode"], invocation_complete=not blocking,
                  complete=not blocking and stop is None,
                  may_publish=not blocking and stop is None and flags["phase"] is None and not flags["docs_only"] and not flags["skip_synthesis"])
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


class _RegistryLock:
    """
    An OS byte-range lock on a persistent lock file. The OS releases it when
    its holder exits, so a crashed coordinator leaves no stale lock behind.
    """

    def __init__(self, path: Path, descriptor: int) -> None:
        self.path = path
        self.descriptor = descriptor

    def unlink(self) -> None:
        # Kept under its historical name: release, never delete, so a second
        # holder cannot lock a different inode of the same path.
        try:
            if os.name == "nt":
                import msvcrt
                os.lseek(self.descriptor, 0, os.SEEK_SET)
                msvcrt.locking(self.descriptor, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.descriptor, fcntl.LOCK_UN)
        finally:
            os.close(self.descriptor)


def _try_lock(descriptor: int) -> bool:
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _acquire_registry_lock(root: Path) -> _RegistryLock:
    lock = root / ".registry.lock"
    _reject_links(lock)
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + 10
    while not _try_lock(descriptor):
        if time.monotonic() >= deadline:
            os.close(descriptor)
            raise RunControlError("another coordinator holds the registry lock; retry after it finishes")
        time.sleep(0.05)
    return _RegistryLock(lock, descriptor)


def _read_registry(root: Path) -> dict:
    path = root / "runs.json"
    _reject_links(path)
    if not path.exists():
        return {"schema": 2, "active": [], "latest_completed": None}
    registry = _read_json(path)
    if (not isinstance(registry, dict) or not isinstance(registry.get("active"), list)
            or any(not isinstance(item, dict) or not isinstance(item.get("run_id"), str)
                   or not item["run_id"] for item in registry["active"])):
        raise RunControlError("malformed runs registry")
    return registry


def update_registration(run_dir: Path, *, active: bool) -> dict:
    run_dir, root, state = _run_context(run_dir)
    if active and (not isinstance(state.get("started_at"), str) or not state["started_at"]):
        raise RunControlError("registration requires state.started_at")
    lock = _acquire_registry_lock(root)
    try:
        registry = _read_registry(root)
        entries = [item for item in registry["active"] if item["run_id"] != state["run_id"]]
        if active:
            entries.append({key: state.get(key) for key in
                            ("run_id", "target", "mode", "started_at", "parent_run")})
        registry["active"] = entries
        _write_json_atomic(root / "runs.json", registry)
        return {"run_id": state["run_id"], "active": active,
                "registry": (root / "runs.json").as_posix()}
    finally:
        lock.unlink()


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
        if language:
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


def cmd_write(args: argparse.Namespace) -> int:
    try:
        with ExitStack() as stack:
            previous = stack.enter_context(open_snapshot(Path(args.reuse))) if args.reuse else None
            result = write_snapshot(Path(args.target), Path(args.out),
                                    format=getattr(args, "format", "sqlite"), previous=previous)
        print(f"snapshot: {result['file_count']} files -> {args.out}")
        return 0
    except (OSError, ValueError) as error:
        print(f"snapshot: cannot write manifest: {error}", file=sys.stderr)
        return 2


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


def main(argv: list[str] | None = None) -> int:
    from languages.python import require_minimum_interpreter
    require_minimum_interpreter("snapshot.py")
    parser = argparse.ArgumentParser(description="Codebase Map structural snapshots and change sets.")
    sub = parser.add_subparsers(dest="command", required=True)

    scope_parser = sub.add_parser("scope", help="count what a run would analyze and what its perimeter leaves out")
    scope_parser.add_argument("target")
    scope_parser.set_defaults(func=cmd_scope)

    write_parser = sub.add_parser("write", help="write a manifest for a target tree")
    write_parser.add_argument("target")
    write_parser.add_argument("--out", required=True)
    write_parser.add_argument("--format", choices=("sqlite", "json"), default="sqlite")
    write_parser.add_argument("--reuse", help="prior manifest; verify every file before reusing its parse")
    write_parser.set_defaults(func=cmd_write)

    resolve_parser = sub.add_parser("resolve", help="resolve the declared snapshot path and small header of a bound run")
    resolve_parser.add_argument("run_dir")
    resolve_parser.set_defaults(func=cmd_resolve)

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

    meta_query_parser = sub.add_parser("meta-query", help="query Meta-Code symbols, their cards with freshness against this snapshot, and bounded changesets")
    meta_query_parser.add_argument("manifest")
    meta_query_parser.add_argument("--path", action="append", default=[])
    meta_query_parser.add_argument("--symbol")
    meta_query_parser.add_argument("--freshness")
    meta_query_parser.add_argument("--no-history", action="store_true")
    meta_query_parser.add_argument("--limit", type=int, default=100)
    meta_query_parser.add_argument("--cards", help="card store; default: cards.sqlite of the analysis root the snapshot belongs to")
    meta_query_parser.set_defaults(func=cmd_meta_query)

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

    meta_upsert_parser = sub.add_parser("meta-upsert", help="write Meta-Code cards, bound to the digests of this snapshot, to the card store")
    meta_upsert_parser.add_argument("manifest")
    meta_upsert_parser.add_argument("--input", required=True, help="cards JSON file, or - for standard input")
    meta_upsert_parser.add_argument("--cards", help="card store; default: cards.sqlite of the analysis root the snapshot belongs to")
    meta_upsert_parser.set_defaults(func=cmd_meta_upsert)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
