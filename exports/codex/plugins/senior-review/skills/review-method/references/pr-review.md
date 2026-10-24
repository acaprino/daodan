<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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

## Phase 2: Risk and Architecture Assessment

Dispatch the validated jobs under preparation's
`references/composition.md`. The roster supplies required coverage, not additional
workers. Each job preserves canonical member methods and reports per-member
outcomes in the same delivery ledger.

Use isolated contexts through the host harness. The PR variant changes the final presentation,
not the required reviewer
set. Resolve every identity through the compiled catalog and its canonical role
or method binding, including accessibility, performance, operability and applicable
stack specialists. Do not substitute a fixed pair of code/security reviewers.

Read the Shared Instructions for All Agents section of `references/code-review.md`
inside this skill. Apply its intent, scope, hypothesis and premise-provenance rules
using this PR's exact candidate and comparison. Unknown intent stays unknown.
Load `senior-review:review-quality-gates` and its
`references/code-review-agents.md` for concise worker handoffs and input adaptations.
Follow preparation's `references/stack-dimensions.md` for stack/method bindings.
Keep native role methods and outputs; do not paste a second security, architecture,
performance or hygiene checklist into a generalist prompt.

Record expected jobs, member identities, report paths and snapshot bindings before dispatch.
Preserve the blind premise input boundary and its existing discovery delivery;
verification lenses receive only their assigned claims in fresh contexts. Each
worker returns findings or an explicit no-findings result, coverage and gaps.
The delivery barrier accounts for every expected job and member as delivered or failed.
A missing specialist result cannot be described as clean or silently omitted.

The coordinator consolidates those deliveries through the existing verification
gates before producing the PR risk assessment and description. Classify change
type, affected contracts, breaking behavior and residual risks using verified
findings and recorded evidence. Size and file counts describe the candidate;
they do not independently establish defect severity, a risk score or a need to
split the PR. Keep source cleanup, workspace hygiene and dependency results with
their actual owners, recording unassessed dimensions explicitly.

This method reviews and describes the PR. Any application edit, commit, publication
or comment follows the enclosing run's existing authorization rules.
