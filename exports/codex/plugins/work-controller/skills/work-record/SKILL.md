---
name: work-record
description: >
  Shared working discipline, run identity, snapshots, delivery/verification
  accounting, authorization continuity, user questions and phase recovery.
  Load before authoring components/tools, briefing workers, asking users,
  recording, resuming or closing project interventions.
---

> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.
> This plugin declares an MCP server, `work-controller`, started with `uv run --no-config --no-project --script <plugin-root>/skills/work-record/scripts/controller.py mcp`. This host does not start a plugin-declared MCP server on its own. Before calling this server's tools, register that command under that name in the host's MCP configuration and verify the connection.

<daodan_host_binding host="codex">
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

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

# Work record

## Ownership

Own operational records and validation. The contract,
`<plugin-root>/contracts/work.toml`, belongs in consumers'
`contract.shared_schemas`, never copied. Workflow `[dispatch]` lists method workers;
`inline_workers` binds this plugin's `isolated-worker` to a task/report contract. Only grants authorize work. Domain owners
keep findings, severity and dispositions; results reference original reports,
hashes, authors, input snapshots and interpreting adapters.

Read `references/process-runtime.md` before graph composition/execution/resume
or console/MCP use. The complete runtime is bundled:
`<plugin-root>/skills/work-record/scripts/controller.py`; no separate
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

Use `python "<plugin-root>/skills/work-record/scripts/run_state.py"`.
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
