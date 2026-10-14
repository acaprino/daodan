# Reading an analysis

Coordinators: before output lookup, run `python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/migrate_root.py" --project <project-root>`.
Require exit 0. Workers only resolve bindings; legacy roots/bindings activate migration load.

## Output Usage Guide

Consult these files:

| Your Task | Start With | Also Check |
|-----------|-----------|------------|
| Onboarding / understanding the project | 07-final-report, 01-structure | 04-semantics |
| Writing new feature | 01-structure (Where to Add), 02-interfaces | 04-semantics |
| Fixing a bug | 03-flows, 05-risks | 01-structure |
| Refactoring | 01-structure, 04-semantics, 05-risks | 03-flows |
| Code review | 02-interfaces, 05-risks | 06-documentation |
| Updating documentation | 06-documentation, 04-semantics | 02-interfaces |
| Finding where the project documents a concept | knowledge/documentation-leads.md | knowledge/navigation.md |

Phase 0's `knowledge/` files contain discovery leads, never verified facts.
`/senior-review:team-review` Phase 1d joins `knowledge/documentation-leads.md`
against independent discovery; skipping Phase 0 leaves that input missing.
