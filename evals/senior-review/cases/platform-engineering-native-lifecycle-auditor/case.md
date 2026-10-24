# platform-engineering:native-lifecycle-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR151–155 and relevant platform security/reference mechanisms (initial pair: recreation state). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

The host destroys the controller on suspend and reconstructs it from saved. save_state omits draft, so typing then recreation returns empty text despite the declared retention requirement.

## Correct countercase

save_state and construction preserve draft. Do not require a database for the supplied host saved-state contract.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **revoked-permission-and-return (PR152; OAuth-return portion of PR164)**: Cached permission is not current OS authority; lost pending transaction breaks external-auth return. Countercase: Revocation recovery and saved transaction binding preserve required lifecycle. This packet does not test transport pinning, screenshots, backups or binary secrets.
- **native-capability-and-background (PR153, PR155; biometric portion of PR163)**: Timer continuation and unguarded biometric availability fail on declared lifecycle/device conditions. Countercase: Native scheduler plus supported credential fallback meets the contract without arbitrary memory budgets. This packet does not test screenshot/backup policy.

## Screenshot and backup boundaries (PR163)

The existing variant-directory materializer includes `privacy-policy.json` from exactly one variant. Each named scenario is independent. Its supported host version, effective platform bridge semantics, data classifications and approved privacy requirements are supplied synthetic facts, not a statement that Android or a production device was tested.

- **screen-capture**: Defect: the session card is visible on the only window while its effective secure-surface setting is false; the supplied capture path therefore includes the device-only credential. Correct: the effective platform-enforced secure setting makes that window blank to capture while leaving the user-visible card available. Do not demand hiding the required card from the user, a new biometric step or a universal screenshot prohibition.
- **cloud-backup**: Defect: backup is enabled and the sole session database is included by effective rules, so its device-only credential is copied to the cloud contrary to the approved policy. Correct: only that database is excluded by the effective path rule; preferences are intentionally backed up. Do not require disabling every backup, encrypting an excluded file or claiming an actual backup was run.

These two mechanisms have separate requirements/guards. A correct screenshot setting does not establish backup exclusion, and valid biometric fallback is evidence for neither. Record unknown actual device/vendor behavior as unexercised runtime; the source-contained effective assumptions are sufficient for this bounded static packet.
