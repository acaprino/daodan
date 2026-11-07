# Context: branch-943bdc44c-simplified

Index of hypotheses from the coordinator, not ground truth. Confirm against source before using anything here as a premise.

## Object

`benchmarks/scope-resolution/app/` is the benchmark's mini-app (`orders-demo`, standard library only, `app/pyproject.toml`). The commit changes one expression in `orders/pricing.py::compute_total` (line 19). Signature, callees and line numbers are unchanged.

## Stated contracts, read from the candidate

Paths relative to `benchmarks/scope-resolution/app/packages/`.

| Where | Text |
|---|---|
| `orders/pricing.py:1` | module: order total, customer discount and VAT |
| `orders/pricing.py:12` | `compute_discount`: loyalty percentage applied to the net |
| `orders/pricing.py:18` | `compute_total`: "netto - sconto cliente + IVA (VAT)" |
| `orders/service.py:24` | `checkout`: stock, total with VAT, ledger, notification |
| `orders/ledger.py:14` | `record`: records order and total, VAT included |
| `orders/api.py:5-6` | the order total includes VAT computed by the pricing module |

No separate requirement document for these amounts was located. No test exercises the amounts: `test_app_structures.py` checks structure and importability.

## Call evidence

- Map run `daodan-lite-20261107-2`, `edit_impact` on `compute_total`: caller `orders/service.py::OrderService.checkout` (site line 26), callees `compute_discount` and `vat_amount`, blind spot `order.get`. Bound to an earlier revision than the candidate: its digests describe that revision, not this one. Saved at `OUT/tools/edit-impact.json`.
- Not visible to the graph, found by reading: `orders/api.py:37` registers `service.checkout` as the `checkout` event callback, reached through `Dispatcher.handle` (`orders/api.py:29`).
- Value flow to read: `orders/service.py:26`, `:28`, `:30`; `orders/ledger.py:18`.
- Fields also named `total`, link not established: `payments/gateway.py:10`, `:15`, `orders/reporting.py:14`.

## Evidence pack (candidate, `OUT/tools/`)

| Tool | Command | Exit | Output |
|---|---|---|---|
| ruff 0.15.20 | `ruff check --no-cache pricing.py` | 0 | `ruff-check.txt` |
| ruff 0.15.20 | `ruff format --check --no-cache pricing.py` | 0 | `ruff-format.txt` |
| vulture 2.16 | `vulture --min-confidence 80 pricing.py` | 0 | `vulture.txt` |
| radon 6.0.1 | `radon cc -s pricing.py` | 0 | `radon-cc.txt` |
| pytest 9.1.1 | `python -B -m pytest -q -p no:cacheprovider test_app_structures.py`, on a copy at `OUT/scratch/candidate` | 0, 11 passed | `pytest-app-structures.txt` |

Missing: `mypy` and `pyright` (`pip install mypy`), `complexipy` (`pip install complexipy`). No project ruff or type-checker configuration at the repository root.

## Map gaps

- No base and candidate snapshot pair exists for these two refs: `stale_callers` is unavailable and the digests above are not bound to the delta.
- `codebase_map_search` returned `index_state: stale` with `retrieval_stale: binding differs: sqlite_version; run codebase_map_index(run_id='daodan-lite-20261107-2')`. Use text search; the index is not repaired in this review.
- `codebase_map_diff` compares with the main checkout, not this work tree: `parser_changed: true`, 264 files modified, 117 added, 75 removed. Every map row is a lead.
