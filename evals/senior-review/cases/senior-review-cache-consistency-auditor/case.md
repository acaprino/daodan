# cache-consistency-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:cache-consistency-auditor`; content basis.
- Authored control family: SD079-083. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD080.

Defect: read(1), admin_rename(1,"new"), read(1) yields old after the successful rename because the alternate writer does not invalidate.

Correct / must_not_report: All writers traverse invalidation; process-local sequential contract needs no distributed cache, TTL, event bus or lock. Do not infer unsupported concurrent stale refill.

## tenant_key (scorer only)

Controls: SD079.

Requirement: Two tenants may share user ID. Profiles differ by tenant; get_profile reads authoritative data. Cache is shared across tenants.

Defect: Second tenant reuses first tenant cached value for same user ID; key omits a computation dimension.

Correct / must_not_report: Tuple key binds both dimensions; authorization consequence may be routed without duplicating the key defect.

## stale_fill (scorer only)

Controls: SD081-083.

Requirement: A fill reads version V, pauses, then commits its result. Invalidation advances current_version even on deletion; only a result matching current version may be published. apply is atomic.

Defect: Old fill started before invalidation publishes after deletion/update and restores stale data.

Correct / must_not_report: Version fence drops obsolete fills, including tombstone version changes; no TTL is necessary for the stated guarantee.

## replica_decision (scorer only)

Controls: SD082.

Requirement: After changing an entitlement, confirmation must reflect the authoritative committed value immediately. Replica may lag by an explicitly permitted second, but that lag is not allowed for the confirmation decision.

Defect: A lagging replica reports old entitlement as immediate confirmation, exceeding this reader consistency contract.

Correct / must_not_report: Authoritative read meets confirmation semantics while replica lag remains valid for other eventual views.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
