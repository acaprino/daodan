---
dimension: local-concurrency
reviewer: senior-review:local-concurrency-auditor
status: delivered
job_id: job-03
candidate: 943bdc44c66dfd9782f6d38c82922a1f08783653
body_sha256: a5bca62579145b80e82f421d504579c9655205f7101aae497856a533536e0ab4
scope_id: orders-module
output_path: D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/blind-b/jobs/job-03.md
knowledge_usage: []
gaps:
  - No caller in scope starts threads or processes. The concurrent-caller model is taken from the package's own locks, see F1 premise note.
  - Multi-process stock left open. STOCK and the per-sku locks are process-local while the ledger lockfile is cross-process; no requirement states a multi-worker deployment, so "each worker owns its own STOCK" is neither a defect nor refuted.
  - Alternate pipelines left open. service.py:21 shares one pipeline instance across concurrent checkouts; no alternate class or thread-safety contract exists in scope.
  - Notification handlers come from ORDER_NOTIFY_HANDLERS and are outside the sources; their thread safety is unknown. They run with no lock held.
  - O_EXCL atomicity assumed for a local filesystem; no deployment information exists.
  - Static inspection only, no runtime exercise; this assignment has no reproduction grant.
member_results:
  - specialist_id: senior-review:local-concurrency-auditor
    status: delivered
    coverage: complete
    finding_ids: [job-03-F1, job-03-F2]
    gaps: as listed above
---

# Local concurrency: orders package

## Findings

### job-03-F1: lockfile contention fails the writer instead of serializing it, after stock is already taken

- `file`: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- `line`: 10 (reached from `ledger.py:15`, `ledger.py:27`, `service.py:28`, `service.py:34`)
- `severity`: High
- `confidence`: 80
- `evidence`: `_acquire_lock` is one non-blocking `os.open(..., O_CREAT | O_EXCL | O_WRONLY)` with no wait or retry. `except` and `FileExistsError` appear nowhere in `app/packages`. `service.py:25` has already decremented stock when `service.py:28` runs, and `release_stock` has no caller.
- Competing paths: `Dispatcher.handle("checkout")` against another `checkout` or `refund_request`, on any sku, because the lockfile is global to the ledger.
- Ordering:
  - T0: A passes `reserve_stock`, enters `record`, creates `ledger.lock`.
  - T1: B passes `reserve_stock`; `STOCK` drops. The per-sku lock was released at `inventory.py:24` and does not cover the ledger.
  - T2: B reaches `ledger.py:15` before A reaches `ledger.py:21`; `os.open` raises `FileExistsError` naming `ledger.lock`.
  - Outcome: A succeeds. B's exception leaves `Dispatcher.handle`, with no ledger line, no notification and B's units still deducted. A caller that retries reserves a second time.
- Existing guard and why it fails: `O_EXCL` provides mutual exclusion, which holds, but gives contenders no way to wait, so the lock turns normal contention into an error.
- Observable consequence: during any overlap of ledger writes, a checkout or refund caller gets a `FileExistsError` about `ledger.lock`. The operator later finds stock lower than the ledger lines account for; a failed refund is simply not recorded.
- Fix direction: make acquisition wait. Prefer a kernel-held blocking lock on a permanent file (`fcntl.flock` or `msvcrt.locking`, both stdlib), which also resolves F2. The alternative is retrying `O_EXCL` with backoff up to a deadline, then raising a named timeout error. Compensation in `checkout` for a failed ledger step belongs with this fix (see Cross-Reviewer Notes).
- `premise`: no code path waits for, retries or handles a writer that finds `ledger.lock` already present.
- `premise_provenance`: independent
- Premise note: the need for concurrent callers is inferred, not shown by a caller. `inventory.py:1` and `inventory.py:8-9` take per-sku thread locks and `ledger.py:1` declares a lockfile, and neither has a purpose without overlapping callers. `api.py:34-39` shares one service process-wide.
- `trigger`: two ledger writes overlap, so that one reaches `ledger.py:15` or `ledger.py:27` while the other is between lock creation and `LOCK_PATH.unlink`.
- `counterevidence_checked`: searched `app/packages` for `except`, `FileExistsError` and callers of `release_stock`: none. No docstring declares fail-fast behaviour; `api.py:3` documents only `KeyError`. `test_app_structures.py` asserts nothing about the ledger's runtime behaviour.
- `introduced_by_candidate`: false
- `evidence_class`: derived

### job-03-F2: a holder that dies leaves `ledger.lock` behind and every later ledger write fails

- `file`: `benchmarks/scope-resolution/app/packages/orders/ledger.py`
- `line`: 15 (same shape at `ledger.py:27`; release only at `ledger.py:19-21` and `ledger.py:31-33`)
- `severity`: High
- `confidence`: 85
- `evidence`: the only removal of the lock is `LOCK_PATH.unlink(missing_ok=True)` in the holder's own `finally`. The lockfile carries no PID, host or timestamp (`_acquire_lock` writes nothing), and no stale-lock detection exists. `os.close(fd)` at `ledger.py:20` and `ledger.py:32` also precedes the unlink, so a failing close skips it.
- Competing paths: the dead holder of `record` or `record_refund` against every later `record` and `record_refund` in the same working directory, including after a restart.
- Ordering:
  - T0: A runs `ledger.py:15`; `ledger.lock` exists on disk.
  - T1: the process is ended before `ledger.py:21` without running `finally`.
  - T2: the process restarts. In-memory state resets, but the file persists.
  - T3: every checkout decrements `STOCK`, then raises `FileExistsError` at `ledger.py:15`; every refund raises at `ledger.py:27`.
  - Outcome: the ledger accepts nothing until someone deletes the file by hand, and each failed checkout drains stock in the meantime.
- Existing guard and why it fails: `try/finally` covers exceptions in the section, including `KeyboardInterrupt`, but not process death. Python's default SIGTERM disposition terminates without running `finally`, and nothing in scope installs a handler.
- Observable consequence: after a kill landing inside one ledger write, all checkouts and refunds fail with an error indistinguishable from F1's contention, and restarting does not help. The operator must recognize the file and delete it.
- Fix direction: use a kernel-held lock on a permanent file that is never unlinked, so the OS releases it when the holder dies. Avoid PID-based reclaim unless it takes over atomically and confirms ownership before release: `unlink(missing_ok=True)` has no owner check, so a holder still alive after a manual cleanup would delete its successor's lock.
- `premise`: nothing other than the holder's own `finally` ever removes `ledger.lock`, and that `finally` does not run when the process is killed.
- `premise_provenance`: independent
- `trigger`: SIGTERM with the default disposition (deploy or service stop), SIGKILL or OOM kill, Windows `TerminateProcess`, `os._exit` or power loss, while a process is between lock creation and unlink. The window is the duration of one append, and its effect lasts until manual removal.
- `counterevidence_checked`: searched `app/packages` for other uses of `LOCK_PATH`, startup cleanup and signal handling: only `ledger.py:10`, `ledger.py:21`, `ledger.py:33`. `fd` is unused for locking; nothing calls `flock` or `locking`.
- `introduced_by_candidate`: false
- `evidence_class`: derived

## Examined scope and completed checks

All 9 files were read; `big_module.py` by one body (`:10-28`), the census and a text search. Read for context: `payments/*`, `shipping/rates.py`, `pyproject.toml`, `test_app_structures.py`, `AGENTS.md`.

- Stock atomicity, no finding. `_lock_for` publishes one stable lock per sku under `_GUARD` and never removes it. Both writers (`inventory.py:23`, `inventory.py:30`) hold that lock, so the check-then-act at `inventory.py:20-23` is atomic in-process. Different locks on one dict are sound because the invariant is per key and individual dict operations are thread-safe in CPython.
- Failure inside the sku lock, no finding. A bad `qty` raises at `inventory.py:21` before any write and `with` releases the lock.
- Deadlock, no cycle. `_GUARD` is released before the sku lock is taken; `checkout` releases each lock before the next step. `send_via` runs with no lock held, so a reentrant handler cannot self-deadlock.
- Ledger mutual exclusion, holds while the holder lives. `record` and `record_refund` share one lock path across threads and processes. The stream closes and flushes before `finally` releases, so the next holder sees complete lines. No ledger reader exists in scope.
- Working-directory lock identity, no finding here. Lock and ledger resolve against the same cwd, which breaks only with `os.chdir` during the section; no `os.chdir` exists in scope.
- `EVENT_REGISTRY`, no finding. It is an intentionally shared latest value, pinned by `test_app_structures.py:30-35`. Concurrent `register_defaults` calls can mix two services, but those services are behaviourally identical.
- Shared objects, no finding. `DefaultPipeline` is stateless. `compute_total` reads `order` several times, but no concurrent writer of `net` or `loyalty_percent` exists in scope.
- `notifications.py`, no finding. There is no writer of `os.environ` in scope, and `importlib.import_module` takes its own import locks.
- `pricing.py`, `reporting.py`, `big_module.py`, no finding. They hold constants and pure functions only.

## Cross-Reviewer Notes

- `service.py:25` discards the `reserve_stock` result, so overselling occurs even sequentially; the lock works but its outcome is ignored (local correctness).
- `service.py:25-29` has no compensation when any later step fails, and `release_stock` has no caller (transaction integrity).
- `api.py:23` stores `_service`, but `api.py:26` never uses it; a `Dispatcher` built on a custom service runs whichever handler was registered last (logic integrity).
- `ledger.py:5-6` makes the ledger's location depend on the process working directory, so processes in different directories keep separate ledgers (resource lifecycle or configuration).
