# secret-exposure-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:secret-exposure-auditor`; content basis.
- Authored control family: SD030, SD033-035. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD030.

Defect: diagnostics({"region":"eu","service_credential":"synthetic-value"}) returns the backend credential to anonymous callers. Identify unauthorized reader and boundary without copying credential bytes into report.

Correct / must_not_report: A region is public. Absence of a vault or encryption in this pure function is not a defect; injected deployment configuration and narrowed diagnostics meet the supplied boundary.

## nonce_scope (scorer only)

Controls: SD034.

Requirement: The supplied AEAD seal(key_id,nonce,data) requires a nonce never reused under a key. The caller provides arbitrary data; allocate_nonce(key_id) atomically allocates unique nonces for the entire key lifetime.

Defect: Two encryptions under one key reuse nonce0, violating the supplied AEAD confidentiality/authenticity requirement.

Correct / must_not_report: Atomic allocator covers all writers and key lifetime; no unsupported runtime cipher claim is needed.

## retired_key (scorer only)

Controls: SD035.

Requirement: active_ids is authoritative; retired keys are retained solely to read an archive and must not authorize current requests. verify cryptographically validates the signature.

Defect: A retained retired key can still authorize a new signed request despite its exclusion from active_ids.

Correct / must_not_report: Archive retention is permitted; current authority is independently restricted to active IDs.

## comparison_oracle (scorer only)

Controls: SD033.

Requirement: The HTTP response must not disclose secret prefixes. Diagnostics currently return the comparison result and inspected-prefix count to the caller; secrets have fixed length.

Defect: Explicit inspected count reveals how far guesses match, allowing adaptive recovery; no noisy timing measurement is necessary for this modeled side channel.

Correct / must_not_report: Only constant-time equality result is returned; absence of a timing experiment is not a claim of measured leakage.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
