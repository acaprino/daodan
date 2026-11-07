# Consolidated findings: branch-943bdc44c

Candidate 943bdc44c, base 6dd2c2bbf, review basis changeset. Inputs: `jobs/job-01.md` (job-01, `senior-review:code-auditor`, member `senior-review:local-correctness-auditor`, delivered). Delivery ledger: 1/1 jobs delivered; 26/26 members accounted (1 complete, 25 not-applicable per `02-selection.md`).

Consolidation rules applied: no duplicates (one reviewer); J01-F1 and J01-F2 share `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` with different failure modes: **co-located**, kept separate. Corroboration: none possible (one independent reviewer); echoes: none. `[MAP-GAP]` findings: none (no logic-integrity reviewer ran). Verification (Phase 4b, `98-verification.md`): J01-F1 verified, High (Lens 3 High); J01-F2 verified, Medium (Lens 3 Medium); both `reproduced` by Lens 1; 0 filtered, 0 contested, 0 premise-refuted.

## Critical (0)

## High (1)

### J01-F1: `compute_total` subtracts the loyalty discount twice
- Location: `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` @943bdc44c (co-located with J01-F2)
- Category: local correctness, incorrect calculation (CWE-682)
- Question: Q1, Q2 (01-context.md H1, S8, D1-D3, D6)
- Evidence: `:19` subtracts `compute_discount(order)` twice; the unchanged docstring `:18` "netto - sconto cliente + IVA" and base `:19` @6dd2c2bbf subtract it once; `compute_discount` is pure (`:13-14`); VAT is then computed on the understated net (`:20`, `:6-8`); the total is persisted (`benchmarks/scope-resolution/app/packages/orders/ledger.py:18`) and returned (`benchmarks/scope-resolution/app/packages/orders/service.py:30`, `benchmarks/scope-resolution/app/packages/orders/api.py:27`). Derived example: net 100, loyalty 10 gives 97.6 instead of 109.8.
- Severity: High (native; Lens 3 vote High). Confidence: 85. evidence_class: reproduced (Lens 1; reviewer: derived). introduced_by_candidate: true. Flag: verified.
- Premise: "for an order with net ≠ 0 and loyalty_percent ≠ 0, `compute_total` @943bdc44c computes its taxable net as net − 2·compute_discount(order), and no repository source specifies more than the single "sconto cliente" term of `pricing.py:18`." Provenance: independent.
- Trigger: `Dispatcher.handle("checkout", {"net": 100, "loyalty_percent": 10, ...})` returns and records 97.6 instead of 109.8.
- Fix direction: restore `net = order.get("net", 0) - compute_discount(order)`; if a second discount is intended, model it as its own rule, update the docstring and add a numeric test for `compute_total`.

## Medium (1)

### J01-F2: zero and negative totals reachable for 50 ≤ loyalty_percent ≤ 100
- Location: `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` @943bdc44c; consequence at `benchmarks/scope-resolution/app/packages/orders/service.py:26-30`, `benchmarks/scope-resolution/app/packages/orders/ledger.py:18` (co-located with J01-F1)
- Category: local correctness, boundary condition (CWE-682; taxonomy 3.8)
- Question: Q3 (01-context.md H3, D1, D4)
- Evidence: taxable net = net·(1 − 2p/100) for net > 0, ≤ 0 for p ≥ 50 on the candidate versus p > 100 on base; no guard or clamp in pricing, checkout, `DefaultPipeline.step` or the dispatcher. Derived examples: p 60 gives −24.4 (VAT −4.4); p 100 gives −122.0 (base 0.0); p 50 gives 0.0 (base 61.0).
- Severity: Medium (native; Lens 3 vote Medium). Confidence: 75. evidence_class: reproduced (Lens 1; reviewer: derived). Flag: verified; Lens 0 premise_form non-compliant (minimal premise re-derived, HOLDS). introduced_by_candidate: true for 50 ≤ p ≤ 100 (the missing guard and negatives above 100 are preexisting).
- Premise: "with net > 0 and 50 < loyalty_percent ≤ 100, `compute_total` @943bdc44c returns a negative value, and no code between `Dispatcher.handle` and `ledger.record` rejects or clamps it." Provenance: independent.
- Trigger: checkout payload `{"net": 100, "loyalty_percent": 60, ...}` returns and records −24.4.
- Fix direction: fixing J01-F1 restores the base threshold (p > 100); a range check on `loyalty_percent` or on the taxable net before `ledger.record` if non-positive totals are never valid.

## Low (0)

## Cross-reviewer notes (not findings)
- Logic-integrity selection gap: domain rule "one loyalty discount" across documents, and payment amount versus ledger, are uncovered (job-01).
- Testing: no numeric test exercises `compute_total`/`compute_discount`/`vat_amount`; `benchmarks/scope-resolution/test_app_structures.py:71` is a text check (job-01).
- Preexisting, outside `conclusion_paths`, unchanged: `service.py:25` ignores the `False` from `reserve_stock`; `ledger.py:9-10,15` `O_EXCL` lock can raise after stock was reserved (job-01).
