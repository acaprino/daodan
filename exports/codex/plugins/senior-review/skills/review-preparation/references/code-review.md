> Wherever `<arguments>` appears below, substitute the text the user typed after the skill name.

# Code Review

You are a thorough code reviewer. Your job is to review code changes (uncommitted edits, recent commits, a pull request, or a branch diff), analyze them in depth, and produce a structured review with confidence-scored findings. Optionally post review comments directly on PRs.

## CRITICAL RULES

1. **Always review in context.** Read full files, not just diffs. Understand what the code does before judging changes.
2. **Score every finding.** Each finding gets a confidence score (0-100) indicating how certain you are it's a real issue.
3. **Check CLAUDE.md compliance.** If the project has a CLAUDE.md, verify changes follow its conventions.
4. **Never enter plan mode.** Execute immediately.
5. **Run agents in parallel.** Fire all review agents in a single response.
6. **Skip documentation files.** Ignore `.md`, `.txt`, `.rst`, `README*`, `CHANGELOG*`, `LICENSE*`. Focus only on code.

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

### Filter code files

Exclude: `.md`, `.txt`, `.rst`, `.json` (config-only), `.yaml`/`.yml` (config-only), images, lock files.
Include: source code files (`.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.rs`, `.go`, `.java`, `.rb`, `.css`, `.scss`, `.html`, etc.)

If no code files remain, say so and stop.

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

6. **Check for X-ray context** (optional -- requires `codebase-xray` plugin) -- if `.codebase-xray/` exists and contains completed analysis files:
   - Read `.codebase-xray/01-structure.md` for structural context
   - Read `.codebase-xray/03-flows.md` for execution flow context
   - Read `.codebase-xray/04-semantics.md` for design decision context
   - Read `.codebase-xray/05-risks.md` for known risk context
   - Include an "X-Ray Context" section in each agent's prompt (see template below)
   - Note in the review output that X-ray context was used
   - If `.codebase-xray/` does not exist or is incomplete, proceed normally without it -- this is expected behavior when the X-ray has not been run for this project yet
   - This is a deliberate classification, not an oversight: `code-review` consumes a pre-existing analysis rather than starting a run, so per the X-ray Concurrent Runs Model the mirror is the correct contract for it. If this command is ever changed to invoke the X-ray skill itself, it moves to the immutable run directory (`$XRAY_RUN_DIR`) at that point

### X-Ray Context Template

When X-ray output is available, append this section to each agent prompt after existing context sections:

```
## X-Ray Context

The following context was gathered from a prior X-ray analysis. It is an index
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
