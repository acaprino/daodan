---
name: python-scaffold-method
description: >
  Generate a fresh project skeleton, tests and lint config included.
  TRIGGER WHEN: `/daodan:init-project` runs on an empty folder and the user wants a Python project, or the user asks to start a new Python project, bootstrap FastAPI/Django/CLI/library structure, or set up uv+pytest+ruff from scratch.
  DO NOT TRIGGER WHEN: adding to an existing project (use python-engineer).
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
