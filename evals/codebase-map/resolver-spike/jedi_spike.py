# /// script
# requires-python = ">=3.11"
# dependencies = ["jedi>=0.19"]
# ///
"""Spike: how many unresolved Python call references Jedi resolves, and to where.

Read-only over a project checkout. Sampled: the files with the most unresolved
call references, capped per file, so the run is bounded and the rate is an
estimate over a declared sample, never a whole-project claim.
"""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "plugins" / "codebase-map" / "skills" / "map-method" / "scripts"))
from snapshot_store import _unpack  # noqa: E402

import jedi  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--files", type=int, default=25)
    parser.add_argument("--per-file", type=int, default=40)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    project_root = args.project.resolve()
    from snapshot_store import open_snapshot  # noqa: E402

    with open_snapshot(args.manifest) as store:
        manifest_root = Path(store.metadata["root"])
    db = sqlite3.connect(args.manifest)

    by_file = collections.Counter()
    positions: dict[str, list[tuple[int, int, str]]] = collections.defaultdict(list)
    query = ("SELECT r.file, r.l0, r.c0, r.payload FROM sem_references r "
             "JOIN sem_coverage c ON c.file=r.file "
             "WHERE r.kind='call' AND r.resolution!='resolved' AND c.language='python'")
    for file, line, column, blob in db.execute(query):
        record = _unpack(blob)
        if record.get("reason") == "unbound-name":
            continue  # a builtin or undeclared global is not a lost edge
        by_file[file] += 1
        positions[file].append((line, column, ".".join(record.get("parts") or []),
                                record.get("reason") or "none"))

    sample = [file for file, _ in by_file.most_common(args.files)]
    selected = [(file, item) for file in sample for item in positions[file][:args.per_file]]

    jedi_project = jedi.Project(path=str(project_root), added_sys_path=[str(project_root)])
    verdicts = collections.Counter()
    by_reason = collections.defaultdict(collections.Counter)
    targets = collections.Counter()
    examples = collections.defaultdict(list)
    result_extra: dict = {}
    latencies: list[float] = []
    started_all = time.perf_counter()

    for file, (line, column, parts, reason) in selected:
        absolute = manifest_root / file
        if not absolute.is_file():
            verdicts["file-missing"] += 1
            continue
        started = time.perf_counter()
        try:
            # A fresh Script per position and the default fast_parser: reusing
            # scripts or disabling fast_parser raises KeyError inside Jedi 0.20.1.
            inferred = jedi.Script(path=str(absolute), project=jedi_project).infer(
                line=line, column=column)
        except Exception as error:  # noqa: BLE001
            verdicts[f"infer-error:{type(error).__name__}"] += 1
            by_reason[reason][f"infer-error:{type(error).__name__}"] += 1
            if "first_traceback" not in result_extra:
                import traceback
                result_extra["first_traceback"] = traceback.format_exc(limit=14)
                result_extra["first_position"] = f"{file}:{line}:{column} {parts}"
            continue
        latencies.append(time.perf_counter() - started)
        if not inferred:
            verdicts["still-unresolved"] += 1
            by_reason[reason]["still-unresolved"] += 1
            if len(examples["still-unresolved"]) < 6:
                examples["still-unresolved"].append(f"{file}:{line}:{column} {parts}")
            continue
        definition = inferred[0]
        module_path = getattr(definition, "module_path", None)
        module = getattr(definition, "module_name", None) or ""
        if module_path is None:
            key = "builtin-or-compiled"
            targets[module.split(".")[0] or definition.name] += 1
        else:
            try:
                relative = Path(module_path).resolve().relative_to(project_root)
            except ValueError:
                key = "external-package"
                targets[module.split(".")[0] or "site-packages"] += 1
            else:
                key = "project-edge"
                targets[f"{relative.as_posix()}::{definition.name}"] += 1
        verdicts[key] += 1
        by_reason[reason][key] += 1
        if len(examples[key]) < 8:
            examples[key].append(f"{file}:{line}:{column} {parts} -> {module}::{definition.name}")

    total = sum(verdicts.values())
    elapsed = time.perf_counter() - started_all
    latencies.sort()
    result = {
        "engine": {"name": "jedi", "version": jedi.__version__, "runtime": "pure-python",
                   "fast_parser": bool(jedi.settings.fast_parser),
                   "python": sys.version.split()[0]},
        "project": str(project_root),
        "sample": {"files": len(sample), "positions": len(selected),
                   "unresolved_call_refs_total": sum(by_file.values())},
        "verdicts": dict(verdicts),
        "verdicts_by_unresolved_reason": {key: dict(value) for key, value in sorted(by_reason.items())},
        "elapsed_seconds": elapsed,
        "latency_ms": {"mean": (sum(latencies) / len(latencies) * 1000) if latencies else None,
                       "p95": (latencies[int(len(latencies) * 0.95) - 1] * 1000) if latencies else None},
        "top_project_targets": targets.most_common(15),
        "examples": {key: value for key, value in examples.items() if value},
        **result_extra,
    }
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
