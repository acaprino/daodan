---
description: >
  Audit a codebase for structural entropy, or with --diff check whether a change introduces new entropy. Report-only; binds a current Codebase Map run through phase 4, obtaining one when needed.
  TRIGGER WHEN: the user asks to audit duplicated knowledge, competing sources of truth, redundant models, derivable state, or wrong abstractions.
argument-hint: "[path] [--diff [<base-ref>]] [--scope <subpath>] [--severity-floor low|medium|high] [--focus all|knowledge|form|D1..D7] [--no-index] [--rebuild-index]"
---


## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

# /abstraction-architect:audit

Audit a codebase for structural entropy: duplicated domain knowledge, competing sources of truth, redundant representations, duplicated or derivable state, missed unification, prior art that already exists, and abstractions that are fighting their callers. Report-only.

## Usage

```
/abstraction-architect:audit                                    # audit current directory
/abstraction-architect:audit src/services                       # audit a subpath
/abstraction-architect:audit --severity-floor high              # only high-severity findings
/abstraction-architect:audit --focus knowledge                  # D1-D4 only
/abstraction-architect:audit --focus D2                         # competing sources of truth only
/abstraction-architect:audit --diff                             # does my change add entropy?
/abstraction-architect:audit --diff origin/master               # same, against an explicit base ref
/abstraction-architect:audit --rebuild-index                    # ignore any existing concept index
```

## Arguments

- `[path]` (optional) — codebase root. Default: current working directory.
- `--diff [<base-ref>]` (optional) — run diff-anchored instead of a whole-codebase audit. Asks the same seven questions as "introduced or aggravated by this change". Base ref defaults to the merge base with the default branch, falling back to `HEAD` for uncommitted work.
- `--scope <subpath>` (optional) — limit findings to a subtree. The Codebase Map still runs on the full codebase.
- `--severity-floor low|medium|high` (optional) — default `medium`.
- `--focus all|knowledge|form|D1..D7` (optional) — default `all`. `knowledge` is D1 to D4, `form` is D5 to D7, or name a single dimension.
- `--no-index` (optional) — do not read or write `concept-index.json`. Use when auditing a directory that is not a git repository, or to measure what the audit finds without a seed.
- `--rebuild-index` (optional, global mode only) — ignore any existing index and census the codebase from scratch. Use after a large refactor or a history rewrite.

## What this command does

1. **Resolves the target path.** Defaults to the current working directory.

2. **Resolves the diff (`--diff` only).** Runs `git diff --name-only <base-ref>...HEAD` plus `git diff --name-only` for uncommitted work, and passes the union as `changed_files`. Aborts with a clear message when the path is not a git repository.

3. **Acquires bound static context.** Follow the global or diff branch below, retaining the exact run directory, `run_id`, target, flags and the exact snapshot path from `snapshot.py resolve <bound-run-dir>`, never the mirror. The optional `08-interconnect-map.md` is read only from the same bound run; without it, knowledge-track findings carry `Bounded-context exception: unverified`.

4. **Resolves the concept index.** Unless `--no-index`, checks `<path>/.abstraction-architect/concept-index.json` and runs the freshness script. Reports the state to the user before spawning, so a `delta-stale` index is visible rather than silent:

   ```
   Concept index: delta-stale (baseline a13fe2, HEAD 92ac10, 4 concepts to revalidate)
   ```

   An absent or unusable index is not an error. The audit proceeds and declares the reduced coverage in its Gaps section.

5. **Spawns the `abstraction-architect-agent` agent** through its declared host harness, placing in the worker prompt `codebase_path`, `mode`, `xray_path` (the bound run directory), `map_run_id`, `map_snapshot_path`, `map_changes_path`, `map_outside_diff_changed_files`, `concept_index_path`, `changed_files` under `--diff`, and the parsed scope, severity-floor and focus flags.

6. **The agent writes the report** to `<path>/.abstraction-architect/findings.md`, or `findings-diff.md` under `--diff`. In global mode it also rewrites `concept-index.json`. **Diff mode never writes the index.**

7. **Prints to the user:** the report path, summary counts, the concept index state, and the top three findings as one-line previews.

The full report stays in the file so the user opens it deliberately.

### Global acquisition

After the migration preflight, inspect `.codebase-map/runs/*/state.json`, not just
`runs.json -> latest_completed`. Select the newest run by its recorded start time
that holds nonempty `01-structure.md`, `02-interfaces.md`, `03-flows.md` and
`04-semantics.md`. Validate `run_id` against the run directory, the snapshot's
`root` against this worktree and its `target` against the resolved audit target.
Exclude active or failed runs and broken bindings. A stopped partial run with all
four delivered files is eligible; its later phases need not exist.

Load the provider's `references/snapshot.md` and `references/reading.md` through
`codebase-map:map-method`. Check the selected run against the current worktree:

```bash
python "<codebase-map script directory>/snapshot.py" diff \
  <bound-run-dir> <target> --out <audit-check-dir> --verify
```

`<audit-check-dir>` is owned by this audit, outside the Map store and analyzed
source. Preserve the parent snapshot and phase files. A current run has no
added, modified or removed files, no stale claims in `01` to `04`, and a valid
parser/root/target binding. Read it as is. Partial publication status by itself
does not make its delivered first four phases stale; `recommendation` alone is
not the currentness check. Parser mismatch or other invalid evidence requires
fresh context, never an assumption of freshness.

For a stale eligible run, execute the canonical analyze entry with its exact
`parent_run` supplied as an internal caller binding and its original flags:

```text
/codebase-map:analyze <target> --update --stop-after 4 --run-name <new-audit-run-name> <original flags>
```

The child keeps the parent's identity in its lineage, preserves its source
snapshot, and re-derives stale claims through phase 4. Keep the new child's
returned run binding, not the old run or `latest_completed`. Do not inherit an
`08-interconnect-map.md` that the bounded child did not regenerate.

When no eligible run exists, obtain the first four phases with:

```text
/codebase-map:analyze <target> --no-update --stop-after 4 --run-name <new-audit-run-name> --depth=full
```

Execute only the canonical entry's preflight, answerable scope checkpoints,
dispatch, delivery gate and publication decision here. Dispatch its
`codebase-map:map-analyst` through this workflow's declared harness in an isolated
context; loading the role as a skill executes no analysis. The partial Map stays
in its run and never publishes. Require the gate's valid delivered `01` to `04`
and bound snapshot before auditing. Missing or failed delivery stops the audit
with its diagnostic path; do not substitute the mirror.

### Diff acquisition

Under `--diff`, this command never launches a Map. Bind the newest target-bound
run with `01-structure.md` and `02-interfaces.md` when one exists, using the same
root, target and identity checks. Run the verified snapshot diff into this
audit's check directory. Compute the union of `files.added`, `files.modified`
and `files.removed`, subtract the resolved `changed_files` under review, and pass
every remaining path as `map_outside_diff_changed_files`. The auditor reports
every path in Gaps as changed since that bound snapshot outside the review diff.
Do not present the stale Map as current; read current source before promoting a
finding. An invalid snapshot, parser mismatch or failed check is a named gap.
With no valid run, continue on the concept index and independent discovery at
reduced confidence and state the missing Map and freshness evidence in Gaps.

### Auditor delivery

The worker consumes only the supplied immutable binding and never acquires a
new Map. The coordinator retains the native report owner and delivery checks.

## Output location

`<path>/.abstraction-architect/findings.md`, or `<path>/.abstraction-architect/findings-diff.md` under `--diff`.

The directory is created automatically if missing. Re-running the command overwrites the previous report.

## Prerequisites

- The `codebase-map` plugin must be installed (a hard dependency declared in this plugin's `plugin.toml`). `--diff` degrades gracefully without Codebase Map output and reports the reduced confidence in its Gaps section.
- `--diff` requires the target path to be a git repository.
- For monorepos large enough to benefit from partitioned analysis, run `/codebase-map:team-analyze` first to produce `08-interconnect-map.md`; the auditor will then include bounded-context fusion findings.

## Related commands

- `/codebase-map:analyze` — produces the bound run this command consumes; acquisition stops after phase 4 when context is missing or stale.
- `/codebase-map:team-analyze` — partitioned Codebase Map for monorepos; adds `08-interconnect-map.md` to the output.
- `/senior-review:code-review` and `/senior-review:team-review` — both run this agent in diff mode as their abstraction dimension, so a review already answers the "was this already available?" question for the changed code. Use `--diff` here when you want that check on its own, without the rest of the review.
- `/clean-code:clean-code` — style and readability cleanup. Different concern.

## Out of scope

This command does not produce a refactoring plan. The `suggested direction` field in each finding names the target layer or refactoring move in one sentence.
