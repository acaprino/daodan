---
name: semantic-interconnect-mapper
description: >
  Phase 1b context builder mapping contracts, invariants, domain rules, call graphs and integration boundaries for downstream reviewers and doc writers.
  TRIGGER WHEN: dispatched by the team entry of codebase-map:map-method, by senior-review's branch review (/daodan:review-branch) or by project-knowledge's guide method (/daodan:write-docs), or asked to map contracts, invariants, domain rules or integration boundaries.
  DO NOT TRIGGER WHEN: no prior context artifact exists yet (run /daodan:map-code or codebase-explorer first).
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
