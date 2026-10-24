# All-reviewer selection evaluation

Tested 22 registered lenses: 21 independent reviewers/auditors and the document-structure audit hybrid. The suite contains 132 individual controls and 12 complete problems.

This measures Julia's selection decisions. The reviewer agents themselves were not run against defects. All inputs include the task and concrete source/document evidence. This is a new synthetic selection suite, not directly comparable with the earlier code-hunk pilot. Questions and labels were fixed before inference; no threshold tuning or paid LLM baseline was performed.

Execution coverage: 348/420 requests returned complete outputs; 852 binary decisions were classified. All grounded controls completed actual inference: True. Catalog input rejections are not negative predictions.

| Variant | Individual correct | Required positive roles found | Negative controls incorrectly activated | Roles with all six controls correct |
| --- | --- | --- | --- | --- |
| catalog_noul | 34/60 | 25/30 | 21/30 | 1/22 |
| grounded_noul | 69/132 | 36/66 | 33/66 | 1/22 |
| grounded_choice | 72/132 | 39/66 | 33/66 | 1/22 |

## Individual reviewers

Every lens has three positive and three negative controls. Cells show true positives / positive support, then false positives / negative support. Missing or incompatible outputs remain unavailable.

| Reviewer | Exact catalog | Grounded noul | Grounded binary choice |
| --- | --- | --- | --- |
| abstraction-architect:abstraction-architect-agent | 0/0 TP; 0/0 FP (0/6 available) | 3/3 TP; 3/3 FP (6/6 available) | 3/3 TP; 3/3 FP (6/6 available) |
| platform-engineering:platform-reviewer | 0/0 TP; 0/0 FP (0/6 available) | 3/3 TP; 2/3 FP (6/6 available) | 3/3 TP; 2/3 FP (6/6 available) |
| project-knowledge:doc-humanizer | 3/3 TP; 2/3 FP (6/6 available) | 1/3 TP; 1/3 FP (6/6 available) | 1/3 TP; 1/3 FP (6/6 available) |
| project-knowledge:documentation-engineer | 0/0 TP; 0/0 FP (0/6 available) | 1/3 TP; 1/3 FP (6/6 available) | 1/3 TP; 1/3 FP (6/6 available) |
| project-knowledge:guide-reviewer | 0/0 TP; 0/0 FP (0/6 available) | 0/3 TP; 0/3 FP (6/6 available) | 1/3 TP; 0/3 FP (6/6 available) |
| project-knowledge:instructions-auditor | 0/0 TP; 0/0 FP (0/6 available) | 0/3 TP; 2/3 FP (6/6 available) | 0/3 TP; 1/3 FP (6/6 available) |
| react-development:react-performance-optimizer | 0/0 TP; 0/0 FP (0/6 available) | 0/3 TP; 0/3 FP (6/6 available) | 0/3 TP; 0/3 FP (6/6 available) |
| repo-hygiene:workspace-auditor | 0/0 TP; 0/0 FP (0/6 available) | 0/3 TP; 0/3 FP (6/6 available) | 0/3 TP; 0/3 FP (6/6 available) |
| senior-review:api-contract-auditor | 3/3 TP; 3/3 FP (6/6 available) | 0/3 TP; 0/3 FP (6/6 available) | 0/3 TP; 0/3 FP (6/6 available) |
| senior-review:chicken-egg-detector | 2/3 TP; 3/3 FP (6/6 available) | 3/3 TP; 2/3 FP (6/6 available) | 3/3 TP; 2/3 FP (6/6 available) |
| senior-review:cleanup-auditor | 0/0 TP; 0/0 FP (0/6 available) | 3/3 TP; 3/3 FP (6/6 available) | 3/3 TP; 3/3 FP (6/6 available) |
| senior-review:code-auditor | 2/3 TP; 2/3 FP (6/6 available) | 3/3 TP; 3/3 FP (6/6 available) | 3/3 TP; 3/3 FP (6/6 available) |
| senior-review:data-integrity-auditor | 3/3 TP; 3/3 FP (6/6 available) | 3/3 TP; 1/3 FP (6/6 available) | 3/3 TP; 1/3 FP (6/6 available) |
| senior-review:distributed-flow-auditor | 0/0 TP; 0/0 FP (0/6 available) | 3/3 TP; 3/3 FP (6/6 available) | 3/3 TP; 3/3 FP (6/6 available) |
| senior-review:logic-integrity-auditor | 3/3 TP; 2/3 FP (6/6 available) | 0/3 TP; 2/3 FP (6/6 available) | 0/3 TP; 3/3 FP (6/6 available) |
| senior-review:premise-auditor | 0/0 TP; 0/0 FP (0/6 available) | 1/3 TP; 1/3 FP (6/6 available) | 1/3 TP; 1/3 FP (6/6 available) |
| senior-review:resource-lifecycle-auditor | 0/3 TP; 1/3 FP (6/6 available) | 2/3 TP; 3/3 FP (6/6 available) | 2/3 TP; 3/3 FP (6/6 available) |
| senior-review:security-auditor | 3/3 TP; 0/3 FP (6/6 available) | 2/3 TP; 2/3 FP (6/6 available) | 3/3 TP; 1/3 FP (6/6 available) |
| senior-review:temporal-resilience-auditor | 3/3 TP; 3/3 FP (6/6 available) | 3/3 TP; 2/3 FP (6/6 available) | 3/3 TP; 2/3 FP (6/6 available) |
| senior-review:ui-race-auditor | 0/0 TP; 0/0 FP (0/6 available) | 1/3 TP; 2/3 FP (6/6 available) | 2/3 TP; 3/3 FP (6/6 available) |
| testing:test-suite-auditor | 3/3 TP; 2/3 FP (6/6 available) | 1/3 TP; 0/3 FP (6/6 available) | 1/3 TP; 0/3 FP (6/6 available) |
| typescript-development:type-safety-auditor | 0/0 TP; 0/0 FP (0/6 available) | 3/3 TP; 0/3 FP (6/6 available) | 3/3 TP; 0/3 FP (6/6 available) |

The exact catalog preserves extracted frontmatter strings. Missing negative criteria and oversized options are recorded as input incompatibilities. Grounded variants are explicitly authored adaptations to the role bodies. The binary choice variant uses the same descriptions, independently for every reviewer; it does not force a team to contain one person.

## Selected teams

Each problem specifies mandatory and acceptable optional reviewers. Every other lens is forbidden within the stated scope. An acceptable team includes every mandatory lens and no forbidden lens. Exact-required equality additionally excludes optional additions; it is reported separately. A missing or partial decision cannot form a scored team.

| Variant | Acceptable teams | Exact required teams | Mandatory reviewers found | Out-of-scope selections | Total selected |
| --- | --- | --- | --- | --- | --- |
| grounded_noul | 0/12 | 0/12 | 25/39 | 102 | 140 |
| grounded_choice | 0/12 | 0/12 | 24/39 | 107 | 146 |

| Problem | Variant | Required found | Missing | Out-of-scope selections | Team acceptable |
| --- | --- | --- | --- | --- | --- |
| T01 | grounded_noul | 4/5 | senior-review:data-integrity-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:doc-humanizer, senior-review:cleanup-auditor, senior-review:resource-lifecycle-auditor, senior-review:ui-race-auditor, typescript-development:type-safety-auditor | False |
| T01 | grounded_choice | 4/5 | senior-review:data-integrity-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:doc-humanizer, react-development:react-performance-optimizer, senior-review:cleanup-auditor, senior-review:resource-lifecycle-auditor, senior-review:ui-race-auditor, typescript-development:type-safety-auditor | False |
| T02 | grounded_noul | 4/4 | none | platform-engineering:platform-reviewer, project-knowledge:guide-reviewer, project-knowledge:instructions-auditor, senior-review:chicken-egg-detector, senior-review:cleanup-auditor, senior-review:distributed-flow-auditor, senior-review:security-auditor, senior-review:ui-race-auditor | False |
| T02 | grounded_choice | 4/4 | none | platform-engineering:platform-reviewer, project-knowledge:documentation-engineer, project-knowledge:guide-reviewer, project-knowledge:instructions-auditor, senior-review:chicken-egg-detector, senior-review:cleanup-auditor, senior-review:data-integrity-auditor, senior-review:distributed-flow-auditor, senior-review:security-auditor, senior-review:ui-race-auditor | False |
| T03 | grounded_noul | 3/4 | senior-review:api-contract-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:guide-reviewer, senior-review:chicken-egg-detector, senior-review:cleanup-auditor, senior-review:data-integrity-auditor, senior-review:security-auditor, typescript-development:type-safety-auditor | False |
| T03 | grounded_choice | 3/4 | senior-review:api-contract-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:doc-humanizer, project-knowledge:guide-reviewer, senior-review:chicken-egg-detector, senior-review:cleanup-auditor, senior-review:data-integrity-auditor, senior-review:resource-lifecycle-auditor, senior-review:security-auditor, senior-review:temporal-resilience-auditor, typescript-development:type-safety-auditor | False |
| T04 | grounded_noul | 3/4 | senior-review:distributed-flow-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:guide-reviewer, senior-review:cleanup-auditor, senior-review:data-integrity-auditor, senior-review:security-auditor, senior-review:temporal-resilience-auditor, senior-review:ui-race-auditor | False |
| T04 | grounded_choice | 3/4 | senior-review:distributed-flow-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:guide-reviewer, senior-review:cleanup-auditor, senior-review:data-integrity-auditor, senior-review:security-auditor, senior-review:temporal-resilience-auditor, senior-review:ui-race-auditor | False |
| T05 | grounded_noul | 3/4 | react-development:react-performance-optimizer | abstraction-architect:abstraction-architect-agent, senior-review:cleanup-auditor, senior-review:distributed-flow-auditor, senior-review:temporal-resilience-auditor | False |
| T05 | grounded_choice | 3/4 | react-development:react-performance-optimizer | abstraction-architect:abstraction-architect-agent, senior-review:cleanup-auditor, senior-review:distributed-flow-auditor, senior-review:temporal-resilience-auditor | False |
| T06 | grounded_noul | 3/4 | senior-review:api-contract-auditor | platform-engineering:platform-reviewer, project-knowledge:documentation-engineer, senior-review:chicken-egg-detector, senior-review:cleanup-auditor, senior-review:data-integrity-auditor, senior-review:distributed-flow-auditor, senior-review:temporal-resilience-auditor | False |
| T06 | grounded_choice | 3/4 | senior-review:api-contract-auditor | platform-engineering:platform-reviewer, project-knowledge:documentation-engineer, senior-review:chicken-egg-detector, senior-review:cleanup-auditor, senior-review:data-integrity-auditor, senior-review:distributed-flow-auditor, senior-review:temporal-resilience-auditor | False |
| T07 | grounded_noul | 3/3 | none | platform-engineering:platform-reviewer, project-knowledge:doc-humanizer, project-knowledge:guide-reviewer, react-development:react-performance-optimizer, senior-review:chicken-egg-detector, senior-review:data-integrity-auditor, senior-review:distributed-flow-auditor, senior-review:resource-lifecycle-auditor, senior-review:security-auditor, senior-review:temporal-resilience-auditor | False |
| T07 | grounded_choice | 3/3 | none | platform-engineering:platform-reviewer, project-knowledge:guide-reviewer, react-development:react-performance-optimizer, senior-review:chicken-egg-detector, senior-review:data-integrity-auditor, senior-review:distributed-flow-auditor, senior-review:resource-lifecycle-auditor, senior-review:security-auditor, senior-review:temporal-resilience-auditor, senior-review:ui-race-auditor | False |
| T08 | grounded_noul | 1/2 | repo-hygiene:workspace-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, senior-review:chicken-egg-detector, senior-review:distributed-flow-auditor, senior-review:logic-integrity-auditor, senior-review:security-auditor, testing:test-suite-auditor | False |
| T08 | grounded_choice | 0/2 | repo-hygiene:workspace-auditor, senior-review:cleanup-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, senior-review:chicken-egg-detector, senior-review:distributed-flow-auditor, senior-review:logic-integrity-auditor, senior-review:security-auditor | False |
| T09 | grounded_noul | 0/1 | testing:test-suite-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:doc-humanizer, project-knowledge:guide-reviewer, senior-review:chicken-egg-detector, senior-review:cleanup-auditor, senior-review:data-integrity-auditor, senior-review:distributed-flow-auditor, senior-review:logic-integrity-auditor, senior-review:resource-lifecycle-auditor, senior-review:temporal-resilience-auditor, senior-review:ui-race-auditor, typescript-development:type-safety-auditor | False |
| T09 | grounded_choice | 0/1 | testing:test-suite-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:doc-humanizer, project-knowledge:guide-reviewer, senior-review:chicken-egg-detector, senior-review:cleanup-auditor, senior-review:data-integrity-auditor, senior-review:distributed-flow-auditor, senior-review:logic-integrity-auditor, senior-review:resource-lifecycle-auditor, senior-review:security-auditor, senior-review:temporal-resilience-auditor, senior-review:ui-race-auditor, typescript-development:type-safety-auditor | False |
| T10 | grounded_noul | 0/2 | project-knowledge:documentation-engineer, senior-review:premise-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, senior-review:chicken-egg-detector, senior-review:code-auditor, senior-review:data-integrity-auditor, senior-review:resource-lifecycle-auditor, senior-review:security-auditor, senior-review:temporal-resilience-auditor | False |
| T10 | grounded_choice | 0/2 | project-knowledge:documentation-engineer, senior-review:premise-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:instructions-auditor, senior-review:chicken-egg-detector, senior-review:code-auditor, senior-review:data-integrity-auditor, senior-review:resource-lifecycle-auditor, senior-review:security-auditor, senior-review:temporal-resilience-auditor | False |
| T11 | grounded_noul | 1/2 | project-knowledge:instructions-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:doc-humanizer, senior-review:api-contract-auditor, senior-review:chicken-egg-detector, senior-review:cleanup-auditor, senior-review:code-auditor, senior-review:distributed-flow-auditor, senior-review:resource-lifecycle-auditor, senior-review:security-auditor, senior-review:temporal-resilience-auditor, testing:test-suite-auditor | False |
| T11 | grounded_choice | 1/2 | project-knowledge:instructions-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, project-knowledge:doc-humanizer, senior-review:chicken-egg-detector, senior-review:cleanup-auditor, senior-review:code-auditor, senior-review:distributed-flow-auditor, senior-review:resource-lifecycle-auditor, senior-review:security-auditor, senior-review:temporal-resilience-auditor, testing:test-suite-auditor | False |
| T12 | grounded_noul | 0/4 | project-knowledge:doc-humanizer, project-knowledge:documentation-engineer, project-knowledge:guide-reviewer, senior-review:premise-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, react-development:react-performance-optimizer, senior-review:chicken-egg-detector, senior-review:code-auditor, senior-review:logic-integrity-auditor, senior-review:resource-lifecycle-auditor, senior-review:security-auditor, senior-review:ui-race-auditor, testing:test-suite-auditor | False |
| T12 | grounded_choice | 0/4 | project-knowledge:doc-humanizer, project-knowledge:documentation-engineer, project-knowledge:guide-reviewer, senior-review:premise-auditor | abstraction-architect:abstraction-architect-agent, platform-engineering:platform-reviewer, react-development:react-performance-optimizer, senior-review:chicken-egg-detector, senior-review:code-auditor, senior-review:logic-integrity-auditor, senior-review:resource-lifecycle-auditor, senior-review:security-auditor, senior-review:ui-race-auditor | False |

## Evidence and limits

[Frozen suite](runs/20261020T-all-reviewers/suite.json) contains each expected answer, source locator and rationale. [Inventory](runs/20261020T-all-reviewers/inventory.json) classifies all registered roles. [Scoring JSON](runs/20261020T-all-reviewers/scores.json) retains every selected team and individual confusion counts. The run also preserves exact requests, actual submitted payloads, raw outputs, encoding diagnostics and model identity.

These few controls per role expose failures and coverage gaps; they cannot certify production reliability. Team labels are explicit scope judgments, not exhaustive universal truths about reviewer usefulness. A role may be relevant to multiple artifacts; optional eligibility prevents treating every reasonable extra reviewer as a proven error. Actual review effectiveness, runtime savings and net token economics remain unmeasured.

Rebuild without inference:

```powershell
python -B evals/senior-review/choicer-eval/all_reviewers_eval.py report
```
