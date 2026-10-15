---
name: report-renderer
description: >
  Render an authoritative Markdown report as a standalone local HTML view using
  fixed reusable assets. TRIGGER WHEN: a report benefits from navigation,
  comparison, table filtering or naming-weight exploration, or the user requests
  an HTML report. DO NOT TRIGGER WHEN: diagram-only exports (use learning:forcegraph-exporter or learning:markmind-exporter).
---

# Report Renderer

Keep the completed Markdown report authoritative. Render its presentation with
the bundled helper. Supply report content once; do not generate custom HTML,
CSS or JavaScript for each report. This skill supplies a renderer, not an agent
executor, evidence collector, workflow scheduler or completion gate.

## Contract

Use UTF-8 Markdown. The helper embeds its exact source bytes for viewing and
download, displays the source filename and SHA-256, and writes one standalone
UTF-8 HTML file. It uses only Python's standard library. CSS and JavaScript are
bundled under `assets/` and embedded in the result. No server, CDN, external font,
browser installation or network request is required to render or use the controls.
Images remain references; referenced images and followed external links may
require the network. The helper never fetches them. The CLI rebases local URLs
when the output is in another folder so that they still reach the source's
original evidence or image target.

Supported presentation: headings and anchors, paragraphs, nested ordered and
unordered lists, task lists, blockquotes, tables, fenced code, inline code,
emphasis, validated links and images. Unsupported constructs remain visible.
Raw HTML is escaped. Mermaid fences remain visible source because this renderer
does not interpret diagrams. Original verdicts, recommendations, evidence,
uncertainty, provenance and coverage are retained.

## Render

1. Finish and verify the native Markdown report through its owning workflow.
2. Select `report` for analysis or general reports, `review` for review tables,
   or `naming` for the canonical brand naming template.
3. Choose an explicit dedicated output root owned by this task inside the project
   or the workflow's authorized artifact directory. Do not name the repository
   root, a shared folder or private app storage as a convenience boundary.
4. Run the shipped helper. Resolve relative paths against the working directory.

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/report-renderer/scripts/render_report.py" --input "/project/reports/report.md" --output "/project/reports/html/report.html" --profile report --root "/project/reports/html"
```

The output must be inside the explicit root. The helper rejects `..` traversal,
symlinks, Windows junctions/reparse points on output paths or root ancestry,
source overwrite (including an existing hard-link alias), and an existing output
unless `--force` explicitly authorizes replacing that rendered view. Missing
output directories are created after validation; output replacement is atomic.
`--force` never bypasses the other guards. Inputs must be ordinary UTF-8 files.
Filesystem checks protect ordinary use, not hostile concurrent path mutation.

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/report-renderer/scripts/render_report.py" --input "/project/reports/naming.md" --output "/project/reports/html/naming.html" --profile naming --root "/project/reports/html" --force
```

The library seam is `render_report(markdown, profile="report",
source_name="report.md") -> str`. It performs no filesystem writes. The CLI
preserves the input file's line endings and UTF-8 bytes; the string API embeds
the string's UTF-8 encoding.

## Interactions and bounds

- Navigation and source disclosure use native keyboard-accessible controls.
- Table filters hide rows only in the current view. They do not change source,
  evidence, scores, verdicts or completion accounting.
- Task checkboxes change only the open page and reset when it reloads. They do
  not write canonical state or count as completed workflow checks.
- The naming profile recognizes the canonical `Criterion | Weight | names`
  Scorecard with its final Overall row, including explicit common translations
  of those three labels in Italian, French, Spanish, German, Portuguese, Dutch,
  Polish and Swedish. Parenthetical score qualifiers retain their original
  wording. Common translated `not scored` values stay excluded; zero denominator
  uses an original unscored label when available. Eligibility also requires the
  canonical percentage-weight and score-cell structure. Other tables remain
  normal tables. If no supported Scorecard is found, the page explains that
  weight exploration is unavailable; the complete report remains visible.
- Weight edits recompute only that Scorecard's Overall row. Each candidate's
  denominator includes its scored criteria only. `not scored` contributes no
  weight; zero denominator displays the unscored label (`not scored` by default).
  `unverified`, `not screened` and translated parenthetical qualifiers
  remain visible in source cells and in recalculated outcomes. Weights accept
  finite numbers from 0 through 100. Reset restores exact original weights and
  Overall cells. The original recommendation and all other scores stay intact.
- The review profile adds filtering without deriving verdicts or severity.
- Naming details can collapse within a name section. Report source and contents
  can collapse in every profile. All content remains available without scripting.

## Verify and deliver

Confirm helper success, the complete original sections/evidence/qualifiers, the
source payload and hash, and the source-download reference. This is the required
structural verification and needs no browser. When an authorized browser is
available and the requested result relies on interactions, exercise those
controls, including naming zero-weight/reset behavior. Otherwise state that
interactions were not exercised; a browser is optional for this renderer.

A Codebase Map caller stays static. Never add a browser exercise or product runtime
step to its workflow. Development tests of the fixed renderer's controls are
separate evidence from a caller's live run or product-runtime coverage.

Present the HTML beside the native Markdown, stating that controls affect the
local view only. Keep workers' handoffs in the native report format; the
coordinator renders after consolidation.

Do not assert token savings from this skill alone. Compare generation, revisions
and later consumption on the actual workflow before claiming a measured benefit.

## Inspiration and provenance

The idea of separating agent-authored content from reusable presentation was
inspired by [agent-html-kit](https://github.com/leex279/agent-html-kit), an MIT
project inspected at commit `7752a14`. This implementation is original; it copies
no upstream code, templates or assets. This leaf uses Daodan's Markdown reports
and preserves their owning workflows' contracts.
