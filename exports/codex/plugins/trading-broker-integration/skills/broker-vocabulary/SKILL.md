---
name: broker-vocabulary
description: >
  Vendor-neutral vocabulary for programmatic broker integration: the five access archetypes, the
  second axis separating a single broker from a multi-broker platform, the reference order state
  machine, session and recovery, and the evidence ladder that decides what a claim about a venue is
  worth.
  TRIGGER WHEN: comparing brokers or integration paths, starting an integration against a broker with
  no dedicated skill, or naming what kind of access path a system uses.
  DO NOT TRIGGER WHEN: the question is about one specific broker that has its own skill (use the ibkr
  or mt5 skill), or about strategy, backtesting, or portfolio construction.
---

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

# Broker Connectivity

The vocabulary that is the same for every broker. Use it to name what kind of access path a system has,
to model an order's life without borrowing one vendor's words for it, and to say what a claim about a
venue is actually worth.

It exists because broker knowledge is written per vendor and therefore reads as if every problem were
unique. Most are not. Session exclusivity, a login built for a human, a connection flag that lies, a
place call that proves nothing, and a fact everybody repeats that nobody measured are properties of the
access path, and they recur across brokers that share nothing else.

## The five archetypes

| Archetype | Meaning |
|---|---|
| `direct-api` | A cloud API. No vendor component on your machine |
| `local-terminal` | A vendor application runs locally, holds the session, and may handle orders itself |
| `vendor-gateway` | A vendor-operated gateway or protocol engine, usually behind certification |
| `bridge` | Third-party software between a platform and a broker, operated by neither |
| `in-platform` | Code running inside the vendor's own application |

Name the archetype before designing anything. It decides what must run, what dies with what, and which
recovery story is available to you. A vendor is not an archetype: the same broker can be `direct-api`
for one product and `local-terminal` for another (`access-archetypes.md` has IBKR as its own
counterexample), so state the archetype of the path you are on, not the vendor's name. With that
caveat, Interactive Brokers and MetaTrader 5 are both `local-terminal` on the paths this marketplace
documents, which is why their operational problems are the same problems. Sharing an archetype
transfers operational lessons; it does not transfer facts.

A second axis, independent of the archetype, separates a `single-broker` subject from a
`multi-broker-platform` one sitting many independent brokers behind the same software. IBKR is
`single-broker` and MetaTrader 5 is `multi-broker-platform`, and a fact measured on one broker is not
even guaranteed to hold for the next broker on the same platform.

## Evidence

Claims about venue behaviour are ranked on an evidence ladder, from your own probe transcript down to
a search-engine or AI summary that is not evidence at any strength. The ladder has **six ranks**, and
every claim about broker behaviour in a repository carries one of three provenance tags: `MEASURED`,
`DOCUMENTED` or `ASSUMED`.

## Reference materials

- `access-archetypes.md`: the five archetypes, what changes between them (session state, blast radius,
  what you must keep alive, the failure surface each adds), the second axis separating a single
  broker from a multi-broker platform, and where the two integrated brokers sit on both
- `order-lifecycle-reference-model.md`: the reference state machine keyed on who has acknowledged what,
  the three layers that can refuse an order, the three identifiers and what survives a cancel or a
  replace, what a successful place call proves, and how to map a vendor's vocabulary onto this one
- `session-and-recovery.md`: the three session-exclusivity regimes, authentication with no human in the
  loop, the connection flag that lies, reconciling ground truth after a gap, and what must be persisted
- `evidence-and-probes.md`: the evidence ladder, the provenance tags, how to design a probe that
  answers something, and the question classes a demo environment cannot settle

## Adding a vendor skill

A new vendor skill in this plugin (alongside `ibkr` and `mt5`) earns its place by using this
vocabulary rather than reinventing one. It should carry four sections, in the shape the two
existing vendor skills already use: **Quick start** (the handful of decisions that get someone
running today), **Key decision points** (default versus when to deviate, as a table), **Symptoms
to entry points** (a table from what a user is seeing to the reference file that explains it),
and **Reference materials** (what each reference file covers, so a reader can pick the right one
without opening several).

Two things carry across every vendor skill regardless of section structure. First, state
provenance on any fact that matters: whether it was measured against a real account, read and
quoted from documentation, or assumed. An unmarked claim reads as more certain than it is, and
the reader has no way to tell a fact worth trusting from one worth re-checking. Second, map the
vendor's own order-state and order-type vocabulary onto `order-lifecycle-reference-model.md`'s
names, explicitly, rather than silently writing in the vendor's words and leaving the reader to
translate. `ibkr` and `mt5` both carry a table doing exactly this; follow their shape.
