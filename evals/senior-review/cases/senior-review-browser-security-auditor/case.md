# browser-security-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:browser-security-auditor`; content basis.
- Authored control family: SD025-026, SD028-029. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD025.

Defect: A comment containing an HTML element with an event handler is inserted as markup in the served HTML. Source, HTML context and reachable script execution form the defect; no browser execution is claimed by static review.

Correct / must_not_report: HTML text-context escaping is effective. Missing CSP/CSRF tokens alone is not a finding; there is no authenticated state-changing operation or other context insertion.

## ambient_mutation (scorer only)

Controls: SD026.

Requirement: Browser cookies automatically authenticate transfer requests, including cross-origin POSTs. Trusted origin is https://app.example. The supplied same-origin token check is authoritative; account identity is server-derived.

Defect: A foreign page can cause an ambient-cookie authenticated transfer without a verified origin/token.

Correct / must_not_report: Effective origin and token gate precede the mutation; no missing named middleware claim is valid.

## credentialed_cors (scorer only)

Controls: SD028-029.

Requirement: Profile is authenticated by an ambient cookie; only https://app.example may read it cross-origin. These are the final edge response headers and no later policy is applied.

Defect: An arbitrary foreign origin is reflected with credentials enabled, allowing authenticated browser reads.

Correct / must_not_report: Allowlisted final headers enforce the real requirement; absent CSP on this JSON endpoint is not independently a demonstrated exploit.

## cookie_transport (scorer only)

Controls: SD029.

Requirement: Session cookie must be sent only over HTTPS. The application remains reachable at HTTP on the same host and no transport upgrade occurs before cookie transmission. HttpOnly and SameSite alone do not protect that hop.

Defect: Missing Secure sends ambient credential on the reachable HTTP request, exposing it on an unprotected hop.

Correct / must_not_report: Secure binds cookie to HTTPS; no blanket missing-header finding is justified beyond supplied path.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
