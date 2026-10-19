---
name: project-protocol
description: >
  Shared working discipline, canonical run identity, snapshot bindings, delivery
  and verification accounting,
  authorization continuity and safe phase recovery for coordinated project work.
  Load before briefing workers, recording, resuming or closing a project intervention.
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# Project protocol

## Ownership

A workflow may declare `[dispatch]` independently of its phase graph: `roles`
lists exact local or `provider/role` identities, `isolated` requires a separate
context, and boolean `inline_workers` binds only this plugin's canonical
`isolated-worker`. That binding requires a hard provider dependency and isolation.
It accepts a concrete task and report contract without exposing other registry
roles. Loaded methods retain their domain prompts; metadata carries no prompt.

This leaf owns operational records and their validation. Canonical contracts are
`${CLAUDE_PLUGIN_ROOT}/contracts/work.toml` and
`${CLAUDE_PLUGIN_ROOT}/contracts/project-result.toml`. Consumers declare those
exports by provider/path in `contract.shared_schemas`; they never copy them.
Review findings, severity and native dispositions remain the domain owner's
payload. A common result references the original report, its hash, its author,
its input snapshot and the adapter that interpreted it.

Keep operational state under a dedicated root inside the project, default
`.daodan/runs/<id>/`. The root sentinel is `.daodan-root`. A coordinator owns
`work.json` and `result.json`; each dispatched worker owns one declared report.
Never place run state, temporary paths or task progress in durable instructions.

## Working discipline

The coordinator and every worker apply these rules to their assigned task.

Working assumptions: State material assumptions and unresolved alternatives before dependent work. Ask only for an essential decision that existing instructions or authorization cannot resolve; continue independent authorized work.

Working simplicity: Choose the simplest design that satisfies approved requirements. Reuse existing owners and conventions; add no speculative features, abstractions or configuration. Prefer suitable existing code, standard-library facilities and maintained libraries over reimplementing solved problems. Before recommending or adopting a dependency, verify maintenance and support status, fit, compatibility, license, security and total integration cost using current official sources. Disclose unverified status; do not recommend discontinued or unverified libraries by default. Justify custom code when reuse is unsuitable or more complex.

Working scope: Limit edits to the task and owned files, match existing style and preserve unrelated work. Remove code made unused by your changes; remove preexisting code only when its removal is explicitly authorized and any required checks or approvals are satisfied.

Working verification: Define observable success criteria from approved requirements. Run meaningful checks on the actual candidate and preserve independent protection. Report unavailable checks; missing required checks or deliveries keep the task open. Finish when the criteria are met.

Working redesign: Fix the cause, never the symptom. When a defect shows that a script, skill, contract or workflow is shaped wrong for its problem, redesign that unit from the ground up so it solves the whole problem, instead of patching the case at hand. A patch that leaves the design wrong is debt, not a fix; record the redesign decision and its reason.

Existing task authorization covers removal necessary to the approved change;
preserve owner-required acceptance and test-retirement rules. This discipline
grants no additional mutation or runtime authority. For a read-only worker,
success concerns the assigned evidence and report within its permitted method.

## Isolated worker briefs

Before dispatch, include the task objective, approved requirement source,
applicable instruction rules and observable delivery criteria in the worker
brief, alongside its input snapshot, owned files, authorizations, budget and
expected report path. Carry these four rules into each isolated worker prompt
rather than relying on inherited coordinator context. A role body alone is not
the full task.

For independent discovery, omit peer findings and unverified coordinator
conclusions. Verification or criticism may receive findings explicitly assigned
by the domain method as declared inputs. Keep those purposes and their delivery
criteria distinct.

## Run-state interface

Use `python "${CLAUDE_PLUGIN_ROOT}/skills/project-protocol/scripts/run_state.py"`:

```text
init --project ROOT --payload INPUT.json [--out INTERNAL_ROOT] [--run-id ID]
show --project ROOT --run-id ID [--out INTERNAL_ROOT]
update --project ROOT --run-id ID --expected-revision N --payload PATCH.json
validate --project ROOT --run-id ID [--out INTERNAL_ROOT] [--current] [--result RUN_RESULT.json]
resume --project ROOT --run-id ID --payload CONTEXT.json [--out INTERNAL_ROOT]
snapshot --project ROOT --payload CONTEXT.json [--out INTERNAL_ROOT]
```

Pass `--out` consistently once a custom root is selected. Init requires
`operation`, `objective`, `scope` (`paths`, optional `focus` and `excluded`),
`authorizations` and `budget`; phases, plan, deliveries and gates default to
empty. Declare every expected worker in `deliveries` before dispatch and every
known mandatory check in `required_gates` before execution; gate identifiers
are append-only. Init, show and update emit the full record.

Update merges objects and replaces arrays, refuses a revision mismatch, and
captures the current `candidate` binding. Identity, original scope,
authorizations, the baseline binding and a completed run are immutable.

A gate carries its status, the candidate snapshot digest and `head`, and
evidence naming the command or the remote job with its exact revision and
attempt. Snapshots hash scoped inputs byte for byte, dirty and untracked files
included, never the run's output root, and record file kind and executable
state where the filesystem supports it. A remote check counts only when the
candidate has a Git revision and `head_matches_snapshot` is true: a job for HEAD
cannot verify uncommitted edits, ignored inputs or transformed line endings, so
run the check locally or record it as unavailable. `snapshot` returns a fresh
candidate binding after source changes.

Validate checks a historical record; `--current` rejects changed scoped inputs
or workspace identity before a result counts for the present project;
`--result` checks the canonical envelope against this revision, snapshot,
ledger and gate statuses. Resume requires current `authorizations` and an equal
scope, verifies project, worktree, HEAD and candidate snapshot, returns the
record with pending phases and deliveries, and changes nothing. New input or a
broader authorization is a new run. Record an interruption's reason and phase
as soon as possible.

## Loop sections

A lifecycle run may carry six optional sections, declared under `[loop]` in
the work contract and validated whenever present.

| Section | Holds | The helper refuses |
|---|---|---|
| `workspace` | mode `WORKTREE`, `BRANCH` or `IN_PLACE`, branch, `base_sha`, environment bindings | a binding that carries a secret value |
| `preflight` | test baseline `GREEN`, `KNOWN_RED` with its fingerprint, or `UNKNOWN_RED`; migration state | an unknown state |
| `adr` | active record identities and the proposed one | a malformed id |
| `waves` | tasks with `write_set`, `oracle` (command plus the failure it must produce first), `verification`, optional `resource_locks`, `produces`, `consumes` | more than four files without a reasoned `granularity_exception` (six at most); two tasks of one wave sharing a file, a lock or a produced-consumed contract; a parallel wave outside `WORKTREE`; a `sealed` wave with an uncommitted task |
| `rulings` | the worker's recorded local decisions | an update that alters or drops one |
| `review` | the roster computed by `review_roster.py compute --shape light\|branch --diff DIFF --out ROSTER.json`: tier, roles, verification depth, blind derivation, critic | a delivery whose `role` is outside the roster |

Check a draft plan before it enters a run with `plan-check --project ROOT
--payload PLAN.json`; the refusal names the rule, so the planner corrects the
plan rather than the record. Record the review roster before dispatching
reviewers; `review_roster.py check` refuses a dispatch plan before it runs.
`--deeper` raises the tier one step and nothing lowers it. Thresholds live at
the top of the helper and change only with a recorded probe.

## State and completion

Read the values and allowed transitions from the canonical work contract. Run
states are `in_progress`, `complete`; phase states are `pending`, `in_progress`,
`complete`, `skipped`; worker deliveries are `pending`, `running`, `delivered`,
`failed`. A failed worker may be retried with the failure retained in its attempt
history. Record why a phase is skipped. Complete means every declared phase is
closed, every expected delivery is delivered, no interruption remains and every
required gate passed for the current candidate with evidence. Failed or unavailable
checks remain explicit; a partial report does not authorize marking the run complete.
Every delivered worker requires an `output` naming an existing report inside
its owned run, including workers with no findings. Coordinator records and locks
do not count as worker reports.

Worker status and test outcome are different facts. A worker that honestly reports
a product defect can deliver successfully. Accounting for a worker failure does
not turn it into a successful delivery. Report the uncovered dimension.

## Baseline, gate and recovery

Before a mutating phase, verify exclusive ownership of the working tree, including
its other active sessions. Bulk removal requires an isolated owned worktree; a clean
status alone is insufficient. Record the authorized paths, starting HEAD, full scoped
snapshot, preexisting tracked edits and untracked files. Resolve build and test gates
from the project's instructions. If the baseline is failing, unavailable or forbidden
locally without a correlated remote alternative, leave the phase open.

Record `pre_phase_sha` immediately before each phase. Save enough pre-phase file
state to recover precisely that phase's owned edits. Apply, capture candidate,
execute the declared gates, then commit only when authorized. Record the commit and
the candidate it verifies. Do not derive a rollback target from `HEAD~1`.

On failure before commit, restore only the phase's owned edits to their captured
pre-phase values. Preserve the preceding successful phase and all preexisting or
foreign files. A reset to `pre_phase_sha` is allowed only in an exclusively owned,
isolated worktree with a proven clean pre-phase baseline and no foreign changes;
otherwise use path-scoped restoration or leave recovery to the user with the exact
conflict. Never run `git clean`, broad checkout or hard reset in a shared checkout.
An already published phase is undone by an authorized revert, never history rewrite.

The run-state helper records and validates the procedure; it does not execute Git
rollback, dispatch workers, enforce their token limits or confine their other tools.
Its own writes are confined mechanically. Tool confinement elsewhere is an explicit
prompt obligation until an adapter has a measured runtime mechanism.

## Compiler dispatch resources

Cross-plugin role bindings resolve against the kernel registry and mandatory
dependencies. Named-agent hosts receive the owner-qualified native identity. Inline
adapters receive only the external bodies actually declared in the phase graph,
under generated `contracts/dispatch/<owner>/<role>.md`. Each resource identifies its
canonical owner, version and source hash; these are unregistered compiler output,
not hand-authored copies or new roles. Host drift checks cover canonical edits.
Resolve any owner-relative helper from that owner's installed skill, rather than
mistaking the coordinator's root for the role's root.
