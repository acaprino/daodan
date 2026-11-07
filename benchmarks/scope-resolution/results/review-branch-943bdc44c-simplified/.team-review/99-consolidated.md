# Consolidated findings (before verification)

Delivery ledger: job-01 delivered, job-02 delivered, job-03 delivered. All members complete. `knowledge_usage` is `[]` in all three.

## F1. High, confidence 92: `compute_total` subtracts the customer discount twice

- Location: `benchmarks/scope-resolution/app/packages/orders/pricing.py:19`.
- Sources: LC-01 (job-01), LI-1 (job-02). Same file, line and issue: merged, both credited.
- Premise (LC-01, verbatim): "the contract of `compute_total` applies the customer discount exactly once."
- Premise (LI-1, verbatim): "the required formula of `compute_total` subtracts the customer discount exactly once, and no requirement establishes a second subtraction."
- Provenance: independent in both. Corroborated under the rule, with a limit: both take the rule from the same docstring (`pricing.py:18`), and `02-selection.md` pointed at the docstrings.
- Trigger: `checkout` with non-zero `net` and non-zero `loyalty_percent`.
- `introduced_by_candidate`: true. Evidence class as delivered: derived.

## AL-1. Medium, confidence 95: docstring states a formula the code no longer computes

`benchmarks/scope-resolution/app/packages/orders/pricing.py:18`. Co-located with F1, distinct failure mode (a false statement), same correction. Source: job-03.

## AL-2. Medium, confidence 60: C4 expects `clarify`, but the fixture now favours one target

`benchmarks/scope-resolution/ground_truth.json:67`. Predicted, not measured. Source: job-03.

## AL-3. Low, confidence 75: declared measurements are not labelled as measured on an earlier fixture

`benchmarks/scope-resolution/README.md:39-43`. Source: job-03.

## Notes from workers, not findings

Preexisting, outside the finding scope, possibly deliberate fixture shapes: `service.py:25` ignores the `False` from `reserve_stock`; `payments/gateway.py:10,15` read an `order["total"]` that nothing sets.

## After verification

F1: verified, High, evidence class `reproduced` (base 109.8, candidate 97.6, in the return value and the ledger line). AL-1, AL-2, AL-3: `unverified (tier)`. Filtered: 0.
