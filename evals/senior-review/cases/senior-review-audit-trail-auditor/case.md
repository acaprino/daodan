# audit-trail-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:audit-trail-auditor`; content basis.
- Authored control family: SD038-039. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD039.

Defect: A newline in display_name fabricates an additional physical audit record attributed to a chosen actor. Append-only storage cannot repair record framing.

Correct / must_not_report: JSON escapes embedded newlines and binds actor identity. Do not demand a particular audit vendor, a second sink or cryptographic signatures where append-only authenticated transport already meets integrity requirements.

## alternate_action (scorer only)

Controls: SD038.

Requirement: Both single and batch changes require an attributable immutable event. audit_write has authoritative actor and append-only delivery; its failure prevents the change. apply_change is otherwise authorized.

Defect: Batch directly invokes mutation and skips the mandatory audit/actor attribution path.

Correct / must_not_report: Each batch item traverses authoritative audit; no duplicate local diagnostic event is required.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
