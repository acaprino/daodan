---
name: work-record
description: >
  Shared working discipline, canonical run identity, snapshot bindings, delivery
  and verification accounting, authorization continuity, questions to the user
  and safe phase recovery for coordinated project work. Load before authoring
  agent components or tools, briefing workers, asking the user, recording,
  resuming or closing a project intervention.
---

# Work record

## Ownership

This leaf owns operational records and their validation. Its contract,
`${CLAUDE_PLUGIN_ROOT}/contracts/work.toml`, is declared by consumers in
`contract.shared_schemas` and never copied. A workflow's `[dispatch]` lists its
method workers; `inline_workers` binds this plugin's `isolated-worker` to a
concrete task and report contract. Only a grant authorizes work. Domain owners
keep findings, severity and dispositions; a result references the original
report, its hash, author, input snapshot and interpreting adapter.

State lives in `.daodan/` of the main checkout (the project root outside Git),
so worktree records survive removal and every session shares one agenda. The
coordinator owns `work.json`, `result.json` and its scratch files in the run
directory; each worker owns one declared report.

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

Use `python "${CLAUDE_PLUGIN_ROOT}/skills/work-record/scripts/run_state.py"`.
Every write names this session with `--session ID`:

```text
init --project ROOT --payload INPUT.json [--run-id ID]
update --project ROOT --run-id ID --expected-revision N --payload PATCH.json
ask --project ROOT --run-id ID --payload QUESTION.json
answer --project ROOT --run-id ID --payload ANSWER.json
resume --project ROOT --run-id ID --payload CONTEXT.json
show --project ROOT --run-id ID
snapshot --project ROOT --run-id ID
validate --project ROOT --run-id ID [--current] [--result RESULT.json]
agenda --project ROOT [--branch NAME]
first-use --project ROOT
```

Init requires `operation`, `objective`, `scope` (`paths`, optional `focus` and
`excluded`), `authorizations` and `budget`. Declare every expected worker in
`deliveries` before dispatch and every known mandatory check in
`required_gates`. Update merges objects, replaces arrays and refuses a stale
revision; a refused write changes nothing, so a draft plan is checked by
writing it. Identity, scope, `authorizations`, the baseline and a completed run
never change. Required gates, rulings, reviews and `grants` are append-only: an
authorization asked later is a grant with its kind, scope and the user's answer
as `source` (`kind: user`, `reference`). Questions change only through `ask`
and `answer`; read `references/questions.md` before asking.

A task is written only by the session that holds it; `--take-over` passes it to
this session after the user confirms the other one is closed. `resume` checks
the current authorizations, scope and candidate, records this session as the
holder, and returns the record with pending phases, deliveries and questions,
the tasks still `waiting` and those to `replan`. A branch holds one open loop
task; a completed run releases its agenda row. New input or a broader scope is
a new run; record an interruption's reason and phase at once.

A gate carries its status, the candidate `digest` and `head` that `snapshot`
prints, and evidence naming the command, or the remote job with its revision
and attempt. Snapshots hash scoped inputs byte for byte, dirty and untracked
files included. A remote check counts only when `head_matches_snapshot` is
true: a job for HEAD cannot verify uncommitted, ignored or transformed inputs,
so run the check locally or record it unavailable. `validate --current` rejects
changed inputs or workspace; `--result` checks the envelope against this
revision, snapshot, ledger and gates.

## Loop sections

A lifecycle run may carry `workspace`, `preflight`, `adr`, `waves`, `rulings`,
`reviews`, `questions` and `environment`; each is validated when present, and a
refusal names its rule. A wave task that needs an answer lists `question:<id>`
in `consumes` and waits for it. A review's roster is appended as senior-review's
`review_roster.py compute` wrote it, before dispatch; `--deeper` appends one a
tier up, and nothing lowers one.

## State and completion

Runs are `in_progress` or `complete`; phases `pending`, `in_progress`,
`complete` or `skipped` (with a reason); deliveries `pending`, `running`,
`delivered` or `failed`, a retry keeping its failed attempt. Completion requires
closed phases, every delivery delivered, no interruption, no open question and
every required gate passed on the current candidate. Keep failed or unavailable
checks explicit; partial reports authorize nothing. A delivered worker names an
existing run-owned `output`, even without findings. A worker that honestly
reports a product defect delivered; a worker failure never becomes a delivery.
Report the uncovered dimension.

## Baseline, gate and recovery

Before a mutating phase, verify exclusive ownership of the working tree, other
active sessions included; bulk removal needs an isolated owned worktree, never
a clean status alone. Record the authorized paths, starting HEAD, scoped
snapshot, preexisting edits and untracked files, and resolve build and test
gates from the project's instructions. A failing, unavailable or forbidden
baseline without a correlated remote alternative leaves the phase open.

Immediately before a phase, record `pre_phase_sha` and the file state needed to
recover its owned edits. Apply, capture the candidate, run the declared gates,
commit only when authorized, and record the commit with the candidate it
verifies. On failure before commit, restore only the phase's owned edits and
keep the preceding phase and every foreign file; never derive a rollback target
from `HEAD~1`. Reset to `pre_phase_sha` only in an exclusively owned worktree
with a proven clean baseline and no foreign change; otherwise restore by path
or hand the exact conflict to the user. Never run `git clean`, a broad checkout
or a hard reset in a shared checkout. A published phase is undone by an
authorized revert, never by rewriting history.

The helper confines its own writes mechanically. It does not roll back, dispatch
workers or confine their tools: that stays a prompt obligation until an adapter
proves a mechanism.

## Compiler dispatch resources

Named-agent hosts dispatch the owner-qualified identity; inline adapters read
another plugin's role from a generated `contracts/dispatch/<owner>/<role>.md`
naming its owner, version and source hash. Resolve an owner-relative helper
from that owner's installed skill, not the coordinator's root.
