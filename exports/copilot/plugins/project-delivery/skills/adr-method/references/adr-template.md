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

# ADR record format

Version 1 of a decision is `docs/adr/ADR-NNNN-<slug>.md`; version N is
`ADR-NNNN-vN-<slug>.md`, slug of version 1. The helper writes the front matter
and header, the coordinator the body. Run `template`, then `validate` before use.

## Front matter (written by the helper, canonical order)

```yaml
---
adr_id: ADR-0014
version: 2
title: Separate draft validation from executable order validation
status: Accepted
author: Alfio Caprino
scope:
  paths:
    - src/orders/**
  modules:
    - orders.validation
  domains:
    - order-lifecycle
governs_symbols:
  - py:src/orders/validator.py#validate_order
depends_on:
  - ADR-0009
created_from_task: change-3f9a1c
proposed_on: 2026-10-24
proposed_at_sha: 9c4e1b0a2d3f
accepted_on: 2026-10-25
accepted_at_sha: 1a2b3c4d5e6f
last_verified_sha: null
retired_on: null
retired_reason: null
supersedes:
  - ADR-0006
superseded_by: null
changes:
  - INV-001
---
```

Under the title, between `<!-- adr-header:start -->` and
`<!-- adr-header:end -->`, every write regenerates one line:
`Version 2 · Accepted 2026-10-25 at 1a2b3c4 · proposed 2026-10-24 by Alfio Caprino`.

Rules the validator enforces:

- `status` is `Proposed`, `Accepted` (with `accepted_on`, and `accepted_at_sha`,
  null only if accepted before the first commit),
  `Superseded` (with `superseded_by`: a later version, `ADR-0014 v3`, or another
  decision listing it in `supersedes`) or `Abandoned` (with `retired_on`,
  `retired_reason`). Chains never loop or end in a `Proposed` or `Abandoned` record.
- `scope` names at least one path pattern, module or domain; `/**` matches
  everything below, other patterns are shell globs.
- `governs_symbols` holds Codebase Map identities (`<language>:<path>#<name>`).
- `supersedes` and `depends_on` name other decisions, `Accepted` at proposal.
  `changes` lists the items whose text differs from the `Accepted` version.

Versions: at most one `Accepted` and one `Proposed` version per decision.

## Body sections

Three sections are mandatory, each with numbered items; placeholders are
refused.

```markdown
## Verified Interview Examples
- **EX-001** (nominal): Input: `validate_order(OrderInput(symbol="AAPL", qty=10))` -> Expected: `ValidatedOrder(qty=10)`
- **EX-002** (boundary): Input: `validate_order(OrderInput(symbol="AAPL", qty=0))` -> Expected: raises `InvalidQuantityError(code="QTY_NON_POSITIVE")`

## Rejected Alternatives
- **RA-001**: a boolean `allow_zero_qty` on `validate_order()`; rejected because it weakens the execution invariant.

## Enforceable Invariants
- **INV-001**: `validate_order()` never accepts `qty <= 0` on any caller path.
```

`EX-*` items are the plan's oracle: each micro-task names the examples it
makes pass. `RA-*` items stop a later task from reintroducing a rejected
design. Reviewers check `INV-*` items on every wave touching the scope.

The other sections (`Context and Problem Statement`, `Decision Drivers`,
`Decision`, `Consequences`, `Confirmation`) are expected but judged by a
reviewer, not the machine.
