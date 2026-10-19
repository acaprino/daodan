---
name: readability-method
description: >
  Canonical readability-only plan, transformation, candidate validation and owned recovery. Load when running /daodan:refactor-code for readability or lifecycle readability phases.
---

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

# Clean Code

Load the `project-protocol:project-protocol` skill for execution preflight, baseline,
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
