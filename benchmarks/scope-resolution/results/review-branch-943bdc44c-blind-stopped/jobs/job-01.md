# job-01: local correctness, branch-943bdc44c-simplified

## Envelope

```yaml
job_id: job-01
dimension: local-correctness
reviewer: senior-review:local-correctness-auditor
status: delivered
scope_id: branch-943bdc44c-simplified
input_mode: independent
candidate: 943bdc44c66dfd9782f6d38c82922a1f08783653
base: 6dd2c2bbf
body_sha256: 1284b7ba7593477acd493f6fcb611414ec927978938f3bbcef5e698edb900c80
role_sha256: 4fd495dcbc019bfe7a73b12766ad4e8ab6754b1491ee7f60bc64b88cdb61eb1b
findings: [LC-1]
gaps: [G-1, G-2, G-3, G-4]
output_path: OUT/jobs/job-01.md
knowledge_usage: []
```

## member_results

| specialist | delivery | coverage | findings | gaps |
|---|---|---|---|---|
| `senior-review:local-correctness-auditor` | delivered | complete (static only, no runtime exercise) | LC-1 | G-1, G-2, G-3, G-4 |

## Findings

### LC-1: `compute_total` subtracts the customer discount twice

- file: `benchmarks/scope-resolution/app/packages/orders/pricing.py`
- line: 19
- severity: High. Every order with a loyalty discount gets a wrong total, short by about 1.22 times the discount, and the wrong amount is written to the ledger. Reach is this benchmark mini-app.
- confidence: 95
- introduced_by_candidate: true
- evidence_class: derived (source reading and hand arithmetic; nothing executed)
- premise: `compute_total` must subtract the customer discount exactly once.
- premise_provenance: independent

**Evidence.** Line 19 is now `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`; the base had one subtraction. The contract directly above it, unchanged at line 18, reads "netto - sconto cliente + IVA (VAT)": one discount. `compute_discount` (lines 11-14) only reads `net` and `loyalty_percent` and mutates nothing, so both calls return the same value: this is one discount counted twice, not two rules. The reduced `net` is also the VAT base at line 20, so VAT falls too.

Hand-derived results for `net=100`:

| `loyalty_percent` | base total | candidate total | note |
|---|---|---|---|
| 0 or absent | 122.0 | 122.0 | no change |
| 10 | 109.8 | 97.6 | VAT 19.8 becomes 17.6; 12.2 short |
| 50 | 61.0 | 0.0 | order is free |
| 60 | 48.8 | -24.4 | negative total; the base goes negative only above 100 |

**Trigger.** Any order reaching `compute_total` whose discount rounds to non-zero, for example `{"sku": "demo-sku", "qty": 1, "net": 100, "loyalty_percent": 10}`.

**Reachable path.** `Dispatcher.handle("checkout", payload)` (`orders/api.py:29`, registered at `:37`) calls `OrderService.checkout`, which calls `pricing.compute_total` (`orders/service.py:26`). The value goes to `ledger.record` (`service.py:28`) and is appended to `ledger.log` (`orders/ledger.py:18`). It is then returned (`service.py:30`, `api.py:27`) if `send_via` at `service.py:29` does not raise; the ledger line is written either way. Ledger lines written with this code stay wrong after a fix.

**counterevidence_checked.**
- A second discount source: `shipping/rates.py:15` `volume_discount` is a separate shipping rule and is not called here.
- A stated double-discount rule: searching the work tree outside `results/` for `loyalty_percent` and double-discount wording matched only `pricing.py`.
- Stated intent: the commit message gives no reason and the docstring formula was not changed.
- Mutation of the inputs: across `app/`, the literal key `net` appears only at `pricing.py:14` and `:19`, and `compute_discount` holds no state.
- A guard on the discount range: none. `DefaultPipeline.step` runs after `compute_total` and only sets `validated` (`service.py:14`, `:27`).
- A stock guard before the total: none. `reserve_stock` returning `False` does not stop `checkout` (`service.py:25`, `inventory.py:22`).
- Tests: `test_app_structures.py` has no amount assertion, only the text check for `def compute_discount(` at `:71`, so its 11 passes (`OUT/tools/pytest-app-structures.txt`) do not bear on this.

**Fix direction.** Restore `net = order.get("net", 0) - compute_discount(order)`. If a second discount is really wanted, state it as its own rule and update line 18. Add an amount test with `loyalty_percent > 0` that checks both the total and the VAT base.

## Effects not established

- `payments/gateway.py:10`, `:15` and `orders/reporting.py:14` read `total` from their own dict. Nothing in `app/` assigns `order["total"]`, and nothing in `app/` calls `charge` or `format_daily_summary`. No effect through them is claimed.
- `payments/refunds.py:15` `issue_refund` takes its amount from the caller and has no in-app caller. `OrderService.refund_request` writes `REFUND` with no amount (`ledger.py:30`).
- `orders/reporting.py:11` uses only `VAT_RATE`, which is unchanged.
- `send_via` receives `order`, not `total` (`service.py:29`). Its handler comes from `ORDER_NOTIFY_HANDLERS` and lies outside the sources (`notifications.py:13-15`), so a receipt effect can be neither shown nor excluded.

## Checks completed

| Check | Result |
|---|---|
| Arithmetic, sign, VAT base | LC-1 |
| Bounds: zero, absent, 50, above 50 | Zero and absent unchanged; above 0 wrong; above 50 negative (LC-1) |
| Coercion, precision, rounding | The candidate adds one float subtraction and no new rounding step or type |
| Evaluation order, side effects | `compute_discount` is pure; the repeated call has no side effect |
| Initialization, scope, aliases, defaults | `net` is bound once, shadows nothing, and `order` is not mutated |
| Errors and partial success | The line adds no I/O or new exception; a non-numeric `net` raises as in the base |
| State after failure, next attempt | `compute_total` keeps no state; only the ledger retains the wrong value (LC-1) |
| Other owners of the same fact | `payments/refunds.py:7` has its own `VAT_RATE`, unchanged by the candidate |

## Examined scope

Read in the work tree at the candidate: `orders/pricing.py`, `service.py`, `ledger.py`, `api.py`, `reporting.py`, `inventory.py`, `notifications.py`, `payments/gateway.py`, `payments/refunds.py`, `test_app_structures.py`; targeted searches over `app/`, including `orders/big_module.py` and `shipping/rates.py`, which were not read in full. Also the base expression and `AGENTS.md` through `git show 6dd2c2bbf:`, and the shared context, re-derived rather than relied on. No map tool was used, so no map anchors are cited.

## Gaps

- G-1: no runtime exercise (no run grant). The table above is hand-derived.
- G-2: intent is unknown. The premise rests on the docstrings at `pricing.py:18` and `:12`; no separate requirement for these amounts was found. A requirement outside the work tree stating a double discount would refute LC-1.
- G-3: no driver in `app/` calls `register_defaults` or `Dispatcher.handle`; reachability rests on them being the public entry point (`api.py:30`). Their callers outside `app/` were not searched.
- G-4: on unchanged lines, outside the conclusion path `pricing.py:19`, so not assessed as findings. Seen while tracing the path: `service.py:25` discards the `False` that `reserve_stock` returns on insufficient stock, so `checkout` still records a total. Not assessed: the other partial effects of `checkout` (`service.py:25-29`) and float money handling.

Disclosure: an early broad search over `benchmarks/scope-resolution` returned preview lines from `ground_truth.json`, `results/probe-graph.md` and `results/run-*/traces.json`. Their spill file was not opened and nothing here rests on them: the call chain was re-read from source. The later wording search also covered `ground_truth.json`, with files-only output, and did not match it.
