# Verify (phase 6, and the standalone gate)

Verification binds every check to an exact candidate: a lifecycle run's
candidate, or the working tree, branch or range the user names. Load the
protocol's snapshot and gate procedure. Record the baseline separately from
the candidate and include uncommitted changes in the candidate fingerprint.
A remote job on an older revision does not verify this candidate; a gate that
needs a push needs its own authorization, otherwise it stays unavailable.

## Checks

1. The project's declared test, lint, type and build commands on the
   candidate, through `testing:test-preparation` for runner and
   configuration. Passing self-generated assertions alone establish no
   oracle; record wrong-oracle evidence apart from product defects and
   environment failures.
2. Every `EX-*` of the run's proposed record has a passing test on the
   candidate and a failing one on the base; every `INV-*` is named by at
   least one test or one review finding that confirms it holds.
3. Instruction consequences through `project-knowledge:instructions-method`
   when commands, setup, test policy or architecture changed: canonical and
   generated parity, and whether the host loaded the result is a separate,
   possibly unavailable, probe.

## Review of the candidate (stage D)

Run `senior-review:review-method` through `senior-review:review-preparation`
with shape `branch` and stage `candidate` on the whole candidate (`base_sha`
to the candidate head, untracked scoped files included), passing the run's
scope, baseline and candidate.
Preparation reads the policy from the base commit, builds the evidence pack,
computes the roster from the candidate's signals, and grants the reachability
lens a reproduction scratch path when the workspace is a `WORKTREE` or
`BRANCH` owned by this run.

A confirmed `Critical` or `High` finding opens one remediation wave through
`references/waves.md`, reviewed with shape `light`, then stage D again as a
new review entry. At most two such waves; a third blocking result
returns to the user with the finding, the attempts and the options.

## Result

Only the owner of a finding applies its remediation; verify produces evidence
and a result. A failed gate names the observed failure and the next action.
Static inventory, in-depth reading and runtime exercise are reported as three
coverage facts. Account for every expected delivery and required check before
completing the run; an unavailable runner, missing credentials or an
unexercised product path are declared gaps, never passed checks.
