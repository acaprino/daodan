# platform-engineering:app-distribution-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR154 packaging, PR159–160 and relevant platform distribution references (initial pair: working-directory resource lookup). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

The package puts help.html under resources, but help_path resolves it relative to arbitrary process cwd. Launch from /tmp fails the required help lookup. The packet supplies the path semantics, so no actual packaging is claimed.

## Correct countercase

The resource root passed by the host is used explicitly. Do not require a particular packaging framework when the declared root contract suffices.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **artifact-target-and-inclusion (PR154, PR158)**: Report concrete target/resource mismatch from supplied artifacts, not successful execution. Countercase: Matching inventory is structural evidence only; do not claim installation or reject unexercised runtime as a product defect. This does not exercise PR167.
- **verified-update-channel (PR159; update-verification portion of PR166)**: Nightly selection and skipped verification violate two explicit distribution requirements; no update may be executed. Countercase: Stable channel and verified-install guard satisfy the binding; underlying cryptography is a separate owner. An updater hook does not prove ASAR/fuse integrity.

## Packaged archive integrity (PR167)

The existing directory materializer includes `archive-integrity.json` from exactly one variant. Supported version/artifact, attacker file permissions, trusted executable metadata and loader behavior are explicit synthetic facts. Do not infer actual installed Electron behavior or a successful platform probe from the packet.

- **replace-archive**: Defect: an attacker may replace app.asar without modifying the trusted executable; archive validation is effectively disabled, so changed JavaScript is accepted despite an immutable expected digest in the binary. Correct: the effective validation fuse rejects the mismatching archive before any app code. OS executable signing alone is insufficient for this mutable separate file; no specific signing service is required.
- **directory-fallback**: Defect: archive validation is enabled but the loader may select attacker-created resources/app before the validated archive. OnlyLoadAppFromAsar is false, so a valid original archive cannot protect the selected directory code. Correct: enforced archive-only loading ignores the directory and selects the validated original archive. Do not report a mere directory's existence when the effective loader cannot select it.

Both assume this Windows build supports the declared enforcement and the attacker cannot change binary metadata/settings. Unsupported versions, absent artifact settings or a different trust requirement would need their own evidence/gap; they are not silently covered by these scenes. No archive, executable or installation was actually modified or launched.
