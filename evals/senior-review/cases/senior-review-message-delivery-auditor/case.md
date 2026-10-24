# message-delivery-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:message-delivery-auditor`; content basis.
- Authored control family: SD112-118, SD120-121. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD114.

Defect: A crash or process exception after ack but before durable application loses the event permanently. Cite acknowledgement before durable work and broker contract.

Correct / must_not_report: Ack after durable process permits redelivery after commit, but process already deduplicates the stable event identity. No DLQ is required for this success/crash contract and ack is not a publish confirmation.

## publish_routing (scorer only)

Controls: SD112-113.

Requirement: A successful publish means routed to the required durable queue. transport returns {confirmed,routed}; confirmation alone can acknowledge an unroutable publish. Unroutable or unconfirmed publication must remain pending.

Defect: confirmed=True and routed=False marks an undelivered event done, losing required routing guarantee.

Correct / must_not_report: Both acceptance and routing checked; a queue declaration alone is not used as live evidence.

## ack_range (scorer only)

Controls: SD115.

Requirement: Delivery tags1 and2 are in flight on one channel. Work2 can finish before work1. ack(tag,multiple=True) confirms every tag through tag; incomplete work must not be acknowledged.

Defect: Completing tag2 acknowledges unfinished tag1; crash can lose its work.

Correct / must_not_report: Individual ack covers only completed work under channel ownership.

## ordering_identity (scorer only)

Controls: SD116-117, SD120-121.

Requirement: Entity events carry monotonic sequence; wall clocks across nodes can differ. Republish changes transport_id but retains logical_id. apply_event is serial and must neither regress sequence nor repeat logical events.

Defect: A newer sequence with smaller wall timestamp is dropped; republish bypasses identity dedup by changing transport_id. Require each mechanism separately.

Correct / must_not_report: Entity sequence and stable logical ID enforce actual ordering/dedup contract; global FIFO is unnecessary.

## terminal_routing (scorer only)

Controls: SD118.

Requirement: After3failed attempts a poison message must leave the work queue and remain available to operator redrive. message['attempts'] is the application attempt number that just failed, starting at1. republish preserves the supplied application field; its separate broker delivery counter resets to0. archive is durable retained terminal storage, so no DLQ product is required.

Defect: The handler explicitly resets the carried application attempt number to0 on each republish, so poison work loops indefinitely and never reaches terminal retention. This is distinct from the broker's reset of its own delivery counter.

Correct / must_not_report: The application attempt number advances for the next delivery, and failure of attempt3 reaches durable archive. A separate reset broker counter does not reset this carried application value. Durable archive after the declared cap is a valid alternative to DLQ; no loss is accepted or invented.

Fixture clarification before dispatch: original source/case bytes and unexecuted targets9d87c896a42d/3d19fb5893fd remain preserved. The old wording did not distinguish the two counters, so its intended correct countercase was ambiguous. Fresh attempts use this explicit distinction; no reviewer body or algorithm changed.

## partition_commit (scorer only)

Controls: SD120.

Requirement: Kafka-style commit(offset) acknowledges all prior offsets in the partition. Offsets10and11 process concurrently; only11has finished. Commit must not cover unfinished10.

Defect: Committing12 after only11 finishes covers unfinished10 and can lose it after restart.

Correct / must_not_report: Only contiguous completed prefix is committed; this is partition offset semantics, not per-message AMQP ack.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.

## Independent logical-delivery clarification

The earlier timestamp-guarded assignment did not independently establish repeated application for an identical replay. Preserve the old report's six supported mechanisms and unproved identity consequence. Ordering now has its own apply_ordered function; apply_once has serial delivery and an observable normally-returning application callback. Two deliveries with identical logical_id/payload and distinct transport_id cause two callbacks in the defect and one in the correct counterpart. No timestamp-restamping assumption is used. Source/oracle/old targets are archived before this change. No production reviewer body changed.
