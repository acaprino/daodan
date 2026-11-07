- Verdict: REAL
- Confidence: 97
- Evidence_class: reproduced
- Reason: `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` @943bdc44c subtracts `compute_discount(order)` twice, so taxable net = net·(1 − 2p/100) and is ≤ 0 for p ≥ 50; `OrderService.checkout` (`service.py:26-28`) passes it unchecked to `ledger.record` (`ledger.py:18`), reached via `Dispatcher.handle("checkout", ...)` (`api.py:29-31`, `25-27`) after `register_defaults()` (`api.py:34-39`). Reproduced end to end: base records 61.0 / 48.8 / 30.5 / 1.22 for p 50 / 60 / 75 / 99, candidate records 0.0 / −24.4 / −61.0 / −119.56.

## Reproduction

Citation check: the diff (`git diff 6dd2c2bbf 943bdc44c`, 1 file, 1 line) changes only `pricing.py:19`; no guard on `loyalty_percent` or on the net exists in `pricing.py`, `service.py` (`DefaultPipeline.step` at `service.py:13-15` runs after the total and only sets `validated`), `api.py` or `ledger.py:13-22`. `inventory.reserve_stock` (`service.py:25`) returns a bool that `checkout` ignores, so it does not stop the path either.

Setup (scratch only, work tree untouched): `git archive 6dd2c2bbf benchmarks/scope-resolution/app/packages/orders | tar -x -C $S/base` and the same for `943bdc44c` into `$S/cand`, run in the work tree. Notification handler: identical no-op stub on both refs, `stubs/noop_notify.py` = `def send(order): return None`, wired by `ORDER_NOTIFY_HANDLERS=email_receipt=noop_notify:send` (set inside the test). `PYTHONDONTWRITEBYTECODE=1`; each run from its own scratch cwd (`run-base`, `run-cand`) so `ledger.log`/`ledger.lock` stay in scratch.

Test source (`$S/test_j01f2.py`):
```python
"""J01-F2: for net > 0 and loyalty_percent in 50..99 the recorded checkout total is positive."""
import os
import sys
from pathlib import Path

pkg_root, stub_dir = sys.argv[1], sys.argv[2]
sys.path[:0] = [pkg_root, stub_dir]
os.environ["ORDER_NOTIFY_HANDLERS"] = "email_receipt=noop_notify:send"

from orders import api  # noqa: E402

dispatcher = api.register_defaults()
failures = []
for i, p in enumerate([50, 60, 75, 99, 100]):
    payload = {"id": f"o{p}", "sku": "demo-sku", "qty": 1, "net": 100, "loyalty_percent": p}
    total = dispatcher.handle("checkout", payload)
    print(f"p={p} total={total}")
    if p < 100 and not total > 0:
        failures.append((p, total))
print("ledger.log:", Path("ledger.log").read_text(encoding="utf-8").replace("\n", " | "))
print("FAIL" if failures else "PASS", failures)
sys.exit(1 if failures else 0)
```
p 100 is printed only (base gives 0.0, so the positivity property is asserted for 50..99).

Commands (`S=$OUT/scratch/J01-F2-lens1`, `P=benchmarks/scope-resolution/app/packages`):
- `cd $S/run-base && python -B $S/test_j01f2.py $S/base/$P $S/stubs`
- `cd $S/run-cand && python -B $S/test_j01f2.py $S/cand/$P $S/stubs`

Base 6dd2c2bbf (exit 0, PASS):
```
p=50 total=61.0
p=60 total=48.8
p=75 total=30.5
p=99 total=1.22
p=100 total=0.0
ledger.log: o50	61.0 | o60	48.8 | o75	30.5 | o99	1.22 | o100	0.0 |
PASS []
```
Candidate 943bdc44c (exit 1, FAIL):
```
p=50 total=0.0
p=60 total=-24.4
p=75 total=-61.0
p=99 total=-119.56
p=100 total=-122.0
ledger.log: o50	0.0 | o60	-24.4 | o75	-61.0 | o99	-119.56 | o100	-122.0 |
FAIL [(50, 0.0), (60, -24.4), (75, -61.0), (99, -119.56)]
```
The values match the finding's examples (p 60 → −24.4, p 100 → −122.0 vs base 0.0, p 50 → 0.0 vs base 61.0), and the ledger records the negative totals. Scope note: introduced by the candidate for 50 ≤ p ≤ 100; the missing range guard and negative totals for p > 100 already exist on base. The test file was removed after both runs.

## Created files

All under `$OUT/scratch/J01-F2-lens1/`:
- `base/benchmarks/scope-resolution/app/packages/orders/*` (base archive): removed
- `cand/benchmarks/scope-resolution/app/packages/orders/*` (candidate archive): removed
- `stubs/noop_notify.py`: removed
- `test_j01f2.py`: removed
- `run-base/ledger.log`, `run-cand/ledger.log`: removed (no `ledger.lock` left; no `__pycache__` created)
- the directory `scratch/J01-F2-lens1/` itself remains, empty
- `$OUT/verification/J01-F2-lens1.md`: this file, exists

Work tree `D:/Projects/daodan/.claude/worktrees/bench-branch-943bdc44c` at HEAD 943bdc44c66dfd9782f6d38c82922a1f08783653: `git status --porcelain` is empty at the end.
