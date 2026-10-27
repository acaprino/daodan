---
name: deckcraft
description: >
  Create, inspect, edit, render and export PPTX through the external DeckCraft
  runtime, preserving sources and checking native-feature losses. TRIGGER WHEN:
  direct native PowerPoint construction, targeted PPTX changes, slide previews,
  printable PDF or DeckCraft.
  DO NOT TRIGGER WHEN: only a spreadsheet or document is requested.
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.
> This package retains its lifecycle callback scripts, but this host has no declared native hook registration. Use the method's explicit workflow checkpoints; automatic interception outside those workflows is unavailable.

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# DeckCraft presentation operations

Use the external [DeckCraft](https://github.com/storytold/deckcraft) engine for
direct native deck construction, targeted edits, native object operations,
rendering and PDF export. It is the only presentation construction engine.
Read `references/runtime.md` before discovery or the first operation. Office
ships transport and read-only inspection helpers and the pinned installer of
`office:intake`, not the engine or an MCP server. When `discover` finds no engine,
follow the engine recovery in `office:intake`'s dependency preflight.

The presentation coordinator loads `office:pptx` for creative
decisions, specialist review and image-tool ownership. When invoked by it, return
operation evidence without starting another coordinator or specialist team.
Read `${PLUGIN_ROOT}/skills/pptx/references/pptx-compatibility.md`
and `${PLUGIN_ROOT}/skills/pptx/references/layout-patterns.md`
before design or native construction, including direct use. Bind accepted object
geometry, font choices and native editability to actual supported commands.
For a narrow edit/export, preserve the existing design and apply only the relevant
compatibility and preservation checks.

For bounded `proposal` production under `office:design`'s
`references/art-direction.md`, consume the assigned candidate's unselected DESIGN
payload, editorial working data, candidate-specific actual plan/binding and native
specification. Validate the proposal with `require_selected=False` and verify exact
project/content/design identities and requested formats. Build only the assigned
representative units to separate native specimens and render their saved bytes.
These are proof artifacts, not selected final deliveries; never fabricate selection
or skip source/native checks for the units in scope.

For newly planned `final` construction, consume the content projection, finalized plan,
selected `office:design` record and accepted native object specification. Follow
`office:content`'s `references/records.md` to explicitly load/validate CONTENT.md
with that actual plan and DESIGN.md; compare project, content revision and exact
requested formats. The coordinator finalizes display values/canonical plan
binding after visual selection under `office:pptx` before production. Apply
the assigned palette/font values through native themes/styles/masters; a separate
POTX is optional except when requested. Do not reopen content, visual selection
or composition here. Local legacy edits retain the source without fabricating
global records. These handoffs do not replace specialist or saved-render review.
Return inherited-binding gaps to the coordinator for the rebind procedure in
`office:design`'s `references/records.md`; retain exact matching checks.

## Discover and establish scope

```text
python "${PLUGIN_ROOT}/skills/deckcraft/scripts/deckcraft_bridge.py" discover
python "${PLUGIN_ROOT}/skills/deckcraft/scripts/deckcraft_bridge.py" cli help run
python "${PLUGIN_ROOT}/skills/deckcraft/scripts/pptx_inspect.py" inspect SOURCE.pptx
```

Record actual version and selected executable. Resolve the requested objects and
allowed changes from the brief. Preserve the source and hash it before work.
Read the inventory's slide order, content, notes, relationships, parts and feature
lists. Use the runtime's document/slide inspection to resolve actual object IDs.
Do not infer IDs from a thumbnail or reuse them after an unrelated document load.

The inspector accepts ordinary PPTX and `.potx` templates, not macro-enabled variants. It
checks bounded ZIP/XML and relationships; it does not render, evaluate chart
semantics or establish full OOXML conformance. Never treat `valid: true` as a
fidelity verdict. Inspect errors and deltas, including changed parts and binaries.

## Preserve before editing

For an imported deck, first save a no-edit round-trip to a separate candidate.
Compare original and round-trip with the packaged inspector and render both.
Check slide order/count, hidden flags, text, notes, layouts, masters, theme, charts,
embedded workbooks, diagrams, media, comments, animation and links as applicable.
Engine logs may report lost slides or damaged media despite a successful exit.

Unexplained losses or changed formatting block the affected edit. Preserve the
source, identify the unsupported feature and request a real fidelity/scope
decision only if another authorized preserving route is unavailable. A deck
with known unsupported features must not silently become a simplified deck.
Preview/PDF-only work needs source inspection and render review, not a resave.

## Apply scoped changes

Use runtime command discovery before unfamiliar operations. Write a bounded JSON
array of `{ "command": "...", "params": { ... } }` records to the owned workspace,
then apply it to a new path:

```text
python "${PLUGIN_ROOT}/skills/deckcraft/scripts/deckcraft_bridge.py" apply --input SOURCE.pptx --commands edits.json --output CANDIDATE.pptx
python "${PLUGIN_ROOT}/skills/deckcraft/scripts/pptx_inspect.py" compare SOURCE.pptx CANDIDATE.pptx
python "${PLUGIN_ROOT}/skills/deckcraft/scripts/pptx_inspect.py" coverage SOURCE.pptx CANDIDATE.pptx --cuts cuts.json
```

`compare` matches slides by position, so it suits scoped edits. After a restyle,
restructure or shortening, use `coverage`: it checks, independently of slide
position, that every source paragraph, table cell, chart text and speaker note
reached the candidate, except the approved cuts (`cuts.json`, a JSON list of
`{"text": ..., "reason": ...}` or `{"slide": N, "reason": ...}`). `complete` is
true only when no item is unexpectedly missing; missing items carry their closest
candidate text and a similarity ratio. Parts listed under `skipped` (SmartArt,
`chartEx` charts) are not covered and need inspection on the renders. It is
structural text evidence, not a visual or fidelity verdict.

The helper refuses input overwrite, existing output and file/app commands inside
edit plans. It transports arguments without shell interpolation. It is not a
sandbox or transaction manager: an engine failure can leave partial artifacts.
Keep failed outputs separate and verify before retrying. Direct `cli` passthrough
has the runtime's ordinary permissions. Large Windows plans need smaller batches
to distinct saved candidates or the verified native MCP interface.

Retain native text, charts, tables and shapes. `text.set` replaces the whole text
and retains only first-run formatting; use verified range operations for a narrow
rich-text edit. Chart data edits can detach an embedded workbook and drop a
secondary axis; verify and preserve those requirements before writing. Discover
supported commands instead of inventing an OOXML-preservation promise.

Generated or edited imagery must follow `office:pptx`'s harness
tool contract. Existing approved assets do not require generation. Do not replace
editable content with a whole-slide raster image.

## Render, export and deliver

Render source and final candidate into distinct fresh directories. Check the
expected page count and inspect actual images; hidden slides also need evidence.
An existing output folder may contain stale images and cannot prove coverage.
Export a separate PDF when requested, then inspect its page count and rendering.
PDF defaults exclude hidden slides; record the intended inclusion policy.

Recheck the source hash after all engine operations. Review unexpected deltas
against the allowed edits, including formatting-only XML changes. Identical
inventory counts cannot prove that a graph, relationship or visual survived.
Resolve the independent review required by the presentation coordinator.

Deliver candidate PPTX, requested previews/PDF and the operation evidence with
engine/version, preservation findings, inspected pages and known limits. A
printable PDF is not a completed physical print job. DeckCraft rendering alone
does not prove exact rendering in Microsoft PowerPoint.
