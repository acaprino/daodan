<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# Verify (phase 6, and the standalone gate)

Load `references/specification.md`; recheck bound specification digest/approval
before candidate review. Legacy/pure repairs retain their intent.

Bind checks to the named candidate, including uncommitted content, through
protocol snapshots/gates; retain baseline. Carry post-task obligations per
`references/context-cycle.md`. Older remote checks cannot verify it; a
required push needs authorization or stays unavailable.

## Checks

1. Run declared test/lint/type/build commands on the candidate through
   `testing:test-preparation` runner/configuration diagnosis. Route packet
   `validation_obligations` to `testing:test-writer`, which confirms each oracle.
   Self-generated assertions alone establish no oracle; distinguish wrong oracle, product and
   environment failures.
2. Changed `EX-*` need candidate-passing, base-failing tests; retained requirements
   need candidate-passing regressions. Each specification/record `INV-*` needs
   a confirming test or review finding.
3. For command/setup/test-policy/architecture changes, use
   `project-knowledge:instructions-method` for canonical/generated parity.
   Actual host loading is a separate, possibly unavailable probe.

## Review of the candidate (stage D)

Run `senior-review:review-method` through `senior-review:review-preparation`,
shape `branch`, stage `candidate`, on `base_sha` through candidate head including
scoped untracked files. Pass scope/baseline/candidate and specification `EX-*`/`INV-*`. Preparation reads base policy,
builds evidence and computes the roster; the reachability lens receives reproduction
scratch only in a run-owned `WORKTREE` or `BRANCH`.

Retain jobs, member coverage and independent verification in the ledger. Select
no second roster/body. Light waves use this composition contract with distinct
preparation and one discovery job.

A confirmed `Critical`/`High` opens one remediation wave through
`references/waves.md`, reviewed as `light`, then stage D as a new review entry.
At most two waves; a third blocking result returns finding, attempts and options
to the user.

## Result

Owners remediate; verify supplies evidence/result. A failed gate
names observed failure and next action. Report inventory, in-depth reading and
runtime exercise separately. Account for every expected delivery and required
check before completion. Unavailable runners/credentials and unexercised product
paths are gaps, never passed checks.
