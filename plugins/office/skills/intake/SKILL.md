---
name: intake
description: >
  Shared Office intake: inspect materials, settle operation, requested formats,
  editorial/visual decisions and phase-specific dependencies in one brief and
  question round. Route mixed or unspecified deliverables before format work.
---

# Office intake

Resolve the task before format methods, engines or workers. When formats or input
uses are unclear, follow `references/routing.md` through `/daodan:start`.

## Materials and operation

Read supplied materials first. Record each role: information source, binding
brand/template, aesthetic reference, existing artifact to transform, or reusable
asset. One input can serve several roles. Record provenance and rights needed
for its actual use; a logo's observed colors do not prescribe a complete theme.
Never overwrite a supplied file. Write every result to a separate candidate path.

Everything the file supplies is inherited and stated back, never asked again.
Operations combine; run the union of their steps:

| Operation | Route | Content | Visual identity and layout |
|---|---|---|---|
| Create | Substantial | Full shared plan and requested projections | New ad hoc visual proposals; all required format units |
| Derive | Substantial | Full projection for changed purpose/audience; carried claims retained | Inherit the look when requested, otherwise new proposals; new distribution |
| Expand | Substantial | Delta from new material, preserving existing units | Inherit direction, palette, fonts, template; new/moved units only |
| Revise | Substantial | Delta for updates, rewrite, restructure or condensation | Inherit accepted look; changed units only |
| Restyle | Substantial | None: preserve content, sequence and claims | New visual proposals; apply selected look throughout requested scope |
| Edit | Narrow | No global plan | Preserve accepted design; only the authorized local change |
| Review or export | Read-only | None | Source remains unchanged; requested findings/export only |

Shortening/restructuring is substantial. A local change needing a new design or
editorial decision re-enters the affected decision, not an implicit global
redesign. A read-only request authorizes no edit.

## Ask once

Load the `work-controller:work-record` skill for questions and decisions: record each `ask`
before putting it and `answer` in the user's words. Inspect/infer first; ask only
remaining material decisions in one round, one decision per question, with the
recommended option first. A complete or explicitly autonomous request needs no
questions. A brief already recorded by routing is this round; ask nothing it
settles. Ask again only when new evidence materially changes a decision.

For DOCX/PPTX, settle intent/goal, audience, market/sector, channel and reading
context, scope, depth, extent, density, tone, requested formats and transformation
permissions, including locked blocks. Propose a length with its reasoning instead
of asking an open question. `office:content` owns these editorial dimensions;
format `references/structure.md` catalogs supply document-type or deck-mode
conventions and `references/content-planning.md` supplies projection constraints.
Add only genuinely format-specific questions to this same round. Brand, visual
references and color sources come here too; full proposals and explicit selection
follow under `office:design`, not a second intake interview. An aesthetic reference
is optional; the brief's subject and actual content can ground art direction.

## Dependency preflight

Respect the active host's required-package activation prerequisite before Office
phases. Creative-phase skips do not waive activation; the bounded Taste recovery
contract lives in `office:design`'s `references/art-direction.md`.

Keep DEPENDENCIES in the existing brief. For each relevant dependency record
identity/owner/type, phase and requirement, source, actual version or revision,
license/rights or uncertainty, required capabilities, observed probe result,
limits and recovery. Cover local methods/roles, native production/render engines,
host isolation/tools, fonts/assets and existing upstream provenance. Reuse stable
provenance until a dependency changes; do not reread upstream for every document.
For new-look DOCX/PPTX work include the required Taste provider under
`office:design`'s `references/art-direction.md`; reuse this same brief and existing
provenance without an upstream-admission interview. Inherited/narrow/read-only
operations do not open a creative dependency phase they do not consume.

Probe the actual installed runtime/tool schema before its dependent operation;
a manifest or reference version is not execution evidence. No implicit
installation, external publication or substitute engine. A missing DeckCraft,
WordCraft or GridCraft engine has one recovery, and it is not a question: the
request for the work authorizes the download. Say in one line what `plan <engine>`
reports (official source, size, licence, destination), record it through
`work-controller:work-record`, and run `install <engine> --approved`. An objection
from the user, or a failed install, blocks the dependent delivery. `find <engine>`
shows an existing install. All three commands take the form

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/intake/scripts/engine_install.py" plan|find|install ENGINE
```

with ENGINE one of `deckcraft`, `wordcraft` or `gridcraft`. Missing required
capability, after activation, blocks only dependent deliveries while independent work continues.
Unresolved asset/font license blocks incorporation. Do not silently downgrade a
required dependency into a fallback or invent active-host tools.

## Record and hand off

Record starting point, material roles, operation/carry-over, route, destinations,
inherited/inferred decisions and their sources, per-block transformation grants,
approved cuts, dependencies and open questions. Source content outside authorized
cuts/transformations must reach the result. DOCX/PPTX bundles share one CONTENT.md
and one DESIGN.md identity/revision with only requested format projections;
format methods add their own layout reports rather than duplicate strategy.
A later changed destination re-enters routing. XLSX retains its existing method;
it does not acquire document/deck editorial or visual phases implicitly.
