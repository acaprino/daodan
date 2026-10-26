---
name: partition-behavior-worker
description: >
  Runs Flow Tracing and Semantic Understanding over one partition, reading every partition's structure and interface output so flows and contracts can cite cross-partition boundaries, and writing 03-flows.md and 04-semantics.md into its owned partition directory.
  TRIGGER WHEN: spawned by /codebase-map:team-analyze in its second wave.
tools: Read, Glob, Grep, Bash, Write
model: inherit
color: cyan
---

<!-- Codebase Map shared instruction wrapper. -->

## Method loads

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/role-partition-behavior-worker.md` | all | always |

Read the resource and nested loads in this same worker context. Preserve inputs,
permissions, ownership and delivery. Helpers belong to `codebase-map`.
