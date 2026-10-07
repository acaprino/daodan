## Step 5: Final Review Output

Synthesize everything into the final structured review using the full template in the `senior-review:review-quality-gates` skill, file `references/code-review-output.md` (read it now). The template covers: review scope header (with intent, reviewers, verification counts), overall score, findings tables per dimension, coverage and coverage-gaps sections, pattern consistency, CLAUDE.md compliance, pre-existing issues, and the closing verdict block.

The verdict is one of **Ready to merge / Ready with fixes / Not ready**, with 1-2 sentences of reasoning and a severity-ordered fix list. Under `--strict`, any Critical finding forces `Not ready`.

## Step 5b: CLAUDE.md Alignment Check

Cross-reference the findings with the project's `CLAUDE.md` (already read in Step 2). If any documented convention, structure, or workflow is stale, add a `### CLAUDE.md Staleness` section to the review output. Details in `references/code-review-output.md`.

## Step 6: Auto-Comment on PR (if --auto-comment)

When reviewing a PR with `--auto-comment`, post the review as inline PR comments with committable suggestions where the fix is small and self-contained. The full comment format, the suggestion inclusion rules, and the `gh api` invocations are in `references/code-review-output.md`; follow them exactly.

## Step 7: Fix Loop (if --fix, --commit, or verdict is "Ready with fixes")

**The two flags are distinct contracts.** `--fix` means edit and verify: apply the fixes, run the tests, and leave the working tree modified with NO commits, so the user reviews and commits themselves. `--commit` implies `--fix` and adds the commits: one per fix or batch in 7b, one per phase in 7c. When the loop is entered via the verdict rather than a flag, ask which contract the user wants before touching anything.

The complete workflow lives in the `senior-review:review-quality-gates` skill, file `references/code-review-fix-loop.md` (read it before entering the loop). In brief:

- **7a Severity acceptance**: one multi-select prompt over the severity levels that have findings.
- **7b Apply fixes**: fix subagents apply the minimal correct fix per finding, run tests, and commit only under `--commit`.
- **7c Application cleanup**: load the `senior-review:application-cleanup-method` skill with the accepted findings. It requires commit authorization, completed targeted fixes when applicable, and a clean exclusively owned isolated worktree. The common protocol restores the captured pre-phase state on a failed candidate gate. Under plain `--fix`, leave this action open and explain its preconditions. Test-file bulk removal belongs to `/testing:test-consolidate`.

Follow the reference file exactly for 7c's critical rules (clean-tree pre-flight, phase isolation, gate-after-every-phase, grep-before-delete, side-effect protections, vulture approval), the baseline capture, the per-phase template, the docs-phase gating, and the cleanup report.
