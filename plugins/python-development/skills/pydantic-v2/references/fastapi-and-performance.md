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
