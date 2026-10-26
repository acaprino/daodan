<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
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

## Step 5: Final Review Output

Use the template in `references/code-review-output.md` of the
`senior-review:review-quality-gates` skill. Include actual scope, intent, reviewers,
verification, relevant findings, coverage/gaps, instruction compliance, preexisting
issues and verdict. Write each finding once. Omit empty dimension sections and
an overall score unless the caller requested a defined scoring method.

The verdict is one of **Ready to merge / Ready with fixes / Not ready**, with 1-2 sentences of reasoning and a severity-ordered fix list. Under `--strict`, any Critical finding forces `Not ready`.

## Step 5b: CLAUDE.md Alignment Check

Cross-reference the findings with the project's `CLAUDE.md` (already read in Step 2). If any documented convention, structure, or workflow is stale, add a `### CLAUDE.md Staleness` section to the review output. Details in `references/code-review-output.md`.

Save the finalized native report and apply that reference's optional human-view
hook once before delivery. Its presentation contract belongs to
`senior-review:review-consolidation`; do not ask a worker to generate HTML.

## Step 6: Auto-Comment on PR (if --auto-comment)

When reviewing a PR with `--auto-comment`, post the review as inline PR comments with committable suggestions where the fix is small and self-contained. The full comment format, the suggestion inclusion rules, and the `gh api` invocations are in `references/code-review-output.md`; follow them exactly.

## Step 7: Fix Loop (if the run records a `fix` or `commit` grant, or verdict is "Ready with fixes")

**The two grants are distinct contracts.** A `fix` grant means edit and verify: apply the fixes, run the tests, and leave the working tree modified with NO commits, so the user reviews and commits themselves. A `commit` grant implies `fix` and adds the commits: one per fix or batch in 7b, one per phase in 7c. When the loop is entered via the verdict rather than a grant, ask which contract the user wants before touching anything, and record the answer as a grant.

The complete workflow lives in the `senior-review:review-quality-gates` skill, file `references/code-review-fix-loop.md` (read it before entering the loop). In brief:

- **7a Severity acceptance**: one multi-select prompt over the severity levels that have findings.
- **7b Apply fixes**: fix subagents apply the minimal correct fix per finding, run tests, and commit only under a `commit` grant.
- **7c Application cleanup**: load the `senior-review:application-cleanup-method` skill with the accepted findings. It requires commit authorization, completed targeted fixes when applicable, and a clean exclusively owned isolated worktree. The common protocol restores the captured pre-phase state on a failed candidate gate. Under a `fix` grant alone, leave this action open and explain its preconditions. Test-file bulk removal belongs to `testing:test-remediation-method`, mode `consolidate`.

Follow the reference file exactly for 7c's critical rules (clean-tree pre-flight, phase isolation, gate-after-every-phase, grep-before-delete, side-effect protections, vulture approval), the baseline capture, the per-phase template, the docs-phase gating, and the cleanup report.
