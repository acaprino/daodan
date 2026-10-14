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

## Compatibility entry

`codebase-xray:partition-structure-worker` is the retained role identity for Codebase Map.

Load `codebase-map:map-method` through the active host's advertised skill
identity and verify its provider. Resolve the references named below relative to
that loaded skill's own installed location. Every installed-root marker, nested
Method load and helper path in those references belongs to `codebase-map`, never
to this compatibility package. Follow the provider's host binding when its native
skill identity differs from its logical identity.

## Method loads

| Resource | Sections | When |
|---|---|---|
| `codebase-map:map-method` | all | always |
| `references/role-partition-structure-worker.md` inside the loaded `codebase-map:map-method` skill | all | always |

Before executing the shared worker, require the coordinator to have completed
root migration. For supplied analysis-root bindings (run, partition, output or
`xray_path`), use the loaded provider's `migrate_root.py resolve` command from
`references/migration.md` and pass the resolved paths to the shared worker.
Preserve each run ID, suffix and ownership. If resolution still selects
`.codebase-xray`, stop for coordinator migration. This worker performs no root
migration and never writes the legacy store. Forward other inputs unchanged.

Read the complete shared instruction resource and its nested Method loads, then
execute it in this same worker context. Preserve flags, run identity and current manifest; translate only the
analysis-root path bindings as required above. Preserve authorization, tool permissions, ownership and delivery accounting.
This wrapper owns registration metadata; the shared resource contains behavior only.
Loading it does not start another context. Do not dispatch another worker to execute this shared resource. Never load
a registered role as a skill. The canonical method is the skill being loaded.
