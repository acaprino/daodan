# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Read-only probe over a Codebase Map manifest for the resolver measurement campaign.

Prints per-file / per-prefix distributions of unresolved call references so a
measurement can be scoped before it runs. Never writes.
"""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "plugins" / "codebase-map" / "skills" / "map-method" / "scripts"))
from snapshot_store import _unpack, open_snapshot  # noqa: E402


def load_positions(manifest: Path, language: str, prefix: str = ""):
    db = sqlite3.connect(manifest)
    by_file: collections.Counter[str] = collections.Counter()
    reasons: collections.Counter[str] = collections.Counter()
    positions: dict[str, list] = collections.defaultdict(list)
    query = (
        "SELECT r.file, r.l0, r.c0, r.payload FROM sem_references r "
        "JOIN sem_coverage c ON c.file=r.file "
        "WHERE r.kind='call' AND r.resolution!='resolved' AND c.language=?")
    params: list = [language]
    if prefix:
        query += " AND r.file LIKE ?"
        params.append(prefix + "%")
    for file, line, column, blob in db.execute(query, params):
        record = _unpack(blob)
        reason = record.get("reason") or "none"
        reasons[reason] += 1
        if reason == "unbound-name":
            continue
        by_file[file] += 1
        positions[file].append((line, column, record.get("parts") or [], reason))
    return by_file, reasons, positions


def group_by_prefix(by_file: collections.Counter, prefixes: list[str]) -> dict[str, int]:
    out = {p or "<none>": 0 for p in prefixes}
    out["<other>"] = 0
    for file, count in by_file.items():
        hit = next((p for p in prefixes if p and file.startswith(p)), None)
        out[hit if hit is not None else "<other>"] += count
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--prefix", default="")
    parser.add_argument("--top", type=int, default=60)
    parser.add_argument("--group", action="append", default=[],
                        help="manifest-relative prefix to aggregate totals for")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    with open_snapshot(args.manifest) as store:
        root = store.metadata.get("root")
    by_file, reasons, positions = load_positions(args.manifest, args.language, args.prefix)

    payload = {
        "manifest": str(args.manifest),
        "root": root,
        "language": args.language,
        "prefix_filter": args.prefix,
        "total_measurable": sum(by_file.values()),
        "files": len(by_file),
        "reasons": dict(reasons),
        "groups": group_by_prefix(by_file, args.group) if args.group else None,
        "per_file_top": by_file.most_common(args.top),
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
