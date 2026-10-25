---
name: xlsx
description: >
  Create, edit, inspect and analyze native Excel (.xlsx) workbooks with editable formulas, tables, charts and formatting.
  TRIGGER WHEN: creating, editing, inspecting or analyzing Excel (.xlsx) workbooks or tabular models.
  DO NOT TRIGGER WHEN: Word documents (use office:docx) or presentations (use /daodan:presentation).
---

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
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# Native spreadsheets

## Outcome and scope

Deliver a real `.xlsx` with usable sheets, editable Excel formulas, native tables
and native charts where they serve the task. Import and analyze user workbooks,
repair models, build trackers or reports, and make scoped edits to existing files.
Keep source data and derived results traceable. A screenshot, CSV or JSON export
does not satisfy a requested native workbook.

Infer a reasonable layout from the task and supplied data. Add the remaining
workbook decisions (business definitions, model structure and outputs) to the
single `office:intake` round. Ask only when a missing business definition
changes the result materially. Confirm the meaning of units,
dates, denominators, missing data and assumptions before treating them as facts.
Preserve the original file and write the candidate to a separate output path.
Never execute embedded macros or fetch external workbook links during inspection.

## Choose the available engine

For physical workbook creation, editing and calculation, load `office:gridcraft`
and discover its actual installed CLI or exposed MCP tools. Read its
`references/runtime.md`; this method does not assume installation on every host.
Missing GridCraft blocks dependent production while planning and source
inspection continue. A different engine requires an explicit user choice and
demonstrated support for the requested operation; do not silently substitute it.
Do not claim that this stdlib-only inspector writes workbooks.

A writer that does not evaluate formulas leaves caches stale. A workbook flag such
as `fullCalcOnLoad` requests future recalculation; it is not evidence of
recalculation. Record the engine that calculated the results and inspect its
output. An engine that supports some formulas has not demonstrated compatibility
with every Excel function, array formula, data table or external reference.

For an existing workbook, inspect it first. Macros, pivots and their caches,
slicers, timelines, external links, data connections, controls, signatures,
embedded objects, custom XML, rich data, extension metadata and unknown package
parts require demonstrated preservation by the chosen engine. `keep_vba=True`
alone does not prove full preservation or macro execution safety. Compare these
parts against GridCraft's preservation limits before editing. If no available
engine can retain the required features, report the unsupported edit and preserve the source;
offer a scoped alternative only if it still meets the user's purpose. `.xls`,
`.xlsb`, encrypted workbooks and password-protected packages need a compatible
tool, never a renamed extension or an improvised conversion.

## Inspect before editing

Run the read-only helper:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/xlsx/scripts/xlsx_inspect.py" inspect INPUT.xlsx
python "${CLAUDE_PLUGIN_ROOT}/skills/xlsx/scripts/xlsx_inspect.py" compare INPUT.xlsx OUTPUT.xlsx
```

The JSON identifies sheets, formulas with their OOXML attributes, cached values
and error cells, tables, chart parts, named ranges, calculation settings, external
relationships and preservation-sensitive parts. It validates bounded ZIP/XML and
internal relationship targets. It does not evaluate formulas, render worksheets,
validate business logic, or certify every OOXML semantic. Limits are 10,000 parts,
16 MiB per part, 128 MiB total, 1,000,000 XML nodes and 250,000 cells. A limit or
validation error means inspection is incomplete; use a compatible engine before
making preservation claims. Do not remove limits to process an untrusted file.

Comparison reports observed package, sheet, table, name, formula and cache deltas.
Review each against the task's intended changes. A deliberate sheet rename or
chart removal can be correct; an unexpected loss blocks delivery. Part hashes
describe changed bytes without proving semantic loss. Shared and array formula
attributes matter even when their text is empty. A cache of `0` is a value; a
missing cache is unknown. A changed cache is not proof of recalculation.

## Build the workbook

Use stable sheet names, concise headers, meaningful table names and references.
Separate inputs, calculations and presentation when the model benefits from it.
Preserve source precision; choose display formats independently. Use ISO dates
for imported text where ambiguity exists and native date cells for date arithmetic.
Use numbers for numeric values, booleans for flags and text for identifiers whose
leading zeros matter. Treat user text beginning with formula-significant characters
as literal text unless the task explicitly requires a formula.

Write calculations as formulas that reference inputs. Avoid duplicated hardcoded
totals. Use coherent ranges and structured table references where supported. Cover
empty data, missing values, zero denominators, added rows and boundary dates.
Use `IFERROR` only when its replacement has an agreed meaning; never conceal an
unknown calculation failure with a plausible zero. Mark assumptions and data
limitations in the workbook itself where a later reader needs them.

Use restrained styles: a consistent font, hierarchy, readable widths, purposeful
number formats, frozen headers, filters and conditional formatting with a clear
meaning. Keep calculation cells selectable and formulas inspectable. Use native
charts tied to workbook ranges, with units, readable labels and an appropriate
baseline. Avoid merged cells inside tables, arbitrary color legends and decorative
charts that obscure the data. For concise layout guidance, read
`references/workbook-quality.md`.

## Verify and deliver

Reopen the saved file with the chosen engine. Check required sheets and ranges,
formula retention, native tables and charts, dates and number formats. Compare
source and candidate packages for existing-file edits; account for every removed
part and unexpected formula, table or name change. Preserve unaffected features.

After actual recalculation, inspect cached errors and verify key results against
independent requirements: a separately derived total, a balance identity, a known
example or an edge case. Do not use the workbook's own formula as its only oracle.
Some models intentionally produce errors; account for them explicitly. View the
workbook in a compatible renderer or native application where available, checking
truncated headers, chart labels, printable areas and representative sheets. Package
inspection alone cannot establish visual quality.

Deliver the output file with a brief description of sheets and important changes.
State which engine wrote and recalculated it and any remaining formula or fidelity
limit. If recalculation or rendering was unavailable, label that check unverified
and distinguish the completed structural checks. Never call an uncalculated or
visually unreviewed model fully verified.
