# Phase 7

## Phase 7: Final Report

Synthesize all `$RUN_DIR/*.md` files (01 through 06) into a consolidated report.

**Context management strategy** (to avoid "lost in the middle" on large codebases):
1. Read each phase file one at a time
2. After reading each file, extract the key findings into a running summary (max 5 bullet points per phase)
3. After processing all 6 files, write the final report from the extracted summaries
4. For detailed sections, cross-reference the original phase files rather than duplicating content

**Output file:** `$RUN_DIR/07-final-report.md`

```markdown
# Codebase X-Ray Analysis Report

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
- Run: [run-id]
- Target: [path]
- Files in inventory: [count] (parsed source: [N], configuration and documentation: [N], presentation: [N]; extensions outside those three sets are absent from every count). Outside the perimeter by rule: [N] dot directories ([names]) and [N] paths Git ignores, ignore rules [applied | unavailable], from the manifest's `scope` block
- Files read in depth: [count, and the list or the directories]
- Exercised at runtime: none. This is static analysis; if the user supplied runtime evidence, cite it here instead
- Phases completed: [list]
- Date: [timestamp]
```

The three coverage lines are mandatory, in the condensed lite report as well. A single file count read as coverage is how a blocking defect in an inventoried component once went unreported: the component was in the inventory, the stylesheet that broke it was not, and nothing had exercised the path. The inventory line names what the perimeter left out for the same reason: `.github/` or a generated client is exactly what a reader assumes was read.

Update `$RUN_DIR/state.json`: set `status` to `"complete"`.
