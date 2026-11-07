# job-01 report: branch-943bdc44c

Paths: `A` = `benchmarks/scope-resolution/app/packages`. Candidate 943bdc44c, base 6dd2c2bbf. All evidence is static reading (no execution grant): `derived`.

## Result envelope

```yaml
dimension: correctness (security assessed: no applicable construct)
reviewer: senior-review:code-auditor (member run: senior-review:local-correctness-auditor)
status: delivered
output_path: OUT/jobs/job-01.md
findings: [J01-F1, J01-F2]
gaps: see ## gaps
knowledge_usage:
  - {selection: af96a6fdd282cd2ad38586a7a9c30fafbe748ec8f0df4238c5dbd5cf0a38a97c, worker: job-01, scope: branch-943bdc44c, knowledge_id: senior-review:defect-taxonomy, file: SKILL.md, sha256: 92c07a4ec219d5c2a3ae0c29fa699a8b15f453f833116cf912095716faeba514, status: loaded, applied: "Python weighting -> logic-types.md; security.md not loaded (no input sink, secret, path or markup in the changed line)"}
  - {selection: af96a6fdd282cd2ad38586a7a9c30fafbe748ec8f0df4238c5dbd5cf0a38a97c, worker: job-01, scope: branch-943bdc44c, knowledge_id: senior-review:defect-taxonomy, file: SKILL.toml, sha256: 877fe2575eab9d0e4719b4a04b202575431cf8a07311132d2777104f74bc21dc, status: loaded, applied: "metadata only (dimensions correctness, security)"}
  - {selection: af96a6fdd282cd2ad38586a7a9c30fafbe748ec8f0df4238c5dbd5cf0a38a97c, worker: job-01, scope: branch-943bdc44c, knowledge_id: senior-review:defect-taxonomy, file: references/review-frameworks.md, sha256: a482e0daeb031e76a954805ef58ad8efd508652e3015a0ef2350692d18829de5, status: loaded, applied: "severity table: CRITICAL example 'silent wrong output' considered for J01-F1, capped at High (derived evidence only, intent unknown); execution protocol steps 1-7"}
  - {selection: af96a6fdd282cd2ad38586a7a9c30fafbe748ec8f0df4238c5dbd5cf0a38a97c, worker: job-01, scope: branch-943bdc44c, knowledge_id: senior-review:defect-taxonomy, file: references/logic-types.md, sha256: 9667a3fcb39031a376c4087f05e46b1536e3c8c25da2ddbde5ae590fd89865d2, status: loaded, applied: "3.8 boundary conditions (loyalty_percent 0/50/100/>100, net 0/<0, missing keys) -> J01-F2; 4.3 currency rounding -> checked: both calls return the same rounded d, no new rounding step, no finding; CWE-682 mapping for J01-F1"}
```

All four hashes equal those in `knowledge/selection.json`.

## Answers

- **Q1 (H1, S8, D1-D3, D6): it subtracts the discount twice.** `A/orders/pricing.py:19` @943bdc44c: `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`. `compute_discount` (`:11-14`) reads `order` only through `.get` and mutates nothing, and in `OrderService.checkout` nothing runs between the two calls (`DefaultPipeline.step` runs after, `A/orders/service.py:26-27`). So both calls return the same d. The result is net − 2d. The unchanged contract at `:18` ("netto - sconto cliente + IVA") and base `:19` @6dd2c2bbf have one discount term. Two calls to the same pure function with the same input cannot add a different, second discount. → J01-F1.
- **Q2 (H2, D2): no.** VAT is `vat_amount(net)` on net − 2d (`:20`, `:6-8`). Against the one-discount base, VAT is too low by 0.22·d (±0.01 from rounding), and the total by about 1.22·d. Example: net 100, loyalty 10 → d 10.0. Base: taxable 90, VAT 19.8, total 109.8. Candidate: 80, 17.6, 97.6. With `loyalty_percent` 0 or missing, or net 0, both sides give the same result. Part of J01-F1.
- **Q3 (H3, D1, D4): taxable net ≤ 0 for net > 0 once loyalty_percent ≥ 50.** It is zero at 50, within the 0.01 rounding of d, and negative above 50. On base it goes negative only above 100. Examples: p 50 → total 0.0 (base 61.0); p 60 → −24.4 with VAT −4.4 (base 48.8); p 100 → −122.0 (base 0.0). Nothing rejects or clamps the value. The dispatcher passes the payload as-is (`A/orders/api.py:4,25-27`). Neither `compute_discount` nor `compute_total` checks the range. `checkout` stores the value (`A/orders/service.py:26`), `ledger.record` writes `f"{id}\t{total}"` for any value (`A/orders/ledger.py:18`), and `checkout` returns it (`service.py:30`). With negative net (also unvalidated, preexisting), p > 50 flips the sign to a positive total. → J01-F2.
- **Q4 (S2, S3, S7, D4, D5, H4):** in the tree the value reaches three places, all through `checkout`. (a) The return value of `checkout` (`service.py:30`). (b) The ledger line `<id>\t<total>` (`ledger.py:18`). (c) The `checkout` callback result, via `Dispatcher.handle` → `_invoke` → `EVENT_REGISTRY["checkout"](payload)` (`api.py:25-31,37`). `git grep` @943bdc44c finds no other caller of `compute_total`/`compute_discount` in `*.py`. `reporting.py:11` uses only `pricing.VAT_RATE`, and its `row['total']` (`:14`) comes from the caller. `refunds.issue_refund` takes a caller-supplied amount and has its own `VAT_RATE` (`A/payments/refunds.py:7,15-21`). `notifications.send_via` gets the `order` dict, and `checkout` never writes the total into it (`service.py:23-30`). `gateway.py:10,15` reads `order.get("total", 0)`, and nothing in the tree writes `order["total"]`. Whether out-of-tree code (env-configured notification handlers, `notifications.py:11-15`; callers that copy the return value into `order["total"]`) depends on the value is not visible (gap). No test checks the value: the only test hit, `benchmarks/scope-resolution/test_app_structures.py:71`, is a text check.

## findings

### J01-F1 — compute_total subtracts the loyalty discount twice (Q1, Q2)

- file: `benchmarks/scope-resolution/app/packages/orders/pricing.py`
- line: 19 (@943bdc44c)
- evidence: `:19` @943bdc44c subtracts `compute_discount(order)` twice. `:18` (unchanged) specifies "netto - sconto cliente + IVA". Base `:19` @6dd2c2bbf subtracts it once. `compute_discount` is pure (`:13-14`), so the result is net − 2d. VAT (`:20`, `:6-8`) is then computed on that understated base. The understated total is persisted (`A/orders/ledger.py:18`) and returned (`A/orders/service.py:30`, `A/orders/api.py:27`). The commit message ("benchmark: aggiorna il calcolo in pricing.py") gives no reason.
- severity: High. A wrong monetary amount is silently recorded and returned for every order with loyalty_percent ≠ 0, with no error signal. Not Critical: the evidence is derived only and the intent is unstated.
- confidence: 85
- fix direction: restore `net = order.get("net", 0) - compute_discount(order)`. If a second discount is really wanted, write it as its own rule, update the docstring at `:18`, and add a numeric test for `compute_total` (e.g. net 100, loyalty 10 → 109.8 under the single-discount rule).
- premise: for an order with net ≠ 0 and loyalty_percent ≠ 0, `compute_total` @943bdc44c computes its taxable net as net − 2·compute_discount(order), and no repository source specifies more than the single "sconto cliente" term of `pricing.py:18`.
- premise_provenance: independent (re-derived from pricing.py at both revisions, service.py, ledger.py, api.py and a `git grep` of consumers; 01-context H1 only raised the question)
- trigger: `Dispatcher.handle("checkout", {"net": 100, "loyalty_percent": 10, "sku": ..., "qty": ..., "id": ...})` returns and records 97.6 instead of 109.8
- counterevidence_checked: commit message (no reason given); docstrings `pricing.py:1,12,18` (one discount); any second discount source (none: same function, same input); any add-back downstream in `checkout`/`ledger.record` (none); a test fixing the expected total (none; `test_app_structures.py:71` is text-only); other callers that could expect the new value (none in tree)
- introduced_by_candidate: true
- evidence_class: derived
- CWE: 682 (Incorrect Calculation)

### J01-F2 — the candidate makes zero and negative totals reachable for 50 ≤ loyalty_percent ≤ 100 (Q3)

- file: `benchmarks/scope-resolution/app/packages/orders/pricing.py`
- line: 19 (@943bdc44c); consequence at `A/orders/service.py:26-30`, `A/orders/ledger.py:18`
- evidence: for net > 0, taxable net = net·(1 − 2p/100) up to the rounding of d. It is ≤ 0 for p ≥ 50 on the candidate, but only for p > 100 on base (`pricing.py:19` @6dd2c2bbf). No range guard or clamp exists in `compute_discount` (`:11-14`), `compute_total` (`:17-20`), `checkout` (`service.py:23-30`), `DefaultPipeline.step` (only sets `validated`, and runs after the total, `service.py:13-15,27`) or the dispatcher (`api.py:4,25-27`). Examples: p 60 → total −24.4, VAT −4.4, ledger line `<id>\t-24.4`; p 100 → −122.0 (base 0.0); p 50 → 0.0 (base 61.0).
- severity: Medium. It needs loyalty_percent ≥ 50, and no domain constraint was found that allows or forbids such values. Once triggered, the ledger gets a negative sale amount and negative VAT. Same root line as J01-F1, reported separately because the sign defect remains even if the double discount turns out to be intended.
- confidence: 75
- fix direction: fixing J01-F1 brings the threshold back to p > 100. If a non-positive total is never valid, also reject loyalty_percent outside 0..100 or a taxable net below 0 before `ledger.record` (that guard is missing on base too).
- premise: with net > 0 and 50 < loyalty_percent ≤ 100, `compute_total` @943bdc44c returns a negative value, and no code between `Dispatcher.handle` and `ledger.record` rejects or clamps it.
- premise_provenance: independent
- trigger: checkout payload `{"net": 100, "loyalty_percent": 60, ...}` → checkout returns and records −24.4
- counterevidence_checked: validation of `loyalty_percent`/`net` in pricing.py, service.py, api.py, DefaultPipeline (none); `max(..., 0)` or a sign check (none); `ledger.record` accepts any value (`ledger.py:13-22`); documents limiting loyalty_percent to < 50 (none found)
- introduced_by_candidate: true for 50 ≤ p ≤ 100. The negative total for p > 100 and the missing range guard are preexisting.
- evidence_class: derived
- CWE: 682; taxonomy 3.8 boundary conditions

## member_results

| Specialist ID | Status | Coverage | Findings | Gaps / notes |
|---|---|---|---|---|
| senior-review:local-correctness-auditor | delivered | complete (Q1-Q4) | J01-F1, J01-F2 | static only; out-of-tree consumers unknown |
| senior-review:local-concurrency-auditor | delivered | not-applicable per 02-selection.md | — | consistent: in process nothing mutates `order` between the two calls; concurrent mutation of a shared payload would be preexisting, not examined |
| senior-review:input-validation-auditor | delivered | not-applicable per 02-selection.md | — | consistent: no syntax or executable sink; the missing loyalty range check is a domain bound (J01-F2), not input-to-sink |
| senior-review:resource-lifecycle-auditor | delivered | not-applicable per 02-selection.md | — | consistent for the diff; see Cross-Reviewer Notes for the preexisting ledger lock |
| senior-review:algorithmic-cost-auditor | delivered | not-applicable per 02-selection.md | — | consistent: one extra O(1) pure call |
| senior-review:authorization-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:session-delegation-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:secret-exposure-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:untrusted-resource-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:browser-security-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:callback-authenticity-auditor | delivered | not-applicable per 02-selection.md | — | consistent: `on_event` is in-process registration, no signed callback |
| senior-review:ai-boundary-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:audit-trail-auditor | delivered | not-applicable per 02-selection.md | — | consistent: the ledger line changes value, not attribution or framing |
| senior-review:capacity-quota-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:transaction-integrity-auditor | delivered | not-applicable per 02-selection.md | — | consistent for the diff; preexisting stock/ledger non-atomicity in Cross-Reviewer Notes |
| senior-review:schema-coherence-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:cache-consistency-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:data-representation-auditor | delivered | not-applicable per 02-selection.md | — | consistent: `ledger.py:18` format unchanged |
| senior-review:data-retention-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:chicken-egg-detector | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:temporal-resilience-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:message-delivery-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:remote-effect-auditor | delivered | not-applicable per 02-selection.md | — | possible reach through out-of-tree `order["total"]` writers to `gateway.py:10,15` (gap, Cross-Reviewer Notes) |
| senior-review:service-resilience-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:environment-binding-auditor | delivered | not-applicable per 02-selection.md | — | — |
| senior-review:api-contract-auditor | delivered | not-applicable per 02-selection.md | — | consistent: signature unchanged; the docstring contract is covered by J01-F1 |

The code read contradicts no 02-selection.md reason.

## Examined scope and completed checks

- Read @943bdc44c: `A/orders/pricing.py`, `service.py`, `ledger.py`, `api.py`, `notifications.py`, `inventory.py`, `reporting.py`; `A/payments/gateway.py`, `refunds.py`; `A/shipping/rates.py`. Read @6dd2c2bbf: `A/orders/pricing.py`. `git diff 6dd2c2bbf 943bdc44c` confirms service.py, ledger.py and api.py are unchanged. `git grep` @943bdc44c for consumers of `compute_total`/`compute_discount`/`pricing`/`total` in `*.py`. `big_module.py` checked by grep only (no `pricing` import).
- Checks done: arithmetic and units (net − d vs net − 2d, VAT base); precision and rounding (d rounded once per call, both values equal); bounds (p 0/missing, net 0/missing, p 50, 50 < p ≤ 100, p > 100, net < 0); purity and aliasing (no mutation by `compute_discount`; pipeline runs after); error paths (missing keys give 0 as on base; non-numeric values raise TypeError as on base); outcome returned to the caller and persisted (checkout, ledger, dispatcher); consumers in the tree.
- Map: no map query run. Context S2/S3/S7 used as leads only and re-derived with `git grep` and source reading.

## gaps

- Not run (no reproduction grant): every number is derived.
- Intent unknown. Question for the author: "Is the double subtraction of the loyalty discount intended? If so, what is the second discount, and should the docstring at pricing.py:18 change?"
- Out-of-tree consumers not visible: handlers configured by `ORDER_NOTIFY_HANDLERS` (`notifications.py:11-15`), callers of `Dispatcher.handle`, and writers of `order["total"]` read by `gateway.py:10,15`.
- Valid range of `loyalty_percent`: no requirement found. This limits J01-F2's severity.
- Not read: benchmark fixture documents (`CASES.md`, `ground_truth.json`, `results/`), to keep the review independent of benchmark expectations. 01a reports they state no numeric requirement, and no premise here depends on them.
- From the scope: Python baseline missing; mypy/pyright absent (types of `net`/`loyalty_percent` not checked); `codebase_map_graph` failed (S4), so `git grep` was used instead.

## Cross-Reviewer Notes

- logic-integrity (selection gap): this job checks only the local docstring rule. Two cross-component questions are uncovered: whether any domain document requires a single loyalty discount, and whether the amount charged by payments matches the ledger.
- Tests: nothing numeric exercises `compute_total`, `compute_discount` or `vat_amount`. `test_app_structures.py:71` checks only the text `def compute_discount(`, so the passing structure suite (11 passed on both sides) cannot detect J01-F1.
- Preexisting, outside `conclusion_paths`, unchanged by the candidate, not findings:
  - `service.py:25` @943bdc44c discards the `False` that `reserve_stock` returns (`inventory.py:21-22`), so checkout records a ledger line even when stock is insufficient.
  - `ledger.py:9-10,15` opens the lock with `O_EXCL`, which raises `FileExistsError` when `ledger.lock` already exists. That happens after stock was reserved at `service.py:25`, which is left decremented. Owners: resource-lifecycle and transaction-integrity.
- remote-effect / logic-integrity: if out-of-tree code copies `checkout`'s return value into `order["total"]`, `gateway.charge` charges the double-discounted, possibly negative, amount (`gateway.py:10,15,24-27`).

declined: []

## Created files

- `OUT/jobs/job-01.md` (this report)
