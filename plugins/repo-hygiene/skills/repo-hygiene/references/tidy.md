# Tidy method

Detect and, once authorized, apply the workspace-hygiene fixes that the filesystem and
git can decide without reading a line of source. `/daodan:tidy-repo` loads this method
inside a run it already holds, and a lifecycle plan reaches it through
`repo-hygiene:repo-hygiene` for reversible workspace operations. Everything that needs
to know what a symbol means belongs to senior-review (`senior-review:cleanup-auditor`
detects it, `senior-review:application-cleanup-method` applies it), and this method
never reaches for it.

## Inputs

- **TARGET**, the caller's free text, read in this order:
  - empty: the repository root;
  - a path: that path;
  - a commit, a branch or a pull request: not a perimeter for this method, which runs
    the **full** profile over the working tree. Tidy the root of the repository that
    holds it and say so. Diff-scoped hygiene is the **lite** profile, which
    `senior-review:review-method` runs;
  - any other text: read it for a path and for phase names; with neither, the
    repository root.
- **Phases.** All four by default: `garbage`, `gitignore`, `scratch`, `git-state`.
  Restrict them only when TARGET names phases.
- **Apply authorization.** Never assumed. The preview always runs first; applying is
  one question asked after the report (Step 4), with or without one commit per phase.
- **The run.** The coordinator's run (`project-protocol:project-protocol`). Its run
  directory holds the tidy report and the recorded authorization. The quarantine keeps
  its project path, `.repo-hygiene/quarantine/`, because the catalog's application
  safety table names it.

## Prime directives

1. **No build gate, and no pretending to need one.** Nothing this method applies can
   break a build, because nothing it applies is code. That is the reason the gate is
   absent, and it is also the boundary: the moment a proposed removal could change what
   the build sees, it is not this method's to make.
2. **Every mutation is reversible, or it is not made.** Tracked files go through git and
   git remembers them. Untracked files go to quarantine, never to `rm`. Git refs are not
   touched at all. See Phase 4.
3. **Preview is the default.** Until the run records an apply authorization, this method
   reports and changes nothing.
4. **Evidence before action.** Apply nothing whose finding does not quote the command
   output that produced it.

## Step 1: Scope

Resolve the target path from TARGET (default: repository root) and the phases (default:
all four). Confirm the path is inside a git working tree; if it is not, say so and
stop, since five of the seven checks are git queries.

## Step 2: Detect

Run the `repo-hygiene:repo-hygiene` catalog at the **full** profile: C1 filesystem
garbage, C2 generated artifacts tracked in git, C3 `.gitignore` completeness, C4
`.gitignore` archaeology, C5 scratch directories, C6 orphan doc-assets, C7 git
auxiliary state. Dispatch one `repo-hygiene:workspace-auditor` in an isolated context
to run it: it receives the resolved scope and phases, and writes the tidy report to the
run directory.

Two rules from the skill are the ones that get skipped under time pressure, and both
exist because being wrong is expensive:

- **C2**: a tracked build output may be published on purpose. Run the publication check
  before proposing to untrack anything.
- **C6**: a doc-asset with no literal Markdown link may still be reached from a config,
  a stylesheet, or a template. Run the widening search before calling it orphaned.

## Step 3: Report

Group findings by phase, ordered as the phases run. State the disposition and
confidence of each, and give the deliberately-kept list its own section: an artifact
cleared once should not be re-litigated by the next run.

This report is the preview. Then ask for the apply authorization (Step 4); without an
apply answer, stop here.

## Step 4: Apply

### Authorization

Ask only when the report holds a finding that some phase would apply; a report whose
findings are all `KEEP`, `REVIEW`, `REPORT-ONLY` or `git-state` needs no question.
Reuse an apply authorization the run already records. Otherwise ask once, through the
host's question tool, with the report's counts per phase, and record the answer in the
run (`project-protocol:project-protocol`). When the session has no question tool, write
the question to the run's `questions` section, end the turn after the report, and
resume on the same run with the answer.

| Answer | Contract |
|---|---|
| Keep the preview | Nothing is modified. |
| Apply without commits | Apply, leaving the working tree modified with no commits. The user reviews `git status` and commits. |
| Apply with commits | Implies applying, and adds one commit per phase. |

The two apply answers mean exactly what applying and committing mean in
`senior-review:review-method`, so knowing one method teaches the other.

The answer authorizes the phases. It does not replace the item-level confirmations
below: `git rm --cached` in `gitignore` and orphan doc-assets in `scratch` are still
confirmed item by item.

### Pre-flight

Applying with commits requires a clean working tree, because its per-phase commits are
its revert mechanism and an unrelated modified file would be swept into one of them. If
the tree is dirty, name the dirty paths and stop.

Applying without commits has no such requirement. It stages nothing and commits
nothing, so an unrelated change is never at risk. This is the answer for a user who
wants the tidy without interrupting whatever else is in flight, and it is the reason the
clean-tree rule is attached to the commit answer rather than to the method.

**Staging is always by explicit path.** Never `git add -A`, never `git add .`. Several
sessions can share a repository, and a blanket stage publishes someone else's
half-finished work.

### The four phases

Run only the phases the accepted findings require, in this order.

**1. `garbage`** (C1). Filesystem cruft and shell-redirection artifacts. Tracked files:
`git rm`. Untracked files: move to quarantine per the rule below. The safest phase in
the method, and the only one with no judgment in it.

**2. `gitignore`** (C2, C3, C4). Append missing patterns first, then handle tracked
matches. `git rm --cached` is applied **one item at a time, each confirmed**, and the
confirmation shows the publication check's result for that path. The asymmetry is
deliberate: appending a pattern is reversible by editing a line, while untracking a
file that a clean checkout needs produces a repository that builds locally and ships
broken. Regenerate `.gitignore` wholesale only if it was empty or clearly minimal;
otherwise append.

**3. `scratch`** (C5, C6). Scratch and pipeline-output directories, then orphan
doc-assets. Untracked and already ignored: quarantine, no commit. Tracked: `git rm -r`
plus an ignore entry. Orphan doc-assets require item-level approval, and the prompt
shows both searches that failed to find a reference, so the user is approving a real
absence rather than a Grep that was too narrow.

**4. `git-state`** (C7). **Detection-only. Nothing here is ever applied, under any
answer.**

The reason is not caution, it is that the revert mechanism does not reach. Every other
phase mutates tracked content, so its commit records the change and reverting restores
it. Dropping a stash produces no diff for any commit to hold. Removing a worktree takes
its uncommitted files with it. Deleting a branch leaves the tip in a reflog that
expires. A per-phase commit cannot roll back a mutation that leaves no trace in the
tree, so this method does not make one. The findings carry `git stash drop`,
`git worktree remove`, and `git branch -d` for the user to run and own.

### Per phase, under the commit answer

1. Re-verify each candidate immediately before acting. A finding is a snapshot; the
   tree may have moved.
2. Apply in batches of five to twenty.
3. Stage by explicit path and commit: `chore(tidy): <phase> -- <count> items`.
4. Proceed to the next phase.

There is no build-and-test gate between phases. Adding one would be ceremony for
`garbage` and `scratch`, and for `gitignore` the protection that actually matters is
the per-item confirmation in the phase itself, not a test suite that passes because the
untracked files are still sitting on disk.

### Quarantine, for untracked removals

Untracked files are the one class git cannot restore, so they are never deleted:

```
.repo-hygiene/quarantine/<YYYY-MM-DD-HHMM>/<original relative path>
```

The run appends `.repo-hygiene/` to `.gitignore` if it is not already ignored, and
reports the quarantine path. The user deletes the directory when satisfied. This is
what makes applying without commits safe: every operation it performs is undoable by
hand, including the ones git has no record of.

## Step 5: Report what happened

One row per phase: status, items, commit sha where one was made, and the quarantine
path if anything was moved. Then the `git-state` findings, unapplied by design, with
their commands.

Close with the alignment check: Grep the removed paths against `README.md`, `CLAUDE.md`,
and `docs/`, and propose an edit for any hit. A tidy that leaves the documentation
describing a deleted directory has moved the mess rather than cleared it.
