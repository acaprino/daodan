---
name: partition-structure-worker
description: >
  Runs Structure Extraction and Interface Analysis over one partition, writing 01-structure.md and 02-interfaces.md into its owned partition directory.
  TRIGGER WHEN: spawned by /codebase-map:team-analyze in its first wave.
  DO NOT TRIGGER WHEN: outside that pipeline; /codebase-map:analyze extracts structure inline without an agent.
tools: Read, Glob, Grep, Bash, Write
model: inherit
color: cyan
---

<!-- Codebase Map shared instruction wrapper. -->

## Method loads

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/role-partition-structure-worker.md` | all | always |

Read the resource and nested loads in this same worker context. Preserve inputs,
permissions, ownership and delivery. Helpers belong to `codebase-map`.
