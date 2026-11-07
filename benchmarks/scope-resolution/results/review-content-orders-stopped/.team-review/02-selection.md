# Selection

Each reviewer covers the whole scope with its own mandate.

| Reviewer | Why |
|---|---|
| `senior-review:local-correctness-auditor` | Money arithmetic, discarded return values, partial success and error outcomes in every module |
| `senior-review:logic-integrity-auditor` | Docstrings state money, VAT and refund rules; checkout orders stock, ledger and notification across components |
| `senior-review:local-concurrency-auditor` | Per-sku thread locks, process-wide dicts and an exclusive lockfile shared by every ledger writer |
| `senior-review:resource-lifecycle-auditor` | The lockfile and its descriptor in `ledger.py` are acquired and released by hand; `_LOCKS` is a retained registry |
| `senior-review:transaction-integrity-auditor` | The ledger file is the only persistent store; repeated events and interrupted checkouts bear on its invariants |
| `senior-review:data-representation-auditor` | Money as float with rounding, and values written to the ledger and audit formatters |
| `senior-review:input-validation-auditor` | Payload values reach arithmetic and stock, and an order field selects a handler loaded with importlib |

Not selected, with evidence:

- `temporal-resilience-auditor`: no timer, scheduler, retry or worker in scope; the lockfile's failure paths are covered by the resource and concurrency reviewers.
- `remote-effect-auditor`: no provider contract in source; the notification handler is external and its partial-failure consequence stays with the local reviewers. Provider semantics remain a gap.
- `application-reachability-auditor`, `cleanup-auditor`: cleanup was not requested; `test_app_structures.py` pins `big_module.py` as intentional. Reachability is not audited.
- `premise-auditor`: not a defect hunter by its mandate; it stays available as Lens 0 (`support`).
- `performance-auditor` family: the roster's signal is `sorted(` on one entry's keys; no SQL, asset, quota or billing surface.
- `security-auditor` family other than input validation: no identity, credential, browser, upload, callback signature or AI surface in scope; no approved audit obligation for `audit-trail-auditor`.
- `api-contract-auditor`, `chicken-egg-detector`, `environment-binding-auditor`, UI and accessibility roles: no schema, startup sequence, deployment layer or UI in scope.

## Stack dimensions

- python: active (`.py` target). Former python-development methods unavailable: declared missing baseline.
- dependencies: skipped, no manifest in scope and `app/pyproject.toml` declares none.
- react, typescript, platform: skipped, no such file in scope.

## Unavailable competence, declared gaps

- Python stack baseline, as above.
- Testing quality: no specialist in the base. Signal: the only test is structural.
- Structural entropy: no specialist in the base. Signals: `VAT_RATE` in both `pricing.py` and `payments/refunds.py`; 105 same-body formatters.
- Workspace hygiene: no specialist in the base; not signalled.

## Knowledge

`knowledge_selection: ""`. Host inventory read from the session's skill list: no skill there is review knowledge classified for this scope; `defect-taxonomy` reaches workers through their role bodies. Catalog validation unavailable.

## Plan

Target `orders` package at candidate `943bdc44c`, content basis. Tier `medium` (9 production files), verification `all-above-floor`, critic not in the tier. Seven reviewers above, dispatched one after another. Gaps as listed here and in `00-scope.md`.
