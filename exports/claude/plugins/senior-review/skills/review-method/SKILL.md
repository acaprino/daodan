---
name: review-method
description: >
  Unified review engine: the light review and the branch review (variants team-review and pr-review, and code-review), including signal-selected stack specialists.
  TRIGGER WHEN: the user asks to review current changes, a commit, a file, a plan, a specification, a document, a branch or a pull request for defects, or /daodan:review-changes, /daodan:review-branch or a lifecycle review phase runs a review.
  DO NOT TRIGGER WHEN: establishing the root cause of a reported failure without reviewing an artifact (use investigation-method), or removing dead code (use application-cleanup-method).
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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
Preparation resolves absent `shape` (`light`/`branch`) and `target-kind`
(`changeset`/`plan`/`spec`/`doc`). Output: native report and project-result envelope.

**Shape `light`:** read only `references/light.md` in this method. Branch uses
`team-review`, or `pr-review` for a pull request, through these steps.

Do not delegate execution to another workflow or nested lifecycle scheduler.
For team-review Phase 1a, the coordinator executes `codebase-map:map-method`
analyze preflight, answerable checkpoints, delivery check and publication decision.
Its `codebase-map:map-analyst` executes requested phases in one isolated context
through the declared host harness. Loading a method executes no phase; the analyst
is a role, never a skill or declarative `invoke`.
Keep one review preparation and final report owner; required workers retain isolation.

The workflow sidecar declares `dispatch.roles` and isolated inline workers.
Inline lens, critic, history, hygiene and minimal-fix briefs use
`work-controller:isolated-worker` through that host binding, never an invented
generic role. Bind scope, authorization, budget, report path and delivered/failed
outcome for every brief.

1. Load `senior-review:review-preparation`, unless a prepared bundle exists.
   Validate target, run, snapshot, knowledge schema/candidate/fingerprints/scope,
   delivery IDs and applicable activation evidence or skip/gap reason. Reprepare
   stale or incomplete bindings against this candidate, without another run or
   duplicate dispatch.
2. Read `references/<variant>.md`. Dispatch validated `jobs` once each under
   preparation's `references/composition.md`, including stack members. The roster
   supplies coverage obligations, never another dispatch list. Core inputs remain
   canonical in `senior-review:review-quality-gates`; stack members use their
   provider definitions and shared preparation. Preserve `knowledge_selection`;
   assign scoped `knowledge_ids`, fingerprint and exact catalog load/reference
   bindings. Workers read assigned knowledge, apply it against source and return
   `knowledge_usage` with scope, worker, hashes, references and application evidence.
   Account for knowledge lenses in the same ledger.
   No worker receives peer findings before delivery.
   Use isolated contexts and the host's coordination mechanism.
   Account for every selected worker before starting consolidation.
   Each member retains canonical checks, coverage and finding references.
   Context, blind derivation and verification keep separate inputs and deliveries.
3. Load `senior-review:review-consolidation` with native results. Finish it before
   the variant's output/fix tail.
4. Code review then reads `references/code-review-delivery.md`; team/PR delivery
   stays in consolidation. Execute delivery and authorized fixes once. Application
   subtraction uses `senior-review:application-cleanup-method`; significant semantic
   refactors return to the caller's development plan, never cleanup.

Read-only review preserves application files and preexisting edits. The
coordinator alone may perform the project-bound Codebase Map preflight: move an
idle legacy archive intact and write only bound relocation metadata. It
authorizes no application changes, analysis run, worker migration or generic filesystem move.
Before accepted fixes load `work-controller:work-record` for preflight,
authorizations, baseline, candidate gate and owned recovery. Commit/publication
require separate authorization; review grants neither.
