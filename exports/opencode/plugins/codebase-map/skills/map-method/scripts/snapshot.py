#!/usr/bin/env python3
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

Standard library only. Parsing reuses the adapters in ./languages/.
"""

from __future__ import annotations

import argparse
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
from tree_scope import Perimeter, git_executable  # noqa: E402

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
    "scope_record",
    "symbol_spans",
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

# Non-source files a phase file legitimately cites.
DOC_EXTENSIONS = frozenset({
    ".cfg", ".ini", ".json", ".md", ".ps1", ".rst", ".sh", ".toml", ".txt",
    ".xml", ".yaml", ".yml",
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
    ".htm", ".html", ".sass", ".svelte", ".vue",
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
    The base every manifest path is relative to: the git top level when the
    target is inside a repository, otherwise the target itself.
    """
    base = target.parent if target.is_file() else target
    git = git_executable()
    if git is None:
        return base
    try:
        proc = subprocess.run(
            [git, "-C", str(base), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return base
    if proc.returncode != 0 or not proc.stdout.strip():
        return base
    return Path(proc.stdout.strip())


def parser_fingerprint() -> str:
    """Identity of the structural helpers and installed parser versions.

    Compute once per snapshot or read batch. Start a fresh process after updating
    helper code; this fingerprint does not reload already imported Python modules.
    Grammar availability is checked separately by parser_profile.
    """
    digest = hashlib.sha256()
    helpers = [SCRIPT_DIR / name for name in
               ("snapshot.py", "ast_parser.py", "tree_scope.py", "source_reader.py",
                "semantic_index.py", "dependency_graph.py")]
    helpers += sorted((SCRIPT_DIR / "languages").rglob("*.py"))
    for helper in helpers:
        if helper.is_file():
            digest.update(helper.relative_to(SCRIPT_DIR).as_posix().encode("utf-8") + b"\0")
            digest.update(helper.read_bytes())
            digest.update(b"\0")
    packages = ("tree-sitter", "tree-sitter-language-pack", "tree-sitter-java",
                "tree-sitter-javascript", "tree-sitter-typescript", "tree-sitter-rust")
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
    if language in {"java", "javascript", "typescript", "rust"}:
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
    """Commit, branch and dirtiness, as metadata. Nothing in the diff depends on it."""
    git = git_executable()
    if git is None:
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


def symbol_spans(result, lines: list[str]) -> dict[str, dict]:
    """
    Every symbol in a parse result, qualified, with its line span and body hash.

    Top-level symbols (classes and free functions) are spanned first: an exact
    end line where the adapter has one, otherwise the line before the next
    top-level symbol. Methods are spanned inside their class, so a class span
    always encloses its methods and editing a method moves both hashes.
    """
    total = len(lines)
    top: list[dict] = []
    for cls in result.classes:
        if cls.line_number > 0:
            top.append({
                "name": cls.name, "kind": cls.kind, "start": cls.line_number,
                "end": getattr(cls, "end_line", None), "methods": list(cls.methods),
            })
    for func in result.functions:
        if func.line_number > 0:
            top.append({
                "name": func.name, "kind": "function", "start": func.line_number,
                "end": getattr(func, "end_line", None), "methods": [],
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

    def record(name: str, kind: str, start: int, end: int, precision: str) -> None:
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
        if existing is not None:
            start = min(start, existing["start"])
            end = max(end, existing["end"])
            precision = "merged"
        spans[name] = {
            "kind": kind,
            "start": start,
            "end": end,
            "hash": span_hash(start, end),
            "span_precision": precision,
        }

    for item in top:
        record(item["name"], item["kind"], item["start"], item["end"], item["precision"])
        methods = sorted(
            (m for m in item["methods"] if m.line_number > 0),
            key=lambda m: m.line_number,
        )
        for index, method in enumerate(methods):
            end = getattr(method, "end_line", None)
            precision = "exact" if end else "inferred"
            if not end:
                end = methods[index + 1].line_number - 1 if index + 1 < len(methods) else item["end"]
            record(f"{item['name']}.{method.name}", "method", method.line_number, end, precision)
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
    command share. `git_ignore` is `unavailable` when the target is in no work
    tree or git did not answer: no ignore rule was applied then, and a reader
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
    old = manifest.get("files", {})
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
    old_files = manifest.get("files", {})
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
            elif previous["hash"] != spec["hash"]:
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
    """Resolve each manifest specifier once, keeping its binding provenance.

    JS/TS paths match only explicit relative, configured or workspace targets.
    Python absolute modules use the analyzed root and its conventional src
    directory; relative Python modules start at the importing package.
    """
    root = Path(manifest.get("root") or ".").resolve()
    target = (root / (manifest.get("target") or ".")).resolve()
    config = ts_path_config(target) if config is None else config
    files = manifest.get("files", {})
    perimeter = Perimeter(target)
    by_absolute = {(root / rel).resolve(): rel for rel in files
                   if ((root / rel).resolve().is_relative_to(target) or (root / rel).resolve() == target)
                   and perimeter.covers(root / rel) and not is_forbidden(Path(rel).name)}
    known = _by_basename(by_absolute.values())

    def lookup(candidate: str, importer: str) -> str | None:
        for path in _module_candidates(candidate, importer):
            match = by_absolute.get(Path(path).resolve())
            if match:
                return match
        return None

    graph = {}
    for importer, entry in files.items():
        if (root / importer).resolve() not in by_absolute:
            graph[importer] = {}
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
        graph[importer] = modules
    return graph


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
    old_files = manifest.get("files", {})
    fresh = symbols.get("fresh", {})
    current_imports: dict[str, list[str]] = {}
    for rel in comparison["unchanged"]:
        current_imports[rel] = list(old_files.get(rel, {}).get("imports", []))
    for rel, entry in fresh.items():
        current_imports[rel] = list(entry.get("imports", []))

    resolvable = list(current_imports) + [rel for rel in comparison["removed"] if rel not in current_imports]
    graph_manifest = {**manifest, "root": comparison.get("root") or manifest.get("root"),
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
    parent_dir = Path(args.parent_run)
    target = Path(args.target)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    reasons: list[str] = []
    manifest = _read_json(parent_dir / "snapshot" / "manifest.json")
    parent_state = _read_json(parent_dir / "state.json") or {}
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
    claims = scan_claims(parent_dir, comparison, symbols, importers) if manifest.get("files") else []

    affected_files = sorted(
        set(comparison["added"]) | set(comparison["removed"]) | set(comparison["modified"])
        | {entry["file"] for entry in importers}
    )
    # With no parent manifest, this falls back to the current worktree's file
    # count: the same fallback the ratio's denominator uses just below, so the
    # two always agree. A consumer that recomputes the ratio from the stored
    # totals must never divide by a files_in_snapshot of 0.
    total = len(manifest.get("files") or {}) or len(comparison["current"]) or 1
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
        "parent_manifest_sha256": hashlib.sha256((parent_dir / "snapshot/manifest.json").read_bytes()).hexdigest()
        if (parent_dir / "snapshot/manifest.json").is_file() else None,
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


def _run_context(run_dir: Path) -> tuple[Path, Path, dict]:
    _reject_links(run_dir)
    run_dir = run_dir.resolve()
    if run_dir.parent.name != "runs" or run_dir.parent.parent.name != ".codebase-map":
        raise RunControlError("run must be inside the project's .codebase-map/runs/<run-id>")
    root = run_dir.parent.parent
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
    path = run_dir / "snapshot/manifest.json"
    _reject_links(path)
    manifest = _read_json(path)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        raise RunControlError("run requires snapshot/manifest.json")
    validate_reuse_manifest(manifest)
    target = Path(state["target"])
    if not target.is_absolute():
        target = root.parent / target
    target = target.resolve()
    try:
        target.relative_to(root.parent)
    except ValueError as exc:
        raise RunControlError("target is outside this run's project") from exc
    if not isinstance(manifest.get("root"), str) or not isinstance(manifest.get("target"), str):
        raise RunControlError("snapshot requires root and target binding")
    if (Path(manifest["root"]) / manifest["target"]).resolve() != target:
        raise RunControlError("snapshot and state target bindings differ")
    if Path(manifest["root"]).resolve() != repo_root(target).resolve():
        raise RunControlError("snapshot root differs from the target's repository binding")
    for name in manifest["files"]:
        relative = Path(name)
        source = (Path(manifest["root"]) / relative).resolve()
        if relative.is_absolute() or ".." in relative.parts:
            raise RunControlError("snapshot file paths must be confined relative paths")
        try:
            source.relative_to(root.parent)
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
        for name, entry in manifest["files"].items():
            source = Path(manifest["root"]) / name
            if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != entry.get("raw_hash"):
                raise RunControlError("worktree bytes changed since the run snapshot; start a new run or update")
            if entry.get("parser_profile") != parser_profile(source, entry.get("language")):
                raise RunControlError("effective parser changed since the run snapshot; start a new run")
    return manifest


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
        "binding": {"project": root.parent.as_posix(), "target": state["target"], "parent_run": state.get("parent_run"), "parent_phases": state.get("parent_phases"), "incremental": updating},
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
    expected = {"project": root.parent.as_posix(), "target": state["target"], "parent_run": state.get("parent_run"), "parent_phases": state.get("parent_phases"), "incremental": state.get("incremental") is not None}
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
        return (provenance.get("run_id") == state["run_id"] and provenance.get("manifest_sha256") == hashlib.sha256((run_dir / "snapshot/manifest.json").read_bytes()).hexdigest())
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
    parent_manifest = hashlib.sha256((parent / "snapshot/manifest.json").read_bytes()).hexdigest()
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
            manifest_hash = hashlib.sha256((run_dir / "snapshot/manifest.json").read_bytes()).hexdigest()
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
    if (not isinstance(manifest, dict) or type(manifest.get("schema")) is not int or manifest["schema"] != SCHEMA
            or not isinstance(manifest.get("files"), dict)
            or not isinstance(manifest.get("root"), str)
            or not isinstance(manifest.get("target"), str)):
        raise ValueError("expected a snapshot object with schema, root, target and files")
    if "parser_fingerprint" in manifest and not isinstance(manifest["parser_fingerprint"], str):
        raise ValueError("invalid cached parser fingerprint")
    for rel, entry in manifest["files"].items():
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


def cmd_write(args: argparse.Namespace) -> int:
    previous = None
    if args.reuse:
        try:
            previous = json.loads(Path(args.reuse).read_text(encoding="utf-8"))
            if not isinstance(previous, dict):
                raise ValueError("reuse manifest must be a JSON object")
        except (OSError, ValueError) as exc:
            print(f"snapshot: cannot reuse manifest: {exc}", file=sys.stderr)
            return 2
    try:
        manifest = build_manifest(Path(args.target), previous)
    except (OSError, ValueError) as exc:
        print(f"snapshot: cannot build manifest: {exc}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=out.parent, prefix=f".{out.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        os.replace(temporary, out)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"snapshot: {len(manifest['files'])} files -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Codebase Map structural snapshots and change sets.")
    sub = parser.add_subparsers(dest="command", required=True)

    scope_parser = sub.add_parser("scope", help="count what a run would analyze and what its perimeter leaves out")
    scope_parser.add_argument("target")
    scope_parser.set_defaults(func=cmd_scope)

    write_parser = sub.add_parser("write", help="write a manifest for a target tree")
    write_parser.add_argument("target")
    write_parser.add_argument("--out", required=True)
    write_parser.add_argument("--reuse", help="prior manifest; verify every file before reusing its parse")
    write_parser.set_defaults(func=cmd_write)

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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
