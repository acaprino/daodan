---
dimension: resource-lifecycle
reviewer: senior-review:resource-lifecycle-auditor
status: delivered
job_id: job-04
candidate: 943bdc44c66dfd9782f6d38c82922a1f08783653
body_sha256: ee9dc6d6abe457b3c59507bb9853d634b21504c825a630e999f82e425603dc3c
scope_id: orders-module
output_path: D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/blind-b/jobs/job-04.md
knowledge_usage: []
gaps:
  - Static inspection only, no runtime exercise; every process-death and interrupt path below is derived from language semantics.
  - No host process, entry point or shutdown path exists in `app/`, so supervisor behaviour and restart policy are unknown.
  - The env-loaded notification handler and any custom `pipeline_cls` are outside the source; what they acquire is unknown.
  - The assigned body_sha256 was not reproduced: raw file 8e02c111..., frontmatter stripped da701fce... and 79e2536c.... The normalization is unknown. The body on disk was applied.
member_results:
  - specialist_id: senior-review:resource-lifecycle-auditor
    status: delivered
    coverage: complete
    finding_ids: [job-04-F1, job-04-F2, job-04-F3]
    gaps: as above
---

# Resource lifecycle: orders package

## Findings

### job-04-F1: a dead process leaves `ledger.lock` behind and blocks every later ledger write

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 10 (release at 19-21, 31-33)
- severity: Medium. The impact is total once triggered, but the window is one append and nothing in scope shows a deployed long-running host.
- confidence: 90
- evidence:
  - Acquire: `os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)` (`ledger.py:10`), called from `record` (`:15`) and `record_refund` (`:27`).
  - Owner: the directory entry is the lock. `fd` holds no OS lock and is kept only to be closed, so ownership is not tied to the process.
  - Release: `finally` (`:19-21`, `:31-33`), which covers Python exceptions and nothing else.
  - Broken exits:
    - SIGKILL, default-disposition SIGTERM (no `signal` use anywhere in `app/`), `os._exit`, OOM kill or power loss between `:10` and `:21`.
    - `os.close(fd)` raising at `:20` skips the unlink at `:21`.
    - `unlink` raising at `:21` leaves the lock and replaces any in-flight exception.
    - KeyboardInterrupt landing between `fd = _acquire_lock()` and `try`, or between `:20` and `:21`.
  - Sequence: the process dies while appending; `ledger.lock` stays in the cwd; after restart every `_acquire_lock` raises `FileExistsError` on `ledger.lock`.
- consequence: after one such exit, every `checkout` (`service.py:28`) and every `refund_request` (`service.py:34`) raises `FileExistsError` until an operator deletes the file. A restart does not fix it, unlike a thread lock. The error names only a relative path, so the operator must also work out the process's cwd. Each blocked checkout also consumes stock (job-04-F2).
- premise: no code path removes or overrides a `ledger.lock` left by a holder that no longer exists.
- premise_provenance: independent
- trigger: process termination, or a failure in the release sequence, while the lock is held.
- counterevidence_checked:
  - Python exceptions inside the write, including `open` failure, `order.get` failure and write or close errors, are covered by `finally`; they are not reported.
  - Acquire failure correctly sits outside `try`, so a loser does not unlink the winner's lock.
  - No pid, mtime, TTL, retry or stale check exists in `ledger.py`.
  - No `atexit`, `signal` or lock cleanup exists in `app/` (text search).
  - `test_app_structures.py` pins nothing in `ledger.py`.
- introduced_by_candidate: n/a
- evidence_class: derived
- fix: make the OS own the release. Keep a permanent lock file and take `fcntl.flock` or `msvcrt.locking` on the existing `fd`; the OS drops it on process death. Put acquire and release in one context manager used by both `record` and `record_refund`, so the release order lives in one place. Whether contention waits or fails stays with the concurrency owner.

### job-04-F2: a granted stock reservation is never released when checkout fails before the ledger

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 25 (release defined at `inventory.py:27`, no caller)
- severity: Medium
- confidence: 85
- evidence:
  - Rule evidence: `inventory.py:17-18` and `:27-28` define a held quantity with a release operation for a cancelled order. No text defines a failed checkout, so treating an unrecorded failed order as abandoned is my inference.
  - Acquire: `inventory.reserve_stock(order["sku"], order["qty"])` (`service.py:25`) subtracts from `STOCK` (`inventory.py:23`).
  - Owner: `checkout`, and only it. The boolean is discarded and nothing returns it, so a caller catching the exception cannot tell whether units were granted. A blind `release_stock` could inflate stock.
  - Broken exits, all without `try` in `checkout` (`service.py:23-30`):
    - `pricing.compute_total` raising, e.g. `TypeError` at `pricing.py:14` for `net="10"`.
    - `self._pipeline.step` raising (`service.py:27`), the natural way for a replacement validation class (`service.py:19-21`) to reject an order.
    - `ledger.record` raising (`service.py:28`), including `FileExistsError` when another writer holds the lock (`ledger.py:10`, no wait) or after job-04-F1.
  - Release: text search of `app/` finds `release_stock` only at its definition.
  - Sequence with the seeded `STOCK = {"demo-sku": 10}`: failed checkouts totalling 10 units leave `STOCK["demo-sku"]` at 0 with no ledger line for any of them, until the process restarts.
- consequence: stock is under-counted for the process lifetime with no matching sale, and later `reserve_stock` calls return False for units nobody bought. Today checkout ignores that False, so the visible effect is a wrong stock figure; once the return is honoured, customers are refused stock that was never sold.
- premise: no path after a granted `reserve_stock` returns the units when `checkout` raises before `ledger.record` completes.
- premise_provenance: independent
- trigger: a `checkout` event with non-numeric `net`, a pipeline that raises, or a concurrent or stale ledger lock.
- counterevidence_checked:
  - `Dispatcher` (`api.py:25-31`) adds no handling.
  - Nothing in `app/` or the structural test calls `release_stock`.
  - A failure in `send_via` (`service.py:29`) is excluded: the order is already recorded, so keeping the reservation is defensible.
  - A restart resets the in-memory `STOCK`, which limits the leak's duration.
- introduced_by_candidate: n/a
- evidence_class: derived
- fix: reserve after the steps that can reject (`compute_total`, `step`), act on the returned boolean, and compensate only around the ledger write with `try`/`except BaseException: inventory.release_stock(...); raise`. Keep notification outside that scope.

### job-04-F3: `_LOCKS` keeps one entry per sku value forever, even for skus refused

- file: `benchmarks/scope-resolution/app/packages/orders/inventory.py`
- line: 14
- severity: Low
- confidence: 70
- evidence:
  - What grows: `_LOCKS.setdefault(sku, threading.Lock())` (`:14`) runs before the stock check at `:20`, keyed by `order["sku"]` from a payload passed as is (`api.py:4`, `service.py:25`).
  - Useful lifetime over: for a sku absent from `STOCK`, `reserve_stock` returns False (`:21-22`) and creates no stock entry, so the lock has guarded nothing once the `with` exits.
  - What keeps it reachable: the module global `_LOCKS`. No removal exists, and naive eviction would be unsafe because it could split lock identity for a waiting thread.
- consequence: process memory grows with each new distinct sku value for the process lifetime. An operator would see only slow memory growth, with no error. Growth rate is not quantified, because no workload or ingress exists in scope.
- premise: nothing bounds the set of sku values that reach `_lock_for`.
- premise_provenance: independent
- trigger: `checkout` events carrying an unbounded stream of distinct sku values.
- counterevidence_checked:
  - No validation exists in `api.py`, `service.py` or the default pipeline.
  - A sku domain bounded upstream would make this harmless process-lifetime retention; no such bound is visible in scope, and this is why confidence and severity stay low.
  - Unhashable skus raise `TypeError` inside `with _GUARD` and release correctly.
  - `test_app_structures.py` does not pin `_LOCKS`.
- introduced_by_candidate: n/a
- evidence_class: derived
- fix: in `reserve_stock`, return False before allocating a lock when the sku is absent from `STOCK`, re-reading under the lock as today. `_LOCKS` is then bounded by the keys of `STOCK`, and the per-sku design stated at `inventory.py:1` stays.

## Examined scope and completed checks

All 9 files were read. `big_module.py`: the first functions were read and the census (one normalized body across 105 functions) applied; text search found no acquire, open, try or lock construct. `__init__.py` is empty.

| Resource class | Result |
|---|---|
| Lockfile and descriptor (`ledger.py:10`) | Exception paths released once; process death and release failures are job-04-F1 |
| Ledger stream (`ledger.py:17`, `:29`) | `with` covers all exits; `ledger.log` growth is required retention, not a finding |
| Double release of the lockfile | One `finally` per acquire. Unlink by name could remove another owner's lock only after an external deletion; no such path in scope |
| `_GUARD`, per-sku locks | `with` covers early return and exceptions; `_GUARD` is released before the sku lock is taken, so there is no nested hold |
| Locks across external calls | `send_via`, `step` and `compute_total` all run outside both locks, so a handler re-entering the ledger cannot self-block |
| Stock reservation | job-04-F2 |
| `_LOCKS`, `STOCK`, `EVENT_REGISTRY` | `_LOCKS` is job-04-F3. `STOCK` grows only through refused-qty edge cases, left to input validation. `EVENT_REGISTRY` is keyed by code-set names and replacement drops the old bound method |
| `OrderService` and pipeline | No close protocol, but the default pipeline holds nothing; a resource-owning custom pipeline is a gap, not a finding |
| `importlib` modules | `sys.modules` retention is process-lifetime and bounded by the env mapping |
| Tasks, threads, timers, subprocesses, sockets, pools, listeners | None in `app/` by text search, so cancellation and shutdown checks have no subject beyond process death in job-04-F1 |
| `payments/`, `shipping/` | Text search only: they reference no orders stock or ledger resource |

Candidate confirmed with `git rev-parse HEAD`; `git status --porcelain` was empty.

## Cross-Reviewer Notes

- `service.py:25` discards the `reserve_stock` boolean, so checkout proceeds and records a sale without stock.
- `ledger.py:10` has no wait or retry: a concurrent writer gets `FileExistsError` instead of queueing.
- `notifications.py:13`: with `ORDER_NOTIFY_HANDLERS` unset, every checkout raises `KeyError` after the ledger line is written, and a retry reserves and records again.
- `api.py:23`: `Dispatcher._service` is never used. A second `register_defaults()` rebinds the global registry, so an earlier dispatcher routes to the newest service.
- `ledger.py:5-6`: both paths are cwd-relative, so processes with different cwds get separate ledgers and separate locks.
