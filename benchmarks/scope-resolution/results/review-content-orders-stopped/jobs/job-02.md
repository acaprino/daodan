---
dimension: logic-integrity
reviewer: senior-review:logic-integrity-auditor
status: delivered
job_id: job-02
candidate: 943bdc44c66dfd9782f6d38c82922a1f08783653
body_sha256: beda2809d9580b89e7ee803cc528f81f7d666784214c5bc630884221acc1ee67
scope_id: orders-module
output_path: D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/blind-b/jobs/job-02.md
knowledge_usage: []
gaps:
  - No snapshot-bound map rows (graph tool failed); call edges re-derived by text search in app/packages only. Callers elsewhere under app/ are outside the admitted read scope and rest on 01-context.md:20.
  - Deployment multiplicity unverifiable: the package has no process entrypoint. STOCK (inventory.py:7) is per-process and seeded at import, while the ledger file outlives the process and its O_EXCL lockfile is a cross-process mechanism. Whether several processes or restarts coexist with one ledger cannot be settled, so no stock invariant is claimed beyond one process lifetime.
  - The notification handler lives outside the source (ORDER_NOTIFY_HANDLERS); its behaviour is unknown.
  - Static review, no application code run. Runtime values below are hand-derived.
member_results:
  - specialist_id: senior-review:logic-integrity-auditor
    status: delivered
    coverage: complete
    finding_ids: [job-02-F1, job-02-F2, job-02-F3, job-02-F4, job-02-F5, job-02-F6, job-02-F7]
    gaps: see above
---

# Findings

All paths are under `benchmarks/scope-resolution/app/packages/orders/`. In every finding `introduced_by_candidate: false`, `evidence_class: derived`. The `file` value is that prefix plus the file named.

## job-02-F1: customer discount subtracted twice (L4)

- file: `benchmarks/scope-resolution/app/packages/orders/pricing.py`, line: 19. Severity: High. Confidence: 97.
- evidence: rule at `pricing.py:18` "netto - sconto cliente + IVA (VAT)" and `pricing.py:12` (context anchor `01-context.md:11`). Line 19 is `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`, and VAT at line 20 is computed on that reduced base.
- trigger: any order with `loyalty_percent > 0` through `checkout`. `net=100, loyalty_percent=10` gives 97.6 instead of 109.8 (net 90 + VAT 19.8). `loyalty_percent=60` gives -24.4 instead of 48.8.
- consequence: `checkout` returns and `ledger.record` stores an understated total, with VAT under-computed on every discounted order. From 50% loyalty the total reaches zero or below. A customer or operator sees the wrong amount in the return value and in `ledger.log`.
- premise: the documented order total applies the customer discount exactly once.
- premise_provenance: independent.
- counterevidence_checked: no second discount type in orders. `volume_discount` (`shipping/rates.py:15`) applies to shipping quotes only and `compute_total` does not use it. `test_app_structures.py:70-72` pins only the existence of `compute_discount`. No other total path exists.
- fix: compute the discount once: `net = order.get("net", 0) - compute_discount(order)`.

## job-02-F2: checkout completes when the reservation failed (L1)

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`, line: 25. Severity: High. Confidence: 95.
- evidence: [MAP-GAP] rule at `inventory.py:18` "False se la scorta non basta" and `service.py:24`, where checkout is the full path starting from stock. Line 25 discards the boolean. Lines 26-30 continue unconditionally.
- trigger: `checkout({"sku": "demo-sku", "qty": 11, ...})` with stock 10, or any unknown sku.
- consequence: stock stays unchanged and `reserve_stock` returns False, yet the sale is written to the ledger, the customer gets a notification and the caller gets a total. Goods with no stock are sold, and the operator only finds out when ledger lines exceed stock.
- premise: no code path between `reserve_stock` returning False and `ledger.record` stops the checkout.
- premise_provenance: independent.
- counterevidence_checked: `service.py:25` is the only caller of `reserve_stock` in app/packages. `DefaultPipeline.step` does not read stock. `ledger.record` and `send_via` have no stock check. No test covers runtime behaviour.
- fix: stop before pricing and ledger when `reserve_stock` is False, with an explicit out-of-stock outcome for the caller.

## job-02-F3: a failed checkout keeps its reservation and ledger line; retry doubles them (L2.3, L6.2, L7)

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`, lines: 25-29. Severity: High. Confidence: 85.
- evidence: [MAP-GAP] rule at `inventory.py:28` "Rilascia una riserva (annullamento ordine)", which makes a reservation releasable when an order is cancelled. `release_stock` has no caller in app/packages, `checkout` has no `try`, and `register_defaults` (`api.py:37-38`) wires no cancel event. So no transition leaves "reserved" other than success. `ledger.record` (line 28) runs before the raising `send_via` (line 29), and `notifications.py:13-14` raises `KeyError` on a missing env var or unmapped channel.
- trigger: `ORDER_NOTIFY_HANDLERS` unset, or a channel absent from it. Then every checkout does: `STOCK` 10 to 9, ledger line `A\t<total>`, `KeyError` to the caller. Re-dispatching the same order once the env is fixed gives `STOCK` 8, a second `A\t<total>` line and one notification. Earlier failures leak stock alone: `FileExistsError` from `ledger.py:10`, or a pipeline or `compute_total` exception.
- consequence: the caller is told the checkout failed while the ledger records a sale. Units stay reserved until the process restarts. One logical order retried appears twice in the ledger and takes twice the stock. The operator sees ledger totals with no delivered result and stock that drains without completed orders.
- premise: no path in the package releases a reservation or neutralizes a ledger line when a later `checkout` step raises, and neither step deduplicates on order identity.
- premise_provenance: independent.
- counterevidence_checked: searched app/packages for `release_stock`, `cancel`, `annull`, and any id check in `ledger.py`: only the definition and its docstring. Each step's exception propagates through `_invoke` and `handle` (`api.py:25-31`), neither of which catches it. No in-tree retry exists, so the duplicate needs a caller re-dispatch; the stock and ledger divergence does not. `os.environ[` is pinned as a structure by `test_app_structures.py:56`; the defect is the state left behind, not the lookup.
- fix: release the reservation on any failure before the ledger write; treat notification failure as post-commit (report it without failing the sale, or send through a retriable outbox); key ledger writes on order id so a retry is a no-op.

## job-02-F4: refund entry has no amount and no VAT share (L4, L8)

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`, line: 30. Severity: High. Confidence: 90.
- evidence: rule at `ledger.py:26` "Registra uno storno (rimborso) con la quota IVA/VAT", `service.py:33` "storno IVA/VAT" and `ledger.py:1` "breakdown IVA (VAT)" (context anchor `01-context.md:13`). Line 30 writes `{id}\tREFUND\n`. Order lines at `ledger.py:18` carry only `{id}\t{total}`, so no VAT breakdown exists on either line. The second column holds a number or the word REFUND.
- trigger: every `refund_request` event, for example `{"id": "A"}`, writes `A\tREFUND`.
- consequence: the ledger, the only persistent financial record, contains no reversed amount and no reversed VAT. Revenue and VAT summed from it stay overstated by every refund. A partial refund, which `payments/refunds.py:16` treats as legitimate, cannot be told from a total one, and a duplicate request cannot be told from a second partial. `refund_request` returns the input order rather than a reversal entry.
- premise: `record_refund` writes no VAT share or amount to the ledger and receives none from its caller.
- premise_provenance: independent.
- counterevidence_checked: `refund_request` (`service.py:34`) is the only caller and passes only `order`. `payments/refunds.py` has `vat_portion` and `issue_refund`, the shape the docstring describes, but nothing in orders calls them. `pricing.py` has no gross-to-VAT helper used here. No other writer of `ledger.log`.
- fix: take the refunded amount in the request, compute its VAT share with one shared helper, and write amount and VAT on the refund line. Add net and VAT to order lines, or correct the module docstring if the breakdown is not wanted.

## job-02-F5: validation runs after the effects it should guard, and its result is discarded (L5.1)

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`, line: 27. Severity: Medium. Confidence: 75.
- evidence: [MAP-GAP] rule at `service.py:3-4`, `:11` and `:20`: the pipeline is the replaceable order validation. Order is reserve (25), price (26), validate (27), with the return value of `step` dropped, although `DefaultPipeline.step` returns the order (`service.py:15`). `DefaultPipeline.step` stamps `validated = True` without checking anything (`service.py:14`).
- trigger: `OrderService(pipeline_cls=Strict)`. If `Strict.step` raises on an invalid order, stock is already taken and never released. If it returns a normalized copy, the ledger and sender still use the raw order. If it mutates `net` or `loyalty_percent` in place, the ledger stores a total priced before validation while the sender receives the changed order.
- consequence: a stricter pipeline cannot prevent stock loss or wrong pricing on the orders it rejects or corrects. Operators see stock fall on rejected orders and ledger totals disagreeing with the validated data. In the default configuration, every order, however invalid, leaves checkout marked `validated: True`.
- premise: in `checkout`, stock mutation and pricing both happen before any pipeline code runs, and no consumer uses the return of `step`.
- premise_provenance: independent.
- counterevidence_checked: `test_app_structures.py:46-49` pins only the text `self._pipeline.step(` and `setattr(`, not the order. No reader of `validated` in app/packages. The default never raises, so with the default pipeline only the stamp is observable; the rest needs the documented alternative class.
- fix: run `step` first, continue with its return value, and only then reserve and price.

## job-02-F6: the receipt handler is not given the total or VAT it must report (L1.2, L8)

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`, line: 29. Severity: Medium. Confidence: 60.
- evidence: [MAP-GAP] rule at `notifications.py:5` "La ricevuta riporta l'IVA (VAT)" and `notifications.py:19` "IVA inclusa". `total` is a local at `service.py:26` and is never placed on `order`; only `validated` is added (`service.py:14`). `send_via(channel, order)` passes that dict alone to the handler (`notifications.py:21`). Neighbouring consumers read `total` from the dict (`reporting.py:14`, `payments/gateway.py:10`).
- trigger: any successful checkout with a configured handler and a payload without its own `total` or VAT field.
- consequence: the handler has no total or VAT value from checkout. A receipt shows nothing for them, or a value the handler recalculated itself, which can diverge from the ledger total under a mutating pipeline (F5).
- premise: the object passed to the notification handler carries neither the computed total nor a VAT amount.
- premise_provenance: independent.
- counterevidence_checked: no other argument or shared state reaches `sender`. A handler could import `pricing` and recompute from `net` and `loyalty_percent`, or a caller could prefill the field; neither exists in source and the handler is out of source, which is why confidence is limited.
- fix: pass the computed total and VAT to the handler, either as explicit arguments or on a copy of the order.

## job-02-F7: Dispatcher ignores its own service; routing follows the last registration (L2)

- file: `benchmarks/scope-resolution/app/packages/orders/api.py`, line: 26. Severity: Low. Confidence: 65.
- evidence: [MAP-GAP] rule at `service.py:3-4`, configurable validation by constructor, and `api.py:22`, where a Dispatcher takes a service. `self._service` is stored at `api.py:23` and read nowhere. `_invoke` uses process-wide `EVENT_REGISTRY` (`api.py:10`, `:26`). `register_defaults` takes no pipeline and overwrites any earlier registration (`api.py:36-38`).
- trigger: `Dispatcher(OrderService(Strict)).handle("checkout", o)`. With no registration it raises `KeyError`. After any `register_defaults()` it runs the default pipeline. Equally, `on_event("checkout", strict.checkout)` followed by `register_defaults()` silently replaces the strict handler.
- consequence: an operator who configures a stricter pipeline gets the default validation with no error, and two dispatchers in one process cannot route to different services. No in-tree code builds a custom pipeline today, hence Low.
- premise: no `Dispatcher` method reads `self._service`.
- premise_provenance: independent.
- counterevidence_checked: the search of app/packages shows `_service` only at `api.py:23`. `test_app_structures.py:30-35` pins `EVENT_REGISTRY`, `on_event` and `_invoke` by name, so the registry stays; the defect is the ignored constructor argument and silent overwrite. In the in-tree path both dispatcher and registry hold the same service, so nothing diverges there.
- fix: remove the constructor argument and document one process-wide registry, or make the registry per-Dispatcher and route through its service.

# Examined scope and completed checks

Examined: all 9 scoped files (`__init__.py` empty). Context read: `payments/*`, `shipping/rates.py`, `pyproject.toml`, `test_app_structures.py`, `AGENTS.md` as supplied. Anchors used: `01-context.md:9-16,20-22`.

`big_module.py`: one body read closely (`:10-28`). Own AST pass (parse only, nothing imported): 105 functions, name, docstring label and label constant agree on all, one distinct body, contiguous indices, no duplicate names. No importer in app/packages. Nothing in it reaches a domain rule of checkout or refund.

| Category | Result |
|---|---|
| L1 contracts | F2, F6. `api.py:3-4` holds: an unregistered event raises `KeyError(name)`, payload passed unchanged |
| L2 invariants, multiplicity | F3, F7. Stock mutators are only `reserve_stock` and `release_stock`, both under the per-sku lock: atomic within one process. Ledger writers are only `record` and `record_refund`, both under the lockfile. Multi-process stock: unverifiable, see gaps |
| L3 assumptions | `ORDER_NOTIFY_HANDLERS` required: consequence in F3. Rest in notes |
| L4 domain rules | F1, F4. VAT base is the discounted net, consistent with `pricing.py:18` apart from F1. `reporting.py:11` takes its rate from `pricing.VAT_RATE`; it equals `payments/refunds.py:7` at this candidate |
| L5 ordering, reentrancy | F5, F3. `step` and `sender` run with no inventory or ledger lock held, so reentering `handle` from them deadlocks nothing |
| L6 idempotency | F3. Repeated `refund_request` appends a line each time; no rule establishes refund uniqueness, so it is not a separate finding |
| L7 state machine | F3. No stored order state exists. No rule forbids refunding an unrecorded or already refunded order, so none is imposed |
| L8 representation | F4 column shape, F6. Rest in notes |

# Cross-Reviewer Notes

- input-validation: negative `qty` raises stock at `inventory.py:21-23`, and `qty=0` creates an entry for an unknown sku.
- input-validation: `loyalty_percent` is unbounded and a missing `net` gives total 0 (`pricing.py:13-14`, `:19`).
- input-validation: `service.py:29` takes the channel from the payload while `notifications.py:1` says it comes from configuration.
- concurrency, resource-lifecycle: `ledger.py:10` fails immediately on an existing lockfile, so a concurrent writer gets `FileExistsError` and a stale lockfile blocks every order and refund.
- transaction-integrity: `ledger.py:5-6` paths are cwd-relative, so a different cwd means a different ledger and lock.
- data-representation: `big_module.py:16-17` applies `.2f` to bool and int, so `validated` prints `1.00` and `qty` prints `2.00`.
- data-representation: a missing id is written as `?` (`ledger.py:18`, `:30`), so such lines cannot be matched to an order.
- local-correctness: a handler `KeyError` (`service.py:25`, `notifications.py:13-14`) has the same type as the `api.py:3` missing-registration signal.
- out of scope: `payments/gateway.py:10`, `:15` read `order.get("total", 0)` and checkout never sets `total`; no in-tree path links them.
