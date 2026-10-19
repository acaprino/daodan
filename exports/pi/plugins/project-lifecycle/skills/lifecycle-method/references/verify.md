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

# Verify (phase 6, and the standalone gate)

Verification binds every check to an exact candidate: a lifecycle run's
candidate, or the working tree, branch or range the user names. Load the
protocol's snapshot and gate procedure. Record the baseline separately from
the candidate and include uncommitted changes in the candidate fingerprint.
A remote job on an older revision does not verify this candidate; a gate that
needs a push needs its own authorization, otherwise it stays unavailable.

## Checks

1. The project's declared test, lint, type and build commands on the
   candidate, through `testing:test-preparation` for runner and
   configuration. Passing self-generated assertions alone establish no
   oracle; record wrong-oracle evidence apart from product defects and
   environment failures.
2. Every `EX-*` of the run's proposed record has a passing test on the
   candidate and a failing one on the base; every `INV-*` is named by at
   least one test or one review finding that confirms it holds.
3. Instruction consequences through `project-knowledge:instructions-method`
   when commands, setup, test policy or architecture changed: canonical and
   generated parity, and whether the host loaded the result is a separate,
   possibly unavailable, probe.

## Review of the candidate (stage D)

Run `senior-review:review-method` through `senior-review:review-preparation`
with budget `full` on the whole candidate (`base_sha` to the candidate head,
untracked scoped files included), passing the run's scope, baseline and
candidate so preparation never guesses a diff. Preparation reads the policy
from the base commit, builds the evidence pack, selects every dimension the
candidate activates, and grants the reachability lens a reproduction scratch
path when the workspace is a `WORKTREE` or `BRANCH` owned by this run.

A confirmed `Critical` or `High` finding opens one remediation wave through
`references/waves.md`, reviewed again with budget `delta`, then the affected
dimensions of stage D again. At most two such waves; a third blocking result
returns to the user with the finding, the attempts and the options.

## Result

Only the owner of a finding applies its remediation; verify produces evidence
and a result. A failed gate names the observed failure and the next action.
Static inventory, in-depth reading and runtime exercise are reported as three
coverage facts. Account for every expected delivery and required check before
completing the run; an unavailable runner, missing credentials or an
unexercised product path are declared gaps, never passed checks.
