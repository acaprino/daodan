<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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

<!-- Generated dispatch body. Owner: senior-review:operability-auditor; version: 1.0.2; source-sha256: fa9efc1a55dc7c190de7587c85957f0b1b1c7052612c17f4580b3863c8921935. Edit the owner's kernel, never this resource. -->

This body belongs to `senior-review`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<senior-review-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `senior-review`. The owning plugin's declared logical skill identities are `senior-review:defect-taxonomy`, `senior-review:review-quality-gates`, `senior-review:review-method`, `senior-review:review-preparation`, `senior-review:review-consolidation`, `senior-review:application-cleanup-method`, `senior-review:investigation-method`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Pi skill name bindings: `senior-review:defect-taxonomy` -> compiled registry name `defect-taxonomy` at `skills/defect-taxonomy/SKILL.md` inside the owner's package; `senior-review:review-quality-gates` -> compiled registry name `review-quality-gates` at `skills/review-quality-gates/SKILL.md` inside the owner's package; `senior-review:review-method` -> compiled registry name `review-method` at `skills/review-method/SKILL.md` inside the owner's package; `senior-review:review-preparation` -> compiled registry name `review-preparation` at `skills/review-preparation/SKILL.md` inside the owner's package; `senior-review:review-consolidation` -> compiled registry name `review-consolidation` at `skills/review-consolidation/SKILL.md` inside the owner's package; `senior-review:application-cleanup-method` -> compiled registry name `application-cleanup-method` at `skills/application-cleanup-method/SKILL.md` inside the owner's package; `senior-review:investigation-method` -> compiled registry name `investigation-method` at `skills/investigation-method/SKILL.md` inside the owner's package. Confirm those names and provider paths in the active inventory before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Specialist `senior-review:observability-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Observability Auditor



## Mandate and activation

Follow an actual failure through detection and notification against the operational requirement.

## Required input

Read error/task paths, effective filters/sampling/exporters, signal definitions, alert rules/routes, detection needs and supplied exercises bound to environment/version/candidate.

## Causal checks

- Trace errors through catch/handler/background task, translation, cause/stack retention, filtering, sampling, export and flush. Seek equivalent channels before alleging silence.
- Follow operation identity and useful context across ingress, async work and services; preserve diagnostic needs without demanding personal data.
- Check metric meaning, units, cardinality and aggregation against the actual outcome. Distinguish accepted/started from completed; success before completion may hide failure.
- Trace expressions, windows, suppression, routing and actionable context to the receiver. Compare declared detection needs with maintenance windows and equivalent alerts.
- Keep configured routes, source-verified paths and observed reception separate. Never send a test alert or invent reception evidence.

## Counterevidence

An upstream supervisor, native correlation, alternate delivered channel or intentional maintenance window may satisfy the same requirement. Do not require a vendor or log format by preference.

## Boundaries and output

Security owns audit authenticity and leaked diagnostics; service health owns serving capability, runtime cost owns charged work.

Add failure, signal chain, environment and receiver/detection requirement; state delivery/exercise gaps in the common report.

## Specialist `senior-review:service-health-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Service Health Auditor



## Mandate and activation

Determine whether a health result causes the correct admission or restart action at steady state.

## Required input

Read effective probes, their orchestrator/load-balancer/watchdog consumers, local dependencies, degraded-service contract and recovery behavior.

## Causal checks

- Trace each health response into the action taken by its consumer; distinguish readiness/admission from liveness/restart.
- Check normal, degraded, external-outage and recovered states against actual permitted service. A passing probe with unusable required work or a restart loop that destroys useful work needs a concrete path.
- Verify recovery of health/routing after the dependency returns; inspect stale probe state and equivalent local guarantees.
- Distinguish intentional downtime or unsupported operations from a continuity breach; do not invent availability objectives.

## Counterevidence

Local liveness with degraded readiness can be correct. Managed health checks and existing fallbacks count when their effective behavior meets the requirement.

## Boundaries and output

Startup prerequisites and initial readiness belong to chicken-egg; deployment admission/drain/replacement ordering belongs to release compatibility; resource and retry mechanisms keep their owners.

Report the failure state, probe result, consumer action and lost serving capability. Keep supplied runtime evidence separate from derived transitions.

## Specialist `senior-review:release-compatibility-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Release Compatibility Auditor



## Mandate and activation

Follow each permitted release transition while old and new components coexist.

## Required input

Read supported upgrade/rollback contract, deployment topology, old/new readers and writers, schemas/cache/message formats, migration phases, drain settings and applicable engine semantics.

## Causal checks

- Evaluate every schema/backfill phase against active old/new readers and writers, including defaults, constraints, destructive changes and cached/messages formats. Verify expansion, dual operation and retirement ordering rather than mandate a named strategy.
- Trace migration locks and backfill work against declared availability using engine/version and supplied execution evidence; do not guess durations.
- Follow admission stop, routing withdrawal, in-flight completion, termination and usable replacement capacity. Include connections, sessions and jobs required to survive rollout.
- Trace rollback or explicitly accepted forward-fix across binaries, schema, configuration and already-written state. A previous binary alone may no longer read the data.
- Check that release instructions and named identities/assets can enact the transition without executing it.

## Counterevidence

Additive schemas, compatible readers, explicit maintenance downtime, online operations proven for the engine and an accepted executable forward-fix can refute a claim.

## Boundaries and output

Startup prerequisite order belongs to chicken-egg, steady-state probes to service health, transformation correctness to data owners, disaster restoration to recovery and native platform support to platform.

Add the phase/version compatibility timeline, active consumers, violated continuity requirement and existing guard to the common report.

## Specialist `senior-review:environment-binding-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Environment Binding Auditor



## Mandate and activation

Trace the deployed artifact and environment selection into its effective resources.

## Required input

Read environment requirements, pipeline/promotion, precedence and interpolation rules, runtime configuration, identities/secret references, endpoints and datasets. Checked-in defaults alone do not establish resolved values.

## Causal checks

- Follow artifact promotion and selection to actual endpoints, datasets, secret references and service identities. Check accidental production/staging crossover and intended differences.
- Resolve missing variables, key typos, unresolved placeholders, defaults and override precedence to the actual consumer or explicit fail-fast behavior.
- Check locale, timezone and URL assumptions against the configured environment and permitted inputs; distinguish environment interpretation from persistent data representation.
- Follow sidecar/mesh routing and target selection through effective rules. Record unavailable deployment values as gaps rather than guessing them.
- Inspect procedure permissions and asset availability by reference; never expose secret values or deploy to verify a binding.

## Counterevidence

Intentional environment differences, explicit locale/timezone, validation before effects and effective external overrides can satisfy the contract. No particular staging topology is mandatory.

## Boundaries and output

Authentication/mTLS identity security belongs to session delegation; retries to service resilience; stored date semantics to data representation.

Report selection, resolved value/reference, consumer and unintended resource consequence; name unknown layers.

## Specialist `senior-review:feature-flag-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Feature Flag Auditor



## Mandate and activation

Trace flag combinations and transitions through the supported release/configuration contract.

## Required input

Read permitted combinations, defaults, provider failure/cache behavior, cohort identity, version prerequisites and activation/deactivation paths.

## Causal checks

- Check default and unavailable-provider states against supported old/new versions and prerequisite schemas/services. Follow evaluation errors and stale values into selected branches.
- Trace rollout cohorts and identity stability; establish which versions or tenants can receive a branch and whether required dependencies are present.
- Evaluate interacting flags in permitted combinations and state changes, including deactivation and return to the fallback path. Preserve coherent stored/session state.
- Compare allegedly permanent flags with the current contract and consumers; age or a long-lived off branch alone proves neither defect nor dead code.

## Counterevidence

Safe fallback, prerequisite guards, intentionally stable cohorts and documented permanent variation refute purely pattern-based findings.

## Boundaries and output

Domain meaning of a branch belongs to logic integrity, source reachability to application cleanup and mixed-version schema compatibility to release compatibility.

Add the flag combination, provider/version state, selected path and failure transition to the common report.

## Specialist `senior-review:recovery-auditor`

Provider `senior-review` owns these instructions and unqualified skills. Resolve `<senior-review-plugin-root>` from that installed provider's verified location.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Recovery Auditor



## Mandate and activation

Prove whether the declared recovery path survives its failure scenario and restores authoritative service.

## Required input

Read disaster scope, asset inventory, dependency graph, backup selection/retention/access, keys/identities, schemas/versions, runbook and supplied restore exercises with objective/environment/time bindings.

## Causal checks

- Map data, configuration, schemas, objects, keys and dependencies into surviving backup domains. Check selection, retention, access and identity availability together.
- Trace consistent snapshots, replay and restore order across related assets against the recovery point. Replication alone does not protect against every destructive event.
- Follow restoration through decrypting, compatible versions, integrity checks and dependency reconnection into a usable service. Verify required commands/assets/identities without executing them.
- Check failover and failback authority, writes accepted during recovery, fencing/reconciliation and surviving dependencies.
- Compare relevant exercise outcomes and elapsed time with declared RPO/RTO. Backup upload success does not establish successful restore; absent objectives remain unknown.

## Counterevidence

Applicable managed-service guarantees, independent key recovery, coherent replay and equivalent tested paths may satisfy the same objective. Never perform backup, restore, failover or deployment as an implicit review step.

## Boundaries and output

Release-specific coexistence belongs to release compatibility; transformation invariants to data integrity; this mandate owns restoration sequence and recoverability.

Add disaster, missing/broken asset or transition, source chain and operational consequence; distinguish configured recovery from exercised restoration.

## Composed delivery

Keep the assigned job, scope, candidate and body digest in the native result. Return one member_results entry per specialist: specialist_id, status (delivered or failed), coverage (complete or incomplete), findings (canonical finding IDs) and gaps. Write each finding once and reference it from every relevant member. A clean member still declares its checks and coverage. Missing input or unfinished checks leave that member incomplete; a delivered report does not imply successful coverage.
