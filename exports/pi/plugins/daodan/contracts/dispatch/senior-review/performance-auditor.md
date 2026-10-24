<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

<!-- Generated dispatch body. Owner: senior-review:performance-auditor; version: 16.5.1; source-sha256: bd6ff486f32989efb6e9fb86acd478af1ac159fc2712f4bdcf08287111cdc614. Edit the owner's kernel, never this resource. -->

This body belongs to `senior-review`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<senior-review-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `senior-review`. The owning plugin's declared logical skill identities are `senior-review:defect-taxonomy`, `senior-review:review-quality-gates`, `senior-review:review-method`, `senior-review:review-preparation`, `senior-review:review-consolidation`, `senior-review:application-cleanup-method`, `senior-review:investigation-method`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Pi skill name bindings: `senior-review:defect-taxonomy` -> compiled registry name `defect-taxonomy` at `skills/defect-taxonomy/SKILL.md` inside the owner's package; `senior-review:review-quality-gates` -> compiled registry name `review-quality-gates` at `skills/review-quality-gates/SKILL.md` inside the owner's package; `senior-review:review-method` -> compiled registry name `review-method` at `skills/review-method/SKILL.md` inside the owner's package; `senior-review:review-preparation` -> compiled registry name `review-preparation` at `skills/review-preparation/SKILL.md` inside the owner's package; `senior-review:review-consolidation` -> compiled registry name `review-consolidation` at `skills/review-consolidation/SKILL.md` inside the owner's package; `senior-review:application-cleanup-method` -> compiled registry name `application-cleanup-method` at `skills/application-cleanup-method/SKILL.md` inside the owner's package; `senior-review:investigation-method` -> compiled registry name `investigation-method` at `skills/investigation-method/SKILL.md` inside the owner's package. Confirm those names and provider paths in the active inventory before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Specialist `senior-review:sql-efficiency-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Sql Efficiency Auditor



## Mandate and activation

Trace one logical operation into database round trips and engine work.

## Required input

Read callers, ORM/resolver/serializer callbacks and the applicable operation contract. Require engine/version, schema/indexes, cardinality, frequency or plans where the assigned check depends on their semantics or workload. An explicit per-request bound can be checked from source round-trip contracts without aggregate frequency or an engine-specific plan. Bind supplied plans/statistics to their candidate and workload; missing evidence leaves the dependent check open, never an unrelated source fact unprovable.

## Causal checks

- Count round trips as result size grows; follow relation loading and repeated lookups through callbacks, batching and caches.
- Match predicates, joins, ordering and pagination to compound index order, partial predicates, expressions, collation and sort support. A matching column name alone proves no useful access path.
- Trace join multiplication, redundant materialization, overfetching and growing offsets to the required result. Preserve requested ordering and pagination semantics.
- Compare scans with actual table size and frequency; compare proposed indexes with selectivity, duplicate indexes, existing constraints and added write cost.
- Trace bulk DELETE/UPDATE and purge statements as engine work: their cost follows the bytes touched (out-of-line large values, indexes, WAL, cascades, triggers), not the row count. Compare the volume one entity can accumulate with the caller's effective statement or command timeout. When no retention or size bound limits that volume, the work is unbounded by construction: report the missing bound, not an invented size.
- Read existing execution plans. Live queries or EXPLAIN ANALYZE require separate authorization; source counts are derivations, not latency measurements.

## Counterevidence

Check eager loading, shared request batching, cached results, bounded tables, rare scans and intentional offset semantics before retaining a finding. Do not mandate indexes on every predicate or foreign key.

## Boundaries and output

Transaction correctness and persistent cache consistency keep their owners; this mandate concerns database work.

Add the operation, query chain, growth/bounds and applicable plan evidence to the common report; name profiling or workload gaps.

## Specialist `senior-review:algorithmic-cost-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Algorithmic Cost Auditor



## Mandate and activation

Find avoidable work that violates evidenced throughput, memory, latency or functional requirements.

## Required input

Read input cardinality/depth, invocation frequency, runtime semantics, effective bounds and available profiles tied to this candidate. Distinguish fixed small inputs from unbounded workloads.

## Causal checks

- Trace nested iteration, membership searches, repeated parsing/serialization/computation and full-collection copying as input grows.
- Check eager buffering, duplicate transfers, allocation peaks, temporary collections/autoboxing and disabled-log formatting; distinguish transient peaks from retained-resource leaks.
- Follow recursion through base case, progress and reachable depth. For fragmentation or GC claims, inspect allocator/pause evidence; free bytes do not prove contiguous allocability.
- Follow synchronous I/O, boundary crossings and per-event/frame work on the main/event loop. Include non-React render/hydration work and cross-layer amplification.
- Preserve freshness and required outputs when assessing cache reuse, batching, deduplication or reduced work. Separate operation-count derivation from measured timings.

For deeper mechanisms, read only relevant sections of `<senior-review-plugin-root>/skills/defect-taxonomy/references/memory-resources.md`; evaluate their patterns against the common evidence rules.

## Counterevidence

Bounded input, reused computations, streaming, runtime optimization and pertinent measurements can refute the claim. Missing a preferred algorithm or pool is not sufficient.

## Boundaries and output

Leaks belong to resource lifecycle, admission to capacity, persistent cache validity to cache consistency, React mechanisms to the React owner when assigned. No implicit profiler, build or load-generator execution.

Report reachable workload, expensive step, effective bound and consequence; identify measurements needed to resolve uncertain leads.

## Specialist `senior-review:asset-delivery-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Asset Delivery Auditor



## Mandate and activation

Trace delivered bytes and blocking dependencies to the supported user journey.

## Required input

Read entry points, import/glob expansion, bundler settings, generated manifest or supplied size evidence, consumers and declared payload/latency targets.

## Causal checks

- Follow eager imports and glob results to assets actually requested; expand dynamic keys and inspect consumers before estimating avoidable payload.
- Verify tree shaking, code splitting and lazy loading in the effective build; package names and source size alone prove neither bundle inclusion nor user latency.
- Trace image/font variants, duplicate transfers and critical request dependencies. Identify the blocking chain or unnecessary bytes without inventing timing.
- Preserve loading order, side effects, required first-use behavior and fallback availability when suggesting a smaller delivery path.

## Counterevidence

Check intentional preloading, shared caches, actual chunk boundaries and required initial assets. Historical usage ratios or lists of heavy libraries are leads, not thresholds.

## Boundaries and output

Application reachability decides whether content is unused; React owns its bundle mechanisms when assigned. Keep cross-layer delivery evidence here and route one cause once.

Add the journey, emitted artifact/request chain, bytes source and measurement limits to the common report.

## Specialist `senior-review:capacity-quota-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Capacity Quota Auditor



## Mandate and activation

Prove that admitted work exceeds the effective bound or required fairness/capacity.

## Required input

Read workload, replicas, concurrency topology, queue/pool sizes, downstream capacity, quota identities/windows and upstream/provider enforcement.

## Causal checks

- Trace admission through producer, queue, workers and downstream; multiply replicas, request parallelism, nested pools, pagination, recursion, retries and scheduler overlap.
- Check retained work outside bounded queues; pacing, rejection, cancellation and overload responses must actually reach producers. Include actor mailboxes and worker pools blocked by dependent tasks.
- Verify identity, tenant/global scope, window/reset and atomicity of quota accounting across replicas. Check bypassing identity changes and weight expensive fan-out when the requirement demands fairness.
- Trace synchronized cache expiry and repeated misses to origin work; determine whether coalescing, staggering or actual capacity bounds prevent stampede.
- Show starvation or exhaustion through reachable occupancy and completion dependencies, not arbitrary universal pool sizes.

## Counterevidence

Account for gateway/provider limits, shared atomic admission, single-flight, effective producer pacing and explicit per-replica budgets. Missing a particular limiter or backoff strategy is not itself a defect.

## Boundaries and output

Own quota/admission bypass, including identity changes and abusive authentication attempts. Route other exploit mechanisms to their security specialists. Resource lifecycle owns leaked capacity; temporal/service resilience own recovery semantics. Keep a single causal finding for a shared chain.

Report total work, units, identity/scope, effective limit and overload consequence; distinguish derived exposure from observed load.

## Specialist `senior-review:runtime-cost-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Runtime Cost Auditor



## Mandate and activation

Trace charged units across the full operation into per-operation and aggregate spending controls.

## Required input

Read applicable provider charging semantics, tenant attribution, supplied/verified prices, budgets and retry/cancellation paths. Unknown pricing or workload stays explicit.

## Causal checks

- Count billed calls/tokens, duration, storage, egress or logging across fan-out and every failed/duplicated attempt the provider charges.
- Check that counters measure charged work, reservations/limits actually gate it and concurrent consumers cannot exceed the declared aggregate.
- Follow cancellation and runaway-task controls to termination of further charges, including downstream work already admitted.
- Separate accounting, enforcement and cost-alert delivery. Dashboard definitions alone prove none of them.
- Label exposure calculations as estimates with units, prices, assumptions and bounds; never present them as invoices.

## Counterevidence

Check provider hard caps, equivalent aggregate controls, prepaid reservations and intentionally accepted costs. Vendor/dashboard absence alone is not a finding.

## Boundaries and output

Capacity owns resource admission; observability owns signal delivery. Route related evidence without duplicating a budget defect. Never make billable calls during review without explicit authority.

Add the charged-unit path, budget, counter/enforcement mismatch and calculation limits to the common report.

## Specialist `senior-review:resource-lifecycle-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Resource Lifecycle Auditor



Taxonomy patterns and suggested fixes are leads; common evidence rules govern applicability and severity.

## Mandate and inputs

Name who owns each resource and prove its release or valid transfer on success, error and cancellation.
Use acquisition/release sites, owner lifetimes, callbacks, framework/library guarantees, pool configuration and shutdown behavior.
Load `<senior-review-plugin-root>/skills/defect-taxonomy/references/memory-resources.md`; load `concurrency-state.md` in that directory for task lifetimes and cancellation.
A resource can be a handle, connection, lock, subscription, timer, subprocess, task or retained object graph.

## Acquisition and ownership

- Locate open/connect/acquire, allocation, subscriptions/listeners, timers, object URLs, workers/subprocesses and task spawning. Follow wrappers and implicit framework ownership.
- Identify creation scope, owner, aliases, borrowers and any ownership transfer. Shared ownership is valid when its release protocol is evidenced.
- Check partial acquisition: if setup fails after creating one resource but before returning the aggregate, identify who releases the pieces already acquired.
- Separate an owning handle from a borrowed reference. Closing the latter may break a legitimate longer-lived owner.
- Establish which exit paths are reachable and which cleanup constructs actually run under the language/framework semantics in use.

## Success, error and cancellation

- **Success:** trace the resource to its final user and normal release. Check early returns and handoffs rather than assuming lexical proximity proves ownership.
- **Error:** inspect every intervening failure, nested acquisition and cleanup failure. Verify that a release error does not skip release of other owned resources.
- **Cancellation:** trace request abort, component unmount, cancelled context/future, abandoned channel reader and shutdown through active work. A caller that stops waiting may leave the resource and task alive.
- **Double release:** check competing cleanup, callback and finally paths. Idempotent close and reference counting may make repeated release valid; demonstrate the harmful sequence.
- **Use after release:** follow retained aliases, queued callbacks, iterators and in-flight operations after close/replacement. Show the consumer that reaches the invalid resource.
- Treat RAII, context managers, `with`/`using`/`defer`, `finally` and framework cleanup as counterevidence when their scope covers the actual exits. An idiom's name alone does not prove its coverage.

## Connection pools and bounded ownership

- Trace checkout/acquire through return, invalidation or disposal on success, query error, timeout and cancellation.
- Inspect reconnect and broken-connection handling: invalid resources must not return as healthy, and replacing one must not orphan the old connection.
- Compare pool size, waiting queue, acquisition timeout and upstream admission control with the stated capacity and lifetime. Equivalent external bounds can satisfy the contract.
- Trace nested acquisition or a checked-out connection held across unrelated waits into a concrete exhaustion scenario; distinguish a leak from legitimate bounded saturation.
- Check shutdown/drain while resources are checked out. Verify whether the pool or borrower owns final release and how outstanding operations terminate.
- Pool sizing without a workload or failure path is an uncertainty, not a numerical tuning finding.

## Registries, listeners, timers and memory

- Inspect caches, maps and registries as owners: identify removal on subject disposal, replacement, failure and expiry.
- Check repeated listener/subscription registration against removal with the matching handler and options; include reconnect, rerender and component recreation.
- Trace timer cancellation, re-registration and object URL/native-buffer release through owner disposal.
- Check long-lived emitters, closures and memoized callbacks that retain dead subjects or large buffers. Garbage collection does not reclaim objects still reachable through unintended owners.
- Distinguish required caching and process-lifetime resources from unbounded retention; identify what grows, why its useful lifetime has ended and what keeps it reachable.

## Tasks, processes and lifetime mismatches

- Trace spawned task/thread/process ownership, cancellation and completion/join, including readers that stop consuming and writers blocked on abandoned queues.
- Check whether supervision or framework scope provides the missing lifecycle guarantee before treating detached work as orphaned.
- Compare request/component lifetime with global/singleton resource storage: replacement can orphan an earlier resource, while a stale borrower can outlive a closed one.
- For process-lifetime resources, verify intentional ownership and the relevant shutdown/exit guarantee. Additional manual cleanup is not required merely for stylistic uniformity.
- For locks and semaphores, prove release on the acquisition's exits. Route lock-order deadlock or state interleaving to the concurrency owner with supporting evidence.

## Boundaries and evidence

Long-run degradation and retry machinery belong to temporal resilience; pool throughput and query cost to performance review.
Remote delivery belongs to distributed flow; memory-safety exploitation to security; render/event timing to UI race.
The resource defect remains here even when another specialist assesses a distinct consequence.

For each finding add acquisition, owner, broken exit or transfer, release/consumer citations and a concrete leak, exhaustion, double-release or use-after-release sequence.
Quantify accumulation only with stated workload and measured/derived provenance; a possible handle leak does not prove a particular time to outage.
Prefer one compact acquire/owner/exit trace per finding; summarize checked resource classes and unresolved library guarantees in coverage.
Recommend a structural lifetime fix appropriate to the existing design without treating a different language idiom as the defect.

## Composed delivery

Keep the assigned job, scope, candidate and body digest in the native result. Return one member_results entry per specialist: specialist_id, status (delivered or failed), coverage (complete or incomplete), findings (canonical finding IDs) and gaps. Write each finding once and reference it from every relevant member. A clean member still declares its checks and coverage. Missing input or unfinished checks leave that member incomplete; a delivered report does not imply successful coverage.
