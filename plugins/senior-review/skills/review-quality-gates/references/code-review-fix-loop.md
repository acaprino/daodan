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
  - role: "general-purpose"
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

$ARGUMENTS
