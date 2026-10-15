# Codebase Map Analysis

## Coordinator boundary

Resolve the run, present scope, dispatch one isolated `codebase-map:map-analyst`,
verify its delivery and publish only when the gate permits it. Do not read analyzed
source or execute phase procedures in this context. Helpers may inventory and
parse it mechanically. If required isolation is unavailable, stop with that
capability gap. Honor existing authorization; ask only for an unresolved choice
or an explicitly requested approval. Questions stay in this answerable context.
Never enter plan mode or apply changes to analyzed source.

## Method loads

Read these resources and their selected nested loads in the coordinator context.
The analyst has its own load contract; do not load its phase units here.

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/SKILL.md` | before: Method loads; section: Resources | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/run.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/snapshot.md` | before: Prerequisites | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/migration.md` | all | migration |

## Preflight

### Resolve controls and run identity

Run the project-bound migration in `references/run.md` before root lookup.
Parse target and existing flags (`critical`, `comments`, `docs_only`, `phase`,
`depth`), `--run-name`, `--update` and `--no-update`. Additional controls:

- `--phase N`, N from 1 to 6: Phase 0 plus N only. Refuse `--phase 7`; a final
  report needs the phase files it summarizes. Never publish a single-phase run.
- `--docs-only`: Phase 0 plus 6 only, never published.
- `--stop-after N`, N from 1 to 6: stop this invocation after N, retaining the
  run's complete mode obligations. Later artifacts are `not_yet_produced`, not
  skipped or delivery gaps. Refuse it with single-phase or docs-only controls.
- `--resume-from [N]`: require `--run-name` identifying the exact interrupted
  run. Resume from N (1 to 7), or the gate's `first_incomplete_phase`. Keep the
  same mode and flags; a different mode or flags require a new run. The stop
  bounds an invocation, so resume drops it.

Use `references/run.md` for registration and collision handling. On resume select
that existing directory without a collision suffix; require classic mode,
matching normalized project/target, state and manifest. Do not overwrite its
state or silently choose another active run. Show other active runs and start
alongside when the user requested a new run. Offer legacy-layout migration when
the run reference identifies it. Cancel leaves the shared mirror untouched.

For a fresh run initialize `state.json` with run id, normalized target,
`mode: "classic"`, `status: "in_progress"`, effective flags, timestamps,
`current_phase: 0`, empty completed phases/files, and real parent/incremental
fields (null for a full run). Do not put stop or resume in immutable mode flags.
Invoke `snapshot.py register $RUN_DIR`; repeat after resolving parent lineage.

### Resolve an update base

Skip parent detection with `--no-update`, on resume, or for docs/single-phase
requests. Otherwise use `latest_completed` only when its recorded target matches,
its mode is classic and its manifest exists. Team output, including `08`, is never
carried into an ordinary classic update. `--update` without a usable parent is
an error; name the failed binding and explain that a full run creates a base.

A composed caller may supply an exact `parent_run` binding instead of
`latest_completed`. Validate its project/root, target, common flags and manifest.
A partial or team parent is usable only for a caller's bounded `--stop-after 4`
request when the gate confirms its declared `01` through `04` deliveries. Carry
only those canonical files into a new classic child by setting its
`parent_phases: [1,2,3,4]`; never carry `08`, merge run
modes or resume a team run as classic. Absent later files remain future produced
obligations, never missing inherited artifacts. Keep normal completed classic
parent requirements for unbound parent selection.

With a candidate, run the verified diff from `references/snapshot.md`, passing
this run's effective flags. Read only metadata and recommendation. Show modified,
added and removed files/symbols, affected claims by phase, blast radius and affected
files versus inventory. Parent commit/age come from the parent's state; the
change set's git field describes the current tree. A recommendation is advice:
resolve incremental versus full from the request or existing answers, and ask
when undecided. With `full`, show every reason and retain both choices. With
`none`, offer the supported bound parent or a full analysis. Returning the parent
without source reading needs no new analysis; preserve its snapshot.

### Present the scope

Use `snapshot.py scope` from the snapshot unit. Show target, run id, parent,
active run count, file/language totals, selected flags and expected phases.
Always repeat the scope's not-analyzed dot directories (names or outermost names
and count), ignored paths and ignore status (`applied` or `unavailable`). A user
can name an excluded directory as a target.

Fresh choices are full analysis, one phase, quick scan (`--stop-after 2`), lite
or cancel. Full selects 0 through 7; lite selects 0, 1, 2, 5 and condensed 7.
Docs-only selects 0 and 6. Single-phase selects 0 and N. The delivery helper,
not a second prompt table, decides produced/inherited/skipped artifacts. For a
large, multi-language or multi-workspace scope recommend the team entry before
dispatch and resolve that choice. A classic run stays one isolated context.

Use a permitted input tool for an unresolved decision. If unavailable, ask the
actual question in chat and wait; elapsed time is no answer. Do not pause merely
because the workflow has a scope checkpoint.

### Prepare the binding

After scope is settled, write the initial current snapshot and copy its own `git`
field to this run's state, following `references/snapshot.md`. Reuse the verified
same-target parent manifest even for a selected full analysis; preserve the
parent. On an accepted update record actual parent id, base snapshot time and
incremental counts, then run `carry` before `prepare`. This lets the helper
classify unaffected files with the carry record's provenance. It never inherits
missing files. Full mode leaves parent/incremental null.

Invoke `prepare $RUN_DIR` from the snapshot unit.

Pass applicable `--phase N` or `--stop-after N` controls. Require successful
preparation; its `delivery` fixes effective mode/flags, artifacts and `run_phases`.
Keep skipped reasons and inherited parent/carry provenance intact. The
coordinator owns this first snapshot; ownership transfers to the analyst for
refresh during analysis. Do not repeat an initial snapshot write.

On resume first check the existing run, then verify its manifest against the
current target using `diff --verify` in `$RUN_DIR/resume-check/`. If source or
parser identity changed, do not retain earlier artifacts as current: report
the mismatch and resolve a new full/update run. With unchanged inputs invoke
`prepare $RUN_DIR --resume-from [N] --run-name <exact-id>`; pass supplied
mode/flags only for equality validation. Earlier confirmed artifacts acquire
same-run provenance; the helper selects the first incomplete produced phase
when N was omitted. Never fresh-prepare over a resume declaration.

## Isolated analysis

Dispatch the required `codebase-map:map-analyst` role with exact project root,
target, run id/directory, prepared state/delivery, manifest, accepted flags,
parent/changes/carry bindings and `run_phases`. State the exclusive run write
root and snapshot handoff. The analyst asks nothing, reads source, executes only
declared phases and reports paths plus its check result.

Wait for an artifact delivery. An empty response, idle worker or stopped turn
does not deliver a report. Verify native paths and rerun the single gate:

Invoke `check $RUN_DIR --json` from the snapshot unit.

Use `missing`, `empty`, `unexpected`, `invalid_inherited`, `stale` and
`undocumented_added` to identify gaps. Recover only missing produced work;
inherited/skipped artifacts never become incomplete phases. Re-dispatch from
`first_incomplete_phase` after a prepared same-mode resume, or name the blocker.
Do not restart successful phases or replace parent evidence.

## Publish and completion

For a delivered stop record partial status and pending `not_yet_produced`
artifacts. Docs-only and single-phase results stay in the run. Report their
exact paths, coverage and continuation; never replace the shared mirror.

For a complete publishing mode, only this coordinator loads `human-view.md`
when a view is requested or useful. Verify native output and every requested
view before completion; a requested view failure keeps the run open. Then
require `complete` and `may_publish` from the gate and invoke `publish $RUN_DIR`
from the snapshot unit.

The helper replaces the whole mirror and updates the registry as specified in
`references/run.md`; never copy just the files that happen to exist. On partial,
failed or aborted delivery, record recoverable state and invoke
`snapshot.py unregister $RUN_DIR`; the mirror stays untouched.

Present exact run directory, parent and publication/partial status, produced
files, inventory/read-in-depth/runtime coverage (runtime: none unless supplied),
risks and documentation gaps. Updates link `changes.md` and count confirmed,
revised, retired and added claims. Derive a prioritized action plan from cited
findings and offer development, readability or knowledge work as a separate task.
Specific downstream invocations retain this run and snapshot; only an explicitly
latest-state consumer reads the mutable mirror.
