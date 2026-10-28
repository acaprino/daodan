<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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

# Remediation Workflow

Mechanics for bonifying an already-degraded suite. The ladder is: measure, quarantine, consolidate, verify. Never "grand refactor of the suite": that loses the real coverage buried in the mess and blocks development for weeks. Remediation runs opportunistically, per module, alongside normal work.

## 1. Measure first: the TEST_AUDIT.md contract

The audit mode of `testing:test-remediation-method` maintains a `TEST_AUDIT.md` at the audited root. Format:

- Each run PREPENDS a `## Audit <ISO date>` section, newest first, so the file reads as its own history in addition to git's.
- The section carries a metrics table with a delta column against the previous audit section when one exists:

| Metric | Value | Delta |
|---|---|---|
| Test files | | |
| Test cases | | |
| Total runtime | | |
| Skipped/disabled | | |
| Failing | | |
| Flaky (rerun disagreement) | | |
| Orphan test files | | |
| Layer distribution (unit/integration/e2e) | | |
| Top-10 slowest (list) | | |
| Per-module coverage (when tooling exists) | | |

- Below the table: the audit findings summary from the test-suite-auditor (by severity, with file:line evidence) and the recommended remediation order.
- The file can be versioned in git as the native audit history. Commit only under
  explicit authorization; an audit request alone does not authorize a commit.

## 2. Canonical remediation

Load the `testing:test-remediation-method` skill for cause classification, quarantine,
behavior/failure-mode inventory, approval, replacement and snapshot-bound gates.
Its references contain the audit and consolidation procedures. This skill owns
placement/prevention rules and the native audit format, not a second fix loop.

## 5. Mutation testing (guidance only)

Mutation testing supplies additional evidence by mutating code and recording which tests detect changes. Equivalent, unreachable or invalid mutants require analysis; a surviving mutant alone cannot justify deletion. Configuration guidance, not a shipped runner:

| Stack | Tool |
|---|---|
| JS/TS | Stryker |
| Python | mutmut |
| JVM | PIT |
| Rust | cargo-mutants |
| .NET | Stryker.NET |

Choose a project-approved scope and cadence from measured cost, risk and CI budget;
fast changed-code runs can be commit gates while costly full-suite runs can be
scheduled. The audit consumes available reports without launching a new mutation
job. Feed valid, non-equivalent reachable survivors into investigation of missing
behavioral protection, not automatic pruning. Classify existing failures and
establish a comparable baseline before treating mutation results as gate evidence.
