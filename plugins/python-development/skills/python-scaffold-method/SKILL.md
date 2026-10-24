---
name: python-scaffold-method
description: >
  Generate a fresh project skeleton, tests and lint config included.
  TRIGGER WHEN: `/daodan:init-project` runs on an empty folder and the user wants a Python project, or the user asks to start a new Python project, bootstrap FastAPI/Django/CLI/library structure, or set up uv+pytest+ruff from scratch.
  DO NOT TRIGGER WHEN: adding to an existing project (use python-engineer).
---

# Python Project Scaffolding

You are a Python project architecture expert. Generate complete project structures with modern tooling (uv, FastAPI, Django), type hints, testing setup, and configuration.

A coordinator that already holds a run loads this method: `/daodan:init-project` on an empty folder when the user wants a Python project.

## Inputs

- **TARGET**: what the caller passes. Read it as:
  - a path to an empty folder: that folder is the project root, and its name is the default project name;
  - free text: the project name and a description of the project. With no folder given, the project root is a new `<project-name>/` folder in the current directory.

  A folder that already holds a project is out of scope: adding to an existing project belongs to `python-engineer`.
- **Project name**: required. Read it from the text, otherwise use the folder name. If neither gives one, ask for it together with the type question of Step 1.
- **Project type**: a method decision read from TARGET (Step 1): a type the text names (`fastapi`, `django`, `library`, `cli`, `generic`) or one inferred from the description. No default: if the type is unclear, ask (Step 1).
- **Writing files**: an authorization asked at Step 2. The confirmed plan is that authorization: ask once with the host's question tool and record the answer in the run (`work-controller:work-record`). Nothing is created before it.

## CRITICAL RULES

1. **Confirm before writing files.** Present the project plan and get user approval before creating anything.
2. **Use uv for everything.** Package management, virtual environments, running scripts.
3. **Never enter plan mode.** Execute immediately.

## Step 1: Determine Project Type

From TARGET, identify:
- **Project name** (required)
- **Project type** from a type the text names, or infer from description:
  - `fastapi`: REST APIs, microservices, async applications
  - `django`: Full-stack web applications, admin panels
  - `library`: Reusable packages, utilities
  - `cli`: Command-line tools
  - `generic`: Standard Python applications

If type is unclear, ask:

```
Project: [name]

What type of project?
1. FastAPI -- REST APIs, microservices, async
2. Django -- Full-stack web, admin panels
3. Library -- Reusable package
4. CLI -- Command-line tool
5. Generic -- Standard Python application
```

## Step 2: Present Plan & Confirm

Show the complete project structure before creating files:

```
Project: [name]
Type: [type]
Python: >=3.11

Directory structure:
[complete tree]

Key dependencies:
[list]

Tooling:
- Package manager: uv
- Linter: ruff
- Tests: pytest
- Type checking: mypy (library/cli only)

1. Create this project
2. Adjust -- change structure or dependencies
3. Cancel
```

Do NOT create any files until the user confirms.

## Step 3: Scaffold

After approval, create the project. The top directory of each tree below is the project root.

### FastAPI Project

```
fastapi-project/
├── pyproject.toml
├── .gitignore
├── .env.example
├── Makefile
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── endpoints/
│       │       │   ├── __init__.py
│       │       │   ├── users.py
│       │       │   └── health.py
│       │       └── router.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── security.py
│       │   └── database.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── user.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── user.py
│       └── services/
│           ├── __init__.py
│           └── user_service.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── api/
        ├── __init__.py
        └── test_users.py
```

Dependencies: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`
Dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`

### Django Project

Initialize with `django-admin startproject config .`, then `python manage.py startapp core`.

Dependencies: `django`, `django-environ`, `psycopg[binary]`, `gunicorn`
Dev: `django-debug-toolbar`, `pytest-django`, `ruff`

### Library Project

```
library-name/
├── pyproject.toml (hatchling build backend)
├── LICENSE
├── src/
│   └── library_name/
│       ├── __init__.py
│       ├── py.typed
│       └── core.py
└── tests/
    ├── __init__.py
    └── test_core.py
```

### CLI Project

Same as Library but with `[project.scripts]` entry and `typer` + `rich` dependencies.

### Generic Project

Minimal: `pyproject.toml`, `src/project_name/__init__.py`, `tests/`, `Makefile`.

## Step 4: Verify

After scaffolding, run verification:

```bash
cd [project root]
uv sync
uv run pytest -v
```

Present results:
```
Project [name] scaffolded successfully.

Files created: [count]
Dependencies installed: [count]
Tests: [pass/fail]

Next steps:
1. cd [project root]
2. uv sync
3. [type-specific start command]
```
