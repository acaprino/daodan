# Python Dead Code CI/CD, Monorepo Workflows, and Troubleshooting

On-demand reference for `python-development:python-dead-code`.

## 1. CI/CD Integration

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
      - name: Check unused imports and variables
        run: uvx ruff check . --select F401,F841 --output-format github
      - name: Check dead code (vulture)
        run: uvx vulture src/ --min-confidence 90
```

### Pre-commit Hook (`.pre-commit-config.yaml`)

```yaml
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

## 2. Monorepo and Library Workflows

```bash
# Monorepo: scan specific packages or share a whitelist
vulture packages/core/ --min-confidence 80
vulture packages/ whitelist.py --min-confidence 80

# Library development: be conservative with public API symbols and __init__.py re-exports
vulture src/mylib/ --min-confidence 90
ruff check src/mylib/ --select F401 --per-file-ignores "__init__.py:F401"
```

## 3. Troubleshooting

- **Too many false positives**: raise `--min-confidence` to `90`, generate a starter whitelist (`vulture [target] --make-whitelist > whitelist.py`) and prune it to intentional framework/dynamic symbols, and pass `--exclude` for migrations, generated code, and virtualenvs.
- **Ruff not detecting unused imports**: verify `F401` is active (`ruff check --show-settings | grep F401`) or pass `--select F401` explicitly.
- **Overlap between Ruff and Vulture**: Both tools flag unused imports; use `ruff check --select F401 --fix` for imports and `vulture` for unused functions, classes, properties, and unreachable branches, deduplicating before reporting.
