# Verify (phase 6, and the standalone gate)

Load `references/specification.md`; recheck bound specification digest/approval
before candidate review. Legacy/pure repairs retain their intent.

Bind checks to the named candidate, including uncommitted content, through
protocol snapshots/gates; retain baseline. Carry post-task obligations per
`references/context-cycle.md`. Older remote checks cannot verify it; a
required push needs authorization or stays unavailable.

## Checks

1. Run declared test/lint/type/build commands on the candidate through
   `testing:test-preparation` runner/configuration diagnosis. Route packet
   `validation_obligations` to `testing:test-writer`, which confirms each oracle.
   Self-generated assertions alone establish no oracle; distinguish wrong oracle, product and
   environment failures.
2. Changed `EX-*` need candidate-passing, base-failing tests; retained requirements
   need candidate-passing regressions. Each specification/record `INV-*` needs
   a confirming test or review finding.
3. For command/setup/test-policy/architecture changes, use
   `project-knowledge:instructions-method` for canonical/generated parity.
   Actual host loading is a separate, possibly unavailable probe.

## Review of the candidate (stage D)

Run `senior-review:review-method` through `senior-review:review-preparation`,
shape `branch`, stage `candidate`, on `base_sha` through candidate head including
scoped untracked files. Pass scope/baseline/candidate and specification `EX-*`/`INV-*`. Preparation reads base policy,
builds evidence and computes the roster; the reachability lens receives reproduction
scratch only in a run-owned `WORKTREE` or `BRANCH`.

Retain jobs, member coverage and independent verification in the ledger. Select
no second roster/body. Light waves use this composition contract with distinct
preparation and one discovery job.

A confirmed `Critical`/`High` opens one remediation wave through
`references/waves.md`, reviewed as `light`, then stage D as a new review entry.
At most two waves; a third blocking result returns finding, attempts and options
to the user.

## Result

Owners remediate; verify supplies evidence/result. A failed gate
names observed failure and next action. Report inventory, in-depth reading and
runtime exercise separately. Account for every expected delivery and required
check before completion. Unavailable runners/credentials and unexercised product
paths are gaps, never passed checks.
