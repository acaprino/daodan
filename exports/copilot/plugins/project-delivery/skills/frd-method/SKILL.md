---
name: frd-method
description: >
  Extract, validate, reconcile, approve, version and verify evidence-bound functional requirements documents in docs/frd/.
  TRIGGER WHEN: the user asks for an evidence-bound FRD, requirements and domain references must be extracted from project sources, a fresh extraction must be reconciled with manual review, or an FRD needs approval, revision or verification.
  DO NOT TRIGGER WHEN: recording an architecture or technical decision (use project-delivery:adr-method), writing general project documentation without evidence spans, or treating current implementation as an automatically approved requirement.
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# Evidence-bound functional requirements

Load `work-controller:work-record` for run ownership and authorization. Read
`references/frd-schema.md` before constructing or changing extraction data.
The helper is
`python "${PLUGIN_ROOT}/skills/frd-method/scripts/frd_tool.py"`.
It writes only the FRD records and their generated index.

## Grounded extraction

Before substantive claims, load `research:science-based-approach` and compose
its automatic checkpoint. In the schema, scientific evidence requires a pinned
local revision, exact digest and Unicode excerpt, never just a URL. Keep needs,
hypotheses, observations and support separate. Unauthorized publication leaves
a named gap. Evidence never approves or rewrites an Accepted FRD.

1. Establish behavior, actors and scope from the request and interview; keep current, documented and requested behavior distinct.
2. Inspect code and documents. Use Codebase Map to locate evidence, then read cited source; the map is static navigation, not correctness or runtime proof.
3. Record requirements, entities and relationships with exact Unicode spans; report contradictions and runtime gaps.
4. Write extraction JSON and run `propose`. Records and items remain `Proposed` and `extracted`, never approved or verified.

Evidence must point to a project-relative file and match its current byte digest
and exact `[start,end)` excerpt. Do not cite an inaccessible, stale or inferred
span. Do not put secrets in excerpts.

## Load map

| Step | Run |
|---|---|
| Before using records | `validate --project ROOT` |
| New FRD | `propose --project ROOT --title T --slug S --task TASK --sha SHA --data FILE` |
| Revise Accepted | `propose --project ROOT --revise FRD-NNNN --task TASK --sha SHA --data FILE --expect-digest D` |
| Reconcile extraction | `merge --project ROOT --frd FRD-NNNN --data FILE --expect-digest D` |
| Review or correct an item | `resolve --project ROOT --frd FRD-NNNN --item ID --status verified\|corrected\|rejected --expect-digest D [--data FILE]` |
| Resolve a disagreement | the same `resolve`, adding `--conflict CONFLICT-NNNN` |
| Exact text approved by user | `promote --project ROOT --frd FRD-NNNN --sha SHA --expect-digest D` |
| Reviewer confirmed conformance | `verify --project ROOT --frd FRD-NNNN --sha SHA --expect-digest D` |
| Repair a stale index | `index --project ROOT` |

Use `validate --frd FRD-NNNN` to obtain the current Proposed and Accepted
versions and their digests. Every mutation of an existing record is optimistic:
read the exact record, then pass its digest. A mismatch means read and review
the new bytes rather than retrying blindly.

## Reconciliation and approval

`merge` never deletes missing items or overwrites semantic changes. It unions
new evidence, preserves `verified`, `corrected` and `rejected` review states,
and opens conflicts when extraction disagrees with an existing item. Resolve
each conflict explicitly. A manual correction uses complete item JSON and fresh
valid evidence. Promotion refuses unresolved conflicts.

Show the exact candidate and digest to the user. Call `promote` only after the
user explicitly approves that candidate. Never auto-approve because validation
passed, sources agree, a map contains a claim, or an implementation already
exists. Promotion accepts the FRD and supersedes its previous version; it does
not verify implementation. Only a separate reviewer conformance check justifies
`verify` and `last_verified_sha`.
