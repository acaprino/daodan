---
name: kernel-marketplace
description: >
  Maintain neutral multi-host plugin kernels through their compiler instead of editing generated host packages.
  TRIGGER WHEN: marketplace operations target daodan/v1 kernels or compiler-managed exports.
  DO NOT TRIGGER WHEN: the target is a legacy Claude marketplace with hand-authored native packages.
---

# Kernel marketplace operations

Identify the source profile first. Read the target's durable instructions,
plugins/*/plugin.toml and adapter declarations. A daodan/v1 manifest establishes
the neutral profile even though generated catalogs also resemble native packages.

## Source boundary

Hand-authored plugin source: plugin.toml, roles/, workflows/ with MD and TOML
sidecars, skills/, contracts/ and policies/. Adapter mechanisms live in adapters/.
A root references/, scripts/ or mcp/ is not a shipped runtime resource; put helpers
under skills/<name>/ and declare an MCP server in plugin.toml when needed.

Generated exports and root marketplace manifests are output. Never register a
kernel by editing catalog arrays, author a native commands/ copy, or hand-fix
one host's export. Markdown is behavior, TOML declarative metadata.
No name repeats across role, skill and workflow kinds within a kernel.

## Health and review

Use the target compiler's read-only validation/drift command, dependency,
registration, bundled-path, fact-anchor and vocabulary gates. On Daodan the
authoritative command is python scripts/daodan_build.py --check --support, followed
by the required scripts and tests listed in its durable instructions.

A native-package audit can check generated package integrity, but its registration
fixes must be translated back into kernel declarations. Report source defects,
compiler defects and generated drift separately. Review the whole consequence set,
including documentation, evals and unchanged consumers.

## Scaffold and content authoring

1. Choose a kebab-case plugin and distinct role/skill/workflow names.
2. Create plugin.toml with schema daodan/v1, version 1.0.0, identity, closed
   capability requirements, hard dependency declarations and components.
3. Write meaningful behavior under the corresponding source directories. A
   workflow needs an entry body and sidecar with phases, contract and deliverables.
4. Add only needed contracts/policies. Runtime helper files live under a skill.
5. Validate declared components and dependencies, then compile every host.
6. Review the resulting source and package behavior before publishing.

Do not put host tool primitives in neutral behavior. Each adapter supplies its
binding and coordination strategy. Declared roles/schemas must actually resolve.
Do not preserve unused or optional local dependencies to make a compiler pass.

## Version, sync and publication

Bump each changed kernel version and the marketplace version according to the
target's rules. Rebuild all hosts and stage source plus generated results together,
using explicit paths. A rebuild alone is not a plugin source change.

Follow the target's upstream/licensing workflow before import or synchronization.
Verify gates before an authorized push. Read-only review, source changes, commits
and publication are separate scopes; preserve already granted human authorization.

