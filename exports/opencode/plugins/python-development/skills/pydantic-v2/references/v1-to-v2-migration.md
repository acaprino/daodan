<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
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

# Pydantic v1 to v2 Migration Checklist and References

On-demand reference for `python-development:pydantic-v2`.

## v1 -> v2 migration checklist

Run `bump-pydantic` for the mechanical transforms:

```bash
uvx bump-pydantic src/
```

Then handle the cases the tool cannot convert automatically:

- `@validator` -> `@field_validator` + `@classmethod` decorator above the validator
- `@root_validator(pre=True)` -> `@model_validator(mode="before")`, method is classmethod, first arg is `cls`, takes raw dict
- `@root_validator` (no pre) -> `@model_validator(mode="after")`, method **returns `self`** and is a **plain instance method** (2.12+ deprecated the classmethod form)
- `Config.allow_population_by_field_name` -> `ConfigDict(validate_by_name=True)` (and `validate_by_alias=True`, `serialize_by_alias=True` as needed). The older `populate_by_name=True` still works but is pending v3 deprecation
- `Config.orm_mode` -> `model_config = ConfigDict(from_attributes=True)`
- `Config.schema_extra` -> `model_config = ConfigDict(json_schema_extra={...})`
- `Config.extra = "allow"|"forbid"|"ignore"` -> `ConfigDict(extra=...)`
- `parse_obj` -> `model_validate`; `parse_raw` -> `model_validate_json`; `dict()` -> `model_dump()`; `json()` -> `model_dump_json()`
- Generic `BaseModel[T]`: v2 uses native Python generics, not `GenericModel`; PEP 695 syntax supported since 2.11
- `Field(..., env="FOO")` in settings -> moved to `pydantic-settings` package (`BaseSettings` is no longer in `pydantic`)
- `__fields__` -> `model_fields` (the shape changed: `FieldInfo` objects, not `ModelField`)
- `__root__` model -> use `RootModel[T]` (`from pydantic import RootModel`)
- `Optional[X] = None`: v1 allowed no default on `Optional`, v2 requires an explicit `= None` default to be optional
- `smart_union`: default behavior in v2; old `smart_union=True` is a no-op
- `ValidationError.errors()` format changed (`msg`, `type`, `loc`, `input`, `ctx`, `url`): regenerate any error-envelope tests
- `parse_obj_as(list[Foo], data)` -> `TypeAdapter(list[Foo]).validate_python(data)` (instantiate adapter at module scope)

### What `bump-pydantic` misses

Requires manual conversion:

- Custom `__get_validators__` / `__modify_schema__` -> `__get_pydantic_core_schema__` + `__get_pydantic_json_schema__`
- `each_item=True` validators on sequence fields
- Custom `json_encoders` in `Config` -> `@field_serializer` or `Annotated` `PlainSerializer`
- Complex wrap validators with branching logic
- `@validator(always=True)` on computed fields -> `@computed_field`

Always diff the changes manually after running `bump-pydantic`.

## Official Documentation Links

- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Pydantic v2 Core Concepts: Models](https://docs.pydantic.dev/latest/concepts/models/)
- [Validators concept](https://pydantic.dev/docs/validation/latest/concepts/validators/)
- [Serialization concept](https://pydantic.dev/docs/validation/latest/concepts/serialization/)
- [Strict mode](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/)
- [Performance guide](https://pydantic.dev/docs/validation/latest/concepts/performance/)
- [JSON Schema modes](https://pydantic.dev/docs/validation/latest/concepts/json_schema/)
- [Unions and discriminators](https://pydantic.dev/docs/validation/latest/concepts/unions/)
- [Configuration API (`defer_build`, `cache_strings`)](https://docs.pydantic.dev/latest/api/config/)
- [Functional Validators API](https://docs.pydantic.dev/latest/api/functional_validators/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Secret Types](https://docs.pydantic.dev/2.0/usage/types/secrets/)
- [Pydantic 2.13 release (2026-04)](https://pydantic.dev/articles/pydantic-v2-13-release)
- [Pydantic 2.12 release](https://pydantic.dev/articles/pydantic-v2-12-release)
- [Pydantic 2.11 release (2025)](https://pydantic.dev/articles/pydantic-v2-11-release)
- [FastAPI + Pydantic v2 response models](https://fastapi.tiangolo.com/tutorial/response-model/)
- [#8859: YYYY-MM-DD datetime UTC conversion](https://github.com/pydantic/pydantic/issues/8859)
- [#10735: model_dump shallow-copy trap](https://github.com/pydantic/pydantic/issues/10735)
- [#5683: extra=allow dump behavior v1 vs v2](https://github.com/pydantic/pydantic/issues/5683)
