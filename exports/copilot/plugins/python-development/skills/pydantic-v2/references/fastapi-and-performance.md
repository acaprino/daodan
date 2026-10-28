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

# Pydantic v2 FastAPI, Settings, Security and Performance

On-demand reference for `python-development:pydantic-v2`.

## Monetary precision (CWE-681 defense)

Never use `float` for money. Two idiomatic v2 options:

```python
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from typing import Annotated
from pydantic import BaseModel, Field, condecimal

getcontext().rounding = ROUND_HALF_EVEN  # banker's rounding for financial totals

# Option A (preferred): Annotated with Field constraints
USDAmount = Annotated[Decimal, Field(max_digits=14, decimal_places=2, ge=0)]

# Option B: condecimal() wrapper (still supported)
USDAmountV1Style = condecimal(max_digits=14, decimal_places=2, ge=0)

class Invoice(BaseModel):
    subtotal: USDAmount
    tax: USDAmount
    total: USDAmount
```

See `senior-review:defect-taxonomy` CWE-681 / CWE-682 for the full monetary-precision rules.

## Settings management (`pydantic-settings`)

v2 extracted settings into a separate package `pydantic-settings`:

```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
    )

    database_url: str
    stripe_secret_key: SecretStr  # redacted in repr / model_dump_json
    debug: bool = False
    port: int = Field(default=8000, ge=1, le=65535)

settings = AppSettings()
```

- `SecretStr` / `SecretBytes` hide the value in logs and tracebacks: use for every API key, password, or token.
- Reading the value: `settings.stripe_secret_key.get_secret_value()`.
- Source priority (high -> low): init args > env vars > `.env` file > defaults.

## FastAPI integration

### Response models

```python
from fastapi import FastAPI
from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    email: str

class UserDB(UserOut):
    password_hash: str  # server-side only, never exposed

app = FastAPI()

@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int) -> UserDB:
    # Returning the broader UserDB is fine; FastAPI projects through UserOut.
    return await fetch_user(user_id)
```

FastAPI uses `response_model` for serialization, stripping `password_hash`. Prefer this to manual dict construction.

### Request validation and custom error envelopes

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_failed",
            "details": exc.errors(),   # Pydantic v2 error format
            "request_id": request.headers.get("x-request-id"),
        },
    )
```

v2 error shape differs from v1 (`ctx`, `input`, and `url` fields changed). If you serialize errors to clients, pin the shape in an integration test.

### Streaming / long-lived response models

`model_dump_json()` is faster than `json.dumps(model.model_dump())` for streaming. For SSE / WebSocket, cache `MyModel.__pydantic_serializer__` and call `serializer.to_json(instance)`.

## Performance notes

Ordered guide from the official Pydantic Performance documentation:

1. **`model_validate_json(raw_bytes)` over `model_validate(json.loads(raw_bytes))`**: skips Python dict materialization; `pydantic-core` streams directly from bytes.
2. **Instantiate `TypeAdapter` at module scope**, never inside request handlers. Each instantiation rebuilds validators.
3. **Concrete types beat abstract ones**: `list[int]` beats `Sequence[int]`; `dict` beats `Mapping`.
4. **Discriminated unions >> untagged unions**: direct lookup via the tag field, no scoring of all variants.
5. **`TypedDict`** via `TypeAdapter` is ~2.5x faster than an equivalent nested `BaseModel` for pure-data shapes.
6. **Avoid wrap validators in hot paths**: they materialize data in Python.
7. **Core-side constraints (`Field(ge=...)`) >> Python `@field_validator`**: express ranges, lengths, regex patterns as metadata.
8. **`FailFast` annotation on sequences** (2.8+) stops validation on first failure instead of collecting all errors:
   ```python
   from typing import Annotated
   from pydantic import FailFast
   ids: Annotated[list[int], FailFast()]
   ```
9. **`cache_strings="all"` (default)**: Pydantic caches repeated strings across validation calls. Set to `"none"` only for adversarial input with high string entropy.
10. **`defer_build=True`** in `ConfigDict`: delay schema build until first validation. Useful when defining many models at import time. Harmful if you want startup-time errors on malformed schemas.
11. **`MyModel.__pydantic_serializer__.to_json(instance)`**: bytes fast-path for SSE / WebSocket / bulk export. Cache the serializer at module scope.
12. **`model_construct(**data)`**: skips all validation and coercion. Safe only for already-validated internal data; unsafe across trust boundaries.

### Free-threaded Python (3.13+) and `model_rebuild()`

- Pydantic 2.11 added experimental free-threaded (`nogil`) support; 2.12 ships official builds for Python 3.14 free-threaded.
- `model_rebuild()` is needed when a forward-referenced model is defined out of order. Never call it in a hot path (rebuilds the Rust schema from scratch).

## Security and secrets

```python
from pydantic import BaseModel, SecretStr

class Credentials(BaseModel):
    api_key: SecretStr

c = Credentials(api_key="sk-real-secret-123")
print(c)                   # api_key=SecretStr('**********')
print(c.model_dump_json()) # {"api_key":"**********"}
c.api_key.get_secret_value()  # real value, use only at the trusted sink
```

### Untrusted input safety

- `TypeAdapter.validate_python(untrusted)` has the same safety model as `BaseModel.model_validate`.
- `model_validate_json(raw_bytes)` streams through `pydantic-core` with built-in depth/size bounds; prefer over `json.loads` + `model_validate`.
- Deep recursive models: `pydantic-core` has Rust-side stack safety for JSON traversal, but Python-level validators at depth can still overflow. Cap recursion via a `mode="before"` validator that counts.
- Mutable nested objects in `model_dump()` output alias back to the model (shallow copy): use `model.model_copy(deep=True).model_dump()` when downstream code mutates.

## PydanticAI and Logfire

- **[Logfire](https://logfire.pydantic.dev/)**: `logfire.instrument_pydantic(record="failure")` traces failed validations in production; `logfire.instrument_pydantic_ai()` instruments PydanticAI agents end-to-end.
- **[PydanticAI](https://ai.pydantic.dev/)**: type-safe LLM agent framework built on Pydantic models with durable execution, built-in evals, MCP support, and Logfire tracing.
