# react-development:react-effects-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR037–040, PR053, PR070, PR083–084, PR086, PR090, PR108–110, PR119 (initial pair: stale subscription). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

After label changes, the installed pulse listener still writes the first label because the effect has an empty dependency list. The event handler must use the current prop. Cite closure capture and subscription lifetime.

## Correct countercase

The effect replaces the listener whenever label changes and removes the previous listener. Do not demand useEffectEvent or a ref when reactive resubscription satisfies the contract.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **dependency-cycle (PR083, PR108, PR119)**: Trace data write → new callback → effect rerun → another load; a state setter alone is insufficient. Countercase: No data dependency cycle; stale completion is suppressed.
- **lifetime-and-action (PR039, PR053, PR090, PR110)**: Report repeat submission on theme change and timer surviving unmount as separate causal failures. Countercase: User action owns submission; timer has deterministic teardown.
- **state-ownership (PR070, PR084, PR086)**: Report caller mutation, stale derived sum and collapsed queued updates by their different triggers. Countercase: Copied sort is valid without toSorted; functional updates preserve both increments.
- **effect-event-contract (PR037–038, PR040)**: Effect Event dependency changes identity and needlessly reconnects on render; retain room as genuinely reactive. Countercase: The event reads latest theme without suppressing room changes; no stable-callback claim.
