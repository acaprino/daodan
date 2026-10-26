---
adr_id: ADR-0007
version: 1
title: Coordinate evidence-bound project evolution in Project Delivery
status: Proposed
author: Alfio Caprino
scope:
  paths:
    - plugins/project-delivery/**
    - plugins/work-controller/**
    - docs/frd/**
  modules:
  domains:
    - project-delivery
    - requirements-engineering
    - decision-records
governs_symbols:
depends_on:
created_from_task: project-delivery
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

# ADR-0007: Coordinate evidence-bound project evolution in Project Delivery

<!-- adr-header:start -->
Version 1 · Proposed 2026-10-25 by Alfio Caprino
<!-- adr-header:end -->

## Context and Problem Statement

Project Delivery coordinates analysis, debugging, fixes, features and complete project documentation. Its delivery-method needs one evidence-bound flow from interview to merge, comparable in guidance to Superpowers but stronger in provenance, adversarial verification, resumability and handoff.

## Decision Drivers

1. Specifications come from a Wayfinder-style interview grounded in actual code and existing documents.
2. Codebase Map maximizes discovery and impact analysis but remains static evidence, never a correctness oracle.
3. Implementation plans contain bit-sized jobs with explicit oracles and pass adversarial review before execution.
4. Work Controller in Daodan owns graph and job execution and conservative resume; the local model-routing provider owns confirmed model selection and pricing. Installed-host dispatch, cross-session handoff and observed per-job models require their own execution evidence.
5. ADR and FRD require versioned, verifiable artifacts; current behavior and stale documentation never become approved requirements automatically.

## Decision

Project Delivery owns delivery-method, adr-method, frd-method and project-bootstrap. delivery-method coordinates investigation, specification, planning, adversarial plan review, execution, verified commits, reconciliation, final review and merge. It delegates execution to work-controller@daodan and specialist work to their owners rather than vendoring Superpowers or creating another scheduler. A process binding preserves the work record's grants, deliveries and current-candidate gates; an engine success cannot satisfy those domain checks by itself.

FRD records requirements plus people, organizations, locations, relationships and source spans. Spans use Unicode [start,end) offsets, document digest and excerpt. Manual corrections use optimistic digests and persist across re-extraction. Bootstrap proposes missing ADR and FRD from code, documentation and Codebase Map, verifies claims against source and declares runtime gaps. Generated records remain Proposed until approved.

## Consequences

Planning and execution share the run record and exact candidate bindings. Every job is resumable after interruption and transferable through the agenda and explicit session takeover. Documentation owners remain independent; Project Delivery composes them for complete documentation activities.

## Verified Interview Examples

- **EX-001** (nominal): Input: a feature request on a mapped repository -> Expected: a grounded interview specification, a bit-sized plan with base-failing oracles and an adversarial PASS before any execution job.
- **EX-002** (boundary): Input: a plan step reviewed on digest D that changes before execution -> Expected: execution and commit remain blocked until planning or review is repeated on the new candidate.

## Rejected Alternatives

- **RA-001**: execute a plan immediately after its structural validation; rejected because validation does not challenge premises, feasibility or oracle quality.
- **RA-002**: vendor Superpowers or build a second graph executor inside delivery-method; rejected because ownership would diverge and resume semantics would weaken.

## Enforceable Invariants

- **INV-001**: no execution job starts without an approved specification and an adversarially reviewed bit-sized plan on the same candidate.
- **INV-002**: every executable job has stable identity, owned paths, oracle, verification, resume state and session-handoff binding.
- **INV-003**: generated ADR and FRD preserve evidence and conflicts and cannot become Accepted without explicit approval.

## Confirmation

Verify interview and plan contracts, adversarial review gates, graph execution and resume, FRD spans and manual corrections, bootstrap source verification, commit and merge gates, all host renderings and live evals separately when available.
