# Python Development Plugin

Python implementation, scaffolding, refactoring and framework techniques. Test ownership, validity and retirement belong to [testing](testing.md); Python contributes pytest techniques to that common method.

## Agents

### `python-engineer`

Hands-on Python 3.12+ engineer. Designs system architecture and implements production-ready code using modern tooling (uv, ruff, FastAPI, Pydantic). Async-first, type-safe, well-tested.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Planning new Python projects, designing architecture, making tech stack decisions, implementing Python features |

**Invocation:**
```
Use the python-engineer agent to [design/implement/optimize] [feature]
```

**Expertise:**
- Python 3.12+ features (pattern matching, generics, Protocol typing, dataclasses)
- Modern tooling: uv, ruff, mypy/pyright, pyproject.toml
- Web frameworks: FastAPI, Django 5.x, SQLAlchemy 2.0+, Pydantic v2
- Data pipelines, structured logging, async I/O
- Docker multi-stage builds, K8s manifests, cloud deploy

---

### `python-refactor-agent`

Expert Python refactoring agent. Cleans up legacy code, reduces complexity, removes dead code using vulture/ruff, and improves documentation/comments.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Refactoring code, removing dead code, optimizing imports, reducing cognitive complexity, improving code readability and docstrings |

**Invocation:**
```
Use the python-refactor-agent to refactor [module/file]
```

**Capabilities:**
- Code quality tools: ruff, vulture, mypy
- Refactoring patterns: Extract Method, Replace Conditional with Polymorphism, introducing Dataclasses/Protocols
- Complexity reduction: flattening nested loops/conditionals
- Dead code removal: unused imports, variables, functions, and classes
- Documentation: antirez's 9-type comment taxonomy, Google-style docstrings
- Leverages `python-refactor-method`, `python-dead-code`, `python-comments`, and `python-performance-optimization` skills

---

Test work dispatches `testing:test-writer` or `testing:test-suite-auditor`. The retired `python-test-engineer` has no replacement role inside this plugin. Load `pytest-patterns` for Python fixture, mocking and runner details while using the canonical testing owner.

---

## Skills

### `python-refactor-method`

Systematic 4-phase refactoring workflow that transforms complex code into clean, maintainable code.

| | |
|---|---|
| **Invoke** | `/python-development:python-refactor` or skill reference |
| **Use for** | Legacy modernization, complexity reduction, OOP transformation |

**4-Phase Workflow:**
1. **Analysis**: measure complexity metrics, identify issues
2. **Planning**: prioritize issues, select refactoring patterns
3. **Execution**: apply patterns incrementally with test validation
4. **Validation**: verify tests pass, metrics improved, no regression

**Key Features:**
- 7 executable Python scripts for metrics
- Cognitive complexity calculation
- flake8 integration with 16 curated plugins
- OOP transformation patterns
- Regression prevention checklists

**Synergy:** Uses `pytest-patterns`, the common testing method and `python-performance-optimization`.

---

### `pytest-patterns`

Python techniques for pytest, fixtures, mocking and runners. Behavioral oracles come from the requirement or independent evidence. Test counts and coverage percentages do not establish correctness.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Unit tests, integration tests, fixtures, mocking, coverage |

**Patterns included:**
- pytest fixtures (function, module, session scoped)
- Parameterized tests
- Mocking with unittest.mock
- Async testing with pytest-asyncio
- Property-based testing with Hypothesis
- Database testing patterns

---

### `python-performance-optimization`

Profiling and optimization techniques for Python applications.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Profiling, bottleneck identification, memory optimization |

**Tools covered:**
- cProfile and py-spy for CPU profiling
- memory_profiler for memory analysis
- pytest-benchmark for benchmarking
- Line profiling and flame graphs

---

### `async-python-patterns`

Async/await patterns for high-performance concurrent applications.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | asyncio, concurrent I/O, WebSockets, background tasks |

**Patterns included:**
- Event loop fundamentals
- gather(), create_task(), wait_for()
- Producer-consumer with asyncio.Queue
- Semaphores for rate limiting
- Async context managers and iterators

---

### `python-packaging`

Create and distribute Python packages with modern standards.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Library creation, PyPI publishing, CLI tools |

**Topics covered:**
- pyproject.toml configuration
- Source layout (src/) best practices
- Entry points and CLI tools
- Publishing to PyPI/TestPyPI
- Dynamic versioning with setuptools-scm

---

### `uv-package-manager`

Fast Python dependency management with uv (10-100x faster than pip).

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Dependency management, virtual environments, lockfiles |

**Key commands:**
| Task | Command |
|------|---------|
| Create project | `uv init my-project` |
| Add dependency | `uv add requests` |
| Sync from lock | `uv sync --frozen` |
| Run script | `uv run python app.py` |

---

### `python-dead-code`

Detect and remove unused Python code using vulture and ruff.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Dead code detection, unused imports, unreachable code, framework-aware cleanup |

**Two-tool approach:**
- Ruff: Fast lint-level checks (F401 unused imports, F841 unused variables, F811 redefined names)
- Vulture: Deeper analysis for unused functions, classes, and unreachable code

**Framework-aware:** Handles false positives for Django, FastAPI, pytest, click, and more.

---

### `python-comments`

Write and audit Python code comments using antirez's 9-type taxonomy.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Comment quality review, docstring improvements, documentation audits |

**Two modes:**
- **Write**: add or improve comments in code using systematic classification
- **Audit**: classify and assess existing comments with a structured report

**Features:**
- 9-type comment taxonomy (Function, Design, Why, Teacher, Checklist, Guide, Trivial, Debt, Backup)
- Python-specific mapping (docstrings, inline comments, type hints)
- Quality scoring and improvement recommendations

---

### `pydantic-v2`

Deep guide to Pydantic v2 (2.13+) for production Python. Covers validators, serializers, performance tuning, security, and v1 -> v2 migration, with notes on the 2.11, 2.12 and 2.13 releases. Also documents PydanticAI and Logfire integration.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Writing or refactoring Pydantic models in Python 3.10+; migrating from v1 to v2; choosing `Annotated[Decimal, ...]` vs `condecimal` for money; designing FastAPI request/response schemas and error envelopes; hot-path performance tuning |

**Sections:**
- Core model patterns (`ConfigDict`, `Annotated[T, Field(...)]`, `@computed_field`, discriminated unions)
- Validators: mode decision rules (after/before/wrap/plain), Annotated reusable pattern, `ValidationInfo.context`, `PydanticCustomError`
- Serialization: custom `@field_serializer` / `@model_serializer`, `PlainSerializer`/`WrapSerializer` via Annotated, validation-vs-serialization JSON Schema modes, alias trinity, polymorphic serialization (2.13+)
- Discriminated unions (`Literal` discriminator field)
- Performance: 12-point optimization guide (model_validate_json bytes path, TypeAdapter at module scope, discriminated unions, TypedDict via TypeAdapter, FailFast, defer_build, cache_strings, __pydantic_serializer__ bytes fast-path, model_construct), plus free-threaded Python and `model_rebuild()` notes
- Monetary precision (CWE-681 defense) with `Annotated[Decimal, Field(...)]`
- Settings management via `pydantic-settings` (`SettingsConfigDict` with `.env` file and env prefix, SecretStr, source priority)
- FastAPI integration (response_model projection, RequestValidationError envelope, streaming/SSE)
- Security and secrets (SecretStr/SecretBytes, TypeAdapter safety model, recursive depth guard)
- PydanticAI + Logfire (logfire.instrument_pydantic, logfire.instrument_pydantic_ai, agent framework)
- v1 -> v2 migration checklist (bump-pydantic coverage + gaps; `GenericModel` to native generics with PEP 695 syntax, `__root__` to `RootModel[T]`, `parse_obj_as` to `TypeAdapter`)
- Common gotchas (`strict=True` set globally breaking FastAPI query-param coercion, so apply it per-field or per-call; extra=allow v1/v2 diff, @model_validator(mode="after") classmethod deprecation 2.12+, UTC AwareDatetime trap, model_dump shallow-copy trap, Path/deque constraint removal in 2.11+)

---

## Commands

### `/python-development:python-scaffold`

Scaffold production-ready Python projects with modern tooling. Presents the plan and asks for confirmation before writing files.

```
/python-development:python-scaffold <project-name> [--type fastapi|django|library|cli|generic]
/python-development:python-scaffold user-service --type fastapi
```

The project name is required. Without `--type`, the type is inferred from the request, and asked for when it is unclear.

**Project types:** FastAPI, Django, Library, CLI, Generic

**Generates:** Directory structure, pyproject.toml, pytest config, Makefile, .env.example, .gitignore. Verifies the result with `uv sync` + `pytest` after scaffolding.

---

### `/python-development:python-refactor`

Metrics-driven 4-phase refactoring with checkpoint approval before execution and persistent output files.

```
/python-development:python-refactor src/legacy_module.py
/python-development:python-refactor src/billing/ --strict-mode
```

`--strict-mode` makes the checkpoint recommend partial execution whenever the plan contains High-risk changes. Run state lives in `.python-refactor/state.json`: a run still in progress is offered for resume or a fresh start, and a completed one is offered for archiving before a fresh start.

**Phases:** Analysis -> Planning -> (Checkpoint) -> Execution -> Validation

**Output:** `.python-refactor/` directory with analysis, plan, execution log, and validation report.

---

### `/python-development:python-audit`

Consolidated Python code-quality audit. Runs ruff (lint + format) + mypy/pyright (types) + vulture (dead code) + complexipy/radon (complexity) + pytest coverage in parallel, then aggregates findings into a prioritized fix list at `.python-audit/REPORT.md`.

```
/python-development:python-audit src/                # full audit of src/
/python-development:python-audit . --skip-types      # skip type-check phase
/python-development:python-audit . --skip-coverage   # skip the pytest coverage phase
/python-development:python-audit . --strict          # exit 1 if any critical finding (CI-friendly)
```

**Framework-aware dead-code filtering:** Django admin handlers, FastAPI `@app.*` / `@router.*` routes, pytest `conftest.py` fixtures, click commands all recognized so their "unused" callables aren't falsely flagged.

**Report contains:** Lint issues by rule category, type errors by hot file, dead code with confidence, complexity flags (cognitive > 15, MI < 65), coverage gaps, auto-fixable delta.

---

**Related:** [senior-review](senior-review.md) (language-agnostic code review, including dead-code detection) | [clean-code](clean-code.md) (post-refactor code cleanup) | the upstream agent-teams `/agent-teams:team-feature` (wshobson/agents) for end-to-end development
