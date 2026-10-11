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

# Verify

Verification can inspect an exact lifecycle run or a candidate project snapshot.
Load project-protocol's snapshot and gate procedure. Define which behavior,
protection and consequences must hold before choosing the smallest relevant checks.

Record the baseline separately from the candidate. Include noncommitted changes in
the candidate fingerprint. Every check records command/tool, environment, status,
snapshot/revision, scope, output reference and its limitations. A remote green job
on the old branch HEAD does not validate uncommitted edits. If CI requires a push,
the publication and recovery sequence needs actual authorization; otherwise mark
that gate unavailable and preserve the candidate for review.

Use testing:test-preparation for runner/configuration and meaningful protection.
Passing self-generated assertions alone does not establish a correct oracle.
For suite changes, verify the accepted behavior inventory, independent failure modes,
resource isolation and replacement protection through the testing methods. Record
wrong-oracle evidence separately from product corrections and environmental failures.
Review affected contracts and failure paths through senior-review:review-method.
Pass the run's resolved scope, captured baseline and exact candidate bindings to
senior-review:review-preparation for the code-review variant, with this run's
output root. Include full scoped untracked-file content and any baseline evidence;
declare unavailable comparisons. Supply that same prepared bundle to review-method
so it cannot auto-select an unrelated Git diff or last commit, or prepare twice.
The same preparation selects applicable React, TypeScript and platform workers;
their required provider bindings are declared by this lifecycle entry. Present
the complete review selection and expected cost before dispatch. The assessment's
quick audit cap does not remove a required correctness dimension from a candidate
gate. Reuse only snapshot-bound deliveries and report failed or unavailable ones.
Use knowledge audit for consequences outside the diff, and abstraction audit for
changed concept ownership. Scope these operations to risk; do not launch all
auditors on an unrelated one-line change.

When instructions or their dependencies changed, use
project-knowledge:instructions-method to verify canonical/generated parity, applicable
scope, actual commands and prerequisites, and project-specific test policy. Distinguish
a file on disk from evidence that the intended host loaded it. Record required reloads,
new-session checks and enforcement limits. A required loading probe without evidence
stays unavailable; successful synchronization alone cannot satisfy it.

Static inventory/read coverage and runtime exercised paths are separate. Source
review cannot assert browser functionality. Missing credentials, unavailable
runners or unexecuted product paths are declared gaps, not successful checks.

Only the owner of a finding may apply its remediation; verify itself produces
evidence and a result. A failed gate points to the exact observed failure and next
action. Count expected deliveries and required checks before completing the run.
