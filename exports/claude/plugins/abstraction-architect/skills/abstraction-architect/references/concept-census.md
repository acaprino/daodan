<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# The Concept Census

The census is what makes D1 through D4 possible. Without it the agent can only compare shapes, and comparing shapes finds the wrong things: identical status enums in two bounded contexts look like a defect, and one policy written three different ways looks like nothing at all.

## The rule that governs the whole method

> `precision over recall` governs what is **reported**, not what is **searched**.

Discovery is deliberately liberal. Promotion to a finding is deliberately strict. Conflating the two is how an auditor ends up not searching at all, which is the defect this method replaces.

```
DISCOVERY                    liberal Glob and Grep, many candidates, cheap
      |
      v
CONTEXT VERIFICATION         read the definitions, the writers, the consumers
      |
      v
SEMANTIC TEST                same concept? same authority? same lifecycle? same boundary?
      |
      v
FINDING                      only here does precision apply
```

## Phase 1: the seed map

Read the supplied bound run's phase files and extract the territory: modules, responsibilities, entities and domain concepts, services, persistence, configuration, boundaries, principal flows, public interfaces. Retain its run and snapshot identity; the root mirror is not this input.

The census is seeded by this map on purpose. Beginning by sweeping eighty thousand files at random produces order-dependent coverage and burns the budget before reaching the interesting part.

**The seed map's completeness is not a premise.** Extraction starts from it and is not limited by it. A module Codebase Map did not surface is a gap in the census, and the census may add concepts the map never named. There is no rule of the form "do not search where the map says nothing".

## Phase 2: concept extraction

From the seed map, derive two kinds of concept.

**Entity concepts**, the domain nouns:

```
Customer  Order  Payment  Subscription  Permission  Refund  Price  Status  Tenant  Feature
```

**Behavioural concepts**, which are the ones a noun-only census misses and which carry most of the D1 findings:

```
eligibility  approval  normalization  calculation  expiration
validation   mapping   defaulting     derivation
```

A policy such as "orders above a threshold need approval" is an *approval* concept. It has no single noun and no single home, which is exactly why it ends up written three times.

## Phase 3: discovery

For each concept, search for its **representations**, not for its name. Four search families, run together, because each alone produces false negatives.

**By name and near-synonym.** For a `subscription status` concept:

```
SubscriptionStatus   subscription_state   plan_status
isActive   enabled   expiresAt > now   ACTIVE = "active"
```

**By literal.** Thresholds, magic numbers, regexes, endpoint paths, env var names, error strings, header names, date windows. Copy-paste survives renaming; literals do not change. This is the family that finds `30` in three files and `1000` in three others.

**By call.** The same external call with the same parameters: same SDK method, same table, same queue, same config key.

**By shape of decision.** Predicates over the same field, comparisons against the same bound, branches keyed on the same enum. This family finds the policy that was reimplemented rather than copied.

Record every hit. A hit is a candidate, never a finding.

## The Concept Evidence Index

Discovery produces one entry per concept. The persisted form is defined in `references/concept-index-protocol.md`; this is the shape to think in:

```
Concept: Refund eligibility
Kind: policy

Representations:
  RefundPolicy.can_refund              domain/refund_policy.py   candidate_owner
  SupportRefundService.is_eligible     support/refunds.py        implementation
  REFUND_WINDOW_DAYS                   config/refunds.py         parameter
  Order.refundable_until               domain/order.py           derived_field

Writers:    RefundPolicy, AdminRefundSettings
Consumers:  checkout, support-api
Canonical owner:  ambiguous

Evidence:
  same 30-day policy confirmed in three contexts
  support implementation bypasses RefundPolicy
```

With this in hand the agent can reason about ownership. Without it, the best available move is "grep magic numbers, found 30 three times, report it", which is the behaviour this method exists to replace.

## Phase 4: hypothesis testing

For each concept with more than one representation, assign the track, run the dimension gate from `references/evidence-tracks.md`, apply the four lenses from `references/dimensions.md`, and classify to a single primary dimension.

A concept with one representation is not a finding. It is the healthy case, and the index records it so the next run can tell when a second appears.
