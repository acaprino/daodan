# Repair

Two uses, one discipline.

## A defect with a reproduction

Run the change cycle with phases 2 to 4 shortened:

1. Phase 1 as `references/preflight.md`; an `UNKNOWN_RED` baseline that is
   the defect itself becomes the oracle.
2. The interview fixes the observed behavior, the expected behavior and the
   trigger as one `EX-*`, plus the invariant the fix must keep. A decision
   record is written only when the fix changes a contract or a rule; a pure
   defect records its examples in the plan.
3. One wave: `testing:test-writer` writes the reproduction test (`RED`),
   the stack's specialist writes the fix inside its `write_set`, the oracle
   turns `GREEN`, the direct callers' tests run.
4. Stage C on the wave; then `references/finish.md`, whose stage D tier the
   roster computes.

Without a known cause, `senior-review:investigation-method` runs first, and
its reproduction test is the oracle.

## A plan produced by assess

Require the exact run and plan identity, then validate project identity,
authorizations and the recorded input snapshot through the protocol. Changed
inputs invalidate the affected action; reassess it rather than applying an
old plan. Each action runs through its canonical owner: knowledge methods for
instructions and documents, `testing:test-remediation-method` for tests,
`repo-hygiene:repo-hygiene` for reversible workspace operations,
`senior-review:application-cleanup-method` for application removal (commit
authorization and clean-tree prerequisites included), the change cycle for
semantic refactors with a known intent, followed by the abstraction audit.
`clean-code` is readability only; no other method guesses whether a symbol is
dead.

## Shared rules

Before each mutating phase record the exclusive workspace, `pre_phase_sha`,
the pre-step bytes, the candidate scope and the required gate. A failure
before commit restores the captured pre-phase state, never `HEAD~1`; published
commits are reverted with publication authorization. Tests first distinguish
product defect, wrong oracle, environment, flaky or unknown; an uncertain
failing test is not eligible for quarantine. Finish only when required actions,
gates and deliveries are accounted for, leaving incompatible commit-only
actions, unavailable gates and open design decisions visible. Re-check
documents and instructions outside the diff that the repair made stale.
