```yaml
dimension: input-validation
reviewer: senior-review:input-validation-auditor
status: delivered
job_id: job-07
candidate: 943bdc44c66dfd9782f6d38c82922a1f08783653
body_sha256: 5463cd41d99b4caa1e3bbe0b777913c86436cc95e24ac94643ba02ad56f09bb5
scope_id: orders-module
output_path: D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/blind-b/jobs/job-07.md
knowledge_usage: []
gaps:
  - No transport adapter, parser or caller of Dispatcher.handle exists in the read scope. Payload controllability rests on api.py:1, api.py:4 and api.py:30; upstream size, schema and NaN handling are unknown.
  - No reader of ledger.log exists in the app, so the only stated ledger format is the writer's.
  - Handlers named by ORDER_NOTIFY_HANDLERS are outside the repository scope; what each does with a selected channel or the full payload is unknown.
  - Static review only, nothing executed. Every quantity below is derived, none measured.
  - big_module.py: 4 bodies read (lines 10-80), the other 101 covered by big_module-census.json (1 distinct normalized body) and a text search for sinks.
member_results:
  - specialist_id: senior-review:input-validation-auditor
    status: delivered
    coverage: complete
    finding_ids: [job-07-F1, job-07-F2, job-07-F3, job-07-F4, job-07-F5, job-07-F6]
    gaps: as listed above
```

Common entry premise: the payload reaches `checkout` and `refund_request` unchanged from `Dispatcher.handle`, the declared public entry (`api.py:4`, `api.py:30`). `DefaultPipeline.step` is the only "validation" and checks nothing (`service.py:13-15`). Severity is capped at Medium because no network surface exists in scope. Paths are under `benchmarks/scope-resolution/app/packages/orders/`.

## Findings

### job-07-F1: order id forges ledger records (Medium)

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 18 (also 30)
- evidence: `stream.write(f"{order.get('id', '?')}\t{total}\n")` and `f"{order.get('id', '?')}\tREFUND\n"` interpolate the raw id into a one-record-per-line, tab-separated format.
- severity: Medium
- confidence: 85
- consequence: anyone reading `ledger.log` sees a REFUND or a total for an order that never happened, structurally identical to a real row.
- fix: write each record with a structured encoding (`json.dumps` per line, as `big_module.py:28` does), or reject ids containing control characters at entry.
- premise: a payload `id` containing newline or tab reaches `ledger.py:18` and `:30` with no escaping or rejection.
- premise_provenance: independent
- trigger: `handle("refund_request", {"id": "A1\tREFUND\nB"})` writes two rows, `A1<TAB>REFUND` and `B<TAB>REFUND`. `handle("checkout", {"id": "A1\t0.00\nA2", ...})` writes `A1<TAB>0.00` and `A2<TAB><total>`.
- counterevidence_checked: dispatcher, pipeline and ledger for a type, character or length check: none. `id` is unconstrained in `service.py`. No trusted id source exists in the app.
- introduced_by_candidate: n/a
- evidence_class: derived

### job-07-F2: price and discount taken from the payload reach the ledger without type or range check (Medium)

- file: `benchmarks/scope-resolution/app/packages/orders/pricing.py`
- line: 14 (also 13, 19)
- evidence: `order.get("net", 0)` and `order.get("loyalty_percent", 0)` are the only inputs of the total. No catalog or customer lookup exists; `total` goes straight to `ledger.record` (`service.py:26`, `:28`) and is returned.
- severity: Medium
- confidence: 70
- consequence: the ledger records `<id><TAB>-122.0` and the caller receives -122.0 for a sale. A missing `net` records `0.0` while stock is debited. `net = float("nan")` writes `nan` into the ledger.
- fix: at entry, require `net` to be a finite real number >= 0 and `loyalty_percent` in 0-100, excluding bool; better, derive both from a server-side source rather than the event.
- premise: no code between `Dispatcher.handle` and `ledger.record` constrains `net` or `loyalty_percent`; rule evidence is `pricing.py:12` ("percentuale di fedeltà") and `:18` ("netto - sconto cliente + IVA").
- premise_provenance: independent
- trigger: `{"sku":"demo-sku","qty":1,"net":100,"loyalty_percent":100}`: discount 100.0, net -100.0, VAT -22.0, total -122.0. `{"sku":"demo-sku","qty":1,"net":-100}` gives the same total.
- counterevidence_checked: guards in `service.py`, `api.py`, `pricing.py`: none. A trusted upstream computing these fields would narrow this finding, and none is in scope (gap). `payments/gateway.py` reads `order["total"]` but is not called by orders, so no charge is shown.
- introduced_by_candidate: n/a
- evidence_class: derived

### job-07-F3: `net * loyalty` is sequence repetition on mistyped input, allocating before rejection (Medium)

- file: `benchmarks/scope-resolution/app/packages/orders/pricing.py`
- line: 14
- evidence: `round(order.get("net", 0) * loyalty / 100, 2)`. With an int and a str or list, `*` repeats the sequence; `/ 100` raises `TypeError` only after the result exists.
- severity: Medium
- confidence: 80
- consequence: from a payload of about 60 bytes, the worker's memory rises by an amount the sender picks. The caller then sees `TypeError`, or `MemoryError` if allocation fails; the process may be OOM-killed; other threads stall during the fill on a GIL build. Stock was already debited (F5).
- fix: type-check both fields as real numbers before any arithmetic (same guard as F2), so `*` can never mean repetition.
- premise: `compute_discount` receives `net` and `loyalty_percent` with their payload types, with no check before line 14.
- premise_provenance: independent
- trigger: `{"sku":"demo-sku","qty":1,"net":2000000000,"loyalty_percent":"aaaa"}`: 8e9 ASCII characters, about 8 GB. `{"sku":"demo-sku","qty":1,"net":[0],"loyalty_percent":1000000000}`: 1e9 references, about 8 GB. Derived assumptions: CPython, 1 byte per ASCII character, 8-byte pointers, payload types preserved (`api.py:4`). A float `net` raises immediately, so `net` must be an int when the sequence is `loyalty_percent`.
- counterevidence_checked: pre-sink bounds in `service.py:25` (touches only sku and qty) and `api.py`: none. An upstream byte limit would not bound this, because the size comes from a number's value. An upstream schema would close it; none is in scope (gap).
- introduced_by_candidate: n/a
- evidence_class: derived

### job-07-F4: non-positive or NaN `qty` passes the only stock guard and inverts or poisons it (Medium)

- file: `benchmarks/scope-resolution/app/packages/orders/inventory.py`
- line: 21 (also 23)
- evidence: `if available < qty: return False` followed by `STOCK[sku] = available - qty`. The contract is "Riserva qty unità di sku; False se la scorta non basta" (`:18`).
- severity: Medium
- confidence: 85
- consequence: a "reservation" adds stock and returns True, and creates stock for SKUs that do not exist. After NaN, `reserve_stock` never again returns False for that SKU, because `nan < q` is False and `nan - q` stays NaN. `STOCK` then misstates inventory. `checkout` also discards this return today (see notes), so stock enforcement fails either way.
- fix: in `reserve_stock`, reject unless `type(qty) is int and qty > 0`; apply the same to `release_stock`, whose positive-qty path has no guard (`:30`).
- premise: `qty` reaches `inventory.py:21` unchecked, and `available < qty` is False for any negative or NaN value.
- premise_provenance: independent
- trigger: `{"sku":"demo-sku","qty":-5,...}`: 10 becomes 15, returns True. `{"sku":"ghost","qty":-5,...}`: creates `STOCK["ghost"] = 5`. `{"sku":"demo-sku","qty":float("nan"),...}`: stock becomes NaN. `qty=0.5` yields 9.5.
- counterevidence_checked: guards in `service.py:25` and `api.py`: none. A non-numeric `qty` raises `TypeError` at line 21 before any write, so strings are closed.
- introduced_by_candidate: n/a
- evidence_class: derived

### job-07-F5: the validation pipeline runs after stock and pricing, so malformed orders consume stock and a real validator cannot prevent it (Medium)

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 25 (also 26, 27, 13-15)
- evidence: order is `reserve_stock` (`:25`), `compute_total` (`:26`), then `self._pipeline.step(order)` (`:27`), whose return value is discarded. Docstrings call this the validation and make it replaceable (`:3-4`, `:11`, `:20`).
- severity: Medium
- confidence: 85
- consequence: one malformed call empties a SKU's stock with no order and no ledger row; the caller sees `TypeError`. `reserve_stock` then returns False for everyone, which `checkout` currently ignores. A replacement validator that raises leaves stock debited, and one that returns a normalized order changes neither stock nor total.
- fix: run the pipeline first, use its return value, then reserve and price; give `DefaultPipeline` the actual checks for the fields in F1-F4 and F6.
- premise: no check of payload shape or range precedes `inventory.reserve_stock` on any route into `checkout`.
- premise_provenance: independent
- trigger: `{"sku":"demo-sku","qty":10,"net":"x"}`: `STOCK` goes from 10 to 0, then `"x" * 0 / 100` raises `TypeError` at `pricing.py:14`. No `release_stock` call exists in the path. Also `OrderService(pipeline_cls=Strict)` where `Strict.step` raises on `qty <= 0`: the reservation has already happened.
- counterevidence_checked: `release_stock` callers: none in the app. `try` or compensation in `checkout`: none. Missing `sku` or `qty` raises `KeyError` before any effect, so only absent keys are closed. `order["validated"]` has no reader in the app.
- introduced_by_candidate: n/a
- evidence_class: derived

### job-07-F6: `channel` documented as configuration is read from the order, and an unknown value is rejected only after the ledger write (Low)

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 29 (also `notifications.py:1`, `notifications.py:14`)
- evidence: `order.get("channel", "email_receipt")` against "il canale arriva dalla configurazione come stringa" (`notifications.py:1`) and "canale configurato" (`:19`).
- severity: Low
- confidence: 80
- consequence: the caller receives `KeyError: 'nope'` for an order already in the ledger with stock debited, and each retry adds another row and debit. The caller can also pick any configured handler; what that exposes depends on the operator's mapping (gap).
- fix: resolve the channel from configuration, or check it against the mapping keys before any effect.
- premise: the handler key at `notifications.py:14` is the payload's `channel`, looked up only after `service.py:25` and `:28`.
- premise_provenance: independent
- trigger: `{"sku":"demo-sku","qty":1,"net":10,"channel":"nope"}` with `ORDER_NOTIFY_HANDLERS` set.
- counterevidence_checked: arbitrary code loading from the payload is closed: `mapping[channel]` admits only operator-defined keys, and module and function names come only from the environment, so this finding does not claim code execution. The importlib structure itself is pinned by `test_app_structures.py:56-57`.
- introduced_by_candidate: n/a
- evidence_class: derived

## Examined scope and completed checks

All 9 scoped files, plus `payments/*`, `shipping/*`, `app/pyproject.toml` and `test_app_structures.py` for context. Taxonomy sections read: 6.14 and the monetary 6.13 of `security.md`; others not applicable given the sink search below.

- Sink search across orders for eval, exec, compile, pickle, marshal, shelve, yaml, subprocess, popen, os.system, sqlite, Template, format_map, `.format(`, `re.*`, gzip, zlib, literal_eval, json.load(s): 0 matches. No SQL, shell, template, deserialization, regex or decompression surface.
- `EVENT_REGISTRY[name]` (`api.py:26`): `name` selects only registered callbacks, closed. `setattr` (`service.py:21`): fixed attribute, `pipeline_cls` comes from code, closed.
- `LEDGER_PATH` and `LOCK_PATH`: fixed literals, no input reaches a path.
- `reporting.py:14`: same newline shape as F1, but no caller exists and the docstring assigns formatting to the caller. No finding.
- `big_module.py`: `json.dumps` escapes every value, so newlines cannot break a record; no caller exists. No finding.

## Cross-Reviewer Notes

- local-correctness: `service.py:25` discards the `reserve_stock` result, so insufficient stock does not stop checkout.
- logic-integrity: `pricing.py:19` subtracts `compute_discount` twice against `pricing.py:18`, lowering the negative-total threshold in F2 from above 100% to above 50%.
- logic-integrity: `ledger.py:30` writes no amount or VAT portion against the `ledger.py:26` docstring, and `record_refund` accepts any or no id.
- resource-lifecycle: `inventory.py:14` retains one lock per distinct payload SKU forever, with no check that the SKU exists.
- local-correctness: `notifications.py:13-14` parses operator config on each send; an empty value or trailing comma raises `ValueError`, and a space after a comma yields `KeyError`, both only after the ledger write. Operator-controlled, so not an adversarial finding.
- local-correctness: `api.py:3` promises `KeyError` with the event name, but `service.py:25`, `notifications.py:13` and `:14` raise `KeyError` through the same call, so a caller cannot tell them apart.
- data-representation: `big_module.py:16-17` formats bools and integer ids with `.2f` (`True` becomes `1.00`), and an int too large for float raises `OverflowError`.
- data-representation: `ledger.py:18` and `:30` write a missing id as `?`, leaving a row attributable to no order.
