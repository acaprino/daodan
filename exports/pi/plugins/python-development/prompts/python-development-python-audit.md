---
description: 'Run ruff, mypy/pyright, vulture, complexipy/radon and pytest, then report prioritized fixes. TRIGGER WHEN: the user asks to audit a Python codebase across lint, types, complexity, dead code and coverage, or to prepare a codebase for release review. DO NOT TRIGGER WHEN: only one dimension is in scope: restructuring (use /python-development:python-refactor), dead code alone (use /senior-review:code-review --commit), or test writing (use testing:test-writer with pytest-patterns context).'
argument-hint: '<path> [--strict] [--skip-types] [--skip-coverage]'
---

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

# Python Audit

End-to-end Python code-quality audit. Runs the five tools that matter most, aggregates findings, and outputs a prioritized fix list.

## CRITICAL RULES

1. **Use uv for tool execution** -- `uvx ruff`, `uvx mypy`, `uvx vulture` when not in project deps; `uv run ...` when they are.
2. **Run all phases in parallel where possible** -- ruff + vulture + complexity can run concurrently; type-check is separate.
3. **Never auto-fix without approval** -- always show the diff / finding count first, ask before applying.
4. **Scale output to scope** -- for small modules report everything; for 10K+ file repos summarize and prioritize.

## Procedure

### Phase 1 -- Lint (ruff)

```bash
uvx ruff check "$ARGUMENTS" --output-format=json > .python-audit/ruff.json
uvx ruff format --check "$ARGUMENTS"
```

Summarize:
- Total issues by rule category (E/F/W/B/I/N/UP/PL/RUF/PERF)
- Top 5 rules by frequency
- Auto-fixable count (`ruff check --fix` preview)

### Phase 2 -- Types (mypy or pyright)

Detect the project's type checker:
- `mypy.ini`, `[tool.mypy]` in pyproject -> mypy
- `pyrightconfig.json`, `basedpyright` in deps -> pyright / basedpyright
- Neither -> run mypy in strict mode

```bash
uvx mypy --config-file pyproject.toml "$ARGUMENTS" > .python-audit/mypy.txt
# or
uvx pyright "$ARGUMENTS" --outputjson > .python-audit/pyright.json
```

Summarize:
- Total errors / warnings
- Hot files (top 5 by error count)
- Missing-annotation clusters (`disallow_untyped_defs` violations)

### Phase 3 -- Dead Code (vulture + ruff unused)

```bash
uvx vulture "$ARGUMENTS" --min-confidence 80 > .python-audit/vulture.txt
uvx ruff check "$ARGUMENTS" --select F401,F811,F841 --output-format=json > .python-audit/ruff-unused.json
```

Apply framework-aware filtering:
- Django: ignore `admin.py` handlers, `models.Meta`, `signals.py`
- FastAPI: ignore `@app.*` / `@router.*` decorated functions
- pytest: ignore `conftest.py` fixtures, `test_*` functions
- click: ignore `@click.command()` / `@click.group()` targets

### Phase 4 -- Complexity (complexipy + radon)

```bash
uvx complexipy "$ARGUMENTS" --max-complexity-allowed 15 > .python-audit/complexipy.txt
uvx radon mi "$ARGUMENTS" -s > .python-audit/radon-mi.txt
uvx radon cc "$ARGUMENTS" -s -a > .python-audit/radon-cc.txt
```

Flag:
- Functions with cognitive complexity > 15
- Files with Maintainability Index < 65 (yellow) or < 20 (red)
- Average cyclomatic complexity per file

### Phase 5 -- Coverage (if --skip-coverage not set)

```bash
uv run pytest --cov=src --cov-report=json:.python-audit/coverage.json --cov-report=term
```

Flag:
- Required behavioral protection gaps; line coverage is supporting evidence, not a universal quota
- Files with 0% coverage (genuinely untested vs excluded)
- Branch coverage delta (if measured)

## Report Format

Write consolidated report to `.python-audit/REPORT.md`:

```markdown
# Python Audit Report -- <target> -- <date>

## Summary
- Lint: <N> issues (<M> auto-fixable)
- Types: <N> errors in <K> files
- Dead code: <N> unused items (confidence >= 80%)
- Complexity: <K> functions exceed threshold
- Coverage: <P>% (descriptive; project policy where declared)

## Critical (fix before release)
- [path:line] <issue> -- <why it matters>
- ...

## High
- ...

## Medium / polish
- ...

## Auto-fixable (safe to apply)
- `uvx ruff check --fix` resolves <N> issues; diff summary:
- `uvx ruff format` formats <N> files

## Coverage gaps
| File | Lines | Missed | Note |
|------|-------|--------|------|
| ... | ... | ... | ... |
```

## Exit Codes

Return exit code 1 if any critical issues are present and `--strict` is set; otherwise always exit 0 (the report is the value).

## Synergies

- Deep refactoring with metrics -> `/python-development:python-refactor`
- Dead code removal only -> `/senior-review:code-review --commit`
- Missing behavior checks -> `testing:test-writer` with `python-development:pytest-patterns` technical context
- CLAUDE.md updates after cleanup -> `/project-knowledge:instructions`
