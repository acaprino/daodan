---
name: instructions-method
description: >
  Create, audit and maintain durable project instructions in AGENTS.md, CLAUDE.md or the target host's established instruction file. Provides an explicit audit-only method.
---

# Durable instructions method

Load `project-protocol:project-protocol` for run records and gates.
Receive project root, worktree/snapshot, scope, requested instruction destinations,
mode, existing files, evidence paths and authorizations. Reuse the caller's run.

## Destination and authority

Use explicit user destinations first, then the project's existing authoritative
instruction file and documented synchronization rule. For a new project, use the
active host's instruction mechanism (AGENTS.md for Codex, CLAUDE.md for Claude,
or the host's configured rules). If the binding is unknown, present concrete
destinations before writing; do not invent a universal filename. Multiple hosts
may use generated or thin-pointer copies only under an explicit project rule.
Never maintain two independent contradictory instruction sets. Honor nested
scopes and do not rewrite a generated instruction copy directly.

## Preparation

Read manifests, source structure, entry points, configured commands and CI before
checking claims. Map evergreen categories and ownership rather than every file.
Read approved requirements/decisions separately from implementation. A supplied
X-ray is consumed through `codebase-xray:xray-method`, bound to its exact run and
snapshot, preserving unknown/disputed claims and inherited premise provenance.

## Audit and create

Dispatch `instructions-auditor` with explicit audit-only or create mode and the
inputs above. Audit-only returns findings to the owned run, without editing any
durable file. Use its claim/reference/duplication checks; do not add another
detector prompt to the caller. Creation uses a planned destination and verified
facts, not invented project policy.

Read `references/working-principles.md` when a new project needs working guidance
and `references/test-suite-rules.md` when tests exist or are planned. Existing
equivalent rules remain valid; missing canonical wording alone is not a defect.
`references/instruction-example.md` illustrates structure, not current package
versions or requirements for the target project.

## Apply and verify

Audit is the default. With authorized fix/commit, reuse the same claim report and
read `${CLAUDE_PLUGIN_ROOT}/skills/project-knowledge/references/apply-method.md`.
Preserve unverified claims without inventing
support; distinguish them from disproved claims. Resolve uncertain intent before
changing an obligation. Extract repeated detail to existing docs with a working
pointer when authorized; keep the primary entry point coherent. Recheck paths,
commands, instruction scope and generated-copy parity before recording completion.
Run status, task lists, temporary paths and one-run results stay in the operational
record, never in durable instructions.
