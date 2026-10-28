---
name: frd-method
description: >
  Extract, validate, reconcile, approve, version and verify evidence-bound functional requirements documents in docs/frd/.
  TRIGGER WHEN: the user asks for an evidence-bound FRD, requirements and domain references must be extracted from project sources, a fresh extraction must be reconciled with manual review, or an FRD needs approval, revision or verification.
  DO NOT TRIGGER WHEN: recording an architecture or technical decision (use project-delivery:adr-method), writing general project documentation without evidence spans, or treating current implementation as an automatically approved requirement.
---

> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.
> This package registers lifecycle callbacks through `hooks/hooks.json` when the plugin is enabled. Execution requires the host's hook trust approval and Python 3 on PATH as `python`. The compiler does not approve hooks or modify host settings. Generated registration and subprocess checks do not prove installed-host execution.

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

# Evidence-bound functional requirements

Load `work-controller:work-record` for run ownership and authorization. Read
`references/frd-schema.md` before constructing or changing extraction data.
The helper is
`python "<plugin-root>/skills/frd-method/scripts/frd_tool.py"`.
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
