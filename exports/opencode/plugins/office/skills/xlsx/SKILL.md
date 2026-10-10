---
name: xlsx
description: >
  Create, edit, inspect and analyze native Excel workbooks with editable formulas,
  tables, charts and professional formatting. Preserve existing workbook features,
  verify calculated results with a compatible engine and disclose unsupported fidelity.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/`, `agents/` and `commands/`. The loader substitutes it in every body it registers; in any other file, resolve it once from where that file was loaded.

# Native spreadsheets

## Outcome and scope

Deliver a real `.xlsx` with usable sheets, editable Excel formulas, native tables
and native charts where they serve the task. Import and analyze user workbooks,
repair models, build trackers or reports, and make scoped edits to existing files.
Keep source data and derived results traceable. A screenshot, CSV or JSON export
does not satisfy a requested native workbook.

Infer a reasonable layout from the task and supplied data. Ask only when a missing
business definition changes the result materially. Confirm the meaning of units,
dates, denominators, missing data and assumptions before treating them as facts.
Preserve the original file and write the candidate to a separate output path.
Never execute embedded macros or fetch external workbook links during inspection.

## Choose the available engine

Discover tools and installed runtimes before creating or editing the workbook.
Prefer the host's bundled spreadsheet or artifact engine when it is available.
Read that engine's current instructions and inspect its actual API; this skill does
not assume a vendor-specific runtime, connector or package exists on every host.

For supported simple OOXML workbooks, an explicitly available `openpyxl` is a
fallback for creation and editing. Load editable workbooks with formulas retained
(`data_only=False`); use a separate `data_only=True` read only to inspect caches.
Never save the editable candidate from a cached-value-only load. Check the installed
version's feature support before a round-trip. Do not silently install dependencies
or claim that this stdlib-only inspector writes workbooks.

`openpyxl` writes formulas but does not evaluate them. A workbook flag such as
`fullCalcOnLoad` requests future recalculation; it is not evidence of recalculation.
For formula work, use an available compatible Excel or LibreOffice calculation
engine, or a documented host engine whose support covers the formulas in this
model. Record the engine and inspect its output after recalculation. An engine
that supports some formulas has not demonstrated compatibility with every Excel
function, array formula, data table or external reference.

For an existing workbook, inspect it first. Macros, pivots and their caches,
slicers, timelines, external links, data connections, controls, signatures,
embedded objects, custom XML, rich data, extension metadata and unknown package
parts require demonstrated preservation by the chosen engine. `keep_vba=True`
alone does not prove full preservation or macro execution safety. Prefer the native
application or a compatible host engine for such files. If no available engine can
retain the required features, report the unsupported edit and preserve the source;
offer a scoped alternative only if it still meets the user's purpose. `.xls`,
`.xlsb`, encrypted workbooks and password-protected packages need a compatible
tool, never a renamed extension or an improvised conversion.

## Inspect before editing

Run the read-only helper:

```text
python "<plugin-root>/skills/xlsx/scripts/xlsx_inspect.py" inspect INPUT.xlsx
python "<plugin-root>/skills/xlsx/scripts/xlsx_inspect.py" compare INPUT.xlsx OUTPUT.xlsx
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
