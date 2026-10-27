---
name: gridcraft
description: >
  Create, edit, inspect, calculate and check real Excel workbooks through the
  external GridCraft CLI or exposed MCP interface. TRIGGER WHEN: producing or
  editing XLSX for office:xlsx, recalculating formulas or checking workbook
  fidelity with GridCraft.
  DO NOT TRIGGER WHEN: only read-only package inspection is needed (use office:xlsx's inspector).
---

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
