# Project run report view

Only the coordinator loads this reference when HTML is requested or navigation
and comparison materially help the final report. Workers deliver their native
reports. Load the `report-rendering:report-renderer` skill by its registered identity and
resolve the helper from that installed provider.

## Source and ownership

Use the reviewed `handover.md`, the final `campaign-final.md`, or the operation's
completed human-readable Markdown report in its exact owned run. When an
operation has no such report, persist its existing final summary once as
`run-summary.md` inside the run. Derive it from the native deliveries and actual
run/result records, linking details rather than copying specialist reports.
The JSON envelope and stage records retain their authority; never pass JSON to
the Markdown renderer or infer completion from a summary.

Preserve scope/snapshot bindings, finding provenance, accepted decisions,
outstanding actions, authorization, unavailable gates and the resume line.
Keep inventory, files read and runtime exercise separate. For a campaign, label
earlier stage checks historical and identify the final current verification.
Dry-run and stopped outcomes retain that status and their unexecuted work.
For handover, retain observed versus exercised commands and the absence of
maintenance authorization.

## Render and close

Set `$RUN_DIR` to the existing dedicated project-contained run directory,
`$REPORT_MD` to that final Markdown file and `$REPORT_HTML` to its same-stem
HTML path inside `$RUN_DIR`. The repository root, a shared directory and an
earlier stage's closed run are not output roots. Run:

```bash
python "<resolved-report-renderer-helper>" --input "$REPORT_MD" --output "$REPORT_HTML" --profile report --root "$RUN_DIR"
```

Follow the provider's verification and intentional-overwrite contract. Render
after native report review and before closing the owning run. Record Markdown
and HTML paths in that run's outputs, then validate its envelope and required
gates. An explicitly requested missing or failed HTML delivery keeps the run
open; preserve completed earlier stages and the available native report.

Navigation, filters and task checkboxes affect only the local view. They neither
approve a roadmap nor change deliveries, gate results, dispositions or run state.
The provider needs no browser for structural verification. Rendering adds no
product-runtime coverage, instruction activation proof or token-saving claim.
