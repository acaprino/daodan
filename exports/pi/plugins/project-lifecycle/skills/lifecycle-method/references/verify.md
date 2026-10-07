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
Review affected contracts and failure paths through senior-review:review-method.
Use knowledge audit for consequences outside the diff, and abstraction audit for
changed concept ownership. Scope these operations to risk; do not launch all
auditors on an unrelated one-line change.

Static inventory/read coverage and runtime exercised paths are separate. Source
review cannot assert browser functionality. Missing credentials, unavailable
runners or unexecuted product paths are declared gaps, not successful checks.

Only the owner of a finding may apply its remediation; verify itself produces
evidence and a result. A failed gate points to the exact observed failure and next
action. Count expected deliveries and required checks before completing the run.

