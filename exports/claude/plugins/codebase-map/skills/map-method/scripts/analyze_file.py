#!/usr/bin/env python3
"""
Analyze File CLI.

Main entry point for analyzing a single source file: classification, structural
parse, and (optionally) cross-codebase usage lookup for its exported symbols.
Multi-language: Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust, CSS/SCSS/LESS.

Usage:
    python analyze_file.py --file <path> [options]
    python analyze_file.py --file <path> --symbol <name>
"""

import argparse
import json
import logging
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from classifier import classify_from_content, compute_fan_in
from ast_parser import parse_content
from usage_finder import (
    find_all_usages_batch, validate_symbol, SOURCE_EXTENSIONS, _resolve_project_root_and_paths,
)

__all__ = ["analyze_single_file", "format_as_markdown", "format_as_summary"]


def analyze_single_file(
    file_path: Path,
    find_usages: bool = False,
    project_root: Path | None = None,
    symbol: str | None = None,
    *, snapshot_path: Path | None = None,
) -> dict[str, Any]:
    with ExitStack() as stack:
        return _analyze_single_file(file_path, find_usages, project_root, symbol, snapshot_path, stack)


def _analyze_single_file(file_path, find_usages, project_root, symbol, snapshot_path, stack):
    """
    Perform complete analysis of a single source file.

    Args:
        file_path: Path to the source file (.py/.java/.js/.ts/.sql/PL-SQL/.rs/.css/.scss/.less)
        find_usages: Whether to find usages of exported symbols
        project_root: Root of the project (for usage finding)
        symbol: Restrict the usage search to this single exported symbol.
            Ignored unless find_usages is set. Returns an error result if the
            file does not export it.

    Returns:
        Dict with complete analysis results
    """
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}

    if file_path.suffix.lower() not in SOURCE_EXTENSIONS:
        return {
            "error": (
                f"Unsupported file extension {file_path.suffix!r}. "
                f"Supported: {', '.join(sorted(SOURCE_EXTENSIONS))}"
            )
        }

    from snapshot_store import open_snapshot
    from source_reader import _binding, _source_path
    manifest = None
    if snapshot_path is not None:
        manifest = stack.enter_context(open_snapshot(snapshot_path))
        bound_root, bound_target, perimeter = _binding(manifest)
        try:
            rel = file_path.resolve().relative_to(bound_root).as_posix()
        except ValueError as error:
            raise ValueError("source is outside the snapshot root") from error
        if not manifest.has_file(rel):
            raise ValueError("source is not inventoried in the snapshot")
        _source_path(rel, bound_root, bound_target, perimeter)
    else:
        import snapshot
        from tree_scope import Perimeter
        graph_target, _ = _resolve_project_root_and_paths(file_path, project_root)
        if snapshot.is_forbidden(file_path.name) or not Perimeter(graph_target).covers(file_path.resolve()):
            raise ValueError("source is outside the current perimeter")
    content = file_path.read_bytes().decode("utf-8")

    # Step 2: Parse structure
    try:
        structure = parse_content(content, file_path)
    except (SyntaxError, ValueError) as e:
        classification = classify_from_content(content, str(file_path))
        return {
            "error": f"Parse error in file: {e}",
            "classification": classification.classification.value,
        }

    from store_consumers import temporary_snapshot, consumer_reader, file_analysis, find_usages as store_usages

    graph_target, _ = _resolve_project_root_and_paths(file_path, project_root)
    if snapshot_path is None:
        manifest = stack.enter_context(temporary_snapshot(
            graph_target, parse_results={file_path.resolve(): (content, structure)}))
    graph_root = Path(manifest["root"])
    try:
        relative_path = file_path.resolve().relative_to(graph_root).as_posix()
    except ValueError:
        return {"error": "Source file is outside the snapshot root"}
    if not manifest.has_file(relative_path):
        return {"error": "Source file is not inventoried in the snapshot"}
    source_observations = {relative_path: content.encode("utf-8")}
    semantic_db = stack.enter_context(consumer_reader(
        manifest, fresh=snapshot_path is None, observations=source_observations))
    imported_by_count = semantic_db.execute(
        "SELECT count(DISTINCT source) FROM sem_edges WHERE target=? AND source<>?",
        (relative_path, relative_path)).fetchone()[0]
    semantic_analysis, graph_metrics, resolved_modules = file_analysis(manifest, semantic_db, relative_path)
    classification = classify_from_content(
        content, str(file_path), imported_by_count=imported_by_count, parse_result=structure,
    )

    # Step 3: Find usages (if requested)
    usages = {}
    if find_usages:
        if symbol is not None:
            if symbol not in structure.exported_symbols:
                exported = ", ".join(structure.exported_symbols) or "(none)"
                return {
                    "error": (
                        f"Symbol {symbol!r} is not exported by {file_path}. "
                        f"Exported symbols: {exported}"
                    ),
                    "classification": classification.classification.value,
                }
            target_symbols = [symbol]
        else:
            target_symbols = structure.exported_symbols[:5]  # Limit to first 5

        valid_targets: list[str] = []
        for target in target_symbols:
            try:
                validate_symbol(target)
                valid_targets.append(target)
            except ValueError as err:
                # A stylesheet exports class names such as `md:flex` that a usage
                # search refuses; one refusal must not end the whole analysis.
                usages[target] = {"error": str(err)}

        batch_results = store_usages(
            manifest, semantic_db, valid_targets, file_path, graph_target,
            limit=5, observations=source_observations,
        ) if valid_targets else {}
        for target in valid_targets:
            usage_result = batch_results[target]
            usages[target] = {
                "count": usage_result.total_count,
                "limit": usage_result.limit,
                "truncated": usage_result.truncated,
                "resolved_count": usage_result.resolved_count,
                "ast_candidate_count": usage_result.ast_candidate_count,
                "lexical_candidate_count": usage_result.lexical_candidate_count,
                "precision": usage_result.precision,
                "importing_modules": usage_result.importing_modules[:5],
                "importing_modules_total": len(usage_result.importing_modules),
                "truncated_sections": (["usages"] if usage_result.truncated else [])
                                      + (["importing_modules"] if len(usage_result.importing_modules) > 5 else []),
                "sample_usages": [
                    {
                        "file": u.file_path,
                        "line": u.line_number,
                        "type": u.usage_type,
                        "precision": u.precision,
                        "span": u.span,
                        "caller": u.caller,
                        "target_id": u.target_id,
                        "reason": u.reason,
                    }
                    for u in usage_result.usages[:5]
                ],
            }

    # Build result
    result = {
        "file": str(file_path),
        "language": structure.language,
        "parser_notes": structure.notes,
        "imported_by_count": imported_by_count,
        "semantic_analysis": semantic_analysis,
        "dependency_graph": graph_metrics,
        "classification": {
            "level": classification.classification.value,
            "lines_of_code": classification.lines_of_code,
            "num_dependencies": classification.num_dependencies,
            "imported_by_count": classification.imported_by_count,
            "verification_required": classification.verification_required,
            "reasoning": classification.reasoning,
            "critical_patterns": len(classification.critical_patterns_found),
            "complexity_indicators": len(classification.complexity_indicators),
        },
        "structure": {
            "classes": [
                {
                    "name": c.name,
                    "kind": c.kind,
                    "visibility": c.visibility,
                    "bases": c.bases,
                    "methods": [
                        {
                            "name": m.name,
                            "is_async": m.is_async,
                            "visibility": m.visibility,
                            "params": [p.name for p in m.parameters],
                            "calls_made": m.calls_made,
                        }
                        for m in c.methods
                    ],
                    "class_variables": c.class_variables,
                    "line": c.line_number,
                    "docstring": c.docstring[:100] if c.docstring else None,
                }
                for c in structure.classes
            ],
            "functions": [
                {
                    "name": f.name,
                    "is_async": f.is_async,
                    "visibility": f.visibility,
                    "params": [p.name for p in f.parameters],
                    "return_type": f.return_annotation,
                    "calls_made": f.calls_made,
                    "line": f.line_number,
                }
                for f in structure.functions
            ],
            "constants": structure.constants,
            "exported_symbols": structure.exported_symbols,
        },
        "dependencies": {
            "internal": list(
                sorted({i.module for i in structure.imports if resolved_modules.get(i.module)})
            ),
            "external": list(
                sorted({i.module for i in structure.imports if i.module and not resolved_modules.get(i.module)})
            ),
        },
        "external_calls": {
            call_type: [
                {"pattern": c.pattern, "line": c.line_number}
                for c in structure.external_calls
                if c.call_type == call_type
            ]
            for call_type in ["database", "network", "filesystem", "messaging", "ipc"]
            if any(c.call_type == call_type for c in structure.external_calls)
        },
    }

    if usages:
        result["usages"] = usages

    return result


def format_as_markdown(analysis: dict[str, Any]) -> str:
    """Format analysis result as Markdown."""
    if "error" in analysis:
        return f"## Error\n\n{analysis['error']}"

    lines = []

    # Header
    file_name = Path(analysis["file"]).name
    lines.append(f"# Analysis: {file_name}")
    lines.append("")
    if analysis.get("language"):
        notes = analysis.get("parser_notes") or []
        notes_text = f" ({', '.join(notes)})" if notes else ""
        lines.append(f"**Language:** {analysis['language']}{notes_text}")
        lines.append("")

    # Classification
    cls = analysis["classification"]
    lines.append("## Classification")
    lines.append("")
    lines.append(f"- **Level:** {cls['level'].upper()}")
    lines.append(f"- **Lines of Code:** {cls['lines_of_code']}")
    lines.append(f"- **Dependencies:** {cls['num_dependencies']}")
    lines.append(f"- **Importing files:** {cls.get('imported_by_count', 0)}")
    lines.append(f"- **Verification Required:** {'Yes' if cls['verification_required'] else 'No'}")
    lines.append(f"- **Reasoning:** {cls['reasoning']}")
    lines.append("")

    semantic = analysis.get("semantic_analysis")
    if semantic:
        counts = semantic["counts"]
        lines += ["## Static call bindings", "",
                  f"Coverage: {semantic['coverage']['status']}. "
                  f"Recorded callsites: {counts['callsites']}; resolved: {counts['resolved_callsites']}; "
                  f"unresolved: {counts['unresolved_callsites']}.",
                  f"Resolved incoming calls: {counts['incoming_calls']}. "
                  "An empty incoming list does not establish that a declaration is unused.", ""]
    graph = analysis.get("dependency_graph")
    if graph:
        lines += ["## Import graph diagnostics", "",
                  f"Cycles containing this file: {graph.get('totals', {}).get('import_cycles', len(graph['import_cycles']))}. "
                  f"Transitive importing files: {graph.get('totals', {}).get('transitive_importers', len(graph['transitive_importers']))}.",
                  "Reachability describes static imports. It does not change the one-hop update recommendation.", ""]

    # Structure - Classes (and class-like: interface, enum, type-alias, package, table...)
    if analysis["structure"]["classes"]:
        lines.append("## Classes / Types")
        lines.append("")
        for cls_info in analysis["structure"]["classes"]:
            bases = f" : {', '.join(cls_info['bases'])}" if cls_info['bases'] else ""
            kind = cls_info.get("kind") or "class"
            vis = f"{cls_info['visibility']} " if cls_info.get("visibility") else ""
            lines.append(f"### `{vis}{kind} {cls_info['name']}{bases}`")
            lines.append("")
            if cls_info.get("docstring"):
                lines.append(f"> {cls_info['docstring']}")
                lines.append("")
            lines.append(f"*Line {cls_info['line']}*")
            lines.append("")

            if cls_info["class_variables"]:
                lines.append("**Fields:**")
                for var in cls_info["class_variables"]:
                    lines.append(f"- `{var}`")
                lines.append("")

            if cls_info["methods"]:
                lines.append("**Methods:**")
                for method in cls_info["methods"]:
                    async_prefix = "async " if method["is_async"] else ""
                    vis_prefix = f"{method['visibility']} " if method.get("visibility") else ""
                    params = ", ".join(method["params"])
                    lines.append(f"- `{vis_prefix}{async_prefix}{method['name']}({params})`")
                lines.append("")

    # Structure - Functions
    if analysis["structure"]["functions"]:
        lines.append("## Functions / Procedures")
        lines.append("")
        for func in analysis["structure"]["functions"]:
            async_prefix = "async " if func["is_async"] else ""
            vis_prefix = f"{func['visibility']} " if func.get("visibility") else ""
            params = ", ".join(func["params"])
            ret = f" -> {func['return_type']}" if func.get("return_type") else ""
            lines.append(f"- `{vis_prefix}{async_prefix}{func['name']}({params}){ret}` (line {func['line']})")
        lines.append("")

    # Dependencies
    lines.append("## Dependencies")
    lines.append("")
    deps = analysis["dependencies"]
    if deps["internal"]:
        lines.append("**Internal:**")
        for dep in sorted(deps["internal"]):
            lines.append(f"- `{dep}`")
        lines.append("")
    if deps["external"]:
        lines.append("**External:**")
        for dep in sorted(deps["external"]):
            lines.append(f"- `{dep}`")
        lines.append("")

    # External Calls
    if analysis.get("external_calls"):
        lines.append("## External System Calls")
        lines.append("")
        for call_type, calls in analysis["external_calls"].items():
            lines.append(f"**{call_type.upper()}:**")
            for call in calls[:5]:  # Limit display
                lines.append(f"- `{call['pattern']}` (line {call['line']})")
            lines.append("")

    # Usages
    if analysis.get("usages"):
        lines.append("## Symbol Usages")
        lines.append("")
        for symbol, usage_data in analysis["usages"].items():
            if "error" in usage_data:
                lines.append(f"### `{symbol}`: not searched. {usage_data['error']}")
                lines.append("")
                continue
            lines.append(f"### `{symbol}` ({usage_data['count']} usages)")
            lines.append("")
            if "resolved_count" in usage_data:
                lines.append(
                    f"Resolved: {usage_data['resolved_count']}; "
                    f"AST candidates: {usage_data['ast_candidate_count']}; "
                    f"lexical candidates: {usage_data['lexical_candidate_count']}."
                )
                lines.append("")
            if usage_data["importing_modules"]:
                lines.append("**Imported by:**")
                for mod in usage_data["importing_modules"][:5]:
                    lines.append(f"- `{mod}`")
                lines.append("")

    return "\n".join(lines)


def format_as_summary(analysis: dict[str, Any]) -> str:
    """Format analysis result as a brief summary."""
    if "error" in analysis:
        return f"Error: {analysis['error']}"

    cls = analysis["classification"]
    struct = analysis["structure"]

    lang = analysis.get("language", "?")
    notes = analysis.get("parser_notes") or []
    note_text = f" ({notes[0]})" if notes else ""
    # Per the ParseResult docstring: "functions" is top-level only; class
    # methods live in classes[*].methods. Count both for the "callables"
    # number so Java files (which always have functions=[]) show the right
    # total.
    top_level_funcs = len(struct["functions"])
    method_count = sum(len(c.get("methods") or []) for c in struct["classes"])
    callable_total = top_level_funcs + method_count
    lines = [
        f"File: {analysis['file']}",
        f"Language: {lang}{note_text}",
        f"Classification: {cls['level'].upper()} ({cls['reasoning']})",
        f"LOC: {cls['lines_of_code']} | Dependencies: {cls['num_dependencies']}",
        f"Importing files: {cls.get('imported_by_count', 0)}",
        f"Classes/Types: {len(struct['classes'])} | Callables: {callable_total} (top-level: {top_level_funcs}, methods: {method_count})",
        f"Exported: {', '.join(struct['exported_symbols'][:5])}{'...' if len(struct['exported_symbols']) > 5 else ''}",
        f"Internal deps: {len(analysis['dependencies']['internal'])} | External deps: {len(analysis['dependencies']['external'])}",
    ]

    semantic = analysis.get("semantic_analysis")
    if semantic:
        counts = semantic["counts"]
        lines.append(f"Static calls ({semantic['coverage']['status']}): "
                     f"{counts['resolved_callsites']} resolved, {counts['unresolved_callsites']} unresolved")

    if cls["verification_required"]:
        lines.append("*** VERIFICATION REQUIRED ***")

    return "\n".join(lines)


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description=(
            "Analyze a source file: classification, structure, and optional "
            "usage lookup. Supports Python, Java, JavaScript, TypeScript, "
            "SQL, PL/SQL, Rust, CSS/SCSS/LESS."
        )
    )

    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="Path to source file to analyze (any supported language)",
    )
    parser.add_argument(
        "-s", "--symbol",
        type=str,
        help=(
            "Restrict the usage search to this exported symbol "
            "(implies --find-usages)"
        ),
    )
    parser.add_argument(
        "-o", "--output-format",
        choices=["json", "markdown", "summary"],
        default="summary",
        help="Output format (default: summary)",
    )
    parser.add_argument(
        "-u", "--find-usages",
        action="store_true",
        help="Find usages of exported symbols",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root directory",
    )

    parser.add_argument("--snapshot", type=Path, help="Reuse the run's bound SQLite or explicit JSON snapshot")
    args = parser.parse_args()

    if not args.file:
        parser.error("--file is required")

    # Resolve paths
    file_path = args.file
    if not file_path.is_absolute():
        file_path = args.project_root / file_path

    # Run analysis
    result = analyze_single_file(
        file_path,
        find_usages=args.find_usages or args.symbol is not None,
        project_root=args.project_root,
        symbol=args.symbol,
        snapshot_path=args.snapshot,
    )

    # Format output
    if args.output_format == "json":
        print(json.dumps(result, separators=(",", ":"), default=str))
    elif args.output_format == "markdown":
        print(format_as_markdown(result))
    else:  # summary
        print(format_as_summary(result))


if __name__ == "__main__":
    main()
