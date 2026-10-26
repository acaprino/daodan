---
name: map-method
description: >
  Static mapping and standalone navigation of existing map evidence.
  TRIGGER WHEN: project questions, unfamiliar code, debugging, feature work, refactors, reviews or documentation. Consult map evidence before broad exploration. Loading the skill starts no analysis or refresh. Verify claims against source; search the repository without usable maps.
  DO NOT TRIGGER WHEN: no project code or documentation.
---

# Codebase Map Analysis Skill

## Language Support

| Language | Extensions | Structural extraction | Comment syntax |
|---|---|---|---|
| Python | `.py`, `.pyi` | stdlib `ast` (always available) | `#` line + docstrings |
| Java | `.java` | tree-sitter (preferred) or regex | `//`, `/* */`, Javadoc `/** */` |
| JavaScript | `.js`, `.mjs`, `.cjs`, `.jsx` | tree-sitter (preferred) or regex | `//`, `/* */`, JSDoc `/** */` |
| TypeScript | `.ts`, `.tsx`, `.mts`, `.cts` | tree-sitter (preferred) or regex; adds interfaces, enums, type aliases | `//`, `/* */`, JSDoc `/** */` |
| SQL | `.sql`, `.ddl`, `.dml` | regex DDL (tables, views, indexes, sequences, types, functions, procedures, triggers) | `--`, `/* */` |
| PL/SQL (Oracle) | `.pks`, `.pkb`, `.plsql`, `.pls`, `.pck`, `.prc`, `.fnc`, `.trg` | regex (packages, package bodies, type bodies, cursors, exceptions, %TYPE/%ROWTYPE references) | `--`, `/* */` |
| Rust | `.rs` | tree-sitter (preferred) or regex; structs, enums, traits, impls (with `Trait for Type` naming), mods, unions, type aliases | `//`, `/* */`, rustdoc `///` / `//!` / `/** */` / `/*! */` |
| Go | `.go` | tree-sitter (preferred) or regex; functions, methods, types | `//`, `/* */` |
| CSS, SCSS, LESS | `.css`, `.scss`, `.less` | stdlib tokenizer, never tree-sitter; one symbol per applied rule (flattened selector within enclosing at-rules); top-level at-rules, Sass/LESS variables, mixins, Sass functions; `@import`/`@use`/`@forward`; Tailwind `@apply` layout utilities expanded as declarations | `/* */`, and `//` outside plain CSS |

`.sql` is disambiguated against PL/SQL by Oracle-specific content markers (`languages/__init__.py`); `plpgsql` stays SQL.

## How This Skill Is Invoked

`references/entry-analyze.md` dispatches isolated `codebase-map:map-analyst`;
`references/entry-team-analyze.md` uses isolated partition workers. Entries own
`.codebase-map/` publication (`references/run.md`).
Loading `codebase-map:map-method` starts no analysis or run.

## Load map

| Unit | Holds | Loaded by |
|---|---|---|
| `references/migration.md` | legacy root migration and bound-path resolution | legacy archives, redirects, bindings or blocked preflight |
| `references/run.md` | classic/team runs, concurrency and perimeter | whoever owns the run |
| `references/snapshot.md` | snapshot ownership, scope, write, diff, carry and check commands | whoever owns the run's snapshot |
| `references/update.md` | incremental re-derivation | analyst on accepted updates |
| `references/deepen.md` | cards an area lacks | area deepening; analyst in `cards` mode |
| `references/evidence.md` | evidence, forbidden files, commands, source reading, classification; maintained-document verification separately | every phase worker and every consumer that reads source |
| `references/reading.md` | analysis reading | every consumer of a bound analysis |
| `references/standalone.md` | shared read-only map discovery, navigation, impact and fallback | every map consumer, including analysis and composed workflows |
| `references/phase-0.md` | Phase 0 knowledge discovery | analyst and team entry |
| `references/phases-1-2.md` | Phase 1 structure, Phase 2 interfaces | phase 1 and 2 workers |
| `references/phases-3-4.md` | Phase 3 flows, Phase 4 semantics and the analysis loop | phase 3 and 4 workers |
| `references/phases-5-6.md` | Phase 5 patterns and risks, Phase 6 documentation health | phase 5 and 6 workers |
| `references/phase-7.md` | Phase 7 final report | analyst and synthesizer |

## Consumer map

- Every map consumer, including analyze and composed workflows: `references/standalone.md` and `references/reading.md` section `Task views`. Ordinary standalone source reads add `references/evidence.md` sections `CRITICAL PRINCIPLE: EVIDENCE-ANCHORED OUTPUT` and `Forbidden Files`; composed consumers keep their own authorized evidence and producer procedures.
- Forbidden files: `references/evidence.md`.
- Consuming a bound analysis: `references/reading.md`, plus `references/evidence.md` before Maintained documentation for source. For durable-document verification, read its Maintained documentation section. Snapshot verification/refresh uses `references/snapshot.md` before Prerequisites.
- Run analyses through `references/entry-analyze.md`; composed callers declare isolated `codebase-map/map-analyst`.

## Team bindings

Use canonical skeletons in owned output. Put partition identity below titles, never in headings. Workers and synthesizers do not update classic state.

## Method loads

Conditional reads: methodology, patterns, comments; migration for legacy roots, redirects, bindings or blocked preflight. Follow nested loads; count their union with core reads.

| Resource | Sections | When |
|---|---|---|
| `references/AI_ANALYSIS_METHODOLOGY.md` | all | methodology |
| `references/SEMANTIC_PATTERNS.md` | all | patterns |
| `references/ANTIREZ_COMMENTING_STANDARDS.md` | all | comments |
| `references/migration.md` | all | migration |

## Resources

Python >= 3.10 scripts: `${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/`.
Language Support above applies throughout.

- `ast_parser.py`: structural extraction dispatcher.
- `analyze_file.py`: classification/structure/usages; workflows reuse `--snapshot`.
- `classifier.py`: language-aware criticality.
- `usage_finder.py`: cross-file symbol usages.
- `comment_rewriter.py`: multi-language comment analysis.
- `rewrite_comments.py`: comment quality CLI: scan/analyze/rewrite/report.
- `doc_review.py`: documentation maintenance (Phase 6).
- `migrate_root.py`: project-bound legacy migration; historical-path resolution.
- `snapshot.py`: scope, SQLite snapshots (explicit JSON), run resolution, incremental changes.
- `source_reader.py`: manifest graphs, outlines and validated source blocks.
- MCP and Code Mode: `references/mcp.md`; `mcp_server.py`, `mcp_service.py`, `code_mode.py`, `code_mode_runner.js`.
- `tree_scope.py`: shared Git, dot-directory and dependency/build perimeter.
- `cascade_scan.py`: global stylesheet layout risks, cascade overrides and screen rules (Phase 5).
- `languages/`: per-language adapters listed above.
- `requirements.txt`: optional tree-sitter and tree-sitter-language-pack dependencies.
