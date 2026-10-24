---
name: design
description: >
  Shared visual design method for Office documents and presentations: one
  direction for composition, rhythm and type; an ad hoc palette built from the
  user's colour source and chosen from candidates in the browser; the argument
  mode, editorial hierarchy, typography, and font fetching, installation and
  embedding. TRIGGER WHEN: an Office intake resolved the substantial route for a
  Word document or PowerPoint deck. DO NOT TRIGGER WHEN: the route is narrow or
  read-only, or the deliverable is a website, a workbook or a standalone image.
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

# Office design

Decide how a file looks once, for the whole file, and hand the format method a
complete record it can build and review against. This skill adds no worker and
no engine: `office:pptx` and `office:docx` own construction,
rendering and review; the format designer roles write their reports under the
direction and palette recorded here.

## One direction, one palette, one pairing

A **direction** from `references/directions.md` fixes composition and rhythm
for slides and pages, and names the font pairing from
`references/font-pairings.md`. The **palette** is built for this file from the
user's own colour source (below); a direction's row only supplies default seeds
when the user gives no source. A supplied brand or template always wins:
extract its palette and fonts as direction `H`, check every text colour at
`4.5:1`, and keep the rest of these rules. A file derived from an existing one
keeps the source's direction and palette unless the brief asks for a restyle.
Do not mix directions, do not replace the accepted palette or pairing silently,
and record every substitution with its reason.

A Word document and a presentation made from the same brief share one
direction, one palette and one pairing, so the pair reads as one piece of work.

## Build the palette from the user's source

Ask at intake where the colours come from, and run the matching extraction:

```text
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" from-image LOGO-OR-PICTURE.png
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" from-url https://example.com
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" from-css PROJECT-DIR-OR-STYLESHEET
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" from-file EXISTING.pptx
```

| Source | What is read |
|---|---|
| An image: logo, photograph, illustration, screenshot | Dominant colours by area, neutrals dropped (needs Pillow) |
| A website | `theme-color`, the first stylesheets, the social image and icon |
| A project's stylesheets or design tokens (CSS, SCSS, LESS, token JSON, a design document) | Declared colours, with `primary`, `brand`, `accent` tokens weighted first |
| An existing PPTX or DOCX | The theme colour scheme and the colours used on its pages |
| A mood, sector or direction in words ("finance, sober", "warm, artisan") | You choose one or two seed hues and chroma from that description and record the reasoning; no script |
| Nothing | The seeds of the chosen direction's row |

Take one or two seeds from the result (the primary colour and, when it adds
character, a second one) and build the candidates:

```text
python "${PLUGIN_ROOT}/skills/design/scripts/palette.py" candidates --seed "#1D4ED8" --seed "#E76F51" > candidates.json
python "${PLUGIN_ROOT}/skills/design/scripts/palette_preview.py" candidates.json --out compare.html --open
```

`candidates` builds five complete palettes from the same seeds, each changing one
thing: sober, faithful, bold, deep and dark. Every palette carries the roles
background, ink, surface, accent, muted text and three or four data colours.
The script guarantees legibility, not taste: ink, accent and muted text hold at
least `4.5:1` on both background and surface; data colours hold `3:1` on the
background, differ from each other perceptually and stay apart under simulated
red-green colour blindness; background, surface and ink share the seed's hue at
low chroma so the palette reads as one; only the accent is saturated.

`palette_preview.py` writes one static page: a compact overview of the five
candidates, with the detail of each (colour roles, contrast figures, the same
sample slide and sample page) shown on hover and pinned on click. Open it for the
user, then **ask which number to use**; the page cannot report the choice. On a
fully autonomous request choose `faithful` unless the brief's tone argues for
another variant, and say so. Record the chosen palette's hex values by role in
the brief; construction and review verify against them. Do not retouch a chosen
colour by hand without re-running `palette.py check` on the result.

## Choose the argument mode

The mode decides how the file argues; the direction decides how it looks. Choose
it from the audience and purpose settled at intake and record it with the
direction. A file derived from an existing one keeps the source's mode unless
the brief changes its purpose.

| Mode | Use when | Slide headline | Word equivalent | Sequence |
|---|---|---|---|---|
| Pyramid | A recommendation or decision for executives, a board or a client | Action headline: the takeaway as a full sentence | Decision memo: answer, then arguments as numbered headings | Answer first, then supporting arguments, then evidence |
| Narrative | Persuading or rallying: pitch, vision, change programme | Story beat: a claim that moves the story on | Proposal: situation, complication, resolution, ask | Situation, complication, resolution, ending on the ask |
| Instructional | Training, onboarding, a procedure | Numbered task or step label | Handbook: goal, numbered steps, check | Goal, steps in order, check or recap |
| Showcase | Portfolio, product, launch, image-led files | Short label, or none when the visual carries the slide | Dossier: plates with captions, little running text | One focal item per page, alternating hero and detail |
| Briefing | Status reports, updates, files read without a presenter | Topic label plus a one-line status | Briefing: fixed sections in a stable order | Fixed sections in a stable order, same slots in every edition |

## Procedure on the substantial route

1. Take audience, purpose, argument mode, direction or brand, colour source,
   carry-over and approved cuts from the intake record. Ask nothing that intake
   already settled.
2. Build the palette candidates from the colour source, show the comparison and
   record the chosen palette.
3. Build the reading map with `references/editorial-design.md`: what the reader
   understands or decides at the opening, middle and close; content roles;
   entry and re-entry points; a communication job for every figure.
4. Set the type roles with `references/typography.md`: the fewest roles that
   show the structure, sizes in points, weights, spacing and reading measure,
   mapped to the direction's pairing. Numeric scales live with the format:
   `office:pptx`'s `design-library.md` for the 16:9 canvas,
   `office:docx`'s `document-design.md` for the page.
5. Install the pairing's faces before construction (below) and record which
   faces were installed, which fell back and why.
6. Hand the format method the record: direction, mode, palette by role, pairing
   and font status, reading map, type roles and open decisions. The format
   designer role turns it into slide-object or page specifications.
7. After the final save, embed the fonts and record the inspection result.

A narrow edit or a read-only task does not re-enter this procedure: it keeps
the accepted direction and palette and records that choice.

## Fetch, install and embed fonts

A pairing's faces are downloaded and installed, never assumed present. Before
construction, in the coordinator, with the pairing's `Spec` from the catalog:

```text
python "${PLUGIN_ROOT}/skills/design/scripts/font_fetch.py" status "Inter:ital,wght@0,400;0,600;0,700;1,400"
python "${PLUGIN_ROOT}/skills/design/scripts/font_fetch.py" install "Inter:ital,wght@0,400;0,600;0,700;1,400"
```

`install` downloads only the missing faces from Google Fonts, verifies each
file's family, weight, style, embedded license (OFL, Apache or UFL) and embedding
permission, and installs it for the current user without administrator rights.
Tell the user which faces were installed. A face that fails verification or
download is not used: fall back to the pairing's Office font and record why.
Applications already running may need a restart to see a new font; render with a
renderer started after installation.

After saving the final DOCX or PPTX, embed the fonts so recipients see the same
type, and inspect the result:

```text
python "${PLUGIN_ROOT}/skills/design/scripts/font_embed.py" embed CANDIDATE.pptx DELIVERY.pptx
python "${PLUGIN_ROOT}/skills/design/scripts/font_embed.py" inspect DELIVERY.pptx
```

`embed` saves a new copy through an installed Microsoft PowerPoint or Word on
Windows. PowerPoint embeds only the characters used, so a recipient can view the
deck as designed but needs the font installed to type new text in it; Word embeds
complete fonts. Without that engine, `embed` reports the missing capability:
deliver the file with the pairing's Office fallback named, or a PDF, and say that
recipients need the fonts. `inspect` works on any host and lists the fonts a file
uses and embeds. Report fonts left unembedded; do not claim embedding without
the inspection result.

## Evidence

Design guidance does not certify an editable file, accessibility, pagination,
embedding or rendering fidelity. The format method's saved-file render, package
inspection and independent review supply that evidence; record what was
observed and what remained unverified, separately. Contrast figures come from
the hex values, not from how an engine, projector or printer reproduces them.
