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
first operation. Office ships this method, not the engine, installer or MCP server.
Discover the executable or actual exposed MCP tools and inspect their current
schema. Do not invent commands or silently install another writing library.

When called by `office:docx`, consume its accepted document design report, the
`office:design` record (direction, palette by role, pairing) and source inventory. The document coordinator builds
the file; do not start another designer or workflow. Map the page plan to supported
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

Apply the accepted native style map and page settings. Keep headings, body text,
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
