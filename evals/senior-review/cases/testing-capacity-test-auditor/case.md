# testing:capacity-test-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR022 (pair: sequential workload misses concurrent limit). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

The required simultaneous pair never exists: each send is awaited before starting the next. Therefore capacity loss specifically at concurrency two would not fail this test. Report workload mismatch; do not claim measured throughput.

## Correct countercase

asyncio.gather starts both sends concurrently and the oracle verifies both succeed. The source-only review cannot establish real service throughput, but must not retain the sequential-workload finding.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **bottleneck-and-oracle (PR022)**: Report unexercised bottleneck, nonrepresentative workload and missing outcome oracle; no throughput number may be invented. Countercase: The source design matches requirements while runtime remains explicitly unmeasured.
