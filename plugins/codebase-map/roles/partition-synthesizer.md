---
name: partition-synthesizer
description: >
  Consolidates per-partition Codebase Map outputs into 01..07.md in the run directory with cross-partition sections and a team-mode final report.
  TRIGGER WHEN: dispatched by the team entry of codebase-map:map-method (/daodan:map-code) in its consolidation phase.
  DO NOT TRIGGER WHEN: outside that team pipeline. The classic analyze entry dispatches isolated codebase-map:map-analyst.
tools: Read, Glob, Grep, Write
model: inherit
color: purple
---

<!-- Codebase Map shared instruction wrapper. -->

## Method loads

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/role-partition-synthesizer.md` | all | always |

Read the resource and nested loads in this same worker context. Preserve inputs,
permissions, ownership and delivery. Helpers belong to `codebase-map`.
