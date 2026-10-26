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

# Phases 4 and 5: plan and execution

## Compile the plan

Translate the record into micro-tasks grouped into waves. Each task carries `id`,
`write_set`, `oracle` (command and expected pre-change failure), `verification`
command, relevant `resource_locks`, `produces`, `consumes` (`question:<id>` waits
for an answer), the `EX-*` it makes pass and `INV-*` it enforces. Use provider I1
per `references/context-cycle.md`; approved contracts determine precedence. Build
missing oracle fixtures first.

Write the draft into `waves`. The helper refuses an unjustified write set over
four files, tasks sharing files, locks or produced-consumed contracts in one wave,
parallelism outside `WORKTREE`, and missing oracles. A refusal writes nothing;
correct the plan until accepted.

## Review of the plan (stage B)

Run `senior-review:review-method`, shape `light`, kind `plan`, stage `plan`, as
an adversarial review: the premise auditor tries to falsify cited paths, symbols,
callers and every oracle's stated failure. Record `plan_candidate` and a
`plan_review` receipt. No task may enter `running` before the review is delivered
with PASS. Use three rounds, then ask. Present the approved plan
and expected cost; stop for approval unless authorization covers execution.

## Execute a wave

For a new process-backed run, admit the approved graph and bind it as
`work-controller:work-record` describes in `references/process-runtime.md`
before dispatch. Graph agent jobs map to declared native worker reports;
review deliveries outside the graph retain their own ledger entries. Use
the bundled controller's ready packet and attempt identity for dispatch,
admit its artifact before recording the corresponding native delivery, and
continue its frontier after admission. It does not replace stages B or C,
authorize a commit, or turn a missing report into a delivery. Omit engine
commit jobs from the bound graph: this method owns reviewed commits.

For each task in wave order, parallel only in a `WORKTREE`:

1. Record `pre_phase_sha` and pre-step bytes of every `write_set` file.
2. Verify `task-packet` per `references/context-cycle.md`; dispatch with
   `references/worker-brief.md`: dispatch `python-development:python-engineer`
   for Python, dispatch `typescript-development:typescript-engineer` for
   TypeScript/JavaScript, dispatch `testing:test-writer` for tests only,
   otherwise the isolated worker; load skill `skill-catalog:skill-catalog` for knowledge. The writer runs the
   oracle first, returning `ORACLE_INVALID` if it passes or fails differently;
   writes only `write_set`, returning `NEEDS_REPLAN` if more files are needed;
   runs verification, records uncovered local rulings and returns `OK` with paths.
3. On `OK`, confirm paths, rerun verification and snapshot the uncommitted
   candidate. Record passing `verification_receipt` with its digest and HEAD.
4. Run `senior-review:review-method`, shape `light`, kind `changeset`, stage
   `pre-commit-<task id>`, on that candidate. Record its roster before dispatch
   and its result as `pre_commit_review`. `BLOCK`, missing evidence or any edit
   prevents commit; edits require fresh snapshot, verification and review.
5. With PASS and commit authorization, stage only owned paths and make one atomic
   commit: `<type>(<area>): <task title>`, trailer `Daodan-Task: <run id> wave <n>/<m>`.
   Record `commit_sha`. The helper accepts committed status only when current
   HEAD is that commit and scoped bytes match the reviewed digest. Without
   authorization, retain the candidate uncommitted. After uncertain interruption,
   inspect HEAD and bytes on resume; never repeat blindly or use `HEAD~1`.
6. At the barrier, refresh map and protocol candidate; prepare `post-task` per
   `references/context-cycle.md`. On other outcomes, restore owned pre-step bytes,
   remove only task-created files and preserve everything else. `NEEDS_REPLAN`
   returns to planning; `ORACLE_INVALID` returns to record or test.

## Review of the wave (stage C)

With every task committed or its candidate recorded, run
`senior-review:review-method`, shape `light`, stage `wave-<n>`, on its diff with
`EX-*`, `INV-*` and rulings as intent. Record the wave candidate and PASS
`wave_review` on the same digest and HEAD. `BLOCK` reopens the task. Seal only
when every task is committed and the wave review is delivered. Then start the
next wave.

Requested `clean-code:readability-method` edits form a new planned task with fresh
verification and pre-commit review; never amend a reviewed candidate silently.
