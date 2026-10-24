# data-representation-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:data-representation-auditor`; content basis.
- Authored control family: SD084-089. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD087.

Defect: With limit=1, second page skips id=2 because filtering uses only created while ordering uses (created,id). The concrete row omission is the required finding.

Correct / must_not_report: The composite cursor includes the tie breaker. Do not require offset pagination, a different timestamp precision or claim concurrent mutation despite the unchanged dataset contract.

## money_and_time (scorer only)

Controls: SD084-085.

Requirement: Amounts are exact decimal currency values; persistence must preserve their decimal sum. This currency domain admits at most 1000 finite decimal strings, each from 0 through 1000000000 with at most two fractional digits; arithmetic uses a 28-significant-digit decimal context, unchanged during the operation. Instants supplied with UTC offset must retain that offset on round trip. No live clock involved.

Defect: 0.1+0.2 persists nonexact decimal value; removing tzinfo discards required instant offset. These are separate conversion mechanisms.

Correct / must_not_report: Decimal sum and offset-preserving serialization satisfy explicit semantics; no claim that every float or local date is wrong.

## stored_versions (scorer only)

Controls: SD086, SD088.

Requirement: Stored v1 rows use name, v2 rows use display; v1 must remain readable. display may legitimately be NULL and must not silently become an empty value. No other version exists.

Defect: v1 row lacks display and fails; v2 NULL is collapsed to an unintended empty string.

Correct / must_not_report: Version-aware selection preserves NULL and old rows; absence of a new schema technology is irrelevant.

## backfill_race (scorer only)

Controls: SD088-089.

Requirement: Backfill uses a captured row revision and computed value. It may restart and race with writers; applying a conversion may not overwrite newer edits. compare_and_set is atomic.

Defect: A delayed conversion unconditionally overwrites data edited after its snapshot; replay can repeat stale overwrite.

Correct / must_not_report: CAS preserves newer data and explicitly returns conflict for reconciliation; no unconditional overwrite is hidden as completion.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.

## Currency-domain clarification

The original unbounded correct packet admitted a valid Decimal context-rounding counterexample at 10^28+0.01. Its native report remains a supported unexpected fixture defect, not a false positive. This fresh domain states the intended bounded currency inputs and effective arithmetic context in both variants; at most 10^12 with two decimal places fits within 28 significant digits. The original binary-float 0.10+0.20 defect remains reachable. No implementation or reviewer body changed. Previous bytes and target copies are retained in the run's representation-decimal-domain archive.
