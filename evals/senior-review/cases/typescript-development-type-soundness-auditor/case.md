# typescript-development:type-soundness-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR121–122, PR124–125, PR130–140 (initial pair: false type predicate). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

isUser checks only id but promises name:string. {id:"1",name:3} passes and greet calls toUpperCase on a number. The full predicate contract, not the presence of a cast, is the defect.

## Correct countercase

The predicate checks both fields and rejects malformed input. Do not require a schema dependency or flag the Record cast after the object guard.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **assertions-and-generics (PR121–122, PR124–125, PR130–132, PR139)**: Unconstrained values and absent lookup bypass types; also the first bad function returns a string despite number. Cite reachable instantiations. Countercase: A structural constraint and actual guard suffice without a schema or comment.
- **effective-config-and-exhaustiveness (PR133–138)**: Report missing refunded result and unsafe absent lookup. Do not report absent local strict when inherited. Countercase: Complete Record and runtime guard are valid without never/satisfies syntax or mandatory flag changes.
