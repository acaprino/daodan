# job-01: local correctness, branch-943bdc44c-simplified

## Envelope

- `dimension`: local-correctness
- `reviewer`: senior-review:local-correctness-auditor
- `status`: delivered
- `findings`: [LC-01]
- `gaps`: see Gaps
- `output_path`: OUT/jobs/job-01.md
- `knowledge_usage`: []
- Candidate `943bdc44c66dfd9782f6d38c82922a1f08783653` confirmed by `git rev-parse HEAD` in the work tree; base `6dd2c2bbf`. Basis: changeset.

## Findings

### LC-01: `compute_total` subtracts the customer discount twice

- `file`: `benchmarks/scope-resolution/app/packages/orders/pricing.py`
- `line`: 19
- `severity`: High
- `confidence`: 92
- `evidence`: `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`. The docstring on line 18, unchanged, states "netto - sconto cliente + IVA (VAT)": one discount. `compute_discount` (lines 11-14) reads `order` only, so the second call returns the same value: the effect is exactly 2x the discount, not a compounded one. The doubled `net` then feeds `vat_amount(net)` on line 20, so the VAT is also computed on an understated base.
- Effect path: `Dispatcher.handle("checkout", order)` (`app/packages/orders/api.py:29-31`, wired at `api.py:37`) -> `OrderService.checkout` (`app/packages/orders/service.py:26`) -> written to the append-only ledger (`service.py:28`, `app/packages/orders/ledger.py:17-18`) and returned to the dispatcher caller (`service.py:30`). `ledger.record_refund` stores no amount (`ledger.py:30`), so the ledger has no correcting entry for a wrong total.
- Incorrect result, hand-computed from the source, not executed:

| `net` | `loyalty_percent` | Base total | Candidate total | Note |
|---|---|---|---|---|
| 100 | missing or 0 | 122.0 | 122.0 | no difference, so orders without loyalty hide the defect |
| 100 | 10 | 109.8 | 97.6 | short by 12.2, which is discount x 1.22 |
| 100 | 50 | 61.0 | 0.0 | order becomes free |
| 100 | 60 | 48.8 | -24.4 | negative total and negative VAT; base goes negative only above 100% |

- Fix direction: restore the single subtraction, `net = order.get("net", 0) - compute_discount(order)`. If a doubled discount is really required, the author must state it, update the docstrings on lines 12 and 18, and decide the behaviour above 50%. Either way, add a test that calls `compute_total` with a non-zero `loyalty_percent`: none exists today.
- `premise`: the contract of `compute_total` applies the customer discount exactly once.
- `premise_provenance`: independent (lines 12, 13 and 18 and the base line, read directly; the map packet was used only to locate callers).
- `trigger`: any order with non-zero `net` and non-zero `loyalty_percent` reaching `compute_total`, for example `{"net": 100, "loyalty_percent": 10, "sku": "demo-sku", "qty": 1}` through the `checkout` event.
- `counterevidence_checked`:
  - Second discount concept in pricing: none. The only other discount is `volume_discount` (`app/packages/shipping/rates.py:15`), used only by `quote` in that file on the shipping rate.
  - Stated reason: commit subject and body give none. Search for `doppio|due volte|double|twice|raddopp|cumul|stack` in the benchmark's py, md, json and toml files, excluding `results/` and `big_module.py`: no hits.
  - Upstream compensation or downstream clamp: `loyalty_percent` occurs only at `pricing.py:13`; nothing halves it or clamps `net` or the total before the ledger write.
  - Cases: `CASES.md` C1 and the `ground_truth.json` C1 and C5 rationales name this chain but define no formula, so they neither support nor refute the doubling.
  - Tests: `test_app_structures.py` only imports `orders.api` (line 23) and checks text (line 71); `test_resolver.py` does not call pricing. The settled "11 passed" therefore does not exercise this line and does not refute the finding.
- `introduced_by_candidate`: true
- `evidence_class`: derived
- Severity note: High for the app's own contract, because every loyalty order gets a wrong persisted money amount. The app is a benchmark fixture and is not shipped, so no real money is at stake; the derived numbers would not justify Critical anyway.

## Completed checks

- Reachability and multiplicity: `service.py:26` is the only caller found by text search under `benchmarks/scope-resolution`, excluding `results/`; this agrees with the packet. `reporting.py:11` reads only `VAT_RATE`. `gateway.py:10,15` read `order["total"]`, which nothing in the app sets, so the candidate's value does not reach payment. Notifications receive `order`, not the total.
- Packet blind spot `order.get` (unknown receiver): resolved by reading; `order` is the event payload and the code treats it as a dict.
- Bounds: missing or zero `loyalty_percent`, missing `net`, 50%, above 50%, tabulated above and part of LC-01. There is no separate defect.
- Coercion and null: `None` or string values raise `TypeError` at the same expressions in base and candidate; no change. No caller shows such input is valid.
- Rounding and precision: per-step `round()` on binary floats is preexisting and line 20 is unchanged; no requirement is violated, so no finding.
- Precedence, initialization, scope, aliases, mutation: left-associative subtraction, one local variable, no mutation in pricing. The extra call adds no side effect.
- Failure paths: no new raise, catch or I/O in the changed line. Exception conditions match base.

## Gaps

- No execution granted: every number above is hand-computed.
- Map tools not in my tool set. I used the saved packet from run `daodan-lite-20261107-2`, bound to an earlier revision, with `edge_view_coverage: missing_store`, and confirmed callers by text search.
- No pricing requirement exists outside the code: the requirement rests on docstrings and base behaviour.
- Not assessed, other owners: invariant and tax semantics (logic-integrity), staleness of cases, ground truth and frozen results (artifact-lifecycle).

## Out of finding scope, not findings

Preexisting and not effects of this change; they may be deliberate fixture shapes.
- `service.py:25` discards the `False` from `reserve_stock` (`inventory.py:21-22`), so an out-of-stock order is still totalled and recorded.
- `gateway.py:10,15` default the charge to 0 because `checkout` never stores `order["total"]`.

## member_results

| Specialist | Delivery | Coverage | Finding IDs | Gaps |
|---|---|---|---|---|
| senior-review:local-correctness-auditor | delivered | complete | LC-01 | no execution; saved map packet only |
