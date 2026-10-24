---
name: readability-method
description: >
  Canonical readability-only plan, transformation, candidate validation and owned recovery. Load when running /daodan:refactor-code for readability or lifecycle readability phases.
---


# Clean Code

Load the `work-controller:work-record` skill for execution preflight, baseline,
candidate gate and recovery. Capture the owned files' exact pre-edit contents,
including preexisting edits and untracked files. Use path-scoped restoration on
failure; hard reset needs an exclusively owned clean isolated workspace and
captured `pre_phase_sha`. Required remote checks match the candidate snapshot and
command/configuration/job identity. Do not overwrite another writer's later edit.

Use the `clean-code-agent` to rewrite source code for readability without changing behavior.

## Rules

1. **Validate before and after.** Establish a baseline with type checker + tests + linter, then verify no regressions.
2. **Preview first.** Show proposed changes without modifying files; without an apply authorization, stop there.
3. **Revert on failure.** If any validation fails after a change, restore the exact saved pre-edit content through the common protocol; preserve preexisting edits and stop on a foreign-writer conflict.
4. **Reuse explicit scope authorization.** Show the reviewable preview; ask only for choices not already covered by the caller's accepted plan or a `fix` grant the run records.
5. **Block without validation tools.** If no tests AND no type checker exist, proceed only on the user's explicit answer to that gate.

## Step 1: Identify Target

From the caller's target, determine files to clean:
- If a file path: clean that file
- If a directory: clean all source files in it
- Filter out test files (unless they reference renamed symbols)

List the files to be cleaned and their language.

## Step 2: Establish Validation Baseline

Detect available validation tools by inspecting project files:

| Tool | How to detect | Command |
|------|--------------|---------|
| **Type checker** | `tsconfig.json` | `tsc --noEmit` |
| | `mypy.ini`, `pyrightconfig.json`, or mypy/pyright in `pyproject.toml` | `mypy .` or `pyright` |
| | `Cargo.toml` | `cargo check` |
| | `go.mod` | `go vet ./...` |
| **Test runner** | `package.json` | `npm test` |
| | `pyproject.toml` or `setup.py` | `pytest` |
| | `Cargo.toml` | `cargo test` |
| | `go.mod` | `go test ./...` |
| | `Makefile` with test target | `make test` |
| **Linter** | `ruff.toml` or ruff config in `pyproject.toml` | `ruff check` |
| | `.eslintrc*` or `eslint.config.*` | `eslint` |
| | `Cargo.toml` | `cargo clippy` |

Run all detected tools and capture both stdout and stderr. Record the baseline.

**Hard gate:** if NO tests AND NO type checker are found, stop and tell the user:

```
No tests or type checker found. Cannot validate that changes are safe.

1. Cancel: set up tests or type checking first (recommended)
2. Proceed anyway: I'll be careful but regressions may go undetected
```

An apply authorization alone does NOT bypass this gate. Only an answer of 2 to this question does; record it in the run as a `fix` grant that names the missing validation.

## Step 3: Preview Changes

Always show the preview first. When the run already records a `fix` grant covering these files, apply all changes after showing it without asking; otherwise ask once with the options below and record the answer as a grant.

For each file, analyze and propose:
- Variable/function renames (vague -> domain-meaningful)
- Boilerplate comments to remove (paraphrase comments, empty docstrings)
- Why-comments to add (non-obvious business logic)
- Structural simplifications (flatten nesting, remove redundant abstractions, consolidate logic)

Present the preview:

```
Clean Code preview for: [target]

[file1]:
- Rename `data` -> `user_profile` (line 23)
- Rename `proc` -> `process_payment` (line 45)
- Remove boilerplate docstring (line 12-15)
- Flatten nested if/else chain (line 30-50)
- Add comment explaining retry logic (line 67)

[file2]:
- ...

Total changes: [count] across [file count] files

1. Apply all changes
2. Apply to specific files only
3. Cancel
```

When the user asked for a preview only, or chose Cancel, stop after the preview.

## Step 4: Apply Changes

Dispatch one `clean-code-agent` in its own isolated context with a prepared brief. The agent executes that task: it does not reload this method, repeat Steps 1 to 3, dispatch further workers or commit. Its safety rules and transformation guidelines live in the role: do not repeat them here. Its brief:

```
Improve the readability of this code. Zero behavior changes.

Owned files: [list of files]
Approved changes: [from the preview]
Baseline: [tools detected in Step 2, their commands and results]
Authorization: [the `fix` grant, and the go-ahead without validation tools when given; the caller commits, the worker never does]
Report path: [assigned report path]
```

## Step 5: Validate & Report

Re-run ALL validation tools detected in Step 2, in this order:

1. **Type checker**: if it fails on a file that passed in baseline, revert that file
2. **Tests**: if any previously-passing test now fails, revert the responsible file
3. **Linter**: if new errors appear, fix or revert
4. **Non-code grep**: for every renamed symbol, search `.json`, `.yaml`, `.yml`, `.toml`, `.env`, `.cfg`, `.ini`, `.xml`, `.html`, `.md` for the OLD name. Report matches as warnings.

Present summary:

```
Clean Code complete for: [target]

Files modified: [count]
Changes made:
- Renames: [count]
- Comments removed: [count]
- Comments added: [count]
- Structural simplifications: [count]

Validation:
  Type check: [passed / N errors: reverted] or [not available]
  Tests: [all passing / X failures: reverted] or [not available]
  Linter: [passed / N new warnings] or [not available]

Stale references found in non-code files:
  - [config.json:12]: still references old name `data`
  - [README.md:45]: documents old function name `proc`

Review the changes with: git diff
```

When the caller asks for a strict pass, also flag any remaining readability concerns that weren't auto-fixable.

## What It Does / Does NOT Do

**Does:** rename vague local variables, remove paraphrase comments, add why-comments, simplify structure (flatten nesting, remove redundant abstractions, consolidate logic).

**Does not:** reorder code, extract functions, change APIs, remove error handling/validations/imports, modify test files, over-simplify. See the agent's safety rules for the full list.

Return deeper structural changes to the caller's development plan; this method applies readability only.
