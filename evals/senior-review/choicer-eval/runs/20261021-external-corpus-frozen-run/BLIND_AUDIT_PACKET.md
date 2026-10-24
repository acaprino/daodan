# Blind code-only audit packet

Do not read `blind_audit_key_DO_NOT_READ_DURING_AUDIT.json`, `cases.json` or external issue text while filling this packet.

## Rubric

### security-auditor
- Applies: Controls access to accounts or private data, validates untrusted input, or handles credentials, secrets or sensitive output.
- Excludes: Pure internal computation, non-security hashing/IDs, or generic error handling without a trust boundary.

### data-integrity-auditor
- Applies: Reads, writes, invalidates or reconciles persisted records or cached copies of external state.
- Excludes: Temporary local dictionaries, sets or counters used only inside a computation.

### temporal-resilience-auditor
- Applies: Governs retries, timeouts, timers, polling, backoff, recovery after failure or visibility of background errors over time.
- Excludes: Merely using async syntax or converting a timestamp/date value.

### resource-lifecycle-auditor
- Applies: Acquires, retains or releases a lock, file, connection, subscription, worker or bounded resource slot across normal, error or cancel paths.
- Excludes: Ordinary value allocation, string connection URLs or plain async calls without owned resource lifecycle.

### ui-race-auditor
- Applies: Coordinates UI events or asynchronous results with rendered state, visibility, focus, scroll or layout.
- Excludes: Backend logic, static text or styling without asynchronous UI state coordination.

### distributed-flow-auditor
- Applies: Publishes, receives, acknowledges or routes messages across a service/process boundary or defines producer-consumer transport contracts.
- Excludes: In-process function calls or local data transformations.

### logic-integrity-auditor
- Applies: Enforces a domain rule, allowed state transition, ordering requirement, idempotency condition, fallback semantics or ownership invariant.
- Excludes: Generic formatting, logging or numerical/date conversion without a domain invariant.

### cleanup-auditor
- Applies: Shows unused or obsolete code, dependencies or assets, or documentation/comments that disagree with the implementation.
- Excludes: Normal code or comments with no visible obsolescence or contradiction in the supplied input.

## Items

- Jupiter calibration items: 8 (`J01`..`J08`)
- External development items: 27 (`D01`..`D27`)
- Fill judgments in `blind_audit_packet.json`.
