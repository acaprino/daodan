---
name: xray-method
description: >
  X-ray method: mechanical structure extraction fused with semantic reading into a ground-truth account of WHAT, WHY, HOW and CONSEQUENCES. Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust, CSS/SCSS/LESS.
  TRIGGER WHEN: encountering an unfamiliar codebase, needing pre-review technical context, before a major refactor, or when documentation is stale or missing.
  DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use /project-knowledge:guide), a public-facing README, or a review verdict (senior-review consumes this output instead).
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Codebase X-Ray Analysis Skill

## Overview

The analysis establishes:

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

`/codebase-xray:analyze` runs phases inline; `/codebase-xray:team-analyze` dispatches isolated partition workers that read this method. Both own `.codebase-xray/` run state (`references/run.md`).

The method is `codebase-xray:xray-method`; `codebase-xray:analyze` names only its workflow.

## Load map

| Unit | Holds | Loaded by |
|---|---|---|
| `references/run.md` | concurrent runs model, perimeter, classic or team | whoever owns the run |
| `references/snapshot.md` | snapshot write, scope count, diff, carry, check commands and owner prerequisites | whoever owns the run's snapshot |
| `references/update.md` | incremental updates and the incremental depth procedure | a run accepted as an update |
| `references/evidence.md` | evidence-anchored output, forbidden files, script commands, source reading, file classification; maintained-document verification is separate | every phase worker and every consumer that reads source |
| `references/reading.md` | how to read a finished analysis | every consumer of a bound analysis |
| `references/phase-0.md` | Phase 0, project knowledge discovery | the run owner, before Phase 1 |
| `references/phases-1-2.md` | Phase 1 structure, Phase 2 interfaces | phase 1 and 2 workers |
| `references/phases-3-4.md` | Phase 3 flows, Phase 4 semantics and the analysis loop | phase 3 and 4 workers |
| `references/phases-5-6.md` | Phase 5 patterns and risks, Phase 6 documentation health | phase 5 and 6 workers |
| `references/phase-7.md` | Phase 7 final report | the run owner |

## Consumer map

- Forbidden files: `references/evidence.md`.
- Consuming a bound analysis: `references/reading.md`, plus `references/evidence.md` before Maintained documentation for source. For durable-document verification, read its Maintained documentation section. Snapshot verification/refresh uses `references/snapshot.md` before Prerequisites.
- Running an analysis: the `codebase-xray:analyze` workflow, never this skill alone. Loading the method runs no phase and creates no run directory.

## Team bindings

Apply the common skeleton to the owned output directory. Partition files state their partition below the title; common headings never gain scope qualifiers. Classic state updates do not apply to workers or the synthesizer.

## References

The phase units own the canonical skeletons.

## Method loads

Optional additions to the entry's core reads. Enable each only when its guidance is needed: methodology for deeper analysis, patterns for recognition, comments for taxonomy. Follow declared nested reads; count their union with core reads.

| Resource | Sections | When |
|---|---|---|
| `references/AI_ANALYSIS_METHODOLOGY.md` | all | methodology |
| `references/SEMANTIC_PATTERNS.md` | all | patterns |
| `references/ANTIREZ_COMMENTING_STANDARDS.md` | all | comments |

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
