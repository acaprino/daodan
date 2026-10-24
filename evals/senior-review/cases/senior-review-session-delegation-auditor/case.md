# session-delegation-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:session-delegation-auditor`; content basis.
- Authored control family: SD001, SD006-008, SD010, SD031-032, RC010. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD001.

Defect: A valid console token with iss=company, sub=alice, exp=200 at now=100 and active alice authenticates to billing. Missing audience enforcement crosses delegated authority; signature verification itself works.

Correct / must_not_report: Do not report unsigned-token acceptance or missing JWT library: the fixture uses its documented HMAC protocol and validates signature, audience, issuer, expiry and account state. Key is an injected secret, no default credential.

## login_rotation (scorer only)

Controls: SD006, SD008.

Requirement: Anonymous session IDs are attacker selectable. Login must replace the old ID; store is backend-only. fresh_id supplies a secure unique ID.

Defect: The attacker-selected anonymous ID becomes authenticated and remains known to the attacker.

Correct / must_not_report: Fresh server-generated ID replaces old authority and old key is removed; protected backend store itself is valid.

## refresh_revocation (scorer only)

Controls: SD007.

Requirement: An account-wide revocation counter invalidates all older refresh tokens. The refresh operation is atomic and the token signature was verified before this function.

Defect: Old refresh token revocation=0 can renew after account counter becomes1, regaining current authority.

Correct / must_not_report: Effective atomic counter and active check deny revoked refresh; concurrency is explicitly serialized by the owner.

## delegated_resource (scorer only)

Controls: SD010.

Requirement: A download capability delegates GET only for the signed resource until expiry. Expected MAC is supplied by a trusted HMAC signer; caller controls resource and operation.

Defect: Signature covers expiry only; replacing resource retains valid authorization for an ungranted object.

Correct / must_not_report: Resource, operation and expiry are canonically bound; the trusted MAC implementation supplies cryptographic authenticity.

## credential_prediction (scorer only)

Controls: SD031.

Requirement: Password reset tokens grant account control. Observers know request_time and account_id; fresh_secret is a supplied cryptographically secure 256-bit generator.

Defect: Known ID/time determine the reset credential, enabling unauthorized reset.

Correct / must_not_report: Supplied secure generator is sufficient; do not demand a token framework or online provider test.

## password_derivation (scorer only)

Controls: SD032.

Requirement: Passwords must use the approved slow password KDF with unique random salt; offline database theft is in scope. kdf(password,salt) and random_salt provide those approved properties.

Defect: Fast unsalted digest bypasses the explicitly approved password KDF, permitting direct bulk dictionary comparison after theft.

Correct / must_not_report: Injected approved KDF and fresh salt satisfy the requirement; do not invent parameters for an unavailable KDF implementation.

## service_identity (scorer only)

Controls: RC010.

Requirement: A trusted mTLS certificate chain authenticates a peer name. Billing accepts only peer billing-worker; other company services have valid chains but different authority.

Defect: Trusting any certificate from company CA accepts an unintended service identity.

Correct / must_not_report: Chain plus expected peer binding covers the delegation boundary; routing alone is not identity.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
