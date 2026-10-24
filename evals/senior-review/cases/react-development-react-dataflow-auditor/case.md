# react-development:react-dataflow-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR041–046, PR054, PR056, PR097, PR099–106, PR113, PR118; PR120 Query gcTime (initial pair: cross-request mutable state). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

Two overlapping render requests overwrite currentUser before the first resumes after load. User A can receive User B’s data. Cite the module-scoped assignment, suspension and later read; this is request isolation, not speculative cache advice.

## Correct countercase

Each invocation reads its own user parameter after suspension. Do not require a cache or parallel fetch when no repeated independent I/O exists.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **dependency-waterfall (PR041–046, PR097, PR104–105)**: Sequential independent awaits derive about 800ms from supplied durations, exceeding budget; no new library required. Countercase: Parallel independent reads preserve dependencies and fit supplied timing; no need to parallelize auth.
- **freshness-and-storage (PR054, PR056, PR099–100, PR113, PR120 cache)**: Account-independent cache key and unchecked persisted schema violate separate explicit requirements. Countercase: An account key plus schema fallback suffices; 5-minute freshness is explicitly permitted, so do not demand staleTime:0.
- **serialization-and-lifetime (PR101–102, PR106, PR118)**: Report excessive server/client payload exposing token and unbound completion work; route token exposure to security as an adjacent cause. Countercase: Minimal serialized fields and the supported lifetime binding satisfy the stated operations.
