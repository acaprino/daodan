# Workbook quality

Start from the reader's decision. Put the answer and its units close to the data
that supports it. Use a summary sheet only when it saves the reader work.

| Element | Useful default | Verification |
| --- | --- | --- |
| Input table | One record per row; unique column headers; native filter | Added records do not omit totals or chart data |
| Formulas | References to inputs; consistent patterns; editable cells | Check a result independently and exercise empty or zero input |
| Number formats | Units in headers; dates and percentages explicit | Display rounding does not change stored precision |
| Navigation | Short sheet names; frozen header; useful widths | Open at a meaningful area with headers visible |
| Charts | Native range-based objects; readable labels; truthful scale | Chart remains editable and matches the underlying cells |
| Printing | Meaningful print area; sensible orientation and page scale | Headers remain legible and columns are not cut off |
| Existing features | Preserve unaffected sheets, names, tables and objects | Compare parts and formulas before and after the edit |

For business models, give assumptions a visible home with source, date and units.
If colors distinguish inputs and calculations, include their meaning and use them
consistently. Keep the workbook useful without relying on color alone.

For formula validation, choose cases from the requirements rather than from the
implementation: a known transaction total, beginning and ending balances, an empty
dataset or a denominator of zero. Recalculation evidence names the actual engine,
the saved output and the checked results. Saved formula text and a recalculation
flag establish none of those facts by themselves.
