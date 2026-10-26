---
name: instructions-method
description: >
  Create, audit and maintain durable project instructions in AGENTS.md, CLAUDE.md or the target host's instruction file.
  TRIGGER WHEN: auditing, creating or updating AGENTS.md, CLAUDE.md or durable project instruction files.
---

# Durable instructions method

Load the skill `work-controller:work-record` for run records and gates.
Receive project root, worktree/snapshot, scope, requested instruction destinations,
mode, existing files, evidence paths and authorizations. Reuse the caller's run.

## Destination and authority

Read `references/instruction-loading.md` during preparation. Bind the actual
host/version, configured discovery and applicable root/nested scopes; a file's
presence does not prove it is loaded or enforceable. Record evidence and unknowns
in the owned run rather than assuming every host reads the same files.

Use explicit user destinations first, then the project's existing authoritative
instruction file and documented synchronization rule. For a new project, use the
mechanism confirmed for the active host/configuration (for example AGENTS.md for
Codex, CLAUDE.md for Claude, or configured rules). If the binding is unknown, present concrete
destinations before writing; do not invent a universal filename. Multiple hosts
may use generated or thin-pointer copies only under an explicit project rule.
Never maintain two independent contradictory instruction sets. Honor nested
scopes and do not rewrite a generated instruction copy directly.

## Preparation

Read manifests, source structure, entry points, configured commands and CI before
checking claims. Map evergreen categories and ownership rather than every file.
Read approved requirements/decisions separately from implementation. A supplied
Codebase Map is consumed through `codebase-map:map-method`, bound to its exact run and
snapshot, preserving unknown/disputed claims and inherited premise provenance.
For test guidance, derive the policy from this project's configured commands,
services, conventions and approved behavior. Check its completeness with
`references/test-suite-rules.md`; do not turn a template into project authority.

## Audit and create

Dispatch `instructions-auditor` with explicit audit-only or create mode and the
inputs above. Audit-only returns findings to the owned run, without editing any
durable file. Use its claim/reference/duplication checks; do not add another
detector prompt to the caller. Creation uses a planned destination and verified
facts, not invented project policy.

Read `references/working-principles.md` when a new project needs working guidance
and `references/test-suite-rules.md` when tests exist or are planned. Existing
equivalent rules remain valid; missing canonical wording alone is not a defect.
Read `references/output-economy.md` when creating or maintaining context/output
guidance or instructions for projects that author agent components or tools.
Keep the always-loaded rule short and preserve required reading,
independent verification and domain report contracts.
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
Apply the project's synchronization rule from its canonical owner. Distinguish
verified generated parity from instruction activation: use a supported reload or
new session when required, or record the unperformed loading check and its effect
on the active run. Never claim a textual obligation is mechanically enforced
without evidence of the actual guard in the relevant environment.
Run status, task lists, temporary paths and one-run results stay in the operational
record, never in durable instructions.

## Loop block

A project driven by the lifecycle loop carries one bounded block in its
authoritative instruction file, between `<!-- LOOP-HARNESS:BEGIN -->` and
`<!-- LOOP-HARNESS:END -->`. The block holds only what every task needs at
its start: the verified test, lint, type and build commands with their
prerequisites; on a project that keeps decision records, the active ones per
domain, by identity and title, supplied by the caller as resolved active decision inputs; the
workspace convention (worktree root, branch naming); the neutral specification
destination (`docs/specs/` unless explicitly configured otherwise); and routing:
design/brainstorm requests use Daodan's delivery method, which writes and obtains approval of
the specification before planning, reusing existing answers. This is an instruction,
not proof of automatic host activation. State that run records live under
`.daodan/runs/`. Reasons stay in the records,
procedures stay in the loaded methods, and run state never enters the block.

Create the block at project initialization when creation is authorized;
otherwise report it as a planned change. At the close of a task, regenerate
the block from the run record and, when the project keeps decision records, the
record index, and touch nothing outside
the markers. A missing marker pair in an existing file is a finding, not a
reason to append a second block. Generated copies follow the project's
synchronization rule as for any other instruction change.

## Coordinator delivery

For requested HTML or useful comparison/navigation, the coordinator reads
`${CLAUDE_PLUGIN_ROOT}/skills/project-knowledge/references/human-view.md` before
closing the run. Instructions-auditor deliveries stay native.
