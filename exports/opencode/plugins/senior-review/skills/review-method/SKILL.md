---
name: review-method
description: >
  Unified review engine for code-review, team-review and pr-review, including signal-selected stack specialists. Load when executing any senior-review workflow or lifecycle review phase.
---

<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Unified review method

Input: variant, target/flags, output root; optional same-snapshot `prepared` bundle.
Output: native report and the project-result envelope. Do not delegate execution
to a second workflow or a nested lifecycle scheduler. In team-review Phase 1a,
the coordinator executes the canonical `codebase-map:analyze` entry's preflight,
answerable checkpoints, delivery check and publication decision. Its
`codebase-map:map-analyst` runs the requested phases in one isolated context
through this workflow's declared host harness. Loading the method alone executes
no phase; use the analyst as a role, never as a skill or declarative `invoke`.
Keep one review preparation and final report owner; required workers still run
in isolated contexts through the declared host bindings.

The consuming workflow declares the named reviewer inventory in `dispatch.roles`
and isolated inline workers in its sidecar. Any inline lens, critic, history,
hygiene or minimal-fix brief in the references uses the canonical
`project-protocol:isolated-worker` binding supplied by the host harness. Use that
exact binding rather than a generic host role name. Keep scope, authorization,
budget, expected report path and delivered or failed outcome for every brief.

1. Load the `senior-review:review-preparation` skill, unless a same-snapshot prepared bundle
   was supplied. Validate its target, run identity and snapshot before reusing it.
   Complete missing stack selection through review-preparation before dispatch;
   Validate the prepared knowledge selection's schema, candidate/run/snapshot,
   content and metadata fingerprints, scope and assigned delivery IDs as well.
   A missing or stale knowledge binding requires preparation against this exact
   candidate before dispatch, not reuse of an older-schema or another-run bundle.
   a reused bundle needs activation evidence or a skip/gap reason for all three
   stack dimensions. Do not prepare another run or dispatch a reviewer twice.
2. Read `references/<variant>.md` in this skill. Dispatch the full prepared selection,
   including applicable React, TypeScript and platform reviewers, in the same batch.
   Core role inputs and prompts remain canonical in `senior-review:review-quality-gates`;
   stack roles use their canonical provider definitions and preparation's shared inputs.
   Preserve the prepared `knowledge_selection` and assign each worker only its scoped
   `knowledge_ids`, selection fingerprint and exact catalog load/reference bindings.
   Each worker loads its assigned knowledge as read-only input, applies it against
   code evidence, and returns `knowledge_usage` with scope, worker, hashes, references
   and application explanation. Account for task-specific knowledge lenses in this
   same dispatch and delivery ledger. No worker receives peer findings before delivery.
   Use isolated contexts and the host's supplied coordination mechanism. Account
   for every selected worker before starting consolidation.
3. Load the `senior-review:review-consolidation` skill with all native reviewer
   results. Do not run the reference's output/fix tail until consolidation finishes.
4. For code review, read `references/code-review-delivery.md` only after all core
   and stack results have passed native consolidation and verification. Team
   and PR report delivery remains in their consolidation references. Run delivery
   and any authorized fix steps once. Application subtraction loads
   `senior-review:application-cleanup-method`; significant semantic refactors are
   returned to the caller's development plan and are never delegated to cleanup.

Read-only review preserves application files and preexisting edits.
The coordinator alone may perform the project-bound Codebase Map preflight
before dispatch: move an idle legacy archive intact and write only bound
relocation metadata. This bounded exception authorizes no application changes,
analysis run, worker migration or generic filesystem move.
Before any accepted fix, load
`project-protocol:project-protocol` for execution preflight, authorizations,
baseline, candidate gate and owned recovery. Commit and publication are separate
authorizations; a request for review is not authorization to publish.
