# callback-authenticity-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:callback-authenticity-auditor`; content basis.
- Authored control family: SD036-037. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD037.

Defect: An old correctly signed payload (timestamp=100, now=1000) reaches apply_event. Signature authenticates the bytes but does not enforce the required replay window.

Correct / must_not_report: The corrected time check precedes effects and binds the signed timestamp. Do not call legitimate retry inside the window a forgery or demand a separate duplicate handler despite the supplied apply_event contract.

## verification_failure (scorer only)

Controls: SD036.

Requirement: verify authenticates the exact raw bytes and raises on any mismatch; dispatch creates an irreversible business effect. Verification failure must prevent dispatch.

Defect: Raised signature error is swallowed and the unverified body reaches dispatch.

Correct / must_not_report: Rejection propagates before effects; raw-body verifier may be supplied middleware rather than duplicated code.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
