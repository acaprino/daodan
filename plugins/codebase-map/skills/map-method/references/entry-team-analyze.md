# Team Codebase Map Analysis

Partition the target, dispatch isolated workers in two waves, synthesize, map
the cross-partition surface, publish. The host harness dispatches workers and
records each one `delivered` or `failed`; nothing writes outside the roots of
the `write-confinement` policy. If the harness cannot run workers in isolated
contexts, stop and say so: a partition analysis that read another partition's
output is not this artifact. Never enter plan mode.

## Method loads

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/SKILL.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/run.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/snapshot.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/phase-0.md` | all | always |

## Rules

1. Phases run in order; only `--skip-synthesis` and `--skip-interconnect` skip one.
2. Every spawn prompt enumerates the files the worker owns.
3. All output stays in `$RUN_DIR` until publish; concurrent runs share no file.
4. Wave 2 starts only after every Wave 1 worker is recorded delivered or failed; synthesis only after every partition is accounted for.
5. Resume re-spawns only the missing workers.
6. Invoking this workflow authorizes the analysis. Show the scope, then proceed. Ask only for a material unresolved choice or an explicitly requested approval; a missing `--yes` is not a reason to stop.

## Preflight

1. Parse `$ARGUMENTS`:
   - `<target>` (default cwd)
   - `--critical`: prioritize auth, payment and persistence in Phases 3 and 4
   - `--comments`: comment audit in Phase 6
   - `--depth=lite|full`: lite spawns no behavior worker, quality workers write only `05-risks.md`, the synthesizer skips 03, 04 and 06
   - `--partition <path>` (repeatable, overrides detection), `--partition-name <name>` for the N-th manual partition (1-indexed)
   - `--skip-interconnect` (no Phase 3), `--skip-synthesis` (no Phase 2 or 3)
   - `--run-name <name>`, `--format sqlite|json` (default SQLite for a new run)
   - `--yes`: take the recommended eligible scope; ordinary language authorizes the same
   - `--update`: require an update base; `--no-update`: run every partition fresh
   - Reject `--phase N` and `--docs-only`: point at `references/entry-analyze.md`
2. Resolve the run per `## Concurrent Runs Model` in `references/run.md`: `run-id` is `--run-name` normalized to `[a-z0-9-]` or `<slug-of-target>-<YYYYMMDD-HHMMSS>`, suffixed `-2`, `-3`... on collision; `RUN_DIR = .codebase-map/runs/<run-id>`. From `.codebase-map/runs.json` offer to resume a matching in-progress team run or start alongside; a root `state.json` with `current_phase` and no `runs.json` is a legacy layout, offer to migrate it into `.codebase-map/runs/legacy-<date>/` first.
3. Detect an update base unless `--no-update`: `latest_completed` is a candidate parent when it is a completed team run, its `target` normalizes to this target and `snapshot.py resolve <parent-run-dir>` resolves. With a candidate, run the change set once over the whole target and hold `changes.json`:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" diff \
     .codebase-map/runs/<parent-id> <target> --out $RUN_DIR --verify --flags '<this run's flags as JSON>'
   ```

   `--update` with no candidate stops and names the failed condition (no completed run for this target, not team mode, no manifest). `--update` with a candidate requires that base but the execution mode is still resolved at the checkpoint.
4. Create `$RUN_DIR/state.json`:

   ```json
   {
     "run_id": "<run-id>", "target": "$ARGUMENTS_TARGET", "mode": "team", "status": "in_progress",
     "flags": {"critical": false, "comments": false, "depth": "full"},
     "parent_run": null, "base_snapshot_created_at": null, "git": null, "incremental": null,
     "partitions": [],
     "phases": {"phase_0_detection": "pending", "phase_1_partition_workers": "pending",
                "phase_2_synthesis": "pending", "phase_3_interconnect": "pending"},
     "agents_spawned": [], "files_created": [],
     "started_at": "<ISO_TIMESTAMP>", "completed_at": null
   }
   ```

   On an incremental run write `parent_run`, `base_snapshot_created_at` (the parent manifest's `created_at`) and `incremental` (`{affected_files, files_in_snapshot}` from the change set's `totals`) now, with real values. `git` starts `null` and is copied from the snapshot written after the checkpoint. Record `snapshot_format` and `source_manifest` under `state.json -> snapshot` as `references/snapshot.md` specifies; storage is separate from flags and resume preserves it.
5. `snapshot.py register $RUN_DIR`; repeat after lineage changes. Never write `runs.json` directly.

## Phase 0: knowledge and partitions

1. Project knowledge discovery (`references/phase-0.md`) runs once, inline, before partition detection, over the whole target. No partition worker owns `$RUN_DIR/knowledge/navigation.md` or `documentation-leads.md`.
2. With `--partition`, use the manual list; names from `--partition-name` or the path basename. Otherwise the first matching rule wins:
   1. Workspace manifests: `pnpm-workspace.yaml` `packages`; `package.json` `workspaces`; `lerna.json` `packages`; `nx.json` with `apps/` and `libs/`; `turbo.json` with `apps/` and `packages/`; `Cargo.toml` `[workspace] members`; `pyproject.toml` `[tool.uv.workspace] members`.
   2. Convention: `apps/`, `packages/` or `services/` with more than one subdirectory; `src/` subdirectories each with a `package.json` or `pyproject.toml`.
   3. Layer: `src/{backend,frontend}`, `src/{api,web}`, `src/{server,client}`, or root `backend/` + `frontend/`.
   4. Language: `classifier.py` counts; at least 2 languages with at least 20 files each, one partition per language. Stylesheets never form a partition and never count: they stay with the code they style.
   5. Fallback: one partition `root`.
3. Outside every partition: whatever `## Perimeter` in `references/run.md` leaves out. A partition path the user names is analyzed as given.
4. Names: workspace basename, slug of the path on collision, language name, or `root`; lowercase, separators to hyphen, accents stripped, `[a-z0-9-]`.
5. Per partition, `file_count` from `snapshot.py scope <partition path>` and `loc_estimate` over the same files (`wc -l` or `cloc`). Run `snapshot.py scope <target>` once: its `scope` block is the preview's `Not analyzed` line.

### Partition-level update

The unit of an update is the partition, coarser than the claim-level update of `references/entry-analyze.md`. Available only with a candidate parent whose change set does not recommend `full`; the checkpoint decides whether to use it.

1. The set of partition names and paths must equal the parent's `state.json -> partitions`; any difference means a full run, named at the checkpoint.
2. A partition's affected files are the change set's `affected_files` under its path. Record `partitions[i].update` as `"copied"` (none) or `"re-analyzed"` with the count, before either branch runs: the summary and `changes.md` read this field and cannot reconstruct it.
3. Copied: once the update is accepted, copy `.codebase-map/runs/<parent-id>/partitions/<name>/` whole into `$RUN_DIR/partitions/<name>/` and set `status: "done"`. Both waves skip a partition already `"done"`.
4. Re-analyzed: both waves, normal prompts, the workers never see the change set.
5. Synthesis and the interconnect map always run: they are cross-partition by construction.
6. `changes.md` holds the change set's three mechanical sections plus a `## Partitions` table read from `partitions[i].update`.

### Scope preview

Always shown, after discovery and detection, with observed values: the spawn plan counts the workers actually dispatched after depth, skipped phases and copied partitions. It waits only for an unresolved decision. With an eligible update, list each partition as `unchanged (copied)` or `re-analyzed ([N] affected files)` with the parent run-id and totals above, and recommend the update unless a full run was requested. When the change set recommends `full` or the partition set differs, give the reasons (`changes.json` `reasons`, plus "the partition set changed since the parent run") and recommend a full run. Never offer an ineligible update.

```
Codebase Map team-mode scope:
Target: <target>
Run: <run-id>  (concurrent active runs: <count or "none">)

Detected partitioning strategy: <strategy name>

Partitions (<N>):
  P1: <path>          (<language>, <file-count> files, ~<loc>k LOC)
  ...

Not analyzed: <N> dot directories (<names>), <N> paths Git ignores (ignore rules: <applied | unavailable>)

Mode: <full or partition-level update, depth and active flags>
Spawn plan: <structure count> structure + <behavior count> behavior + <quality count> quality
            + <synthesizer count> synthesizer + <mapper count> interconnect-mapper = <total> agents.
```

Proceed in the same turn when the scope is settled: a fresh run of the requested target, `--no-update`, an update already chosen, `--yes` or "proceed with your recommendation", partitions the user supplied. Ask when a material choice remains (update or fresh undecided, conflicting inclusion rules, a requested partition approval): one concrete question after the preview, through the host's user-input tool or, without one, as plain text ending the turn. Accept ordinary replies ("yes", "exclude web", "merge api and workers") and recompute eligibility and the preview when the set changes. A later request to wait beats an earlier `--yes`. Never end with only a statement that confirmation is required; an unavailable tool or elapsed time is not an answer, the decision stays pending. On cancel: `status: "cancelled"`, `snapshot.py unregister $RUN_DIR`, exit.

Then finalize `partitions` as `{name, path, language_primary, file_count, loc_estimate, status: "pending"}` and set `phase_0_detection: "complete"`.

### Snapshot and preparation

1. Write the snapshot over the whole target before any dispatch; it is global, no worker writes to it:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write \
     <target> --format "$snapshot_format" --out "$source_manifest"
   ```

   With a same-target candidate parent add `--reuse "$parent_manifest"`, also for a full run: bytes and parser identity are checked before structure is retained, the inventory is still scanned and hashed. Never skip this write because the diff recommended `none`: diff normalizes line endings, block readers need byte identity.
2. `snapshot.py resolve $RUN_DIR`; keep its path as `source_manifest` and copy its `git` into state.
3. If the accepted option is an update, apply `### Partition-level update` now.
4. `prepare $RUN_DIR` from `references/snapshot.md` with the accepted mode and flags. Keep its produced, inherited and skipped declarations; `08-interconnect-map.md` is the team-only artifact. Never turn a failed worker or missing map into a skipped phase.

Every worker receives the exact `source_manifest` path, read-only; it is never a second index. Workers seed `source_reader.py graph` with exact files, never directories, read through `source_reader.py read`, and record their reading as their role prescribes. A stale manifest is refreshed by this coordinator before reading continues.

## Phase 1: partition workers, two waves

### Wave 1: structure

For each partition whose `status` is not `"done"`, create `$RUN_DIR/partitions/<name>/` and dispatch one `partition-structure-worker`, title `P<i>.A — Structure+Interfaces for partition <name>`:

```
You are partition-structure-worker on partition "<name>".

Identity: P<i>.A
Run directory: <RUN_DIR>
Current source manifest: <source_manifest> (read-only)
Owned files:
  - <RUN_DIR>/partitions/<name>/01-structure.md
  - <RUN_DIR>/partitions/<name>/02-interfaces.md
DO NOT touch any other file under .codebase-map/.

Target path for this partition: <path>
Active flags: --critical=<bool> --comments=<bool> --depth=<lite|full>
Sibling partitions: <name -> path, one per line>

Follow your role's Method loads; never load every method unit. Seed
source_reader.py graph with exact inventoried files below the partition,
read through source_reader.py read, record ## Source reading in each output.

Completion: report delivered naming both files, or failed with the reason.
```

Record each dispatch in `agents_spawned[]` as `{name: "P<i>.A", role: "partition-structure-worker", partition: "<name>", status: "dispatched"}`. Hold the barrier until every `P<i>.A` is delivered or failed; a copied partition has none. Then set each partition `"structure_done"` or `"failed"` and `phase_1_partition_workers: "wave1_done"`.

### Wave 2: behavior and quality

For each partition with `status == "structure_done"`:

1. Unless `--depth=lite`, dispatch one `partition-behavior-worker`, title `P<i>.B — Flows+Semantics for partition <name>`, same template with owned files `03-flows.md` and `04-semantics.md` and these extra lines:

   ```
   Required reads: <RUN_DIR>/partitions/*/01-structure.md and 02-interfaces.md (ALL partitions).
   Seed the graph from Wave 1 leads with 2-3 hops; expand to callers, callees, gates,
   invariants, configuration and relevant CSS/markup beyond import edges.
   Cite a call or import leaving your partition as <other-partition>::<symbol>.
   ```

2. Dispatch one `partition-quality-worker`, title `P<i>.C — Risks+Docs for partition <name>`, same template as B including its extra lines; owned files `05-risks.md` and `06-documentation.md`, only `05-risks.md` under lite.

Record both. Hold the barrier; when `P<i>.B` and `P<i>.C` (only `P<i>.C` in lite) are delivered set `"done"`. When every partition is `done` or `failed`, set `phase_1_partition_workers: "complete"`, or `"failed"` if every partition failed.

## Phase 2: synthesis

Skip with `--skip-synthesis`. Dispatch one `partition-synthesizer`:

```
You are partition-synthesizer.

Identity: SYNTH
Run directory: <RUN_DIR>
Owned files: <RUN_DIR>/01-structure.md through 07-final-report.md (skip 03, 04, 06 if depth=lite).
DO NOT touch 08-interconnect-map.md, any partition file, or the .codebase-map/ root.

Active flags: <flags from state.json>
Partitions to consolidate: <{name, path, status, language_primary} per partition>

For a failed partition add a "⚠ Missing partitions" callout in every consolidated
file; 07-final-report.md then opens with a "Partial Completeness Warning".
Read <RUN_DIR>/partitions/*/ and apply your role's consolidation rules. Union the
workers' ## Source reading sections, deduplicated by path; keep graph, outline
and inventory metadata separate; do not re-read source. Distinguish source read
in this run from reading carried with copied parent partitions.

Completion: report delivered when every owned file is written, or failed with the reason.
```

On delivery set `phase_2_synthesis: "complete"`. On failure set it `"failed"`, set `phase_3_interconnect: "skipped_due_to_phase_2_failure"` and go to Phase 4.

## Phase 3: interconnect map

Skip with `--skip-interconnect`, `--skip-synthesis` or a failed Phase 2. Dispatch one `semantic-interconnect-mapper`:

```
Build the interconnect map from the consolidated team output.

Primary context: <RUN_DIR>/01-07.md. Current source manifest: <source_manifest> (read-only).
Scope: the cross-partition surface only. Read 02-interfaces.md ## Cross-Partition Exports,
03-flows.md ## Cross-Partition Flows, 04-semantics.md ## Hidden Contracts (cross-partition)
and 05-risks.md ## Cross-Partition Risk Attribution (whichever exist), then the source they
cite. Seed source_reader.py graph with exact files, 2-3 hops; read through read; outline for
definitions. Partition-internal contracts are already in the partition outputs.
Output path: <RUN_DIR>/08-interconnect-map.md

Produce the full map of your role: Call Graph limited to symbols crossing a partition
boundary (2-3 hops, crossing edges marked), Contracts, Invariants, Domain Rules,
Assumptions, Integration Hot-Spots, Change Impact Radius, Reviewer Hints. Every claim
cites file:line; call rows keep graph identities, callsite and declaration evidence,
resolution and a separate evidence status. No recommendations, no fixes. Empty sections
are acceptable.
```

On delivery set `phase_3_interconnect: "complete"`; on failure `"failed"` and continue. An undeclared skip or a failed map never permits publication.

## Phase 4: publish

`07-final-report.md` is the human view: no HTML renderer is adapted, a requested HTML view keeps the run open.

1. Account for every dispatched worker as delivered or failed; none may still be writing.
2. `check $RUN_DIR --json` from `references/snapshot.md`. Missing or empty produced artifacts, stale markers, invalid inherited provenance or unexpected files keep the run open: recover through resume or report the blocker.
3. Publish only when `complete` and `may_publish` are true and every requested view is delivered: `publish $RUN_DIR` replaces the whole mirror, including `08`, with rollback protection. `--skip-synthesis` results stay in the run: record partial status, `snapshot.py unregister $RUN_DIR`, leave the mirror intact.
4. Summary:

```
Codebase Map (team mode) complete for: <target>
Run: <run-id> (<published to .codebase-map/ root | partial, run only>)
Parent: <parent-id or "none (full run)">

Partitions: <N> (<name: done | failed | copied | re-analyzed ([N] affected files)>)

Output Files:
  Knowledge discovery:      .codebase-map/runs/<run-id>/knowledge/navigation.md, documentation-leads.md
  Per-partition reports:    .codebase-map/runs/<run-id>/partitions/*/01..06.md
  Consolidated reports:     .codebase-map/runs/<run-id>/01-structure.md .. 07-final-report.md
  Interconnect map:         .codebase-map/runs/<run-id>/08-interconnect-map.md (if Phase 3 ran)
  Root mirror:              .codebase-map/01..08.md

Summary:
  - Files in inventory: <count>  |  Read in depth: <count>  |  Exercised at runtime: none
  - Anti-patterns:   <count>  |  Red flags: <count>  |  Tech debt: <count>
  - Documentation gaps: <count>
  - Cross-partition flows: <count>
```

On an incremental run each partition reports `partitions[i].update` (a failed one still reports `failed`) and the summary points at `changes.md ## Partitions`.

5. Suggest independent next steps with the exact run directory and snapshot. Fixes, reviews and durable documents are separate tasks, never applied inside this run.

## Resume

An active team run with `status == "in_progress"` is offered for resume:

- `phase_0_detection != "complete"`: remove the run, restart
- `phase_1_partition_workers == "pending"`: Wave 1
- `"wave1_done"`: Wave 2 for every partition `"structure_done"`
- `"complete"` and `phase_2_synthesis != "complete"`: Phase 2
- `phase_2_synthesis == "complete"` and `phase_3_interconnect != "complete"`: Phase 3
- `phase_3_interconnect == "complete"`: Phase 4

Resume dispatches fresh workers; contexts are not restored and the run directory carries the identity.

## Examples

- `.` — detect partitions, full depth, proceed after the preview
- `. --depth=lite` — 2N+2 agents
- `. --partition packages/api --partition packages/web --yes`
- `. --skip-synthesis` — per-partition reports only, no publish
- `apps/backend --run-name backend` — named run alongside other active runs
