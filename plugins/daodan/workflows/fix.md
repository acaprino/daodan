---
description: >
  Repair integrity defects in a Word, PowerPoint or Excel file on a new copy,
  then verify that every repaired finding is gone and nothing new appeared.
  TRIGGER WHEN: the user asks to fix, repair or clean up defects in an existing
  DOCX, PPTX or XLSX, or to apply the findings of verify.
argument-hint: "<file to fix> [findings or changes to apply]"
---

Fix the file named in: $ARGUMENTS

Load `office:integrity`. Run its Verify section on the source first, unless a
report for the same SHA-256 is supplied. Then follow its Fix section: apply `safe`
and `content` findings, apply `review` findings only when the request names them,
and write the result to a new candidate path. The source is never modified.

Verify the candidate and compare both reports. Deliver the candidate only when
every applied fix is confirmed and no new finding appeared; otherwise deliver the
source report, the rejected change and its cause. Include the applied changes,
the findings left open with their reasons and the checks that remained unverified.
