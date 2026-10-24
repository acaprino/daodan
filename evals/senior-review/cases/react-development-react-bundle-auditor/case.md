# react-development:react-bundle-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR047–052, PR078, PR111, PR120 module-delivery portion (initial pair: eager optional feature). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

The source imports optional-export statically; the supplied matching build map confirms its 800KB inclusion in the home chunk, violating the explicit 100KB home budget. The feature is reachable only after clicking Export. Both source reachability and budget are required evidence.

## Correct countercase

Dynamic import moves the exporter to a separate requested chunk; the supplied build map puts home at 30KB. Do not flag the barrel/package name or the existence of an 800KB optional chunk alone.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **supported-exports (PR047–048)**: Deep-import advice that ignores export restrictions breaks the build; show the effective resolution contract. Countercase: Do not report the public barrel import when supplied tree shaking removes unused modules.
- **preload-and-critical-work (PR049–052, PR078, PR120 module)**: Optional work blocks entry while required first-operation reporting is deferred; technique alone is not the rule. Countercase: Required reporter remains eager and chart stays conditional; no mandatory hover preload or arbitrary chunk grouping.
