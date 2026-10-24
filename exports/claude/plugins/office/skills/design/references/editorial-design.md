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
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

<!-- Adapted from marcmarti9/agentit, skills/editorial-design/SKILL.md,
revision fc38111622ac459ccf843234863bd0b8fcb6ebfd (Apache-2.0).
Modified for Office native formats, production ownership and harness image tools.
See agentit-upstream.md for attribution, licenses and sync boundaries. -->

# Editorial design for Office

Design how a reader enters, navigates and retains a story. Own the editorial
concept, hierarchy, sequence and reading furniture. Pair with `typography.md`
for typography and spatial decisions.
`office:docx` owns native Word production; `office:presentation-design` coordinates
PPTX production through the selected engine. This skill adds no worker or engine.

## Inputs and boundary

Use approved content or an explicitly provisional outline, audience, reading
setting, figures/tables/quotes/notes, brand constraints and target format. Preserve
meaning, accepted wording, facts and attribution. Missing evidence permits a
provisional structure, not invented claims. Keep one existing document brief or
presentation design report; do not create a second reporting pipeline.

Preserve an accepted brand, template or direction. The direction recorded at
intake (`directions.md`) supplies palette and pairing; this method decides
composition under it. Do not replace the accepted direction or a Word template
silently.

## Procedure

1. Define the reading job: what the reader should understand or decide at the
   opening, middle and close. Map sections or slide roles before styling.
2. Assign content roles: title, standfirst, headings, body, captions, callouts,
   notes, source lines and navigation. Pair their hierarchy with
   `typography.md` rather than choosing sizes independently.
3. Design entry and re-entry points. Use a lead, meaningful headings, contents or
   running cues where the document's length warrants them. Avoid ceremonial
   navigation on a short sequential read.
4. Give every figure a communication job, source, caption and nearby explanation.
   Choose inset, breakout or full-width treatment deliberately. Preserve readable
   labels and native editable data when required. A pull quote must earn its space.
5. Vary reading, evidence, rest and emphasis. Use whitespace, crop, scale and
   pacing to serve the argument. Avoid repeating one layout or applying a universal
   ratio. Choose a composition from the content, not from decoration.
6. Adapt to the medium using the native-format rules below. A live deck needs a
   clear claim per slide and presenter context; circulation needs enough labels,
   sources and context to stand alone.
7. Review actual saved-file renders with realistic content. Check reading order,
   sequence, captions, headings, contrast, crop, overflow and intended viewing
   distance. A design sketch or generated reference image is not this evidence.
8. Record reading map, style roles, figure associations, chosen theme, native
   representations and remaining checks in the existing brief or design report.

## Native-format rules

| Target | Composition | Production evidence |
|---|---|---|
| DOCX | Flowing paragraphs with native heading styles, sections, lists, captions and tables; intentional page size, margins and breaks | Render the saved DOCX; inspect pagination, heading attachment, table splits, footers and references |
| PPTX | Fixed canvas with explicit object geometry; the recorded direction and a justified pattern per slide | Follow the presentation compatibility brief; verify editable objects and inspect actual candidate slide renders |
| Reusable template | Representative page/slide types with realistic content, stable role names and reuse guidance | Verify what the selected engine actually preserves; do not claim untested master-layout or template-format support |

Do not build a website and assume conversion preserves its layout pixel for pixel.
For PPTX, read
`${CLAUDE_PLUGIN_ROOT}/skills/presentation-design/references/pptx-compatibility.md`
and honor its editability and target-application evidence rules. For DOCX, prefer
native flow and styles over floating text boxes used to imitate a screenshot.

For generated or edited imagery, the shared image contract is
`${CLAUDE_PLUGIN_ROOT}/skills/presentation-design/references/image-tools.md`;
this method only returns image intent, reference assets, crop and placement to
the production owner.

## Review and handoff

Give the production owner the content map, source associations, hierarchy,
figure/caption links, medium-specific layout choices and unresolved decisions.
Keep dense research traceable; make projected claims readable from the stated
distance. Do not quietly rewrite approved content to repair layout.

For ordinary printing, inspect the actual paginated export. Commercial press
claims additionally need the printer's written process, profile, stock, trim,
bleed, safety, binding, ink limits and proof specification. Without these, label
the print concept provisional; do not invent production values.

Editorial guidance does not certify an editable file, accessibility, font
embedding, exact pagination or print readiness. Record observed renders and
unavailable checks separately. Complete this design contribution when the reading
map, meaningful figure associations and medium-specific choices are explicit;
the existing production method retains its file and delivery gates.
