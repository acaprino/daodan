# Context: the orders package

An index of what the coordinator read, not ground truth: confirm every premise in source. Paths are under `benchmarks/scope-resolution/app/packages/orders/` unless stated.

## Purpose and flow

Stdlib-only demo orders app (`../../pyproject.toml:4`), Italian docstrings. No README or specification states business rules for it beyond these docstrings, which are the available semantic contract.

- `api.py`: process-wide `EVENT_REGISTRY` (`:10`), `on_event` (`:13`), `Dispatcher.handle` -> `_invoke` (`:25-31`), `register_defaults` wires `checkout` and `refund_request` on one `OrderService` (`:34-39`). Docstring: a missing registration raises `KeyError` with the event name; callbacks get the payload as it is.
- `service.py`: `OrderService.checkout` (`:23-30`) calls `inventory.reserve_stock`, `pricing.compute_total`, `self._pipeline.step`, `ledger.record`, `notifications.send_via`, and returns the total. `refund_request` (`:32-34`) calls `ledger.record_refund`. `DefaultPipeline.step` (`:13-15`); the pipeline class is replaceable (`:19-21`).
- `pricing.py`: `VAT_RATE` (`:3`), `vat_amount` (`:6`), `compute_discount` (`:11`), `compute_total` (`:17`). Docstring contract of the total: "netto - sconto cliente + IVA (VAT)" (`:18`).
- `inventory.py`: in-memory `STOCK` (`:7`), per-sku locks `_LOCKS` under `_GUARD` (`:8-14`), `reserve_stock` returns a boolean (`:17-24`), `release_stock` (`:27-31`).
- `ledger.py`: cwd-relative `LEDGER_PATH` and `LOCK_PATH` (`:5-6`), `_acquire_lock` with `O_CREAT | O_EXCL` (`:9-10`), `record` (`:13-22`), `record_refund` (`:25-34`), whose docstring promises a reversal with the VAT portion.
- `notifications.py`: `_handler_for` parses env `ORDER_NOTIFY_HANDLERS` ("canale=modulo:funzione,...") and loads with importlib (`:11-15`); `send_via` (`:18-21`).
- `reporting.py`: `format_daily_summary` (`:9-15`), header from `pricing.VAT_RATE`.
- `big_module.py`: 2108 lines, audit-entry formatters. Census at `tools/big_module-census.json` (AST normalized for name, docstring and label): 105 top-level functions, one distinct normalized body, plus `AUDIT_SCHEMA` and one import. Read one body closely and use the census for the rest, or say otherwise.

## Consumers and neighbours

- In `app/`, nothing outside the package imports `orders`. Only `api.py` and `service.py` and `reporting.py` import siblings (`api.py:8`, `service.py:7`, `reporting.py:6`). No import of `big_module` or `reporting` found by text search in `app/`.
- `../payments/refunds.py` has its own `VAT_RATE` (`:7`) and `vat_portion`, `issue_refund`; nothing in orders calls them. `../payments/gateway.py` and `../shipping/rates.py` do not touch orders.
- `benchmarks/scope-resolution/test_app_structures.py` is the only test that imports the package. It pins these as intentional structures of the benchmark app, by text: `EVENT_REGISTRY`, `on_event`, `_invoke`, "KeyError" in `api.py`; `setattr(` and `self._pipeline.step(` in `service.py`; `os.environ[` and `importlib.import_module(` in `notifications.py`; `pricing.VAT_RATE` as the only pricing use in `reporting.py`; size of `big_module.py`. It asserts no runtime behaviour of checkout, pricing, stock or ledger.

## Evidence pack (candidate 943bdc44c, Python 3.13.14)

| Tool | Command | Exit | Output |
|---|---|---|---|
| ruff 0.15.20 | `ruff check --no-cache --output-format=concise <orders>` | 0 | `tools/ruff-check.txt`: all checks passed |
| ruff 0.15.20 | `ruff format --no-cache --check <orders>` | 1 | `tools/ruff-format.txt`: 7 of 9 files would be reformatted; no formatter is configured in the project, style is no finding |
| vulture 2.16 | `vulture --min-confidence 80 <orders>` | 0 | `tools/vulture.txt`: empty |
| pytest 9.1.1 | `pytest -p no:cacheprovider -q test_app_structures.py`, on the copy `scratch/structures` | 0 | `tools/pytest-structures.txt`: 11 passed |

Missing tools, gaps: mypy and pyright (`pip install mypy`), complexipy and radon (`pip install radon`). No secret scanner configured. No project lint, build or test command is declared for the app.

## Map

Run `daodan-lite-20261107-2`, bound to `7bd0ff186c50`, not the candidate. `codebase_map_outline` and `codebase_map_read` may help locate. `codebase_map_search` (stale index) and `codebase_map_graph` (parser fingerprint) fail: use text search in the work tree.
