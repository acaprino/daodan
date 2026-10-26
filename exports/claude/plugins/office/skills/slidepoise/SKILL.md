---
name: slidepoise
description: >
  Create and revise professional, editable PowerPoint presentations through the
  external SlidePoise framework, with visual design, native reconstruction and
  rendered review. TRIGGER WHEN: the user asks for a PPTX, pitch deck, consulting
  presentation, branded slides, a presentation from research or a workbook, or
  SlidePoise. DO NOT TRIGGER WHEN: the requested deliverable is only an Excel
  workbook (use office:xlsx) or an image without an editable presentation.
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

# Editable presentations

Produce a usable editable `.pptx` whose argument, visual design and rendered pages
meet the user's brief. The local integration delegates presentation construction
to [SlidePoise](https://github.com/henryhyw/slidepoise), an MIT-licensed external
framework. Its skill, references, schemas and runtime remain upstream-owned and
are read from the installed runtime. Read `references/runtime.md` before setup or
the first presentation. Daodan installation alone does not install that runtime.

## Establish the outcome

Infer audience, purpose, language, presentation length, delivery context, source
material and brand from the request. Ask only for material missing decisions.
Develop a clear narrative: what the audience should understand or decide, what
supports the recommendation, and which assumptions remain uncertain. Preserve
the user's accepted wording, actual figures, exact logos and required sources.
Keep source attribution and dates attached to claims. Never invent customer
results, market figures or citations to make a deck look complete.

Match interaction to the request. A sample can resolve uncertainty about style;
a fully autonomous request authorizes routine design decisions and corrections.
Do not introduce per-slide permission gates. Changes to scope, source meaning,
brand identity or a paid generation budget require a real user decision.

## Discover and load the external method

Run the bundled bridge using the host's Python executable:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/slidepoise/scripts/slidepoise_bridge.py" discover
python "${CLAUDE_PLUGIN_ROOT}/skills/slidepoise/scripts/slidepoise_bridge.py" cli doctor
```

Respect `SLIDEPOISE_HOME`, or pass the bridge's `--home` option before its command.
Read the `SKILL.md` at the returned `skill_root` and the relevant references it
names. Use absolute installed paths for those reads. Discover and inspect the
current image-generation and image-viewing interfaces before creative work.
Load the selected external Profile, configuration and Library Sets through the
runtime. Host installation support and a successful doctor do not prove that an
image tool or preview renderer is available.

The external skill is authoritative for its runtime contracts and CLI syntax.
Use its packaged schemas and command help rather than recreating their layouts.
Execute installed scripts through the bridge's `script` command, which resolves
them against the discovered external skill. Paths passed as script arguments
remain relative to the current presentation workspace, so use absolute paths
when operations span slide directories.

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/slidepoise/scripts/slidepoise_bridge.py" script slidepoise_runtime.py --help
```

If discovery fails, resolve the explicit missing prerequisite from the runtime
reference. Continue useful brief and source preparation. Do not claim a PPTX was
constructed, rendered or visually reviewed without the corresponding evidence.

## Design, reconstruct and inspect

Follow the installed SlidePoise method from deck planning through generation,
semantic mapping, measured reconstruction, assembly and final inspection.

- Keep one authoritative outline and shared visual direction. Each slide has a
  communication job, supported message, stable ID and source obligations.
- Inspect relevant visual references and actual assets. Let comparisons,
  relationships and evidence determine the composition. Use a coherent hierarchy,
  typography and color system while allowing slide layouts to vary.
- Generate from the runtime's compiled request using the user's selected image
  tool. Preserve its prompt and reference ordering. Manual image exchange is an
  explicit choice when creative generation is unavailable; it cannot supply a
  missing reconstruction engine or visual reader.
- Reconstruct selected designs through the upstream semantic map, OpenCV evidence
  and constructor-scene pipeline. Native text, tables, charts, shapes and
  connectors must remain editable where their meaning requires it. Photographs,
  textures and illustrations may remain distinct image objects.
- Inspect the actual rendered PPTX pages against both the brief and the selected
  designs. Check text clipping, figure labels, connector direction, alignment,
  contrast, brand fidelity, sources and deck-wide consistency. A contact sheet
  helps compare pages; full-resolution inspection resolves material details.
- Correct routine defects within the accepted brief, rebuild affected pages and
  inspect the changed renders. Package validity, object counts and a reference
  image alone do not establish design quality or faithful reconstruction.

For a deck based on Excel, load the `office:xlsx` skill to read the actual workbook,
verify the intended figures and retain native chart data. Keep workbook formulas
and their calculation status visible in the source evidence. Do not substitute
screenshots for requested editable charts or tables.

For Word sources, load the `office:docx` skill to inspect the actual paragraphs,
tables, annotations and source structure before extracting the deck's argument.
Keep unresolved revisions and source qualifications visible in the evidence.

## Deliver

Deliver the editable `.pptx`, a useful preview and a concise account of material
raster content or unresolved limitations. Verify that the package opens and that
requested native objects exist. State the render engine and whether every page
was inspected. If rendering is unavailable, clearly label the delivered file as
unreviewed and do not describe the presentation as visually verified.

The work directory and construction contracts support iteration; the user should
receive the presentation and usable previews without managing those internals.
