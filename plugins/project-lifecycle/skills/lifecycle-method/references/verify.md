# Verify

Verification can inspect an exact lifecycle run or a candidate project snapshot.
Load project-protocol's snapshot and gate procedure. Define which behavior,
protection and consequences must hold before choosing the smallest relevant checks.

Record the baseline separately from the candidate. Include noncommitted changes in
the candidate fingerprint. Every check records command/tool, environment, status,
snapshot/revision, scope, output reference and its limitations. A remote green job
on the old branch HEAD does not validate uncommitted edits. If CI requires a push,
the publication and recovery sequence needs actual authorization; otherwise mark
that gate unavailable and preserve the candidate for review.

Use testing:test-preparation for runner/configuration and meaningful protection.
Passing self-generated assertions alone does not establish a correct oracle.
For suite changes, verify the accepted behavior inventory, independent failure modes,
resource isolation and replacement protection through the testing methods. Record
wrong-oracle evidence separately from product corrections and environmental failures.
Review affected contracts and failure paths through senior-review:review-method.
Pass the run's resolved scope, captured baseline and exact candidate bindings to
senior-review:review-preparation for the code-review variant, with this run's
output root. Include full scoped untracked-file content and any baseline evidence;
declare unavailable comparisons. Supply that same prepared bundle to review-method
so it cannot auto-select an unrelated Git diff or last commit, or prepare twice.
The same preparation selects applicable React, TypeScript and platform workers;
their required provider bindings are declared by this lifecycle entry. Present
the complete review selection and expected cost before dispatch. The assessment's
quick audit cap does not remove a required correctness dimension from a candidate
gate. Reuse only snapshot-bound deliveries and report failed or unavailable ones.
Use knowledge audit for consequences outside the diff, and abstraction audit for
changed concept ownership. Scope these operations to risk; do not launch all
auditors on an unrelated one-line change.

When instructions or their dependencies changed, use
project-knowledge:instructions-method to verify canonical/generated parity, applicable
scope, actual commands and prerequisites, and project-specific test policy. Distinguish
a file on disk from evidence that the intended host loaded it. Record required reloads,
new-session checks and enforcement limits. A required loading probe without evidence
stays unavailable; successful synchronization alone cannot satisfy it.

Static inventory/read coverage and runtime exercised paths are separate. Source
review cannot assert browser functionality. Missing credentials, unavailable
runners or unexecuted product paths are declared gaps, not successful checks.

Only the owner of a finding may apply its remediation; verify itself produces
evidence and a result. A failed gate points to the exact observed failure and next
action. Count expected deliveries and required checks before completing the run.

