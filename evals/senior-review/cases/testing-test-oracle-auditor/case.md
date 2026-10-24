# testing:test-oracle-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR011–017, PR024, PR029–030, PR324 (pair: mock tautology versus real behavior). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

test_discount stubs the function under test and asserts its programmed return. It passes if production discount returns any wrong value. The report must connect the absent production call to the unprotected 10% requirement.

## Correct countercase

The correct test invokes discount and compares against independent 90 for an input of 100. It is valid despite being one assertion and using a simple function.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **contradiction (PR011, PR024, PR029–030)**: Identify the wrong oracle from independent authority, not test majority or current code. Countercase: Coupon state justifies a different outcome; no contradictory finding.
- **call-echo (PR012, PR015)**: Show that mirrored calls fail to protect either observable output. Countercase: Boundary double is justified; production behavior and independent outcomes remain exercised.
- **empty-assertions (PR013, PR016–017)**: Report the vacuous loop/empty-result protection gap; equivalent survivor is not a second defect. Countercase: Length plus field assertions cover the required failure mode; no finding from equivalent mutation.
