# remote-effect-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:remote-effect-auditor`; content basis.
- Authored control family: SD096-097, SD105-111, SD119, SD122. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## Fixture storage clarification

For saga_compensation, saga is an abstract durable record: each assignment persists before the next statement, including when a later refund call times out. For prepared_recovery, decision_log is the durable decision map and participant state assignments persist. For outbox_durability, outbox is an abstract durable map: pop persists removal, and a successful send return is a durable external receipt. These storage guarantees apply only to these named scenarios, not to ordinary Python dictionaries generally.

Clarification preserves the original receipt/decision/outbox durability requirements. Earlier prepared targets are retained as unexecuted attempt 1; attempt 2 binds these explicit guarantees.

## primary (scorer only)

Controls: SD105-106, SD111.

Defect: First charge commits remotely but timeout leaves results empty; retry uses a new next_attempt key and commits another charge. This resolves the historical payment oracle ambiguity by explicitly allowing retry past the local guard.

Correct / must_not_report: The stable order ID binds both calls to the provider idempotency guarantee for the supplied horizon. Do not require a local distributed transaction or claim the local result guard alone prevented the original duplicate.

## lease_fence (scorer only)

Controls: SD096-097.

Requirement: A worker may pause beyond lease expiry while a replacement obtains a larger epoch. The remote sink rejects epochs lower than its recorded current epoch. Lease check at start alone cannot revoke already-running work.

Defect: Paused old leader sends an unfenced effect after replacement; the receiver has no epoch to reject stale authority.

Correct / must_not_report: Sink-enforced monotonic fence blocks old work; no consensus implementation is inferred beyond supplied ownership guarantees.

## saga_compensation (scorer only)

Controls: SD109-110.

Requirement: After a failed saga step, refund is required exactly once. refund(key) is provider-idempotent, but may time out after commit. Saga stays recovery-pending until refund receipt is durable; retry uses the same saga ID.

Defect: Sets compensated before receipt; timeout leaves no recovery. Changing attempt_id on retry also permits repeated refund.

Correct / must_not_report: Stable saga key and post-receipt state preserve retriable recovery under provider guarantee.

## prepared_recovery (scorer only)

Controls: SD122.

Requirement: Coordinator decision is durably recorded as commit/abort. Recovered participants in prepared state must consult it and resolve; no autonomous heuristic abort is permitted.

Defect: Recovered participant ignores available durable decision and remains prepared indefinitely.

Correct / must_not_report: Durable decision resolves participant without inventing a saga or changing transaction semantics.

## outbox_durability (scorer only)

Controls: SD107.

Requirement: Outbox events remain pending until external durable receipt. send may raise before or after the remote effect; stable key provides provider deduplication. Local removal is durable.

Defect: Outbox entry is removed before successful delivery; transport failure erases the only retry source.

Correct / must_not_report: Entry remains until durable receipt and stable provider key prevents repeat effects after response loss.

## late_payment (scorer only)

Controls: SD108, SD119.

Requirement: Payment state paid is monotonic. A delayed pending event or redriven old event cannot regress paid. Events have stable operation identity and applied version; states are pending/paid only.

Defect: Delayed pending event regresses paid and can reopen remote workflow despite completed effect.

Correct / must_not_report: Monotonic terminal state plus version guard absorbs authentic delayed/redriven events; no forgery is claimed.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.

## Admitted compensation retry correction and old setup adjudication

Root independently found that old private oracle said attempt_id changes on retry while old admitted source only read saga['attempt_id']; no caller or declared relation established that change. Preserve all original6/7 numeric comparisons and six supported causal findings, but classify the seventh row as setup-limited, not a demonstrated reviewer omission. The generic body correction remains historical method clarification; it does not prove the original miss. Fresh variants admit the same actual retry_compensation caller: one unchanged saga id, attempt-A then attempt-B after a provider commit with lost response. RefundProvider records one effect per distinct key and returns the same receipt for repeated keys. Defect can therefore produce two provider refund entries independently of its early terminal/receipt defect; correct calls the same saga id twice and records one entry, receipt before terminal. No target code was executed. The reviewer body remains unchanged.
