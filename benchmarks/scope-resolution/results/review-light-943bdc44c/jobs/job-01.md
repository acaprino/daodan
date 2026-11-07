# job-01: light-943bdc44c, senior-review:code-auditor (composition)

## Examined scope

- Candidate 943bdc44c66dfd9782f6d38c82922a1f08783653, base 6dd2c2bbf, worktree D:/Projects/daodan/.claude/worktrees/seed-blind; review_basis changeset, input_mode independent, read-only.
- Changed file read in full: benchmarks/scope-resolution/app/packages/orders/pricing.py (base via `git show 6dd2c2bbf:`).
- Callers and consumers read: app/packages/orders/service.py (only call site, :26), ledger.py, api.py, reporting.py, notifications.py (`send_via` signature), payments/gateway.py, payments/refunds.py, shipping/rates.py:15-20 (`volume_discount`), app/pyproject.toml.
- Benchmark contract read: benchmarks/scope-resolution/README.md, CASES.md, ground_truth.json (C1 :3-15, C5 :90, C8 :135), test_app_structures.py (test list, :62-72), grep of the other scripts; base AGENTS.md.
- Runtime exercise (static inspection and runtime are separate facts): one `python -B` process loading base and candidate pricing.py with `runpy`, calling `compute_total` on 7 orders. `OrderService.checkout` was not run because `ledger.record` writes `ledger.log` and `ledger.lock` in the cwd.
- Graph locators used as leads only: symbols-at (changed symbol `compute_total`, lines 17-20); `git grep` re-run, same single call site.
- Knowledge: explicit empty selection, nothing loaded.

## Reviewer-result envelope

```yaml
dimension: code-audit (light review, 26 member roles)
reviewer: senior-review:code-auditor
status: delivered
findings: [F1]
gaps:
  - "edit-impact failed (ModuleNotFoundError: No module named 'edge_view') and stale-callers unavailable (no candidate map run): callers established by git grep and by reading the source. Text search does not see dynamic dispatch; Dispatcher reaches checkout through EVENT_REGISTRY (api.py:13-16, :25-27), read by hand."
  - "The project's tests do not exercise pricing arithmetic: no test calls compute_total or checks a total (the 46 passed, 1 xfailed are structural and resolver tests; test_app_structures.py:70-72 only checks that `def compute_discount(` exists). The green suite neither confirms nor refutes F1."
  - "No stated range for loyalty_percent and no audit or retention policy for ledger.log: those checks rest on the docstrings alone."
  - "Codebase Map run daodan-lite-20261107-2 is bound to 7bd0ff186, where pricing.py is the base version: map evidence for compute_total describes the base body. Not verified with codebase_map_diff."
output_path: D:/Projects/daodan/benchmarks/scope-resolution/results/review-light-943bdc44c/jobs/job-01.md
knowledge_usage: []
```

## Findings

### F1: the loyalty discount is subtracted twice from the order total

- file: benchmarks/scope-resolution/app/packages/orders/pricing.py
- line: 19
- severity: High
- confidence: 95
- classification: introduced (`introduced_by_candidate: true`)
- evidence_class: reproduced
- evidence: the candidate line is `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`; the base line was `net = order.get("net", 0) - compute_discount(order)`. The function's declared contract is pricing.py:18 `"""Totale ordine: netto - sconto cliente + IVA (VAT)."""` (one discount), and `compute_discount` (pricing.py:11-14) already returns the whole loyalty discount (`net * loyalty / 100`). Run output, base vs candidate `compute_total`:
  - `{"net":100,"loyalty_percent":10}`: 109.8 vs 97.6
  - `{"net":19.99,"loyalty_percent":5}`: 23.17 vs 21.95
  - `{"net":100,"loyalty_percent":50}`: 61.0 vs 0.0
  - `{"net":100,"loyalty_percent":60}`: 48.8 vs -24.4
  - `{"net":100,"loyalty_percent":100}`: 0.0 vs -122.0
  - `{"net":100}` and `{}`: unchanged (122.0, 0.0)

  The value goes through `OrderService.checkout`: `total = pricing.compute_total(order)` (service.py:26), it is persisted by `ledger.record(order, total)` (service.py:28, written at ledger.py:18) and returned (service.py:30) to the `"checkout"` callback that `register_defaults` registers (api.py:37) and that `Dispatcher.handle` returns (api.py:29-31). VAT is computed on the wrong net (pricing.py:20 through `vat_amount`, pricing.py:8), so for loyalty_percent > 50 VAT is negative too.
- premise: compute_total's required result subtracts the customer loyalty discount from the net exactly once.
- premise_provenance: independent (docstrings pricing.py:1, :12 and :18, base code, the call chain read in service.py, ledger.py and api.py, and the run; the symbols-at locator only pointed to the symbol).
- trigger: any checkout of an order with `net > 0` and `loyalty_percent > 0`: the total is short by one more discount. With `loyalty_percent` = 50 the total becomes 0.0; above 50 the total and its VAT become negative (the base went negative only above 100).
- counterevidence_checked: the commit message ("benchmark: aggiorna il calcolo in pricing.py") gives no rationale for a second discount; the docstring at pricing.py:18 was not updated; pricing.py has no second discount function (the only other discount, `volume_discount` at shipping/rates.py:15, is a shipping rate that compute_total does not call); no guard or clamp on loyalty_percent or on a negative net exists in pricing.py or service.py; no test pins the total; ground_truth.json C1 (:15) and CASES.md:7 describe `compute_discount` as the single customer discount; the second call does not apply a different rule, because `compute_discount` is pure and returns the same value both times.
- fix direction: restore one subtraction, `net = order.get("net", 0) - compute_discount(order)`. If a second reduction is really wanted, give it its own named function and rule, and update pricing.py:18. Add a behavioral test of `compute_total` with `loyalty_percent > 0` (e.g. net 100, loyalty 10 -> 109.8), since the current suite cannot catch this.
- routing: the mechanism is local arithmetic (local-correctness-auditor). data-representation-auditor (wrong and negative money persisted in ledger.log) and api-contract-auditor (docstring contract of compute_total and the checkout return value) add consequences, not separate findings.

### Effects on the benchmark (checked, no finding)

The change keeps symbols, imports, the `compute_total -> compute_discount` call edge and the line numbers cited by ground_truth.json (pricing.py:11, :19; service.py:26; reporting.py:11). The expected perimeters of C1, C5 and C8, and the assertions in test_app_structures.py:62-72, still hold. reporting.py reads only `pricing.VAT_RATE`, and gateway.py reads `order["total"]`, which `checkout` never sets, so neither is affected. The change alters the fixture's runtime behavior, not the static structure the benchmark measures.

## member_results

| specialist_id | status | coverage | findings | checks done / why not applicable | gaps |
|---|---|---|---|---|---|
| local-correctness-auditor | delivered | complete | F1 | arithmetic, units, rounding, zero/empty/negative bounds, pure-function repeat, return value to the caller | no behavioral tests |
| local-concurrency-auditor | delivered | complete | - | pricing functions are pure, with no shared state; the ledger lockfile (ledger.py:9-10) is unchanged and was not touched by the candidate | - |
| input-validation-auditor | delivered | complete | - | order values are used only arithmetically, with no interpreting sink; loyalty_percent is unbounded already at base, and no stated limit exists to violate (author question Q2) | no stated range |
| resource-lifecycle-auditor | delivered | complete | - | the changed code acquires no resource; ledger.record's lock and file are released in `finally` (ledger.py:19-21) and unchanged | - |
| algorithmic-cost-auditor | delivered | complete | - | the extra `compute_discount` call is O(1), with no throughput requirement; its only effect is F1 | - |
| authorization-auditor | delivered | complete | - | no principal, grant or resource access in scope | - |
| session-delegation-auditor | delivered | complete | - | no credentials or sessions in scope | - |
| secret-exposure-auditor | delivered | complete | - | no secrets or crypto; the ledger writes order id and total only | - |
| untrusted-resource-auditor | delivered | complete | - | no caller-controlled path or URL; LEDGER_PATH is fixed (ledger.py:5) | - |
| browser-security-auditor | delivered | complete | - | no browser surface | - |
| callback-authenticity-auditor | delivered | complete | - | api.py callbacks are an in-process registry, not signed external callbacks; unchanged | - |
| ai-boundary-auditor | delivered | complete | - | no model context or tool authority in scope | - |
| audit-trail-auditor | delivered | complete | - | ledger.log records the F1 total, but no approved audit obligation is supplied; the wrong value is F1's consequence, routed there | no audit policy |
| capacity-quota-auditor | delivered | complete | - | no admission, queue or quota in scope | - |
| transaction-integrity-auditor | delivered | complete | - | the ledger append is unchanged; the persisted wrong value comes from arithmetic (F1), not from a transaction boundary | - |
| schema-coherence-auditor | delivered | complete | - | no DDL, ORM or SQL in the app | - |
| cache-consistency-auditor | delivered | complete | - | no cache or derived store | - |
| data-representation-auditor | delivered | complete | F1 (consequence) | money as float rounded to 2 decimals at each step: no new precision loss beyond base; the meaning changes (short and negative totals and VAT persisted in ledger.log), routed to F1 | - |
| data-retention-auditor | delivered | complete | - | no deletion or expiry path changed; no retention policy supplied | no retention policy |
| chicken-egg-detector | delivered | complete | - | no startup or initialization change; register_defaults is unchanged | - |
| temporal-resilience-auditor | delivered | complete | - | no timers, retries or background jobs | - |
| message-delivery-auditor | delivered | complete | - | no broker; notifications.send_via (notifications.py:18) receives the order, not the total, and is unchanged | - |
| remote-effect-auditor | delivered | complete | - | the total reaches no external effect: payments/gateway.py:10, :15 read `order["total"]`, which checkout never sets (preexisting disconnect, not in the changed path) | - |
| service-resilience-auditor | delivered | complete | - | no cross-service calls | - |
| environment-binding-auditor | delivered | complete | - | no configuration or environment selection; VAT_RATE is a constant (pricing.py:3) | - |
| api-contract-auditor | delivered | complete | F1 (consequence) | the compute_total docstring contract (pricing.py:18) is violated by the candidate; checkout's return reaches the dispatcher's caller (api.py:29-31); routed to F1 | - |

## Questions for the author

1. benchmarks/scope-resolution/app/packages/orders/pricing.py:19: is the second `- compute_discount(order)` intended? If it stands for a second discount, which rule, and what should the docstring at pricing.py:18 say?
2. benchmarks/scope-resolution/app/packages/orders/pricing.py:13: what range does `loyalty_percent` admit? With the candidate, values above 50 produce negative totals and negative VAT (pricing.py:20); at base this happened only above 100.
3. benchmarks/scope-resolution/README.md:3-4: is a change to the fixture's runtime behavior meant to stay in `app/`? The README describes `app/` only as the scope-resolution fixture and declares no behavior change.
