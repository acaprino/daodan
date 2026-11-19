"""Line ranges, or a unified diff, mapped to the symbols of one or two snapshots."""
from __future__ import annotations

import json
import re

from snapshot_store import SnapshotStore


SYMBOLS_AT_SCHEMA = "daodan/symbols-at/v1"
MAX_SYMBOLS_AT_REQUESTS = 100
MAX_SYMBOLS_AT_RANGES = 100
MAX_DIFF_CHARS = 4_000_000
MAX_DIFF_HUNKS = 2_000


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


class _DiffReader:
    """The file sections of a unified diff, read line by line."""

    _HEADERS = (("rename from ", "old_path"), ("rename to ", "new_path"),
                ("copy from ", "old_path"), ("copy to ", "new_path"))

    def __init__(self):
        self.sections: list[dict] = []
        self.section: dict | None = None
        self.hunk: dict | None = None
        self.old_line = self.new_line = self.old_left = self.new_left = 0

    def close_hunk(self) -> None:
        if self.section is not None and self.hunk is not None:
            self.hunk["removed_ranges"] = _coalesce_lines(self.hunk.pop("removed_lines"))
            self.hunk["added_ranges"] = _coalesce_lines(self.hunk.pop("added_lines"))
            self.section["hunks"].append(self.hunk)
        self.hunk = None

    def close_section(self) -> None:
        self.close_hunk()
        if self.section is not None:
            self.sections.append(self.section)
        self.section = None

    def read(self, raw: str) -> None:
        if raw.startswith("diff --git "):
            self.close_section()
            self.section = {"old_path": None, "new_path": None, "hunks": []}
            return
        if self.section is None:
            if raw.startswith("--- "):
                self.section = {"old_path": _diff_path(raw[4:]), "new_path": None, "hunks": []}
            return
        header_open = self.hunk is None or (self.old_left <= 0 and self.new_left <= 0)
        if header_open and self._header(raw):
            return
        match = _HUNK_HEADER.match(raw) if header_open else None
        if match:
            self._open_hunk(match)
            return
        if self.hunk is None or (self.old_left <= 0 and self.new_left <= 0):
            return
        self._body(raw)

    def _header(self, raw: str) -> bool:
        """A file header line between hunks: rename, copy, `---` or `+++`."""
        for prefix, key in self._HEADERS:
            if raw.startswith(prefix):
                self.section[key] = _diff_path(raw[len(prefix):])
                return True
        if raw.startswith("--- "):
            if self.section["hunks"] or self.section["new_path"] is not None:
                self.close_section()
                self.section = {"old_path": None, "new_path": None, "hunks": []}
            self.section["old_path"] = _diff_path(raw[4:])
            return True
        if raw.startswith("+++ "):
            self.section["new_path"] = _diff_path(raw[4:])
            return True
        return False

    def _open_hunk(self, match) -> None:
        self.close_hunk()
        hunks = sum(len(item["hunks"]) for item in self.sections)
        hunks += sum(len(item["hunks"]) for item in ([self.section] if self.section else []))
        if hunks >= MAX_DIFF_HUNKS:
            raise ValueError(f"diff has more than {MAX_DIFF_HUNKS} hunks")
        self.old_line = int(match.group(1))
        self.old_left = int(match.group(2) or "1")
        self.new_line = int(match.group(3))
        self.new_left = int(match.group(4) or "1")
        self.hunk = {"old_start": self.old_line, "old_count": self.old_left,
                     "new_start": self.new_line, "new_count": self.new_left,
                     "removed_lines": [], "added_lines": []}

    def _body(self, raw: str) -> None:
        prefix = raw[:1] or " "
        if prefix == "\\":
            return
        if prefix == "-":
            self.hunk["removed_lines"].append(self.old_line)
            self.old_line += 1
            self.old_left -= 1
        elif prefix == "+":
            self.hunk["added_lines"].append(self.new_line)
            self.new_line += 1
            self.new_left -= 1
        else:
            self.old_line += 1
            self.new_line += 1
            self.old_left -= 1
            self.new_left -= 1


def parse_unified_diff(text: str) -> list[dict]:
    """File sections and hunks of a unified diff, with changed line numbers.

    Only headers and hunk line positions are retained. Removed lines belong to
    the old side and added lines to the new side; context lines belong to both
    and are not changes.
    """
    if not isinstance(text, str) or len(text) > MAX_DIFF_CHARS:
        raise ValueError(f"diff must be text of at most {MAX_DIFF_CHARS} characters")
    reader = _DiffReader()
    for raw in text.splitlines():
        reader.read(raw)
    reader.close_section()
    return reader.sections


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
