- premise_verdict: HOLDS
- premise_form: non-compliant
- reason: The stated premise quantifies over every net > 0 and is literally false: rounding the discount to cents gives a zero total, not a negative one (net 0.02, p 60: `compute_discount` = round(0.012, 2) = 0.01 at pricing.py:14, so the taxable net is 0.02 − 0.01 − 0.01 = 0.0 at pricing.py:19 and the total is 0.0 at pricing.py:20). I re-derived a minimal premise: some reachable input with net > 0 and 50 ≤ p ≤ 100 (net 100, p 60 → −24.4; base 61.0 at p 50, 0.0 at p 100) gives a total ≤ 0, and nothing on the default path clamps or rejects it. That premise holds: the payload is passed to the handler unchanged (api.py:25-27, 29-31), the only "checkout" registration is `service.checkout` with `DefaultPipeline` (api.py:36-37). `checkout` computes the total before `step` and passes it on unchanged (service.py:13-15, 26-28), and `ledger.record` writes any value (ledger.py:18).

Derived premise challenged: "there exists an order with net > 0 and 50 ≤ loyalty_percent ≤ 100 for which `compute_total` @943bdc44c returns a value ≤ 0 while base returns > 0, and no code on the default dispatch path `Dispatcher.handle` → `_invoke` → `OrderService.checkout` → `ledger.record` rejects or clamps it."

Note: the rounding counterexample only removes the universal "negative for every net > 0" from the stated wording. The result is zero, which is still the non-positive outcome the finding describes, so it does not touch the finding. It also partly contradicts the finding's "≤ 0 for p ≥ 50 up to rounding": net 0.03, p 50 gives round(0.015, 2) = 0.01, so the total is 0.01 > 0. That is wording only and does not decide the finding.

## Searched
- `pricing.py:6-20` @943bdc44c and the base `pricing.py:19` (`git show 6dd2c2bbf`): worked the arithmetic and the cent rounding by hand, including the edge cases at small net.
- `service.py`, `api.py`, `ledger.py`, `inventory.py`, `notifications.py`, `__init__.py` (empty) in `benchmarks/scope-resolution/app/packages/orders/`: the whole path from `Dispatcher.handle` to `ledger.record`. Looked for a guard, clamp, raise or rewrite of `total`. `reserve_stock`'s return value is ignored and it does not look at net or loyalty.
- Second paths, searched with grep over `benchmarks/scope-resolution/app`: other `on_event("checkout", …)` registrations, other `pipeline_cls` or pipeline classes, other callers of `compute_total`, `compute_discount` and `ledger.record`, imports of `orders` from `payments/` and `shipping/`, `reporting.py` (uses only `VAT_RATE`), `big_module.py` (formatters only). None found.
- Docs and tests in the work tree that could state a domain limit on `loyalty_percent`: `benchmarks/scope-resolution/CASES.md`, `README.md`, `ground_truth.json`, `test_app_structures.py`. No range or validity rule.
- `git diff --stat 6dd2c2bbf 943bdc44c`: the only change is `pricing.py`.

## Created files
- `OUT/verification/J01-F2-lens0.md`
