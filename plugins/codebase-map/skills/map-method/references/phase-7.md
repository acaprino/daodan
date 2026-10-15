# Phase 7

## Phase 7: Final Report

Synthesize all `$RUN_DIR/*.md` files (01 through 06) into a consolidated report.

Read phase files sequentially and retain up to five key-findings bullets per
phase. Synthesize after all six; link detailed phase reports. This context limit
never removes required sections or evidence.

**Output file:** `$RUN_DIR/07-final-report.md`

```markdown
# Codebase Map Analysis Report

## Target
[From scope]

## Executive Summary
[2-3 sentences on overall codebase health]

## Project at a Glance
[2-3 paragraph narrative explaining what this project does, who it's for, and how it works - written for someone who has never seen the codebase]

## Architecture Overview
[Mermaid diagram + narrative from Phases 1-2]

## Technology Decisions
[Key tech choices and why they were made - useful for presentations and onboarding]

## Critical Paths
[Key findings from Phase 3]

## Key Process Diagrams
[Include the most important Mermaid flowcharts from 03-flows.md - select 3-5 diagrams that best represent the system's core processes. Prioritize E2E and Functional diagrams over Technical ones. Reference 03-flows.md for the complete set.]

## Design Insights
[Key findings from Phase 4]

## Risk Assessment
| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Anti-patterns | X | X | X | X |
| Security risks | X | X | X | X |
| Usability-blocking | X | X | X | X |
| Technical debt | X | X | X | X |
| Doc gaps | X | X | X | X |

## Documentation vs Reality
[Discrepancies found between existing docs and actual code behavior - useful for doc maintenance]

## Top Priority Actions
1. [Most important fix/improvement]
2. [Second priority]
3. [Third priority]

## Detailed Findings
[Cross-references to phase files for full details]

## Quick Reference: Which File to Consult

| Your Task | Start With | Also Check |
|-----------|-----------|------------|
| Onboarding / understanding the project | 07-final-report, 01-structure | 04-semantics |
| Writing new feature | 01-structure (Where to Add), 02-interfaces | 04-semantics |
| Fixing a bug | 03-flows, 05-risks | 01-structure |
| Refactoring | 01-structure, 04-semantics, 05-risks | 03-flows |
| Code review | 02-interfaces, 05-risks | 06-documentation |
| Updating documentation | 06-documentation, 04-semantics | 02-interfaces |
| Creating report/presentation | 07-final-report, 01-structure | 04-semantics |
| Finding doc vs code discrepancies | 06-documentation | 03-flows, 05-risks |

## Analysis Metadata
- Mode: classic
- Run: [run-id]
- Target: [path]
- Files in inventory: [count] (parsed source: [N], configuration and documentation: [N], presentation: [N]; extensions outside those three sets are absent from every count). Outside the perimeter by rule: [N] dot directories ([names]) and [N] paths Git ignores, ignore rules [applied | unavailable], from the manifest's `scope` block
- Files read in depth: [count, and the list or the directories]
- Exercised at runtime: none. This is static analysis; if the user supplied runtime evidence, cite it here instead
- Phases completed: [list]
- Date: [timestamp]
```

The three coverage lines are mandatory, including in the condensed lite report.

For requested or useful HTML, only the entry coordinator loads `references/human-view.md`.
Workers never load presentation instructions. The entry coordinator marks the run
complete only after native delivery and every requested view pass their gates.

## Team mode

### Team extensions

| Heading | File | Mode | Writer | After | Aggregation |
|---|---|---|---|---|---|
| Partial Completeness Warning | 07-final-report.md | consolidated | partition-synthesizer | first | Only for failed partitions; name them and the incomplete sections. |
| Partition Map | 07-final-report.md | consolidated | partition-synthesizer | Project at a Glance | Repeat the 01 Partition Map. |
| Cross-Partition Topology | 07-final-report.md | consolidated | partition-synthesizer | Project at a Glance | Repeat the 01 Dependency Graph. |
| Per-Partition Health Scorecard | 07-final-report.md | consolidated | partition-synthesizer | Design Insights | One row per partition: anti-pattern/red-flag C/H/M/L, doc gaps, debt and health. |

### Partition worker

The report is written by the synthesizer, not partition workers.

### Consolidation

| File | Common heading | Rule |
|---|---|---|
| 07-final-report.md | Executive Summary | Derive overall health from consolidated risk and documentation files. |
| 07-final-report.md | Project at a Glance | Aggregate semantics, or structure observations when semantics is absent. |
| 07-final-report.md | Architecture Overview | Synthesize 01 and 02. |
| 07-final-report.md | Technology Decisions | Aggregate partition technology choices. |
| 07-final-report.md | Critical Paths | Use Cross-Partition Flows when present; otherwise partition critical paths. |
| 07-final-report.md | Key Process Diagrams | Prioritize cross-partition end-to-end diagrams. |
| 07-final-report.md | Design Insights | Use Cross-Partition ADR when present. |
| 07-final-report.md | Risk Assessment | Keep the severity matrix and add a Cross-Partition Risk Attribution row. |
| 07-final-report.md | Documentation vs Reality | Aggregate mismatches. |
| 07-final-report.md | Top Priority Actions | Critical/high findings with cross-partition impact and citations. |
| 07-final-report.md | Quick Reference: Which File to Consult | Add the team-only cross-partition design-decisions row: 04 Cross-Partition ADR and 01; also 02 Cross-Partition Exports. Code review also checks 08. |
| 07-final-report.md | Analysis Metadata | Mode: team; include partition count/list; coverage comes from the consolidated reading ledger, not new source reads. |
