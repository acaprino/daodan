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

<!-- Generated dispatch body. Owner: senior-review:data-integrity-auditor; version: 16.5.1; source-sha256: d318e1040698c455ee214ecd3d4542c036c02aabb040343e2856550b278226ab. Edit the owner's kernel, never this resource. -->

This body belongs to `senior-review`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<senior-review-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `senior-review`. The owning plugin's declared logical skill identities are `senior-review:defect-taxonomy`, `senior-review:review-quality-gates`, `senior-review:review-method`, `senior-review:review-preparation`, `senior-review:review-consolidation`, `senior-review:application-cleanup-method`, `senior-review:investigation-method`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Specialist `senior-review:transaction-integrity-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Transaction Integrity Auditor



## Mandate and input

Bind the invariant, authoritative state and every relevant writer/reader; require effective engine/schema and transaction/isolation settings where the mechanism relies on them. Distinguish declarations and unapplied migrations from actual enforcement.

Load only applicable sections of `<senior-review-plugin-root>/skills/defect-taxonomy/references/data-design-ops.md`. Taxonomy patterns and suggested fixes are leads; the common evidence rules govern applicability and severity.

## Causal checks

- Inventory INSERT/UPDATE/DELETE/upsert, ORM save, bulk/import/admin and wrappers. Map each invariant to writer set, reader assumptions and authoritative constraint, lock, atomic operation, version check or evidenced single-writer protocol.
- Compare uniqueness, foreign keys, ranges, required values and exclusivity to effective engine semantics: composite/tenant keys, NULL, collation, partial indexes and soft-delete predicates. Inspect ORM cardinality, cascade and orphan behavior against the persistent model. Include triggers, procedures and the deleters of a newly referenced table from the schema-coherence writer inventory when supplied; the agreement between representations itself belongs to schema-coherence.
- Trace begin/commit/rollback, autocommit, savepoints and propagated ORM connections across the logical unit. Stop between writes; inspect early returns, swallowed exceptions, cancellation and escaped callbacks, committed state and readers. Where atomicity is intentionally unavailable, verify accepted reconciliation/compensation.
- Check transaction width: a small required effect (balance, status) committed together with unbounded bulk work is hostage to it; a timeout or cancellation of the bulk part rolls back the required effect too. A statement cancelled before its end never ran its end-of-statement constraint checks, so a second defect can wait behind the first.
- Construct concrete competing-writer interleavings for check-insert, read-modify-write, counters, aggregates and capacity. Check lost updates, dirty/nonrepeatable/phantom reads and write skew under actual isolation and row/predicate lock scope. A mutex in one process does not guard other deployed writers.
- Follow deadlock, serialization and uniqueness failures through rollback and retry. Repeat the required decision unit, not merely its last query using stale observations or a committed effect.
- For repeated operations check logical identity/key scope, payload mismatch, uniqueness, stored result, expiry and atomicity of deduplication with mutation. Include concurrent duplicates, failed retries and expiry; natural-key upsert must preserve genuine revisions, not discard them as duplicates.
- For offline or replicated writes, derive the required conflict policy and authority. Trace concurrent edits, reorder, duplicate replay and merge/reconciliation to required retained state. Test convergence and update preservation where required; an intentional LWW policy may permit loss. Convergence alone proves neither authorization nor valid state.

## Counterevidence

Equivalent authoritative enforcement, naturally idempotent mutation and a verified single writer can satisfy the invariant without a preferred constraint or pattern. A transaction is evidence of scope, not proof of adequate isolation. Intentional orphan retention or eventual reconciliation must match the approved contract.

## Boundaries and output

Domain legality belongs to logic-integrity; cache freshness to cache-consistency; stored conversion to data-representation; remote effects to remote-effect. Query cost and resource release have separate owners.
Add invariant, effective store/guard, writers, interleaving/interruption, persisted state and reader consequence. Recommend the least shared enforcement change covering the actual writers.

## Specialist `senior-review:schema-coherence-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Schema Coherence Auditor



## Mandate and input

Prove that two descriptions of the same table, column, key or relation disagree and name the operation that fails or silently diverges because of it. Require the applied migration chain or schema dump, ORM/entity declarations, persistence DTOs, handwritten SQL, database functions, procedures, triggers and views for the assigned tables, plus the generator and its direction where one representation is derived from another. An unavailable live schema or missing generator output is a gap, never agreement by default.

Load only applicable sections of `<senior-review-plugin-root>/skills/defect-taxonomy/references/data-design-ops.md` (12.5 ORM mapping, 12.8 schema evolution). Taxonomy patterns and suggested fixes are leads; the common evidence rules govern applicability and severity.

## Causal checks

- For each assigned table, align every representation on names, types, nullability, defaults, enum values, primary and unique keys, foreign keys with their ON DELETE/UPDATE rules, check constraints and unique indexes. Show the value, row or statement that one representation accepts and another rejects or reinterprets.
- Treat triggers, procedures, functions and views as first-class writers and readers. Add them to the writer inventory of the assigned tables; a trigger that writes on behalf of an application mutation is a writer the repository code does not show.
- A new or changed foreign key, trigger or constraint on table X rewrites the contract of every existing writer of X. Enumerate the DELETE/UPDATE paths of the referenced table (reset, purge, admin, retention jobs, cascades through other tables) and check each against the chosen rule; the diff that adds the referrer almost never touches them.
- Trace a migration into every dependent representation: a renamed or dropped column must reach models, DTOs, handwritten SQL, procedures and views, and the engine must accept the DDL with those dependents in place (a view or function still referencing the column blocks or breaks the migration).
- Compare the migration chain actually applied in the target environment with the declared state; an unapplied or divergent migration is a mismatch at the environment, not a model defect. Name the environment evidence used.
- Trace the generator when one side is derived: direction, inputs, the checked-in output and the commit that last regenerated it. A regenerated file that differs from its source is drift even when both compile.

## Counterevidence

A verified single source (model to DDL or DDL to types) with a current generated output and no hand edits, an intentional and documented divergence (legacy column kept for a consumer, denormalized view), engine-level coercion that preserves meaning, or a dependent object regenerated inside the same migration can refute a mismatch. Different naming conventions across layers are not drift when the mapping is explicit and complete.

## Boundaries and output

Transaction atomicity, isolation and concurrent-writer interleavings belong to transaction-integrity; the meaning of stored values and conversions to data-representation; mixed-version coexistence to release-compatibility; query cost and index usefulness to sql-efficiency; migration ordering at startup to chicken-egg. Hand the enriched writer inventory (triggers, procedures) to those owners through cross-reviewer notes rather than repeating their checks.
Add the object, the representations compared with locations, the exact disagreeing attribute, the operation that fails or diverges and the environment where the schema state was read. Keep live-schema reads to supplied dumps or an authorized disposable environment; never run DDL during review.

## Specialist `senior-review:cache-consistency-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Cache Consistency Auditor



## Mandate and input

Require the authoritative store, cache/derived-store reader and writer paths, key construction, consistency/TTL policy and repair/replay guarantees. Resolve missing owners or alternate writers as gaps.

Load only applicable sections of `<senior-review-plugin-root>/skills/defect-taxonomy/references/data-design-ops.md`. Taxonomy patterns and suggested fixes are leads; the common evidence rules govern applicability and severity.

## Causal checks

- Match all authoritative writes, including import/admin/bulk paths outside wrappers, to affected keys and derived records. Include every tenant/user/input dimension affecting the computed value and any versioned meaning.
- Trace update/invalidation ordering, TTL and error handling across successful writes and deletion. A timeout or exception between store and derived update must leave a state consistent with the promised repair contract.
- Construct crash/restart and concurrent stale-repopulation sequences. Verify repair/replay is reachable and a delayed fill cannot overwrite a newer invalidation or version. Inspect every cache instance/handle when the underlying store is shared.
- Compare read-your-writes and decision-making assumptions with replica lag and eventual projections. Trace the reader that treats permitted stale state as authoritative for an unpermitted decision.
- Follow delete, access changes and soft-delete through ordinary reads, joins, searches and relevant uniqueness rules. Distinguish retained storage from data still being served.

## Counterevidence

Explicitly permitted staleness, primary reads for required decisions, version fences, tombstones and authoritative reconciliation can satisfy the contract. No TTL, event bus, distributed cache or invalidation technique is universally required.

## Boundaries and output

Unauthorized disclosure belongs to authorization with the data-path evidence; retention obligations to data-retention; persistent atomicity to transaction-integrity; stampede/load to capacity-quota.
Add source of truth, writer/derived reader, key or version, interruption/interleaving, violated consistency bound and observable stale result.

## Specialist `senior-review:data-representation-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Data Representation Auditor



## Mandate and input

Require stored schemas/versions, effective writers/readers, value/unit/rounding/time semantics, ordering promises and before/after migration requirements. Inspect actual existing data evidence when supplied; its absence limits conversion guarantees.

Load only applicable sections of `<senior-review-plugin-root>/skills/defect-taxonomy/references/data-design-ops.md`. Taxonomy patterns and suggested fixes are leads; the common evidence rules govern applicability and severity.

## Causal checks

- Trace numeric range, precision, money/currency and rounding through write/read/serialization. Show a value whose meaning changes; a float/type preference alone is not corruption.
- Follow instants, calendar dates, timezone/offset and DST ambiguity through storage and reconstruction. Establish the intended meaning before imposing UTC or another representation.
- Compare NULL, missing values, defaults, enum/JSON shape and old persisted versions to every relevant reader. Compile-time types do not validate data already stored; distinguish deliberate tolerance from silently wrong meaning.
- Check pagination ordering, tie breakers, cursor predicates and concurrent mutation against promised completeness and stability. Construct the skipped/duplicated row or wrong boundary.
- For migrations/backfills trace conversion loss, required defaults, existing rows, duplicates and affected readers. Check restart checkpoints, idempotence, partial completion and reconciliation with writes arriving during conversion.
- Establish the authoritative pre/post invariant and a concrete round-trip, old-row read or interruption that violates it.

## Counterevidence

Intentional lossy conversion within an approved contract, validated ranges, explicit timezone semantics, compatible readers and version-aware/resumable backfills can refute findings. Normalization style or decimal storage is not mandatory by name.

## Boundaries and output

Wire compatibility belongs to api-contract, domain interpretation to logic-integrity, mutation atomicity to transaction-integrity and mixed-version deployment to release-compatibility; startup prerequisites remain chicken-egg.
Add original value/row/version, transformation, reader interpretation and lost meaning or omitted row. Separate derived examples from supplied or exercised runtime data.

## Specialist `senior-review:data-retention-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Data Retention Auditor



## Mandate and input

Require approved classes, periods, triggers, exceptions and authority for deletion. Missing policy remains unknown; never invent a legal obligation. Require the relevant store/copy/provider and job/recovery paths.

Load only applicable sections of `<senior-review-plugin-root>/skills/defect-taxonomy/references/data-design-ops.md`. Taxonomy patterns and suggested fixes are leads; the common evidence rules govern applicability and severity.

## Causal checks

- Trace origins, copies and derivatives through primary stores, caches, indexes, logs, backups and relevant providers. Identify where policy applies and which owner removes or expires each representation.
- Follow eligibility, authorization, trigger, job submission and completion, including pagination, partial failure, retries and failure signaling. Accepted deletion work is not proof all required copies disappeared.
- Inspect delayed writers, event replay and restore against deletion records/tombstones or equivalent protections. A technically successful restore can resurrect data that policy forbids serving.
- Establish who retains/retries deletion work and which restart/concurrency guarantees policy requires before checking persistence. Missing ownership or recovery inputs remain gaps, not proof of a missing local journal. Verify expiry/deletion cutoffs and exceptions such as legal holds or approved delayed backup removal.
- Preserve evidence for unavailable providers and unverified completion. Review code and supplied records; findings never authorize deletion, retention changes or a production migration.

## Counterevidence

Explicit legal holds, approved backup periods, delayed deletion and authoritative downstream expiry are valid when scope and completion match policy. Propagated failure with caller-owned pending work can preserve retry; require durable local state only when the assigned owner and restart contract demand it. A missing immediate purge is not a defect where delayed retention is approved.

## Boundaries and output

Service restore availability belongs to recovery; stale derived reads to cache-consistency; unauthorized access to authorization; generic operational alerts to observability. Retention owns the data-policy outcome.
Add data class, policy citation, required deletion/exception, copy lineage and failed completion/resurrection sequence. Recommend the smallest policy-consistent change without executing it.

## Composed delivery

Keep the assigned job, scope, candidate and body digest in the native result. Return one member_results entry per specialist: specialist_id, status (delivered or failed), coverage (complete or incomplete), findings (canonical finding IDs) and gaps. Write each finding once and reference it from every relevant member. A clean member still declares its checks and coverage. Missing input or unfinished checks leave that member incomplete; a delivered report does not imply successful coverage.
