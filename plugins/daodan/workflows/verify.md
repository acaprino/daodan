---
description: >
  Check a Word, PowerPoint or Excel file for integrity defects without changing
  it: broken links and references, formula errors, inconsistent formulas, missing
  alternative text, empty placeholders and more. TRIGGER WHEN: the user asks to
  verify, check, validate or audit an existing DOCX, PPTX or XLSX.
argument-hint: "<file to verify>"
---

Verify the file named in: $ARGUMENTS

Load `office:integrity` and follow its Verify section on that exact file. Never
write to it. Cover the checks the static report lists as not performed with the
format's engine where available (`office:wordcraft`, `office:deckcraft`,
`office:gridcraft`), and label the rest unverified.

Deliver the verdict, the findings grouped by severity with locations and fix
classes, the coverage of the not-performed checks, and the file's SHA-256. Offer
`fix` for findings whose class is `safe` or `content`.
