# python-development:python-semantics-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR236, PR250–258, PR305, PR314–315, PR321 (initial pair: mutable default and repeated calls). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

Calling collect("a") then collect("b") without an explicit list returns ["a","b"] on the second call, violating per-call isolation. The list default was allocated once at definition.

## Correct countercase

A None sentinel creates a fresh list only for omitted state, while an explicit supplied list remains intentionally mutable. Do not require a class, type hints or refactoring this small module.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **default-evaluation (PR305, PR321)**: A default call freezes time at definition; show first/later invocation difference. Countercase: Sentinel reevaluates per call; no class or dependency required.
- **short-circuit-and-binding (PR250–255, PR315)**: Eager extraction violates short-circuit side-effect/exception behavior; local shadowing makes list uncallable. Countercase: Guard order and builtin binding satisfy behavior; pure functions remain valid.
- **exception-and-return (PR236, PR252, PR256, PR258, PR314)**: Expanded catch scope swallows read failure and truthiness collapses false/zero/empty with missing sentinel. Countercase: Separate read scope and identity check preserve authorized semantics.
