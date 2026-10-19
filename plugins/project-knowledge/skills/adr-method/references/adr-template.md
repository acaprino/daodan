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
