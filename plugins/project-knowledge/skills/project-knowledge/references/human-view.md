# Optional knowledge report view

The coordinator loads this reference when the user requests HTML or navigation
and table filtering materially help compare instruction claims, documentation
findings or proposed changes. Short answers need no view. Workers retain their
native deliveries; the coordinator renders only after consolidation and
verification required by the owning method.

## Native source

Use the final run-owned Markdown audit or change summary at its declared report
path. If that summary is not yet saved, write it once from the delivered native
findings and verified changes. Link supporting reports and documents instead of
copying their bodies. The source is the coordinator's report, rather than a
worker handoff, `work.json`, `result.json`, AGENTS.md, CLAUDE.md or another durable
document. Preserve their authoritative contents and paths.

For instruction creation, cite the delivered canonical instruction file and its
verification as evidence in the summary. Keep transient task state in the run.
Include the scope and snapshot, claim status and locators, source/approved-intent
distinctions, inherited premise provenance, duplication findings, proposed and
applied dispositions, retained facts, unavailable checks and uncovered surfaces.
Retain canonical/generated destinations, scoped loading evidence, copy-parity
results and unperformed reload, activation or enforcement checks. A rendered
view cannot settle unknown instruction loading or satisfy an unavailable gate.

## Render and account

Load the `report-rendering:report-renderer` skill and resolve its bundled helper from that
registered skill. Resolve the final Markdown and its same-stem HTML sibling to
exact paths in the dedicated owned run directory. Bind that exact directory as
`--root`; the repository root and shared artifact folders are not boundaries.
Use the `review` profile for findings and document changes:

```text
python "<resolved report-renderer helper>" --input "<owned run>/knowledge-report.md" --output "<owned run>/knowledge-report.html" --profile review --root "<owned run>"
```

Replace the sample filenames with the owner's declared final report path; use
the same dedicated run directory in all three paths. Reuse fixed presentation
without custom HTML, a repeated audit or copied instruction bodies. Keep the
native Markdown and durable files untouched. Task checkboxes and table filters
affect only the open view: they approve no proposal, apply no edit and complete
no workflow check. Rendering grants no new mutation or publication authority.

Verify helper success and the provider's structural checks, including the exact
source payload/hash and retained evidence/unknowns. No browser phase is required;
record interactions as unexercised when no authorized browser check ran. Do not
claim token savings without workflow measurements.

Record successful HTML delivery as a derived view in the owner's outputs and
link it beside the native report before work-controller validation and closure.
Preserve the owning method's delivery and verification gates. Diagnose rendering
failure through the provider and retain the native source. If an explicitly
requested HTML view remains missing or failed, keep that deliverable and the run
open; record the failure rather than claiming delivery. An unrequested optional
view failure leaves the native outcome intact and is reported as a limitation.
