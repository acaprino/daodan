# ADR record format

Version 1 of a decision is `docs/adr/ADR-NNNN-<slug>.md`; version N is
`ADR-NNNN-vN-<slug>.md`, slug of version 1. The helper writes the front matter
and header, the coordinator the body. Run `template` for the skeleton and
`validate` before anyone uses the record.

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

- `status` is `Proposed`, `Accepted` (with `accepted_on`, `accepted_at_sha`),
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
