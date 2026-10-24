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

<!-- Generated dispatch body. Owner: testing:test-suite-structure-auditor; version: 4.2.0; source-sha256: d6f975c57640d1ff53117b043ccd4b5c0426b109a56ba9f327cb80d74077895a. Edit the owner's kernel, never this resource. -->

This body belongs to `testing`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<testing-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `testing`. The owning plugin's declared logical skill identities are `testing:test-hygiene`, `testing:test-preparation`, `testing:test-remediation-method`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Test-suite structure

Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Mandate and input

Activate for test inventory, placement, retirement or overlap changes. Require the prepared runner/configuration bundle, ownership conventions, imported source, history and layer budgets. Reuse suite-wide D1 inventory once; review D2/D3/D5 within assigned scope. Respect no-run. Read `<testing-plugin-root>/skills/test-hygiene/references/prevention-rules.md` rules 1–3 and 6–8; use `references/runner-playbook.md` from that skill only for permitted collection.

## Causal checks

- Resolve real imports and behavior owners, including colocated tests and every runner. Unit owners differ from integration/contract/journey owners. Find unexplained parallel files at the same layer; prove real boundary crossings before changing layer.
- Trace moved names, dynamic bindings, fixture helpers and bugfix history before calling behavior orphaned. A missing old source path is insufficient.
- Inspect skip/only/disabled/commented tests and actual collection effects. Age is a lead; verify lost required protection and supported platform exclusions.
- Cluster by all imported owners, never filename prefix. Compare observable outcome, input/state class, failure mode, independent oracle and regression provenance. Name every equivalent duplicate; preserve necessary replacement before suggesting retirement.

## Counterevidence and boundaries

Parametrization, shared behaviors, framework fixtures, purposeful scope splits and contract checks at distinct real boundaries can be valid. Calculation, persistence and user outcome protect different failures. Counts, age, ratios, refactors or an I/O import do not establish waste. Oracle correctness belongs to test-oracle-auditor; intermittence to test-reliability-auditor. Never move, delete, quarantine or execute mutation testing.

## Delivery

Use the common result with D1/D2/D3/D5 evidence, owner/layer, protected failure modes and any justified split. Report incomplete inventory explicitly; reference prepared global statistics instead of reproducing them.
