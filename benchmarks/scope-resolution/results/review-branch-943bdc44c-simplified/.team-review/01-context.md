# Context

## Object

`benchmarks/scope-resolution/app/` is a small stdlib-only orders app, the fixture of the scope-resolution benchmark (`benchmarks/scope-resolution/README.md`). It is not shipped software. The benchmark measures which files a resolver or model selects on a real Codebase Map run of this app.

## Relevant source (candidate work tree)

All paths are under `benchmarks/scope-resolution/`.

| Reference | What it is |
|---|---|
| `app/packages/orders/pricing.py:11-14` | `compute_discount(order)` and its docstring |
| `app/packages/orders/pricing.py:17-20` | `compute_total(order)` and its docstring: the changed function |
| `app/packages/orders/pricing.py:6-8` | `vat_amount(net)`, callee |
| `app/packages/orders/service.py:23-30` | `OrderService.checkout`, the only static caller of `compute_total` (line 26) |
| `app/packages/orders/api.py:34-39` | `register_defaults`: `checkout` event wired to `service.checkout` |
| `app/packages/orders/ledger.py:13-22` | `ledger.record(order, total)`: persists the returned total |
| `app/packages/orders/reporting.py:11` | uses only `pricing.VAT_RATE` |
| `ground_truth.json` (C1, C5 rationales) | cites `pricing.py:11`, `pricing.py:19`, `service.py:26` |
| `CASES.md`, `README.md`, `results/` | cases, declared measurements, frozen run outputs |
| `test_app_structures.py:70-72`, `test_resolver.py:47-50` | tests naming this code |

## Map evidence

Run `daodan-lite-20261107-2`, root `D:/Projects/daodan`, commit `7bd0ff186c50` (dirty), completed before the candidate. It is bound to an earlier revision: use it to locate code and read what decides from the work tree. Saved packet: `OUT/tools/edit-impact-summary.json`. It lists `compute_total` with one caller and two callees, and related tests 0. `codebase_map_search` returns an empty result with a stale-index gap on this run: use text search.

## Evidence pack (candidate, `app/packages/orders/pricing.py`)

| Tool | Command | Exit | Output |
|---|---|---|---|
| ruff 0.15.20 | `python -B -m ruff check --no-cache` | 0 | `OUT/tools/ruff-check.txt` |
| ruff 0.15.20 | `python -B -m ruff format --no-cache --check` | 0 | `OUT/tools/ruff-format.txt` |
| vulture 2.16 | `python -B -m vulture --min-confidence 80` | 0 | `OUT/tools/vulture.txt` |
| pytest 9.1.1 | `python -B -m pytest -q -p no:cacheprovider test_app_structures.py` | 0, 11 passed | `OUT/tools/pytest-app-structures.txt` |

Not installed: mypy, pyright, complexipy, radon. No project lint or test configuration exists for this fixture beyond the benchmark's own pytest command.
