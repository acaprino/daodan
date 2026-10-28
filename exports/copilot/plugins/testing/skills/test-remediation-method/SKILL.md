---
name: test-remediation-method
description: >
  Maintain existing test suites: diagnose failures, review and consolidate redundant tests, preserving behavior, independent failure modes and bugfix provenance. Load for suite audits, quarantine or rationalization through /daodan:maintain-tests (also composed by /daodan:tidy-repo).
---

<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# Test remediation

Input: `mode=audit|quarantine|consolidate`, prepared native audit/inventory, target,
output root, explicit accepted scope, authorizations and required gate configuration.
Output: native audit or remediation ledger plus project-result envelope. Audit is
report-only; quarantine/consolidation apply only explicitly accepted actions.

Load the `testing:test-hygiene` skill and `work-controller:work-record`. Reuse a prepared
bundle only for the same target and snapshot; otherwise load `testing:test-preparation`.
Before mutation check ownership, preserved starting edits, authorization, baseline,
required local/remote lanes and recovery point. Capture `pre_phase_sha` immediately
before each phase; hard reset requires an exclusively owned clean isolated worktree.
Read `references/audit.md` or `references/consolidate.md` in this skill; a quarantine
request uses the audit's accepted remediation section, not another detection pass.
For quarantine paths, exclusion configuration and the native ledger, read
`references/quarantine-layout.md` inside this skill. This is the sole layout owner.

## Cause classification before disposition

| Cause | Required evidence | Owner/action |
|---|---|---|
| product-defect | Independent contract/oracle disagrees with product behavior | Product implementation owner; keep the regression active and block affected closure |
| wrong-oracle | Authorized requirement or independent expected result disproves the assertion | `testing:test-writer` repairs the oracle, records why; never derive expected result from the tested implementation |
| environment | Dependency, service, credentials, runner or configuration explains failure | Environment/configuration owner; repair setup or explicitly defer affected verification |
| test-isolation | Reproduction identifies leaked state, colliding fixtures or unfinished test work | `testing:test-writer` repairs setup/teardown and proves isolation without losing product regression protection |
| intermittent | Rerun/CI disagreement under recorded comparable conditions | Observed symptom, not a root cause; distinguish product race, test isolation and environment before disposition |
| unknown | Evidence cannot yet distinguish product, oracle or environment | Preserve the test and mark the affected action open; investigate before quarantine |

Skip age, module rename, equal coverage and red CI are not sufficient diagnoses.
Propose quarantine only after classification and assessment of remaining behavioral
protection. Acceptance names exact files, cause, return condition and unresolved
risk; earlier authorization is reused if it already covers those items. An
unanswered inventory row stays. Failed tests are not made irrelevant by moving them.

An intermittent failure can expose a genuine product concurrency, cancellation or
resource-lifecycle defect. Reclassify an evidenced product race as product-defect
and keep its regression active. Repair test-state leaks or resource collisions as
test isolation defects using test-hygiene prevention rule 9. Temporary quarantine
requires evidenced remaining intermittence, owner, return condition, accepted risk
and preserved meaningful protection; adding retries is not causal diagnosis.

Protect distinct failure modes, boundary contracts and tests born from real bugs.
Current implementation is evidence, never its own oracle. Mutation reports are
supporting evidence; surviving mutants are not automatic proof of worthless tests.
Gate the candidate before its commit using same-snapshot evidence. Preserve native
findings, missing measurements and source provenance in the result envelope.
