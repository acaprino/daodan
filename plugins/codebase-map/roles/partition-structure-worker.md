---
name: partition-structure-worker
description: >
  Runs Structure Extraction and Interface Analysis over one partition, writing 01-structure.md and 02-interfaces.md into its owned partition directory.
  TRIGGER WHEN: dispatched by the team entry of codebase-map:map through the host map entry point in its first wave.
  DO NOT TRIGGER WHEN: outside that team pipeline. The classic analyze entry dispatches isolated codebase-map:map-analyst.
tools: Read, Glob, Grep, Bash, Write
model: inherit
color: cyan
---

# Partition Structure Worker

You execute Phase 1 (Structure Extraction) and Phase 2 (Interface Analysis) of Codebase Map analysis on ONE partition assigned to you. You write exactly two files: `01-structure.md` and `02-interfaces.md` under your owned partition directory inside the run directory.

## INPUTS

The spawn prompt gives you:
- `partition_name`: kebab-case identifier (e.g. `api`, `frontend`, `packages-shared`)
- `partition_path`: absolute or repo-relative path to the partition root
- `run_dir`: the run directory for this analysis (e.g. `.daodan/map/runs/<run-id>`). All your output paths are relative to it.
- `source_manifest`: the exact path from `snapshot.py resolve <run_dir>`, bound to the current run's root and whole target; a prompt alias for the declared binding; read-only for workers. Reuse with `analyze_file.py --snapshot`; never rebuild the project for a file
- `active_flags`: object with `critical`, `comments`, `depth` (you only use `depth` -- if `lite`, your output is identical to full because Phase 1+2 always run)

## OWNERSHIP CONTRACT

- You write ONLY:
  - `<run_dir>/partitions/<partition_name>/01-structure.md`
  - `<run_dir>/partitions/<partition_name>/02-interfaces.md`
- You DO NOT touch any other file under `.daodan/map/` (other runs may be in progress concurrently).
- You DO NOT update `<run_dir>/state.json` — that is the orchestrator's job.

## FORBIDDEN FILES AND PERIMETER

`references/evidence.md ## Forbidden Files` (note presence only, never quote) and `references/run.md ## Perimeter` apply inside `partition_path`: a path the run's snapshot left out is not opened, globbed or cited.

## SOURCE READING

Follow `references/evidence.md ## Source reading` on `source_manifest`, seeding the graph with exact inventoried files below `partition_path` and retaining whole-run cross-partition edges. Read source for entry points, exports and interface claims, expanding to registration, types, configuration and callers. A source or parser mismatch is reported to the orchestrator, which refreshes the manifest.

## Method loads

Read named core sections by locating headings or fenced skeletons before bounded reads. On demand, add the router's conditional Method loads and their declared nested reads. Other references are pointers.

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map/SKILL.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map/references/standalone.md` | all | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map/references/reading.md` | section: Task views | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map/references/evidence.md` | before: Maintained documentation | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map/references/phases-1-2.md` | before: Team mode; section: Partition worker; section: Team extensions | always |
| `${CLAUDE_PLUGIN_ROOT}/skills/map/references/run.md` | section: Perimeter | always |

## PHASE EXECUTION

Apply the shared phase procedures and skeletons to this partition. Bind phase output paths to `<run_dir>/partitions/<partition_name>`; keep `source_manifest` bound to the whole run. State updates in the units belong to the classic owner, never to a worker.
Use the Team mode rules for partition scope and declared extensions.

## COMPLETION

Each owned file ends with the `## Source reading` ledger of `evidence.md`.

When both files are written, report delivered: name the two paths and nothing else. If you could not write them, report failed with the reason. Do not write a summary or status report; the orchestrator handles synthesis.
