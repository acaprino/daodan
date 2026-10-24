# testing:test-suite-structure-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR003–007, PR009–010, PR026–028 (pair: equivalent protection versus independent persistence). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

Both unit tests exercise the same total([2,3]) input, result and failure mode with no independent protection or bugfix provenance. Report redundant coverage with both locations; do not use naming similarity as proof.

## Correct countercase

The second test writes and reads the result through SQLite, protecting persistence separately from the pure calculation. Do not call it redundant merely because the value is also 5.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **layer (PR003–005, PR027–028)**: Report the real-boundary placement/budget violation, not just a database import. Countercase: Preserve the independent service and persistence layers.
- **moved-behavior (PR006, PR026)**: Report lost protection after rename; do not call the behavior retired. Countercase: Do not flag the renamed source or old test filename as an orphan.
- **focused-collection (PR007)**: Report .only suppressing required rejection coverage. Countercase: No focused collection remains; the declared platform exclusion is valid.

## Required production-input completion

Before dispatch, the independent scorer found the canonical role requires actual imported behavior owners/reachable production flow, while the old packet supplied only tests and verbal outcomes. Old prepared attempts remain unexecuted and byte-preserved. Fresh variants supply the same minimal production owners and explicit hypothetical fixture/runner contracts, without changing test behavior or reviewer bodies. This establishes source applicability; runtime remains unauthorized and unobserved.
