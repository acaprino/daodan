<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

# GridCraft runtime and delegated contract

Reference: [storytold/gridcraft](https://github.com/storytold/gridcraft),
release [v0.11.1](https://github.com/storytold/gridcraft/releases/tag/v0.11.1),
source revision `ac8da7d49cbeb4be6aa1ad5869f3d29fe2da8cd9` (2026-10-22).
The repository is active and declares MIT OR Apache-2.0. This method delegates
to an installed runtime and redistributes no engine code. The reference release
is alpha; record the actual local version and read its command schema on use.

- [CLI contract](https://github.com/storytold/gridcraft/blob/v0.11.1/docs/cli.md)
- [MCP contract](https://github.com/storytold/gridcraft/blob/v0.11.1/docs/mcp.md)
- [File-format parity](https://github.com/storytold/gridcraft/blob/v0.11.1/docs/file-format-parity.md)
- [Known gaps](https://github.com/storytold/gridcraft/blob/v0.11.1/docs/gaps.md)

## Discover, then install on approval

Look for an actual exposed GridCraft MCP interface or `gridcraft-cli` in the
host's executable search path and verified application install location. Check
existence instead of assuming PATH registration. The desktop UI is not required
for headless CLI or MCP operations.

Then check the engine Office installed itself with
`office:intake`'s `engine_install.py find gridcraft`. When none exists, tell the
user in one line what `engine_install.py plan gridcraft` reports (official source, size,
licence, destination), record it, then run
`engine_install.py install gridcraft --approved`. It downloads only the pinned release asset
from `github.com/storytold/gridcraft`, checks its size and SHA-256, unpacks it into
the owned engine home (`~/.daodan/engines`, or `DAODAN_ENGINE_HOME`) and proves
`--version` before it reports success; without approval nothing is fetched.
Windows x64 is the verified path; Linux x86_64 and macOS assets are pinned by
digest and proved by the same probe. Elsewhere use the
[official release page](https://github.com/storytold/gridcraft/releases).

## Discover the actual API

`<gridcraft-cli>` below is the verified executable path, not a literal command:

```text
<gridcraft-cli> version
<gridcraft-cli> commands --json
<gridcraft-cli> functions --search LOOKUP
<gridcraft-cli> info source.xlsx --json
<gridcraft-cli> cat source.xlsx --range A1:F20 --formulas
<gridcraft-cli> eval "=SUM(B2:B9)" --in source.xlsx --json
```

`run` opens a file, a sample or a blank workbook, applies commands in order,
saves `--out` and prints requested ranges. The first failing step stops the run
with a non-zero exit. A script has one command per line, either `id={json}` or a
JSON object `{"command": "cell.set", "params": {...}}`:

```text
<gridcraft-cli> run --script steps.jsonl --out candidate.xlsx --print used --formulas
<gridcraft-cli> run --in source.xlsx --script steps.jsonl --out candidate.xlsx
```

Keep literal cell content in the script file rather than building shell-quoted
inline `--cmd` strings. Inputs beginning with `=` are formulas; treat user text
beginning with formula-significant characters as literal text unless a formula
is intended. Read current command definitions for parameters rather than guessing.

## Calculation and verification

GridCraft evaluates formulas with its own engine (upstream lists more than 500
functions, dynamic arrays, `LET` and `LAMBDA`; `functions` reports the installed set). Its results are evidence
for that engine. For a workbook Excel or another calculating application saved,
`check` recalculates every formula and compares it with the stored results, then
round-trips the file through GridCraft's writer and compares named categories:

```text
<gridcraft-cli> check source.xlsx --json
```

Mismatches roll up by function. Volatile functions and formulas saved without a
value, or under `fullCalcOnLoad`, are counted as having no oracle. A clean `check`
on the source is evidence that GridCraft calculates and preserves that workbook's
checked categories; it is not proof of every Excel feature. A workbook GridCraft
produced has no external oracle, so verify key results independently.

## Preservation limits at the reference version

- Upstream's top known gap is that saved XLSX output is not yet proven in
  Microsoft Excel on a real-world corpus. Excel fidelity remains unverified
  unless the candidate is actually opened in Excel.
- Slicers and their caches, timelines, the data model, table query tables,
  unmodelled `extLst` entries and some chart options are dropped on save.
  Pass-through keeps custom XML, external links, connections, sheet query tables,
  printer settings, form and ActiveX controls, OLE objects and sheet backgrounds.
- `.xlsm` keeps the VBA project byte-for-byte and never runs macros.
- `.xls`, `.xlsb` and `.ods` are imported (values; `.xls` also formulas) and saved
  only as `.xlsx`. Large workbooks of about 100 MB may not open; recalculation is
  single-threaded.

Run `check` or a no-edit round-trip with the packaged inspector before editing an
imported workbook. Unexplained loss blocks the affected edit.

## Templates

`.xltx` and `.xltm` open and save with the template content type chosen by the
output extension; `.xltx` drops a VBA project. "New from template" behaviour is
missing in the reference release: open the template and save a new `.xlsx`
candidate, never overwriting the template.

## MCP interface

`gridcraft-cli mcp` serves headless sessions over stdio; `--in FILE` starts with a
workbook open. `--connect PORT` drives a running app started with
`gridcraft --control PORT`, sharing its live state with the person at the window.
After a lost response in connected mode, inspect state before replaying a
mutating request.

The reference server exposes `execute_command`, `list_commands`,
`inspect_workbook`, `read_range`, `write_range`, `set_cell`, `get_cell`,
`evaluate_formula`, `select`, `format_range`, `open_workbook`, `save_workbook`,
`new_workbook`, `undo`, `redo`, `screenshot` (connected mode only) and
`list_functions`. Discover the actual exposed schema before use.

The reference release documents no folder-confinement flags for its MCP server.
Do not claim confinement of GridCraft file access; a caller that needs bounded
reads and writes must enforce them before passing paths to the engine.
