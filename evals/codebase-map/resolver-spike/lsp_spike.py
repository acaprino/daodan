# /// script
# requires-python = ">=3.11"
# dependencies = ["multilspy>=0.0.35"]
# ///
"""Spike: how many unresolved TypeScript/JavaScript call references the language
server of the project resolves, and to where.

Read-only over the project. multilspy downloads the language server binary into
its own package directory inside this scratch environment; nothing is written to
the project. Sampled, so the rate is an estimate over a declared sample.
"""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "plugins" / "codebase-map" / "skills" / "map-method" / "scripts"))
from snapshot_store import _unpack, open_snapshot  # noqa: E402

from multilspy import SyncLanguageServer  # noqa: E402
from multilspy.multilspy_config import MultilspyConfig  # noqa: E402
from multilspy.multilspy_logger import MultilspyLogger  # noqa: E402


def uri_to_path(uri: str) -> Path | None:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return None
    return Path(url2pathname(unquote(parsed.path)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True, help="language server workspace root")
    parser.add_argument("--language", default="typescript", choices=["typescript", "javascript"])
    parser.add_argument("--files", type=int, default=25)
    parser.add_argument("--per-file", type=int, default=40)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--server-binary", default=None,
                        help="explicit server executable; required on Windows, where multilspy "
                             "launches the extensionless npm shim and fails with WinError 193")
    args = parser.parse_args()

    workspace = args.project.resolve()
    with open_snapshot(args.manifest) as store:
        manifest_root = Path(store.metadata["root"])
    try:
        prefix = workspace.relative_to(manifest_root).as_posix() + "/"
    except ValueError:
        raise SystemExit(f"workspace {workspace} is outside the snapshot root {manifest_root}")

    db = sqlite3.connect(args.manifest)
    languages = ("typescript",) if args.language == "typescript" else ("javascript",)
    marks = ",".join("?" for _ in languages)
    by_file = collections.Counter()
    positions: dict[str, list[tuple[int, int, str, str]]] = collections.defaultdict(list)
    query = (f"SELECT r.file, r.l0, r.c0, r.payload FROM sem_references r "
             f"JOIN sem_coverage c ON c.file=r.file "
             f"WHERE r.kind='call' AND r.resolution!='resolved' AND c.language IN ({marks})")
    for file, line, column, blob in db.execute(query, languages):
        if not file.startswith(prefix):
            continue
        record = _unpack(blob)
        if record.get("reason") == "unbound-name":
            continue
        by_file[file] += 1
        positions[file].append((line, column, ".".join(record.get("parts") or []),
                                record.get("reason") or "none"))
    sample = [file for file, _ in by_file.most_common(args.files)]
    selected = [(file, item) for file in sample for item in positions[file][:args.per_file]]
    if not selected:
        raise SystemExit(f"no unresolved {args.language} call references under {prefix}")

    node_modules = workspace / "node_modules"
    settings = {"code_language": args.language}
    if args.server_binary:
        settings["server_binary"] = args.server_binary
    config = MultilspyConfig.from_dict(settings)
    server = SyncLanguageServer.create(config, MultilspyLogger(), str(workspace))
    verdicts = collections.Counter()
    by_reason = collections.defaultdict(collections.Counter)
    targets = collections.Counter()
    examples = collections.defaultdict(list)
    latencies: list[float] = []
    errors: dict[str, int] = {}

    started_all = time.perf_counter()
    with server.start_server():
        startup = time.perf_counter() - started_all
        for file, (line, column, parts, reason) in selected:
            relative = file[len(prefix):]
            if not (workspace / relative).is_file():
                verdicts["file-missing"] += 1
                continue
            started = time.perf_counter()
            try:
                # LSP positions are zero-based lines and characters.
                found = server.request_definition(relative, line - 1, column)
            except Exception as error:  # noqa: BLE001
                key = f"error:{type(error).__name__}"
                verdicts[key] += 1
                by_reason[reason][key] += 1
                errors[key] = errors.get(key, 0) + 1
                continue
            latencies.append(time.perf_counter() - started)
            if not found:
                verdicts["still-unresolved"] += 1
                by_reason[reason]["still-unresolved"] += 1
                if len(examples["still-unresolved"]) < 8:
                    examples["still-unresolved"].append(f"{file}:{line}:{column} {parts}")
                continue
            location = found[0] if isinstance(found, list) else found
            path = uri_to_path(location.get("uri", "")) if isinstance(location, dict) else None
            if path is None:
                key = "unreadable-location"
            else:
                resolved = path.resolve()
                relative_text = resolved.as_posix()
                if "node_modules" in relative_text:
                    key = "external-package"
                    targets[relative_text.split("node_modules/")[-1].split("/")[0]] += 1
                else:
                    try:
                        inside = resolved.relative_to(workspace)
                    except ValueError:
                        key = "outside-workspace"
                        targets[str(resolved.parent)] += 1
                    else:
                        key = "project-edge"
                        targets[inside.as_posix()] += 1
            verdicts[key] += 1
            by_reason[reason][key] += 1
            if len(examples[key]) < 8:
                examples[key].append(f"{file}:{line}:{column} {parts} -> {path}")

    elapsed = time.perf_counter() - started_all
    latencies.sort()
    result = {
        "engine": {"name": f"{args.language}-language-server via multilspy",
                   "language": args.language, "python": sys.version.split()[0]},
        "workspace": str(workspace),
        "node_modules_present": node_modules.is_dir(),
        "sample": {"files": len(sample), "positions": len(selected),
                   "unresolved_call_refs_in_workspace": sum(by_file.values())},
        "verdicts": dict(verdicts),
        "verdicts_by_unresolved_reason": {key: dict(value) for key, value in sorted(by_reason.items())},
        "server_startup_seconds": startup,
        "elapsed_seconds": elapsed,
        "latency_ms": {"mean": (sum(latencies) / len(latencies) * 1000) if latencies else None,
                       "p95": (latencies[int(len(latencies) * 0.95) - 1] * 1000) if latencies else None},
        "top_targets": targets.most_common(15),
        "examples": {key: value for key, value in examples.items() if value},
        "errors": errors,
    }
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: result[key] for key in
                      ("engine", "workspace", "node_modules_present", "sample", "verdicts",
                       "verdicts_by_unresolved_reason", "server_startup_seconds",
                       "elapsed_seconds", "latency_ms")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
