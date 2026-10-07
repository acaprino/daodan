# Stack dimensions

Use the resolved target, relevant package configuration and exact candidate
snapshot. Inspect the affected package in a monorepo; unrelated root dependencies
are not an activation signal. Add these bindings to the native reviewer selection
alongside the other dimensions. There is one dispatch round and one delivery ledger.

| Dimension ID | Automatic activation evidence | Canonical role |
|---|---|---|
| react | React in the relevant package and target includes JSX/TSX or affected React runtime | `react-development:react-performance-optimizer` |
| typescript | Relevant TypeScript configuration and target includes TS/TSX/type contracts | `typescript-development:type-safety-auditor` |
| platform | At least two verified frontend, backend, API-route, multiple-service or desktop-shell integration signals relevant to the target | `platform-engineering:platform-reviewer` |

Select each dimension once. A false signal records a code-based skip reason. An
unreadable or ambiguous signal records a coverage gap; it is not evidence of
inapplicability. Required provider dependencies supply the roles regardless of
selection. A matched role that cannot run is a failed delivery, never a clean skip
or a generic substitute.

Respect team review's explicit --reviewers selection and --all override. Record
manual selection as activation evidence, including the lack of an automatic
signal when appropriate. Normalize legacy selectors before applying that scope:
react-perf/react-performance select react, and ts-safety/type-safety select
typescript. An explicit performance selector resolves to react when the relevant
React signal is verified; otherwise it selects the existing general-performance
dimension, with a React coverage gap if applicability is unknown. Do not dispatch
both performance bindings for that one selector. Architecture review remains a
separate dimension even when it shares the general code-auditor role. Record the
requested spelling and resolved dimension in the plan.

--no-context removes shared context from these workers
as it does from other reviewers; it does not remove the dimensions. --fast changes
verification cost, not which applicable specialists are selected.

The canonical roles retain their own knowledge, analysis method and native output.
Before dispatch, load review-consolidation's `references/stack-findings.md` inside
that skill. Include its native review field requirements and severity mapping in
the brief, alongside the role's own report format. Preserve the original report;
the existing evidenced-finding envelope carries the fields required by this review.
Supply the prepared target, diff, intent, project instructions, run identity,
snapshot and assigned intermediate report path. Add the variant's shared scope
and premise-provenance instructions from review-method and review-quality-gates;
include context paths only when context is enabled. Quantitative performance
claims need the evidence required by review-quality-gates. Missing runtime
measurements remain gaps, not invented results.

Dispatch these reviewers with the other selected dimensions in isolated contexts.
Do not run their standalone workflows, repeat preparation or publish another
report. Consolidation waits for every selected reviewer to deliver or fail, and
preserves source role, severity, evidence and premise provenance in the same native
finding set. Independent reviewers do not receive peer findings before delivery.
