# Reading an analysis

## Output Usage Guide

After analysis completes, consult the right file for your task:

| Your Task | Start With | Also Check |
|-----------|-----------|------------|
| Onboarding / understanding the project | 07-final-report, 01-structure | 04-semantics |
| Writing new feature | 01-structure (Where to Add), 02-interfaces | 04-semantics |
| Fixing a bug | 03-flows, 05-risks | 01-structure |
| Refactoring | 01-structure, 04-semantics, 05-risks | 03-flows |
| Code review | 02-interfaces, 05-risks | 06-documentation |
| Updating documentation | 06-documentation, 04-semantics | 02-interfaces |
| Finding where the project documents a concept | knowledge/documentation-leads.md | knowledge/navigation.md |

The two `knowledge/` files are Phase 0 output and are the only files in the set produced without reading code: every row is a lead, never a verified fact. `/senior-review:team-review` Phase 1d reads `knowledge/documentation-leads.md` from the run directory and joins it against its own independent discovery, so a run that skips Phase 0 leaves that consumer with an empty half.
