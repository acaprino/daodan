---
name: project-bootstrap
description: >
  Draft missing ADR and FRD from verified project evidence without turning legacy behavior or stale documentation into approved requirements.
  TRIGGER WHEN: a project has no ADR or FRD, existing project knowledge must be bootstrapped from code, documentation or Codebase Map, or /daodan:init-project needs initial requirement records.
  DO NOT TRIGGER WHEN: recording one already understood decision (use adr-method), editing an existing FRD (use frd-method), or running the implementation cycle (use delivery-method).
---

# Project knowledge bootstrap

Load `work-controller:work-record`, `project-delivery:adr-method` and
`project-delivery:frd-method`. Work in an owned run; generated records are drafts
and no project behavior changes.

## 1. Inventory and evidence

Detect `docs/adr/README.md` and the FRD index. Validate existing records before
using them; missing artifacts are a drafting request, not permission to invent.
Inventory documentation, source, tests and configuration. Use
`codebase-map:map-method` to validate or refresh a current completed map and
maximize structural discovery. If no current completed map exists, search and read
the source directly and record reduced structural coverage. A map is static
evidence, never a correctness verdict.

Classify each input claim as observed, documented or derived. Verify behavioral
documentation against current source and tests before using it. Contradictions
become explicit FRD conflicts or user questions. Unexercised runtime behavior is
a limitation, never a silent pass.

## 2. Draft and reconcile

Extract FRD requirements, entities, relations and exact evidence spans through
`frd-method`. Include only evidenced people, organizations, locations and
relations; uncertainty stays explicit. Draft architectural decisions only when
the evidence supports a real design choice and alternatives. Current behavior is
a candidate explanation, not an approved requirement.

Write Proposed artifacts through the helpers. Preserve source digests and manual
corrections on every later merge. Review contradictions with the user, then run
the relevant document/spec review. Only explicit approval promotes an artifact.
After implementation, reconciliation and verification use the same candidate and
merge gates as every other delivery.
