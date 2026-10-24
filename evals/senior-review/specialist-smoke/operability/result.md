# Operability review

- dimension: operability
- reviewer: senior-review:operability-auditor
- status: delivered
- output_path: evals/senior-review/specialist-smoke/operability/result.md
- knowledge_usage: []
- gaps: []

## Findings

### A: Renaming the column interrupts active v1 instances

- file: migration-a.sql
- line: 1
- severity: High
- confidence: 99
- confidence_rationale: The authoritative requirements explicitly identify the v1 column read, migration-before-v2 ordering, continued v1 service and absence of compatibility mappings. The single rename statement directly removes that column name. This establishes the compatibility failure with very high confidence through static reasoning; no runtime reproduction was performed.
- evidence_class: derived
- premise_provenance: independent
- premise: `requirements.md:3-8` makes the proposals independent, requires both versions to serve during rollout, keeps v1 active until v2 is healthy, and runs the migration before v2 starts. v1 reads `customers.name`; no alias, view or query rewrite exists.
- trigger: Execute Proposal A's migration while v1 is still serving, as required by `requirements.md:10`.
- evidence: `migration-a.sql:1` renames `name` to `display_name`, removing the column name used by v1. Subsequent v1 reads of that column fail before any v2 instance starts; the required mixed-version serving interval therefore cannot be maintained.
- counterevidence_checked:
  - The stated sequence drains v1 only after starting v2; it provides no earlier drain or compatibility mapping. Proposal B preserves `name`, but is an independent proposal and is not part of A's release.
- fix_direction: Expand the schema with `display_name` while retaining `name`, populate it under an appropriate write-consistency contract, then deploy v2. Defer removal of `name` until v1 and any supported rollback requirement no longer need it. Proposal B already supplies an expansion and a contract that disables writes.

## Scope and checks

Read all three assigned sources: `requirements.md`, `migration-a.sql` and `migration-b.sql`. Traced each independent proposal from the starting schema through its pre-start migration, mixed-version interval and stated rollback constraints. No base/candidate comparison was assigned, so introduction status is not assessed.

No operability defect found in Proposal B within this contract: `migration-b.sql:1-2` adds and populates `display_name` while retaining `name`. `requirements.md:11-13` retains the old column throughout the rollback window, disables writes during migration and permits only reads during rollout, so the supplied scenario does not establish divergent writes or an incompatible reader.

Static source inspection only. No database, application, deployment or probe execution occurred. Engine-specific locks, migration duration, runtime success and deployment controls are not established by these inputs; no timing or availability behavior beyond the explicit missing-column consequence is claimed.
