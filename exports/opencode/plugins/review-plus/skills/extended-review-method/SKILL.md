---
name: extended-review-method
description: >
  Extend universal review with mandatory signal-selected specialist roles, without copying the senior engine.
---

# Extended review

Input: `variant=code-review|team-review|pr-review`, target, original senior flags
and output root. Output: the native senior report with extended coverage.

The entry's dispatch inventory exposes both extension roles and the roles used
by the canonical senior methods. This declares available bindings and isolation;
it does not copy the senior phase graph or re-run its prompts. Inline verification,
criticism and fix tasks use the canonical `project-protocol:isolated-worker`
binding. Required provider dependencies make every declared binding concrete.

1. Load the `senior-review:review-preparation` skill once. Its exact snapshot, brief and
   shared context are inputs to every specialist and to the universal engine.
2. Select zero or one worker per dimension using the table below. A false signal
   yields an empty selection and a recorded reason. A matching signal always
   dispatches the installed role; failure yields failed delivery and degraded coverage.
3. Dispatch each selected specialist in its own isolated context. Use that role's
   existing method and the senior prepared brief, diff, context provenance, target
   instructions and native finding fields. Load the `senior-review:review-quality-gates` skill
   for the shared-context premise and quantitative evidence rules. No copied role
   prompt lives here. Require file:line evidence and premise provenance on findings.
4. Join all three specialist deliveries, including explicit failed/empty results.
   Load the `senior-review:review-method` skill with `prepared` and `extension_results` plus
   their native delivery ledger. The same final consolidation/panel/report handles
   core and specialist findings; never publish a second report or run preparation twice.

| Selection | Signal | Existing role |
|---|---|---|
| react | React in the relevant package and target includes JSX/TSX or affected React runtime | `react-development:react-performance-optimizer` |
| typescript | Relevant TypeScript configuration and target includes TS/TSX/type contracts | `typescript-development:type-safety-auditor` |
| platform | At least two verified frontend, backend, API-route, multiple-service or desktop-shell integration signals | `platform-engineering:platform-reviewer` |

The three plugins are mandatory dependencies. Selections describe the code, never
installation. Report the core and extension dimension sets and all missing evidence.
