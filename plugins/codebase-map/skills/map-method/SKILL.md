---
name: map-method
description: >
  Static codebase mapping: structure, purpose, integrations and change consequences. Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust, Go, CSS/SCSS/LESS.
  TRIGGER WHEN: unfamiliar codebases, pre-review context, major refactors, or stale documentation.
  DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use /daodan:write-docs), a public-facing README, or a review verdict (senior-review consumes this output instead).
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
| CSS, SCSS, LESS | `.css`, `.scss`, `.less` | stdlib tokenizer, never tree-sitter: one symbol per applied rule, named by its flattened selector inside its enclosing at-rules; top-level at-rules and Sass or LESS variables; mixins and Sass functions; `@import` / `@use` / `@forward`; Tailwind `@apply` layout utilities read as the declarations they inline | `/* */`, and `//` outside plain CSS |

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
| `references/run.md` | concurrent runs model, perimeter, classic or team | whoever owns the run |
| `references/snapshot.md` | snapshot write, scope count, diff, carry, check commands and owner prerequisites | whoever owns the run's snapshot |
| `references/update.md` | incremental re-derivation | analyst on accepted updates |
| `references/deepen.md` | cards an area lacks | area deepening; analyst in `cards` mode |
| `references/evidence.md` | evidence-anchored output, forbidden files, script commands, source reading, file classification; maintained-document verification is separate | every phase worker and every consumer that reads source |
| `references/reading.md` | how to read a finished analysis | every consumer of a bound analysis |
| `references/phase-0.md` | Phase 0, project knowledge discovery | analyst and team entry |
| `references/phases-1-2.md` | Phase 1 structure, Phase 2 interfaces | phase 1 and 2 workers |
| `references/phases-3-4.md` | Phase 3 flows, Phase 4 semantics and the analysis loop | phase 3 and 4 workers |
| `references/phases-5-6.md` | Phase 5 patterns and risks, Phase 6 documentation health | phase 5 and 6 workers |
| `references/phase-7.md` | Phase 7 final report | analyst and synthesizer |

## Consumer map

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

Scripts: `${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/` (Python >= 3.10; multi-language targets).

- `ast_parser.py`: structural extraction dispatcher.
- `analyze_file.py`: per-file classification/structure/usages; workflow calls reuse `--snapshot`.
- `classifier.py`: language-aware criticality classification.
- `usage_finder.py`: cross-file symbol usages across supported extensions.
- `comment_rewriter.py`: multi-language comment analysis engine.
- `rewrite_comments.py`: comment quality CLI: scan/analyze/rewrite/report.
- `doc_review.py`: documentation maintenance (Phase 6).
- `migrate_root.py`: project-bound legacy migration and historical path resolution.
- `snapshot.py`: scope, SQLite snapshots (JSON explicit), run resolution and incremental changes.
- `source_reader.py`: manifest graphs, outlines and validated source blocks.
- `tree_scope.py`: shared Git, dot-directory and dependency/build perimeter.
- `cascade_scan.py`: global stylesheet layout risks, cascade override candidates and screen rules (Phase 5).
- `languages/`: per-language adapters using the Language Support methods.
- `requirements.txt`: optional tree-sitter and tree-sitter-language-pack dependencies.
