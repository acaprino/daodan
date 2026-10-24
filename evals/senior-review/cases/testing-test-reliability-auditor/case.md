# testing:test-reliability-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR001–002, PR008, PR018–019, PR031–036 (pair: environment leak). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

test_staging leaves MODE=staging globally, so test_default fails when executed afterward. Report the concrete order-dependent leak, not a claim that flakiness was observed. No suite run is authorized.

## Correct countercase

patch.dict restores MODE after the staging test. The default assertion is guarded by an explicit initial environment contract; do not flag environment use alone.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **attempt-provenance (PR001–002, PR008, PR035–036)**: Report erased attempt and unsupported clean conclusion; do not invent a flaky-test cause. Countercase: Accurate accounting and an open diagnosis are valid.
- **resource-cleanup (PR031–034)**: Identify resource collision and failure-path cleanup with exact triggering conditions; static evidence is not observed intermittence. Countercase: Independent ownership and unconditional cleanup satisfy isolation.
- **measurement-freshness (PR018–019, PR036)**: Reject stale metrics as current evidence and retain the unprotected requirement. Countercase: An explicit unavailable check is not a new product defect or green verification.
