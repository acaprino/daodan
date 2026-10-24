> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

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

# Deterministic request routing

The coordinator executes this sequence. The classifier reports task signals;
`task_router.py` alone selects the model. A skill is not a model-call executor.
All input, prompt, reply and proposal files belong inside the owned run directory.
To refresh the model catalog, its prices or the price rules, read
`model-catalog-refresh.md` in this directory. To price a host's logged usage, run
`scripts/usage_pricing.py`; its docstring is the contract.

## Preflight inventory

1. Identify the active host and its actual model inventory through registered
   tools or its configuration. Save only model identities, prices, limits,
   modalities, tool support and available variants as `MODELS.json`. Never copy
   credentials or the whole provider configuration. Use the native `provider`
   model map, a `providers` tool projection or a flat `models` list accepted by
   `task_router.py`. The annotated `screened` output of `tier_router.py discover`
   is not a native inventory: do not feed it back as `--models`.
2. Verify whether the active call/dispatch mechanism accepts an explicit model
   identity and a reasoning variant. Record these measured facts as
   `environment.models.host`, `model_override_supported` and
   `effort_override_supported`, with the inventory path and SHA256 digest.
   Missing support is false, never inferred from a model name or registration.
   Initialize `assignments` to an empty object on a new run; preserve existing
   assignments on resume and check them as below.
3. Resolve this skill's bundled `references/model-catalog.json`. It is the
   primary tier source. Record its revision and file digest; expose low
   confidence tiers and missing board evidence in the proposal. An unreadable
   catalog is a routing blocker. Refreshing sources is a separate action;
   network access is optional and the harvest helpers require explicit `--fetch`.

The inventory is availability evidence, not a confirmed tier mapping. Keep
legacy `environment.models.tiers` separate: a per-request selection must never
replace a global tier entry because another intent may govern a different board.

## Route each LLM node

For every DAG node, job or process that calls an LLM, create its own REQUEST.txt
with the node/job/process identity, worker role, objective, relevant context/input
digests, required capabilities and risk. Run this sequence once for that node
before its first dispatch; revalidate on resume and reroute when those inputs
change. The root model supplies no DAG-wide assignment. A deterministic node
that makes no LLM call needs no model.

Assignments are currently keyed by request digest. A `node_id` to binding map
and automatic consumption by the DAG dispatcher remain future integration;
the coordinator performs the per-node sequence today.

Read the node's request, inventory and catalog. Use the project's interpreter
and the installed protocol helper:

```text
python -B "${PLUGIN_ROOT}/skills/project-protocol/scripts/task_router.py" plan --request REQUEST.txt --models MODELS.json --out ROUTING_PLAN.json
```

When `status` is `awaiting-classification`, invoke exactly
`classifier.model_id` through the host's supported model-call mechanism, using
the emitted `prompt.system` and `prompt.user`. Save the raw reply to REPLY.txt.
No selection authority is delegated to that model. Never repair its enums,
replace its reply with a coordinator classification, or silently substitute the
session model. If the classifier is unavailable, the host cannot select it, the
call fails or `status` is `no-classifier`, record the gap and use `--no-reply`.

```text
python -B "${PLUGIN_ROOT}/skills/project-protocol/scripts/task_router.py" assign --plan ROUTING_PLAN.json --reply REPLY.txt --models MODELS.json --catalog "${PLUGIN_ROOT}/skills/project-protocol/references/model-catalog.json" --out ROUTING_ASSIGNMENT.json
```

For that failure branch, replace `--reply REPLY.txt` with `--no-reply`.
Missing or invalid classification escalates to tier3. Only the module applies
weights, risk floors, the governing board, capability gates and selection rules.
`best-undefined`, `no-candidate` and a nonzero exit cannot authorize a dispatch;
inspect their diagnostics and resolve the missing input or capability first.
No failed selection produces a `binding_proposal`.

## Confirm and record

Show the selected model and effort, tier, governing evidence, cost assumptions,
unknown capabilities and fallback reasons. Obtain explicit human confirmation
for this concrete proposal before recording a binding. A previous confirmation
of the exact unchanged binding remains valid; inventory discovery grants none.
An automatic run-wide approval policy is not implemented; the current
confirmation gate applies to each node's concrete proposal.

Copy `binding_proposal` unchanged into
`environment.models.assignments[request_sha256]`, adding only
`confirmation` with `confirmed: true`, `source` (the user's actual answer or
reference), `host`, `model_override_supported` and `effort_override_supported`.
These capability fields snapshot the verified support at confirmation time;
they do not track later changes to the current host flags. Preserve this
historical evidence when a resumed host loses support and record its current
gap in the top-level fields instead.
Persist that patch through `run_state.py update --project ROOT --run-id ID
--expected-revision N --payload PATCH.json`, preserving the interpreter, commands
and existing assignments. On a revision conflict, reread and merge the current
record; never overwrite another coordinator's state.

If the host cannot apply the selected model or its effort, retain the proposal
as unbound evidence and record the capability gap. Do not create a confirmed
assignment. Continue with inherited model settings only when the caller's method
permits inheritance, describing that limitation; otherwise leave dispatch open.
The stored `model_param` representation `provider/model#effort` is not a
universal tool argument. Bind `model_id` and `effort` to the actual fields and
available identities of the active host.

## Dispatch and resume

Immediately before each dispatch, read the request as UTF-8 text with universal
newlines, encode that text as UTF-8 and take its SHA256, matching `plan`.
Look up only its `assignments[request_sha256]`. Verify human confirmation,
`confirmation.host` against the current host, current host support, selected
identity/variant availability and the current inventory and
catalog file digests against the binding. A different request, changed inventory
or changed catalog requires fresh `plan` and `assign`; do not reuse another
intent's assignment or an older catalog's order. A changed selection needs its
own confirmation. Dispatch with that exact binding through the supported host
mechanism; otherwise follow the unbound branch above.

The run helper validates recorded shape, matching identities, digests and a
confirmation source. It does not prove that a human supplied that source or that
the host applied the model; the coordinator verifies those execution facts.
