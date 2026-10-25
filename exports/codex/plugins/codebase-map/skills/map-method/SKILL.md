---
name: map-method
description: >
  Static mapping and standalone navigation of existing map evidence.
  TRIGGER WHEN: project questions, unfamiliar code, debugging, feature work, refactors, reviews or documentation. Consult map evidence before broad exploration. Loading the skill starts no analysis or refresh. Verify claims against source; search the repository without usable maps.
  DO NOT TRIGGER WHEN: no project code or documentation.
---

> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.
> This plugin declares an MCP server, `codebase-map`, started with `uv run --no-config --no-project --script <plugin-root>/skills/map-method/scripts/mcp_server.py`. This host does not start a plugin-declared MCP server on its own. Before calling this server's tools, register that command under that name in the host's MCP configuration and verify the connection.

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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
| `references/standalone.md` | shared read-only map discovery, navigation, impact and fallback | every map consumer, including analysis and composed workflows |
| `references/phase-0.md` | Phase 0, project knowledge discovery | analyst and team entry |
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

Python >= 3.10 scripts: `<plugin-root>/skills/map-method/scripts/`.
Language Support above applies throughout.

- `ast_parser.py`: structural extraction dispatcher.
- `analyze_file.py`: classification, structure, usages; workflows reuse `--snapshot`.
- `classifier.py`: language-aware criticality metrics.
- `usage_finder.py`: cross-file symbol usages.
- `comment_rewriter.py`: comment analysis engine.
- `rewrite_comments.py`: comment scan/analyze/rewrite/report CLI.
- `doc_review.py`: documentation maintenance (Phase 6).
- `migrate_root.py`: project-bound legacy migration; historical paths.
- `snapshot.py`: scope, snapshots, runs, incremental changes; SQLite, explicit JSON.
- `source_reader.py`: manifest graphs, outlines, validated source blocks.
- `tree_scope.py`: Git, dot-directory and dependency/build perimeter.
- `cascade_scan.py`: global layout risks, cascade overrides, screen rules (Phase 5).
- `languages/`: language adapters.
- `requirements.txt`: optional tree-sitter and tree-sitter-language-pack.
