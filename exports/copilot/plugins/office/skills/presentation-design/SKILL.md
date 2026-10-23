---
name: presentation-design
description: >
  Coordinate presentation art direction, editable construction and independent
  rendered review through creative specialists. TRIGGER WHEN: creating,
  redesigning or editing a PPTX, reusable presentation template or branded deck.
  DO NOT TRIGGER WHEN: the deliverable is a website or a standalone image.
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

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

# Presentation design and delivery

Own the presentation outcome, not a second construction engine. Read
`references/pptx-compatibility.md` and `references/design-library.md` before
creative work, image generation or native construction. Apply their target,
direction, pattern, slide-object and verification requirements to the
presentation plan and any selected creative provider.
Choose the deck's visual direction from `references/visual-directions.md` and each
slide's pattern from `references/layout-patterns.md`; record both in the plan so
construction and review can verify them.
Read
`references/creative-providers.md` when first loading a creative provider or
resolving its availability. Read `references/image-tools.md` before image work.

Coordinated execution uses the registered `office:create-presentation` workflow
entry and its generated dispatch bindings. If this skill was loaded directly,
resolve that entry on the active host before dispatch; continue the same task,
not a nested workflow. A role name alone cannot supply an inline worker body.

## Route the request

Keep one brief and outline: audience, decision, language, sources, required
wording, brand assets, delivery context, slide roles and editable objects. Resolve
material uncertainty; infer routine choices within the user's authorization.
Preserve facts and citations. Do not manufacture evidence to fill a composition.

Ask the user for the decisions that shape the deck before construction, in one
round of questions: art direction (a library direction or their brand), style
constraints, content and page count, and the slide types they expect. Suggest
concrete options from `references/visual-directions.md` and
`references/layout-patterns.md` rather than an open question. When the user
already gave a complete brief, state the inferred choices instead of asking again.

For a deck with more than a few slides, or whenever direction is genuinely
uncertain, prepare the plan and show a preview before construction: compile the
plan JSON in `references/design-preview.md`, render it with
`python "${PLUGIN_ROOT}/skills/presentation-design/scripts/design_preview.py"`,
and let the user choose the direction and the slide sequence. A separate style
proof costs image generations and needs the user's explicit budget decision and
their chosen number of candidate directions; a full autonomous request authorizes
routine choices without a preview gate.

| Request | Method | Specialist scope |
|---|---|---|
| New deck, new template, substantial redesign | `office:slidepoise` (visual-first reconstruction) or `office:deckcraft` (direct native construction when requested or when SlidePoise is unavailable) | Designer establishes direction and slide-object plan; reviewer inspects final renders |
| Targeted content or formatting edit | `office:deckcraft` | Preserve direction; designer only if a design decision is needed; reviewer checks changes and preservation |
| Preview or printable PDF only | `office:deckcraft` | No redesign; reviewer checks exported pages against the source |

For a reusable template, provide an editable exemplar deck, representative page
types, reusable visual rules and a short reuse note. Do not label a PPTX exemplar
as a PowerPoint `.potx` template or claim master-layout support without verification.

## Delegate with bounded ownership

Establish the target canvas, engine capabilities, fonts and required editability
before consulting creative providers. Pass that compatibility brief to workers.
Select optional creative providers under `references/creative-providers.md` and
pass their selection and availability to each worker. With none installed,
use Office's presentation criteria and the selected engine's guidance. Optional
provider absence does not waive design or independent review deliveries.

The coordinator is the sole deck writer and image-tool caller. Workers read the
brief, source evidence and artifacts, and write only their assigned report.
They do not launch further workers, rewrite the deck or start another engine.
Default models inherit the session. Use the active host's actual isolated
dispatch mechanism and generated role bindings, including when only one reviewer
is required. Unavailable isolation blocks that delivery.

Dispatch `office:presentation-designer` for creative work. Supply brief, outline,
sources, brand assets, existing renders, compatibility brief, absolute report
path and selected creative providers. Require direction, the slide-object
specification from `references/pptx-compatibility.md`, image requests and unresolved
decisions. Verify the report exists and its geometry, typography and native-object
choices are supported before construction or image generation. For a narrow edit
or export, record why a new design delivery is
unnecessary; preserve the accepted direction.

Load the selected engine skill and perform construction or editing in the
coordinator. Give SlidePoise the accepted compatibility brief and design report
as context for its planning and compiled generation request. Do not recreate its
construction schemas locally. Reject references that cannot be reconstructed
with the required editability before propagating their design across the deck.
DeckCraft applies scoped edits to a separate candidate after preservation checks.
Keep source and earlier candidates intact.

Dispatch `office:presentation-reviewer` after actual candidate rendering. Supply
the exact candidate path and SHA-256, render engine/version, page manifest,
brief, design report, source and candidate inventories, allowed changes and
selected creative providers, accepted slide-object specification and font evidence.
Require inspected page identities, concrete defects, preservation findings,
coverage gaps, separate target-application fidelity evidence and a
pass/needs-fix/blocked verdict. An empty response or an
uninspected contact sheet cannot satisfy this delivery.

Verify report artifacts and coverage, resolve substantive findings, rerender
changed pages and obtain an updated review tied to the new candidate. Retain
prior review evidence for unchanged pages only when their identity and rendered
content are proved unchanged. Do not apply a verdict to another file. Inspect
or resume a missing delivery, or record a concrete blocker.

## Completion evidence

Keep one presentation review with candidate identity, requested scope, engines
and versions, source preservation, native-object checks, image provenance,
rendered/inspected/total page counts, target-application verification or its
absence, font substitutions, visual/editability compromises, specialist report paths, consulted or
unavailable creative providers and remaining gaps.
The coordinator owns the final verdict. Structure checks cannot establish visual
quality; rendered images cannot establish native editability. Claims about
Microsoft PowerPoint fidelity require actual PowerPoint rendering evidence under
`references/pptx-compatibility.md`; previews from another engine remain separate.

Deliver the deck and useful previews with remaining limits. Do not claim a
visually reviewed result when actual candidate renders or visual access were
unavailable. Continue independent work when a required capability blocks a step.
For export-only requests, the unchanged source PPTX is the presentation artifact;
identify it explicitly, review its renders and the requested export, and do not
claim to have created or edited another PPTX.
