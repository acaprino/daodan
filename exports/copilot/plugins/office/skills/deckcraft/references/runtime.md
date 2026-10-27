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

# External DeckCraft runtime

Reference release: **0.10.0**, tag `v0.10.0`, commit
`b47195feec0f0fe4220d8943ad1c8add5dad8072`, released 2026-10-22.
Upstream is active but describes alpha fidelity limits. Source is dual licensed
MIT OR Apache-2.0. No upstream implementation is copied into Office.

- [Official release and platform packages](https://github.com/storytold/deckcraft/releases/tag/v0.10.0)
- [CLI contract](https://github.com/storytold/deckcraft/blob/v0.10.0/apps/deckcraft-cli/src/help.rs)
- [MCP contract](https://github.com/storytold/deckcraft/blob/v0.10.0/docs/mcp.md)
- [MIT license](https://github.com/storytold/deckcraft/blob/v0.10.0/LICENSE-MIT)

Discovery order: `DECKCRAFT_CLI`, then PATH, then the engine Office installed
itself. When none exists, tell the user in one line what
`office:intake`'s `engine_install.py plan deckcraft` reports (official source,
size, licence, destination), record it, then run
`engine_install.py install deckcraft --approved`. It downloads only
the pinned release asset from `github.com/storytold/deckcraft`, checks its size and
SHA-256, unpacks it into the owned engine home (`~/.daodan/engines`, or
`DAODAN_ENGINE_HOME`) and proves `--version` before it reports success; without
approval nothing is fetched. Pinned platforms: Windows x64, Linux x86_64 and macOS.
Windows x64 is the verified path; the other assets are pinned by digest and proved
by the same `--version` probe. On any other platform install the official package
yourself and set `DECKCRAFT_CLI`. Do not launch the desktop app merely to use the
CLI. The bridge's `--binary ABSOLUTE_PATH` before its subcommand overrides
discovery. Verify the
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
