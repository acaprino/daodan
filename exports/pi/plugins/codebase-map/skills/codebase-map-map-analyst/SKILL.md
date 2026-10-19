---
name: codebase-map-map-analyst
description: 'Owns the declared classic Codebase Map phases in one isolated context, reading the bound snapshot and writing only its runs analysis artifacts. TRIGGER WHEN: dispatched by an analysis coordinator with a prepared classic run and resolved scope.'
disable-model-invocation: true
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

Declared role operation allowlist: read files; discover file paths; search file contents; execute shell commands; create or overwrite files. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.

# Classic analysis owner

## Boundaries

Ask no questions. The coordinator resolves scope and flags before dispatch.
Never edit analyzed source, including comments or documentation. Write only
inside the exact `$RUN_DIR` in the brief; preserve parent runs and inherited
artifacts. Never publish, register runs, choose modes, or generate human views.
The coordinator owns completion, requested views and the shared mirror.

## Inputs and method loads

Require the project root, normalized target, run id/directory, prepared
`state.json` delivery, current snapshot path from `snapshot.py resolve <run-dir>`, accepted flags, optional
parent/changes/carry bindings and `run_phases`. Reject a missing or inconsistent
binding as a delivery gap. `phase-N` means N is in the prepared `run_phases`.
Load each selected section when reaching its phase, not all phase units up front.
On demand follow the router's conditional loads; pointers alone are not reads.

## Method loads

| Resource | Sections | When |
|---|---|---|
| `<plugin-root>/skills/map-method/SKILL.md` | all | always |
| `<plugin-root>/skills/map-method/references/snapshot.md` | before: Prerequisites | always |
| `<plugin-root>/skills/map-method/references/evidence.md` | before: Maintained documentation | always |
| `<plugin-root>/skills/map-method/references/phase-0.md` | all | phase-0 |
| `<plugin-root>/skills/map-method/references/phases-1-2.md` | section: Phase 1: Structure Extraction | phase-1 |
| `<plugin-root>/skills/map-method/references/phases-1-2.md` | section: Phase 2: Interface Analysis | phase-2 |
| `<plugin-root>/skills/map-method/references/phases-3-4.md` | section: Phase 3: Flow Tracing; section: AI-Powered Semantic Analysis; section: Analysis Loop Workflow; section: The Semantic Analysis Mandate | phase-3 |
| `<plugin-root>/skills/map-method/references/phases-3-4.md` | section: Phase 4: Semantic Understanding; section: AI-Powered Semantic Analysis; section: Analysis Loop Workflow; section: The Semantic Analysis Mandate | phase-4 |
| `<plugin-root>/skills/map-method/references/phases-5-6.md` | section: Phase 5: Pattern & Risk Detection; section: Red Flags to Identify | phase-5 |
| `<plugin-root>/skills/map-method/references/phases-5-6.md` | section: Phase 6: Documentation Health; section: Documentation Diagnosis Commands (Phase 6); section: Documentation diagnosis | phase-6 |
| `<plugin-root>/skills/map-method/references/evidence.md` | from: Maintained documentation | phase-6 |
| `<plugin-root>/skills/map-method/references/phases-5-6.md` | section: Comment Quality Commands (Antirez Standards); section: Comment Type Classification; section: Comment quality analysis | comments and phase-6 and not-lite |
| `<plugin-root>/skills/map-method/references/phase-7.md` | before: Team mode | phase-7 |
| `<plugin-root>/skills/map-method/references/update.md` | all | update |
| `<plugin-root>/skills/map-method/references/deepen.md` | section: Analyst in cards mode | cards |

## Execute the prepared brief

A brief with mode `cards` binds an existing run's manifest and a symbol list
instead of `run_phases`: write their cards as `references/deepen.md` directs
and deliver the upsert result; the steps below are for analysis runs.

1. Read state and snapshot binding. The coordinator wrote the initial manifest;
   do not repeat it. Become this run's snapshot owner. On changed bytes or parser
   mismatch, refresh only this manifest with `snapshot.py write --reuse`.
   Report invalidated delivery and affected earlier claims; never retain them as
   current. Resume requires a newly verified coordinator brief.
2. Execute `run_phases` in numerical order. Follow each phase unit's procedure
   and canonical skeleton. Phase 0 writes both knowledge files whenever selected.
   Read existing `01-structure.md` and `02-interfaces.md` before later full-run
   phases. A single phase derives its prerequisites from source and the snapshot;
   never invent or write earlier phase files. Inherited files remain untouched.
3. For an accepted update follow `references/update.md`, including re-derivation,
   retirement, added symbols and the completion sections of `changes.md`. The
   coordinator already carried the parent before preparing delivery. Re-derive
   only declared produced phases; do not reread unaffected inherited phases.
   A stop leaves later marked claims pending for resume.
4. Lite phases are those the brief selected. In Phase 5 omit detailed state
   machine/flow diagrams for non-critical files. The condensed Phase 7 covers
   structure, interfaces and risks; omit Critical Paths, Design Insights, Key
   Process Diagrams and Documentation vs Reality. Keep all three coverage figures.
5. With comments, full depth and selected Phase 6, write `comment_health.md` and record the
   proposed changes in `06-documentation.md`. Applying them belongs to a separately
   authorized development or readability task.
6. Write each phase file when that phase finishes. Update only this run's
   `current_phase`, `completed_phases`, `files_created`, reading ledger and update
   counts. Leave `delivery` declarations unchanged. Record stop or failure as
   partial with the blocker and last delivered phase; never mark the run complete.

## Delivery

Run the snapshot unit's `check $RUN_DIR --json`. Deliver the exact run id,
directory and manifest, produced artifact paths, check result and first
incomplete phase, with any refresh or unresolved evidence gap. A stopped turn
or empty response is not a result. Missing required artifacts keep delivery open;
finish them or name the concrete blocker. The coordinator verifies the files
and decides recovery, completion and publication.
