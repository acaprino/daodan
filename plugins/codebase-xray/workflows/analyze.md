---
description: >
  Run a Codebase Map: document WHAT, WHY, HOW and CONSEQUENCES into phased files, with concurrent-run support.
  TRIGGER WHEN: the user asks for a deep analysis of an unfamiliar codebase, pre-review context, or a structure-plus-semantics snapshot.
  DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use /project-knowledge:guide) or a shallow overview.
argument-hint: "<target path> [--critical] [--comments] [--docs-only] [--phase N] [--depth=lite|full] [--run-name <name>] [--update] [--no-update] [--resume-from [N]] [--stop-after N]"
---

<!-- Codebase Map shared instruction wrapper. -->

## Compatibility entry

`codebase-xray:analyze` is the retained workflow identity for Codebase Map.

Load `codebase-map:map-method` through the active host's advertised skill
identity and verify its provider. Resolve the references named below relative to
that loaded skill's own installed location. Every installed-root marker, nested
Method load and helper path in those references belongs to `codebase-map`, never
to this compatibility package. Follow the provider's host binding when its native
skill identity differs from its logical identity.

## Method loads

| Resource | Sections | When |
|---|---|---|
| `codebase-map:map-method` | before: Method loads; section: Resources | always |
| `references/entry-analyze.md` inside the loaded `codebase-map:map-method` skill | all | always |

Read the complete shared instruction resource and its nested Method loads, then
execute it in this same coordinator context. Forward all caller inputs and arguments
unchanged, including flags, run identity, current manifest and explicit output
paths. Preserve authorization, tool permissions, ownership and delivery accounting.
This wrapper owns registration metadata; the shared resource contains behavior only.
Loading it does not start another context. Do not dispatch another worker to
execute this shared coordinator resource. Dispatch `codebase-map:map-analyst`
in the required isolated analysis phase. Do not read analyzed source or execute
phase procedures in this context.
Never load a registered role as a skill. Helpers belong to `codebase-map`.
