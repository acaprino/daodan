# Review Knowledge Leads

> Leads, not truth. Immutable once written.
> Source-derived pointers, not inherited Codebase Map knowledge leads or analytical conclusions.
> All anchors @943bdc44c unless marked @6dd2c2bbf. Paths relative to the repository root.

## Navigation rules followed
| Source | Rule |
|--------|------|
| `git show 6dd2c2bbf:AGENTS.md` | No navigation rule (no "look here first" file). Applied rules: style/format belong to the configured linter/formatter, not to reviews; benchmarks declare parameters and measured results in their README. |
| (none) | No CLAUDE.md or nested instruction file in the tree. |

## Concepts touched by this diff
| Concept | Where it appears in the diff |
|---------|------------------------------|
| `compute_total` (order total) | benchmarks/scope-resolution/app/packages/orders/pricing.py:17-20 (changed line 19) |
| `compute_discount` (sconto cliente / loyalty discount) | pricing.py:19, now called twice; hunk header names `def compute_discount(order):` |
| net (netto) | pricing.py:19 `net = ...` |
| VAT (IVA), `vat_amount` | pricing.py:20 (context line: `round(net + vat_amount(net), 2)`) |

## Leads
| Concept | Document / test | Anchor | Status |
|---------|-----------------|--------|--------|
| order total formula | docstring of `compute_total` | benchmarks/scope-resolution/app/packages/orders/pricing.py:18 "Totale ordine: netto - sconto cliente + IVA (VAT)." | lead: states one discount term; unchanged by the candidate |
| loyalty discount | docstring and body of `compute_discount` | pricing.py:11-14 "Sconto cliente: percentuale di fedeltà applicata al netto." | lead: discount = round(net * loyalty_percent / 100, 2) |
| VAT on net | `vat_amount`, `VAT_RATE` | pricing.py:3, 6-8 | lead: VAT computed on the post-discount net |
| total consumer | `OrderService.checkout` | benchmarks/scope-resolution/app/packages/orders/service.py:23-30 (`total = pricing.compute_total(order)` at :26, `ledger.record(order, total)` at :28, `return total` at :30) | lead: total flows to the ledger and to the caller |
| total persisted | `ledger.record` | benchmarks/scope-resolution/app/packages/orders/ledger.py:13-22 (writes `{id}\t{total}` at :18) | lead |
| entry point | `register_defaults`, `Dispatcher` | benchmarks/scope-resolution/app/packages/orders/api.py:34-39, :25-31; module docstring :5-6 "Il totale ordine include l'IVA (VAT) calcolata dal modulo pricing." | lead: callback dispatch reaches checkout |
| payment amount | `gateway` | benchmarks/scope-resolution/app/packages/payments/gateway.py:10, :15 read `order.get("total", 0)` | lead: reads an order key `total`; no code found that writes `order["total"]` from `compute_total` |
| structure tests | `test_app_structures.py` | benchmarks/scope-resolution/test_app_structures.py:15-17 (compileall), :70-72 (`"def compute_discount(" in pricing.py`) | lead: text/compile checks only, no numeric assertion on totals |
| benchmark fixture docs | `CASES.md`, `ground_truth.json`, `docs/specs/2026-11-04-benchmark-subproject-scope-resolution.md` | CASES.md:7 (C1), ground_truth.json:15 (C1 rationale: compute_discount ← compute_total ← OrderService.checkout), docs/specs/2026-11-04-benchmark-subproject-scope-resolution.md:45 (chain on_event → _invoke → checkout → compute_total → ledger.record) | lead: the app is a scope-resolution fixture; documents the caller chain, no numeric requirement |

## Concepts with no lead found
- No test exercises `compute_total` or `compute_discount` numerically (no test imports `pricing`).
- No requirement, spec, README or commit text explains why the discount should be subtracted a second time; the commit message says only "aggiorna il calcolo in pricing.py".
- No document states the expected total for a given order (e.g. net 100, loyalty 10%).
