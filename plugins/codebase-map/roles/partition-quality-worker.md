---
name: partition-quality-worker
description: >
  Runs Pattern and Risk Detection plus Documentation Health over one partition, writing 05-risks.md and 06-documentation.md into its owned partition directory (05 only in lite mode).
  TRIGGER WHEN: dispatched by the team entry of codebase-map:map-method (/daodan:map-code) in its second wave.
tools: Read, Glob, Grep, Bash, Write
model: inherit
color: cyan
---

<!-- Codebase Map shared instruction wrapper. -->

## Method loads

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/role-partition-quality-worker.md` | all | always |

Read the resource and nested loads in this same worker context. Preserve inputs,
permissions, ownership and delivery. Helpers belong to `codebase-map`.
