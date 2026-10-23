# Reading an analysis

Coordinators: before lookup, run `python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/migrate_root.py" --project <project-root>`; require exit 0.
Workers only resolve bindings; legacy bindings require migration.

## Views

Generate `semantic-map.md` with `semantic_map.py MANIFEST --path AREA`; unread/stale
cards use `deepen.md`. Keep provenance and existing phase reports.

| Task | Start | Also |
|------|------------|------------|
| Onboarding | 07-final-report, 01-structure | 04-semantics |
| Feature | 01-structure, 02-interfaces | 04-semantics |
| Bug | 03-flows, 05-risks | 01-structure |
| Refactoring | 01-structure, 04-semantics, 05-risks | 03-flows |
| Review | 02-interfaces, 05-risks | 06-documentation |
| Documentation | 06-documentation, 04-semantics | 02-interfaces |
| Concepts | knowledge/documentation-leads.md | knowledge/navigation.md |

Phase 0's `knowledge/` holds unverified leads; `team-review` Phase 1d joins
`knowledge/documentation-leads.md` with independent discovery. Skipping Phase 0 loses that input.
