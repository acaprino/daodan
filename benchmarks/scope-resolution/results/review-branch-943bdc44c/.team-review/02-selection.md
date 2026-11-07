# Selection

Review `branch-943bdc44c`, candidate 943bdc44c, base 6dd2c2bbf. Tier and verification policy from `ROSTER.json` (small, `high-and-above`, no critic). Catalog: `CATALOG.json` (50 entries, plugin.toml sha256 `761565841a6c8670...`). Bound plan: `PREPARED-REVIEW.json`.

## Questions
| Id | Question | Reference | Control | Status |
|---|---|---|---|---|
| Q1 | Does `compute_total` still compute "netto - sconto cliente + IVA" for `loyalty_percent` != 0, or subtract the discount twice? | 01-context.md H1, S8, D1-D3, D6 | `senior-review:local-correctness-auditor` (arithmetic against the local docstring contract, callers) | assigned to job-01 |
| Q2 | Is VAT still computed on the intended taxable base? | 01-context.md H2, D2 | `senior-review:local-correctness-auditor` (values, units) | assigned to job-01 |
| Q3 | For which inputs does the new net become negative, and what do checkout and the ledger record? | 01-context.md H3, D1, D4 | `senior-review:local-correctness-auditor` (bounds, zero/max, returned outcome) | assigned to job-01 |
| Q4 | What do the consumers of `compute_total` observe, and does any other consumer depend on it? | 01-context.md S2, S3, S7, D4, D5, H4 | `senior-review:local-correctness-auditor` (relevant callers, returned outcome to the caller) | assigned to job-01; cross-component domain-rule ownership is a selection gap (see logic-integrity below) |

## Baselines
| Stack | Control | Status |
|---|---|---|
| python | none in the catalog: former python-development methods are unavailable (review-preparation `references/stack-dimensions.md`) | baseline missing: python |

## Candidates

Shortlist from the triggers in the role descriptions against the changed lines (one arithmetic expression on a dict value with two calls to a pure function, `A/orders/pricing.py:19`) and Q1-Q4. Bodies read only for the shortlisted candidates.

| Candidate | Body read | Decision | Reason |
|---|---|---|---|
| senior-review:local-correctness-auditor | yes (`roles/local-correctness-auditor.md`, sha256 `4fd495dcbc019bfe...`) | applicable: Q1, Q2, Q3, Q4 | Mandate "observable wrong behavior in the local contract using independent requirements and callers"; causal checks cover arithmetic, units, bounds incl. zero/max and returned outcomes. |
| senior-review:logic-integrity-auditor | yes (`roles/logic-integrity-auditor.md`) | applicable: Q1, Q4 (L4 money rule across checkout and ledger) | Not in the computed roster (small tier) and not a member of `senior-review:code-auditor`: selection gap, not dispatched. Its local part (the docstring rule of `compute_total`) is covered by local-correctness on Q1. |
| senior-review:data-representation-auditor | yes (`roles/data-representation-auditor.md`) | not applicable | No change to stored representation, rounding, units or conversion: `ledger.record` writes `{total}` unchanged (`A/orders/ledger.py:18`); the role routes domain interpretation to logic-integrity. |
| senior-review:api-contract-auditor | yes (`roles/api-contract-auditor.md`, head) | not applicable | No declared boundary (schema, validator, serializer, DTO); `compute_total` signature is unchanged (diff S8); the docstring promise is the local contract owned by local-correctness. |
| senior-review:premise-auditor | yes (support role) | support only | Lens 0 in Phase 4b; not a discovery control. |
| local-concurrency, input-validation, resource-lifecycle, algorithmic-cost, chicken-egg-detector, temporal-resilience | no | not shortlisted | Changed line has no shared state, new input sink, acquired resource, loop/cost change (one extra O(1) pure call), startup step or timer. |
| security members: authorization, session-delegation, secret-exposure, untrusted-resource, browser-security, callback-authenticity, ai-boundary, audit-trail, capacity-quota | no | not shortlisted | No credential, permission, secret, path/URL, markup, callback signature, model output, audit attribution or quota in the changed line. |
| data-integrity members: transaction-integrity, schema-coherence, cache-consistency, data-retention | no | not shortlisted | No transaction boundary, schema, cache or retention path touched; the ledger write is unchanged. |
| distributed-flow members: message-delivery, remote-effect, service-resilience, environment-binding | no | not shortlisted | No broker, remote call, service timeout or environment binding in the changed line. |
| other catalog roles (accessibility, performance, operability, cleanup, ui-race, dependency-usage and their members) | no | not shortlisted | Outside the roster; no UI, perf-measured path, operations, dead code, UI timing or manifest in the diff. |

## Jobs
| Job | Questions | Reviewer | Reason for a separate job |
|---|---|---|---|
| job-01 | Q1, Q2, Q3, Q4 | `senior-review:code-auditor` (bound role); selected member `senior-review:local-correctness-auditor` | Single job: all questions share one context (one function, its two callees and its one caller). No second job: no separate context, uncovered competence or justified independent verification. |

## Gaps
- **Composition:** `composition.py bind` binds job-01 with all 26 leaf members of `senior-review:code-auditor` (computed-roster and code-review floor); it reads no Step 3 selection and the roster applicability rows cannot narrow a roster identity's own members. The worker applies the selected member's checks and records the other 25 members against the reasons above.
- **Selection:** logic-integrity-auditor applicable but outside the roster (above).
- **Baseline missing: python.**
