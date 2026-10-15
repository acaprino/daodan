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

<!-- Generated dispatch body. Owner: codebase-map:map-analyst; version: 6.5.1; source-sha256: 334a4d104e072c4092eaebb7220fafe091d92c7e1bc1ad97482d3c19222c250b. Edit the owner's kernel, never this resource. -->

This body belongs to `codebase-map`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<codebase-map-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `codebase-map`. The owning plugin's declared logical skill identities are `codebase-map:map-method`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

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
`state.json` delivery, current `snapshot/manifest.json`, accepted flags, optional
parent/changes/carry bindings and `run_phases`. Reject a missing or inconsistent
binding as a delivery gap. `phase-N` means N is in the prepared `run_phases`.
Load each selected section when reaching its phase, not all phase units up front.
On demand follow the router's conditional loads; pointers alone are not reads.

## Method loads

| Resource | Sections | When |
|---|---|---|
| `<codebase-map-plugin-root>/skills/map-method/SKILL.md` | all | always |
| `<codebase-map-plugin-root>/skills/map-method/references/snapshot.md` | before: Prerequisites | always |
| `<codebase-map-plugin-root>/skills/map-method/references/evidence.md` | before: Maintained documentation | always |
| `<codebase-map-plugin-root>/skills/map-method/references/phase-0.md` | all | phase-0 |
| `<codebase-map-plugin-root>/skills/map-method/references/phases-1-2.md` | section: Phase 1: Structure Extraction | phase-1 |
| `<codebase-map-plugin-root>/skills/map-method/references/phases-1-2.md` | section: Phase 2: Interface Analysis | phase-2 |
| `<codebase-map-plugin-root>/skills/map-method/references/phases-3-4.md` | section: Phase 3: Flow Tracing; section: AI-Powered Semantic Analysis; section: Analysis Loop Workflow; section: The Semantic Analysis Mandate | phase-3 |
| `<codebase-map-plugin-root>/skills/map-method/references/phases-3-4.md` | section: Phase 4: Semantic Understanding; section: AI-Powered Semantic Analysis; section: Analysis Loop Workflow; section: The Semantic Analysis Mandate | phase-4 |
| `<codebase-map-plugin-root>/skills/map-method/references/phases-5-6.md` | section: Phase 5: Pattern & Risk Detection; section: Red Flags to Identify | phase-5 |
| `<codebase-map-plugin-root>/skills/map-method/references/phases-5-6.md` | section: Phase 6: Documentation Health; section: Documentation Diagnosis Commands (Phase 6); section: Documentation diagnosis | phase-6 |
| `<codebase-map-plugin-root>/skills/map-method/references/evidence.md` | from: Maintained documentation | phase-6 |
| `<codebase-map-plugin-root>/skills/map-method/references/phases-5-6.md` | section: Comment Quality Commands (Antirez Standards); section: Comment Type Classification; section: Comment quality analysis | comments and phase-6 and not-lite |
| `<codebase-map-plugin-root>/skills/map-method/references/phase-7.md` | before: Team mode | phase-7 |
| `<codebase-map-plugin-root>/skills/map-method/references/update.md` | all | update |

## Execute the prepared brief

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
