- Verdict: REAL
- Confidence: 97
- Evidence_class: reproduced
- Reason: `pricing.py:19` @943bdc44c subtracts the pure `compute_discount` (`:11-14`) twice, contradicting the contract at `pricing.py:18` and base `:19`; the value flows unchanged through `api.py:29-31` -> `service.py:26,28,30` -> `ledger.py:18`. For net 100, loyalty 10, the candidate returns and records 97.6, the base 109.8.

## Reproduction

Path traced: `api.register_defaults()` (`api.py:34-39`) registers `OrderService().checkout`; `Dispatcher.handle` (`api.py:29-31`) -> `_invoke` (`:25-27`) -> `checkout` (`service.py:23-30`): `compute_total` at `:26`, `ledger.record(order, total)` at `:28` (writes `total` verbatim at `ledger.py:18`), returns `total` at `:30`. No add-back or second discount source anywhere; the only Python caller of `compute_total` is `service.py:26`; the only test reference is the text-only `test_app_structures.py:71`.

Setup: `git archive <ref> benchmarks/scope-resolution/app/packages | tar -x -C <scratch>/{base,cand}` for `6dd2c2bbf` and `943bdc44c`, run from the work tree (read-only). Each run from its own scratch cwd (`run_base`, `run_cand`) so `ledger.log`/`ledger.lock` stay in scratch. `PYTHONDONTWRITEBYTECODE=1`, `python -B`.

Test source (`OUT/scratch/J01-F1-lens1/test_total.py`):
```python
import sys, os
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "benchmarks/scope-resolution/app"))
from packages.orders import api, pricing
order = {"id": "o1", "sku": "A", "qty": 1, "net": 100, "loyalty_percent": 10}
# contract pricing.py:18: net - one customer discount + VAT
d = pricing.compute_discount(dict(order))
expected = round((100 - d) + pricing.vat_amount(100 - d), 2)
disp = api.register_defaults()
got = disp.handle("checkout", dict(order))
log = open("ledger.log", encoding="utf-8").read().strip()
print("discount", d, "expected", expected, "got", got, "ledger", repr(log))
assert got == expected, f"FAIL: got {got}, expected {expected}"
print("PASS")
```

Commands:
```
cd <scratch>/run_base && python -B <scratch>/test_total.py <scratch>/base
cd <scratch>/run_cand && python -B <scratch>/test_total.py <scratch>/cand
```

Run 1 (no env): both refs raised `KeyError: 'ORDER_NOTIFY_HANDLERS'` at `notifications.py:13` (step `service.py:29`, after the ledger write). Ledger already held `o1\t109.8` (base) and `o1\t97.6` (candidate): the wrong total is recorded even when checkout then fails. The notification prerequisite is environmental and identical on both refs.

Run 2 (`ORDER_NOTIFY_HANDLERS="email_receipt=builtins:id"` as a no-op stub, ledger files removed first):
- Base 6dd2c2bbf: `discount 10.0 expected 109.8 got 109.8 ledger 'o1\t109.8'` / `PASS`, exit 0.
- Candidate 943bdc44c: `discount 10.0 expected 109.8 got 97.6 ledger 'o1\t97.6'` / `AssertionError: FAIL: got 97.6, expected 109.8`, exit 1.

Passes on base, fails on candidate: reproduced. The test file and both extracted trees were removed afterwards.

## Created files

| File | Still exists |
|---|---|
| `OUT/scratch/J01-F1-lens1/test_total.py` | no (removed) |
| `OUT/scratch/J01-F1-lens1/base/` (git archive of 6dd2c2bbf packages) | no (removed) |
| `OUT/scratch/J01-F1-lens1/cand/` (git archive of 943bdc44c packages) | no (removed) |
| `OUT/scratch/J01-F1-lens1/run_base/ledger.log` | no (removed) |
| `OUT/scratch/J01-F1-lens1/run_cand/ledger.log` | no (removed) |
| `OUT/verification/J01-F1-lens1.md` | yes (this verdict) |

`OUT/scratch/J01-F1-lens1/` is empty (directory kept). Work tree `D:/Projects/daodan/.claude/worktrees/bench-branch-943bdc44c` at HEAD 943bdc44c66dfd9782f6d38c82922a1f08783653: `git status --porcelain` output is empty.
