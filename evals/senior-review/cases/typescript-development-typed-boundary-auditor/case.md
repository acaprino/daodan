# typescript-development:typed-boundary-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR123, PR126–129 (initial pair: HTTP/JSON annotation without validation). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

The JSON cast makes a numeric id look typed as string. Input {"id":7} reaches .toLowerCase and throws despite the required invalid result. Report missing runtime validation at ingress.

## Correct countercase

The guard rejects numeric IDs before typed use and accepts valid strings. Do not require a schema library or centralized module for this single boundary.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **queue-storage-env (PR126–129)**: Identify separate unchecked queue/storage shapes and invalid/NaN environment conversion, with malformed or missing inputs. Countercase: Existing handwritten parser and key-specific checks are sufficient; no centralized configuration module required.
- **trusted-adapter (PR123, PR127–128)**: The unguarded adapter makes a typed handler unsafe. Countercase: Do not require duplicate validation inside handle after the only caller has validated.
