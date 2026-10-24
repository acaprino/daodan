<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

<!-- Adapted from claude-office-skills/skills, ppt-visual/SKILL.md, MIT.
Revision 9c4c7d5cd2813a8936bf2c9fdb174ea883b85a11.
Modified for Office shared themes, native objects and the existing design report.
Full retained license: LICENSE-ppt-visual-MIT.txt. -->

# PPT Visual composition handoff

Use these adapted wireframes to make the existing slide plan concrete. The
`office:presentation-designer` remains the PowerPoint design agent. Use the
palette and pairing of the `office:design` record. Keep `layout-patterns.md` as
the canonical pattern catalog and
`pptx-compatibility.md` as the native-object and geometry contract.
These are planning templates, not binary PPTX files or additional style presets.

## Wireframe choices

Map these compositions to the selected library pattern. Preserve the accepted
canvas/direction and vary placement only for a content reason. The brackets
below show regions, not raster images or an automatic reconstruction promise.

| Wireframe | Library pattern | Region sketch |
|---|---|---|
| Title | 1 Cover | `[ title + subtitle ] [ image/accent ]; [ author/date ] [ logo ]` |
| Statement | 3 Divider or 15 Quote, by purpose | `[ open space ]; [ main statement ]; [ attribution if quoted ]` |
| Three columns | 4 Executive summary | `[ action headline ]; [ lead + detail ] [ lead + detail ] [ lead + detail ]` |
| Split image/text | 14 Case study, or the chosen content pattern | `[ image ] [ headline + explanation ]; [ source ]` |
| Data highlight | 5 Key metric spotlight | `[ headline ]; [ primary value + unit/context ]; [ supporting values ]; [ source/period ]` |
| Timeline | 10 Timeline and roadmap | `[ headline ]; [ milestone ] -> [ milestone ] -> [ milestone ]; [ dates/owners ]` |
| Comparison | 7 Comparison matrix | `[ common criterion ]; [ option A ] [ option B ]; [ explicit conclusion ]` |
| Process | 11 Process flow | `[ headline ]; [ stage ] -> [ stage ] -> [ stage ]; [ handoff labels ]` |
| Quote with portrait | 15 Quote and testimonial | `[ exact quotation + attribution ] [ separate portrait ]; [ source ]` |

Use native text, shapes, connectors, charts or tables for editable meaning.
Photographs, textures and illustrations may be distinct image objects. Use a
native labeled shape instead of unsupported SmartArt when that preserves the
requested editability. Record limitations before construction. Motion is optional
and only planned when requested and supported by the actual engine.

## Return a concrete layout for each slide

Add the following to the existing design report, not a second report:

1. Stable slide ID, communication job, headline, selected pattern and wireframe.
2. A small region sketch using real content labels, with reading order and
   the reason for the chosen arrangement. Existing pattern variants are enough;
   do not generate competing designs for every slide.
3. Slot-level placement: declared origin/units, `x`, `y`, width, height, padding,
   alignment and layering. Bind every region to supported native objects under
   `pptx-compatibility.md`, rather than leaving approximate positions to the builder.
4. Exact accepted text, font role/size/weight and shared semantic color token for
   each slot. Keep theme identity visible; do not select a second palette here.
5. Native data, object editability, source notes and chart/table labels. Use real
   values and citations, not the upstream example's illustrative growth figures.
6. Needed image/icon descriptions, crop, dimensions, intended placement and
   provenance. Choose supplied/reused, searched or generated/edited assets under
   `image-tools.md`. The coordinator calls the active harness image tool for the
   generated/edit route; the designer does not call another image service.
7. Construction notes, overflow/splitting behavior, unsupported effects and review
   checks. The saved candidate still requires actual rendering and native-object
   verification. Wireframes and reference images cannot certify either.

For a reusable presentation template, supply representative editable cover,
content, evidence and closing layouts as needed, plus replacement instructions.
This is a design specification until the producer builds the exemplar. Do not
call it POTX or a master-layout system without verified support.

## Adaptation and upkeep

Source: [PPT Visual](https://github.com/claude-office-skills/skills/blob/9c4c7d5cd2813a8936bf2c9fdb174ea883b85a11/ppt-visual/SKILL.md).
The upstream supplies nine wireframes and a slide-specification format, not a
binary template pack. This adaptation retains those composition ideas and
handoff structure, maps them to Office's existing patterns, and delegates palette
and font selection to `office:design`. It omits foreign models/MCP tools, separate
color/font catalogs, automatic image-library sourcing and universal design slogans.
The exact MIT license ships beside this reference. This is a pinned adapted
snapshot; review upstream manually when requested or when a concrete need arises.
