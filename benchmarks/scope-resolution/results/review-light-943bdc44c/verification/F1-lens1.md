# F1 - Lens 1 (Reachability / Correctness)

- Verdict: REAL
- Confidence: 97
- Evidence_class: reproduced
- Reason: benchmarks/scope-resolution/app/packages/orders/pricing.py:19 subtracts the pure compute_discount(order) (pricing.py:11-14) twice, contradicting the unchanged docstring at pricing.py:18 ("netto - sconto cliente + IVA"); OrderService.checkout reaches it unconditionally at service.py:26 and persists/returns the wrong total via ledger.record (service.py:28, ledger.py:13-22) and `return total` (service.py:30).

## Trace

- Citation correct: candidate 943bdc44c, pricing.py:19 `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`; base 6dd2c2bbf has a single subtraction.
- Path: OrderService.checkout (service.py:23) -> inventory.reserve_stock (service.py:25) -> pricing.compute_total (service.py:26) -> ledger.record(order, total) writes `{id}\t{total}` (ledger.py:18) -> returned (service.py:30). No branch, clamp or validation on net or loyalty_percent in pricing.py or service.py.
- Trigger: any checkout with net > 0 and loyalty_percent > 0 (loyalty_percent = 0 is unaffected).
- Other consumers: reporting.py:11 reads only pricing.VAT_RATE; no test in benchmarks/scope-resolution (results/ excluded) pins compute_total.

## Commands and outputs

Scratch: D:/Projects/daodan/.claude/tmp/lens1-F1/ (env TEMP/TMP/TMPDIR=/d/Projects/daodan/.claude/tmp, PYTHONDONTWRITEBYTECODE=1)

```
git show 6dd2c2bbf:benchmarks/scope-resolution/app/packages/orders/pricing.py > lens1-F1/pricing_base.py
git show 943bdc44c:benchmarks/scope-resolution/app/packages/orders/pricing.py > lens1-F1/pricing_cand.py
python -B lens1-F1/repro_f1.py <pricing file>   # loads the file, asserts compute_total on 3 cases
```

repro_f1.py expectations (from the docstring formula net - discount + VAT 22%): net=100/loyalty=10 -> 109.8; net=100/loyalty=50 -> 61.0; net=100/loyalty=0 -> 122.0.

```
== base 6dd2c2bbf
PASS {'net': 100, 'loyalty_percent': 10} expected=109.8 got=109.8
PASS {'net': 100, 'loyalty_percent': 50} expected=61.0 got=61.0
PASS {'net': 100, 'loyalty_percent': 0} expected=122.0 got=122.0
INFO loyalty=60 total=48.8
exit=0
== candidate 943bdc44c
FAIL {'net': 100, 'loyalty_percent': 10} expected=109.8 got=97.6
FAIL {'net': 100, 'loyalty_percent': 50} expected=61.0 got=0.0
PASS {'net': 100, 'loyalty_percent': 0} expected=122.0 got=122.0
INFO loyalty=60 total=-24.4
exit=1
```

Base passes, candidate fails: total short by one extra discount plus its VAT, 0.0 at 50%, negative (-24.4) at 60%, matching the finding.

Scratch files removed after the run.
