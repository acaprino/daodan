# data-retention-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:data-retention-auditor`; content basis.
- Authored control family: SD090-092. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD090, SD092.

Defect: After customer 1 is erased, restoring a backup containing 1 republishes deleted data. The durable deletion set is available but ignored.

Correct / must_not_report: The corrected restore filters tombstones before publication. The explicitly permitted 30-day encrypted backup retention is not a policy violation and no legal requirement may be invented.

## copy_completion (scorer only)

Controls: SD090-091.

Requirement: Primary and search copies must both be deleted unless legal_hold is true. Provider deletion may fail; on failure caller must receive failure and retain work for retry.

Defect: Deletes data despite hold and reports complete when search deletion fails, hiding an undeleted required copy.

Correct / must_not_report: Explicit hold and propagated provider failure preserve policy/retry semantics. Do not call approved hold a privacy defect.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.

## Explicit caller path for corrected-body primary qualification

The original correct source remains preserved as a precision failure: local helper ownership/durability was inferred without proof. The fresh primary variants now show the same complete caller-owned pending path and explicit process-lifetime/provider contracts. In defect, swallowed search failure returns complete and causes the caller to remove unfinished work; missing hold still deletes exempt copies. In correct, OSError leaves pending work and retry is idempotent. Restore remains unchanged. Original mixed target and both ownership probes are also rerun byte-identically under the corrected generic mandate; no old result is relabeled.
