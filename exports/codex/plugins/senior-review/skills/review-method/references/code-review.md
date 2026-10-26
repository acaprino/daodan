<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

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
  the Codebase Map output or the interconnect map, it is `shared-context`, even if
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
| B2 | Dead code, unused parameters, VCS hygiene (lite, diff-scoped, rules from `repo-hygiene`) | `project-protocol:isolated-worker` | Always |
| C | UI race conditions | `senior-review:ui-race-auditor` | Changed files include UI/frontend code (`.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`, `.qml`, or scroll/focus/layout manipulation) |
| E | Git blame and history | `project-protocol:isolated-worker` | Always |
| F | Testing quality | `testing:test-suite-auditor` | Diff touches test files |
| G | API contracts | `project-protocol:isolated-worker` | Diff touches API-related files (routes, serializers, OpenAPI/GraphQL/proto specs, DTOs) |
| H | Data migrations | `project-protocol:isolated-worker` | Diff touches migration files |
| J | Structural entropy (duplicated knowledge, competing owners, redundant representation, derivable state, missed unification, prior art, abstraction fitness) | `abstraction-architect:abstraction-architect-agent` | Diff adds at least one function/method/class/module/constant table or 5+ line block |
| L | Temporal resilience (failure-over-time) | `senior-review:temporal-resilience-auditor` | Diff touches timers, schedulers, polling, retry/reconnect, cron, queue workers, daemons, updaters, watchdogs |
| M | Data integrity (persistence semantics) | `senior-review:data-integrity-auditor` | Diff touches schemas, models, ORM, raw SQL, caches, or transaction boundaries |
| N | Resource lifecycle (ownership and release) | `senior-review:resource-lifecycle-auditor` | Diff acquires files, sockets, connections, subprocesses, listeners, locks, tasks, or timers |

Add the selected stack dimensions to these core slots in the same batch. Testing,
structural entropy and stack specialists use required external providers. Skip
only on absent code signals or an explicit reviewer scope; declare unknown signals
as gaps. A failed binding is a failed delivery, never an omitted dimension.

---
