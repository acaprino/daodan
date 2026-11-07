# Lens 1 (Reachability / Correctness) - CA-01

- Verdict: REAL
- Confidence: 97
- Evidence_class: reproduced
- Reason: benchmarks/scope-resolution/app/packages/orders/pricing.py:19 subtracts compute_discount(order) twice (base 6dd2c2bbf subtracts it once); reached directly and via OrderService.checkout (benchmarks/scope-resolution/app/packages/orders/service.py:26), whose total goes to ledger.record (ledger.py:13-22).

## Evidence
- Citation correct: line 19 of candidate f38ceeb9f is `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`.
- compute_discount (pricing.py:11-14) is pure (reads order, no mutation), so the second call returns the same amount: discount applied twice.
- Callers: only service.py:26 (`total = pricing.compute_total(order)`), then `ledger.record(order, total)` and `return total`. No caller compensates.
- Requirement: docstring pricing.py:18 "netto - sconto cliente + IVA"; benchmarks/scope-resolution/test_pricing_oracle.py:18 expects 109.8 (discount once). README.md:24-27 declares it a deliberately seeded defect for the benchmark; that confirms the defect, it does not make it correct behavior.
- Reproduction (scratch test, removed after run):
  - base 6dd2c2bbf: 3 passed (net 100 / loyalty 10 -> 109.8; loyalty 60 -> >= 0; no loyalty -> 122.0).
  - candidate f38ceeb9f: 2 failed, 1 passed: `assert 97.6 == 109.8`; `assert -24.4 >= 0` (negative total above 50% loyalty confirmed).
- Trigger: any order with net > 0 and loyalty_percent > 0; loyalty_percent == 0 is unaffected.
