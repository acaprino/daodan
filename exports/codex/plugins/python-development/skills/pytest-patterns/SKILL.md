---
name: pytest-patterns
description: >
  Python-specific pytest fixtures, async tests, parametrization, mocks and framework configuration.
  Load as technical context for testing:test-writer or Python development; universal test principles and TDD belong to testing.
---

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
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

# Python Testing Patterns

Generate focused, behavior-driven tests with pytest. Prioritize observable behavior over implementation details. For framework configuration (pyproject.toml, plugins, CI), see `references/framework-config.md`. For deep conftest patterns and heavy-dep mocking, see `references/pytest-infrastructure.md`. For authoring and TDD, use the canonical testing owner.

## Canonical authoring owner

Load the `testing:test-hygiene` skill for placement, prevention and meaningful test protection.
Delegate test authoring to `testing:test-writer`, supplying these Python techniques
as context. Load the `testing:test-remediation-method` skill for existing failures before
changing assertions. TDD discipline belongs to testing's declared upstream skill.
This skill owns pytest mechanics, not another test philosophy or coverage quota.
Independent exact expected values are valid when justified by the contract;
never derive the oracle from the tested implementation or weaken it to get green.

## 3. Naming Convention (BDD)

**Class-based grouping** -- nest by feature, then scenario:

```python
class TestUserService:
    class TestCreateUser:
        def test_should_create_when_valid_data(self): ...
        def test_should_raise_when_email_exists(self): ...
```

**Flat function naming** -- `test_<action>_should_<outcome>_when_<condition>`:

```python
def test_create_user_should_succeed_when_valid_data(): ...
def test_login_should_fail_when_password_expired(): ...
```

## 4. AAA Structure (Arrange-Act-Assert)

```python
def test_transfer_should_debit_sender_when_sufficient_funds():
    # Arrange
    sender = make_account(balance=100)
    receiver = make_account(balance=50)

    # Act
    transfer(sender, receiver, amount=30)

    # Assert
    assert sender.balance == 70
    assert receiver.balance == 80
```

## 5. Reusable Fakes via Factory Fixtures

Prefer factory fixtures in `conftest.py` over raw dicts:

```python
# conftest.py
@pytest.fixture
def make_user():
    def _make_user(name="Test User", email="test@example.com", active=True):
        return User(name=name, email=email, active=active)
    return _make_user

def test_deactivate_user(make_user):
    user = make_user(active=True)
    user.deactivate()
    assert user.active is False
```

## 6. Core Patterns (the few worth memorizing)

### Fixtures -- narrowest scope possible

```python
@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture(scope="module")  # or scope="session" for engine
def api_client(): yield TestClient(app)
```

Share via `conftest.py` -- pytest auto-discovers.

### Parametrization with custom IDs

```python
@pytest.mark.parametrize("input_val,expected", [
    pytest.param("user@example.com", True, id="valid-email"),
    pytest.param("no-at-sign.com", False, id="missing-at"),
    pytest.param("", False, id="empty-string"),
])
def test_is_valid_email(input_val, expected):
    assert is_valid_email(input_val) == expected
```

### Mocking -- the only patterns you need

```python
@patch("myapp.services.requests.get")                      # patch where USED (top-level import)
def test_fetch_user(mock_get):
    mock_get.return_value.json.return_value = {"id": 1}
    result = fetch_user(1)
    mock_get.assert_called_once_with("https://api.example.com/users/1")

@patch("myapp.services.UserRepository", autospec=True)     # autospec catches signature drift
def test_repo_call(MockRepo): ...

@patch("myapp.client.requests.get", side_effect=ConnectionError("timeout"))
def test_network_error(mock_get):
    with pytest.raises(ServiceUnavailableError):
        fetch_data("https://api.example.com/data")
```

### The lazy-import gotcha (the rule that catches everyone)

When a function imports inside another function (lazy import), it is NOT a module-level attribute at the usage site. **Patch at the definition site, not the usage site.**

```python
# WRONG -- AttributeError: module has no attribute 'get_db'
monkeypatch.setattr("myapp.services.processor.get_db", mock_db)

# CORRECT -- patch where get_db is DEFINED
monkeypatch.setattr("myapp.database.get_db", mock_db)
```

Rule: if `monkeypatch.setattr` raises `AttributeError`, check whether the target is a lazy import. If so, patch the module where the function is defined.

### Async tests

```python
@pytest.mark.asyncio
async def test_async_fetch():
    result = await async_fetch("https://api.example.com")
    assert result["status"] == "ok"
```

Set `asyncio_mode = "auto"` in `pyproject.toml` to skip the `@pytest.mark.asyncio` decorator.

### Property-based with hypothesis

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=1000))
def test_deposit_increases_balance(amount):
    account = Account(balance=0)
    account.deposit(amount)
    assert account.balance == amount
```

### Temporary files / env

```python
def test_export(tmp_path):                             # auto-cleaned
    output = tmp_path / "report.csv"
    export_report(output, [{"name": "Alice"}])
    assert "Alice" in output.read_text()

def test_db_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    assert get_database_url() == "postgresql://localhost/test"
```

## 7. Pytest technique pitfalls

| Anti-pattern | Why it's bad | Do this instead |
|--------------|--------------|-----------------|
| `assert obj is not None` alone | Asserts nothing about behavior | Assert on a specific attribute or return value |
| Mocking the function under test | Tests nothing real | Mock its dependencies instead |
| Testing framework internals | Validates pytest/SQLAlchemy, not your code | Test your logic through public API |
| Copy-pasting mock setup in every test | Fragile, hard to maintain | Extract into fixtures or factory functions |
| Testing private methods directly | Couples tests to implementation | Test through the public interface |
| Catching exceptions inside test code | Swallows real failures silently | Use `pytest.raises` as context manager |
| No assertions in test body | Test always passes, proves nothing | Every test must assert something |
| Asserting on `mock.called` only | Doesn't verify correct arguments | Use `assert_called_once_with(expected_args)` |
| Heavy mocks in sub-directory conftest | Root tests load real deps first; mocks too late | Place ALL heavy dependency mocks in root `tests/conftest.py` |
| Missing markers on heavy-dep tests | Tests break silently when deps are mocked by default | Mark `@pytest.mark.slow`, use `--strict-markers` |
| Incomplete external service mocking | One unmocked service hangs CI (e.g., `google.auth.default()`) | Audit ALL external calls before finalizing integration conftest |
| Patching lazy import at use site | Function not bound at module level | Patch at definition site (see Core Patterns above) |

## 8. Pytest Infrastructure (the load-bearing rules)

### conftest execution order

Root `tests/conftest.py` runs **FIRST**. Sub-directory conftest files run only when their tests are collected.

**Heavy mocks go in root conftest.** If you mock ortools, scipy, prometheus_client, or any large native dependency, do it in root `tests/conftest.py`. Sub-directory conftest mocks are too late -- collection-time imports already loaded the real module.

```python
# tests/conftest.py (ROOT -- runs first, before any test collection)
import sys
from unittest.mock import MagicMock

for _mod in ("ortools", "ortools.sat.python.cp_model",
             "scipy", "scipy.optimize", "prometheus_client"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
```

### External service mock completeness

Every external service the app uses must have a mock in the integration conftest:

| Service | What to mock | Why |
|---------|--------------|-----|
| Database | connection / session | Real DB not in CI |
| Auth | token verification | No auth server in tests |
| Cloud storage | upload / download | `google.auth.default()` hangs |
| Email | send functions | Sends real emails |
| Payment | charge / refund | Hits real API |

Audit: grep production code for external service imports; verify each has a mock.

### Marker discipline

Tests requiring real heavy dependencies (scipy.optimize, real DB, ML models) MUST be marked:

```python
pytestmark = pytest.mark.slow                  # module-level

@pytest.mark.slow                              # per-test or per-class
class TestPortionSolver: ...
```

A fast local command may select `-m "not slow and not e2e"`; required slow/service lanes stay explicit in the candidate gate and cannot be silently omitted.

For full conftest+sys.modules race + environment-safety patterns, see `references/pytest-infrastructure.md`.

## References

- `references/framework-config.md` -- pytest config, plugins, CI/CD
- `references/pytest-infrastructure.md` -- conftest ordering, heavy-dep mocking, mock target decision tree, external service audit
- pytest docs: https://docs.pytest.org/
- unittest.mock docs: https://docs.python.org/3/library/unittest.mock.html
- hypothesis docs: https://hypothesis.readthedocs.io/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
