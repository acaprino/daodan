---
name: docx
description: >
  Create, read and edit native Word documents with professional styles, page
  layouts, tables, images and editable text. Preserve existing document features,
  select a compatible engine for advanced content and verify saved document pages.
---

# Native Word documents

## Outcome and scope

Deliver a real editable `.docx` that meets the reader's purpose and the user's
brief. Read supplied documents, create reports or proposals, revise selected
content and apply templates using native Word structures. A PDF, screenshot or
Markdown export can accompany the document but does not satisfy a DOCX request.

Infer audience, language, document type, required sections and visual direction
from the request and supplied template. Ask only when a missing decision changes
the result materially. Keep figures, citations and accepted wording faithful to
their sources; distinguish assumptions from established facts. Preserve the source
file and save edits to a separate output path. Never execute embedded objects,
macros or external links while inspecting a document.

## Choose the available engine

Discover available tools and installed runtimes. Prefer a host's document or
artifact engine when its actual API supports the required DOCX operations. Read
its current instructions; this method assumes no vendor-specific runtime exists
on every host. A host tool that exports a DOCX has not thereby demonstrated that
it can round-trip every feature of an existing Word document.

An explicitly available `python-docx` can create and edit supported paragraphs,
styles, lists, tables, sections, headers, footers and inline images. Confirm its
installed version and supported operations before use. It is not a Word layout
engine and does not fully author or update tracked revisions, comment anchors,
complex fields, footnotes, equations, content controls or every drawing type.
Do not silently install dependencies or describe the bundled inspector as a
document-writing engine.

Inspect an existing file before choosing an editing engine. Revisions, comments,
hyperlinks, field codes and results, footnotes/endnotes, OMML equations, content
controls, embedded objects, signatures, custom XML and unknown package parts
require demonstrated preservation. Use an available compatible Word application
or documented host engine for edits it supports. Do not assume LibreOffice or any
other converter preserves all Word features. If no available engine can retain a
required feature, preserve the source and report the unsupported operation.
Legacy `.doc`, encrypted documents and macro-enabled files require a compatible
tool; changing the extension is not a conversion.
Preserve a required macro-enabled source format and its macros. Never downgrade
DOCM to DOCX without authorization for that conversion and its feature loss.

## Inspect before editing

Use the read-only helper on native DOCX packages:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/docx/scripts/docx_inspect.py" inspect INPUT.docx
python "${CLAUDE_PLUGIN_ROOT}/skills/docx/scripts/docx_inspect.py" compare INPUT.docx OUTPUT.docx
```

The JSON inventories native content, document structure and preservation-sensitive
features, validates bounded ZIP/XML and internal relationship targets, and reports
observed changes between packages. It does not render pages, update fields, check
business meaning or certify every OOXML semantic. A validation or limit failure
means inspection is incomplete; use a compatible engine before making preservation
claims. Do not disable inspection limits to process an untrusted file.

Establish which paragraphs, table cells, sections and objects the task authorizes
changing. Preserve unaffected content and formatting. Never replace an entire
existing paragraph through `paragraph.text` or flatten all runs for a small edit:
that can destroy run formatting, hyperlinks, fields and annotation anchors. Use
supported run-aware or native range editing, preserving boundaries and relationships.
Do not strip tracked changes, accept revisions, delete comments or rebuild advanced
content merely to make an editing library handle it.

## Build and revise the document

Read `references/document-quality.md` for layout and review guidance. Apply a
consistent style hierarchy: title, native heading levels, body, captions and table
styles. Use real list numbering and native page/section breaks. Manual spaces,
blank-line padding and typed bullet characters are not layout structures. Preserve
the template's style IDs and inheritance when making a scoped revision.

Choose page size, orientation, margins and sections for the brief, template and
locale. Use paragraph spacing, line spacing, tab stops, keep-with-next and widow/
orphan controls deliberately. Set headers and footers per section, including
first-page or odd/even variants where needed. Use native page-number fields rather
than manually typed pagination. Avoid forcing a global paper size onto every task.

Keep tables editable, with meaningful headers, legible widths and appropriate row
breaks. Insert images as native image objects with stable proportions, captions
and useful alternative text. Keep text selectable. Use native references, bookmarks
and fields when the selected engine supports them; do not present static typed
numbers as automatically maintained cross-references or a table of contents.

When fields, a TOC or pagination must be current, update them through an available
compatible Word or LibreOffice engine whose support covers this document, then
save and inspect that result. A request-to-update flag or cached page count is not
proof that fields were updated or pages laid out. Report unsupported field updates
instead of claiming completion from field codes alone.

## Verify and deliver

Reopen the actual saved output with the chosen engine. Check required text, native
styles, lists, tables, images, section settings, headers/footers and references.
For existing-file edits, compare source and candidate; account for removed parts
and unexpected content, style, relationship or sensitive-feature changes. Changed
part hashes show changed bytes, not semantic loss. Counts alone cannot prove that
comment anchors, revision ranges, fields or hyperlinks remain valid.

Render the saved DOCX with an available compatible renderer and inspect its actual
pages. Check clipping, overlaps, headings separated from their text, tables split
awkwardly, blank pages, image quality, page numbers and header/footer collisions.
Correct routine defects within the brief, save and review the affected pages again.
Verify key claims and figures independently of the document's own text.

Deliver the editable `.docx`, with a useful preview when available, and a concise
account of changes. Name the editing and rendering engines and any remaining
preservation or field-update limit. If rendering was unavailable, label page layout
unverified and distinguish completed structural checks. Never call a document
visually verified from package inspection alone.
