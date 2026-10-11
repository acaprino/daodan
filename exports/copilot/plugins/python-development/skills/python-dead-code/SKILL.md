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

Detect and remove unused code in Python projects using vulture and ruff. Framework-aware analysis that distinguishes real dead code from convention-driven usage patterns.

## Core Expertise

**What it detects**
- Unused imports (ruff F401)
- Unused variables (ruff F841)
- Redefined-unused names (ruff F811)
- Unused functions and classes (vulture)
- Unreachable code after return/raise/break (vulture)

**Key capabilities**
- Two-tool approach: ruff for fast lint-level checks, vulture for deeper analysis
- Framework-aware false positive filtering
- Confidence scoring (vulture `--min-confidence`)
- Whitelist support for intentional exceptions
- CI/CD integration (GitHub Actions, pre-commit)

## Installation

```bash
# Using uv (recommended)
uv tool install vulture
uv tool install ruff

# Or via pip
pip install vulture ruff

# Verify installation
uv run vulture --version 2>/dev/null || vulture --version
uv run ruff --version 2>/dev/null || ruff --version
```

## Basic Usage

### Ruff (Fast Lint-Level Checks)

```bash
# Unused imports (F401)
ruff check [target] --select F401

# Unused variables (F841)
ruff check [target] --select F841

# Redefined unused names (F811)
ruff check [target] --select F811

# All unused-code rules together
ruff check [target] --select F401,F811,F841

# Auto-fix safe removals (imports only)
ruff check [target] --select F401 --fix

# Preview what would be fixed
ruff check [target] --select F401 --fix --diff
```

### Vulture (Deep Unused Code Detection)

```bash
# Full scan with default confidence (60%)
vulture [target]

# Higher confidence -- fewer false positives (recommended)
vulture [target] --min-confidence 80

# Very high confidence -- only obvious dead code
vulture [target] --min-confidence 90

# Scan with whitelist
vulture [target] whitelist.py --min-confidence 80

# Exclude specific paths
vulture [target] --exclude "venv,__pycache__,.git,migrations"

# Sort by confidence (highest first)
vulture [target] --min-confidence 80 --sort-by-size
```

## Categorizing Findings

Group results into these categories for structured reporting:

| Category | Source | Rule/Detection |
|----------|--------|----------------|
| Unused imports | ruff | F401 |
| Unused variables | ruff | F841 |
| Redefined-unused | ruff | F811 |
| Unused functions | vulture | `unused function` |
| Unused classes | vulture | `unused class` |
| Unused properties | vulture | `unused property` |
| Unreachable code | vulture | `unreachable code` |

### Interpreting Vulture Output

```
src/utils.py:42: unused function 'calculate_tax' (60% confidence)
src/models.py:15: unused class 'LegacyUser' (90% confidence)
src/views.py:8: unused import 'render' (90% confidence)
```

- **90-100% confidence**: Almost certainly dead code
- **80-89% confidence**: Very likely dead code, worth investigating
- **60-79% confidence**: Possible dead code, check for dynamic usage

## False Positive Handling

### Framework Conventions

These patterns are NOT dead code even if vulture flags them:

**Django**
- Views referenced in `urls.py` via string paths
- Model fields (accessed via ORM, not direct attribute access)
- Signal handlers connected via `@receiver`
- Management commands (`handle` method)
- Admin classes registered with `@admin.register`
- Middleware classes referenced in `MIDDLEWARE` setting
- Template tags and filters
- Form/serializer fields

**FastAPI / Flask**
- Route handlers decorated with `@app.get`, `@app.post`, etc.
- Dependency injection functions used in `Depends()`
- Event handlers (`@app.on_event`)
- Exception handlers

**pytest**
- Fixtures decorated with `@pytest.fixture` (used by name injection)
- Conftest fixtures (auto-discovered)
- Parametrize arguments
- Plugin hooks (`pytest_*` functions)

**click / typer**
- Commands decorated with `@cli.command()`
- Callback functions
- Parameter callbacks

**General Python**
- `__all__` exports
- `__init__`, `__str__`, `__repr__`, and other dunder methods
- `getattr` / `importlib` dynamic access
- Abstract method implementations
- Celery tasks decorated with `@app.task` or `@shared_task`
- Pydantic model fields and validators

### Creating Whitelist Files

```python
# whitelist.py -- tell vulture these are intentionally used

# Django views (referenced via urls.py string paths)
index_view  # unused function
detail_view  # unused function

# pytest fixtures
db_session  # unused function
mock_client  # unused function

# Celery tasks
send_notification_email  # unused function

# Signal handlers
on_user_created  # unused function
```

Generate a whitelist automatically:

```bash
# Vulture can generate a whitelist from its findings
vulture [target] --make-whitelist > whitelist.py
```

Then review and keep only the intentional entries.

## Configuration

### pyproject.toml (ruff)

```toml
[tool.ruff.lint]
# Enable unused-code rules
select = ["F401", "F811", "F841"]

[tool.ruff.lint.per-file-ignores]
# Allow unused imports in __init__.py (re-exports)
"__init__.py" = ["F401"]
# Allow unused imports in conftest.py (fixtures)
"conftest.py" = ["F401"]
# Allow unused imports in type stubs
"*.pyi" = ["F401"]
```

### pyproject.toml (vulture)

```toml
[tool.vulture]
min_confidence = 80
exclude = [
    "venv/",
    ".venv/",
    "__pycache__/",
    "migrations/",
    "node_modules/",
]
paths = ["src/", "app/"]
```

### .vulture_whitelist.py

```python
# Symbols that vulture flags but are used dynamically
from myapp.models import *  # noqa: F403 -- re-export
```

## Cleanup Workflow

Apply removals in safest-first order:

### 1. Unused imports (safest)

```bash
# Auto-fix with ruff
ruff check [target] --select F401 --fix

# Or remove manually via editor
```

Verify: `python -c "import mymodule"` still works.

### 2. Unused variables

```bash
# Review each finding
ruff check [target] --select F841
```

For unpacking, replace with `_`:
```python
# Before
x, y, z = get_coords()  # z unused

# After
x, y, _ = get_coords()
```

### 3. Unused functions and classes (riskiest)

For each vulture finding with >= 80% confidence:

1. **Search for dynamic usage**: `grep -r "function_name"` across the codebase
2. **Check `__all__` exports**: is it in a public API?
3. **Check decorators**: `@receiver`, `@app.task`, `@pytest.fixture`, etc.
4. **Check string references**: URLs, configs, serializers referencing by name
5. **If truly unused**: delete the definition

### 4. Unreachable code

Remove code blocks after unconditional `return`, `raise`, `break`, or `continue`.

## CI/CD Integration

### GitHub Actions

```yaml
name: Dead Code Check
on:
  push:
    branches: [main]
  pull_request:

jobs:
  dead-code:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4

      - name: Check unused imports
        run: uvx ruff check . --select F401,F841 --output-format github

      - name: Check dead code (vulture)
        run: uvx vulture src/ --min-confidence 90
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--select, "F401,F841", --fix]

  - repo: https://github.com/jendrikseipp/vulture
    rev: v2.14
    hooks:
      - id: vulture
        args: [--min-confidence, "90"]
```

### Makefile Target

```makefile
.PHONY: dead-code
dead-code:
	ruff check . --select F401,F811,F841
	vulture src/ --min-confidence 80
```

## Common Patterns

### Check Only Imports (Fastest)

```bash
ruff check . --select F401
```

Use in CI for strict import hygiene.

### Full Dead Code Audit

```bash
# Step 1: fast lint checks
ruff check . --select F401,F811,F841

# Step 2: deep analysis
vulture . --min-confidence 80 --exclude "venv,migrations,__pycache__"

# Step 3: cross-reference and filter false positives
```

### Monorepo / Multi-package

```bash
# Scan specific packages
vulture packages/core/ --min-confidence 80
vulture packages/api/ --min-confidence 80

# Or scan all with shared whitelist
vulture packages/ whitelist.py --min-confidence 80
```

### Library Development

```bash
# Be conservative -- public API symbols may appear unused
vulture src/mylib/ --min-confidence 90

# Exclude __init__.py re-exports
ruff check src/mylib/ --select F401 --per-file-ignores "__init__.py:F401"
```

## Troubleshooting

### Too Many False Positives

- Increase `--min-confidence` to 90
- Create a whitelist file for framework-specific patterns
- Use `--exclude` for generated code, migrations, vendored code

### Vulture Missing Files

```bash
# Ensure target path is correct
vulture src/ tests/ --min-confidence 80

# Debug: list what vulture scans
vulture src/ --min-confidence 80 2>&1 | head -20
```

### Ruff Not Detecting Unused Imports

```bash
# Check if F401 is enabled
ruff check --show-settings | grep F401

# Force enable
ruff check . --select F401 --config "lint.select = ['F401']"
```

### Conflict Between Ruff and Vulture

Ruff and vulture may flag the same import. Use ruff for imports (auto-fixable) and vulture for functions/classes (needs manual review). Deduplicate findings before presenting.

## References

- Vulture docs: https://github.com/jendrikseipp/vulture
- Ruff F rules: https://docs.astral.sh/ruff/rules/#pyflakes-f
- Ruff configuration: https://docs.astral.sh/ruff/configuration/
