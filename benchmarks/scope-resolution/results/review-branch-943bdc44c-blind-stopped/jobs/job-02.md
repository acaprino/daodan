# job-02: logic integrity, branch-943bdc44c-simplified

## Envelope

- dimension: logic-integrity
- reviewer: senior-review:logic-integrity-auditor
- status: delivered
- findings: [LI-01]
- gaps: G1-G5 below
- output_path: OUT/jobs/job-02.md
- knowledge_usage: []
- candidate 943bdc44c, base 6dd2c2bbf, basis changeset, static inspection only (no run grant)

## member_results

| Specialist | Delivery | Coverage | Findings | Gaps |
|---|---|---|---|---|
| senior-review:logic-integrity-auditor | delivered | complete | LI-01 | G1-G5 |

## Finding LI-01: customer discount subtracted twice from every discounted order total

- L-category: L4 (domain money rule), with L1.2 (unkept postcondition of `compute_total`)
- file: benchmarks/scope-resolution/app/packages/orders/pricing.py
- line: 19
- severity: High. The taxonomy rates a silent financial error Critical. It is held at High because the evidence is derived and the app is a benchmark fixture with no in-repo caller of its public entry.
- confidence: 93 (the remaining doubt is author intent, see G3)
- evidence: `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`
- rule evidence:
  - `pricing.py:18`, unchanged by the commit: "Totale ordine: netto - sconto cliente + IVA (VAT)", one discount term.
  - `pricing.py:12`: the customer discount is one loyalty percentage applied to the net.
  - Base line 19 subtracted it once.
  - Context anchors: `01-context.md`, stated contracts rows `orders/pricing.py:12` and `:18`.
- violated location: `pricing.py:19`. `pricing.py:20` then computes VAT on the reduced `net`, so the VAT is understated too.
- actors and sequence:
  1. A caller invokes `Dispatcher.handle("checkout", order)` (`orders/api.py:29`) after `register_defaults()` registered `service.checkout` (`orders/api.py:37`), or calls `OrderService.checkout` directly.
  2. `orders/service.py:26` calls `pricing.compute_total(order)`.
  3. `pricing.py:19` subtracts the same discount twice. `compute_discount` is pure and `order` is not mutated between the calls, so both calls return the same value.
  4. `orders/service.py:28` passes the total to `ledger.record`, and `orders/ledger.py:18` appends it to `ledger.log`.
  5. `orders/service.py:30` returns it to the caller.
- trigger: an order with `net` != 0 and `loyalty_percent` != 0. With no loyalty, base and candidate agree, so a no-discount smoke check cannot see the defect.
- observable symptom (hand-derived, not executed):

| net | loyalty_percent | base total | candidate total |
|---|---|---|---|
| 100 | 0 | 122.0 | 122.0 |
| 100 | 10 | 109.8 (VAT 19.8) | 97.6 (VAT 17.6) |
| 100 | 50 | 61.0 | 0.0 |
| 100 | 60 | 48.8 | -24.4 |

  - The undercharge is 1.22 x the discount.
  - The total turns negative above 50% loyalty (base: above 100%). No guard bounds `loyalty_percent`. The project states no legal range, so this is a conditional consequence, not a separate rule.
  - The ledger entry is written before `notifications.send_via` (`orders/service.py:29`), so the wrong amount persists even when that step raises `KeyError` on an unset `ORDER_NOTIFY_HANDLERS` (`orders/notifications.py:13`).
- premise: no requirement or contract in scope authorizes applying the customer discount twice to one order.
- premise_provenance: independent (re-derived from candidate source and `git show 6dd2c2bbf:...pricing.py`)
- counterevidence_checked:
  - The commit message gives no reason, and the docstring was not updated with the formula.
  - No requirement document states a double discount; text search covered `CASES.md`, `ground_truth.json` and the benchmark `*.py` (`README.md`: "sconto" only as a sample search term). `ground_truth.json:15` cites the call chain only.
  - The second term is not another discount: it is the same call with the same argument. `volume_discount` (`packages/shipping/rates.py:15`) belongs to shipping quotes and is not used here.
  - No later correction: `pipeline.step` runs after the total is computed and does not touch it; `ledger.record` stores it as received.
  - No alternate path keeps a correct value: `compute_total` has one definition and one call site.
  - The tests do not refute it: the 11 passing tests in `test_app_structures.py` check structure and importability only.
- introduced_by_candidate: true
- evidence_class: derived
- fix direction:
  - Restore one subtraction: `net = order.get("net", 0) - compute_discount(order)`.
  - If a double discount was intended, state that rule at `pricing.py:18` and in a requirement.
  - Either way, add an amount test with `loyalty_percent` > 0 through `compute_total`.

## Applicable categories and checks

| Cat. | Result |
|---|---|
| L1 | LI-01. Preconditions and signature unchanged. |
| L2 | Multiplicity settled inside the repo: one `compute_total`, one static caller (`service.py:26`), one dynamic registration (`api.py:37`), one writer of amounts (`ledger.py:18`). `OrderService` in `tests/test_xray_snapshot.py:37` is that test's own class. No other total computation or reconciliation exists. Outside the repo: G2. |
| L3 | `compute_discount` purity holds (`pricing.py:11-14`). The "second call sees the reduced net" reading is false: it reads `order["net"]`, which is never reassigned. |
| L4 | LI-01. |
| L5 | Step order in `checkout` unchanged; no forbidden state added by the candidate. |
| L6 | Not compounding: `order` keeps its `net`, so a repeated call gives the same wrong value. No new repeated effect. |
| L7 | No transition or terminal state changed; not applicable to this change. |
| L8 | Ledger line format and two-decimal rounding unchanged. Negative amounts are reachable sooner (see LI-01); no in-app code parses `ledger.log` (`LEDGER_PATH` appears only in `ledger.py`). |

Examined anchors, under `benchmarks/scope-resolution/`:

- `app/packages/orders/pricing.py`, `service.py`, `ledger.py`, `api.py`, `reporting.py`, `inventory.py`, `notifications.py`
- `app/packages/payments/gateway.py`, `refunds.py`; `app/packages/shipping/rates.py`
- `test_app_structures.py`; greps of `ground_truth.json`, `CASES.md`, `README.md`
- `OUT/tools/edit-impact.json`; the base line via `git show`

## Gaps

- G1, map: the Codebase Map tools and ToolSearch were not available in this session, so there is no error text to record. Used the saved `OUT/tools/edit-impact.json` as a lead and text search on the work tree. The context also reports a stale index and no base/candidate snapshot pair.
- G2, downstream reach unverifiable: nothing in the app assigns `order["total"]`, and `register_defaults`, `Dispatcher.handle`, `gateway.charge`, `format_daily_summary` and `issue_refund` have no in-repo caller. Whether the wrong total reaches a charge, report or refund depends on callers outside the repo; not claimed.
- G3, intent: the "why" is unknown and no separate requirement document exists. The rule rests on the docstrings and the base code.
- G4, runtime: no run grant, so the values are hand-derived and unexecuted.
- G5, tests: no test exercises amounts. Reported here as a gap because no testing specialist is in the base.

## Preexisting lead, outside the conclusion path (not a finding)

`orders/service.py:25` ignores the `False` that `reserve_stock` returns on insufficient stock (`orders/inventory.py:21-22`), so such an order still reaches pricing and the ledger. Not touched by the candidate.
