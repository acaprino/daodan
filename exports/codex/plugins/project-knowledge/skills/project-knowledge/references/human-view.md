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
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

# Optional knowledge report view

The coordinator loads this reference when the user requests HTML or navigation
and table filtering materially help compare instruction claims, documentation
findings or proposed changes. Short answers need no view. Workers retain their
native deliveries; the coordinator renders only after consolidation and
verification required by the owning method.

## Native source

Use the final run-owned Markdown audit or change summary at its declared report
path. If that summary is not yet saved, write it once from the delivered native
findings and verified changes. Link supporting reports and documents instead of
copying their bodies. The source is the coordinator's report, rather than a
worker handoff, `work.json`, `result.json`, AGENTS.md, CLAUDE.md or another durable
document. Preserve their authoritative contents and paths.

For instruction creation, cite the delivered canonical instruction file and its
verification as evidence in the summary. Keep transient task state in the run.
Include the scope and snapshot, claim status and locators, source/approved-intent
distinctions, inherited premise provenance, duplication findings, proposed and
applied dispositions, retained facts, unavailable checks and uncovered surfaces.
Retain canonical/generated destinations, scoped loading evidence, copy-parity
results and unperformed reload, activation or enforcement checks. A rendered
view cannot settle unknown instruction loading or satisfy an unavailable gate.

## Render and account

Load the `report-rendering:report-renderer` skill and resolve its bundled helper from that
registered skill. Resolve the final Markdown and its same-stem HTML sibling to
exact paths in the dedicated owned run directory. Bind that exact directory as
`--root`; the repository root and shared artifact folders are not boundaries.
Use the `review` profile for findings and document changes:

```text
python "<resolved report-renderer helper>" --input "<owned run>/knowledge-report.md" --output "<owned run>/knowledge-report.html" --profile review --root "<owned run>"
```

Replace the sample filenames with the owner's declared final report path; use
the same dedicated run directory in all three paths. Reuse fixed presentation
without custom HTML, a repeated audit or copied instruction bodies. Keep the
native Markdown and durable files untouched. Task checkboxes and table filters
affect only the open view: they approve no proposal, apply no edit and complete
no workflow check. Rendering grants no new mutation or publication authority.

Verify helper success and the provider's structural checks, including the exact
source payload/hash and retained evidence/unknowns. No browser phase is required;
record interactions as unexercised when no authorized browser check ran. Do not
claim token savings without workflow measurements.

Record successful HTML delivery as a derived view in the owner's outputs and
link it beside the native report before work-controller validation and closure.
Preserve the owning method's delivery and verification gates. Diagnose rendering
failure through the provider and retain the native source. If an explicitly
requested HTML view remains missing or failed, keep that deliverable and the run
open; record the failure rather than claiming delivery. An unrequested optional
view failure leaves the native outcome intact and is reported as a limitation.
