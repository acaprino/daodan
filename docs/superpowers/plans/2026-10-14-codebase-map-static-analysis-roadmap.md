# Codebase Map static analysis engine modernization

Scope: the deterministic helpers in `plugins/codebase-map/skills/map-method/scripts/`,
engine tests and the engine section of `docs/plugins/codebase-map.md`. Preserve
CLI fields, load-budget caps, the source perimeter, stylesheet support and the
separation between static analysis and runtime evidence.

The engine work is independent of the atomic-method refactor. Publication must
include only engine changes from shared files and regenerate all five hosts.

## Required behavior for steps 1–5

| Step | Behavior | Main implementation |
|---|---|---|
| 1 | One source read/parse for file analysis, shared TS/JS AST and batched usage search | `analyze_file.py`, `ast_parser.py`, language adapters, `usage_finder.py` |
| 2 | Accurate declarations, preserved spans, syntax diagnostics and no declarations/calls from comment or literal text | language adapters, `snapshot.file_entry` |
| 3 | Per-thread parsers, shared immutable grammars, deterministic parallel snapshots and bounded configuration resolution | `_treesitter.py`, `snapshot.py` |
| 4 | Distinct importing-file counts from the actual graph, available without a symbol usage query | `compute_fan_in`, `classify_directory`, `analyze_file.py` |
| 5 | Per-callable AST call extraction for JS/TS, Java and Rust, including construction and macros | `query_captures`, `extract_ast_calls`, language adapters |

### Reading, reuse and batch work

`ast_parser.parse_content` accepts already-loaded source. The file analyzer reads
bytes once, decodes without newline rewriting and supplies `(content, ParseResult)`
to `snapshot.build_manifest(..., parse_results=...)`. This keeps source identity,
structural extraction, graph construction and classification tied to the same
observation. The optional usage batch reuses that manifest.

Snapshots inventory and hash the selected target even when verified structure is
reused. Fresh entries can parse concurrently at a batch of eight, with at most
eight workers. The result order remains deterministic. Source-reading and parsing
counts are testable properties; runtime speed or token savings require separate
measurement and are not inferred from them.

Usage discovery selects permitted files before searching with ripgrep, grep or
Python fallback. It deduplicates requested symbols and resolves import bindings
once for a batch, rather than guessing a module name from a dotted filename.

### Structural extraction and call attribution

Use the existing `ClassInfo`, `FunctionInfo`, `bases` and `class_variables` models.
TypeScript adds interface/enum members, namespaces, abstract declarations and
heritage; Java retains nested types, records and enum members; Rust retains
module qualification, fields, variants, aliases, constants, macros and trait
implementations. Recognized JavaScript component wrappers remain callable;
ordinary operations with callback arguments do not imply a callable result.

A syntax error remains a parse error even when intact declarations can be kept.
Partial symbols cannot authorize narrow source reading of a damaged file.
SQL/PLSQL masking preserves newlines and quoted identifiers while excluding
comment and string contents from declaration matching.

`FunctionInfo.calls_made` lists distinct syntactic call names in source order.
Call nodes, construction nodes and Rust macros feed extraction. A nested
callable owns its own body; comments, string literals and type annotations do not
create outgoing calls. Native extraction and regex fallback remain distinguishable.
These names do not claim dynamic resolution of receivers or runtime call targets.

### Configuration and the internal graph

`ts_path_config(target)` supplies bounded configuration to
`module_targets(manifest, config=None)`. It supports JSONC, relative `extends`
(including cycles), `baseUrl`, `paths`, package-local configurations and workspace
package entry points/subpaths. Relative configuration values retain their owning
configuration directory. No config or alias can expand the target perimeter.
External package configuration and runtime resolver hooks are not executed.

The graph retains import specifiers even when an adapter initially regards them
as external. Resolution decides which recorded paths are internal. It does not
invent an edge to an unrelated file with a matching basename. The same resolver
serves blast radius, usage importers and classification. Python relative levels
and `from package import module` retain their module meaning.

`compute_fan_in(target_dir, perimeter=None, manifest=None)` counts distinct
importing files, excluding self-imports. `classify_directory` shares one manifest
and graph. File analysis exposes `imported_by_count` without `--find-usages` and
independently of its optional five-symbol usage limit.

The existing classifier uses categories, not a numeric importance score. Its
fan-in thresholds are eight importers for high-complexity verification and
fifteen for critical classification, alongside the existing critical-pattern
rules. Earlier drafts described nonexistent `importance_score`, `typedef`,
`field` and `parent_class` APIs. Those names are not requirements to create a
second scoring or structural model.

## Verification contract

Behavioral fixtures cover SQL/PLSQL comments and literals, JS callback results,
thread isolation and cache invalidation, native call attribution, nested scopes,
configuration inheritance/precedence, workspace exports, source confinement,
Python relatives, shared usage graphs and fan-in without usage lookup.

Run the complete repository suite on an LF candidate with all engine changes.
Run native parser fixtures locally when grammars are available and record skips
when they are not. Keep structural host rendering evidence separate from live
host execution. All five generated packages must reproduce, repository linters
and documentation parity must pass, versions must increase, and an independent
review must resolve material findings before publication. Preserve foreign edits.

## Follow-on phases

### Step 6: Portable references and import graph diagnostics

The [portable semantic increment](2026-10-15-codebase-map-portable-semantics.md)
implements source-bound Python and native JS/TS references and callsite positions,
conservative direct declaration links, iterative strongly connected cycle
components, reverse import reachability and stdlib PageRank. It reuses the parsed
trees and resolved import graph. Parameters and convergence remain visible;
centrality does not automatically establish product criticality or runtime impact.

The implemented owner is `dependency_graph.py`, not a second classifier score.
File and change reports expose the diagnostics while retaining the existing
one-hop affected-file and recommendation rules. K-core, host-native graph
integration, embedding retrieval and compiler type inference remain outside this
increment. Native syntax metadata has a measured size and extraction-time cost,
documented with its sample limitations in the new plan and engine documentation.

### Step 7: Additional `tree-sitter` language adapters (Go, C#, Kotlin, PHP, Ruby)

**Why:** `tree-sitter-language-pack` already ships grammars for Go, C#, Kotlin, PHP, and Ruby. Adding lightweight adapters under `languages/` using `_treesitter.py` (`parse_tree`, `syntax_error_notes`, `mask_comments`) extends first-class structural coverage without adding new dependencies.

Planned tasks:
- [ ] Add `languages/go.py`, `languages/csharp.py`, and `languages/kotlin.py` adapters wired into `languages/__init__.py`, `ast_parser.py`, `classifier.py`, and `snapshot.py:PARSER_PROFILES`.
- [ ] Add fixture tests for each new adapter in `tests/test_xray_scripts.py`.

### Step 8: Local semantic embeddings & hybrid search (Deferred / Optional)

**Why deferred:** Adding a local embedding runtime (`fastembed` / ONNX Runtime / `sqlite-vec`) introduces binary dependencies, model download/caching lifecycle, and index warm-up latency. Inside Tri-Tech Code / OpenCode hosts, `codebase_search` and `codebase_context` already provide semantic vector retrieval. Keep `codebase-map` 100% deterministic and zero-model-dependency unless standalone CLI semantic search is explicitly requested.

If activated in the future:
- [ ] Provide an optional, opt-in `semantic_index.py` helper backed by `fastembed` (ONNX) + SQLite storing symbol docstring/signature vectors under `.codebase-map/runs/<id>/snapshot/vectors.sqlite`.
- [ ] Never require embeddings for `snapshot.py`, `ast_parser.py`, or any mandatory gate.
