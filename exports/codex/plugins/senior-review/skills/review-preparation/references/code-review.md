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



## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

# Code Review

You are a thorough code reviewer. Your job is to review code changes (uncommitted edits, recent commits, a pull request, or a branch diff), analyze them in depth, and produce a structured review with confidence-scored findings. Optionally post review comments directly on PRs.

## CRITICAL RULES

1. **Always review in context.** Read full files, not just diffs. Understand what the code does before judging changes.
2. **Score every finding.** Each finding gets a confidence score (0-100) indicating how certain you are it's a real issue.
3. **Check CLAUDE.md compliance.** If the project has a CLAUDE.md, verify changes follow its conventions.
4. **Never enter plan mode.** Execute immediately.
5. **Run agents in parallel.** Fire all review agents in a single response.
6. **Review the target as given, whatever its kind.** Resolve the target kind through `references/candidate-grounding.md` before Step 1. A document, a plan or a specification is reviewed for what it claims about the code and for what it would make the code do; nothing is skipped for its extension.

## Step 0: Pre-Review Skip Check (PR only)

If `<arguments>` contains a PR number (Case C), run a quick eligibility check **before** gathering any context. Launch a **haiku** agent that checks:

```bash
# Fetch PR metadata
gh pr view <N> --json state,isDraft,author,title,labels

# Check for prior Claude comments
gh pr view <N> --comments --json comments --jq '.comments[].author.login'
```

**Skip the review and stop** if ANY of these are true:
- PR state is `CLOSED` or `MERGED`
- PR is a draft (`isDraft: true`)
- PR is trivial/automated: author is a bot, title matches version-only bumps (`chore(deps):`, `bump *`, `Merge branch`), or has label `skip-review`
- Claude has already commented on this PR (check for `claude` or `github-actions[bot]` with Claude-style review content in comments)

**Still review** Claude-generated PRs (author is Claude but content is real code).

If skipped, print the reason and stop:
```
Skipping review: [PR is closed / PR is draft / PR is trivial / Already reviewed]
```

If not a PR review (Cases A, B, D, E), skip this step entirely.

---

## Step 1: Identify Review Target

**Caller-bound candidate takes precedence.** When the caller supplies resolved
scope, baseline and candidate bindings, validate them through review-preparation
and review exactly that candidate. Derive changed paths and before/after content
from the captured baseline and candidate, including newly created untracked files;
Git's tracked-file lists alone do not enumerate this target. If baseline content
cannot be recovered, declare the comparison gap and do not substitute HEAD~1 or a
branch diff. If the candidate equals the supplied baseline, report no changes in
that scope rather than reviewing an unrelated commit. Continue Step 1b/Step 2 with
the supplied target and its evidence, without running Cases A-E below.

For standalone calls without a caller-bound candidate, determine what to review
from `<arguments>` using this priority:

**Case A -- Uncommitted/staged changes exist** (no explicit PR or branch arg):

```bash
git diff --name-only          # unstaged changes
git diff --cached --name-only # staged changes
```

If either has results, use uncommitted changes as the review target. The diff source is "uncommitted changes".

**Case B -- `--commits N` flag provided:**

Use `git diff HEAD~N..HEAD` as the review target. The diff source is "last N commits".

**Case C -- PR number provided** (e.g. `42`, `#42`):

```bash
gh pr view 42 --json number,title,body,baseRefName,headRefName,files
gh pr diff 42
```

**Case D -- `--branch <name>` provided:**

```bash
git log main..<branch> --oneline
git diff main...<branch>
```

**Case E -- No arguments, no uncommitted changes:**

Detect current branch and compare against main/master:

```bash
CURRENT=$(git branch --show-current)
BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git diff ${BASE}...${CURRENT}
```

If the branch is main/master with no diff, fall back to last commit (`HEAD~1..HEAD`).

### Partition the target by kind

Apply section 1 of `references/candidate-grounding.md` to every file in the
target. Source files, stylesheets, markup and contract files are the
`changeset`; manifests and lockfiles activate the `dependencies` dimension;
Markdown, text and reStructuredText files are a `plan`, a `spec` or a `doc`
and get their own scope and roster; images and generated files are listed and
not reviewed. Prepare each kind present, with one brief and one ledger.

If no file falls in any kind, say so and stop.

## Step 1b: Intent Discovery

Before diving into file contents, understand **what the change is trying to accomplish**. Run a single bash call:

```bash
echo "BRANCH:" && git rev-parse --abbrev-ref HEAD && echo "COMMITS:" && git log --oneline ${MERGE_BASE:-HEAD~1}..HEAD
```

Combined with conversation context (user description, PR title/body if available), write a 2-3 line intent summary:

```
Intent: Simplify tax calculation by replacing the multi-tier rate lookup
with a flat-rate computation. Must not regress edge cases in tax-exempt handling.
```

**Pass this intent to every agent** in Step 3. Intent shapes how hard each reviewer looks -- a "fix typo" intent means less scrutiny than a "rewrite auth middleware" intent.

**When intent is ambiguous:** Ask one question: "What is the primary goal of these changes?" Do not proceed until intent is established.

## Step 2: Gather Context

For each changed code file:

1. **Read the full file** -- understand surrounding context
2. **Get the diff** -- know exactly what changed
3. **Get recent commit history for changed files** -- understand the business context behind the code

```bash
git log -n 5 --oneline <file>
```

4. **Check for past PR comments** on the same files (if reviewing a PR):

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --jq '.[].path' | sort -u
```

5. **Read CLAUDE.md** if it exists -- note project conventions, naming rules, patterns

6. **Check for Codebase Map context** (optional -- requires `codebase-map` plugin) -- if `.codebase-map/` exists and contains completed analysis files:
   - Read `.codebase-map/01-structure.md` for structural context
   - Read `.codebase-map/03-flows.md` for execution flow context
   - Read `.codebase-map/04-semantics.md` for design decision context
   - Read `.codebase-map/05-risks.md` for known risk context
   - Include an "Codebase Map Context" section in each agent's prompt (see template below)
   - Note in the review output that Codebase Map context was used
   - If `.codebase-map/` does not exist or is incomplete, proceed normally without it -- this is expected behavior when the Codebase Map has not been run for this project yet
   - This is a deliberate classification, not an oversight: `code-review` consumes a pre-existing analysis rather than starting a run, so per the Codebase Map Concurrent Runs Model the mirror is the correct contract for it. If this command is ever changed to invoke the Codebase Map skill itself, it moves to the immutable run directory (`$XRAY_RUN_DIR`) at that point

### Codebase Map Context Template

When Codebase Map output is available, append this section to each agent prompt after existing context sections:

```
## Codebase Map Context

The following context was gathered from a prior Codebase Map analysis. It is an index
of hypotheses produced by one upstream observer, not ground truth.

Use it to know WHERE to look. Do not use it to know WHAT IS TRUE: re-derive any
claim you intend to stand a finding on. Actively look for code paths that
contradict it; finding one is a result, not a failure. Silence in this context is
not evidence of absence.

Do not restate findings already reported here as if they were your own; add the
issues your specialized perspective reveals.

### Structure & Flows
[Insert relevant excerpts from 01-structure.md and 03-flows.md]

### Design Decisions & Assumptions
[Insert relevant excerpts from 04-semantics.md]

### Known Risks
[Insert relevant excerpts from 05-risks.md]
```

## Step 2b: Large Change Set Handling

Before proceeding, check the total size of changed code:

```bash
git diff --shortstat  # or the equivalent for the detected diff source
```

If total changed lines exceed 500, batch the files into groups of 3-5 files per agent invocation. Run each batch sequentially, consolidating findings across batches before scoring. This prevents context window overflow and "lost in the middle" attention degradation.
