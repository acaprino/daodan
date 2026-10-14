---
name: xray-method
description: >
  Compatibility skill for the former Codebase X-ray name. Loads the canonical
  Codebase Map method while preserving the caller's scope and execution context.
---

<!-- Codebase Map shared instruction wrapper. -->

## Canonical method

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

Use the loaded method in this same context under the caller's existing scope,
authorization, permissions and output ownership. Do not dispatch another worker,
invent an extra analysis run, or load a registered role as a skill.

## Compatibility boundary

The retained plugin exposes the former registered workflow, skill and role IDs.
All analysis behavior belongs to `codebase-map`, and all new analysis writes use
its canonical output contract. Literal helper paths into an older cached plugin
version are not redirected. Resolve the helper from the installed canonical
`map-method` skill before reusing its arguments; do not execute a guessed cache
path or copy an old helper into this compatibility package.

Retained analysis-root bindings use the canonical method's migration resolver.
Loading this alias alone starts no analysis or migration.
