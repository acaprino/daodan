# Consolidated findings: branch-943bdc44c-simplified

Delivery ledger: job-01 `local-correctness-auditor` delivered, complete, static only; job-02 `logic-integrity-auditor` delivered, complete, static only. Barrier closed: 2/2.

## High (1)

### F-01: `compute_total` subtracts the customer discount twice

- Location: `benchmarks/scope-resolution/app/packages/orders/pricing.py:19`
- Merged: LC-1 (`jobs/job-01.md`, High, confidence 95), LI-01 (`jobs/job-02.md`, High, confidence 93, L4 with L1.2).
- Agreement: corroborated. Both premises are declared `independent` and re-derived from source; both reviewers also had `01-context.md`.
- introduced_by_candidate: true. evidence_class before the panel: derived.
- Premises: LC-1 "`compute_total` must subtract the customer discount exactly once"; LI-01 "no requirement or contract in scope authorizes applying the customer discount twice to one order".
- Trigger: an order with `net` != 0 and a `loyalty_percent` whose discount rounds to non-zero.
- Fix direction: restore `net = order.get("net", 0) - compute_discount(order)`; if a second discount is wanted, state it as its own rule at `pricing.py:18`; add an amount test with `loyalty_percent` > 0.

No Critical, Medium or Low findings. No `[MAP-GAP]` finding.

## Notes outside the conclusion path, not findings, not verified

- Both reviewers: `orders/service.py:25` discards the `False` that `reserve_stock` returns (`orders/inventory.py:22`). Preexisting, not touched by the candidate.
