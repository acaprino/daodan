---
name: python-audit-method
description: >
  Run ruff, mypy/pyright, vulture, complexipy/radon and pytest, then report prioritized fixes.
  TRIGGER WHEN: `/daodan:check-health` runs on a Python project, the user asks to audit a Python codebase across lint, types, complexity, dead code and coverage, or a codebase is prepared for release review.
  DO NOT TRIGGER WHEN: only one dimension is in scope: restructuring (use python-development:python-refactor-method), dead code alone (use senior-review:application-cleanup-method), or test writing (use testing:test-writer with pytest-patterns context).
---

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# Python Audit

End-to-end Python code-quality audit. Runs the five tools that matter most, aggregates findings, and outputs a prioritized fix list.

A coordinator that already holds a run loads this method: `/daodan:check-health` on a Python project.

## Inputs

- **TARGET**: what the caller passes. Read it as:
  - a path to a file or directory: audit it as given;
  - a commit, PR or branch: audit the Python files (`.py`, `.pyi`) it changes that exist in the working tree;
  - free text naming a module or package: resolve it to its project-relative path;
  - nothing: the project root.

  In the commands below, `TARGET` stands for the resolved path or paths, each quoted.
- **RUN_DIR**: the caller's run directory. Every file this method writes for itself (tool outputs and `REPORT.md`) goes there, never in the project.
- **Strictness**: a method decision. Default: off, and the audit completes with its report whatever it finds. On when the caller's request asks for a release gate (release review, release readiness, a strict audit). See Exit Codes.
- **Type checking**: a method decision. Default: run Phase 2. Leave it out only when the caller's request excludes type checking; the Summary then reads `Types: not run (excluded by the request)`.
- **Coverage**: a method decision. Default: run Phase 5. Leave it out when the project has no pytest suite (no `test_*.py` or `*_test.py` files and no pytest configuration) or when the caller's request excludes coverage; the Summary then reads `Coverage: not run (<reason>)`.
- **Applying fixes**: an authorization asked when needed (rule 3), once, with the host's question tool, and recorded in the run (`work-controller:work-record`). Without it the audit is a preview: the report lists the auto-fixable items and nothing is edited.

## CRITICAL RULES

1. **Use uv for tool execution** -- `uvx ruff`, `uvx mypy`, `uvx vulture` when not in project deps; `uv run ...` when they are.
2. **Run all phases in parallel where possible** -- ruff + vulture + complexity can run concurrently; type-check is separate.
3. **Never auto-fix without approval** -- always show the diff / finding count first, ask before applying.
4. **Scale output to scope** -- for small modules report everything; for 10K+ file repos summarize and prioritize.

## Procedure

### Phase 1 -- Lint (ruff)

```bash
uvx ruff check TARGET --output-format=json > RUN_DIR/ruff.json
uvx ruff format --check TARGET
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
uvx mypy --config-file pyproject.toml TARGET > RUN_DIR/mypy.txt
# or
uvx pyright TARGET --outputjson > RUN_DIR/pyright.json
```

Summarize:
- Total errors / warnings
- Hot files (top 5 by error count)
- Missing-annotation clusters (`disallow_untyped_defs` violations)

### Phase 3 -- Dead Code (vulture + ruff unused)

```bash
uvx vulture TARGET --min-confidence 80 > RUN_DIR/vulture.txt
uvx ruff check TARGET --select F401,F811,F841 --output-format=json > RUN_DIR/ruff-unused.json
```

Apply framework-aware filtering:
- Django: ignore `admin.py` handlers, `models.Meta`, `signals.py`
- FastAPI: ignore `@app.*` / `@router.*` decorated functions
- pytest: ignore `conftest.py` fixtures, `test_*` functions
- click: ignore `@click.command()` / `@click.group()` targets

### Phase 4 -- Complexity (complexipy + radon)

```bash
uvx complexipy TARGET --max-complexity-allowed 15 > RUN_DIR/complexipy.txt
uvx radon mi TARGET -s > RUN_DIR/radon-mi.txt
uvx radon cc TARGET -s -a > RUN_DIR/radon-cc.txt
```

Flag:
- Functions with cognitive complexity > 15
- Files with Maintainability Index < 65 (yellow) or < 20 (red)
- Average cyclomatic complexity per file

### Phase 5 -- Coverage (when the coverage decision is to run it)

```bash
uv run pytest --cov=src --cov-report=json:RUN_DIR/coverage.json --cov-report=term
```

Flag:
- Required behavioral protection gaps; line coverage is supporting evidence, not a universal quota
- Files with 0% coverage (genuinely untested vs excluded)
- Branch coverage delta (if measured)

## Report Format

Write consolidated report to `RUN_DIR/REPORT.md`:

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

Return exit code 1 if any critical issues are present and strictness is on; otherwise always exit 0 (the report is the value).

## Synergies

- Deep refactoring with metrics -> `python-development:python-refactor-method` (`/daodan:refactor-code`)
- Dead code removal only -> `/daodan:tidy-repo` (`senior-review:application-cleanup-method`)
- Missing behavior checks -> `testing:test-writer` with `python-development:pytest-patterns` technical context
- CLAUDE.md updates after cleanup -> `/daodan:write-docs` (`project-knowledge:instructions-method`)
