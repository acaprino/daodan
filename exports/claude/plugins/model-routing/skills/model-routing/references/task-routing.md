<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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
   available variants and every capability the host declares (the features and
   input/output modalities named in `scripts/model_capabilities.py`) as
   `MODELS.json`. Never copy
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
and the installed model-routing helper:

```text
python -B "${CLAUDE_PLUGIN_ROOT}/skills/model-routing/scripts/task_router.py" plan --request REQUEST.txt --models MODELS.json --out ROUTING_PLAN.json
```

When `status` is `awaiting-classification`, invoke exactly
`classifier.model_id` through the host's supported model-call mechanism, using
the emitted `prompt.system` and `prompt.user`. Save the raw reply to REPLY.txt.
No selection authority is delegated to that model. Never repair its enums,
replace its reply with a coordinator classification, or silently substitute the
session model. If the classifier is unavailable, the host cannot select it, the
call fails or `status` is `no-classifier`, record the gap and use `--no-reply`.

```text
python -B "${CLAUDE_PLUGIN_ROOT}/skills/model-routing/scripts/task_router.py" assign --plan ROUTING_PLAN.json --reply REPLY.txt --models MODELS.json --catalog "${CLAUDE_PLUGIN_ROOT}/skills/model-routing/references/model-catalog.json" --out ROUTING_ASSIGNMENT.json
```

For that failure branch, replace `--reply REPLY.txt` with `--no-reply`.
Add `--require CAPABILITY` once for each capability the node's inputs need and
no classification can infer: `input.video` for an attached video,
`structured_output` for a schema-bound reply. A name outside the vocabulary
fails the run. The host's inventory decides each gate; an unreported capability
is flagged, and the catalog's differing view of the chosen model is reported
in `chosen_capability_disagreements`.
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

Copy `binding_proposal` unchanged into a binding artifact, adding only
`confirmation` with `confirmed: true`, `source` (the user's actual answer or
reference), `host`, `model_override_supported` and `effort_override_supported`.
These capability fields snapshot the verified support at confirmation time;
they do not track later changes to the current host flags. Preserve this
historical evidence when a resumed host loses support and record its current
gap in the caller's current host metadata instead.
Return the confirmed binding artifact to the caller's persistence owner.
Standalone use saves it beside the request in the owned run directory; no
record provider is required. The caller supplies its persisted
`assignments[request_sha256]` for dispatch and resume, preserving existing
assignments and reconciling concurrent updates through its own storage contract.

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
Look up only its caller-supplied `assignments[request_sha256]`. Verify human confirmation,
`confirmation.host` against the current host, current host support, selected
identity/variant availability, the current inventory and catalog file digests
and the node's required capabilities against the binding. A different request,
changed inventory, changed catalog or changed requirements requires fresh `plan`
and `assign`; do not reuse another
intent's assignment or an older catalog's order. A changed selection needs its
own confirmation. Dispatch with that exact binding through the supported host
mechanism; otherwise follow the unbound branch above.

A recorded confirmation source does not prove that a human supplied it or that
the host applied the model; the coordinator verifies those execution facts.
