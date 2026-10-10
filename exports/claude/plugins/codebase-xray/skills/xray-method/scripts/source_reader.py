#!/usr/bin/env python3
"""Read verified source blocks from an X-ray snapshot, without a second index.

Context is everything outside exact function and method definitions, plus their
boundary lines in braced languages. Selected symbols and explicit ranges are
added to that context. Uncertain structure uses
the complete file. This selects lines, not a complete semantic dependency graph.
Each requested file is read once; its captured bytes are verified before decoding.
Outline consults metadata only and does not verify current source freshness.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import stat
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import snapshot  # noqa: E402
from tree_scope import Perimeter  # noqa: E402

__all__ = ["outline_manifest", "read_packet"]

SCHEMA = "xray/source-reading/v1"


def _files(manifest: dict) -> dict:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        raise ValueError("manifest must contain a files inventory")
    if manifest.get("schema") != snapshot.SCHEMA:
        raise ValueError("unsupported manifest schema; refresh the manifest")
    return manifest["files"]


def _reference(manifest: dict, files: dict) -> dict:
    return {
        "schema": SCHEMA,
        "root": manifest.get("root"),
        "target": manifest.get("target"),
        "scope": copy.deepcopy(manifest.get("scope", {})),
        "inventory": {
            "files": len(files),
            "schema": manifest.get("schema"),
            "created_at": manifest.get("created_at"),
            "parser_fingerprint": manifest.get("parser_fingerprint"),
        },
    }


def outline_manifest(manifest: dict, path: str | None = None,
                     pattern: str | None = None, limit: int = 100) -> dict:
    """Bounded navigation metadata, with no source reads or parser checks."""
    files = _files(manifest)
    if path is not None and path not in files:
        raise ValueError(f"path is not inventoried: {path}")
    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be a positive integer")
    try:
        matcher = re.compile(pattern) if pattern is not None else None
    except re.error as exc:
        raise ValueError(f"invalid pattern: {exc}") from exc
    items = []
    matched = 0
    for rel in sorted(files):
        if path is not None and rel != path:
            continue
        entry = files[rel]
        if not isinstance(entry, dict) or not isinstance(entry.get("symbols", {}), dict):
            raise ValueError(f"invalid inventory entry: {rel}")
        symbols = entry.get("symbols", {})
        for name, spec in sorted(symbols.items()) if symbols else [(None, {})]:
            if matcher and not (matcher.search(rel) or matcher.search(name or "")):
                continue
            matched += 1
            if len(items) == limit:
                continue
            if not isinstance(spec, dict):
                raise ValueError(f"invalid symbol metadata: {rel}:{name}")
            items.append({
                "path": rel,
                "symbol": name,
                "kind": spec.get("kind", "file"),
                "start": spec.get("start"),
                "end": spec.get("end"),
                "span_precision": spec.get("span_precision"),
                "language": entry.get("language"),
                "status": entry.get("status"),
                "lines": entry.get("lines"),
                "parser_notes": copy.deepcopy(entry.get("parser_notes", [])),
            })
    packet = _reference(manifest, files)
    packet.update(items=items, matched=matched, truncated=matched > len(items))
    return packet


def _relative(value: object, allow_root: bool = False) -> str:
    if allow_root and value == ".":
        return "."
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or value.startswith("/") or "\0" in value
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError("path must be an exact repository-relative POSIX path")
    return value


def _no_links(path: Path) -> None:
    """Refuse both symbolic links and Windows junction/reparse ancestors."""
    for component in [*reversed(path.parents), path]:
        try:
            info = component.lstat()
        except OSError as exc:
            raise ValueError(f"path is missing or inaccessible: {path}") from exc
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"symlink or reparse path is not permitted: {component}")


def _binding(manifest: dict) -> tuple[Path, Path, Perimeter]:
    value = manifest.get("root")
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ValueError("manifest root must be an absolute repository directory")
    root = Path(value)
    if any(part in (".", "..") for part in root.parts):
        raise ValueError("manifest root must be canonical")
    _no_links(root)
    if not root.is_dir():
        raise ValueError("manifest root is not a directory")
    target = root / _relative(manifest.get("target"), allow_root=True)
    _no_links(target)
    if not (target.is_dir() or target.is_file()):
        raise ValueError("manifest target is not a file or directory")
    return root, target, Perimeter(target)


def _source_path(rel: str, root: Path, target: Path, perimeter: Perimeter) -> Path:
    _relative(rel)
    if snapshot.is_forbidden(Path(rel).name):
        raise ValueError(f"forbidden source path: {rel}")
    path = root / rel
    # covers() deliberately passes paths outside its base, so check the target
    # boundary independently before consulting it.
    if target.is_dir():
        if not path.is_relative_to(target):
            raise ValueError(f"source is outside the manifest target: {rel}")
    elif path != target:
        raise ValueError(f"source is outside the manifest target: {rel}")
    _no_links(path)
    if not path.is_file():
        raise ValueError(f"source is not a regular file: {rel}")
    if not perimeter.covers(path):
        raise ValueError(f"source is outside the current perimeter: {rel}")
    return path


def _interval(start: object, end: object, total: int) -> tuple[int, int]:
    if type(start) is not int or type(end) is not int or not 1 <= start <= end <= total:
        raise ValueError(f"invalid line range: {start}:{end} (file has {total} lines)")
    return start, end


def _merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _context(symbols: dict, total: int, language: str | None = None) -> list[tuple[int, int]]:
    callables = [
        _interval(spec.get("start"), spec.get("end"), total)
        for spec in symbols.values() if spec.get("kind") in ("function", "method")
    ]
    definitions = _merge(callables)
    context = []
    cursor = 1
    for start, end in definitions:
        if cursor < start:
            context.append((cursor, start - 1))
        cursor = end + 1
    if cursor <= total:
        context.append((cursor, total))
    if language in {"java", "javascript", "typescript", "rust"}:
        # Line spans lack columns. A boundary can also declare a global or field,
        # so retain it even when the neighbouring callable is not selected.
        context.extend((line, line) for span in callables for line in span)
    return context


def _shared_lines(symbols: dict, lines: list[str], language: str | None) -> bool:
    """Line spans cannot isolate declarations that share a physical line."""
    if max(map(len, lines), default=0) > snapshot.MAX_STYLESHEET_LINE:
        return True
    callables = sorted(_interval(spec.get("start"), spec.get("end"), len(lines))
                       for spec in symbols.values() if spec.get("kind") in ("function", "method"))
    if any(left[1] >= right[0] for left, right in zip(callables, callables[1:])):
        return True
    if language in {"java", "javascript", "typescript", "rust"}:
        if any(start == end for start, end in callables):
            return True
    containers = [_interval(spec.get("start"), spec.get("end"), len(lines))
                  for spec in symbols.values() if spec.get("kind") not in ("function", "method")]
    # Python's class end is its last statement's end, not a closing brace.
    # In braced languages a shared end can hide fields or the class closure.
    starts = {start for start, _ in containers}
    ends = {end for _, end in containers}
    return any(start in starts or (language != "python" and end in ends)
               for start, end in callables)


def read_packet(manifest: dict, requests: list[dict]) -> dict:
    """Return verified blocks; invalid requests raise ValueError without a packet.

    source_characters_emitted counts unnumbered text plus one newline per emitted
    line. Source bytes are raw bytes read once for each distinct requested path.
    Scope and inventory metadata reference the supplied snapshot; current target
    and perimeter membership are checked for the requested paths only.
    """
    files = _files(manifest)
    if not isinstance(requests, list):
        raise ValueError("requests must be a list")
    root, target, perimeter = _binding(manifest)
    fingerprint = manifest.get("parser_fingerprint")
    if fingerprint is not None and fingerprint != snapshot.parser_fingerprint():
        raise ValueError("parser fingerprint changed; refresh the manifest")

    planned = {}
    for request in requests:
        if not isinstance(request, dict) or set(request) - {"path", "symbols", "ranges", "full_file"}:
            raise ValueError("invalid read request")
        rel = _relative(request.get("path"))
        if rel not in files:
            raise ValueError(f"path is not inventoried: {rel}")
        entry = files[rel]
        if not isinstance(entry, dict) or not isinstance(entry.get("symbols", {}), dict):
            raise ValueError(f"invalid inventory entry: {rel}")
        total = entry.get("lines")
        if type(total) is not int or total < 1:
            raise ValueError(f"invalid line count: {rel}")
        names, ranges = request.get("symbols", []), request.get("ranges", [])
        if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
            raise ValueError("symbols must be a list of qualified symbol names")
        if not isinstance(ranges, list) or type(request.get("full_file", False)) is not bool:
            raise ValueError("ranges must be a list and full_file must be a boolean")
        for name in names:
            if name not in entry.get("symbols", {}):
                raise ValueError(f"unknown symbol: {rel}:{name}")
        selected_ranges = []
        for span in ranges:
            if not isinstance(span, dict) or set(span) != {"start", "end"}:
                raise ValueError("ranges require start and end")
            selected_ranges.append(_interval(span["start"], span["end"], total))
        if rel not in planned:
            path = _source_path(rel, root, target, perimeter)
            profile = entry.get("parser_profile")
            if profile is not None and profile != snapshot.parser_profile(path, entry.get("language")):
                raise ValueError(f"parser backend changed for {rel}; refresh the manifest")
            planned[rel] = {"path": path, "entry": entry, "names": set(), "ranges": [], "full": False}
        plan = planned[rel]
        plan["names"].update(names)
        plan["ranges"].extend(selected_ranges)
        plan["full"] |= request.get("full_file", False)

    packet = _reference(manifest, files)
    packet["files"] = []
    metrics = {"source_bytes_read": 0, "source_lines_emitted": 0, "source_characters_emitted": 0}
    for rel, plan in planned.items():
        entry, path = plan["entry"], plan["path"]
        _source_path(rel, root, target, perimeter)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ValueError(f"source is missing or inaccessible: {rel}") from exc
        metrics["source_bytes_read"] += len(data)
        raw_hash = entry.get("raw_hash")
        if raw_hash is not None and hashlib.sha256(data).hexdigest() != raw_hash:
            raise ValueError(f"source changed for {rel}; refresh the manifest")
        text = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
        if raw_hash is None and snapshot.hash_text(text) != entry.get("hash"):
            raise ValueError(f"source changed for {rel}; refresh the manifest")
        _source_path(rel, root, target, perimeter)
        lines = text.split("\n")
        total = len(lines)
        if total != entry["lines"]:
            raise ValueError(f"line metadata is inconsistent for {rel}; refresh the manifest")
        symbols = entry.get("symbols", {})
        notes = []
        legacy = raw_hash is None or fingerprint is None or entry.get("parser_profile") is None
        uncertain = any(not isinstance(spec, dict) or spec.get("span_precision") != "exact"
                        for spec in symbols.values())
        if not uncertain:
            uncertain = _shared_lines(symbols, lines, entry.get("language"))
        if legacy:
            notes.append("Legacy identity metadata: full-file fallback; refresh the manifest.")
        if entry.get("status") != "parsed" or uncertain:
            notes.append("Uncertain or file-level structure: full-file fallback.")
        fallback = legacy or entry.get("status") != "parsed" or uncertain
        if plan["full"] or fallback:
            intervals = [(1, total)]
            reason = "full-file" if plan["full"] else "full-file-fallback"
        else:
            for name, spec in symbols.items():
                _interval(spec.get("start"), spec.get("end"), total)
            intervals = _context(symbols, total, entry.get("language")) + plan["ranges"]
            intervals.extend((symbols[name]["start"], symbols[name]["end"]) for name in plan["names"])
            intervals = _merge(intervals)
            reason = "context-and-selection"
        blocks = []
        for start, end in intervals:
            selected = lines[start - 1:end]
            blocks.append({
                "start": start, "end": end, "reason": reason,
                "source": "".join(f"{number}: {line}\n" for number, line in enumerate(selected, start)),
            })
            metrics["source_lines_emitted"] += len(selected)
            metrics["source_characters_emitted"] += sum(len(line) + 1 for line in selected)
        packet["files"].append({
            "path": rel, "raw_hash": raw_hash, "hash": entry.get("hash"),
            "status": entry.get("status"), "parser_profile": copy.deepcopy(entry.get("parser_profile")),
            "parser_notes": copy.deepcopy(entry.get("parser_notes", [])), "notes": notes,
            "blocks": blocks,
        })
    packet["metrics"] = metrics
    return packet


def _line_argument(value: str) -> dict:
    try:
        start, end = (int(part) for part in value.split(":"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("lines must be START:END") from exc
    return {"start": start, "end": end}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    outline = commands.add_parser("outline", help="navigate snapshot metadata without reading sources")
    outline.add_argument("manifest", type=Path)
    outline.add_argument("--path")
    outline.add_argument("--pattern")
    outline.add_argument("--limit", type=int, default=100)
    read = commands.add_parser("read", help="read source blocks verified against the snapshot")
    read.add_argument("manifest", type=Path)
    selection = read.add_mutually_exclusive_group(required=True)
    selection.add_argument("--path")
    selection.add_argument("--requests", type=Path)
    read.add_argument("--symbol", action="append", default=[])
    read.add_argument("--lines", action="append", type=_line_argument, default=[])
    read.add_argument("--full", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if args.command == "outline":
            packet = outline_manifest(manifest, args.path, args.pattern, args.limit)
        else:
            if args.requests:
                if args.symbol or args.lines or args.full:
                    raise ValueError("batch requests cannot be combined with selection options")
                requests = json.loads(args.requests.read_text(encoding="utf-8"))
                if isinstance(requests, dict):
                    requests = requests.get("requests")
            else:
                requests = [{"path": args.path, "symbols": args.symbol,
                             "ranges": args.lines, "full_file": args.full}]
            packet = read_packet(manifest, requests)
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(packet, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
