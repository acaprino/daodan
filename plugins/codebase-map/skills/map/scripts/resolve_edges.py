#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Resolve a snapshot's call references with a probed engine.

The lexical resolver in `resolution.py` is the floor: it resolves a unique lexical
binding and nothing it cannot prove. Measured on two real projects it resolved 9.7%
and 13.0% of call references, and an engine recovered 31.6% of the sampled positions
it was asked about (evals/codebase-map/resolver-spike, spec §3.2.2). This command
attaches that engine, and it is optional in the strict sense: it is probed, never
assumed, and its absence is a declared degradation that writes nothing.

Three rules keep an engine's output from being mistaken for the lexical graph's:

1. **Every edge names its resolver.** `payload.resolver` is `builtin-lexical` for a
   lexically resolved reference and `<engine>@<version>` for one this command wrote,
   with `payload.confidence` `confirmed`, `candidate` or `external`. Edges of two
   resolvers are not comparable and are never merged into one count.
2. **An edge must arrive at a symbol the snapshot already holds.** The engine's
   answer is graded by membership in this snapshot's own declaration table, which is
   the measured grading and also the prerequisite's point: an engine attached before
   the extraction convention widened produced edges with no arrival node. A target
   file outside the inventory is `external-definition`; a name inside the inventory
   that is no declaration is `project-not-a-symbol`, recorded as a candidate.
3. **Coverage is declared, never implied.** One inference costs about 99 ms (p95
   307 ms), so a whole project's unresolved population is hours, not seconds. The
   run reports how many positions it asked about out of how many, and `--limit`
   bounds it. A partial pass is a partial pass.

The calls the lexical resolver bound are asked about too, after the unresolved ones:
where the engine names another declaration or a definition outside the project, its
answer is stored and replaces the lexical target in the edge view. Their counts stay
apart, in `checked`, so `population`, `asked` and `confirmed` keep describing the
calls the lexical resolver left unresolved.

One property of an engine's answer needs stating before a consumer trusts an edge:
it can land on a *contract* rather than an implementation. Verified on this
repository's own scripts, `adapter.parse(...)` in `ast_parser.py` infers to the
`LanguageAdapter.parse` declaration in `languages/base.py`, which is the protocol the
call goes through, not the adapter that runs. Such an edge is true and is not
comparable to one landing on a concrete body: a consumer that propagates through it
(`stale-callers`, `edit_impact`) must decide that separately, which is one reason
these edges stay in their own store instead of being merged into the lexical graph.

`--pass` runs every analyzer the snapshot's languages need, as the detached pass does;
`--engine <entry>` runs one stage, under uv with its adapter's requirements (`stage_command`).
"""
from __future__ import annotations

import argparse
import importlib
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

# The names other modules reach through this one, from the modules that own them. The language servers come
# before the pass: an adapter imports this module back while the pass builds `ENGINES` (`indexers/runtime.py`).
from source_positions import (byte_to_char, byte_to_utf16, char_to_byte, EngineFailure, Location,  # noqa: E402,F401
                              SourceLines, utf16_to_byte)
from engine_tools import (_declared_requirements, _platform, download, executable_name,  # noqa: E402,F401
                          free_memory, go_jobs, GO_VERSION,
                          KOTLIN_ANALYSIS, KOTLIN_COMPILER, KOTLIN_OPT_INS, KOTLIN_RUNTIME, maven_artifact,
                          MAVEN_CENTRAL, maven_central_dir, node_environment, npm_key, npm_manifests,
                          npm_modules, open_url, package_directories, python_environment,
                          python_manifests, RUST_ANALYZER_RELEASE, RUST_VERSION,
                          shared_cache_dir, shared_engine_dir, unpack, USER_AGENT)
from language_servers import (_multilspy_pins, ENGINE_THREADS, LSP_REQUEST_TIMEOUT, LspEngine,  # noqa: E402,F401
                              MirroredEngine, SERVER_MEMORY_MB)
from scip_engine import ScipEngine  # noqa: E402,F401
from edge_grading import (callee_column, classify_reference, grade, grade_all, inventory_files,  # noqa: E402,F401
                          project_callee_names, symbol_table, verify_sources)
from edge_store import (coverage_violation, default_edge_store, EDGE_SCHEMA, kept_languages,  # noqa: E402,F401
                        language_coverage, read_edge_holes, read_edge_store, store_binding,
                        write_edge_store)
from position_stage import (ANSWERS_NAME, default_answers_path, dependency_digests, PUBLISH_SECONDS,  # noqa: E402,F401
                            resolve_edges, snapshot_languages)
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
    parser.add_argument("--engine", choices=("scip", *(spec.name for spec in engine_pass.ENGINES)),
                        help="the analyzer of one stage: an entry of the pass, or scip for --scip-index")
    parser.add_argument("--scip-index", action="append", default=[], type=Path,
                        help="path to a precomputed SCIP index file (index.scip Protobuf or JSON) when --engine "
                             "scip is used")
    parser.add_argument("--limit", type=int, default=None,
                        help="ask about at most this many positions")
    parser.add_argument("--stride", type=int, default=1,
                        help="ask about every Nth position, for a deterministic sample")
    parser.add_argument("--dry-run", action="store_true",
                        help="ask every position and grade it, without reusing cached answers or writing")
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
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be nonnegative")
    if args.stride < 1:
        parser.error("--stride must be positive")
    return args


def _stage(args: argparse.Namespace, manifest: Path) -> dict:
    """One stage's report: a precomputed SCIP index, an adapter's position engine or an indexer's graph."""
    with open_snapshot(manifest) as store:
        project_root = (Path(store["root"]) / store["target"]).resolve()
    if project_root.is_file():
        project_root = project_root.parent
    if args.engine == "scip":
        engine = ScipEngine(project_root, [path.resolve() for path in args.scip_index])
    else:
        spec = next(spec for spec in engine_pass.ENGINES if spec.name == args.engine)
        module = importlib.import_module(f"indexers.{spec.indexer}")
        if not hasattr(module, "engine"):
            return index_stage(spec, manifest, project_root, out=args.out)
        engine = module.engine(project_root)
    return resolve_edges(manifest, engine=engine, limit=args.limit, stride=args.stride, dry_run=args.dry_run,
                         out=args.out)


def main(argv: list[str] | None = None) -> int:
    require_minimum_interpreter("resolve_edges.py")
    args = _arguments(argv)
    manifest = args.manifest.resolve()
    if not manifest.is_file():
        print(json.dumps({"error": f"no such manifest: {manifest}"}), file=sys.stderr)
        return 2
    if args.whole_pass:
        # The detached pass is the pipeline after the scan: the stack, each analyzer, then the complete graph.
        import pipeline
        results = pipeline.run(manifest, start="stack",
                               report_path=(args.report_out or manifest.with_name(REPORT_NAME)).resolve())
        report = results.get("analyze") or {}
        if "failed" in report:
            print(f"the analysis failed: {report['failed']}", file=sys.stderr)
            return 1
        print(json.dumps({key: report[key] for key in ("available", "languages")}, indent=2, sort_keys=True))
        return 0 if report.get("available") else 1
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
