---
dimension: local-correctness
reviewer: senior-review:local-correctness-auditor
status: delivered
job_id: job-01
candidate: 943bdc44c66dfd9782f6d38c82922a1f08783653
body_sha256: 1284b7ba7593477acd493f6fcb611414ec927978938f3bbcef5e698edb900c80
scope_id: orders-module
output_path: D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/blind-b/jobs/job-01.md
knowledge_usage: []
gaps:
  - Static inspection only. The application was never run; stdlib semantics were confirmed with isolated expressions and an AST parse that executes no application code.
  - The handlers named by ORDER_NOTIFY_HANDLERS are outside the source, so their return semantics are unknown. The discarded send_via result at service.py:29 could not be judged.
  - No requirement source exists beyond docstrings; every rule cited below is a docstring.
  - Python stack baseline unavailable (declared by the coordinator). Taxonomy references not loaded; no mechanism required them.
member_results:
  - specialist_id: senior-review:local-correctness-auditor
    status: delivered
    coverage: complete
    finding_ids: [job-01-F1, job-01-F2, job-01-F3, job-01-F4, job-01-F5, job-01-F6, job-01-F7, job-01-F8, job-01-F9, job-01-F10]
    gaps: static only; external handler contract unknown
---

# Findings

Paths are repository-relative. `orders/` means `benchmarks/scope-resolution/app/packages/orders/`.

## job-01-F1: customer discount is subtracted twice

- file: `benchmarks/scope-resolution/app/packages/orders/pricing.py`
- line: 19
- evidence: `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`; the docstring at `:18` states "netto - sconto cliente + IVA (VAT)", one discount.
- severity: High
- confidence: 97
- consequence: every order with `loyalty_percent > 0` is undercharged and its VAT understated, silently. With net 100 and 10%, the caller and the ledger get 97.6 (VAT 17.60) instead of 109.8 (VAT 19.80).
- fix: subtract `compute_discount(order)` once.
- premise: `compute_total` subtracts the discount twice while its contract defines one subtraction.
- premise_provenance: independent
- trigger: any `checkout` payload with non-zero `loyalty_percent` and non-zero `net`.
- counterevidence_checked: `compute_discount` (`:11-14`) returns the single full discount, not half; no second discount type exists in `orders/pricing.py`; `volume_discount` belongs to shipping and is not called here; no test asserts a total.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-01-F2: checkout ignores a failed stock reservation

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 25
- evidence: `inventory.reserve_stock(order["sku"], order["qty"])` discards the boolean whose contract is "False se la scorta non basta" (`orders/inventory.py:18`).
- severity: High
- confidence: 95
- consequence: an order that cannot be fulfilled looks successful. With `STOCK = {"demo-sku": 10}`, `{"id": "A", "sku": "demo-sku", "qty": 11, "net": 100}` moves no stock, but the ledger gets `A\t122.0`, a receipt is sent and 122.0 is returned. An unknown sku behaves the same.
- fix: check the result before any later step and return or raise a distinct out-of-stock outcome that `checkout` callers can see.
- premise: no path in `checkout` reads the result of `reserve_stock`.
- premise_provenance: independent
- trigger: `qty` above available stock, or any sku missing from `STOCK` with `qty > 0`.
- counterevidence_checked: `service.py:25` is the only call of `reserve_stock` in `app/packages`; `reserve_stock` returns False rather than raising; `DefaultPipeline.step` checks nothing; the dispatcher adds no guard.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-01-F3: a notification failure after the ledger write reports a failed checkout, and a retry books it twice

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 29
- evidence: `ledger.record` (`:28`) has already appended when `notifications.send_via` runs, with no `try` around it. `orders/notifications.py:13` reads `os.environ["ORDER_NOTIFY_HANDLERS"]` with no default.
- severity: High
- confidence: 90
- consequence: the caller gets an exception and no total, although stock is reduced and the ledger line is written. Retrying the event appends a second line and reserves stock again. The operator sees `KeyError: 'ORDER_NOTIFY_HANDLERS'` or `KeyError: 'email_receipt'` from `handle`, the exception `orders/api.py:3` documents as a missing event registration, so a caller following that contract misreads a booked checkout as an unknown event.
- fix: settle the notification policy. If it is best-effort, catch its failure after the ledger write, report it through a separate outcome and return the total. If it is mandatory, resolve the handler before any effect and compensate on send failure.
- premise: an exception raised by `send_via` propagates out of `checkout` after `ledger.record` has appended, and no later attempt can detect the earlier entry.
- premise_provenance: independent
- trigger: any of: `ORDER_NOTIFY_HANDLERS` unset; channel absent from the mapping, including `"channel": None`; value `""` or a trailing comma, which raises `ValueError: dictionary update sequence element #N has length 1; 2 is required`; import failure; a handler that raises.
- counterevidence_checked: no `try/except` in `service.py` or `api.py`; `ledger.record` only appends and has no duplicate check; the environment variable has no default in the source or in `app/pyproject.toml`; no docstring makes the notification best-effort, and either reading of its status is violated.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-01-F4: stock reserved by checkout is never released when a later step fails

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 25
- evidence: reservation comes first and nothing compensates at `:26-29`. `release_stock` (`orders/inventory.py:27`, "annullamento ordine") has no caller in `app/packages`.
- severity: Medium
- confidence: 88
- consequence: each failed checkout permanently removes units from `STOCK` for the life of the process, with no order behind them. With `net: None`, or with `ledger.lock` present, the caller sees `TypeError` or `FileExistsError` while `demo-sku` drops from 10 to 10 - qty; each retry removes more. Once F2 is fixed, this surfaces as false out-of-stock refusals.
- fix: wrap the steps after a successful reservation and call `release_stock` when one fails before the ledger write.
- premise: no code path calls `release_stock` after a failed checkout.
- premise_provenance: independent
- trigger: an exception at `service.py:26-28` after a successful reservation: invalid `net` or `loyalty_percent`, a rejecting custom pipeline, or `FileExistsError` from `orders/ledger.py:10`.
- counterevidence_checked: text search of `app/packages` for `release_stock` found only its definition; no `try/finally` in `checkout`; `OrderService` has no cancellation path.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-01-F5: the refund entry has no amount and no VAT portion

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 30
- evidence: `stream.write(f"{order.get('id', '?')}\tREFUND\n")`. `:26` promises "uno storno (rimborso) con la quota IVA/VAT", `orders/service.py:33` says "storno IVA/VAT", and `:1` says "breakdown IVA (VAT)", which `record` (`:18`) does not write either.
- severity: Medium
- confidence: 90
- consequence: an operator reading the ledger sees `A\tREFUND` and cannot tell how much was reversed or how much VAT it carried, so the entry cannot be netted against `A\t122.0`. `refund_request` returns the unchanged payload, so the caller gets no amount either.
- fix: require the refund amount, compute its VAT portion and write both, for example `id\tREFUND\tamount\tvat`.
- premise: `record_refund` writes no amount and no VAT value to any output.
- premise_provenance: independent
- trigger: any `refund_request` event.
- counterevidence_checked: `payments/refunds.py:10-21` computes such a VAT portion, but nothing in `orders` calls it; `record_refund` has no other writer or return value carrying the figures.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-01-F6: the validation pipeline runs after its subject is consumed, and its result is discarded

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 27
- evidence: order of calls at `:25-28`: reserve, total, then `self._pipeline.step(order)` with the return value ignored. `:3-4` and `:20` describe the pipeline as replaceable validation; `DefaultPipeline.step` (`:13-15`) returns the order.
- severity: Medium
- confidence: 70
- consequence: a configured validator cannot do its job. If it raises, stock is already gone. If it changes `net` in place, the total was already computed from the old value, so ledger and caller get the unvalidated figure. If it returns a normalized copy, ledger and notification still use the original. The default stamps `validated=True` even after a failed reservation or on a negative quantity.
- fix: run `order = self._pipeline.step(order)` first, then reserve and compute the total from its result.
- premise: `step` runs after both `reserve_stock` and `compute_total`, and `checkout` does not use its return value.
- premise_provenance: independent
- trigger: `OrderService(pipeline_cls=P)` where `P.step` rejects, mutates or returns a copy. Default path: any order, for the stamped flag only.
- counterevidence_checked: `test_app_structures.py:46-49` pins only the text `self._pipeline.step(` and `setattr(`, not the position; nothing in `app/packages` reads `validated`; no in-scope caller passes a custom class, which limits today's reach to the documented constructor option.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-01-F7: the receipt handler receives neither total nor VAT

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 29
- evidence: `total` stays a local at `:26` and only `order` reaches `send_via`. `orders/notifications.py:5` says "La ricevuta riporta l'IVA (VAT)" and `:19` says "IVA inclusa". Nothing in `checkout` adds `total` or VAT to the order.
- severity: Low
- confidence: 55
- consequence: a handler reading the total or VAT from its argument finds neither, so the receipt omits them or fails after the ledger write (F3), unless the handler recomputes them from `orders/pricing.py`.
- fix: pass the computed total and VAT to `send_via` explicitly.
- premise: the object passed to `send_via` holds no computed total or VAT.
- premise_provenance: independent
- trigger: any checkout with a handler that relies on its argument for the figures.
- counterevidence_checked: handlers are outside the source, so one could recompute (hence Low and the confidence); the only `total` readers in the app, `payments/gateway.py:10,15`, default to 0 and are not called from orders.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-01-F8: a negative quantity increases stock and reports success

- file: `benchmarks/scope-resolution/app/packages/orders/inventory.py`
- line: 21
- evidence: `if available < qty: return False`, then `STOCK[sku] = available - qty` at `:23`, with no lower bound on `qty`.
- severity: Medium
- confidence: 85
- consequence: `reserve_stock("demo-sku", -5)` returns True and raises stock from 10 to 15. An unknown sku with -5 is created with 5 units; with `qty=0` it is created with 0. Through `checkout`, the order is also recorded and notified as normal.
- fix: reject `qty <= 0` in `reserve_stock`, and apply the same bound in `release_stock`, where a negative `qty` lowers stock.
- premise: no check between the event payload and `inventory.py:23` rejects a non-positive `qty`.
- premise_provenance: independent
- trigger: an `order` payload with `qty <= 0`.
- counterevidence_checked: `orders/api.py:4` passes the payload as it is; `DefaultPipeline.step` only sets a flag and runs later; `release_stock` is the only documented way to increase stock (`inventory.py:27-28`). Rule evidence: "Riserva qty unità".
- introduced_by_candidate: n/a
- evidence_class: derived

## job-01-F9: audit formatters render booleans and integer identifiers as money

- file: `benchmarks/scope-resolution/app/packages/orders/big_module.py`
- line: 16
- evidence: `isinstance(value, (int, float))` followed by `f"{key}={value:.2f}"` at `:17`. `bool` is a subclass of `int`. All 105 functions share this body; an AST pass re-derived this independently of the census.
- severity: Low
- confidence: 80
- consequence: an entry with `validated=True` (set on every order by `orders/service.py:14`), `id=123` and `qty=2` produces `validated=1.00`, `id=123.00` and `qty=2.00`. Integers above 2**53 lose digits: `2**53+1` prints as `9007199254740992.00`, a different identifier. Low because nothing imports the module today.
- fix: test `bool` first and apply two decimals only to money fields or to `float`; fix it once, at whatever generates the 105 copies.
- premise: the numeric branch accepts `bool` and every `int`, and formats them with `:.2f`.
- premise_provenance: independent
- trigger: calling any `format_*_entry_*` with a boolean or integer value.
- counterevidence_checked: no importer of `big_module` in `app/packages`; `test_app_structures.py:81-85` pins only its size; module docstring sets no rule that integers are amounts.
- introduced_by_candidate: n/a
- evidence_class: derived

## job-01-F10: Dispatcher stores its service and never uses it

- file: `benchmarks/scope-resolution/app/packages/orders/api.py`
- line: 23
- evidence: `self._service = service` is never read; `_invoke` (`:26`) resolves through the process-wide `EVENT_REGISTRY`.
- severity: Low
- confidence: 50
- consequence: after `register_defaults()`, `Dispatcher(OrderService(pipeline_cls=Strict)).handle("checkout", order)` runs the default service, so `Strict` is silently skipped. Without prior registration, the same call raises `KeyError`.
- fix: drop the `service` parameter, or register and resolve callbacks per dispatcher.
- premise: `Dispatcher` behaviour does not depend on the service it is constructed with.
- premise_provenance: independent
- trigger: constructing a `Dispatcher` with a service other than the last one registered.
- counterevidence_checked: the class docstring (`:20`) says it routes to registered callbacks, which supports the registry; the only construction site, `:39`, passes the registered service, so today's path shows no wrong result; `test_app_structures.py:30-35` pins the registry, not `_service`.
- introduced_by_candidate: n/a
- evidence_class: derived

# Examined scope and completed checks

All 9 scoped files were read; `big_module.py` lines 1-80 closely, the rest through an AST check. Context read: `payments/*`, `shipping/rates.py`, `app/pyproject.toml`, `test_app_structures.py`.

Checked with no finding:

- `big_module.py`: 105 unique names, contiguous rows, name, label and docstring agree in every function, one body. The census normalizes these fields, so this was checked separately.
- `inventory.py`: `available < qty` is correct when equal; `_lock_for` returns one lock per sku.
- `api.py`: a missing registration raises `KeyError` with the event name; the payload is passed unchanged, as documented.
- `pricing.py`: `vat_amount` on the discounted net matches the docstring order.
- `reporting.py:11`: renders `22%`; row access matches the documented input.
- `service.py:21`: `setattr` and `pipeline_cls or DefaultPipeline` initialize correctly on every path.
- `ledger.py`: closing before unlinking is the correct order; the `finally` fault points are noted below.
- Mutable defaults, shadowing, callback capture and iterator invalidation: none in scope. `register_defaults` called twice replaces the callbacks with an equivalent service.

# Cross-Reviewer Notes

- Concurrency: `orders/ledger.py:10` raises `FileExistsError` for a concurrent writer instead of waiting.
- Resource lifecycle: a crash between `ledger.py:15` and `:21` leaves `ledger.lock`, which blocks every later write; `os.close` raising at `:20` or `:32` would also skip the unlink.
- Environment: `ledger.py:5-6` are cwd-relative, so processes in different directories use separate ledgers and locks.
- Data representation: `pricing.py:8` uses float `round`; `round(2.75 * 0.22, 2)` gives 0.6. No rounding rule is established in the project.
- Data representation: an `id` holding a tab or newline breaks the line format at `ledger.py:18,30`; a missing `id` is written as `?`.
- Input validation: a missing `net` gives total 0.0 recorded as normal (`pricing.py:14,19`); `loyalty_percent` above 100 gives a negative total.
- Input validation: `service.py:29` takes the channel from the payload, while `notifications.py:1` says it comes from configuration.
- Transaction integrity: `checkout` and `refund_request` have no idempotency key, and a refund is recorded without checking for a prior checkout.
- Structural entropy: `VAT_RATE` is defined in both `orders/pricing.py:3` and `payments/refunds.py:7`.
