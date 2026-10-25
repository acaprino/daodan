---
name: design
description: >
  Shared visual design method for Office documents and presentations: one
  direction for composition, rhythm and type; an ad hoc palette built from the
  user's colour source and chosen from candidates in the browser; editorial
  hierarchy, typography, and font fetching, installation and embedding. How a
  file argues stays with its format. TRIGGER WHEN: an Office intake resolved the substantial route for a
  Word document or PowerPoint deck. DO NOT TRIGGER WHEN: the route is narrow or
  read-only, or the deliverable is a website, a workbook or a standalone image.
license: Apache-2.0
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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
python "<plugin-root>/skills/design/scripts/palette.py" from-image LOGO-OR-PICTURE.png
python "<plugin-root>/skills/design/scripts/palette.py" from-url https://example.com
python "<plugin-root>/skills/design/scripts/palette.py" from-css PROJECT-DIR-OR-STYLESHEET
python "<plugin-root>/skills/design/scripts/palette.py" from-file EXISTING.pptx
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
python "<plugin-root>/skills/design/scripts/palette.py" candidates --seed "#1D4ED8" --seed "#E76F51" > candidates.json
python "<plugin-root>/skills/design/scripts/palette_preview.py" candidates.json --out compare.html --open
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

## Write the theme into a template

The palette and pairing reach the file as a real theme, not only as values the
engine applies object by object. Generate the base template from the chosen
palette and pairing:

```text
python "<plugin-root>/skills/design/scripts/template_kit.py" BASE.potx --palette candidates.json --variant faithful --pairing 2
python "<plugin-root>/skills/design/scripts/template_kit.py" BASE.dotx --palette candidates.json --variant faithful --pairing 2 --page a4
```

A `.potx` carries the theme (palette roles as theme colours, pairing as heading
and body fonts), a slide master and nine layouts mapped to the patterns of
`office:pptx`'s `layout-patterns.md`; a `.dotx` carries the theme and the
paragraph, character and table styles, page geometry and a page-number footer.
`.pptx` and `.docx` outputs are the same base as an ordinary file to build on;
`--samples` adds one sample slide per layout or sample pages for rendering. Brand
fonts replace the pairing with `--heading-font` and `--body-font`. The report
lists layouts, theme colours, fonts and notes; it never overwrites a file.

Inherit instead of generating when the user supplies a template or a file whose
look must carry over (direction `H`): build on that file itself, so its masters,
layouts, styles and theme survive, and use `palette.py from-file` only to record
its colours. Render a sample built on any template before claiming its look.

## Structure belongs to the format

This skill decides how a file looks, never how it argues. A deck chooses one of
the five argument modes of `office:pptx` (`references/design-library.md`:
pyramid, narrative, instructional, showcase, briefing), because a deck is
spoken over and its headlines carry the argument. A document chooses one of the
document types of `office:docx` (`references/document-types.md`: decision memo,
briefing note, proposal, report, white paper, procedure, handbook, tutorial,
policy, minutes, letter, image-led dossier), because a document is read alone
and its section sequence is the argument. The two catalogs are not mapped onto
each other: a deck and a document made from the same brief share direction,
palette and pairing, and each takes its structure from its own catalog.

## Procedure on the substantial route

Run it only when the operation recorded at intake gives the file a new look:
create, restyle, or derive without carrying the look over. An expansion or
revision inherits the file's direction, palette, pairing and template; record
them with `palette.py from-file` and skip the palette choice, font fetch and
template generation, and design new parts with what the file already uses.

1. Take audience, purpose, the format's structure choice (argument mode for a
   deck, document type for a document), direction or brand, colour source,
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
   faces were installed, which fell back and why. Generate the base template
   from the chosen palette and pairing, or keep the supplied one (above).
6. Hand the format method the record: direction, palette by role, pairing and
   font status, reading map, type roles and open decisions; the format keeps its
   own structure choice beside it. The format
   designer role turns it into slide-object or page specifications.
7. After the final save, embed the fonts and record the inspection result.

A narrow edit or a read-only task does not re-enter this procedure: it keeps
the accepted direction and palette and records that choice.

## Fetch, install and embed fonts

A pairing's faces are downloaded and installed, never assumed present. Before
construction, in the coordinator, with the pairing's `Spec` from the catalog:

```text
python "<plugin-root>/skills/design/scripts/font_fetch.py" status "Inter:ital,wght@0,400;0,600;0,700;1,400"
python "<plugin-root>/skills/design/scripts/font_fetch.py" install "Inter:ital,wght@0,400;0,600;0,700;1,400"
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
python "<plugin-root>/skills/design/scripts/font_embed.py" embed CANDIDATE.pptx DELIVERY.pptx
python "<plugin-root>/skills/design/scripts/font_embed.py" inspect DELIVERY.pptx
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
