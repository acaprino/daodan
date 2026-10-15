---
description: >
  Run a Codebase Map: document WHAT, WHY, HOW and CONSEQUENCES into phased files, with concurrent-run support.
  TRIGGER WHEN: the user asks for a deep analysis of an unfamiliar codebase, pre-review context, or a structure-plus-semantics snapshot.
  DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use /project-knowledge:guide) or a shallow overview.
argument-hint: "<target path> [--critical] [--comments] [--docs-only] [--phase N] [--depth=lite|full] [--run-name <name>] [--update] [--no-update] [--resume-from [N]] [--stop-after N]"
---

<!-- Codebase Map shared instruction wrapper. -->

## Method loads

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/entry-analyze.md` | all | always |

Read the resource and nested loads in this same coordinator context. Preserve inputs,
permissions, ownership and delivery. Dispatch `codebase-map:map-analyst` in the
required isolated analysis phase. Helpers belong to `codebase-map`.
