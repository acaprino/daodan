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

## Step 3: Run Parallel Review Agents

Use the host coordination mechanism to dispatch the validated jobs in isolated contexts.

### Shared Instructions for All Agents

Include these instructions in every agent prompt:

```
## Intent
[paste the 2-3 line intent summary from Step 1b]

## Diff Scope & Pre-existing Classification

For changeset basis, classify findings under the base policy into three tiers:

- **Primary** -- lines added or modified in the diff. Your main focus. Full confidence.
- **Secondary** -- unchanged code in the same function/block as a changed line. Report
  if the diff makes the issue newly relevant, noting the interaction.
- **Pre-existing** -- issues in unchanged code unrelated to the diff. Mark these with
  `[PRE-EXISTING]` prefix. They are reported separately and do NOT count toward the verdict.

Rule: if you'd flag the same issue on an identical diff without the surrounding file,
it's pre-existing. If the diff makes it newly relevant, it's secondary.
An unchanged evidence line alone does not make an exposed defect ineligible.
For content basis, admit evidenced defects in the named scope, including
preexisting ones, under the requested snapshot's policy. For claims basis, judge
the document's assertions under its method; do not reinterpret it as a source audit.

## Premise declaration (required on every finding)

Every finding carries two extra fields:

- **Load-bearing premise:** the single proposition whose falsity collapses this
  finding. It must be minimal, falsifiable and scoped.
    Bad:  "The implementation is broken."
    Bad:  "Heartbeat handling is incorrect."   (a paraphrase of your finding)
    Good: "No credential-bearing response path exists after registration."
- **premise_provenance:** one of `independent`, `shared-context`, `mixed`.
  This records CAUSAL DEPENDENCE, not citation. If you absorbed the premise from
  the Codebase Map output or the interconnect map, it is `shared-context`, even if
  your finding never cites an anchor. `mixed` means part of the premise rests on
  shared context and part on evidence you derived yourself. Declare `independent`
  only when you re-derived the whole premise from code, tests or documents you
  read yourself.

## Hypothesis fields (required on every finding)

A finding is a hypothesis the verification panel will try to falsify. Give it:

- **Trigger:** the concrete input, state or timing under which the defect
  manifests. "Could fail" without a trigger is not a finding.
- **Counterevidence checked:** what you looked for that would have refuted the
  finding (guards, validations, callers, tests, configuration) and did not find.
- **introduced_by_candidate:** true only when the candidate change causes the
  defect. Apply the classification above only to changeset basis; this field does
  not exclude an eligible content or claims finding.
- **evidence_class:** `reproduced` (a test or run showed it), `tool-reported`
  (a tool in the evidence pack reported it), `measured` or `derived`.

The evidence pack is attached to this brief. Do not restate a tool line and do
not spend reading on what a tool already settled; report what tools cannot see.
```

Dispatch the validated jobs in isolated contexts using the host's supported
coordination mechanism. Preserve the roster's floor, support requirements and verification
level. The native variant supplies finding classification and report structure;
it does not add always-on workers or shrink the prepared set.

### Dispatch

Dispatch the validated jobs under preparation's
`references/composition.md`, once each. Keep the computed roster as required
coverage, not a second dispatch list. Preserve every member's canonical method,
scope and result in the same ledger. The role-oriented instructions below describe
each member's obligations within its assigned job.

Load `senior-review:review-quality-gates` and its
`references/code-review-agents.md` for the shared handoff and input adaptations.
Each selected member executes its canonical body. Resolve all identities through
the compiled catalog, including accessibility, general performance and operability;
API and migration reviews use their registered owners rather than duplicate
inline checklists. Stack and method bindings come from preparation's
`references/stack-dimensions.md`.

Record each expected job, its member identities, scope, snapshot and assigned intermediate output
before dispatch. Reuse Phase 1c's same-snapshot blind premise delivery when it is
the selected premise discovery result; later verification remains separate.
Preserve required isolation and omit peer findings from independent discovery.
A missing catalog binding, prerequisite or delivery remains a failed or incomplete
review, never an omitted dimension or a clean result. Account for every expected
job and member before consolidation. The coordinator alone writes the native final report.
