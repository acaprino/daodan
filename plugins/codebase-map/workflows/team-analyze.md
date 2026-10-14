---
description: >
  Multi-agent Codebase Map for large or multi-workspace codebases: splits the project into its natural units, works them in parallel, and publishes one consolidated result set to the .codebase-map/ root.
  TRIGGER WHEN: the user wants Codebase Map analysis on a monorepo, or a cross-partition interconnection map produced as part of the same flow.
  DO NOT TRIGGER WHEN: the target is a single small directory, or the user wants a documentation-only audit (use /codebase-map:analyze, optionally with --docs-only).
argument-hint: "<target> [--critical] [--comments] [--depth=lite|full] [--partition <path>] [--partition-name <name>] [--skip-interconnect] [--skip-synthesis] [--run-name <name>] [--yes] [--update] [--no-update]"
---

<!-- Codebase Map shared instruction wrapper. -->

## Method loads

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/entry-team-analyze.md` | all | always |

Read the resource and nested loads in this same coordinator context. Preserve inputs,
permissions, ownership and delivery. Helpers belong to `codebase-map`.
