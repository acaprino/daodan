# service-resilience-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:service-resilience-auditor`; content basis.
- Authored control family: SD094-095, SD098-104, SD123, RC010. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD100-101.

Defect: A persistent outage produces 3x3=9 transport attempts, exceeding the explicit total budget of 3. State the count as code-derived, not measured latency or resource cost.

Correct / must_not_report: One retry layer makes exactly three attempts. Fixed immediate retry is allowed by this explicit contract; absence of jitter, breaker or backoff alone is not a defect.

## remaining_deadline (scorer only)

Controls: SD098-099.

Requirement: Two sequential remote calls must finish within the caller absolute deadline. call(timeout) spends its entire timeout before returning if the service is slow; clock reports elapsed time and each call respects supplied timeout.

Defect: Second sequential call reuses the original full allowance after the first consumed it; total work exceeds caller budget.

Correct / must_not_report: Remaining budget recomputed and exhaustion prevents starting more work; no nominal timeout comparison substitutes for the trace.

## breaker_recovery (scorer only)

Controls: SD102-103, SD123.

Requirement: An open per-destination breaker must allow one probe after cooldown; isolated destination state is supplied and the transport has its own cancellation/deadline guarantee. No dead connection is permitted to monopolize other destinations.

Defect: Once open, the breaker can never probe after recovery deadline, permanently disabling a healthy destination.

Correct / must_not_report: Per-destination cooldown probe resumes service; supplied transport limits are counterevidence to hypothetical zombie starvation.

## honest_outcome (scorer only)

Controls: SD094-095, SD104.

Requirement: Remote timeout is an unknown effect outcome; request ID allows later reconciliation. Returning confirmed success without a receipt is prohibited.

Defect: Timeout path reports completion without a confirmed effect and loses correlation needed for reconciliation.

Correct / must_not_report: Pending plus stable request ID honestly preserves unresolved outcome; it is not necessarily a failed effect.

## destination_bulkhead (scorer only)

Controls: SD103.

Requirement: Failed destination A must not consume destination B reserved worker capacity. acquire chooses a supplied finite pool; work may block until its enforced long deadline.

Defect: A calls exhaust shared pool, so independent B cannot acquire its promised reserved capacity.

Correct / must_not_report: Per-destination supplied pool enforces required isolation; no universal bulkhead requirement extends outside this contract.

## half_open_progress (scorer only)

Controls: SD098, SD123.

Requirement: A half-open connection may make receive wait forever. receive(deadline,cancel_on_timeout=True) guarantees underlying work stops at deadline; caller must not leave work alive after giving up.

Defect: Unbounded receive on a half-open channel can block required progress indefinitely despite a caller deadline being available.

Correct / must_not_report: Transport-enforced deadline/cancellation supplies progress without a separate heartbeat mechanism.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
