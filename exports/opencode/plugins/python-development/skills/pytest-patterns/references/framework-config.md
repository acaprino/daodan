<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Framework Configuration

pytest + coverage + plugins + CI integration. Most surface lives in pytest/coverage docs; this file is the recommended baseline shape and project-configurable measurement conventions.

## When to use

Setting up `pyproject.toml` for a new Python project's test suite, or auditing an existing test config for missing essentials (markers registered, branch coverage, fail-under threshold, parallel execution).

## Recommended `pyproject.toml` baseline

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests",
    "unit: marks unit tests",
    "e2e: marks end-to-end tests",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/migrations/*", "*/__main__.py", "*/conftest.py"]

[tool.coverage.report]
show_missing = true
skip_empty = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
    "@overload",
]
```

## Gotchas

- **`--strict-markers` is non-negotiable** -- without it, typos in `@pytest.mark.foo` silently pass instead of erroring. Every marker must be registered in `markers`.
- **`branch = true` matters more than line coverage.** Catches untested conditionals (the `if x:` where you never tested the false branch). Always set it.
- **`filterwarnings = ["error", ...]`** turns warnings into failures by default -- you opt back in for known noise. Without `error`, deprecation traps land in production.
- **Coverage thresholds are project policy**, configured consistently when the project requires them. No percentage proves preservation of meaningful behavior; protect the approved failure-mode inventory independently.
- **`exclude_lines` for `if TYPE_CHECKING:` and `@overload`** -- otherwise import-time-only code shows as uncovered.
- **`ignore_errors` and `pragma: no cover` are easy to abuse** -- audit them periodically. They hide real coverage gaps.
- **`pytest-randomly`** is the cheapest way to catch hidden test interdependencies (tests passing only because of run order). Add it day one.
- **`pytest-asyncio` mode**: in `[tool.pytest.ini_options]` set `asyncio_mode = "auto"` if you want async test functions auto-detected; otherwise decorate with `@pytest.mark.asyncio`.

## Marker patterns

```bash
pytest -m unit                          # only unit tests
pytest -m "not slow"                    # skip slow
pytest -m integration                   # only integration
pytest -m "not e2e"                     # exclude e2e
pytest -k "test_login or test_signup"   # name-based selection (not marker)
```

## Plugin selector (the curated list)

| Plugin | Purpose |
|--------|---------|
| `pytest-cov` | Coverage reporting |
| `pytest-asyncio` | Async test support |
| `pytest-mock` | Thin `unittest.mock` wrapper with cleanup |
| `hypothesis` | Property-based testing |
| `pytest-xdist` | Parallel test execution (`-n auto`) |
| `pytest-randomly` | Randomize test order (catches order dependencies) |
| `pytest-timeout` | Per-test timeouts (kills hung tests in CI) |
| `pytest-sugar` | Better terminal output |

Select the plugins required by the project; example installation: `uv add --dev pytest-cov pytest-asyncio pytest-mock hypothesis pytest-xdist pytest-randomly pytest-timeout`

## CI metrics worth tracking

| Metric | Target | Tool |
|--------|--------|------|
| Line coverage | Descriptive; project policy if defined | pytest-cov + coverage.py |
| Branch coverage | Descriptive; examine meaningful branches | coverage.py with `branch = true` |
| Coverage delta | Investigate changed protection; not equivalence | Codecov PR comments |
| Test execution time | < 5 min | `pytest --durations=10`, pytest-timeout |
| Flaky test count | 0 | pytest-randomly + CI history |

## Version floor

| Tool | Min | Notes |
|------|-----|-------|
| Python | 3.11+ | 3.12+ recommended for improved error messages |
| pytest | 8.0+ | Improved assertion introspection |
| pytest-cov | 5.0+ | Latest coverage.py support |
| coverage.py | 7.0+ | Branch coverage improvements |
| pytest-asyncio | 0.23+ | Auto mode |
| hypothesis | 6.90+ | Python 3.12+ support |
| pytest-xdist | 3.5+ | Load balancing |

## Official docs

- pytest config reference: https://docs.pytest.org/en/stable/reference/customize.html
- pytest markers: https://docs.pytest.org/en/stable/example/markers.html
- coverage.py config reference: https://coverage.readthedocs.io/en/latest/config.html
- coverage.py exclude_lines: https://coverage.readthedocs.io/en/latest/excluding.html
- pytest-cov: https://pytest-cov.readthedocs.io/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- pytest-xdist: https://pytest-xdist.readthedocs.io/
- pytest-randomly: https://github.com/pytest-dev/pytest-randomly
- hypothesis: https://hypothesis.readthedocs.io/
- Codecov: https://docs.codecov.com/

## Related

- Load the `testing:test-hygiene` skill for canonical principles and use `testing:test-writer` for authoring; this reference owns Python configuration mechanics.
- `pytest-infrastructure.md` -- conftest patterns, fixture scoping, sys.modules race
- `python-comments` skill -- pairs well via the `D` ruff rule set for docstring coverage
