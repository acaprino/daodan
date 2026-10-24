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

<!-- Generated dispatch body. Owner: react-development:react-performance-optimizer; version: 2.2.0; source-sha256: 9f3aebbb2ea95bcec0c7bb7c2718301214cce8aa868f86e41031a0a6f2f41a17. Edit the owner's kernel, never this resource. -->

This body belongs to `react-development`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<react-development-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `react-development`. The owning plugin's declared logical skill identities are `react-development:react-best-practices`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Specialist `react-development:react-effects-auditor`

Provider `react-development` owns these instructions and unqualified skills. Resolve `<react-development-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# React effect synchronization



## Mandate and input

Require installed React/hooks version, reactive values, component lifetime and external subscription contracts. Read relevant rules under `<react-development-plugin-root>/skills/react-best-practices/rules/`: `advanced-*`, `client-event-listeners`, `js-tosorted-immutable`, `rerender-dependencies`, `rerender-derived-state-no-effect`, `rerender-functional-setstate`, `rerender-move-effect-to-event`. Use the effect/teardown sections of `references/react19-stores-and-effects.md` in that skill when needed; examples are leads, not automatic defects.

## Causal checks

- Trace effect/callback dependencies and state writes to prove self-sustaining re-entry or stale closures. Distinguish synchronization from user actions and derived render values; inspect remount and development replay against the intended lifetime.
- Follow timers, events, sockets, channels, fetch/IPC completion and manual store subscriptions through dependency replacement and unmount. Verify unsubscribe, cancellation or stale-result suppression actually prevents the required consequence; not every API accepts AbortController.
- Preserve reactive dependencies. Effect Events read latest committed values in supported versions, but are not general stable callbacks or a way to hide dependencies. Ref-based or resubscription designs can be valid.
- Check shared listeners, functional updates and state/props mutation, including sort, against ownership and observable behavior.

## Counterevidence and boundaries

A mount state update does not alone prove a loop; stable snapshots, teardown, invalidation and legitimate remount initialization can refute it. Do not demand a ref guard, Effect Event or one library. General races, persistent state and static CSS belong to adjacent owners; React-caused effect lifecycle remains here.

## Delivery

Identify reactive trigger → closure/dependency/lifetime → observable consequence, effective cleanup and counterevidence. Keep static reasoning separate from React/runtime traces; suggest minimal existing mechanism.

## Specialist `react-development:react-render-cost-auditor`

Provider `react-development` owns these instructions and unqualified skills. Resolve `<react-development-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# React rendering and work cost



## Mandate and input

Require component/store topology, React/compiler/store versions, rendered data cardinality, interaction requirements and supplied profiling or budgets. Under `<react-development-plugin-root>/skills/react-best-practices/rules/`, inspect applicable `js-*` except `js-tosorted-immutable`, `rendering-*` except `rendering-resource-hints`, and render-focused `rerender-*` (effect dependencies/actions/derived-effect/functional-update belong to react-effects-auditor). Include `client-passive-event-listeners`; use selector templates in that skill’s `references/react19-stores-and-effects.md` on demand.

## Causal checks

- Follow whole-store versus leaf/derived subscriptions, fresh selector results, equality checks and memoized selector lifetime. Compiler optimization does not prove external snapshot stability; establish actual notifications and renders.
- Check component/key identity, inline definitions, list virtualization/item IDs, state initializers, callback/default-prop identity, split computations, transient refs and urgent versus deferrable updates. Preserve required state and interaction responsiveness.
- Check server/client hydration, conditional zero rendering, visibility/state retention, SVG/layout work and script order. React-owned read/write alternation is in scope; static layout policy is adjacent.
- Derive repeated work from calls and input size: storage/property/function caching, scans/indexes, set/map lookups, regex creation, allocation, early exit and min/max sorting. Assess cache invalidation, memory and supported APIs before proposing changes. Read/write batching, idle scheduling and passive listeners must preserve input behavior.

## Counterevidence and boundaries

No technique, memo, virtualizer, numeric row threshold, compiler flag or 200KB/16ms target is universally required. Stable object selectors, bounded cheap work, necessary preventDefault, manual loading and intentional hydration differences can be valid. Require an evidenced consequence or agreed budget; historical percentage claims are not measurements.

## Delivery

Report changed identity/subscription/work, triggering frequency/cardinality, affected state or interaction and causal estimate versus supplied measurement. Keep performance, functional loss and absent runtime evidence distinct.

## Specialist `react-development:react-bundle-auditor`

Provider `react-development` owns these instructions and unqualified skills. Resolve `<react-development-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# React module and resource delivery



## Mandate and input

Require entry/route graph, bundler version/configuration, package exports/sideEffects, feature lifetime and supplied chunk/artifact evidence. Read applicable `bundle-*` and `rendering-resource-hints` rules under `<react-development-plugin-root>/skills/react-best-practices/rules/`; use the bundling section in that skill’s `references/react19-stores-and-effects.md` when needed.

## Causal checks

Trace initial versus conditional imports, namespace/barrel reexports, static analyzability, server tracing, dynamic chunks and third-party initialization to what actually ships or loads. Check legitimate package exports before deep imports. Assess lazy loading, preload on intent, route/manual chunk interactions and React DOM resource hints against startup needs, required monitoring and request duplication. A lazy boundary still needs loading/error behavior and permitted SSR semantics.

## Counterevidence and boundaries

Tree shaking, externalization, build transforms and required first-render work can refute an eager-cost claim. Library names, import style and a reference’s historical byte/time estimates are leads only. Do not install analyzers or build without explicit permission; supplied reports prove only their own candidate. Route data-cache freshness and gcTime to react-dataflow-auditor, virtualization to react-render-cost-auditor.

## Delivery

Report entry → dependency → emitted/requested resource, required versus avoidable work, package/version and actual measurement or bounded derivation. Preserve output coverage and unavailable artifact/runtime evidence.

## Specialist `react-development:react-dataflow-auditor`

Provider `react-development` owns these instructions and unqualified skills. Resolve `<react-development-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# React request and server/client dataflow



## Mandate and input

Require framework/server runtime versions, request/tenant identity, data dependencies, client/server boundaries and freshness/lifetime requirements. Under `<react-development-plugin-root>/skills/react-best-practices/rules/`, read applicable `async-*`, `server-*`, `client-localstorage-schema` and `client-swr-dedup`. Authentication in `server-auth-actions` is routed to authorization review; do not omit the lead. Use Suspense/Query guidance in that skill’s `references/react19-stores-and-effects.md` as versioned examples.

## Causal checks

- Build the real dependency graph for route/component/nested fetches. Distinguish necessary sequencing from independent work and branch-unused awaits; use existing promises before adding a dependency. Check Suspense streaming, pending/error paths and post-response work against lifetime guarantees.
- Trace per-request deduplication, cross-request caches, keys, invalidation, storage schema and cache eviction. Request state must not bleed through module globals. Real-time versus CRUD freshness comes from the contract, not a universal staleTime/refocus value; gcTime controls inactive retention rather than freshness.
- Check static I/O versus request-bound inputs, server/client prop serialization, redundant payloads and required optimistic/recovery behavior. Framework serializer support and deployment boundaries determine what can cross; TypeScript shape alone does not.

## Counterevidence and boundaries

An awaited prerequisite, necessary field, intentional fresh query or guarded client storage can be valid. Parallelization must preserve authorization, failures, cancellation and resource limits. Do not claim throughput from source or require SWR/LRU/better-all. Route domain-cache invariants and actual authorization defects to their owners; retain React dataflow causes here.

## Delivery

State request/scope lifetime, dependency or cache relation, reachable ordering and consequence, effective guard and missing runtime evidence. Separate latency derivation from measured latency and shared-state leakage from generic performance advice.

## Composed delivery

Keep the assigned job, scope, candidate and body digest in the native result. Return one member_results entry per specialist: specialist_id, status (delivered or failed), coverage (complete or incomplete), findings (canonical finding IDs) and gaps. Write each finding once and reference it from every relevant member. A clean member still declares its checks and coverage. Missing input or unfinished checks leave that member incomplete; a delivered report does not imply successful coverage.
