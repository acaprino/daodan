---
name: test-remediation-method
description: >
  Classify test failures before gated quarantine or consolidation, preserving behavior, independent failure modes and bugfix provenance.
---

# Test remediation

Input: `mode=audit|quarantine|consolidate`, prepared native audit/inventory, target,
output root, explicit accepted scope, authorizations and required gate configuration.
Output: native audit or remediation ledger plus project-result envelope. Audit is
report-only; quarantine/consolidation apply only explicitly accepted actions.

Load the `testing:test-hygiene` skill and `project-protocol:project-protocol`. Reuse a prepared
bundle only for the same target and snapshot; otherwise load `testing:test-preparation`.
Before mutation check ownership, preserved starting edits, authorization, baseline,
required local/remote lanes and recovery point. Capture `pre_phase_sha` immediately
before each phase; hard reset requires an exclusively owned clean isolated worktree.
Read `references/audit.md` or `references/consolidate.md` in this skill; a quarantine
request uses the audit's accepted remediation section, not another detection pass.
For quarantine paths, exclusion configuration and the native ledger, read
`references/quarantine-layout.md` inside this skill. This is the sole layout owner.

## Cause classification before disposition

| Cause | Required evidence | Owner/action |
|---|---|---|
| product-defect | Independent contract/oracle disagrees with product behavior | Product implementation owner; keep the regression active and block affected closure |
| wrong-oracle | Authorized requirement or independent expected result disproves the assertion | `testing:test-writer` repairs the oracle, records why; never derive expected result from the tested implementation |
| environment | Dependency, service, credentials, runner or configuration explains failure | Environment/configuration owner; repair setup or explicitly defer affected verification |
| test-isolation | Reproduction identifies leaked state, colliding fixtures or unfinished test work | `testing:test-writer` repairs setup/teardown and proves isolation without losing product regression protection |
| intermittent | Rerun/CI disagreement under recorded comparable conditions | Observed symptom, not a root cause; distinguish product race, test isolation and environment before disposition |
| unknown | Evidence cannot yet distinguish product, oracle or environment | Preserve the test and mark the affected action open; investigate before quarantine |

Skip age, module rename, equal coverage and red CI are not sufficient diagnoses.
Propose quarantine only after classification and assessment of remaining behavioral
protection. Acceptance names exact files, cause, return condition and unresolved
risk; earlier authorization is reused if it already covers those items. An
unanswered inventory row stays. Failed tests are not made irrelevant by moving them.

An intermittent failure can expose a genuine product concurrency, cancellation or
resource-lifecycle defect. Reclassify an evidenced product race as product-defect
and keep its regression active. Repair test-state leaks or resource collisions as
test isolation defects using test-hygiene prevention rule 9. Temporary quarantine
requires evidenced remaining intermittence, owner, return condition, accepted risk
and preserved meaningful protection; adding retries is not causal diagnosis.

Protect distinct failure modes, boundary contracts and tests born from real bugs.
Current implementation is evidence, never its own oracle. Mutation reports are
supporting evidence; surviving mutants are not automatic proof of worthless tests.
Gate the candidate before its commit using same-snapshot evidence. Preserve native
findings, missing measurements and source provenance in the result envelope.
