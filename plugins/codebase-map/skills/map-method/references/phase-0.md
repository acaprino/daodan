# Phase 0

## Phase 0: Project Knowledge Discovery

Runs in **every depth, including `--depth=lite`**, and runs first, in the orchestrating context: reading project instructions and globbing for index files is cheap, and what it finds shapes what every later phase looks for.

Phases 1 through 7 keep their numbers. `--phase N` is a user-facing flag and renumbering would break every invocation that names a phase.

**Phase 0 is a preamble, not a selectable analysis phase.** It runs before every invocation, `--phase 5` and `--docs-only` included, and it does not change the numbering semantics of phases 1 to 7. `--phase 5` still means "run phase 5 and nothing else from the analysis set", with the preamble in front of it. `--phase 0` runs the preamble alone, which is a legitimate way to ask only "how does this repository document itself".

This phase owns discovery of **how the repository documents itself**. It does not evaluate whether the documentation is accurate, which is Phase 6.

1. Read `CLAUDE.md`, `AGENTS.md` and any equivalent project instruction file at the repository root and in the target's ancestors. Record any navigation instruction they give, especially a statement of the form "look here first to find where a concept lives".
2. Locate the canonical indexes the project actually uses. Glob for, at minimum: `**/SEARCH_INDEX.md`, `**/INDEX.md`, `docs/README.md`, `README.md`, `**/BY_DOMAIN.md`, `**/adr/**`, `**/decisions/**`, `**/architecture/**`, `**/domains/**`. Record what exists, not what you expected to exist. The perimeter applies here as everywhere: an index under a dot directory, or one Git ignores, is not a lead.
3. For each concept, symbol and subsystem in the analysis scope, search the located documents for an entry. Record the concept, the document, and the anchor or heading that matched.
4. Write both output files. Every row is a lead with status `documented` or `unverified`. Nothing here is `verified`, because this phase reads no code.

`$RUN_DIR` below is the active run directory, `.codebase-map/runs/<run-id>/`, per the Concurrent Runs Model in `references/run.md`.

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
[How this repository organizes its knowledge, in prose. Name the file the project treats as its semantic index, if it has one.]

## Not found
[Index kinds searched for and absent. An absent index is a fact worth recording.]
```

**Output file:** `$RUN_DIR/knowledge/documentation-leads.md`

```markdown
# Documentation Leads

> Leads, not truth. Every row is a pointer to where the project claims a concept lives.
> Status is `documented` or `unverified`. No row here is `verified`: this phase reads no code.

| Concept / symbol | Document | Anchor | Status |
|------------------|----------|--------|--------|

## Concepts in scope with no lead
[Concepts the scope touches for which no document was found. This list is what a
downstream consumer must discover independently.]
```

This unit is the only copy of Phase 0. `/codebase-map:analyze` runs it before its first analysis phase, and `/codebase-map:team-analyze` runs it once for the whole run. `/senior-review:team-review` reaches this phase through the `analyze` workflow, and its Phase 1d consumes `knowledge/documentation-leads.md` from whichever path produced the run.
