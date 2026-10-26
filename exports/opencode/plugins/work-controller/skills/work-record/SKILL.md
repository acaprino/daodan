---
name: work-record
description: >
  Shared working discipline, canonical run identity, snapshot bindings, delivery
  and verification accounting, authorization continuity, questions to the user
  and safe phase recovery for coordinated project work. Load before authoring
  agent components or tools, briefing workers, asking the user, recording,
  resuming or closing a project intervention.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/`, `agents/` and `commands/`. The loader substitutes it in every body it registers; in any other file, resolve it once from where that file was loaded.

<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

This leaf owns operational records and their validation. Its contract,
`<plugin-root>/contracts/work.toml`, is declared by consumers in
`contract.shared_schemas` and never copied. A workflow's `[dispatch]` lists its
method workers; `inline_workers` binds this plugin's `isolated-worker` to a
concrete task and report contract. Only a grant authorizes work. Domain owners
keep findings, severity and dispositions; a result references the original
report, its hash, author, input snapshot and interpreting adapter.

The complete local process runtime is bundled in this plugin. Before composing,
executing or resuming a graph, or opening its console or MCP interface, read
`references/process-runtime.md`. The launcher is
`<plugin-root>/skills/work-record/scripts/controller.py`; no standalone
repository or separately installed process-controller package is required.

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

Use `python "<plugin-root>/skills/work-record/scripts/run_state.py"`.
Every write names this session with `--session ID`:

```text
init --project ROOT --payload INPUT.json [--run-id ID]
update --project ROOT --run-id ID --expected-revision N --payload PATCH.json
ask --project ROOT --run-id ID --payload QUESTION.json
answer --project ROOT --run-id ID --payload ANSWER.json
resume --project ROOT --run-id ID --payload CONTEXT.json
show --project ROOT --run-id ID [--historical]
snapshot --project ROOT --run-id ID
validate --project ROOT --run-id ID [--current] [--result RESULT.json]
agenda --project ROOT [--branch NAME]
first-use --project ROOT
bind-process --project ROOT --run-id ID --expected-revision N --payload BINDING.json
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

Only the holder writes a task; `--take-over` follows confirmation that the other
session closed. `resume` checks authorizations, scope and candidate, records the
holder and returns pending work and replans. A branch holds one open loop task.
New input or scope means a new run; record interruptions at once. `show --historical`
reads old records; never resumes them.

A gate carries its status, the candidate `digest` and `head` that `snapshot`
prints, and evidence naming the command, or the remote job with its revision
and attempt. Snapshots hash scoped inputs byte for byte, dirty and untracked
files included. A remote check counts only when `head_matches_snapshot` is
true: a job for HEAD cannot verify uncommitted, ignored or transformed inputs,
so run the check locally or record it unavailable. `validate --current` rejects
changed inputs or workspace; `--result` checks the envelope against this
revision, snapshot, ledger and gates.

New process-backed consumers set `process_required: true` at init. Before
dispatch, admit the YAML graph and use `bind-process` to attach its immutable
identity and native delivery mapping. The bridge verifies delivered report
bytes against admitted process artifacts and requires process success in
addition to every existing domain gate. It grants no execution or commit
authority. Existing JSON records remain readable and resumable without an
invented graph or rewritten history. The exact binding and recovery procedure
is in `references/process-runtime.md`.

## Loop sections

A lifecycle run may carry `workspace`, `preflight`, `adr`, `waves`, `rulings`,
`reviews`, `questions`, `environment` and `integration`, each validated when present. A wave task that needs an answer lists `question:<id>`
in `consumes` and waits for it. A review's roster is appended as senior-review's
`review_roster.py compute` wrote it, before dispatch; `--deeper` appends one a
tier up, and nothing lowers one. Running tasks need a delivered adversarial
PASS plan review on the exact plan digest and current bytes. Commits bind parent,
owned diff and wave trailer; completion binds sealed waves, branch review,
reviewed ancestry, merge and realignment. Resume reconciles commit-record crashes.

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

Before a phase, record `pre_phase_sha` and recovery bytes. Snapshot the applied
candidate; run gates and review before commit. Committed tasks need `candidate`,
passing `verification_receipt`, PASS `pre_commit_review`, `commit_sha` and light
changeset review binding. The helper rejects stale bindings
and checks HEAD and bytes. Commit when authorized. On failure, restore owned
edits and
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
