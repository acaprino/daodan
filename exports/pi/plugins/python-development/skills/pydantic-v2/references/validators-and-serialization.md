<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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

# Pydantic v2 Validators, Serialization and Unions

On-demand reference for `python-development:pydantic-v2`.

## Validators

### Mode decision rules

| Mode | When to use | Performance | Returns |
|------|------------|-------------|---------|
| `after` (default) | 90% of cases: logic on already-coerced value | Fast | Same type as field |
| `before` | Reshape raw input (string split, legacy key mapping) | Python callback overhead | Any (type-coerced afterward) |
| `wrap` | Catch `ValidationError`, add logging, force `PydanticUseDefault` | Slowest: materializes data in Python | Same type as field |
| `plain` | Fully custom, no coercion, no downstream validators | N/A (terminates validation) | **Trusted as-is**: dangerous for type safety |

**Performance rule:** express constraints in `Field(...)` or `Annotated` metadata whenever possible so the Rust engine handles them. Python-level validators (`@field_validator`, `mode="before"`, `mode="wrap"`) incur per-value Python-call overhead.

### Field validators

```python
from pydantic import BaseModel, ValidationInfo, field_validator

class User(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str, info: ValidationInfo) -> str:
        # info.data: already-validated fields (in declaration order; cannot access later fields)
        # info.context: user-supplied dict via Model.model_validate(data, context={...})
        # info.mode: "python" | "json" | "strings"
        # info.field_name: the field being validated
        if len(v) < 12:
            raise ValueError("password must be at least 12 chars")
        return v
```

### Annotated validators (reusable pattern)

Prefer `Annotated` metadata over decorator validators when the same logic applies across multiple models:

```python
from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, WrapValidator, BaseModel

def lower(v: str) -> str:
    return v.lower()

def ensure_https(v: str) -> str:
    if not v.startswith("https://"):
        raise ValueError("URL must be https")
    return v

LowerStr = Annotated[str, AfterValidator(lower)]
HttpsUrl = Annotated[str, AfterValidator(ensure_https)]

class User(BaseModel):
    email: LowerStr
    avatar_url: HttpsUrl
```

**Ordering rule:** `Before` and `Wrap` validators run right-to-left; `After` validators run left-to-right; decorator-style `@field_validator`s are appended last.

### ValidationInfo and info.context

Stable API across 2.x. Context passes through to custom serializers (2.7+):

```python
user = User.model_validate(payload, context={"tenant_id": request.tenant_id})
# Inside a field_validator / model_validator / field_serializer:
#   info.context["tenant_id"] is available
```

Use context for tenant-aware validation, feature flags, or bypass switches, not for data that belongs on the model.

### Model validators

```python
@model_validator(mode="before")
@classmethod
def normalize_input(cls, data: dict) -> dict:
    # mode="before": classmethod, first arg cls, receives raw input (often dict)
    # Do NOT mutate then raise: mutations leak to downstream validators
    if isinstance(data, dict) and "userEmail" in data and "user_email" not in data:
        data["user_email"] = data.pop("userEmail")
    return data

@model_validator(mode="after")
def check_date_order(self) -> "Event":
    # mode="after": INSTANCE method (@classmethod deprecated in 2.12)
    # returns self, not a dict
    if self.start_date > self.end_date:
        raise ValueError("start_date must be <= end_date")
    return self
```

### Error customization

```python
from pydantic_core import PydanticCustomError

@field_validator("sku")
@classmethod
def sku_format(cls, v: str) -> str:
    if not v.isalnum():
        raise PydanticCustomError(
            "invalid_sku",              # machine-readable error type
            "{field} must be alphanumeric",  # template (formatted by Pydantic)
            {"field": "sku"},           # context dict
        )
    return v
```

- Raising `ValueError` auto-wraps into a Pydantic error (simplest path).
- Avoid `assert` (skipped under `python -O`).
- `loc` (error location) is determined by validator position; not user-editable at raise site.

### Inheritance

Base-class model validators run on subclass instances. Overriding in a subclass **replaces** (does not extend) the parent. Prefer composition via `Annotated` validators over deep inheritance.

## Serialization: `model_dump`, `model_dump_json`, `model_validate`

| v1 | v2 |
|----|----|
| `model.dict()` | `model.model_dump()` |
| `model.json()` | `model.model_dump_json()` |
| `Model.parse_obj(...)` | `Model.model_validate(...)` |
| `Model.parse_raw(...)` | `Model.model_validate_json(...)` |
| `Model.construct(...)` | `Model.model_construct(...)` |
| `Model.schema()` | `Model.model_json_schema()` |
| `Model.__fields__` | `Model.model_fields` |

### Serialization modes

```python
model.model_dump(mode="python")   # native Python types (Decimal stays Decimal)
model.model_dump(mode="json")     # JSON-compatible types (Decimal -> str, UUID -> str, datetime -> ISO)
model.model_dump(mode="strings")  # everything coerced to str (CSV / form encodings)

model.model_dump(exclude={"password_hash"})
model.model_dump(include={"id", "name"})
model.model_dump(exclude_none=True)
model.model_dump(by_alias=True)   # use field aliases as keys
model.model_dump(round_trip=True) # output can be fed back into model_validate

# 2.13+ polymorphic: subclass instances serialize by their actual type, exposing subclass-only fields
model.model_dump(polymorphic_serialization=True)
```

### Custom serializers

```python
from typing import Annotated
from pydantic import (
    BaseModel, field_serializer, model_serializer,
    PlainSerializer, SerializerFunctionWrapHandler,
)

class Order(BaseModel):
    total: Decimal
    created_at: datetime

    @field_serializer("total", when_used="json")
    def serialize_total(self, v: Decimal) -> str:
        return f"${v:.2f}"

    @model_serializer(mode="wrap")
    def add_envelope(self, handler: SerializerFunctionWrapHandler) -> dict:
        return {"version": 1, "data": handler(self)}

UsdAmount = Annotated[
    Decimal,
    PlainSerializer(lambda v: f"${v:.2f}", return_type=str, when_used="json"),
]
```

`when_used` values: `"always"` (default), `"json"`, `"json-unless-none"`, `"unless-none"`.

### JSON Schema modes

`model_json_schema(mode="validation" | "serialization")` returns different shapes:

```python
Model.model_json_schema(mode="validation")     # request shape: computed_fields absent, input-only aliases
Model.model_json_schema(mode="serialization")  # response shape: computed_fields required, output aliases
```

**FastAPI uses both:** validation mode for request schemas, serialization mode for response schemas. Pydantic v2 targets OpenAPI 3.1 natively.

### Aliases: three flavors

| Field arg | Affects |
|-----------|---------|
| `alias="x"` | Both validation input AND serialization output |
| `validation_alias="x"` | Input only |
| `serialization_alias="x"` | Output only |

Pydantic 2.11 added per-config control:

```python
class ApiResponse(BaseModel):
    model_config = ConfigDict(
        validate_by_alias=True,    # accept aliases in input
        validate_by_name=True,     # also accept field names in input
        serialize_by_alias=True,   # emit aliases in output
    )
    user_id: str = Field(alias="userId")
```

`populate_by_name` still works but is pending v3 deprecation.

### Fast JSON emission and round-tripping

```python
raw = model.model_dump_json()
raw_bytes = MyModel.__pydantic_serializer__.to_json(model)  # bytes directly from Rust
```

Cache `__pydantic_serializer__` at module scope for ultra-hot paths (SSE, WebSocket, bulk export). `model.model_dump(round_trip=True)` guarantees `Model.model_validate(dumped)` yields an equivalent instance for `RootModel`s, discriminated unions, and aliased fields.

## Discriminated unions

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

class EmailEvent(BaseModel):
    type: Literal["email"]
    to: str
    subject: str

class SmsEvent(BaseModel):
    type: Literal["sms"]
    to: str
    body: str

Event = Annotated[Union[EmailEvent, SmsEvent], Field(discriminator="type")]

class Envelope(BaseModel):
    id: str
    event: Event
```

Faster than v1 unions (`pydantic-core` picks the variant directly via the tag field) and produces cleaner error messages.
