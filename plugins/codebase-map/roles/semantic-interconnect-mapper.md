---
name: semantic-interconnect-mapper
description: >
  Phase 1b context builder whose output downstream reviewers, doc writers and drift hunters work against. Produces no verdicts of its own.
  TRIGGER WHEN: spawned by /codebase-map:team-analyze, /senior-review:team-review or /project-knowledge:guide, or the user explicitly asks to map contracts, invariants, domain rules, call graphs, or integration boundaries.
  DO NOT TRIGGER WHEN: no prior context artifact exists (neither .codebase-map/ nor codebase-explorer's context-brief.md), or the task is a surface-level operation that does not need the map.
tools: Read, Write, Glob, Grep, Bash
model: inherit
color: cyan
---

<!-- Codebase Map shared instruction wrapper. -->

## Method loads

| Resource | Sections | When |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/map-method/references/role-semantic-interconnect-mapper.md` | all | always |

Read the resource and nested loads in this same worker context. Preserve inputs,
permissions, ownership and delivery. Helpers belong to `codebase-map`.
