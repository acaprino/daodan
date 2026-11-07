# F1 — Lens 1 (Reachability / Correctness)

Citation checked: `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` is the only changed line in the changeset (`git diff 2889c58 109c1d7 --stat`: 1 file, +1/-1). Candidate subtracts `compute_discount(order)` twice; base subtracts it once. Docstring at :18 ("netto - sconto cliente + IVA") is unchanged. `compute_discount` (:11-14) is pure, so the two calls return the same value.

Reachability: sole caller is `service.py:26` (`total = pricing.compute_total(order)`) inside `OrderService.checkout`, which passes `total` to `ledger.record` (service.py:28 -> ledger.py:18 writes it to `ledger.log`) and returns it; `api.py:37` registers `service.checkout` as the "checkout" event handler. Any order dict with `loyalty_percent > 0` triggers it; `loyalty_percent` absent/0 is unaffected.

Scratch test (`scratch_F1_test.py`, written at the granted path, run, then deleted): loads `pricing.py` by path, order `{"net": 100.0, "loyalty_percent": 10}`, expected per docstring = round(90 + 19.8, 2) = 109.8.
- Base (`git show 2889c58:...pricing.py` into scratchpad): `python3 -I scratch_F1_test.py base <scratch>/base_pricing/pricing.py` -> `discount=10.0 expected_total=109.8 got=109.8`, PASS, exit 0.
- Candidate (working tree): `python3 -I scratch_F1_test.py candidate /home/user/daodan/benchmarks/scope-resolution/app/packages/orders/pricing.py /home/user/daodan/benchmarks/scope-resolution/app <scratch>/run` -> `got=97.6`; `OrderService().checkout(...)` (inventory/notifications stubbed, cwd = scratch) returned `97.6` and wrote `o1\t97.6` to ledger.log; AssertionError, exit 1.

- Verdict: REAL
- Confidence: 98
- Evidence_class: reproduced
- Reason: `pricing.py:19` subtracts the pure `compute_discount(order)` twice, so for `loyalty_percent > 0` `compute_total` returns 97.6 instead of the documented 109.8 (net 100, 10%), and `service.py:26-28` propagates that value to the caller and to `ledger.log`; the base passes the same test.
