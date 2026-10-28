---
name: gridcraft
description: >
  Create, edit, inspect, calculate and check real Excel workbooks through the
  external GridCraft CLI or exposed MCP interface. TRIGGER WHEN: producing or
  editing XLSX for office:xlsx, recalculating formulas or checking workbook
  fidelity with GridCraft.
  DO NOT TRIGGER WHEN: only read-only package inspection is needed (use office:xlsx's inspector).
---

> This package retains its lifecycle callback scripts, but this host has no declared native hook registration. Use the method's explicit workflow checkpoints; automatic interception outside those workflows is unavailable.

<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# GridCraft workbook production

Use the external [GridCraft](https://github.com/storytold/gridcraft) engine to
produce, edit and calculate the actual workbook. Read `references/runtime.md`
before the first operation. Office ships this method and the pinned installer of
`office:intake`, not the engine or an MCP server. Discover the executable or
actual exposed MCP tools and inspect their current schema. When none exists,
follow the engine recovery in `office:intake`'s dependency preflight. Do not
invent commands or silently install another library.

When called by `office:xlsx`, consume its accepted workbook plan and source
inventory. The workbook coordinator builds the file; do not start another
workflow. Map the plan to supported native sheets, cells, formulas, tables,
names, conditional formats, validations and charts.

## Inspect and preserve

Record executable/version and input identity. For an existing workbook, run the
`office:xlsx` inspector first, then `check` the source to learn which formulas
GridCraft reproduces and which categories survive its round-trip. Save a no-edit
round-trip to a separate candidate and compare packages before substantive edits.
GridCraft remains alpha; an opens/saves result does not demonstrate preservation
of every Excel feature. Features listed as dropped in the runtime reference block
an edit of a workbook that contains them, unless the user accepts that loss.

## Build the physical file

Discover commands, then write a bounded script in the owned workspace and run it
to an explicit new output path. For edits use `--in` with the source; for a new
workbook start blank. For a template, open the `.xltx` and save a new `.xlsx`;
never overwrite the template. Keep calculations as formulas referencing inputs,
and tables, names and charts native.

Verify that the output exists at the resolved path, reopen it with `info` and
read the key ranges with formulas and values. Command success alone is
insufficient. A CSV, JSON, HTML or screenshot does not satisfy a requested XLSX.

## Calculate, check and deliver

Read calculated values for the key results and compare them with independent
requirements: a separately derived total, a balance identity, a known example or
an edge case. A workbook's own formula is not its only oracle. For an edited
workbook that Excel saved, keep the source `check` result as the baseline and
report any function mismatch it found.

Return the physical `.xlsx`, engine/version, candidate identity, checked results,
preservation evidence and remaining gaps to the coordinator. GridCraft results do
not prove identical Microsoft Excel calculation or rendering; that requires the
candidate opened in Excel. Missing runtime blocks dependent production while
planning and source inspection continue.
