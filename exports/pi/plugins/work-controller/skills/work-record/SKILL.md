---
name: work-record
description: >
  Shared working discipline, canonical run identity, snapshot bindings, delivery
  and verification accounting,
  authorization continuity and safe phase recovery for coordinated project work.
  Load before authoring agent components or tools, briefing workers, recording,
  resuming or closing a project intervention.
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

# Work record

## Ownership

A workflow's `[dispatch]` lists permitted method workers; `inline_workers` binds
this plugin's `isolated-worker` to a concrete task and report contract, exposing
no other role. Set method `--option` from the user's words or default; only a grant
authorizes work.

This leaf owns operational records and their validation. Canonical contracts are
`<plugin-root>/contracts/work.toml` and
`<plugin-root>/contracts/project-result.toml`. Consumers declare those
exports by provider/path in `contract.shared_schemas`; they never copy them.
Review findings, severity and native dispositions remain the domain owner's
payload. A common result references the original report, its hash, author,
input snapshot and interpreting adapter.

State lives under `.daodan/` in the main checkout (project root outside Git),
preserving worktree records after removal and one shared agenda. `.daodan-root`
is the sentinel. The coordinator owns `work.json`, `result.json` and scratch
files/payloads/plans under its run directory; each worker owns one declared
report. Never put scratch files beside project files or run state in durable
instructions.

## Working discipline

The coordinator and every worker apply these rules to their assigned task.

Working assumptions: State material assumptions and unresolved alternatives before dependent work. Ask only for an essential decision that existing instructions or authorization cannot resolve; continue independent authorized work.

Working simplicity: Choose the simplest design that satisfies approved requirements and existing contracts. Prefer, in order, suitable project code and conventions, platform or standard-library facilities, dependencies already available, then the least new code. Explain an exception when an earlier option cannot meet the requirement or is more complex overall. Reuse existing owners; add no speculative features, abstractions or configuration. Preserve boundary validation, data-loss prevention, security and accessibility. Before recommending or adopting a dependency, verify maintenance and support status, fit, compatibility, license, security and total integration cost using current official sources. Disclose unverified status; do not recommend discontinued or unverified libraries by default.

Working scope: Limit edits to the task and owned files, match existing style and preserve unrelated work. Remove code made unused by your changes; remove preexisting code only when its removal is explicitly authorized and any required checks or approvals are satisfied.

Working verification: Define observable success criteria from approved requirements. Run meaningful checks on the actual candidate and preserve independent protection. Report unavailable checks; missing required checks or deliveries keep the task open. Finish when the criteria are met.

Working redesign: Fix the cause, never the symptom. When a defect shows that a script, skill, contract or workflow is shaped wrong for its problem, redesign that unit from the ground up so it solves the whole problem, instead of patching the case at hand. A patch that leaves the design wrong is debt, not a fix; record the redesign decision and its reason.

Existing task authorization covers removal necessary to the approved change;
preserve owner-required acceptance and test-retirement rules. This discipline
grants no additional mutation or runtime authority. For a read-only worker,
success concerns the assigned evidence and report within its permitted method.

## Authoring components

Before creating or updating skills, agents, roles, workflows, prompts, tools,
templates or specialist guidance, read and apply `references/component-authoring.md`.

## Isolated worker briefs

Before dispatch, brief each worker with task objective, approved requirement
source, applicable instruction rules, observable delivery criteria, input
snapshot, owned files, authorizations, budget and expected report path. Include
the working discipline in each prompt; inherited context and a role body alone
do not define the task.

For independent discovery, omit peer findings and unverified coordinator
conclusions. Verification or criticism may receive findings explicitly assigned
by the domain method as declared inputs. Keep those purposes and their delivery
criteria distinct.

## Run-state interface

Use `python "<plugin-root>/skills/work-record/scripts/run_state.py"`:

```text
init --project ROOT --payload INPUT.json [--out INTERNAL_ROOT] [--run-id ID]
show --project ROOT --run-id ID [--out INTERNAL_ROOT]
update --project ROOT --run-id ID --expected-revision N --payload PATCH.json
validate --project ROOT --run-id ID [--out INTERNAL_ROOT] [--current] [--result RUN_RESULT.json]
resume --project ROOT --run-id ID --payload CONTEXT.json [--out INTERNAL_ROOT]
snapshot --project ROOT --payload CONTEXT.json [--out INTERNAL_ROOT]
agenda --project ROOT [--branch NAME] [--out INTERNAL_ROOT]
```

`agenda.json` beside `runs/` holds one row per task: operation, objective,
branch, phase, sealed waves, record, review tier, unanswered questions,
holder. `--session ID` on init, update and resume records the holder; a task
another session holds is refused until `--take-over`, once the user confirms
that session is closed. A branch holds one open loop task; a completed run
releases its row.

Keep a custom `--out` consistent. Init requires
`operation`, `objective`, `scope` (`paths`, optional `focus` and `excluded`),
`authorizations` and `budget`; phases, plan, deliveries and gates default to
empty. Declare every expected worker in `deliveries` before dispatch and every
known mandatory check in `required_gates` before execution; gate identifiers
are append-only. Init, show and update emit the full record.

Update merges objects and replaces arrays, refuses a revision mismatch, and
captures the current `candidate` binding. Identity, original scope,
authorizations, the baseline binding and a completed run are immutable. An
authorization asked later, at the step that needs it, is appended to `grants`
(kind `fix`, `commit`, `merge`, `push`, `purge`, `send`, `publish` or
`install`, its scope, the user's answer as `source`); grants are append-only.

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
or workspace identity; `--result` checks the envelope against this revision,
snapshot, ledger and gates. Resume needs current `authorizations` and an
equal scope, verifies project, worktree, HEAD and candidate, returns the
record with pending phases, deliveries and questions, and changes nothing.
New input or a broader scope is a new run. Record an interruption's reason and
phase at once.

## Loop sections

A lifecycle run may carry the optional sections of the work contract's
`[loop]`, each validated whenever present.

| Section | Holds | The helper refuses |
|---|---|---|
| `workspace` | mode `WORKTREE`, `BRANCH` or `IN_PLACE`, branch, `base_sha`, environment bindings | a binding that carries a secret value |
| `preflight` | test baseline `GREEN`, `KNOWN_RED` with its fingerprint, or `UNKNOWN_RED`; migration state | an unknown state |
| `adr` | active record identities and the proposed one | a malformed id |
| `waves` | tasks with `write_set`, `oracle` (command and the failure it must produce first), `verification`, optional `resource_locks`, `produces`, `consumes` | over four files without a reasoned `granularity_exception` (six at most); two tasks of a wave sharing a file, lock or contract; a parallel wave outside `WORKTREE`; a `sealed` wave with an uncommitted task |
| `rulings` | the worker's recorded local decisions | an update that alters or drops one |
| `questions` | questions the host could not ask: `id`, `phase`, `text`, later `answer` | an empty answer or a repeated id |
| `environment` | `interpreter`, `commands` (test, lint, types, build, migrations), confirmed `models.assignments` | unknown commands; malformed or unconfirmed bindings |
| `reviews` | one entry per review (record, plan, each wave, candidate) as senior-review's `review_roster.py compute` wrote it: id, stage, shape, kind, tier, roster, support, verification | a delivery naming a review whose roster and support lack its `role`; altering or dropping an entry |

Check a draft plan with `plan-check --project ROOT --payload PLAN.json`
before it enters a run; the refusal names the rule. Append a review's roster
before dispatch; `--deeper` appends one a tier up, nothing lowers one,
thresholds change only with a recorded probe.

## State and completion

The work contract defines states and transitions: runs `in_progress` or
`complete`; phases `pending`, `in_progress`, `complete`, `skipped` (record why);
deliveries `pending`, `running`, `delivered`, `failed` (retain failures in retry
history). Completion requires closed phases, all deliveries delivered, no
interruption and every required gate passed with current-candidate evidence.
Keep failed or unavailable checks explicit; partial reports authorize nothing.
Every delivered worker names an existing run-owned `output`, even without
findings; coordinator records and locks are not worker reports. A worker that
honestly reports a product defect delivered; accounting for a worker failure
does not turn it into a delivery. Report the uncovered dimension.

## Baseline, gate and recovery

Before a mutating phase, verify exclusive ownership of the working tree,
other active sessions included; bulk removal needs an isolated owned
worktree, never a clean status alone. Record the authorized paths, starting
HEAD, full scoped snapshot, preexisting edits and untracked files, and
resolve build and test gates from the project's instructions. A failing,
unavailable or locally forbidden baseline without a correlated remote
alternative leaves the phase open.

Record `pre_phase_sha` and enough pre-phase file state to recover that
phase's owned edits, immediately before the phase. Apply, capture the
candidate, run the declared gates, commit only when authorized, and record
the commit with the candidate it verifies. Never derive a rollback target
from `HEAD~1`. On failure before commit, restore only the phase's owned
edits to their captured values and keep the preceding phase and every
foreign file. A reset to `pre_phase_sha` is allowed only in an exclusively
owned isolated worktree with a proven clean baseline and no foreign change;
otherwise restore by path or hand the exact conflict to the user. Never run
`git clean`, a broad checkout or a hard reset in a shared checkout. A
published phase is undone by an authorized revert, never by rewriting
history.

The helper records and validates the procedure. It does not run Git
rollback, dispatch workers, enforce their token limits or confine their
other tools: its own writes are confined mechanically, and confinement
elsewhere is a prompt obligation until an adapter has a measured mechanism.

## Compiler dispatch resources

Named-agent hosts dispatch the owner-qualified identity; inline adapters read
another plugin's role from a generated `contracts/dispatch/<owner>/<role>.md`
naming its owner, version and source hash. Resolve an owner-relative helper
from that owner's installed skill, not the coordinator's root.
