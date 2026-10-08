# Scope-aware Skill Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. The approved design and implementation request authorize continuous execution in this session.

**Goal:** Select available knowledge skills for any stack and bind their use to the unified review.

**Architecture:** A leaf catalog provider indexes metadata, selects by candidate scope and locks selected content. The compiler emits metadata and adapter inventory instructions; senior-review prepares and accounts for the same bindings throughout its existing pipeline.

**Tech Stack:** Standard-library Python, Markdown behavior, TOML metadata/contracts and existing five-host compiler.

**Spec:** ../specs/2026-10-07-skill-catalog-design.md

## Global Constraints

- Edit content kernels and adapters; exports are generated only.
- Preserve required method/role dependencies, isolated contexts and one report.
- Resolve only actual host/project inventory; unknown is never installed or reviewed.
- Read knowledge bodies on demand, bind exact candidate/run/snapshot and fail selected loads explicitly.
- Helpers write no project or package files; project-protocol persists run-owned records.
- Preserve preexisting edits. The checkout was clean at `2b572848`.
- Implementation remains local; commits and publication are outside this request.

## Review Focus

- A generated index mistaken for installed coverage: explicit inventory intersection.
- Metadata changes between selection and loading: exact metadata and body fingerprints.
- Unclassified external workflow mistaken for knowledge: unknown kind is a gap.
- Windows junction or traversal in a selected reference: resolved root confinement.
- Thousands of irrelevant bodies loaded during discovery: metadata-only search and lazy reads.

### Task 1: Runtime catalog

Files: create `plugins/skill-catalog/skills/skill-catalog/scripts/catalog.py` and `tests/test_skill_catalog.py`.
Interfaces: `metadata_for(directory)`, `index_inventory(declared, inventory)`,
`search(catalog, query, operation, limit=20)`, `select(catalog, request)`,
`prepare(catalog, request)`, `load_skill(selection, identity)`,
`read_reference(selection, identity, relative)`, `validate_usage(selection, usages)`.

- [x] Write behavioral fixtures for the spec's selection, lazy-read and failure cases.
- [x] Run `python -B -m unittest tests.test_skill_catalog`; expect missing helper failures.
- [x] Implement metadata-only discovery, exact scope selection and fingerprinted reads.
- [x] Run the same tests; expect all pass.

### Task 2: Compiler and metadata

Files: create `scripts/daodan/skill_catalog.py`, catalog kernel and knowledge sidecars;
modify `scripts/daodan/render.py`, `validate.py` and five adapter catalog instructions.
Interfaces: `declared_catalog(registry)`, `validate_skill_metadata(plugin)` and generated
`skills/skill-catalog/references/catalog.json` plus `references/host-inventory.md`.

- [x] Add compiler tests for malformed metadata, exact registered skills and five-host deterministic output.
- [x] Run tests; expect absent compiler integration failures.
- [x] Implement validation/index rendering and annotate existing knowledge at its owner.
- [x] Run compiler/catalog tests; expect pass.

### Task 3: Review integration

Files: senior-review preparation/method/consolidation, roles and contracts;
repository dependency policy, host/plugin documentation and dependency tests.
Interfaces: prepared briefs carry `knowledge_selection`; bindings carry `knowledge_ids`;
results carry `knowledge_usage`; final report carries knowledge coverage/gaps.

- [x] Add port tests for catalog ownership, reuse, loading failure and per-worker accounting.
- [x] Run port tests; expect missing integration failures.
- [x] Connect discovery/preparation, scoped worker knowledge and consolidation once.
- [x] Run port/dependency tests; expect pass.

### Task 4: Publication artifacts and review

- [x] Bump changed owner versions and marketplace version; regenerate five hosts and docs/instructions.
- [x] Run full unit suite, consistency linters, documentation/instruction parity and build drift gate.
- [x] Obtain one fresh-context whole-change review and fix material findings with regressions.
- [x] Preserve the local changes and report verified results plus installed-host limits.

## Verified result

Marketplace 32.0.0 adds skill-catalog 1.0.0; senior-review 15.0.0 is its first
automatic consumer. All 38 changed existing owners have version increments.
The five exports reproduce from their kernels. The complete suite passes 501 tests
with one symbolic-link fixture skipped for local OS privilege; native Windows
junction probes passed separately. Dependency, bundled-path, host-vocabulary,
registration, fact-anchor, documentation/instruction parity and confinement-policy
checks pass. Real catalog CLI fixtures pass in all five compiled package layouts.

One fresh-context review identified three P2 issues: an empty/truncated selection
bypassing usage validation, an unassigned dimension hidden by flattened workers,
and LF/CRLF disagreement between declaration and installed metadata. Each has an
observed failing regression followed by a passing fix and green full suite.

Verification decisions: installed-host inventory and end-to-end dispatch remain
unverified; a host's inventory procedure may still need adaptation. Native Windows
junction rejection was verified at the provider root and inside references using
owned temporary fixtures; other filesystem configurations remain outside that
probe and may require additional regression coverage. Changes remain local.
