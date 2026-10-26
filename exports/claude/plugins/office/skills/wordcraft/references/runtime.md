<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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
