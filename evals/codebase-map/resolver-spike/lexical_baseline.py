# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Read-only inspection of a Codebase Map manifest for the resolver campaign.

Prints the schema of the semantic tables, the resolution breakdown of `call`
references per language (our lexical resolver's own baseline), and sample
payloads per unresolved reason so a measurement can be designed against the
real record shape. Never writes.
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--language", default=None)
    parser.add_argument("--prefix", default="")
    parser.add_argument("--payload-samples", type=int, default=2)
    parser.add_argument("--schema", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    db = sqlite3.connect(f"file:{args.manifest}?mode=ro", uri=True)
    out: dict = {"manifest": str(args.manifest)}

    with open_snapshot(args.manifest) as store:
        out["root"] = store.metadata.get("root")
        out["metadata_keys"] = sorted(store.metadata.keys())

    if args.schema:
        out["tables"] = [r[0] for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        out["sem_references_columns"] = [
            (r[1], r[2]) for r in db.execute("PRAGMA table_info(sem_references)")]
        out["sem_coverage_columns"] = [
            (r[1], r[2]) for r in db.execute("PRAGMA table_info(sem_coverage)")]
        out["languages"] = [list(r) for r in db.execute(
            "SELECT language, COUNT(*) FROM sem_coverage GROUP BY language ORDER BY 2 DESC")]

    where = "c.language = ?" if args.language else "1=1"
    params: list = [args.language] if args.language else []
    if args.prefix:
        where += " AND r.file LIKE ?"
        params.append(args.prefix + "%")

    out["call_refs_by_language_and_resolution"] = [
        list(r) for r in db.execute(
            f"SELECT c.language, r.resolution, COUNT(*) FROM sem_references r "
            f"JOIN sem_coverage c ON c.file = r.file "
            f"WHERE r.kind='call' AND ({where}) "
            f"GROUP BY c.language, r.resolution ORDER BY c.language, 3 DESC", params)]
    out["kinds"] = [list(r) for r in db.execute(
        f"SELECT r.kind, COUNT(*) FROM sem_references r JOIN sem_coverage c ON c.file=r.file "
        f"WHERE ({where}) GROUP BY r.kind ORDER BY 2 DESC", params)]

    # lexical baseline: what our own resolver settles, per language
    baseline: dict[str, dict] = {}
    for language, resolution, count in out["call_refs_by_language_and_resolution"]:
        entry = baseline.setdefault(language, {"resolved": 0, "unresolved": 0, "by_resolution": {}})
        entry["by_resolution"][resolution] = count
        if resolution == "resolved":
            entry["resolved"] += count
        else:
            entry["unresolved"] += count
    for language, entry in baseline.items():
        total = entry["resolved"] + entry["unresolved"]
        entry["total"] = total
        entry["lexical_resolved_share"] = (entry["resolved"] / total) if total else None
    out["lexical_baseline"] = baseline

    if args.payload_samples:
        samples: dict[str, list] = collections.defaultdict(list)
        q = (f"SELECT r.file, r.l0, r.c0, r.payload FROM sem_references r "
             f"JOIN sem_coverage c ON c.file=r.file "
             f"WHERE r.kind='call' AND r.resolution!='resolved' AND ({where})")
        for file, line, column, blob in db.execute(q, params):
            record = _unpack(blob)
            reason = record.get("reason") or "none"
            if len(samples[reason]) < args.payload_samples:
                samples[reason].append({"file": file, "l0": line, "c0": column,
                                        "record": record})
        out["payload_samples_by_reason"] = dict(samples)

    text = json.dumps(out, indent=2, ensure_ascii=False, default=str)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
