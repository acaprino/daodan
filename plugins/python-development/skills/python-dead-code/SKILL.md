---
name: python-dead-code
description: >
  Find and remove unused variables, functions, classes and unreachable branches with vulture and ruff, filtering framework false positives (Django, FastAPI, pytest, click).
  TRIGGER WHEN: cleaning up Python codebases, enforcing import hygiene, or integrating dead code checks into CI.
---

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
