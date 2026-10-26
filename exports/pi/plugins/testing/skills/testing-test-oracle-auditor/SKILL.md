---
name: testing-test-oracle-auditor
description: 'Review contradictory, implementation-coupled or vacuous assertions against independent product requirements. TRIGGER WHEN: reviewing contradictory, implementation-coupled or vacuous assertions against independent product requirements. DO NOT TRIGGER WHEN: implementing changes or applying remediation.'
disable-model-invocation: true
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.

# Test oracle integrity

Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Mandate and input

Activate for assertions, doubles, tolerance changes, contradictory results or mutation reports. Require approved behavior, tests, exercised production paths and relevant history. Read `<plugin-root>/skills/test-hygiene/references/prevention-rules.md` rules 4–8. Use supplied preparation; do not start remediation or mutation jobs.

## Causal checks

- D6: compare incompatible assertions for the same input/state with independent authority. Supported versions, migrations and boundaries may legitimately differ; implementation or majority agreement cannot decide the oracle.
- D7: trace internal mocks, call-echo checks, private access and internal snapshots to the observable contract they protect. Separate valid protocol-order diagnostics from mirrored implementation.
- D8: find missing assertions, tautologies, fully mocked production behavior, conditional assertions and empty loops. Follow assertion helpers before concluding none execute. A double of a library or framework object (logger, clock, HTTP client) that accepts any arguments hides argument-contract violations of the real object; require at least one test that constructs the real record or request and exercises the code after the call.
- Read existing mutation reports; establish mutant validity, reachability and non-equivalence before inferring missing protection. Inspect weakened/deleted assertions or widened tolerances against requirements and bugfix evidence.

## Counterevidence and boundaries

An internal hook or double can protect a real boundary; a mutation survivor can be equivalent or unreachable. Red tests may correctly expose product defects, while green ones can encode wrong behavior. Retirement requires retired behavior or verified replacement protection, never age, count or refactor alone. Structure and reliability own their distinct mechanisms.

## Delivery

Identify D6/D7/D8, independent oracle, exact production behavior exercised or bypassed, and the unprotected failure mode. Name product, oracle or unresolved owner. Preserve valid protection; recommend the smallest justified repair without applying it.
