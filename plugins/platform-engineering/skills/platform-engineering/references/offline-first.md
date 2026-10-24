# Offline-First Design

For review, apply these mechanisms only to declared offline journeys and supported versions. Requirements decide authority, conflict behavior and budgets; library/pattern suggestions are not findings or installation permission.

## Required design questions

- **Design the data model for offline-first from the start** for PWA and mobile apps -- retrofitting is extremely difficult.
- Declare which facts may be accepted locally, which require server authority, and how reconnect reconciles them. Local presence does not grant business or authorization authority.
- For writes that may conflict, define and verify the required conflict-resolution behavior.
- Queue writes with unique identifiers and timestamps for reconciliation -- idempotency is non-negotiable.

## Conflict Resolution Strategies

| Strategy | Best for | Example |
|----------|---------|---------|
| **Last-Write-Wins (LWW)** | Simplest approach, infrequent conflicts | Trello -- human users are forgiving |
| **CRDTs** (Conflict-Free Replicated Data Types) | Collaborative editing, guaranteed convergence | Figma -- multiple users edit simultaneously |
| **Operational Transform (OT)** | Real-time collaborative text editing | Google Docs |
| **Field-level merge** | Mixed scenarios | Auto-resolve different field changes, prompt user for same-field conflicts |

## DO

- Use **optimistic UI updates** -- apply changes locally immediately, sync in background, reconcile later.
- For PWAs, select supported service-worker, cache, storage and background mechanisms for the promised journey; use an existing fallback when a target lacks an API.
- For mobile: use the Repository pattern with offline-first reads and write queues.

## DON'T

- Assume "eventually consistent" means "always correct" -- CRDTs solve merge conflicts, not authorization or validation.
- Skip testing offline scenarios.
- Store unbounded offline data without compaction/garbage collection.

## Official docs

- MDN Background Sync API: https://developer.mozilla.org/en-US/docs/Web/API/Background_Synchronization_API
- MDN IndexedDB: https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API
- Workbox (Google's service worker toolkit): https://developer.chrome.com/docs/workbox
- Yjs (CRDT library): https://github.com/yjs/yjs
- Automerge (CRDT library): https://automerge.org/
- ShareJS / sharedb (Operational Transform): https://github.com/share/sharedb
- Android WorkManager: https://developer.android.com/topic/libraries/architecture/workmanager
- iOS BGTaskScheduler: https://developer.apple.com/documentation/backgroundtasks/bgtaskscheduler
