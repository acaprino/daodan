# Optional human view

Loaded only by the report/run owner when the user requests HTML, or navigation
and table filtering would materially help read the completed analysis. Partition
workers and the synthesizer do not load this reference or generate a separate UI.

Load `report-rendering:report-renderer` and resolve its helper through that skill.
Render the completed `$RUN_DIR/07-final-report.md` to
`$RUN_DIR/07-final-report.html` with `--profile report` and `--root $RUN_DIR`.
Use the fixed renderer instead of generating HTML/CSS or repeating the analysis.
Preserve every section, citation, claim status, coverage figure and unknown value.
Diagrams remain visible as source when no existing renderer is available.

Keep the view in the identified run directory and link its exact path; do not
publish another latest-run mirror. Verify only structural rendering and helper
delivery here. Do not add browser exercise to the X-ray: presentation is not
runtime evidence, and domain verification retains its existing scope.

The summary budget controls context, not required evidence or coverage. The final
owner writes native synthesis once and links required phase details. Rendering
does not replace mandatory reading, independent verification or completion gates.

Diagnose a rendering error through the provider's recovery contract, preserving
native Markdown. If the view still fails, report that failure explicitly. An
explicitly requested HTML deliverable remains open, so the run owner does not mark
the run complete or publish a completed requested output. An unrequested optional
view failure does not change the native analysis outcome. Once native output and
every requested view are delivered, the run owner applies normal completion.
