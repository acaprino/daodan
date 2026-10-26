#!/usr/bin/env python3
"""Read verified source blocks from a Codebase Map snapshot, without a second index.

Context is everything outside exact function and method definitions, plus their
boundary lines in braced languages. Selected symbols and explicit ranges are
added to that context. Uncertain structure uses
the complete file. This selects lines, not a complete semantic dependency graph.
Each requested file is read once; its captured bytes are verified before decoding.
Outline consults metadata only and does not verify current source freshness.
Graph verifies the supplied manifest's sources and queries its recorded static
bindings, returning bounded links and requests for subsequent verified reads.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import stat
import sys
from contextlib import ExitStack
from collections import Counter, deque
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import snapshot  # noqa: E402
from snapshot_store import SnapshotStore, file_headers, open_snapshot  # noqa: E402
from tree_scope import Perimeter  # noqa: E402

__all__ = ["outline_manifest", "read_packet", "graph_packet"]

SCHEMA = "xray/source-reading/v1"


def _files(manifest: dict) -> dict:
    if isinstance(manifest, SnapshotStore):
        return file_headers(manifest)
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
    if pattern is not None and not isinstance(pattern, str):
        raise ValueError("pattern must be text")
    alternatives = [part.casefold() for part in pattern.split("|") if part] if pattern else []
    if pattern is not None and not alternatives:
        raise ValueError("pattern must name at least one literal substring")

    # Literal substrings separated by `|`, case-insensitive. A regular
    # expression from an MCP client could backtrack for minutes on every
    # inventoried name while holding the project lock.
    class _Literal:
        @staticmethod
        def search(text: str) -> bool:
            folded = text.casefold()
            return any(part in folded for part in alternatives)

    matcher = _Literal if pattern is not None else None
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


def graph_packet(manifest: dict, paths: list[str] | None = None,
                 hops: int = 2, limit: int = 100) -> dict:
    """Query recorded static links and return verified-reader requests.

    Only resolved call edges expand the symbol neighborhood, in both directions.
    Imports and centrality remain separate discovery metadata. Sources are
    verified once through the existing index; this never parses or writes them.
    """
    if isinstance(manifest, SnapshotStore):
        from semantic_store import query_graph
        return query_graph(manifest, paths, hops, limit)
    from dependency_graph import dependency_graph_metrics, transitive_importers
    from semantic_index import build_semantic_index

    files = _files(manifest)
    if type(hops) is not int or not 1 <= hops <= 3:
        raise ValueError("hops must be an integer from 1 to 3")
    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be a positive integer")
    if paths is not None and (not isinstance(paths, list) or not paths):
        raise ValueError("paths must be a nonempty list of exact inventoried files")
    for rel in files:
        _relative(rel)
    selected = sorted(set(files if paths is None else [_relative(path) for path in paths]))
    if any(path not in files for path in selected):
        raise ValueError("graph seed path is not inventoried")
    root, target, perimeter = _binding(manifest)
    if manifest.get("parser_fingerprint") != snapshot.parser_fingerprint():
        raise ValueError("parser fingerprint changed or is missing; refresh the manifest")
    permitted, excluded, observations = {}, {}, {}
    for rel, entry in files.items():
        if not isinstance(entry, dict):
            raise ValueError("invalid inventory entry; refresh the manifest")
        modules, bindings = entry.get("imports", []), entry.get("import_bindings", [])
        if (not isinstance(modules, list) or any(not isinstance(module, str) or not module for module in modules)
                or not isinstance(bindings, list) or any(
                    not isinstance(binding, dict) or not isinstance(binding.get("module"), str)
                    or not isinstance(binding.get("names", []), list)
                    or any(not isinstance(name, str) for name in binding.get("names", []))
                    or ("from" in binding and type(binding["from"]) is not bool)
                    for binding in bindings)):
            raise ValueError(f"invalid import metadata for {rel}; refresh the manifest")
        path = root / rel
        within = path.is_relative_to(target) if target.is_dir() else path == target
        if not within or snapshot.is_forbidden(path.name) or not perimeter.covers(path):
            if paths is not None and rel in selected:
                raise ValueError(f"graph seed is outside the current perimeter: {rel}")
            excluded[rel] = {"status": "excluded", "reason": "outside-current-perimeter",
                             "verified_source": False, "reference_count": 0, "resolved_count": 0}
            continue
        try:
            _source_path(rel, root, target, perimeter)
        except ValueError as exc:
            raise ValueError(f"cannot verify graph source {rel}; refresh the manifest: {exc}") from exc
        if entry.get("parser_profile") != snapshot.parser_profile(path, entry.get("language")):
            raise ValueError(f"parser backend changed for {rel}; refresh the manifest")
        permitted[rel] = entry
    # Finish path/backend preflight for the whole query before opening sources.
    for rel, entry in permitted.items():
        path = root / rel
        try:
            data = path.read_bytes() if path.stat().st_size <= snapshot.MAX_FILE_BYTES else None
        except OSError as exc:
            raise ValueError(f"cannot verify graph source {rel}; refresh the manifest") from exc
        if data is not None:
            if hashlib.sha256(data).hexdigest() != entry.get("raw_hash"):
                raise ValueError(f"source identity changed or is missing for {rel}; refresh the manifest")
            lines = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n").split("\n")
            if type(entry.get("lines")) is not int or entry["lines"] != len(lines):
                raise ValueError(f"line metadata is inconsistent for {rel}; refresh the manifest")
            observations[rel] = data

    # Restrict the existing index to preflighted entries before it can resolve
    # paths. A newly ignored link must not redirect a read into another file.
    current_manifest = {**manifest, "files": permitted}
    config = snapshot.ts_path_config(target, source_observations={root / rel: data
                                                                 for rel, data in observations.items()})
    index = build_semantic_index(current_manifest,
                                 import_graph=snapshot.resolved_imports(current_manifest, config, include_self=True),
                                 source_observations=observations)
    coverage = {**excluded, **index["coverage"]}
    invalid = {"stale", "fingerprint-mismatch", "unbound-source", "malformed"}
    for rel, item in coverage.items():
        if item["status"] in invalid:
            raise ValueError(f"graph evidence is {item['status']} for {rel}; refresh the manifest")
    verified = {rel for rel, item in coverage.items() if item["verified_source"]}
    declarations = index["declarations"]
    calls = [item for item in index["references"] if item["kind"] == "call"]

    def caller_node(call):
        return call["caller"] or call["file"] + "::@module"

    seeds = {identity for identity, item in declarations.items()
             if item["file"] in selected and item["kind"] in {"function", "class"}}
    seeds.update(path + "::@module" for path in selected if path in verified)
    adjacency = {}
    for call in calls:
        if call["resolution"] == "resolved":
            caller, callee = caller_node(call), call["target_id"]
            adjacency.setdefault(caller, set()).add(callee)
            adjacency.setdefault(callee, set()).add(caller)
    distance = dict.fromkeys(seeds, 0)
    pending = deque(sorted(seeds))
    while pending:
        node = pending.popleft()
        if distance[node] == hops:
            continue
        for neighbor in sorted(adjacency.get(node, ())):
            if neighbor not in distance:
                distance[neighbor] = distance[node] + 1
                pending.append(neighbor)
    selected_calls = []
    for call in calls:
        depth = distance.get(caller_node(call), hops)
        if call["resolution"] == "resolved":
            depth = min(depth, distance.get(call["target_id"], hops))
        if depth < hops:
            selected_calls.append({**call, "depth": depth + 1})
    selected_calls.sort(key=lambda item: (item["depth"], item["file"], item["span"], item["id"]))
    selected_declarations = [{**item, "depth": distance[identity]}
                             for identity, item in declarations.items() if identity in distance]
    selected_declarations.sort(key=lambda item: (item["depth"], item["file"], item["span"], item["id"]))
    related = set(selected) | {item["file"] for item in selected_declarations}
    related.update(item["file"] for item in selected_calls)

    imports = {rel: sorted({dependency for targets in index["_import_graph"].get(rel, {}).values()
                            for dependency in targets if dependency in verified})
               for rel in sorted(verified)}
    metrics = dependency_graph_metrics(imports)
    reverse = {}
    for importer, dependencies in imports.items():
        for dependency in dependencies:
            reverse.setdefault(dependency, []).append(importer)
    import_rows = [{"source": rel, "target": dependency} for rel, targets in imports.items()
                   for dependency in targets if rel in related or dependency in related]
    packet = _reference(manifest, files)
    packet.update(schema="xray/source-graph/v1",
                  manifest_digest=hashlib.sha256(json.dumps(manifest, sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest(),
                  query={"hops": hops, "limit": limit, "path_count": len(selected),
                         "whole_inventory": paths is None}, totals={}, truncated=[])

    def bounded(name, items):
        packet["totals"][name] = len(items)
        if len(items) > limit:
            packet["truncated"].append(name)
        return copy.deepcopy(items[:limit])

    packet["query"]["paths"] = bounded("query_paths", selected)
    packet["calls"] = bounded("calls", selected_calls)
    packet["declarations"] = bounded("declarations", selected_declarations)
    packet["imports"] = bounded("imports", import_rows)
    packet["coverage"] = {
        "counts": dict(sorted(Counter(item["status"] for item in coverage.values()).items())),
        "files": bounded("coverage", [{"path": rel, **coverage[rel]} for rel in sorted(
            coverage, key=lambda path: (path not in related, path))]),
    }
    packet["diagnostics"] = {
        "import_cycles": bounded("import_cycles", metrics["import_cycles"]),
        "transitive_importers": bounded("transitive_importers", transitive_importers(reverse, selected)),
        "pagerank": bounded("pagerank", [{"file": rel, "score": score} for rel, score in sorted(
            metrics["pagerank"].items(), key=lambda item: (-item[1], item[0]))]),
        **{name: value for name, value in metrics.items() if name.startswith("pagerank_")},
    }
    packet["totals"]["cycle_members"] = sum(len(cycle) for cycle in metrics["import_cycles"])
    if any(len(cycle) > limit for cycle in packet["diagnostics"]["import_cycles"]):
        packet["truncated"].append("cycle_members")
        packet["diagnostics"]["import_cycles"] = [cycle[:limit] for cycle in
                                                   packet["diagnostics"]["import_cycles"]]
    ranges = {path: [] for path in selected if path in verified}

    def add_range(item):
        span = item["span"]
        ranges.setdefault(item["file"], []).append((span[0], span[2]))

    for item in packet["declarations"]:
        add_range(item)
    for call in packet["calls"]:
        add_range(call)
        if call["target_id"] in declarations:
            add_range(declarations[call["target_id"]])
    requests, range_total = [], 0
    for rel, intervals in sorted(ranges.items()):
        intervals = _merge(intervals)
        range_total += len(intervals)
        if len(intervals) > limit and "request_ranges" not in packet["truncated"]:
            packet["truncated"].append("request_ranges")
        if not intervals:
            requests.append({"path": rel, "full_file": True})
        else:
            requests.append({"path": rel, "ranges": [{"start": start, "end": end}
                                                       for start, end in intervals[:limit]]})
    packet["requests"] = bounded("requests", requests)
    packet["totals"]["request_ranges"] = range_total
    packet["truncated"].sort()
    packet["notes"] = [
        "Static resolved bindings expand in both directions; unresolved calls never establish an edge.",
        "Module configuration uses only verified inventoried observations; newly added files require a refreshed inventory.",
        "Imports, transitive reachability and PageRank guide reading; they do not establish runtime propagation or change update invalidation.",
        "Coverage gaps and truncation prevent completeness claims; an empty incoming list does not prove a symbol unused.",
        "Read the selected requests through source_reader read before making source-supported claims. Application runtime coverage: none.",
    ]
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
    graph = commands.add_parser("graph", help="query verified snapshot call/import links and reading requests")
    graph.add_argument("manifest", type=Path)
    graph.add_argument("--path", action="append")
    graph.add_argument("--hops", type=int, choices=(1, 2, 3), default=2)
    graph.add_argument("--limit", type=int, default=100)
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
        with ExitStack() as stack:
            manifest = stack.enter_context(open_snapshot(args.manifest))
            if args.command == "outline":
                packet = outline_manifest(manifest, args.path, args.pattern, args.limit)
            elif args.command == "graph":
                packet = graph_packet(manifest, args.path, args.hops, args.limit)
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
    print(json.dumps(packet, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
