---
name: python-dead-code
description: >
  Find and remove unused variables, functions, classes and unreachable branches with vulture and ruff, filtering framework false positives (Django, FastAPI, pytest, click).
  TRIGGER WHEN: cleaning up Python codebases, enforcing import hygiene, or integrating dead code checks into CI.
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
