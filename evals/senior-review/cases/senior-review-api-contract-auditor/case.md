# api-contract-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:api-contract-auditor`; content basis.
- Authored control family: SD043-064, EX163-164, RC026. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD043, SD046, SD056, RC026.

Defect: serialize({"id":7}) emits a JSON number; consume fails despite the mock and shared type carrying a string. Full credit must trace actual serialization, authoritative type and consumer.

Correct / must_not_report: Shared contract and serializer agree in the atomic boundary. Do not demand OpenAPI, a schema registry, an additional reviewer, or conflate shape correctness with business eligibility.

## request_and_error (scorer only)

Controls: SD044-045, SD047.

Requirement: The interface accepts integer limit1..10 and rejects missing/NULL/string/unknown fields with JSON {error:invalid}, status400. Accepted response is JSON with items and status200; client always decodes JSON.

Defect: Missing/coerced/out-of-range/unknown request fields violate declared acceptance; malformed input returns HTML to a JSON-only consumer. These are acceptance and error-envelope mechanisms.

Correct / must_not_report: Exact boundary validation and JSON errors meet this contract without requiring a schema library.

## strict_compatibility (scorer only)

Controls: SD051-053, SD056-059.

Requirement: Old consumer remains supported and accepts only status=ready or busy plus id:string. It rejects unknown fields. New producer is not atomically deployed with that consumer; changing the schema document alone does not remove support.

Defect: New enum plus new optional field break the actual strict old consumer despite being additive-looking. Qualify each value-direction claim.

Correct / must_not_report: Emitted value remains in supported old decoder domain; no mandatory version bump is inferred if compatibility is preserved.

## protobuf_tags (scorer only)

Controls: SD054.

Requirement: Wire tag1 is immutable string account_id for supported old readers. New region field must not reuse tag1; encoder returns numeric-tag payload and old_reader interprets tag1 as account identity.

Defect: Tag1 changes meaning from account to region and old reader consumes wrong identity even though both are strings.

Correct / must_not_report: Original tag meaning is preserved; new tag can coexist without an invented registry.

## graphql_nullability (scorer only)

Controls: SD055.

Requirement: GraphQL schema declares display:String! for each returned user. Stored display may be NULL; the approved resolver fallback is user ID. A selected display field must not bubble null into the parent response.

Defect: NULL stored value reaches a non-null GraphQL resolver field and propagates response failure.

Correct / must_not_report: Approved ID fallback meets non-null semantics; do not treat it as a missing DB migration obligation.

## stream_terminal (scorer only)

Controls: SD048, SD061-063.

Requirement: AI provider chunks may be partial; only complete output with finish=stop may reach consume, and it must contain id:string. Refusal/truncation must return failed. Schema examples never authorize actions.

Defect: Parseable partial/truncated data enters success without finish check; wrong shape/type reaches consume without validation.

Correct / must_not_report: Terminal status plus runtime shape check handles refusal/truncation and malformed arguments; schema-valid id still does not grant authority.

## units_and_cursor (scorer only)

Controls: SD049, SD064.

Requirement: The external API requires timeout seconds while caller budget is integer milliseconds. Pagination cursor on the wire must be a string even when internal ID is numeric.

Defect: 5000ms becomes5000seconds and numeric cursor violates string decoder. The units and cursor mismatches are distinct.

Correct / must_not_report: Explicit unit conversion and string serialization meet the existing interface.

## retained_message (scorer only)

Controls: SD057-060.

Requirement: Retained wire version1 uses event_id and value; current version2 uses event_id and payload. Both are supported. Unknown versions and malformed values must fail explicitly; JSON scalar value must be a string.

Defect: Old retained message fails despite supported v1; malformed/unknown inputs are not validated against actual version contract.

Correct / must_not_report: Version-specific decoder handles retained data and rejects unsupported shape; transport ack consequences are not part of this function.

## Correct-countercase correction

The original retained_message countercase admitted a JSON boolean version because
Python treats True as equal to 1 (and dictionary membership used numeric equality).
Only wire versions 1 and 2 are supported; true is not either numeric wire version.
The corrected decoder explicitly rejects boolean versions before its value check.
Original case/source and prepared unexecuted correct trial remain retained; a new
correct attempt binds this fix. Defective target and reviewer body are unchanged.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
