---
name: design
description: >
  Design a shared visual identity for requested Office documents and decks:
  Taste art direction, real native proposal comparison, explicit DESIGN.md
  selection, semantic palette, typography, imagery and native theme handoff.
  Use when intake calls for a new look; revisions inherit accepted decisions.
license: Apache-2.0
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

<!-- The editorial and typography references are adapted from marcmarti9/agentit
(Apache-2.0); directions Q to T carry seed palettes from anthropics/skills Theme
Factory (Apache-2.0). See references/agentit-upstream.md and
references/theme-factory-upstream.md for attribution and retained licenses. -->

# Office visual design

Own the shared visual system. `office:content` owns intent, audience, market,
claims, depth and logical sequence; DOCX/PPTX designers own final composition
and native geometry. This skill adds no worker or engine. One brief can yield
both formats with the same selected design and independent layouts.

## Preserve or design

Read the brief, material roles and accepted content/design records. New work,
restyle or a derivation without inherited look designs an identity for the
actual subject, audience, brand and requested formats. Expansion and revision
inherit accepted direction, palette, type and template; skip new proposals,
font installation and template generation unless their authorized scope changes
them. Narrow edits and read-only work retain the accepted look.

For a new look, follow the single Taste input/output and proposal-review contract
in `references/art-direction.md`. It consumes the settled Office brief and returns
our design payloads; it adds no intake, editorial strategy or production engine.

When inherited content identity/revision or requested formats change, use the
inherited-design rebinding procedure in `references/records.md`. Keep the visual
choice and predecessor intact while publishing a correctly bound new record.

Use `references/directions.md` and `references/font-pairings.md` as resources,
not compulsory letters, pairings or presets. Derive the palette through the
sample, converge and justify steps in `directions.md` before keeping any seed,
and keep the proposal set spread across its temperatures. Proposals may adapt
compatible principles into one coherent identity. `references/diagram-style.md`
supplies the colour roles, node treatments, strokes, grid and label sizes for
diagrams built from native shapes. A supplied brand or template always wins;
inherit its masters/styles and record actual colors/fonts. Separate observed
source values from proposed additions; record justified fallbacks.

## Prepare usable palettes

Extract the user's color source with the existing helpers:

```text
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" from-image LOGO.png
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" from-url https://example.com
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" from-css PROJECT-OR-STYLESHEET
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" from-file EXISTING.docx
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" candidates --seed "#1D4ED8" > palettes.json
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" check selected-palette.json
```

For words or no source, choose and justify seeds from the brief; the script does
not interpret language. Candidate generation can report failed checks. Inspect
`check.passes` and diagnostics, extract the actual palette object to
`selected-palette.json`, filter failed candidates or refine their colors/
data categories, then rerun `palette.py check` on the actual palette. Never select
`faithful` or another variant merely because it was generated. Preserve text
contrast of `4.5:1`, data contrast of `3:1` and the helper's distinctness/CVD checks;
do not claim a passing palette before observing its result. A binding brand
conflict needs a supported treatment or recorded decision, not silent recoloring.

`palette_preview.py` remains an optional chromatic helper:

```text
python "${PLUGIN_ROOT}/skills/design/scripts/palette_preview.py" palettes.json --out palette-compare.html --open
```

It shows fixed palette examples and cannot record a choice. It does not satisfy
the complete visual-system comparison below.

## Prove, compare and select the complete system

Follow `references/art-direction.md` for the bounded Taste contribution and
`references/records.md` for the v2 proposal/CLI contract. Author two or three
complete unselected DESIGN payloads on the exact editorial working revision.
Give each a subject-specific idea and coherent type, palette, imagery, form and
data treatment. Use the same complete real content, sources and representative
jobs in only the requested formats; a table/evidence job can be inapplicable
with its recorded reason, never invented. A recolor or font swap is not another
compositional direction. Detailed hierarchy/type guidance stays in
`references/editorial-design.md` and `references/typography.md`.

Dispatch the existing format designers and reviewers in `proposal` mode under
the art-direction contract. Resolve authorized image requests before building
separate native specimens, inspect their saved renders and repair failed
creative proposals. Cover the opening and difficult real-content jobs, not just
an attractive cover. Assemble the exact reviewed native frames and bindings as
`office/design-candidates/v2`. V1 is a limited theme sampler and cannot satisfy
this complete creative comparison.

```text
python "${PLUGIN_ROOT}/skills/design/scripts/design_compare.py" candidates.json --out COMPARE.html
python "${PLUGIN_ROOT}/skills/design/scripts/design_compare.py" candidates.json --select technical --authority user --source "Decision Q2" --out DESIGN.md
python "${PLUGIN_ROOT}/skills/content/scripts/office_records.py" validate DESIGN.md
```

Open and inspect the native-render gallery; keep its proof limits visible.
Record the user's explicit answer through the existing Work Controller question contract,
or select with `--authority autonomous` under an existing grant and cite its
source. Browser highlighting is not a returned answer. A compatible combination
is a new complete authored candidate with parent IDs and greater revision;
create fresh native proof and review it before selecting. No automatic merge
invents decisions.

Load the saved `DESIGN.md` through `office_records.load_record(Path(...))`, run
`validate_design`, and compare `project_id`, `content.project_id`,
`content.revision` and exact `formats` to the loaded content. The name alone
proves nothing. Pass this exact design revision to designers, producers and
reviewers in `final` mode. Revisions use new paths; never overwrite accepted
records.

The selected record owns semantic colors/proportions, type roles/fallbacks,
spacing principles, imagery, data, components and requested-format adaptations.
For PPTX the coordinator now fills the existing plan's display `direction` from
this selection, recomputes its `canonical-json-v1` binding, and freezes/validates
final `CONTENT.md` with that actual plan under the format method. This derived
binding finalization changes no claims or content revision. Editorial changes
return to the content owner. Shared design supplies no slide/page geometry.

## Materialize native styles and optional templates

Apply selected values through native styles, themes, masters and layouts. A
separate DOTX/POTX is optional for ordinary work; generate one when useful or
when reusable templates are requested. The existing kit can materialize a
compatible palette/font choice:

```text
python "${PLUGIN_ROOT}/skills/design/scripts/template_kit.py" BASE.potx --palette palettes.json --variant deep --pairing 2
python "${PLUGIN_ROOT}/skills/design/scripts/template_kit.py" BASE.dotx --palette palettes.json --variant deep --pairing 2 --page a4
```

Use the actual selected passing variant and supported font arguments; the
example does not select a project palette. Custom fonts use `--heading-font`
and `--body-font`. The kit's POTX has a master and nine pattern layouts; its
DOTX has native styles, page geometry and footer. Ordinary PPTX/DOCX bases and
`--samples` are supported. Preserve a supplied template instead of regenerating
it; `palette.py from-file` records its values. Render an actual sample before
claiming template behavior. Kit geometry does not override the designer's
accepted composition or the runtime's actual capabilities.

## Fonts and final-file evidence

Check selected families, real weights, glyph coverage, licenses, embedding
permissions and installed faces before construction. Reuse available approved
faces. Missing open faces can use the existing verified fetch/install helper
within the brief's dependency authority:

```text
python "${PLUGIN_ROOT}/skills/design/scripts/font_fetch.py" status "Inter:ital,wght@0,400;0,600;0,700;1,400"
python "${PLUGIN_ROOT}/skills/design/scripts/font_fetch.py" install "Inter:ital,wght@0,400;0,600;0,700;1,400"
python "${PLUGIN_ROOT}/skills/design/scripts/font_embed.py" embed CANDIDATE.pptx DELIVERY.pptx
python "${PLUGIN_ROOT}/skills/design/scripts/font_embed.py" inspect DELIVERY.pptx
```

`install` downloads only missing faces, verifies family/weight/style, embedded
open license and embedding permission, and installs for the current user. Record
installed faces and substitutions. Do not use a failed or unlicensed face;
record an approved compatible fallback. Render in an application started after
installation when needed.

Embedding saves a separate copy through installed Microsoft Word/PowerPoint on
Windows. PowerPoint embeds used characters, Word complete fonts. Missing engine
or embedding support is a named limit, not proof that fonts travelled. Complete
embedding before preservation checks, actual saved-file rendering and independent
review so they bind to the exact delivered copy. Read-only work never embeds into
the source. Contrast checks, HTML previews and structural records do not prove
editability, accessibility, pagination, embedding or target-application fidelity;
format methods retain those checks and disclose unavailable evidence.
