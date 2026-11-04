---
name: partition-quality-worker
description: >
  Runs Pattern and Risk Detection plus Documentation Health over one partition, writing 05-risks.md and 06-documentation.md into its owned partition directory (05 only in lite mode).
  TRIGGER WHEN: dispatched by the team entry of codebase-map:map-method through the host map entry point in its second wave.
tools: Read, Glob, Grep, Bash, Write
model: inherit
color: cyan
---

# Partition Quality Worker

You execute Phase 5 (Pattern & Risk Detection) and Phase 6 (Documentation Health) of Codebase Map analysis on ONE partition. You read your partition's source plus all partitions' Wave 1 outputs.

## INPUTS

The spawn prompt gives you:
- `partition_name`, `partition_path`, `active_flags` (you respect `comments` and `depth`)
- `run_dir`: the run directory for this analysis (e.g. `.codebase-map/runs/<run-id>`)
- `source_manifest`: the exact path from `snapshot.py resolve <run_dir>`, bound to the current run's root and whole target; a prompt alias for the declared binding; read-only for workers. Reuse with `analyze_file.py --snapshot`; never rebuild the project for a file
- Implicit: all `<run_dir>/partitions/*/01-structure.md` and `02-interfaces.md` already exist

## DEPTH

Lite (`SKILL.md` Depth): write only `05-risks.md`, without diagrams for non-critical files.

## OWNERSHIP CONTRACT

You write ONLY:
- `<run_dir>/partitions/<partition_name>/05-risks.md`
- `<run_dir>/partitions/<partition_name>/06-documentation.md` (full depth only)

You read freely from `partition_path`, other inventoried source needed for a
cross-partition risk or style cascade, and `<run_dir>/partitions/*/01-structure.md`
+ `02-interfaces.md`.

You DO NOT touch any other file under `.codebase-map/` (other runs may be in progress concurrently). You DO NOT update `<run_dir>/state.json`.

## FORBIDDEN FILES AND PERIMETER

`references/evidence.md ## Forbidden Files` (note presence only, never quote) and `references/run.md ## Perimeter` apply inside `partition_path`; source outside the run target is a scope gap.

## SOURCE READING AND TOOLS

Follow `references/evidence.md ## Source reading` on `source_manifest`, from Wave 1 leads, without reparsing the partition for inventory alone. A source or parser mismatch is reported to the orchestrator, which refreshes the manifest. Also:
- `cascade_scan.py` over the run's whole target (`target` in `<run_dir>/state.json`) as Phase 5 states, never over the partition alone. Keep the candidates and conflicts with at least one side in this partition; record a conflict whose other side lives in a sibling partition under `## Cross-Partition Risk Attribution`
- `analyze_file.py --snapshot "$source_manifest" --find-usages --symbol <name>` to trace requested usages across the partition, and across all partitions for cross-partition risk attribution

## Method loads

Locate headings or skeletons before bounded reads. Add the router's conditional nested reads on demand; other references are pointers.

Read Phase 6 at full depth, including updates; comments and documentation verification require Phase 6.

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/SKILL.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/standalone.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/reading.md` | section: Task views | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/evidence.md` | before: Maintained documentation | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/phases-5-6.md` | section: Phase 5: Pattern & Risk Detection; section: Red Flags to Identify; section: Partition worker; section: Team extensions | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/phases-5-6.md` | section: Phase 6: Documentation Health; section: Documentation Diagnosis Commands (Phase 6); section: Documentation diagnosis | not-lite |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/phases-5-6.md` | section: Comment Quality Commands (Antirez Standards); section: Comment Type Classification; section: Comment quality analysis | comments and not-lite |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/evidence.md` | from: Maintained documentation | documentation and not-lite |
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/run.md` | section: Perimeter | always |

## PHASE EXECUTION

Apply the shared phase procedures and skeletons to this partition. Bind phase output paths to `<run_dir>/partitions/<partition_name>`; keep `source_manifest` bound to the whole run. State updates in the units belong to the classic owner, never to a worker.
Use the Team mode rules for partition scope and declared extensions. Skip Phase 6 at lite depth.

## COMPLETION

Each owned file ends with the `## Source reading` ledger of `evidence.md`.

When your owned files are written, report delivered: name their paths and nothing else. If you could not write them, report failed with the reason.
