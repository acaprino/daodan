---
description: >
  Multi-agent Codebase Map for monorepos and multi-workspace projects: analyzes partitions in parallel and publishes consolidated results to .codebase-map/.
  TRIGGER WHEN: running Codebase Map analysis on a monorepo or generating a cross-partition interconnection map.
  DO NOT TRIGGER WHEN: single small directory or documentation-only audit (use /codebase-map:analyze).
argument-hint: "<target> [--format sqlite|json] [--critical] [--comments] [--depth=lite|full] [--partition <path>] [--partition-name <name>] [--skip-interconnect] [--skip-synthesis] [--run-name <name>] [--yes] [--update] [--no-update]"
---

<!-- Codebase Map shared instruction wrapper. -->

## Method loads

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/entry-team-analyze.md` | all | always |

Read the resource and nested loads in this same coordinator context. Preserve inputs,
permissions, ownership and delivery. Helpers belong to `codebase-map`.
