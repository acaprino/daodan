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

## Discover without installing

Look for an actual exposed GridCraft MCP interface or `gridcraft-cli` in the
host's executable search path and verified application install location. Check
existence instead of assuming PATH registration. The desktop UI is not required
for headless CLI or MCP operations. Use the
[official release page](https://github.com/storytold/gridcraft/releases) for a
missing runtime; installation is a separate action under user authorization.

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
