---
dimension: transaction-integrity
reviewer: senior-review:transaction-integrity-auditor
status: delivered
job_id: job-05
candidate: 943bdc44c66dfd9782f6d38c82922a1f08783653
body_sha256: ee74a3ab8781f796c25898a5ca7f3e1d54f3cc0825123937a7ce13aeda8b4d3f
scope_id: orders-module
output_path: D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/blind-b/jobs/job-05.md
knowledge_usage: []
gaps:
  - Static inspection only, nothing executed. FileExistsError on lock contention is derived from O_CREAT|O_EXCL semantics.
  - Deployment model undeclared (threads, processes, working directory). F5, F7 and F8 state the condition they depend on.
  - No reader of ledger.log exists in app/; reader consequence is limited to the operator and to any consumer outside the read scope.
  - No durability requirement exists in the docstrings. No fsync and a possible torn row on a failed flush (ledger.py:17-18) were checked and not reported as findings, by the brief's rule against imposed requirements.
  - The notification handler is external (env-configured); its delivery and idempotency semantics are unknown.
  - body_sha256 is the dispatched value. sha256 of the role file is f6bf4037...0143, and a92b37a6...b296 without frontmatter. The dispatched hash was not reproduced; review content is unaffected.
member_results:
  - specialist_id: senior-review:transaction-integrity-auditor
    status: delivered
    coverage: complete
    finding_ids: [job-05-F1, job-05-F2, job-05-F3, job-05-F4, job-05-F5, job-05-F6, job-05-F7, job-05-F8, job-05-F9]
    gaps: as listed above
---

# Findings

Invariants bound, with rule evidence:

- I1: a sale row in the ledger implies a held reservation, and a held reservation implies a sale row (`service.py:24` describes one path; `inventory.py:18` defines the refusal).
- I2: one logical order yields one reservation and one sale row.
- I3: a reversal targets an identifiable recorded entry ("storno", `ledger.py:26`, `service.py:33`).

Stores and writers: `ledger.log` (only persistent store), writers `ledger.record` and `ledger.record_refund`, guard `ledger.lock`. `STOCK` (in memory), writers `reserve_stock` and `release_stock`, guard per-sku `threading.Lock`. No transaction spans the two stores.

## job-05-F1

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 25
- severity: High
- confidence: 95
- evidence: `inventory.reserve_stock(order["sku"], order["qty"])` discards the boolean. `inventory.py:21-22` returns `False` without changing stock, and checkout continues through `ledger.record` and `send_via`.
- consequence: an order for `qty` 11 of `demo-sku` (stock 10), or for an unknown sku, gets a persisted sale row, a receipt and a returned total with no stock behind it. The operator sees sold goods that were never reserved. I1 is broken.
- premise: `checkout` has no path that stops or branches on a `False` from `reserve_stock`.
- premise_provenance: independent
- trigger: `checkout` with `qty` above available stock, or a sku missing from `STOCK`.
- counterevidence_checked: no check elsewhere in `service.py`; `api.py:25-31` passes the payload straight through; `DefaultPipeline.step` (`service.py:13-15`) only sets a flag; no second stock check exists in `app/`.
- fix: refuse the order when `reserve_stock` returns `False`, before pricing, ledger or notification, with an outcome the caller can read.
- introduced_by_candidate: false
- evidence_class: derived

## job-05-F2

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 25
- severity: High
- confidence: 92
- evidence: the reservation at `:25` commits first. `:26-28` can raise with no `try` and no compensation. `release_stock` (`inventory.py:27`) has no caller in `app/` (text search).
- consequence: stock stays decremented with no ledger row and no order, for the life of the process. Each retry takes more. Sellable stock drains without sales; today F1 hides the symptom, and once F1 is fixed customers are refused for stock that exists. I1 is broken.
- premise: no code path calls `release_stock` when a step after `reserve_stock` raises.
- premise_provenance: independent
- trigger: any of: non-numeric `net` (`"100" * 0 / 100` raises TypeError at `pricing.py:14`); a replacement pipeline (`service.py:19-21`) that raises to reject an order, since validation runs after the reservation; `ledger.record` raising FileExistsError (F5, F6) or OSError.
- counterevidence_checked: no `except` or `finally` in `service.py` or `api.py`; no caller-side compensation in `app/`; `reserve_stock` itself is correct and does not leak on its own TypeError.
- fix: validate and price before reserving; wrap the reserve-to-ledger span so any exception releases the reservation, recording only after success.
- introduced_by_candidate: false
- evidence_class: derived

## job-05-F3

- file: `benchmarks/scope-resolution/app/packages/orders/service.py`
- line: 29
- severity: High
- confidence: 88
- evidence: `send_via` runs after the ledger row is durable at the file level (`:28`) and its exceptions propagate through `api.py:27`. `notifications.py:13` reads `os.environ["ORDER_NOTIFY_HANDLERS"]`, so with the variable unset every checkout raises KeyError after commit. `mapping[channel]` (`:14`), the import and the handler itself raise at the same point. Ledger and inventory hold no record of order identity to check against.
- consequence: the caller receives an exception and no total for an order already recorded and reserved. The KeyError looks the same as the pre-commit KeyError from `order["sku"]` (`service.py:25`), so failure does not tell the caller whether anything committed. Resending the event writes a second sale row and takes stock again. The operator sees the same id twice with the amount counted twice. I2 is broken.
- premise: a failure in `send_via` reaches the caller as a checkout failure, and nothing in `checkout` or `ledger.record` detects an already recorded order id.
- premise_provenance: independent
- trigger: `ORDER_NOTIFY_HANDLERS` unset or lacking the channel, or a failing handler; duplication then needs the caller to resend. No retrier exists in the read scope, so the false failure is certain and the duplicate is conditional on the caller.
- counterevidence_checked: no `try` around `send_via`; no idempotency key, lookup or read of `ledger.log` anywhere in `app/`; `test_app_structures.py` pins the `os.environ[` text, not this failure behaviour.
- fix: treat notification as post-commit: catch and record its failure (a retryable pending entry) and still return the total. Add one dedup check on order id under the ledger lock, shared by retries.
- introduced_by_candidate: false
- evidence_class: derived

## job-05-F4

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 25
- severity: Medium
- confidence: 62
- evidence: `record_refund` appends `{id}\tREFUND\n` unconditionally. `service.py:32-34` adds no check. The row carries no amount, while `payments/refunds.py:16` treats refunds as "parziale o totale", so two rows cannot be told apart as a replay or as two partial refunds.
- consequence: a replayed `refund_request`, or one for an id never sold, persists a reversal with nothing to reverse. An operator reconciling the ledger cannot compute what was refunded or detect the duplicate. I3 is broken.
- premise: nothing checks, before appending a REFUND row, that a sale row exists for the id or that it is not already reversed.
- premise_provenance: independent
- trigger: `refund_request` delivered twice for one id, or with an unknown id.
- counterevidence_checked: no read of `ledger.log` in `app/`; `payments.refunds.issue_refund` is not called by orders. The uniqueness rule is inferred from "storno" only, which limits confidence: no document states it.
- fix: under the ledger lock, look up the sale row and prior reversals, and store a refund identity and amount in the row, so a replay is detected and a partial refund stays representable.
- introduced_by_candidate: false
- evidence_class: derived

## job-05-F5

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 10
- severity: Medium
- confidence: 88
- evidence: `_acquire_lock` is a single `os.open` with `O_CREAT | O_EXCL`, without wait or retry, called at `:15` and `:27`; nothing catches the error.
- consequence: mutual exclusion holds, but the loser of any overlap fails instead of queuing. W1 acquires at `:15`; W2 has already reserved stock (`service.py:25`), reaches `:15`, gets FileExistsError. W2's order has no row, its stock is leaked (F2), and the caller sees a raw file error. A refund that collides the same way is not recorded.
- premise: a writer that finds `ledger.lock` present fails at once, and no caller retries it.
- premise_provenance: independent
- trigger: two overlapping ledger writers, threads or processes with the same working directory. Requires concurrent use, which the lockfile itself anticipates.
- counterevidence_checked: no retry loop in `ledger.py`, `service.py` or `api.py`; no outer lock serializes checkout (the sku lock is released at `inventory.py:24` before the ledger step).
- fix: a blocking OS lock on the ledger file (`fcntl`/`msvcrt`, stdlib) in one shared helper for both writers, so a contending writer waits.
- introduced_by_candidate: false
- evidence_class: derived

## job-05-F6

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 15
- severity: Medium
- confidence: 85
- evidence: the lock is a durable file holding no owner or age, removed only by `finally` at `:20-21` and `:32-33`. A process death between acquire and `finally` leaves it on disk.
- consequence: after restart every `record` and `record_refund` raises FileExistsError until an operator deletes `ledger.lock`, which nothing tells them to do. No sale or refund is recorded in that time, and each failed checkout also leaks stock (F2).
- premise: no code removes or expires a `ledger.lock` left by a dead process.
- premise_provenance: independent
- trigger: kill, out-of-memory or power loss while a writer is between `:15` and `:21`. Ordinary exceptions do run `finally`, so only process death triggers it.
- counterevidence_checked: no startup cleanup, staleness check or pid in the file; `unlink(missing_ok=True)` only runs on the holder's own path.
- fix: the OS lock of F5, which the kernel releases at process death, removes this state altogether.
- introduced_by_candidate: false
- evidence_class: derived

## job-05-F7

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 5
- severity: Medium
- confidence: 75
- evidence: `Path("ledger.log")` and `Path("ledger.lock")` resolve against the working directory at each call, with no configured root.
- consequence: a service started from another directory silently opens a new empty ledger, without error. The accounting history forks, the operator finds partial data at the expected path, and locks in separate directories do not exclude each other. A `chdir` while a write holds the lock makes `:21` unlink the wrong path, leaving a stale lock (F6).
- premise: the authoritative ledger location depends on the working directory of the process.
- premise_provenance: independent
- trigger: two invocations or a restart with a different working directory, or `os.chdir` in-process (handlers are external code, `notifications.py:15`).
- counterevidence_checked: no assignment of `LEDGER_PATH` or `LOCK_PATH` elsewhere in `app/`; no `chdir` in `app/`; no environment override. The deployment working directory is undeclared.
- fix: resolve one absolute ledger root once at startup, from configuration, and derive both paths from it.
- introduced_by_candidate: false
- evidence_class: derived

## job-05-F8

- file: `benchmarks/scope-resolution/app/packages/orders/inventory.py`
- line: 7
- severity: Medium
- confidence: 55
- evidence: `STOCK` and its `threading.Lock`s live in one process, while the ledger persists and uses a cross-process lockfile. Ledger rows hold neither sku nor qty (`ledger.py:18`), so stock cannot be rebuilt from them.
- consequence: after a restart `demo-sku` is back at 10 while the ledger keeps all sales, so `reserve_stock` accepts quantity already sold. Two processes sharing a ledger each hold their own 10 units, and the thread locks do not guard the other process. The `False` promised at `inventory.py:18` stops being reliable.
- premise: stock has no store or rebuild step outliving the process or shared across processes.
- premise_provenance: independent
- trigger: process restart after any sale, or a second process with the same working directory.
- counterevidence_checked: no persistence or startup rebuild in `app/`. Against the finding: the app is a demo (`pyproject.toml:4`), `STOCK` looks like seed data, no document promises durable stock or multi-process use. This is why confidence is low.
- fix: if multi-run stock matters, keep stock in the same store and guard as the ledger, or record sku and qty per row and rebuild at startup. Otherwise state the single-process, per-run assumption in the module docstring.
- introduced_by_candidate: false
- evidence_class: derived

## job-05-F9

- file: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- line: 18
- severity: Low
- confidence: 85
- evidence: `order.get('id', '?')` at `:18` and `:30` persists a shared placeholder as the only key of the row, while `sku` and `qty` are required (`service.py:25`).
- consequence: distinct orders without an id collapse under `?`, so their sale rows cannot be attributed and `?\tREFUND` cannot be tied to any of them. The operator finds money rows with no owner.
- premise: an order without `id` reaches `ledger.record` and is written with `?` rather than refused.
- premise_provenance: independent
- trigger: a `checkout` or `refund_request` payload without `id`.
- counterevidence_checked: `api.py:4` passes payloads unchanged; `DefaultPipeline.step` checks nothing; no earlier `id` access in `service.py`.
- fix: require `order["id"]` at the start of `checkout` and `refund_request`, before any stock or ledger effect.
- introduced_by_candidate: false
- evidence_class: derived

# Cross-Reviewer Notes

- `pricing.py:19` subtracts `compute_discount` twice against the `:18` contract, so the ledger persists the wrong total (logic-integrity).
- `ledger.py:30` writes no VAT portion or amount though `ledger.py:26` promises it (logic-integrity).
- `ledger.py:18` and `:30` write `id` unescaped: a tab or newline in it forges rows, including `REFUND` rows (input-validation).
- `inventory.py:21-23` with negative `qty` raises stock instead of refusing (input-validation).
- `service.py:26-27` prices before the pipeline runs and discards its return value, so a pipeline can only reject by raising (logic-integrity).

# Examined scope and completed checks

Examined: all 9 scoped files. `big_module.py`: one body read closely, census used for the 105 same-body functions, text search found no file I/O, `try` or `except`, so it has no writers and is not a store. `reporting.py` reads no store, and `__init__.py` is empty. `payments/*`, `shipping/*`, `pyproject.toml` and `test_app_structures.py` read as context; none touches the ledger or stock. Work tree confirmed clean at the candidate.

| Check | Result |
|---|---|
| Writer inventory | Ledger: 2 writers, append only, same guard. `STOCK`: 2 writers, same per-sku lock. `release_stock` has no caller. |
| Read-modify-write on stock | No finding within one process: `:19-24` and `:29-31` share the sku lock and `_lock_for` is atomic under `_GUARD`. Beyond one process: F8. |
| Lock ordering and deadlock | No nested locks: the sku lock is released before the ledger lock, so no deadlock path. |
| Lock release on in-process exception | Correct, `finally` at `ledger.py:19-21` and `:31-33`. The acquire sits outside `try`, so a failed acquire does not remove another writer's lock. |
| Atomicity across stores | F1, F2, F3. |
| Competing-writer interleavings | F5, F7, F8. |
| Interruption and recovery | F2, F3, F6. |
| Replay and dedup | F3, F4, F9. |
| Retry | No retrier in scope; effect of a caller resend covered in F2 and F3. |
| Constraints, ORM, isolation, migrations, triggers, transaction width, offline or replicated merge | Not applicable: no database, ORM, schema, bulk work or replication in scope. |
