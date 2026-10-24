# chicken-egg-detector qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:chicken-egg-detector`; content basis.
- Authored control family: EX016-023, RC007, RC011, RC041. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: EX016-017, EX020-023, RC007, RC011, RC041.

Defect: start on a fresh store returns before the only schema creator can run. Serving waits on schema while migration is gated on serving, so restart does not establish progress. Populated upgrade can hide it.

Correct / must_not_report: Migration is independent and precedes useful readiness. Do not report a harmless linear dependency, force the correct order into a cycle, or require steady-state liveness to depend on the database.

## early_default (scorer only)

Controls: EX019-020.

Requirement: First construction may occur before required endpoint configuration arrives. A later configure call must bind the endpoint before readiness; initialized means the endpoint is usable.

Defect: Early default marks initialization complete and prevents later required endpoint binding, regardless of retry.

Correct / must_not_report: Default remains uninitialized until the actual dependency binds; sequential late configuration is supported.

## readiness_order (scorer only)

Controls: EX018, EX021-023.

Requirement: Traffic can arrive immediately when router.publish is called. Requests require migrated schema and initialized pool. Migration is independent and supports the prior schema; no first request may see an uninitialized dependency.

Defect: Router accepts first request before migration/pool setup, exposing missing prerequisites.

Correct / must_not_report: Independent migration then pool then routing establish readiness without making liveness depend on remote services.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
