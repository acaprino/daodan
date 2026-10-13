# X-ray atomic method, step 2: one skeleton per phase file

Spec: `docs/superpowers/specs/2026-10-12-xray-atomic-method-design.md`, refactor
plan step 2 and "One skeleton per phase file". One commit. This step decides
meaning heading by heading; every change below is listed in the commit message.

## Scope of this step

In: one canonical skeleton per phase file `01` to `07`, in its phase unit, with the
classic headings; the team extensions declared in the same unit; the three
partition workers and the synthesizer cite those skeletons instead of carrying
their own; `references/analysis-templates.md` folded into the units and
`templates/` retired; the skeleton and consumer test.

Out: narrowing what workers and the mapper load (step 3); the analyst role and the
thin entry (step 4); prose tightening (step 5). File names `01` to `08` never
change.

## Consumers found

The mapper and `team-analyze` read four exact consolidated headings: `Cross-Partition Exports` (02), `Cross-Partition Flows` (03), `Hidden Contracts (cross-partition)` (04), and `Cross-Partition Risk Attribution` (05). Consumer tests inspect both actual bodies. Other external readers consume whole phase files or the interconnect map. The synthesizer also resolves its Quick Reference targets.

## Budget-preserving reads

Method loads tables make section and mode reads explicit. Classic execution excludes Team mode; workers read the shared phase procedure/skeleton and partition rules; synthesis reads skeletons, extension declarations and consolidation rules. Update instructions are loaded only on updates. Missing resources and section boundaries fail the guard.

On-demand methodology, pattern and comment knowledge remain optional. Their declared nested reads are counted once, including the methodology's reading guide. Core caps remain unchanged; optional additions have separate frozen baselines measured from the pre-refactor resources, which the old guard did not traverse. Verify every enabled combination and report core and optional totals separately.

Owner prerequisites move verbatim to snapshot.md; the analysis loop moves to phases-3-4.md. Maintained-document verification is folded into its own evidence.md section. Inventory restatements are merged into Phase 1, preserving the minified threshold, file-level formats, exclusions and snapshot metadata. Duplicate phase routing is removed; historical rationale is retained in plugin documentation. These moves preserve rules without raising existing budgets.

## Common headings: classic wins

A team qualifier in a heading moves into the section's first line as content
("Grouped by partition.", "Sorted by severity.").

| File | Team heading today | Becomes | Where |
|---|---|---|---|
| 01 | Entry Points (within this partition) | Entry Points | structure worker |
| 01 | Naming Conventions Observed | Naming Conventions | structure worker |
| 01 | Dependency Graph (cross-partition view) | Dependency Graph | synthesizer |
| 01 | Global Entry Points | Entry Points | synthesizer |
| 01 | Naming Conventions (per partition) | Naming Conventions | synthesizer |
| 01 | (missing) | Key Observations | synthesizer gains it |
| 02 | Public APIs (by partition), Contracts (by partition), How to Add a New Module (per partition) | qualifier dropped | synthesizer |
| 03 | Critical Paths (by partition), Data Flow (consolidated) | qualifier dropped | synthesizer |
| 04 | Module Purposes (by partition), Design Decisions (by partition), Architecture Decision Records (per partition), Embedded Assumptions (consolidated) | qualifier dropped | synthesizer |
| 04 | Conventions Observed | Conventions to Follow | behavior worker, synthesizer |
| 04 | (missing) | Hidden Contracts, partition-local entries | synthesizer gains it |
| 05 | Anti-Patterns Found (by severity), Red Flags (by severity), Technical Debt Inventory (by partition) | qualifier dropped | synthesizer |
| 06 | Documentation vs Code Accuracy (by partition), Coverage Gaps (priority-sorted), Broken References (by partition) | qualifier dropped | synthesizer |
| 06 | Comment Quality [if active_flags.comments] / [if --comments] | Comment Quality, written only when the comments flag is active (stated once, in prose) | both |
| 07 | Codebase X-Ray Analysis Report (Team Mode) | Codebase X-Ray Analysis Report; the mode stays in Analysis Metadata `Mode:` | synthesizer |
| 07 | Critical Paths (cross-partition), Risk Assessment (global) | qualifier dropped | synthesizer |
| 07 | dangling `Cross-Partition Risks` row | `Cross-Partition Risk Attribution` row, the heading `05` has | synthesizer |

Classic `07` gains `Mode: classic` in Analysis Metadata, so both modes state it in
the same place.

## Team extensions, declared

Each unit gets a `### Team extensions` table: heading, file, written by, position
in the skeleton, aggregation.

| Heading | File | Written by | Aggregation |
|---|---|---|---|
| Cross-Partition Outgoing References | partition `01` | structure worker | read by the synthesizer for `01` Cross-Partition Reference Summary and `02` Cross-Partition Exports; not in the consolidated file |
| Cross-Partition Inbound References | partition `02` | structure worker | read by the synthesizer for Cross-Partition Exports; not in the consolidated file |
| Partition Map | `01`, `07` | synthesizer | one row per partition; `07` repeats the `01` table |
| Cross-Partition Reference Summary | `01` | synthesizer | outgoing references grouped by target partition |
| Cross-Partition Exports | `02` | synthesizer | outgoing references reconciled with sibling exporters |
| Cross-Partition Flows | `03` | synthesizer | flows whose citations cross a partition boundary |
| Cross-Partition ADR | `04` | synthesizer | ADRs involving more than one partition, reframed as global |
| Hidden Contracts (cross-partition) | `04` | synthesizer | every partition entry in `<this> ↔ <other>` notation |
| Cross-Partition Risk Attribution | partition `05`, `05` | quality worker, synthesizer | worker attributes; synthesizer deduplicates |
| Partial Completeness Warning | `07`, first section | synthesizer | only when a partition failed |
| Cross-Partition Topology | `07` | synthesizer | the `01` Dependency Graph |
| Per-Partition Health Scorecard | `07` | synthesizer | one row per partition |

The Quick Reference row "Cross-partition design decisions" is team only and is
declared with the extensions.

## Who cites what

- Structure worker: skeletons of `01` and `02` in `phases-1-2.md`, plus its two
  extensions. Behavior worker: `03` and `04` in `phases-3-4.md`. Quality worker:
  `05` and `06` in `phases-5-6.md`, plus Cross-Partition Risk Attribution. Each
  keeps its partition-scope rules ("within this partition" goes into content) and
  loses its own heading list.
- Synthesizer: per file, "the skeleton in `<unit>`, plus these extensions", keeping
  its consolidation rule for each section (concatenate, sort, deduplicate). Its
  hard rule that output is indistinguishable from classic now has a test behind it.
- `analyze` already loads the phase units; nothing changes there.

If a worker's measured load rises, the budget is not raised: the plan stops and the
step is reported with the numbers.

## Fold of `analysis-templates.md` and `templates/`

| Section | Destination |
|---|---|
| Verification trust model, iron law, temporal purity, verification requirements, status markers (including the stylesheet form `modal.css::.modal` that `tests/test_xray_stylesheet.py` relies on) | `references/evidence.md` |
| Comment classification, comment quality, documentation diagnosis | `references/phases-5-6.md` |
| Semantic analysis mandate | `references/phases-3-4.md` |
| JSON and Markdown per-file output sections | retired with `templates/semantic_analysis.md` and `templates/analysis_report.md`: no phase file is written from them |

Citers repointed: `evidence.md` (two lines) and the router's References list. The
move check from step 1 runs again over the folded sections.

## Test: `tests/test_xray_skeletons.py`

1. Each phase file `01` to `07` has exactly one skeleton, in its unit's fenced
   block; no role or workflow carries a `# Phase N` skeleton.
2. Every heading a worker or the synthesizer names for a phase file is either in
   that file's skeleton or in the unit's declared extensions.
3. The synthesizer's headings for each file equal the skeleton headings plus the
   extensions declared as written by the synthesizer, in the same order.
4. No heading in a skeleton or a team rule carries a scope qualifier
   (`(by partition)`, `(per partition)`, `(consolidated)`, `(global)`,
   `(within this partition)`, `(Team Mode)`); `(cross-partition)` is allowed only
   in the declared `Hidden Contracts (cross-partition)`.
5. Every heading cited by a consumer exists: the synthesizer's Quick Reference
   targets and the four headings the spec preserves.

## Release

codebase-xray 5.4.0 to 5.5.0 (the team output headings change), skill-catalog
1.0.4 to 1.0.5, marketplace 32.12.0 to 32.13.0. Rebuild, sync docs and Codex
instructions, every gate on an LF extraction, push, watch publication. The step 1
load budgets stay or go down.
