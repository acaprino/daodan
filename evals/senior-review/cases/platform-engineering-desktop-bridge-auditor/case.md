# platform-engineering:desktop-bridge-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR156–158, PR161 and platform-security/client-server bridge portions (initial pair: channel registration mismatch). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

The preload invokes save-document but main registers save-file only; invoking the required Save path finds no handler. Report registration mismatch, not a security vulnerability inferred from IPC existence.

## Correct countercase

The exposed call and registered handler agree on save-document and preserve the payload. Do not require a wider bridge or rename the public contract.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **window-capability (PR156–157, PR165, PR168–169)**: The intended caller identity does not match the capability binding; preserve denial for preview. Countercase: Do not widen the command to all windows or report intentional preview denial.
- **event-restart (PR160)**: After restart the required completion event has no listener. Countercase: Re-registration restores exactly one listener under the stated host contract.
