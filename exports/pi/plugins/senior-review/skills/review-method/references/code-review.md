## Step 3: Run Parallel Review Agents

Use the host coordination mechanism to dispatch the selected roles in isolated contexts.

### Shared Instructions for All Agents

Include these instructions in every agent prompt:

```
## Intent
[paste the 2-3 line intent summary from Step 1b]

## Diff Scope & Pre-existing Classification

Classify every finding into one of three tiers:

- **Primary** -- lines added or modified in the diff. Your main focus. Full confidence.
- **Secondary** -- unchanged code in the same function/block as a changed line. Report
  if the diff makes the issue newly relevant, noting the interaction.
- **Pre-existing** -- issues in unchanged code unrelated to the diff. Mark these with
  `[PRE-EXISTING]` prefix. They are reported separately and do NOT count toward the verdict.

Rule: if you'd flag the same issue on an identical diff without the surrounding file,
it's pre-existing. If the diff makes it newly relevant, it's secondary.

## Premise declaration (required on every finding)

Every finding carries two extra fields:

- **Load-bearing premise:** the single proposition whose falsity collapses this
  finding. It must be minimal, falsifiable and scoped.
    Bad:  "The implementation is broken."
    Bad:  "Heartbeat handling is incorrect."   (a paraphrase of your finding)
    Good: "No credential-bearing response path exists after registration."
- **premise_provenance:** one of `independent`, `shared-context`, `mixed`.
  This records CAUSAL DEPENDENCE, not citation. If you absorbed the premise from
  the X-ray output or the interconnect map, it is `shared-context`, even if
  your finding never cites an anchor. `mixed` means part of the premise rests on
  shared context and part on evidence you derived yourself. Declare `independent`
  only when you re-derived the whole premise from code, tests or documents you
  read yourself.
```

Run all selected agents **in parallel** in a single response; conditional agents run only when their dispatch condition matches:

### Dispatch table

The core spawn prompts live in the `senior-review:review-quality-gates` skill,
file `references/code-review-agents.md` (resolve it inside that skill's installed
directory). Stack bindings and inputs come from review-preparation's
`references/stack-dimensions.md`; their prompts remain in their canonical role
definitions. Dispatch the complete prepared selection once, using the shared
instructions above for every reviewer.

| Agent | Dimension | role | Run when |
|-------|-----------|---------------|----------|
| A | Code audit: architecture, failure flow, patterns, scoring | `senior-review:code-auditor` | Always |
| B | Security | `senior-review:security-auditor` | Always |
| B2 | Dead code, unused parameters, VCS hygiene (lite, diff-scoped, rules from `repo-hygiene`) | `general-purpose` | Always |
| C | UI race conditions | `senior-review:ui-race-auditor` | Changed files include UI/frontend code (`.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`, `.qml`, or scroll/focus/layout manipulation) |
| E | Git blame and history | `general-purpose` | Always |
| F | Testing quality | `testing:test-suite-auditor` | Diff touches test files |
| G | API contracts | `general-purpose` | Diff touches API-related files (routes, serializers, OpenAPI/GraphQL/proto specs, DTOs) |
| H | Data migrations | `general-purpose` | Diff touches migration files |
| J | Structural entropy (duplicated knowledge, competing owners, redundant representation, derivable state, missed unification, prior art, abstraction fitness) | `abstraction-architect:abstraction-architect-agent` | Diff adds at least one function/method/class/module/constant table or 5+ line block |
| L | Temporal resilience (failure-over-time) | `senior-review:temporal-resilience-auditor` | Diff touches timers, schedulers, polling, retry/reconnect, cron, queue workers, daemons, updaters, watchdogs |
| M | Data integrity (persistence semantics) | `senior-review:data-integrity-auditor` | Diff touches schemas, models, ORM, raw SQL, caches, or transaction boundaries |
| N | Resource lifecycle (ownership and release) | `senior-review:resource-lifecycle-auditor` | Diff acquires files, sockets, connections, subprocesses, listeners, locks, tasks, or timers |

Add the selected stack dimensions to these core slots in the same batch. Testing,
structural entropy and stack specialists use required external providers. Skip
only on absent code signals or an explicit reviewer scope; declare unknown signals
as gaps. A failed binding is a failed delivery, never an omitted dimension.

---
