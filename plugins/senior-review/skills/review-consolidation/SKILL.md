---
name: review-consolidation
description: >
  Consolidate native review findings with evidence provenance, delivery accounting and adversarial verification. Load when consolidating code-review, team-review or pr-review results.
---

# Review consolidation

Input: variant, prepared context/selection, native results and delivery ledger.
Output: native report and project-result envelope through existing review contracts,
without another finding schema.

Read `references/stack-findings.md` before confidence filtering or severity sorting.
Retain native labels, roles and evidence; validate required delivery fields.

Load `senior-review:review-quality-gates`. Account for every expected job and
member/scope obligation against candidate/body-bound deliveries before filtering.
Validate `member_results`, including failures, timeouts and incomplete coverage.
Share canonical finding IDs without duplicating findings; preserve source role,
native severity, premise and evidence provenance in one ledger. Failed or missing
required coverage prevents completion; never merge failure into success.
A single final writer emits the report.

Account separately for blind derivation, critic and eligible verification lenses
under work-controller; discovery cannot satisfy a check through its job ID, file
or context. Historical records retain their original contract.

Load `skill-catalog:skill-catalog`; run `validate-usage` against prepared
`knowledge_selection` and worker `knowledge_usage`. Verify assigned scope/worker,
selection/body fingerprints and used references. Failed/stale/missing selected
knowledge fails delivery coverage and leaves required candidate gates unsatisfied.
Preserve inventory/classification/match gaps in `knowledge_coverage` and report
coverage. Knowledge neither proves execution nor establishes a finding's premise.
Generic patterns require source evidence and falsifiable premises. Independent
derivation may use domain knowledge, never shared project conclusions or peer findings.

Read `references/<variant>.md`; execute consolidation, fresh lenses, completeness
and reporting. PR description follows the same delivery/provenance/panel gates.
Shared premises are echoes, not independent corroboration. Deduplication preserves
independent evidence and distinct failure modes.

Load `work-controller:work-record` to validate the snapshot and publish the
envelope. Explicitly degraded coverage cannot claim missing reviewers ran or
static analysis exercised runtime; mandatory missing coverage keeps completion open.

## Optional human view

The final writer saves complete native Markdown once in the owned output root,
using the caller's path or variant filename. Link native details with verdict,
material findings and gaps; include full text when requested or needed for approval.
Workers deliver native reports, never separate UI or another final synthesis.

For requested HTML or useful navigation/filters,
load the `report-rendering:report-renderer` skill and resolve its helper there.
Use saved Markdown as `--input`, its same-stem `.html` sibling as `--output`,
`--profile review` and the prepared owned root as `--root`. The fixed renderer
adds controls, never analysis, findings or a schema. Native `output_path` remains
authoritative; account for HTML as a derived view.

Preserve native sections/fields, roles/severities, evidence/confidence, premises/
provenance, verification, filtered counts, knowledge/coverage gaps and degraded or
unknown states. Link worker and verification details instead of copying them.
Economy never removes required evidence, independent premise reconstruction,
lenses or gates.

Verify rendering before delivery. Diagnose failure through provider recovery and
preserve Markdown. Persistent optional failure is explicitly reported and never
listed as successful. Requested HTML remains an open deliverable; unrequested
optional view failure leaves the native outcome intact.
