<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

# uv Package Manager Reference

`uv` (Astral) is a Rust-rewritten replacement for pip / pip-tools / pipx / virtualenv / pyenv. Most surface lives at https://docs.astral.sh/uv; this file is the recommended workflows + the gotchas + the migration story.

## When to use

Setting up a new Python project with `uv`, migrating from pip / poetry, or wiring `uv` into CI/CD and Docker. For the architectural opinions (when to migrate, lockfile policy), see `uv-package-manager/SKILL.md`.

## The commands you'll actually use daily

| Task | Command |
|------|---------|
| New project | `uv init my-project` |
| Add a dep | `uv add requests` |
| Add a dev dep | `uv add --dev pytest` |
| Add an optional group | `uv add --optional docs sphinx` |
| Sync from lockfile | `uv sync` |
| Sync with dev + extras | `uv sync --all-extras --dev` |
| Run a command in the env | `uv run pytest` |
| Run a script with inline deps | `uv run script.py` |
| Install a tool globally | `uv tool install ruff` |
| Pin Python version | `uv python install 3.12` then `uv python pin 3.12` |
| Rebuild lockfile from scratch | `uv lock --upgrade` |

## Gotchas

- **`uv.lock` is the source of truth in CI** -- always pass `--frozen` to `uv sync` so CI fails if the lockfile is out of date instead of silently regenerating it. Without `--frozen`, "works on my machine" lockfile drift goes undetected.
- **`uv venv` creates `.venv` automatically** at project root -- don't fight it. If you want a custom location, set `UV_PROJECT_ENVIRONMENT=/path/to/venv`.
- **`uv sync` removes packages not in the lockfile**, including ones you `pip install`-ed manually. This is intentional; if you need ad-hoc packages, `uv add` them or use `uv run --with`.
- **`uv add --dev` writes to `[tool.uv.dev-dependencies]` (NOT `[project.optional-dependencies].dev`)** -- the two are separate by design. Optional groups are user-installable; dev deps are project-internal.
- **`uv pip install` works** for pip-compatible workflows, but does NOT update `pyproject.toml` or the lockfile. Use only for one-off installs in throwaway venvs.
- **Workspaces** (`[tool.uv.workspace]`) are uv-specific -- they share a single lockfile across multi-package monorepos. `uv add --path ./packages/foo` for cross-package deps.
- **`uv tool install` is the modern pipx**. Tools live in isolated venvs under `~/.local/share/uv/tools/`. Use `uv tool run <tool>` (or `uvx <tool>`) for one-shot runs without persistent install.
- **Python version pinning**: `uv python pin 3.12` writes `.python-version`. CI: `uv python install 3.12` ensures it's available. uv manages Python interpreters itself -- no need for pyenv.
- **`uv sync --frozen --no-dev`** in production Dockerfiles -- skip dev deps, fail on stale lock.
- **Cache location**: `~/.cache/uv/` (Linux/macOS), `%LOCALAPPDATA%\uv\cache\` (Windows). `uv cache prune` cleans unreferenced entries.

## CI/CD pattern (GitHub Actions)

```yaml
- uses: actions/checkout@v4
- uses: astral-sh/setup-uv@v2
  with: { enable-cache: true }
- run: uv python install 3.12
- run: uv sync --all-extras --dev --frozen      # <-- --frozen is the key flag
- run: uv run pytest
- run: uv run ruff check .
```

`astral-sh/setup-uv@v2` handles caching automatically. With `enable-cache: true`, the `~/.cache/uv` lookup is keyed on `uv.lock`.

## Docker pattern (multi-stage, prod-ready)

```dockerfile
# Stage 1: build deps with uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project    # deps only, no app code

# Stage 2: runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "my_package"]
```

`--no-install-project` skips installing the project code itself -- the next stage adds it. This way Docker layer cache only invalidates on dep changes, not source changes.

## Workspace (monorepo) layout

```
monorepo/
├── pyproject.toml                   # root: declares workspace
├── uv.lock                          # ONE shared lockfile
├── packages/
│   ├── package-a/
│   │   └── pyproject.toml
│   └── package-b/
│       └── pyproject.toml
```

Root `pyproject.toml`:
```toml
[tool.uv.workspace]
members = ["packages/*"]
```

In `package-b/pyproject.toml`, depend on package-a:
```toml
dependencies = ["package-a"]

[tool.uv.sources]
package-a = { workspace = true }
```

`uv sync` from root installs both packages in editable mode against the shared `.venv`.

## Migration from pip / poetry / pipenv

| From | Migration step |
|------|----------------|
| **pip + requirements.txt** | `uv init`, then `uv add $(cat requirements.txt)`. Move dev deps via `uv add --dev`. |
| **poetry** | `uv init`, copy `[tool.poetry.dependencies]` deps to `[project.dependencies]`, run `uv lock`. Poetry's `^` becomes `>=` (or pin manually). |
| **pipenv** | `uv init`, port `[packages]` and `[dev-packages]` from Pipfile to `[project.dependencies]` / `[tool.uv.dev-dependencies]`. |
| **pyenv** | `uv python install <version>` replaces pyenv. `.python-version` is shared with pyenv -- works in both. |
| **pipx** | `uv tool install <tool>` replaces pipx. Tools live under `~/.local/share/uv/tools/`. |

## Inline script metadata (PEP 723)

uv can run a single script with inline dep declarations:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "rich"]
# ///

import requests
from rich import print
print(requests.get("https://httpbin.org/json").json())
```

`uv run script.py` resolves and installs deps in a one-shot venv. Great for tutorials, gists, throwaway tools.

## Performance notes (why people switch)

- 10-100× faster than pip for resolution + install (Rust + parallel)
- Single binary, no Python required to run uv itself
- One unified lockfile vs poetry/pipenv's varied formats
- Native virtualenv management (no need for separate `python -m venv`)

## Official docs

- uv home: https://docs.astral.sh/uv/
- Project structure: https://docs.astral.sh/uv/concepts/projects/
- Workspaces: https://docs.astral.sh/uv/concepts/projects/workspaces/
- Tools (pipx replacement): https://docs.astral.sh/uv/concepts/tools/
- Python interpreter management: https://docs.astral.sh/uv/concepts/python-versions/
- Lockfile format: https://docs.astral.sh/uv/concepts/projects/sync/
- pip interface (compat): https://docs.astral.sh/uv/pip/
- GitHub Actions: https://docs.astral.sh/uv/guides/integration/github/
- Docker: https://docs.astral.sh/uv/guides/integration/docker/
- PEP 723 (inline script metadata): https://peps.python.org/pep-0723/

## Related

- `uv-package-manager/SKILL.md` -- the architectural opinions and migration playbook
- `python-packaging/references/packaging-guide.md` -- the publish side that uv supports via `uv build` + `uv publish`
- `pytest-patterns/references/framework-config.md` -- pytest config in the same `pyproject.toml`
