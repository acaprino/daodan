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

# ADR record format

A record is `docs/adr/ADR-NNNN-<slug>.md`. The helper writes the front matter;
the coordinator writes the body after the interview. Run `template` to print
the body skeleton and `validate` before the record is used by anyone.

## Front matter (written by the helper, canonical order)

```yaml
---
adr_id: ADR-0014
title: Separate draft validation from executable order validation
status: Proposed
scope:
  paths:
    - src/orders/**
  modules:
    - orders.validation
  domains:
    - order-lifecycle
governs_symbols:
  - py:src/orders/validator.py#validate_order
created_from_task: change-3f9a1c
proposed_at_sha: 9c4e1b0a2d3f
accepted_at_sha: null
last_verified_sha: null
supersedes:
  - ADR-0006
superseded_by: null
---
```

Rules the validator enforces:

- `status` is `Proposed`, `Accepted` or `Superseded`. `Proposed` has no
  `accepted_at_sha` and no `superseded_by`. `Accepted` carries
  `accepted_at_sha`. `Superseded` names `superseded_by`, and that record lists
  this one in `supersedes`. Chains never loop and never end in a `Proposed`
  record.
- `scope` names at least one path pattern, module or domain. A path pattern
  ending in `/**` matches everything below it; other patterns are shell globs.
- `governs_symbols` holds stable symbol identities from the Codebase Map
  (`<language>:<path>#<qualified name>`), so a changed symbol finds its record.
- `supersedes` names only `Accepted` records at proposal time; promotion marks
  each of them `Superseded by` this record in one transaction.

## Body sections

Three sections are mandatory and each needs numbered items; the validator
refuses template placeholders left in place.

```markdown
## Verified Interview Examples
- **EX-001** (nominal): Input: `validate_order(OrderInput(symbol="AAPL", qty=10))` -> Expected: `ValidatedOrder(qty=10)`
- **EX-002** (boundary): Input: `validate_order(OrderInput(symbol="AAPL", qty=0))` -> Expected: raises `InvalidQuantityError(code="QTY_NON_POSITIVE")`
- **EX-003** (draft path): Input: `validate_draft(DraftInput(symbol="AAPL", qty=0))` -> Expected: `DraftValidationResult(valid=True, executable=False, missing=["qty"])`

## Rejected Alternatives
- **RA-001**: a boolean `allow_zero_qty` on `validate_order()`; rejected because it weakens the invariant on the execution path and every caller would have to know the flag.

## Enforceable Invariants
- **INV-001**: `validate_order()` never accepts `qty <= 0` on any caller path.
- **INV-002**: no order with `executable == False` reaches `OrderRouter.submit()`.
```

`EX-*` items are the oracle of the plan: each micro-task names the examples it
makes pass. `RA-*` items stop a later task from reintroducing a rejected
design. `INV-*` items are what reviewers check on every wave that touches the
scope.

The remaining sections (`Context and Problem Statement`, `Decision Drivers`,
`Decision`, `Consequences`, `Confirmation`) are expected in every record but not
machine-checked: a reviewer judges them.
