<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

# Billing Meters (Usage-Based Billing)

Modern usage-based billing primitive. The legacy `usage_type=metered` + `SubscriptionItem.create_usage_record` flow was **removed** in API version `2025-03-31.basil`. On any newer version, metered prices must be backed by a Meter.

## When to use

Bill by API calls, seats, GB stored, generated tokens, or any metric that aggregates per billing period. Skip if you bill a flat subscription or per-item one-off charges -- a plain `Price` is enough.

## The 3-object mental model

1. **Meter** -- defines an `event_name` and aggregation (`sum`, `count`, `last_during_period`). The `max` aggregation from the legacy API has no equivalent.
2. **Price** -- a recurring Price with `recurring.meter` pointing at the meter ID.
3. **MeterEvent** -- reported as usage happens, identified by `stripe_customer_id` in the payload (not subscription-item id like the legacy API).

## Gotchas

- **Idempotency is explicit via `identifier`.** Always send one; Stripe dedupes `(event_name, identifier)` pairs. Retries without an identifier double-count.
- **Backfill window is ~35 days.** Later corrections need `MeterEventAdjustment` with `type=cancel`.
- **`event_name` is immutable** after creation. Pick stable domain nouns (`api_request`, `seat`, `gb_stored`).
- **Events for customers without an active meter-backed subscription are accepted but not invoiced.** Useful for "report early, bill later" flows.
- **High throughput (>1k events/sec)** uses the V2 `/v2/billing/meter_events` stream; trades sync validation for up to 10k/sec.
- **Webhooks worth subscribing to:** `v1.billing.meter.error_report_triggered` (validation failures), `v1.billing.meter.no_meter_found` (typos in event_name).

## Migration from legacy usage records

Map `SubscriptionItem.create_usage_record(si_xxx, quantity=150, ...)` to `stripe.billing.MeterEvent.create(event_name=..., payload={stripe_customer_id, value: "150"}, identifier=...)`. Key differences: customer-addressed instead of subscription-item-addressed, explicit `identifier` instead of implicit timestamp idempotency, no `max` aggregation. For in-flight subscriptions, use subscription schedules to phase onto the meter-backed price at period end.

## Official docs

- Overview: https://docs.stripe.com/billing/subscriptions/usage-based
- Implementation guide (canonical code samples): https://docs.stripe.com/billing/subscriptions/usage-based/implementation-guide
- Recording usage: https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api
- Migration from legacy: https://docs.stripe.com/billing/subscriptions/usage-based-legacy/migration-guide
- API reference (Meter): https://docs.stripe.com/api/billing/meter
- API reference (MeterEvent): https://docs.stripe.com/api/billing/meter-event
- Breaking change notice: https://docs.stripe.com/changelog/basil/2025-03-31/deprecate-legacy-usage-based-billing

## Related

- `webhooks-production.md` -- `v1.billing.meter.*` events
- `usage-revenue-modeling.md` -- modeling usage distributions for pricing
