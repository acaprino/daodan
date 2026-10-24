# platform-engineering:offline-lifecycle-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR147–150 and relevant PR162–171 reference leads (initial pair: old client assets). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

Activation immediately deletes v1 while an existing v1 controlled client still needs /v1/editor.js offline. The next lazy load loses a required asset. Cite supplied client lifecycle and deletion order.

## Correct countercase

Activation retains v1 until no live old client requires it; v2 shell/version is separate. Do not flag old cache retention or require immediate skipWaiting.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **scope-and-fallback (PR147, PR149–150)**: The registered worker cannot control the promised app entry; do not assume registration implies offline support. Countercase: Correct scope and fallback satisfy the declared path; optional denied push need not block entry.
- **queued-write-resume (PR170–171, PR173–174)**: Memory-only queue loses edits at termination; rejection has no rollback/reconciliation path. Countercase: Durable queue plus explicit recovery state suffices; conflict policy stays with the data owner.
