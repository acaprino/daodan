> Wherever `<arguments>` appears below, substitute the text the user typed after the skill name.

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

# Code-review fix loop (Step 7)

The complete `--fix` / `--commit` workflow for `/senior-review:code-review`:
severity acceptance, targeted fixes (7b), and the gated five-phase cleanup
removal (7c). Loaded on demand by the command when the fix loop is entered.

## Step 7: Fix Loop (if --fix, --commit, or verdict is "Ready with fixes")

After presenting the review (Step 5/6), offer an interactive fix cycle. Skip this step if the verdict is "Ready to merge" with no findings, or if the user didn't request fixes.

**The two flags are distinct contracts.** `--fix` means edit and verify: apply the fixes, run the tests, and leave the working tree modified with NO commits, so the user reviews and commits themselves. `--commit` implies `--fix` and adds the commits: one per fix or batch in 7b, one per phase in 7c. When the loop is entered via the verdict rather than a flag, ask which contract the user wants before touching anything.

Targeted fixes (7b) are minimal changes. Bulk application subtraction (7c) loads
the named cleanup method with its own preconditions. Test-file consolidation is
owned by `/testing:test-consolidate`; semantic refactors return to the development
plan. Load the `project-protocol:project-protocol` skill before mutation and preserve the
caller's workspace, authorizations and pre-phase recovery point.

### 7a. Severity Acceptance

Present a single prompt listing all severity levels with findings. Use the host question mechanism with multiple severity choices:

When Critical or High findings exist:
- [x] **Critical + High (Recommended)** -- N issues
- [ ] **Medium** -- N issues
- [ ] **Low** -- N issues

When only Medium/Low findings exist:
- [ ] **Medium** -- N issues
- [ ] **Low** -- N issues

Only include severity levels that have findings. Reuse an already accepted finding
list/severity scope from the caller's plan; ask only for missing choices.

### 7b. Apply Fixes

For the selected severities, spawn one or more fix subagents:

```
Isolated worker brief:
  - description: "Fix [N] review findings"
  - role: "project-protocol:isolated-worker"
  - prompt: |
    Fix the following code review findings. For each finding, apply the
    minimal correct fix. Run tests after fixing to verify no regressions.

    ## Findings to Fix
    [filtered findings at selected severities with file:line and suggested fix]

    ## Rules
    - Fix ONLY the listed findings, do not refactor surrounding code
    - Run existing tests after each fix
    - If a fix would require significant refactoring, note it and skip
    - {if --commit: Commit each fix or batch of related fixes | if --fix only:
      Do NOT commit anything; leave the working tree modified for the user}
```

Wait for all fixes to complete before proceeding.

### 7c. Application cleanup

Load the `senior-review:application-cleanup-method` skill with the accepted severities and
findings from 7a, targeted-fix delivery when applicable, clean owned isolated workspace, output
root and commit authorization. The method contains the canonical five phases.
Under plain `--fix`, leave subtraction open and report that its commit-only
preconditions are missing. Do not duplicate its gate or recovery rules here.

### 7d. Re-review Offer

After fixes land, present:
- **Run another review round (Recommended)** -- verify fixes and check for new issues
- **Proceed without re-review**

If another round: run the full Step 1-7 flow again (fresh agents, fresh scope).

### 7e. Post-fix Options

After the fix-review cycle completes (clean verdict or user chose to stop):

**On a feature branch:**
- **Create a PR (Recommended)** -- push and open via `gh pr create`
- **Continue without PR**

**On main/master:**
- **Continue**

<arguments>
