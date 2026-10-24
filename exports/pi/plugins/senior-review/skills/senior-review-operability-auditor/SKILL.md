---
name: senior-review-operability-auditor
description: 'Reviews whether operators can detect failures, release compatible versions and recover service and data under declared operational requirements. TRIGGER WHEN: target changes error reporting, logs, probes, alerts, deployment, schema rollout, feature flags, environment configuration or backup and restore. DO NOT TRIGGER WHEN: only bootstrap cycles, local retry behavior or native client compatibility is at issue; use startup, temporal resilience or platform reviewers.'
disable-model-invocation: true
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.

# Operability Auditor

Trace a real failure or release transition through its operational controls.
Configuration presence is not evidence of a delivered signal or successful recovery.

## Shared review method

Before analysis, read
`<plugin-root>/skills/review-quality-gates/references/reviewer-common.md`.
It owns scope, snapshot, evidence, independence, knowledge usage and delivery.
Use its compact report; add the failed operational transition and its requirement.

## Establish the operating contract

- Identify service boundaries, environments, deployment topology, operators,
  supported release transitions and declared availability/recovery objectives.
- Read code, effective configuration, pipeline and relevant runbook together.
  Distinguish checked-in defaults from resolved deployment values.
- Bind supplied operational evidence to its candidate, environment, version and
  time. Missing deployment access or undeclared objectives are coverage gaps.
- Do not require a particular observability vendor, staging topology, rollout
  strategy or numeric objective without a contract or concrete failure scenario.

## Error signals, correlation and alerts

- Follow relevant errors from catch/handler/background task to the intended log,
  metric, trace or error channel, including filtering, sampling and exporter setup.
- Check errors swallowed, relabeled as success, lost before flush or excluded by
  routing. Inspect an equivalent reporting path before claiming silent failure.
- Follow correlation across ingress, async work and service boundaries. Verify
  useful operation context survives; do not demand personal data in diagnostic logs.
- Check signal meaning, units, cardinality and aggregation against the monitored
  outcome. A success counter before completion may mask the failure being monitored.
- Trace alert expressions, windows, suppression, routes and actionable context
  against declared detection needs. Check equivalent alerts and planned maintenance.
- Distinguish a configured route from observed alert reception. Cite supplied
  exercise evidence when claiming delivery; never send a test alert during review.

## Health and continuity

- Trace readiness/liveness responses to actual serving capability and the consumer:
  orchestrator, load balancer, watchdog or human operator.
- Check degraded operation, dependency failure and recovery. A liveness probe that
  restarts healthy local work during an external outage needs a concrete restart path.
- Confirm admission stops before drain/termination, in-flight work receives the
  permitted completion window and replacement capacity becomes usable in time.
- Follow connections, sessions and jobs across deployment transitions; distinguish
  intended downtime from a violated continuity requirement.
- Startup prerequisite cycles and premature initial readiness belong to the startup
  reviewer; keep steady-state health and rollout routing here.

## Releases, schemas and environments

- Compare old and new readers/writers with each schema/backfill phase. Check
  expand/contract ordering, mixed versions, rollback windows and cache/message formats.
- Identify locks, lengthy migrations or backfills that defeat the declared release
  strategy using engine semantics and available execution evidence, not guessed timing.
- Trace rollback or an explicitly accepted forward-fix through application artifacts,
  schema, configuration and stored state. A prior binary alone may be insufficient.
- Check feature-flag defaults, unavailable-provider behavior, rollout cohorts,
  deactivation and coexistence across versions. Business meaning of branches belongs
  to logic integrity; release compatibility of those branches belongs here.
- Trace artifact promotion and environment selection to actual endpoints, datasets,
  secret references and runtime configuration. Check intended differences before
  alleging staging/production drift or requiring a new environment.
- Check rollback/drain/recovery instructions are executable with the declared
  identities and assets. Do not expose secret values or execute the procedure.

## Backup, restore and disaster recovery

- Map the recoverable service to data, configuration, schemas, object stores,
  required keys and external dependencies. Trace each required asset into backup
  selection, retention, access and a surviving failure domain.
- Check snapshot consistency across related assets and the order of replay or
  restoration against the declared recovery point. Replication alone does not prove
  protection against the failure under review.
- Follow restoration into a usable service, including keys/credentials, compatible
  versions, integrity checks and reconnection of dependencies.
- Examine supplied restore exercises for relevant assets, versions, failure scope,
  outcome and elapsed time; backup success does not establish restore success.
- Trace failover and failback, writes during recovery, dependency availability and
  authoritative state selection against the declared disaster scenario.
- Compare evidence to declared recovery point/time objectives. Unknown objectives
  remain unknown; do not invent targets or require a destructive rollback.
- Check managed-service guarantees and existing equivalent recovery paths before
  alleging missing controls. Do not perform a backup, restore, failover or deployment.

## Evidence and boundaries

For each finding, cite the operational requirement, trigger, affected environment,
control chain, source/configuration locations and failed outcome. Retain relevant
counterevidence, including equivalent channels, intentional maintenance windows,
accepted forward-fix strategies and applicable managed-service guarantees.

- Data transformation/invariants belong to data integrity; service-version/schema
  coexistence and restoration sequence belong here.
- Retry/deadline behavior belongs to temporal resilience; cross-service delivery
  semantics to distributed flow; resource release mechanics to resource lifecycle.
- Security audit trails, leaked diagnostics and privileged deployment permissions
  belong to security. Native client runtime compatibility belongs to platform.
- Read existing exercise results; testing owns whether protection is adequate.
  Keep configured, source-verified and runtime-demonstrated coverage distinct.
