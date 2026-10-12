---
description: 'Tidy the workspace: filesystem garbage, generated artifacts tracked in git, `.gitignore` gaps and stale rules, scratch directories, orphan doc-assets, and git auxiliary state. Detects by default; applies with --fix or --commit. TRIGGER WHEN: the user asks to clean up a repository, remove committed build output, fix or audit `.gitignore`, clear scratch and pipeline-output directories, or list stale stashes, orphan worktrees and gone-upstream branches. DO NOT TRIGGER WHEN: the target needs source comprehension (dead code, unused exports, unused dependencies, orphan application assets), which belongs to `/senior-review:code-review`; or the target is test files, which belongs to `/testing:test-consolidate`.'
---

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

# tidy

<!-- Generated by the Daodan compiler for opencode. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **named-agent**, and declared
isolation **required**.

Dispatch one worker per entry in the plan below with the `subagent` tool. Name the role as the
agent, using the qualified identity in the bindings below, and give it a short `description` and the full
task as `prompt`. Each agent runs in a fresh child session, so isolation is native here.
For a local role the qualified form is `agent: "repo-hygiene:<role>"`; external roles
use their owner's prefix from the bindings, never the coordinator's prefix.

Under `parallel-subagents`, dispatch every worker of one phase with `background: true`, then wait
for every completion notice before the phase closes; do not poll. Under `serial-isolated`, dispatch
them one at a time in the foreground.

Every role below is registered as an agent by this package. A `subagent` call that answers with an
unknown agent means the install is broken: stop and report it, never continue with a shorter
report.

Coordinator completion ownership: keep the method's owned run and delivery ledger,
including each expected worker, attempt, report path and required check evidence.
Validate report artifacts before recording delivered. An empty final message or
worker stop remains missing delivery: inspect or resume when permitted, otherwise
record failed with the uncovered scope. Follow the declared join and phase gates;
a recorded failure is accounted for, never converted into a successful delivery.
Continue authorized work and recovery until the requested result and its checks
exist or a concrete blocker is recorded. Preserve the exclusive final report owner
and the ledger schema; a tool exit or a promise cannot satisfy completion.

Harness obligations, none of them optional:

- Every dispatched worker runs in its own context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so the coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `workspace-auditor`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `workspace-auditor` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:tidy-report`.

Role bindings:

- `workspace-auditor`: dispatch the installed `repo-hygiene:workspace-auditor` agent by its qualified identity.

The phase graph and the record schemas are in `contracts/tidy.workflow.toml`.

## Method

# Tidy

Detect and, on request, apply the workspace-hygiene fixes that the filesystem and git
can decide without reading a line of source. Everything that needs to know what a
symbol means belongs to `/senior-review:code-review`, and this command never reaches
for it.

## Requirements

$ARGUMENTS

## Prime directives

1. **No build gate, and no pretending to need one.** Nothing this command applies can
   break a build, because nothing it applies is code. That is the reason the gate is
   absent, and it is also the boundary: the moment a proposed removal could change what
   the build sees, it is not this command's to make.
2. **Every mutation is reversible, or it is not made.** Tracked files go through git and
   git remembers them. Untracked files go to quarantine, never to `rm`. Git refs are not
   touched at all. See Phase 4.
3. **Detection is the default.** Without `--fix` or `--commit`, this command reports and
   changes nothing.
4. **Evidence before action.** Apply nothing whose finding does not quote the command
   output that produced it.

## Step 1: Scope and flags

Resolve the target path (default: repository root). Confirm it is inside a git working
tree; if it is not, say so and stop, since five of the seven checks are git queries.

| Flag | Contract |
|---|---|
| none | Detect and report. Nothing is modified. |
| `--fix` | Apply, leaving the working tree modified with no commits. The user reviews `git status` and commits. |
| `--commit` | Implies `--fix`, and adds one commit per phase. |
| `--phases=` | Restrict to the named phases. Default is all four. |

The two flags mean exactly what they mean in `/senior-review:code-review`, so knowing
one command teaches the other.

## Step 2: Detect

Load the `repo-hygiene:repo-hygiene` skill and run its catalog at the **full** profile:
C1 filesystem garbage, C2 generated artifacts tracked in git, C3 `.gitignore`
completeness, C4 `.gitignore` archaeology, C5 scratch directories, C6 orphan
doc-assets, C7 git auxiliary state.

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

Stop here unless `--fix` or `--commit` was given.

## Step 4: Apply

### Pre-flight

`--commit` requires a clean working tree, because its per-phase commits are its revert
mechanism and an unrelated modified file would be swept into one of them. If the tree
is dirty, name the dirty paths and stop.

`--fix` has no such requirement. It stages nothing and commits nothing, so an unrelated
change is never at risk. This is the mode for a user who wants the tidy without
interrupting whatever else is in flight, and it is the reason the clean-tree rule is
attached to `--commit` rather than to the command.

**Staging is always by explicit path.** Never `git add -A`, never `git add .`. Several
sessions can share a repository, and a blanket stage publishes someone else's
half-finished work.

### The four phases

Run only the phases the accepted findings require, in this order.

**1. `garbage`** (C1). Filesystem cruft and shell-redirection artifacts. Tracked files:
`git rm`. Untracked files: move to quarantine per the rule below. The safest phase in
the command, and the only one with no judgment in it.

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

**4. `git-state`** (C7). **Detection-only. Nothing here is ever applied, at any flag.**

The reason is not caution, it is that the revert mechanism does not reach. Every other
phase mutates tracked content, so its commit records the change and reverting restores
it. Dropping a stash produces no diff for any commit to hold. Removing a worktree takes
its uncommitted files with it. Deleting a branch leaves the tip in a reflog that
expires. A per-phase commit cannot roll back a mutation that leaves no trace in the
tree, so this command does not make one. The findings carry `git stash drop`,
`git worktree remove`, and `git branch -d` for the user to run and own.

### Per phase, under `--commit`

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
what makes `--fix` safe without commits: every operation it performs is undoable by
hand, including the ones git has no record of.

## Step 5: Report what happened

One row per phase: status, items, commit sha where one was made, and the quarantine
path if anything was moved. Then the `git-state` findings, unapplied by design, with
their commands.

Close with the alignment check: Grep the removed paths against `README.md`, `CLAUDE.md`,
and `docs/`, and propose an edit for any hit. A tidy that leaves the documentation
describing a deleted directory has moved the mess rather than cleared it.
