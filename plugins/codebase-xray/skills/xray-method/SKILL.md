---
name: xray-method
description: >
  X-ray method: mechanical structure extraction fused with semantic reading into a ground-truth account of WHAT, WHY, HOW and CONSEQUENCES. Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust, CSS/SCSS/LESS.
  TRIGGER WHEN: encountering an unfamiliar codebase, needing pre-review technical context, before a major refactor, or when documentation is stale or missing.
  DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use /project-knowledge:guide), a public-facing README, or a review verdict (senior-review consumes this output instead).
---

# Codebase X-Ray Analysis Skill

## Overview

This skill combines **mechanical structure extraction** with **semantic reading** to produce comprehensive codebase documentation. It captures:

- **WHAT** the code does (structure, functions, classes)
- **WHY** it exists (business purpose, design decisions)
- **HOW** it integrates (dependencies, contracts, flows)
- **CONSEQUENCES** of changes (side effects, failure modes)

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
| CSS, SCSS, LESS | `.css`, `.scss`, `.less` | stdlib tokenizer, never tree-sitter: one symbol per applied rule, named by its flattened selector inside its enclosing at-rules; top-level at-rules and Sass or LESS variables; mixins and Sass functions; `@import` / `@use` / `@forward`; Tailwind `@apply` layout utilities read as the declarations they inline | `/* */`, and `//` outside plain CSS |

`.sql` files are disambiguated against PL/SQL by inspecting content for Oracle-specific markers (`CREATE OR REPLACE PACKAGE`, `DBMS_OUTPUT`, `%TYPE`, `%ROWTYPE`, `UTL_FILE`, `PRAGMA AUTONOMOUS`, etc.). PostgreSQL `plpgsql` is correctly classified as SQL.

## How This Skill Is Invoked

This skill is the method; the commands apply it. `/codebase-xray:analyze` runs every phase inline in one context, and `/codebase-xray:team-analyze` partitions the target and dispatches the phases per partition to isolated workers, which read this skill directly. Both manage their state automatically under `.codebase-xray/` using the concurrent runs model in `references/run.md`.

The skill's own name is `codebase-xray:xray-method`. `codebase-xray:analyze` names the command, and only the command: the two used to share a name, and on a host that lists both under one identifier the command shadowed the skill.

This file is a router. The method lives in the units below, each loaded when its work starts, never all at once by default.

## Load map

| Unit | Holds | Loaded by |
|---|---|---|
| `references/run.md` | concurrent runs model, perimeter, classic or team | whoever owns the run |
| `references/snapshot.md` | snapshot write, scope count, diff, carry and check commands | whoever owns the run's snapshot |
| `references/update.md` | incremental updates and the incremental depth procedure | a run accepted as an update |
| `references/evidence.md` | evidence-anchored output, forbidden files, prerequisites, script commands, source reading, file classification | every phase worker and every consumer that reads source |
| `references/reading.md` | how to read a finished analysis | every consumer of a bound analysis |
| `references/phase-0.md` | Phase 0, project knowledge discovery | the run owner, before Phase 1 |
| `references/phases-1-2.md` | Phase 1 structure, Phase 2 interfaces | phase 1 and 2 workers |
| `references/phases-3-4.md` | Phase 3 flows, Phase 4 semantics | phase 3 and 4 workers |
| `references/phases-5-6.md` | Phase 5 patterns and risks, Phase 6 documentation health | phase 5 and 6 workers |
| `references/phase-7.md` | Phase 7 final report | the run owner |

## Consumer map

- Forbidden files: `references/evidence.md`.
- Consuming a bound analysis: `references/reading.md`, plus `references/evidence.md` to read source from its snapshot.
- Running an analysis: the `codebase-xray:analyze` workflow, never this skill alone. Loading the method runs no phase and creates no run directory.

## References

- `references/analysis-templates.md` - Verification trust model, temporal purity principle, documentation status markers, comment classification, maintenance workflows
- `templates/semantic_analysis.md` - AI-powered per-file analysis template
- `templates/analysis_report.md` - Module-level report template

Read on demand, never by default:

- `references/AI_ANALYSIS_METHODOLOGY.md` - Complete analysis methodology
- `references/SEMANTIC_PATTERNS.md` - Pattern recognition guide
- `references/ANTIREZ_COMMENTING_STANDARDS.md` - Comment taxonomy

## Resources

- **Scripts**: `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/` - analysis tools (Python >= 3.10 runtime, multi-language targets)
  - `ast_parser.py` - structural extraction dispatcher
  - `analyze_file.py` - per-file CLI (classification + structure + usages)
  - `classifier.py` - language-aware criticality classifier
  - `usage_finder.py` - cross-file symbol usage finder (multi-language extensions)
  - `comment_rewriter.py` - multi-language comment analysis engine
  - `rewrite_comments.py` - comment quality CLI (scan / analyze / rewrite / report)
  - `doc_review.py` - documentation maintenance (Phase 6)
  - `snapshot.py` - scope count, structural snapshots and incremental change sets
  - `source_reader.py` - snapshot outline and validated source blocks with shared context
  - `tree_scope.py` - the perimeter every tree-walking script applies: nothing Git ignores, no dot directory, no dependency or build output
  - `cascade_scan.py` - stylesheet rules with global reach that can break a screen, with the rules each can override in cascade order, screen-level rules first (Phase 5)
  - `languages/` - per-language adapters (Python `ast`, Java/JS/TS/Rust via tree-sitter or regex, SQL/PL-SQL regex, CSS/SCSS/LESS stdlib tokenizer)
    - `base.py` - shared dataclasses + `LanguageAdapter` Protocol
    - `__init__.py` - extension dispatch (`detect_language`, `get_adapter`)
    - `comments.py` - per-language comment lexer (includes rustdoc post-processor)
    - `_treesitter.py` - optional tree-sitter loader with fallbacks
    - `python.py`, `java.py`, `javascript.py`, `typescript.py`, `sql.py`, `plsql.py`, `rust.py`, `stylesheet.py`
  - `requirements.txt` - optional dependencies (tree-sitter + tree-sitter-language-pack)
