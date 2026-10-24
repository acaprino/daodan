# logic-integrity-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:logic-integrity-auditor`; content basis.
- Authored control family: SD124-142, EX165. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD124, SD132-134, SD138-139.

Defect: batch_edit changes a completed order despite the explicit terminal-state rule. Cite the independently supplied rule, alternate caller and mutator; do not invent a payment requirement from names.

Correct / must_not_report: All mutation paths use the terminal guard. Scoped semantic context is an accepted prerequisite without an interconnect-map file; absence of a DB constraint is not a domain finding.

## unknown_state (scorer only)

Controls: SD131-133, SD142.

Requirement: External market state can be open, closed or unknown. Unknown must suspend trading decisions and remain distinguishable from confirmed closed. No name-derived extra business rule applies.

Defect: Unknown observation collapses into confirmed closed, violating the explicit tri-state rule and any consumer that treats closed as evidence.

Correct / must_not_report: Unknown preserved; failing safe does not require presenting a known negative fact.

## shared_handles (scorer only)

Controls: SD127-130.

Requirement: Two handles refer to one shared coordinator. Revocation through either handle invalidates all previously issued views; view_epoch must always reflect shared epoch, not per-instance captured state.

Defect: A.revoke advances shared epoch but B.view_epoch remains its old captured epoch. Enumerating both instances is required, not inferring singleton behavior.

Correct / must_not_report: Both handles read authoritative shared state; separate handle objects are not inherently defective.

## revision_identity (scorer only)

Controls: SD136-137.

Requirement: Same event ID with a larger revision is a new provider correction and must update value. Repeating same or older revision is a duplicate. Input handling is serial.

Defect: ID-only dedup discards a genuine higher revision, confusing same identity with same logical operation.

Correct / must_not_report: Revision-aware update preserves corrections and suppresses true duplicates; no remote idempotency claim is implied.

## reentrant_transition (scorer only)

Controls: SD125, SD134-135, SD138.

Requirement: Order notification callbacks may synchronously reenter the order. Invariant requires paid state iff receipt is present at every callback boundary.

Defect: Callback observes paid without receipt and can act on forbidden intermediate state; concurrent threads are unnecessary.

Correct / must_not_report: Both invariant fields established before observer reentry; a new state-machine library is unnecessary.

## completion_artifact (scorer only)

Controls: SD125, SD140.

Requirement: A task is complete only when every required artifact was delivered and nonempty. A stopped worker may have delivered nothing; provided artifacts map contains actual captured bytes.

Defect: Stopped worker with missing required report is declared complete. This is a domain completion defect, not evidence of delivered work.

Correct / must_not_report: Actual nonempty required deliveries gate completion; zero findings may still have a valid report.

## domain_units (scorer only)

Controls: SD141.

Requirement: Wire payload amount is integer cents, including valid zero. The display contract is decimal euros; wire type itself is valid.

Defect: Schema-valid100cents becomes100euros; semantic unit conversion, not JSON type mismatch, is the cause.

Correct / must_not_report: Correct unit mapping preserves zero and cents without inventing a wire-schema defect.

## exception_contract (scorer only)

Controls: SD126.

Requirement: Service promises ValueError for invalid requests; caller catches it and records rejected. Parser raises RuntimeError for malformed input. Other failures must propagate unchanged.

Defect: Malformed input raises the parser RuntimeError through service, bypassing caller contractual rejection path.

Correct / must_not_report: Boundary translates the declared parser failure and preserves cause; no blanket catch required.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
