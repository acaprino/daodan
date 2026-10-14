---
description: >
  Multi-agent Codebase Map for large or multi-workspace codebases: splits the project into its natural units, works them in parallel, and publishes one consolidated result set to the .codebase-map/ root.
  TRIGGER WHEN: the user wants Codebase Map analysis on a monorepo, or a cross-partition interconnection map produced as part of the same flow.
  DO NOT TRIGGER WHEN: the target is a single small directory, or the user wants a documentation-only audit (use /codebase-map:analyze, optionally with --docs-only).
argument-hint: "<target> [--critical] [--comments] [--depth=lite|full] [--partition <path>] [--partition-name <name>] [--skip-interconnect] [--skip-synthesis] [--run-name <name>] [--yes] [--update] [--no-update]"
---

<!-- Codebase Map shared instruction wrapper. -->

## Compatibility entry

`codebase-xray:team-analyze` is the retained workflow identity for Codebase Map.

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
| `references/entry-team-analyze.md` inside the loaded `codebase-map:map-method` skill | all | always |

Read the complete shared instruction resource and its nested Method loads, then
execute it in this same coordinator context. Forward all caller inputs and arguments
unchanged, including flags, run identity, current manifest and explicit output
paths. Preserve authorization, tool permissions, ownership and delivery accounting.
This wrapper owns registration metadata; the shared resource contains behavior only.
Loading it does not start another context. Do not dispatch another worker to execute this shared resource. Never load
a registered role as a skill. The canonical method is the skill being loaded.

## Canonical dispatch bindings

The shared workflow's short worker names resolve to the canonical provider roles
declared by this entry's sidecar and generated harness:

| Shared worker name | Canonical role binding |
|---|---|
| `partition-behavior-worker` | `codebase-map/partition-behavior-worker` |
| `partition-quality-worker` | `codebase-map/partition-quality-worker` |
| `partition-structure-worker` | `codebase-map/partition-structure-worker` |
| `partition-synthesizer` | `codebase-map/partition-synthesizer` |
| `semantic-interconnect-mapper` | `codebase-map/semantic-interconnect-mapper` |

Use those generated bindings for workflow-owned workers, preserving required
isolation, barriers, file ownership and the delivery ledger. The compatibility
wrapper itself stays in the coordinator context.
