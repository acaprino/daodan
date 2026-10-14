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

Load the `skill-catalog:skill-catalog` skill and run `validate-usage` against the
prepared `knowledge_selection` and all worker `knowledge_usage` records. Verify
every assigned scope/worker, the selection/body fingerprints and used references.
Failed, stale or missing selected knowledge is failed delivery coverage; any required
candidate gate stays unsatisfied. Keep unresolved inventory/classification/match
gaps in `knowledge_coverage` and the same report's coverage section. Loaded knowledge
does not prove that code paths ran, or establish a finding's premise. Preserve
knowledge provenance with each finding; generic knowledge patterns still need code
evidence and falsifiable premises. An independent derivation may use generic domain
knowledge, never shared project conclusions or peer findings.

Read `references/<variant>.md` inside this skill. Execute its consolidation, fresh
verification lenses, completeness check and report stages. For PR review, use the
same delivery/provenance/panel rules before producing the native PR description.
Two reviewers inheriting the same premise are an echo, not independent corroboration.
Deduplication preserves independent evidence and distinct failure modes.

Load the `project-protocol:project-protocol` skill to validate the snapshot and publish the
result envelope. A report can complete with explicitly degraded coverage; it cannot
claim a missing reviewer ran, or that static analysis exercised runtime behavior.

## Optional human view

The final writer saves the complete native Markdown report in the prepared owned
output root, using the caller's declared report path or the variant's filename.
Generate report content once. In the conversation link to native details with the
verdict, material findings and remaining gaps, except when a required approval or
the user's request needs the complete text. Workers deliver their native reports;
they do not produce separate UI or another final synthesis.

When the user requests HTML, or navigation and finding-table filters would
materially aid review, load the `report-rendering:report-renderer` skill and resolve its
helper through that skill. Use the saved native Markdown as `--input`, its
same-stem `.html` sibling as `--output`, `--profile review`, and the same prepared
owned output root as `--root`. The fixed renderer supplies controls, without new
analysis, finding content or a second finding schema. Keep the native report as
the authoritative `output_path`; account for the HTML only as a derived view.

Preserve all native sections and fields, source roles and severities, evidence,
confidence, premises and their provenance, verification results, filtered counts,
knowledge coverage, coverage gaps and degraded or unknown states. Link to native
worker and verification details instead of copying their full content into another
layout. Output economy never removes required evidence, independent premise
reconstruction, verification lenses or completion gates.

Verify the helper outcome before claiming delivery. Diagnose a rendering error
through the provider's recovery contract and preserve native Markdown. If the
view still fails, record the optional view failure explicitly and do not list it
as a successful output. An explicitly requested HTML deliverable remains open;
an unrequested optional view failure leaves the native review outcome intact.
