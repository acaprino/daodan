---
dimension: data-representation
reviewer: senior-review:data-representation-auditor
status: delivered
job_id: job-06
candidate: 943bdc44c66dfd9782f6d38c82922a1f08783653
body_sha256: e1706fc20ff239deddb253534e59f82ce25c678955d3404ac38e439d63bb1334
scope_id: orders-module
output_path: D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/blind-b/jobs/job-06.md
knowledge_usage: []
gaps:
  - No existing ledger.log data was supplied; every row below is derived from the writer's format, none was observed on disk.
  - No reader of ledger.log exists in app/ (text search), so reader interpretation is derived from the row format and the docstrings, not from a parser.
  - The application was not run. Float results come from the same expressions evaluated standalone on stdin; no scoped module was imported.
  - The notification handler is external (env ORDER_NOTIFY_HANDLERS); what it reads from the order is unknown.
member_results:
  - specialist_id: senior-review:data-representation-auditor
    status: delivered
    coverage: complete
    finding_ids: [job-06-F1, job-06-F2, job-06-F3, job-06-F4, job-06-F5, job-06-F6, job-06-F7]
    gaps: same as above
---

# Findings

Paths are relative to the repository. Rule evidence is limited to docstrings, as the brief requires. `test_vat_spread_at_least_8_files` only needs the words VAT or IVA in 8 files, so a docstring mention may partly exist for the benchmark; the docstrings remain the only contract available.

## job-06-F1: a refund row stores no amount and no VAT share

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 30
- severity: High
- confidence: 88
- evidence: `ledger.py:26` promises "uno storno (rimborso) con la quota IVA/VAT", `service.py:33` "storno IVA/VAT", `ledger.py:1` "breakdown IVA (VAT)". `ledger.py:30` writes only `{id}\tREFUND\n`. The second column is a number on sale rows and a literal on refund rows, with no sign and no value.
- original to lost meaning: order `A1` sold, row `A1\t122.0`. A refund of 50 of that order, row `A1\tREFUND`. A full refund, the same row. The amount, the VAT share and full versus partial never reach the store, and the file is the only persistent record in the package.
- consequence: an operator reconciling `ledger.log` sees that something was reversed and cannot compute how much, the VAT to reverse, or the balance of the day. Rows already written cannot be repaired, because the values were never stored.
- premise: no refund amount or VAT share is written to the ledger by any path of `refund_request`.
- premise_provenance: independent
- trigger: any `Dispatcher.handle("refund_request", {"id": "A1", ...})` after `register_defaults()`; `api.py:38` wires it, `service.py:34` forwards it.
- counterevidence_checked: a reader could derive the amount from the sale row only if every refund were full and every id unique. No docstring says so, `record_refund` does not look up the sale, `payments/refunds.py:16` models partial refunds ("parziale o totale"), and `issue_refund` in `payments/refunds.py:15` has its `vat` field but orders never calls it. No other writer of refund values found.
- fix direction: pass amount and VAT to `record_refund` and write them as signed columns, for example `{id}\tREFUND\t-{amount}\t-{vat}`. Readers must treat the old two-column rows as "amount unknown", since they cannot be backfilled.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-06-F2: a missing `net` is persisted as a real zero total

- file: `benchmarks/scope-resolution/app/packages/orders/pricing.py`
- line: 19
- severity: Medium
- confidence: 70
- evidence: `pricing.py:14` and `:19` use `order.get("net", 0)`. `service.py:25` reads `order["sku"]` and `order["qty"]` strictly, and `DefaultPipeline.step` (`service.py:13-15`) validates nothing and runs after the total.
- original to lost meaning: `{"id": "A1", "sku": "demo-sku", "qty": 1}` becomes total `0.0`, stock goes from 10 to 9, row `A1\t0.0`, and `checkout` returns `0.0`. "Amount unknown" is stored as "free order", identical to a genuine zero-priced sale.
- consequence: the operator sees a completed sale at 0.0 with no error, and stock has left. The caller of `checkout` receives 0.0 as the order total.
- premise: no check on the checkout path rejects an order without `net` before the ledger write.
- premise_provenance: independent
- trigger: an event payload without the `net` key. An explicit `None` raises `TypeError` instead, so the two absent forms also behave differently.
- counterevidence_checked: no docstring states that a missing net means zero; `compute_discount` says only "applicata al netto". The default for `loyalty_percent` (`:13`) is sound, absence means no discount, and is not part of this finding. `payments/gateway.py:10` uses the same `.get(..., 0)` habit, which could mean deliberate tolerance, but nothing states it.
- fix direction: read `order["net"]` as `sku` and `qty` already are, or reject the order before `reserve_stock`.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-06-F3: a missing or null order id is stored as an ordinary id

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 18
- severity: Medium
- confidence: 72
- evidence: `ledger.py:18` and `:30` write `order.get('id', '?')`. Missing becomes `?`, explicit `None` becomes `None`. Checkout requires only `sku` and `qty`.
- original to lost meaning: `{"sku": "demo-sku", "qty": 1, "net": 100}` writes `?\t122.0`. Two such orders produce identical rows. `{"sku": ...}` sent to `refund_request` writes `?\tREFUND`, which cannot be tied to any sale. A real id `"?"` or `"None"` collides with the placeholders.
- consequence: money in the register belongs to no identifiable order; the operator cannot attribute a sale or match a refund to it.
- premise: an order without an id reaches the ledger write without being rejected.
- premise_provenance: independent
- trigger: an event payload with no `id` or with `id: None`.
- counterevidence_checked: the `?` default is deliberate in the code, but no docstring allows anonymous orders, and `ledger.py:1` calls these "voci ordine". No validation upstream in `api.py:25-31` or `service.py:13-15`.
- fix direction: require a non-empty id before any effect of checkout or refund; drop the placeholder.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-06-F4: the id is written unescaped into a tab and newline delimited row

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 18
- severity: Medium
- confidence: 68
- evidence: `ledger.py:18` and `:30` interpolate the id into `{id}\t...\n` with no escaping. `api.py:4` states that callbacks get the payload "così com'è", and no later step sanitizes it.
- original to lost meaning: id `"A1\t0.0\nA2"` with net 100 writes two rows, `A1\t0.0` and `A2\t122.0`. Id `"A1\tREFUND\nB"` writes a refund row for `A1` with no refund having happened. The row count and the columns no longer match the events.
- consequence: anyone reading the register line by line sees a sale or refund that never occurred, and a total attributed to the wrong order. Nothing marks those rows as forged.
- premise: an id containing tab or newline reaches `stream.write` unchanged.
- premise_provenance: independent
- trigger: a payload whose `id` holds `\t` or `\n`. `\r` also splits the line for a reader with universal newlines.
- counterevidence_checked: no id format is validated anywhere in scope; no reader exists that could detect the extra columns. Severity stays at Medium for that reason, and because who controls the payload is not established.
- fix direction: write one JSON object per line, or use `csv` quoting, and tag the format so that old rows stay distinguishable; or reject control characters during validation.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-06-F5: the same net can yield VAT and total one cent apart

- file: `benchmarks/scope-resolution/app/packages/orders/pricing.py`
- line: 19
- severity: Low
- confidence: 80
- evidence: `pricing.py:19` subtracts floats and leaves the result unrounded, then `pricing.py:8` runs `round(net * VAT_RATE, 2)`. A half-cent product lands on either side depending on binary noise. `vat_amount` is documented as "IVA dovuta sul netto", a function of the net; this is the only rule relied on, as the project names no rounding mode.
- original to lost meaning: `{"net": 10.31, "loyalty_percent": 10}` gives net `8.250000000000002`, VAT 1.82, total 10.07. `{"net": 8.25}` gives VAT 1.81, total 10.06. With the double discount of `:19` removed the effect stays: `{"net": 9.12, "loyalty_percent": 15}` gives net `7.749999999999999`, VAT 1.70, against 1.71 for `{"net": 7.75}`. Without subtraction the direction is still inconsistent: net 1.25 gives 0.28 (up), net 2.25 gives 0.49 (down).
- consequence: two customers with the same net are charged and registered one cent apart, permanently in `ledger.log`. The size is one cent per affected order.
- premise: `compute_total` returns different totals for orders whose two-decimal net after discount is equal.
- premise_provenance: independent
- trigger: a net after discount ending in .25 or .75. The sweep below found no mismatch elsewhere.
- counterevidence_checked: float alone is not the defect here. For the nets 0.01 to 9999.99 not ending in .25 or .75, `round(net * 0.22, 2)` matched exact half-up in every case. For the 2000 nets ending in .25 or .75 up to 999.75 it matched half-up in 1079 and half-even in 1035, so neither mode describes it. The final `round` at `:20` does not undo the difference.
- fix direction: compute in integer cents or `Decimal` with one declared rounding mode. Rounding the net before `vat_amount` removes the path dependence only. The owner has to name the mode.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-06-F6: a sale row has no VAT breakdown and no rate

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 18
- severity: Low
- confidence: 55
- evidence: `ledger.py:1` promises "breakdown IVA (VAT)", but `ledger.py:14` says "ordine e totale (IVA/VAT inclusa)" and `:18` writes the gross alone. The two docstrings disagree; the code follows the narrower one. `reporting.py:3` speaks of the "corrente" rate, so the project treats the rate as a value of the moment.
- original to lost meaning: row `A1\t122.0` holds neither VAT, net nor rate. Today nothing is lost: in a sweep of nets 0.01 to 19999.99, `round(g - g / 1.22, 2)` returned the stored VAT in every case. After a change of `VAT_RATE`, the same reader computes the wrong VAT on every older row, with nothing in the row to reveal it.
- consequence: none visible until the rate changes; then the VAT of past sales cannot be recovered from the register.
- premise: no ledger row records the VAT rate or VAT amount in force at write time.
- premise_provenance: independent
- trigger: a change of `pricing.py:3`, followed by any VAT reading of older rows.
- counterevidence_checked: the recoverability sweep above is why this is Low. No rate history exists in scope. No rate change is planned in any file read.
- fix direction: write net, VAT and rate columns; or, if the gross is all that is wanted, correct `ledger.py:1`. This is an owner choice.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-06-F7: audit formatters render every number as a two-decimal amount

- file: `benchmarks/scope-resolution/app/packages/orders/big_module.py`
- line: 16
- severity: Low
- confidence: 72
- evidence: `big_module.py:16-17` applies `:.2f` to everything passing `isinstance(value, (int, float))`, and `bool` passes. Body read at `:10-28`; the census reports one normalized body for all 105 functions.
- original to lost meaning: an order as `checkout` leaves it, with `validated: True` from `service.py:14`, gives `validated=1.00`. `id: 1001` gives `id=1001.00`, `qty: 2` gives `qty=2.00`, `loyalty_percent: 7.125` gives `loyalty_percent=7.12`, `vat_rate: 0.225` gives `vat_rate=0.23`, id `9007199254740993` gives `id=9007199254740992.00`, a different id. Fields are stored as strings under `audit/v1`, so the original value is gone from the record.
- consequence: an auditor reads a flag as an amount, sees a rounded discount or rate, and in the last case a wrong id.
- premise: the numeric branch does not distinguish money from flags, counts, identifiers or rates.
- premise_provenance: mixed (body read directly; extension to 105 functions from `tools/big_module-census.json`)
- trigger: calling any `format_*_entry_*` with such a field. No caller exists in `app/`, hence Low: today this is a defect of the public functions, not of a live path.
- counterevidence_checked: no docstring limits entries to money fields, and `big_module.py:3` says it covers all registered entry families. Text search found no importer of `big_module` and no field whitelist.
- fix direction: exclude `bool`, apply `:.2f` only to named money fields, write other numbers unchanged. `test_big_module_size` pins at least 700 lines and 101 `def `, so a shared helper must respect that.
- introduced_by_candidate: n/a
- evidence_class: derived

# Examined scope and completed checks

All 9 files. `__init__.py` is empty. `big_module.py`: one body read closely plus the census, as the context allows. Context only: `payments/*`, `shipping/rates.py`, `test_app_structures.py`. Taxonomy: only section 12.8 of `data-design-ops.md` applies, and only as a lead; the rest concerns SQL, ORM and other surfaces absent here.

- Numeric, money, rounding: F2, F5, F7. The ledger total uses float `repr` (`122.0`, `12.2`): decimals vary, but the value round-trips, so no finding. `Decimal` input is unsupported (`net * VAT_RATE` raises `TypeError`), and nothing supplies it.
- NULL, missing, defaults: F2, F3. In `big_module.py:18-19`, `None` and the literal `"-"` both give `key=-`. Not raised: no caller and no known field holds `"-"`.
- Enum and shape: the second ledger column in F1. `AUDIT_SCHEMA` is a constant with no reader. The ledger has no format version; relevant only once its format changes, so the F1 and F4 fixes must add one.
- Time: no date, instant or timezone is stored or read in `app/`. A ledger row has no date, and `format_daily_summary` takes pre-formatted rows from a caller that does not exist. No project rule ties that report to the ledger, so this is an observation, not a finding.
- Currency and units: no currency anywhere; single-currency is consistent with the source. `compute_total` ignores `qty`, so `net` reads as order-level; no docstring contradicts it.
- Reporting header: `pricing.VAT_RATE:.0%` gives `22%` for the current rate. A fractional rate would be rounded (0.225 gives `22%`), but no such rate exists.
- Pagination, cursors, migrations, backfills: none in `app/` (text search). Not applicable.

# Cross-Reviewer Notes

- logic-integrity: `pricing.py:19` subtracts the discount twice; net 100 with loyalty 10 stores 97.6 instead of 109.8.
- logic-integrity: `checkout` keeps the total out of the order, so the receipt handler (`notifications.py:19-21`) gets no total or VAT despite `notifications.py:5`.
- local-correctness: `service.py:25` ignores the result of `reserve_stock`, so a ledger row is written for an order with no stock.
- input-validation: `{"net": 100, "loyalty_percent": 60}` stores a negative sale (`-24.4`); a NaN `net` stores `nan`; `reserve_stock("demo-sku", -5)` raises stock and a fractional `qty` makes it fractional.
- environment-binding: `ledger.py:5-6` are relative to the working directory, so a process started elsewhere writes a different register.
