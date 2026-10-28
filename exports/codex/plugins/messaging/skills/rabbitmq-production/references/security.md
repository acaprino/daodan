<daodan_host_binding host="codex">
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

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
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
