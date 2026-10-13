---
description: >
  Run an X-ray: document WHAT, WHY, HOW and CONSEQUENCES into phased files, with concurrent-run support.
  TRIGGER WHEN: the user asks for a deep analysis of an unfamiliar codebase, pre-review context, or a structure-plus-semantics snapshot.
  DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use /project-knowledge:guide) or a shallow overview.
argument-hint: "<target path> [--critical] [--comments] [--docs-only] [--phase N] [--depth=lite|full] [--run-name <name>] [--update] [--no-update]"
---

# Codebase X-Ray Analysis

## CRITICAL RULES

1. **Execute phases in order.** Unless `--phase N` skips to a specific phase.
2. **Write output files.** Each phase produces a file in the run directory for context passing.
3. **Run isolation.** All writes go to `$RUN_DIR` until the publish step. Never write phase files to the `.codebase-xray/` root during analysis: concurrent runs share that root.
4. **Stop at checkpoints.** Confirm scope before starting analysis and before applying changes.
5. **Never enter plan mode.** Execute immediately.
6. **Code is ground truth.** Document what the code actually does, not what you think it should do.

## Method

## Method loads

Read named core sections by locating headings or fenced skeletons before bounded reads. On demand, add the router's conditional Method loads and their declared nested reads. Other references are pointers.

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/SKILL.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/evidence.md` | before: Maintained documentation | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/run.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/snapshot.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/update.md` | all | update |
| `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/phase-0.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/phases-1-2.md` | before: Team mode | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/phases-3-4.md` | before: Team mode | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/phases-5-6.md` | before: Team mode | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/phase-7.md` | before: Team mode | always |


## Pre-flight

### 1. Resolve the run

Analyses are concurrent-safe: each invocation is an isolated **run** under `.codebase-xray/runs/<run-id>/` (see `## Concurrent Runs Model` in the method's `references/run.md`).

1. Compute `run-id`: value of `--run-name` (normalized to `[a-z0-9-]`) or `<slug-of-target>-<YYYYMMDD-HHMMSS>`. On collision with an existing run directory, append `-2`, `-3`, ...
2. Set `RUN_DIR = .codebase-xray/runs/<run-id>`.
3. Read `.codebase-xray/runs.json` if it exists:
   - **Active runs listed**: show them (run-id, target, mode, started_at) and ask: resume one of them, or start this new run alongside? Starting alongside is normal and safe; runs never share files.
   - **Legacy layout** (root `state.json` with a `current_phase` field and no `runs.json`): offer to migrate the old files into `.codebase-xray/runs/legacy-<date>/` before proceeding.
4. Register the run: create/update `runs.json` with read-modify-write, appending `{run_id, target, mode: "classic", started_at}` to `active`. Never drop entries you did not create.

### 1b. Detect an update base

An X-ray run is a set of claims about a tree. When that tree has barely moved since the last run, re-deriving every claim is the whole reading cost paid again for an answer already on disk. This step finds out mechanically whether that is the case. It spends no model tokens: `snapshot.py` does the work.

Skip this step entirely if `--no-update` was passed.

1. From `runs.json`, take `latest_completed`. The candidate parent is that run when its recorded `target` normalizes to the same path as this invocation's target, `.codebase-xray/runs/<id>/state.json` records `mode: "classic"`, and `.codebase-xray/runs/<id>/snapshot/manifest.json` exists. A completed **team** run is never a usable parent here: its `08-interconnect-map.md` is cross-partition output this workflow has no phase to regenerate, so carrying it forward would leave a stale marker nothing in `## Execution Order` ever revisits, and the check in step 8 would then refuse to publish. Treat a `latest_completed` team run the same as no candidate parent at all.
2. With a candidate, run the change set:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" diff \
     .codebase-xray/runs/<parent-id> <target> --out $RUN_DIR --verify --flags '<this run's flags as JSON>'
   ```

3. Read `$RUN_DIR/changes.json` and take `recommendation` and `totals`. They drive the checkpoint in step 3.

With `--update` and no candidate parent, stop and say which condition failed (no completed run for this target, the latest completed run for this target is a team run, or a parent with no manifest), and that a full run is the way to create one. Never fabricate a parent. With a candidate present, `--update` changes nothing else: the checkpoint in step 3 still presents both options and waits, exactly as CRITICAL RULE 4 requires.

A parent from before this feature has no manifest, and the change set says so with `recommendation: full`. That is reported, never guessed at.

### 2. Initialize state

Create `$RUN_DIR/` and `$RUN_DIR/state.json`:

```json
{
  "run_id": "<run-id>",
  "target": "$ARGUMENTS",
  "mode": "classic",
  "status": "in_progress",
  "flags": {
    "critical": false,
    "comments": false,
    "docs_only": false,
    "phase": null,
    "depth": "full"
  },
  "parent_run": null,
  "base_snapshot_created_at": null,
  "git": null,
  "incremental": null,
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP"
}
```

Parse flags: `--critical` (prioritize high-risk code), `--comments` (comment quality mode), `--docs-only` (documentation health only, skip to Phase 6), `--phase N` (start at phase N), `--depth=lite` (lightweight analysis: skip flow tracing diagrams, state machine diagrams, and detailed dependency analysis for non-critical files, producing only structure + interfaces + risks + final summary), `--run-name <name>` (explicit run identity for concurrent or repeated analyses).

On an incremental run, step 1b's change set already exists by the time this file is written, so `parent_run` (the parent's run-id), `base_snapshot_created_at` (the parent manifest's `created_at`) and `incremental`'s `affected_files`, `files_in_snapshot` and `claims_affected` (from the change set's `totals`) are written here with their real values, not left for later. `extra_reads` has no source in the change set: it counts reads outside the affected-files budget, which cannot happen before any phase has run, so it starts at `0` here and is updated once the `## Extra reads` log is written, at step 9 of the incremental depth procedure in `references/update.md`. `git` cannot follow the at-creation rule either: the snapshot that supplies it is not written until `## Execution Order`, so it starts `null` here and is copied in right after that step. A full run leaves `parent_run` and `incremental` as `null` and still records `git` and the snapshot: every run is a possible parent.

Register `parent_run` in the run's `runs.json` entry as well, `null` for a full run. The chain of `parent_run` values is the analysis history; nothing else is added to hold it.

### 3. Confirm scope

Count the scope mechanically, then present it:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" scope <target>
```

It prints the file count by set and by language from the same walk the manifest takes, and the `scope` block: whether Git's ignore rules were applied, the dot directories left out and how many ignored paths the walk met. Never count by hand: a hand count does not apply the perimeter, and the user would confirm one number and get another.

With no candidate parent from step 1b, present the classic block below. With a candidate, present the variant that matches the change set's `recommendation`. Every variant carries the `Not analyzed` line, with the directory names in full or, when they are many, the outermost ones and a count. A user who needs one of them analyzed names it as a target.

**With `recommendation: incremental`:**

```
X-ray target: [path]
Run: [run-id]   parent: [parent-id] ([commit], [age])
Since parent: [N] modified, [N] added, [N] removed files; [N] symbols changed, [N] added, [N] removed
Blast radius: [N] importing files
Affected claims: [N] ([per-phase-file breakdown])
Files affected: [N] of [total]
Not analyzed: [N] dot directories ([names]), [N] paths Git ignores (ignore rules: [applied | unavailable])

1. Incremental update from [parent-id] ([N] affected files)
2. Full analysis ([total] inventoried files; source reading follows the claims)
3. Cancel
```

`[commit]` and `[age]` describe the parent run, not this one: read `[commit]` from `.codebase-xray/runs/<parent-id>/state.json -> git.commit` (copied into that run's own state right after it wrote its snapshot) and derive `[age]` from that run's `started_at`. `changes.json`'s own `git` field describes the current worktree instead, and is never the source for this line.

**With `recommendation: full`**, present the same figures with the options reversed, and print every entry of `reasons` under the figures so the user sees why (ratio over threshold, parent without a manifest, parent not complete, flags differing from the parent's). The incremental option stays selectable: the recommendation is advice, and the user decides.

**With `recommendation: none`**, say that no analysis change was detected in the
normalized content, name the parent's published output, and offer a full
analysis or return that supported parent analysis. Do not run an incremental
update that would re-derive nothing. If no phase reads source, this shortcut
does not require a new full run. A caller wanting source blocks still obtains a
current snapshot in its owned run with `snapshot.py write --reuse` before
reading: verified diff normalizes LF/CRLF, while the reader checks exact bytes.
Preserve the parent analysis and snapshot.

**With no candidate parent:**

```
X-ray target: [path]
Run: [run-id]  (concurrent active runs: [count or "none"])
Files to analyze: [count] ([language breakdown])
Not analyzed: [N] dot directories ([names]), [N] paths Git ignores (ignore rules: [applied | unavailable])
Flags: [active flags]

Analysis phases:
0. Project Knowledge Discovery (always runs)
1. Structure Extraction -- file inventory, dependency graph
2. Interface Analysis -- public APIs, contracts, exports
3. Flow Tracing -- data flow, control flow, critical paths
4. Semantic Understanding -- WHY code exists, design decisions, ADRs
5. Pattern & Risk Detection -- anti-patterns, red flags, tech debt
6. Documentation Health -- existing docs accuracy, gaps
7. Final Report -- consolidated findings

1. Proceed with full analysis
2. Analyze specific phase only (--phase N)
3. Quick scan (phases 1-2 only)
4. Lite mode (--depth=lite: structure + interfaces + risks + summary, skip detailed flows/diagrams)
5. Cancel
```

## Execution Order

After scope confirmation, execute phases inline in order. Classic scope is one package, under about 200 files, one language. For a larger target, recommend `/codebase-xray:team-analyze` at scope confirmation and stop.

**Every run writes a snapshot**, right after scope confirmation and before Phase 0, as `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/snapshot.md` says, including its `--reuse` and `state.json` steps.

### Source reading in every code phase

Every code phase reads source from this run's snapshot as `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/evidence.md` says, and its report carries the `## Source reading` section that unit defines.

### Full depth (default)

1. **Phase 0**, Project Knowledge Discovery. Writes `$RUN_DIR/knowledge/navigation.md` and `$RUN_DIR/knowledge/documentation-leads.md`.
2. **Phases 1 and 2**, Structure and Interfaces. Their output (dependency graph, entry points, module inventory) is what every later phase reads first.
3. **Phases 3 and 4**, Flows and Semantics, then **Phases 5 and 6**, Risks and Documentation. Each phase re-reads `$RUN_DIR/01-structure.md` and `$RUN_DIR/02-interfaces.md` from disk rather than relying on what is still in context.
4. **Phase 7**, Final Report, with the context-management strategy it describes.

Write each phase file the moment its phase completes. A phase file on disk is the context the next phase reads; nothing carried only in this context survives a long run.

### Lite depth (`--depth=lite`)

Lightweight mode for smaller projects, MVPs, or quick assessments: Phase 0, then Phases 1 and 2, then Phase 5, then a condensed Phase 7.

Skip Phase 3 (Flow Tracing), Phase 4 (Semantic Understanding), and Phase 6 (Documentation Health). **Phase 0 (Project Knowledge Discovery) is not skippable and runs in lite exactly as in full**: it is the cheap discovery pass, while Phase 6 is the expensive audit. Conflating the two is what made lite mode blind to a project's own documentation. In Phase 5, skip detailed state machine diagrams and Mermaid flowcharts for non-critical files, focusing on anti-patterns, red flags, and tech debt items.

The condensed `$RUN_DIR/07-final-report.md` covers structure, interfaces, and risks only. It omits the "Critical Paths", "Design Insights", "Key Process Diagrams", and "Documentation vs Reality" sections.

### Incremental depth (an update accepted at the checkpoint)

Follow `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/references/update.md`: carry the parent, re-derive only what changed, gate with `snapshot.py check`, then publish as a full run.

### Overrides

If `--phase N` or `--docs-only` flags are set, run only the requested phase(s), after Phase 0.

---

## Publish Step

After Phase 7 completes:

1. Copy `$RUN_DIR/01-*.md` through `$RUN_DIR/07-final-report.md` (the ones that exist for the active flags) and `$RUN_DIR/state.json` to the `.codebase-xray/` root, overwriting the previous mirror.

`changes.md`, `changes.json` and `snapshot/` stay in the run directory and are never mirrored: the root mirror is the latest-state contract, and history lives under `runs/`.

2. Update `runs.json` with read-modify-write: remove this run from `active`, set `latest_completed` to this run-id.
3. The root mirror is what downstream consumers (`/senior-review:team-review`, `/senior-review:code-review`, `/project-knowledge:guide`, `/project-knowledge:instructions --create`, `/project-knowledge:instructions --fix`) read. The run directory stays intact for history and comparison.

If the analysis is aborted or fails, remove the run from `active` in `runs.json` and leave the root mirror untouched.

---

## Completion

Present the analysis summary and a proposed action plan derived from findings, then ask the user what they want to do.

```
Codebase X-ray complete for: $ARGUMENTS
Run: [run-id] (published to .codebase-xray/ root)
Parent: [parent-id or "none (full run)"]

Output Files:
- Structure: .codebase-xray/runs/[run-id]/01-structure.md
- Interfaces: .codebase-xray/runs/[run-id]/02-interfaces.md
- Flows: .codebase-xray/runs/[run-id]/03-flows.md
- Semantics: .codebase-xray/runs/[run-id]/04-semantics.md
- Risks: .codebase-xray/runs/[run-id]/05-risks.md
- Documentation: .codebase-xray/runs/[run-id]/06-documentation.md
- Final Report: .codebase-xray/runs/[run-id]/07-final-report.md
(mirrored to .codebase-xray/ root for downstream consumers)

Summary:
- Files in inventory: [count] | Read in depth: [count] | Exercised at runtime: none
- Anti-patterns: [count] | Red flags: [count] | Tech debt items: [count]
- Documentation gaps: [count]
```

On an incremental run, add a fourth line after `Parent:` naming the same four buckets `### Incremental depth` step 9 writes to `changes.md`: `Claims: [N] confirmed, [N] revised, [N] retired, [N] added. Detail in .codebase-xray/runs/[run-id]/changes.md`. A full run has no such line: there is no `changes.md` to point at, and "carried" is not a bucket anything writes, since counting it would mean reading every citation in the parent's phase files, the cost this whole mechanism exists to avoid.

### Proposed Action Plan

After presenting the summary, generate a prioritized action plan based on the analysis findings. Group actions by urgency:

```
Proposed Action Plan
====================

CRITICAL (fix now):
1. [Action derived from 05-risks critical findings]
2. [Action derived from security red flags]

HIGH (fix soon):
3. [Action derived from anti-patterns or tech debt]
4. [Action derived from documentation gaps]

RECOMMENDED (improve when possible):
5. [Action derived from code quality observations]
6. [Action derived from naming/convention inconsistencies]
```

Each action must reference the specific finding and file from the analysis (e.g., "Fix missing input validation in `src/auth/login.py:45` - see 05-risks.md").

### Next steps

The analysis ends with its evidence, coverage and action plan. Offer the user the
appropriate development, knowledge or specialist path as a separate task. Do not
apply application fixes inside an X-ray run: it owns only its analysis artifacts.
Comments, type annotations, stale references and document changes require their
own scope, authorization, baseline and verification.

Keep the exact run directory and source snapshot in every downstream reference.
A mutable root mirror is suitable only for an explicitly latest-state consumer.

## Quick Examples

- `/codebase-xray:analyze src/` -- Full 7-phase analysis
- `/codebase-xray:analyze src/ --depth=lite` -- Lightweight: structure + interfaces + risks only
- `/codebase-xray:analyze src/auth/ --critical` -- Prioritize security-critical code
- `/codebase-xray:analyze src/ --docs-only` -- Documentation health check only
- `/codebase-xray:analyze src/ --comments` -- Include comment quality audit
- `/codebase-xray:analyze src/ --phase 5` -- Jump to pattern & risk detection
- `/codebase-xray:analyze src/api --run-name api` -- Named run; a second session can run `/codebase-xray:analyze src/web --run-name web` concurrently
- `/codebase-xray:analyze src/ --update` -- require an update base; a missing or unusable parent run is a hard stop instead of a silent full run
- `/codebase-xray:analyze src/ --no-update` -- skip detection and run a full analysis

## Integration with Code Review

Published analysis output in `.codebase-xray/` is automatically picked up by `/senior-review:code-review`. `/senior-review:team-review` builds the same context itself: its Phase 1a invokes this command (`--depth=lite` by default). Run an X-ray first, then run a code review for the most thorough analysis possible.
