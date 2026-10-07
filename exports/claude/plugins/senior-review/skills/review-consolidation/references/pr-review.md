## Phase 3: Generate PR Description

Using the analysis from Phase 1 and agent findings from Phase 2, generate a complete PR description.

### PR Description Template

```markdown
## Summary

[2-3 sentence executive summary of what this PR does and why]

**Risk Level**: [Low/Medium/High/Critical] | **Review Time**: ~[estimate] min | **Lines**: +[X] / -[Y]

## What Changed

### [Category Icon] [Category] Changes
- [status]: `filename` -- [brief description of change]

[Repeat for each category with changes]

## Why These Changes

[Extract motivation from commit messages and code context -- the business reason]

## Type of Change

- [ ] New feature
- [ ] Bug fix
- [ ] Refactoring
- [ ] Dependency update
- [ ] Configuration change
- [ ] Documentation

## How to Test

1. [Step-by-step testing instructions]
2. [Include specific commands to run]
3. [Expected outcomes]

## Risk Assessment

| Factor | Level | Details |
|--------|-------|---------|
| Size | [Low/Med/High] | [X files, Y lines] |
| Complexity | [Low/Med/High] | [description] |
| Test Coverage | [Low/Med/High] | [description] |
| Dependencies | [Low/Med/High] | [description] |
| Security | [Low/Med/High] | [description] |

[Include any security findings from Agent B]

## Hygiene

[Include the hygiene findings from Agent A, or "Clean". One row per finding
with the path, what it is, and the cleanup phase that resolves it. Omit this
section entirely when the diff is clean, rather than leaving an empty heading.]

## Breaking Changes

[List any breaking changes, or "None"]

## Review Checklist

### General
- [ ] Self-review completed
- [ ] No debugging code left
- [ ] No sensitive data exposed

### Code Quality
[Context-aware items based on file types changed]

### Testing
[Items based on whether tests were added/modified]

### Security
[Items based on security agent findings]
```

### PR Split Suggestions (if applicable)

If `--split-check` flag is set or PR exceeds 500 lines, include:

```markdown
## PR Split Suggestion

This PR is [X] lines across [Y] files. Consider splitting into:

1. **[logical unit 1]**: [files], [purpose]
2. **[logical unit 2]**: [files], [purpose]

This improves review quality and reduces merge conflict risk.
```

---

## Phase 4: Present & Optionally Create PR

### Always: Present the description

Show the complete PR description in the conversation and ask:

```
PR description generated.

Risk Level: [level]
Files: [count] | Lines: +[X]/-[Y]

1. Create PR now (pushes branch and creates PR via gh)
2. Copy description only (I'll create the PR manually)
3. Revise -- adjust the description first
```

### If `--create` flag or user chooses option 1:

First check if branch is pushed:
```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null
```

If not pushed, ask:
```
Branch [name] hasn't been pushed to remote. Push and create PR?
```

Then create the PR:
```bash
git push -u origin [branch-name]
gh pr create --base [base-branch] --title "[title]" --body "[description]"
```

Present the PR URL when done.

### CLAUDE.md Alignment Check

After generating the PR description, check if changes suggest the project's `CLAUDE.md` needs updating:

1. Read `CLAUDE.md` (if it exists)
2. Cross-reference changed files with documented conventions, structure, and workflows
3. If `CLAUDE.md` references outdated information, add a note in the PR description under a `## CLAUDE.md Updates Needed` section

---

### If `--strict-mode` and Critical risk:

```
STRICT MODE: Critical risk factors detected. Recommend splitting or addressing security findings before creating PR.
```
