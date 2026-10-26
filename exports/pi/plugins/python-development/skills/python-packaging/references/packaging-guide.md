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

# Python Packaging Reference

`pyproject.toml` shape, src-layout, build/publish flow, and the gotchas that bite when distributing to PyPI. The full PEP 621 metadata schema lives upstream; this file is the recommended baseline + the trip-wires.

## When to use

Setting up a new Python package for distribution, or auditing an existing `pyproject.toml`. For decision-tree (when to package vs ship as a private repo), see `python-packaging/SKILL.md`.

## Recommended `pyproject.toml` baseline

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-awesome-package"
version = "1.0.0"
description = "An awesome Python package"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [{name = "Your Name", email = "you@example.com"}]
keywords = ["example", "package"]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "requests>=2.28.0,<3.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=7", "pytest-cov", "ruff", "mypy"]
docs = ["sphinx>=5", "sphinx-rtd-theme"]

[project.urls]
Homepage = "https://github.com/username/repo"
Repository = "https://github.com/username/repo"
"Bug Tracker" = "https://github.com/username/repo/issues"

[project.scripts]
my-cli = "my_package.cli:main"

[tool.setuptools]
package-dir = {"" = "src"}                  # src-layout
zip-safe = false

[tool.setuptools.packages.find]
where = ["src"]
include = ["my_package*"]

[tool.setuptools.package-data]
my_package = ["py.typed", "*.pyi", "data/*.json"]
```

## Gotchas (the trip-wires)

- **Always use src-layout** (`src/my_package/`), never flat layout (`my_package/` at repo root). Flat layout means `pip install -e .` plus a stale local import can shadow the installed package, leading to "tests pass locally, fail in CI" mysteries.
- **`py.typed` marker file** is required for downstream type checkers to honor your annotations. Add an empty `py.typed` to your package dir AND list it in `package-data`. PEP 561.
- **`license = {text = "MIT"}` vs `license = {file = "LICENSE"}`** -- newer setuptools prefers `text` for SPDX identifiers; `file` includes the LICENSE file content. Don't mix them.
- **Version conflicts**: `dependencies = ["requests>=2.28.0,<3.0.0"]` -- always pin upper-bounds for runtime deps to avoid breaking when a dep majors. Loose `>=` is the leading cause of "worked yesterday" issues.
- **`requires-python = ">=3.11"`** matters: pip uses it to skip the package on incompatible Pythons. Forgetting this means users on 3.9 get the wheel and crash on import.
- **Build backend choice**: `setuptools` (default), `hatchling` (modern, simpler), `flit_core` (minimal pure-Python), `pdm-backend`, `poetry-core`. Pick one and stick with it. Mixing backends across a monorepo is friction.
- **`twine check dist/*`** before `twine upload`. Catches malformed README rendering, missing classifiers, and other PyPI-rejection issues before you publish.
- **Test on TestPyPI first** (`twine upload --repository testpypi dist/*`). PyPI uploads are immutable -- you cannot delete or replace a version, only yank it.
- **Use API tokens, not passwords** for PyPI uploads. Configure in `~/.pypirc` or via `TWINE_PASSWORD` env var.
- **Wheels and sdists**: `python -m build` produces both. Wheels (`.whl`) are pre-built for fast install; sdist (`.tar.gz`) is the source fallback. Always ship both.

## Build + publish (the canonical flow)

```bash
# Modern: PEP 517 build
pip install build twine
python -m build                            # produces dist/*.whl + dist/*.tar.gz
twine check dist/*                         # verify before upload
twine upload --repository testpypi dist/*  # test first
twine upload dist/*                        # publish to PyPI
```

For uv users, replace `pip install build twine` with `uv tool install build twine`.

## src-layout structure

```
my-awesome-package/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── py.typed                       # PEP 561 marker
│       ├── core.py
│       └── cli.py
└── tests/
    ├── test_core.py
    └── test_cli.py
```

Then `pip install -e ".[dev]"` installs editable + dev deps.

## Versioning conventions

| Strategy | Use |
|----------|-----|
| **Semantic versioning** (semver) | Public APIs, libraries -- MAJOR.MINOR.PATCH |
| **CalVer** (e.g. 2026.4.26) | Apps, end-user tools where API stability isn't promised |
| **Pre-release** (1.0.0a1, 1.0.0b1, 1.0.0rc1) | Alpha / beta / RC channels |
| **Post-release** (1.0.0.post1) | Metadata-only fixes (typo in README, wrong classifier) |

PyPI accepts PEP 440 versions only -- `1.0.0-rc1` is invalid; use `1.0.0rc1`.

## Common classifiers (the few you need)

```toml
classifiers = [
    "Development Status :: 4 - Beta",       # 1=Planning, 4=Beta, 5=Production/Stable
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries",
    "Typing :: Typed",                      # if you ship type hints
]
```

Full list: https://pypi.org/classifiers/.

## Entry points (CLI commands + plugin systems)

```toml
[project.scripts]
my-cli = "my_package.cli:main"              # `my-cli` command runs my_package.cli.main()

[project.entry-points."my_package.plugins"]
plugin1 = "my_package.plugins:plugin1"      # plugin discovery via importlib.metadata
```

## Trusted publishing (the modern PyPI auth)

For GitHub Actions, configure **trusted publishing** in PyPI project settings -- no API token needed, uses OIDC. Workflow:

```yaml
- uses: pypa/gh-action-pypi-publish@release/v1
```

Requires PyPI project to have the GH org/repo/workflow registered. Token-free, audit-friendly.

## Official docs

- PEP 621 (pyproject.toml `[project]` table): https://peps.python.org/pep-0621/
- PEP 517 (build backends): https://peps.python.org/pep-0517/
- PEP 561 (`py.typed` marker): https://peps.python.org/pep-0561/
- PEP 440 (version specifiers): https://peps.python.org/pep-0440/
- packaging.python.org tutorials: https://packaging.python.org/en/latest/tutorials/packaging-projects/
- setuptools `pyproject.toml`: https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html
- hatchling: https://hatch.pypa.io/latest/config/build/
- flit_core: https://flit.pypa.io/
- twine: https://twine.readthedocs.io/
- `python -m build`: https://build.pypa.io/
- TestPyPI: https://test.pypi.org/
- PyPI trusted publishers: https://docs.pypi.org/trusted-publishers/
- PyPI classifiers: https://pypi.org/classifiers/

## Related

- `python-packaging/SKILL.md` -- decision tree (when to package, src vs flat, build backend choice)
- `uv-package-manager` skill -- modern dep management that pairs with this
- `pytest-patterns/references/framework-config.md` -- pytest config that lives in the same `pyproject.toml`
