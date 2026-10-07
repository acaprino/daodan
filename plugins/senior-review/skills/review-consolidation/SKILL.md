---
name: review-consolidation
description: >
  Consolidate native review findings with evidence provenance, delivery accounting and adversarial verification.
---

# Review consolidation

Input: variant, prepared brief/context/selection, native reviewer results, delivery
ledger. Output: the existing native review report
plus a project-result envelope. Keep canonical native reports; use the existing
review contracts to integrate their findings, without another finding schema.

Read `references/stack-findings.md` inside this skill before confidence filtering
or severity sorting. It defines how the specialist outputs enter the native review
contract while retaining original labels, source roles and evidence. Validate
required fields before treating a specialist delivery as complete.

Load the `senior-review:review-quality-gates` skill. Before consolidation account for every
selected reviewer, including stack specialists, failure, timeout or incomplete
delivery. Use one input finding set and delivery ledger for all dimensions;
preserve source role, native severity, premise and evidence provenance. Never merge
a failed worker into a successful result. A single final writer emits the report.

Read `references/<variant>.md` inside this skill. Execute its consolidation, fresh
verification lenses, completeness check and report stages. For PR review, use the
same delivery/provenance/panel rules before producing the native PR description.
Two reviewers inheriting the same premise are an echo, not independent corroboration.
Deduplication preserves independent evidence and distinct failure modes.

Load the `project-protocol:project-protocol` skill to validate the snapshot and publish the
result envelope. A report can complete with explicitly degraded coverage; it cannot
claim a missing reviewer ran, or that static analysis exercised runtime behavior.
