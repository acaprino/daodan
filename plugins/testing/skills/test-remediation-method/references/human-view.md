# Optional human view

Only the coordinator loads this reference when the user requests HTML, or the
completed audit/consolidation report substantially benefits from navigation,
comparison or table filtering. Workers deliver native findings, not presentation.

Load the `report-rendering:report-renderer` skill and resolve its shipped helper through
that registered skill. Render the final native Markdown once with `--profile review`.
Audit uses the task-selected `TEST_AUDIT.md` after any accepted fix and
its final refresh; consolidation uses Step 8's existing coordinator report or
Step 2's final dry-run inventory report, preserving its unexecuted work and status.
Never render `work.json` or `result.json` as Markdown or create another state ledger.

Bind `--input` to that exact final Markdown path. Bind `--output` to
`<output-root>/<report-stem>.html` and `--root` to the same dedicated, exact
task-owned `<output-root>` inside the project. Verify that root's ownership through
the prepared protocol run. A shared target directory containing `TEST_AUDIT.md`
does not become owned by the audit: choose the run's dedicated output directory
instead. Keep the canonical audit and owned `findings.md` at their native paths;
the helper rebases relative evidence links when rendering in a different directory.

Set `$REPORT_MD` to the exact native source, `$OUTPUT_ROOT` to the verified
dedicated output directory and `$REPORT_HTML` to its same-stem HTML path inside
that directory. Run:

```bash
python "<resolved-report-renderer-helper>" --input "$REPORT_MD" --output "$REPORT_HTML" --profile review --root "$OUTPUT_ROOT"
```

Preserve classifications, inventory acceptance, protected behaviors and failure
modes, oracle/bugfix provenance, quarantine ledger references, evidence, coverage
and gates. Retain `--no-run`, stale, unavailable and unknown measurements without
turning them into zero or a pass. Filters and checkboxes affect only the view;
they never accept categories, retire tests, change dispositions or satisfy gates.

Verify helper success and the complete embedded source/hash, required sections,
evidence and uncertainty through the renderer's structural checks. A browser is
optional; state when interactions were not exercised. Link HTML beside native
Markdown through the existing delivery envelope. Rendering adds no authority,
mutation, behavioral verification or measured token saving.

Diagnose and recover render failures while preserving native output. If requested
HTML is failed or missing, leave that deliverable open and do not close the run.
An unrequested optional view failure is reported without changing the native
audit/consolidation result. Apply normal completion only after required gates and
every requested deliverable are verified.
