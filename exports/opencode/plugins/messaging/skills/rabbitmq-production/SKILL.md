---
name: rabbitmq-production
description: >
  Knowledge base for running RabbitMQ under production load, split into on-demand references.
  TRIGGER WHEN: designing, operating, upgrading, monitoring or securing RabbitMQ in production, or implementing delivery patterns (retry, outbox, idempotency, RPC).
  DO NOT TRIGGER WHEN: quick conceptual questions (use rabbitmq-expert directly).
---

<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# RabbitMQ Production

Index for running RabbitMQ 4.x in production: version and upgrade gates, delivery patterns, sizing and monitoring thresholds, security hardening. References hold the full write-ups; canonical reference lives at https://www.rabbitmq.com/docs.

## Scope

The `rabbitmq-expert` agent covers exchange types, queue topology design, clustering and HA, protocols, and first-aid diagnostics inline. This skill supplies what the agent defers here: version-specific upgrade gates, sizing and monitoring thresholds, full delivery-pattern write-ups, and security hardening. Load the matching reference below instead of reasoning from general RabbitMQ knowledge; defaults and limits change materially between minor versions.

## When to use

- Planning or executing a RabbitMQ upgrade across major or minor versions
- Choosing a queue type for a new workload (classic, quorum, stream)
- Implementing a delivery pattern (retry, outbox, idempotency, RPC)
- Sizing a cluster or setting monitoring thresholds and alarms
- Hardening a broker for TLS or multi-tenancy
- Diagnosing an operational incident beyond first-aid `rabbitmqctl` checks

## How to use this skill

The quick tables below are for fast checks during a conversation. For anything version-sensitive or that changes broker behavior (an upgrade, a sizing decision, a security control, a delivery pattern implementation), load the matching reference file first rather than relying on the quick table alone. The quick tables summarize; the references are the source of truth within this skill.

## Current state

Current stable series: RabbitMQ 4.3 (latest patch 4.3.4). Community support for 4.1 ended 2026-01-31, for 4.2 ended 2026-07-31; 4.3 is supported until 2026-11-30. Minimum Erlang 27.0. Source: https://www.rabbitmq.com/release-information (checked 2026-08-10).

Full timeline, breaking changes per version, and client/library compatibility: load `versions-and-upgrades.md`.

## Queue type quick table

| Queue type | Notes |
|---|---|
| classic | CQv2, non-replicated; transient denied by default in 4.3 |
| quorum | default for durable work; delivery-limit 20 default; 32 priorities and delayed retries in 4.3 |
| stream | 5M+ backlogs, fan-out, replay; no TTL, no priority, no DLX |

Topology ceilings and per-type operational limits: load `operations.md`. The queue-type decision list lives in the `rabbitmq-expert` agent.

## Key thresholds quick table

| Threshold | Value |
|---|---|
| Memory watermark | 0.4 to 0.7 (default 0.6) |
| Disk free minimum | 4 GB |
| File descriptors | 50K+ |
| Connection churn alarm | above 100 connections/s |
| Default max message size | 16 MiB |
| Quorum topology ceiling | roughly 5,000 queues per cluster |
| Prometheus scrape interval | 30s |

Full sizing methodology, alarm wiring, and diagnostic playbooks: load `operations.md`.

## Delivery patterns (client-neutral)

Retry, outbox, idempotency, and RPC patterns are written in client-neutral pseudocode so they apply across AMQP client libraries. Load `patterns.md` before implementing any of them.

- Do not implement retry, outbox, idempotency, or RPC from general AMQP knowledge alone; load `patterns.md` first
- The pattern snippets in the `rabbitmq-expert` agent are quick illustrations, not the full write-up

## Reference index

| Reference | Load when |
|---|---|
| `versions-and-upgrades.md` | upgrades, breaking changes, client/library choices |
| `patterns.md` | implementing any delivery pattern |
| `operations.md` | sizing, monitoring, diagnostics beyond first aid |
| `security.md` | hardening, TLS, multi-tenancy |
