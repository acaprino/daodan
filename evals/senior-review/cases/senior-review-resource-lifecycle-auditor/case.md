# resource-lifecycle-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:resource-lifecycle-auditor`; content basis.
- Authored control family: EX079-097, RC004-005, RC016, RC043. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: EX079, EX081-082, EX086, EX097.

Defect: A query exception exits read before release and leaves pool.active increased; repeated failures accumulate outstanding ownership. No invented time-to-outage is justified.

Correct / must_not_report: finally covers success, exception and synchronous cancellation exits. Do not require a context manager by name or call a bounded legitimate checkout a leak.

## partial_acquire (scorer only)

Controls: EX080, EX082.

Requirement: open_first succeeds, open_second may raise, and caller owns each acquired resource. close methods may raise too; every independently owned handle must still receive close.

Defect: Second acquisition failure leaks first; first.close failure also skips second.close in defective cleanup.

Correct / must_not_report: Nested ownership scopes release previously acquired handles even when acquisition or cleanup fails.

## borrowed_lifetime (scorer only)

Controls: EX084-085, EX094-095.

Requirement: The pool owns the borrowed handle; a request must not close it. Background use must finish before returning the borrow. join waits for all uses; task has no own release authority. start either fails before launching or succeeds; join completes all uses before returning or raising.

Defect: Request closes a borrowed owner handle while background task may still use it, creating use-after-release and invalid pooled ownership.

Correct / must_not_report: Joining task before returning borrow preserves owner lifetime; no manual close of borrowed handle is required.

## listener_identity (scorer only)

Controls: EX090-093.

Requirement: Emitter strongly retains handlers until identical handler is removed. Mount may repeat; disposed components must no longer be retained. Component owns the subscription.

Defect: Disposer creates a different lambda so the original strong reference remains; repeated mount/dispose retains dead components.

Correct / must_not_report: Stable handler identity enables actual removal and garbage collection; weak references are optional.

## cancelled_permit (scorer only)

Controls: EX083, EX096.

Requirement: Work may raise BaseException cancellation after permit acquisition. Every successful acquire must be paired with release; permit release does not throw.

Defect: Cancellation outside Exception skips both releases, retaining permit.

Correct / must_not_report: Finally covers BaseException exits; cancellation propagation is preserved.

## broken_pool_return (scorer only)

Controls: EX086-089.

Requirement: A query error marks the connection broken. Healthy release returns it to checkout; discard closes and removes it. query sets broken before raising; cancellation and other errors need the same final ownership check.

Defect: Broken connection is returned as healthy and reused by later borrowers.

Correct / must_not_report: Invalidation disposes broken resource while normal return preserves valid reuse.

## timer_owner (scorer only)

Controls: EX092, EX094-095.

Requirement: timer.start retains the callback until cancel. The component disposer must cancel its timer; process-lifetime ownership is not intended.

Defect: Disposal does nothing, so timer retains callback/component and continues after owner destruction.

Correct / must_not_report: Disposer releases exactly the timer token it owns; scheduler cadence is a separate concern.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
