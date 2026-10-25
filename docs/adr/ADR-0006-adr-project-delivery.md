---
adr_id: ADR-0006
version: 1
title: Extract ADR-driven project delivery into adr-project
status: Proposed
author: Alfio Caprino
scope:
  paths:
    - plugins/adr-project/**
    - plugins/project-lifecycle/**
    - plugins/project-knowledge/**
    - plugins/work-controller/**
    - plugins/daodan/**
  modules:
  domains:
    - project-delivery
    - decision-records
governs_symbols:
depends_on:
created_from_task: adr-project-extraction
proposed_on: 2026-10-25
proposed_at_sha: 3f957279fe68f7e807fb54bf6560ba40df0adb1d
accepted_on: null
accepted_at_sha: null
last_verified_sha: null
retired_on: null
retired_reason: null
supersedes:
superseded_by: null
changes:
---

# ADR-0006: Extract ADR-driven project delivery into adr-project

<!-- adr-header:start -->
Version 1 · Proposed 2026-10-25 by Alfio Caprino
<!-- adr-header:end -->

## Context and Problem Statement

Project decisions, implementation planning and delivery currently span project-knowledge and project-lifecycle. The wave contract also permits a commit before its light review, so a committed step is not necessarily a reviewed working step.

## Decision Drivers

1. ADR-driven project delivery must be installable and usable as one coherent plugin.
2. Daodan remains an umbrella of independently owned plugins that compose through declared providers.
3. Every implementation commit must be bound to successful verification and review of the same unchanged candidate.
4. Existing run recovery, authorization and merge behavior must remain intact.

## Decision

Create `adr-project`, owning `adr-method` and `project-method`. Move the change cycle, specifications, wave plans, resume, verification, final merge and realignment into it. Keep assessment, Senior Maintainer campaigns and handover in `project-lifecycle`; keep guides, instructions and README ownership in `project-knowledge`. Daodan workflows remain thin entries into these providers.

Require each committed wave task to carry a candidate snapshot, a passing verification receipt and a passing pre-commit light review bound to that snapshot. Reject stale, missing or blocked evidence mechanically before a task can be recorded as committed or its wave sealed. Any later edit requires a new snapshot and new evidence.

## Consequences

`adr-project` depends on review, knowledge, mapping and stack specialists. `project-lifecycle` depends on `adr-project` for execution stages. Neither `project-knowledge` nor `senior-review` depends back on `adr-project`: callers supply resolved decision records to their methods. This avoids dependency cycles and preserves independent use.

## Verified Interview Examples

- **EX-001** (nominal): Input: a task with passing verification and a PASS light review on candidate digest D -> Expected: the task may be recorded as committed on D and the wave may seal when all tasks satisfy the gate.
- **EX-002** (boundary): Input: the task files change after review D -> Expected: committed status and wave sealing are refused until verification and review are repeated on the new digest.

## Rejected Alternatives

- **RA-001**: leave ADR in project-knowledge and only rename project-lifecycle; rejected because decision ownership and project delivery would remain split.
- **RA-002**: commit each task before its light review; rejected because a blocked review would leave an unverified step in branch history.

## Enforceable Invariants

- **INV-001**: no wave task reaches `committed` without verification and PASS review receipts naming its exact candidate snapshot.
- **INV-002**: no wave reaches `sealed` while any task lacks a valid pre-commit evidence chain or is not committed.
- **INV-003**: `project-knowledge` and `senior-review` never require `adr-project`; resolved decisions cross their boundaries as inputs.

## Confirmation

Run the work-record behavioral tests, ADR tests, compiler and host contract suites, dependency and bundled-path linters, documentation parity and full unittest discovery. Build every host and verify deterministic output. Installed-host execution remains separately reported when not exercised.
