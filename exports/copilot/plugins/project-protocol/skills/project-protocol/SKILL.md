---
name: project-protocol
description: >
  Shared working discipline, canonical run identity, snapshot bindings, delivery
  and verification accounting,
  authorization continuity and safe phase recovery for coordinated project work.
  Load before briefing workers, recording, resuming or closing a project intervention.
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

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
`${PLUGIN_ROOT}/contracts/work.toml` and
`${PLUGIN_ROOT}/contracts/project-result.toml`. Consumers declare those
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

Use `python "${PLUGIN_ROOT}/skills/project-protocol/scripts/run_state.py"`:

```text
init --project ROOT --payload INPUT.json [--out INTERNAL_ROOT] [--run-id ID]
show --project ROOT --run-id ID [--out INTERNAL_ROOT]
update --project ROOT --run-id ID --expected-revision N --payload PATCH.json
validate --project ROOT --run-id ID [--out INTERNAL_ROOT] [--current] [--result RUN_RESULT.json]
resume --project ROOT --run-id ID --payload CONTEXT.json [--out INTERNAL_ROOT]
snapshot --project ROOT --payload CONTEXT.json [--out INTERNAL_ROOT]
```

Pass `--out` consistently after a custom root is selected. Init requires
`operation`, `objective`, `scope` (`paths` and optional `focus`/`excluded`),
`authorizations` and `budget`. It defaults phases, plan, deliveries and gates to
empty containers. Declare every expected worker in `deliveries` before dispatch
and every known mandatory check in `required_gates` before execution. Add newly
discovered checks before executing them; required gate identifiers are append-only.
Snapshot hashes
include dirty and untracked scoped inputs, never the run's own output root.

Update recursively merges objects and replaces arrays. Identity, original scope,
authorizations and baseline project binding are immutable. Completed runs are immutable.
A revision mismatch writes nothing. The helper captures the current `candidate`
binding on each update. `snapshot` returns a candidate project binding for a gate
after source changes. A gate carries `status`, the candidate snapshot digest,
candidate `head` when present, and evidence identifying the command or remote job.
Remote evidence also identifies the exact source revision and job attempt. A green
job for an earlier candidate is not the gate for this one.
Remote-only checks require a nonempty Git revision and `head_matches_snapshot`
true in the captured candidate. The helper compares scoped bytes with actual
HEAD blobs and detects untracked inputs, including ignored input files. Index
flags cannot hide a content change from that comparison. A job for
HEAD cannot verify uncommitted edits. Without this binding, run a check against
the actual local candidate or record the remote check as unavailable.
The comparison is byte-exact. A checkout with transformed line endings needs
local verification. Snapshots include regular-file kind and executable state
where the filesystem supports it; HEAD symlink blobs cannot attest a regular file.

Init, show and update emit the full JSON record. Validate emits validity and
identity. `validate --result` also checks the canonical envelope against this exact
work revision, candidate snapshot, delivery ledger and required check statuses.
Plain validation checks a historical record. Add `--current` before accepting a
result as verification of the present project; it rejects changed scoped inputs
or workspace identity.
Resume requires current `authorizations`; an optional supplied scope must
equal the recorded scope. It verifies project/worktree/HEAD and current candidate
snapshot, returns the record plus pending phases and deliveries, and changes no
file. New input or a broader authorization requires a new run, never rebinding a
completed report. Record interruption reason and phase immediately when possible.

## Loop sections

A lifecycle run may carry five optional sections, declared under `[loop]` in
the work contract and validated whenever present: `workspace` (mode
`WORKTREE`, `BRANCH` or `IN_PLACE`, branch, `base_sha`, environment bindings
that never hold a secret value), `preflight` (test baseline `GREEN`,
`KNOWN_RED` with its fingerprint, or `UNKNOWN_RED`; migration state), `adr`
(active record identities and the proposed one), `waves` and `rulings`.

A wave task names its `write_set`, `oracle` (command plus the failure it must
produce before the change), `verification` command, and optional
`resource_locks`, `produces` and `consumes`. The helper refuses more than four
files in a `write_set` without a reasoned `granularity_exception` (six at
most), two tasks of one wave that share a file, a lock or a produced-consumed
contract, a parallel wave outside a `WORKTREE` workspace, and a `sealed` wave
with an uncommitted task. Rulings are the worker's recorded local decisions;
an update that alters or drops one is refused. Check a draft plan before it
enters a run with `plan-check --project ROOT --payload PLAN.json`; the refusal
names the exact rule, so the planner corrects the plan rather than the record.

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
