---
name: work-record
description: >
  Shared working discipline, run identity, snapshots, delivery/verification
  accounting, authorization continuity, user questions and phase recovery.
  Load before authoring components/tools, briefing workers, asking users,
  recording, resuming or closing project interventions.
---

# Work record

## Ownership

Own operational records and validation. The contract,
`${CLAUDE_PLUGIN_ROOT}/contracts/work.toml`, belongs in consumers'
`contract.shared_schemas`, never copied. Workflow `[dispatch]` lists method workers;
`inline_workers` binds this plugin's `isolated-worker` to a task/report contract. Only grants authorize work. Domain owners
keep findings, severity and dispositions; results reference original reports,
hashes, authors, input snapshots and interpreting adapters.

Read `references/process-runtime.md` before graph composition/execution/resume
or console/MCP use. The complete runtime is bundled:
`${CLAUDE_PLUGIN_ROOT}/skills/work-record/scripts/controller.py`; no separate
repository/process-controller installation required.

State: main checkout's `.daodan/` (project root outside Git). Records survive
worktree removal; sessions share one agenda. Coordinator owns run `work.json`,
`result.json`, scratch; workers own one declared report each.

## Working discipline

Coordinator and workers apply these rules to assigned tasks.

Working assumptions: State material assumptions and unresolved alternatives before dependent work. Ask only for an essential decision that existing instructions or authorization cannot resolve; continue independent authorized work.

Working simplicity: Choose the simplest design that satisfies approved requirements and existing contracts. Prefer, in order, suitable project code and conventions, platform or standard-library facilities, dependencies already available, then the least new code. Explain an exception when an earlier option cannot meet the requirement or is more complex overall. Reuse existing owners; add no speculative features, abstractions or configuration. Preserve boundary validation, data-loss prevention, security and accessibility. Before recommending or adopting a dependency, verify maintenance and support status, fit, compatibility, license, security and total integration cost using current official sources. Disclose unverified status; do not recommend discontinued or unverified libraries by default.

Working scope: Limit edits to the task and owned files, match existing style and preserve unrelated work. Remove code made unused by your changes; remove preexisting code only when its removal is explicitly authorized and any required checks or approvals are satisfied.

Working verification: Define observable success criteria from approved requirements. Run meaningful checks on the actual candidate and preserve independent protection. Report unavailable checks; missing required checks or deliveries keep the task open. Finish when the criteria are met.

Working redesign: Fix the cause, never the symptom. When a defect shows that a script, skill, contract or workflow is shaped wrong for its problem, redesign that unit from the ground up so it solves the whole problem, instead of patching the case at hand. A patch that leaves the design wrong is debt, not a fix; record the redesign decision and its reason.

Existing task authorization covers removal necessary to the approved change; preserve owner-required acceptance
and test-retirement rules. This discipline grants no additional mutation/runtime
authority. Read-only success concerns assigned evidence/report within the permitted method.

## Authoring components

Before creating or updating skills, agents, roles, workflows, prompts, tools,
templates or specialist guidance, read and apply `references/component-authoring.md`.

## Isolated worker briefs

Before dispatch, brief workers with objective, approved requirement source,
applicable instructions, observable delivery criteria, input snapshot, owned files,
authorizations, budget and report path. Include working discipline in every prompt;
inherited context and role bodies alone do not define tasks.

Independent discovery excludes peer findings and unverified coordinator conclusions.
Verification/criticism may receive findings the domain method explicitly declares
as inputs. Keep purposes and delivery criteria distinct.

## Run-state interface

Use `python "${CLAUDE_PLUGIN_ROOT}/skills/work-record/scripts/run_state.py"`.
Append `--project ROOT` throughout; append `--run-id ID` except to init,
agenda and first-use. Writes also require this session's `--session ID`.

```text
init --payload INPUT.json [--run-id ID]
update --expected-revision N --payload PATCH.json
ask --payload QUESTION.json
answer --payload ANSWER.json
resume --payload CONTEXT.json
show [--historical]
snapshot
validate [--current] [--result RESULT.json]
agenda [--branch NAME]
first-use
bind-process --expected-revision N --payload BINDING.json
```

Init requires `operation`, `objective`, `scope` (`paths`, optional `focus`,
`excluded`), `authorizations`, `budget`. Declare expected `deliveries` workers
before dispatch and known mandatory `required_gates`. Updates merge objects, replace arrays and reject
stale revisions without changes; check draft plans by writing them. Identity,
scope, `authorizations`, baseline and completed runs never change. Required gates, rulings, reviews and `grants` are append-only: later
authorization is a grant with kind, scope and user answer as `source`
(`kind: user`, `reference`). Questions change only through `ask`/`answer`;
read `references/questions.md` before asking.

Only holders write tasks; `--take-over` requires confirmation the other session
closed. `resume` checks authorizations, scope and candidate, records the holder
and returns pending work/replans. One open loop task per branch. New input/scope
requires a new run; record interruptions immediately. `show --historical` reads,
never resumes, old records.

Gates carry status, snapshot `digest`/`head` and command evidence or remote
job/revision/attempt. Snapshots hash scoped inputs byte-for-byte, including dirty
and untracked files. Remote checks require `head_matches_snapshot: true`: HEAD jobs cannot verify
uncommitted, ignored or transformed inputs; check locally or record unavailable.
`validate --current` rejects changed inputs/workspace; `--result` checks the
envelope against this revision, snapshot, ledger and gates.

New process-backed consumers init `process_required: true`. Before dispatch,
admit YAML; `bind-process` its immutable identity/native delivery mapping.
The bridge matches report bytes to admitted artifacts. Process success supplements
domain gates, granting no execution/commit authority. Legacy JSON stays readable/
resumable without invented graphs/rewritten history. Binding/recovery:
`references/process-runtime.md`.

## Loop sections

Lifecycle runs may carry `workspace`, `preflight`, `adr`, `waves`, `rulings`,
`reviews`, `questions`, `environment`, `integration`, validated when present.
Answer-dependent tasks consume `question:<id>` and wait. Before dispatch append
the roster as senior-review's `review_roster.py compute` wrote it; `--deeper`
appends one tier higher; nothing lowers it. Running tasks need a delivered adversarial
PASS plan review on the exact plan digest and current bytes. Commits bind parent,
owned diff and wave trailer; completion binds sealed waves, branch review,
reviewed ancestry, merge and realignment. Resume reconciles commit-record crashes.

## State and completion

Runs are `in_progress` or `complete`; phases `pending`, `in_progress`,
`complete` or `skipped` (with a reason); deliveries `pending`, `running`,
`delivered` or `failed`; retries retain failed attempts. Completion requires
closed phases, all deliveries delivered, no interruption/open
question and every required gate passed on the current candidate. Keep failed/
unavailable checks explicit; partial reports authorize nothing. Delivered workers
name existing run-owned `output`, even without findings. Honest product-defect
reports count as delivery; worker failures never do. Report uncovered dimensions.

## Baseline, gate and recovery

Before mutation, verify exclusive working-tree ownership, including active
sessions. Bulk removal needs an isolated owned worktree; clean status is insufficient.
Record authorized paths, starting HEAD, scoped snapshot, preexisting edits/untracked
files. Resolve build/test gates from project instructions. Failed/unavailable/forbidden
baselines without correlated remote alternatives leave phases open.

Before a phase, record `pre_phase_sha` and recovery bytes. Snapshot the applied
candidate; run gates and review before commit. Committed tasks need `candidate`,
passing `verification_receipt`, PASS `pre_commit_review`, `commit_sha` and light
changeset review binding. The helper rejects stale bindings and checks HEAD/bytes.
Commit when authorized. On failure, restore owned edits;
preserve preceding phases and foreign files; never derive a rollback target
from `HEAD~1`. Reset to `pre_phase_sha` only in an exclusively owned worktree
with a proven clean baseline and no foreign change; otherwise restore by path
or hand the exact conflict to the user. Never run `git clean`, a broad checkout
or a hard reset in a shared checkout. A published phase is undone by an
authorized revert, never by rewriting history.

The helper mechanically confines its own writes; it neither rolls back, dispatches
workers nor confines their tools. Those remain prompt obligations until an adapter
proves a mechanism.

## Compiler dispatch resources

Named-agent hosts dispatch the owner-qualified identity; inline adapters read
another plugin's role from a generated `contracts/dispatch/<owner>/<role>.md`
naming its owner, version and source hash. Resolve an owner-relative helper
from that owner's installed skill, not the coordinator's root.
