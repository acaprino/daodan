---
name: wordcraft
description: >
  Create, edit, inspect, render and export real editable Word documents through
  the external WordCraft CLI or exposed MCP interface. TRIGGER WHEN: producing
  DOCX from an accepted design, native Word changes or WordCraft rendering/PDF.
  DO NOT TRIGGER WHEN: only a design brief or read-only package inspection is needed.
---

# WordCraft document production

Use the external [WordCraft](https://github.com/storytold/wordcraft) engine to
produce the actual DOCX after design. Read `references/runtime.md` before the
first operation. Office ships this method and the pinned installer of
`office:intake`, not the engine or an MCP server. Discover the executable or
actual exposed MCP tools and inspect their current schema. When none exists,
follow the engine recovery in `office:intake`'s dependency preflight. Do not
invent commands or silently install another writing library.

For bounded `proposal` production under `office:design`'s
`references/art-direction.md`, consume the assigned candidate's unselected DESIGN
payload, editorial working data and native specification. Validate the proposal
with `require_selected=False` and verify exact project/content/design identities
and requested formats; bundles also verify their candidate-specific working PPTX
plan binding. Build only the assigned representative units to separate native
specimens and render their saved bytes. These are proof artifacts, not selected
final deliveries; never fabricate selection or skip source/native checks for the
units in scope.

For `final` production called by `office:docx`, consume its accepted native design report,
source inventory, DOCX content projection and selected `office:design` record.
Explicitly load CONTENT.md/DESIGN.md through `office:content`'s
`references/records.md`, validate them and compare project, content revision and
requested formats. Bundles require the coordinator's finalized actual-PPTX-plan
validation before dependent production. Reuse existing records; local legacy
edits need no fabricated global record. Missing/stale records for a newly planned deliverable block its
production. Return inherited-binding gaps to the coordinator for the canonical
rebind procedure in `office:design`'s `references/records.md`; retain exact
matching checks. The document coordinator builds the file; do not start another designer or workflow. Map the page plan to supported
native paragraphs, styles, lists, sections, tables and images.

## Inspect and preserve

Record executable/version and input identity. For an existing document, use
`office:docx` to inventory preservation-sensitive features before loading it.
Save a no-edit round-trip to a separate candidate and compare packages and actual
renders before substantive edits. WordCraft remains alpha; an opens/saves result
does not demonstrate preservation of every Word feature.

Use documented targeted operations. In the reference version, `layout.pageSetup`
replaces a complete section including header/footer data; do not use a partial
page-setup object as if it were a merge. Prefer supported targeted size/margin
commands or a verified complete section state. Never rebuild an imported file
merely to remove an unsupported feature. Keep the source and earlier candidates.

## Build the physical file

Discover commands, then prepare a bounded job in the owned workspace. Where
supported, use `wordcraft-cli run --script job.json` with explicit new output paths
in `save`. Older versions may require repeated `--cmd` arguments and `--save`;
use their actual help and pass literal JSON as individual process arguments,
without interpolating content into shell syntax.
For edits use its `file` input; for a new document use a supported blank template.
Read current command definitions for parameters and units rather than guessing.
The documented version supports a command list and saving DOCX/PDF in one job.

Apply the assigned proposal or selected DESIGN.md through its native style/theme map and
page settings; a separate DOTX is optional except when requested. Keep headings, body text,
captions, list numbering and table cells editable. Insert generated imagery only
after the harness image contract returns a verified usable asset. WordCraft
does not replace the harness image tool or authorize another image service.
Do not rasterize page text to imitate the design wireframe.

Verify that the requested output exists at the actual resolved path and contains
the required content. Reopen it with WordCraft and inspect the saved candidate;
command success alone is insufficient because unknown style fields may be ignored.
Use the DOCX inspector to check native structures and preservation deltas. A
design report, PDF or screenshot does not satisfy an editable DOCX request.

## Render, correct and deliver

Render actual saved DOCX pages through the available WordCraft interface and
inspect the returned page images with an image-reading tool. Use `info` for page
inventory, then render the required pages explicitly; CLI page numbers start at 1
in the reference version. Check page flow, table splits, captions, headers/footers,
clipping and the shared theme. Fix supported defects within the brief, save and
rerender changed pages. Keep inspected/total page coverage visible.

When requested, export PDF and verify its pages. Field-update options request
engine updates; inspect actual results rather than assuming full Microsoft Word
field/layout equivalence. WordCraft rendering is evidence for that engine, not
proof of identical Word desktop pagination or pixel fidelity.

Return the physical editable `.docx`, requested PDF/previews, engine/version,
candidate identity, design report path, preservation evidence and remaining gaps
to the producing coordinator. Missing rendering remains an unverified-layout
limit. Missing runtime blocks dependent production while design/source work can
continue. Physical printing requires a real supported application/printer action;
CLI `--print` prints command results to stdout, not paper.
