---
name: broker-vocabulary
description: >
  Vendor-neutral broker integration vocabulary: the five archetypes, single-broker vs multi-broker platforms, order state machine, session recovery and evidence ladder.
  TRIGGER WHEN: comparing brokers or integration paths, integrating a broker without a dedicated skill, or classifying an access path.
  DO NOT TRIGGER WHEN: targeting a broker with its own skill (use ibkr or mt5).
---

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
