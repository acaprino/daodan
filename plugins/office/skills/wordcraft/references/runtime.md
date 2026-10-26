# WordCraft runtime and delegated contract

Reference: [storytold/wordcraft](https://github.com/storytold/wordcraft),
release [v0.10.0](https://github.com/storytold/wordcraft/releases/tag/v0.10.0),
source revision `9130181a5fdaee2293e67756fd5458c601489f3c` (2026-10-22).
The repository is active and declares MIT OR Apache-2.0. This method delegates
to an installed runtime and redistributes no engine code. The reference release
is alpha; record the actual local version and read its command schema on use.

## Discover without installing

Look for an actual exposed WordCraft MCP interface or `wordcraft-cli` in the
host's executable search path and verified application install location. The
Windows desktop distribution can include `wordcraft-cli.exe` alongside the app
(for example `C:\Program Files\WordCraft\wordcraft-cli.exe`); check existence
instead of assuming PATH registration or that path on another host. The desktop
UI is not required for ordinary headless CLI operations.

Use the [official release page](https://github.com/storytold/wordcraft/releases)
for a missing runtime. Installation is a separate action under user authorization;
Office installation does not install WordCraft. MCP is an optional transport and
must be configured/exposed by the host before use. Do not assume that an MCP
server process or file access grants every parent-context capability.

## Discover the actual API

`<wordcraft-cli>` below is the verified executable path, not a literal command:

```text
<wordcraft-cli> --version
<wordcraft-cli> run --help
<wordcraft-cli> commands --json
<wordcraft-cli> inspect source.docx
<wordcraft-cli> text source.docx
<wordcraft-cli> info source.docx
```

For v0.10.0, a minimal new-file job has this structure. Replace the demonstration
text and settings with the accepted design; A4 and these margins are examples,
not global defaults:

```json
{
  "template": "blank",
  "commands": [
    {"command": "layout.size", "params": {"name": "A4"}},
    {"command": "layout.margins", "params": {"top": 54, "bottom": 54, "left": 54, "right": 54}},
    "para.heading1",
    {"command": "text.insert", "params": {"text": "Document title"}},
    "text.newParagraph",
    "para.normal",
    {"command": "text.insert", "params": {"text": "Accepted body content."}}
  ],
  "save": ["output.docx", "output.pdf"]
}
```

The reference version uses points for these layout parameters. Existing-file
jobs use `file` for the input and a different output path in `save`. Save paths
are relative to the script directory; paths inside command parameters are
relative to the process working directory. Prefer verified absolute paths when
crossing workspaces. Keep literal content in the JSON file rather than building
shell-quoted inline command strings.

```text
<wordcraft-cli> run --script job.json
<wordcraft-cli> info output.docx
<wordcraft-cli> render output.docx page-1.png --page 1 --scale 2
<wordcraft-cli> convert output.docx output.pdf --update-fields
```

Inspect every saved artifact. PDF export or a field-update flag does not prove
all fields or Microsoft Word layout features were faithfully evaluated. A
successful exit can still leave missing content or ignored formatting fields.

## Preservation and permission limits

The local probe can differ from the reference release. For example, v0.8.0 uses
`run --template T --cmd id={json} --cmd id --save output.docx` and does not accept
`--script`. Use the verified command/parameter registry for that version. Pass
arguments directly to a process API; do not join content-bearing JSON into an
executable shell string. Save DOCX and use `convert` separately when that version
does not support the newer script/save-array interface. Do not automatically
upgrade an installed runtime merely to match these reference examples.

Read the runtime's current feature/parity documentation for the actual input.
The reference version preserves many imported chart/SmartArt/OLE package parts,
but preservation does not imply full editability or equivalent rendering.
Advanced drawings, some VML/row cases, 3D and revision features have limits.
Perform a real no-edit round-trip and native package comparison for existing
documents; unexplained feature loss blocks that editing path.

MCP automation read/write roots are transport-specific options. Do not copy them
onto arbitrary CLI commands or combine them with connection modes without checking
current help. Never widen filesystem access to make an operation pass. Physical
printing and UI requests require an available application interface; `run --print`
is stdout reporting. Use PDF export for a printable artifact when requested.
