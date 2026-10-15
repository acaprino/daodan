---
name: python-dead-code
description: >
  Find and remove unused variables, functions, classes and unreachable branches with vulture and ruff, filtering framework false positives (Django, FastAPI, pytest, click).
  TRIGGER WHEN: cleaning up Python codebases, enforcing import hygiene, or integrating dead code checks into CI.
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

# Python Dead Code Detection

Detect and remove unused code in Python projects using `ruff` (fast lint-level checks for imports and local variables) and `vulture` (AST analysis for unused functions, classes, properties, and unreachable branches), with framework-aware false-positive filtering.

## Reference router

| Task | Reference |
|---|---|
| GitHub Actions, pre-commit hooks, monorepo/library workflows, and false-positive troubleshooting | `references/ci-and-troubleshooting.md` |

## 1. Installation and CLI Usage

```bash
# Install via uv (recommended) or pip
uv tool install vulture
uv tool install ruff

# Ruff: unused imports (F401), redefined names (F811), unused local variables (F841)
ruff check [target] --select F401,F811,F841
ruff check [target] --select F401 --fix --diff

# Vulture: deep unused code detection (60% default, 80%+ recommended)
vulture [target] --min-confidence 80 --exclude "venv,.venv,__pycache__,.git,migrations"
vulture [target] whitelist.py --min-confidence 80 --sort-by-size
```

| Category | Tool | Rule / Confidence |
|---|---|---|
| Unused imports / redefined names / unused locals | `ruff` | `F401`, `F811`, `F841` |
| Unused functions, classes, properties, unreachable code | `vulture` | `90-100%` almost certain; `80-89%` likely; `60-79%` verify dynamic usage |

## 2. Framework False Positives and Whitelists

Do not treat framework-wired symbols as dead code without checking their registration surface:
- **Django**: Views referenced as strings in `urls.py`, ORM model/form/serializer fields, `@receiver` signal handlers, management command `handle()`, `@admin.register` classes, `MIDDLEWARE` entries, template tags/filters.
- **FastAPI / Flask**: `@app.get`/`@app.post` route handlers, `Depends()` callables, lifecycle and exception handlers.
- **pytest**: `@pytest.fixture` functions (including `conftest.py`), `pytest_*` hooks.
- **click / typer / Celery**: `@cli.command()` callbacks, `@app.task` / `@shared_task` workers.
- **General Python**: `__all__` public exports, dunder methods, `getattr`/`importlib` targets, abstract method implementations, Pydantic fields and validators (`@field_validator`, `@model_validator`).

Generate and curate a whitelist for intentional dynamic symbols:

```bash
vulture [target] --make-whitelist > whitelist.py
```

## 3. Configuration (`pyproject.toml`)

```toml
[tool.ruff.lint]
select = ["F401", "F811", "F841"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"conftest.py" = ["F401"]
"*.pyi" = ["F401"]

[tool.vulture]
min_confidence = 80
exclude = ["venv/", ".venv/", "__pycache__/", "migrations/", "node_modules/"]
paths = ["src/", "app/"]
```

## 4. Safest-First Cleanup Order

1. **Unused imports (`F401`)**: run `ruff check [target] --select F401 --fix` (preserving `__init__.py` re-exports) and verify module imports still succeed.
2. **Unused variables (`F841`)**: replace unused tuple unpacking targets with `_`.
3. **Unreachable code**: remove dead statements after unconditional `return`, `raise`, `break`, or `continue`.
4. **Unused functions and classes (`vulture >= 80%`)**: search for string/dynamic references across the codebase, check `__all__` and framework decorators, and remove only after confirming no runtime caller exists.
