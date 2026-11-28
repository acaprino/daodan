#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""The derived edge pass over a snapshot: each language's graph from its analyzer, saved in the edge store.

The lexical resolver in `resolution.py` is the floor: it resolves a unique lexical binding and nothing it cannot
prove. Every other edge comes from an analyzer's stage (`engine_pass.index_stage`): the language's indexer, its
index read as one graph (`code_graph`), the store's entry for the language with its coverage. An edge names its
resolver (`<entry>@<version>`), arrives at a declaration of this snapshot, and a reference the index does not
answer is a hole with its class: coverage is declared, never implied.

`--pass` runs every analyzer the snapshot's languages need, as the detached pass does;
`--engine <entry>` runs one stage.
"""
from __future__ import annotations

import argparse
import json
import os  # noqa: F401  callers patch these three through this module
import shutil  # noqa: F401
import sys
import time  # noqa: F401
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

if __name__ == "__main__":  # one module whether run or imported: the adapters import it back
    sys.modules.setdefault("resolve_edges", sys.modules[__name__])

from languages.python import require_minimum_interpreter  # noqa: E402
import resolution  # noqa: E402,F401
from snapshot_store import open_snapshot  # noqa: E402

# The names other modules reach through this one, from the modules that own them. They come before the pass:
# an adapter imports this module back while the pass builds `ENGINES` (`indexers/runtime.py`).
from source_positions import (byte_to_char, byte_to_utf16, char_to_byte, EngineFailure, Location,  # noqa: E402,F401
                              SourceLines, utf16_to_byte)
from engine_tools import (_declared_requirements, _platform, download, executable_name,  # noqa: E402,F401
                          free_memory, go_jobs, GO_VERSION,
                          KOTLIN_ANALYSIS, KOTLIN_COMPILER, KOTLIN_OPT_INS, KOTLIN_RUNTIME, maven_artifact,
                          MAVEN_CENTRAL, maven_central_dir, node_environment, open_url, python_environment,
                          python_manifests, RUST_ANALYZER_RELEASE, RUST_VERSION,
                          shared_cache_dir, shared_engine_dir, unpack, USER_AGENT)
from edge_grading import callee_column, grade, inventory_files, symbol_table, verify_sources  # noqa: E402,F401
from edge_store import (coverage_violation, default_edge_store, EDGE_SCHEMA, kept_languages,  # noqa: E402,F401
                        language_coverage, read_edge_holes, read_edge_store, store_binding,
                        write_edge_store)
from engine_pass import (_process_alive, compact_report, edge_state, engine_command, ensure_edges,  # noqa: E402,F401
                         index_stage, LOG_NAME, pass_languages, pass_plan, pass_state, REPORT_NAME, reset_pass,
                         run_pass, running_record, stage_command, stop_pass)
import engine_pass  # noqa: E402


def __getattr__(name: str):
    """The analyzers, read from the pass's module: it builds them last, after this module may have been imported."""
    if name in ("ENGINES", "ENGINE_LANGUAGES"):
        return getattr(engine_pass, name)
    raise AttributeError(f"module 'resolve_edges' has no attribute {name!r}")


def _arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("manifest", type=Path, nargs="?", help="a snapshot's manifest.sqlite")
    parser.add_argument("--pass", dest="whole_pass", action="store_true",
                        help="run every analyzer the snapshot's languages need, one after another, as the "
                             "detached pass does")
    parser.add_argument("--engine", choices=tuple(spec.name for spec in engine_pass.ENGINES),
                        help="the analyzer of one stage: an entry of the pass")
    parser.add_argument("--out", type=Path, default=None,
                        help="where to write the derived edge store; default "
                             "engine-edges.sqlite beside the manifest")
    parser.add_argument("--report-out", type=Path, default=None,
                        help="optional file path for the complete JSON report")
    parser.add_argument("--compact", action="store_true",
                        help="emit a compact summary on stdout instead of the full report")
    args = parser.parse_args(argv)
    if args.manifest is None:
        parser.error("a manifest is required")
    if not args.whole_pass and args.engine is None:
        parser.error("--engine or --pass is required")
    return args


def _stage(args: argparse.Namespace, manifest: Path) -> dict:
    """One stage's report: an analyzer's graph of its languages."""
    with open_snapshot(manifest) as store:
        project_root = (Path(store["root"]) / store["target"]).resolve()
    if project_root.is_file():
        project_root = project_root.parent
    spec = next(spec for spec in engine_pass.ENGINES if spec.name == args.engine)
    return index_stage(spec, manifest, project_root, out=args.out)


def main(argv: list[str] | None = None) -> int:
    require_minimum_interpreter("resolve_edges.py")
    args = _arguments(argv)
    manifest = args.manifest.resolve()
    if not manifest.is_file():
        print(json.dumps({"error": f"no such manifest: {manifest}"}), file=sys.stderr)
        return 2
    if args.whole_pass:
        # The detached pass runs every step: `recognize_stack`, `find_modules` and `find_entry_points` keep their records
        # while they are fresh, and run the model commands still unrun.
        import pipeline
        results = pipeline.run(manifest, report_path=(args.report_out or manifest.with_name(REPORT_NAME)).resolve())

        report = results.get(pipeline.LinkCalls.NAME) or {}
        if pipeline.AssembleGraph.NAME not in results:
            cause = next((value["failed"] for value in results.values() if "failed" in value),
                         "the pipeline ended before assemble_graph")
            print(f"the analysis failed: {cause}", file=sys.stderr)
            return 1
        print(json.dumps({key: report[key] for key in ("available", "languages")}, indent=2, sort_keys=True))
        return 0 if report.get("available") or not report["languages"] else 1
    report = _stage(args, manifest)
    report_out = None
    if args.report_out is not None:
        report_out = args.report_out.resolve()
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    emitted = compact_report(report, report_out=report_out) if args.compact else (
        {**report, "report_out": report_out.as_posix()} if report_out is not None else report
    )
    print(json.dumps(emitted, indent=2, sort_keys=True))
    return 0 if report.get("available") else 1


if __name__ == "__main__":
    raise SystemExit(main())
