---
description: >
  Readability-only rewrite of existing source.
  TRIGGER WHEN: the user asks to clean up code, improve naming, remove AI-generated boilerplate, simplify structure, or make code more maintainable without changing behavior.
  DO NOT TRIGGER WHEN: the target is prose or text (use /text-humanizer:humanize-text), or deep architectural refactoring (return to the development plan).
argument-hint: "<file or directory> [--dry-run] [--strict] [--yes] [--force]"
---

# /clean-code:clean-code

Load the `clean-code:readability-method` skill with the target and `$ARGUMENTS`. Supply the
accepted preview/scope, original flags and output root when a coordinator calls
the method. The role owns transformation guidelines; the method owns preparation,
baseline, candidate gate and recovery. Existing edits survive a failed rewrite.
