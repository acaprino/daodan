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

# Security

Security hardening for RabbitMQ 4.x in production: bootstrap defaults to remove, vhost and topic-permission isolation for multi-tenancy, TLS, and secrets handling. Load this reference when hardening a broker for TLS or multi-tenancy, or when the `rabbitmq-expert` agent's inline first-aid advice needs the exact command syntax.

## Bootstrap hardening

Source: https://www.rabbitmq.com/docs/production-checklist

- Delete the default `guest` user in production. By default it can only connect from `localhost` (its credentials are well known), but hardening removes it outright rather than relying on that restriction.
- Set `anonymous_login_user = none` to turn off anonymous logins entirely.
- Create one user per application. A mobile app, a web app, and a data-aggregation service each get their own credential; never share one login across applications. Per-application users let you correlate connections to the owning app, grant fine-grained permissions per app, and roll over one app's credentials without touching another's.

## Virtual hosts

Source: https://www.rabbitmq.com/docs/production-checklist, https://www.rabbitmq.com/docs/access-control

- One vhost per application or environment for isolation, for example `project1_development` and `project1_production`.
- Permissions are granted per vhost as a triple of regular expressions on named resources: configure, write, and read.
- Grant them with `rabbitmqctl set_permissions -p <vhost> <user> <configure-regex> <write-regex> <read-regex>`.
- Withhold access with an unmatchable pattern (RabbitMQ's own examples use `^$`). Pseudo-example for a publisher-only and a consumer-only user on the same vhost:

  ```
  rabbitmqctl set_permissions -p orders publisher-app "^$" "^orders\..*" "^$"
  rabbitmqctl set_permissions -p orders consumer-app "^$" "^$" "^orders\..*"
  ```

  The publisher-only user has no configure and no read access, only write matching the `orders.` prefix. The consumer-only user is the mirror image: write withheld, read granted on the same prefix.

## Topic permissions

Source: https://www.rabbitmq.com/docs/access-control

- Topic exchanges get an additional, opt-in authorization layer on top of the vhost triple above. It does nothing until an administrator defines topic permissions for a specific exchange.
- `rabbitmqctl set_topic_permissions` restricts publish and consume on a topic exchange by routing-key pattern. The routing-key check runs only after the base `basic.publish` permission already allows the call, and is never reached if that check refuses access first. The access-control guide itself points to the `rabbitmqctl` man page for the full argument list rather than inlining an example, so confirm the exact argument order there before scripting it.
- Patterns support variable expansion for `username`, `vhost`, and `client_id`, so one topic-permission rule can scope many tenants on a shared topic exchange instead of giving each tenant a separate exchange.

## TLS

Source: https://www.rabbitmq.com/docs/production-checklist

- Enable TLS on every listener that crosses a public or shared network. RabbitMQ's own guidance: use TLS connections when possible, at least to encrypt traffic.
- Turn on peer verification so the client checks the server's certificate and hostname rather than accepting whatever certificate is presented.
- Evaluate the deployed TLS configuration with `testssl.sh`.
- Where TLS is mandated, disable the plain AMQP listener so there is no unencrypted fallback path.

## Secrets

- Never put credentials in files tracked by version control. Inject them through environment variables or a secret store (a Kubernetes `Secret`, Vault).
- Rotate credentials on any suspected or confirmed compromise.
- The management UI and the management HTTP API authenticate with the same user credentials. Scope monitoring access with the `monitoring` tag instead of `administrator`. Source: https://www.rabbitmq.com/docs/access-control, whose documented pattern for a cluster-wide, read-only monitoring user is:

  ```
  default_users.monitoring.vhost_pattern = .*
  default_users.monitoring.tags = monitoring
  default_users.monitoring.configure = ^$
  default_users.monitoring.write = ^$
  default_users.monitoring.read = .*
  ```
