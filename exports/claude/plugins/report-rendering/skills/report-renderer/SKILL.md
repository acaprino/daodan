---
name: report-renderer
description: >
  Render an authoritative Markdown report as a standalone local HTML view using
  fixed reusable assets. TRIGGER WHEN: a report benefits from navigation,
  comparison, table filtering or naming-weight exploration, or the user requests
  an HTML report. DO NOT TRIGGER WHEN: diagram-only exports (use learning:forcegraph-exporter or learning:markmind-exporter).
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

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
