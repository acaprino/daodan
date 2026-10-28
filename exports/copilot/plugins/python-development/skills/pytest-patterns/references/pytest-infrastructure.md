<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# Pytest Infrastructure Patterns

Patterns for test infrastructure that prevent environment hangs, mock ordering bugs, and incomplete service isolation.

## 1. Conftest Execution Order

### How pytest discovers conftest files

pytest processes conftest.py files top-down by directory depth:

1. `tests/conftest.py` (root) -- runs FIRST
2. `tests/unit/conftest.py` -- runs when unit/ tests are collected
3. `tests/unit/handlers/conftest.py` -- runs when handlers/ tests are collected

### The sys.modules race condition

```
tests/
  conftest.py                  # (A) runs FIRST -- but has NO heavy mocks
  test_csp_ortools.py          # (B) collected EARLY -- triggers `import ortools` at collection time
  unit/
    conftest.py                # (C) runs SECOND -- tries to mock ortools, but sys.modules already has real ortools
    test_optimizer.py
```

Step by step:
1. pytest discovers `tests/conftest.py` (A) and executes it
2. pytest collects `tests/test_csp_ortools.py` (B) -- Python executes module-level imports, loading real `ortools` into `sys.modules`
3. pytest discovers `tests/unit/conftest.py` (C) and executes it -- the guard `if "ortools" not in sys.modules` sees the real module and skips mocking
4. Tests fail because they get the real module instead of the mock

### Rule: All heavy mocks in root conftest

```python
# tests/conftest.py (ROOT -- runs first, before any test collection)
import sys
from unittest.mock import MagicMock

# Mock heavy native deps BEFORE any test file imports them
for _mod in ("ortools", "ortools.sat", "ortools.sat.python", "ortools.sat.python.cp_model",
             "scipy", "scipy.optimize", "prometheus_client"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
```

## 2. Heavy Native Dependency Strategy

### Dependencies that require mocking by default

| Category | Examples | Risk |
|----------|----------|------|
| Scientific computing | scipy, ortools, numpy (heavy parts) | Import hang, slow init |
| ML frameworks | torch, tensorflow, transformers | GPU init, massive import time |
| Monitoring | prometheus_client, opentelemetry | Global state, collectors |
| Cloud SDKs | google.cloud.*, boto3, firebase_admin | Auth checks, credential subprocess |

### Opting in to real deps

Tests needing the real dependency must be marked:

```python
pytestmark = pytest.mark.slow

# or per-test:
@pytest.mark.slow
def test_optimization_with_real_scipy():
    from scipy.optimize import minimize
    result = minimize(objective, x0)
    assert result.success
```

Default `addopts` in pyproject.toml: `-m 'not slow and not e2e'`

## 3. Platform and Environment Safety

### Known platform traps

| Trap | Environment | Symptom |
|------|-------------|---------|
| `platform._wmi_query()` | Python 3.13 + Windows 11 | Infinite hang before conftest |
| `google.auth.default()` | No gcloud credentials | Subprocess hang |
| `subprocess.run("gcloud ...")` | CI without SDK | Timeout |

### Pre-pytest monkey-patching

```python
# run_tests.py -- execute BEFORE pytest.main()
import platform
# Prevent WMI hang on Windows 11 + Python 3.13
if hasattr(platform, "_wmi_query"):
    platform._wmi_query = lambda *a, **kw: ""

import pytest
sys.exit(pytest.main(sys.argv[1:]))
```

### conftest.py is too late for plugin-level calls

Plugins like pyreadline3 and pytest-metadata execute during pytest's own initialization, before any conftest.py runs. If they call `platform.platform()` or `platform.processor()`, conftest cannot intercept them. The only fix is a test runner wrapper.

## 4. Mock Target Decision Tree

### Standard import (module-level)

```python
# app/services/user_service.py
from app.clients.stripe import charge_customer  # module-level import

# Test: patch where USED
@patch("app.services.user_service.charge_customer")
```

### Lazy import (inside function)

```python
# app/services/user_service.py
def process_payment():
    from app.clients.stripe import charge_customer  # lazy import
    return charge_customer(...)

# Test: patch where DEFINED
@patch("app.clients.stripe.charge_customer")
```

### Decision rule

1. Find the import statement for the dependency
2. Is it at module top-level? -- Patch where used (the importing module)
3. Is it inside a function body? -- Patch where defined (the source module)
4. If `monkeypatch.setattr` raises AttributeError -- the target is a lazy import, switch to definition site

## 5. External Service Audit Checklist

Before finalizing an integration test conftest, enumerate every external service:

- [ ] Database connections (MongoDB, PostgreSQL, Redis)
- [ ] Authentication providers (Firebase Auth, Auth0, OAuth)
- [ ] Cloud storage (Firebase Storage, S3, GCS)
- [ ] Message queues (RabbitMQ, Kafka, SQS)
- [ ] Payment processors (Stripe, PayPal)
- [ ] Email/SMS services (SendGrid, Twilio)
- [ ] Search engines (Elasticsearch, Algolia)
- [ ] Monitoring/telemetry (Prometheus, DataDog, Sentry)
- [ ] External APIs (Google Maps, OpenAI, etc.)

For each, verify the mock exists in conftest and uses `autouse=True`.

### Audit technique

```bash
# Find all external service imports in the app
grep -rn "import.*firebase\|import.*google\|import.*boto3\|import.*stripe\|import.*mongo\|import.*redis" src/
```

Cross-reference against conftest mocks. Every match must have a corresponding mock.
