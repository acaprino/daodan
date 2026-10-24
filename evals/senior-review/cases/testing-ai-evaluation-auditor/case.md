# testing:ai-evaluation-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR023 (pair: training leakage and self-derived oracle). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

The evaluation tests the same question used in training and obtains its expected answer from the current model itself. A consistently wrong response passes. Identify both leakage and dependent oracle as distinct reasons the claimed held-out factual capability is unproved.

## Correct countercase

Evaluation uses a held-out question and independently authored exact factual answer; training excludes it. Do not demand an LLM judge or a universal number of repetitions for this explicitly deterministic fixture.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **retrieval-tools-and-variance (PR023)**: Identify missing required adversarial/retrieval/tool/output protection and cherry-picked attempts, not a universal score deficiency. Countercase: Explicit failed delivery is honest; deterministic structural checks are distinct from semantic evaluation.
