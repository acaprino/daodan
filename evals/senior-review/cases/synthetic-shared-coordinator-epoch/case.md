# Case: synthetic-shared-coordinator-epoch (code-auditor, logic-integrity)

Synthetic. Setup is deterministic: start from an empty scratch repository, make one empty base commit, materialize exactly the two files below verbatim in a second commit, and treat that second commit as `review_rev`. The review scope given to the reviewer is literally `flow/catalog.ts flow/wiring.ts` (the diff of base to `review_rev`). The reviewer receives the materialized files and diff only, never this case file.

## Buggy code

```ts
// flow/catalog.ts
type Coordinator = { epoch: number; credential?: string; snapshot?: string; snapshotEpoch: number }
const COORDINATORS = Symbol.for('eval.flow.catalog.coordinators')
const realm = globalThis as typeof globalThis & { [COORDINATORS]?: Map<string, Coordinator> }
const coordinators = realm[COORDINATORS] ??= new Map<string, Coordinator>()

export function createCatalog(origin: string, readKey: () => Promise<string | undefined>) {
  let coordinator = coordinators.get(origin)
  if (!coordinator) { coordinator = { epoch: 0, snapshotEpoch: -1 }; coordinators.set(origin, coordinator) }
  const shared = coordinator
  let verified: string | undefined
  let refreshing: Promise<void> | undefined

  const key = async () => {
    const id = await readKey()
    if (id !== shared.credential) { shared.credential = id; ++shared.epoch }
    verified = id
    return id
  }
  const refresh = (): Promise<void> => {
    if (refreshing) return refreshing
    const pending = (async () => {
      const id = await key(); if (!id) return
      shared.snapshot = `limits-for:${id}`; shared.snapshotEpoch = shared.epoch
    })()
    refreshing = pending
    void pending.finally(() => { if (refreshing === pending) refreshing = undefined })
    return pending
  }
  return {
    refresh,
    invalidateCredentials() { ++shared.epoch; shared.credential = undefined; verified = undefined; refreshing = undefined },
    limits(): string | undefined {
      if (!verified || shared.credential !== verified) return undefined
      return shared.snapshotEpoch === shared.epoch ? shared.snapshot : undefined
    },
    start() { void refresh(); setInterval(() => { void refresh() }, 600000) },
  }
}
```

```ts
// flow/wiring.ts
import { createCatalog } from './catalog'
// Test-controlled credential source. The scorer may reassign currentKey and may
// wrap readKeyFromDisk with deferred promises to control resolution order in a
// reproduction; the reviewer target is the code exactly as written here.
let currentKey: string | undefined = 'k1'
export const readKeyFromDisk = async (): Promise<string | undefined> => currentKey
export const setCurrentKey = (value: string | undefined) => { currentKey = value }
// Two live locations in one process share one coordinator through the realm registry.
export const locationA = createCatalog('https://gateway.example', readKeyFromDisk)
export const locationB = createCatalog('https://gateway.example', readKeyFromDisk)
locationA.start()
locationB.start()
```

## Ground truth (2 bugs)

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | Rotation branch only: B has verified credential `k1`. A observes the rotation to `k2` first (its `key()` sets `shared.credential = k2` and increments `shared.epoch`). B still holds `verified = k1`, so `locationB.limits()` returns `undefined`, and no refresh by A can repair B, because A's snapshot belongs to `k2` while B's `verified` is `k1`. B recovers only when B itself successfully observes the current key (its own refresh, at the latest its 600000 ms interval). Full mechanism: per-handle `verified` against shared `credential`, with `snapshotEpoch` against shared `epoch` in `limits()`. | code-auditor (per-instance state divergence), logic-integrity (cross-instance invariant) |
| 2 | Refresh concurrency: `refreshing` is per-handle, so two handles can refresh concurrently against one coordinator with no invalidation involved. On one handle, a refresh in flight followed by `invalidateCredentials()` clears `refreshing` without cancelling that refresh, so a second refresh starts. In both shapes, when the overlapping `key()` observations return different credential ids and resolve out of order, the last resolver wins the shared `credential`, `epoch` and snapshot, regardless of which observation started first or is fresher. | code-auditor (shared state race), temporal-resilience (repeated failure cost) |

## must_not_report

| Claim | Status on these facts | Why |
|-------|----------------------|-----|
| Snapshot data from a previous credential can be served to a new credential in steady state, with no refresh in flight | False at this revision | In steady state `limits()` compares `shared.snapshotEpoch === shared.epoch` and `shared.credential !== verified` returns `undefined`, so cross-credential serving is guarded. Under the overlapping refreshes of bug 2 a stale snapshot can instead be served transiently against a newer credential; that serving is a manifestation of bug 2 and scores there, never as this anti-finding. |
| After an invalidation with the same credential, B can recover only through its own key observation | False at this revision | A refresh by A with the same credential restores `shared.credential` and `snapshotEpoch`, and `limits()` on B serves again without B observing anything. The recovery source is the error in this claim, not the temporary unavailability itself, which is real until some handle refreshes: after an invalidation with no further refresh, B stays without limits until the next 600000 ms interval tick. |

## Scoring notes

- Bug 1: full credit requires the rotation precondition, the per-handle `verified` against shared `credential` mechanism, and recovery only through B's own successful key observation. A generic "cache may be stale" is a partial. Naming `verifiedEpoch` earns no credit: this snippet has no such variable, and importing one from similar production code is a misread of the target.
- Bug 2: full credit requires either trigger (two handles refreshing concurrently, or one handle with refresh, invalidate, refresh) plus two `key()` observations returning different ids resolving out of order. A single handle refreshing alone, with no second overlapping observation, cannot produce it.
- A reviewer that reports a `must_not_report` claim as a finding has produced a false positive even if it also found both bugs. Record which lens, if any, killed such a finding in the verification panel.
