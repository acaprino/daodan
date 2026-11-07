- Verdict: REAL
- Confidence: 97
- Evidence_class: reproduced
- Reason: `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` subtracts `compute_discount(order)` twice against the single discount stated at `pricing.py:18`, and it is reached through `api.py:31` -> `api.py:27` -> `service.py:26`. The test passes on base (109.8) and fails on candidate (97.6), both in the return value and in the ledger line written by `ledger.py:18`.

## Citation and path

- Citation correct: the changed line is `pricing.py:19`; the docstring is on line 18. It is the only change between `6dd2c2bbf` and `943bdc44c` (`git diff --stat`: 1 file, 1 line).
- Path: `register_defaults` registers `service.checkout` (`api.py:37`); `Dispatcher.handle` (`api.py:31`) -> `_invoke` (`api.py:27`) -> `OrderService.checkout` -> `pricing.compute_total` (`service.py:26`) -> `ledger.record` (`service.py:28`, `ledger.py:18`) -> `return total` (`service.py:30`).
- Trigger: `checkout` with non-zero `net` and `loyalty_percent`. With net 100 and loyalty 10 the candidate gives net 80 (effective 20% discount), VAT 17.6 on the reduced net, total 97.6. Zero loyalty is unaffected (122.0 on both).
- No compensation: `compute_discount` is pure and returns the same value on both calls (`pricing.py:11-14`); nothing after `service.py:26` changes `total`.

## Limits

- `register_defaults`, `.handle` and `loyalty_percent` have no caller or producer inside `benchmarks/scope-resolution`, apart from the read at `pricing.py:13`. The app is a library fixture, so reachability is shown through its public entry point with a caller-supplied payload (`api.py:4`: payload passed as is).
- Without `ORDER_NOTIFY_HANDLERS`, `notifications.py:13` raises `KeyError` at `service.py:29`: the wrong ledger line is already written but `checkout` does not return. The test sets the variable to `email_receipt=builtins:id`.

## Commands

All from the work tree or the scratch path, with the TEMP/TMP/TMPDIR prefix. Python 3.13.14.

1. `git show <ref>:benchmarks/scope-resolution/app/packages/orders/<f>.py > scratch/f1-lens1/<base|cand>/packages/orders/<f>.py`, for `<f>` in `__init__ api inventory ledger notifications pricing service`, refs `6dd2c2bbf` and `943bdc44c`.
2. `diff -r` of the two copies: only `pricing.py` line 19 differs.
3. `cd scratch/f1-lens1/run-<label> && F1_ROOT=scratch/f1-lens1/<label> python -B scratch/f1-lens1/test_f1.py`, one process at a time, absolute paths.

## Outcomes

| Test | Base `6dd2c2bbf` | Candidate `943bdc44c` |
|---|---|---|
| `test_copy_under_test` | ok | ok |
| `test_no_loyalty_control` | ok | ok |
| `test_total_one_discount` | ok | FAIL: `97.6 != 109.8` |
| `test_checkout_path_return_and_ledger` | ok | FAIL: `(97.6, 'f1\t97.6') != (109.8, 'f1\t109.8')` |
| Exit code | 0 | 1 |
| `ledger.log` in the scratch path | `f1	109.8` | `f1	97.6` |

## Test text

```python
"""F1: compute_total must subtract the loyalty discount once (pricing.py:18)."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.environ["F1_ROOT"])
# send_via (service.py:29) needs a handler; builtins:id is a harmless no-op sender.
os.environ["ORDER_NOTIFY_HANDLERS"] = "email_receipt=builtins:id"

from packages.orders import pricing
from packages.orders.api import register_defaults

ORDER = {"id": "f1", "sku": "demo-sku", "qty": 1, "net": 100, "loyalty_percent": 10}


class F1(unittest.TestCase):
    def test_copy_under_test(self):
        self.assertTrue(Path(pricing.__file__).resolve().is_relative_to(Path(os.environ["F1_ROOT"]).resolve()))

    def test_no_loyalty_control(self):
        self.assertEqual(pricing.compute_total({"net": 100}), 122.0)

    def test_total_one_discount(self):
        # 100 - 10 = 90; VAT 19.8; total 109.8
        self.assertEqual(pricing.compute_total(dict(ORDER)), 109.8)

    def test_checkout_path_return_and_ledger(self):
        total = register_defaults().handle("checkout", dict(ORDER))
        line = Path("ledger.log").read_text(encoding="utf-8").splitlines()[-1]
        self.assertEqual((total, line), (109.8, "f1\t109.8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

## Files created and removed

Created under `scratch/` (removed with `rm -rf scratch/f1-lens1`, directory included):

- scratch/f1-lens1/base/packages/orders/__init__.py
- scratch/f1-lens1/base/packages/orders/api.py
- scratch/f1-lens1/base/packages/orders/inventory.py
- scratch/f1-lens1/base/packages/orders/ledger.py
- scratch/f1-lens1/base/packages/orders/notifications.py
- scratch/f1-lens1/base/packages/orders/pricing.py
- scratch/f1-lens1/base/packages/orders/service.py
- scratch/f1-lens1/cand/packages/orders/__init__.py
- scratch/f1-lens1/cand/packages/orders/api.py
- scratch/f1-lens1/cand/packages/orders/inventory.py
- scratch/f1-lens1/cand/packages/orders/ledger.py
- scratch/f1-lens1/cand/packages/orders/notifications.py
- scratch/f1-lens1/cand/packages/orders/pricing.py
- scratch/f1-lens1/cand/packages/orders/service.py
- scratch/f1-lens1/run-base/ledger.log
- scratch/f1-lens1/run-cand/ledger.log
- scratch/f1-lens1/test_f1.py

After removal: 0 entries left in `scratch/`. Work tree `git status --short`: 0 lines. Kept: this report only.

## Disclosures

- This commit was mentioned in content already loaded in the session: the auto-memory index carries a line calling `943bdc44c` a seeded defect, and the git status snapshot lists an untracked `benchmarks/scope-resolution/results/review-light-943bdc44c/` directory, which I did not open. Neither is used as evidence; the verdict rests on the source at the two refs and the test above.
- Deviation from the read limits: one `ls -la` of the `OUT` root showed the names of its entries. No file outside `scratch/` and this report was read or written.
