# External DeckCraft runtime

Reference release: **0.10.0**, tag `v0.10.0`, commit
`b47195feec0f0fe4220d8943ad1c8add5dad8072`, released 2026-10-22.
Upstream is active but describes alpha fidelity limits. Source is dual licensed
MIT OR Apache-2.0. No upstream implementation is copied into Office.

- [Official release and platform packages](https://github.com/storytold/deckcraft/releases/tag/v0.10.0)
- [CLI contract](https://github.com/storytold/deckcraft/blob/v0.10.0/apps/deckcraft-cli/src/help.rs)
- [MCP contract](https://github.com/storytold/deckcraft/blob/v0.10.0/docs/mcp.md)
- [MIT license](https://github.com/storytold/deckcraft/blob/v0.10.0/LICENSE-MIT)

Install a compatible official package or extract the portable package into an
owned runtime directory. Do not launch the desktop app merely to use the CLI.
Put `deckcraft-cli` on PATH or set `DECKCRAFT_CLI` to its executable. The bridge's
`--binary ABSOLUTE_PATH` before its subcommand overrides discovery. Verify the
reported version and command help; a different version requires contract checks,
not silent assumptions about the reference release. No separate PowerPoint
installation is needed for DeckCraft rendering. Fonts still affect the output.

## CLI operations at the reference version

Examples below are upstream CLI arguments; prepend the bridge's `cli` command
when using its discovery. Paths are examples in the owned presentation workspace.
Use separate argument arrays when invoking through a shell tool; do not interpolate
untrusted slide text into shell source. The `apply` helper accepts a JSON file and
handles repeated command arguments for editing.

```text
deckcraft-cli --version
deckcraft-cli commands format.
deckcraft-cli describe insert.textBox
deckcraft-cli info SOURCE.pptx
deckcraft-cli run --in SOURCE.pptx --print --cmd 'slide.inspect={"index":0}'
deckcraft-cli run --in SOURCE.pptx --save ROUNDTRIP.pptx
deckcraft-cli render CANDIDATE.pptx --all --scale 2 NEW_PREVIEW_DIRECTORY
deckcraft-cli run --in CANDIDATE.pptx --export PRINT.pdf --export-params '{"layout":"slides","dpi":300}'
```

Slide indices are zero-based; insertion selects the object for subsequent format
commands. Inspect an actual slide to obtain object IDs. A targeted edit plan uses
`slide.go` with `index`, followed by `text.set` with `id` and `text`, subject to the
rich-text preservation warning in the skill. Command output with `--print` is
human-readable, not a JSON document. Preserve stderr warnings as evidence.

A new CLI session starts with a title slide. For explicitly requested native
construction, start the plan with `file.new` and parameters
`{"blank":true,"size":[960,540]}`, then `slide.new` with `{"layout":"blank"}`.
The bridge permits this first command only when no input is supplied.

`render --all` includes hidden slides and writes numbered PNGs. PDF export
excludes hidden slides by default; use verified `includeHidden` parameters when
required. PDF slides consist of raster artwork plus searchable text, not editable
PowerPoint objects or guaranteed vector graphics. Notes and handout layouts are
separate export choices; inspect current help for their parameters. Physical
printing requires a separate available printer interface and user instruction.

The runtime aborts a failed command before trailing save/export, but commands can
have other side effects. A successful load can still warn about lost slides or
damaged media. The independent inspector and actual renders remain necessary.
Chart data replacement can remove an embedded workbook and lose a secondary axis;
an unchanged chart has a different preservation path. Do not generalize a simple
fixture's success to arbitrary imported decks, animations or complex templates.

## Rendering limits at the reference version

Renders and PDF export come from DeckCraft's own renderer. Upstream lists these
gaps in [docs/gaps.md](https://github.com/storytold/deckcraft/blob/v0.10.0/docs/gaps.md):

- Only Regular, Bold and Italic faces are drawn
  ([#69](https://github.com/storytold/deckcraft/issues/69)). Light, Medium and
  Semibold (weights 300, 500, 600) render as a substitute. Prefer 400 and 700 in
  a DeckCraft deck, or record that its renders cannot verify the other weights.
- SVG pictures are not rendered or inserted; an SVG icon shows only its raster
  fallback. Insert PNG, JPEG or EMF.
- A MicroType Express embedded font subset is not drawn; raw TrueType/OpenType
  and Embedded OpenType faces are.
- PDF export rasterizes slide artwork; text stays searchable.

## Templates

A `.potx` opens as a presentation. At the reference version a save to `.potx`
writes the presentation content type, so PowerPoint does not treat the result as
a template: deliver an editable exemplar `.pptx` as `office:pptx` describes rather
than claiming a `.potx`. To start from a supplied template, open it and save a new
`.pptx` candidate; never overwrite the template. Upstream issues open at the
reference date: a master header change does not reach existing slides and new
slides miss it ([#1111](https://github.com/storytold/deckcraft/issues/1111)), and
authoring a complete template from commands is incomplete
([#300](https://github.com/storytold/deckcraft/issues/300)). Verify master and
layout inheritance on actual renders.

## Optional native MCP interface

Prefer an already exposed native DeckCraft MCP tool when its schema and session
contract have been verified. Office does not declare a bundled MCP server because
the executable is supplied externally. The CLI remains available without a host
registering that server. Configure MCP using the active host's supported mechanism:

```text
deckcraft-cli mcp --automation-read-root EXISTING_PROJECT --automation-write-root EXISTING_OUTPUT
```

Both root directories must exist. Explicitly set both: supplying one root type
does not grant the omitted type. These bounds belong to headless MCP; the CLI
bridge does not enforce them. Do not claim confinement for desktop attachment.
`--connect` is incompatible with these root flags.

The reference server exposes `inspect_document`, `inspect_slide` with `index`,
`batch` with `commands` and `keepGoing:false`, and `save_presentation` with `path`.
`export` with `path`, `format:"png"`, `all:true`, `scale:2` writes preview files.
`render_slide` takes `slide` and `scale`, and does not accept an output `path`.
Discover the actual exposed schema before use. A connected desktop shares mutable
state; after a lost response, inspect state before replaying a mutating request.
