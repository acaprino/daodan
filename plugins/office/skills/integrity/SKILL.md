---
name: integrity
description: >
  Verify the integrity of a Word, PowerPoint or Excel file with static rules, then
  repair what can be repaired on a separate candidate. TRIGGER WHEN: checking a
  DOCX, PPTX or XLSX for broken links, formula errors, missing alternative text,
  inconsistent formulas, empty placeholders or other defects, or fixing them.
  DO NOT TRIGGER WHEN: creating a new document, deck or workbook (use the office
  document, presentation or workbook workflows).
---

# Office file integrity

Read `references/rules.md` for the rules, severities and fix classes.

## Verify

Run the read-only checker on the exact file and keep its JSON report:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/integrity/scripts/office_verify.py" INPUT
```

Exit code 0 means no error finding, 1 an error finding or an unreadable package,
2 an unsupported or missing file. The report records the file's SHA-256, verdict
(`pass`, `warnings` or `fail`), counts per severity, findings per rule and the
checks it did not perform. Findings beyond `--max-per-rule` are counted, not listed.

When OfficeCLI is installed the checker also runs its schema validation and
issue scan and says so in `checkers`; otherwise schema validity stays in
`not_checked`. Static rules do not see layout or calculation. Cover the
`not_checked` items with the format's engine when it is available: render pages or slides and inspect them
for overflow and overlap, and run `office:gridcraft`'s `check` for recalculation.
Report any uncovered item as unverified. A `pass` is never a visual or calculation verdict.

Present findings grouped by severity, most severe first, each with its location
and fix class. Keep the source untouched.

## Fix

Repair only on a new candidate path; never overwrite the source. Load the format's
engine skill (`office:wordcraft`, `office:deckcraft` or `office:gridcraft`) and
follow its preservation steps before the first change.

- `safe`: apply.
- `content`: write content that only describes what is already present, such as
  alternative text read from the actual image or a title taken from the slide's
  own text. Never invent facts.
- `review`: apply only when the user's request names that change; otherwise list
  it with the proposed edit.
- `none`: report.

After the changes, run the checker on the candidate and compare the two reports.
Every fixed finding must be gone and no new finding may appear; otherwise discard
the candidate or the failing change. Run the format's inspector `compare` (or
`coverage` after structural edits) between source and candidate and account for
every delta. Deliver the candidate with both reports, the applied changes, the
findings left open with their reasons, and the checks that remained unverified.
