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
- **The run.** The coordinator's run (`work-controller:work-record`). Its run
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
Reuse an apply authorization the run already records. Otherwise ask once, with the
report's counts per phase, by the question rule of the run
(`work-controller:work-record`): record the question with `ask`, ask it, record the
user's reply with `answer` and the authorization it gives as a grant. Without a
question tool, the turn ends after the report and resumes on the same run with the
answer.

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
