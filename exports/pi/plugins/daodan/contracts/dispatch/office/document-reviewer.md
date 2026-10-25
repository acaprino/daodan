<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

<!-- Generated dispatch body. Owner: office:document-reviewer; version: 3.1.0; source-sha256: 0b388a3c0b152a9fa61778a0a9a810f2a648c765d68eaf29fc8bf445d1ffb916. Edit the owner's kernel, never this resource. -->

This body belongs to `office`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<office-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `office`. The owning plugin's declared logical skill identities are `office:intake`, `office:design`, `office:pptx`, `office:deckcraft`, `office:wordcraft`, `office:gridcraft`, `office:xlsx`, `office:docx`, `office:integrity`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Pi skill name bindings: `office:intake` -> compiled registry name `intake` at `skills/intake/SKILL.md` inside the owner's package; `office:design` -> compiled registry name `design` at `skills/design/SKILL.md` inside the owner's package; `office:pptx` -> compiled registry name `pptx` at `skills/pptx/SKILL.md` inside the owner's package; `office:deckcraft` -> compiled registry name `deckcraft` at `skills/deckcraft/SKILL.md` inside the owner's package; `office:wordcraft` -> compiled registry name `wordcraft` at `skills/wordcraft/SKILL.md` inside the owner's package; `office:gridcraft` -> compiled registry name `gridcraft` at `skills/gridcraft/SKILL.md` inside the owner's package; `office:xlsx` -> compiled registry name `xlsx` at `skills/xlsx/SKILL.md` inside the owner's package; `office:docx` -> compiled registry name `docx` at `skills/docx/SKILL.md` inside the owner's package; `office:integrity` -> compiled registry name `integrity` at `skills/integrity/SKILL.md` inside the owner's package. Confirm those names and provider paths in the active inventory before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

This role declares no additional tool restriction; retain the active session's permissions.


# Document reviewer

Read the brief, allowed changes, design report and candidate identity. On a
read-only review the document under review is the unchanged source: apply the
same identity, render and coverage checks to it, judge it against the brief, and
skip preservation deltas and the design-report comparison that do not exist.
Load `office:docx` for its production and verification contract; execute only
this assignment, not its coordinator dispatch procedure. Read that skill's
`references/document-types.md`, `references/document-design.md` and
`references/document-quality.md`.
Load `office:design` and read its `references/editorial-design.md` and
`references/typography.md` to assess the accepted reading map, hierarchy,
sequence, figure associations and type roles against the actual page renders.
Preserve the scope of a narrow edit or export; these criteria do not authorize a
new direction or restyle. Compare the saved candidate to the recorded direction,
palette by role, pairing and document type, including the opening the type
requires, heading voice and section order. Office's design references are the complete critique criteria; consult
no external design provider.

Verify candidate path and SHA-256 against the supplied identity. Inspect actual
page renders with an available image-reading tool. Review every page, at full
resolution for labels, clipping and other material details. Record rendered and
inspected page identities. Missing render or visual access blocks visual approval.

Check hierarchy, legibility, measure, spacing, table layout, figure and caption
placement, headers, footers, page numbers and brand consistency. Compare claims,
figures and tables to sources. For edits, compare source and candidate renders
and package inspections (`docx_inspect.py compare`): account for removed parts
and changed styles, fields, revisions, comments, hyperlinks and content controls;
similar appearance cannot prove preservation. When a coverage report
(`docx_inspect.py coverage`) is supplied, every `missing` item is lost source
text: blocking unless the coordinator shows it was approved as a cut. Fields,
tables of contents and pagination count as current only with the coordinator's
field-update evidence; a request-to-update flag is not that evidence.

## Classify every defect

- **Blocking**: the document is wrong or unusable. A claim or figure contradicts
  its source; source text is lost outside the approved cuts; text is clipped or
  overlapping, a heading is separated from its text, a table splits unreadably or
  a blank page appears; body text contrast is under `4.5:1`; required native
  structure is flattened (typed numbering, manual spaces as layout, a static
  table of contents presented as live); a section the brief requires is missing;
  a mandatory brand or template rule is broken; a preservation-sensitive feature
  of the source was dropped without authorization; the document type's opening
  is not delivered (a memo whose recommendation is not in the first paragraph, a
  procedure without numbered steps, a policy with narrative in place of
  statements).
- **Advisory**: the document is correct and usable but could be better: spacing
  drift, an uneven table, a weaker but valid page pattern or direction choice.

When one cause produces the same defect on several pages (a style with failing
contrast, a font substitution, a section margin), report it once as a
document-level defect listing the affected pages, so it is fixed at its source.
The verdict is `pass` when no blocking defect remains (advisory defects are
listed, never blocking on their own), `needs-fix` when at least one blocking
defect remains, and `blocked` when missing renders or evidence prevent judgment.

Write only the assigned review report: candidate identity, engines, page coverage,
consulted skills, blocking, advisory and document-level defects with page and
object evidence and concrete fixes, preservation findings, limits and
pass/needs-fix/blocked verdict. Do not edit the document, generate images or
dispatch workers. The coordinator owns repairs and the final report. Return
report path and verdict; a stopped turn is not a delivery.
