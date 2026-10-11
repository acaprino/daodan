---
name: rabbitmq-production
description: >
  Knowledge base for running the broker under real load, split into references loaded on demand.
  TRIGGER WHEN: designing, operating, upgrading, monitoring, or securing RabbitMQ in production, or implementing delivery patterns (retry, outbox, idempotency, RPC).
  DO NOT TRIGGER WHEN: the task is a quick conceptual question the rabbitmq-expert agent answers without production detail.
---

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
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
