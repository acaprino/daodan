---
name: pydantic-v2
description: >
  Pydantic v2 models, validators, serialization, FastAPI schemas and v1-to-v2 migration.
  TRIGGER WHEN: writing or refactoring Pydantic v2 models in Python 3.10+, migrating from Pydantic v1, handling Decimal money fields, or designing FastAPI request/response schemas.
  DO NOT TRIGGER WHEN: Python testing (use pytest-patterns) or TypeScript schemas (use typescript-development).
---

# Pydantic v2

Pydantic v2 (current stable **2.13** as of 2026-04-19, paired with Python 3.10-3.14 including 3.14 free-threaded builds) is a rewrite on `pydantic-core` (Rust). Several v1 patterns silently break or behave differently.

Notable recent releases:
- **2.11** (2025): 2x schema build-time improvements, 2-5x memory reduction for nested models, PEP 695/696 generic syntax, experimental free-threaded Python 3.13, `validate_by_alias` / `validate_by_name` / `serialize_by_alias` config (`populate_by_name` pending v3 deprecation), `Path` and `deque` no longer accept constraints.
- **2.12**: Python 3.14 support (PEP 649/749 annotations), experimental `MISSING` sentinel, `exclude_if` on fields, `ensure_ascii` on JSON output, `serialize_as_any` unified behavior, `@model_validator(mode="after")` classmethod deprecated (write as instance method).
- **2.13** (April 2026): **Polymorphic serialization** (`model_dump(polymorphic_serialization=True)`), `exclude_if` extended to computed fields, `ascii_only` in `StringConstraints`, `model_fields_set` tracks post-instantiation extras.

## Reference router

Load only the reference your task needs:

| Task | Reference | Covers |
|---|---|---|
| Custom validators, `ValidationInfo`, `model_dump`, aliases, JSON Schema modes, discriminated unions | `references/validators-and-serialization.md` | Validator mode table (`after`/`before`/`wrap`/`plain`), `Annotated` validators, `PydanticCustomError`, serialization modes, custom serializers, input/output aliases |
| FastAPI endpoints, `pydantic-settings`, `Decimal` money fields, `SecretStr`, hot-path performance, Logfire/PydanticAI | `references/fastapi-and-performance.md` | CWE-681 monetary precision, `BaseSettings`, FastAPI `response_model` and 422 error envelopes, 12-point performance checklist, untrusted input bounds |
| Migrating a codebase from Pydantic v1 to v2 | `references/v1-to-v2-migration.md` | `bump-pydantic` usage, manual decorator/config/method replacements, what `bump-pydantic` misses, official links |

## Core model patterns

```python
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
    model_validator,
)

# Type aliases with constraints: preferred in v2 over constr() / conint()
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
USDAmount = Annotated[Decimal, Field(max_digits=14, decimal_places=2, ge=0)]

class LineItem(BaseModel):
    model_config = ConfigDict(
        strict=True,               # refuse string "1" for int field
        frozen=True,               # hashable + immutable
        validate_by_name=True,     # accept field name alongside alias (2.11+)
        validate_by_alias=True,
        str_strip_whitespace=True, # strip on all str fields
        extra="forbid",            # reject unknown keys
    )

    sku: NonEmptyStr
    quantity: int = Field(ge=1)
    unit_price: USDAmount
    currency: Literal["USD", "EUR", "GBP"] = "USD"

    @computed_field
    @property
    def total(self) -> USDAmount:
        return self.unit_price * self.quantity

    @field_validator("sku")
    @classmethod
    def sku_format(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("sku must be alphanumeric")
        return v.upper()

    @model_validator(mode="after")
    def cross_field_check(self) -> "LineItem":
        if self.currency == "USD" and self.unit_price > Decimal("10000"):
            raise ValueError("USD line item exceeds single-item limit")
        return self
```

### Key rules

- `model_config = ConfigDict(...)` replaces the v1 inner `class Config:` pattern.
- `Annotated[T, Field(...)]` or `Annotated[T, StringConstraints(...)]` is the idiomatic v2 way to attach constraints.
- `@computed_field` replaces the v1 `@property` + `validator(always=True)` pattern and appears in `model_dump()` automatically.
- `@field_validator("field_name")` replaces v1 `@validator("field_name")` and requires `@classmethod` below it.
- `@model_validator(mode="before" | "after")` replaces v1 `@root_validator`. In `mode="after"` the method is a plain instance method returning `self` (`@classmethod` on `mode="after"` is deprecated in 2.12+).
- Prefer `validate_by_alias` / `validate_by_name` / `serialize_by_alias` (2.11+) over legacy `populate_by_name=True`.
- `Path` and `deque` no longer accept `Field` constraints (2.11+): use a custom validator for length or pattern checks.

## Common gotchas

- **`strict=True` breaks JSON API query/path coercion**: FastAPI coerces `"1"` -> `1` for path/query params only when `strict` is not enabled globally. Apply `strict=True` selectively per field or per call.
- **`extra="forbid"` + evolving clients**: rejects unknown fields. Use `"forbid"` for internal contracts and `"ignore"` (default) for public ingress.
- **`extra="allow"` + `model_dump()`**: v2 excludes extras from dumps by default unless configured; 2.13 tracks post-instantiation extra assignments in `model_fields_set`.
- **`@computed_field` with expensive work**: runs on every `model_dump()`. Cache if expensive, or use a regular `@property` when it should not be serialized.
- **Frozen models are hashable**: use `model_copy(update={...})` to derive a modified instance.
- **Discriminator must be a `Literal`, not `str`**: `Field(discriminator="type")` requires each union member to declare `type: Literal["..."]`.
- **v2 does not validate on `__setattr__` by default**: set `ConfigDict(validate_assignment=True)` when mutating attributes after construction.
- **UTC / timezone handling**: `AwareDatetime` coerces naive input as local time then converts to UTC; `NaiveDatetime` rejects tz-aware input. 2.12 added explicit timestamp-unit control (`seconds` vs `ms`).
- **`model_dump()` is shallow**: mutating a nested custom object in the dumped dict mutates the model instance. Use `model.model_copy(deep=True).model_dump()` if downstream code mutates.
- **`Optional[X]` requires `= None`**: v2 requires an explicit default for optional fields (`field: str | None = None`).

## Integration

- Python architecture / API design with Pydantic v2 -> `python-development:python-engineer` agent
- Testing Pydantic models -> `python-development:pytest-patterns` skill
- FastAPI project scaffolding with v2 defaults -> `python-development:python-scaffold-method` skill (FastAPI type), reached through `/daodan:init-project` on an empty folder
- Monetary precision patterns -> `senior-review:defect-taxonomy` (CWE-681 / CWE-682)
- TypeScript equivalent (Zod / valibot) -> `typescript-development:mastering-typescript` skill
