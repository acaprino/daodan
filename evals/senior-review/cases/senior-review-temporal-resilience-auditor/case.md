# temporal-resilience-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:temporal-resilience-auditor`; content basis.
- Authored control family: EX098-114, EX142, EX164-166, SD143, RC002, RC005, RC034-036. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: EX098, EX100-103.

Defect: After first OSError the busy flag remains true; every later tick returns even if fetch would recover. Explain first failure, repeated tick and persistent stopped state; a running process is insufficient.

Correct / must_not_report: Finally clears the guard and truthful status permits recovery on the next serial tick. Process-lifetime polling does not require persistence, exponential backoff or a finite retry cap by default.

## loop_progress (scorer only)

Controls: EX102, EX104-106, EX142, EX166.

Requirement: Queue items may fail permanently. After a failed attempt the item must be removed to terminal failures so later items progress; this is the approved retry policy. No broker is involved.

Defect: Permanent failure remains at queue head and is retried on every tick, repeatedly recording failure while blocking later work.

Correct / must_not_report: Explicit terminal policy removes failed item and progresses; no universal backoff or retry limit is imposed.

## restart_guard (scorer only)

Controls: EX108-110.

Requirement: A required persisted job with running state can outlive its process. Lease expires at expires; new process must reclaim after expiry, and owner schedules reclaimed work. now is the supplied valid lease clock.

Defect: Persisted running flag blocks takeover forever even after lease expiry and process death.

Correct / must_not_report: Expiry permits required recovery and renews the lease; this job differs from process-lifetime polling.

## clock_budget (scorer only)

Controls: EX111-113.

Requirement: Timeout is elapsed duration and must remain bounded across wall-clock rewinds. mono reports monotonic elapsed seconds, wall may rewind; process sleep/resume counts toward this timer by supplied clock contract.

Defect: Wall rewind makes elapsed negative and extends a timeout that should be based on elapsed duration.

Correct / must_not_report: Supplied monotonic clock includes suspension; no unsupported claim that every monotonic clock has this property.

## signal_transition (scorer only)

Controls: EX099, EX107, EX114.

Requirement: Notify once on healthy-to-degraded transition and once on recovery; repeated same state must not spam. Notification returns synchronously and reliably.

Defect: Every failed tick repeats degraded notification and recovery is never announced despite required transition signaling.

Correct / must_not_report: One signal per state transition supplies meaningful observer state without a particular monitoring vendor.

## calendar_occurrence (scorer only)

Controls: EX112.

Requirement: A daily job uses local calendar date as logical occurrence identity. On DST fallback two ticks share that date and local hour but clock_hour includes different UTC offsets as (hour,offset) tuples. Exactly one execution per date is required.

Defect: Two fallback ticks (day, (2,+2)) and (day, (2,+1)) have distinct keys and execute twice for the same daily occurrence.

Correct / must_not_report: One durable day identity satisfies the explicit once-per-day rule independent of repeated clock hours.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
