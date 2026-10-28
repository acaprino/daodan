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

# Phases 4 and 5: plan and execution

## Compile the plan

Load `references/specification.md`; verify the specification binding when present.
Translate approved requirements and decisions into waves. Each task carries `id`,
`write_set`, `oracle` (command and expected pre-change failure), `verification`,
`resource_locks`, `produces`, `consumes` (`question:<id>` waits for an answer),
`EX-*` and `INV-*`. Cite the specification path, SHA-256 and approval source.
Pure repair/refactor and legacy runs without a specification retain their method.
Use provider I1 per `references/context-cycle.md`; approved contracts determine
precedence. Build missing oracle fixtures first.

Write `waves`. The helper refuses unjustified write sets over four files,
overlapping files/locks/contracts within a wave, parallelism outside `WORKTREE`
and missing oracles. Correct rejected plans; refusal writes nothing.

## Review of the plan (stage B)

Run `senior-review:review-method`, shape `light`, kind `plan`, stage `plan`:
falsify cited paths, symbols, callers and oracle failures. Record `plan_candidate`
and PASS `plan_review` before tasks run. After three unsuccessful rounds, ask.
Show the plan and cost; obtain approval unless execution is already authorized.

## Execute a wave

New process-backed runs admit and bind the approved graph and worker outputs
through `work-controller:work-record`'s `references/process-runtime.md` before
dispatch. Use its ready packet/attempt; admit artifacts before native delivery.
Reviews retain their ledger. Process success replaces no domain gate or grant;
omit engine commit jobs. Verify the specification binding before execution.

For each task, parallel only in `WORKTREE`:

1. Capture `pre_phase_sha` and pre-step bytes of every owned file.
2. Verify `task-packet` per `references/context-cycle.md`. Brief through
   `references/worker-brief.md`; dispatch `python-development:python-engineer`,
   dispatch `typescript-development:typescript-engineer`, `testing:test-writer` for tests,
   otherwise the isolated worker. Load `skill-catalog:skill-catalog` for knowledge.
   Run the oracle first: unexpected success/failure is `ORACLE_INVALID`. Stay in
   `write_set`, else `NEEDS_REPLAN`; verify and return paths plus uncovered rulings.
3. On `OK`, confirm paths, rerun verification and snapshot the candidate.
   Record PASS `verification_receipt` with digest and HEAD.
4. Run `senior-review:review-method`, shape `light`, kind `changeset`, stage
   `pre-commit-<task id>`. Record roster and `pre_commit_review`. BLOCK, missing
   evidence or edits prevent commit; edits require fresh verification and review.
5. With PASS and commit authorization, stage owned paths and commit atomically:
   `<type>(<area>): <task title>`, trailer `Daodan-Task: <run id> wave <n>/<m>`.
   Record `commit_sha`; HEAD and scoped bytes must match the reviewed candidate.
   Otherwise retain uncommitted. After interruption inspect HEAD/bytes; never
   retry blindly or assume `HEAD~1`.
6. Refresh map/protocol and prepare `post-task`. On failure restore only captured
   owned bytes, remove task-created files and preserve other work. `NEEDS_REPLAN`
   returns to planning; `ORACLE_INVALID` to specification/test.

## Review of the wave (stage C)

Review every completed wave through `senior-review:review-method`, shape `light`,
stage `wave-<n>`, using `EX-*`, `INV-*` and rulings. Record PASS `wave_review`
on its exact digest/HEAD. BLOCK reopens the task. Seal only after every task
is committed and reviewed. Requested readability edits through
`clean-code:readability-method` require a new planned, verified and reviewed task.
