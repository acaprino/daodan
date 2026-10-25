---
adr_id: ADR-0008
version: 1
title: Consolidate review and project knowledge into drkerr
status: Proposed
author: Alfio Caprino
scope:
  paths:
    - plugins/drkerr/**
    - plugins/daodan/**
    - plugins/project-delivery/**
    - plugins/project-lifecycle/**
    - plugins/work-controller/**
    - scripts/**
    - docs/**
    - tests/**
    - evals/**
    - CLAUDE.md
    - README.md
  modules:
  domains:
    - code-review
    - project-knowledge
    - documentation
governs_symbols:
depends_on:
created_from_task: drkerr-consolidation
proposed_on: 2026-10-25
proposed_at_sha: 48c58f546746cda1d4c0c7880f490767e7dd94fa
accepted_on: null
accepted_at_sha: null
last_verified_sha: null
retired_on: null
retired_reason: null
supersedes:
superseded_by: null
changes:
---

# ADR-0008: Consolidate review and project knowledge into drkerr

<!-- adr-header:start -->
Version 1 · Proposed 2026-10-25 by Alfio Caprino
<!-- adr-header:end -->

## Context and Problem Statement

Code review, documentation review and documentation authoring currently live in two plugins, `senior-review` and `project-knowledge`. The requested canonical owner for the combined capability is `drkerr`. The migration must change identities without losing the existing methods, reviewer catalog, documentation writers or evidence contracts.

## Decision Drivers

1. One canonical owner for review and durable project knowledge.
2. Existing component behavior and provider boundaries remain intact unless separately changed.
3. Generated host packages reproduce from kernels and require no hand editing.
4. Historical run records and dated design evidence remain readable and are not rewritten as if they used the new identity.
5. The dependency graph has no self-edge or second owner for the consolidated capabilities.

## Decision

Consolidate both kernels into `plugins/drkerr`. New runtime references use `drkerr:<component>`. Preserve component filenames, review compositions and contracts. The manifest contains the union of required dependencies, excluding the retired internal edge between the two former plugins. `text-humanizer@shinatama` remains required.

Update consumers, compiler special cases, tests, documentation and the dependency table. Regenerate every host and the documentation indexes. `work-controller` accepts historical `senior-review` process-role bindings only as legacy evidence where its recorded support permits them; new reviews use `drkerr` identities. Historical reports, ADRs and run records are not rewritten.

## Consequences

The former plugin directories and current documentation pages are retired. No compatibility plugin duplicates ownership. Consumers must depend on `drkerr`. Historical references describe the old state and carry no installation or dispatch guarantee.

## Rejected Alternatives

- **RA-001:** keep `senior-review` and `project-knowledge` as parallel compatibility owners; rejected because it preserves two canonical identities and increases dependency and documentation duplication.
- **RA-002:** rename only prose and marketplace labels while retaining old qualified component IDs; rejected because it creates inconsistent runtime and documentation identities.

## Enforceable Invariants

- **INV-001:** all new component references and dispatch bindings resolve to `drkerr` or another declared provider.
- **INV-002:** `drkerr` declares no dependency on `senior-review` or `project-knowledge`, and no local consumer retains a runtime dependency on those retired identities.
- **INV-003:** the five host packages, registration, bundled paths, documentation and instruction parity checks reproduce from the consolidated kernel.
- **INV-004:** historical records remain readable without granting them new execution or transition authority.

## Verified Interview Examples

- **EX-001** (nominal): Input: a new review references `drkerr:review-method` -> Expected: the consolidated provider resolves, all consumer references resolve and every host package reproduces from its kernel.
- **EX-002** (boundary): Input: a historical record carries `senior-review:premise-auditor` -> Expected: it remains readable under its original support binding, while a new dispatch with a retired provider identity is rejected.
- **EX-003** (failure): Input: a consumer retains a runtime dependency on `senior-review` or `project-knowledge` -> Expected: dependency validation fails and names the stale reference.

## Confirmation

Run the dependency, registration, bundled-path, fact-anchor and host-vocabulary linters; compiler and host contract tests; reviewer catalog, roster, composition and work-record tests including legacy bindings; all-host build and drift checks; documentation and Codex instruction parity checks. Live host execution remains separate evidence.
