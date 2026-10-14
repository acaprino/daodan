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

## Step 5: Final Review Output

Synthesize everything into the final structured review using the full template in the `senior-review:review-quality-gates` skill, file `references/code-review-output.md` (read it now). The template covers: review scope header (with intent, reviewers, verification counts), overall score, findings tables per dimension, coverage and coverage-gaps sections, pattern consistency, CLAUDE.md compliance, pre-existing issues, and the closing verdict block.

The verdict is one of **Ready to merge / Ready with fixes / Not ready**, with 1-2 sentences of reasoning and a severity-ordered fix list. Under `--strict`, any Critical finding forces `Not ready`.

## Step 5b: CLAUDE.md Alignment Check

Cross-reference the findings with the project's `CLAUDE.md` (already read in Step 2). If any documented convention, structure, or workflow is stale, add a `### CLAUDE.md Staleness` section to the review output. Details in `references/code-review-output.md`.

Save the finalized native report and apply that reference's optional human-view
hook once before delivery. Its presentation contract belongs to
`senior-review:review-consolidation`; do not ask a worker to generate HTML.

## Step 6: Auto-Comment on PR (if --auto-comment)

When reviewing a PR with `--auto-comment`, post the review as inline PR comments with committable suggestions where the fix is small and self-contained. The full comment format, the suggestion inclusion rules, and the `gh api` invocations are in `references/code-review-output.md`; follow them exactly.

## Step 7: Fix Loop (if --fix, --commit, or verdict is "Ready with fixes")

**The two flags are distinct contracts.** `--fix` means edit and verify: apply the fixes, run the tests, and leave the working tree modified with NO commits, so the user reviews and commits themselves. `--commit` implies `--fix` and adds the commits: one per fix or batch in 7b, one per phase in 7c. When the loop is entered via the verdict rather than a flag, ask which contract the user wants before touching anything.

The complete workflow lives in the `senior-review:review-quality-gates` skill, file `references/code-review-fix-loop.md` (read it before entering the loop). In brief:

- **7a Severity acceptance**: one multi-select prompt over the severity levels that have findings.
- **7b Apply fixes**: fix subagents apply the minimal correct fix per finding, run tests, and commit only under `--commit`.
- **7c Application cleanup**: load the `senior-review:application-cleanup-method` skill with the accepted findings. It requires commit authorization, completed targeted fixes when applicable, and a clean exclusively owned isolated worktree. The common protocol restores the captured pre-phase state on a failed candidate gate. Under plain `--fix`, leave this action open and explain its preconditions. Test-file bulk removal belongs to `/testing:test-consolidate`.

Follow the reference file exactly for 7c's critical rules (clean-tree pre-flight, phase isolation, gate-after-every-phase, grep-before-delete, side-effect protections, vulture approval), the baseline capture, the per-phase template, the docs-phase gating, and the cleanup report.
