# PR Enhancement Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Start from git diff.** All analysis comes from `git diff` and `git log` -- the actual changes are ground truth.
3. **Run agents in parallel where marked.** Fire parallel agents in a single response.
4. **Confirm before creating PR.** If `--create` flag is set, show the full PR description for approval before running `gh pr create`.
5. **Never enter plan mode.** Execute immediately.
6. **Never push without permission.** If the branch hasn't been pushed, ask the user before pushing.

## Phase 1: Analyze Changes

### Step 1A: Identify the diff

```bash
# Detect base branch with fallback
BASE_BRANCH="${BASE_ARG:-main}"
if ! git show-ref --verify --quiet "refs/heads/$BASE_BRANCH" && \
   ! git show-ref --verify --quiet "refs/remotes/origin/$BASE_BRANCH"; then
  BASE_BRANCH="master"  # Fallback if main doesn't exist
fi
git fetch origin "$BASE_BRANCH" 2>/dev/null || true
MERGE_BASE=$(git merge-base HEAD "origin/$BASE_BRANCH")
git log --oneline "$MERGE_BASE"..HEAD
git diff "$MERGE_BASE"...HEAD --stat
git diff "$MERGE_BASE"...HEAD --name-status
```

If `--base` flag provides a different base branch, use that as `BASE_ARG`.

If no commits diverge from base, check for uncommitted changes:
```bash
git diff --name-only
git diff --cached --name-only
```

If nothing to analyze, say so and stop.

### Step 1B: Categorize changed files

Group files by type:
- **Source code**: `.py`, `.js`, `.ts`, `.tsx`, `.rs`, `.go`, `.java`, etc.
- **Tests**: files matching `test_*`, `*_test.*`, `*.spec.*`, `*.test.*`
- **Config**: `.json`, `.yaml`, `.yml`, `.toml`, `Dockerfile`, `Makefile`
- **Docs**: `.md`, `.txt`, `.rst`
- **Styles**: `.css`, `.scss`, `.less`
- **Build/CI**: `.github/`, `Jenkinsfile`, CI configs

### Step 1C: Compute statistics

```bash
git diff main...HEAD --shortstat
```

Present change summary:
```
Branch: [branch name]
Base: [base branch]
Commits: [count]
Files changed: [count] ([source] source, [test] test, [config] config, [docs] docs)
Lines: +[insertions] / -[deletions] (net: [net change])
```

---
