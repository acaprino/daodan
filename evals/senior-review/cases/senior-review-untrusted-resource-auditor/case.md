# untrusted-resource-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:untrusted-resource-auditor`; content basis.
- Authored control family: SD022-023, SD027, RC032. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD022.

Defect: download("../private/config.txt") normalizes outside the permitted root and returns private bytes. Cite normalization and use, not a hypothetical symlink.

Correct / must_not_report: Containment by path components closes traversal and absolute-path escape in this immutable virtual filesystem. Do not invent TOCTOU, symlink, DNS or upload execution capabilities absent from the fixture.

## redirect_destination (scorer only)

Controls: SD027.

Requirement: All outgoing requests must remain on public.example. The virtual transport follows the returned redirect target, with no network; initial and redirected URLs are attacker influenced.

Defect: A permitted initial URL redirects to an internal virtual URL; validating initial host does not bind final contact.

Correct / must_not_report: Both actual hops constrained in the one-hop immutable virtual transport. DNS rebinding is not modeled and must not be claimed as executed.

## upload_interpretation (scorer only)

Controls: SD023.

Requirement: Public uploads must never be served as executable HTML. Stored content is rendered using the returned MIME type. Bytes are untrusted; image_transform validates/decodes and emits inert PNG or rejects, including decompression limits.

Defect: Raw attacker bytes served as HTML can execute on the trusted upload origin, bypassing the non-executable upload contract.

Correct / must_not_report: Validated inert transformation and matching MIME close the path; filename extension is unnecessary.

## check_use_binding (scorer only)

Controls: RC032.

Requirement: An attacker may replace the directory entry between resolve and open. resolver.is_allowed checks the resolved path; open_checked_handle atomically confines and returns the opened allowed descriptor. Pure injected operations, no real filesystem.

Defect: Attacker swaps name after validation; reopening original name can reach a different, disallowed object.

Correct / must_not_report: Atomic confined descriptor binds validation to the actual opened resource, not merely a stale path string.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
