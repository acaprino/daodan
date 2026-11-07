# Scope: content-orders

- Request (verbatim): "Cerca problemi nel modulo ordini del benchmark scope-resolution."
- Shape `branch`, variant `team-review`, kind `changeset` (source files), basis `content`: no comparison named, no diff; the review judges current content, preexisting defects included.
- Candidate: `943bdc44c66dfd9782f6d38c82922a1f08783653`, detached work tree `D:/Projects/daodan/.claude/worktrees/bench-branch-943bdc44c`.
- Flags: all defaults. Governing policy: `AGENTS.md` of the work tree.
- Intent: no change is under review; find defects in the orders package of the demo app the scope-resolution benchmark uses as its target ("Mini-app dimostrativa ... solo stdlib", `benchmarks/scope-resolution/app/pyproject.toml:4`). Source: the request and that manifest.

## Request to files

Outcome: `resolved`. Stopped because the request names one package and its directory is complete: 3 map queries and 1 outline, then the 8 non-empty files read.

| File | Evidence |
|---|---|
| `benchmarks/scope-resolution/app/packages/orders/__init__.py` | Package marker, empty |
| `benchmarks/scope-resolution/app/packages/orders/api.py` | `api.py:1` "Entry point degli eventi ordine" |
| `benchmarks/scope-resolution/app/packages/orders/service.py` | `service.py:1` "Servizio ordini" |
| `benchmarks/scope-resolution/app/packages/orders/pricing.py` | `pricing.py:1` "totale ordine, sconto cliente e IVA" |
| `benchmarks/scope-resolution/app/packages/orders/inventory.py` | `service.py:7` imported; `inventory.py:17` `reserve_stock` |
| `benchmarks/scope-resolution/app/packages/orders/ledger.py` | `service.py:7` imported; `ledger.py:1` "voci ordine" |
| `benchmarks/scope-resolution/app/packages/orders/notifications.py` | `service.py:7` imported; `notifications.py:1` |
| `benchmarks/scope-resolution/app/packages/orders/reporting.py` | In the package; `reporting.py:6` imports pricing |
| `benchmarks/scope-resolution/app/packages/orders/big_module.py` | In the package; `big_module.py:1` audit-entry formatting |

Not in scope, read as context only: `packages/payments/*`, `packages/shipping/*`, `app/pyproject.toml`, `benchmarks/scope-resolution/test_app_structures.py`.

## Gaps of this phase

- `codebase_map_modules(query="ordini")`: `unknown`, "no module, alias or path matches the name".
- `codebase_map_modules(query="benchmarks/scope-resolution")`: `unknown`, same reason.
- `codebase_map_modules(query="orders")`: `Error executing tool codebase_map_modules: 'location'`.
- `codebase_map_search`: empty with `index_state: stale`, gap `retrieval_stale: binding differs: sqlite_version; run codebase_map_index(run_id='daodan-lite-20261107-2')`. Not an empty search; not repaired by rule of this run. Text search used.
- `codebase_map_graph`: `Error executing tool codebase_map_graph: parser fingerprint changed or is missing; refresh the manifest`. Call edges come from reading imports and calls in the source.
- Run `daodan-lite-20261107-2` is bound to commit `7bd0ff186c50`, not to the candidate; `codebase_map_outline` worked and served only to locate. Decisive content was read from the work tree.
- No protocol run record exists for this standalone review.

## Pre-review work tree

`git status --porcelain` output: empty (saved at `tools/pre-review-status.txt`).
