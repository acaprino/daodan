---
name: python-audit-method
description: >
  Run ruff, mypy/pyright, vulture, complexipy/radon and pytest, then report prioritized fixes.
  TRIGGER WHEN: `/daodan:check-health` runs on a Python project, the user asks to audit a Python codebase across lint, types, complexity, dead code and coverage, or a codebase is prepared for release review.
  DO NOT TRIGGER WHEN: only one dimension is in scope: restructuring (use python-development:python-refactor-method), dead code alone (use senior-review:application-cleanup-method), or test writing (use testing:test-writer with pytest-patterns context).
---

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
