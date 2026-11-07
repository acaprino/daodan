# F1 — Lens 0 (premise challenge)

- Finding: High, `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` subtracts `compute_discount(order)` twice.
- Premise: "The documented pricing rule in `pricing.py:18` requires the customer discount to be subtracted from the net exactly once."
- Scope of the proposition: every statement of the order-total rule reachable in the repository (docstrings, callers, tests, fixtures, git history), and every code path that could legitimately define a second customer concession.

Searched (base `2889c58`, candidate `109c1d7`):
- `pricing.py:1` module docstring and `pricing.py:18` rule docstring, identical at base and HEAD (`git show 2889c58:...pricing.py`): "netto - sconto cliente + IVA (VAT)", one subtrahend. `compute_discount` (`pricing.py:11-14`) unchanged and returns the full `net * loyalty / 100`, so two calls are not two halves of one concession.
- Changeset: `git diff 2889c58 109c1d7` touches only `pricing.py:19`; commit message `109c1d7` ("benchmark: aggiorna il calcolo in pricing.py") states no rule change.
- Callers: `service.py:26` is the sole caller of `compute_total`; `service.py:3`, `service.py:24`, `api.py:5-6`, `ledger.py:14` describe the total as "netto/totale con IVA" and name no second discount. `reporting.py:11` uses only `pricing.VAT_RATE`.
- Second discount mechanisms: `git grep -i 'discount|sconto|concession|twice|doppio|due volte'` over the app and repository finds only `shipping/rates.py:15` `volume_discount`, applied to the shipping rate at `rates.py:27`, never to the order net. `big_module.py` has no pricing symbol.
- Tests: `test_app_structures.py:70-72` asserts only that `compute_discount` and `volume_discount` are defined; no test asserts a numeric total, so none asserts a double subtraction.
- Fixture `ground_truth.json:15, :90`: describes the chain `compute_discount -> compute_total -> OrderService.checkout` as a scope case; no rule content.
- Numeric check (python, base vs HEAD): `{net:100, loyalty_percent:10}` base 109.80, HEAD 97.60; `{net:50, loyalty_percent:60}` HEAD -12.20 (negative total). Orders with `loyalty_percent` 0 or absent are unchanged.

No file:line defines, documents or asserts a second subtraction of the customer discount.

- premise_verdict: HOLDS
- refutation_target: (none)
- counterexample: (none)
- premise_form: compliant
- reason: The rule at `pricing.py:18` ("netto - sconto cliente + IVA") is unchanged between `2889c58` and `109c1d7` and names a single subtrahend; the only other discount in the repository, `shipping/rates.py:15` `volume_discount`, applies to the shipping rate (`rates.py:27`), not the order net, and no test, docstring or fixture (`test_app_structures.py:70-72`, `service.py:24`, `ground_truth.json:15`) describes a second customer concession.
