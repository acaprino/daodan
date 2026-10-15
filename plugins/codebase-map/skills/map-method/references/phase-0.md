# Phase 0

## Phase 0: Project Knowledge Discovery

Run first on every fresh run at every depth, including `--depth=lite`, `--phase N` (N from 1 to 6) and `--docs-only`. For `/codebase-map:analyze`, the isolated analyst runs Phase 0; for `/codebase-map:team-analyze`, the entry runs it once globally. A resume can inherit confirmed knowledge files. Phase 0 is a nonselectable preamble; phases 1 to 7 retain their numbers. Refuse `--phase 0` and `--phase 7`.

Discover how the repository documents itself to guide phases; leave accuracy evaluation to Phase 6.

1. Read `CLAUDE.md`, `AGENTS.md` and any equivalent project instruction file at the repository root and in the target's ancestors. Record navigation instructions, especially where to look first for a concept.
2. Find the canonical indexes actually used. Glob at minimum: `**/SEARCH_INDEX.md`, `**/INDEX.md`, `docs/README.md`, `README.md`, `**/BY_DOMAIN.md`, `**/adr/**`, `**/decisions/**`, `**/architecture/**`, `**/domains/**`. Record existing and absent index kinds. Apply the perimeter: indexes under dot directories or ignored by Git are not leads.
3. For every scoped concept, symbol and subsystem, search those documents; record the concept, document and matching anchor or heading.
4. Write both files below. Every row is a `documented` or `unverified` lead, never `verified`; this phase reads no code.

`$RUN_DIR` is the active `.codebase-map/runs/<run-id>/` directory, per the Concurrent Runs Model in `references/run.md`.

**Output file:** `$RUN_DIR/knowledge/navigation.md`

```markdown
# Project Knowledge Navigation

## Project instructions read
| File | Navigation rule it states |
|------|---------------------------|

## Canonical indexes found
| Index | Path | What it indexes |
|-------|------|-----------------|

## Conventions observed
[Describe knowledge organization in prose; name the semantic-index file, if any.]

## Not found
[Searched-for index kinds that are absent.]
```

**Output file:** `$RUN_DIR/knowledge/documentation-leads.md`

```markdown
# Documentation Leads

> Discovery leads, never verified facts: pointers to where the project claims a concept lives.
> Status: `documented` or `unverified`, never `verified`; this phase reads no code.

| Concept / symbol | Document | Anchor | Status |
|------------------|----------|--------|--------|

## Concepts in scope with no lead
[List scoped concepts with no document, which downstream consumers must discover independently.]
```

This unit is Phase 0's only copy. `/senior-review:team-review` reaches it through `analyze`; Phase 1d consumes `knowledge/documentation-leads.md` from whichever path produced the run.
