# Context: branch-943bdc44c

Built by the coordinator in Phase 1 with the complete run `daodan-lite-20261107-2` (repo_revision 7bd0ff186c50). For the scoped files the run holds base-side content: map `raw_hash` of pricing.py = base blob `d656c18b842129ac`, of service.py = base blob `3d75edaff842000b` (service.py is unchanged by the candidate). Map calls went through the `MapService` backend (`OUT/tools/map_call.py`, `python -B`) because the MCP tools are not exposed in this session; raw outputs are in `OUT/tools/`. Paths are repository-relative; `A` = `benchmarks/scope-resolution/app/packages`. Version tags: `@run` = run daodan-lite-20261107-2, `@base` = 6dd2c2bbf, `@cand` = 943bdc44c.

**Epistemic status:** an index of hypotheses from one observer, not ground truth. Re-derive before use.

## Static facts

Tool-reported.

- S1. `symbols_at` on `A/orders/pricing.py` lines 16-20 -> one symbol `A/orders/pricing.py::compute_total`, function, lines 17-20, public, one parameter `order`, body_hash `sha256:409ad5cbd18ea5dc` (base side) @run. Gaps: none. (tools/symbols_at.json)
- S2. `edit_impact(["A/orders/pricing.py::compute_total"])` @run: callers total 1 -> `A/orders/service.py::OrderService.checkout` lines 23-30; callees total 2 -> `A/orders/pricing.py::compute_discount` 11-14 and `A/orders/pricing.py::vat_amount` 6-8; `related_tests_total` 0; blind spot `order.get` (unknown-receiver); `edge_view.coverage.status` `missing_store` (no engine store, lexical edges only); `freshness_basis` lexical; `do_not_touch` unavailable ("requires a base/candidate fingerprint delta; use stale-callers"); `recent_changes` []. (tools/edit_impact.json)
- S3. `edit_impact(["A/orders/service.py::OrderService.checkout"], include_source=false)` @run: callers total 0; callees `A/orders/inventory.py::reserve_stock`, `A/orders/ledger.py::record`, `A/orders/notifications.py::send_via`, `A/orders/pricing.py::compute_total`; blind spots `order.get`, `self._pipeline.step` (unknown-receiver); `related_tests_total` 0. (tools/edit_impact-checkout.json)
- S4. `graph(paths=["A/orders/pricing.py"], hops=1)` @run **failed**: `ValueError: path is missing or inaccessible: D:\Projects\daodan\plugins\codebase-map\skills\map-method\SKILL.md` (raised in `source_reader._no_links`, called from `store_graph._preflight`; the run's inventory still lists the pre-rename `skills/map-method/` paths). Fallback: text search, rows marked below. (tools/graph-pricing.json)
- S5. `search("compute_total")` @run: exact `A/orders/pricing.py::compute_total`; 193 matched, 15 returned; source hits in `A/orders/pricing.py` and `A/orders/service.py` (method, class); the rest are benchmark result JSON files and a tools guide. `search("compute_discount")`: exact `A/orders/pricing.py::compute_discount`; also `benchmarks/scope-resolution/test_app_structures.py` (function hit). Index fresh; embedding unavailable. (tools/search-*.json)
- S6. `modules(query="orders")` @run: `resolved`, module `orders` = `A/orders/*` (workspace member, description null). (tools/modules-orders.json)
- S7. Text search @cand (`git grep`; fallback: text search for S4): `pricing.compute_total` occurs only at `A/orders/service.py:26`; `from . import ... pricing` at `A/orders/service.py:7` and `A/orders/reporting.py:6`; `reporting.py` uses only `pricing.VAT_RATE` (`A/orders/reporting.py:11`); `on_event("checkout", service.checkout)` at `A/orders/api.py:37`; `A/payments/gateway.py:10,15` read `order.get("total", 0)`; no code writes `order["total"]`. (fallback: text search)
- S8. Diff @base..@cand: one hunk; `A/orders/pricing.py:19` `net = order.get("net", 0) - compute_discount(order)` becomes `net = order.get("net", 0) - compute_discount(order) - compute_discount(order)`. `review_roster.py` lists touched symbol `compute_discount` (taken from the hunk header `def compute_discount(order):`); S1 places the changed line in `compute_total`.
- S9. Evidence pack @cand (00-scope.md): ruff check/format clean, vulture clean, radon all A(1); `test_app_structures.py` 11 passed on base and candidate copies; no test imports `pricing`; mypy/pyright/complexipy absent.
- S10. Codebase Map knowledge leads through the permitted tools: `edit_impact` card `null` for compute_total; module description `null`. They add nothing to and contradict nothing in `01a-review-knowledge-leads.md`.

## Supported descriptions

Behaviour the cited code shows; re-derive before use.

- D1. `compute_discount(order)` returns `round(order.get("net", 0) * order.get("loyalty_percent", 0) / 100, 2)` and does not mutate `order` (`A/orders/pricing.py:11-14` @cand), so both calls at :19 return the same value d.
- D2. @base `compute_total` computes `net' = net - d`; @cand it computes `net' = net - 2d`; both return `round(net' + vat_amount(net'), 2)` with `vat_amount(x) = round(x * 0.22, 2)` (`A/orders/pricing.py:3,6-8,19-20`).
- D3. Derived example (not executed): order `{"net": 100, "loyalty_percent": 10}` gives d = 10.0; @base net' 90.0, VAT 19.8, total 109.8; @cand net' 80.0, VAT 17.6, total 97.6. With `loyalty_percent` 0 both sides return the same total.
- D4. `OrderService.checkout` stores `total = pricing.compute_total(order)`, passes it to `ledger.record(order, total)`, which appends `{id}<TAB>{total}` to `ledger.log`, and returns it (`A/orders/service.py:23-30`, `A/orders/ledger.py:13-22` @cand, unchanged).
- D5. `register_defaults()` registers `service.checkout` for event `checkout`; `Dispatcher.handle` -> `_invoke` -> `EVENT_REGISTRY[name](payload)` (`A/orders/api.py:25-39` @cand), so the payload dict reaches `compute_total` unvalidated (fallback: text search for the callback edge, which S3 does not see).
- D6. Docstrings unchanged by the candidate: `compute_total` "Totale ordine: netto - sconto cliente + IVA (VAT)." (`A/orders/pricing.py:18`); `compute_discount` "Sconto cliente: percentuale di fedeltà applicata al netto." (`:12`); module "Prezzi: totale ordine, sconto cliente e IVA (VAT)." (`:1`).

## Hypotheses

- H1. Contradiction between sources: the code at `A/orders/pricing.py:19` @cand subtracts the loyalty discount twice, while the unchanged docstring at `A/orders/pricing.py:18` @cand states one discount term ("netto - sconto cliente + IVA"). Other side: the commit message "aggiorna il calcolo in pricing.py" announces an intended change of the calculation but states no rule; no requirement, test or document found supports a double discount (01a, "Concepts with no lead found").
- H2. VAT is now computed on `net - 2d`, so it falls by `0.22 * d` relative to @base (`A/orders/pricing.py:20`).
- H3. For `loyalty_percent` > 50 the @cand net' is negative (`net - 2 * net * p / 100 < 0`), giving a negative VAT and total that checkout records in the ledger; @base reaches a negative net only above 100 (`A/orders/pricing.py:13-14,19-20`; `A/orders/service.py:26-28`).
- H4. The only consumer of the value is `OrderService.checkout` (S2, S7); the payments gateway reads `order["total"]`, which nothing found writes from `compute_total` (S7), so whether payments see the new total is unknown.

## Not covered

- Graph expansion (S4 failed): beyond one hop only text search; `notifications.send_via` targets loaded by `importlib` (`A/orders/notifications.py:7-15`) were not followed.
- `stale-callers`: unavailable (single base-side run; no candidate run).
- `A/payments/refunds.py` (own VAT copy), `A/shipping/rates.py` (`volume_discount`), `A/orders/big_module.py`, `inventory.py`, `reporting.py` beyond the S7 line: not read; S7 shows no dependency on `compute_total` or `compute_discount`.
- Codebase Map analysis artifacts (`01..07.md`, knowledge/): not read (not among the permitted tools).
- No test exercises `compute_total`, `compute_discount` or `vat_amount` numerically (S2, S9): no test exercises compute_total.

## Questions

| Id | Question | Context reference |
|---|---|---|
| Q1 | Does `compute_total` still compute "netto - sconto cliente + IVA" for an order with `loyalty_percent` != 0, or does it now subtract the loyalty discount twice? | H1; S8; D1-D3, D6 (`A/orders/pricing.py:18-19` @cand) |
| Q2 | Is VAT still computed on the intended taxable base (net minus one discount)? | H2; D2 (`A/orders/pricing.py:20`, `:6-8`) |
| Q3 | For which inputs does the new net become negative, and what do checkout and the ledger then record? | H3; D1, D4 (`A/orders/pricing.py:13-14,19-20`; `A/orders/service.py:26-28`; `A/orders/ledger.py:18`) |
| Q4 | What do the consumers of `compute_total` observe (checkout return value, ledger line, the `checkout` event callback), and does any other consumer depend on the value? | S2, S3, S7; D4, D5; H4 |
